from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def combined_time_grid(
    t_start: float,
    t_stop: float,
    num_times: int,
    *,
    grid_kind: str = "linear",
    dense_t_start: float | None = None,
    dense_t_stop: float | None = None,
    dense_num_times: int = 0,
    include_times: Sequence[float] = (),
) -> np.ndarray:
    """Combine a base linear/geometric grid with a dense local grid."""
    if t_start <= 0 or t_stop <= t_start:
        raise ValueError("Require 0 < t_start < t_stop")
    if num_times < 2:
        raise ValueError("num_times must be at least 2")
    if grid_kind not in {"linear", "geometric"}:
        raise ValueError("grid_kind must be either 'linear' or 'geometric'")

    base = (
        np.linspace(t_start, t_stop, num_times)
        if grid_kind == "linear"
        else np.geomspace(t_start, t_stop, num_times)
    )
    parts = [base]

    dense_values = (dense_t_start, dense_t_stop, dense_num_times)
    dense_requested = any(
        value not in (None, 0) for value in dense_values
    )
    if dense_requested:
        if dense_t_start is None or dense_t_stop is None or dense_num_times < 2:
            raise ValueError(
                "dense_t_start, dense_t_stop, and dense_num_times >= 2 "
                "must be provided together"
            )
        if not t_start <= dense_t_start < dense_t_stop <= t_stop:
            raise ValueError("The dense grid must lie inside the base interval")
        parts.append(np.linspace(dense_t_start, dense_t_stop, dense_num_times))

    included = np.asarray(include_times, dtype=float)
    if included.size:
        if not np.all(np.isfinite(included)) or np.any(included <= 0):
            raise ValueError("include_times must be finite and positive")
        if np.any(included < t_start) or np.any(included > t_stop):
            raise ValueError("include_times must lie inside the base interval")
        parts.append(included)

    return np.unique(np.concatenate(parts))


def analytic_optimal_time(alpha: float, order: int, epsilon_e: float) -> float:
    """Return the minimizer for alpha*t**order in the QPE cost model."""
    if alpha <= 0 or order < 1 or epsilon_e <= 0:
        raise ValueError("alpha, order, and epsilon_e must be positive")
    return float((epsilon_e / ((order + 1) * alpha)) ** (1.0 / order))


def analytic_minimum_cost(
    beta: float,
    n_exp: int,
    alpha: float,
    order: int,
    epsilon_e: float,
) -> float:
    """Return beta*Nexp/[t*(epsilon-e)] at the power-law optimum."""
    if beta <= 0 or n_exp <= 0:
        raise ValueError("beta and n_exp must be positive")
    optimum = analytic_optimal_time(alpha, order, epsilon_e)
    remaining_error = epsilon_e * order / (order + 1)
    return float(beta * n_exp / (optimum * remaining_error))


def measured_cost_curve(
    times: np.ndarray,
    errors: np.ndarray,
    *,
    beta: float,
    n_exp: int,
    epsilon_e: float,
) -> np.ndarray:
    """Evaluate the cost on measured points; invalid denominators are NaN."""
    times_array = np.asarray(times, dtype=float).ravel()
    errors_array = np.asarray(errors, dtype=float).ravel()
    if times_array.shape != errors_array.shape or times_array.size == 0:
        raise ValueError("times and errors must have the same nonzero size")
    if beta <= 0 or n_exp <= 0 or epsilon_e <= 0:
        raise ValueError("beta, n_exp, and epsilon_e must be positive")
    if not np.all(np.isfinite(times_array)) or np.any(times_array <= 0):
        raise ValueError("times must be finite and positive")

    costs = np.full(times_array.shape, np.nan)
    valid = np.isfinite(errors_array) & (errors_array >= 0) & (
        errors_array < epsilon_e
    )
    costs[valid] = beta * n_exp / (
        times_array[valid] * (epsilon_e - errors_array[valid])
    )
    return costs


def discrete_minimum(times: np.ndarray, values: np.ndarray) -> dict[str, Any] | None:
    """Return the smallest finite sampled value and its grid location."""
    times_array = np.asarray(times, dtype=float).ravel()
    values_array = np.asarray(values, dtype=float).ravel()
    if times_array.shape != values_array.shape or times_array.size == 0:
        raise ValueError("times and values must have the same nonzero size")
    finite = np.flatnonzero(np.isfinite(values_array))
    if finite.size == 0:
        return None
    index = int(finite[np.argmin(values_array[finite])])
    return {
        "index": index,
        "time": float(times_array[index]),
        "value": float(values_array[index]),
        "is_boundary_of_valid_grid": bool(index in (finite[0], finite[-1])),
    }


def power_law_validity_intervals(
    times: np.ndarray,
    errors: np.ndarray,
    *,
    alpha: float,
    order: int,
    noise_floor: float,
    relative_tolerance: float,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Return pointwise model deviations and consecutive valid intervals."""
    times_array = np.asarray(times, dtype=float).ravel()
    errors_array = np.asarray(errors, dtype=float).ravel()
    if times_array.shape != errors_array.shape or times_array.size == 0:
        raise ValueError("times and errors must have the same nonzero size")
    if alpha <= 0 or order < 1 or noise_floor < 0:
        raise ValueError("alpha/order must be positive and noise_floor non-negative")
    if not 0 < relative_tolerance < 1:
        raise ValueError("relative_tolerance must lie in (0, 1)")

    model = alpha * times_array**order
    deviations = np.full(times_array.shape, np.nan)
    reliable = np.isfinite(errors_array) & (errors_array > noise_floor)
    deviations[reliable] = np.abs(errors_array[reliable] / model[reliable] - 1.0)
    valid = reliable & (deviations <= relative_tolerance)

    intervals: list[dict[str, Any]] = []
    start: int | None = None
    for index, is_valid in enumerate(np.append(valid, False)):
        if is_valid and start is None:
            start = index
        elif not is_valid and start is not None:
            stop = index
            intervals.append(
                {
                    "start_index": start,
                    "stop_index_exclusive": stop,
                    "t_start": float(times_array[start]),
                    "t_stop": float(times_array[stop - 1]),
                    "num_points": stop - start,
                }
            )
            start = None
    return deviations, intervals
