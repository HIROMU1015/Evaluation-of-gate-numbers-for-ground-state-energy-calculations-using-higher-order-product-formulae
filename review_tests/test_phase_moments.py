from __future__ import annotations

import numpy as np
import pytest

from trotterlib.phase_moments import dominant_phase_from_moments


def _mixture_moments(
    phases: np.ndarray, weights: np.ndarray, maximum_power: int
) -> np.ndarray:
    powers = np.arange(maximum_power + 1)
    return np.asarray(
        [np.sum(weights * np.exp(1j * phases * power)) for power in powers]
    )


def test_pure_phase_is_recovered_after_gram_rank_reduction() -> None:
    phase = 0.037
    moments = np.exp(1j * phase * np.arange(7))

    result = dominant_phase_from_moments(
        moments,
        evolution_time=2.0,
        reference_energy=0.0,
        subspace_dimension=6,
    )

    assert result["retained_rank"] == 1
    assert result["selected"]["energy_shift_hartree"] == pytest.approx(
        phase / 2.0, abs=1e-13
    )


def test_two_phase_mixture_recovers_dominant_component() -> None:
    phases = np.array([0.012, -0.43])
    weights = np.array([0.997, 0.003])
    moments = _mixture_moments(phases, weights, maximum_power=2)

    result = dominant_phase_from_moments(
        moments,
        evolution_time=1.5,
        reference_energy=0.0,
        subspace_dimension=2,
        gram_relative_cutoff=1e-13,
    )

    assert result["retained_rank"] == 2
    assert result["selected"]["energy_shift_hartree"] == pytest.approx(
        phases[0] / 1.5, abs=1e-11
    )
    assert result["selected"][
        "estimated_reference_overlap_probability"
    ] == pytest.approx(weights[0], abs=1e-11)


def test_reference_energy_demodulation_recovers_small_shift() -> None:
    reference = -1.73
    shift = 2.4e-5
    time = 3.1
    moments = np.exp(
        1j * (reference + shift) * time * np.arange(5)
    )

    result = dominant_phase_from_moments(
        moments,
        evolution_time=time,
        reference_energy=reference,
        subspace_dimension=4,
    )

    assert result["selected"]["energy_shift_hartree"] == pytest.approx(
        shift, abs=1e-13
    )


def test_rejects_subspace_larger_than_available_moments() -> None:
    with pytest.raises(ValueError, match="subspace_dimension"):
        dominant_phase_from_moments(
            [1.0, 0.9 + 0.1j],
            evolution_time=1.0,
            reference_energy=0.0,
            subspace_dimension=2,
        )
