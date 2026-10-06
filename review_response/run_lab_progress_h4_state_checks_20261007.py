"""Frozen H4 state controls and long-time error decomposition; scalar outputs only."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np

from review_response._pf_first_study_experiment_a_support import (
    atomic_json, propagator_minus, sha256_array, sha256_file, write_csv,
)
from review_response.pf_first_study_experiment_a import track_direct_branch
from review_response.pf_first_study_phase_common import (
    build_unitary, evaluate_fit, load_h4_source, model_cost,
    proxy_noise_hartree, quality_class, scaled_power_fit, state_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/lab_progress_h4_state_checks_20261007"
BASE_PROTOCOL = "PF_first_study_protocol_20260925.json"
OLD_A = "artifacts/pf_first_study_phase_a_20260925_6265243"
OLD_B = "artifacts/pf_first_study_phase_b_20260925_5a2f0a2"
STATE_IDS = ("rhf", "cis", "cisd", "cisdt", "exact")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def freeze(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if (output / "protocol.json").exists():
        raise RuntimeError("protocol already frozen; do not overwrite")
    base = json.loads((ROOT / BASE_PROTOCOL).read_text())
    old = json.loads((ROOT / OLD_A / "predictions.json").read_text())
    formulas = []
    for row in old["experiment_B"]["formula_predictions"]:
        fid = row["formula_id"]
        scale = row["proxy_t_ana_hartree_inverse"]
        formulas.append({
            "formula_id": fid,
            "s2_sequence": base["formulae"][fid]["s2_sequence"],
            "step_cost": row["step_cost_pauli_rotations"],
            "training_times": [float(r * scale) for r in (0.1, 0.2, 0.3, 0.4, 0.5)],
            "candidate_times": row["selection_grid_hartree_inverse"],
            "original_model": row["primary_model"],
            "original_selected_time": row["selected_time_hartree_inverse"],
        })
    snapshot = git("rev-parse", "HEAD")
    sources = [BASE_PROTOCOL, OLD_A + "/predictions.json",
               OLD_B + "/observables.csv", OLD_B + "/branch_audit.csv"]
    sources += [base["source_identity"][key]["path"]
                for key in ("f01_bundle", "h01_state_bundle")]
    registry = []
    for rel in sources:
        origin = git("log", "-1", "--format=%H", snapshot, "--", rel)
        actual = (ROOT / rel).read_bytes()
        if subprocess.check_output(["git", "show", f"{snapshot}:{rel}"], cwd=ROOT) != actual:
            raise ValueError(f"source differs from snapshot: {rel}")
        registry.append({"path": rel, "origin_result_commit": origin,
                         "verified_snapshot_commit": snapshot, "sha256": sha256_file(ROOT / rel)})
    protocol = {
        "protocol_id": "lab_progress_h4_state_bridge_and_matched_state_controls_20261007",
        "frozen_before_new_numerical_evaluation": True,
        "user_authorization": "2026-10-07: conditions may be chosen by Codex; run additional checks in parallel",
        "study_type": "post-hoc diagnostic extension, not an independent holdout or replacement formal result",
        "input_snapshot_commit": snapshot, "source_registry": registry,
        "runner_sha256": sha256_file(Path(__file__)),
        "system": "archived H4 linear chain, 1.0 Angstrom, STO-3G, 4 electrons, Nalpha=Nbeta=2, dimension 36",
        "state_ids": list(STATE_IDS),
        "state_construction": {
            "rhf_cisd_exact": "unaltered archived normalized states; global phase has no effect on proxy",
            "cis": "lowest eigenvector of archived H restricted to determinants with excitation rank <=1 relative to archived RHF determinant (9 dimensions)",
            "cisdt": "lowest eigenvector of archived H restricted to determinants with excitation rank <=3 relative to archived RHF determinant (35 dimensions); no mixing with the exact state",
            "rank_definition": "popcount(full_Fock_index XOR RHF_full_Fock_index)/2",
            "cisd_consistency_control": "rank<=2 positions must equal archived CISD subspace positions; projected ground state must reproduce archived CISD up to phase",
        },
        "formulas": formulas,
        "constants": {"epsilon_E_hartree": base["constants"]["target_error_hartree"],
                      "beta": base["constants"]["qpe_beta"], "budget_multiplier": 1.01},
        "model": {"powers": [4, 6], "fit_intercept": False,
                  "fit": "unweighted least squares with column 2-norm scaling, reused helper",
                  "candidate_rule": "minimum predicted feasible cost over original four PF-specific 401 absolute times; all states use identical training and candidate times",
                  "eligibility": "original signal quality: all five fit signals marginal/resolved, at least three resolved; design condition <=1e8",
                  "state_dependent_leading_time_refit": False},
        "bridge": {"formula_id": "m5_best", "times": [2.1466061014866242, 3.5175172132783867],
                   "model": "original frozen CISD model, unchanged", "states": ["cisd", "exact"]},
        "short_time_reproduction": {"formula_id": "m5_best", "time": 0.4, "states": ["cisd", "exact"]},
        "truth_access": {
            "prediction_phase": "no PF eigenvalue truth or saved direct costs; archived exact state used only as explicit oracle state comparator and fixed quality audit, never to select approximation rank",
            "scoring_phase": "after predictions.json is frozen, compute continuous PF branch on all original four 401-point grids; saved direct rows used only for reproduction and comparison",
            "branch_policy": "reuse track_direct_branch from zero independently for each PF, positive increasing times, degeneracy gap 1e-8; reliable overlap >=0.9 and eigenpair residual <=1e-10",
            "prior_information": "original selections and formal results are already known; this is a diagnostic control, not prospective independent validation",
        },
        "maximum_new_pf_truth_points": 1604,
        "proxy_grid_evaluations": 8020,
        "additional_two_point_bridge_unitaries": 0,
        "stop": "five state controls, 20 models, four original grids, two long bridge points and one short reproduction point; no coefficient search, threshold adjustment, candidate expansion, or rescue after scoring",
        "publication": "scalar CSV/JSON, code, metadata and report only; no new matrices, unitaries or state vectors are written into the artifact",
    }
    atomic_json(output / "protocol.json", protocol)
    print(f"FROZEN {sha256_file(output / 'protocol.json')}", flush=True)


def inputs(output: Path) -> tuple[dict, dict, dict]:
    protocol = json.loads((output / "protocol.json").read_text())
    if sha256_file(Path(__file__)) != protocol["runner_sha256"]:
        raise ValueError("runner changed after protocol freeze")
    for source in protocol["source_registry"]:
        if sha256_file(ROOT / source["path"]) != source["sha256"]:
            raise ValueError("source changed after protocol freeze")
    base = json.loads((ROOT / BASE_PROTOCOL).read_text())
    system, source_audit = load_h4_source(ROOT, base)
    archive = np.load(ROOT / base["source_identity"]["h01_state_bundle"]["path"])
    ranks = np.asarray([(int(v) ^ int(archive["H4_hf_full_index"])).bit_count() // 2
                        for v in archive["H4_sector_full_indices"]])
    if not np.array_equal(np.flatnonzero(ranks <= 2), archive["H4_cisd_subspace_positions"]):
        raise AssertionError("excitation-rank mapping does not reproduce archived CISD positions")
    states = {name: system["states"][name] for name in ("rhf", "cisd", "exact")}
    cisd_overlap = None
    for rank, name in ((1, "cis"), (2, "cisd_control"), (3, "cisdt")):
        positions = np.flatnonzero(ranks <= rank)
        _, vectors = np.linalg.eigh(system["hamiltonian"][np.ix_(positions, positions)])
        state = np.zeros(36, dtype=np.complex128)
        state[positions] = vectors[:, 0]
        if name == "cisd_control":
            cisd_overlap = float(abs(np.vdot(states["cisd"], state)) ** 2)
            if abs(cisd_overlap - 1.0) > 1e-10:
                raise AssertionError("projected CI doubles fails to reproduce stored CISD")
        else:
            states[name] = state
    system["states"] = {name: states[name] for name in STATE_IDS}
    source_audit["cisd_projection_reproduction_overlap"] = cisd_overlap
    source_audit["ci_subspace_dimensions"] = {str(r): int(np.sum(ranks <= r)) for r in range(5)}
    return protocol, system, source_audit


def proxy_rows(system: dict, formula: dict, t: float, repeat: bool = False) -> tuple[np.ndarray, list[dict]]:
    unitary = build_unitary(system["spectra"], formula["s2_sequence"], t)
    unitarity = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(36)))
    echo = propagator_minus(system["hamiltonian"], t) @ unitary
    repeat_echo = None
    if repeat:
        repeat_echo = propagator_minus(system["hamiltonian"], t) @ build_unitary(system["spectra"], formula["s2_sequence"], t)
    rows = []
    h_norm = float(np.linalg.norm(system["hamiltonian"], 2))
    for sid, state in system["states"].items():
        amplitude = complex(np.vdot(state, echo @ state))
        value = float(amplitude.imag / t)
        repeat_difference = (abs(value - float(np.vdot(state, repeat_echo @ state).imag / t))
                             if repeat_echo is not None else 0.0)
        noise = proxy_noise_hartree(unitarity, repeat_difference, h_norm, t)
        rho, quality = quality_class(value, noise)
        rows.append({"formula_id": formula["formula_id"], "state_id": sid,
                     "time_hartree_inverse": t, "proxy_hartree": value,
                     "echo_real": float(amplitude.real), "echo_imaginary": float(amplitude.imag),
                     "proxy_noise_hartree": noise, "signal_to_noise": rho,
                     "quality": quality, "unitarity_residual": unitarity,
                     "repeatability_difference_hartree": repeat_difference})
    return unitary, rows


def predict(output: Path) -> None:
    if (output / "predictions.json").exists():
        raise RuntimeError("predictions already frozen")
    protocol, system, audit = inputs(output)
    const = protocol["constants"]
    training = []
    models = []
    for formula in protocol["formulas"]:
        rows = []
        for t in formula["training_times"]:
            _, point_rows = proxy_rows(system, formula, t, repeat=True)
            rows.extend(point_rows)
        training.extend(rows)
        for sid in STATE_IDS:
            points = [r for r in rows if r["state_id"] == sid]
            model = scaled_power_fit(formula["training_times"], [r["proxy_hartree"] for r in points], (4, 6))
            eligible = (all(r["quality"] in ("marginal", "resolved") for r in points)
                        and sum(r["quality"] == "resolved" for r in points) >= 3
                        and model["scaled_design_condition_number"] <= 1e8)
            candidates = []
            for index, t in enumerate(formula["candidate_times"]):
                shift = evaluate_fit(model, t)
                cost = model_cost(const["epsilon_E_hartree"], const["beta"], formula["step_cost"], t, shift)
                if cost is not None:
                    candidates.append({"index": index, "time": t, "shift": shift, "cost": cost})
            choice = min(candidates, key=lambda r: (r["cost"], r["time"])) if eligible and candidates else None
            models.append({"formula_id": formula["formula_id"], "state_id": sid,
                           "eligible": eligible, "model": model,
                           "resolved_training_count": sum(r["quality"] == "resolved" for r in points),
                           "choice": choice})
        print(f"PREDICTED {formula['formula_id']}", flush=True)
    selections = []
    for sid in STATE_IDS:
        valid = [row for row in models if row["state_id"] == sid and row["choice"] is not None]
        selected = min(valid, key=lambda r: r["choice"]["cost"]) if valid else None
        selections.append({"state_id": sid, "formula_id": selected["formula_id"] if selected else None,
                           "choice": selected["choice"] if selected else None,
                           "budget": selected["choice"]["cost"] * const["budget_multiplier"] if selected else None})
    state_quality = {sid: {**state_diagnostics(system["hamiltonian"], state, system["states"]["exact"], system["energy"]),
                           "state_sha256": sha256_array(state)} for sid, state in system["states"].items()}
    atomic_json(output / "state_quality.json", {"source_audit": audit, "states": state_quality,
                                               "quality_is_audit_only_not_selector_input": True})
    write_csv(output / "training_proxies.csv", training)
    atomic_json(output / "predictions.json", {
        "protocol_sha256": sha256_file(output / "protocol.json"),
        "truth_opened": False, "prediction_frozen_before_new_pf_truth": True,
        "models": models, "selections": selections,
        "selection_only_uses_proxy_models_costs_and_fixed_candidates": True,
    })
    (output / "PREDICTIONS_FROZEN.json").write_text(json.dumps({"prediction_sha256": sha256_file(output / "predictions.json")}, indent=2) + "\n")
    print("PREDICTIONS_FROZEN", flush=True)


def score(output: Path) -> None:
    started = time.monotonic()
    protocol, system, _ = inputs(output)
    frozen = json.loads((output / "PREDICTIONS_FROZEN.json").read_text())
    if frozen["prediction_sha256"] != sha256_file(output / "predictions.json"):
        raise AssertionError("prediction barrier hash changed")
    predictions = json.loads((output / "predictions.json").read_text())
    if predictions["protocol_sha256"] != sha256_file(output / "protocol.json"):
        raise AssertionError("protocol changed after prediction")
    const = protocol["constants"]
    epsilon, beta = const["epsilon_E_hartree"], const["beta"]
    models = {(r["formula_id"], r["state_id"]): r for r in predictions["models"]}
    truth, decomposition = [], []
    truth_lookup = {}
    reproduction_errors = []
    original_truth = [row for row in read_csv(ROOT / OLD_B / "branch_audit.csv")
                      if row["experiment_id"] == "B" and row["grid_role"] == "decision_frozen_grid"]
    if len(original_truth) != 1604:
        raise AssertionError(f"expected 1604 original decision rows, saw {len(original_truth)}")
    saved_lookup = {(r["formula_id"], float(r["time_hartree_inverse"])): r for r in original_truth}
    for formula in protocol["formulas"]:
        fid = formula["formula_id"]
        times = formula["candidate_times"]
        units, proxies = [], []
        for t in times:
            unitary, point_rows = proxy_rows(system, formula, t)
            units.append(unitary)
            proxies.append(point_rows)
        branches = track_direct_branch(units, times, system["states"]["exact"], system["energy"], 1e-8)
        for index, (t, branch, point_rows) in enumerate(zip(times, branches, proxies, strict=True)):
            shift = float(branch["direct_shift_hartree"])
            reliable = (branch["ground_state_overlap_probability"] >= 0.9
                        and branch["previous_branch_overlap_probability"] >= 0.9
                        and branch["eigenpair_residual_2_norm"] <= 1e-10)
            cost = model_cost(epsilon, beta, formula["step_cost"], t, shift)
            row = {"formula_id": fid, "index": index, "time_hartree_inverse": t,
                   **branch, "branch_reliable": reliable, "direct_cost": cost,
                   "unitarity_residual": point_rows[0]["unitarity_residual"]}
            truth.append(row)
            truth_lookup[(fid, index)] = row
            saved = saved_lookup[(fid, t)]
            reproduction_errors.append(abs(shift - float(saved["direct_shift_hartree"])))
            g0 = next(r["proxy_hartree"] for r in point_rows if r["state_id"] == "exact")
            for point in point_rows:
                sid = point["state_id"]
                fitted = evaluate_fit(models[(fid, sid)]["model"], t)
                g = point["proxy_hartree"]
                components = (fitted - g, g - g0, g0 - shift)
                total = fitted - shift
                decomposition.append({"formula_id": fid, "index": index, "state_id": sid,
                    "time_hartree_inverse": t, "model_signed_shift": fitted,
                    "proxy_hartree": g, "exact_proxy_hartree": g0,
                    "direct_shift_hartree": shift, "fit_component": components[0],
                    "state_component": components[1], "proxy_component": components[2],
                    "total_prediction_difference": total,
                    "closure_residual": abs(sum(components) - total),
                    "branch_reliable": reliable, "proxy_quality": point["quality"]})
        print(f"SCORED {fid} {len(times)} PF truth points", flush=True)
    reliable_feasible = [r for r in truth if r["branch_reliable"] and r["direct_cost"] is not None]
    reference = min(reliable_feasible, key=lambda r: r["direct_cost"])
    allocation = []
    selected_decomp = []
    for selected in predictions["selections"]:
        if selected["choice"] is None:
            allocation.append({"state_id": selected["state_id"], "status": "abstain"})
            continue
        sid, fid = selected["state_id"], selected["formula_id"]
        choice, budget = selected["choice"], selected["budget"]
        direct = truth_lookup[(fid, choice["index"])]
        step_cost = next(f["step_cost"] for f in protocol["formulas"] if f["formula_id"] == fid)
        qpe = beta * step_cost / (choice["time"] * budget)
        total = abs(direct["direct_shift_hartree"]) + qpe
        allocation.append({"state_id": sid, "formula_id": fid, "time_hartree_inverse": choice["time"],
            "candidate_index": choice["index"], "predicted_shift": choice["shift"],
            "predicted_cost": choice["cost"], "budget": budget,
            "direct_shift": direct["direct_shift_hartree"], "direct_cost_at_selection": direct["direct_cost"],
            "branch_reliable": direct["branch_reliable"], "qpe_error": qpe,
            "total_error": total, "target_met": direct["branch_reliable"] and total <= epsilon,
            "energy_margin": epsilon - total,
            "budget_over_selected_direct_cost": budget / direct["direct_cost"] if direct["direct_cost"] else None,
            "budget_over_grid_reference": budget / reference["direct_cost"],
            "selected_direct_over_grid_reference": direct["direct_cost"] / reference["direct_cost"] if direct["direct_cost"] else None})
        selected_decomp.extend(r for r in decomposition if (r["formula_id"], r["index"], r["state_id"]) == (fid, choice["index"], sid))
    bridge = []
    original_model = next(f["original_model"] for f in protocol["formulas"] if f["formula_id"] == "m5_best")
    for t in protocol["bridge"]["times"]:
        row = next(r for r in decomposition if r["formula_id"] == "m5_best" and r["state_id"] == "cisd" and r["time_hartree_inverse"] == t)
        fitted = evaluate_fit(original_model, t)
        components = (fitted - row["proxy_hartree"], row["state_component"], row["proxy_component"])
        bridge.append({**row, "model_source": "original_frozen_CISD",
                       "model_signed_shift": fitted, "fit_component": components[0],
                       "total_prediction_difference": fitted - row["direct_shift_hartree"],
                       "closure_residual": abs(sum(components) - (fitted - row["direct_shift_hartree"]))})
    m5 = next(f for f in protocol["formulas"] if f["formula_id"] == "m5_best")
    _, short_points = proxy_rows(system, m5, 0.4)
    short_reproduction = []
    old_obs = read_csv(ROOT / OLD_B / "observables.csv")
    for sid in ("cisd", "exact"):
        actual = next(r["proxy_hartree"] for r in short_points if r["state_id"] == sid)
        saved = next(float(r["proxy_imag_hartree"]) for r in old_obs
                     if r["experiment_id"] == "B" and r["formula_id"] == "m5_best"
                     and r["state_id"] == sid and float(r["time_hartree_inverse"]) == 0.4)
        short_reproduction.append({"state_id": sid, "time": 0.4, "saved_proxy": saved,
                                   "new_proxy": actual, "absolute_difference": abs(actual - saved)})
    checks = {
        "protocol_sha256": sha256_file(output / "protocol.json"),
        "prediction_sha256": sha256_file(output / "predictions.json"),
        "new_pf_truth_point_count": len(truth), "full_proxy_grid_rows": len(decomposition),
        "maximum_saved_truth_shift_difference": max(reproduction_errors),
        "maximum_three_component_closure_residual": max(r["closure_residual"] for r in decomposition + bridge),
        "maximum_pf_unitarity_residual": max(r["unitarity_residual"] for r in truth),
        "maximum_eigenpair_residual": max(r["eigenpair_residual_2_norm"] for r in truth),
        "unreliable_branch_points": sum(not r["branch_reliable"] for r in truth),
        "short_time_reproduction": short_reproduction,
        "reference": reference,
        "elapsed_scoring_seconds": time.monotonic() - started,
        "environment": {name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
        "original_artifacts_changed": False,
    }
    if checks["maximum_saved_truth_shift_difference"] > 1e-10:
        raise AssertionError("fresh truth differs from original beyond 1e-10 Ha")
    if checks["maximum_three_component_closure_residual"] > 1e-15:
        raise AssertionError("signed decomposition fails closure")
    if max(r["absolute_difference"] for r in short_reproduction) > 1e-12:
        raise AssertionError("short-time proxy fails reproduction")
    write_csv(output / "direct_grid.csv", truth)
    write_csv(output / "state_decomposition_grid.csv", decomposition)
    write_csv(output / "allocations.csv", allocation)
    write_csv(output / "selected_decomposition.csv", selected_decomp)
    write_csv(output / "long_time_bridge.csv", bridge)
    atomic_json(output / "checks.json", checks)
    print(json.dumps({"allocations": allocation, "bridge": bridge, "checks": checks}, indent=2), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("freeze", "predict", "score"), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    {"freeze": freeze, "predict": predict, "score": score}[args.phase](args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
