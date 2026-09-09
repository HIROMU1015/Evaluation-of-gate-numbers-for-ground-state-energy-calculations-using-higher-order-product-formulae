"""Compare one- and two-term finite-time error models for saved PF probes."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from trotterlib.config import BETA, TARGET_ERROR


TRAINING_MAXIMUM_RELATIVE_TIME = 0.30
MODEL_OPTIMIZATION_INTERVAL = (0.10, 1.40)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    epsilon = float(TARGET_ERROR)
    if time_value <= 0.0 or error >= epsilon:
        return None
    return float(BETA * int(rotations) / (time_value * (epsilon - error)))


def _fit_record(
    source: Path,
    system: dict[str, Any],
    formula_name: str,
    formula: dict[str, Any],
) -> dict[str, Any]:
    points = sorted(formula["direct_points"], key=lambda point: point["relative_time"])
    training = [
        point
        for point in points
        if float(point["relative_time"])
        <= TRAINING_MAXIMUM_RELATIVE_TIME + 1e-12
    ]
    if len(training) < 3:
        raise ValueError(f"{source}:{formula_name} has too few training points")
    formal_order = int(formula.get("formal_order", 4))
    alpha = float(formula["alpha"])
    analytic_time = float(formula["analytic_time"])
    rotations = int(formula["rotations_per_pf_step"])
    leading_sign = float(
        np.sign(
            np.median(
                [float(point["signed_direct_shift_hartree"]) for point in training]
            )
        )
    )
    if leading_sign == 0.0:
        raise ValueError(f"{source}:{formula_name} has zero leading sign")

    relative_training = np.asarray(
        [float(point["relative_time"]) for point in training]
    )
    absolute_training = np.asarray([float(point["time"]) for point in training])
    shifts = np.asarray(
        [float(point["signed_direct_shift_hartree"]) for point in training]
    )
    normalized = shifts / (
        leading_sign * alpha * np.power(absolute_training, formal_order)
    )
    design = np.column_stack(
        [np.ones_like(relative_training), np.square(relative_training)]
    )
    b0, b2 = np.linalg.lstsq(design, normalized, rcond=None)[0]
    b0 = float(b0)
    b2 = float(b2)

    predictions: list[dict[str, Any]] = []
    for point in points:
        relative_time = float(point["relative_time"])
        time_value = float(point["time"])
        signed_prediction = (
            leading_sign
            * alpha
            * time_value**formal_order
            * (b0 + b2 * relative_time**2)
        )
        predicted_error = abs(float(signed_prediction))
        actual_error = float(point["direct_error_hartree"])
        predictions.append(
            {
                "relative_time": relative_time,
                "time": time_value,
                "actual_error_hartree": actual_error,
                "one_term_model_error_hartree": float(
                    alpha * time_value**formal_order
                ),
                "two_term_model_error_hartree": predicted_error,
                "two_term_signed_residual_hartree": float(
                    float(point["signed_direct_shift_hartree"])
                    - signed_prediction
                ),
                "two_term_residual_over_epsilon": float(
                    abs(float(point["signed_direct_shift_hartree"]) - signed_prediction)
                    / float(TARGET_ERROR)
                ),
                "actual_cost": point["direct_cost"],
                "two_term_model_cost": _cost(time_value, predicted_error, rotations),
                "used_for_fit": relative_time
                <= TRAINING_MAXIMUM_RELATIVE_TIME + 1e-12,
            }
        )

    schedule = next(
        point for point in predictions if abs(point["relative_time"] - 1.0) < 1e-12
    )
    one_term_schedule_ratio = next(
        float(point["direct_to_model_ratio"])
        for point in points
        if abs(float(point["relative_time"]) - 1.0) < 1e-12
    )
    two_term_schedule_ratio = float(
        schedule["two_term_model_error_hartree"]
        / schedule["actual_error_hartree"]
    )
    two_term_schedule_cost_error = None
    if schedule["actual_cost"] is not None and schedule["two_term_model_cost"] is not None:
        two_term_schedule_cost_error = float(
            abs(schedule["two_term_model_cost"] - schedule["actual_cost"])
            / schedule["actual_cost"]
        )

    relative_dense = np.linspace(
        MODEL_OPTIMIZATION_INTERVAL[0], MODEL_OPTIMIZATION_INTERVAL[1], 20001
    )
    time_dense = relative_dense * analytic_time
    signed_dense = (
        leading_sign
        * alpha
        * np.power(time_dense, formal_order)
        * (b0 + b2 * np.square(relative_dense))
    )
    costs_dense = np.full(relative_dense.shape, np.inf)
    errors_dense = np.abs(signed_dense)
    valid = errors_dense < float(TARGET_ERROR)
    costs_dense[valid] = (
        float(BETA)
        * rotations
        / (time_dense[valid] * (float(TARGET_ERROR) - errors_dense[valid]))
    )
    minimum_index = int(np.argmin(costs_dense))

    direct_grid = [
        point
        for point in predictions
        if 0.20 <= point["relative_time"] <= 1.20
        and point["actual_cost"] is not None
    ]
    direct_grid_minimum = min(direct_grid, key=lambda point: point["actual_cost"])
    validation = [
        point
        for point in predictions
        if TRAINING_MAXIMUM_RELATIVE_TIME < point["relative_time"] <= 1.20
    ]
    return {
        "source": str(source),
        "system": system,
        "formula": formula_name,
        "formal_order": formal_order,
        "weights": formula["weights"],
        "s2_stage_count": int(formula["s2_stage_count"]),
        "rotations_per_pf_step": rotations,
        "alpha": alpha,
        "analytic_time_one_term": analytic_time,
        "one_term_model_cost": float(formula["analytic_model_cost"]),
        "fit": {
            "training_maximum_relative_time": TRAINING_MAXIMUM_RELATIVE_TIME,
            "leading_sign": leading_sign,
            "normalized_b0": b0,
            "normalized_b2": b2,
            "next_order_over_leading": float(
                b2 / (b0 * analytic_time**2)
            ),
            "rho_next_at_one_term_analytic_time": float(abs(b2 / b0)),
        },
        "one_term_schedule": {
            "actual_to_model_error_ratio": one_term_schedule_ratio,
            "absolute_error_ratio_deviation": abs(one_term_schedule_ratio - 1.0),
            "cost_relative_error": formula["summary"]["eta_schedule"],
        },
        "two_term_schedule": {
            "model_to_actual_error_ratio": two_term_schedule_ratio,
            "absolute_error_ratio_deviation": abs(two_term_schedule_ratio - 1.0),
            "cost_relative_error": two_term_schedule_cost_error,
        },
        "two_term_model_optimum": {
            "relative_to_one_term_analytic_time": float(
                relative_dense[minimum_index]
            ),
            "time": float(time_dense[minimum_index]),
            "cost": float(costs_dense[minimum_index]),
        },
        "direct_grid_minimum": {
            "relative_to_one_term_analytic_time": direct_grid_minimum[
                "relative_time"
            ],
            "time": direct_grid_minimum["time"],
            "cost": direct_grid_minimum["actual_cost"],
        },
        "maximum_two_term_residual_over_epsilon_validation": float(
            max(point["two_term_residual_over_epsilon"] for point in validation)
        ),
        "predictions": predictions,
        "maximum_eigenpair_residual_2_norm": max(
            float(point["eigenpair_residual_2_norm"]) for point in points
        ),
        "minimum_ground_overlap_probability": min(
            float(point["ground_overlap_probability"]) for point in points
        ),
    }


def _aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_formula: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_formula[record["formula"]].append(record)
    aggregates = {}
    for formula_name, rows in sorted(by_formula.items()):
        aggregates[formula_name] = {
            "record_count": len(rows),
            "formal_order": rows[0]["formal_order"],
            "s2_stage_count": rows[0]["s2_stage_count"],
            "maximum_one_term_schedule_error_ratio_deviation": max(
                row["one_term_schedule"]["absolute_error_ratio_deviation"]
                for row in rows
            ),
            "maximum_two_term_schedule_error_ratio_deviation": max(
                row["two_term_schedule"]["absolute_error_ratio_deviation"]
                for row in rows
            ),
            "maximum_one_term_schedule_cost_relative_error": max(
                row["one_term_schedule"]["cost_relative_error"]
                for row in rows
                if row["one_term_schedule"]["cost_relative_error"] is not None
            ),
            "maximum_two_term_schedule_cost_relative_error": max(
                row["two_term_schedule"]["cost_relative_error"]
                for row in rows
                if row["two_term_schedule"]["cost_relative_error"] is not None
            ),
            "maximum_two_term_residual_over_epsilon_validation": max(
                row["maximum_two_term_residual_over_epsilon_validation"]
                for row in rows
            ),
            "rho_next_range": [
                min(row["fit"]["rho_next_at_one_term_analytic_time"] for row in rows),
                max(row["fit"]["rho_next_at_one_term_analytic_time"] for row in rows),
            ],
        }
    return aggregates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sources: list[Path] = []
    for item in args.inputs:
        if item.is_dir():
            sources.extend(sorted(item.glob("*.json")))
        else:
            sources.append(item)
    records: list[dict[str, Any]] = []
    for source in sources:
        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("status") != "complete" or "system" not in payload:
            continue
        for formula_name, formula in payload.get("formulas", {}).items():
            if formula.get("status") != "complete":
                continue
            records.append(
                _fit_record(source, payload["system"], formula_name, formula)
            )
    if not records:
        raise RuntimeError("no completed formula records found")
    result = {
        "status": "complete",
        "method": {
            "signed_error_model": "a_p*t^p + a_(p+2)*t^(p+2)",
            "training_maximum_relative_time": TRAINING_MAXIMUM_RELATIVE_TIME,
            "normalization": "one-term analytic time and target epsilon_E",
            "model_optimization_interval_relative_to_one_term_time": (
                MODEL_OPTIMIZATION_INTERVAL
            ),
        },
        "aggregates": _aggregate(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
