"""Numerical invariants of the bounded transfer wrapper."""
import numpy as np
from scipy.linalg import expm
from scipy.sparse import csr_matrix

from review_response.pf_first_study_experiment_a import track_direct_branch
from review_response.run_lab_progress_hchain_transfer_20261007 import (
    MolecularActions, direct_point, projected_rank_state,
)
from trotterlib.component_sector_pf import diagonalize_components
from trotterlib.sector_pf import build_sector_pf_unitary


def test_sparse_product_reproduces_existing_dense_pf():
    groups = [np.array([[.4, 0], [0, -.3]]), np.array([[0, .2], [.2, 0]])]
    action = MolecularActions.__new__(MolecularActions)
    action.cisd = np.array([1., 0.], dtype=complex)
    action.groups = groups
    action.spectra = [diagonalize_components(csr_matrix(group)) for group in groups]
    action.full_builds = 0
    dense = [np.linalg.eigh(group) for group in groups]
    sequence = [.6, -.2, .6]
    for t in (.02, .4, 3.):
        assert np.linalg.norm(action.unitary(sequence, t) - build_sector_pf_unitary(dense, sequence, t)) < 1e-12


def test_streaming_schur_branch_matches_historical_unwrap():
    h = np.array([[0., .3], [.3, 1.]])
    energies, vectors = np.linalg.eigh(h)
    exact, energy = vectors[:, 0], energies[0]
    times = [.1, 1., 10., 30.]
    perturbation = np.array([[.00002, 0], [0, 0]])
    unitaries = [expm(1j * t * (h + perturbation)) for t in times]
    expected = track_direct_branch(unitaries, times, exact, energy, 1e-8)
    previous, previous_energy = exact, energy
    for unitary, t, reference in zip(unitaries, times, expected):
        actual, previous, previous_energy = direct_point(unitary, t, exact, energy, previous, previous_energy)
        assert abs(actual["direct_shift"] - reference["direct_shift_hartree"]) < 1e-12
        assert abs(actual["previous_overlap"] - reference["previous_branch_overlap_probability"]) < 1e-12
        assert actual["unwrap_integer"] == reference["unwrap_integer"]


def test_rank_extension_nested_and_variational():
    action = MolecularActions.__new__(MolecularActions)
    action.indices = np.array([15, 23, 51, 105, 240])
    action.spec = {"input_identity": {"RHF_reference_integer": 15}}
    action.cisd = np.zeros(5, dtype=complex)
    rng = np.random.default_rng(2)
    raw = rng.standard_normal((5, 5))
    action.h = raw + raw.T
    state2, info2 = projected_rank_state(action, 2)
    state3, info3 = projected_rank_state(action, 3)
    assert info2["subspace_dimension"] <= info3["subspace_dimension"]
    assert info3["energy_hartree"] <= info2["energy_hartree"] + 1e-12
    assert np.linalg.norm(state2) == 1
    assert abs(np.linalg.norm(state3) - 1) < 1e-12
