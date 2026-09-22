from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from review_response.audit_f01_effective_hamiltonian_pilot import (
    evaluate_operator_polynomial,
    fit_even_effective_operators,
    operator_decomposition,
)


def test_matrix_operator_fit_recovers_synthetic_even_coefficients() -> None:
    hamiltonian = np.asarray([[0.2, 0.1], [0.1, -0.3]], dtype=np.complex128)
    d4 = np.asarray([[0.03, -0.01j], [0.01j, -0.02]], dtype=np.complex128)
    d6 = np.asarray([[0.001, 0.0003], [0.0003, -0.0007]], dtype=np.complex128)
    d8 = np.asarray([[2e-5, 1e-5j], [-1e-5j, -3e-5]], dtype=np.complex128)
    times = np.geomspace(0.08, 0.6, 12)
    corrections = np.asarray(
        [d4 * t**4 + d6 * t**6 + d8 * t**8 for t in times]
    )
    fitted = fit_even_effective_operators(times, corrections, (4, 6, 8))
    assert np.linalg.norm(fitted["coefficients"][0] - d4) < 2e-14
    assert np.linalg.norm(fitted["coefficients"][1] - d6) < 2e-13
    assert np.linalg.norm(fitted["coefficients"][2] - d8) < 2e-12


def test_operator_polynomial_uses_declared_orders() -> None:
    hamiltonian = np.diag([-0.4, 0.7]).astype(np.complex128)
    d4 = np.asarray([[0.01, 0.002], [0.002, -0.01]], dtype=np.complex128)
    d6 = np.asarray([[0.003, 0.0], [0.0, -0.002]], dtype=np.complex128)
    time_value = 0.3
    evaluated = evaluate_operator_polynomial(
        hamiltonian, (4, 6), (d4, d6), time_value
    )
    expected = hamiltonian + d4 * time_value**4 + d6 * time_value**6
    assert np.linalg.norm(evaluated - expected) < 1e-16
    assert np.linalg.norm(expm(1j * time_value * evaluated)) > 0.0


def test_operator_decomposition_preserves_ground_state_coupling_norm() -> None:
    hamiltonian = np.diag([-1.0, 0.2, 0.8]).astype(np.complex128)
    state = np.asarray([1.0, 0.0, 0.0], dtype=np.complex128)
    operator = np.asarray(
        [[0.3, 0.04, -0.02j], [0.04, -0.1, 0.01], [0.02j, 0.01, 0.2]],
        dtype=np.complex128,
    )
    result = operator_decomposition(hamiltonian, state, operator, 4)
    expected = np.sqrt(0.04**2 + 0.02**2)
    assert abs(result["ground_to_excited_coupling_norm"] - expected) < 1e-15
    assert abs(result["centered_action_norm"] - expected) < 1e-15
    assert result["selected_ground_index"] == 0
