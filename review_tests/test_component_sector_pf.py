import numpy as np
from openfermion.linalg import get_sparse_operator
from openfermion.ops import QubitOperator
from scipy.linalg import expm

from trotterlib.component_sector_pf import (
    component_exponential,
    diagonalize_components,
    find_balanced_z2_symmetry,
    qubit_operator_sector_matrix,
)


def test_direct_sector_matrix_matches_openfermion() -> None:
    operator = (
        0.3 * QubitOperator(())
        + 0.7 * QubitOperator("Z0")
        - 0.2 * QubitOperator("X0 X2")
        + 0.4 * QubitOperator("Y1 Y3")
        + 0.1j * QubitOperator("X0 Y2")
        - 0.1j * QubitOperator("Y0 X2")
    )
    basis = np.asarray([0, 3, 5, 6, 9, 10, 12, 15], dtype=np.int64)
    actual = qubit_operator_sector_matrix(
        operator, 4, basis, remove_constant=False
    ).toarray()
    full = get_sparse_operator(operator, n_qubits=4).tocsr()
    expected = full[basis, :][:, basis].toarray()
    np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=1e-14)


def test_component_exponential_is_exact() -> None:
    matrix = np.asarray(
        [
            [0.2, 0.1j, 0.0, 0.0],
            [-0.1j, -0.3, 0.0, 0.0],
            [0.0, 0.0, 0.7, 0.25],
            [0.0, 0.0, 0.25, 0.1],
        ],
        dtype=np.complex128,
    )
    from scipy.sparse import csr_matrix

    spectrum = diagonalize_components(csr_matrix(matrix))
    actual = component_exponential(spectrum, 0.37).toarray()
    expected = expm(1j * 0.37 * matrix)
    np.testing.assert_allclose(actual, expected, atol=2e-14, rtol=2e-14)
    assert spectrum.component_count == 2
    assert spectrum.maximum_component_size == 2


def test_symmetry_discovery_finds_definite_balanced_sector() -> None:
    # X0 X1 commutes with Z0 Z1.  The chosen state has +1 parity.
    groups = [QubitOperator("X0 X1"), QubitOperator("Z0")]
    basis = np.arange(4, dtype=np.int64)
    state = np.asarray([1.0, 0.0, 0.0, 1.0], dtype=np.complex128)
    state /= np.linalg.norm(state)
    mask, target, selected, diagnostics = find_balanced_z2_symmetry(
        groups, 2, basis, state
    )
    assert mask != 0
    assert target in (0, 1)
    assert selected.size == 2
    assert diagnostics["ground_state_outside_norm"] == 0.0
