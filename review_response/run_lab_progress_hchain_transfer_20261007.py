"""Bounded four-PF allocation transfer: frozen CISD prediction then direct truth.

Reuse sanitized molecular inputs, component exponentials, rolling leading fits,
and scaled two-term fits. No new molecular generation or PF search. Matrices and
vectors are kept only in /tmp; published outputs contain scalars and metadata.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time

import numpy as np
from scipy.linalg import schur
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from review_response.hchain_input_reference_preparation import sha_array
from review_response.pf_first_study_phase_common import (
    evaluate_fit, leading_fit, model_cost, scaled_power_fit, state_diagnostics,
)
from trotterlib.component_sector_pf import component_exponential, diagonalize_components
from trotterlib.config import DECOMPO_NUM
from trotterlib.pf_decomposition import iter_s2_sequence_steps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/lab_progress_hchain_transfer_20261007"
PRIVATE = Path("/tmp/lab_progress_hchain_transfer_20261007")
SYSTEMS = ("H2", "H3", "H5", "H6")
PREP = "artifacts/hchain_input_reference_preparation_20261004_06922cb"
ODD = "artifacts/hchain_h3_h5_h7_extension_20261004"
SOURCE_ROOT = ROOT.parent
EPSILON = 0.00015936001019904
BETA = 1.2
MARGIN = 1.01


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_csv(path, rows):
    if not rows:
        Path(path).write_text("system,status\n")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict))
                             else value for key, value in row.items()})


def source_entry(path, snapshot):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path),
            "origin_result_commit": git("log", "-1", "--format=%H", snapshot, "--", str(path.relative_to(ROOT))),
            "verified_snapshot_commit": snapshot}


def freeze():
    if OUT.exists() or PRIVATE.exists():
        raise FileExistsError("one-shot output exists; no implicit rerun")
    OUT.mkdir(parents=True)
    PRIVATE.mkdir()
    snapshot = git("rev-parse", "HEAD")
    inherited = json.loads((ROOT / "PF_first_study_protocol_20260925.json").read_text())
    even_identity = json.loads((ROOT / PREP / "input_identity.json").read_text())
    even_files = json.loads((ROOT / PREP / "runtime_manifest.json").read_text())["files"]
    odd_inputs = json.loads((ROOT / ODD / "inputs/payload.json").read_text())
    odd_specs = json.loads((ROOT / "docs/second_study_v2/hchain_odd_extension_20261004/protocol.json").read_text())["systems"]
    specifications = []
    for name in SYSTEMS:
        even = name in ("H2", "H6")
        directory = SOURCE_ROOT / ("pf-second-study-v2-hchain-input-reference-preparation-20261004" if even
                                   else "pf-second-study-v2-hchain-h3-h5-h7-extension-20261004")
        runtime = directory / (PREP if even else ODD) / ".runtime"
        identity = even_identity[name] if even else odd_inputs["input_identity"][name]
        filename = f"{name}_predictor_input.npz" if even else f"{name}_input.npz"
        expected = next(row for row in (even_files if even else odd_inputs["runtime_files"])
                        if row["path"] == filename)
        if sha(runtime / filename) != expected["sha256"]:
            raise ValueError(f"input hash mismatch: {name}")
        shutil.copyfile(runtime / filename, PRIVATE / f"{name}_input.npz")
        if name == "H2":
            # Same affine merged-circuit counts used in the historical H2 analyses.
            stage_cost = {key: int(DECOMPO_NUM[name]["2nd"] + (len(value["s2_sequence"]) - 1)
                                 * (DECOMPO_NUM[name]["4th"] - DECOMPO_NUM[name]["2nd"]) // 2)
                          for key, value in inherited["formulae"].items()}
            counts = None
        else:
            operator_name = "h6_group_operators.json" if even else f"{name}_group_operators.json"
            operators = json.loads((runtime / operator_name).read_text())
            counts = operators.get("Pauli_counts", operators.get("counts"))
            if counts is None:
                raise ValueError("Pauli group counts unavailable")
            stage_cost = {key: sum(counts[index] for index, _ in
                                  iter_s2_sequence_steps(len(counts), value["s2_sequence"]))
                          for key, value in inherited["formulae"].items()}
        if stage_cost["current_m3"] != identity["K"]:
            raise ValueError("K reproduction failed")
        if even:
            atoms = int(name[1:])
            spec = {"system": name, "atoms": atoms, "charge": 0, "multiplicity": 1,
                    "n_alpha": atoms // 2, "n_beta": atoms // 2,
                    "sector_kind": "fixed_interleaved_spin_populations" if name == "H2" else "fixed_half_populations"}
        else:
            spec = next(row for row in odd_specs if row["system"] == name).copy()
        specifications.append({**spec, "geometry_rule": "linear z_i=i-(n-1)/2 Angstrom",
                               "basis": "sto-3g", "input_identity": identity,
                               "input_file_sha256": expected["sha256"], "input_file_bytes": expected["bytes"],
                               "runtime_source": str((runtime / filename).relative_to(ROOT.parent.parent)),
                               "Pauli_group_counts": counts, "K_by_formula": stage_cost})
    registry_paths = ["PF_first_study_protocol_20260925.json", f"{PREP}/input_identity.json",
                      f"{PREP}/runtime_manifest.json", f"{ODD}/inputs/payload.json",
                      "docs/second_study_v2/hchain_odd_extension_20261004/protocol.json",
                      "review_response/pf_first_study_phase_common.py", "review_response/pf_first_study_experiment_a.py",
                      "review_response/run_hchain_truth_scoring.py", "src/trotterlib/component_sector_pf.py",
                      "src/trotterlib/sector_pf.py", "src/trotterlib/pf_decomposition.py", "src/trotterlib/config.py"]
    protocol = {
        "schema": "lab_progress_hchain_transfer_v1", "frozen_utc": utc(), "verified_snapshot_commit": snapshot,
        "authorization": "2026-10-07 user permits practical new validation conditions and parallel execution",
        "systems": specifications, "formulae": inherited["formulae"],
        "formula_ids": inherited["scope"]["included_formula_ids"],
        "leading_fit": inherited["experiment_B_h4"]["decision_track"]["short_time_leading_fit"],
        "training_ratios": [0.1, 0.2, 0.3, 0.4, 0.5],
        "candidate_grid": {"kind": "geomspace", "lower": 0.25, "upper": 2.0, "count": 401},
        "constants": {"epsilon_E": EPSILON, "beta": BETA, "budget_multiplier": MARGIN},
        "predictor": "CISD only; no full-H ground solve before all predictions are frozen",
        "prediction_proxy": "Im <psi|exp(-iHt)U_P(t)|psi> / t; expm_multiply on same Hamiltonian",
        "PF_construction": "existing sparse component exponential sequential merged PF, as run_hchain_truth_scoring.full_unitary",
        "training_signal_gate": "all five marginal/resolved; at least three resolved, inherited noise formula",
        "truth_branch": {"method": "complex Schur; maximum previous-vector overlap; unwrap using previous energy",
                          "ground_overlap_minimum": 0.9, "previous_overlap_minimum": 0.9,
                          "eigenpair_residual_maximum": 1e-10, "unitarity_frobenius_maximum": 1e-10,
                          "degeneracy_policy": "unreliable individual-vector branches excluded, no post-truth rescue"},
        "state_contrast": "CISD, mean-field determinant, rank<=3 CISDT and exact ground on identical CISD five fit times and 401 candidate times; exact is oracle only",
        "CISDT_state_rule": "lowest projected-H eigenstate on excitation rank<=3 relative to existing mean-field determinant; also reproduce rank<=2 saved CISD with fidelity>=1-1e-10; no rank search",
        "maximum_scaled_design_condition_number": inherited["experiment_B_h4"]["fixed_time_mechanism_track"]["maximum_scaled_design_condition_number"],
        "long_time_decomposition": "at each formula CISD/RHF/CISDT/exact-selected point and direct grid minimum: f_psi-g_psi, g_psi-g0, g0-delta",
        "stop": {"system_count": 4, "PFs_per_system_maximum": 4, "leading_times_per_PF": 34,
                 "fit_times_per_PF": 5, "direct_candidate_times_per_eligible_PF": 401,
                 "ground_solves_per_system": 1, "workers_maximum": 2, "BLAS_threads": 1,
                 "wall_seconds_maximum": 5400, "no_failed_fit_grid_or_rule_rescue": True},
        "source_registry": [source_entry(ROOT / name, snapshot) for name in registry_paths],
        "runner_sha256": sha(__file__), "private_matrix_vector_directory": str(PRIVATE),
        "public_matrix_vector_count": 0, "historical_science_artifacts_modified": False,
    }
    write_json(OUT / "protocol.json", protocol)
    write_json(OUT / "PROTOCOL_FROZEN.json", {"utc": utc(), "protocol_sha256": sha(OUT / "protocol.json"),
                                             "runner_sha256": sha(__file__), "truth_opened": False})
    return protocol


def verify_protocol():
    marker = json.loads((OUT / "PROTOCOL_FROZEN.json").read_text())
    if marker["protocol_sha256"] != sha(OUT / "protocol.json") or marker["runner_sha256"] != sha(__file__):
        raise ValueError("protocol or runner changed after freeze")
    return json.loads((OUT / "protocol.json").read_text())


class MolecularActions:
    def __init__(self, name, protocol):
        self.spec = next(row for row in protocol["systems"] if row["system"] == name)
        path = PRIVATE / f"{name}_input.npz"
        if sha(path) != self.spec["input_file_sha256"]:
            raise ValueError("private input byte mismatch")
        with np.load(path, allow_pickle=False) as data:
            self.h = np.asarray(data["hamiltonian"], dtype=complex)
            self.cisd = np.asarray(data["cisd"], dtype=complex)
            self.indices = np.asarray(data["sector_indices"])
            self.groups = [np.asarray(data[key], dtype=complex) for key in sorted(data.files) if key.startswith("group_")]
        identity = self.spec["input_identity"]
        if sha_array(self.h) != identity["H_sha256_numpy_v1"] or sha_array(self.cisd) != identity["CISD_sha256_numpy_v1"]:
            raise ValueError("H or CISD array mismatch")
        if [sha_array(group) for group in self.groups] != identity["group_sha256_numpy_v1"]:
            raise ValueError("group array mismatch")
        self.spectra = [diagonalize_components(csr_matrix(group)) for group in self.groups]
        self.h_sparse = csr_matrix(self.h)
        self.hnorm = float(np.linalg.norm(self.h, 2))
        self.full_builds = 0
        self.exponentials = 0
        self.started = time.perf_counter()

    def unitary(self, sequence, t):
        self.full_builds += 1
        unitary = np.eye(len(self.cisd), dtype=complex)
        gates = {}
        for index, weight in iter_s2_sequence_steps(len(self.groups), sequence):
            key = (index, weight)
            if key not in gates:
                gates[key] = component_exponential(self.spectra[index], t * weight)
            unitary = gates[key] @ unitary
        return unitary

    def proxies(self, unitary, states, t):
        self.exponentials += len(states)
        block = np.column_stack(states)
        evolved = expm_multiply(1j * t * self.h_sparse, block)
        product = unitary @ block
        return [float(np.vdot(evolved[:, j], product[:, j]).imag / t) for j in range(len(states))]

    def point(self, sequence, t):
        unitary = self.unitary(sequence, t)
        repeated = self.unitary(sequence, t)
        signal = self.proxies(unitary, [self.cisd], t)[0]
        repeat = self.proxies(repeated, [self.cisd], t)[0]
        unitarity = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0])))
        if unitarity > 1e-10:
            raise ValueError("unitarity gate failed")
        noise = max(unitarity / t, abs(signal - repeat),
                    50 * np.finfo(float).eps * max(self.hnorm, 1 / t))
        rho = abs(signal) / max(noise, 1e-300)
        return {"time": float(t), "proxy_imag_hartree": signal,
                "unitarity_frobenius": unitarity, "proxy_noise_hartree": noise,
                "rho": rho, "quality": "resolved" if rho >= 100 else "marginal" if rho >= 10 else "unresolved"}

    def resource(self):
        return {"full_PF_builds": self.full_builds, "H_exponential_vector_actions": self.exponentials,
                "elapsed_seconds": time.perf_counter() - self.started,
                "peak_RSS_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "BLAS_threads": 1}


def predict_formula(task):
    name, formula = task
    protocol = verify_protocol()
    action = MolecularActions(name, protocol)
    sequence = protocol["formulae"][formula]["s2_sequence"]
    spec = protocol["leading_fit"]
    leading_times = np.geomspace(spec["minimum_hartree_inverse"], spec["maximum_hartree_inverse"], spec["count"])
    points = [action.point(sequence, float(t)) for t in leading_times]
    leading = leading_fit(leading_times, [row["proxy_imag_hartree"] for row in points], spec, 4)
    result = {"system": name, "formula": formula, "leading_fit": leading,
              "leading_points": points, "eligible": False, "status": "short_time_leading_fit_failed",
              "K": action.spec["K_by_formula"][formula]}
    if leading["qualified"]:
        alpha = float(leading["selected_window"]["fixed_order_alpha"])
        tref = float((EPSILON / (5 * abs(alpha))) ** 0.25)
        training = [action.point(sequence, float(r * tref)) for r in protocol["training_ratios"]]
        model = scaled_power_fit([row["time"] for row in training], [row["proxy_imag_hartree"] for row in training], (4, 6))
        grid = np.geomspace(0.25, 2, 401) * tref
        candidates = [{"index": index, "time": float(t), "shift": evaluate_fit(model, float(t)),
                       "cost": model_cost(EPSILON, BETA, result["K"], float(t), evaluate_fit(model, float(t)))}
                      for index, t in enumerate(grid)]
        quality = all(row["quality"] in ("marginal", "resolved") for row in training) and sum(row["quality"] == "resolved" for row in training) >= 3
        feasible = [row for row in candidates if row["cost"] is not None]
        eligible = quality and model["scaled_design_condition_number"] <= protocol["maximum_scaled_design_condition_number"] and bool(feasible)
        result.update({"alpha": alpha, "t_proxy": tref, "training_points": training,
                       "model": model, "grid": [float(t) for t in grid], "model_candidates": candidates,
                       "quality_gate": quality, "eligible": eligible,
                       "status": "eligible" if eligible else "training_signal_or_design_gate_failed"})
        if eligible:
            selected = min(feasible, key=lambda row: row["cost"])
            result["selection"] = {**selected, "budget": MARGIN * selected["cost"]}
    result["resource"] = action.resource()
    write_json(OUT / name / f"prediction_{formula}.json", result)
    print(json.dumps({"event": "PREDICTION", "system": name, "formula": formula,
                      "status": result["status"], "seconds": result["resource"]["elapsed_seconds"]}), flush=True)
    return result


def direct_point(unitary, t, exact, energy, previous, previous_energy):
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ previous) ** 2
    index = int(np.argmax(overlaps))
    vector = vectors[:, index]
    phase = float(np.angle(eigenvalues[index]))
    unwrap = int(np.rint((previous_energy * t - phase) / (2 * np.pi)))
    effective = (phase + 2 * np.pi * unwrap) / t
    residual = float(np.linalg.norm(unitary @ vector - eigenvalues[index] * vector))
    ground_overlap = float(abs(np.vdot(exact, vector)) ** 2)
    previous_overlap = float(overlaps[index])
    unitarity = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(len(vector))))
    reliable = ground_overlap >= .9 and previous_overlap >= .9 and residual <= 1e-10 and unitarity <= 1e-10
    return {"time": float(t), "direct_shift": float(effective - energy),
            "ground_overlap": ground_overlap, "previous_overlap": previous_overlap,
            "eigenpair_residual": residual, "unitarity_frobenius": unitarity,
            "unwrap_integer": unwrap, "branch_reliable": bool(reliable)}, vector, effective


def contrast_choice(model, prediction):
    feasible = []
    for index, t in enumerate(prediction["grid"]):
        shift = evaluate_fit(model, t)
        cost = model_cost(EPSILON, BETA, prediction["K"], t, shift)
        if cost is not None:
            feasible.append({"index": index, "time": t, "shift": shift, "cost": cost, "budget": MARGIN * cost})
    return min(feasible, key=lambda row: row["cost"]) if feasible else None


def projected_rank_state(action, rank):
    reference = int(action.spec["input_identity"]["RHF_reference_integer"])
    positions = [j for j, full_index in enumerate(action.indices)
                 if (int(full_index) ^ reference).bit_count() // 2 <= rank]
    values, vectors = np.linalg.eigh(action.h[np.ix_(positions, positions)])
    state = np.zeros_like(action.cisd)
    state[positions] = vectors[:, 0]
    state /= np.linalg.norm(state)
    return state, {"excitation_rank_maximum": rank, "subspace_dimension": len(positions),
                   "energy_hartree": float(values[0]), "full_sector_dimension": len(state)}


def truth_formula(task):
    name, formula = task
    protocol = verify_protocol()
    seal = json.loads((OUT / "PREDICTIONS_FROZEN.json").read_text())
    for relative, expected in seal["prediction_sha256"].items():
        if sha(OUT / relative) != expected:
            raise ValueError("prediction changed after truth barrier")
    prediction = json.loads((OUT / name / f"prediction_{formula}.json").read_text())
    if not prediction["eligible"]:
        return None
    action = MolecularActions(name, protocol)
    with np.load(PRIVATE / f"{name}_ground.npz", allow_pickle=False) as data:
        exact, energy = data["state"], float(data["energy"])
    rhf = np.zeros_like(action.cisd)
    position = int(np.flatnonzero(action.indices == action.spec["input_identity"]["RHF_reference_integer"])[0])
    rhf[position] = 1
    rank2, rank2_info = projected_rank_state(action, 2)
    fidelity = float(abs(np.vdot(rank2, action.cisd)) ** 2)
    if fidelity < 1 - 1e-10:
        raise ValueError("rank<=2 CISD reproduction failed")
    cisdt, cisdt_info = projected_rank_state(action, 3)
    states = {"rhf": rhf, "cisd": action.cisd, "cisdt": cisdt, "exact": exact}
    times = [row["time"] for row in prediction["training_points"]]
    training_values = {key: [] for key in states}
    sequence = protocol["formulae"][formula]["s2_sequence"]
    for t in times:
        unitary = action.unitary(sequence, t)
        values = action.proxies(unitary, list(states.values()), t)
        for key, value in zip(states, values):
            training_values[key].append(value)
    models = {key: scaled_power_fit(times, values, (4, 6)) for key, values in training_values.items()}
    if np.max(np.abs(np.asarray(models["cisd"]["coefficients"]) - prediction["model"]["coefficients"])) > 1e-12:
        raise ValueError("CISD frozen model reproduction failed")
    rows = []
    previous, previous_energy = exact, energy
    started = time.perf_counter()
    for index, t in enumerate(prediction["grid"]):
        unitary = action.unitary(sequence, t)
        direct, previous, previous_energy = direct_point(unitary, t, exact, energy, previous, previous_energy)
        cost = model_cost(EPSILON, BETA, prediction["K"], t, direct["direct_shift"])
        direct.update({"system": name, "formula": formula, "index": index, "direct_cost": cost})
        rows.append(direct)
        if index % 100 == 0:
            print(json.dumps({"event": "TRUTH_PROGRESS", "system": name, "formula": formula,
                              "completed": index + 1, "seconds": time.perf_counter() - started}), flush=True)
    feasible = [row for row in rows if row["branch_reliable"] and row["direct_cost"] is not None]
    minimum = min(feasible, key=lambda row: row["direct_cost"], default=None)
    focus = {prediction["selection"]["index"]: "CISD_selected"}
    if minimum is not None:
        focus[minimum["index"]] = focus.get(minimum["index"], "") + "+direct_grid_min"
    for state, model in models.items():
        choice = prediction["selection"] if state == "cisd" else contrast_choice(model, prediction)
        if choice is not None:
            index = choice["index"]
            focus[index] = focus.get(index, "") + f"+{state}_selected"
    decomposition = []
    for index, role in focus.items():
        direct = rows[index]
        t = direct["time"]
        unitary = action.unitary(sequence, t)
        values = dict(zip(states, action.proxies(unitary, list(states.values()), t)))
        for state in states:
            fitted = evaluate_fit(models[state], t)
            terms = [fitted - values[state], values[state] - values["exact"], values["exact"] - direct["direct_shift"]]
            closure = fitted - direct["direct_shift"] - sum(terms)
            if abs(closure) > max(1e-12, 1e-8 * EPSILON):
                raise ValueError("three-component closure failed")
            decomposition.append({"system": name, "formula": formula, "point_role": role,
                                  "index": index, "time": t, "state": state, "model_shift": fitted,
                                  "proxy": values[state], "exact_proxy": values["exact"],
                                  "direct_shift": direct["direct_shift"], "fit_term": terms[0],
                                  "state_term": terms[1], "proxy_term": terms[2], "closure": closure,
                                  "dominant_absolute_term": ("fit", "state", "proxy")[int(np.argmax(np.abs(terms)))],
                                  "branch_reliable": direct["branch_reliable"]})
    contrasts = []
    for state, model in models.items():
        selection = prediction["selection"] if state == "cisd" else contrast_choice(model, prediction)
        if selection is None:
            continue
        direct = rows[selection["index"]]
        total = abs(direct["direct_shift"]) + BETA * prediction["K"] / (selection["time"] * selection["budget"])
        contrasts.append({"system": name, "formula": formula, "state": state,
                          "model": model, "selection": selection, "direct_shift": direct["direct_shift"],
                          "direct_cost": direct["direct_cost"], "total_error": total,
                          "precision_met": bool(total <= EPSILON), "branch_reliable": direct["branch_reliable"],
                          "oracle_only": state == "exact"})
    result = {"system": name, "formula": formula, "candidate_count": len(rows),
              "reliable_count": sum(row["branch_reliable"] for row in rows), "direct_minimum": minimum,
              "contrasts": contrasts, "decomposition": decomposition,
              "projected_state_preparation": {"rank2": rank2_info, "saved_CISD_reproduction_fidelity": fidelity,
                                               "cisdt": cisdt_info},
              "state_diagnostics": {key: state_diagnostics(action.h, state, exact, energy) for key, state in states.items()},
              "resource": action.resource()}
    write_csv(OUT / name / f"direct_grid_{formula}.csv", rows)
    write_json(OUT / name / f"truth_{formula}.json", result)
    print(json.dumps({"event": "TRUTH_COMPLETE", "system": name, "formula": formula,
                      "seconds": result["resource"]["elapsed_seconds"]}), flush=True)
    return result


def summarize(protocol, predictions, truths):
    summaries, contrast_rows, decomposition_rows = [], [], []
    for name in SYSTEMS:
        valid = [row for row in predictions if row["system"] == name and row["eligible"]]
        truth = [row for row in truths if row is not None and row["system"] == name]
        if not valid:
            summaries.append({"system": name, "status": "abstained_no_qualified_PF", "eligible_PF_count": 0})
            continue
        selected = min(valid, key=lambda row: row["selection"]["cost"])
        selected_truth = next(row for row in truth if row["formula"] == selected["formula"])
        direct = next(row for row in selected_truth["contrasts"] if row["state"] == "cisd")
        minima = [row["direct_minimum"] for row in truth if row["direct_minimum"] is not None]
        minimum = min(minima, key=lambda row: row["direct_cost"], default=None)
        budget = selected["selection"]["budget"]
        summaries.append({"system": name, "status": "scored", "eligible_PF_count": len(valid),
                          "selected_formula": selected["formula"], "selected_time": selected["selection"]["time"],
                          "budget": budget, "direct_cost_selected": direct["direct_cost"],
                          "total_error": direct["total_error"], "precision_met": direct["precision_met"],
                          "branch_reliable": direct["branch_reliable"], "direct_grid_minimum": minimum,
                          "budget_over_selected_cost": budget / direct["direct_cost"] if direct["direct_cost"] else None,
                          "budget_over_grid_minimum": budget / minimum["direct_cost"] if minimum else None,
                          "CISD_ground_overlap": selected_truth["state_diagnostics"]["cisd"]["exact_overlap_probability"]})
        for state in ("rhf", "cisd", "cisdt", "exact"):
            candidates = [c for row in truth for c in row["contrasts"] if c["state"] == state]
            if candidates:
                choice = min(candidates, key=lambda row: row["selection"]["cost"])
                selected_formula = next(row["formula"] for row in truth if choice in row["contrasts"])
                contrast_rows.append({"system": name, "state": state, "formula": selected_formula,
                                      "time": choice["selection"]["time"], "budget": choice["selection"]["budget"],
                                      "total_error": choice["total_error"], "precision_met": choice["precision_met"],
                                      "branch_reliable": choice["branch_reliable"],
                                      "budget_over_grid_minimum": choice["selection"]["budget"] / minimum["direct_cost"] if minimum else None,
                                      "oracle_only": state == "exact"})
        decomposition_rows.extend(row for formula in truth for row in formula["decomposition"])
    write_csv(OUT / "allocation_summary.csv", summaries)
    write_csv(OUT / "matched_state_allocation.csv", contrast_rows)
    write_csv(OUT / "long_time_error_decomposition.csv", decomposition_rows)
    write_json(OUT / "summary.json", {"schema": "lab_progress_hchain_transfer_results_v1",
                                      "systems": summaries, "matched_state_allocations": contrast_rows,
                                      "protocol_sha256": sha(OUT / "protocol.json"),
                                      "prediction_freeze_sha256": sha(OUT / "PREDICTIONS_FROZEN.json"),
                                      "completed_utc": utc(), "public_matrix_vector_count": 0,
                                      "same_401_grid_and_five_fit_rule_as_H4": True,
                                      "unqualified_PFs_not_rescued": True})
    write_json(OUT / "manifest.json", {"manifest_self_excluded": True,
                                       "files": [{"path": str(path.relative_to(OUT)), "sha256": sha(path),
                                                  "bytes": path.stat().st_size}
                                                 for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "manifest.json"]})


def run():
    started = time.perf_counter()
    protocol = freeze()
    tasks = [(name, formula) for name in SYSTEMS for formula in protocol["formula_ids"]]
    with ProcessPoolExecutor(max_workers=2) as pool:
        predictions = [future.result() for future in as_completed([pool.submit(predict_formula, task) for task in tasks])]
    files = {str(path.relative_to(OUT)): sha(path) for path in sorted(OUT.glob("*/prediction_*.json"))}
    write_json(OUT / "PREDICTIONS_FROZEN.json", {"utc": utc(), "prediction_sha256": files,
                                               "full_H_ground_solves_before_freeze": 0, "truth_opened": False,
                                               "protocol_sha256": sha(OUT / "protocol.json")})
    print(json.dumps({"event": "ALL_PREDICTIONS_FROZEN", "seconds": time.perf_counter() - started}), flush=True)
    ground_records = []
    for name in SYSTEMS:
        action = MolecularActions(name, protocol)
        energy, vectors = np.linalg.eigh(action.h)
        ground = vectors[:, 0]
        residual = float(np.linalg.norm(action.h @ ground - energy[0] * ground))
        if residual > 1e-10:
            raise ValueError("full H ground residual gate failed")
        np.savez_compressed(PRIVATE / f"{name}_ground.npz", state=ground, energy=np.asarray(energy[0]))
        ground_records.append({"system": name, "energy": float(energy[0]), "residual": residual,
                               "dimension": len(ground), "ground_solves": 1,
                               "historical_Z2_200_H6_sector_used": False})
    write_json(OUT / "ground_scalar_diagnostics.json", ground_records)
    with ProcessPoolExecutor(max_workers=2) as pool:
        truths = [future.result() for future in as_completed([pool.submit(truth_formula, task) for task in tasks])]
    if time.perf_counter() - started > protocol["stop"]["wall_seconds_maximum"]:
        raise RuntimeError("wall ceiling exceeded")
    write_json(OUT / "execution.json", {"started_seconds_reference": started,
                                        "elapsed_seconds": time.perf_counter() - started,
                                        "Python": os.sys.version, "packages": {name: importlib.metadata.version(name)
                                                                               for name in ("numpy", "scipy", "pyscf", "openfermion")},
                                        "threads": {key: os.environ.get(key) for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
                                        "workers": 2, "inherited_artifacts_modified": False})
    summarize(protocol, predictions, truths)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
