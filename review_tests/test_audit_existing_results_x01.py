"""Regression tests for the X01 A01/A02 saved-result audit."""

from __future__ import annotations

import math

import audit_existing_results_x01 as audit


def test_comparison_metric_recomputation_uses_saved_direct_values() -> None:
    model = {
        "predicted_time_direct_point": {"direct_cost": 110.0, "time": 2.0},
        "predicted_time_model_cost": 100.0,
        "saved_local_direct_minimum": {"direct_cost": 100.0, "time": 2.1},
        "saved_unseen_predictions": [
            {"residual_over_epsilon": 0.01},
            {"residual_over_epsilon": 0.03},
        ],
    }
    result = audit.comparison_model_metrics(model)
    assert math.isclose(result["eta_star"], 10.0 / 110.0)
    assert math.isclose(result["eta_min"], 0.1)
    assert math.isclose(result["eta_t"], abs(2.0 / 2.1 - 1.0))
    assert result["maximum_unseen_residual_over_epsilon"] == 0.03


def test_saved_x01_sources_reaggregate_exactly() -> None:
    result = audit.run_audit(
        audit.DEFAULT_FIVE, audit.DEFAULT_TWELVE, audit.DEFAULT_JOINT
    )
    assert result["condition_row_count"] == 319
    assert result["metric_reproduction_eligible_count"] == 318
    assert result["metric_unavailable_row_count"] == 1
    assert result["metric_reproduction_pass_count"] == 318
    assert result["pass_reproduction_pass_count"] == 319
    assert result["cost_ratio_row_count"] == 17
    assert result["cost_ratio_reproduction_pass_count"] == 17
    assert result["joint_candidate_count"] == 31
    assert result["joint_summary_reproduction_pass_count"] == 31

    combined = {
        (row["pf"], row["model"]): row
        for row in result["combined_holdout_rows"]
    }
    assert combined[("two_term_center", "two_term")]["passed"] == 17
    assert combined[("current_m3", "two_term")]["passed"] == 16

    top = result["joint_candidate_rows"][0]
    assert top["candidate"] == "joint_refine_r0_s0046"
    assert top["passed_conditions"] == 6
