"""Truth-only Phase-B scorer for the frozen HF domain pilot prediction."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import pickle
import resource
import subprocess
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

import hf_domain_intervention_pilot as core
import run_full_electron_nh3_higher_term_diagnosis as diagnosis
import run_h01_approximate_state_calibration as h01
from _pf_first_study_s0_exact_time_scoring_base import direct_branch_point


CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")
TIME_RTOL = 2e-14
FIRST_STUDY_PROTOCOL_SHA256 = "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"


def git_output(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def verify_committed_prediction(
    *, project_root: Path, prediction_root: Path,
    prediction_commit: str, artifact_relative: Path,
) -> tuple[dict[str, Any], str]:
    if git_output(project_root, "rev-parse", "HEAD") != prediction_commit:
        raise core.HFPilotError("HEAD must equal the prediction freeze commit")
    prediction, digest = core.verify_prediction_files(prediction_root)
    expected_files = {
        "prediction.json", "prediction.sha256", "PREDICTION_FROZEN.json",
        "source_audit.json", "access_audit.json", "resource_audit.json",
        "manifest.json",
    }
    actual_files = {path.name for path in prediction_root.iterdir() if path.is_file()}
    if actual_files != expected_files:
        raise core.HFPilotError("prediction artifact file set changed")
    for name in sorted(expected_files):
        blob = subprocess.run(
            ["git", "show", f"{prediction_commit}:{(artifact_relative / name).as_posix()}"],
            cwd=project_root, check=True, capture_output=True,
        ).stdout
        if blob != (prediction_root / name).read_bytes():
            raise core.HFPilotError(f"prediction commit blob mismatch: {name}")
    return prediction, digest


def _convert(value: str) -> Any:
    if value == "":
        return None
    if value in ("True", "False"):
        return value == "True"
    try:
        return float(value)
    except ValueError:
        return value


def truth_rows(paths: Sequence[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            raise core.HFPilotError(f"truth source missing: {path}")
        if path.suffix.lower() != ".csv":
            raise core.HFPilotError("only audited CSV truth sources are accepted")
        with path.open(newline="", encoding="utf-8") as stream:
            for raw in csv.DictReader(stream):
                row = {key: _convert(value) for key, value in raw.items()}
                row["truth_source_path"] = str(path.resolve())
                row["truth_source_sha256"] = core.sha256_file(path)
                rows.append(row)
    return rows


def exact_match(
    rows: Iterable[Mapping[str, Any]], condition: str, time_value: float,
) -> dict[str, Any] | None:
    matches = [
        dict(row) for row in rows
        if row.get("condition") == condition
        and row.get("formula") in (None, "current_m3")
        and row.get("time") is not None
        and math.isclose(float(row["time"]), float(time_value), rel_tol=0.0, abs_tol=TIME_RTOL)
        and row.get("signed_direct_shift_hartree") is not None
    ]
    if len(matches) > 1:
        shifts = {round(float(row["signed_direct_shift_hartree"]), 14) for row in matches}
        if len(shifts) != 1:
            raise core.HFPilotError("conflicting exact-coordinate truth")
    return None if not matches else matches[0]


def load_truth_systems(cache_root: Path, authorization: Mapping[str, Any]) -> dict[str, Any]:
    expected = authorization["resolved_execution_blockers"]["cache_preflight"]
    systems = {}
    for condition in CONDITIONS:
        path = cache_root / "cache" / f"{condition}.pkl"
        if not path.is_file() or core.sha256_file(path) != expected["pickle_sha256"][condition]:
            raise core.HFPilotError(f"truth cache identity mismatch: {condition}")
        system = h01._load_system(path)
        if system.get("hamiltonian_sha256") != expected["hamiltonian_sha256"][condition]:
            raise core.HFPilotError(f"truth Hamiltonian identity mismatch: {condition}")
        systems[condition] = system
    return systems


def find_candidate(condition: Mapping[str, Any], candidate_id: str) -> dict[str, Any]:
    return next(
        dict(row) for row in condition["candidates"]
        if row["candidate_id"] == candidate_id
    )


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    root = args.project_root.resolve()
    prediction, prediction_hash = verify_committed_prediction(
        project_root=root,
        prediction_root=args.prediction_root.resolve(),
        prediction_commit=args.prediction_commit,
        artifact_relative=args.prediction_artifact_relative,
    )
    authorization = core.load_json(args.authorization.resolve())
    if prediction["authorization_sha256"] != core.sha256_file(args.authorization.resolve()):
        raise core.HFPilotError("prediction/authorization identity mismatch")
    output = args.output_dir.resolve()
    if output.exists():
        raise core.HFPilotError("scoring output must be new")
    output.mkdir(parents=True)
    source_rows = truth_rows([path.resolve() for path in args.truth_source])
    first_study_protocol_path = root / "PF_first_study_protocol_20260925.json"
    if core.sha256_file(first_study_protocol_path) != FIRST_STUDY_PROTOCOL_SHA256:
        raise core.HFPilotError("first-study protocol identity mismatch")
    direct_phase_cluster_threshold = float(
        core.load_json(first_study_protocol_path)["phase_and_branch_policy"]["degenerate_phase_gap_radians"]
    )
    systems = load_truth_systems(args.cache_root.resolve(), authorization)
    source_contract = core.load_json(args.source_contract.resolve())
    sequence = [float(value) for value in source_contract["current_m3_sequence"]]
    constants = core.load_json(args.p0_protocol.resolve())["fixed_constants"]
    epsilon = float(constants["epsilon_E_hartree"])
    beta = float(constants["beta"])
    rotations = int(constants["K_current_m3_per_step"])
    baseline_rows = {
        row["condition"]: row
        for row in core.load_json(args.p0_protocol.resolve())["baseline_contract"]["conditions"]
    }
    truth_by_condition: dict[str, dict[str, dict[str, Any]]] = {}
    truth_output: list[dict[str, Any]] = []
    computed = 0
    reused = 0
    for condition_payload in prediction["conditions"]:
        condition = condition_payload["condition"]
        truth_by_condition[condition] = {}
        system = systems[condition]
        exact_state = np.asarray(system["state"], dtype=np.complex128)
        exact_energy = float(system["energy"])
        for candidate in condition_payload["candidates"]:
            candidate_id = candidate["candidate_id"]
            time_value = float(candidate["time_hartree_inverse"])
            saved = exact_match(source_rows, condition, time_value)
            if saved is not None:
                point = {
                    "time": time_value,
                    "signed_direct_shift_hartree": float(saved["signed_direct_shift_hartree"]),
                    "minimum_selected_phase_gap_radians": float(saved["minimum_selected_phase_gap_radians"]),
                    "eigenpair_residual_2_norm": saved.get("eigenpair_residual_2_norm"),
                    "unitarity_residual_frobenius": saved.get("unitarity_residual_frobenius"),
                    "branch_selection_disagrees_with_comparator": saved.get("branch_selection_disagrees_with_comparator", False),
                    "truth_source": "reused_exact_coordinate",
                    "truth_source_path": saved["truth_source_path"],
                    "truth_source_sha256": saved["truth_source_sha256"],
                }
                reused += 1
            else:
                if float(candidate["factor_of_T0"]) == 1.0:
                    raise core.HFPilotError("T0 reproduction truth must be reused, not recomputed")
                if computed >= 4:
                    raise core.HFPilotError("new direct truth limit exceeded")
                unitary, build = diagnosis._build_cpu(system, sequence, time_value)
                point, _ = direct_branch_point(
                    unitary, exact_state, exact_energy, time_value,
                    rotations, epsilon, None, direct_phase_cluster_threshold,
                )
                point["truth_source"] = "new_exact_coordinate_after_prediction_freeze"
                point["build_timing_seconds"] = build
                computed += 1
                del unitary
            point.update({"condition": condition, "candidate_id": candidate_id})
            truth_by_condition[condition][candidate_id] = point
            truth_output.append(point)
    if computed > 4 or reused < 2 or computed + reused != 6:
        raise core.HFPilotError("truth accounting mismatch")
    condition_scores: list[dict[str, Any]] = []
    coordinate_scores: list[dict[str, Any]] = []
    for condition_payload in prediction["conditions"]:
        condition = condition_payload["condition"]
        baseline = baseline_rows[condition]
        t0_candidate = next(
            row for row in condition_payload["candidates"]
            if float(row["factor_of_T0"]) == 1.0
        )
        t0_m1 = t0_candidate["M1"]
        t0_truth = truth_by_condition[condition][t0_candidate["candidate_id"]]
        t0_branch = core.physical_branch_correct(
            predicted_shift_hartree=t0_m1["signed_shift_estimate_hartree"],
            direct_shift_hartree=t0_truth["signed_direct_shift_hartree"],
            truth_phase_gap_radians=t0_truth["minimum_selected_phase_gap_radians"],
            time_value=t0_truth["time"],
        )
        t0_pass = core.t0_reproduction_pass(
            abstained=t0_m1["abstained"], branch_correct=t0_branch,
            predicted_shift_hartree=t0_m1["signed_shift_estimate_hartree"],
            width_hartree=t0_m1["width_hartree"],
            direct_shift_hartree=t0_truth["signed_direct_shift_hartree"],
        )
        selections = condition_payload["selection"]
        m1_selection = selections["M1"]
        m1_candidate = find_candidate(condition_payload, m1_selection["selected_candidate"])
        m1_truth = truth_by_condition[condition][m1_selection["selected_candidate"]]
        m1_row = m1_candidate["M1"]
        m1_branch = core.physical_branch_correct(
            predicted_shift_hartree=m1_row["signed_shift_estimate_hartree"],
            direct_shift_hartree=m1_truth["signed_direct_shift_hartree"],
            truth_phase_gap_radians=m1_truth["minimum_selected_phase_gap_radians"],
            time_value=m1_truth["time"],
        )
        m1_safe = core.direct_budget_safe(
            direct_shift_hartree=m1_truth["signed_direct_shift_hartree"],
            beta=beta, rotations=rotations,
            time_value=m1_selection["selected_time_hartree_inverse"],
            frozen_budget=m1_selection["frozen_continuous_budget"],
            epsilon_hartree=epsilon,
        )
        target_budget = 0.90 * float(baseline["B0_continuous"])
        spectral_signal = bool(
            t0_pass and m1_branch and m1_safe
            and not m1_selection["fallback"]
            and float(m1_selection["selected_time_hartree_inverse"]) > float(baseline["T0_hartree_inverse"])
            and float(m1_selection["frozen_continuous_budget"]) <= target_budget
        )
        fixed_width_blocked = False
        for candidate in condition_payload["candidates"]:
            row = candidate["M1"]
            if float(candidate["factor_of_T0"]) <= 1.0:
                continue
            truth = truth_by_condition[condition][candidate["candidate_id"]]
            branch = core.physical_branch_correct(
                predicted_shift_hartree=row["signed_shift_estimate_hartree"],
                direct_shift_hartree=truth["signed_direct_shift_hartree"],
                truth_phase_gap_radians=truth["minimum_selected_phase_gap_radians"],
                time_value=truth["time"],
            )
            fixed_width_blocked = fixed_width_blocked or bool(
                branch
                and abs(float(row["signed_shift_estimate_hartree"])) <= float(row["allowance_hartree"])
                and float(row["e_use_hartree"]) > float(row["allowance_hartree"])
            )
        b1_scores: list[dict[str, Any]] = []
        for selection in selections["B1"]:
            candidate = find_candidate(condition_payload, selection["selected_candidate"])
            truth = truth_by_condition[condition][selection["selected_candidate"]]
            safe = core.direct_budget_safe(
                direct_shift_hartree=truth["signed_direct_shift_hartree"],
                beta=beta, rotations=rotations,
                time_value=selection["selected_time_hartree_inverse"],
                frozen_budget=selection["frozen_continuous_budget"],
                epsilon_hartree=epsilon,
            )
            b1_scores.append({
                "gamma": selection["gamma"],
                "selected_candidate": selection["selected_candidate"],
                "fallback": selection["fallback"],
                "safe": safe,
                "frozen_continuous_budget": selection["frozen_continuous_budget"],
                "target_met": bool(
                    not selection["fallback"]
                    and selection["frozen_continuous_budget"] <= target_budget
                ),
            })
        condition_scores.append({
            "condition": condition,
            "evaluable": True,
            "T0_reproduction_pass": t0_pass,
            "T0_branch_correct": t0_branch,
            "selected_branch_valid": m1_branch,
            "M1_selected_candidate": m1_selection["selected_candidate"],
            "M1_fallback": m1_selection["fallback"],
            "M1_safe": m1_safe,
            "M1_frozen_continuous_budget": m1_selection["frozen_continuous_budget"],
            "unsafe_selected_intervention": bool(not m1_selection["fallback"] and not m1_safe),
            "spectral_strong_signal": spectral_signal,
            "fixed_width_blocked": fixed_width_blocked,
            "B1": b1_scores,
            "cheap_proxy_matches_or_dominates": False,
        })
        for candidate in condition_payload["candidates"]:
            truth = truth_by_condition[condition][candidate["candidate_id"]]
            coordinate_scores.append({
                "condition": condition,
                "candidate_id": candidate["candidate_id"],
                "factor_of_T0": candidate["factor_of_T0"],
                "time_hartree_inverse": candidate["time_hartree_inverse"],
                "M1_signed_shift_hartree": candidate["M1"]["signed_shift_estimate_hartree"],
                "M1_width_hartree": candidate["M1"]["width_hartree"],
                "direct_shift_hartree": truth["signed_direct_shift_hartree"],
                "phase_gap_radians": truth["minimum_selected_phase_gap_radians"],
                "M1_branch_correct": core.physical_branch_correct(
                    predicted_shift_hartree=candidate["M1"]["signed_shift_estimate_hartree"],
                    direct_shift_hartree=truth["signed_direct_shift_hartree"],
                    truth_phase_gap_radians=truth["minimum_selected_phase_gap_radians"],
                    time_value=truth["time"],
                ),
                "truth_source": truth["truth_source"],
            })
    m1_coverage = sum(bool(row["spectral_strong_signal"]) for row in condition_scores)
    m1_aggregate = sum(float(row["M1_frozen_continuous_budget"]) for row in condition_scores)
    gamma_frontier: list[dict[str, Any]] = []
    for gamma in authorization["phase_a"]["gamma_arms"]:
        rows = [next(item for item in row["B1"] if float(item["gamma"]) == float(gamma)) for row in condition_scores]
        coverage = sum(bool(item["safe"] and item["target_met"]) for item in rows)
        aggregate = sum(float(item["frozen_continuous_budget"]) for item in rows)
        gamma_frontier.append({
            "gamma": float(gamma), "safe_target_coverage": coverage,
            "aggregate_frozen_continuous_budget": aggregate,
            "matches_or_dominates_M1": bool(coverage >= m1_coverage and aggregate <= m1_aggregate),
        })
    cheap = any(row["matches_or_dominates_M1"] for row in gamma_frontier)
    for row in condition_scores:
        row["cheap_proxy_matches_or_dominates"] = cheap
    classification = core.choose_completion_status(condition_scores)
    result = {
        "schema": "hf_domain_intervention_scoring_v1",
        "status": "second_study_v2_hf_domain_pilot_complete_review_required",
        "classification": classification,
        "prediction_sha256": prediction_hash,
        "prediction_commit": args.prediction_commit,
        "truth_accounting": {
            "coordinate_count": 6,
            "direct_phase_cluster_threshold_radians": direct_phase_cluster_threshold,
            "reused_exact_coordinates": reused,
            "new_direct_coordinates": computed,
            "new_direct_coordinate_limit": 4,
        },
        "condition_scores": condition_scores,
        "B1_gamma_frontier": gamma_frontier,
        "coordinate_scores": coordinate_scores,
        "next_stage_authorized": False,
    }
    core.write_json(output / "result.json", result)
    write_csv(output / "coordinate_scoring.csv", coordinate_scores)
    core.write_json(output / "truth_audit.json", {
        "truth_points": truth_output,
        "new_direct_coordinates": computed,
        "reused_exact_coordinates": reused,
        "nearest_coordinate_substitution": False,
        "interpolation": False,
    })
    core.write_json(output / "resource_audit.json", {
        "wall_seconds": time.perf_counter() - started,
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "cpu_processes": 1,
        "blas_threads": 1,
        "gpu_operation_count": 0,
    })
    core.write_json(output / "COMPLETE.json", {
        "status": result["status"],
        "classification": classification,
        "prediction_sha256": prediction_hash,
        "automatic_next_stage": False,
    })
    names = ["result.json", "coordinate_scoring.csv", "truth_audit.json", "resource_audit.json", "COMPLETE.json"]
    core.write_json(output / "manifest.json", {
        "schema": "hf_domain_intervention_result_manifest_v1",
        "manifest_self_excluded": True,
        "files": [
            {"path": name, "bytes": (output / name).stat().st_size, "sha256": core.sha256_file(output / name)}
            for name in names
        ],
    })
    print(json.dumps({
        "status": result["status"], "classification": classification,
        "prediction_sha256": prediction_hash, "new_truth": computed,
        "output": str(output),
    }, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--p0-protocol", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--source-contract", required=True, type=Path)
    parser.add_argument("--prediction-root", required=True, type=Path)
    parser.add_argument("--prediction-commit", required=True)
    parser.add_argument("--prediction-artifact-relative", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--truth-source", required=True, type=Path, nargs="+")
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
