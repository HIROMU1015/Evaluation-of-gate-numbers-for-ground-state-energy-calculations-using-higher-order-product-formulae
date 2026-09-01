from __future__ import annotations

import numpy as np
import pytest

import trotterlib.qiskit_time_evolution_pyscf as pyscf_ground_state
from trotterlib.qiskit_time_evolution_pyscf import (
    FCI_DAVIDSON_RETRY_LINDEP,
    FCI_RESIDUAL_TOLERANCE,
    GroupedFCIResult,
    MAX_FULL_PSPACE_DIMENSION,
    _solve_checked_fci,
    make_checked_fci_result_from_pyscf_solver_grouper,
    make_fci_vector_from_pyscf_solver_grouper,
)


@pytest.fixture(scope="module")
def checked_h4_result() -> GroupedFCIResult:
    return make_checked_fci_result_from_pyscf_solver_grouper(4)


def test_checked_h4_fci_uses_bounded_pyscf_exact_path(
    checked_h4_result: GroupedFCIResult,
) -> None:
    result = checked_h4_result
    diagnostics = result.diagnostics

    assert diagnostics["source"] == "PySCF FCI"
    assert diagnostics["method"] == "pyscf_full_pspace_lapack_eigh"
    assert diagnostics["scf_converged"]
    assert diagnostics["fci_converged"]
    assert not diagnostics["used_scipy_eigsh"]
    assert diagnostics["ci_dimension"] <= MAX_FULL_PSPACE_DIMENSION
    assert diagnostics["fci_residual_norm"] <= FCI_RESIDUAL_TOLERANCE
    assert np.isclose(np.linalg.norm(result.state_vector), 1.0)


def test_grouped_fci_compatibility_wrapper_preserves_tuple_api(
    checked_h4_result: GroupedFCIResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pyscf_ground_state,
        "make_checked_fci_result_from_pyscf_solver_grouper",
        lambda molecule_type: checked_h4_result,
    )
    groups, n_qubits, energy, state = (
        make_fci_vector_from_pyscf_solver_grouper(4)
    )

    assert groups
    assert n_qubits == 8
    assert np.isfinite(energy)
    assert state.shape == (1 << n_qubits, 1)
    assert np.isclose(np.linalg.norm(state), 1.0)


def test_checked_fci_retries_davidson_linear_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMolecule:
        nelec = (4, 5)

        @staticmethod
        def energy_nuc() -> float:
            return 0.5

    class FakeMeanField:
        converged = True
        mo_coeff = np.eye(9)

        @staticmethod
        def energy_nuc() -> float:
            return 0.5

    class FakeSolver:
        def __init__(self) -> None:
            self.conv_tol = None
            self.conv_tol_residual = None
            self.max_cycle = None
            self.max_space = None
            self.pspace_size = 400
            self.davidson_only = False
            self.lindep = 1e-14
            self.converged = False
            self.norb = 9
            self.nelec = (4, 5)
            self.calls: list[np.ndarray | None] = []

        def kernel(
            self, ci0: np.ndarray | None = None
        ) -> tuple[float, np.ndarray]:
            self.calls.append(ci0)
            self.converged = len(self.calls) == 2
            return -1.0, np.ones((126, 126))

    fake_solver = FakeSolver()
    residuals = iter((9e-8, 5e-11))
    monkeypatch.setattr(
        pyscf_ground_state.fci,
        "FCI",
        lambda mol, mo_coeff: fake_solver,
    )
    monkeypatch.setattr(
        pyscf_ground_state,
        "_fci_residual_norm",
        lambda *args, **kwargs: next(residuals),
    )

    _, energy, _, diagnostics = _solve_checked_fci(
        FakeMolecule(),
        FakeMeanField(),
        np.eye(9),
        np.zeros((9, 9, 9, 9)),
    )

    assert energy == -1.0
    assert len(fake_solver.calls) == 2
    assert fake_solver.calls[0] is None
    assert fake_solver.calls[1] is not None
    assert fake_solver.lindep == FCI_DAVIDSON_RETRY_LINDEP
    assert diagnostics["davidson_retry_performed"]
    assert not diagnostics["davidson_attempts"][0]["fci_converged"]
    assert diagnostics["davidson_attempts"][1]["fci_converged"]
    assert diagnostics["fci_residual_norm"] <= FCI_RESIDUAL_TOLERANCE
    assert not diagnostics["used_scipy_eigsh"]
