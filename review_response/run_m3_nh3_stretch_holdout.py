"""Validate fixed m=3 PFs on bond-stretched NH3 active-space holdouts.

The product-formula coefficients and all model thresholds are frozen.  Each
Hamiltonian and its component spectra are prepared once per condition.  Exact
PF unitaries are built in the same population plus exact-Z2 block used by the
committed CPU holdout.  A GPU is benchmarked only when an idle device is
available without displacing an existing process.
"""

from __future__ import annotations

import argparse
import copy
from collections.abc import Sequence
from datetime import datetime
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import threading
import time
import traceback
from typing import Any

import numpy as np
from scipy.linalg import schur

import compare_one_two_term_models_server2 as comparison
import run_two_term_pf_m3_holdout_server2 as holdout
from trotterlib.component_sector_pf import ComponentSpectrum, component_exponential
from trotterlib.pf_decomposition import iter_s2_sequence_steps, symmetric_s2_sequence


SOURCE_COMMIT = "73cdbf200d348cc610d4c20f45a3208ce7ad2e7e"
GPU_IMPLEMENTATION_REFERENCE = "a8df777"
PILOT_CONDITION = "NH3_r125_631g"
LOCAL_GRID_RELATIVE_TO_T_STAR = (0.9, 0.95, 0.975, 1.0, 1.025, 1.05, 1.1)
GPU_IDS = (0, 1, 2, 3)
GPU_IDLE_MAX_UTILIZATION_PERCENT = 5
GPU_IDLE_MAX_MEMORY_USED_MIB = 1024
GPU_SHIFT_TOLERANCE_HARTREE = 1e-10
GPU_COST_RELATIVE_TOLERANCE = 1e-6
FEASIBLE_MAX_PROJECTED_WALL_SECONDS = 7200.0
ESTIMATED_DIRECT_POINTS_PER_CONDITION = 24
BRANCH_RESIDUAL_TOLERANCE = 1e-10
EQUILIBRIUM_SUMMARY = Path(
    "artifacts/m3_one_two_term_model_comparison_server2_20260910_92df2db_cpu/"
    "summary.json"
)


def _stretch_geometry(scale: float) -> list[tuple[str, tuple[float, float, float]]]:
    nitrogen_symbol, nitrogen_coordinates = holdout.NH3_GEOMETRY[0]
    center = np.asarray(nitrogen_coordinates, dtype=float)
    geometry = [(nitrogen_symbol, tuple(float(value) for value in center))]
    for symbol, coordinates in holdout.NH3_GEOMETRY[1:]:
        position = center + float(scale) * (
            np.asarray(coordinates, dtype=float) - center
        )
        geometry.append((symbol, tuple(float(value) for value in position)))
    return geometry


CONDITIONS: dict[str, dict[str, Any]] = {
    "NH3_r125_631g": {
        "geometry": _stretch_geometry(1.25),
        "basis": "6-31g",
        "multiplicity": 1,
        "charge": 0,
        "frozen_core_spatial_orbitals": 1,
        "active_spatial_orbitals": 7,
        "bond_scale": 1.25,
        "selection_role": "unused NH3 bond-stretch holdout",
    },
    "NH3_r125_ccpvdz": {
        "geometry": _stretch_geometry(1.25),
        "basis": "cc-pvdz",
        "multiplicity": 1,
        "charge": 0,
        "frozen_core_spatial_orbitals": 1,
        "active_spatial_orbitals": 7,
        "bond_scale": 1.25,
        "selection_role": "unused NH3 bond-stretch holdout",
    },
    "NH3_r150_631g": {
        "geometry": _stretch_geometry(1.50),
        "basis": "6-31g",
        "multiplicity": 1,
        "charge": 0,
        "frozen_core_spatial_orbitals": 1,
        "active_spatial_orbitals": 7,
        "bond_scale": 1.50,
        "selection_role": "unused NH3 bond-stretch holdout",
    },
    "NH3_r150_ccpvdz": {
        "geometry": _stretch_geometry(1.50),
        "basis": "cc-pvdz",
        "multiplicity": 1,
        "charge": 0,
        "frozen_core_spatial_orbitals": 1,
        "active_spatial_orbitals": 7,
        "bond_scale": 1.50,
        "selection_role": "unused NH3 bond-stretch holdout",
    },
}


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _package_versions() -> dict[str, str | None]:
    names = (
        "numpy",
        "scipy",
        "pyscf",
        "openfermion",
        "qiskit",
        "qiskit-aer",
        "qiskit-aer-gpu",
        "cupy-cuda12x",
    )
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _gpu_snapshot() -> list[dict[str, Any]]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.used,"
            "memory.free,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        capture_output=True,
        check=True,
        timeout=90,
    )
    rows = []
    for line in completed.stdout.splitlines():
        fields = [item.strip() for item in line.split(",")]
        if len(fields) != 8:
            continue
        gpu_id = int(fields[0])
        if gpu_id not in GPU_IDS:
            continue
        rows.append(
            {
                "physical_gpu_id": gpu_id,
                "name": fields[1],
                "uuid": fields[2],
                "driver_version": fields[3],
                "memory_used_mib": int(fields[4]),
                "memory_free_mib": int(fields[5]),
                "memory_total_mib": int(fields[6]),
                "utilization_percent": int(fields[7]),
            }
        )
    return sorted(rows, key=lambda item: item["physical_gpu_id"])


def _idle_gpu_choice(snapshot: Sequence[dict[str, Any]]) -> tuple[int | None, dict[str, Any]]:
    decisions = {}
    eligible = []
    for row in snapshot:
        reasons = []
        if int(row["utilization_percent"]) > GPU_IDLE_MAX_UTILIZATION_PERCENT:
            reasons.append("utilization_above_idle_limit")
        if int(row["memory_used_mib"]) > GPU_IDLE_MAX_MEMORY_USED_MIB:
            reasons.append("memory_use_above_idle_limit")
        decisions[str(row["physical_gpu_id"])] = {
            "eligible": not reasons,
            "rejection_reasons": reasons,
        }
        if not reasons:
            eligible.append(int(row["physical_gpu_id"]))
    return (eligible[0] if eligible else None), decisions


class GpuMemoryMonitor:
    """Sample one GPU and terminate only this monitor subprocess."""

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
        except Exception as exc:
            self.errors.append(f"{type(exc).__name__}: {exc}")

    def __exit__(self, exc_type, exc, traceback_value) -> None:
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


def _build_s2_stage_gpu(
    spectra: Sequence[ComponentSpectrum],
    time_value: float,
    weight: float,
):
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    dimension = spectra[0].dimension
    stage = cp.eye(dimension, dtype=cp.complex128)
    half_gates = []
    for spectrum in spectra[:-1]:
        gate = gpu_csr_matrix(
            component_exponential(spectrum, time_value * weight / 2.0)
        )
        half_gates.append(gate)
        stage = gate @ stage
    last_gate = gpu_csr_matrix(
        component_exponential(spectra[-1], time_value * weight)
    )
    stage = last_gate @ stage
    for gate in reversed(half_gates):
        stage = gate @ stage
    return stage


def _build_pf_unitary_gpu(
    spectra: Sequence[ComponentSpectrum],
    sequence: Sequence[float],
    time_value: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp

    cache: dict[float, Any] = {}
    stage_seconds = {}
    started = time.perf_counter()
    for weight in dict.fromkeys(float(value) for value in sequence):
        stage_started = time.perf_counter()
        cache[weight] = _build_s2_stage_gpu(spectra, time_value, weight)
        cp.cuda.Stream.null.synchronize()
        stage_seconds[repr(weight)] = float(
            time.perf_counter() - stage_started
        )
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
) -> tuple[dict[str, Any], np.ndarray, int]:
    schur_started = time.perf_counter()
    triangular, vectors = schur(
        unitary, output="complex", check_finite=False
    )
    schur_seconds = time.perf_counter() - schur_started
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    signed_shift = float(
        np.angle(np.exp(-1j * energy * time_value) * eigenvalue) / time_value
    )
    vector = vectors[:, selected]
    residual = float(
        np.linalg.norm(unitary @ vector - eigenvalue * vector)
    )
    point = {
        "time": float(time_value),
        "principal_signed_shift_hartree": signed_shift,
        "signed_direct_shift_hartree": signed_shift,
        "direct_error_hartree": abs(signed_shift),
        "direct_cost": holdout._cost(
            float(time_value), abs(signed_shift), rotations
        ),
        "selection_rule": "maximum exact-ground-state overlap",
        "selected_schur_index": selected,
        "selected_eigenvalue": eigenvalue,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "ground_overlap_probability": float(overlaps[selected]),
        "eigenpair_residual_2_norm": residual,
        "schur_off_diagonal_residual_frobenius_norm": float(
            np.linalg.norm(triangular - np.diag(eigenvalues))
        ),
        "timing_seconds": {"cpu_schur": float(schur_seconds)},
    }
    del triangular
    return point, vectors, selected


class DirectEvaluator:
    def __init__(
        self,
        system: dict[str, Any],
        sequence: Sequence[float],
        rotations: int,
        backend: str = "cpu",
        gpu_id: int | None = None,
    ):
        self.system = system
        self.sequence = list(map(float, sequence))
        self.rotations = int(rotations)
        self.backend = str(backend)
        self.gpu_id = gpu_id
        self.cache: list[dict[str, Any]] = []
        self.maximum_gpu_peak_delta_mib: int | None = None
        self.maximum_gpu_pool_reserved_bytes = 0

    def set_backend(self, backend: str, gpu_id: int | None) -> None:
        self.backend = str(backend)
        self.gpu_id = gpu_id

    def _matching(self, time_value: float) -> dict[str, Any] | None:
        for record in self.cache:
            if abs(float(record["time"]) - float(time_value)) <= 1e-12 * max(
                1.0, abs(float(time_value))
            ):
                return record
        return None

    def calculate_uncached(
        self, time_value: float, backend: str, gpu_id: int | None = None
    ) -> dict[str, Any]:
        started = time.perf_counter()
        rss_before = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        gpu_memory = None
        if backend == "cpu":
            unitary, build = holdout._build_pf_unitary_cpu(
                self.system["component_spectra"],
                self.sequence,
                float(time_value),
            )
        elif backend == "gpu":
            if gpu_id is None:
                raise RuntimeError("GPU backend requires a physical GPU id")
            before = next(
                row for row in _gpu_snapshot()
                if int(row["physical_gpu_id"]) == int(gpu_id)
            )
            baseline = int(before["memory_used_mib"])
            with GpuMemoryMonitor(gpu_id) as monitor:
                unitary, build = _build_pf_unitary_gpu(
                    self.system["component_spectra"],
                    self.sequence,
                    float(time_value),
                )
            gpu_memory = monitor.summary(baseline)
            peak_delta = gpu_memory["peak_delta_mib"]
            if peak_delta is not None:
                if self.maximum_gpu_peak_delta_mib is None:
                    self.maximum_gpu_peak_delta_mib = int(peak_delta)
                else:
                    self.maximum_gpu_peak_delta_mib = max(
                        self.maximum_gpu_peak_delta_mib, int(peak_delta)
                    )
            self.maximum_gpu_pool_reserved_bytes = max(
                self.maximum_gpu_pool_reserved_bytes,
                int(build["cupy_memory_pool_reserved_bytes_before_release"]),
            )
        else:
            raise ValueError(f"unknown backend: {backend}")
        point, vectors, selected = _analyze_unitary(
            unitary,
            np.asarray(self.system["state"]),
            float(self.system["energy"]),
            float(time_value),
            self.rotations,
        )
        point["timing_seconds"].update(build)
        point["timing_seconds"]["total"] = float(
            time.perf_counter() - started
        )
        point["backend"] = backend
        point["peak_cpu_rss_kib_after"] = int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
        point["peak_cpu_rss_kib_before"] = rss_before
        if gpu_memory is not None:
            point["gpu_memory"] = gpu_memory
        return {
            "time": float(time_value),
            "point": point,
            "vectors": vectors,
            "selected_index": selected,
        }

    def seed(self, record: dict[str, Any]) -> None:
        if self._matching(float(record["time"])) is None:
            self.cache.append(record)

    def direct(self, time_value: float) -> dict[str, Any]:
        cached = self._matching(float(time_value))
        if cached is None:
            cached = self.calculate_uncached(
                float(time_value), self.backend, self.gpu_id
            )
            self.cache.append(cached)
            reused = False
        else:
            reused = True
        point = copy.deepcopy(cached["point"])
        point["cache_reused"] = reused
        return point

    def annotate_branch(self, points: Sequence[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(self.cache, key=lambda item: float(item["time"]))
        diagnostics: dict[str, dict[str, Any]] = {}
        previous_vector = None
        previous_shift = None
        continuity_agreement = []
        for record in ordered:
            point = record["point"]
            vectors = record["vectors"]
            selected = int(record["selected_index"])
            principal = float(point["principal_signed_shift_hartree"])
            if previous_vector is None:
                previous_overlap = None
                continuation_index = selected
                same = True
                winding = 0
                signed_shift = principal
            else:
                continuation = np.abs(
                    vectors.conj().T @ previous_vector
                ) ** 2
                continuation_index = int(np.argmax(continuation))
                previous_overlap = float(continuation[selected])
                same = continuation_index == selected
                period = 2.0 * np.pi / float(record["time"])
                winding = int(round((previous_shift - principal) / period))
                signed_shift = float(principal + winding * period)
            diagnostics[float(record["time"]).hex()] = {
                "overlap_with_previous_selected_probability": previous_overlap,
                "maximum_previous_overlap_schur_index": continuation_index,
                "ground_and_continuation_selection_agree": bool(same),
                "phase_unwrap_winding": winding,
                "unwrapped_signed_shift_hartree": signed_shift,
            }
            continuity_agreement.append(bool(same))
            previous_vector = vectors[:, selected].copy()
            previous_shift = signed_shift

        for point in points:
            diagnostic = diagnostics[float(point["time"]).hex()]
            point.update(diagnostic)
            if diagnostic["phase_unwrap_winding"] != 0:
                raise RuntimeError(
                    "nonzero eigenphase winding requires metric recomputation"
                )

        adjacent = [
            float(item["overlap_with_previous_selected_probability"])
            for item in diagnostics.values()
            if item["overlap_with_previous_selected_probability"] is not None
        ]
        residuals = [
            float(record["point"]["eigenpair_residual_2_norm"])
            for record in ordered
        ]
        ground_overlaps = [
            float(record["point"]["ground_overlap_probability"])
            for record in ordered
        ]
        checks = {
            "ground_and_continuation_selection_agree_at_all_times": all(
                continuity_agreement
            ),
            "all_phase_unwrap_windings_zero": all(
                item["phase_unwrap_winding"] == 0
                for item in diagnostics.values()
            ),
            "maximum_eigenpair_residual_within_tolerance": (
                max(residuals) <= BRANCH_RESIDUAL_TOLERANCE
            ),
        }
        return {
            "selection_definition": (
                "direct error uses maximum exact-ground-state overlap; "
                "adjacent-time continuation is an independent validity gate"
            ),
            "time_order": [float(record["time"]) for record in ordered],
            "minimum_ground_overlap_probability": min(ground_overlaps),
            "minimum_adjacent_time_overlap_probability": (
                min(adjacent) if adjacent else None
            ),
            "maximum_eigenpair_residual_2_norm": max(residuals),
            "checks": checks,
            "passed": all(checks.values()),
        }


def _benchmark(
    evaluator: DirectEvaluator,
    time_value: float,
    preparation_seconds: float,
    condition_workers: int,
) -> dict[str, Any]:
    snapshot = _gpu_snapshot()
    gpu_id, decisions = _idle_gpu_choice(snapshot)
    cpu_record = evaluator.calculate_uncached(time_value, "cpu")
    cpu_point = copy.deepcopy(cpu_record["point"])
    gpu_attempt: dict[str, Any]
    selected_backend = "cpu"
    selected_gpu_id = None
    selected_seconds = float(cpu_point["timing_seconds"]["total"])

    if gpu_id is None:
        evaluator.seed(cpu_record)
        gpu_attempt = {
            "status": "skipped_no_idle_gpu",
            "reason": (
                "All allowed GPUs exceeded the predeclared idle utilization "
                "or memory-use threshold; no existing process was touched."
            ),
        }
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(int(gpu_id))
        gpu_record = evaluator.calculate_uncached(time_value, "gpu", gpu_id)
        gpu_point = copy.deepcopy(gpu_record["point"])
        shift_difference = abs(
            float(gpu_point["signed_direct_shift_hartree"])
            - float(cpu_point["signed_direct_shift_hartree"])
        )
        cpu_cost = float(cpu_point["direct_cost"])
        gpu_cost = float(gpu_point["direct_cost"])
        cost_difference = abs(gpu_cost / cpu_cost - 1.0)
        checks = {
            "signed_shift_within_tolerance": (
                shift_difference <= GPU_SHIFT_TOLERANCE_HARTREE
            ),
            "direct_cost_within_tolerance": (
                cost_difference <= GPU_COST_RELATIVE_TOLERANCE
            ),
        }
        gpu_attempt = {
            "status": "complete",
            "physical_gpu_id": int(gpu_id),
            "point": gpu_point,
            "signed_shift_absolute_difference_hartree": shift_difference,
            "direct_cost_relative_difference": cost_difference,
            "checks": checks,
            "passed": all(checks.values()),
        }
        if all(checks.values()) and float(
            gpu_point["timing_seconds"]["total"]
        ) < float(cpu_point["timing_seconds"]["total"]):
            selected_backend = "gpu"
            selected_gpu_id = int(gpu_id)
            selected_seconds = float(gpu_point["timing_seconds"]["total"])
            evaluator.seed(gpu_record)
        else:
            evaluator.seed(cpu_record)

    batches = 1 + math.ceil(
        (len(CONDITIONS) - 1)
        / max(1, 1 if selected_backend == "gpu" else int(condition_workers))
    )
    projected = float(
        batches
        * (
            float(preparation_seconds)
            + ESTIMATED_DIRECT_POINTS_PER_CONDITION * selected_seconds
        )
    )
    feasible = projected <= FEASIBLE_MAX_PROJECTED_WALL_SECONDS
    evaluator.set_backend(selected_backend, selected_gpu_id)
    return {
        "status": "complete",
        "representative_condition": PILOT_CONDITION,
        "representative_formula": "two_term_center",
        "representative_time": float(time_value),
        "cpu_point": cpu_point,
        "gpu_snapshot_before": snapshot,
        "gpu_idle_gate": {
            "maximum_utilization_percent": GPU_IDLE_MAX_UTILIZATION_PERCENT,
            "maximum_memory_used_mib": GPU_IDLE_MAX_MEMORY_USED_MIB,
            "decisions": decisions,
        },
        "gpu_attempt": gpu_attempt,
        "selected_backend": selected_backend,
        "selected_physical_gpu_id": selected_gpu_id,
        "selected_point_seconds": selected_seconds,
        "estimated_direct_points_per_condition": (
            ESTIMATED_DIRECT_POINTS_PER_CONDITION
        ),
        "projected_all_conditions_wall_seconds": projected,
        "feasible_limit_seconds": FEASIBLE_MAX_PROJECTED_WALL_SECONDS,
        "feasible": feasible,
        "gpu_implementation_reference": GPU_IMPLEMENTATION_REFERENCE,
    }


def _local_grid(
    evaluator: DirectEvaluator,
    model: dict[str, Any],
    optimum: dict[str, Any],
    analytic_time: float,
    checkpoint: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    points = []
    for relative in LOCAL_GRID_RELATIVE_TO_T_STAR:
        target_time = float(relative) * float(optimum["time"])
        point = evaluator.direct(target_time)
        prediction = holdout._model_prediction(model, target_time)
        point.update(
            {
                "relative_to_t_star": float(relative),
                "relative_to_t_ana": float(target_time / analytic_time),
                "two_term_signed_shift_hartree": prediction,
                "two_term_error_hartree": abs(prediction),
                "two_term_cost": holdout._cost(
                    target_time, abs(prediction), evaluator.rotations
                ),
                "two_term_signed_residual_hartree": float(
                    point["signed_direct_shift_hartree"] - prediction
                ),
                "two_term_residual_over_epsilon": float(
                    abs(point["signed_direct_shift_hartree"] - prediction)
                    / holdout.EPSILON_E
                ),
            }
        )
        points.append(point)
        checkpoint(points)
    finite = [point for point in points if point["direct_cost"] is not None]
    minimum = min(finite, key=lambda point: float(point["direct_cost"]))
    minimum_index = points.index(minimum)
    return points, {
        "protocol": "fixed seven-point grid frozen before stretched-NH3 run",
        "relative_to_t_star": list(LOCAL_GRID_RELATIVE_TO_T_STAR),
        "direct_grid_minimum": minimum,
        "final_grid_bracketed": bool(0 < minimum_index < len(points) - 1),
    }


def _model_definition_records(
    formula: dict[str, Any],
    additional_points: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    definitions = comparison._model_definitions(formula)
    validation = sorted(
        formula["local_direct_points"], key=lambda point: float(point["time"])
    )
    direct_minimum = min(
        (point for point in validation if point["direct_cost"] is not None),
        key=lambda point: float(point["direct_cost"]),
    )
    models = {}
    for model_name, definition in definitions.items():
        predictions = []
        for point in validation:
            predicted_shift = comparison._model_shift(
                definition, float(point["time"])
            )
            predicted_cost = holdout._cost(
                float(point["time"]),
                abs(predicted_shift),
                int(formula["rotations_per_pf_step"]),
            )
            direct_cost = point["direct_cost"]
            predictions.append(
                {
                    "time": float(point["time"]),
                    "relative_to_t_ana": float(point["relative_to_t_ana"]),
                    "relative_to_t_star": float(point["relative_to_t_star"]),
                    "signed_direct_shift_hartree": float(
                        point["signed_direct_shift_hartree"]
                    ),
                    "signed_model_shift_hartree": predicted_shift,
                    "residual_over_epsilon": float(
                        abs(
                            float(point["signed_direct_shift_hartree"])
                            - predicted_shift
                        )
                        / holdout.EPSILON_E
                    ),
                    "direct_cost": direct_cost,
                    "model_cost": predicted_cost,
                    "cost_relative_error": (
                        None
                        if direct_cost is None or predicted_cost is None
                        else abs(float(predicted_cost) - float(direct_cost))
                        / float(direct_cost)
                    ),
                }
            )
        if model_name == "two_term":
            schedule_point = min(
                validation,
                key=lambda point: abs(
                    float(point["relative_to_t_star"]) - 1.0
                ),
            )
        else:
            schedule_point = additional_points[model_name]
        target_time = float(definition["predicted_optimal_time"])
        predicted_shift = comparison._model_shift(definition, target_time)
        model_cost = holdout._cost(
            target_time,
            abs(predicted_shift),
            int(formula["rotations_per_pf_step"]),
        )
        direct_cost = schedule_point["direct_cost"]
        metrics = {
            "predicted_time_cost_relative_error": (
                None
                if model_cost is None or direct_cost is None
                else abs(float(model_cost) - float(direct_cost))
                / float(direct_cost)
            ),
            "direct_cost_loss_against_local_grid": (
                None
                if direct_cost is None
                else float(direct_cost) / float(direct_minimum["direct_cost"])
                - 1.0
            ),
            "predicted_time_difference_from_local_grid_minimum": abs(
                target_time / float(direct_minimum["time"]) - 1.0
            ),
            "maximum_unseen_residual_over_epsilon": max(
                float(point["residual_over_epsilon"])
                for point in predictions
            ),
        }
        threshold_map = {
            "predicted_time_cost_relative_error": 0.01,
            "direct_cost_loss_against_local_grid": 0.01,
            "predicted_time_difference_from_local_grid_minimum": 0.05,
            "maximum_unseen_residual_over_epsilon": 0.05,
        }
        checks = {
            key: value is not None and float(value) <= threshold_map[key]
            for key, value in metrics.items()
        }
        models[model_name] = {
            "definition": definition,
            "training_points_relative_to_t_ana": list(
                holdout.TRAINING_RELATIVE_TIMES
            ),
            "training_points_excluded_from_validation": True,
            "unseen_grid_relative_to_t_star": list(
                LOCAL_GRID_RELATIVE_TO_T_STAR
            ),
            "unseen_predictions": predictions,
            "accepted_sampled_time_range": comparison._accepted_sampled_intervals(
                predictions, 0.05
            ),
            "predicted_time_direct_point": schedule_point,
            "predicted_time_model_shift_hartree": predicted_shift,
            "predicted_time_model_cost": model_cost,
            "local_direct_minimum": direct_minimum,
            "metrics": metrics,
            "threshold_checks": checks,
            "passed": all(checks.values()),
            "eta_t_scope": "fixed local grid; not a continuous optimum claim",
        }
    return models


def _run_formula(
    formula_name: str,
    weights: Sequence[float],
    system: dict[str, Any],
    formula: dict[str, Any],
    checkpoint: Any,
    backend: str,
    gpu_id: int | None,
    benchmark_requested: bool,
    preparation_seconds: float,
    condition_workers: int,
) -> tuple[dict[str, Any], dict[str, Any] | None, DirectEvaluator]:
    sequence = symmetric_s2_sequence(weights)
    rotations = holdout._rotation_count(system, sequence)
    evaluator = DirectEvaluator(system, sequence, rotations, backend, gpu_id)
    formula.update(
        {
            "status": "short_time_fit",
            "weights": list(map(float, weights)),
            "formal_order": holdout.FORMAL_ORDER,
            "s2_sequence": sequence,
            "s2_stage_count": len(sequence),
            "rotations_per_pf_step": rotations,
        }
    )
    checkpoint()

    def fit_checkpoint(partial: dict[str, Any]) -> None:
        formula["short_time_fit_partial"] = partial
        checkpoint()

    fit = holdout._short_time_fit(system, sequence, fit_checkpoint)
    formula.pop("short_time_fit_partial", None)
    alpha = float(fit["selected_window"]["fixed_order_alpha"])
    analytic_time = holdout._analytic_time(alpha)
    benchmark = None
    if benchmark_requested:
        formula["status"] = "backend_benchmark"
        checkpoint()
        benchmark = _benchmark(
            evaluator,
            analytic_time,
            preparation_seconds,
            condition_workers,
        )
        formula["backend_benchmark"] = benchmark
        checkpoint()
        if not bool(benchmark["feasible"]):
            raise RuntimeError(
                "projected four-condition runtime exceeds feasibility limit"
            )
        backend = str(benchmark["selected_backend"])
        gpu_id = benchmark["selected_physical_gpu_id"]
    evaluator.set_backend(backend, gpu_id)
    formula.update(
        {
            "status": "training_direct_points",
            "selected_backend": backend,
            "selected_physical_gpu_id": gpu_id,
            "short_time_fit": fit,
            "alpha": alpha,
            "analytic_time": analytic_time,
            "one_term_analytic_model_cost": holdout._cost(
                analytic_time, alpha * analytic_time**4, rotations
            ),
            "training_direct_points": [],
        }
    )
    checkpoint()

    for relative in holdout.TRAINING_RELATIVE_TIMES:
        point = evaluator.direct(float(relative) * analytic_time)
        point.update(
            {
                "relative_to_t_ana": float(relative),
                "one_term_model_error_hartree": float(
                    alpha * point["time"] ** 4
                ),
                "used_for_model_fit": True,
            }
        )
        formula["training_direct_points"].append(point)
        checkpoint()

    two_term = holdout._fit_two_term(
        formula["training_direct_points"], alpha, analytic_time
    )
    optimum = holdout._model_optimum(two_term, analytic_time, rotations)
    formula.update(
        {
            "status": "local_direct_grid",
            "two_term_model": two_term,
            "two_term_model_optimum": optimum,
            "local_direct_points": [],
        }
    )
    checkpoint()

    def local_checkpoint(points: list[dict[str, Any]]) -> None:
        formula["local_direct_points"] = points
        checkpoint()

    local_points, local_analysis = _local_grid(
        evaluator, two_term, optimum, analytic_time, local_checkpoint
    )
    formula["local_grid_analysis"] = local_analysis
    definitions = comparison._model_definitions(formula)
    formula["model_definitions"] = definitions
    formula["status"] = "one_term_predicted_direct_points"
    formula["additional_direct_points"] = {}
    checkpoint()

    for model_name in ("original_one_term", "refit_one_term"):
        target = float(definitions[model_name]["predicted_optimal_time"])
        point = evaluator.direct(target)
        point.update(
            {
                "schedule_for_model": model_name,
                "relative_to_t_ana": float(target / analytic_time),
            }
        )
        formula["additional_direct_points"][model_name] = (
            comparison._point_with_all_model_predictions(
                point, definitions, rotations
            )
        )
        checkpoint()

    all_points = (
        formula["training_direct_points"]
        + formula["local_direct_points"]
        + list(formula["additional_direct_points"].values())
    )
    branch = evaluator.annotate_branch(all_points)
    formula["branch_continuity"] = branch
    formula["models"] = _model_definition_records(
        formula, formula["additional_direct_points"]
    )
    two_metrics = formula["models"]["two_term"]["metrics"]
    formula["metrics"] = {
        "eta_star": two_metrics["predicted_time_cost_relative_error"],
        "eta_min": two_metrics["direct_cost_loss_against_local_grid"],
        "eta_t": two_metrics[
            "predicted_time_difference_from_local_grid_minimum"
        ],
        "maximum_unseen_residual_over_epsilon": two_metrics[
            "maximum_unseen_residual_over_epsilon"
        ],
        "minimum_ground_overlap_probability": (
            branch["minimum_ground_overlap_probability"]
        ),
        "minimum_adjacent_time_overlap_probability": (
            branch["minimum_adjacent_time_overlap_probability"]
        ),
        "maximum_eigenpair_residual_2_norm": (
            branch["maximum_eigenpair_residual_2_norm"]
        ),
    }
    formula["passed"] = bool(
        formula["models"]["two_term"]["passed"] and branch["passed"]
    )
    formula["status"] = "complete"
    checkpoint()
    evaluator.cache.clear()
    if not branch["passed"]:
        raise RuntimeError(
            f"{formula_name}: eigenbranch validity gate failed"
        )
    return formula, benchmark, evaluator


def worker(args: argparse.Namespace) -> int:
    condition = str(args.condition)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output.parent / (output.stem + "_work")
    work_dir.mkdir(parents=True, exist_ok=True)
    spec = CONDITIONS[condition]
    payload: dict[str, Any] = {
        "status": "running",
        "started_at": _now(),
        "condition": condition,
        "source_commit": SOURCE_COMMIT,
        "gpu_implementation_reference": GPU_IMPLEMENTATION_REFERENCE,
        "git": holdout._git_state(),
        "environment": {
            "python": platform.python_version(),
            "python_executable": os.path.realpath(sys.executable),
            "packages": _package_versions(),
            "blas_threads": int(args.blas_threads),
            "cuda_visible_devices_at_start": os.environ.get(
                "CUDA_VISIBLE_DEVICES"
            ),
        },
        "protocol": {
            "coefficients_frozen": True,
            "coefficient_search_performed": False,
            "training_relative_to_t_ana": list(
                holdout.TRAINING_RELATIVE_TIMES
            ),
            "training_excluded_from_validation": True,
            "local_grid_relative_to_two_term_t_star": list(
                LOCAL_GRID_RELATIVE_TO_T_STAR
            ),
            "model_optimization_interval_relative_to_t_ana": list(
                holdout.MODEL_OPTIMIZATION_INTERVAL
            ),
            "pass_thresholds": {
                "predicted_time_cost_relative_error": 0.01,
                "direct_cost_loss_against_local_grid": 0.01,
                "predicted_time_difference_from_local_grid_minimum": 0.05,
                "maximum_unseen_residual_over_epsilon": 0.05,
            },
            "direct_error": (
                "signed PF eigenvalue shift from the exact conserved-sector "
                "unitary eigenphase; overlap phase is not substituted"
            ),
        },
        "geometry_transform": {
            "definition": "r_H'=r_N+lambda*(r_H-r_N); N fixed",
            "bond_scale": float(spec["bond_scale"]),
            "reference_geometry_angstrom": list(holdout.NH3_GEOMETRY),
            "stretched_geometry_angstrom": spec["geometry"],
            "geometry_optimization_performed": False,
        },
        "system": None,
        "benchmark": None,
        "formulas": {},
    }

    def checkpoint() -> None:
        holdout._atomic_json(output, payload)

    checkpoint()
    started = time.perf_counter()
    try:
        if str(args.backend) == "gpu":
            if args.gpu_id is None:
                raise RuntimeError("GPU worker requires --gpu-id")
            snapshot = _gpu_snapshot()
            selected = next(
                row
                for row in snapshot
                if int(row["physical_gpu_id"]) == int(args.gpu_id)
            )
            _, decisions = _idle_gpu_choice(snapshot)
            decision = decisions[str(int(args.gpu_id))]
            payload["environment"]["gpu_start_snapshot"] = selected
            payload["environment"]["gpu_start_idle_gate"] = decision
            checkpoint()
            if not bool(decision["eligible"]):
                raise RuntimeError(
                    "selected GPU is no longer idle; refusing to displace "
                    "an existing process"
                )
            os.environ["CUDA_VISIBLE_DEVICES"] = str(int(args.gpu_id))
            payload["environment"]["cuda_visible_devices_effective"] = (
                os.environ["CUDA_VISIBLE_DEVICES"]
            )
        print(f"{condition}: prepare active-space system", flush=True)
        system, metadata = holdout._prepare_system(
            condition,
            spec,
            work_dir,
            int(args.component_processes),
        )
        payload["system"] = metadata
        payload["status"] = "formulas"
        checkpoint()
        backend = str(args.backend)
        gpu_id = args.gpu_id
        evaluators = []
        for formula_name, weights in holdout.FORMULAS.items():
            print(
                f"{condition}/{formula_name}: begin with backend={backend}",
                flush=True,
            )
            formula: dict[str, Any] = {}
            payload["formulas"][formula_name] = formula
            result, benchmark, evaluator = _run_formula(
                formula_name,
                weights,
                system,
                formula,
                checkpoint,
                backend,
                gpu_id,
                bool(args.benchmark and formula_name == "two_term_center"),
                float(metadata["preparation_seconds"]),
                int(args.condition_workers),
            )
            payload["formulas"][formula_name] = result
            evaluators.append(evaluator)
            if benchmark is not None:
                payload["benchmark"] = benchmark
                backend = str(benchmark["selected_backend"])
                gpu_id = benchmark["selected_physical_gpu_id"]
            checkpoint()

        new_formula = payload["formulas"]["two_term_center"]
        current_formula = payload["formulas"]["current_m3"]
        new_cost = float(
            new_formula["models"]["two_term"][
                "predicted_time_direct_point"
            ]["direct_cost"]
        )
        current_cost = float(
            current_formula["models"]["two_term"][
                "predicted_time_direct_point"
            ]["direct_cost"]
        )
        original_fail_two_pass = []
        refit_fail_two_pass = []
        for formula_name, formula in payload["formulas"].items():
            if (
                not formula["models"]["original_one_term"]["passed"]
                and formula["models"]["two_term"]["passed"]
            ):
                original_fail_two_pass.append(formula_name)
            if (
                not formula["models"]["refit_one_term"]["passed"]
                and formula["models"]["two_term"]["passed"]
            ):
                refit_fail_two_pass.append(formula_name)
        payload["comparison"] = {
            "direct_cost_at_each_pf_own_two_term_optimum_ratio_new_over_current": (
                new_cost / current_cost
            ),
            "model_accuracy_and_pf_cost_kept_separate": True,
            "original_one_term_failed_but_two_term_passed": (
                original_fail_two_pass
            ),
            "refit_one_term_failed_but_two_term_passed": refit_fail_two_pass,
        }
        payload.update(
            {
                "status": "complete",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "maximum_gpu_peak_delta_mib": max(
                    (
                        evaluator.maximum_gpu_peak_delta_mib
                        for evaluator in evaluators
                        if evaluator.maximum_gpu_peak_delta_mib is not None
                    ),
                    default=None,
                ),
                "maximum_gpu_pool_reserved_bytes": max(
                    evaluator.maximum_gpu_pool_reserved_bytes
                    for evaluator in evaluators
                ),
            }
        )
        checkpoint()
        print(f"{condition}: complete", flush=True)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        checkpoint()
        traceback.print_exc()
        return 1


def _condition_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "queued"}
    try:
        payload = _load(path)
    except Exception as exc:
        return {"status": "temporarily_unreadable", "error": str(exc)}
    return {
        "status": payload.get("status"),
        "formula_status": {
            name: formula.get("status")
            for name, formula in payload.get("formulas", {}).items()
        },
        "direct_point_counts": {
            name: {
                "training": len(formula.get("training_direct_points", [])),
                "unseen": len(formula.get("local_direct_points", [])),
                "additional": len(formula.get("additional_direct_points", {})),
            }
            for name, formula in payload.get("formulas", {}).items()
        },
        "selected_backend": (
            payload.get("benchmark", {}) or {}
        ).get("selected_backend"),
        "error": payload.get("error"),
    }


def _aggregate(output_dir: Path) -> dict[str, Any]:
    conditions = {
        name: _load(output_dir / "conditions" / f"{name}.json")
        for name in CONDITIONS
    }
    if not all(item.get("status") == "complete" for item in conditions.values()):
        raise RuntimeError("cannot aggregate incomplete condition records")
    records = []
    for condition, item in conditions.items():
        for formula_name, formula in item["formulas"].items():
            records.append(
                {
                    "condition": condition,
                    "bond_scale": float(CONDITIONS[condition]["bond_scale"]),
                    "basis": str(CONDITIONS[condition]["basis"]),
                    "formula": formula_name,
                    "weights": formula["weights"],
                    "analytic_time": float(formula["analytic_time"]),
                    "models": formula["models"],
                    "branch_continuity": formula["branch_continuity"],
                    "two_term_passed_with_branch_gate": bool(formula["passed"]),
                }
            )

    pass_counts = {}
    for formula_name in holdout.FORMULAS:
        pass_counts[formula_name] = {}
        formula_rows = [
            row for row in records if row["formula"] == formula_name
        ]
        for model_name in comparison.MODEL_NAMES:
            pass_counts[formula_name][model_name] = {
                "passed": sum(
                    bool(row["models"][model_name]["passed"])
                    for row in formula_rows
                ),
                "total": len(formula_rows),
            }
    original_fail_two_pass = [
        {"condition": row["condition"], "formula": row["formula"]}
        for row in records
        if not row["models"]["original_one_term"]["passed"]
        and row["models"]["two_term"]["passed"]
    ]
    refit_fail_two_pass = [
        {"condition": row["condition"], "formula": row["formula"]}
        for row in records
        if not row["models"]["refit_one_term"]["passed"]
        and row["models"]["two_term"]["passed"]
    ]
    cost_ratios = {
        condition: float(
            item["comparison"][
                "direct_cost_at_each_pf_own_two_term_optimum_ratio_new_over_current"
            ]
        )
        for condition, item in conditions.items()
    }
    equilibrium = _load(EQUILIBRIUM_SUMMARY)
    equilibrium_reference = {
        condition: {
            "source": str(EQUILIBRIUM_SUMMARY.resolve()),
            "direct_cost_ratio_new_over_current": equilibrium[
                "direct_cost_ratio_new_over_current_at_each_pf_own_two_term_optimum"
            ][condition],
            "records": [
                record
                for record in equilibrium["records"]
                if record["condition"] == condition
            ],
        }
        for condition in ("NH3_631g", "NH3_ccpvdz")
    }
    new_two_term = pass_counts["two_term_center"]["two_term"]
    if new_two_term["passed"] == new_two_term["total"]:
        transfer_statement = (
            "The fixed new PF plus the two-term model passes all four stretched "
            "NH3 basis/geometry holdouts."
        )
    else:
        transfer_statement = (
            "The fixed new PF plus the two-term model does not pass all four "
            "stretched NH3 basis/geometry holdouts."
        )
    original_total = sum(
        pass_counts[name]["original_one_term"]["passed"]
        for name in holdout.FORMULAS
    )
    refit_total = sum(
        pass_counts[name]["refit_one_term"]["passed"]
        for name in holdout.FORMULAS
    )
    two_total = sum(
        pass_counts[name]["two_term"]["passed"]
        for name in holdout.FORMULAS
    )
    if original_total == len(records):
        model_category = 1
    elif refit_total == len(records):
        model_category = 2
    else:
        model_category = 3
    cost_statement = (
        "The new PF has lower direct cost than current_m3 in every stretched "
        "condition at each PF's own two-term optimum."
        if all(value < 1.0 for value in cost_ratios.values())
        else (
            "The new PF is not lower-cost than current_m3 in every stretched "
            "condition at each PF's own two-term optimum."
        )
    )
    payload = {
        "status": "complete",
        "completed_at": _now(),
        "source_commit": SOURCE_COMMIT,
        "execution_git": holdout._git_state(),
        "scope": {
            "new_conditions": list(CONDITIONS),
            "active_space": "CAS(8e,7o), one frozen N 1s canonical orbital",
            "active_space_size_dependence_tested": False,
            "coefficient_search_performed": False,
            "ch4_started": False,
        },
        "benchmark": conditions[PILOT_CONDITION]["benchmark"],
        "pass_counts_by_formula": pass_counts,
        "pass_counts_all_eight_condition_formula_records": {
            "original_one_term": {"passed": original_total, "total": len(records)},
            "refit_one_term": {"passed": refit_total, "total": len(records)},
            "two_term": {"passed": two_total, "total": len(records)},
        },
        "original_one_term_failed_but_two_term_passed": original_fail_two_pass,
        "refit_one_term_failed_but_two_term_passed": refit_fail_two_pass,
        "direct_cost_ratio_new_over_current_at_each_pf_own_two_term_optimum": (
            cost_ratios
        ),
        "model_accuracy_and_pf_cost_kept_separate": True,
        "branch_diagnostics": {
            "all_passed": all(
                bool(row["branch_continuity"]["passed"]) for row in records
            ),
            "minimum_ground_overlap_probability": min(
                float(
                    row["branch_continuity"][
                        "minimum_ground_overlap_probability"
                    ]
                )
                for row in records
            ),
            "minimum_adjacent_time_overlap_probability": min(
                float(
                    row["branch_continuity"][
                        "minimum_adjacent_time_overlap_probability"
                    ]
                )
                for row in records
            ),
            "maximum_eigenpair_residual_2_norm": max(
                float(
                    row["branch_continuity"][
                        "maximum_eigenpair_residual_2_norm"
                    ]
                )
                for row in records
            ),
        },
        "condition_resources": {
            condition: {
                "elapsed_seconds": item["elapsed_seconds"],
                "preparation_seconds": item["system"]["preparation_seconds"],
                "peak_cpu_rss_kib": item["peak_cpu_rss_kib"],
                "maximum_gpu_peak_delta_mib": item[
                    "maximum_gpu_peak_delta_mib"
                ],
                "maximum_gpu_pool_reserved_bytes": item[
                    "maximum_gpu_pool_reserved_bytes"
                ],
            }
            for condition, item in conditions.items()
        },
        "equilibrium_reference_reused_without_recalculation": (
            equilibrium_reference
        ),
        "conclusion": {
            "new_candidate_transfer": transfer_statement,
            "model_comparison_category": model_category,
            "model_comparison_statement": {
                1: "The original one-term model is sufficient on all records.",
                2: "Direct fourth-order recalibration is sufficient on all records.",
                3: (
                    "Adding the sixth-order term is required for full declared "
                    "coverage or stable prediction accuracy."
                ),
            }[model_category],
            "cost_comparison": cost_statement,
        },
        "records": records,
    }
    holdout._atomic_json(output_dir / "summary.json", payload)
    return payload


def _format(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.6g}"


def _write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    benchmark = summary["benchmark"]
    gpu_status = benchmark["gpu_attempt"]["status"]
    lines = [
        "# Fixed m=3 PF validation on bond-stretched NH3",
        "",
        f"Source result commit: {SOURCE_COMMIT}",
        f"Status: {summary['status']}",
        "",
        "## Backend pilot",
        "",
        (
            f"Pilot: {PILOT_CONDITION}, two_term_center at t=t_ana. "
            f"CPU time {_format(benchmark['cpu_point']['timing_seconds']['total'])} s; "
            f"GPU attempt {gpu_status}; selected {benchmark['selected_backend']}. "
            f"Projected wall time {_format(benchmark['projected_all_conditions_wall_seconds'])} s."
        ),
        "",
        (
            "A GPU was used only if it passed the idle-resource gate. Existing "
            "processes were neither stopped nor displaced."
        ),
        "",
        "## Model results",
        "",
        (
            "| condition | PF | model | a4 | a6 | t_ana | t_pred | R_max | "
            "eta_C | eta_min | eta_t | pass |"
        ),
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["records"]:
        for model_name in comparison.MODEL_NAMES:
            model = row["models"][model_name]
            definition = model["definition"]
            metrics = model["metrics"]
            lines.append(
                f"| {row['condition']} | {row['formula']} | {model_name} | "
                f"{_format(definition['a4'])} | {_format(definition['a6'])} | "
                f"{_format(row['analytic_time'])} | "
                f"{_format(definition['predicted_optimal_time'])} | "
                f"{_format(metrics['maximum_unseen_residual_over_epsilon'])} | "
                f"{_format(metrics['predicted_time_cost_relative_error'])} | "
                f"{_format(metrics['direct_cost_loss_against_local_grid'])} | "
                f"{_format(metrics['predicted_time_difference_from_local_grid_minimum'])} | "
                f"{model['passed']} |"
            )
    lines.extend(["", "## Pass counts", ""])
    for formula_name, models in summary["pass_counts_by_formula"].items():
        lines.append(f"- {formula_name}:")
        for model_name in comparison.MODEL_NAMES:
            count = models[model_name]
            lines.append(
                f"  - {model_name}: {count['passed']}/{count['total']}"
            )
    lines.extend(
        [
            "",
            (
                "Original one-term failed but two-term passed: "
                f"{summary['original_one_term_failed_but_two_term_passed']}"
            ),
            (
                "Refitted one-term failed but two-term passed: "
                f"{summary['refit_one_term_failed_but_two_term_passed']}"
            ),
            "",
            "## Direct PF-cost comparison",
            "",
            "| condition | direct cost ratio new/current |",
            "|---|---:|",
        ]
    )
    for condition, ratio in summary[
        "direct_cost_ratio_new_over_current_at_each_pf_own_two_term_optimum"
    ].items():
        lines.append(f"| {condition} | {_format(ratio)} |")
    lines.extend(["", "## Branch and resource diagnostics", ""])
    branch = summary["branch_diagnostics"]
    lines.append(
        "- Branch gate: "
        f"{branch['all_passed']}; minimum ground overlap "
        f"{_format(branch['minimum_ground_overlap_probability'])}; "
        "minimum adjacent-time overlap "
        f"{_format(branch['minimum_adjacent_time_overlap_probability'])}; "
        "maximum eigenpair residual "
        f"{_format(branch['maximum_eigenpair_residual_2_norm'])}."
    )
    lines.extend(
        [
            "",
            "| condition | elapsed s | preparation s | peak CPU RSS KiB | peak GPU delta MiB |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for condition, values in summary["condition_resources"].items():
        lines.append(
            f"| {condition} | {_format(values['elapsed_seconds'])} | "
            f"{_format(values['preparation_seconds'])} | "
            f"{_format(values['peak_cpu_rss_kib'])} | "
            f"{_format(values['maximum_gpu_peak_delta_mib'])} |"
        )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            summary["conclusion"]["new_candidate_transfer"],
            "",
            summary["conclusion"]["model_comparison_statement"],
            "",
            summary["conclusion"]["cost_comparison"],
            "",
            (
                "The equilibrium NH3 records from 73cdbf2 are reused only as a "
                "reference and are not included in the new four-condition pass count."
            ),
            (
                "All eta_t and eta_min values are resolved on the frozen local "
                "grid; they do not establish a continuous optimum."
            ),
            "",
        ]
    )
    (output_dir / "report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def _progress_payload(
    output_dir: Path,
    status: str,
    queued: Sequence[str],
    running: dict[str, subprocess.Popen[Any]],
    failures: dict[str, int],
) -> dict[str, Any]:
    return {
        "status": status,
        "updated_at": _now(),
        "queued": list(queued),
        "running": {
            condition: process.pid for condition, process in running.items()
        },
        "failures": failures,
        "conditions": {
            condition: _condition_status(
                output_dir / "conditions" / f"{condition}.json"
            )
            for condition in CONDITIONS
        },
    }


def launch(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "conditions").mkdir()
    (output_dir / "tmp").mkdir()
    started = time.perf_counter()
    manifest = {
        "status": "pilot",
        "started_at": _now(),
        "source_commit": SOURCE_COMMIT,
        "git": holdout._git_state(),
        "conditions": list(CONDITIONS),
        "pilot_condition": PILOT_CONDITION,
        "execution_strategy": {
            "pilot_then_remaining": True,
            "condition_workers_if_cpu": int(args.condition_workers),
            "blas_threads_per_worker": int(args.blas_threads),
            "component_processes_per_condition": int(
                args.component_processes
            ),
            "gpu_policy": (
                "benchmark/use only an idle GPU 0-3; never stop or displace "
                "an existing process"
            ),
        },
        "resource_snapshot": holdout._resource_snapshot(),
        "existing_json_overwritten": False,
        "main_merged": False,
        "ch4_started": False,
    }
    holdout._atomic_json(output_dir / "run_manifest.json", manifest)
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": str(int(args.blas_threads)),
            "OMP_NUM_THREADS": str(int(args.blas_threads)),
            "MKL_NUM_THREADS": str(int(args.blas_threads)),
            "NUMEXPR_NUM_THREADS": str(int(args.blas_threads)),
            "TMPDIR": str(output_dir / "tmp"),
        }
    )

    def worker_command(
        condition: str,
        backend: str,
        gpu_id: int | None,
        benchmark: bool,
    ) -> list[str]:
        command = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "worker",
            "--condition",
            condition,
            "--output",
            str(output_dir / "conditions" / f"{condition}.json"),
            "--backend",
            backend,
            "--blas-threads",
            str(int(args.blas_threads)),
            "--component-processes",
            str(int(args.component_processes)),
            "--condition-workers",
            str(int(args.condition_workers)),
        ]
        if gpu_id is not None:
            command.extend(["--gpu-id", str(int(gpu_id))])
        if benchmark:
            command.append("--benchmark")
        return command

    pilot_log = (
        output_dir / "conditions" / f"{PILOT_CONDITION}.log"
    ).open("x", encoding="utf-8", buffering=1)
    pilot = subprocess.Popen(
        worker_command(PILOT_CONDITION, "cpu", None, True),
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        stdout=pilot_log,
        stderr=subprocess.STDOUT,
    )
    running = {PILOT_CONDITION: pilot}
    holdout._atomic_json(
        output_dir / "progress.json",
        _progress_payload(output_dir, "pilot", [], running, {}),
    )
    print(f"started pilot {PILOT_CONDITION}: pid={pilot.pid}", flush=True)
    while pilot.poll() is None:
        holdout._atomic_json(
            output_dir / "progress.json",
            _progress_payload(output_dir, "pilot", [], running, {}),
        )
        time.sleep(float(args.poll_seconds))
    pilot_log.close()
    running.clear()
    if pilot.returncode != 0:
        manifest.update(
            {
                "status": "pilot_failed",
                "completed_at": _now(),
                "pilot_returncode": int(pilot.returncode),
                "elapsed_seconds": float(time.perf_counter() - started),
            }
        )
        holdout._atomic_json(output_dir / "run_manifest.json", manifest)
        holdout._atomic_json(
            output_dir / "progress.json",
            _progress_payload(
                output_dir,
                "pilot_failed",
                list(CONDITIONS)[1:],
                {},
                {PILOT_CONDITION: int(pilot.returncode)},
            ),
        )
        return 1

    pilot_payload = _load(
        output_dir / "conditions" / f"{PILOT_CONDITION}.json"
    )
    benchmark = pilot_payload["benchmark"]
    if not bool(benchmark["feasible"]):
        manifest.update(
            {
                "status": "stopped_after_infeasible_pilot",
                "completed_at": _now(),
                "benchmark": benchmark,
                "elapsed_seconds": float(time.perf_counter() - started),
            }
        )
        holdout._atomic_json(output_dir / "run_manifest.json", manifest)
        return 2

    selected_backend = str(benchmark["selected_backend"])
    selected_gpu_id = benchmark["selected_physical_gpu_id"]
    manifest.update(
        {
            "status": "remaining_conditions",
            "benchmark": benchmark,
            "selected_backend": selected_backend,
            "selected_physical_gpu_id": selected_gpu_id,
        }
    )
    holdout._atomic_json(output_dir / "run_manifest.json", manifest)
    queue = list(CONDITIONS)[1:]
    failures: dict[str, int] = {}
    running_handles: dict[
        str, tuple[subprocess.Popen[Any], Any]
    ] = {}
    worker_limit = (
        1 if selected_backend == "gpu" else int(args.condition_workers)
    )
    if selected_backend == "cpu":
        environment["CUDA_VISIBLE_DEVICES"] = ""

    while queue or running_handles:
        while queue and len(running_handles) < worker_limit:
            condition = queue.pop(0)
            log_handle = (
                output_dir / "conditions" / f"{condition}.log"
            ).open("x", encoding="utf-8", buffering=1)
            process = subprocess.Popen(
                worker_command(
                    condition,
                    selected_backend,
                    selected_gpu_id,
                    False,
                ),
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
            running_handles[condition] = (process, log_handle)
            print(f"started {condition}: pid={process.pid}", flush=True)
        running_processes = {
            condition: process
            for condition, (process, _) in running_handles.items()
        }
        holdout._atomic_json(
            output_dir / "progress.json",
            _progress_payload(
                output_dir,
                "remaining_conditions",
                queue,
                running_processes,
                failures,
            ),
        )
        if not running_handles:
            continue
        time.sleep(float(args.poll_seconds))
        for condition, (process, log_handle) in list(
            running_handles.items()
        ):
            returncode = process.poll()
            if returncode is None:
                continue
            log_handle.close()
            del running_handles[condition]
            if returncode != 0:
                failures[condition] = int(returncode)
            print(
                f"finished {condition}: returncode={returncode}", flush=True
            )

    final_status = "failed" if failures else "complete"
    holdout._atomic_json(
        output_dir / "progress.json",
        _progress_payload(output_dir, final_status, [], {}, failures),
    )
    if failures:
        manifest.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "failures": failures,
                "elapsed_seconds": float(time.perf_counter() - started),
            }
        )
        holdout._atomic_json(output_dir / "run_manifest.json", manifest)
        return 1

    summary = _aggregate(output_dir)
    _write_report(output_dir, summary)
    manifest.update(
        {
            "status": "complete",
            "completed_at": _now(),
            "failures": {},
            "summary": str(output_dir / "summary.json"),
            "report": str(output_dir / "report.md"),
            "elapsed_seconds": float(time.perf_counter() - started),
        }
    )
    holdout._atomic_json(output_dir / "run_manifest.json", manifest)
    print(
        "complete: "
        + summary["conclusion"]["new_candidate_transfer"],
        flush=True,
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument(
        "--condition", choices=list(CONDITIONS), required=True
    )
    worker_parser.add_argument("--output", type=Path, required=True)
    worker_parser.add_argument(
        "--backend", choices=("cpu", "gpu"), default="cpu"
    )
    worker_parser.add_argument("--gpu-id", type=int)
    worker_parser.add_argument("--benchmark", action="store_true")
    worker_parser.add_argument("--blas-threads", type=int, default=2)
    worker_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    worker_parser.add_argument("--condition-workers", type=int, default=2)
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--output-dir", type=Path, required=True)
    launch_parser.add_argument(
        "--condition-workers", type=int, default=2
    )
    launch_parser.add_argument("--blas-threads", type=int, default=2)
    launch_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    launch_parser.add_argument("--poll-seconds", type=float, default=10.0)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    if parsed.command == "worker":
        raise SystemExit(worker(parsed))
    raise SystemExit(launch(parsed))
