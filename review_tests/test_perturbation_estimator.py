from __future__ import annotations

import numpy as np

from trotterlib.plots_timeevo_error import _collect_perturbation_errors


def test_phase_rotated_estimator_recovers_a_small_energy_shift() -> None:
    reference = np.array([1.0, 0.0], dtype=complex)
    energy = -1.7
    energy_shift = 2.5e-5
    times = (-0.4, -0.2, 0.2, 0.4)
    evolved = [
        (time, np.exp(-1j * (energy + energy_shift) * time) * reference)
        for time in times
    ]

    times_out, estimates = _collect_perturbation_errors(evolved, energy, reference)

    assert times_out == [abs(time) for time in times]
    np.testing.assert_allclose(estimates, energy_shift, rtol=2e-10, atol=1e-14)


def test_phase_rotated_estimator_does_not_divide_by_trigonometric_phase() -> None:
    reference = np.array([0.0, 1.0], dtype=complex)
    energy = np.pi / 2
    energy_shift = -1e-6
    time = 1.0  # cos(E t) = 0 for the previous estimator.
    evolved = np.exp(-1j * (energy + energy_shift) * time) * reference

    _, estimates = _collect_perturbation_errors([(time, evolved)], energy, reference)

    np.testing.assert_allclose(estimates, abs(energy_shift), rtol=1e-9, atol=1e-14)
