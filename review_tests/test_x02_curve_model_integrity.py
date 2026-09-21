"""Unit tests for the shared finite-time curve/model audit."""

from __future__ import annotations

import numpy as np
import pytest

import audit_x02_curve_model_integrity as audit


def test_scaled_even_power_fit_recovers_three_known_coefficients() -> None:
    times = np.asarray([0.11, 0.19, 0.27, 0.38, 0.51])
    expected = np.asarray([2.3e-4, -7.1e-5, 1.9e-5])
    values = sum(
        coefficient * times ** (4 + 2 * index)
        for index, coefficient in enumerate(expected)
    )

    model = audit._fit_signed_coefficients(times, values, 4, 3)

    assert model["coefficients"] == pytest.approx(expected, rel=2e-10)
    assert audit._model_prediction(model, times) == pytest.approx(values, rel=2e-12)
    assert model["scaled_design_condition_number"] < model[
        "raw_design_condition_number"
    ]


def test_infeasible_model_cost_is_not_clipped_to_a_finite_value() -> None:
    result = audit._sampled_model_optimum([1e-2], 4, (0.5, 2.0))

    assert result["status"] == "infeasible_error_budget"
    assert result["minimum_cost"] is None
    assert result["feasible_point_count"] == 0


def test_synthetic_zero_boundary_and_near_zero_controls_pass() -> None:
    rows = audit.evaluate_synthetic_controls()

    assert len(rows) == 4
    assert all(row["passed"] for row in rows)
    index = {row["case_id"]: row for row in rows}
    assert index["two_roots"]["root_bracket_count"] >= 2
    assert index["upper_boundary"]["boundary_minimum"] is True
    assert index["near_zero_leading"]["leading_only_analytic_time"] > 2.0


def test_earliest_qualified_window_is_selected() -> None:
    times = np.geomspace(0.02, 1.8, 34)
    errors = 3.0e-4 * times**4

    selected, windows = audit._earliest_qualified_window(times, errors, 4)

    assert windows
    assert selected is not None
    assert selected["start_index"] == 0
    assert selected["free_order"] == pytest.approx(4.0, abs=1e-12)


def test_noise_floor_sign_flips_are_not_counted_as_resolved_roots() -> None:
    values = np.asarray([1e-14, -2e-14, 1e-8, -2e-8])

    assert audit._sign_change_count(values) == 3
    assert audit._resolved_sign_change_count(values) == 1
