import ctypes
from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import List, Tuple

import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp, Statevector

from .config import (
    PFLabel,
    QISKIT_AER_METHOD,
    QISKIT_AER_PRECISION,
    QISKIT_AER_TARGET_GPUS,
    QISKIT_SIMULATOR_DEVICE,
)
from .product_formula import _get_w_list as _pf_get_w_list


_CUDA_PRELOAD_HANDLES: list[object] = []
_CUDA_PRELOAD_ERRORS: Tuple[str, ...] = ()
_AER_RUNTIME_PREPARED = False

_AER_PARAMETERIZED_BASIS_GATES = (
    "unitary",
    "u",
    "cx",
    "rz",
    "p",
    "x",
    "sx",
    "id",
)


@dataclass(frozen=True)
class AerParameterizedTemplate:
    """Aer-safe circuit body transpiled once with one time parameter."""

    circuit: QuantumCircuit
    parameter_name: str
    num_qubits: int
    optimization_level: int
    input_num_instructions: int
    transpiled_num_instructions: int
    prepare_profile: dict[str, object]


def _prepare_aer_runtime() -> None:
    """Prefer CUDA libraries bundled with the active Python environment.

    ``qiskit-aer-gpu`` installs CUDA wheels alongside Aer.  On shared GPU
    servers, an older system ``libnvJitLink`` can otherwise be loaded before
    the matching wheel libraries and make even the Aer CPU backend fail to
    import.  Loading the wheel libraries in dependency order keeps the fix
    local to this Python process and does not modify the server environment.
    """
    global _AER_RUNTIME_PREPARED, _CUDA_PRELOAD_ERRORS
    if _AER_RUNTIME_PREPARED:
        return
    _AER_RUNTIME_PREPARED = True

    site_packages_roots = (
        Path(sys.prefix)
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages",
        Path(sys.prefix)
        / "lib64"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages",
    )
    library_paths = (
        Path("nvidia/nvjitlink/lib/libnvJitLink.so.12"),
        Path("nvidia/cuda_runtime/lib/libcudart.so.12"),
        Path("nvidia/cublas/lib/libcublasLt.so.12"),
        Path("nvidia/cublas/lib/libcublas.so.12"),
        Path("nvidia/cusparse/lib/libcusparse.so.12"),
        Path("nvidia/cusolver/lib/libcusolver.so.11"),
    )

    cuda_lib_dirs: list[str] = []
    errors: list[str] = []
    mode = getattr(ctypes, "RTLD_GLOBAL", 0)
    for site_packages in site_packages_roots:
        for relative_path in library_paths:
            library_path = site_packages / relative_path
            if not library_path.is_file():
                continue
            library_dir = str(library_path.parent)
            if library_dir not in cuda_lib_dirs:
                cuda_lib_dirs.append(library_dir)
            try:
                _CUDA_PRELOAD_HANDLES.append(
                    ctypes.CDLL(str(library_path), mode=mode)
                )
            except OSError as exc:
                errors.append(f"{library_path}: {exc}")

    current_dirs = [
        path for path in os.environ.get("LD_LIBRARY_PATH", "").split(":") if path
    ]
    merged_dirs = list(dict.fromkeys([*cuda_lib_dirs, *current_dirs]))
    if merged_dirs:
        os.environ["LD_LIBRARY_PATH"] = ":".join(merged_dirs)
    _CUDA_PRELOAD_ERRORS = tuple(errors)


# Match the reference GPU runner's import contract: importing the project
# module is sufficient to prepare the CUDA wheel libraries before a caller
# imports qiskit_aer.  The operation is process-local and is a no-op when the
# active environment does not contain the optional CUDA wheels.
_prepare_aer_runtime()


def free_var(name: str, scope: dict) -> None:
    """ローカル変数を解放して GC を促す（メモリ圧を下げるための補助）。"""
    # スコープから削除して GC を促進
    if name in scope:
        del scope[name]
        import gc

        gc.collect()


@lru_cache(maxsize=None)
def available_aer_devices() -> Tuple[str, ...]:
    """Return the simulator devices provided by the installed Aer package."""
    _prepare_aer_runtime()
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:  # pragma: no cover - depends on server setup
        raise RuntimeError(
            "Qiskit Aer is required for GPU simulation. Install "
            "requirements-gpu.txt on the GPU server."
        ) from exc

    return tuple(str(device).upper() for device in AerSimulator().available_devices())


@lru_cache(maxsize=None)
def _aer_simulator(
    device: str,
    method: str,
    precision: str,
    target_gpus: Tuple[int, ...],
):
    """Construct one Aer backend per worker process and simulator setting."""
    _prepare_aer_runtime()
    from qiskit_aer import AerSimulator

    normalized_device = device.upper()
    devices = available_aer_devices()
    if normalized_device not in devices:
        raise RuntimeError(
            f"Requested Aer device {normalized_device!r}, but this installation "
            f"provides only {devices}. On an NVIDIA server, install "
            "requirements-gpu.txt and check the CUDA/driver setup."
        )

    options = {
        "method": method,
        "device": normalized_device,
        "precision": precision,
    }
    if normalized_device == "GPU":
        # The body circuit is already decomposed and transpiled. Repeating
        # Aer's host-side fusion analysis for every time value is expensive.
        options["fusion_enable"] = False
    simulator = AerSimulator(**options)
    if normalized_device == "GPU" and target_gpus:
        # qiskit-aer-gpu 0.15.1 does not expose target_gpus. Newer builds may
        # support it, so set it only after inspecting the actual backend.
        if "target_gpus" not in vars(simulator.options):
            raise RuntimeError(
                "This Qiskit Aer build does not support target_gpus. "
                "Select one GPU per process with CUDA_VISIBLE_DEVICES instead."
            )
        simulator.set_options(target_gpus=list(target_gpus))
    return simulator


def _find_parameter(circuit: QuantumCircuit, parameter_name: str) -> Parameter:
    matches = [
        parameter
        for parameter in circuit.parameters
        if getattr(parameter, "name", None) == parameter_name
    ]
    if len(matches) != 1:
        raise ValueError(
            "Parameterized Aer circuit must contain exactly one parameter "
            f"named {parameter_name!r}; found {len(matches)}."
        )
    return matches[0]


def build_parameterized_aer_template(
    circuit: QuantumCircuit,
    *,
    parameter_name: str,
    device: str = "GPU",
    optimization_level: int = 0,
) -> AerParameterizedTemplate:
    """Transpile a one-parameter circuit body once for repeated Aer runs."""
    started = perf_counter()
    normalized_device = device.upper()
    if normalized_device not in available_aer_devices():
        raise RuntimeError(
            f"Requested Aer device {normalized_device!r} is not available."
        )
    _find_parameter(circuit, parameter_name)

    transpile_started = perf_counter()
    compiled = transpile(
        circuit,
        basis_gates=list(_AER_PARAMETERIZED_BASIS_GATES),
        optimization_level=int(optimization_level),
    )
    transpile_seconds = perf_counter() - transpile_started
    _find_parameter(compiled, parameter_name)

    unsupported = sorted(
        {
            getattr(instruction.operation, "name", "")
            for instruction in compiled.data
        }
        & {"PauliEvolution", "pauli_evolution", "rzz", "xx_plus_yy"}
    )
    if unsupported:
        raise ValueError(
            "Aer template transpilation left unsupported instructions: "
            f"{unsupported}"
        )

    profile: dict[str, object] = {
        "execution_strategy": "pretranspiled_parameterized_body",
        "device": normalized_device,
        "optimization_level": int(optimization_level),
        "input_num_instructions": int(len(circuit.data)),
        "transpiled_num_instructions": int(len(compiled.data)),
        "transpile_seconds": float(transpile_seconds),
        "total_seconds": float(perf_counter() - started),
    }
    return AerParameterizedTemplate(
        circuit=compiled,
        parameter_name=str(parameter_name),
        num_qubits=int(circuit.num_qubits),
        optimization_level=int(optimization_level),
        input_num_instructions=int(len(circuit.data)),
        transpiled_num_instructions=int(len(compiled.data)),
        prepare_profile=profile,
    )


def run_parameterized_aer_template(
    template: AerParameterizedTemplate,
    eigenvector: np.ndarray,
    *,
    parameter_value: float,
    device: str = "GPU",
    target_gpus: Tuple[int, ...] = (),
) -> tuple[Statevector, dict[str, object]]:
    """Bind one value and run a pretranspiled circuit body without retranspiling."""
    started = perf_counter()
    initial_state = np.asarray(eigenvector, dtype=complex).reshape(-1)
    expected_size = 1 << int(template.num_qubits)
    if initial_state.size != expected_size:
        raise ValueError(
            f"Initial state has size {initial_state.size}, expected {expected_size}"
        )

    backend = _aer_simulator(
        device.upper(),
        QISKIT_AER_METHOD,
        QISKIT_AER_PRECISION,
        tuple(int(value) for value in target_gpus),
    )

    bind_started = perf_counter()
    simulation_circuit = QuantumCircuit(template.num_qubits)
    simulation_circuit.set_statevector(initial_state)
    simulation_circuit.compose(template.circuit, inplace=True, copy=False)
    simulation_circuit.save_statevector()
    parameter = _find_parameter(simulation_circuit, template.parameter_name)
    bound_circuit = simulation_circuit.assign_parameters(
        {parameter: float(parameter_value)},
        inplace=False,
    )
    bind_seconds = perf_counter() - bind_started

    run_started = perf_counter()
    result = backend.run(bound_circuit).result()
    run_seconds = perf_counter() - run_started
    if not result.success:
        raise RuntimeError(f"Aer simulation failed: {result.status}")
    statevector = Statevector(
        np.asarray(result.get_statevector(0), dtype=complex)
    )
    profile: dict[str, object] = {
        "execution_strategy": "pretranspiled_parameterized_body",
        "device": device.upper(),
        "target_gpus": [int(value) for value in target_gpus],
        "parameter_value": float(parameter_value),
        "bind_seconds": float(bind_seconds),
        "simulator_run_seconds": float(run_seconds),
        "total_seconds": float(perf_counter() - started),
    }
    return statevector, profile


def _apply_time_evolution_aer(
    eigenvector: np.ndarray,
    time_evolution_circuit: QuantumCircuit,
    *,
    device: str,
) -> Statevector:
    """Apply a circuit to an arbitrary state using an Aer CPU/GPU backend."""
    initial_state = np.asarray(eigenvector, dtype=complex).reshape(-1)
    expected_size = 1 << time_evolution_circuit.num_qubits
    if initial_state.size != expected_size:
        raise ValueError(
            f"Initial state has size {initial_state.size}, expected {expected_size}"
        )

    backend = _aer_simulator(
        device.upper(),
        QISKIT_AER_METHOD,
        QISKIT_AER_PRECISION,
        QISKIT_AER_TARGET_GPUS,
    )
    simulation_circuit = QuantumCircuit(time_evolution_circuit.num_qubits)
    simulation_circuit.set_statevector(initial_state)
    simulation_circuit.compose(time_evolution_circuit, inplace=True)
    simulation_circuit.save_statevector()
    compiled = transpile(simulation_circuit, backend, optimization_level=0)
    result = backend.run(compiled).result()
    if not result.success:
        raise RuntimeError(f"Aer simulation failed: {result.status}")
    return Statevector(np.asarray(result.get_statevector(0), dtype=complex))


def apply_time_evolution(
    eigenvector: np.ndarray, time_evolution_circuit: QuantumCircuit
) -> Statevector:
    """Apply the circuit with Qiskit CPU or Aer GPU statevector simulation.

    The default CPU path preserves the previous ``Statevector.evolve``
    behavior. Set ``TROTTER_QISKIT_DEVICE=GPU`` before importing trotterlib to
    select the Aer GPU path.
    """
    if QISKIT_SIMULATOR_DEVICE == "GPU":
        return _apply_time_evolution_aer(
            eigenvector,
            time_evolution_circuit,
            device="GPU",
        )
    return Statevector(eigenvector).evolve(time_evolution_circuit)


def term_to_sparse_pauli(
    term: Tuple[Tuple[int, str], ...],
    n_qubits: int,
) -> SparsePauliOp:
    """OpenFermion term を Qiskit の SparsePauliOp に変換する。"""
    # 注意: 右端が q0（Qiskit）。既存挙動維持のためラベル反転は行わない。
    X = SparsePauliOp("X")
    Y = SparsePauliOp("Y")
    Z = SparsePauliOp("Z")
    I = SparsePauliOp("I")
    pauli_dict = {"I": I, "X": X, "Y": Y, "Z": Z}
    pauli_operators = [I] * n_qubits
    for index, pauli_op_name in term:
        pauli_operators[index] = pauli_dict[pauli_op_name]
    pauli_op = pauli_operators[0]
    for op in pauli_operators[1:]:
        pauli_op ^= op
    return pauli_op


def _get_w_list(num_w: PFLabel) -> List[float]:
    """積公式パラメータ w の系列を取得（分岐を関数化）。"""
    # product_formula 側の実装を使用
    return _pf_get_w_list(num_w)
