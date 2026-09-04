from __future__ import annotations

import numpy as np

from benchmark_direct_pf_solvers import (
    _maximum_or_none,
    analyze_eigensystem,
    build_pf_unitary_cpu,
    ritz_from_moments,
)


def _one_group_spectrum() -> list[tuple[np.ndarray, np.ndarray]]:
    return [(np.asarray([-0.7, 0.4]), np.eye(2, dtype=complex))]


def test_maximum_or_none_handles_invalid_cost_rows() -> None:
    assert _maximum_or_none([None, None]) is None
    assert _maximum_or_none([None, 0.2, 0.1]) == 0.2


def test_cpu_palindromic_stage_reuse_matches_sequential() -> None:
    spectra = _one_group_spectrum()
    for label in ("4th(m5_best)", "8th(Morales-Y8m10b)"):
        sequential, _ = build_pf_unitary_cpu(
            spectra, 0.73, label, reuse_palindromic_stages=False
        )
        reused, profile = build_pf_unitary_cpu(
            spectra, 0.73, label, reuse_palindromic_stages=True
        )
        assert np.allclose(sequential, reused, rtol=0.0, atol=2e-14)
        assert profile["stages_built"] == profile["unique_s2_stage_count"]


def test_eigensystem_returns_signed_shift_and_residual() -> None:
    energy = -0.7
    time_value = 0.4
    unitary = np.diag(np.exp(1j * time_value * np.asarray([energy, 0.4])))
    values = np.diag(unitary)
    vectors = np.eye(2, dtype=complex)
    point, _ = analyze_eigensystem(
        unitary,
        values,
        vectors,
        np.asarray([1.0, 0.0], dtype=complex),
        energy,
        time_value,
        10,
        selection_reference=None,
    )
    assert abs(point["signed_eigenvalue_shift_hartree"]) < 1e-15
    assert point["eigenpair_residual_2_norm"] < 1e-15


def test_unitary_moment_ritz_recovers_connected_eigenphase() -> None:
    phases = np.asarray([-0.21, 0.63])
    probabilities = np.asarray([0.92, 0.08])
    moments = [
        complex(np.sum(probabilities * np.exp(1j * phases * k)))
        for k in range(5)
    ]
    result = ritz_from_moments(
        moments,
        4,
        1e-12,
        energy=-0.21,
        time_value=1.0,
        n_exp=10,
    )
    assert abs(result["effective_energy_hartree"] + 0.21) < 1e-10
    assert result["ground_state_overlap_probability"] > 0.9
    assert result["equivalent_eigenpair_residual_2_norm"] < 1e-7
