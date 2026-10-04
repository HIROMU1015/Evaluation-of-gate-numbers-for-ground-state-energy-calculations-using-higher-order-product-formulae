"""Two-stage bounded H-chain preparation; NOT the nine-candidate validation.

inputs: sanitize H2/H4, generate H6 H/CISD, freeze bytes/identity.
reference: require the input freeze commit, acquire H2/H6 fixed 34-point grids,
reuse H4 saved reference, freeze nine absolute coordinates, stop for review.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

import numpy as np

from review_response.hchain_input_reference_preparation import (
    AllowlistedArchive, Ledger, PreparationError, VectorAdapter, bounded_stage,
    candidate_rows, canonical_hash, checked_functions, reference_result,
    sha_array, sha_file, state_identity, write_json,
)


DOC = "docs/second_study_v2/hchain_input_reference_preparation_20261004"
OLD = "docs/second_study_v2/hchain_independent_validation_20261004"
INPUT_FILES = ("INPUT_FROZEN.json", "input_identity.json", "runtime_manifest.json",
               "source_audit.json", "input_access_audit.json", "input_resource_audit.json")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def environment(contract):
    expected = contract["environment"]
    actual = {"python": sys.executable, "python_version": platform.python_version(),
              "packages": {name: version(name) for name in expected["packages"]},
              "variables": {key: os.environ.get(key) for key in expected["variables"]}}
    if actual != expected:
        raise PreparationError("fixed process environment mismatch")
    if "cupy" in sys.modules:
        raise PreparationError("CuPy was imported")
    return actual


def source_gate(root):
    manifest = json.loads((root / DOC / "implementation_manifest.json").read_text())
    rows = []
    for entry in manifest["files"]:
        path = root / entry["path"]
        data = path.read_bytes()
        if len(data) != entry["bytes"] or sha_file(path) != entry["sha256"]:
            raise PreparationError(f"implementation identity mismatch: {entry['path']}")
        if data != git(root, "show", f"HEAD:{entry['path']}"):
            raise PreparationError(f"uncommitted source: {entry['path']}")
        rows.append(entry)
    # Preserve both the full old manifest and every listed artifact.
    old_manifest = root / OLD / "manifest.json"
    if sha_file(old_manifest) != "62a4dcb19e48678f88a21571fbd00bf64ebfabbb2837b8678a72db37afa658fa":
        raise PreparationError("old planning manifest changed")
    for entry in json.loads(old_manifest.read_text())["files"]:
        path = root / OLD / entry["path"]
        if sha_file(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise PreparationError("old formal artifact changed")
    if git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise PreparationError("tracked/staged worktree must be clean")
    return {"commit": git(root, "rev-parse", "HEAD").decode().strip(),
            "branch": git(root, "branch", "--show-current").decode().strip(),
            "files": rows, "manifest_sha256": sha_file(root / DOC / "implementation_manifest.json"),
            "original_formal_artifacts_changed": False}


def determinant_functions(root, authorization):
    source = authorization["determinant_helpers"]
    return checked_functions(root / source["path"], source["sha256"],
                             ("sector_basis_indices", "hartree_fock_full_basis_index",
                              "determinant_excitation_rank", "determinant_cisd_state"))


def historical_inputs(root, contract, helpers, ledger, access):
    first = json.loads((root / DOC / "archived_input_contract.json").read_text())["source_identity"]
    specifications = contract["systems"][:2]
    group_keys = [key for system in ("h2_arrays_for_experiment_a", "h4_arrays")
                  for key in first[system]["ordered_group_keys"]]
    f01 = AllowlistedArchive(root / first["f01_bundle"]["path"], first["f01_bundle"]["sha256"],
                             ["H2_hamiltonian", "H4_hamiltonian", *group_keys], access)
    states = AllowlistedArchive(root / first["h01_state_bundle"]["path"], first["h01_state_bundle"]["sha256"],
                                ["H2_cisd_state", "H4_cisd_state"], access)
    result, identities = {}, {}
    try:
        for spec in specifications:
            name = spec["system"]
            arrays = first["h2_arrays_for_experiment_a" if name == "H2" else "h4_arrays"]
            h_key = arrays["hamiltonian_key" if name == "H2" else "experiment_hamiltonian_key"]
            h = f01.read(h_key)
            h_hash = arrays["hamiltonian_sha256" if name == "H2" else "experiment_hamiltonian_sha256"]
            if sha_array(h) != h_hash:
                raise PreparationError(f"{name} Hamiltonian identity mismatch")
            groups = [f01.read(key) for key in arrays["ordered_group_keys"]]
            if [sha_array(group) for group in groups] != arrays["ordered_group_sha256"]:
                raise PreparationError(f"{name} group identity mismatch")
            state = states.read(f"{name}_cisd_state")
            if name == "H4" and sha_array(state) != spec["CISD_array_sha256"]:
                raise PreparationError("H4 saved CISD identity mismatch")
            indices = helpers["sector_basis_indices"](spec["num_qubits"], spec["sector_kind"],
                                                       [spec["n_alpha"], spec["n_beta"]])
            if sha_array(indices) != arrays["sector_indices_sha256"]:
                raise PreparationError("archived sector identity mismatch")
            reference = helpers["hartree_fock_full_basis_index"](
                spec["num_qubits"], spec["sector_kind"], [spec["n_alpha"], spec["n_beta"]])
            identities[name] = state_identity(h, groups, state, indices, reference, ledger)
            identities[name].update({"origin": "byte_identical_archived_CISD_reuse", "K": spec["K"],
                                     "archive_origin_commit": first["h01_state_bundle"]["generation_worktree_head_recorded_by_manifest"],
                                     "archive_publication_commit": first["h01_state_bundle"]["publication_commit"],
                                     "verified_snapshot_commit": "99791c0271c8972e90d5fb486ab03f603196bd89"})
            result[name] = {"hamiltonian": h, "groups": groups, "cisd": state, "sector_indices": indices}
    finally:
        f01.close()
        states.close()
    return result, identities


def generate_h6(root, runtime, spec, helpers, ledger):
    """Historical integral/group recipe WITHOUT its exact-ground/Z2 tail."""
    from pyscf import ao2mo, gto, mcscf, scf
    from openfermion import FermionOperator, QubitOperator, jordan_wigner
    from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
    from trotterlib.component_sector_pf import qubit_operator_sector_matrix
    from trotterlib.pf_decomposition import iter_s2_sequence_steps

    ledger.charge("H6_Hamiltonian_generations", 1)
    mol = gto.Mole()
    mol.atom = [("H", (0.0, 0.0, float(i - 2.5))) for i in range(6)]
    mol.unit, mol.basis, mol.spin, mol.charge, mol.symmetry = "Angstrom", "sto-3g", 0, 0, False
    mol.verbose, mol.output = 3, str(runtime / "h6_rhf.log")
    mol.build()
    mean_field = scf.RHF(mol)
    mean_field.conv_tol, mean_field.max_cycle = 1e-12, 200
    mean_field.kernel()
    if not mean_field.converged or mol.nelectron != 6 or mean_field.mo_coeff.shape != (6, 6):
        raise PreparationError("H6 RHF convergence/orbital/electron gate failed")
    cas = mcscf.CASCI(mean_field, 6, 6)
    cas.ncore = 0
    h1, core_energy = cas.get_h1eff(mean_field.mo_coeff)  # no CASCI kernel / exact solve
    eri = ao2mo.restore(1, ao2mo.kernel(mol, mean_field.mo_coeff[:, :6]), 6)
    two_body = np.asarray(eri.transpose(0, 2, 3, 1), order="C")
    with (runtime / "h6_grouping.log").open("w") as log, redirect_stdout(log):
        grouper = Almost_optimal_grouper(float(core_energy), np.asarray(h1), two_body,
                                        fermion_qubit_mapping=jordan_wigner, validation=True)
    grouped = grouper.group_term_list
    grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
    groups_ops = []
    maximum_imaginary = 0.0
    for group in grouped:
        op = jordan_wigner(sum(group, FermionOperator()))
        real_op = QubitOperator()
        for term, coefficient in op.terms.items():
            maximum_imaginary = max(maximum_imaginary, abs(complex(coefficient).imag))
            if abs(complex(coefficient).imag) > 1e-9:
                raise PreparationError("imaginary Pauli coefficient gate failed")
            real_op += QubitOperator(term, float(complex(coefficient).real))
        groups_ops.append(real_op)
    ordered_structure = [[[[int(q), str(p)] for q, p in term] for term in group.terms] for group in groups_ops]
    grouping_hash = canonical_hash(ordered_structure)
    if len(groups_ops) != spec["group_count"] or grouping_hash != spec["ordered_group_structure_sha256"]:
        raise PreparationError("H6 ordered grouping structure identity mismatch; no regrouping rescue")
    counts = [sum(bool(term) for term in group.terms) for group in groups_ops]
    pf = json.loads((root / OLD / "system_and_pf_contract.json").read_text())["PF"]
    rotations = sum(counts[index] for index, weight in iter_s2_sequence_steps(len(counts), pf["s2_sequence"]))
    if rotations != spec["K"]:
        raise PreparationError("H6 merged Pauli-rotation K mismatch")
    indices = helpers["sector_basis_indices"](12, "fixed_half_populations", [3, 3])
    if len(indices) != 400:
        raise PreparationError("H6 must use the full 400-dimensional population sector")
    groups = [qubit_operator_sector_matrix(op, 12, indices, remove_constant=True).toarray() for op in groups_ops]
    h = sum(groups, np.zeros((400, 400), dtype=np.complex128))
    reference = helpers["hartree_fock_full_basis_index"](12, "fixed_half_populations", [3, 3])
    ledger.charge("H6_CISD_generations", 1)
    state, generation = helpers["determinant_cisd_state"](h, indices, reference)
    ledger.counts["CISD_subspace_eigh_calls"] += 1
    # Predeclared new-state gauge: largest-magnitude component real positive.
    pivot = int(np.argmax(np.abs(state)))
    state *= np.exp(-1j * np.angle(state[pivot]))
    if state[pivot].real < 0:
        state *= -1
    identity = state_identity(h, groups, state, indices, reference, ledger)
    identity.update({"origin": "new_same_recipe_population_sector_RHF_CISD", "K": rotations,
                     "grouping_structure_sha256": grouping_hash, "maximum_removed_imaginary_coefficient": maximum_imaginary,
                     "RHF_energy_hartree": float(mean_field.e_tot), "RHF_converged": True,
                     "RHF_orbitals_sha256_numpy_v1": sha_array(mean_field.mo_coeff),
                     "CISD_lowest_subspace_energy_hartree": generation["lowest_subspace_energy_hartree"],
                     "CISD_generation_seconds": generation["state_generation_seconds"],
                     "new_state_gauge": "largest_magnitude_component_real_positive_no_exact_alignment",
                     "historical_exact_Z2_200_sector_used": False,
                     "historical_coefficient_byte_identity_claimed": False})
    np.savez_compressed(runtime / "h6_orbitals_integrals.npz", mo_coeff=mean_field.mo_coeff,
                        h1_effective=h1, two_body=two_body, core_energy=np.asarray(core_energy))
    term_records = [[{"term": [[int(q), str(p)] for q, p in term],
                      "coefficient": [float(complex(coef).real), float(complex(coef).imag)]}
                     for term, coef in op.terms.items()] for op in groups_ops]
    write_json(runtime / "h6_group_operators.json", {"groups": term_records, "Pauli_counts": counts})
    return {"hamiltonian": h, "groups": groups, "cisd": state, "sector_indices": indices}, identity


def save_sanitized(runtime, systems):
    for name, system in systems.items():
        arrays = {key: system[key] for key in ("hamiltonian", "cisd", "sector_indices")}
        arrays.update({f"group_{i:03d}": group for i, group in enumerate(system["groups"])})
        np.savez_compressed(runtime / f"{name}_predictor_input.npz", **arrays)
    return {"files": [{"path": str(path.relative_to(runtime)), "bytes": path.stat().st_size,
                       "sha256": sha_file(path)} for path in sorted(runtime.iterdir()) if path.is_file()],
            "copy_of_mixed_original_archive": False, "predictor_state_keys": ["cisd"],
            "exact_ground_direct_oracle_fields": 0}


def freeze_inputs(root, output, auth, source, env, ledger):
    if output.exists():
        raise PreparationError("new input output required; overwrite/retry prohibited")
    output.mkdir(parents=True)
    runtime = output / ".runtime"
    runtime.mkdir()
    access = []
    write_json(output / "source_audit.json", {**source, "environment": env})
    helpers = determinant_functions(root, auth)
    contract = json.loads((root / OLD / "system_and_pf_contract.json").read_text())
    with bounded_stage(ledger, "input_state_preparation"):
        systems, identities = historical_inputs(root, contract, helpers, ledger, access)
        systems["H6"], identities["H6"] = generate_h6(root, runtime, contract["systems"][2], helpers, ledger)
        runtime_manifest = save_sanitized(runtime, systems)
    write_json(output / "input_identity.json", identities)
    write_json(output / "runtime_manifest.json", runtime_manifest)
    write_json(output / "input_access_audit.json", {"archive_member_reads": access,
                                                   "truth_array_reads": 0, "oracle_alignment": False,
                                                   "boundary": "runtime_member_allowlist_not_claim_of_historical_orchestrator_blindness"})
    write_json(output / "input_resource_audit.json", ledger.payload())
    frozen = {"status": "hchain_input_frozen_reference_not_acquired",
              "origin_implementation_commit": source["commit"], "runtime_manifest_sha256": sha_file(output / "runtime_manifest.json"),
              "input_identity_sha256": sha_file(output / "input_identity.json"),
              "reference_grid_sha256": sha_file(root / DOC / "reference_grid.json"),
              "candidate_science_authorized": False, "truth_authorized_now": False,
              "files": [{"path": name, "bytes": (output / name).stat().st_size,
                         "sha256": sha_file(output / name)} for name in INPUT_FILES if name != "INPUT_FROZEN.json"]}
    write_json(output / "INPUT_FROZEN.json", frozen)
    print(json.dumps({"status": frozen["status"], "counts": ledger.payload()["counts"]}), flush=True)


def frozen_input_gate(root, output, input_commit, source):
    if source["commit"] != input_commit:
        raise PreparationError("HEAD must be the exact input freeze commit")
    previous = git(root, "rev-parse", input_commit + "^").decode().strip()
    changed = git(root, "diff", "--name-only", previous, input_commit).decode().splitlines()
    relative = output.relative_to(root)
    if set(changed) != {str(relative / name) for name in INPUT_FILES}:
        raise PreparationError("input freeze commit must contain exactly six lightweight files")
    for name in INPUT_FILES:
        if (output / name).read_bytes() != git(root, "show", f"{input_commit}:{relative / name}"):
            raise PreparationError("input freeze bytes changed")
    frozen = json.loads((output / "INPUT_FROZEN.json").read_text())
    for entry in frozen["files"]:
        path = output / entry["path"]
        if sha_file(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise PreparationError("input freeze hash mismatch")
    manifest = json.loads((output / "runtime_manifest.json").read_text())
    runtime = output / ".runtime"
    actual_set = {str(path.relative_to(runtime)) for path in runtime.iterdir() if path.is_file()}
    if actual_set != {entry["path"] for entry in manifest["files"]}:
        raise PreparationError("sanitized runtime file-set mismatch")
    for entry in manifest["files"]:
        path = runtime / entry["path"]
        if sha_file(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise PreparationError("sanitized runtime byte identity mismatch")
    if frozen["reference_grid_sha256"] != sha_file(root / DOC / "reference_grid.json"):
        raise PreparationError("reference grid changed after input freeze")
    return json.loads((output / "input_identity.json").read_text()), frozen


def acquire_references(root, output, auth, source, env, ledger, input_commit):
    if any((output / name).exists() for name in ("REFERENCE_STARTED.json", "COMPLETE.json", "STOPPED.json")):
        raise PreparationError("one reference acquisition only; no retry/output switch")
    identities, frozen = frozen_input_gate(root, output, input_commit, source)
    started_at = datetime.now(timezone.utc).isoformat()
    write_json(output / "REFERENCE_STARTED.json", {"input_commit": input_commit, "start_UTC": started_at,
                                                  "source_manifest_sha256": source["manifest_sha256"]})
    fit_contract = json.loads((root / OLD / "cheap_reference_scale_contract.json").read_text())
    helper = fit_contract["fit_function"]
    fit_function = checked_functions(root / helper["path"], helper["sha256"], ["leading_fit"])["leading_fit"]
    sequence = json.loads((root / OLD / "system_and_pf_contract.json").read_text())["PF"]["s2_sequence"]
    saved_metadata = json.loads((root / DOC / "saved_h4_reference_contract.json").read_text())
    if [float(w).hex() for w in sequence] != [float(w).hex() for w in saved_metadata["PF_sequence"]]:
        raise PreparationError("saved H4 PF coefficient ULP identity mismatch")
    if saved_metadata["K"] != identities["H4"]["K"]:
        raise PreparationError("saved H4 PF K identity mismatch")
    for key in ("rolling_window_points", "noise_floor_hartree", "formal_order_tolerance", "minimum_r_squared"):
        if saved_metadata["fit_specification"][key] != fit_contract["fit_rules"][key]:
            raise PreparationError("saved H4 leading-fit specification mismatch")
    grid = json.loads((root / DOC / "reference_grid.json").read_text())["points"]
    times = [float.fromhex(row["hex"]) for row in grid]
    if any(float(row["time"]).hex() != t.hex() for row, t in zip(grid, times, strict=True)):
        raise PreparationError("grid value/hex mismatch")
    references, point_rows = {}, []
    with bounded_stage(ledger, "reference_calibration"):
        for name in ("H2", "H6"):
            path = output / ".runtime" / f"{name}_predictor_input.npz"
            member_log = []
            keys = ["hamiltonian", "cisd", "sector_indices"] + [f"group_{i:03d}" for i in range(len(identities[name]["group_sha256_numpy_v1"]))]
            archive = AllowlistedArchive(path, sha_file(path), keys, member_log)
            try:
                h = archive.read("hamiltonian")
                state = archive.read("cisd")
                groups = [archive.read(key) for key in keys[3:]]
            finally:
                archive.close()
            if sha_array(h) != identities[name]["H_sha256_numpy_v1"] or sha_array(state) != identities[name]["CISD_sha256_numpy_v1"]:
                raise PreparationError("reference input individual array identity mismatch")
            adapter = VectorAdapter(h, groups, sequence, ledger)
            points = []
            for index, t in enumerate(times):
                point = {"system": name, "grid_index": index, **adapter.cheap(state, t)}
                points.append(point)
                point_rows.append(point)
                write_json(output / "reference_points_checkpoint.json", {"points": point_rows,
                                                                         "resource": ledger.payload()})
            ledger.counts["reference_fit_calls"] += 1
            references[name] = reference_result(times, points, fit_function, fit_contract["fit_rules"], auth["epsilon_E"])
            print(json.dumps({"system": name, "t_ref": references[name]["t_ref"], "points": len(points)}), flush=True)
        saved = fit_contract["saved_values"]["H4"]
        path = root / saved["source"]["path"]
        if sha_file(path) != saved["source"]["sha256"]:
            raise PreparationError("H4 saved cheap prediction identity mismatch")
        prediction = json.loads(path.read_text())
        rows = [row for row in prediction["experiment_B"]["formula_predictions"] if row["formula_id"] == "current_m3"]
        if len(rows) != 1:
            raise PreparationError("H4 current_m3 prediction identity ambiguous")
        row = rows[0]
        alpha = row["leading_fit"]["selected_window"]["fixed_order_alpha"]
        # Source key is the historical decision time scale, not a direct optimum.
        time_value = row["proxy_t_ana_hartree_inverse"]
        if float(alpha).hex() != float(saved["alpha_C"]).hex() or float(time_value).hex() != float(saved["t_ref"]).hex():
            raise PreparationError("H4 saved alpha/t_ref identity mismatch")
        references["H4"] = {"alpha_C": alpha, "t_ref": time_value, "t_ref_hex": float(time_value).hex(),
                             "source": "identity_verified_saved_cheap_scalar_reuse", "saved_prediction_sha256": sha_file(path),
                             "origin_commit": saved["source"]["source_commit"], "leading_fit": row["leading_fit"],
                             "new_cheap_actions": 0, "is_oracle_time": False}
    candidates = candidate_rows(references)
    with (output / "candidate_plan.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0]))
        writer.writeheader()
        writer.writerows(candidates)
    write_json(output / "reference_results.json", references)
    write_json(output / "reference_resource_audit.json", {**ledger.payload(), "environment": env,
                                                         "input_preparation_accounted_separately": "input_resource_audit.json"})
    decision = {"status": "hchain_input_reference_preparation_complete_execution_ready",
                "execution_ready": "inputs_coordinates_adapter_schedule_and_scorer_method_only",
                "input_freeze_commit": input_commit, "source_commit": source["commit"],
                "system_count": 3, "candidate_count_frozen": 9, "candidate_cheap_count": 0,
                "candidate_M1_count": 0, "direct_truth_count": 0, "target_phase_gap_count": 0,
                "reference_points_computed": 68, "reference_scales_computed": 2, "reference_scales_reused": 1,
                "candidate_scientific_execution_authorized": False, "truth_authorized": False,
                "push_authorized": False, "old_formal_statuses_unchanged": True,
                "next": "review_this_freeze_then_separately_authorize_one_nine_coordinate_run",
                "remaining_not_claimed": ["M1 performance", "combined H1 measured cost", "direct branch/gap gates", "rigorous width certificate", "holdout generalization"]}
    write_json(output / "COMPLETE.json", decision)
    report = ["# H-chain truth-free input/reference preparation", "", f"Status: `{decision['status']}`", "",
              "Inputs and coordinates are ready for a separately authorized candidate run; that run has NOT occurred.", "",
              "| System | sector | CISD dimension | t_ref | source |", "|---|---:|---:|---:|---|"]
    for name in ("H2", "H4", "H6"):
        report.append(f"| {name} | {identities[name]['sector_dimension']} | {identities[name]['CISD_subspace_dimension']} | {references[name]['t_ref']:.17g} | {references[name]['source']} |")
    report.extend(["", "H6 is a new frozen coefficient snapshot in the 400-dimensional population sector, not historical 200-dimensional exact/Z2 data.",
                   "", "68 cheap points only; candidate M1, direct truth, target gaps, performance scoring and GPU operations: 0.",
                   "", "H1 combined schedule was stub-tested, not scientifically executed. Internal expm_multiply matvec count remains unknown.",
                   "", "Old blocked/formal results are preserved. The new execution-ready status is limited to preparation, not permission to run candidates."])
    (output / "report.md").write_text("\n".join(report) + "\n")
    names = [*INPUT_FILES, "REFERENCE_STARTED.json", "reference_points_checkpoint.json",
             "candidate_plan.csv", "reference_results.json", "reference_resource_audit.json", "COMPLETE.json", "report.md"]
    write_json(output / "manifest.json", {"manifest_self_excluded": True, "runtime_separately_hash_frozen": True,
                                         "files": [{"path": name, "bytes": (output / name).stat().st_size,
                                                    "sha256": sha_file(output / name)} for name in names]})
    print(json.dumps(decision), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("inputs", "reference"), required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-commit")
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = (root / args.output_dir).resolve()
    if not output.is_relative_to(root / "artifacts"):
        raise PreparationError("output must be a new scoped project artifacts directory")
    # Refusing an existing run must not append a failure marker to that run.
    if args.stage == "inputs" and output.exists():
        raise PreparationError("new input output required; existing directory left unchanged")
    if args.stage == "reference" and any((output / name).exists() for name in
                                         ("REFERENCE_STARTED.json", "COMPLETE.json", "STOPPED.json")):
        raise PreparationError("existing reference attempt left unchanged; retry prohibited")
    auth = json.loads((root / DOC / "authorization.json").read_text())
    env = environment(auth)
    source = source_gate(root)
    ledger = Ledger()
    if auth["scope"] != "truth_free_input_reference_preparation_only":
        raise PreparationError("invalid preparation authorization")
    try:
        if args.stage == "inputs":
            freeze_inputs(root, output, auth, source, env, ledger)
        else:
            if not args.input_commit:
                raise PreparationError("reference acquisition requires an input freeze commit")
            acquire_references(root, output, auth, source, env, ledger, args.input_commit)
        if "cupy" in sys.modules:
            raise PreparationError("CuPy import gate failed")
    except Exception as exc:
        if output.is_dir() and not (output / "STOPPED.json").exists():
            write_json(output / "STOPPED.json", {"stage": args.stage, "status": "failed_preparation_stop_no_rescue",
                                               "error": str(exc), "exception": type(exc).__name__,
                                               "resource": ledger.payload(), "candidate_execution_authorized": False})
        raise


if __name__ == "__main__":
    main()
