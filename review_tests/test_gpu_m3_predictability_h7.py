import numpy as np

from run_gpu_m3_predictability_h7 import (
    _analytic_time,
    _fixed_order_alpha,
    _sequence,
    _summarize_points,
)


def test_frozen_m3_sequence_is_palindromic() -> None:
    weights = [-0.47, 0.33, 0.21, 0.20]
    sequence = _sequence(weights)
    assert sequence == [0.20, 0.21, 0.33, -0.47, 0.33, 0.21, 0.20]
    np.testing.assert_allclose(sequence, sequence[::-1])


def test_fixed_order_fit_and_analytic_time() -> None:
    times = np.asarray([0.06, 0.08, 0.11, 0.13])
    alpha = 2.3e-5
    fitted = _fixed_order_alpha(times, alpha * times**4)
    assert np.isclose(fitted, alpha, rtol=2e-15)
    assert np.isclose(alpha * _analytic_time(alpha) ** 4, 0.00015936001019904 / 5)


def test_summary_uses_frozen_ten_percent_and_cost_rules() -> None:
    points = []
    for relative_time, ratio, cost in [
        (0.1, 1.0, 200.0), (0.3, 1.0, 140.0), (0.5, 1.0, 115.0),
        (0.7, 0.99, 102.0), (0.9, 0.96, 97.0), (1.0, 0.95, 95.0),
        (1.1, 0.91, 96.0), (1.2, 0.88, 104.0), (1.4, 0.80, 160.0),
    ]:
        points.append(
            {
                "relative_time": relative_time, "time": relative_time,
                "direct_to_model_ratio": ratio, "direct_cost": cost,
                "signed_direct_shift_hartree": -ratio,
                "ground_overlap_probability": 0.999,
                "overlap_with_previous_probability": None if relative_time == 0.1 else 0.998,
                "eigenpair_residual_2_norm": 1e-13,
                "maximum_ground_overlap_branch": {"same_as_selected": True},
            }
        )
    summary = _summarize_points(points, model_cost=96.0)
    assert summary["ten_percent_validity"]["t_pass_over_t_ana"] == 1.1
    assert summary["ten_percent_validity"]["t_fail_over_t_ana"] == 1.2
    assert summary["grid_minimum_cost"]["relative_time"] == 1.0
    assert summary["passed"]
