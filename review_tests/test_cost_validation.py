from __future__ import annotations

import numpy as np
import pytest

from trotterlib.cost_validation import (
    analytic_minimum_cost,
    analytic_optimal_time,
    combined_time_grid,
    discrete_minimum,
    measured_cost_curve,
    power_law_validity_intervals,
)


def test_combined_time_grid_unions_and_sorts_points() -> None:
    times = combined_time_grid(
        0.1,
        3.0,
        4,
        grid_kind="geometric",
        dense_t_start=2.0,
        dense_t_stop=2.4,
        dense_num_times=3,
        include_times=[2.25],
    )

    assert np.all(np.diff(times) > 0)
    assert times[0] == pytest.approx(0.1)
    assert times[-1] == pytest.approx(3.0)
    assert 2.2 in times
    assert 2.25 in times


def test_analytic_optimum_matches_sampled_cost_minimum() -> None:
    alpha = 2.5e-6
    order = 4
    epsilon = 1.6e-4
    optimum = analytic_optimal_time(alpha, order, epsilon)
    times = np.array([0.9 * optimum, optimum, 1.1 * optimum])
    errors = alpha * times**order
    costs = measured_cost_curve(
        times, errors, beta=1.2, n_exp=100, epsilon_e=epsilon
    )
    sampled = discrete_minimum(times, costs)

    assert sampled is not None
    assert sampled["time"] == pytest.approx(optimum)
    assert sampled["value"] == pytest.approx(
        analytic_minimum_cost(1.2, 100, alpha, order, epsilon)
    )


def test_measured_cost_masks_exhausted_error_budget() -> None:
    costs = measured_cost_curve(
        np.array([1.0, 2.0]),
        np.array([1e-4, 2e-4]),
        beta=1.2,
        n_exp=10,
        epsilon_e=1.5e-4,
    )

    assert np.isfinite(costs[0])
    assert np.isnan(costs[1])


def test_power_law_validity_returns_consecutive_intervals() -> None:
    times = np.arange(1.0, 7.0)
    model = 2e-6 * times**4
    errors = model.copy()
    errors[0] = 1e-15
    errors[4] *= 1.2

    deviations, intervals = power_law_validity_intervals(
        times,
        errors,
        alpha=2e-6,
        order=4,
        noise_floor=1e-12,
        relative_tolerance=0.05,
    )

    assert np.isnan(deviations[0])
    assert [(entry["t_start"], entry["t_stop"]) for entry in intervals] == [
        (2.0, 4.0),
        (6.0, 6.0),
    ]
