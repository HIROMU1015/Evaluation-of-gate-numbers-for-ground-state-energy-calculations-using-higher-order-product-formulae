"""Read-only scalar classification and hash audit after frozen H4 scoring."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(filename: str) -> list[dict[str, str]]:
    with (HERE / filename).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    protocol = json.loads((HERE / "protocol.json").read_text())
    predictions = json.loads((HERE / "predictions.json").read_text())
    checks = json.loads((HERE / "checks.json").read_text())
    frozen = json.loads((HERE / "PREDICTIONS_FROZEN.json").read_text())
    assert predictions["protocol_sha256"] == digest(HERE / "protocol.json")
    assert frozen["prediction_sha256"] == digest(HERE / "predictions.json")
    assert checks["prediction_sha256"] == frozen["prediction_sha256"]
    for source in protocol["source_registry"]:
        assert digest(ROOT / source["path"]) == source["sha256"]
    assert digest(ROOT / "review_response/run_lab_progress_h4_state_checks_20261007.py") == protocol["runner_sha256"]
    spectral_protocol = json.loads((HERE / "spectral_protocol.json").read_text())
    assert digest(ROOT / "review_response/audit_lab_progress_h4_spectral_proxy_20261007.py") == spectral_protocol["runner_sha256"]
    assert spectral_protocol["input_direct_grid_sha256"] == digest(HERE / "direct_grid.csv")
    epsilon = protocol["constants"]["epsilon_E_hartree"]
    decisions = []
    for row in read_csv("allocations.csv"):
        reliable = row.get("branch_reliable") == "True"
        if row.get("status") == "abstain":
            classification, reason = "abstain", "no eligible predicted candidate"
        elif not reliable:
            classification, reason = "unscorable", "tracked PF branch fails original reliability gate; raw tracked shift is not validated ground-energy error"
        elif float(row["total_error"]) <= epsilon:
            classification, reason = "pass", "reliable PF branch and frozen PF+QPE bound within target"
        else:
            classification, reason = "fail", "reliable PF branch and frozen PF+QPE bound exceeds target"
        decisions.append({"state_id": row["state_id"], "classification": classification,
                          "reason": reason, "formula_id": row.get("formula_id"),
                          "time_hartree_inverse": float(row["time_hartree_inverse"]),
                          "budget": float(row["budget"]),
                          "pf_error_alone_exceeds_target": abs(float(row["direct_shift"])) > epsilon if reliable else None,
                          "validated_total_error_hartree": float(row["total_error"]) if reliable else None,
                          "budget_ratio_is_precision_validated": classification == "pass"})
    assert {r["state_id"]: r["classification"] for r in decisions} == {
        "rhf": "fail", "cis": "fail", "cisd": "pass", "cisdt": "unscorable", "exact": "unscorable"}
    decomposition = read_csv("state_decomposition_grid.csv")
    fixed_comparisons = [row for row in decomposition
                         if row["formula_id"] == "m5_best" and float(row["time_hartree_inverse"]) in protocol["bridge"]["times"]]
    original = json.loads((ROOT / "artifacts/pf_first_study_phase_a_20260925_6265243/predictions.json").read_text())["experiment_B"]["selection"]
    reproduced = next(row for row in predictions["selections"] if row["state_id"] == "cisd")
    assert reproduced["formula_id"] == original["selected_formula"]
    assert reproduced["choice"]["time"] == original["selected_time_hartree_inverse"]
    rel_cost_difference = abs(reproduced["choice"]["cost"] / original["predicted_cost"] - 1.0)
    assert rel_cost_difference < 1e-8
    assert checks["maximum_saved_truth_shift_difference"] <= 1e-10
    assert checks["maximum_three_component_closure_residual"] <= 1e-15
    spectral = json.loads((HERE / "spectral_checks.json").read_text())
    assert len(spectral["summaries"]) == 3
    assert max(r["spectral_sum_closure_residual"] for r in spectral["summaries"]) <= 1e-12
    payload = {
        "post_hoc_classification_only": True, "formal_predictions_or_scoring_changed": False,
        "classification_policy": "reliability checked before accuracy; unscorable tracked shifts never establish ground-energy accuracy failure",
        "decisions": decisions,
        "same_m5_same_time_state_controls": fixed_comparisons,
        "cisd_original_prediction_relative_cost_reproduction_error": rel_cost_difference,
        "checks_passed": True,
        "numerical_unitary_builds": {"training_with_repeats": 40, "candidate_grids": 1604,
                                     "short_proxy_reproduction": 1, "spectral_fixed_points": 3},
        "numerical_pf_diagonalizations": {"candidate_grids": 1604, "spectral_fixed_points": 3},
        "scalar_proxy_evaluations": {"training_including_repeats": 200, "candidate_grids": 8020,
                                     "short_reproduction": 5, "spectral_fixed_points": 15},
    }
    (HERE / "classification_and_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    paths = sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "manifest.json")
    paths += [ROOT / "review_response/run_lab_progress_h4_state_checks_20261007.py",
              ROOT / "review_response/audit_lab_progress_h4_spectral_proxy_20261007.py"]
    manifest = {"self_excluded": ["artifacts/lab_progress_h4_state_checks_20261007/manifest.json"],
                "publication_policy": "code, scalar data, metadata and prose only; no new matrices/vectors/unitaries",
                "source_registry": "protocol.json: source origin_result_commit and verified_snapshot_commit remain separate",
                "files": {str(path.relative_to(ROOT)): digest(path) for path in paths}}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classifications": decisions, "manifest_files": len(paths), "checks_passed": True}, indent=2))


if __name__ == "__main__":
    main()
