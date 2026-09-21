"""Regression tests for the X01 A07 saved cost-benefit audit."""

from __future__ import annotations

import math

import analyze_x01_cost_benefit as analysis


def test_saved_calibration_counts_and_timing_scope() -> None:
    result = analysis.run_analysis()
    assert result["condition_count"] == 17
    assert result["analysis_cluster_count"] == 5
    assert result["calibration_row_count"] == 34
    assert result["strategy_row_count"] == 102
    assert result["paired_two_term_row_count"] == 17
    assert result["raw_source_count"] == 17

    calibration = result["_calibration_rows"]
    assert {row["direct_fit_point_count"] for row in calibration} == {3}
    exceptions = [
        row for row in calibration if row["short_time_proxy_point_count"] != 5
    ]
    assert len(exceptions) == 1
    assert exceptions[0]["condition"] == "LiH_CAS2e4o"
    assert exceptions[0]["pf"] == "current_m3"
    assert exceptions[0]["short_time_proxy_point_count"] == 6


def test_current_two_term_is_lower_quantum_cost_at_equal_saved_success() -> None:
    result = analysis.run_analysis()
    summaries = {
        (row["pf"], row["model"]): row
        for row in result["strategy_summary_rows"]
    }
    current = summaries[("current_m3", "two_term")]
    new = summaries[("two_term_center", "two_term")]
    assert current["margin_adjusted_passed_on_saved_conditions"] == 17
    assert new["margin_adjusted_passed_on_saved_conditions"] == 17
    assert current["total_calibration_points_over_17_conditions"] == 137
    assert new["total_calibration_points_over_17_conditions"] == 136
    assert current["direct_fit_points_over_17_conditions"] == 51
    assert new["direct_fit_points_over_17_conditions"] == 51
    assert new["minimum_quantum_cost_ratio_to_current_m3_two_term"] > 1.14
    assert new["maximum_quantum_cost_ratio_to_current_m3_two_term"] < 1.18
    assert math.isclose(
        new["equal_one_run_basket_cost_ratio_to_current_m3_two_term"],
        1.1498052390514166,
    )
    assert all(
        float(row["margin_adjusted_quantum_cost_ratio_new_over_current"]) > 1.0
        for row in result["_paired_rows"]
    )


def test_aggregate_amortization_has_no_saved_break_even() -> None:
    result = analysis.run_analysis()
    for row in result["amortization_rows"]:
        assert row["quantum_cost_ratio_new_over_current"] > 1.0
        assert row["calibration_seconds_new_minus_current"] > 0.0
        assert row["aggregate_dominance"].startswith("current_m3")
        assert row["current_m3_amortized_calibration_seconds_per_run"] < row[
            "two_term_center_amortized_calibration_seconds_per_run"
        ]
