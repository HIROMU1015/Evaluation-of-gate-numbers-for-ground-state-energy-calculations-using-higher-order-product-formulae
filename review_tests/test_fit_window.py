from __future__ import annotations

import numpy as np
import pytest

from trotterlib.fit_window import (
    estimate_gpu_noise_floor,
    rolling_loglog_fits,
    select_best_rolling_fit,
)


def test_estimate_gpu_noise_floor_uses_low_error_points() -> None:
    cpu = np.array([1e-13, 2e-12, 3e-10, 4e-8])
    gpu = np.array([1.4e-13, 2.1e-12, 3.1e-10, 4.2e-8])

    floor = estimate_gpu_noise_floor(
        cpu,
        gpu,
        safety_factor=5.0,
        low_error_points=2,
    )

    assert floor == pytest.approx(5e-13)


def test_rolling_loglog_fits_masks_windows_below_floor() -> None:
    times = np.linspace(0.1, 0.8, 8)
    errors = 2.5e-5 * times**4
    errors[:2] = 1e-12

    windows = rolling_loglog_fits(
        times,
        errors,
        formal_order=4,
        noise_floor=2e-12,
        window_size=4,
    )

    assert [window["start_index"] for window in windows] == [2, 3, 4]
    best = select_best_rolling_fit(windows)
    assert best is not None
    assert best["free_order"] == pytest.approx(4.0, abs=1e-12)
    assert best["fixed_order_alpha"] == pytest.approx(2.5e-5)
    assert best["r2"] == pytest.approx(1.0)


def test_rolling_loglog_fits_returns_no_window_above_floor() -> None:
    windows = rolling_loglog_fits(
        np.array([0.1, 0.2, 0.3]),
        np.array([1e-13, 2e-13, 3e-13]),
        formal_order=8,
        noise_floor=1e-12,
        window_size=2,
    )

    assert windows == []
    assert select_best_rolling_fit(windows) is None
