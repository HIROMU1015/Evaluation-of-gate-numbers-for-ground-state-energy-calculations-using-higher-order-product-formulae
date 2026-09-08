"""Refine predictable-cost comparisons for fixed m3 and m5 formulas.

This script keeps the frozen short-time protocol and PF coefficients.  For
m5 it brackets the first 10-percent model-deviation boundary.  For the fixed
cost-priority m3 candidate it refines the direct-cost minimum near t_ana.
Dense PF unitaries are constructed on one GPU per worker and diagonalized by
a CPU complex Schur decomposition.  No iterative eigensolver is used.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import pickle
import resource
import sys
import time
import traceback
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

import run_gpu_m3_predictability_h7 as base
import run_m3_h8_h9 as protocol
from trotterlib.config import DECOMPO_NUM
from trotterlib.component_sector_pf import (
    find_balanced_z2_symmetry,
    prepare_component_spectra,
)
from trotterlib.product_formula import _get_s2_sequence


M3_CANDIDATE = "m3_local_c1_r2_s007"
M5_LABEL = "4th(m5_best)"
BOUNDARY_TOLERANCE = 0.01
INITIAL_M3_RATIOS = (0.96, 0.98, 1.0, 1.02, 1.04)
M3_OPTIMUM_STEP = 0.01
M3_SEARCH_LIMITS = (0.90, 1.10)


def prepare_h2(args: argparse.Namespace) -> int:
    """Prepare H2 exactly without assuming one half-population sector.

    The PySCF H2 state in this repository spans two half-population sectors.
    Restricting to either one would discard Hamiltonian couplings, so H2 uses
    the full 16-dimensional basis before applying only an exact diagonal-Z2
    symmetry restriction.
    """

    metadata: dict[str, Any] = {
        "status": "running",
        "started_at": base._now(),
        "git": base._git_state(),
        "configuration": {"h_chain": 2, "processes": args.processes},
    }
    base._atomic_json(args.metadata, metadata)
    try:
        started = time.perf_counter()
        source = base._prepare_system(2)
        groups = source["groups"]
        num_qubits = int(source["num_qubits"])
        full_state = np.asarray(source["state"], dtype=np.complex128).reshape(-1)
        full_state /= np.linalg.norm(full_state)
        full_basis = np.arange(1 << num_qubits, dtype=np.int64)
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, num_qubits, full_basis, full_state
        )
        restricted_basis = full_basis[selected]
        restricted_state = full_state[selected].copy()
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
            raise RuntimeError(f"H2 full-basis Z2 residual is {residual}")
        system = {
            "h_chain": 2,
            "ham_name": source["ham_name"],
            "num_qubits": num_qubits,
            "restricted_basis": restricted_basis,
            "state": restricted_state,
            "energy": energy,
            "component_spectra": spectra,
        }
        with args.output.open("wb") as handle:
            pickle.dump(system, handle, protocol=pickle.HIGHEST_PROTOCOL)
        metadata.update(
            {
                "status": "complete",
                "completed_at": base._now(),
                "system": {
                    "h_chain": 2,
                    "num_qubits": num_qubits,
                    "group_count": len(groups),
                    "ground_energy_without_constant_hartree": energy,
                    "basis_strategy": (
                        "full_Hilbert_basis_then_exact_diagonal_Z2; "
                        "no invalid half-population projection"
                    ),
                    "full_basis_dimension": int(full_basis.size),
                    "diagonal_z2_symmetry": symmetry,
                    "symmetry_mask": int(mask),
                    "symmetry_target_bit": int(target),
                    "restricted_ground_state_residual": residual,
                    "component_representation": compact,
                },
                "timing_seconds": {
                    "total_preparation": float(time.perf_counter() - started)
                },
                "temporary_pickle": str(args.output),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        base._atomic_json(args.metadata, metadata)
        print(
            f"prepared H2: full={full_basis.size}, exact Z2 block="
            f"{restricted_state.size}, groups={len(groups)}",
            flush=True,
        )
        return 0
    except Exception:
        metadata.update(
            status="failed",
            completed_at=base._now(),
            traceback=traceback.format_exc(),
        )
        base._atomic_json(args.metadata, metadata)
        traceback.print_exc()
        return 1


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _formula(kind: str, h_chain: int) -> tuple[list[float], int]:
    if kind == "m5":
        return (
            list(map(float, _get_s2_sequence(M5_LABEL))),
            int(DECOMPO_NUM[f"H{h_chain}"][M5_LABEL]),
        )
    candidate = base._candidate_records()[M3_CANDIDATE]
    return (
        base._sequence(candidate["weights"]),
        int(base._rotations(h_chain)),
    )


def _short_time_fit(system: dict[str, Any], sequence: Sequence[float]) -> dict[str, Any]:
    state = np.asarray(system["state"], dtype=np.complex128)
    energy = float(system["energy"])
    points: list[dict[str, Any]] = []
    fit: dict[str, Any] | None = None
    started = time.perf_counter()
    for time_value in protocol.GRID:
        point_started = time.perf_counter()
        evolved = base._apply_pf_components(
            system["component_spectra"], sequence, float(time_value), state
        )
        overlap = complex(np.vdot(state, evolved))
        rotated = np.exp(-1j * energy * float(time_value)) * overlap
        points.append(
            {
                "time": float(time_value),
                "perturbative_error_hartree": abs(
                    float(rotated.imag / float(time_value))
                ),
                "phase_rotated_overlap": rotated,
                "survival_probability": float(abs(rotated) ** 2),
                "evolved_state_norm": float(np.linalg.norm(evolved)),
                "elapsed_seconds": float(time.perf_counter() - point_started),
            }
        )
        if len(points) >= 5:
            fit = protocol.qualify(
                [point["time"] for point in points],
                [point["perturbative_error_hartree"] for point in points],
            )
            if fit["qualified"]:
                break
    if fit is None:
        raise RuntimeError("short-time fit produced no five-point window")
    fit["points"] = points
    fit["elapsed_seconds"] = float(time.perf_counter() - started)
    fit["error_definition"] = (
        "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
    )
    return fit


def _source_configuration(source: Path | None) -> dict[str, Any] | None:
    if source is None:
        return None
    record = _load(source)
    if record.get("status") != "complete":
        raise RuntimeError(f"baseline source is not complete: {source}")
    return {
        "source": str(source),
        "source_git": record.get("git"),
        "alpha": float(record["alpha"]),
        "t_ana": float(record["t_ana"]),
        "short_time_fit": record.get("short_time_fit", record.get("fit")),
        "points": list(record["points"]),
        "source_summary": record.get("summary"),
    }


def _analyze_maximum_ground_branch(
    unitary: np.ndarray,
    state: np.ndarray,
    energy: float,
    time_value: float,
    rotations: int,
    model_error: float,
) -> tuple[dict[str, Any], np.ndarray]:
    """Return the branch with maximum exact-ground-state overlap.

    Refinement points are independent, so phase continuity is diagnosed after
    sorting them.  At the studied times the physical shift is on the principal
    branch; the principal phase is retained explicitly for auditing.
    """

    schur_started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - schur_started
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(ground_overlaps))
    vector = vectors[:, selected].copy()
    eigenvalue = complex(eigenvalues[selected])
    signed_shift = float(
        np.angle(np.exp(-1j * energy * time_value) * eigenvalue) / time_value
    )
    direct_error = abs(signed_shift)
    residual_started = time.perf_counter()
    eigenpair_residual = float(
        np.linalg.norm(unitary @ vector - eigenvalue * vector)
    )
    residual_seconds = time.perf_counter() - residual_started
    return (
        {
            "time": float(time_value),
            "model_error_hartree": float(model_error),
            "signed_direct_shift_hartree": signed_shift,
            "principal_signed_shift_hartree": signed_shift,
            "phase_unwrap_winding": 0,
            "direct_error_hartree": float(direct_error),
            "direct_to_model_ratio": float(direct_error / model_error),
            "direct_cost": base._cost(time_value, direct_error, rotations),
            "ground_overlap_probability": float(ground_overlaps[selected]),
            "selection_rule": "maximum_ground_state_overlap",
            "selected_schur_index": selected,
            "selected_eigenvalue": eigenvalue,
            "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
            "eigenpair_residual_2_norm": eigenpair_residual,
            "schur_off_diagonal_residual_frobenius_norm": float(
                np.linalg.norm(triangular - np.diag(eigenvalues))
            ),
            "timing_seconds": {
                "cpu_schur": float(schur_seconds),
                "cpu_eigenpair_residual": float(residual_seconds),
            },
        },
        vector,
    )


def _passed(point: dict[str, Any]) -> bool:
    return abs(float(point["direct_to_model_ratio"]) - 1.0) <= 0.10


def _ratio_key(value: float) -> str:
    return f"{float(value):.8f}"


class DirectEvaluator:
    def __init__(
        self,
        *,
        system: dict[str, Any],
        sequence: Sequence[float],
        rotations: int,
        alpha: float,
        t_ana: float,
        payload: dict[str, Any],
        output: Path,
    ) -> None:
        self.system = system
        self.sequence = sequence
        self.rotations = int(rotations)
        self.alpha = float(alpha)
        self.t_ana = float(t_ana)
        self.payload = payload
        self.output = output
        self.points: dict[str, dict[str, Any]] = {}
        self.vectors: dict[str, np.ndarray] = {}

    def add_existing(self, point: dict[str, Any]) -> None:
        ratio = float(point["relative_time"])
        self.points[_ratio_key(ratio)] = dict(point)

    def evaluate(self, ratio: float, reason: str) -> dict[str, Any]:
        ratio = round(float(ratio), 8)
        key = _ratio_key(ratio)
        if key in self.points and key in self.vectors:
            return self.points[key]
        time_value = ratio * self.t_ana
        print(
            f"H{self.system['h_chain']} {self.payload['formula']} "
            f"t/t_ana={ratio:.8f}: constructing ({reason})",
            flush=True,
        )
        point_started = time.perf_counter()
        unitary, build = base._build_pf_unitary_gpu(
            self.system["component_spectra"], self.sequence, time_value
        )
        point, vector = _analyze_maximum_ground_branch(
            unitary,
            np.asarray(self.system["state"], dtype=np.complex128),
            float(self.system["energy"]),
            time_value,
            self.rotations,
            self.alpha * time_value**4,
        )
        point["relative_time"] = ratio
        point["reason"] = reason
        point["timing_seconds"].update(build)
        point["timing_seconds"]["point_total"] = float(
            time.perf_counter() - point_started
        )
        self.points[key] = point
        self.vectors[key] = vector
        self.payload["new_points"] = sorted(
            [
                candidate
                for candidate_key, candidate in self.points.items()
                if candidate_key in self.vectors
            ],
            key=lambda candidate: candidate["relative_time"],
        )
        base._atomic_json(self.output, self.payload)
        print(
            f"H{self.system['h_chain']} {self.payload['formula']} "
            f"t/t_ana={ratio:.8f}: ratio={point['direct_to_model_ratio']:.8g}, "
            f"cost={point['direct_cost']}, "
            f"residual={point['eigenpair_residual_2_norm']:.3e}",
            flush=True,
        )
        del unitary
        return point

    def point(self, ratio: float) -> dict[str, Any]:
        return self.points[_ratio_key(ratio)]

    def all_points(self) -> list[dict[str, Any]]:
        return sorted(self.points.values(), key=lambda point: point["relative_time"])

    def new_points(self) -> list[dict[str, Any]]:
        return sorted(
            [self.points[key] for key in self.vectors],
            key=lambda point: point["relative_time"],
        )

    def continuity(self) -> dict[str, Any]:
        ordered = sorted(
            ((float(key), vector) for key, vector in self.vectors.items()),
            key=lambda item: item[0],
        )
        adjacent = []
        for (left_ratio, left), (right_ratio, right) in zip(ordered, ordered[1:]):
            adjacent.append(
                {
                    "left_relative_time": left_ratio,
                    "right_relative_time": right_ratio,
                    "overlap_probability": float(abs(np.vdot(left, right)) ** 2),
                }
            )
        points = self.new_points()
        return {
            "selection_rule": "maximum_ground_state_overlap_per_point",
            "adjacent_new_point_overlaps": adjacent,
            "minimum_adjacent_new_point_overlap_probability": (
                None
                if not adjacent
                else min(item["overlap_probability"] for item in adjacent)
            ),
            "minimum_ground_overlap_probability": (
                None
                if not points
                else min(float(point["ground_overlap_probability"]) for point in points)
            ),
            "maximum_eigenpair_residual_2_norm": (
                None
                if not points
                else max(float(point["eigenpair_residual_2_norm"]) for point in points)
            ),
        }


def _initial_grid(evaluator: DirectEvaluator) -> None:
    for ratio in base.RELATIVE_TIMES:
        evaluator.evaluate(float(ratio), "common_nine_point_baseline")


def _m5_refinement(evaluator: DirectEvaluator) -> dict[str, Any]:
    ordered = evaluator.all_points()
    last_pass: dict[str, Any] | None = None
    first_fail: dict[str, Any] | None = None
    for point in ordered:
        if last_pass is None or first_fail is None:
            if _passed(point) and first_fail is None:
                last_pass = point
            elif first_fail is None:
                first_fail = point
                break
    if last_pass is None:
        raise RuntimeError("m5 has no 10-percent-valid point")

    extension = float(ordered[-1]["relative_time"])
    while first_fail is None and extension < 2.0:
        extension = round(extension + 0.2, 8)
        candidate = evaluator.evaluate(extension, "boundary_extension")
        if _passed(candidate):
            last_pass = candidate
        else:
            first_fail = candidate
    if first_fail is None:
        valid = [
            point
            for point in evaluator.all_points()
            if point["relative_time"] <= last_pass["relative_time"]
            and _passed(point)
            and point["direct_cost"] is not None
        ]
        minimum = min(valid, key=lambda point: float(point["direct_cost"]))
        return {
            "right_censored": True,
            "last_directly_confirmed_pass": last_pass,
            "first_directly_confirmed_fail": None,
            "bracket_width_over_t_ana": None,
            "C_valid_star": minimum,
        }

    low = float(last_pass["relative_time"])
    high = float(first_fail["relative_time"])
    while high - low > BOUNDARY_TOLERANCE:
        middle = round((low + high) / 2.0, 8)
        point = evaluator.evaluate(middle, "m5_ten_percent_boundary_bisection")
        if _passed(point):
            low = middle
            last_pass = point
        else:
            high = middle
            first_fail = point

    valid = [
        point
        for point in evaluator.all_points()
        if float(point["relative_time"]) <= low
        and _passed(point)
        and point["direct_cost"] is not None
    ]
    minimum = min(valid, key=lambda point: float(point["direct_cost"]))
    return {
        "right_censored": False,
        "last_directly_confirmed_pass": last_pass,
        "first_directly_confirmed_fail": first_fail,
        "bracket_width_over_t_ana": float(high - low),
        "C_valid_star": minimum,
        "definition": (
            "minimum directly evaluated cost at or below the last directly "
            "confirmed point satisfying abs(e_direct/e_model-1)<=0.10"
        ),
    }


def _m3_refinement(evaluator: DirectEvaluator) -> dict[str, Any]:
    for ratio in INITIAL_M3_RATIOS:
        evaluator.evaluate(ratio, "m3_initial_optimum_refinement")

    for _ in range(20):
        candidates = [
            point
            for point in evaluator.all_points()
            if M3_SEARCH_LIMITS[0] <= float(point["relative_time"]) <= M3_SEARCH_LIMITS[1]
            and point["direct_cost"] is not None
        ]
        minimum = min(candidates, key=lambda point: float(point["direct_cost"]))
        ratio = round(float(minimum["relative_time"]), 8)
        neighbors = [
            round(ratio - M3_OPTIMUM_STEP, 8),
            round(ratio + M3_OPTIMUM_STEP, 8),
        ]
        missing = [
            neighbor
            for neighbor in neighbors
            if M3_SEARCH_LIMITS[0] <= neighbor <= M3_SEARCH_LIMITS[1]
            and _ratio_key(neighbor) not in evaluator.points
        ]
        if missing:
            for neighbor in missing:
                evaluator.evaluate(neighbor, "m3_adaptive_optimum_refinement")
            continue
        in_range_neighbors = [
            neighbor
            for neighbor in neighbors
            if M3_SEARCH_LIMITS[0] <= neighbor <= M3_SEARCH_LIMITS[1]
        ]
        neighbor_points = [evaluator.point(neighbor) for neighbor in in_range_neighbors]
        if all(
            float(minimum["direct_cost"]) <= float(point["direct_cost"])
            for point in neighbor_points
        ):
            break
    else:
        raise RuntimeError("m3 optimum refinement did not converge in 20 iterations")

    candidates = [
        point
        for point in evaluator.all_points()
        if M3_SEARCH_LIMITS[0] <= float(point["relative_time"]) <= M3_SEARCH_LIMITS[1]
        and point["direct_cost"] is not None
    ]
    minimum = min(candidates, key=lambda point: float(point["direct_cost"]))
    schedule = evaluator.point(1.0)
    valid_candidates = [point for point in candidates if _passed(point)]
    valid_minimum = min(valid_candidates, key=lambda point: float(point["direct_cost"]))
    return {
        "t_star": minimum,
        "C_direct_at_t_ana": schedule,
        "analytic_schedule_cost_increase": float(
            (float(schedule["direct_cost"]) - float(minimum["direct_cost"]))
            / float(minimum["direct_cost"])
        ),
        "C_valid_star": valid_minimum,
        "t_star_is_ten_percent_valid": _passed(minimum),
        "resolution_over_t_ana": M3_OPTIMUM_STEP,
        "search_limits_over_t_ana": list(M3_SEARCH_LIMITS),
    }


def worker(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise RuntimeError(f"Refusing to overwrite {args.output}")
    payload: dict[str, Any] = {
        "status": "running",
        "started_at": base._now(),
        "git": base._git_state(),
        "h_chain": int(args.h),
        "formula": args.formula,
        "gpu_id": int(args.gpu),
        "new_points": [],
    }
    base._atomic_json(args.output, payload)
    try:
        with args.system.open("rb") as handle:
            system = pickle.load(handle)
        if int(system["h_chain"]) != int(args.h):
            raise RuntimeError("system pickle does not match requested H-chain")
        sequence, rotations = _formula(args.formula, args.h)
        source = _source_configuration(args.baseline)
        if source is None:
            fit = _short_time_fit(system, sequence)
            if not fit["qualified"]:
                raise RuntimeError("formal short-time fit did not qualify")
            alpha = float(fit["selected_window"]["fixed_order_alpha"])
            t_ana = float(base._analytic_time(alpha))
            baseline_points: list[dict[str, Any]] = []
        else:
            fit = source["short_time_fit"]
            alpha = float(source["alpha"])
            t_ana = float(source["t_ana"])
            baseline_points = source["points"]
        payload.update(
            {
                "short_time_fit": fit,
                "alpha": alpha,
                "t_ana": t_ana,
                "baseline": source,
                "pauli_rotations_per_step": rotations,
                "s2_stage_count": len(sequence),
                "unique_s2_stage_count": len(set(sequence)),
                "system": {
                    "num_qubits": int(system["num_qubits"]),
                    "symmetry_block_dimension": int(np.asarray(system["state"]).size),
                },
            }
        )
        base._atomic_json(args.output, payload)

        import cupy as cp

        cp.get_default_memory_pool().set_limit(size=6 * 2**30)
        gpu = base._gpu_info(args.gpu)
        free_bytes, _ = cp.cuda.runtime.memGetInfo()
        required_bytes = (7 if args.h == 9 else 3 if args.h == 8 else 1) * 2**30
        if free_bytes < required_bytes:
            raise RuntimeError(
                f"Insufficient free GPU memory: {free_bytes} < {required_bytes}; "
                "stopping only this worker"
            )
        payload["environment"] = base._environment(gpu)
        payload["memory_pool_limit_bytes"] = 6 * 2**30
        evaluator = DirectEvaluator(
            system=system,
            sequence=sequence,
            rotations=rotations,
            alpha=alpha,
            t_ana=t_ana,
            payload=payload,
            output=args.output,
        )
        for point in baseline_points:
            evaluator.add_existing(point)

        started = time.perf_counter()
        with base.GpuMemoryMonitor(args.gpu) as monitor:
            if not baseline_points:
                _initial_grid(evaluator)
            if args.formula == "m5":
                result = _m5_refinement(evaluator)
            else:
                result = _m3_refinement(evaluator)
        payload["result"] = result
        payload["branch_reliability"] = evaluator.continuity()
        payload["gpu_memory"] = monitor.summary(gpu["memory_used_mib"])
        payload["additional_direct_seconds"] = float(time.perf_counter() - started)
        payload["status"] = "complete"
        payload["completed_at"] = base._now()
        base._atomic_json(args.output, payload)
        return 0
    except Exception:
        payload.update(
            status="failed",
            completed_at=base._now(),
            traceback=traceback.format_exc(),
        )
        base._atomic_json(args.output, payload)
        traceback.print_exc()
        return 1


def aggregate(args: argparse.Namespace) -> int:
    records = [_load(path) for path in args.inputs]
    incomplete = [
        f"H{record.get('h_chain')}_{record.get('formula')}"
        for record in records
        if record.get("status") != "complete"
    ]
    systems: dict[str, Any] = {}
    for h_chain in sorted({int(record["h_chain"]) for record in records}):
        by_formula = {
            record["formula"]: record
            for record in records
            if int(record["h_chain"]) == h_chain
        }
        if set(by_formula) != {"m3", "m5"}:
            continue
        m3 = by_formula["m3"]
        m5 = by_formula["m5"]
        if m3.get("status") != "complete" or m5.get("status") != "complete":
            continue
        m3_valid = m3["result"]["C_valid_star"]
        m5_valid = m5["result"]["C_valid_star"]
        input_by_name = {path.name: path for path in args.inputs}
        systems[f"H{h_chain}"] = {
            "m3_source": str(input_by_name[f"H{h_chain}_m3.json"]),
            "m5_source": str(input_by_name[f"H{h_chain}_m5.json"]),
            "m3_t_star_over_t_ana": m3["result"]["t_star"]["relative_time"],
            "m3_C_direct_at_t_ana": m3["result"]["C_direct_at_t_ana"]["direct_cost"],
            "m3_C_direct_at_t_star": m3["result"]["t_star"]["direct_cost"],
            "m3_schedule_cost_increase": m3["result"]["analytic_schedule_cost_increase"],
            "m3_C_valid_star": m3_valid["direct_cost"],
            "m5_boundary": {
                "last_pass_over_t_ana": m5["result"]["last_directly_confirmed_pass"]["relative_time"],
                "first_fail_over_t_ana": (
                    None
                    if m5["result"]["first_directly_confirmed_fail"] is None
                    else m5["result"]["first_directly_confirmed_fail"]["relative_time"]
                ),
                "width_over_t_ana": m5["result"]["bracket_width_over_t_ana"],
                "right_censored": m5["result"]["right_censored"],
            },
            "m5_C_valid_star": m5_valid["direct_cost"],
            "C_valid_star_ratio_m3_over_m5": float(
                m3_valid["direct_cost"] / m5_valid["direct_cost"]
            ),
        }
    payload = {
        "status": "complete" if not incomplete else "incomplete",
        "created_at": base._now(),
        "git": base._git_state(),
        "protocol": {
            "m3_candidate": M3_CANDIDATE,
            "m5_label": M5_LABEL,
            "short_time_protocol": "unchanged e4bcd03 formal protocol",
            "m5_boundary_width_target_over_t_ana": BOUNDARY_TOLERANCE,
            "m3_optimum_resolution_over_t_ana": M3_OPTIMUM_STEP,
        },
        "incomplete_workers": incomplete,
        "systems": systems,
    }
    base._atomic_json(args.output, payload)
    lines = [
        "# Predictable-cost refinement for fixed m3 and m5",
        "",
        "| System | m5 10% boundary [pass, fail] | m5 C_valid* | "
        "m3 t*/t_ana | m3 C(t_ana) | m3 C(t*) | schedule increase | "
        "m3/m5 C_valid* |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in systems.items():
        boundary = result["m5_boundary"]
        lines.append(
            f"| {name} | [{boundary['last_pass_over_t_ana']}, "
            f"{boundary['first_fail_over_t_ana']}] | "
            f"{result['m5_C_valid_star']:.7e} | "
            f"{result['m3_t_star_over_t_ana']:.2f} | "
            f"{result['m3_C_direct_at_t_ana']:.7e} | "
            f"{result['m3_C_direct_at_t_star']:.7e} | "
            f"{result['m3_schedule_cost_increase']:.3%} | "
            f"{result['C_valid_star_ratio_m3_over_m5']:.6f} |"
        )
    if incomplete:
        lines += ["", "Incomplete workers: " + ", ".join(incomplete)]
    lines += [
        "",
        "Cancellation points outside each contiguous 10% model-valid range "
        "are excluded from C_valid*.",
        "",
        "No coefficient search, H10 calculation, molecule extension, or target-error change was performed.",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not incomplete:
        args.complete.write_text(base._now() + "\n", encoding="utf-8")
    return 0 if not incomplete else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument("--h", type=int, choices=[2, 4, 5, 6, 7, 8, 9], required=True)
    worker_parser.add_argument("--formula", choices=["m3", "m5"], required=True)
    worker_parser.add_argument("--gpu", type=int, required=True)
    worker_parser.add_argument("--system", type=Path, required=True)
    worker_parser.add_argument("--baseline", type=Path)
    worker_parser.add_argument("--output", type=Path, required=True)
    prepare_parser = subparsers.add_parser("prepare-h2")
    prepare_parser.add_argument("--processes", type=int, default=1)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--metadata", type=Path, required=True)
    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    aggregate_parser.add_argument("--output", type=Path, required=True)
    aggregate_parser.add_argument("--report", type=Path, required=True)
    aggregate_parser.add_argument("--complete", type=Path, required=True)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    if arguments.mode == "prepare-h2":
        sys.exit(prepare_h2(arguments))
    if arguments.mode == "worker":
        sys.exit(worker(arguments))
    sys.exit(aggregate(arguments))
