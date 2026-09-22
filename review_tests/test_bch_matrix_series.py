from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from review_response.bch_matrix_series import (
    eigenenergy_perturbation_series,
    effective_hamiltonian_series,
    effective_hamiltonian_series_numpy,
    evaluate_matrix_series,
    ordered_exponential_product_series,
)
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import yoshida_4th_list


def _direct_ordered_product(
    generators: list[np.ndarray], time_value: float
) -> np.ndarray:
    dimension = generators[0].shape[0]
    result = np.eye(dimension, dtype=np.complex128)
    for generator in generators:
        result = expm(float(time_value) * generator) @ result
    return result


def test_ordered_exponential_series_matches_direct_product() -> None:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    generators = [0.31j * x, -0.27j * z, 0.19j * (x + 0.2 * z)]
    series = ordered_exponential_product_series(
        generators, maximum_degree=7, decimal_digits=70
    )
    time_value = 0.025
    reconstructed = evaluate_matrix_series(series, time_value)
    direct = _direct_ordered_product(generators, time_value)
    assert np.linalg.norm(reconstructed - direct) < 2e-16


def test_single_exponential_has_no_bch_corrections() -> None:
    hamiltonian = np.asarray(
        [[0.7, 0.2 - 0.1j], [0.2 + 0.1j, -0.4]], dtype=np.complex128
    )
    result = effective_hamiltonian_series(
        [hamiltonian], [(0, 1.0)], maximum_effective_order=6
    )
    coefficients = result["effective_hamiltonian"]
    assert np.linalg.norm(coefficients[0] - hamiltonian) < 1e-15
    assert max(np.linalg.norm(value) for value in coefficients[1:]) < 1e-70


def test_yoshida_fourth_order_structure_for_two_noncommuting_terms() -> None:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    steps = list(iter_s2_sequence_steps(2, sequence))
    result = effective_hamiltonian_series(
        [0.3 * x, 0.8 * z],
        steps,
        maximum_effective_order=6,
        decimal_digits=90,
    )
    coefficients = result["effective_hamiltonian"]
    assert np.linalg.norm(coefficients[0] - (0.3 * x + 0.8 * z)) < 1e-15
    assert max(np.linalg.norm(coefficients[index]) for index in (1, 2, 3, 5)) < 1e-14
    assert np.linalg.norm(coefficients[4]) > 1e-6
    assert np.linalg.norm(coefficients[4] - coefficients[4].conj().T) < 1e-14
    assert np.linalg.norm(coefficients[6] - coefficients[6].conj().T) < 1e-14


def test_numpy_series_matches_high_precision_bch_coefficients() -> None:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    steps = list(iter_s2_sequence_steps(2, sequence))
    high_precision = effective_hamiltonian_series(
        [0.3 * x, 0.8 * z], steps, maximum_effective_order=6
    )["effective_hamiltonian"]
    numpy_series = effective_hamiltonian_series_numpy(
        [0.3 * x, 0.8 * z], steps, maximum_effective_order=6
    )["effective_hamiltonian"]
    assert np.linalg.norm(numpy_series[0] - high_precision[0]) < 2e-15
    assert np.linalg.norm(numpy_series[4] - high_precision[4]) < 2e-14
    assert np.linalg.norm(numpy_series[6] - high_precision[6]) < 2e-13


def test_eigenenergy_series_includes_second_order_state_response() -> None:
    gap = 1.7
    coupling = 0.23
    h0 = np.diag([0.0, gap]).astype(np.complex128)
    perturbation = np.asarray(
        [[0.0, coupling], [coupling, 0.0]], dtype=np.complex128
    )
    zero = np.zeros((2, 2), dtype=np.complex128)
    result = eigenenergy_perturbation_series(
        [h0, perturbation, zero],
        np.asarray([1.0, 0.0]),
        maximum_order=2,
    )
    coefficients = result["energy_coefficients"]
    assert abs(coefficients[0]) < 1e-15
    assert abs(coefficients[1]) < 1e-15
    assert abs(coefficients[2] + coupling**2 / gap) < 1e-15
