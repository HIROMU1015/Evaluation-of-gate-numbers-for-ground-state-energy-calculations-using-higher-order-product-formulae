from __future__ import annotations

import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp, Statevector

import trotterlib.qiskit_time_evolution_utils as evolution_utils


def test_aer_cpu_path_matches_qiskit_statevector_evolve() -> None:
    initial_state = np.array([1, 1j, -0.5, 0.25j], dtype=complex)
    initial_state /= np.linalg.norm(initial_state)
    circuit = QuantumCircuit(2)
    circuit.global_phase = 0.23
    circuit.append(PauliEvolutionGate(SparsePauliOp("XZ"), time=0.17), [0, 1])
    circuit.cx(0, 1)
    circuit.rz(-0.31, 0)

    expected = Statevector(initial_state).evolve(circuit)
    actual = evolution_utils._apply_time_evolution_aer(
        initial_state,
        circuit,
        device="CPU",
    )

    np.testing.assert_allclose(actual.data, expected.data, rtol=1e-12, atol=1e-12)


def test_gpu_setting_dispatches_to_aer(monkeypatch) -> None:
    initial_state = np.array([1.0, 0.0], dtype=complex)
    circuit = QuantumCircuit(1)
    sentinel = Statevector([0.0, 1.0])
    calls: list[str] = []

    def fake_apply(eigenvector, time_evolution_circuit, *, device):
        assert np.array_equal(eigenvector, initial_state)
        assert time_evolution_circuit is circuit
        calls.append(device)
        return sentinel

    monkeypatch.setattr(evolution_utils, "QISKIT_SIMULATOR_DEVICE", "GPU")
    monkeypatch.setattr(evolution_utils, "_apply_time_evolution_aer", fake_apply)

    assert evolution_utils.apply_time_evolution(initial_state, circuit) is sentinel
    assert calls == ["GPU"]
