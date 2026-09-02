from __future__ import annotations

import numpy as np

from validate_global_phase_corrected_cost import (
    correct_overlap_series,
    phase_correction_from_t0,
)


def test_t0_phase_correction_maps_negative_overlap_to_positive_real() -> None:
    overlap_t0 = -0.999999999999 + 2e-8j
    correction = phase_correction_from_t0(overlap_t0)
    corrected = correction * overlap_t0
    assert corrected.real > 0
    assert abs(corrected.imag) < 1e-15
    assert np.isclose(abs(correction), 1.0)


def test_correct_overlap_series_removes_constant_pi_phase() -> None:
    times = np.asarray([0.5, 1.0, 1.5])
    physical_phases = 3e-5 * times**5
    overlaps = -np.exp(1j * physical_phases)
    result = correct_overlap_series(-1.0 + 0.0j, overlaps)
    np.testing.assert_allclose(
        result["unwrapped_phases"], physical_phases, rtol=1e-11, atol=1e-14
    )
    assert result["maximum_adjacent_unwrapped_phase_jump"] < np.pi


def test_correct_overlap_series_unwraps_across_principal_branch() -> None:
    physical_phases = np.asarray([2.9, 3.2, 3.5])
    overlaps = -np.exp(1j * physical_phases)
    result = correct_overlap_series(-1.0 + 0.0j, overlaps)
    np.testing.assert_allclose(
        result["unwrapped_phases"], physical_phases, rtol=0, atol=1e-14
    )
