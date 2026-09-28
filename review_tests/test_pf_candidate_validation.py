from __future__ import annotations

import math
from pathlib import Path

import pf_candidate_validation as validation


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_positive_two_term_zero() -> None:
    model = {
        "coefficient_powers": [4, 6],
        "coefficient_values": [-4.0, 1.0],
    }
    assert validation.positive_two_term_zero(model) == 2.0
    assert validation.positive_two_term_zero(
        {"coefficient_powers": [4, 6], "coefficient_values": [4.0, 1.0]}
    ) is None
    assert validation.positive_two_term_zero(
        {"coefficient_powers": [2, 4], "coefficient_values": [-4.0, 1.0]}
    ) is None


def test_frozen_failure_ledger_and_coordinate_plan() -> None:
    result = validation.build_failure_ledger(PROJECT_ROOT)
    assert len(result["ledger"]) == 16
    assert len(result["coordinate_plan"]) == 10
    assert result["checks"]["selected_coordinate_counts_by_condition"] == {
        "LiF_active_eq_sto3g": 2,
        "LiF_active_stretch150_sto3g": 2,
        "HCl_full_eq_sto3g": 3,
        "HCl_full_stretch150_sto3g": 3,
    }
    assert result["checks"]["saved_selected_coordinate_proxy_count"] == 5
    assert result["checks"]["missing_selected_coordinate_proxy_count"] == 5
    assert result["checks"]["maximum_budget_identity_relative_error"] < 5e-15
    assert (
        result["checks"]["maximum_margin_identity_absolute_residual_hartree"]
        < 5e-18
    )


def test_guarded_error_is_the_budget_error_for_mwr() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "HCl_full_eq_sto3g"
        and item["strategy"] == "multiple_window_rule"
    )
    assert math.isclose(row["absolute_central_prediction_hartree"], 1.8864010878277525e-7)
    assert math.isclose(row["budget_error_used_hartree"], 6.4363245484305005e-6)
    assert row["guard_premium_over_central_hartree"] > 0.0


def test_unsafe_negative_frozen_budget_regret_is_not_safety() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "LiF_active_eq_sto3g"
        and item["strategy"] == "current_fallback"
    )
    assert row["unsafe_execution"] is True
    assert row["frozen_budget_regret"] < 0.0
    assert row["required_cost_over_frozen_budget"] > 1.8
    assert row["evidence_class"] == "post_hoc_truth_diagnostic"


def test_lif_equilibrium_zero_is_near_selected_time() -> None:
    rows = validation.build_failure_ledger(PROJECT_ROOT)["ledger"]
    row = next(
        item
        for item in rows
        if item["condition"] == "LiF_active_eq_sto3g"
        and item["strategy"] == "current_fallback"
    )
    assert math.isclose(
        row["original_model_positive_zero_hartree_inverse"],
        0.9329842669044777,
        rel_tol=0.0,
        abs_tol=2e-15,
    )
    assert row["distance_to_original_model_zero"] < 5e-6


def test_proxy_sign_convention() -> None:
    time_value = 0.2
    positive_shift = 1.0e-3
    negative_shift = -2.0e-3
    assert math.isclose(
        validation.proxy_signed_from_echo(
            math.sin(positive_shift * time_value), time_value
        ),
        math.sin(positive_shift * time_value) / time_value,
    )
    assert validation.proxy_signed_from_echo(
        math.sin(positive_shift * time_value), time_value
    ) > 0.0
    assert validation.proxy_signed_from_echo(
        math.sin(negative_shift * time_value), time_value
    ) < 0.0
    assert validation.proxy_signed_from_echo(0.0, time_value) == 0.0


def test_component_classification_is_fixed_and_cancellation_aware() -> None:
    single = validation.classify_components(
        {"model": 4.0, "state": 1.0, "proxy": 0.5}, 1.5
    )
    assert single["attribution"] == "model"
    assert single["material_by_original_budget_allowance"] == {
        "model": True,
        "state": False,
        "proxy": False,
    }
    mixed = validation.classify_components(
        {"model": 4.0, "state": -3.0, "proxy": 0.1}, 1.0
    )
    assert mixed["attribution"] == "mixed_or_none"
    assert mixed["largest_absolute_component"] == "model"
