from __future__ import annotations

from dataclasses import dataclass
import multiprocessing as mp
import os
from time import perf_counter
from typing import Sequence, Tuple

import numpy as np

from openfermion.ops import QubitOperator

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, ParameterExpression
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp, Statevector

from .config import (
    PFLabel,
    POOL_PROCESSES,
    QISKIT_AER_TARGET_GPUS,
    QISKIT_SIMULATOR_DEVICE,
)
from .qiskit_time_evolution_utils import (
    AerParameterizedTemplate,
    apply_time_evolution,
    build_parameterized_aer_template,
    run_parameterized_aer_template,
    term_to_sparse_pauli,
)
from .pf_decomposition import iter_s2_sequence_steps
from .product_formula import _get_s2_sequence


@dataclass(frozen=True)
class CliqueHamiltonian:
    """Reusable Qiskit Hamiltonian for one commuting clique."""

    hamiltonian: SparsePauliOp | None
    exp_term_count: int


_GROUPED_GPU_TEMPLATE: AerParameterizedTemplate | None = None
_GROUPED_GPU_STATE: np.ndarray | None = None
_GROUPED_GPU_ROTATION_COUNT = 0


def build_clique_hamiltonian(
    commuting_clique: Sequence[QubitOperator],
    num_qubits: int,
) -> CliqueHamiltonian:
    """Convert a clique to one SparsePauliOp without repeated tensor products."""
    pauli_terms: list[tuple[str, float]] = []
    for hamiltonian in commuting_clique:
        for term, coeff in hamiltonian.terms.items():
            if not term:
                continue
            label = ["I"] * int(num_qubits)
            for index, pauli_op_name in term:
                label[int(index)] = str(pauli_op_name)
            pauli_terms.append(("".join(label), float(np.real(coeff))))
    if not pauli_terms:
        return CliqueHamiltonian(hamiltonian=None, exp_term_count=0)
    return CliqueHamiltonian(
        hamiltonian=SparsePauliOp.from_list(pauli_terms),
        exp_term_count=len(pauli_terms),
    )


def _build_clique_hamiltonian_worker(
    args: tuple[Sequence[QubitOperator], int],
) -> CliqueHamiltonian:
    commuting_clique, num_qubits = args
    return build_clique_hamiltonian(commuting_clique, int(num_qubits))


def build_clique_hamiltonians(
    commuting_cliques: Sequence[Sequence[QubitOperator]],
    num_qubits: int,
    *,
    processes: int = 1,
) -> tuple[CliqueHamiltonian, ...]:
    """Build every clique Hamiltonian once, optionally using CPU workers."""
    task_args = [
        (tuple(commuting_clique), int(num_qubits))
        for commuting_clique in commuting_cliques
    ]
    if int(processes) <= 1 or len(task_args) <= 1:
        return tuple(_build_clique_hamiltonian_worker(args) for args in task_args)
    process_count = max(1, min(int(processes), len(task_args)))
    try:
        context = mp.get_context("fork")
    except ValueError:
        context = mp.get_context()
    with context.Pool(processes=process_count) as pool:
        return tuple(
            pool.map(_build_clique_hamiltonian_worker, task_args, chunksize=1)
        )


def add_clique_to_circuit_grouper(
    commuting_clique: Sequence[QubitOperator],
    time: float | ParameterExpression,
    num_qubits: int,
    weight: float,
    circuit: QuantumCircuit,
) -> int:
    """Append one clique, preserving the legacy one-time-point API."""
    clique_hamiltonian: SparsePauliOp | None = None
    exp_term_count = 0
    for hamiltonian in commuting_clique:
        for term, coeff in hamiltonian.terms.items():
            if not term:
                continue
            pauli_op = term_to_sparse_pauli(tuple(term), num_qubits)
            pauli_op = coeff.real * pauli_op
            clique_hamiltonian = (
                pauli_op
                if clique_hamiltonian is None
                else (clique_hamiltonian + pauli_op)
            )
            exp_term_count += 1
    if clique_hamiltonian is None:
        return 0
    circuit.append(
        PauliEvolutionGate(
            clique_hamiltonian,
            time=(weight * time),
            synthesis=None,
        ),
        range(num_qubits),
    )
    return exp_term_count


def add_precomputed_clique_to_circuit_grouper(
    clique_hamiltonian: CliqueHamiltonian,
    time: float | ParameterExpression,
    num_qubits: int,
    weight: float,
    circuit: QuantumCircuit,
) -> int:
    """Append one already converted clique Hamiltonian."""
    if clique_hamiltonian.hamiltonian is None:
        return 0
    circuit.append(
        PauliEvolutionGate(
            clique_hamiltonian.hamiltonian,
            time=(weight * time),
            synthesis=None,
        ),
        range(num_qubits),
    )
    return int(clique_hamiltonian.exp_term_count)


def w_trotter_grouper(
    circuit: QuantumCircuit,
    commuting_cliques: Sequence[Sequence[QubitOperator]],
    time: float | ParameterExpression,
    num_qubits: int,
    pf_label: PFLabel,
) -> int:
    """Append a PF sequence using the original clique representation."""
    sequence = _get_s2_sequence(pf_label)
    exp_term_count = 0
    for term_idx, weight in iter_s2_sequence_steps(
        len(commuting_cliques), sequence
    ):
        exp_term_count += add_clique_to_circuit_grouper(
            commuting_cliques[term_idx],
            time,
            num_qubits,
            weight,
            circuit,
        )
    return exp_term_count


def w_trotter_grouper_precomputed(
    circuit: QuantumCircuit,
    clique_hamiltonians: Sequence[CliqueHamiltonian],
    time: float | ParameterExpression,
    num_qubits: int,
    pf_label: PFLabel,
) -> int:
    """Append a PF sequence while reusing precomputed clique Hamiltonians."""
    sequence = _get_s2_sequence(pf_label)
    exp_term_count = 0
    for term_idx, weight in iter_s2_sequence_steps(
        len(clique_hamiltonians), sequence
    ):
        exp_term_count += add_precomputed_clique_to_circuit_grouper(
            clique_hamiltonians[term_idx],
            time,
            num_qubits,
            weight,
            circuit,
        )
    return exp_term_count


def tEvolution_vector_grouper(
    commuting_cliques: Sequence[Sequence[QubitOperator]],
    time: float,
    num_qubits: int,
    state_vec: np.ndarray,
    pf_label: PFLabel,
) -> Tuple[float, Statevector, int]:
    """Legacy one-time-point grouped evolution."""
    evolution_circuit = QuantumCircuit(num_qubits)
    exp_term_count = w_trotter_grouper(
        evolution_circuit,
        commuting_cliques,
        time,
        num_qubits,
        pf_label,
    )
    final_statevector = apply_time_evolution(state_vec, evolution_circuit)
    return time, final_statevector, exp_term_count


def tEvolution_vector_grouper_precomputed(
    clique_hamiltonians: Sequence[CliqueHamiltonian],
    time: float,
    num_qubits: int,
    state_vec: np.ndarray,
    pf_label: PFLabel,
) -> Tuple[float, Statevector, int]:
    """One-time-point evolution reusing precomputed clique Hamiltonians."""
    evolution_circuit = QuantumCircuit(num_qubits)
    exp_term_count = w_trotter_grouper_precomputed(
        evolution_circuit,
        clique_hamiltonians,
        time,
        num_qubits,
        pf_label,
    )
    final_statevector = apply_time_evolution(state_vec, evolution_circuit)
    return time, final_statevector, exp_term_count


def _set_grouped_gpu_worker_state(
    template: AerParameterizedTemplate | None,
    state_vector: np.ndarray | None,
    rotation_count: int,
) -> None:
    global _GROUPED_GPU_TEMPLATE, _GROUPED_GPU_STATE, _GROUPED_GPU_ROTATION_COUNT
    _GROUPED_GPU_TEMPLATE = template
    _GROUPED_GPU_STATE = state_vector
    _GROUPED_GPU_ROTATION_COUNT = int(rotation_count)


def _run_grouped_gpu_bucket(
    args: tuple[int | None, str | None, tuple[tuple[int, float], ...]],
) -> list[tuple[int, float, Statevector, int, dict[str, object]]]:
    gpu_id, cuda_visible_device, indexed_times = args
    if _GROUPED_GPU_TEMPLATE is None or _GROUPED_GPU_STATE is None:
        raise RuntimeError("Grouped GPU worker was not initialized.")
    if cuda_visible_device is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(cuda_visible_device)
    results = []
    for index, time_value in indexed_times:
        evolved, profile = run_parameterized_aer_template(
            _GROUPED_GPU_TEMPLATE,
            _GROUPED_GPU_STATE,
            parameter_value=float(time_value),
            device="GPU",
            target_gpus=(),
        )
        profile = dict(profile)
        profile["assigned_gpu_id"] = (
            None if gpu_id is None else int(gpu_id)
        )
        profile["worker_cuda_visible_devices"] = cuda_visible_device
        results.append(
            (
                int(index),
                float(time_value),
                evolved,
                int(_GROUPED_GPU_ROTATION_COUNT),
                profile,
            )
        )
    return results


def _unique_gpu_ids(values: Sequence[int]) -> tuple[int, ...]:
    return tuple(dict.fromkeys(int(value) for value in values))


def _resolve_worker_cuda_visible_device(gpu_id: int | None) -> str | None:
    if gpu_id is None:
        return None
    current = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if not current:
        return str(int(gpu_id))
    visible_devices = [value.strip() for value in current.split(",") if value.strip()]
    requested = str(int(gpu_id))
    # When CUDA_VISIBLE_DEVICES restricts the process, Qiskit/Aer GPU IDs are
    # logical indices into that visible set.  Resolve those first: for
    # CUDA_VISIBLE_DEVICES=1,7, logical GPU 1 must map to physical GPU 7, not
    # back to the identically numbered physical GPU 1.
    if 0 <= int(gpu_id) < len(visible_devices):
        return visible_devices[int(gpu_id)]
    if requested in visible_devices:
        return requested
    raise ValueError(
        f"GPU ID {gpu_id} is outside CUDA_VISIBLE_DEVICES={current!r}"
    )


def tEvolution_vectors_grouper_optimized(
    commuting_cliques: Sequence[Sequence[QubitOperator]],
    times: Sequence[float],
    num_qubits: int,
    state_vec: np.ndarray,
    pf_label: PFLabel,
    *,
    device: str | None = None,
    target_gpus: Sequence[int] | None = None,
    processes: int | None = None,
    optimization_level: int = 0,
) -> tuple[list[Tuple[float, Statevector, int]], dict[str, object]]:
    """Evaluate a time grid with reusable cliques and one GPU transpilation.

    When multiple target GPU IDs are configured, complete time points are
    assigned round-robin to one worker per GPU. CUDA visibility is never
    changed here; IDs are interpreted in the caller's existing visible set.
    """
    normalized_device = (device or QISKIT_SIMULATOR_DEVICE).strip().upper()
    if normalized_device not in {"CPU", "GPU"}:
        raise ValueError("device must be either CPU or GPU")
    time_values = [float(value) for value in times]
    if not time_values:
        return [], {
            "execution_strategy": "empty_time_grid",
            "device": normalized_device,
            "processes": 0,
        }

    requested_processes = int(
        POOL_PROCESSES if processes is None else processes
    )
    if requested_processes < 1:
        raise ValueError("processes must be at least 1")

    precompute_started = perf_counter()
    clique_hamiltonians = build_clique_hamiltonians(
        commuting_cliques,
        int(num_qubits),
        processes=min(requested_processes, len(commuting_cliques)),
    )
    clique_precompute_seconds = perf_counter() - precompute_started
    state_flat = np.asarray(state_vec, dtype=complex).reshape(-1)

    if normalized_device == "CPU":
        results: list[Tuple[float, Statevector, int]] = []
        run_started = perf_counter()
        for time_value in time_values:
            circuit = QuantumCircuit(int(num_qubits))
            rotation_count = w_trotter_grouper_precomputed(
                circuit,
                clique_hamiltonians,
                float(time_value),
                int(num_qubits),
                pf_label,
            )
            evolved = Statevector(state_flat).evolve(circuit)
            results.append((float(time_value), evolved, int(rotation_count)))
        return results, {
            "execution_strategy": "precomputed_cliques_cpu",
            "device": "CPU",
            "processes": 1,
            "num_cliques": len(clique_hamiltonians),
            "clique_precompute_seconds": float(clique_precompute_seconds),
            "simulation_seconds": float(perf_counter() - run_started),
        }

    parameter = Parameter("t")
    template_circuit = QuantumCircuit(int(num_qubits))
    rotation_count = w_trotter_grouper_precomputed(
        template_circuit,
        clique_hamiltonians,
        parameter,
        int(num_qubits),
        pf_label,
    )
    template = build_parameterized_aer_template(
        template_circuit,
        parameter_name=parameter.name,
        device="GPU",
        optimization_level=int(optimization_level),
    )

    configured_gpu_ids = _unique_gpu_ids(
        QISKIT_AER_TARGET_GPUS if target_gpus is None else target_gpus
    )
    gpu_slots: tuple[int | None, ...] = (
        tuple(configured_gpu_ids) if configured_gpu_ids else (None,)
    )
    resolved_processes = min(
        requested_processes,
        len(gpu_slots),
        len(time_values),
    )
    active_gpu_slots = gpu_slots[:resolved_processes]
    active_cuda_visible_devices = tuple(
        _resolve_worker_cuda_visible_device(gpu_id)
        for gpu_id in active_gpu_slots
    )
    buckets: list[list[tuple[int, float]]] = [
        [] for _ in range(resolved_processes)
    ]
    for index, time_value in enumerate(time_values):
        buckets[index % resolved_processes].append((index, time_value))
    bucket_args = [
        (
            active_gpu_slots[index],
            active_cuda_visible_devices[index],
            tuple(bucket),
        )
        for index, bucket in enumerate(buckets)
    ]

    simulation_started = perf_counter()
    _set_grouped_gpu_worker_state(template, state_flat, rotation_count)
    try:
        if resolved_processes == 1 and not configured_gpu_ids:
            raw_bucket_results = [_run_grouped_gpu_bucket(bucket_args[0])]
        else:
            # Aer 0.15.1 has no target_gpus option. Spawn clean workers so
            # each can set its own CUDA visibility before importing Aer.
            context = mp.get_context("spawn")
            with context.Pool(
                processes=resolved_processes,
                initializer=_set_grouped_gpu_worker_state,
                initargs=(template, state_flat, rotation_count),
            ) as pool:
                raw_bucket_results = list(
                    pool.map(_run_grouped_gpu_bucket, bucket_args, chunksize=1)
                )
    finally:
        _set_grouped_gpu_worker_state(None, None, 0)

    flat_results = [
        item for bucket_result in raw_bucket_results for item in bucket_result
    ]
    flat_results.sort(key=lambda item: item[0])
    results = [
        (time_value, evolved, count)
        for _, time_value, evolved, count, _ in flat_results
    ]
    time_profiles = [dict(item[4]) for item in flat_results]
    return results, {
        "execution_strategy": "precomputed_cliques_parameterized_gpu",
        "device": "GPU",
        "processes": int(resolved_processes),
        "target_gpus": [
            int(value) for value in active_gpu_slots if value is not None
        ],
        "worker_cuda_visible_devices": [
            value for value in active_cuda_visible_devices if value is not None
        ],
        "num_cliques": len(clique_hamiltonians),
        "pauli_rotations_per_step": int(rotation_count),
        "clique_precompute_seconds": float(clique_precompute_seconds),
        "template_prepare": dict(template.prepare_profile),
        "simulation_seconds": float(perf_counter() - simulation_started),
        "time_profiles": time_profiles,
    }
