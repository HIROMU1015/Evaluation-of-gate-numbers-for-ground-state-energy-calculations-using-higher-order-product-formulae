"""Regression tests for the X01 A06 information-access audit."""

from __future__ import annotations

import audit_x01_information_access as analysis


def test_raw_pipeline_exact_state_dependencies_are_reproduced() -> None:
    result = analysis.run_analysis()
    dependency = result["dependency_audit"]
    assert dependency["raw_condition_count"] == 17
    assert dependency["formula_condition_count"] == 34
    assert dependency["short_time_error_definition_match_count"] == 34
    assert dependency["evaluated_short_time_point_count"] == 171
    assert dependency["selected_short_time_window_point_count"] == 170
    assert dependency["training_direct_point_count"] == 102
    assert dependency["local_validation_direct_point_count"] == 236
    assert dependency["exact_ground_overlap_selection_rule_count"] == 338
    assert dependency["all_short_time_definitions_match"] is True
    assert dependency["all_direct_branch_rules_match"] is True
    assert dependency["runner_exact_state_overlap_dependency_confirmed"] is True
    assert dependency["runner_exact_energy_phase_rotation_dependency_confirmed"] is True


def test_oracle_assisted_calibrated_selector_matches_saved_oracle_choices() -> None:
    result = analysis.run_analysis()
    assert result["condition_count"] == 17
    assert result["calibrated_selector_choice_count"] == 17
    assert result["calibrated_selector_current_m3_count"] == 17
    assert result["calibrated_selector_oracle_agreement_count"] == 17
    assert result["calibrated_selector_strict_frozen_pass_count"] == 17
    assert result["maximum_calibrated_selection_regret"] == 0.0
    assert all(
        row["calibrated_selector_pf"] == "current_m3"
        and row["oracle_candidate_schedule_pf"] == "current_m3"
        and row["selected_strict_frozen_budget_pass"]
        for row in result["_selection_rows"]
    )


def test_practical_and_transfer_tiers_remain_unmeasured() -> None:
    result = analysis.run_analysis()
    tiers = {row["tier"]: row for row in result["performance_tier_rows"]}
    assert tiers["2_practical_target_calibration"]["conditions_scored"] == 0
    assert tiers["3_transfer_only"]["conditions_scored"] == 0
    assert result["practical_target_calibration_status"].startswith("not implemented")
    assert result["transfer_only_status"].startswith("not implemented")

    information = {row["information_id"]: row for row in result["_information_rows"]}
    for key in ("I05", "I06", "I07", "I08", "I09", "I10"):
        assert information[key][
            "available_in_practical_target_calibration_without_exact_state"
        ] is False
        assert information[key]["available_in_transfer_only"] is False
    for key in ("I11", "I12", "I13", "I14"):
        assert information[key]["used_only_for_scoring"] is True
