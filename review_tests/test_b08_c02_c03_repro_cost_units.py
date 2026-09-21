"""Regression tests for the combined B08/C02/C03 audit."""

from __future__ import annotations

import pytest

import audit_b08_c02_c03_repro_cost_units as audit


@pytest.fixture(scope="module")
def result() -> dict:
    return audit.run_analysis()


def test_overall_status_reports_findings_without_hiding_completion(result: dict) -> None:
    assert result["status"] == "complete_with_findings"
    assert result["component_status"] == {
        "B08": "complete_with_findings",
        "C02": "complete",
        "C03": "complete",
    }


def test_b08_every_joint_candidate_condition_has_explicit_status(result: dict) -> None:
    summary = result["B08"]
    assert summary["joint_candidate_count"] == 387
    assert summary["joint_training_condition_count"] == 7
    assert summary["joint_expected_candidate_condition_count"] == 2709
    assert summary["joint_actual_completed_count"] == 572
    assert summary["joint_failed_count"] == 1
    assert summary["joint_censored_count"] == 2136
    assert summary["joint_missing_planned_count"] == 0
    assert summary["physical_accuracy_failure_count"] == 1


def test_b08_cache_archive_and_same_seed_reproduction_pass(result: dict) -> None:
    assert result["B08"]["all_cache_checks_passed"] is True
    assert result["B08"]["same_seed_reproduced_saved_candidates"] is True
    assert all(row["matched"] for row in result["_b08_cache_rows"])


def test_b08_records_metadata_gap_and_fixed_pytest_discovery(result: dict) -> None:
    summary = result["B08"]
    assert summary["metadata_complete_for_all_datasets"] is False
    assert summary["default_pytest_discovery_is_misconfigured"] is False
    assert summary["configured_testpaths"] == ["review_tests"]
    assert summary["review_test_file_count"] >= 27
    discovery = {
        row["check_id"]: row
        for row in result["_b08_metadata_rows"]
        if "check_id" in row
    }
    assert discovery["configured_test_path_exists"]["passed"] is True
    assert discovery["review_tests_in_configured_testpaths"]["passed"] is True


def test_c02_analytic_optimum_matches_scalar_minimization_and_qpe_factor(
    result: dict,
) -> None:
    summary = result["C02"]
    assert summary["random_case_count"] == 24
    assert summary["random_cases_passed"] == 24
    assert summary["boundary_cases_passed"] == summary["boundary_case_count"]
    assert summary["maximum_time_relative_difference"] < 2e-8
    assert summary["maximum_qpe_factor_relative_difference"] < 2e-15
    assert summary["maximum_saved_joint_analytic_time_difference"] < 2e-15
    assert summary["phase_spacing_residual"] < 2e-15


def test_c02_confirms_tdepth_time_formula_remediation(result: dict) -> None:
    summary = result["C02"]
    assert summary["tdepth_time_formula_discrepancy_found"] is False
    assert summary["tdepth_wrong_time_expression_occurrence_count"] == 0
    assert summary["tdepth_corrected_helper_call_occurrence_count"] == 2
    impact = {row["formal_order"]: row for row in result["_c02_impact_rows"]}
    assert impact[4]["legacy_over_correct_time_ratio"] == pytest.approx(5**0.5)
    assert all(row["rotation_synthesis_t_depth_affected"] for row in impact.values())
    assert not any(row["qpe_iteration_factor_affected"] for row in impact.values())


def test_c02_requires_no_existing_figure_regeneration(result: dict) -> None:
    summary = result["C02"]
    assert summary["notebook_tdepth_function_call_count"] == 3
    assert summary["notebook_rz_layer_true_call_count"] == 3
    assert summary["existing_tdepth_figure_count"] == 0
    assert summary["existing_rz_figure_count"] >= 4
    assert summary["figure_regeneration_required"] is False
    assert not any(
        row["affected_by_optimal_time_fix"]
        for row in result["_c02_figure_rows"]
    )


def test_c03_fixed_tables_and_hand_counts_reproduce(result: dict) -> None:
    summary = result["C03"]
    assert summary["formula_count"] == 8
    assert summary["system_count"] == 2
    assert summary["cost_unit_manifest_row_count"] == 16
    assert summary["fixed_table_pass_count"] == summary["fixed_table_check_count"]
    assert summary["maximum_pauli_table_absolute_difference"] == 0
    assert summary["maximum_rz_table_absolute_difference"] == 0
    assert summary["hand_examples_passed"] == summary["hand_example_count"]
    assert summary["maximum_qpe_total_relative_difference"] < 2e-15


def test_c03_cost_units_are_explicitly_distinct(result: dict) -> None:
    manifest = result["_c03_manifest_rows"]
    assert all(
        row["pauli_rotation_unit"] == "Pauli rotations / one PF unitary"
        for row in manifest
    )
    assert all(
        row["rz_layer_unit"] == "greedy RZ layers / one PF unitary"
        for row in manifest
    )
    assert result["C03"]["all_qpe_rows_keep_rotation_and_rz_units_distinct"] is True


def test_source_sentinels_are_present(result: dict) -> None:
    assert all(row["sentinel_present"] for row in result["_source_rows"])
