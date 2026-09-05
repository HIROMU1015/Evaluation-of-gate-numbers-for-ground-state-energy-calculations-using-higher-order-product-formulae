"""Validate frozen m=3 fourth-order PF candidates by exact GPU construction.

The grouped Hamiltonians are restricted first to the fixed-population sector
and then to an exact diagonal-Z2 symmetry block.  Their small connected
components are diagonalized once on CPU.  Each requested PF unitary is then
constructed densely on one GPU and diagonalized exactly with a CPU complex
Schur decomposition.  No iterative or projected eigensolver is used.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.metadata
import json
import math
import os
from pathlib import Path
import pickle
import platform
import resource
import subprocess
import threading
import time
import traceback
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.component_sector_pf import (
    ComponentSpectrum,
    component_exponential,
    find_balanced_z2_symmetry,
    fixed_population_basis,
    prepare_component_spectra,
)
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)

# This establishes the server-tested CUDA wheel library order before CuPy.
from trotterlib import qiskit_time_evolution_grouping as _cuda_preload  # noqa: F401,E402


SOURCE_HOLDOUT = Path(
    "artifacts/pf_cost_predictability_m3_holdout/H6_H7_holdout.json"
)
RELATIVE_TIMES = (0.1, 0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.4)
FIT_TIMES = tuple(float(value) for value in np.geomspace(0.06, 0.8, 15)[:5])
EPSILON_E = float(TARGET_ERROR)
ORDER = 4
H6_SHIFT_TOL = 1e-10
H6_COST_REL_TOL = 1e-6


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


def _git_state() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        capture_output=True, check=False,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, text=True,
        capture_output=True, check=False,
    ).stdout.splitlines()
    return {"commit": commit or None, "dirty": bool(status), "status": status}


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _gpu_info(physical_gpu_id: int) -> dict[str, Any]:
    completed = subprocess.run(
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
    """Sample one physical GPU without interacting with other processes."""

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
                "nvidia-smi", "--query-gpu=memory.used",
                "--format=csv,noheader,nounits", "-i", str(self.gpu_id),
                "-lms", str(self.interval_ms),
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
            message = self.process.stderr.read().strip()
            if message:
                self.errors.append(message)

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


def _candidate_records(source: Path = SOURCE_HOLDOUT) -> dict[str, dict[str, Any]]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    return {str(item["name"]): item for item in payload["candidates"]}


def _sequence(weights: Sequence[float]) -> list[float]:
    return symmetric_s2_sequence([float(value) for value in weights])


def _rotations(h_chain: int) -> int:
    # Every frozen candidate has m=3 and therefore the same seven S2 stages.
    return int(DECOMPO_NUM[f"H{h_chain}"]["4th(new_3)"])


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    if error < 0.0 or error >= EPSILON_E:
        return None
    return float(BETA * rotations / (time_value * (EPSILON_E - error)))


def _fixed_order_alpha(times: Sequence[float], errors: Sequence[float]) -> float:
    times_array = np.asarray(times, dtype=float)
    errors_array = np.asarray(errors, dtype=float)
    if np.any(times_array <= 0.0) or np.any(errors_array <= 0.0):
        raise ValueError("fit times and errors must be positive")
    return float(np.exp(np.mean(np.log(errors_array / times_array**ORDER))))


def _free_log_fit(times: Sequence[float], errors: Sequence[float]) -> dict[str, float]:
    x = np.log(np.asarray(times, dtype=float))
    y = np.log(np.asarray(errors, dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    predicted = intercept + slope * x
    denominator = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 if denominator == 0.0 else 1.0 - float(
        np.sum((y - predicted) ** 2) / denominator
    )
    return {"alpha": float(np.exp(intercept)), "order": float(slope), "r2": r2}


def _analytic_time(alpha: float) -> float:
    return float((EPSILON_E / ((ORDER + 1) * alpha)) ** (1.0 / ORDER))


def prepare_system(args: argparse.Namespace) -> int:
    metadata: dict[str, Any] = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "configuration": {"h_chain": args.h_chain, "processes": args.processes},
    }
    _atomic_json(args.metadata, metadata)
    try:
        started = time.perf_counter()
        source = _prepare_system(int(args.h_chain))
        groups = source["groups"]
        num_qubits = int(source["num_qubits"])
        full_state = np.asarray(source["state"], dtype=np.complex128).reshape(-1)
        full_state /= np.linalg.norm(full_state)
        population_basis, population = fixed_population_basis(num_qubits, full_state)
        population_state = full_state[population_basis].copy()
        population_state /= np.linalg.norm(population_state)
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, num_qubits, population_basis, population_state
        )
        restricted_basis = population_basis[selected]
        restricted_state = population_state[selected].copy()
        restricted_state /= np.linalg.norm(restricted_state)
        spectra, compact = prepare_component_spectra(
            groups,
            num_qubits,
            restricted_basis,
            validation_state=restricted_state,
            processes=int(args.processes),
        )
        summed_action = np.asarray(compact.pop("summed_group_action"))
        energy = float(source["energy_without_constant"])
        residual = float(np.linalg.norm(summed_action - energy * restricted_state))
        if residual > 1e-8:
            raise RuntimeError(f"restricted ground-state residual is {residual}")
        system = {
            "h_chain": int(args.h_chain),
            "ham_name": source["ham_name"],
            "num_qubits": num_qubits,
            "restricted_basis": restricted_basis,
            "state": restricted_state,
            "energy": energy,
            "component_spectra": spectra,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("wb") as handle:
            pickle.dump(system, handle, protocol=pickle.HIGHEST_PROTOCOL)
        metadata.update(
            {
                "status": "complete", "completed_at": _now(),
                "system": {
                    "h_chain": int(args.h_chain), "num_qubits": num_qubits,
                    "group_count": len(groups),
                    "ground_energy_without_constant_hartree": energy,
                    "population_sector": population,
                    "diagonal_z2_symmetry": symmetry,
                    "symmetry_mask": int(mask), "symmetry_target_bit": int(target),
                    "restricted_ground_state_residual": residual,
                    "component_representation": compact,
                },
                "timing_seconds": {"total_preparation": time.perf_counter() - started},
                "temporary_pickle": str(args.output),
                "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            }
        )
        _atomic_json(args.metadata, metadata)
        print(
            f"prepared H{args.h_chain}: population={population_basis.size}, "
            f"exact Z2 block={restricted_state.size}, groups={len(groups)}",
            flush=True,
        )
        return 0
    except Exception as exc:
        metadata.update(
            {"status": "failed", "completed_at": _now(),
             "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}
        )
        _atomic_json(args.metadata, metadata)
        traceback.print_exc()
        return 1


def _apply_pf_components(
    spectra: Sequence[ComponentSpectrum],
    sequence: Sequence[float],
    time_value: float,
    state: np.ndarray,
) -> np.ndarray:
    current = np.asarray(state, dtype=np.complex128).copy()
    gates: dict[tuple[int, float], Any] = {}
    for group_index, raw_weight in iter_s2_sequence_steps(len(spectra), sequence):
        weight = float(raw_weight)
        key = (int(group_index), weight)
        gate = gates.get(key)
        if gate is None:
            gate = component_exponential(spectra[group_index], time_value * weight)
            gates[key] = gate
        current = gate @ current
    return current


def _fit_candidate(system: dict[str, Any], weights: Sequence[float]) -> dict[str, Any]:
    started = time.perf_counter()
    state = np.asarray(system["state"])
    energy = float(system["energy"])
    sequence = _sequence(weights)
    points = []
    for time_value in FIT_TIMES:
        point_started = time.perf_counter()
        evolved = _apply_pf_components(
            system["component_spectra"], sequence, time_value, state
        )
        overlap = complex(np.vdot(state, evolved))
        rotated = np.exp(-1j * energy * time_value) * overlap
        error = abs(float(rotated.imag / time_value))
        points.append(
            {
                "time": time_value,
                "perturbative_error_hartree": error,
                "phase_rotated_overlap": rotated,
                "survival_probability": float(abs(rotated) ** 2),
                "evolved_state_norm": float(np.linalg.norm(evolved)),
                "elapsed_seconds": float(time.perf_counter() - point_started),
            }
        )
    errors = [float(point["perturbative_error_hartree"]) for point in points]
    alpha = _fixed_order_alpha(FIT_TIMES, errors)
    return {
        "fit_times": list(FIT_TIMES), "points": points,
        "fixed_order": ORDER, "fixed_order_alpha": alpha,
        "free_fit": _free_log_fit(FIT_TIMES, errors),
        "analytic_optimal_time": _analytic_time(alpha),
        "elapsed_seconds": float(time.perf_counter() - started),
    }


def _build_s2_stage_gpu(
    spectra: Sequence[ComponentSpectrum], time_value: float, weight: float
):
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    dimension = spectra[0].dimension
    stage = cp.eye(dimension, dtype=cp.complex128)
    half_gates = []
    for spectrum in spectra[:-1]:
        gate = gpu_csr_matrix(component_exponential(spectrum, time_value * weight / 2.0))
        half_gates.append(gate)
        stage = gate @ stage
    last_gate = gpu_csr_matrix(component_exponential(spectra[-1], time_value * weight))
    stage = last_gate @ stage
    for gate in reversed(half_gates):
        stage = gate @ stage
    return stage


def _build_pf_unitary_gpu(
    spectra: Sequence[ComponentSpectrum], sequence: Sequence[float], time_value: float
) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp

    cache: dict[float, Any] = {}
    stage_seconds: dict[str, float] = {}
    started = time.perf_counter()
    for weight in dict.fromkeys(float(value) for value in sequence):
        stage_started = time.perf_counter()
        cache[weight] = _build_s2_stage_gpu(spectra, time_value, weight)
        cp.cuda.Stream.null.synchronize()
        stage_seconds[repr(weight)] = float(time.perf_counter() - stage_started)
    assembly_started = time.perf_counter()
    unitary = cp.eye(spectra[0].dimension, dtype=cp.complex128)
    for weight in sequence:
        unitary = cache[float(weight)] @ unitary
    cp.cuda.Stream.null.synchronize()
    assembly_seconds = time.perf_counter() - assembly_started
    transfer_started = time.perf_counter()
    host = cp.asnumpy(unitary)
    cp.cuda.Stream.null.synchronize()
    transfer_seconds = time.perf_counter() - transfer_started
    pool_bytes = int(cp.get_default_memory_pool().total_bytes())
    total_seconds = time.perf_counter() - started
    del unitary, cache
    cp.get_default_memory_pool().free_all_blocks()
    return host, {
        "gpu_total_build_seconds": float(total_seconds),
        "unique_s2_stage_build_seconds": stage_seconds,
        "dense_stage_assembly_seconds": float(assembly_seconds),
        "gpu_to_cpu_transfer_seconds": float(transfer_seconds),
        "cupy_memory_pool_reserved_bytes_before_release": pool_bytes,
        "s2_stage_count": len(sequence),
        "unique_s2_stage_count": len(set(sequence)),
    }


def _analyze_unitary(
    unitary: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    rotations: int,
    model_error: float,
    previous_vector: np.ndarray | None,
    previous_shift: float | None,
) -> tuple[dict[str, Any], np.ndarray, float]:
    schur_started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - schur_started
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(vectors.conj().T @ state) ** 2
    maximum_ground_index = int(np.argmax(ground_overlaps))
    if previous_vector is None:
        selected = maximum_ground_index
        previous_overlap = None
        selection_rule = "maximum_ground_state_overlap"
    else:
        continuation = np.abs(vectors.conj().T @ previous_vector) ** 2
        selected = int(np.argmax(continuation))
        previous_overlap = float(continuation[selected])
        selection_rule = "maximum_previous_time_eigenvector_overlap"

    def shift_for(index: int, previous: float | None) -> tuple[float, float, int]:
        principal = float(
            np.angle(np.exp(-1j * energy * time_value) * eigenvalues[index])
            / time_value
        )
        if previous is None:
            return principal, principal, 0
        period = 2.0 * np.pi / time_value
        winding = int(round((previous - principal) / period))
        return principal, float(principal + winding * period), winding

    principal, shift, winding = shift_for(selected, previous_shift)
    _, maximum_ground_shift, _ = shift_for(maximum_ground_index, previous_shift)
    vector = vectors[:, selected].copy()
    eigenvalue = complex(eigenvalues[selected])
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    error = abs(shift)
    direct_cost = _cost(time_value, error, rotations)
    diagnostic_started = time.perf_counter()
    unitarity_residual = float(
        np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]))
    )
    diagnostic_seconds = time.perf_counter() - diagnostic_started
    return (
        {
            "time": float(time_value),
            "model_error_hartree": float(model_error),
            "signed_direct_shift_hartree": float(shift),
            "direct_error_hartree": float(error),
            "direct_to_model_ratio": float(error / model_error),
            "direct_cost": direct_cost,
            "principal_signed_shift_hartree": principal,
            "phase_unwrap_winding": winding,
            "ground_overlap_probability": float(ground_overlaps[selected]),
            "overlap_with_previous_probability": previous_overlap,
            "selection_rule": selection_rule,
            "selected_schur_index": selected,
            "maximum_ground_overlap_branch": {
                "schur_index": maximum_ground_index,
                "ground_overlap_probability": float(ground_overlaps[maximum_ground_index]),
                "signed_shift_hartree": float(maximum_ground_shift),
                "same_as_selected": bool(maximum_ground_index == selected),
            },
            "selected_eigenvalue": eigenvalue,
            "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
            "eigenpair_residual_2_norm": residual,
            "schur_off_diagonal_residual_frobenius_norm": float(
                np.linalg.norm(triangular - np.diag(eigenvalues))
            ),
            "unitarity_residual_frobenius_norm": unitarity_residual,
            "timing_seconds": {
                "cpu_schur": float(schur_seconds),
                "cpu_diagnostics": float(diagnostic_seconds),
            },
        },
        vector,
        shift,
    )


def _environment(gpu: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "python_executable": os.path.realpath(os.sys.executable),
        "packages": {
            name: _package_version(name)
            for name in ("numpy", "scipy", "qiskit", "qiskit-aer", "qiskit-aer-gpu", "cupy-cuda12x", "pyscf")
        },
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "gpu": gpu,
    }


def _check_gpu(args: argparse.Namespace) -> dict[str, Any]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible != str(args.gpu_id):
        raise RuntimeError(f"CUDA_VISIBLE_DEVICES must be {args.gpu_id}, got {visible!r}")
    gpu = _gpu_info(args.gpu_id)
    if 2 * int(gpu["memory_used_mib"]) > int(gpu["memory_total_mib"]):
        raise RuntimeError("selected GPU has less than half its memory free")
    return gpu


def h6_gate(args: argparse.Namespace) -> int:
    records = _candidate_records(args.source)
    candidate = records[args.candidate]
    baseline = next(
        point for point in candidate["holdout_systems"]["H6"]["direct_points"]
        if float(point["relative_time"]) == 1.0
    )
    payload: dict[str, Any] = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "candidate": args.candidate, "weights": candidate["weights"],
        "cpu_baseline": baseline,
        "gate_tolerances": {
            "signed_shift_absolute_hartree": H6_SHIFT_TOL,
            "direct_cost_relative": H6_COST_REL_TOL,
        },
    }
    _atomic_json(args.output, payload)
    try:
        gpu = _check_gpu(args)
        with args.system.open("rb") as handle:
            system = pickle.load(handle)
        time_value = float(baseline["time"])
        sequence = _sequence(candidate["weights"])
        baseline_mib = int(gpu["memory_used_mib"])
        total_started = time.perf_counter()
        with GpuMemoryMonitor(args.gpu_id) as monitor:
            unitary, build = _build_pf_unitary_gpu(
                system["component_spectra"], sequence, time_value
            )
        point, _, _ = _analyze_unitary(
            unitary, np.asarray(system["state"]), float(system["energy"]),
            time_value, _rotations(6), float(baseline["model_error_hartree"]),
            None, None,
        )
        point["relative_time"] = 1.0
        point["timing_seconds"].update(build)
        shift_difference = abs(
            float(point["signed_direct_shift_hartree"])
            - float(baseline["signed_direct_shift_hartree"])
        )
        cost_relative_difference = abs(
            float(point["direct_cost"]) / float(baseline["direct_cost"]) - 1.0
        )
        checks = {
            "signed_shift_absolute_difference_within_tolerance": shift_difference <= H6_SHIFT_TOL,
            "direct_cost_relative_difference_within_tolerance": cost_relative_difference <= H6_COST_REL_TOL,
            "signed_branch_matches": bool(
                np.sign(point["signed_direct_shift_hartree"])
                == np.sign(baseline["signed_direct_shift_hartree"])
            ),
        }
        payload.update(
            {
                "status": "complete", "completed_at": _now(),
                "passed": bool(all(checks.values())), "checks": checks,
                "differences": {
                    "signed_shift_absolute_hartree": shift_difference,
                    "direct_cost_relative": cost_relative_difference,
                },
                "gpu_result": point, "environment": _environment(gpu),
                "gpu_memory": monitor.summary(baseline_mib),
                "total_seconds": float(time.perf_counter() - total_started),
                "system": {
                    "h_chain": 6, "num_qubits": int(system["num_qubits"]),
                    "symmetry_block_dimension": int(system["state"].size),
                    "pauli_rotations_per_step": _rotations(6),
                },
            }
        )
        _atomic_json(args.output, payload)
        print(
            f"H6 gate passed={payload['passed']}: shift_diff={shift_difference:.3e}, "
            f"cost_rel_diff={cost_relative_difference:.3e}", flush=True,
        )
        return 0 if payload["passed"] else 2
    except Exception as exc:
        payload.update(
            {"status": "failed", "completed_at": _now(),
             "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}
        )
        _atomic_json(args.output, payload)
        traceback.print_exc()
        return 1


def _summarize_points(points: Sequence[dict[str, Any]], model_cost: float) -> dict[str, Any]:
    contiguous = []
    first_fail = None
    for point in points:
        passed = abs(float(point["direct_to_model_ratio"]) - 1.0) <= 0.10
        if passed and first_fail is None:
            contiguous.append(point)
        elif first_fail is None:
            first_fail = point
    valid_cost_points = [point for point in points if point["direct_cost"] is not None]
    minimum = min(valid_cost_points, key=lambda point: float(point["direct_cost"]))
    signs = [
        int(np.sign(point["signed_direct_shift_hartree"]))
        for point in points if 0.3 <= float(point["relative_time"]) <= 1.1
    ]
    checks = {
        "confirmed_scaling_through_1p1_t_ana": bool(
            contiguous and float(contiguous[-1]["relative_time"]) >= 1.1
        ),
        "direct_optimum_time_within_15_percent": abs(float(minimum["relative_time"]) - 1.0) <= 0.15,
        "minimum_cost_prediction_within_10_percent": abs(float(minimum["direct_cost"]) / model_cost - 1.0) <= 0.10,
        "no_signed_error_zero_crossing_near_schedule": len(set(signs)) <= 1 and 0 not in signs,
    }
    return {
        "ten_percent_validity": {
            "num_contiguous_passed_points": len(contiguous),
            "t_pass_over_t_ana": None if not contiguous else contiguous[-1]["relative_time"],
            "t_fail_over_t_ana": None if first_fail is None else first_fail["relative_time"],
            "right_censored": first_fail is None,
        },
        "grid_minimum_cost": {
            "relative_time": minimum["relative_time"], "time": minimum["time"],
            "cost": minimum["direct_cost"],
            "model_cost_relative_difference": abs(float(minimum["direct_cost"]) / model_cost - 1.0),
        },
        "branch_reliability": {
            "minimum_ground_overlap_probability": min(float(point["ground_overlap_probability"]) for point in points),
            "minimum_adjacent_time_overlap_probability": min(
                float(point["overlap_with_previous_probability"])
                for point in points if point["overlap_with_previous_probability"] is not None
            ),
            "maximum_eigenpair_residual_2_norm": max(float(point["eigenpair_residual_2_norm"]) for point in points),
            "all_selected_branches_are_maximum_ground_overlap": all(
                bool(point["maximum_ground_overlap_branch"]["same_as_selected"])
                for point in points
            ),
        },
        "frozen_predictability_checks": checks,
        "passed": bool(all(checks.values())),
    }


def h7_candidate(args: argparse.Namespace) -> int:
    records = _candidate_records(args.source)
    candidate = records[args.candidate]
    payload: dict[str, Any] = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "candidate": args.candidate, "weights": candidate["weights"],
        "relative_times": list(RELATIVE_TIMES), "points": [],
    }
    _atomic_json(args.output, payload)
    try:
        gate = json.loads(args.h6_gate.read_text(encoding="utf-8"))
        if gate.get("status") != "complete" or not gate.get("passed"):
            raise RuntimeError("H6 GPU/CPU agreement gate has not passed")
        gpu = _check_gpu(args)
        with args.system.open("rb") as handle:
            system = pickle.load(handle)
        if int(system["h_chain"]) != 7:
            raise ValueError("candidate worker requires an H7 compact system")
        fit = _fit_candidate(system, candidate["weights"])
        saved_h7 = candidate["holdout_systems"].get("H7")
        if saved_h7 is not None:
            saved_alpha = float(
                saved_h7["short_time_fit"]
                ["selected_window"]["fixed_order_alpha"]
            )
            computed_alpha = float(fit["fixed_order_alpha"])
            fit["component_cross_check_fixed_order_alpha"] = computed_alpha
            fit["saved_cpu_fixed_order_alpha"] = saved_alpha
            fit["saved_cpu_alpha_relative_difference"] = abs(
                computed_alpha / saved_alpha - 1.0
            )
            fit["fixed_order_alpha"] = saved_alpha
            fit["fixed_order_alpha_source"] = "saved_frozen_CPU_short_time_fit"
            fit["analytic_optimal_time"] = _analytic_time(saved_alpha)
        else:
            fit["fixed_order_alpha_source"] = (
                "new_exact_component_matrix_free_short_time_fit"
            )
        alpha = float(fit["fixed_order_alpha"])
        analytic_time = float(fit["analytic_optimal_time"])
        rotations = _rotations(7)
        model_cost = float(
            BETA * rotations /
            (analytic_time * (EPSILON_E - alpha * analytic_time**ORDER))
        )
        payload.update(
            {
                "short_time_fit": fit,
                "analytic_model_cost": model_cost,
                "system": {
                    "h_chain": 7, "num_qubits": int(system["num_qubits"]),
                    "symmetry_block_dimension": int(system["state"].size),
                    "pauli_rotations_per_step": rotations,
                },
                "environment": _environment(gpu),
            }
        )
        _atomic_json(args.output, payload)
        sequence = _sequence(candidate["weights"])
        previous_vector = None
        previous_shift = None
        baseline_mib = int(gpu["memory_used_mib"])
        candidate_started = time.perf_counter()
        with GpuMemoryMonitor(args.gpu_id) as monitor:
            for relative_time in RELATIVE_TIMES:
                point_started = time.perf_counter()
                time_value = float(relative_time * analytic_time)
                model_error = float(alpha * time_value**ORDER)
                unitary, build = _build_pf_unitary_gpu(
                    system["component_spectra"], sequence, time_value
                )
                point, previous_vector, previous_shift = _analyze_unitary(
                    unitary, np.asarray(system["state"]), float(system["energy"]),
                    time_value, rotations, model_error,
                    previous_vector, previous_shift,
                )
                point["relative_time"] = float(relative_time)
                point["timing_seconds"].update(build)
                point["timing_seconds"]["total_point"] = float(
                    time.perf_counter() - point_started
                )
                payload["points"].append(point)
                payload["elapsed_seconds"] = float(time.perf_counter() - candidate_started)
                _atomic_json(args.output, payload)
                print(
                    f"{args.candidate} t/t_ana={relative_time:g}: "
                    f"shift={point['signed_direct_shift_hartree']:.6e}, "
                    f"ratio={point['direct_to_model_ratio']:.5f}, "
                    f"build={build['gpu_total_build_seconds']:.2f}s",
                    flush=True,
                )
        payload.update(
            {
                "status": "complete", "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - candidate_started),
                "gpu_memory": monitor.summary(baseline_mib),
                "summary": _summarize_points(payload["points"], model_cost),
                "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            }
        )
        _atomic_json(args.output, payload)
        print(f"completed {args.candidate}: passed={payload['summary']['passed']}", flush=True)
        return 0
    except Exception as exc:
        payload.update(
            {"status": "failed", "completed_at": _now(),
             "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}
        )
        _atomic_json(args.output, payload)
        traceback.print_exc()
        return 1


def summarize(args: argparse.Namespace) -> int:
    gate = json.loads(args.h6_gate.read_text(encoding="utf-8"))
    candidates = [json.loads(path.read_text(encoding="utf-8")) for path in args.candidates]
    complete = gate.get("status") == "complete" and gate.get("passed") and all(
        item.get("status") == "complete" for item in candidates
    )
    payload = {
        "schema_version": 1,
        "status": "complete" if complete else "incomplete",
        "purpose": "Frozen m=3 H7 exact direct holdout validation",
        "source_commit": "80f096f9033a7bdbdc7ba1ea2e142035830d8d7a",
        "execution_commit": _git_state(),
        "method": {
            "unitary": "exact dense PF construction on GPU in exact population+Z2 block",
            "eigensolver": "complete CPU complex Schur decomposition",
            "iterative_or_projected_method_used": False,
        },
        "h6_gate": {
            "passed": gate.get("passed"), "differences": gate.get("differences"),
            "gpu_result": gate.get("gpu_result"), "cpu_baseline": gate.get("cpu_baseline"),
            "total_seconds": gate.get("total_seconds"),
        },
        "h7_candidates": [
            {
                "candidate": item["candidate"], "weights": item["weights"],
                "fixed_order_alpha": item.get("short_time_fit", {}).get("fixed_order_alpha"),
                "fixed_order_alpha_source": item.get("short_time_fit", {}).get("fixed_order_alpha_source"),
                "analytic_optimal_time": item.get("short_time_fit", {}).get("analytic_optimal_time"),
                "analytic_model_cost": item.get("analytic_model_cost"),
                "summary": item.get("summary"), "elapsed_seconds": item.get("elapsed_seconds"),
                "gpu_memory": item.get("gpu_memory"),
                "timing_seconds": {
                    "short_time_fit": item.get("short_time_fit", {}).get("elapsed_seconds"),
                    "direct_grid": item.get("elapsed_seconds"),
                    "gpu_unitary_build_sum": sum(
                        float(point["timing_seconds"]["gpu_total_build_seconds"])
                        for point in item.get("points", [])
                    ),
                    "cpu_schur_sum": sum(
                        float(point["timing_seconds"]["cpu_schur"])
                        for point in item.get("points", [])
                    ),
                },
                "points": item.get("points"),
            }
            for item in candidates
        ],
    }
    _atomic_json(args.output, payload)
    lines = [
        "# Frozen m=3 H7 GPU direct validation", "",
        f"Status: **{payload['status']}**", "",
        "The PF unitary was constructed exactly on GPU in an exact symmetry block; "
        "the complete block was then diagonalized by CPU complex Schur. No iterative "
        "or projected eigensolver was used.", "",
        "## H6 GPU/CPU gate", "",
        "| Passed | signed-shift abs. difference (Ha) | cost relative difference | total time (s) |",
        "|---|---:|---:|---:|",
        f"| {gate.get('passed')} | {gate.get('differences', {}).get('signed_shift_absolute_hartree', float('nan')):.3e} "
        f"| {gate.get('differences', {}).get('direct_cost_relative', float('nan')):.3e} "
        f"| {gate.get('total_seconds', float('nan')):.2f} |", "",
        "## H7 candidates", "",
        "| Candidate | alpha | t_ana | t_pass/t_ana | first fail | grid-min t/t_ana | grid-min cost | pass | elapsed (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for item in candidates:
        fit = item.get("short_time_fit", {})
        summary_item = item.get("summary", {})
        validity = summary_item.get("ten_percent_validity", {})
        minimum = summary_item.get("grid_minimum_cost", {})
        lines.append(
            f"| `{item['candidate']}` | {fit.get('fixed_order_alpha', float('nan')):.6e} "
            f"| {fit.get('analytic_optimal_time', float('nan')):.6f} "
            f"| {validity.get('t_pass_over_t_ana')} | {validity.get('t_fail_over_t_ana')} "
            f"| {minimum.get('relative_time')} | {minimum.get('cost', float('nan')):.6e} "
            f"| {summary_item.get('passed')} | {item.get('elapsed_seconds', float('nan')):.2f} |"
        )
    lines.extend(["", "## Branch reliability", ""])
    for item in candidates:
        reliability = item.get("summary", {}).get("branch_reliability", {})
        lines.append(
            f"- `{item['candidate']}`: min ground overlap "
            f"{reliability.get('minimum_ground_overlap_probability', float('nan')):.12f}, "
            f"min adjacent overlap {reliability.get('minimum_adjacent_time_overlap_probability', float('nan')):.12f}, "
            f"max eigenpair residual {reliability.get('maximum_eigenpair_residual_2_norm', float('nan')):.3e}."
        )
    lines.extend(["", "## Timing breakdown", ""])
    for item in candidates:
        points = item.get("points", [])
        build_sum = sum(
            float(point["timing_seconds"]["gpu_total_build_seconds"])
            for point in points
        )
        schur_sum = sum(
            float(point["timing_seconds"]["cpu_schur"]) for point in points
        )
        lines.append(
            f"- `{item['candidate']}`: short-time fit "
            f"{item.get('short_time_fit', {}).get('elapsed_seconds', float('nan')):.2f} s, "
            f"nine-point direct grid {item.get('elapsed_seconds', float('nan')):.2f} s "
            f"(GPU unitary builds {build_sum:.2f} s, CPU Schur {schur_sum:.2f} s), "
            f"peak GPU use {item.get('gpu_memory', {}).get('peak_used_mib')} MiB."
        )
    lines.extend(
        [
            "", "## Scope and next estimate", "",
            "This run stops at the fixed H7 grid. It does not refine the optimum, "
            "change coefficients or thresholds, run H8+, or use an approximate eigensolver.",
            "For another H7 candidate on the same nine-point grid, the observed candidate "
            "elapsed time is the relevant estimate; independent candidates can occupy "
            "different GPUs. From cubic scaling of the exact block operations, an H8 "
            "representative point should be budgeted at roughly 0.5--2 minutes and a "
            "nine-point candidate grid at roughly 5--15 minutes, pending an H8 timing "
            "probe. Any optimum refinement or H8 run requires confirmation.", "",
        ]
    )
    args.report.write_text("\n".join(lines), encoding="utf-8")
    if complete:
        args.complete.write_text(f"complete {datetime.now().astimezone().isoformat()}\n", encoding="utf-8")
    print(f"summary status={payload['status']}: {args.output}", flush=True)
    return 0 if complete else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--h-chain", type=int, required=True)
    prepare.add_argument("--processes", type=int, default=8)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--metadata", type=Path, required=True)
    prepare.set_defaults(function=prepare_system)
    gate = sub.add_parser("h6-gate")
    gate.add_argument("--system", type=Path, required=True)
    gate.add_argument("--source", type=Path, default=SOURCE_HOLDOUT)
    gate.add_argument("--candidate", default="m3_local_c1_r2_s007")
    gate.add_argument("--gpu-id", type=int, required=True)
    gate.add_argument("--output", type=Path, required=True)
    gate.set_defaults(function=h6_gate)
    candidate = sub.add_parser("h7-candidate")
    candidate.add_argument("--system", type=Path, required=True)
    candidate.add_argument("--source", type=Path, default=SOURCE_HOLDOUT)
    candidate.add_argument("--candidate", required=True)
    candidate.add_argument("--h6-gate", type=Path, required=True)
    candidate.add_argument("--gpu-id", type=int, required=True)
    candidate.add_argument("--output", type=Path, required=True)
    candidate.set_defaults(function=h7_candidate)
    summary = sub.add_parser("summarize")
    summary.add_argument("--h6-gate", type=Path, required=True)
    summary.add_argument("--candidates", type=Path, nargs=3, required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--report", type=Path, required=True)
    summary.add_argument("--complete", type=Path, required=True)
    summary.set_defaults(function=summarize)
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.function(args))


if __name__ == "__main__":
    raise SystemExit(main())
