from pathlib import Path

import numpy as np

from run_m3_h10_h11_cost_validation import (
    DIRECT_ROOT,
    _direct_calibration,
    _overlap_point,
)


def test_direct_calibration_is_held_out_on_h8_h9() -> None:
    calibration = _direct_calibration(Path(DIRECT_ROOT))

    assert calibration["training_systems"] == [2, 4, 5, 6, 7]
    assert calibration["holdout_systems"] == [8, 9]
    assert calibration["passed"]
    assert all(item["passed"] for item in calibration["holdout_checks"])


def test_overlap_point_keeps_proxy_and_model_costs_distinct() -> None:
    state = np.asarray([1.0, 0.0], dtype=np.complex128)
    phase = np.exp(0.2j)
    evolved = phase * np.asarray([np.exp(1e-5j), 0.0], dtype=np.complex128)

    point = _overlap_point(
        state,
        evolved,
        energy=0.0,
        time_value=0.5,
        phase_correction=np.conj(phase),
        alpha=1e-5 / 0.5**4,
        rotations=10,
    )

    assert np.isclose(point["overlap_phase_proxy_error_hartree"], 2e-5)
    assert point["model_error_hartree"] == 1e-5
    assert point["overlap_phase_proxy_cost"] is not None
