#!/usr/bin/env python3
"""Score a frozen D2-A prediction against existing development truth."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence


PLANNING_COMMIT = "d99715ef2c575a547394f2a5916abad27213d6fb"
EXPECTED_HASHES = {
    "review_response/pf_spectral_recoverability_d2_protocol_draft.json":
        "fb1d112e13830924ee5bed058cea8a8a6196d01b303b96fff664676db98d83f5",
    "review_response/pf_spectral_recoverability_d2_a_authorization.json":
        "7c0e7bfd3197d0c7d7d0fd37a09bcc92d00c861d6bbaf0400f405450858a1654",
    "artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/direct_points.csv":
        "dc0df4d7587f6c3342ea5ee09b753dec588d7cc6b634cde2adf4a7aeb20bfc78",
    "artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/coordinate_summary.csv":
        "b4bffaddc65a3c9bf25859a65515f1f7959b68374657689d7796f08f5285cd82",
    "artifacts/pf_r1_readonly_design_summary_20260928/coordinate_budget_diagnostics.csv":
        "d492668367d96d3839f37bc2a3fec4da45a8752792416ab8720ec3126b8ba770",
}
COMPLETE_STATUSES = {
    "d2_a_complete_prototype_candidate_stop",
    "d2_a_complete_information_cost_limit_stop",
    "d2_a_complete_close_spectral_route_stop",
}


class ScorerError(RuntimeError):
    """Raised when the frozen scorer boundary is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ScorerError("refusing empty score CSV")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if str(key) not in fields:
                fields.append(str(key))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_sources(root: Path) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PLANNING_COMMIT, head],
        cwd=root, check=False, capture_output=True,
    ).returncode != 0:
        raise ScorerError("planning commit is not an ancestor of HEAD")
    rows = []
    for relative, expected in EXPECTED_HASHES.items():
        actual = sha256_file(root / relative)
        if actual != expected:
            raise ScorerError(f"fixed scorer source mismatch: {relative}")
        rows.append({"path": relative, "sha256": actual})
    return {"head": head, "verified_sources": rows}


def verify_prediction(prediction_root: Path) -> tuple[dict[str, Any], str]:
    manifest = load_json(prediction_root / "manifest.json")
    for row in manifest.get("files", []):
        path = prediction_root / str(row["path"])
        if (
            not path.is_file()
            or path.stat().st_size != int(row["bytes"])
            or sha256_file(path) != str(row["sha256"])
        ):
            raise ScorerError(f"prediction manifest mismatch: {path}")
    marker = load_json(prediction_root / "PREDICTION_FROZEN.json")
    prediction_path = prediction_root / "prediction.json"
    prediction_hash = sha256_file(prediction_path)
    checksum = (prediction_root / "prediction.sha256").read_text(
        encoding="utf-8"
    ).split()[0]
    if (
        marker.get("prediction_sha256") != prediction_hash
        or checksum != prediction_hash
        or not marker.get("scoring_authorized_only_after_this_marker")
    ):
        raise ScorerError("prediction freeze identity mismatch")
    prediction = load_json(prediction_path)
    if (
        prediction.get("status") != "d2_a_prediction_frozen_truth_not_opened"
        or prediction.get("truth_open_count") != 0
        or len(prediction.get("predictions", [])) != 6
    ):
        raise ScorerError("invalid frozen prediction boundary")
    return prediction, prediction_hash


def _key(condition: str, time_value: float) -> tuple[str, str]:
    return str(condition), float(time_value).hex()


def baseline_budget(
    *,
    proxy_signed: float,
    gamma: float,
    beta: float,
    rotations: int,
    time_value: float,
    epsilon: float,
) -> float | None:
    estimate = abs(float(proxy_signed))
    if estimate >= epsilon:
        return None
    return float(gamma * beta * rotations / (time_value * (epsilon - estimate)))


def score_predictions(
    prediction: Mapping[str, Any],
    direct_rows: Sequence[Mapping[str, str]],
    d1_rows: Sequence[Mapping[str, str]],
    baseline_rows: Sequence[Mapping[str, str]],
    protocol: Mapping[str, Any],
) -> list[dict[str, Any]]:
    direct = {
        _key(str(row["condition"]), float(row["time_hartree_inverse"])): row
        for row in direct_rows
    }
    d1 = {
        (str(row["condition"]), str(row["time_hex"])): row for row in d1_rows
    }
    baseline = {
        (str(row["condition"]), str(row["time_hex"])): row
        for row in baseline_rows
    }
    epsilon = float(protocol["prediction_and_budget"]["epsilon_E_hartree"])
    beta = float(protocol["prediction_and_budget"]["qpe_beta"])
    main_gamma = float(protocol["scoring"]["main_baseline_gamma"])
    frontier = [float(value) for value in protocol["scoring"]["baseline_gamma_frontier"]]
    scored: list[dict[str, Any]] = []
    for row in prediction["predictions"]:
        condition = str(row["condition"])
        time_value = float(row["time_hartree_inverse"])
        time_hex = str(row["time_hex"])
        truth = direct.get(_key(condition, time_value))
        diagnostic = d1.get((condition, time_hex))
        base = baseline.get((condition, time_hex))
        if truth is None or diagnostic is None or base is None:
            raise ScorerError(f"missing fixed score input: {condition} {time_hex}")
        primary_dimension = int(row["primary_dimension_used"])
        primary = next(
            item for item in row["prefixes"]
            if int(item["dimension"]) == primary_dimension
        )
        predicted_shift = float(row["signed_shift_estimate_hartree"])
        direct_shift = float(truth["signed_direct_shift_hartree"])
        direct_error = float(truth["direct_error_hartree"])
        estimate_error = abs(predicted_shift - direct_shift)
        raw_e_use = row["e_use_hartree"]
        e_use = (
            None if raw_e_use is None else float(raw_e_use)
        )
        phase_gap_energy = float(diagnostic["phase_gap_radian"]) / time_value
        predicted_unwrap = int(primary["selected_phase_unwrap_integer"])
        truth_unwrap = int(diagnostic["phase_unwrap_integer"])
        branch_correct = (
            predicted_unwrap == truth_unwrap
            and estimate_error < 0.5 * phase_gap_energy
        )
        budget = row["frozen_pauli_rotation_budget"]
        safe = None
        if budget is not None:
            qpe_error = (
                beta * int(row["K_current_m3"]) / (time_value * float(budget))
            )
            safe = direct_error + qpe_error <= epsilon + 1e-15
        base_budgets = {
            str(gamma): baseline_budget(
                proxy_signed=float(base["cisd_proxy_signed_hartree"]),
                gamma=gamma,
                beta=beta,
                rotations=int(row["K_current_m3"]),
                time_value=time_value,
                epsilon=epsilon,
            )
            for gamma in frontier
        }
        main_budget = base_budgets[str(main_gamma)]
        quantum_budget_lower_than_main = (
            budget is not None
            and main_budget is not None
            and float(budget) < float(main_budget)
        )
        scored.append({
            "condition": condition,
            "time_hartree_inverse": time_value,
            "time_hex": time_hex,
            "claim_class": row["claim_class"],
            "abstained": bool(row["abstained"]),
            "predicted_signed_shift_hartree": predicted_shift,
            "direct_signed_shift_hartree": direct_shift,
            "signed_shift_error_hartree": predicted_shift - direct_shift,
            "absolute_shift_error_hartree": estimate_error,
            "predicted_e_use_hartree": e_use,
            "direct_error_hartree": direct_error,
            "dangerous_absolute_error_underestimation_hartree": (
                None if e_use is None else max(0.0, direct_error - e_use)
            ),
            "predicted_phase_unwrap_integer": predicted_unwrap,
            "truth_phase_unwrap_integer": truth_unwrap,
            "branch_correct": branch_correct,
            "branch_energy_half_gap_hartree": 0.5 * phase_gap_energy,
            "frozen_pauli_rotation_budget": budget,
            "frozen_budget_safe": safe,
            "baseline_local_cisd_proxy_signed_hartree": float(
                base["cisd_proxy_signed_hartree"]
            ),
            "baseline_budgets_by_gamma": json.dumps(
                base_budgets, sort_keys=True
            ),
            "main_baseline_gamma": main_gamma,
            "main_baseline_budget": main_budget,
            "quantum_budget_lower_than_main_baseline": quantum_budget_lower_than_main,
        })
    if len(scored) != 6:
        raise ScorerError("scoring did not cover exactly six coordinates")
    return scored


def choose_status(rows: Sequence[Mapping[str, Any]]) -> tuple[str, dict[str, Any]]:
    all_branches = all(bool(row["branch_correct"]) for row in rows)
    abstentions = sum(bool(row["abstained"]) for row in rows)
    unsafe = sum(row["frozen_budget_safe"] is False for row in rows)
    lower_budget = sum(
        bool(row["quantum_budget_lower_than_main_baseline"]) for row in rows
    )
    if not all_branches:
        status = "d2_a_complete_close_spectral_route_stop"
    elif abstentions == 0 and unsafe == 0 and lower_budget > 0:
        status = "d2_a_complete_prototype_candidate_stop"
    else:
        status = "d2_a_complete_information_cost_limit_stop"
    return status, {
        "branch_correct_count": sum(bool(row["branch_correct"]) for row in rows),
        "coordinate_count": len(rows),
        "abstention_count": abstentions,
        "unsafe_frozen_budget_count": unsafe,
        "spectral_budget_lower_than_main_baseline_count": lower_budget,
    }


def build_manifest(output: Path, names: Sequence[str]) -> dict[str, Any]:
    return {
        "schema": "pf_spectral_recoverability_d2_a_result_manifest_v1",
        "files": [
            {
                "path": name,
                "bytes": (output / name).stat().st_size,
                "sha256": sha256_file(output / name),
            }
            for name in names
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--prediction-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    root = args.project_root.resolve()
    source = verify_sources(root)
    prediction_root = args.prediction_root.resolve()
    prediction, prediction_hash = verify_prediction(prediction_root)
    output = (
        args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    ).resolve()
    if output.exists():
        raise ScorerError("score output must be new")
    output.mkdir(parents=True)
    protocol = load_json(
        root / "review_response/pf_spectral_recoverability_d2_protocol_draft.json"
    )
    direct_path = root / (
        "artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/"
        "direct_points.csv"
    )
    d1_path = root / (
        "artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/"
        "coordinate_summary.csv"
    )
    baseline_path = root / (
        "artifacts/pf_r1_readonly_design_summary_20260928/"
        "coordinate_budget_diagnostics.csv"
    )
    rows = score_predictions(
        prediction,
        load_csv(direct_path),
        load_csv(d1_path),
        load_csv(baseline_path),
        protocol,
    )
    status, summary = choose_status(rows)
    if status not in COMPLETE_STATUSES:
        raise ScorerError("invalid completion status")
    write_csv(output / "coordinate_scoring.csv", rows)
    atomic_json(output / "coordinate_scoring.json", {
        "schema": "pf_spectral_recoverability_d2_a_scoring_v1",
        "prediction_sha256": prediction_hash,
        "rows": rows,
    })
    decision = {
        "schema": "pf_spectral_recoverability_d2_a_decision_v1",
        "status": status,
        "prediction_sha256": prediction_hash,
        "prediction_changed_after_freeze": False,
        "scorer_truth_open_count": 3,
        "development_only": True,
        "independent_validation_claim": False,
        "closed_second_study_status": "complete_no_benefit_unchanged",
        "d2_b_authorized": False,
        "holdout_authorized": False,
        "retuning_authorized": False,
        "summary": summary,
        "wall_seconds": time.perf_counter() - started,
        "source_head": source["head"],
    }
    atomic_json(output / "decision.json", decision)
    report = (
        "# D2-A completion\n\n"
        f"- Status: `{status}`\n"
        f"- Prediction SHA-256: `{prediction_hash}`\n"
        f"- Branch correct: {summary['branch_correct_count']}/6\n"
        f"- Abstentions: {summary['abstention_count']}\n"
        f"- Unsafe frozen budgets: {summary['unsafe_frozen_budget_count']}\n"
        f"- Lower quantum budget than main baseline: "
        f"{summary['spectral_budget_lower_than_main_baseline_count']}/6\n"
        "- D2-B authorized: false\n"
        "- Closed second-study result: complete_no_benefit_unchanged\n"
    )
    (output / "report.md").write_text(report, encoding="utf-8")
    atomic_json(output / "D2_A_COMPLETE.json", {
        "status": status,
        "prediction_sha256": prediction_hash,
        "d2_b_authorized": False,
    })
    names = [
        "coordinate_scoring.csv", "coordinate_scoring.json", "decision.json",
        "report.md", "D2_A_COMPLETE.json",
    ]
    atomic_json(output / "manifest.json", build_manifest(output, names))
    print(json.dumps({
        "status": status,
        "prediction_sha256": prediction_hash,
        "summary": summary,
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
