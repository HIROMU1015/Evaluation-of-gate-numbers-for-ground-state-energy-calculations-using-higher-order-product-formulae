from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "review_response"
    / "refine_m3_m5_valid_cost.py"
)
SPEC = importlib.util.spec_from_file_location("valid_cost_refinement", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _point(ratio: float, model_ratio: float, cost: float) -> dict:
    return {
        "relative_time": ratio,
        "direct_to_model_ratio": model_ratio,
        "direct_cost": cost,
    }


class FakeEvaluator:
    def __init__(self, function, initial=()):
        self.function = function
        self.points = {
            MODULE._ratio_key(point["relative_time"]): point for point in initial
        }

    def evaluate(self, ratio, reason):
        key = MODULE._ratio_key(ratio)
        if key not in self.points:
            self.points[key] = self.function(float(ratio))
        return self.points[key]

    def point(self, ratio):
        return self.points[MODULE._ratio_key(ratio)]

    def all_points(self):
        return sorted(self.points.values(), key=lambda point: point["relative_time"])


def test_m5_boundary_is_directly_bracketed_to_one_percent():
    def function(ratio):
        # The direct/model ratio reaches 0.9 at r=0.625 exactly.
        return _point(ratio, 1.0 - 0.16 * ratio, 10.0 - ratio)

    initial = [function(ratio) for ratio in MODULE.base.RELATIVE_TIMES]
    result = MODULE._m5_refinement(FakeEvaluator(function, initial))
    assert result["right_censored"] is False
    assert result["last_directly_confirmed_pass"]["relative_time"] <= 0.625
    assert result["first_directly_confirmed_fail"]["relative_time"] > 0.625
    assert result["bracket_width_over_t_ana"] <= 0.01
    assert result["C_valid_star"]["relative_time"] == result[
        "last_directly_confirmed_pass"
    ]["relative_time"]


def test_m3_adaptive_minimum_has_one_percent_neighbors():
    def function(ratio):
        return _point(ratio, 0.96, 100.0 + (ratio - 1.01) ** 2)

    initial = [function(ratio) for ratio in MODULE.base.RELATIVE_TIMES]
    result = MODULE._m3_refinement(FakeEvaluator(function, initial))
    assert result["t_star"]["relative_time"] == 1.01
    assert result["resolution_over_t_ana"] == 0.01
    assert result["t_star_is_ten_percent_valid"] is True
