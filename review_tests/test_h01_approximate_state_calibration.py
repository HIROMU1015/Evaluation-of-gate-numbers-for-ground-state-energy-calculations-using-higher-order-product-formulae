from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from pyscf.fci import cistring
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

import run_h01_approximate_state_calibration as h01


def test_fixed_protocol_hash_and_scope() -> None:
    observed = hashlib.sha256(h01.PROTOCOL_PATH.read_bytes()).hexdigest()
    assert observed == h01.EXPECTED_PROTOCOL_SHA256
    protocol = h01._protocol()
    assert [item["pf"] for item in protocol["formulae"]] == [
        "current_m3", "yoshida4"
    ]
    assert protocol["calibration"]["primary_relative_to_source_t_ana"] == [
        0.1, 0.2, 0.3, 0.4, 0.5
    ]


def test_pyscf_determinant_to_up_then_down_jw_integer() -> None:
    # q0 and q4 map to the MSB of their respective spin blocks.
    assert h01.determinant_pair_to_basis_integer(0b0001, 0b0001, 4) == 0b10001000
    assert h01.determinant_pair_to_basis_integer(0b0101, 0b0011, 4) == 0b10101100


def test_fcivec_population_mapping_preserves_coefficients_and_norm() -> None:
    norb, nelec = 4, (2, 2)
    alpha = cistring.make_strings(range(norb), nelec[0])
    beta = cistring.make_strings(range(norb), nelec[1])
    basis = h01.diagnosis._population_basis(norb, *nelec)
    coefficients = np.arange(1, len(alpha) * len(beta) + 1, dtype=float).reshape(
        len(alpha), len(beta)
    )
    coefficients /= np.linalg.norm(coefficients)
    population = h01.fcivec_to_population(coefficients, norb, nelec, basis)
    assert np.isclose(np.linalg.norm(population), 1.0)
    lookup = {int(value): index for index, value in enumerate(basis)}
    target = h01.determinant_pair_to_basis_integer(int(alpha[2]), int(beta[3]), norb)
    # Nalpha*Nbeta is even here, so the documented global sign is +1.
    assert population[lookup[target]] == coefficients[2, 3]


def test_rhf_determinant_occupies_lowest_spatial_orbitals() -> None:
    basis = h01.diagnosis._population_basis(4, 2, 2)
    state = h01.rhf_population_state(4, (2, 2), basis)
    target = h01.determinant_pair_to_basis_integer(0b0011, 0b0011, 4)
    assert np.count_nonzero(state) == 1
    assert basis[int(np.argmax(abs(state)))] == target


def test_artificial_exact_echo_identity_and_phase_unwrap() -> None:
    hamiltonian = csr_matrix(np.asarray([[0.3, 0.2], [0.2, -0.4]], dtype=np.complex128))
    state = np.asarray([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    for time_value in (0.1, 0.3, 0.8):
        forward = expm_multiply((1j * time_value) * hamiltonian, state)
        echoed = expm_multiply((-1j * time_value) * hamiltonian, forward)
        overlap = np.vdot(state, echoed)
        assert abs(overlap - 1.0) < 1e-12
    principal = np.angle(np.exp(1j * np.asarray([2.9, 3.1, 3.3, 3.5])))
    assert np.allclose(np.unwrap(principal), [2.9, 3.1, 3.3, 3.5])


def test_proxy_fit_does_not_clip_infeasible_error_budget() -> None:
    points = [
        {"time": value, "echo_phase_hartree": -(value**4 + 0.2 * value**6)}
        for value in (0.1, 0.2, 0.3, 0.4, 0.5)
    ]
    model = h01._fit_proxy(points, "echo_phase_hartree", 5, 1.0, "test")
    assert np.allclose(model["coefficient_values"], [-1.0, -0.2], atol=1e-12)
    # The production cost helper returns None rather than clipping an
    # error that consumes the complete budget.
    epsilon = h01._protocol()["target_error_hartree"]
    assert h01.diagnosis._cost(1.0, epsilon, 10) is None

