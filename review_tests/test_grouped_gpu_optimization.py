from __future__ import annotations

import numpy as np
import pytest

from openfermion.ops import QubitOperator

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector

from trotterlib.qiskit_time_evolution_grouping import (
    _resolve_worker_cuda_visible_device,
    _unique_gpu_ids,
    build_clique_hamiltonians,
    tEvolution_vectors_grouper_optimized,
    w_trotter_grouper,
    w_trotter_grouper_precomputed,
)
from trotterlib.qiskit_time_evolution_utils import (
    build_parameterized_aer_template,
    run_parameterized_aer_template,
)


def _example_cliques() -> list[list[QubitOperator]]:
    return [
        [
            QubitOperator("X0", 0.25),
            QubitOperator("Z1", -0.4),
        ],
        [QubitOperator("Y0 Y1", 0.15)],
    ]


def _example_state() -> np.ndarray:
    state = np.array([1.0, 0.2j, -0.3, 0.1j], dtype=complex)
    return state / np.linalg.norm(state)


@pytest.mark.parametrize("pf_label", ["2nd", "4th(m5_best)"])
def test_precomputed_cliques_match_legacy_circuit(pf_label: str) -> None:
    cliques = _example_cliques()
    precomputed = build_clique_hamiltonians(cliques, 2)
    legacy = QuantumCircuit(2)
    optimized = QuantumCircuit(2)

    legacy_count = w_trotter_grouper(
        legacy,
        cliques,
        -0.23,
        2,
        pf_label,
    )
    optimized_count = w_trotter_grouper_precomputed(
        optimized,
        precomputed,
        -0.23,
        2,
        pf_label,
    )

    expected = Statevector(_example_state()).evolve(legacy)
    actual = Statevector(_example_state()).evolve(optimized)
    assert optimized_count == legacy_count
    np.testing.assert_allclose(actual.data, expected.data, rtol=1e-12, atol=1e-12)


def test_optimized_cpu_time_grid_matches_concrete_circuits() -> None:
    cliques = _example_cliques()
    state = _example_state()
    times = [-0.12, -0.21, -0.37]

    results, profile = tEvolution_vectors_grouper_optimized(
        cliques,
        times,
        2,
        state,
        "4th(m5_best)",
        device="CPU",
        processes=1,
    )

    assert [item[0] for item in results] == times
    assert profile["execution_strategy"] == "precomputed_cliques_cpu"
    for time_value, evolved, rotation_count in results:
        circuit = QuantumCircuit(2)
        expected_count = w_trotter_grouper(
            circuit,
            cliques,
            time_value,
            2,
            "4th(m5_best)",
        )
        expected = Statevector(state).evolve(circuit)
        assert rotation_count == expected_count
        np.testing.assert_allclose(
            evolved.data,
            expected.data,
            rtol=1e-12,
            atol=1e-12,
        )


def test_parameterized_aer_cpu_template_matches_qiskit_statevector() -> None:
    cliques = _example_cliques()
    state = _example_state()
    precomputed = build_clique_hamiltonians(cliques, 2)
    parameter = Parameter("t")
    template_circuit = QuantumCircuit(2)
    w_trotter_grouper_precomputed(
        template_circuit,
        precomputed,
        parameter,
        2,
        "4th(m5_best)",
    )
    template = build_parameterized_aer_template(
        template_circuit,
        parameter_name=parameter.name,
        device="CPU",
    )

    actual, profile = run_parameterized_aer_template(
        template,
        state,
        parameter_value=-0.29,
        device="CPU",
    )
    concrete = template_circuit.assign_parameters({parameter: -0.29})
    expected = Statevector(state).evolve(concrete)

    assert profile["execution_strategy"] == "pretranspiled_parameterized_body"
    np.testing.assert_allclose(actual.data, expected.data, rtol=1e-12, atol=1e-12)


def test_gpu_ids_are_deduplicated_without_reordering() -> None:
    assert _unique_gpu_ids((3, 1, 3, 2, 1)) == (3, 1, 2)


def test_gpu_id_resolution_respects_existing_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "GPU-a,GPU-b")
    assert _resolve_worker_cuda_visible_device(0) == "GPU-a"
    assert _resolve_worker_cuda_visible_device(1) == "GPU-b"
    with pytest.raises(ValueError, match="outside CUDA_VISIBLE_DEVICES"):
        _resolve_worker_cuda_visible_device(2)


def test_gpu_id_resolution_prefers_logical_index_for_numeric_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "1,7")
    assert _resolve_worker_cuda_visible_device(0) == "1"
    assert _resolve_worker_cuda_visible_device(1) == "7"
