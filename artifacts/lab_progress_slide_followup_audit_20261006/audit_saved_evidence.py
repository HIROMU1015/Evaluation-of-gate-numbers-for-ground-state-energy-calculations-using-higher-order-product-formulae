"""Reaggregate existing slide evidence without state, PF, or fitting calculations."""

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
SNAPSHOT = "870b4de4af32edde73d514bc6832dc5533b76cb7"
SOURCES = {
    "h4_search": "artifacts/two_term_pf_m3_refinement_local_20260909/refinement_results.json",
    "holdout_code": "review_response/run_two_term_pf_m3_holdout_server2.py",
    "h4_prediction": "artifacts/pf_first_study_phase_a_20260925_6265243/predictions.json",
    "h4_direct": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/branch_audit.csv",
    "h4_state_quality": "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/state_diagnostics.csv",
    "molecule_state_quality": "artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/state_diagnostics.csv",
    "exact_state_comparison": "artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/aggregate/summary.json",
    "s4_prediction": "artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f/predictions.json",
    "s4_diagnostic": "artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f/state_diagnostics.csv",
}


def read_json(key):
    return json.loads((ROOT / SOURCES[key]).read_text())


def read_csv(key):
    with (ROOT / SOURCES[key]).open() as stream:
        return list(csv.DictReader(stream))


def main():
    registry = {}
    for key, relative in SOURCES.items():
        data = (ROOT / relative).read_bytes()
        assert data == subprocess.check_output(["git", "show", f"{SNAPSHOT}:{relative}"], cwd=ROOT)
        origin = subprocess.check_output(
            ["git", "log", "-1", "--format=%H", SNAPSHOT, "--", relative], cwd=ROOT
        ).decode().strip()
        registry[key] = {
            "path": relative, "origin_result_commit": origin,
            "verified_snapshot_commit": SNAPSHOT,
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    candidate = next(row for row in read_json("h4_search")["candidates"] if row["name"] == "current_m3")
    saved_h4 = candidate["systems"]["H4"]
    point = next(row for row in saved_h4["direct_points"] if row["relative_time"] == 1.0)
    relative_error = abs(saved_h4["analytic_model_cost"] - point["direct_cost"]) / point["direct_cost"]
    assert math.isclose(relative_error, saved_h4["predictability"]["direct_at_analytic_time"]["model_to_direct_cost_relative_error"], rel_tol=1e-12)
    code = (ROOT / SOURCES["holdout_code"]).read_text()
    assert "MODEL_OPTIMIZATION_INTERVAL = (0.1, 1.4)" in code
    assert "MODEL_OPTIMIZATION_POINTS = 20001" in code
    assert "relative = np.linspace(" in code and "selected = int(np.argmin(costs))" in code

    direct = read_csv("h4_direct")
    grids = []
    for formula in read_json("h4_prediction")["experiment_B"]["formula_predictions"]:
        grid = formula["selection_grid_hartree_inverse"]
        rows = [row for row in direct if row["experiment_id"] == "B"
                and row["formula_id"] == formula["formula_id"]
                and row["grid_role"] == "decision_frozen_grid" and row["sign"] == "1"
                and row["branch_reliable"] == "True" and row["infeasible_error_budget"] == "False"]
        best = min(rows, key=lambda row: float(row["direct_cost"]))
        index = grid.index(float(best["time_hartree_inverse"]))
        assert 0 < index < len(grid) - 1
        grids.append({"formula": formula["formula_id"], "candidate_count": len(grid),
                      "interval_hartree_inverse": [min(grid), max(grid)],
                      "direct_minimum_time_hartree_inverse": float(best["time_hartree_inverse"]),
                      "zero_based_minimum_index": index, "minimum_at_interval_endpoint": False})

    quality = []
    for row in read_csv("h4_state_quality"):
        if row["case_id"] == "H4" and row["state_id"] in ("cisd", "rhf"):
            quality.append({"condition": "H4", "state": row["state_id"],
                            "ground_overlap_probability": float(row["exact_overlap_probability"]),
                            "energy_error_hartree": float(row["energy_error_hartree"])})
    for row in read_csv("molecule_state_quality"):
        if row["state_method"] == "cisd":
            quality.append({"condition": row["condition"], "state": "cisd",
                            "ground_overlap_probability": float(row["exact_ground_overlap_probability_evaluation_only"]),
                            "energy_error_hartree": float(row["energy_error_hartree"])})

    diagnostics = {(row["condition"], row["formula"]): row for row in read_csv("s4_diagnostic")}
    s4 = []
    for condition in read_json("s4_prediction")["conditions"]:
        baseline = condition["strategies"]["practical_baseline"]
        targeted = condition["strategies"]["state_targeted_fallback"]
        assert baseline["selection"]["selected_formula"] == targeted["selection"]["selected_formula"]
        assert baseline["selection"]["selected_time"] == targeted["selection"]["selected_time"]
        assert baseline["selection"]["predicted_cost"] == targeted["selection"]["predicted_cost"]
        for formula in baseline["pf_predictions"]:
            row = diagnostics[condition["condition"], formula["formula"]]
            s4.append({"condition": condition["condition"], "formula": formula["formula"],
                       "baseline_cap_applied": formula["fallback_triggered"],
                       "state_diagnostic_triggered": row["state_risk"] == "True",
                       "diagnostic_score": float(row["primary_score"]),
                       "maximum_proxy_difference_hartree": float(row["maximum_absolute_proxy_difference_hartree"]),
                       "magnitude_triggered": row["magnitude_risk"] == "True",
                       "sign_triggered": row["sign_risk"] == "True",
                       "baseline_and_targeted_selection_identical": True})
    uncapped = [row for row in s4 if not row["baseline_cap_applied"]]
    assert len(uncapped) == 8 and not any(row["state_diagnostic_triggered"] for row in uncapped)
    triggered = [row for row in s4 if row["state_diagnostic_triggered"]]
    assert len(triggered) == 2 and all(row["baseline_cap_applied"] for row in triggered)
    assert all(row["sign_triggered"] and not row["magnitude_triggered"] for row in triggered)

    result = {
        "analysis_type": "post_hoc_saved_scalar_and_procedure_audit",
        "scientific_calculation_performed": False, "original_artifacts_modified": False,
        "source_registry": registry,
        "h4_one_term_at_analytic_time": {
            "formula": "current_m3", "scope": "earlier coefficient-search experiment",
            "time_hartree_inverse": point["time"],
            "model_error_hartree": point["model_error_hartree"],
            "direct_error_hartree": point["direct_error_hartree"],
            "model_cost": saved_h4["analytic_model_cost"], "direct_cost": point["direct_cost"],
            "cost_prediction_relative_error": relative_error,
            "interpretation": "Both errors and costs are evaluated at t_ana, not at separately optimized times.",
        },
        "holdout_two_term_time_selection": {
            "method": "numerical minimum of model costs on a 20001-point linear grid",
            "relative_interval": [0.1, 1.4],
            "pf_diagonalization_at_every_model_candidate": False,
            "subsequent_direct_comparison": "saved local direct grid around the model-selected time",
        },
        "h4_candidate_minima": grids,
        "candidate_range_sufficiency": "All four saved direct minima are interior; optimality outside the frozen ranges is unestablished.",
        "saved_state_quality_evaluation_only": quality,
        "earlier_exact_state_comparison": read_json("exact_state_comparison")["decisions"],
        "s4_fixed_diagnostic_comparisons": s4,
        "s4_uncapped_pf_condition_count": len(uncapped),
        "s4_new_diagnostic_trigger_count_in_uncapped": 0,
        "remaining_unestablished": [
            "matched FCI-input allocation selection on the frozen H4 decision grids",
            "sufficiency or global optimality outside the frozen candidate time ranges",
            "which prediction-error component dominates at the long H4 allocation times",
            "a truncation-based diagnostic certifying proximity to the exact ground state",
        ],
    }
    scalar = OUTPUT / "checks.json"
    scalar.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    manifest = {"self_excluded": "manifest.json is excluded from its own hash list",
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__).resolve(), scalar)}}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified H4 same-time comparison, numerical model optimum, frozen-grid minima, state quality, and all 12 S4 diagnostics.")


if __name__ == "__main__":
    main()
