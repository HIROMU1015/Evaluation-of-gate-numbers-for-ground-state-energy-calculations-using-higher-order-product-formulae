"""Regression tests for the X01 A08 simple-alternative comparison."""

from __future__ import annotations

import math

import analyze_x01_simple_alternatives as analysis


def _summaries() -> tuple[dict, dict[str, dict]]:
    result = analysis.run_analysis()
    summaries = {
        row["strategy_id"]: row for row in result["strategy_summary_rows"]
    }
    return result, summaries


def test_all_simple_strategies_cover_the_same_saved_conditions() -> None:
    result, summaries = _summaries()
    assert result["condition_count"] == 17
    assert result["strategy_count"] == 7
    assert result["strategy_row_count"] == 119
    assert result["truth_free_current_two_term_winner_count"] == 17
    assert result["higher_order_status"].startswith("not compared")
    assert all(row["condition_count"] == 17 for row in summaries.values())
    assert all(row["saved_condition_passed"] == 17 for row in summaries.values())


def test_prefixed_safety_rules_reproduce_cost_tradeoffs() -> None:
    _, summaries = _summaries()
    current = summaries["current_two_term_tstar"]
    margin = summaries["current_two_term_plus_1pct_budget"]
    cap = summaries["current_two_term_time_cap_0p9"]
    new_margin = summaries["new_two_term_plus_1pct_budget"]

    assert current["equal_one_run_basket_cost_ratio"] == 1.0
    assert math.isclose(margin["equal_one_run_basket_cost_ratio"], 1.01)
    assert 1.02 < cap["equal_one_run_basket_cost_ratio"] < 1.023
    assert cap["conditions_selecting_nonunit_relative_time"] == 17
    assert 1.15 < new_margin["equal_one_run_basket_cost_ratio"] < 1.19
    assert current["base_calibration_points_over_17"] == 137
    assert new_margin["base_calibration_points_over_17"] == 136


def test_direct_point_search_is_labeled_and_only_changes_lih_locally() -> None:
    result, summaries = _summaries()
    one = summaries["current_one_direct_check_tstar"]
    local = summaries["current_three_point_local_search"]
    full = summaries["current_full_saved_grid_oracle_reference"]

    assert one["validation_truth_used_for_decision"] is True
    assert one["extra_direct_diagnostic_points_over_17"] == 17
    assert local["validation_truth_used_for_decision"] is True
    assert local["extra_direct_diagnostic_points_over_17"] == 51
    assert local["conditions_selecting_nonunit_relative_time"] == 1
    assert full["validation_truth_used_for_decision"] is True
    assert full["extra_direct_diagnostic_points_over_17"] == 117

    rows = result["_strategy_rows"]
    lih_local = next(
        row
        for row in rows
        if row["condition"] == "LiH_CAS2e4o"
        and row["strategy_id"] == "current_three_point_local_search"
    )
    lih_full = next(
        row
        for row in rows
        if row["condition"] == "LiH_CAS2e4o"
        and row["strategy_id"] == "current_full_saved_grid_oracle_reference"
    )
    assert lih_local["selected_relative_to_t_star"] == 1.1
    assert math.isclose(
        lih_local["quantum_cost_ratio_to_current_two_term_t_star"],
        0.9139908669976377,
    )
    assert lih_full["selected_relative_to_t_star"] == 1.2
    assert math.isclose(
        lih_full["quantum_cost_ratio_to_current_two_term_t_star"],
        0.6826582816383985,
    )


def test_higher_order_baseline_is_not_mixed_from_other_conditions() -> None:
    result = analysis.run_analysis()
    availability = {row["baseline"]: row for row in result["availability_rows"]}
    higher = availability["one-order-higher PF"]
    assert higher["status"] == "not compared"
    assert higher["same_hamiltonians"] is False
    assert "no complete sixth- or higher-order result" in higher[
        "reason_if_unavailable"
    ]
