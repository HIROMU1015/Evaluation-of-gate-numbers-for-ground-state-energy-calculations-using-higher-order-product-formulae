"""Benchmark direct and matrix-free PF eigenphase solvers on H chains.

The dense methods work only in the particle/spin conservation sector.  The
matrix-free method applies the grouped PF circuit to full statevectors with
Qiskit Aer GPU and constructs unitary Krylov/Ritz approximations from one
reusable sequence of overlap moments.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
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
from typing import Any, Callable, Sequence

import numpy as np
from openfermion.linalg import get_sparse_operator
from openfermion.ops import QubitOperator
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from scipy.linalg import eigh, schur
from scipy.sparse import identity as sparse_identity

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.product_formula import _get_s2_sequence

# Import this before CuPy.  It preloads the CUDA wheel libraries used by Aer.
from trotterlib.qiskit_time_evolution_grouping import (  # noqa: E402
    build_clique_hamiltonians,
    w_trotter_grouper_precomputed,
)
from trotterlib.qiskit_time_evolution_utils import (  # noqa: E402
    available_aer_devices,
    build_parameterized_aer_template,
    run_parameterized_aer_template,
)


LABELS = ("4th(m5_best)", "8th(Morales-Y8m10b)")
DEFAULT_FACTORS = (0.5, 0.7, 1.0)
DEFAULT_K_VALUES = (8, 16, 32, 64, 96)
DEFAULT_GRAM_CUTOFFS = (1e-10, 1e-12, 1e-14)
DIRECT_ABS_SHIFT_TOL = 1e-10
DIRECT_COST_REL_TOL = 1e-6
DIRECT_RESIDUAL_TOL = 1e-9
PROXY_EPSILON_FRACTION_TOL = 0.02
PROXY_COST_REL_TOL = 0.02
PROXY_PAIR_RATIO_REL_TOL = 0.02
PROXY_LAST_THREE_COST_CHANGE_TOL = 0.01


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
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


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], text=True, capture_output=True, check=False
    )
    return completed.stdout.strip() or None


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _query_gpu(gpu_id: int) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
            "-i",
            str(int(gpu_id)),
        ],
        text=True,
        capture_output=True,
        check=True,
        timeout=90,
    )
    fields = [item.strip() for item in completed.stdout.strip().split(",")]
    if len(fields) != 7:
        raise RuntimeError(f"Unexpected nvidia-smi output: {completed.stdout!r}")
    return {
        "physical_gpu_id": int(fields[0]),
        "name": fields[1],
        "uuid": fields[2],
        "driver_version": fields[3],
        "memory_used_mib": int(fields[4]),
        "memory_total_mib": int(fields[5]),
        "utilization_percent": int(fields[6]),
    }


class GpuMemoryMonitor:
    def __init__(self, gpu_id: int, interval_ms: int = 200):
        self.gpu_id = int(gpu_id)
        self.interval_ms = int(interval_ms)
        self.samples: list[int] = []
        self.errors: list[str] = []
        self.process: subprocess.Popen[str] | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> "GpuMemoryMonitor":
        self.process = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
                "-i",
                str(self.gpu_id),
                "-lms",
                str(self.interval_ms),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        return self

    def _read(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        try:
            for line in self.process.stdout:
                try:
                    self.samples.append(int(line.strip()))
                except ValueError:
                    continue
        except Exception as exc:  # pragma: no cover - server dependent
            self.errors.append(f"{type(exc).__name__}: {exc}")

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.thread is not None:
            self.thread.join(timeout=5)
        if self.process is not None and self.process.stderr is not None:
            error = self.process.stderr.read().strip()
            if error:
                self.errors.append(error)

    def summary(self, baseline_mib: int) -> dict[str, Any]:
        peak = max(self.samples) if self.samples else None
        return {
            "baseline_mib": int(baseline_mib),
            "peak_used_mib": peak,
            "peak_delta_mib": None if peak is None else int(peak - baseline_mib),
            "sample_count": len(self.samples),
            "sampling_interval_ms": self.interval_ms,
            "errors": self.errors,
        }


def _environment(gpu_id: int) -> dict[str, Any]:
    smi = subprocess.run(
        ["nvidia-smi"], text=True, capture_output=True, check=False, timeout=90
    )
    return {
        "created_at": _now(),
        "git_commit": _git_commit(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "python_executable": os.path.realpath(os.sys.executable),
        "packages": {
            name: _package_version(name)
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
        "aer_available_devices": list(available_aer_devices()),
        "gpu": _query_gpu(gpu_id),
        "nvidia_smi_header": smi.stdout.splitlines()[2].strip()
        if len(smi.stdout.splitlines()) > 2
        else None,
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def _as_group_operator(group: Any) -> QubitOperator:
    if isinstance(group, QubitOperator):
        return group
    result = QubitOperator()
    for operator in group:
        result += operator
    return result


def _basis_indices(
    num_qubits: int,
    ground_state: np.ndarray,
    matrices: Sequence[Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    support = np.flatnonzero(np.abs(ground_state) > 1e-12)
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
                    np.sqrt(
                        np.sum(np.abs(matrix[outside, :][:, indices].data) ** 2)
                    )
                )
                for matrix in matrices
            ),
            default=0.0,
        )
        outside_norm = float(
            np.linalg.norm(ground_state[outside]) if outside.size else 0.0
        )
        if leakage <= 1e-11 and outside_norm <= 1e-11:
            return indices, {
                "kind": kind,
                "population_counts": list(counts),
                "dimension": int(indices.size),
                "max_group_leakage_frobenius_norm": leakage,
                "ground_state_outside_norm": outside_norm,
            }
    raise RuntimeError("No invariant basis sector contains the ground state")


def prepare_system(h_chain: int, *, dense: bool) -> dict[str, Any]:
    started = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        source = _prepare_system(int(h_chain))
    num_qubits = int(source["num_qubits"])
    full_state = np.asarray(source["state"], dtype=np.complex128).reshape(-1)
    full_state /= np.linalg.norm(full_state)
    result = {
        "h_chain": int(h_chain),
        "ham_name": source["ham_name"],
        "num_qubits": num_qubits,
        "groups": source["groups"],
        "full_ground_state": full_state,
        "ground_energy_without_constant_hartree": float(
            source["energy_without_constant"]
        ),
        "ground_state_diagnostics": source.get("ground_state_diagnostics"),
        "preparation_seconds_before_dense_sector": float(time.perf_counter() - started),
    }
    if not dense:
        return result

    group_operators = [_as_group_operator(group) for group in source["groups"]]
    identity = sparse_identity(1 << num_qubits, dtype=complex, format="csr")
    full_sparse = []
    for operator in group_operators:
        constant = operator.terms.get((), 0.0)
        matrix = get_sparse_operator(operator, num_qubits).tocsr()
        full_sparse.append(matrix - constant * identity)
    indices, sector = _basis_indices(num_qubits, full_state, full_sparse)
    sector_state = full_state[indices].copy()
    sector_state /= np.linalg.norm(sector_state)
    sector_sparse = [matrix[indices, :][:, indices].tocsr() for matrix in full_sparse]
    action = sum(
        (matrix @ sector_state for matrix in sector_sparse),
        np.zeros_like(sector_state),
    )
    residual = float(
        np.linalg.norm(
            action - result["ground_energy_without_constant_hartree"] * sector_state
        )
    )
    if residual > 1e-9:
        raise RuntimeError(f"H{h_chain} ground-state sector residual is {residual}")
    del full_sparse, group_operators, identity, action

    spectra = []
    diagonalization_started = time.perf_counter()
    for index, sparse_matrix in enumerate(sector_sparse, start=1):
        dense_matrix = sparse_matrix.toarray()
        spectra.append(eigh(dense_matrix, overwrite_a=True, check_finite=False))
        if index == 1 or index % 10 == 0 or index == len(sector_sparse):
            print(
                f"H{h_chain}: group spectrum {index}/{len(sector_sparse)}",
                flush=True,
            )
    dimension = int(sector_state.size)
    sector.update(
        {
            "ground_state_eigenpair_residual": residual,
            "dense_complex_matrix_bytes": int(16 * dimension * dimension),
            "dense_complex_matrix_gib": float(16 * dimension * dimension / 2**30),
            "retained_group_spectra_estimated_bytes": int(
                len(spectra) * (16 * dimension * dimension + 8 * dimension)
            ),
            "group_diagonalization_seconds": float(
                time.perf_counter() - diagonalization_started
            ),
        }
    )
    result.update(
        {
            "sector_indices": indices,
            "sector_ground_state": sector_state,
            "group_spectra": spectra,
            "sector": sector,
            "preparation_seconds": float(time.perf_counter() - started),
        }
    )
    return result


def _stage_cpu(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]], time_value: float, weight: float
) -> np.ndarray:
    dimension = spectra[0][0].size
    stage = np.eye(dimension, dtype=np.complex128)
    for group_index, factor in iter_s2_sequence_steps(len(spectra), [weight]):
        values, vectors = spectra[group_index]
        phases = np.exp(1j * time_value * factor * values)
        stage = ((vectors * phases) @ vectors.conj().T) @ stage
    return stage


def build_pf_unitary_cpu(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    time_value: float,
    label: str,
    *,
    reuse_palindromic_stages: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    sequence = list(_get_s2_sequence(label))
    dimension = spectra[0][0].size
    unitary = np.eye(dimension, dtype=np.complex128)
    cache: dict[float, np.ndarray] = {}
    stage_build_seconds = 0.0
    assembly_started = time.perf_counter()
    for weight in sequence:
        if reuse_palindromic_stages and weight in cache:
            stage = cache[weight]
        else:
            stage_started = time.perf_counter()
            stage = _stage_cpu(spectra, float(time_value), float(weight))
            stage_build_seconds += time.perf_counter() - stage_started
            if reuse_palindromic_stages:
                cache[weight] = stage
        unitary = stage @ unitary
    return unitary, {
        "wall_seconds": float(time.perf_counter() - assembly_started),
        "stage_build_seconds": float(stage_build_seconds),
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(set(sequence)),
        "stages_built": len(cache) if reuse_palindromic_stages else len(sequence),
    }


def build_pf_unitary_gpu_batch(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    times: Sequence[float],
    label: str,
) -> tuple[np.ndarray, dict[str, Any], list[dict[str, Any]] | None]:
    import cupy as cp

    sequence = list(_get_s2_sequence(label))
    time_values = cp.asarray(times, dtype=cp.float64)
    batch = len(times)
    dimension = spectra[0][0].size
    transfer_started = time.perf_counter()
    gpu_spectra = [
        (cp.asarray(values), cp.asarray(vectors)) for values, vectors in spectra
    ]
    cp.cuda.Stream.null.synchronize()
    input_transfer_seconds = time.perf_counter() - transfer_started

    build_started = time.perf_counter()
    unitary = cp.broadcast_to(
        cp.eye(dimension, dtype=cp.complex128), (batch, dimension, dimension)
    ).copy()
    cache: dict[float, Any] = {}
    for weight in sequence:
        if weight not in cache:
            stage = cp.broadcast_to(
                cp.eye(dimension, dtype=cp.complex128),
                (batch, dimension, dimension),
            ).copy()
            for group_index, factor in iter_s2_sequence_steps(
                len(gpu_spectra), [weight]
            ):
                values, vectors = gpu_spectra[group_index]
                phases = cp.exp(
                    1j * time_values[:, None] * float(factor) * values[None, :]
                )
                gates = (
                    vectors[None, :, :] * phases[:, None, :]
                ) @ vectors.conj().T
                stage = gates @ stage
            cache[weight] = stage
        unitary = cache[weight] @ unitary
    cp.cuda.Stream.null.synchronize()
    gpu_build_seconds = time.perf_counter() - build_started

    gpu_eig: list[dict[str, Any]] | None = None
    cupy_general_eig_available = hasattr(cp.linalg, "eig")
    if dimension <= 128 and cupy_general_eig_available:
        gpu_eig = []
        for index in range(batch):
            eig_started = time.perf_counter()
            values, vectors = cp.linalg.eig(unitary[index])
            cp.cuda.Stream.null.synchronize()
            gpu_eig.append(
                {
                    "seconds": float(time.perf_counter() - eig_started),
                    "eigenvalues": cp.asnumpy(values),
                    "eigenvectors": cp.asnumpy(vectors),
                }
            )

    output_started = time.perf_counter()
    host_unitaries = cp.asnumpy(unitary)
    cp.cuda.Stream.null.synchronize()
    output_transfer_seconds = time.perf_counter() - output_started
    del unitary, cache, gpu_spectra
    cp.get_default_memory_pool().free_all_blocks()
    return host_unitaries, {
        "input_transfer_seconds": float(input_transfer_seconds),
        "gpu_build_seconds": float(gpu_build_seconds),
        "output_transfer_seconds": float(output_transfer_seconds),
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(set(sequence)),
        "batch_size": batch,
        "cupy_general_eig_available": bool(cupy_general_eig_available),
        "cupy_general_eig_decision": (
            "measured separately"
            if gpu_eig is not None
            else "unavailable in this CuPy build; SciPy complex Schur retained"
        ),
    }, gpu_eig


def _cost(time_value: float, error: float, n_exp: int) -> float | None:
    if not math.isfinite(error) or error < 0 or error >= TARGET_ERROR:
        return None
    return float(BETA * n_exp / (time_value * (TARGET_ERROR - error)))


def analyze_eigensystem(
    unitary: np.ndarray,
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    n_exp: int,
    *,
    selection_reference: np.ndarray | None,
) -> tuple[dict[str, Any], np.ndarray]:
    norms = np.linalg.norm(eigenvectors, axis=0)
    eigenvectors = eigenvectors / norms
    ground_overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
    reference = state if selection_reference is None else selection_reference
    tracking_overlaps = np.abs(eigenvectors.conj().T @ reference) ** 2
    selected = int(np.argmax(tracking_overlaps))
    vector = eigenvectors[:, selected]
    eigenvalue = complex(eigenvalues[selected])
    phase = float(np.angle(eigenvalue))
    branch = int(np.rint((energy * time_value - phase) / (2 * np.pi)))
    effective_energy = float((phase + 2 * np.pi * branch) / time_value)
    signed_shift = float(effective_energy - energy)
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    return {
        "signed_eigenvalue_shift_hartree": signed_shift,
        "direct_error_hartree": abs(signed_shift),
        "direct_cost": _cost(time_value, abs(signed_shift), n_exp),
        "effective_energy_hartree": effective_energy,
        "raw_eigenphase_rad": phase,
        "phase_branch_integer": branch,
        "selected_ground_state_overlap_probability": float(
            ground_overlaps[selected]
        ),
        "previous_or_reference_vector_overlap_probability": float(
            tracking_overlaps[selected]
        ),
        "maximum_ground_state_overlap_probability": float(np.max(ground_overlaps)),
        "eigenpair_residual_2_norm": residual,
        "unitarity_residual_frobenius_norm": float(
            np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]))
        ),
    }, vector


def analyze_unitary_schur(
    unitary: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    n_exp: int,
    *,
    selection_reference: np.ndarray | None,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    triangular, vectors = schur(
        np.array(unitary, copy=True),
        output="complex",
        overwrite_a=True,
        check_finite=False,
    )
    result, vector = analyze_eigensystem(
        unitary,
        np.diag(triangular),
        vectors,
        state,
        energy,
        time_value,
        n_exp,
        selection_reference=selection_reference,
    )
    result["schur_seconds"] = float(time.perf_counter() - started)
    return result, vector


def benchmark_cpu_dense(
    system: dict[str, Any],
    label: str,
    times: Sequence[float],
    *,
    repeats: int,
    reuse: bool,
    fixed_references: Sequence[np.ndarray] | None,
) -> tuple[dict[str, Any], list[np.ndarray], list[np.ndarray]]:
    state = system["sector_ground_state"]
    energy = system["ground_energy_without_constant_hartree"]
    n_exp = int(DECOMPO_NUM[f"H{system['h_chain']}"][label])
    warmup_unitary, _ = build_pf_unitary_cpu(
        system["group_spectra"], times[0], label, reuse_palindromic_stages=reuse
    )
    analyze_unitary_schur(
        warmup_unitary,
        state,
        energy,
        times[0],
        n_exp,
        selection_reference=(None if fixed_references is None else fixed_references[0]),
    )
    del warmup_unitary

    construction_samples = [[] for _ in times]
    eig_samples = [[] for _ in times]
    numerical_points: list[dict[str, Any]] = []
    numerical_vectors: list[np.ndarray] = []
    numerical_unitaries: list[np.ndarray] = []
    for repeat in range(repeats):
        previous = None
        for index, time_value in enumerate(times):
            unitary, build_profile = build_pf_unitary_cpu(
                system["group_spectra"],
                float(time_value),
                label,
                reuse_palindromic_stages=reuse,
            )
            selection_reference = (
                fixed_references[index]
                if fixed_references is not None
                else previous
            )
            point, vector = analyze_unitary_schur(
                unitary,
                state,
                energy,
                float(time_value),
                n_exp,
                selection_reference=selection_reference,
            )
            construction_samples[index].append(build_profile["wall_seconds"])
            eig_samples[index].append(point["schur_seconds"])
            if repeat == 0:
                numerical_points.append({**point, "construction": build_profile})
                numerical_vectors.append(vector)
                numerical_unitaries.append(unitary)
            previous = vector
    return {
        "status": "complete",
        "backend": "cpu_dense",
        "algorithm": (
            "palindromic_s2_stage_reuse_scipy_schur"
            if reuse
            else "sequential_pf_construction_scipy_schur"
        ),
        "precision": "complex128",
        "warmup_count": 1,
        "measurement_repeats": repeats,
        "points": [
            {
                "time": float(time_value),
                **numerical_points[index],
                "construction_seconds_median": float(
                    statistics.median(construction_samples[index])
                ),
                "schur_seconds_median": float(statistics.median(eig_samples[index])),
                "end_to_end_seconds_median": float(
                    statistics.median(
                        [
                            a + b
                            for a, b in zip(
                                construction_samples[index], eig_samples[index]
                            )
                        ]
                    )
                ),
            }
            for index, time_value in enumerate(times)
        ],
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }, numerical_vectors, numerical_unitaries


def benchmark_gpu_dense(
    system: dict[str, Any],
    label: str,
    times: Sequence[float],
    *,
    repeats: int,
    requested_batch_size: int,
    gpu_id: int,
    references: Sequence[np.ndarray],
    reference_unitaries: Sequence[np.ndarray],
) -> dict[str, Any]:
    state = system["sector_ground_state"]
    energy = system["ground_energy_without_constant_hartree"]
    n_exp = int(DECOMPO_NUM[f"H{system['h_chain']}"][label])
    actual_batch_size = min(int(requested_batch_size), len(times))
    baseline = _query_gpu(gpu_id)["memory_used_mib"]
    construction_samples = [[] for _ in times]
    schur_samples = [[] for _ in times]
    numerical_points: list[dict[str, Any] | None] = [None] * len(times)
    with GpuMemoryMonitor(gpu_id) as monitor:
        warmup, _, _ = build_pf_unitary_gpu_batch(
            system["group_spectra"], [times[0]], label
        )
        analyze_unitary_schur(
            warmup[0],
            state,
            energy,
            times[0],
            n_exp,
            selection_reference=references[0],
        )
        del warmup
        for repeat in range(repeats):
            for start in range(0, len(times), actual_batch_size):
                stop = min(len(times), start + actual_batch_size)
                unitary_batch, profile, gpu_eig = build_pf_unitary_gpu_batch(
                    system["group_spectra"], times[start:stop], label
                )
                per_item_build = profile["gpu_build_seconds"] / (stop - start)
                for local_index, unitary in enumerate(unitary_batch):
                    index = start + local_index
                    point, _ = analyze_unitary_schur(
                        unitary,
                        state,
                        energy,
                        float(times[index]),
                        n_exp,
                        selection_reference=references[index],
                    )
                    construction_samples[index].append(per_item_build)
                    schur_samples[index].append(point["schur_seconds"])
                    if repeat == 0:
                        relative_frobenius = float(
                            np.linalg.norm(unitary - reference_unitaries[index])
                            / np.linalg.norm(reference_unitaries[index])
                        )
                        numerical_points[index] = {
                            "time": float(times[index]),
                            **point,
                            "pf_unitary_relative_frobenius_difference_vs_cpu_sequential": relative_frobenius,
                            "batch_profile": profile,
                        }
                        if gpu_eig is not None:
                            gpu_point, _ = analyze_eigensystem(
                                unitary,
                                gpu_eig[local_index]["eigenvalues"],
                                gpu_eig[local_index]["eigenvectors"],
                                state,
                                energy,
                                float(times[index]),
                                n_exp,
                                selection_reference=references[index],
                            )
                            numerical_points[index]["cupy_general_eig"] = {
                                **gpu_point,
                                "seconds": gpu_eig[local_index]["seconds"],
                            }
    points = []
    for index, raw in enumerate(numerical_points):
        assert raw is not None
        points.append(
            {
                **raw,
                "gpu_construction_seconds_per_item_median": float(
                    statistics.median(construction_samples[index])
                ),
                "cpu_schur_seconds_median": float(
                    statistics.median(schur_samples[index])
                ),
                "end_to_end_compute_seconds_per_item_median": float(
                    statistics.median(
                        [
                            a + b
                            for a, b in zip(
                                construction_samples[index], schur_samples[index]
                            )
                        ]
                    )
                ),
            }
        )
    return {
        "status": "complete",
        "backend": "gpu_dense_cpu_schur",
        "algorithm": "cupy_palindromic_s2_stage_reuse_then_scipy_schur",
        "precision": "complex128",
        "requested_batch_size": int(requested_batch_size),
        "actual_maximum_batch_size": actual_batch_size,
        "batch_size_limited_by_three_scientific_times": bool(
            requested_batch_size > len(times)
        ),
        "warmup_count": 1,
        "measurement_repeats": repeats,
        "points": points,
        "gpu_memory": monitor.summary(baseline),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }


def ritz_from_moments(
    moments: Sequence[complex],
    dimension: int,
    gram_cutoff: float,
    *,
    energy: float,
    time_value: float,
    n_exp: int,
) -> dict[str, Any]:
    if dimension < 1 or len(moments) <= dimension:
        raise ValueError("moments must contain mu_0 through mu_dimension")

    def moment(index: int) -> complex:
        return moments[index] if index >= 0 else np.conj(moments[-index])

    gram = np.empty((dimension, dimension), dtype=np.complex128)
    projected = np.empty_like(gram)
    for row in range(dimension):
        for column in range(dimension):
            gram[row, column] = moment(column - row)
            projected[row, column] = moment(column + 1 - row)
    gram = (gram + gram.conj().T) / 2
    gram_values, gram_vectors = np.linalg.eigh(gram)
    maximum = float(np.max(gram_values))
    keep = gram_values > float(gram_cutoff) * maximum
    rank = int(np.count_nonzero(keep))
    if rank < 1:
        raise RuntimeError("Gram cutoff removed the full Krylov space")
    basis = gram_vectors[:, keep]
    inverse_sqrt = basis / np.sqrt(gram_values[keep])[None, :]
    reduced = inverse_sqrt.conj().T @ projected @ inverse_sqrt
    values, reduced_vectors = np.linalg.eig(reduced)
    coefficients = inverse_sqrt @ reduced_vectors
    overlaps = np.empty(values.size, dtype=float)
    for index in range(values.size):
        coefficient = coefficients[:, index]
        norm = float(np.real(coefficient.conj() @ gram @ coefficient))
        amplitude = sum(moments[j] * coefficient[j] for j in range(dimension))
        overlaps[index] = abs(amplitude) ** 2 / norm
    selected = int(np.argmax(overlaps))
    coefficient = coefficients[:, selected]
    coefficient /= np.sqrt(np.real(coefficient.conj() @ gram @ coefficient))
    eigenvalue = complex(values[selected])
    phase = float(np.angle(eigenvalue))
    branch = int(np.rint((energy * time_value - phase) / (2 * np.pi)))
    effective_energy = float((phase + 2 * np.pi * branch) / time_value)
    signed_shift = float(effective_energy - energy)
    rayleigh = complex(coefficient.conj() @ projected @ coefficient)
    residual_squared = max(
        0.0,
        float(
            np.real(
                1.0
                + abs(eigenvalue) ** 2
                - 2.0 * np.conj(eigenvalue) * rayleigh
            )
        ),
    )
    return {
        "K": int(dimension),
        "gram_cutoff": float(gram_cutoff),
        "gram_rank": rank,
        "gram_largest_eigenvalue": maximum,
        "gram_smallest_retained_eigenvalue": float(np.min(gram_values[keep])),
        "ritz_value": _jsonable(eigenvalue),
        "ritz_value_magnitude": float(abs(eigenvalue)),
        "ground_state_overlap_probability": float(overlaps[selected]),
        "signed_eigenvalue_shift_hartree": signed_shift,
        "direct_like_error_hartree": abs(signed_shift),
        "direct_like_cost": _cost(time_value, abs(signed_shift), n_exp),
        "effective_energy_hartree": effective_energy,
        "raw_eigenphase_rad": phase,
        "phase_branch_integer": branch,
        "equivalent_eigenpair_residual_2_norm": float(math.sqrt(residual_squared)),
    }


def benchmark_matrix_free(
    system: dict[str, Any],
    label: str,
    times: Sequence[float],
    *,
    repeats: int,
    gpu_id: int,
    k_values: Sequence[int],
    gram_cutoffs: Sequence[float],
    direct_points: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    parameter = Parameter("tau")
    clique_started = time.perf_counter()
    cliques = build_clique_hamiltonians(
        system["groups"], system["num_qubits"], processes=1
    )
    clique_seconds = time.perf_counter() - clique_started
    body = QuantumCircuit(system["num_qubits"])
    rotation_count = w_trotter_grouper_precomputed(
        body, cliques, parameter, system["num_qubits"], label
    )
    template = build_parameterized_aer_template(
        body, parameter_name=parameter.name, device="GPU", optimization_level=0
    )
    state0 = system["full_ground_state"]
    energy = system["ground_energy_without_constant_hartree"]
    k_max = max(int(value) for value in k_values)
    baseline = _query_gpu(gpu_id)["memory_used_mib"]
    points = []
    with GpuMemoryMonitor(gpu_id) as monitor:
        run_parameterized_aer_template(
            template,
            state0,
            parameter_value=-float(times[0]),
            device="GPU",
            target_gpus=(),
        )
        for time_index, time_value in enumerate(times):
            repeat_seconds = []
            first_moments: list[complex] | None = None
            first_profiles: list[dict[str, Any]] | None = None
            for repeat in range(repeats):
                current = np.array(state0, copy=True)
                moments = [complex(1.0)]
                profiles = []
                started = time.perf_counter()
                for step in range(1, k_max + 1):
                    evolved, profile = run_parameterized_aer_template(
                        template,
                        current,
                        parameter_value=-float(time_value),
                        device="GPU",
                        target_gpus=(),
                    )
                    current = np.asarray(evolved.data, dtype=np.complex128)
                    moments.append(complex(np.vdot(state0, current)))
                    profiles.append(profile)
                    if step == 1 or step % 8 == 0 or step == k_max:
                        print(
                            f"H{system['h_chain']} {label} t={time_value:.8g} "
                            f"repeat={repeat + 1}/{repeats} moment={step}/{k_max}",
                            flush=True,
                        )
                repeat_seconds.append(time.perf_counter() - started)
                if repeat == 0:
                    first_moments = moments
                    first_profiles = profiles
            assert first_moments is not None and first_profiles is not None
            ritz = [
                ritz_from_moments(
                    first_moments,
                    int(k_value),
                    float(cutoff),
                    energy=energy,
                    time_value=float(time_value),
                    n_exp=int(rotation_count),
                )
                for cutoff in gram_cutoffs
                for k_value in k_values
            ]
            direct = direct_points[time_index]
            for item in ritz:
                item["signed_shift_absolute_difference_vs_cpu_hartree"] = abs(
                    item["signed_eigenvalue_shift_hartree"]
                    - direct["signed_eigenvalue_shift_hartree"]
                )
                item["error_difference_over_epsilon_E"] = abs(
                    item["direct_like_error_hartree"]
                    - direct["direct_error_hartree"]
                ) / TARGET_ERROR
                item["cost_relative_difference_vs_cpu"] = (
                    None
                    if item["direct_like_cost"] is None
                    or direct["direct_cost"] is None
                    else abs(item["direct_like_cost"] / direct["direct_cost"] - 1.0)
                )
            points.append(
                {
                    "time": float(time_value),
                    "moments": [_jsonable(value) for value in first_moments],
                    "K_max": k_max,
                    "ritz_results": ritz,
                    "full_moment_chain_seconds": repeat_seconds,
                    "full_moment_chain_seconds_median": float(
                        statistics.median(repeat_seconds)
                    ),
                    "aer_simulator_seconds_sum": float(
                        sum(profile["simulator_run_seconds"] for profile in first_profiles)
                    ),
                    "host_bind_transfer_and_result_seconds_sum": float(
                        sum(
                            profile["total_seconds"] - profile["simulator_run_seconds"]
                            for profile in first_profiles
                        )
                    ),
                    "statevector_host_round_trips": k_max,
                    "cpu_direct_reference": direct,
                }
            )
    return {
        "status": "complete",
        "backend": "gpu_matrix_free",
        "algorithm": "aer_overlap_moments_unitary_krylov_ritz",
        "precision": "complex128/double",
        "clique_precompute_seconds": float(clique_seconds),
        "template_prepare": template.prepare_profile,
        "pauli_rotations_per_pf_application": int(rotation_count),
        "k_values": list(map(int, k_values)),
        "gram_cutoffs": list(map(float, gram_cutoffs)),
        "moment_reuse": "one mu_0..mu_Kmax sequence reused for every K and cutoff",
        "state_transfer_limitation": (
            "Aer 0.15.1 returns each full statevector to the host; transfer/host "
            "overhead and round-trip count are recorded separately"
        ),
        "warmup_pf_applications": 1,
        "measurement_repeats": repeats,
        "points": points,
        "gpu_memory": monitor.summary(baseline),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }


def run_case(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    visible = [value for value in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if value]
    if visible != [str(args.gpu_id)]:
        raise RuntimeError(
            f"Expected CUDA_VISIBLE_DEVICES={args.gpu_id}, got {visible!r}"
        )
    initial_gpu = _query_gpu(args.gpu_id)
    if initial_gpu["memory_used_mib"] * 2 > initial_gpu["memory_total_mib"]:
        raise RuntimeError("Assigned GPU has less than half its memory free")
    times = [float(args.t_ana * factor) for factor in args.factors]
    repeats = int(args.repeats)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "direct PF eigenvalue solver method comparison",
        "status": "initializing",
        "environment": _environment(args.gpu_id),
        "configuration": {
            "h_chain": int(args.h_chain),
            "label": args.label,
            "t_ana": float(args.t_ana),
            "t_ana_source": args.t_ana_source,
            "relative_time_factors": list(map(float, args.factors)),
            "times": times,
            "repeats": repeats,
            "batch_sizes": list(map(int, args.batch_sizes)),
            "k_values": list(map(int, args.k_values)),
            "gram_cutoffs": list(map(float, args.gram_cutoffs)),
            "epsilon_E_hartree": TARGET_ERROR,
            "beta": BETA,
        },
        "methods": {},
        "started_at": _now(),
    }
    _atomic_json(output, payload)
    try:
        system = prepare_system(int(args.h_chain), dense=True)
        dimension = int(system["sector"]["dimension"])
        one_matrix_gib = float(16 * dimension * dimension / 2**30)
        payload["system"] = {
            "h_chain": int(args.h_chain),
            "num_qubits": int(system["num_qubits"]),
            "full_state_dimension": int(1 << system["num_qubits"]),
            "sector": system["sector"],
            "num_commuting_groups": len(system["groups"]),
            "ground_energy_without_constant_hartree": system[
                "ground_energy_without_constant_hartree"
            ],
            "ground_state_diagnostics": system["ground_state_diagnostics"],
            "used_scipy_eigsh": False,
            "one_sector_complex128_matrix_gib": one_matrix_gib,
        }
        payload["status"] = "running"
        _atomic_json(output, payload)

        cpu_sequential, references, reference_unitaries = benchmark_cpu_dense(
            system,
            args.label,
            times,
            repeats=repeats,
            reuse=False,
            fixed_references=None,
        )
        payload["methods"]["cpu_dense_sequential"] = cpu_sequential
        _atomic_json(output, payload)

        cpu_reuse, _, reuse_unitaries = benchmark_cpu_dense(
            system,
            args.label,
            times,
            repeats=repeats,
            reuse=True,
            fixed_references=references,
        )
        for index, point in enumerate(cpu_reuse["points"]):
            point["pf_unitary_relative_frobenius_difference_vs_cpu_sequential"] = float(
                np.linalg.norm(reuse_unitaries[index] - reference_unitaries[index])
                / np.linalg.norm(reference_unitaries[index])
            )
            point["signed_shift_absolute_difference_vs_cpu_sequential_hartree"] = abs(
                point["signed_eigenvalue_shift_hartree"]
                - cpu_sequential["points"][index]["signed_eigenvalue_shift_hartree"]
            )
            point["cost_relative_difference_vs_cpu_sequential"] = (
                None
                if point["direct_cost"] is None
                or cpu_sequential["points"][index]["direct_cost"] is None
                else abs(
                    point["direct_cost"]
                    / cpu_sequential["points"][index]["direct_cost"]
                    - 1.0
                )
            )
        payload["methods"]["cpu_dense_stage_reuse"] = cpu_reuse
        _atomic_json(output, payload)

        gpu_dense = {}
        for batch_size in args.batch_sizes:
            try:
                result = benchmark_gpu_dense(
                    system,
                    args.label,
                    times,
                    repeats=repeats,
                    requested_batch_size=int(batch_size),
                    gpu_id=int(args.gpu_id),
                    references=references,
                    reference_unitaries=reference_unitaries,
                )
                for index, point in enumerate(result["points"]):
                    reference = cpu_sequential["points"][index]
                    point["signed_shift_absolute_difference_vs_cpu_hartree"] = abs(
                        point["signed_eigenvalue_shift_hartree"]
                        - reference["signed_eigenvalue_shift_hartree"]
                    )
                    point["cost_relative_difference_vs_cpu"] = (
                        None
                        if point["direct_cost"] is None
                        or reference["direct_cost"] is None
                        else abs(point["direct_cost"] / reference["direct_cost"] - 1.0)
                    )
                gpu_dense[str(int(batch_size))] = result
            except Exception as exc:
                gpu_dense[str(int(batch_size))] = {
                    "status": "failed",
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            payload["methods"]["gpu_dense"] = gpu_dense
            _atomic_json(output, payload)

        matrix_free = benchmark_matrix_free(
            system,
            args.label,
            times,
            repeats=repeats,
            gpu_id=int(args.gpu_id),
            k_values=args.k_values,
            gram_cutoffs=args.gram_cutoffs,
            direct_points=cpu_sequential["points"],
        )
        payload["methods"]["gpu_matrix_free"] = matrix_free
        payload["status"] = "complete"
        payload["completed_at"] = _now()
        payload["peak_cpu_rss_kib"] = int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
        _atomic_json(output, payload)
        print(f"saved: {output}", flush=True)
        return 0
    except Exception as exc:
        payload["status"] = "failed"
        payload["completed_at"] = _now()
        payload["exception_type"] = type(exc).__name__
        payload["error"] = str(exc)
        payload["traceback"] = traceback.format_exc()
        payload["peak_cpu_rss_kib"] = int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
        _atomic_json(output, payload)
        traceback.print_exc()
        return 1


def _relative_difference(value: float | None, reference: float | None) -> float | None:
    if value is None or reference is None or reference == 0:
        return None
    return abs(float(value) / float(reference) - 1.0)


def _maximum_or_none(values: Sequence[float | None]) -> float | None:
    finite_values = [float(value) for value in values if value is not None]
    return max(finite_values) if finite_values else None


def summarize(raw_paths: Sequence[Path], output_dir: Path) -> dict[str, Any]:
    records = [json.loads(path.read_text(encoding="utf-8")) for path in raw_paths]
    summary: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "direct PF solver benchmark automatic summary",
        "created_at": _now(),
        "git_commit": _git_commit(),
        "raw_files": [str(path) for path in raw_paths],
        "thresholds": {
            "gpu_dense": {
                "unitary_relative_frobenius": 1e-10,
                "signed_shift_absolute_hartree": DIRECT_ABS_SHIFT_TOL,
                "cost_relative": DIRECT_COST_REL_TOL,
                "ground_overlap_absolute": 1e-8,
                "eigenpair_residual": DIRECT_RESIDUAL_TOL,
            },
            "matrix_free_direct_substitute": {
                "signed_shift_absolute_hartree": DIRECT_ABS_SHIFT_TOL,
                "cost_relative": DIRECT_COST_REL_TOL,
                "equivalent_eigenpair_residual": DIRECT_RESIDUAL_TOL,
            },
            "matrix_free_calibrated_proxy": {
                "error_difference_over_epsilon_E": PROXY_EPSILON_FRACTION_TOL,
                "cost_relative": PROXY_COST_REL_TOL,
                "pair_cost_ratio_relative": PROXY_PAIR_RATIO_REL_TOL,
                "last_three_K_cost_change": PROXY_LAST_THREE_COST_CHANGE_TOL,
            },
        },
        "systems": {},
        "matrix_free_calibration": {},
    }
    csv_rows = []
    for record in records:
        h_key = f"H{record['configuration']['h_chain']}"
        label = record["configuration"]["label"]
        summary["systems"].setdefault(h_key, {})[label] = {
            "status": record["status"],
            "source": next(
                str(path)
                for path, candidate in zip(raw_paths, records)
                if candidate is record
            ),
        }
        if record["status"] != "complete":
            summary["systems"][h_key][label]["error"] = record.get("error")
            continue
        cpu = record["methods"]["cpu_dense_sequential"]["points"]
        reuse = record["methods"]["cpu_dense_stage_reuse"]["points"]
        gpu_batch1 = record["methods"]["gpu_dense"]["1"]
        gpu_passes = gpu_batch1["status"] == "complete" and all(
            point["pf_unitary_relative_frobenius_difference_vs_cpu_sequential"]
            <= 1e-10
            and point["signed_shift_absolute_difference_vs_cpu_hartree"]
            <= DIRECT_ABS_SHIFT_TOL
            and (
                point["cost_relative_difference_vs_cpu"] is None
                or point["cost_relative_difference_vs_cpu"] <= DIRECT_COST_REL_TOL
            )
            and point["eigenpair_residual_2_norm"] <= DIRECT_RESIDUAL_TOL
            for point in gpu_batch1["points"]
        )
        case = summary["systems"][h_key][label]
        case["cpu_stage_reuse_pass"] = all(
            point["pf_unitary_relative_frobenius_difference_vs_cpu_sequential"]
            <= 1e-10
            and point["signed_shift_absolute_difference_vs_cpu_sequential_hartree"]
            <= DIRECT_ABS_SHIFT_TOL
            for point in reuse
        )
        case["gpu_dense_pass"] = gpu_passes
        case["cpu_sequential_seconds_sum"] = float(
            sum(point["end_to_end_seconds_median"] for point in cpu)
        )
        case["cpu_stage_reuse_seconds_sum"] = float(
            sum(point["end_to_end_seconds_median"] for point in reuse)
        )
        case["gpu_dense_batch1_seconds_sum"] = (
            None
            if gpu_batch1["status"] != "complete"
            else float(
                sum(
                    point["end_to_end_compute_seconds_per_item_median"]
                    for point in gpu_batch1["points"]
                )
            )
        )
        for method_name, method in (
            ("cpu_dense_sequential", record["methods"]["cpu_dense_sequential"]),
            ("cpu_dense_stage_reuse", record["methods"]["cpu_dense_stage_reuse"]),
        ):
            for factor, point in zip(record["configuration"]["relative_time_factors"], method["points"]):
                csv_rows.append(
                    {
                        "system": h_key,
                        "pf": label,
                        "time": point["time"],
                        "relative_time": factor,
                        "backend": method["backend"],
                        "algorithm": method["algorithm"],
                        "precision": method["precision"],
                        "batch_size": "",
                        "K": "",
                        "status": method["status"],
                        "signed_shift_hartree": point["signed_eigenvalue_shift_hartree"],
                        "error_hartree": point["direct_error_hartree"],
                        "cost": point["direct_cost"],
                        "residual": point["eigenpair_residual_2_norm"],
                        "seconds": point["end_to_end_seconds_median"],
                        "peak_cpu_rss_kib": method["peak_cpu_rss_kib"],
                        "peak_gpu_delta_mib": "",
                    }
                )
        matrix_free = record["methods"]["gpu_matrix_free"]
        for factor, point in zip(record["configuration"]["relative_time_factors"], matrix_free["points"]):
            for ritz in point["ritz_results"]:
                csv_rows.append(
                    {
                        "system": h_key,
                        "pf": label,
                        "time": point["time"],
                        "relative_time": factor,
                        "backend": matrix_free["backend"],
                        "algorithm": matrix_free["algorithm"],
                        "precision": matrix_free["precision"],
                        "batch_size": "",
                        "K": ritz["K"],
                        "status": matrix_free["status"],
                        "signed_shift_hartree": ritz["signed_eigenvalue_shift_hartree"],
                        "error_hartree": ritz["direct_like_error_hartree"],
                        "cost": ritz["direct_like_cost"],
                        "residual": ritz["equivalent_eigenpair_residual_2_norm"],
                        "seconds": point["full_moment_chain_seconds_median"],
                        "peak_cpu_rss_kib": matrix_free["peak_cpu_rss_kib"],
                        "peak_gpu_delta_mib": matrix_free["gpu_memory"]["peak_delta_mib"],
                    }
                )

    calibration_systems = ["H6", "H7"]
    available = all(
        h in summary["systems"] and all(label in summary["systems"][h] for label in LABELS)
        for h in calibration_systems
    )
    if not available:
        summary["matrix_free_calibration"] = {
            "status": "not validated",
            "reason": "H6/H7 both PF raw results are not all complete",
        }
    else:
        raw_by_key = {
            (f"H{item['configuration']['h_chain']}", item["configuration"]["label"]): item
            for item in records
        }
        candidates = []
        for cutoff in DEFAULT_GRAM_CUTOFFS:
            for k_value in DEFAULT_K_VALUES:
                condition_rows = []
                for h_key in calibration_systems:
                    for label in LABELS:
                        item = raw_by_key[(h_key, label)]
                        for point in item["methods"]["gpu_matrix_free"]["points"]:
                            selected = next(
                                entry
                                for entry in point["ritz_results"]
                                if entry["K"] == k_value
                                and math.isclose(entry["gram_cutoff"], cutoff)
                            )
                            condition_rows.append(selected)
                direct_pass = all(
                    row["signed_shift_absolute_difference_vs_cpu_hartree"]
                    <= DIRECT_ABS_SHIFT_TOL
                    and row["cost_relative_difference_vs_cpu"] is not None
                    and row["cost_relative_difference_vs_cpu"] <= DIRECT_COST_REL_TOL
                    and row["equivalent_eigenpair_residual_2_norm"]
                    <= DIRECT_RESIDUAL_TOL
                    for row in condition_rows
                )
                proxy_pass = all(
                    row["error_difference_over_epsilon_E"]
                    <= PROXY_EPSILON_FRACTION_TOL
                    and row["cost_relative_difference_vs_cpu"] is not None
                    and row["cost_relative_difference_vs_cpu"] <= PROXY_COST_REL_TOL
                    for row in condition_rows
                )
                candidates.append(
                    {
                        "K": k_value,
                        "gram_cutoff": cutoff,
                        "direct_substitute_pointwise_pass": direct_pass,
                        "calibrated_proxy_pointwise_pass": proxy_pass,
                        "maximum_signed_shift_absolute_difference_hartree": max(
                            row["signed_shift_absolute_difference_vs_cpu_hartree"]
                            for row in condition_rows
                        ),
                        "maximum_error_difference_over_epsilon_E": max(
                            row["error_difference_over_epsilon_E"] for row in condition_rows
                        ),
                        "maximum_cost_relative_difference": _maximum_or_none(
                            [
                                row["cost_relative_difference_vs_cpu"]
                                for row in condition_rows
                            ]
                        ),
                        "maximum_residual": max(
                            row["equivalent_eigenpair_residual_2_norm"]
                            for row in condition_rows
                        ),
                    }
                )
        summary["matrix_free_calibration"] = {
            "status": "calibration evaluated",
            "candidates": candidates,
            "note": (
                "Pointwise tests are necessary but not sufficient: final proxy "
                "acceptance also requires pair-cost-ratio and last-three-K stability."
            ),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(output_dir / "benchmark_summary.json", summary)
    fieldnames = list(csv_rows[0]) if csv_rows else ["system", "status"]
    csv_path = output_dir / "benchmark_summary.csv"
    temporary = csv_path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(csv_rows)
    temporary.replace(csv_path)

    lines = [
        "# Direct PF solver benchmark",
        "",
        f"Commit: `{summary['git_commit']}`",
        "",
        "The matrix-free result is not called `e_direct` unless every H6/H7 "
        "calibration condition passes the fixed criteria.",
        "",
        "| System | PF | raw status | CPU stage reuse | GPU dense |",
        "|---|---|---|---|---|",
    ]
    for h_key in sorted(summary["systems"], key=lambda item: int(item[1:])):
        for label, case in summary["systems"][h_key].items():
            lines.append(
                f"| {h_key} | {label} | {case['status']} | "
                f"{case.get('cpu_stage_reuse_pass', 'not evaluated')} | "
                f"{case.get('gpu_dense_pass', 'not evaluated')} |"
            )
    calibration = summary["matrix_free_calibration"]
    lines.extend(
        [
            "",
            "## Matrix-free calibration",
            "",
            f"Status: `{calibration['status']}`",
            "",
            calibration.get("reason", calibration.get("note", "")),
            "",
            "H8 and larger systems must not be started until the complete H6/H7 "
            "direct-substitute or calibrated-proxy rules pass and the selected "
            "K/cutoff are frozen.",
        ]
    )
    _atomic_text(output_dir / "benchmark_report.md", "\n".join(lines) + "\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--h-chain", type=int, required=True)
    run_parser.add_argument("--label", choices=LABELS, required=True)
    run_parser.add_argument("--t-ana", type=float, required=True)
    run_parser.add_argument("--t-ana-source", required=True)
    run_parser.add_argument("--gpu-id", type=int, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--factors", type=float, nargs="+", default=DEFAULT_FACTORS)
    run_parser.add_argument("--repeats", type=int, default=1)
    run_parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 2, 4, 8])
    run_parser.add_argument("--k-values", type=int, nargs="+", default=DEFAULT_K_VALUES)
    run_parser.add_argument(
        "--gram-cutoffs", type=float, nargs="+", default=DEFAULT_GRAM_CUTOFFS
    )
    summary_parser = subparsers.add_parser("summarize")
    summary_parser.add_argument("--raw-json", type=Path, nargs="+", required=True)
    summary_parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "run":
        raise SystemExit(run_case(args))
    summarize(args.raw_json, args.output_dir)


if __name__ == "__main__":
    main()
