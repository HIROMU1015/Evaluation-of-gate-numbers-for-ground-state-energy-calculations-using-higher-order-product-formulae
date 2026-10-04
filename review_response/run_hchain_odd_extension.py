"""Bounded H3/H5/H7 input -> prediction freezes -> truth -> immutable scoring.

Each phase is one-shot. Failure never authorizes a rerun, changed rule or cache.
H8 is not an executable system in this runner.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

import numpy as np

from review_response.hchain_input_reference_preparation import (
    AllowlistedArchive, PreparationError, VectorAdapter, bounded_stage,
    canonical_hash, checked_functions, sha_array, sha_file, state_identity, write_json,
)
from review_response.hchain_prediction_phase import (
    CoordinateActions, ReadBoundary, finite_json, verify_blob, verify_entries,
)
from review_response.hchain_selective_calibration_schedule import (
    BETA, EPSILON, run_shared_schedule, spectral_policy,
)
from review_response.pf_spectral_recoverability_d2 import analyze_coordinate
from review_response.run_hchain_prediction_phase import fixed_environment
from review_response.hchain_truth_scoring import (
    METHOD, bundle, commit_stage, truth_quality, verify_stage,
)
from review_response.run_hchain_truth_scoring import (
    full_unitary, ground_point, helper, serial_truth, utc, write_csv,
)
from review_response.hchain_odd_extension import (
    BASE, DOC, OLD, OUT, PREP_DOC, SYSTEMS, STATUS, SystemLedger,
    commit_files, dimensions, file_entry, git, immutable_score,
    plan_rows, primary_rank, seal, source_gate, validate_plan,
)


def read(path):
    return json.loads(path.read_text())


def freeze(root, out, name, payload, marker, source, access, resource):
    files = bundle(out/name, "payload.json", "FREEZE.json", payload,
                   {"kind": marker, "utc": utc()}, source, access, resource)
    commit = commit_stage(root, out/name, files, f"Freeze odd-chain {marker}")
    verify_stage(root, out/name, commit, "FREEZE.json")
    print(json.dumps({"event": marker, "commit": commit}), flush=True)
    return commit


def frozen(root, out, name):
    path = out/name/"FREEZE.json"
    origin = git(root, "log", "-1", "--format=%H", "--", str(path.relative_to(root))).decode().strip()
    if not origin:
        raise PreparationError(f"{name} stage is not committed")
    verify_stage(root, out/name, origin, "FREEZE.json")
    return read(out/name/"payload.json"), origin


def validate_runtime(out, inputs, *, allow_ground=False):
    runtime = out/".runtime"
    entries = inputs["runtime_files"]
    expected = {row["path"] for row in entries}
    found = {str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file()}
    if allow_ground:
        found -= {f"{name}_ground.npz" for name in SYSTEMS}
    if expected != found or runtime.is_symlink() or any(path.is_symlink() for path in runtime.rglob("*")):
        raise PreparationError("frozen input runtime file set/link mismatch")
    verify_entries(runtime, entries)


def load_system(out, inputs, name, ledger, members, sequence, scopes, *, allow_ground=False):
    validate_runtime(out, inputs, allow_ground=allow_ground)
    spec = inputs["input_identity"][name]
    keys = ["hamiltonian", "cisd", "sector_indices"] + [f"group_{i:03d}" for i in range(spec["group_count"])]
    entry = next(row for row in inputs["runtime_files"] if row["path"] == f"{name}_input.npz")
    archive = AllowlistedArchive(out/".runtime"/entry["path"], entry["sha256"], keys, members)
    try:
        if set(archive.archive.files) != set(keys):
            raise PreparationError("input NPZ key set mismatch")
        h, state, indices = [archive.read(key) for key in keys[:3]]
        groups = [archive.read(key) for key in keys[3:]]
    finally:
        archive.close()
    if (sha_array(h) != spec["H_sha256_numpy_v1"] or sha_array(state) != spec["CISD_sha256_numpy_v1"]
            or sha_array(indices) != spec["sector_indices_sha256_numpy_v1"]
            or [sha_array(g) for g in groups] != spec["group_sha256_numpy_v1"]):
        raise PreparationError("input individual array identity mismatch")
    return {"state": state, "adapter": VectorAdapter(h, groups, sequence, ledger, allowed_kinds=scopes)}


def generate(root, out, spec, helpers, ledger, sequence, chemistry_sha):
    """Canonical integral/group recipe, with no historical exact-ground tail."""
    from pyscf import ao2mo, gto, mcscf, scf
    from openfermion import FermionOperator, QubitOperator, InteractionOperator, get_fermion_operator, jordan_wigner
    from openfermion.chem.molecular_data import spinorb_from_spatial
    from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
    from trotterlib.component_sector_pf import qubit_operator_sector_matrix
    from trotterlib.pf_decomposition import iter_s2_sequence_steps

    name, n = spec["system"], spec["atoms"]
    private = out/".runtime"
    ledger.charge("Hamiltonian_generations", 1)
    mol = gto.Mole()
    mol.atom = [("H", (0., 0., float(i-(n-1)/2))) for i in range(n)]
    mol.unit, mol.basis, mol.spin, mol.charge, mol.symmetry = "Angstrom", "sto-3g", 2, 1, False
    mol.verbose, mol.output = 3, str(private/f"{name}_scf.log")
    mol.build()
    hf = scf.RHF(mol)  # Installed PySCF dispatches nonzero spin to ROHF.
    hf.conv_tol, hf.max_cycle = 1e-12, 200
    hf.kernel()
    if not hf.converged or mol.nelectron != n-1 or hf.mo_coeff.shape != (n, n):
        raise PreparationError("canonical SCF convergence/orbital/electron gate failed")
    cas = mcscf.CASCI(hf, n, (spec["n_alpha"], spec["n_beta"]))
    cas.ncore = 0
    h1, scalar = cas.get_h1eff(hf.mo_coeff)  # NO CASCI kernel/FCI.
    eri = ao2mo.restore(1, ao2mo.kernel(mol, hf.mo_coeff), n)
    two = np.asarray(eri.transpose(0, 2, 3, 1), order="C")
    if name == "H3":
        one_spin, two_spin = spinorb_from_spatial(h1, two)
        op = jordan_wigner(get_fermion_operator(InteractionOperator(float(scalar), one_spin, .5*two_spin)))
        group_function = checked_functions(root/"src/trotterlib/chemistry_hamiltonian.py", chemistry_sha,
            ["min_hamiltonian_grouper"], {"QubitOperator": QubitOperator})["min_hamiltonian_grouper"]
        ops, _ = group_function(op, name)
    else:
        with (private/f"{name}_grouping.log").open("w") as log, redirect_stdout(log):
            grouper = Almost_optimal_grouper(float(scalar), np.asarray(h1), two,
                                            fermion_qubit_mapping=jordan_wigner, validation=True)
        grouped = grouper.group_term_list
        grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
        ops = [jordan_wigner(sum(group, FermionOperator())) for group in grouped]
    real_ops, maximum_imaginary = [], 0.
    for op in ops:
        real_op = QubitOperator()
        for term, coefficient in op.terms.items():
            maximum_imaginary = max(maximum_imaginary, abs(complex(coefficient).imag))
            if abs(complex(coefficient).imag) > 1e-9:
                raise PreparationError("imaginary Pauli coefficient gate failed")
            real_op += QubitOperator(term, float(complex(coefficient).real))
        real_ops.append(real_op)
    counts = [sum(bool(term) for term in op.terms) for op in real_ops]
    k = sum(counts[index] for index, weight in iter_s2_sequence_steps(len(counts), sequence))
    indices = helpers["sector_basis_indices"](2*n, spec["sector_kind"], [spec["n_alpha"], spec["n_beta"]])
    if len(indices) != spec["sector_dimension"]:
        raise PreparationError("population dimension mismatch")
    groups = [qubit_operator_sector_matrix(op, 2*n, indices, remove_constant=True).toarray() for op in real_ops]
    h = sum(groups, np.zeros((len(indices),)*2, dtype=np.complex128))
    reference = helpers["hartree_fock_full_basis_index"](2*n, spec["sector_kind"], [spec["n_alpha"], spec["n_beta"]])
    ledger.charge("CISD_generations", 1)
    state, generation = helpers["determinant_cisd_state"](h, indices, reference)
    ledger.counts["CISD_subspace_eigh_calls"] += 1
    state *= np.exp(-1j*np.angle(state[int(np.argmax(np.abs(state)))]))
    identity = state_identity(h, groups, state, indices, reference, ledger)
    if identity["CISD_subspace_dimension"] != spec["CISD_dimension"]:
        raise PreparationError("CISD dimension mismatch")
    terms = [[{"term": [[int(q), str(p)] for q, p in term], "coefficient": float(coef.real)}
              for term, coef in op.terms.items()] for op in real_ops]
    identity.update({"K": k, "group_count": len(groups), "nonidentity_Pauli_counts": counts,
        "ordered_term_coefficient_sha256": canonical_hash(terms),
        "ordered_group_structure_sha256": canonical_hash([[r["term"] for r in g] for g in terms]),
        "CISD_positions_sha256_numpy_v1": sha_array(np.asarray(identity["CISD_positions"], dtype=np.int64)),
        "MO_sha256_numpy_v1": sha_array(hf.mo_coeff), "SCF_method": type(hf).__name__,
        "SCF_converged": True, "maximum_discarded_imaginary_Pauli_coefficient": maximum_imaginary,
        "CISD_equals_full_population_sector": spec["CISD_dimension"] == len(indices),
        "CISD_is_ground_certificate": False, "new_state_phase": "largest_component_real_positive",
        "generation_source": "review_response/run_hchain_odd_extension.py",
        "generation_source_sha256": sha_file(root/"review_response/run_hchain_odd_extension.py"),
        "historical_byte_identity_claim": False, "exact_state_input_used": False})
    arrays = {"hamiltonian": h, "cisd": state, "sector_indices": indices}
    arrays.update({f"group_{i:03d}": g for i, g in enumerate(groups)})
    np.savez_compressed(private/f"{name}_input.npz", **arrays)
    np.savez_compressed(private/f"{name}_integrals.npz", mo=hf.mo_coeff, h1=h1, two_body=two, scalar=np.asarray(scalar))
    write_json(private/f"{name}_group_operators.json", {"groups": terms, "K": k, "counts": counts})
    return identity


def execute(root, phase):
    start, start_utc = time.perf_counter(), utc()
    source = source_gate(root)
    auth = read(root/DOC/"protocol.json")
    if str(root) != auth["worktree"] or git(root, "branch", "--show-current").decode().strip() != auth["branch"]:
        raise PreparationError("dedicated extension worktree/branch required")
    env = fixed_environment(auth)
    out = root/OUT
    if (out/phase).exists() or (out/f"{phase}_STARTED.json").exists() or (out/f"{phase}_FAILURE.json").exists():
        raise PreparationError("phase already started; no retry or alternate output")
    if phase == "inputs" and out.exists():
        raise PreparationError("one new output only")
    inherited_paths = [root/r["path"] for r in source["inherited_sources"]]
    allowed = inherited_paths + [root/r["path"] for r in source["new_files"]]
    allowed += [root/DOC/"implementation_manifest.json"]
    # Importable source text is permitted, not arbitrary repository artifacts.
    allowed += list((root/"src").rglob("*.py")) + list((root/"review_response").glob("*.py"))
    boundary = ReadBoundary(root, allowed, out)
    sys.addaudithook(boundary.hook)
    ledgers = {s["system"]: SystemLedger(s["primary_m"]) for s in auth["systems"]}
    members, events, stages = [], [], {}
    out.mkdir(exist_ok=True)
    write_json(out/f"{phase}_STARTED.json", {"utc": start_utc, "HEAD": source["execution_HEAD"], "one_shot": True})
    def resource():
        payloads = {n:l.payload() for n,l in ledgers.items()}
        for value in payloads.values():
            value["combined_H1_cost"] = "see_prediction_schedule_resource_only" if phase == "prediction" else "not_a_combined_H1_measurement"
            value["peak_RSS_scope"] = "process_high_water_not_independently_isolated_system_peak"
        return {"phase": phase, "systems": payloads,
                "counts_are_phase_specific_not_cumulative": True,
                "process_elapsed_before_final_write_seconds": time.perf_counter()-start}
    def access():
        payload = boundary.payload(members)
        payload["truth_array_reads"] = sum(l.counts["truth_array_reads"] for l in ledgers.values())
        payload["truth_phase_authorized"] = phase == "truth"
        return payload
    def do_freeze(name, payload, marker):
        return freeze(root, out, name, payload, marker, source_gate(root), access(), resource())
    try:
        sequence = [float.fromhex(h) for h in auth["PF"]["canonical_sequence_hex"]]
        if phase == "inputs":
            (out/".runtime").mkdir()
            identity = {}
            helpers_spec = auth["determinant_helpers"]
            helpers = checked_functions(root/helpers_spec["path"], helpers_spec["sha256"],
                ["sector_basis_indices", "hartree_fock_full_basis_index", "determinant_excitation_rank", "determinant_cisd_state"])
            chemistry = next(r for r in source["inherited_sources"] if r["path"] == "src/trotterlib/chemistry_hamiltonian.py")
            for spec in auth["systems"]:
                name = spec["system"]
                with bounded_stage(ledgers[name], f"{name}_input", 1800):
                    identity[name] = generate(root, out, spec, helpers, ledgers[name], sequence, chemistry["sha256"])
                print(json.dumps({"event": "INPUT_GENERATED", "system": name, "dimension": spec["sector_dimension"], "K": identity[name]["K"]}), flush=True)
            runtime_rows = [file_entry(out/".runtime", p) for p in sorted((out/".runtime").iterdir()) if p.is_file()]
            payload = {"system_identity": auth["systems"], "input_identity": identity, "runtime_files": runtime_rows,
                       "environment": env, "truth_opened": False}
            do_freeze("inputs", payload, "INPUT_FROZEN")
        elif phase == "reference":
            inputs, stages["input_commit"] = frozen(root, out, "inputs")
            references, point_rows = {}, []
            fit_contract = read(root/OLD/"cheap_reference_scale_contract.json")
            fit_spec = fit_contract["fit_function"]
            fit_function = checked_functions(root/fit_spec["path"], fit_spec["sha256"], ["leading_fit"])["leading_fit"]
            times = [float.fromhex(row["hex"]) for row in auth["reference_grid"]]
            for spec in auth["systems"]:
                name, ledger = spec["system"], ledgers[spec["system"]]
                points = []
                with bounded_stage(ledger, f"{name}_reference", 1800):
                    system = load_system(out, inputs, name, ledger, members, sequence, ("reference",))
                    for t in times:
                        points.append({"system": name, **system["adapter"].cheap(system["state"], t)})
                    fit = fit_function(times, [p["delta_C_hartree"] for p in points], fit_contract["fit_rules"], 4)
                point_rows.extend(points)
                ref = {"qualified": fit["qualified"], "leading_fit": finite_json(fit), "t_ref": None, "t_ref_hex": None}
                if ref["qualified"]:
                    alpha = float(fit["selected_window"]["fixed_order_alpha"])
                    t_ref = float((EPSILON/(5*alpha))**.25)
                    if not np.isfinite(t_ref) or alpha <= 0:
                        raise PreparationError("invalid reference alpha/time; no repair")
                    ref.update({"alpha_C": alpha, "t_ref": t_ref, "t_ref_hex": t_ref.hex(), "status": "reference_scale_frozen"})
                else:
                    ref["status"] = f"{name}_reference_scale_unavailable_under_frozen_protocol"
                references[name] = ref
                print(json.dumps({"event": "REFERENCE", "system": name, "status": ref["status"], "t_ref": ref["t_ref"]}), flush=True)
                del system
            rows = plan_rows(references, inputs["input_identity"])
            payload = {"references": references, "points": point_rows, "plan": rows, **stages}
            do_freeze("reference", payload, "REFERENCE_AND_COORDINATES_FROZEN")
        elif phase == "prediction":
            inputs, stages["input_commit"] = frozen(root, out, "inputs")
            ref, stages["reference_commit"] = frozen(root, out, "reference")
            plan = validate_plan(ref["plan"], ref["references"], inputs["input_identity"])
            eligible = [name for name in SYSTEMS if ref["references"][name]["qualified"]]
            loaded, observed, missing = {}, {}, []
            action_counts = {}
            rank = read(root/OLD/"rank_aware_M1_amendment.json")
            for name in eligible:
                with bounded_stage(ledgers[name], f"{name}_shared_preprocessing", 1800):
                    loaded[name] = load_system(out, inputs, name, ledgers[name], members, sequence, ("candidate", "m1"))
            def cheap_acquire(name):
                points = []
                with bounded_stage(ledgers[name], f"{name}_candidate_cheap", 1800):
                    for row in [r for r in plan if r["system"] == name]:
                        points.append({**loaded[name]["adapter"].cheap(loaded[name]["state"], row["time"], kind="candidate"),
                                       "candidate_id": row["candidate_id"], "ratio": row["ratio"]})
                return points, inputs["input_identity"][name]["K"]
            def spectral_acquire(name):
                q_payload, _ = frozen(root, out, "acquisition")
                q = q_payload[name]["q"]
                if not q:
                    frozen(root, out, "h1")
                if name in observed:
                    raise PreparationError("M1 already acquired")
                predictions, previous = [], None
                primary = primary_rank(inputs["input_identity"][name]["sector_dimension"])
                prefixes = [m for m in (1,2,4,8) if m <= primary]
                with bounded_stage(ledgers[name], f"{name}_M1", 1800):
                    for row in [r for r in plan if r["system"] == name]:
                        ledgers[name].charge("Arnoldi_chains", 3)
                        actions = CoordinateActions(loaded[name]["adapter"], row["time"], primary)
                        prediction, previous = analyze_coordinate(start=loaded[name]["state"], apply_u=actions.pf,
                            apply_h=actions.h, time_value=row["time"], prefix_dimensions=prefixes,
                            primary_dimension=primary, previous_vector=previous, numerical_rules=rank["numerical_rules"],
                            epsilon_hartree=EPSILON, beta=BETA, rotations_per_step=row["K"])
                        if actions.pf_count != actions.h_count or actions.pf_count != prediction["available_dimension"]:
                            raise PreparationError("M1 shared-prefix accounting mismatch")
                        p = finite_json(prediction, row["candidate_id"], missing)
                        predictions.append({"system": name, "candidate_id": row["candidate_id"], "time": row["time"],
                            "time_hex": row["time_hex"], "q": q, "e_use": p["e_use_hartree"], "abstain": p["abstained"],
                            "delta_M_hartree": p["signed_shift_estimate_hartree"], "width_M_hartree": p["empirical_width_hartree"],
                            "claim_class": "empirical_width_not_certificate", "core_prediction": p})
                        action_counts[row["candidate_id"]] = {"PF_actions": actions.pf_count, "H_matvecs": actions.h_count,
                            "path": "conditional_H1" if q else "always_M1_comparator_only"}
                observed[name] = predictions
                return predictions
            def barrier(marker, payload, digest):
                directory = "acquisition" if marker == "ACQUISITION_FROZEN" else "h1"
                saved = payload if directory == "acquisition" else {"H1": payload, "conditional_M1": observed,
                                                                      "acquisition_commit": stages["ACQUISITION_FROZEN"]}
                stages[marker] = do_freeze(directory, saved, marker)
                events.append({"event": marker, "canonical_payload_sha256": digest, "commit": stages[marker], "utc": utc()})
            replay = run_shared_schedule(eligible, cheap_acquire, spectral_acquire, barrier)
            for directory in ("acquisition", "h1"):
                frozen(root, out, directory)
            if canonical_hash(replay["cheap"]) != replay["acquisition_hash"] or canonical_hash(replay["H1"]) != replay["H1_hash"]:
                raise PreparationError("q/H1 changed after freeze")
            comparator = {n: {"selected": spectral_policy(p, replay["cheap"][n])[0],
                               "candidate_rows": spectral_policy(p, replay["cheap"][n])[1]}
                          for n,p in replay["always_M1_predictions"].items()}
            for name in eligible:
                c = ledgers[name].counts
                if any(c[k] != 3 for k in ("candidate_cheap_pf_actions", "candidate_h_exponential_actions", "Arnoldi_chains")):
                    raise PreparationError("candidate count mismatch")
            payload = {"eligible_systems": eligible, "plan": plan, "input_identity": inputs["input_identity"],
                "references": ref["references"], "cheap_B0_B1_B2_q": replay["cheap"],
                "H1": replay["H1"], "M1": replay["always_M1_predictions"], "always_M1_decisions": comparator,
                "schedule_resource": replay["resource"], "coordinate_actions": action_counts, "nonfinite_fields": missing,
                "truth_opened": False, "events": events, "stage_commits": stages}
            do_freeze("prediction", payload, "PREDICTION_FROZEN")
        elif phase == "truth":
            prediction, stages["prediction_commit"] = frozen(root, out, "prediction")
            inputs, stages["input_commit"] = frozen(root, out, "inputs")
            ref, stages["reference_commit"] = frozen(root, out, "reference")
            plan = validate_plan(prediction["plan"], ref["references"], inputs["input_identity"])
            method = read(root/METHOD)
            loaded, ground, exacts = {}, {"systems": {}, **stages}, {}
            for name in prediction["eligible_systems"]:
                ledger = ledgers[name]
                with bounded_stage(ledger, f"{name}_same_H_ground", 1800):
                    loaded[name] = load_system(out, inputs, name, ledger, members, sequence, (), allow_ground=True)
                    record, vector = ground_point(loaded[name]["adapter"].h.toarray(), inputs["input_identity"][name], method, ledger)
                    path = out/".runtime"/f"{name}_ground.npz"
                    np.savez_compressed(path, ground_vector=vector, energy=np.asarray(record["energy_hartree"]))
                    record["runtime_file"] = file_entry(out/".runtime", path)
                    ground["systems"][name], exacts[name] = record, vector
            stages["ground_commit"] = do_freeze("ground", ground, "GROUND_FROZEN")
            direct = helper(root)
            points = []
            for name in prediction["eligible_systems"]:
                ledger, previous = ledgers[name], None
                frozen(root, out, "prediction")
                frozen(root, out, "ground")
                ground_file = ground["systems"][name]["runtime_file"]
                verify_entries(out/".runtime", [ground_file])
                # The exact state used for truth must be the byte-frozen ground source.
                with np.load(out/".runtime"/ground_file["path"], allow_pickle=False) as archive:
                    if set(archive.files) != {"ground_vector", "energy"}:
                        raise PreparationError("ground member set mismatch")
                    exact = archive["ground_vector"].copy()
                    energy = float(archive["energy"])
                ledger.counts["truth_array_reads"] += 1
                if sha_array(exact) != ground["systems"][name]["ground_vector_sha256_numpy_v1"] or energy != ground["systems"][name]["energy_hartree"]:
                    raise PreparationError("ground freeze identity mismatch")
                with bounded_stage(ledger, f"{name}_direct_truth_and_gap", 1800):
                    for index, row in enumerate(r for r in plan if r["system"] == name):
                        before = time.perf_counter()
                        u = full_unitary(loaded[name]["adapter"], row["time"], ledger)
                        ledger.timings["truth_full_PF_construction"] += time.perf_counter()-before
                        ledger.charge("direct_Schur_solves", 3)
                        before = time.perf_counter()
                        point, previous = direct(u, exact, energy, row["time"], row["K"], EPSILON, previous, 1e-8)
                        ledger.timings["truth_Schur_branch_gap"] += time.perf_counter()-before
                        ledger.charge("direct_truth_coordinates", 3)
                        ledger.charge("target_phase_gaps", 3)
                        point = serial_truth(point)
                        point.update({"system": name, "candidate_id": row["candidate_id"], "time_hex": row["time_hex"],
                            "H_sha256_numpy_v1": inputs["input_identity"][name]["H_sha256_numpy_v1"],
                            "ground_vector_sha256_numpy_v1": ground["systems"][name]["ground_vector_sha256_numpy_v1"],
                            "phase_unwrap_basis": "principal_ground_relative", "computed": True, "reused": False,
                            "initial_or_continuation": "initial_exact_ground" if index == 0 else "previous_selected_vector"})
                        point["quality"] = truth_quality(point, method)
                        points.append(point)
                        write_json(out/"truth_checkpoints"/f"{row['candidate_id']}.json", point)
                        print(json.dumps({"event": "DIRECT_POINT", "candidate": row["candidate_id"], "quality": point["quality"]["status"]}), flush=True)
            truth = {"points": points, "coordinate_count": len(plan), "nearest_or_interpolation": 0, **stages}
            stages["truth_commit"] = do_freeze("truth", truth, "TRUTH_FROZEN")
            prediction, _ = frozen(root, out, "prediction")
            ground, _ = frozen(root, out, "ground")
            truth, _ = frozen(root, out, "truth")
            scored = immutable_score(prediction, truth, ground)
            scored["stage_commits"] = stages
            write_json(out/"scoring.json", scored)
            write_csv(out/"coordinate_scoring.csv", scored["coordinate_scores"])
            write_csv(out/"decision_scoring.csv", scored["decision_scores"])
            write_json(out/"COMPLETE.json", {"status": STATUS, "utc": utc(), **stages,
                "systems_requested": 3, "systems_reference_eligible": len(prediction["eligible_systems"]),
                "coordinates": len(plan), "next_stage_authorized": False, "H8_science_authorized": False,
                "push_authorized": False, "old_formal_results_unchanged": True})
            do_freeze("scored", scored, "IMMUTABLE_SCORING_COMPLETE")
        if boundary.denials or "cupy" in sys.modules:
            raise PreparationError("access/CPU gate failed")
        for ledger in ledgers.values():
            ledger.check_memory()
            if phase != "truth" and any(ledger.counts[k] for k in ("full_H_ground_solves", "full_pf_unitary_builds", "direct_truth_coordinates", "target_phase_gaps", "truth_array_reads")):
                raise PreparationError("truth barrier violated")
        write_json(out/f"{phase}_execution_audit.json", {"phase": phase, "start_utc": start_utc, "finish_utc": utc(),
            "environment": env, "source": source_gate(root), "resources": resource(), "access": access(),
            "status": "phase_complete", "no_retry": True})
    except BaseException as error:
        write_json(out/f"{phase}_FAILURE.json", {"utc": utc(), "error_type": type(error).__name__,
            "message": str(error), "resources": resource(), "access": access(), "no_retry_or_rescue_authorized": True})
        raise
    finally:
        boundary.enabled = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal-source", action="store_true")
    parser.add_argument("--phase", choices=("inputs", "reference", "prediction", "truth"))
    args = parser.parse_args()
    if bool(args.seal_source) == bool(args.phase):
        parser.error("choose exactly one mode")
    root = Path.cwd().resolve()
    if args.seal_source:
        seal(root)
    else:
        execute(root, args.phase)


if __name__ == "__main__":
    main()
