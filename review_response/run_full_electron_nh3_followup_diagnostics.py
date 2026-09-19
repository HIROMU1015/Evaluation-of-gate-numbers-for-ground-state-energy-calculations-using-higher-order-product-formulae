"""Post-hoc NH3 diagnostics for the joint PF optimum and failed short-time fits."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import pickle
import resource
import time
from typing import Any, Sequence

import numpy as np

import run_full_electron_nh3_higher_term_diagnosis as base
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import symmetric_s2_sequence


FINE_RATIOS = tuple(float(value) for value in np.arange(0.92, 1.021, 0.01))
EXTENDED_SHORT_GRID = tuple(float(value) for value in np.geomspace(0.01, 0.06, 13))
SHORT_CONDITIONS = (
    ("equilibrium", "yoshida4"),
    ("equilibrium", "paper_new4"),
    ("equilibrium", "m5_best"),
    ("equilibrium", "yoshida6_m3"),
    ("stretch150", "paper_new4"),
    ("stretch150", "m5_best"),
    ("stretch150", "yoshida6_m3"),
)


def now() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ratio_key(value: float) -> str:
    return f"r{int(round(100.0 * float(value))):03d}"


def apply_pf_gpu(
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    physical_gpu: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    started = time.perf_counter()
    materialization = 0.0
    transfer_and_action = 0.0
    pool = cp.get_default_memory_pool()
    pool.free_all_blocks()
    with base.GpuMemoryMonitor(physical_gpu) as monitor:
        current = cp.asarray(system["state"], dtype=cp.complex128)
        gates: dict[tuple[int, float], Any] = {}
        for group_index, raw_weight in base.iter_s2_sequence_steps(
            len(system["component_spectra"]), sequence
        ):
            key = (int(group_index), float(raw_weight))
            gate = gates.get(key)
            if gate is None:
                gate_started = time.perf_counter()
                gate_cpu = base.component_exponential(
                    system["component_spectra"][group_index],
                    float(time_value) * float(raw_weight),
                )
                materialization += time.perf_counter() - gate_started
                transfer_started = time.perf_counter()
                gate = gpu_csr_matrix(gate_cpu)
                cp.cuda.Stream.null.synchronize()
                transfer_and_action += time.perf_counter() - transfer_started
                gates[key] = gate
                del gate_cpu
            action_started = time.perf_counter()
            current = gate @ current
            cp.cuda.Stream.null.synchronize()
            transfer_and_action += time.perf_counter() - action_started
        result = cp.asnumpy(current)
        cp.cuda.Stream.null.synchronize()
        pool_peak = int(pool.total_bytes())
        del current, gates
        pool.free_all_blocks()
    return result, {
        "backend": "gpu_exact_sector_matrix_free_state_action",
        "physical_gpu_id": int(physical_gpu),
        "elapsed_seconds": float(time.perf_counter() - started),
        "cpu_component_gate_materialization_seconds": float(materialization),
        "gpu_transfer_and_action_seconds": float(transfer_and_action),
        "cupy_pool_peak_reserved_mib": float(pool_peak / 2**20),
        "gpu_memory": monitor.summary(),
    }


def qualify_extended(
    times: Sequence[float], errors: Sequence[float], order: int
) -> dict[str, Any]:
    windows = rolling_loglog_fits(
        np.asarray(times),
        np.asarray(errors),
        formal_order=int(order),
        noise_floor=base.FIT_NOISE_FLOOR,
        window_size=base.FIT_WINDOW,
    )
    eligible = [
        window
        for window in windows
        if float(window["order_deviation"]) <= base.FIT_ORDER_TOLERANCE
        and float(window["r2"]) >= base.FIT_MINIMUM_R2
    ]
    selected = min(
        eligible, key=lambda item: int(item["start_index"]), default=None
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "formal_order": int(order),
        "grid": list(map(float, times)),
        "noise_floor": base.FIT_NOISE_FLOOR,
        "window_size": base.FIT_WINDOW,
        "order_tolerance": base.FIT_ORDER_TOLERANCE,
        "minimum_r2": base.FIT_MINIMUM_R2,
        "selection_rule": (
            "earliest qualifying consecutive five-point window on the preregistered "
            "extended diagnostic grid"
        ),
    }


def effective_orders(times: Sequence[float], errors: Sequence[float]) -> list[float | None]:
    result: list[float | None] = [None]
    for left_t, right_t, left_e, right_e in zip(
        times[:-1], times[1:], errors[:-1], errors[1:]
    ):
        if left_e <= 0.0 or right_e <= 0.0:
            result.append(None)
        else:
            result.append(
                float(math.log(right_e / left_e) / math.log(right_t / left_t))
            )
    return result


def command_joint_worker(args: argparse.Namespace) -> int:
    system = base._load_system(args.system_cache)
    if system["geometry"] != "stretch150":
        raise RuntimeError("joint fine scan requires the stretch150 system")
    source = load_json(args.source_json)
    result = source["models"]["three_term"]
    model = result["model"]
    t_star = float(result["model_optimum"]["time"])
    formula = base._formulae()["joint_refine_r0_s0046"]
    sequence = symmetric_s2_sequence(formula["weights"])
    rotations = base._rotation_count(system, sequence)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.vector_dir.mkdir(parents=True, exist_ok=True)

    for ratio in args.ratios:
        key = ratio_key(ratio)
        point, vector = base._direct_point(
            system,
            sequence,
            float(ratio) * t_star,
            rotations,
            "gpu",
            args.gpu_id,
            None,
        )
        prediction = base._prediction(model, point["time"])
        point.update(
            {
                "status": "complete",
                "created_at": now(),
                "diagnostic_kind": "post_hoc_fine_optimum_scan",
                "post_hoc": True,
                "formula_name": "joint_refine_r0_s0046",
                "geometry": "stretch150",
                "physical_gpu_id": args.gpu_id,
                "ratio_to_predicted_t_star": float(ratio),
                "predicted_t_star": t_star,
                "model_signed_shift_hartree": prediction,
                "model_cost": base._cost(point["time"], abs(prediction), rotations),
                "signed_residual_hartree": float(
                    point["signed_direct_shift_hartree"] - prediction
                ),
                "residual_over_epsilon": float(
                    abs(point["signed_direct_shift_hartree"] - prediction)
                    / base.EPSILON_E
                ),
                "rotations": rotations,
                "source_result": str(args.source_json),
                "source_commit": source["git"]["commit"],
                "vector_file": key + ".npy",
            }
        )
        base._atomic_json(args.output_dir / (key + ".json"), point)
        np.save(args.vector_dir / (key + ".npy"), vector)
    return 0


def command_short_worker(args: argparse.Namespace) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    system_cache: dict[str, dict[str, Any]] = {}
    for condition in args.conditions:
        geometry, formula_name = condition.split(":", 1)
        pair = (geometry, formula_name)
        if pair not in SHORT_CONDITIONS:
            raise ValueError(f"unexpected short-time condition: {condition}")
        system = system_cache.get(geometry)
        if system is None:
            system = base._load_system(args.cache_dir / (geometry + ".pkl"))
            system_cache[geometry] = system
        source_path = args.source_dir / (geometry + "_raw") / (formula_name + ".json")
        source = load_json(source_path)
        if source["status"] != "short_time_fit_failed":
            raise RuntimeError(
                f"{condition}: expected short_time_fit_failed, got {source['status']}"
            )
        formula = base._formulae()[formula_name]
        sequence = symmetric_s2_sequence(formula["weights"])
        points: list[dict[str, Any]] = []
        errors: list[float] = []
        signed_errors: list[float] = []
        validation_difference = None
        for index, time_value in enumerate(EXTENDED_SHORT_GRID):
            evolved, profile = apply_pf_gpu(
                system, sequence, time_value, args.gpu_id
            )
            if index == 0:
                cpu_evolved = base._apply_pf(system, sequence, time_value)
                validation_difference = float(
                    np.linalg.norm(evolved - cpu_evolved)
                    / max(np.linalg.norm(cpu_evolved), np.finfo(float).tiny)
                )
                if validation_difference > 1e-10:
                    raise RuntimeError(
                        f"{condition}: CPU/GPU state action mismatch "
                        f"{validation_difference}"
                    )
            overlap = complex(np.vdot(system["state"], evolved))
            rotated = np.exp(-1j * system["energy"] * time_value) * overlap
            signed_error = float(rotated.imag / time_value)
            error = abs(signed_error)
            signed_errors.append(signed_error)
            errors.append(error)
            points.append(
                {
                    "time": time_value,
                    "signed_proxy_error_hartree": signed_error,
                    "proxy_error_hartree": error,
                    "phase_rotated_overlap": rotated,
                    "survival_probability": float(abs(rotated) ** 2),
                    "evolved_state_norm": float(np.linalg.norm(evolved)),
                    "profile": profile,
                }
            )
        orders = effective_orders(EXTENDED_SHORT_GRID, errors)
        for point, order in zip(points, orders):
            point["effective_order_from_previous_point"] = order
            point["above_original_noise_floor"] = (
                point["proxy_error_hartree"] > base.FIT_NOISE_FLOOR
            )
        qualification = qualify_extended(
            EXTENDED_SHORT_GRID, errors, int(formula["formal_order"])
        )
        floor_count = sum(error <= base.FIT_NOISE_FLOOR for error in errors)
        if qualification["qualified"]:
            diagnosis = "asymptotic_window_found_below_original_absolute_grid"
        elif floor_count:
            diagnosis = "extended_grid_partly_limited_by_declared_noise_floor"
        else:
            diagnosis = "formal_order_window_not_found_down_to_t_0p01"
        payload = {
            "status": "complete",
            "created_at": now(),
            "diagnostic_kind": "extended_short_time_effective_order",
            "post_hoc": True,
            "geometry": geometry,
            "formula_name": formula_name,
            "formula": formula,
            "physical_gpu_id": args.gpu_id,
            "backend": "gpu_exact_sector_matrix_free_state_action",
            "grid_preregistered_before_execution": True,
            "grid": list(EXTENDED_SHORT_GRID),
            "points": points,
            "effective_orders": orders,
            "qualification": qualification,
            "diagnosis": diagnosis,
            "points_at_or_below_noise_floor": floor_count,
            "minimum_error_over_noise_floor": float(min(errors) / base.FIT_NOISE_FLOOR),
            "cpu_gpu_first_point_relative_2_norm_difference": validation_difference,
            "original_result": {
                "path": str(source_path),
                "status": source["status"],
                "failure_reason": source.get("failure_reason"),
                "evaluated_windows": source["short_time_fit"]["evaluated_windows"],
            },
            "source_commit": source["git"]["commit"],
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        }
        base._atomic_json(
            args.output_dir / (geometry + "__" + formula_name + ".json"), payload
        )
    return 0


def fine_summary(
    point_dir: Path, vector_dir: Path, source_json: Path
) -> dict[str, Any]:
    source = load_json(source_json)
    result = source["models"]["three_term"]
    optimum = result["model_optimum"]
    points = [
        load_json(point_dir / (ratio_key(ratio) + ".json"))
        for ratio in FINE_RATIOS
    ]
    vectors = [
        np.load(vector_dir / (ratio_key(ratio) + ".npy"))
        for ratio in FINE_RATIOS
    ]
    for index, point in enumerate(points):
        point["adjacent_selected_vector_overlap_probability"] = (
            None
            if index == 0
            else float(abs(np.vdot(vectors[index - 1], vectors[index])) ** 2)
        )
    at_star = next(
        point
        for point in points
        if np.isclose(point["ratio_to_predicted_t_star"], 1.0)
    )
    finite = [point for point in points if point["direct_cost"] is not None]
    direct_minimum = min(finite, key=lambda point: float(point["direct_cost"]))
    minimum_index = points.index(direct_minimum)
    metrics = {
        "eta_star": float(
            abs(optimum["cost"] - at_star["direct_cost"])
            / at_star["direct_cost"]
        ),
        "eta_min": float(
            at_star["direct_cost"] / direct_minimum["direct_cost"] - 1.0
        ),
        "eta_t": float(
            abs(optimum["time"] / direct_minimum["time"] - 1.0)
        ),
        "maximum_residual_over_epsilon_on_fine_grid": max(
            point["residual_over_epsilon"] for point in points
        ),
        "minimum_ground_overlap_probability": min(
            point["ground_overlap_probability"] for point in points
        ),
        "minimum_adjacent_vector_overlap_probability": min(
            point["adjacent_selected_vector_overlap_probability"]
            for point in points[1:]
        ),
        "maximum_eigenpair_residual_2_norm": max(
            point["eigenpair_residual_2_norm"] for point in points
        ),
        "fine_grid_minimum_bracketed": 0 < minimum_index < len(points) - 1,
    }
    checks = {
        "eta_star": metrics["eta_star"] <= 0.01,
        "eta_min": metrics["eta_min"] <= 0.01,
        "eta_t": metrics["eta_t"] <= 0.05,
        "maximum_residual_over_epsilon": (
            metrics["maximum_residual_over_epsilon_on_fine_grid"] <= 0.05
        ),
        "fine_grid_minimum_bracketed": metrics["fine_grid_minimum_bracketed"],
    }
    return {
        "status": "complete",
        "diagnostic_kind": "post_hoc_fine_optimum_scan",
        "post_hoc": True,
        "source_model": result["model"],
        "source_model_optimum": optimum,
        "fine_ratios": list(FINE_RATIOS),
        "points": points,
        "direct_fine_grid_minimum": direct_minimum,
        "metrics": metrics,
        "checks": checks,
        "passed_post_hoc_diagnostic": all(checks.values()),
        "interpretation": (
            "coarse_validation_grid_explains_boundary_failure"
            if checks["eta_t"] and checks["eta_min"]
            else "boundary_discrepancy_persists_after_fine_scan"
        ),
    }


def command_aggregate(args: argparse.Namespace) -> int:
    fine = fine_summary(
        args.fine_point_dir, args.vector_dir, args.source_dir
        / "stretch150_raw" / "joint_refine_r0_s0046.json"
    )
    short_records = [
        load_json(args.short_dir / (geometry + "__" + formula + ".json"))
        for geometry, formula in SHORT_CONDITIONS
    ]
    short_summary = {
        "condition_count": len(short_records),
        "qualified_conditions": [
            {
                "geometry": record["geometry"],
                "formula_name": record["formula_name"],
                "selected_window": record["qualification"]["selected_window"],
            }
            for record in short_records
            if record["qualification"]["qualified"]
        ],
        "records": short_records,
    }
    payload = {
        "status": "complete",
        "created_at": now(),
        "scope": {
            "coefficient_reoptimization": False,
            "additional_molecules": False,
            "fine_scan_is_post_hoc": True,
            "short_grid_is_extended_diagnostic": True,
        },
        "fine_joint_stretch150": fine,
        "extended_short_time": short_summary,
        "conclusion": (
            "The original shared protocol remains formally inconclusive. The fine "
            "scan tests whether the joint candidate's sole boundary failure was a "
            "coarse-grid effect, while the extended short-time scans distinguish "
            "missing asymptotic windows from numerical-floor limitations."
        ),
    }
    base._atomic_json(args.output_dir / "summary.json", payload)

    lines = [
        "# Full-electron NH3 follow-up diagnostics",
        "",
        "These calculations are post-hoc diagnostics, not new hold-out tests.",
        "",
        "## joint_refine_r0_s0046 stretch150 fine scan",
        "",
        f"- predicted t*: {fine['source_model_optimum']['time']:.10g}",
        f"- fine-grid direct minimum t: {fine['direct_fine_grid_minimum']['time']:.10g}",
        f"- eta_star: {fine['metrics']['eta_star']:.6%}",
        f"- eta_min: {fine['metrics']['eta_min']:.6%}",
        f"- eta_t: {fine['metrics']['eta_t']:.6%}",
        f"- post-hoc pass: {fine['passed_post_hoc_diagnostic']}",
        f"- interpretation: {fine['interpretation']}",
        "",
        "## Extended short-time effective-order diagnostics",
        "",
        "| geometry | PF | qualified | diagnosis | min error / floor | first qualified window |",
        "|---|---|---:|---|---:|---|",
    ]
    for record in short_records:
        selected = record["qualification"]["selected_window"]
        window = (
            "n/a"
            if selected is None
            else f"{selected['t_start']:.5g}--{selected['t_stop']:.5g}"
        )
        lines.append(
            f"| {record['geometry']} | {record['formula_name']} | "
            f"{record['qualification']['qualified']} | {record['diagnosis']} | "
            f"{record['minimum_error_over_noise_floor']:.6g} | {window} |"
        )
    lines.extend(
        [
            "",
            "No PF coefficients were changed, and no additional molecule was run.",
            "A newly found window does not retroactively change the original protocol result.",
        ]
    )
    (args.output_dir / "report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)

    joint = sub.add_parser("joint-worker")
    joint.add_argument("--system-cache", type=Path, required=True)
    joint.add_argument("--source-json", type=Path, required=True)
    joint.add_argument("--ratios", required=True)
    joint.add_argument("--gpu-id", type=int, required=True)
    joint.add_argument("--output-dir", type=Path, required=True)
    joint.add_argument("--vector-dir", type=Path, required=True)

    short = sub.add_parser("short-worker")
    short.add_argument("--cache-dir", type=Path, required=True)
    short.add_argument("--source-dir", type=Path, required=True)
    short.add_argument("--conditions", required=True)
    short.add_argument("--gpu-id", type=int, required=True)
    short.add_argument("--output-dir", type=Path, required=True)

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--source-dir", type=Path, required=True)
    aggregate.add_argument("--fine-point-dir", type=Path, required=True)
    aggregate.add_argument("--vector-dir", type=Path, required=True)
    aggregate.add_argument("--short-dir", type=Path, required=True)
    aggregate.add_argument("--output-dir", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "joint-worker":
        args.ratios = tuple(float(value) for value in args.ratios.split(","))
        return command_joint_worker(args)
    if args.command == "short-worker":
        args.conditions = tuple(args.conditions.split(","))
        return command_short_worker(args)
    if args.command == "aggregate":
        return command_aggregate(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
