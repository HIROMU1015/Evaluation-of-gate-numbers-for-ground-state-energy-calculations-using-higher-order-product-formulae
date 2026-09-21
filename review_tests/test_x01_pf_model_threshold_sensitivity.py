"""Regression tests for the X01 A03/A04 saved-result analysis."""

from __future__ import annotations

from collections import defaultdict

import analyze_x01_pf_model_threshold_sensitivity as analysis


def test_factorial_design_and_canonical_counts() -> None:
    result = analysis.run_analysis()
    assert result["condition_count"] == 17
    assert result["analysis_cluster_count"] == 5
    assert result["factorial_row_count"] == 6
    assert result["paired_effect_row_count"] == 850
    assert result["threshold_sensitivity_row_count"] == 312
    assert result["threshold_pairwise_row_count"] == 156
    assert result["source_audit_reproduction"] == {
        "fixed_comparison_rows": 102,
        "matching_metric_rows": 102,
        "matching_pass_rows": 102,
    }
    assert result["factorial_design_validation"] == {
        "condition_pf_record_count": 34,
        "common_training_points_relative_to_t_ana": [0.1, 0.2, 0.3],
        "refit_one_term_vs_two_term_same_normalized_loss": True,
        "original_one_term_is_legacy_perturbative_fit": True,
    }
    assert result["canonical_pass_counts"] == {
        "current_m3/original_one_term": 3,
        "current_m3/refit_one_term": 3,
        "current_m3/two_term": 16,
        "two_term_center/original_one_term": 11,
        "two_term_center/refit_one_term": 12,
        "two_term_center/two_term": 17,
    }


def test_one_at_a_time_threshold_curves_recover_canonical_and_are_monotone() -> None:
    result = analysis.run_analysis()
    expected = result["canonical_pass_counts"]
    grouped: dict[tuple[str, str, str], list[tuple[float, int]]] = defaultdict(list)
    for row in result["_sensitivity_rows"]:
        key = (row["varied_metric"], row["pf"], row["model"])
        grouped[key].append((float(row["threshold_multiplier"]), int(row["passed"])))
        if float(row["threshold_multiplier"]) == 1.0:
            assert int(row["passed"]) == expected[f"{row['pf']}/{row['model']}"]
    assert len(grouped) == len(analysis.METRICS) * len(analysis.PFS) * len(
        analysis.MODELS
    )
    for values in grouped.values():
        counts = [count for _, count in sorted(values)]
        assert counts == sorted(counts)


def test_lih_baseline_two_term_failure_is_not_single_threshold_boundary() -> None:
    result = analysis.run_analysis()
    failure = next(
        row
        for row in result["_failure_rows"]
        if row["condition"] == "LiH_CAS2e4o"
        and row["pf"] == "current_m3"
        and row["model"] == "two_term"
    )
    assert failure["canonical_pass"] is False
    assert failure["failed_metric_count"] == 4
    assert set(failure["failed_metrics"].split(";")) == set(analysis.METRICS)

    new = next(
        row
        for row in result["_failure_rows"]
        if row["condition"] == "LiH_CAS2e4o"
        and row["pf"] == "two_term_center"
        and row["model"] == "two_term"
    )
    assert new["canonical_pass"] is True
    assert new["failed_metric_count"] == 0
