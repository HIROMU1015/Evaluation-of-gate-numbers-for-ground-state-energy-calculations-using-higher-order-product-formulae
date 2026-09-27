from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_hchain_direct_optimal_time_scaling as runner


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads(
    (ROOT / "review_response/hchain_direct_optimal_time_scaling_protocol.json").read_text(
        encoding="utf-8"
    )
)


def _formula_result(*, boundary: bool = False) -> dict:
    grid = runner._grid_from_protocol(PROTOCOL)
    points = []
    for relative in grid:
        cost = 3.0 - relative if boundary else 1.0 + (relative - 1.1) ** 2
        shift = 1e-6 * (relative - 0.8)
        points.append(
            {
                "relative_to_analytic_time": relative,
                "time": 2.0 * relative,
                "unitarity_residual_frobenius_norm": 1e-12,
                "schur_off_diagonal_residual_frobenius_norm": 2e-12,
                "maximum_ground_overlap_branch": {
                    "energy_shift_hartree": shift,
                },
                "continuously_tracked_branch": {
                    "cost": cost,
                    "direct_error_hartree": abs(shift),
                    "unwrapped_energy_shift_hartree": shift,
                    "ground_overlap_probability": 0.999,
                    "overlap_with_previous_probability": (
                        None if relative == grid[0] else 0.998
                    ),
                },
            }
        )
    return {"analytic_optimal_time": 2.0, "points": points}


def _summary(time_value: float) -> dict:
    return {
        "status": "scorable",
        "t_grid_star": time_value,
        "near_optimal_component": {"well_localized": True},
    }


def test_protocol_grid_is_exact_and_complete() -> None:
    grid = runner._grid_from_protocol(PROTOCOL)
    assert len(grid) == 31
    assert grid[0] == pytest.approx(0.2)
    assert grid[-1] == pytest.approx(1.7)
    assert all(right - left == pytest.approx(0.05) for left, right in zip(grid, grid[1:]))


def test_formula_summary_selects_direct_interior_minimum() -> None:
    result = runner.summarize_formula(_formula_result(), PROTOCOL)
    assert result["status"] == "scorable"
    assert result["relative_t_grid_star"] == pytest.approx(1.1)
    assert result["t_grid_star"] == pytest.approx(2.2)
    assert result["zero_crossing_assisted_near_optimum"] is False
    assert all(result["gate_results"].values())


def test_boundary_minimum_is_not_scorable() -> None:
    result = runner.summarize_formula(_formula_result(boundary=True), PROTOCOL)
    assert result["status"] == "not_scorable_gate_failure"
    assert result["gate_results"]["interior_minimum"] is False


def test_power_law_leave_one_out_recovers_exact_relation() -> None:
    fit = runner._fit_power_law([2, 4, 6], [3.0, 6.0, 9.0])
    assert fit["a"] == pytest.approx(1.5)
    assert fit["b"] == pytest.approx(1.0)
    loo = runner._loo_predictions([2, 4, 6], [3.0, 6.0, 9.0], "power_law")
    assert loo["maximum_relative_error"] == pytest.approx(0.0, abs=1e-12)


def test_scaling_keeps_even_and_odd_families_separate() -> None:
    summaries = {
        "H2": {"m5": _summary(3.0)},
        "H4": {"m5": _summary(6.0)},
        "H6": {"m5": _summary(9.0)},
        "H5": {"m5": _summary(7.5)},
        "H7": {"m5": _summary(10.5)},
    }
    result = runner.scaling_summary("m5", summaries, PROTOCOL)
    assert result["primary_sizes"] == [2, 4, 6]
    assert result["secondary_sizes"] == [5, 7]
    assert result["decision"] == "small_system_predictable_requires_H8_holdout"
    assert result["secondary_role"] == "descriptive_two_point_trend_only"


def test_job_reuse_requires_protocol_identity_and_exact_scope() -> None:
    grid = runner._grid_from_protocol(PROTOCOL)
    payload = {
        "status": "complete",
        "relative_times": grid,
        "formula_keys": ["m5"],
        "results": {"H2": {}},
        "registered_protocol": {
            "sha256": "abc",
            "h_chain": 2,
            "formula_key": "m5",
        },
    }
    assert runner._job_matches(
        payload,
        protocol_sha256="abc",
        grid=grid,
        h_chain=2,
        formula_key="m5",
    )
    assert not runner._job_matches(
        payload,
        protocol_sha256="different",
        grid=grid,
        h_chain=2,
        formula_key="m5",
    )
