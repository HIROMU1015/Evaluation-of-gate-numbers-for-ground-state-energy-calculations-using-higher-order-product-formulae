"""Regression tests for the T-depth rotation-synthesis optimum."""

from __future__ import annotations

import inspect

import pytest

from trotterlib import cost_extrapolation
from trotterlib.cost_validation import analytic_optimal_time


@pytest.mark.parametrize("order", [2, 4, 6, 8, 10])
def test_t_depth_optimum_uses_validated_power_law_formula(order: int) -> None:
    alpha = 1.7e-4
    epsilon_e = 1.5936001019904e-4

    actual = cost_extrapolation._t_depth_optimal_time(
        alpha, order, epsilon_e
    )
    expected = analytic_optimal_time(alpha, order, epsilon_e)
    legacy_wrong = (epsilon_e / alpha * (order + 1)) ** (1.0 / order)

    assert actual == pytest.approx(expected, rel=2e-15)
    assert actual != pytest.approx(legacy_wrong, rel=1e-12)


def test_both_t_depth_plot_paths_call_the_shared_optimum() -> None:
    source = inspect.getsource(cost_extrapolation)

    assert source.count("t = _t_depth_optimal_time(coeff, expo, target_error)") == 2
    assert "(target_error / coeff * (expo + 1))**(1/expo)" not in source
