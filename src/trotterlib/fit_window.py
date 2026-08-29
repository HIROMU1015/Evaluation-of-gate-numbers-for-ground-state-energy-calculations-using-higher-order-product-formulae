from __future__ import annotations

from typing import Any

import numpy as np

from .analysis_utils import loglog_average_coeff, loglog_fit


def estimate_gpu_noise_floor(
    cpu_errors: np.ndarray,
    gpu_errors: np.ndarray,
    *,
    safety_factor: float = 5.0,
    low_error_points: int = 3,
) -> float:
    """Estimate a PF-specific GPU floor from the lowest-error CPU/GPU points."""
    cpu = np.asarray(cpu_errors, dtype=float).ravel()
    gpu = np.asarray(gpu_errors, dtype=float).ravel()
    if cpu.shape != gpu.shape or cpu.size == 0:
        raise ValueError("CPU and GPU error arrays must have the same nonzero size")
    if safety_factor <= 0:
        raise ValueError("safety_factor must be positive")
    if low_error_points < 1:
        raise ValueError("low_error_points must be at least 1")
    if not np.all(np.isfinite(cpu)) or not np.all(np.isfinite(gpu)):
        raise ValueError("CPU and GPU error arrays must be finite")

    numerical_difference = np.abs(gpu - cpu)
    signal_size = np.maximum(np.abs(cpu), np.abs(gpu))
    sample_size = min(int(low_error_points), cpu.size)
    low_error_indices = np.argsort(signal_size)[:sample_size]
    observed_floor = float(np.max(numerical_difference[low_error_indices]))
    return max(float(np.finfo(float).eps), float(safety_factor) * observed_floor)


def rolling_loglog_fits(
    times: np.ndarray,
    errors: np.ndarray,
    *,
    formal_order: int,
    noise_floor: float,
    window_size: int = 5,
) -> list[dict[str, Any]]:
    """Fit consecutive windows whose errors all exceed a numerical floor."""
    times_array = np.asarray(times, dtype=float).ravel()
    errors_array = np.asarray(errors, dtype=float).ravel()
    if times_array.shape != errors_array.shape or times_array.size == 0:
        raise ValueError("times and errors must have the same nonzero size")
    if window_size < 2 or window_size > times_array.size:
        raise ValueError("window_size must be between 2 and the number of points")
    if formal_order < 1:
        raise ValueError("formal_order must be positive")
    if noise_floor < 0:
        raise ValueError("noise_floor must be non-negative")
    if not np.all(np.isfinite(times_array)) or np.any(times_array <= 0):
        raise ValueError("times must be finite and positive")

    windows: list[dict[str, Any]] = []
    for start in range(times_array.size - window_size + 1):
        stop = start + window_size
        window_times = times_array[start:stop]
        window_errors = errors_array[start:stop]
        eligible = np.isfinite(window_errors) & (window_errors > noise_floor)
        if not np.all(eligible):
            continue
        fit = loglog_fit(
            window_times,
            window_errors,
            mask_nonpositive=False,
            compute_r2=True,
        )
        fixed_order_alpha = loglog_average_coeff(
            window_times,
            window_errors,
            formal_order,
            mask_nonpositive=False,
        )
        windows.append(
            {
                "start_index": int(start),
                "stop_index_exclusive": int(stop),
                "t_start": float(window_times[0]),
                "t_stop": float(window_times[-1]),
                "num_points": int(window_size),
                "free_order": float(fit.slope),
                "free_alpha": float(fit.coeff),
                "r2": float(fit.r2),
                "fixed_order_alpha": float(fixed_order_alpha),
                "order_deviation": abs(float(fit.slope) - int(formal_order)),
            }
        )
    return windows


def select_best_rolling_fit(
    windows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Choose the closest-to-formal-order window, using R2 as a tiebreaker."""
    if not windows:
        return None
    return min(
        windows,
        key=lambda window: (
            float(window["order_deviation"]),
            -float(window["r2"]),
            float(window["t_start"]),
        ),
    )
