"""Backend and phase-convention checks; synthetic matrices only."""
import numpy as np
from scipy.linalg import expm, schur
from scipy.sparse import csr_matrix

from review_response.run_lab_progress_hchain_transfer_20261007 import MolecularActions


def test_block_proxy_matches_dense_echo_for_complex_states_and_signed_times():
    h = np.array([[0.2, 0.3j], [-0.3j, -0.4]], dtype=complex)
    perturbation = np.array([[0.02, 0.01], [0.01, -0.03]])
    states = [np.array([1.0, 1j]) / np.sqrt(2), np.array([0.6, 0.8])]
    action = MolecularActions.__new__(MolecularActions)
    action.h_sparse = csr_matrix(h)
    action.exponentials = 0
    for t in (-0.4, 0.4):
        unitary = expm(1j * t * (h + perturbation))
        actual = action.proxies(unitary, states, t)
        expected = [np.vdot(s, expm(-1j * t * h) @ unitary @ s).imag / t for s in states]
        np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=0)
    assert action.exponentials == 4


def test_spectral_proxy_reconstructs_echo_with_positive_evolution_convention():
    h = np.array([[0.0, 0.15], [0.15, 0.7]])
    energies, vectors = np.linalg.eigh(h)
    exact, energy = vectors[:, 0], energies[0]
    t = 1.3
    u = expm(1j * t * (h + np.diag([0.03, -0.02])))
    tri, pf_vectors = schur(u, output="complex")
    weights = np.abs(pf_vectors.conj().T @ exact) ** 2
    proxy = np.vdot(expm(1j * t * h) @ exact, u @ exact).imag / t
    spectral = np.sum(weights * np.sin(np.angle(np.diag(tri)) - energy * t) / t)
    assert abs(spectral - proxy) < 1e-14
