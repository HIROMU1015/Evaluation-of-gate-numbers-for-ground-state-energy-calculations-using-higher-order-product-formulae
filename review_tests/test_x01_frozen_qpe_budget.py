"""Regression tests for the X01 A05 frozen-QPE-budget audit."""

from __future__ import annotations

import math

import analyze_x01_frozen_qpe_budget as analysis


def test_frozen_budget_score_distinguishes_under_and_over_estimation() -> None:
    target = 0.1
    frozen_cost = 1.0 / (target - 0.02)
    underestimated = analysis.score_frozen_budget(
        time=1.0,
        rotations=1,
        model_signed_shift=0.02,
        direct_signed_shift=0.03,
        frozen_cost=frozen_cost,
        target_error=target,
        beta=1.0,
    )
    assert underestimated["strict_frozen_budget_pass"] is False
    assert underestimated["pf_error_direction"] == "underestimated_pf_error"
    assert math.isclose(underestimated["actual_total_error_bound_hartree"], 0.11)
    assert math.isclose(underestimated["target_excess_hartree"], 0.01)
    assert math.isclose(
        underestimated["additional_cost_fraction_needed"],
        (1.0 / (target - 0.03)) / frozen_cost - 1.0,
    )

    conservative = analysis.score_frozen_budget(
        time=1.0,
        rotations=1,
        model_signed_shift=0.02,
        direct_signed_shift=0.01,
        frozen_cost=frozen_cost,
        target_error=target,
        beta=1.0,
    )
    assert conservative["strict_frozen_budget_pass"] is True
    assert conservative["pf_error_direction"] == "conservative_pf_error"
    assert math.isclose(conservative["actual_total_error_bound_hartree"], 0.09)
    assert conservative["avoidable_cost_fraction_vs_direct"] > 0.0


def test_saved_frozen_budgets_and_cost_identities_reaggregate() -> None:
    result = analysis.run_analysis()
    assert result["row_count"] == 102
    assert result["fixed_metric_rows_reproduced"] == 102
    assert result["fixed_pass_rows_reproduced"] == 102
    assert result["maximum_model_cost_reproduction_relative_difference"] == 0.0
    assert result["maximum_direct_cost_reproduction_relative_difference"] == 0.0
    assert result["maximum_qpe_allowance_reproduction_difference_hartree"] < 1e-18
    assert result["strict_frozen_budget_pass_count"] == 94
    assert result["strict_frozen_budget_failure_count"] == 8
    assert result["eta_star_fail_but_frozen_safe_count"] == 40
    assert result["eta_star_pass_but_frozen_fail_count"] == 8


def test_only_two_term_center_two_term_has_strict_budget_misses() -> None:
    result = analysis.run_analysis()
    lookup = {
        (row["pf"], row["model"]): row for row in result["aggregate_rows"]
    }
    for pf in analysis.PFS:
        for model in analysis.MODELS:
            row = lookup[(pf, model)]
            expected = 9 if (pf, model) == ("two_term_center", "two_term") else 17
            assert row["strict_frozen_budget_passed"] == expected

    center_two = lookup[("two_term_center", "two_term")]
    assert center_two["four_metric_passed"] == 17
    assert center_two["underestimated_pf_error_count"] == 8
    assert center_two["maximum_target_excess_condition"] == "BeH2_stretch150_631g"
    assert center_two["maximum_target_excess_over_epsilon"] < 1e-4
    assert center_two["maximum_additional_cost_fraction_needed"] < 1.3e-4

    failures = result["_failure_rows"]
    assert len(failures) == 8
    assert {row["pf"] for row in failures} == {"two_term_center"}
    assert {row["model"] for row in failures} == {"two_term"}
