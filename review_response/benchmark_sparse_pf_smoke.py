"""Measure one m5 PF application without running an iterative eigensolver.

The H6 reference paths build the exact PF unitary in the conserved sector on
CPU or GPU.  The matrix-free path prepares the same grouped PF as a
parameterized Qiskit circuit and applies it to the full statevector with Aer
GPU.  H8 is deliberately restricted to the matrix-free path.
"""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import threading
import time
import traceback
from typing import Any, Sequence

import numpy as np
from openfermion.linalg import get_sparse_operator
from openfermion.ops import QubitOperator
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from scipy.linalg import eigh
from scipy.sparse import identity as sparse_identity

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.config import DECOMPO_NUM
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.product_formula import _get_s2_sequence

# This import must precede CuPy/qiskit_aer.  It preloads the CUDA wheel
# libraries in the same process without changing the shared server.
from trotterlib.qiskit_time_evolution_grouping import (  # noqa: E402
    build_clique_hamiltonians,
    w_trotter_grouper_precomputed,
)
from trotterlib.qiskit_time_evolution_utils import (  # noqa: E402
    available_aer_devices,
    build_parameterized_aer_template,
    run_parameterized_aer_template,
)


LABEL = "4th(m5_best)"
STATE_TOLERANCE = 1e-10


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() or None


def _gpu_info(physical_gpu_id: int) -> dict[str, Any]:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
            "-i",
            str(int(physical_gpu_id)),
        ],
        text=True,
        capture_output=True,
        check=True,
        timeout=90,
    )
    fields = [field.strip() for field in result.stdout.strip().split(",")]
    if len(fields) != 7:
        raise RuntimeError(f"Unexpected nvidia-smi result: {result.stdout!r}")
    return {
        "physical_gpu_id": int(fields[0]),
        "name": fields[1],
        "uuid": fields[2],
        "driver_version": fields[3],
        "memory_used_mib": int(fields[4]),
        "memory_total_mib": int(fields[5]),
        "utilization_percent": int(fields[6]),
    }


def _environment(physical_gpu_id: int | None) -> dict[str, Any]:
    return {
        "created_at": _now(),
        "git_commit": _git_commit(),
        "python": platform.python_version(),
        "python_executable": os.path.realpath(os.sys.executable),
        "platform": platform.platform(),
        "packages": {
            name: _version(name)
            for name in (
                "numpy",
                "scipy",
                "qiskit",
                "qiskit-aer",
                "qiskit-aer-gpu",
                "cupy-cuda12x",
                "pyscf",
                "openfermion",
            )
        },
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "aer_available_devices": (
            list(available_aer_devices()) if physical_gpu_id is not None else None
        ),
        "gpu_before_run": (
            _gpu_info(physical_gpu_id) if physical_gpu_id is not None else None
        ),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


class GpuMemoryMonitor:
    """Record device-wide and current-Python GPU memory without NVML installs."""

    def __init__(self, physical_gpu_id: int, interval_ms: int = 250):
        self.physical_gpu_id = int(physical_gpu_id)
        self.interval_ms = int(interval_ms)
        self.pid = os.getpid()
        self.baseline = _gpu_info(self.physical_gpu_id)["memory_used_mib"]
        self.device_samples: list[int] = []
        self.process_samples: list[int] = []
        self.errors: list[str] = []
        self._device_process: subprocess.Popen[str] | None = None
        self._app_process: subprocess.Popen[str] | None = None
        self._threads: list[threading.Thread] = []

    def __enter__(self) -> "GpuMemoryMonitor":
        self._device_process = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
                "-i",
                str(self.physical_gpu_id),
                "-lms",
                str(self.interval_ms),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._app_process = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
                "-i",
                str(self.physical_gpu_id),
                "-lms",
                str(self.interval_ms),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        for process, target in (
            (self._device_process, self._read_device),
            (self._app_process, self._read_apps),
        ):
            thread = threading.Thread(target=target, args=(process,), daemon=True)
            thread.start()
            self._threads.append(thread)
        return self

    def _read_device(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            try:
                self.device_samples.append(int(line.strip()))
            except ValueError:
                continue

    def _read_apps(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            fields = [field.strip() for field in line.split(",")]
            if len(fields) != 2:
                continue
            try:
                if int(fields[0]) == self.pid:
                    self.process_samples.append(int(fields[1]))
            except ValueError:
                continue

    def __exit__(self, exc_type, exc, tb) -> None:
        for process in (self._device_process, self._app_process):
            if process is not None and process.poll() is None:
                process.terminate()
        for process in (self._device_process, self._app_process):
            if process is None:
                continue
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if process.stderr is not None:
                error = process.stderr.read().strip()
                if error:
                    self.errors.append(error)
        for thread in self._threads:
            thread.join(timeout=5)

    def summary(self) -> dict[str, Any]:
        device_peak = max(self.device_samples) if self.device_samples else None
        process_peak = max(self.process_samples) if self.process_samples else None
        return {
            "physical_gpu_id": self.physical_gpu_id,
            "baseline_device_used_mib": self.baseline,
            "peak_device_used_mib": device_peak,
            "peak_device_delta_mib": (
                None if device_peak is None else int(device_peak - self.baseline)
            ),
            "peak_current_process_used_mib": process_peak,
            "device_sample_count": len(self.device_samples),
            "process_sample_count": len(self.process_samples),
            "sampling_interval_ms": self.interval_ms,
            "shared_device_caveat": (
                "device-wide delta may include unrelated processes; the current-PID "
                "peak is preferred when available"
            ),
            "errors": self.errors,
        }


def _as_group_operator(group: Any) -> QubitOperator:
    if isinstance(group, QubitOperator):
        return group
    result = QubitOperator()
    for operator in group:
        result += operator
    return result


def _basis_indices(
    num_qubits: int, state: np.ndarray, matrices: Sequence[Any]
) -> tuple[np.ndarray, dict[str, Any]]:
    support = np.flatnonzero(np.abs(state) > 1e-12)
    all_indices = np.arange(1 << num_qubits)
    bitstrings = [format(index, f"0{num_qubits}b") for index in all_indices]
    half = num_qubits // 2
    half_counts = {
        (
            bitstrings[int(index)][:half].count("1"),
            bitstrings[int(index)][half:].count("1"),
        )
        for index in support
    }
    candidates: list[tuple[str, tuple[int, ...], np.ndarray]] = []
    if len(half_counts) == 1:
        counts = next(iter(half_counts))
        candidates.append(
            (
                "fixed_half_populations",
                counts,
                np.asarray(
                    [
                        index
                        for index, bits in enumerate(bitstrings)
                        if (bits[:half].count("1"), bits[half:].count("1"))
                        == counts
                    ],
                    dtype=int,
                ),
            )
        )
    total_counts = {bitstrings[int(index)].count("1") for index in support}
    if len(total_counts) == 1:
        count = next(iter(total_counts))
        candidates.append(
            (
                "fixed_total_population",
                (count,),
                np.asarray(
                    [
                        index
                        for index, bits in enumerate(bitstrings)
                        if bits.count("1") == count
                    ],
                    dtype=int,
                ),
            )
        )
    candidates.append(("full_hilbert_space", (), all_indices))
    for kind, counts, indices in candidates:
        outside = np.setdiff1d(all_indices, indices)
        leakage = max(
            (
                float(
                    np.sqrt(np.sum(np.abs(matrix[outside, :][:, indices].data) ** 2))
                )
                for matrix in matrices
            ),
            default=0.0,
        )
        outside_norm = float(np.linalg.norm(state[outside])) if outside.size else 0.0
        if leakage <= 1e-11 and outside_norm <= 1e-11:
            return indices, {
                "kind": kind,
                "population_counts": list(counts),
                "dimension": int(indices.size),
                "maximum_group_leakage_frobenius_norm": leakage,
                "ground_state_outside_norm": outside_norm,
            }
    raise RuntimeError("No conserved basis sector contains the ground state")


def _prepare_source(h_chain: int) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        source = _prepare_system(int(h_chain))
    state = np.asarray(source["state"], dtype=np.complex128).reshape(-1)
    state /= np.linalg.norm(state)
    source = dict(source)
    source["state"] = state
    return source, float(time.perf_counter() - started)


def _prepare_dense(h_chain: int) -> dict[str, Any]:
    source, chemistry_seconds = _prepare_source(h_chain)
    dense_started = time.perf_counter()
    num_qubits = int(source["num_qubits"])
    state = source["state"]
    identity = sparse_identity(1 << num_qubits, dtype=complex, format="csr")
    full_matrices = []
    for group in source["groups"]:
        operator = _as_group_operator(group)
        constant = operator.terms.get((), 0.0)
        matrix = get_sparse_operator(operator, num_qubits).tocsr()
        full_matrices.append(matrix - constant * identity)
    indices, sector = _basis_indices(num_qubits, state, full_matrices)
    sector_state = np.asarray(state[indices], dtype=np.complex128)
    sector_state /= np.linalg.norm(sector_state)
    sector_matrices = [matrix[indices, :][:, indices].tocsr() for matrix in full_matrices]
    spectra_started = time.perf_counter()
    spectra = []
    for index, matrix in enumerate(sector_matrices, start=1):
        spectra.append(eigh(matrix.toarray(), overwrite_a=True, check_finite=False))
        if index == 1 or index % 10 == 0 or index == len(sector_matrices):
            print(
                f"H{h_chain}: sector spectrum {index}/{len(sector_matrices)}",
                flush=True,
            )
    spectra_seconds = time.perf_counter() - spectra_started
    action = sum(
        (matrix @ sector_state for matrix in sector_matrices),
        np.zeros_like(sector_state),
    )
    residual = float(
        np.linalg.norm(
            action - float(source["energy_without_constant"]) * sector_state
        )
    )
    if residual > 1e-9:
        raise RuntimeError(f"H{h_chain} sector ground-state residual is {residual}")
    return {
        "source": source,
        "sector_indices": indices,
        "sector_state": sector_state,
        "spectra": spectra,
        "sector": {
            **sector,
            "ground_state_eigenpair_residual": residual,
            "dense_complex_matrix_gib": float(
                16 * sector_state.size * sector_state.size / 2**30
            ),
        },
        "chemistry_and_fci_seconds": chemistry_seconds,
        "sector_and_spectra_seconds": float(time.perf_counter() - dense_started),
        "group_diagonalization_seconds": float(spectra_seconds),
    }


def _serialize_groups(groups: Sequence[Any]) -> list[list[dict[str, Any]]]:
    serialized = []
    for group in groups:
        operator = _as_group_operator(group)
        terms = []
        for term, coefficient in operator.terms.items():
            value = complex(coefficient)
            terms.append(
                {
                    "term": [[int(index), str(pauli)] for index, pauli in term],
                    "coefficient": {"real": float(value.real), "imag": float(value.imag)},
                }
            )
        serialized.append(terms)
    return serialized


def _deserialize_groups(
    serialized: Sequence[Sequence[dict[str, Any]]],
) -> list[list[QubitOperator]]:
    groups = []
    for terms in serialized:
        operator = QubitOperator()
        for item in terms:
            term = tuple((int(index), str(pauli)) for index, pauli in item["term"])
            coefficient = complex(
                float(item["coefficient"]["real"]),
                float(item["coefficient"]["imag"]),
            )
            operator += QubitOperator(term, coefficient)
        groups.append([operator])
    return groups


def prepare_shared_h6(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "one shared H6 Hamiltonian, orbital basis, and ground state",
        "status": "running",
        "started_at": _now(),
        "git_commit": _git_commit(),
    }
    _atomic_json(args.output, payload)
    try:
        started = time.perf_counter()
        system = _prepare_dense(6)
        arrays: dict[str, np.ndarray] = {
            "full_ground_state": np.asarray(
                system["source"]["state"], dtype=np.complex128
            ),
            "sector_indices": np.asarray(system["sector_indices"], dtype=np.int64),
            "sector_ground_state": np.asarray(
                system["sector_state"], dtype=np.complex128
            ),
        }
        for index, (values, vectors) in enumerate(system["spectra"]):
            arrays[f"spectrum_values_{index:03d}"] = np.asarray(values, dtype=float)
            arrays[f"spectrum_vectors_{index:03d}"] = np.asarray(
                vectors, dtype=np.complex128
            )
        args.arrays_output.parent.mkdir(parents=True, exist_ok=True)
        np.savez(args.arrays_output, **arrays)
        elapsed = float(time.perf_counter() - started)
        payload.update(
            {
                "status": "complete",
                "arrays_artifact": str(args.arrays_output.resolve()),
                "h_chain": 6,
                "ham_name": system["source"]["ham_name"],
                "num_qubits": int(system["source"]["num_qubits"]),
                "num_groups": len(system["spectra"]),
                "energy_without_constant_hartree": float(
                    system["source"]["energy_without_constant"]
                ),
                "groups": _serialize_groups(system["source"]["groups"]),
                "sector": system["sector"],
                "ground_state_diagnostics": system["source"].get(
                    "ground_state_diagnostics"
                ),
                "timing_seconds": {
                    "chemistry_and_fci": system["chemistry_and_fci_seconds"],
                    "sector_and_group_spectra": system["sector_and_spectra_seconds"],
                    "shared_preparation_total": elapsed,
                },
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 1


def _load_shared_h6(path: Path, *, dense: bool) -> dict[str, Any]:
    started = time.perf_counter()
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("status") != "complete" or int(metadata.get("h_chain", -1)) != 6:
        raise RuntimeError(f"Shared H6 input is not complete: {path}")
    with np.load(metadata["arrays_artifact"], allow_pickle=False) as arrays:
        full_state = np.asarray(arrays["full_ground_state"], dtype=np.complex128)
        result: dict[str, Any] = {
            "source": {
                "ham_name": metadata["ham_name"],
                "num_qubits": int(metadata["num_qubits"]),
                "groups": _deserialize_groups(metadata["groups"]),
                "energy_without_constant": float(
                    metadata["energy_without_constant_hartree"]
                ),
                "state": full_state,
                "ground_state_diagnostics": metadata.get(
                    "ground_state_diagnostics"
                ),
            },
            "shared_preparation_timing_seconds": metadata["timing_seconds"],
            "shared_input": str(path.resolve()),
        }
        if dense:
            result.update(
                {
                    "sector_indices": np.asarray(
                        arrays["sector_indices"], dtype=np.int64
                    ),
                    "sector_state": np.asarray(
                        arrays["sector_ground_state"], dtype=np.complex128
                    ),
                    "spectra": [
                        (
                            np.asarray(
                                arrays[f"spectrum_values_{index:03d}"], dtype=float
                            ),
                            np.asarray(
                                arrays[f"spectrum_vectors_{index:03d}"],
                                dtype=np.complex128,
                            ),
                        )
                        for index in range(int(metadata["num_groups"]))
                    ],
                    "sector": metadata["sector"],
                }
            )
    result["shared_input_load_seconds"] = float(time.perf_counter() - started)
    return result


def _prepare_for_worker(args: argparse.Namespace, *, dense: bool) -> dict[str, Any]:
    if args.shared_input is not None:
        if int(args.h_chain) != 6:
            raise ValueError("The shared input is valid only for H6")
        return _load_shared_h6(args.shared_input, dense=dense)
    if dense:
        return _prepare_dense(args.h_chain)
    source, chemistry_seconds = _prepare_source(args.h_chain)
    return {
        "source": source,
        "chemistry_and_fci_seconds": chemistry_seconds,
        "shared_input_load_seconds": 0.0,
        "shared_input": None,
    }


def _left_apply_cpu(
    matrix: np.ndarray,
    spectrum: tuple[np.ndarray, np.ndarray],
    scaled_time: float,
) -> np.ndarray:
    values, vectors = spectrum
    return vectors @ (
        np.exp(1j * scaled_time * values)[:, None]
        * (vectors.conj().T @ matrix)
    )


def _build_cpu_unitary(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]], time_value: float
) -> tuple[np.ndarray, dict[str, Any]]:
    sequence = list(_get_s2_sequence(LABEL))
    unitary = np.eye(spectra[0][0].size, dtype=np.complex128)
    blocks: dict[float, np.ndarray] = {}
    started = time.perf_counter()
    for raw_weight in sequence:
        weight = float(raw_weight)
        block = blocks.get(weight)
        if block is None:
            block = np.eye(unitary.shape[0], dtype=np.complex128)
            for group_index, factor in iter_s2_sequence_steps(len(spectra), [weight]):
                block = _left_apply_cpu(
                    block, spectra[group_index], time_value * float(factor)
                )
            blocks[weight] = block
        unitary = block @ unitary
    return unitary, {
        "seconds": float(time.perf_counter() - started),
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(blocks),
    }


def _full_state(
    sector_state: np.ndarray, indices: np.ndarray, num_qubits: int
) -> np.ndarray:
    state = np.zeros(1 << int(num_qubits), dtype=np.complex128)
    state[indices] = sector_state
    return state


def _save_state(path: Path, state: np.ndarray, indices: np.ndarray | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if indices is None:
        np.savez_compressed(path, state=np.asarray(state, dtype=np.complex128))
    else:
        np.savez_compressed(
            path,
            state=np.asarray(state, dtype=np.complex128),
            sector_indices=np.asarray(indices, dtype=np.int64),
        )


def _base_payload(args: argparse.Namespace, method: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "purpose": "single PF application dense-versus-matrix-free smoke benchmark",
        "status": "running",
        "method": method,
        "configuration": {
            "h_chain": int(args.h_chain),
            "label": LABEL,
            "t_ana": float(args.t_ana),
            "t_ana_source": args.t_ana_source,
            "relative_time_factor": 0.5,
            "time": float(0.5 * args.t_ana),
            "measurement_repeats": 1,
            "iterative_eigensolver_used": False,
        },
        "started_at": _now(),
    }


def run_cpu_dense(args: argparse.Namespace) -> int:
    payload = _base_payload(args, "cpu_dense_sector_s2_cache")
    payload["environment"] = _environment(None)
    _atomic_json(args.output, payload)
    started = time.perf_counter()
    try:
        system = _prepare_for_worker(args, dense=True)
        warmup_started = time.perf_counter()
        np.eye(8, dtype=np.complex128) @ np.ones(8, dtype=np.complex128)
        warmup_seconds = time.perf_counter() - warmup_started
        unitary, build = _build_cpu_unitary(
            system["spectra"], 0.5 * float(args.t_ana)
        )
        apply_started = time.perf_counter()
        final_sector_state = unitary @ system["sector_state"]
        apply_seconds = time.perf_counter() - apply_started
        final_state = _full_state(
            final_sector_state,
            system["sector_indices"],
            system["source"]["num_qubits"],
        )
        _save_state(args.state_output, final_state, system["sector_indices"])
        shared_timing = system.get("shared_preparation_timing_seconds")
        preprocessing = float(
            system["shared_input_load_seconds"]
            if shared_timing is not None
            else system["chemistry_and_fci_seconds"]
            + system["sector_and_spectra_seconds"]
        )
        payload.update(
            {
                "status": "complete",
                "system": {
                    "num_qubits": int(system["source"]["num_qubits"]),
                    "full_state_dimension": int(final_state.size),
                    "num_commuting_groups": len(system["spectra"]),
                    "sector": system["sector"],
                    "ground_state_diagnostics": system["source"].get(
                        "ground_state_diagnostics"
                    ),
                    "used_scipy_eigsh": False,
                },
                "timing_seconds": {
                    "warmup_excluded": float(warmup_seconds),
                    "shared_preparation_once": (
                        None
                        if shared_timing is None
                        else shared_timing["shared_preparation_total"]
                    ),
                    "local_shared_input_load": system.get(
                        "shared_input_load_seconds"
                    ),
                    "chemistry_and_fci": system.get("chemistry_and_fci_seconds"),
                    "sector_and_group_spectra": system.get(
                        "sector_and_spectra_seconds"
                    ),
                    "preprocessing": float(preprocessing),
                    "pf_unitary_construction": build["seconds"],
                    "pf_application_matvec": float(apply_seconds),
                    "data_transfer": 0.0,
                    "measurement_without_preprocessing": float(
                        build["seconds"] + apply_seconds
                    ),
                    "total": float(time.perf_counter() - started),
                },
                "pf": {
                    **build,
                    "pauli_rotations_per_application": int(
                        DECOMPO_NUM[f"H{args.h_chain}"][LABEL]
                    ),
                    "applications": 1,
                },
                "checks": {
                    "final_state_norm": float(np.linalg.norm(final_state)),
                    "input_output_overlap": _jsonable(
                        complex(np.vdot(system["source"]["state"], final_state))
                    ),
                },
                "state_artifact": str(args.state_output),
                "shared_input": system.get("shared_input"),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 1


def _build_gpu_unitary(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    time_value: float,
) -> tuple[Any, dict[str, Any], list[tuple[Any, Any]]]:
    import cupy as cp

    transfer_started = time.perf_counter()
    gpu_spectra = [(cp.asarray(values), cp.asarray(vectors)) for values, vectors in spectra]
    cp.cuda.Stream.null.synchronize()
    transfer_seconds = time.perf_counter() - transfer_started
    sequence = list(_get_s2_sequence(LABEL))
    dimension = int(spectra[0][0].size)
    unitary = cp.eye(dimension, dtype=cp.complex128)
    blocks: dict[float, Any] = {}
    build_started = time.perf_counter()
    for raw_weight in sequence:
        weight = float(raw_weight)
        block = blocks.get(weight)
        if block is None:
            block = cp.eye(dimension, dtype=cp.complex128)
            for group_index, factor in iter_s2_sequence_steps(
                len(gpu_spectra), [weight]
            ):
                values, vectors = gpu_spectra[group_index]
                phases = cp.exp(1j * time_value * float(factor) * values)
                block = vectors @ (phases[:, None] * (vectors.conj().T @ block))
            blocks[weight] = block
        unitary = block @ unitary
    cp.cuda.Stream.null.synchronize()
    return unitary, {
        "input_spectra_transfer_seconds": float(transfer_seconds),
        "seconds": float(time.perf_counter() - build_started),
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(blocks),
    }, gpu_spectra


def run_gpu_dense(args: argparse.Namespace) -> int:
    payload = _base_payload(args, "gpu_dense_sector_s2_cache")
    payload["environment"] = _environment(args.physical_gpu_id)
    _atomic_json(args.output, payload)
    started = time.perf_counter()
    try:
        visible = [value for value in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if value]
        if visible != [str(args.physical_gpu_id)]:
            raise RuntimeError(
                f"Expected CUDA_VISIBLE_DEVICES={args.physical_gpu_id}, got {visible}"
            )
        initial = _gpu_info(args.physical_gpu_id)
        if initial["memory_used_mib"] * 2 > initial["memory_total_mib"]:
            raise RuntimeError("Assigned GPU no longer has at least half its memory free")
        system = _prepare_for_worker(args, dense=True)
        import cupy as cp

        warmup_started = time.perf_counter()
        warmup = cp.eye(8, dtype=cp.complex128) @ cp.ones(8, dtype=cp.complex128)
        cp.cuda.Stream.null.synchronize()
        del warmup
        warmup_seconds = time.perf_counter() - warmup_started
        with GpuMemoryMonitor(args.physical_gpu_id) as monitor:
            unitary, build, gpu_spectra = _build_gpu_unitary(
                system["spectra"], 0.5 * float(args.t_ana)
            )
            state_transfer_started = time.perf_counter()
            gpu_state = cp.asarray(system["sector_state"])
            cp.cuda.Stream.null.synchronize()
            state_h2d_seconds = time.perf_counter() - state_transfer_started
            apply_started = time.perf_counter()
            gpu_final = unitary @ gpu_state
            cp.cuda.Stream.null.synchronize()
            apply_seconds = time.perf_counter() - apply_started
            output_started = time.perf_counter()
            final_sector_state = cp.asnumpy(gpu_final)
            cp.cuda.Stream.null.synchronize()
            output_d2h_seconds = time.perf_counter() - output_started
            pool_peak_bytes = int(cp.get_default_memory_pool().total_bytes())
            del gpu_final, gpu_state, unitary, gpu_spectra
        final_state = _full_state(
            final_sector_state,
            system["sector_indices"],
            system["source"]["num_qubits"],
        )
        _save_state(args.state_output, final_state, system["sector_indices"])
        shared_timing = system.get("shared_preparation_timing_seconds")
        preprocessing = float(
            system["shared_input_load_seconds"]
            if shared_timing is not None
            else system["chemistry_and_fci_seconds"]
            + system["sector_and_spectra_seconds"]
        )
        total_transfer = (
            build["input_spectra_transfer_seconds"]
            + state_h2d_seconds
            + output_d2h_seconds
        )
        payload.update(
            {
                "status": "complete",
                "system": {
                    "num_qubits": int(system["source"]["num_qubits"]),
                    "full_state_dimension": int(final_state.size),
                    "num_commuting_groups": len(system["spectra"]),
                    "sector": system["sector"],
                    "ground_state_diagnostics": system["source"].get(
                        "ground_state_diagnostics"
                    ),
                    "used_scipy_eigsh": False,
                },
                "timing_seconds": {
                    "warmup_excluded": float(warmup_seconds),
                    "shared_preparation_once": (
                        None
                        if shared_timing is None
                        else shared_timing["shared_preparation_total"]
                    ),
                    "local_shared_input_load": system.get(
                        "shared_input_load_seconds"
                    ),
                    "chemistry_and_fci": system.get("chemistry_and_fci_seconds"),
                    "sector_and_group_spectra": system.get(
                        "sector_and_spectra_seconds"
                    ),
                    "preprocessing": float(preprocessing),
                    "spectra_h2d": build["input_spectra_transfer_seconds"],
                    "state_h2d": float(state_h2d_seconds),
                    "pf_unitary_construction": build["seconds"],
                    "pf_application_matvec": float(apply_seconds),
                    "result_d2h": float(output_d2h_seconds),
                    "data_transfer": float(total_transfer),
                    "measurement_without_preprocessing": float(
                        total_transfer + build["seconds"] + apply_seconds
                    ),
                    "total": float(time.perf_counter() - started),
                },
                "pf": {
                    **build,
                    "pauli_rotations_per_application": int(
                        DECOMPO_NUM[f"H{args.h_chain}"][LABEL]
                    ),
                    "applications": 1,
                },
                "checks": {
                    "final_state_norm": float(np.linalg.norm(final_state)),
                    "input_output_overlap": _jsonable(
                        complex(np.vdot(system["source"]["state"], final_state))
                    ),
                },
                "state_artifact": str(args.state_output),
                "shared_input": system.get("shared_input"),
                "gpu_memory": {
                    **monitor.summary(),
                    "cupy_pool_peak_reserved_mib": float(pool_peak_bytes / 2**20),
                },
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 1


def _warmup_aer() -> dict[str, Any]:
    parameter = Parameter("warmup_tau")
    body = QuantumCircuit(1)
    body.rz(parameter, 0)
    template = build_parameterized_aer_template(
        body,
        parameter_name=parameter.name,
        device="GPU",
        optimization_level=0,
    )
    _, profile = run_parameterized_aer_template(
        template,
        np.asarray([1.0, 0.0], dtype=np.complex128),
        parameter_value=0.125,
        device="GPU",
        target_gpus=(),
    )
    return {"template": template.prepare_profile, "run": profile}


def run_aer_matrix_free(args: argparse.Namespace) -> int:
    payload = _base_payload(args, "qiskit_aer_gpu_matrix_free_full_statevector")
    payload["environment"] = _environment(args.physical_gpu_id)
    _atomic_json(args.output, payload)
    started = time.perf_counter()
    try:
        visible = [value for value in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if value]
        if visible != [str(args.physical_gpu_id)]:
            raise RuntimeError(
                f"Expected CUDA_VISIBLE_DEVICES={args.physical_gpu_id}, got {visible}"
            )
        initial = _gpu_info(args.physical_gpu_id)
        if initial["memory_used_mib"] * 2 > initial["memory_total_mib"]:
            raise RuntimeError("Assigned GPU no longer has at least half its memory free")
        if "GPU" not in available_aer_devices():
            raise RuntimeError("Aer does not report the GPU device")
        prepared = _prepare_for_worker(args, dense=False)
        source = prepared["source"]
        chemistry_seconds = float(prepared.get("chemistry_and_fci_seconds", 0.0))
        shared_load_seconds = float(prepared.get("shared_input_load_seconds", 0.0))
        shared_timing = prepared.get("shared_preparation_timing_seconds")
        state = source["state"]
        warmup_started = time.perf_counter()
        warmup_profile = _warmup_aer()
        warmup_seconds = time.perf_counter() - warmup_started
        clique_started = time.perf_counter()
        cliques = build_clique_hamiltonians(
            source["groups"], int(source["num_qubits"]), processes=1
        )
        clique_seconds = time.perf_counter() - clique_started
        circuit_started = time.perf_counter()
        parameter = Parameter("tau")
        body = QuantumCircuit(int(source["num_qubits"]))
        rotation_count = w_trotter_grouper_precomputed(
            body, cliques, parameter, int(source["num_qubits"]), LABEL
        )
        circuit_seconds = time.perf_counter() - circuit_started
        template = build_parameterized_aer_template(
            body,
            parameter_name=parameter.name,
            device="GPU",
            optimization_level=0,
        )
        expected_rotations = int(DECOMPO_NUM[f"H{args.h_chain}"][LABEL])
        if int(rotation_count) != expected_rotations:
            raise RuntimeError(
                f"PF contains {rotation_count} rotations, expected {expected_rotations}"
            )
        with GpuMemoryMonitor(args.physical_gpu_id) as monitor:
            evolved, run_profile = run_parameterized_aer_template(
                template,
                state,
                parameter_value=-0.5 * float(args.t_ana),
                device="GPU",
                target_gpus=(),
            )
        final_state = np.asarray(evolved.data, dtype=np.complex128)
        _save_state(args.state_output, final_state)
        preprocessing = (
            chemistry_seconds
            + shared_load_seconds
            + clique_seconds
            + circuit_seconds
            + float(template.prepare_profile["total_seconds"])
        )
        host_overhead = float(
            run_profile["total_seconds"] - run_profile["simulator_run_seconds"]
        )
        payload.update(
            {
                "status": "complete",
                "system": {
                    "num_qubits": int(source["num_qubits"]),
                    "full_state_dimension": int(final_state.size),
                    "num_commuting_groups": len(source["groups"]),
                    "ground_state_diagnostics": source.get(
                        "ground_state_diagnostics"
                    ),
                    "used_scipy_eigsh": False,
                },
                "timing_seconds": {
                    "warmup_excluded": float(warmup_seconds),
                    "shared_preparation_once": (
                        None
                        if shared_timing is None
                        else shared_timing["shared_preparation_total"]
                    ),
                    "local_shared_input_load": shared_load_seconds,
                    "chemistry_and_fci": float(chemistry_seconds),
                    "clique_precompute": float(clique_seconds),
                    "parameterized_circuit_build": float(circuit_seconds),
                    "transpile": float(
                        template.prepare_profile["transpile_seconds"]
                    ),
                    "preprocessing": float(preprocessing),
                    "pf_unitary_construction": None,
                    "pf_application_aer_run_including_device_io": float(
                        run_profile["simulator_run_seconds"]
                    ),
                    "host_bind_and_result_overhead": host_overhead,
                    "data_transfer": None,
                    "measurement_without_preprocessing": float(
                        run_profile["total_seconds"]
                    ),
                    "total": float(time.perf_counter() - started),
                },
                "transfer_measurement_note": (
                    "Aer 0.15.1 does not expose H2D/kernel/D2H separately. The Aer "
                    "run includes device I/O; host bind/result overhead is reported "
                    "separately."
                ),
                "pf": {
                    "pauli_rotations_per_application": int(rotation_count),
                    "applications": 1,
                    "dense_group_exponentials_built": 0,
                    "dense_pf_unitaries_built": 0,
                    "input_circuit_instructions": int(len(body.data)),
                    "transpiled_circuit_instructions": int(
                        template.transpiled_num_instructions
                    ),
                },
                "checks": {
                    "final_state_norm": float(np.linalg.norm(final_state)),
                    "input_output_overlap": _jsonable(
                        complex(np.vdot(state, final_state))
                    ),
                },
                "warmup_profile": warmup_profile,
                "template_profile": template.prepare_profile,
                "aer_run_profile": run_profile,
                "state_artifact": str(args.state_output),
                "shared_input": prepared.get("shared_input"),
                "gpu_memory": monitor.summary(),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 1


def _load_state(raw_json: Path) -> tuple[dict[str, Any], np.ndarray]:
    payload = json.loads(raw_json.read_text(encoding="utf-8"))
    if payload.get("status") != "complete":
        raise RuntimeError(f"{raw_json} is not complete")
    artifact = Path(payload["state_artifact"])
    with np.load(artifact) as archive:
        state = np.asarray(archive["state"], dtype=np.complex128)
    return payload, state


def _phase_aligned_difference(
    reference: np.ndarray, candidate: np.ndarray
) -> dict[str, Any]:
    overlap = complex(np.vdot(reference, candidate))
    if abs(overlap) == 0.0:
        raise RuntimeError("Reference and candidate states have zero overlap")
    phase = overlap / abs(overlap)
    aligned = candidate / phase
    difference = float(np.linalg.norm(aligned - reference) / np.linalg.norm(reference))
    return {
        "raw_overlap": _jsonable(overlap),
        "removed_global_phase_rad": float(np.angle(phase)),
        "relative_2_norm_difference": difference,
        "passes_1e-10": bool(difference <= STATE_TOLERANCE),
    }


def attach_external_memory(args: argparse.Namespace) -> int:
    payload = json.loads(args.result_json.read_text(encoding="utf-8"))
    samples: list[tuple[int, int]] = []
    if args.samples_csv.exists():
        for line in args.samples_csv.read_text(encoding="utf-8").splitlines():
            fields = [field.strip() for field in line.split(",")]
            if len(fields) != 2:
                continue
            try:
                samples.append((int(fields[0]), int(fields[1])))
            except ValueError:
                continue
    used = [sample[0] for sample in samples]
    baseline = used[0] if used else None
    peak = max(used) if used else None
    payload["external_gpu_memory"] = {
        "physical_gpu_id": int(args.physical_gpu_id),
        "sampling_started_before_python": True,
        "sampling_interval_ms": int(args.interval_ms),
        "sample_count": len(samples),
        "baseline_device_used_mib": baseline,
        "peak_device_used_mib": peak,
        "peak_device_delta_mib": (
            None if baseline is None or peak is None else int(peak - baseline)
        ),
        "total_device_memory_mib": (
            None if not samples else int(max(sample[1] for sample in samples))
        ),
        "measurement_scope": "whole physical GPU during this worker",
        "shared_device_caveat": (
            "The assigned GPU was required to have at least half its memory free. "
            "Device-wide samples can include a process that starts after assignment."
        ),
        "samples_artifact": str(args.samples_csv),
    }
    _atomic_json(args.result_json, payload)
    return 0 if samples else 1


def verify_h6(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "H6 state agreement after global-phase alignment",
        "status": "running",
        "tolerance": STATE_TOLERANCE,
        "created_at": _now(),
    }
    _atomic_json(args.output, payload)
    try:
        cpu, cpu_state = _load_state(args.cpu_json)
        dense, dense_state = _load_state(args.gpu_dense_json)
        aer, aer_state = _load_state(args.aer_json)
        if not (cpu_state.shape == dense_state.shape == aer_state.shape):
            raise RuntimeError("H6 state shapes differ")
        comparisons = {
            "gpu_dense_vs_cpu_dense": _phase_aligned_difference(
                cpu_state, dense_state
            ),
            "gpu_matrix_free_vs_cpu_dense": _phase_aligned_difference(
                cpu_state, aer_state
            ),
        }
        with np.load(cpu["state_artifact"]) as archive:
            sector_indices = np.asarray(archive["sector_indices"], dtype=np.int64)
        outside = np.ones(cpu_state.size, dtype=bool)
        outside[sector_indices] = False
        leakage = float(np.linalg.norm(aer_state[outside]))
        passed = all(item["passes_1e-10"] for item in comparisons.values())
        payload.update(
            {
                "status": "complete",
                "passed": bool(passed),
                "comparisons": comparisons,
                "gpu_matrix_free_sector_leakage_2_norm": leakage,
                "input_files": [
                    str(args.cpu_json),
                    str(args.gpu_dense_json),
                    str(args.aer_json),
                ],
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0 if passed else 2
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "passed": False,
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 1


def _seconds(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.6g}"


def _memory(payload: dict[str, Any]) -> str:
    external = payload.get("external_gpu_memory")
    if external:
        peak = external.get("peak_device_used_mib")
        delta = external.get("peak_device_delta_mib")
        if peak is not None:
            return f"{peak} MiB peak ({delta} MiB delta)"
    memory = payload.get("gpu_memory")
    if not memory:
        return "n/a"
    process_peak = memory.get("peak_current_process_used_mib")
    if process_peak is not None:
        return f"{process_peak} MiB (PID peak)"
    delta = memory.get("peak_device_delta_mib")
    return "n/a" if delta is None else f"{delta} MiB (device delta)"


def summarize(args: argparse.Namespace) -> int:
    paths = {
        "H6 CPU dense": args.raw_dir / "H6_cpu_dense.json",
        "H6 GPU dense": args.raw_dir / "H6_gpu_dense.json",
        "H6 GPU matrix-free": args.raw_dir / "H6_aer_matrix_free.json",
        "H8 GPU matrix-free": args.raw_dir / "H8_aer_matrix_free.json",
    }
    payloads = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in paths.items()
        if path.exists()
    }
    verification = json.loads(args.verification.read_text(encoding="utf-8"))
    shared_path = args.output_dir / "shared" / "H6_shared_input.json"
    shared = (
        json.loads(shared_path.read_text(encoding="utf-8"))
        if shared_path.exists()
        else None
    )
    shared_summary = (
        None
        if shared is None
        else {
            "status": shared.get("status"),
            "h_chain": shared.get("h_chain"),
            "num_qubits": shared.get("num_qubits"),
            "num_groups": shared.get("num_groups"),
            "sector": shared.get("sector"),
            "timing_seconds": shared.get("timing_seconds"),
            "peak_cpu_rss_kib": shared.get("peak_cpu_rss_kib"),
            "commit_policy": (
                "The 146 MB shared spectra cache is a server-local intermediate "
                "and is intentionally excluded from version control."
            ),
        }
    )
    rows = []
    for name, payload in payloads.items():
        timing = payload.get("timing_seconds", {})
        if "matrix-free" in name:
            action = timing.get("pf_application_aer_run_including_device_io")
        else:
            action = timing.get("pf_application_matvec")
        relative = "n/a"
        if name == "H6 GPU dense":
            relative = f"{verification['comparisons']['gpu_dense_vs_cpu_dense']['relative_2_norm_difference']:.3e}"
        elif name == "H6 GPU matrix-free":
            relative = f"{verification['comparisons']['gpu_matrix_free_vs_cpu_dense']['relative_2_norm_difference']:.3e}"
        rows.append(
            (
                payload["configuration"]["h_chain"],
                name.split(" ", 1)[1],
                _seconds(timing.get("preprocessing")),
                _seconds(timing.get("pf_unitary_construction")),
                _seconds(action),
                _seconds(timing.get("total")),
                _memory(payload),
                relative,
            )
        )
    cpu = payloads.get("H6 CPU dense", {})
    gpu_dense = payloads.get("H6 GPU dense", {})
    matrix_free = payloads.get("H6 GPU matrix-free", {})
    speed: dict[str, Any] = {}
    if cpu and matrix_free:
        cpu_t = cpu["timing_seconds"]
        matrix_t = matrix_free["timing_seconds"]
        speed["cpu_dense_cold_total_over_matrix_free_total"] = (
            cpu_t["total"] / matrix_t["total"]
        )
        speed["cpu_dense_build_plus_matvec_over_matrix_free_run"] = (
            (cpu_t["pf_unitary_construction"] + cpu_t["pf_application_matvec"])
            / matrix_t["pf_application_aer_run_including_device_io"]
        )
        speed["cpu_dense_reused_matvec_over_matrix_free_run"] = (
            cpu_t["pf_application_matvec"]
            / matrix_t["pf_application_aer_run_including_device_io"]
        )
    if gpu_dense and matrix_free:
        dense_t = gpu_dense["timing_seconds"]
        matrix_t = matrix_free["timing_seconds"]
        speed["gpu_dense_build_plus_matvec_over_matrix_free_run"] = (
            (dense_t["pf_unitary_construction"] + dense_t["pf_application_matvec"])
            / matrix_t["pf_application_aer_run_including_device_io"]
        )
        speed["gpu_dense_reused_matvec_over_matrix_free_run"] = (
            dense_t["pf_application_matvec"]
            / matrix_t["pf_application_aer_run_including_device_io"]
        )
    h6_action_times = {}
    h6_cold_times = {}
    if cpu:
        timing = cpu["timing_seconds"]
        h6_action_times["CPU dense reused matvec"] = timing["pf_application_matvec"]
        h6_cold_times["CPU dense build + matvec"] = (
            timing["pf_unitary_construction"] + timing["pf_application_matvec"]
        )
    if gpu_dense:
        timing = gpu_dense["timing_seconds"]
        h6_action_times["GPU dense reused matvec"] = timing["pf_application_matvec"]
        h6_cold_times["GPU dense build + matvec"] = (
            timing["pf_unitary_construction"] + timing["pf_application_matvec"]
        )
    if matrix_free:
        timing = matrix_free["timing_seconds"]
        action = timing["pf_application_aer_run_including_device_io"]
        h6_action_times["GPU matrix-free Aer run"] = action
        h6_cold_times["GPU matrix-free Aer run"] = action
    fastest_reused = min(h6_action_times, key=h6_action_times.get) if h6_action_times else None
    fastest_cold = min(h6_cold_times, key=h6_cold_times.get) if h6_cold_times else None
    summary = {
        "schema_version": 1,
        "status": (
            "complete"
            if len(payloads) == 4
            and all(item.get("status") == "complete" for item in payloads.values())
            else "incomplete"
        ),
        "git_commit": _git_commit(),
        "h6_agreement": verification,
        "h6_shared_preparation": shared_summary,
        "h6_fastest_reused_action": fastest_reused,
        "h6_fastest_cold_action": fastest_cold,
        "speed_ratios": speed,
        "raw_files": {name: str(path) for name, path in paths.items()},
        "created_at": _now(),
    }
    _atomic_json(args.output_dir / "summary.json", summary)
    table = [
        "| 系 | 方式 | 前処理 (s) | 構築 (s) | PF作用 (s) | 総時間 (s) | GPUメモリ | H6相対差 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    table.extend(
        f"| H{h} | {method} | {pre} | {build} | {action} | {total} | {memory} | {difference} |"
        for h, method, pre, build, action, total, memory, difference in rows
    )
    h6_passed = bool(verification.get("passed"))
    h8 = payloads.get("H8 GPU matrix-free", {})
    h8_complete = h8.get("status") == "complete"
    h8_timing = h8.get("timing_seconds", {})
    h8_memory = _memory(h8) if h8 else "n/a"
    shared_seconds = (
        None
        if shared is None
        else shared.get("timing_seconds", {}).get("shared_preparation_total")
    )
    report = "\n".join(
        [
            "# Sparse-style PF smoke benchmark",
            "",
            "Only one `4th(m5_best)` PF application was measured. No iterative, moment/Ritz, Krylov, or dense-PF eigenvalue solver was run. H8 uses the H6 analytic time as a documented runtime-only surrogate because no H8-specific saved `t_ana` exists.",
            "",
            f"The H6 orbital basis, Hamiltonian, ground state, sector, and group spectra were prepared once and shared by all three methods. Shared preparation time: `{_seconds(shared_seconds)} s` (not repeated per method).",
            "",
            *table,
            "",
            "## Speed ratios",
            "",
            "```json",
            json.dumps(_jsonable(speed), indent=2, sort_keys=True),
            "```",
            "",
            "## Conclusions",
            "",
            f"1. H6 GPU matrix-free versus dense reference: **{'PASS' if h6_passed else 'FAIL'}** at relative 2-norm tolerance `{STATE_TOLERANCE:.0e}` after global-phase alignment.",
            f"2. Fastest H6 reused action: **{fastest_reused or 'not available'}**. Fastest action including dense-unitary construction: **{fastest_cold or 'not available'}**.",
            f"3. H8 matrix-free: **{'completed' if h8_complete else 'not completed'}**; PF action `{_seconds(h8_timing.get('pf_application_aer_run_including_device_io'))} s`, total `{_seconds(h8_timing.get('total'))} s`, GPU memory `{h8_memory}`. This one-action smoke test is not an `e_direct` result.",
            "",
        ]
    )
    _atomic_text(args.output_dir / "report.md", report)
    return 0 if summary["status"] == "complete" and h6_passed else 1


def _add_worker_arguments(parser: argparse.ArgumentParser, *, gpu: bool) -> None:
    parser.add_argument("--h-chain", type=int, required=True)
    parser.add_argument("--t-ana", type=float, required=True)
    parser.add_argument("--t-ana-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state-output", type=Path, required=True)
    parser.add_argument("--shared-input", type=Path)
    if gpu:
        parser.add_argument("--physical-gpu-id", type=int, required=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare-h6")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--arrays-output", type=Path, required=True)
    cpu = subparsers.add_parser("cpu-dense")
    _add_worker_arguments(cpu, gpu=False)
    gpu = subparsers.add_parser("gpu-dense")
    _add_worker_arguments(gpu, gpu=True)
    aer = subparsers.add_parser("aer")
    _add_worker_arguments(aer, gpu=True)
    verify = subparsers.add_parser("verify-h6")
    verify.add_argument("--cpu-json", type=Path, required=True)
    verify.add_argument("--gpu-dense-json", type=Path, required=True)
    verify.add_argument("--aer-json", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)
    memory = subparsers.add_parser("attach-memory")
    memory.add_argument("--result-json", type=Path, required=True)
    memory.add_argument("--samples-csv", type=Path, required=True)
    memory.add_argument("--physical-gpu-id", type=int, required=True)
    memory.add_argument("--interval-ms", type=int, default=200)
    report = subparsers.add_parser("summarize")
    report.add_argument("--raw-dir", type=Path, required=True)
    report.add_argument("--verification", type=Path, required=True)
    report.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare-h6":
        status = prepare_shared_h6(args)
    elif args.command == "cpu-dense":
        status = run_cpu_dense(args)
    elif args.command == "gpu-dense":
        status = run_gpu_dense(args)
    elif args.command == "aer":
        status = run_aer_matrix_free(args)
    elif args.command == "verify-h6":
        status = verify_h6(args)
    elif args.command == "attach-memory":
        status = attach_external_memory(args)
    else:
        status = summarize(args)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
