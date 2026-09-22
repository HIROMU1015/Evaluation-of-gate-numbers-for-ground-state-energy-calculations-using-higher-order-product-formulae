from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("pennylane")

from review_response.bch_matrix_series import effective_hamiltonian_series
from review_response.pennylane_bch import (
    bch_expansion_for_symmetric_pf,
    effective_hamiltonian_expectations_from_bch,
    effective_hamiltonian_matrices_from_bch,
    symmetric_pf_product_formula,
)
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import yoshida_4th_list
from trotterlib.sector_pf import build_sector_pf_unitary_sequential


def _matrices() -> list[np.ndarray]:
    return [
        np.asarray([[0.2, 0.3], [0.3, -0.1]], dtype=np.complex128),
        np.asarray([[0.7, -0.2j], [0.2j, -0.4]], dtype=np.complex128),
    ]


def test_product_formula_order_matches_left_applied_repository_order() -> None:
    matrices = _matrices()
    sequence = [0.2, 0.8]
    time_value = 0.17
    formula = symmetric_pf_product_formula(2, sequence)
    pennylane_unitary = formula(1j * time_value).to_matrix(
        {index: matrix for index, matrix in enumerate(matrices)}
    )
    spectra = [np.linalg.eigh(matrix) for matrix in matrices]
    repository_unitary = build_sector_pf_unitary_sequential(
        spectra, sequence, time_value
    )
    assert np.linalg.norm(pennylane_unitary - repository_unitary) < 2e-15


def test_pennylane_bch_matches_independent_matrix_logarithm_series() -> None:
    matrices = _matrices()
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    steps = list(iter_s2_sequence_steps(2, sequence))
    reference = effective_hamiltonian_series(
        matrices, steps, maximum_effective_order=6, decimal_digits=90
    )["effective_hamiltonian"]
    expansion = bch_expansion_for_symmetric_pf(2, sequence, 7)
    evaluated = effective_hamiltonian_matrices_from_bch(expansion, matrices)
    state = np.asarray([0.6 + 0.1j, 0.7 - 0.2j], dtype=np.complex128)
    state /= np.linalg.norm(state)
    expectations, word_counts = effective_hamiltonian_expectations_from_bch(
        expansion, matrices, state
    )

    for order in range(7):
        assert np.linalg.norm(evaluated[order] - reference[order]) < 2e-13
        assert abs(expectations[order] - np.vdot(state, evaluated[order] @ state)) < 2e-13
    assert word_counts[4] > 0
    assert word_counts[6] > 0
