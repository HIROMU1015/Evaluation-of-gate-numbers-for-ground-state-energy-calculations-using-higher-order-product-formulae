from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from scipy.linalg import expm

from review_response.audit_f02_tau8_state_mixing import decompose_a8_state_mixing
from review_response.run_f_hf_mechanism_bridge import (
    EXPECTED_PROTOCOL_SHA256,
    FORMAL_MAXIMUM_ORDER,
    NEW_DIRECT_TRUTH_POINT_COUNT,
    PROTOCOL_PATH,
    SourceIdentityError,
    _finite_log_record,
    _frobenius,
    _relative,
    center_group_identity_components,
    circular_phase_gap,
    diagnostic_annotations,
    effective_hamiltonian_series_arb,
    effective_hamiltonian_series_dtype,
    reconstruct_component_spectrum,
    require_checks,
)
from trotterlib.component_sector_pf import ComponentBatch, ComponentSpectrum
from trotterlib.pf_decomposition import iter_s2_sequence_steps, symmetric_s2_sequence
from trotterlib.product_formula import yoshida_4th_list


def test_component_spectrum_reconstruction() -> None:
    rotation = np.asarray(
        [[1.0, 1.0j], [1.0j, 1.0]], dtype=np.complex128
    ) / np.sqrt(2.0)
    spectrum = ComponentSpectrum(
        dimension=3,
        batches=(
            ComponentBatch(
                indices=np.asarray([[0]]),
                eigenvalues=np.asarray([[2.5]]),
                eigenvectors=None,
            ),
            ComponentBatch(
                indices=np.asarray([[1, 2]]),
                eigenvalues=np.asarray([[-0.4, 1.2]]),
                eigenvectors=rotation[None, :, :],
            ),
        ),
        source_nnz=5,
        component_count=2,
        maximum_component_size=2,
        retained_complex_elements=7,
    )
    expected = np.zeros((3, 3), dtype=np.complex128)
    expected[0, 0] = 2.5
    expected[1:, 1:] = (rotation * np.asarray([-0.4, 1.2])) @ rotation.conj().T
    assert np.allclose(reconstruct_component_spectrum(spectrum), expected, atol=1e-14)


def test_complex128_and_clongdouble_formal_series_agree() -> None:
    x = np.asarray([[0.2, 0.3], [0.3, -0.1]], dtype=np.complex128)
    y = np.asarray([[0.0, -0.2j], [0.2j, 0.4]], dtype=np.complex128)
    steps = [(0, 0.5), (1, 1.0), (0, 0.5)]
    value_128 = effective_hamiltonian_series_dtype(
        [x, y], steps, FORMAL_MAXIMUM_ORDER, np.complex128
    )
    value_long = effective_hamiltonian_series_dtype(
        [x, y], steps, FORMAL_MAXIMUM_ORDER, np.clongdouble
    )
    assert _relative(value_128[0], value_long[0]) < 1e-14
    for order in (4, 6, 8):
        assert _relative(value_128[order], value_long[order]) < 1e-8


def test_arb_formal_series_is_invariant_to_large_group_identity_shifts() -> None:
    x = np.asarray([[0.2, 0.3], [0.3, -0.1]], dtype=np.complex128)
    y = np.asarray([[0.0, -0.2j], [0.2j, 0.4]], dtype=np.complex128)
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    steps = list(iter_s2_sequence_steps(2, sequence))
    reference, _ = effective_hamiltonian_series_arb(
        [x, y], steps, 8, precision_bits=256
    )
    identity = np.eye(2, dtype=np.complex128)
    shifted, _ = effective_hamiltonian_series_arb(
        [x + 1000.0 * identity, y - 300.0 * identity],
        steps,
        8,
        precision_bits=256,
    )
    for order in (4, 6, 8):
        assert _relative(shifted[order], reference[order]) < 1e-11
    hamiltonian = x + y
    forbidden = max(
        _frobenius(reference[order]) / _frobenius(hamiltonian)
        for order in (1, 2, 3, 5, 7)
    )
    assert forbidden < 1e-12


def test_midpoint_identity_gauge_preserves_group_sum() -> None:
    groups = [
        np.diag([-10.0, 3.0]).astype(np.complex128),
        np.asarray([[1.0, 0.2], [0.2, 7.0]], dtype=np.complex128),
    ]
    centered, shifts, total = center_group_identity_components(groups)
    identity = np.eye(2, dtype=np.complex128)
    assert np.allclose(sum(centered) + total * identity, sum(groups), atol=1e-14)
    assert total == pytest.approx(sum(shifts))


def test_reference_unwrapped_log_is_energy_origin_invariant() -> None:
    hamiltonian = np.diag([-31.4, 4.0]).astype(np.complex128)
    time_value = 0.1
    unitary = expm(1j * time_value * hamiltonian)
    energies, vectors = np.linalg.eigh(hamiltonian)
    record = _finite_log_record(unitary, time_value, energies, vectors)
    assert _relative(record["effective_hamiltonian"], hamiltonian) < 1e-13
    assert record["principal_branch_cut_margin_radians"] < 0.01
    assert record["branch_cut_margin_radians"] > 3.0

    energy_shift = 20.0
    shifted_hamiltonian = hamiltonian + energy_shift * np.eye(2)
    shifted_unitary = np.exp(1j * energy_shift * time_value) * unitary
    shifted_energies, shifted_vectors = np.linalg.eigh(shifted_hamiltonian)
    shifted_record = _finite_log_record(
        shifted_unitary,
        time_value,
        shifted_energies,
        shifted_vectors,
    )
    assert _relative(
        shifted_record["effective_hamiltonian"], shifted_hamiltonian
    ) < 1e-13
    assert shifted_record["branch_cut_margin_radians"] == pytest.approx(
        record["branch_cut_margin_radians"], abs=1e-13
    )


def test_a8_state_mixing_identity() -> None:
    hamiltonian = np.diag([0.0, 2.0, 5.0]).astype(np.complex128)
    state = np.asarray([1.0, 0.0, 0.0], dtype=np.complex128)
    d4 = np.asarray(
        [[0.3, 0.4, 0.2j], [0.4, 0.0, 0.0], [-0.2j, 0.0, 0.0]],
        dtype=np.complex128,
    )
    d8 = np.diag([1.7, 0.0, 0.0]).astype(np.complex128)
    result = decompose_a8_state_mixing(hamiltonian, state, d4, d8)
    expected_mix = -(0.4**2) / 2.0 - (0.2**2) / 5.0
    assert result["d8_expectation_hartree"] == pytest.approx(1.7)
    assert result["d4_second_order_mixing_hartree"] == pytest.approx(expected_mix)
    assert result["a8_from_components_hartree"] == pytest.approx(1.7 + expected_mix)


def test_circular_phase_gap_across_branch_cut() -> None:
    phases = np.asarray([np.pi - 0.02, -np.pi + 0.03, 0.2])
    values = np.exp(1j * phases)
    assert circular_phase_gap(values, 0) == pytest.approx(0.05)


def test_source_identity_failure_is_explicit() -> None:
    with pytest.raises(SourceIdentityError, match="hash"):
        require_checks(
            [
                {
                    "check_id": "hash",
                    "measured": False,
                    "threshold": True,
                    "comparison": "==",
                    "passed": False,
                }
            ],
            SourceIdentityError,
        )


def test_diagnostic_points_cannot_be_truth_or_fit_inputs() -> None:
    assert NEW_DIRECT_TRUTH_POINT_COUNT == 0
    for source in ("reused_committed_point", "new_predeclared_f05_diagnostic"):
        annotation = diagnostic_annotations(source)
        assert annotation["point_role"] == "f05_diagnostic_only"
        assert annotation["used_as_direct_truth"] is False
        assert annotation["used_for_model_fit"] is False
        assert annotation["used_for_cost_validation"] is False


def test_runner_reads_the_exact_frozen_protocol() -> None:
    assert hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest() == EXPECTED_PROTOCOL_SHA256
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    assert protocol["phase_gap_grid_relative_to_t_ana"] == [
        0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 0.85,
        0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.25,
    ]
    windows = protocol["operator_expansion"]["finite_log_windows_relative_to_t_ana"]
    assert [row["window_id"] for row in windows] == ["lower", "middle", "upper"]
    assert [row["bins"] for row in windows] == [11, 14, 16]
