from __future__ import annotations

import json
from pathlib import Path

import pytest

from review_response.audit_d03_target_accuracy_dependence import (
    consolidate_direct_points,
    direct_minimum_bracket,
    leading_analytic_time,
    model_prediction,
    optimize_model,
    qpe_cost,
)


def test_qpe_cost_and_infeasible_budget() -> None:
    cost = qpe_cost(0.5, 2.0e-5, 100, 1.0e-4, 1.2)
    assert cost == pytest.approx(3.0e6)
    assert qpe_cost(0.5, 1.0e-4, 100, 1.0e-4, 1.2) is None
    assert qpe_cost(0.5, 1.1e-4, 100, 1.0e-4, 1.2) is None


def test_leading_analytic_time_scaling() -> None:
    base = leading_analytic_time(0.25, 4, 1.0e-4)
    tighter = leading_analytic_time(0.25, 4, 1.0e-5)
    looser = leading_analytic_time(0.25, 4, 1.0e-3)
    assert tighter / base == pytest.approx(10.0 ** (-0.25))
    assert looser / base == pytest.approx(10.0 ** 0.25)


def test_model_optimization_matches_one_term_solution() -> None:
    epsilon = 1.0e-4
    alpha = 0.2
    analytic = leading_analytic_time(alpha, 4, epsilon)
    model = {"coefficient_powers": [4], "coefficient_values": [alpha]}
    result = optimize_model(model, analytic, 50, epsilon, 1.2, [0.5, 1.5], 10001)
    assert result["model_status"] == "complete"
    assert result["model_time"] == pytest.approx(analytic, rel=2e-4)
    assert model_prediction(model, result["model_time"]) == pytest.approx(
        epsilon / 5.0, rel=1e-3
    )


def test_direct_minimum_requires_tight_neighbors() -> None:
    points = []
    for time_value, error in [(0.98, 2.2e-5), (1.0, 2.0e-5), (1.02, 2.2e-5)]:
        points.append(
            {
                "time": time_value,
                "absolute_direct_error_hartree": error,
                "signed_direct_shift_hartree": error,
            }
        )
    result = direct_minimum_bracket(points, 100, 1.0e-4, 1.2, 0.03)
    assert result["direct_grid_minimum_bracketed"] is True
    sparse = direct_minimum_bracket(
        [points[0], points[1], {**points[2], "time": 1.2}],
        100,
        1.0e-4,
        1.2,
        0.03,
    )
    assert sparse["direct_grid_minimum_bracketed"] is False


def test_point_consolidation_deduplicates_sources() -> None:
    point = {
        "time": 0.25,
        "signed_direct_shift_hartree": -2.0e-5,
        "ground_overlap_probability": 0.99,
        "eigenpair_residual_2_norm": 1.0e-14,
    }
    raw = {
        "training_direct_points": [point],
        "models": {"m": {"direct_validation_points": [dict(point)]}},
    }
    fine = {"computed_points": [dict(point)], "reused_points": []}
    result = consolidate_direct_points(raw, fine)
    assert len(result) == 1
    assert result[0]["used_for_original_training"] is True
    assert set(result[0]["sources"]) == {
        "training_direct_points",
        "stage1:m",
        "stage2_computed",
    }


def test_protocol_targets_and_scope_are_frozen() -> None:
    path = Path(__file__).parents[1] / "review_response" / "d03_target_accuracy_dependence_protocol.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    assert protocol["target_errors_hartree"] == {
        "CA": pytest.approx(1.5936001019904e-3),
        "CA_div_10": pytest.approx(1.5936001019904e-4),
        "CA_div_100": pytest.approx(1.5936001019904e-5),
    }
    assert protocol["scope_limits"]["new_direct_points_in_this_local_audit"] == 0
    assert protocol["direct_curve_coverage"]["interpolation_forbidden"] is True
