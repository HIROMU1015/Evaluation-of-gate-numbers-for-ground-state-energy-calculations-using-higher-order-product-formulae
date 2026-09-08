"""Exact H8/H9 m5 comparison using the frozen m=3 validation protocol."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pickle
import sys
import time
import traceback

import numpy as np

import run_gpu_m3_predictability_h7 as base
import run_m3_h8_h9 as m3_runner
from trotterlib.config import DECOMPO_NUM
from trotterlib.product_formula import _get_s2_sequence


LABEL = "4th(m5_best)"
WIDE_TIME_INTERPRETATION = (
    "Previously observed narrow cancellation point on a different, older "
    "t_model scale. It is excluded from the common nine-point comparison."
)


def _rotations(h_chain: int) -> int:
    return int(DECOMPO_NUM[f"H{h_chain}"][LABEL])


def _fit(system: dict) -> dict:
    state = np.asarray(system["state"], dtype=np.complex128)
    energy = float(system["energy"])
    sequence = _get_s2_sequence(LABEL)
    points = []
    fit = None
    started = time.perf_counter()
    for time_value in m3_runner.GRID:
        point_started = time.perf_counter()
        evolved = base._apply_pf_components(
            system["component_spectra"], sequence, float(time_value), state
        )
        overlap = complex(np.vdot(state, evolved))
        rotated = np.exp(-1j * energy * float(time_value)) * overlap
        error = abs(float(rotated.imag / float(time_value)))
        points.append(
            {
                "time": float(time_value),
                "perturbative_error_hartree": error,
                "phase_rotated_overlap": rotated,
                "survival_probability": float(abs(rotated) ** 2),
                "evolved_state_norm": float(np.linalg.norm(evolved)),
                "elapsed_seconds": float(time.perf_counter() - point_started),
            }
        )
        if len(points) >= 5:
            fit = m3_runner.qualify(
                [point["time"] for point in points],
                [point["perturbative_error_hartree"] for point in points],
            )
            if fit["qualified"]:
                break
    assert fit is not None
    fit["points"] = points
    fit["elapsed_seconds"] = float(time.perf_counter() - started)
    fit["error_definition"] = (
        "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
    )
    return fit


def _valid_minimum(points: list[dict]) -> dict:
    contiguous = []
    for point in points:
        if abs(float(point["direct_to_model_ratio"]) - 1.0) > 0.10:
            break
        contiguous.append(point)
    feasible = [point for point in contiguous if point["direct_cost"] is not None]
    if not feasible:
        return {
            "cost": None,
            "relative_time": None,
            "time": None,
            "num_contiguous_valid_points": len(contiguous),
        }
    minimum = min(feasible, key=lambda point: float(point["direct_cost"]))
    return {
        "cost": float(minimum["direct_cost"]),
        "relative_time": float(minimum["relative_time"]),
        "time": float(minimum["time"]),
        "num_contiguous_valid_points": len(contiguous),
        "definition": (
            "Minimum direct cost over the contiguous prefix satisfying "
            "abs(e_direct/e_model - 1) <= 0.10"
        ),
    }


def worker(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise RuntimeError(f"Refusing to overwrite {args.output}")
    payload = {
        "status": "running",
        "started_at": base._now(),
        "git": base._git_state(),
        "h_chain": int(args.h),
        "label": LABEL,
        "relative_times": list(base.RELATIVE_TIMES),
        "points": [],
    }
    base._atomic_json(args.output, payload)
    try:
        with args.system.open("rb") as handle:
            system = pickle.load(handle)
        if int(system["h_chain"]) != int(args.h):
            raise ValueError("system pickle and requested H-chain differ")

        sequence = _get_s2_sequence(LABEL)
        rotations = _rotations(args.h)
        fit = _fit(system)
        payload["short_time_fit"] = fit
        base._atomic_json(args.output, payload)
        if not fit["qualified"]:
            payload.update(status="fit_failed", completed_at=base._now())
            base._atomic_json(args.output, payload)
            return 2

        alpha = float(fit["selected_window"]["fixed_order_alpha"])
        analytic_time = base._analytic_time(alpha)
        model_cost = base._cost(
            analytic_time, alpha * analytic_time**4, rotations
        )
        payload.update(
            alpha=alpha,
            t_ana=analytic_time,
            analytic_model_cost=model_cost,
            pauli_rotations_per_step=rotations,
            s2_stage_count=len(sequence),
            unique_s2_stage_count=len(set(sequence)),
        )

        import cupy as cp

        cp.get_default_memory_pool().set_limit(size=6 * 2**30)
        gpu = base._gpu_info(args.gpu)
        payload["environment"] = base._environment(gpu)
        payload["memory_pool_limit_bytes"] = 6 * 2**30
        previous_vector = None
        previous_shift = None
        direct_started = time.perf_counter()
        with base.GpuMemoryMonitor(args.gpu) as monitor:
            for relative_time in base.RELATIVE_TIMES:
                free_bytes, _ = cp.cuda.runtime.memGetInfo()
                required_bytes = (3 if args.h == 8 else 7) * 2**30
                if free_bytes < required_bytes:
                    raise RuntimeError(
                        f"Insufficient free GPU memory: {free_bytes} < "
                        f"{required_bytes}; stopping without affecting other jobs"
                    )
                time_value = float(relative_time) * analytic_time
                print(
                    f"H{args.h} {LABEL} r={relative_time}: constructing",
                    flush=True,
                )
                unitary, build = base._build_pf_unitary_gpu(
                    system["component_spectra"], sequence, time_value
                )
                point, previous_vector, previous_shift = base._analyze_unitary(
                    unitary,
                    system["state"],
                    system["energy"],
                    time_value,
                    rotations,
                    alpha * time_value**4,
                    previous_vector,
                    previous_shift,
                )
                point["relative_time"] = float(relative_time)
                point["timing_seconds"].update(build)
                payload["points"].append(point)
                payload["gpu_memory"] = monitor.summary(gpu["memory_used_mib"])
                base._atomic_json(args.output, payload)
                print(
                    f"H{args.h} {LABEL} r={relative_time}: "
                    f"ratio={point['direct_to_model_ratio']:.6g}, "
                    f"residual={point['eigenpair_residual_2_norm']:.3e}",
                    flush=True,
                )
                del unitary
        payload["gpu_memory"] = monitor.summary(gpu["memory_used_mib"])
        payload["direct_sweep_seconds"] = float(
            time.perf_counter() - direct_started
        )
        summary = m3_runner.metrics(
            payload["points"], float(model_cost), fit["qualified"]
        )
        summary["validity_constrained_minimum_cost"] = _valid_minimum(
            payload["points"]
        )
        payload["summary"] = summary
        payload.update(
            status="complete",
            completed_at=base._now(),
            total_seconds=float(fit["elapsed_seconds"] + payload["direct_sweep_seconds"]),
        )
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


def _schedule_cost(record: dict) -> float:
    point = next(
        point for point in record["points"]
        if float(point["relative_time"]) == 1.0
    )
    return float(point["direct_cost"])


def _m3_valid_minimum(record: dict) -> dict:
    return _valid_minimum(record["points"])


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    return float(numerator / denominator)


def _wide_time_record(path: Path) -> dict:
    source = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": source["status"],
        "source": str(path),
        "source_git": source.get("git"),
        "old_scale_relative_time": source["configuration"]["relative_time"],
        "absolute_time": source["configuration"]["time"],
        "direct_error_hartree": source["direct"]["direct_error_hartree"],
        "direct_cost": source["direct"]["direct_cost"],
        "ground_state_overlap_probability": source["direct"][
            "selected_ground_state_overlap_probability"
        ],
        "eigenpair_residual_2_norm": source["direct"][
            "eigenpair_residual_2_norm"
        ],
        "included_in_common_nine_point_comparison": False,
        "interpretation": WIDE_TIME_INTERPRETATION,
    }


def aggregate(args: argparse.Namespace) -> int:
    records = {}
    for path in (args.h8, args.h9):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "complete":
            raise RuntimeError(f"Incomplete worker result: {path}")
        records[f"H{record['h_chain']}"] = record

    m3_payload = json.loads(args.m3_summary.read_text(encoding="utf-8"))
    comparisons = {}
    for h_name, m5 in records.items():
        h_chain = int(h_name[1:])
        m3 = next(
            record for record in m3_payload["results"]
            if int(record["h_chain"]) == h_chain
            and record["candidate"] == args.m3_candidate
        )
        m5_valid = m5["summary"]["validity_constrained_minimum_cost"]
        m3_valid = _m3_valid_minimum(m3)
        values = {
            "at_t_ana_direct_cost": {
                "m3": _schedule_cost(m3),
                "m5": _schedule_cost(m5),
            },
            "nine_point_grid_minimum_cost": {
                "m3": float(m3["summary"]["grid_minimum_cost"]["cost"]),
                "m5": float(m5["summary"]["grid_minimum_cost"]["cost"]),
            },
            "ten_percent_valid_range_minimum_cost": {
                "m3": m3_valid["cost"],
                "m5": m5_valid["cost"],
            },
        }
        for item in values.values():
            item["m3_over_m5"] = _ratio(item["m3"], item["m5"])
            item["m5_over_m3"] = _ratio(item["m5"], item["m3"])
        comparisons[h_name] = {
            "ratio_definition": "m3 cost-priority / m5; below 1 favors m3",
            "m3_candidate": args.m3_candidate,
            "values": values,
            "m3_validity_constrained_minimum": m3_valid,
            "m5_validity_constrained_minimum": m5_valid,
        }

    output = {
        "status": "complete",
        "created_at": base._now(),
        "git": base._git_state(),
        "protocol": {
            "label": LABEL,
            "short_time_grid": list(map(float, m3_runner.GRID)),
            "direct_relative_times": list(base.RELATIVE_TIMES),
            "fit_rule": {
                "window_size": 5,
                "noise_floor_hartree": 5e-13,
                "formal_order": 4,
                "free_order_tolerance": 0.2,
                "minimum_r2": 0.999,
                "select_earliest_eligible_window": True,
            },
        },
        "m5_results": records,
        "m3_comparisons": comparisons,
        "wide_time_sensitivity": {"H9": _wide_time_record(args.wide_time_point)},
    }
    # Keep the large per-point records in the worker JSONs, and use references
    # in the combined summary to avoid duplicating them.
    output["m5_results"] = {
        name: {
            "source": str(args.h8 if name == "H8" else args.h9),
            "alpha": record["alpha"],
            "t_ana": record["t_ana"],
            "analytic_model_cost": record["analytic_model_cost"],
            "short_time_fit": record["short_time_fit"],
            "summary": record["summary"],
            "total_seconds": record["total_seconds"],
            "gpu_memory": record["gpu_memory"],
        }
        for name, record in records.items()
    }
    base._atomic_json(args.output, output)
    _write_report(args.report, output)
    args.complete.write_text(base._now() + "\n", encoding="utf-8")
    return 0


def _write_report(path: Path, payload: dict) -> None:
    lines = [
        "# H8/H9 m5 same-protocol comparison",
        "",
        "The m5 short-time fits and nine-point direct sweeps use exactly the "
        "same declared protocol as the frozen m=3 validation.",
        "",
        "| System | alpha | t_ana | t_pass/t_ana | t_fail/t_ana | "
        "eta_schedule | eta_grid | eta_choice | grid min cost | C_valid^min |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("H8", "H9"):
        result = payload["m5_results"][name]
        summary = result["summary"]
        valid = summary["validity_constrained_minimum_cost"]
        ten = summary["ten_percent_validity"]
        lines.append(
            f"| {name} | {result['alpha']:.7e} | {result['t_ana']:.6f} | "
            f"{ten['t_pass_over_t_ana']} | {ten['t_fail_over_t_ana']} | "
            f"{summary['eta_schedule']:.3%} | {summary['eta_grid']:.3%} | "
            f"{summary['eta_choice']:.3%} | "
            f"{summary['grid_minimum_cost']['cost']:.7e} | "
            f"{valid['cost']:.7e} |"
        )
    lines += [
        "",
        "## Cost-priority m=3 / m5 ratios",
        "",
        "Ratios below one favor the m=3 candidate.",
        "",
        "| System | direct cost at each t_ana | nine-point grid minimum | "
        "10% valid-range minimum |",
        "|---|---:|---:|---:|",
    ]
    for name in ("H8", "H9"):
        values = payload["m3_comparisons"][name]["values"]
        lines.append(
            f"| {name} | "
            f"{values['at_t_ana_direct_cost']['m3_over_m5']:.6f} | "
            f"{values['nine_point_grid_minimum_cost']['m3_over_m5']:.6f} | "
            f"{values['ten_percent_valid_range_minimum_cost']['m3_over_m5']:.6f} |"
        )
    wide = payload["wide_time_sensitivity"]["H9"]
    lines += [
        "",
        "## Separate H9 wide-time sensitivity",
        "",
        f"The previously known narrow cancellation point was at old-scale "
        f"factor {wide['old_scale_relative_time']} (absolute "
        f"t={wide['absolute_time']:.6f}), with direct cost "
        f"{wide['direct_cost']:.7e}. It is not included in the common "
        "nine-point comparison.",
        "",
        "No optimum refinement or H10 computation was performed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument("--h", type=int, choices=[8, 9], required=True)
    worker_parser.add_argument("--gpu", type=int, required=True)
    worker_parser.add_argument("--system", type=Path, required=True)
    worker_parser.add_argument("--output", type=Path, required=True)
    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--h8", type=Path, required=True)
    aggregate_parser.add_argument("--h9", type=Path, required=True)
    aggregate_parser.add_argument("--m3-summary", type=Path, required=True)
    aggregate_parser.add_argument(
        "--m3-candidate", default="m3_local_c1_r2_s007"
    )
    aggregate_parser.add_argument("--wide-time-point", type=Path, required=True)
    aggregate_parser.add_argument("--output", type=Path, required=True)
    aggregate_parser.add_argument("--report", type=Path, required=True)
    aggregate_parser.add_argument("--complete", type=Path, required=True)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    if arguments.mode == "worker":
        sys.exit(worker(arguments))
    sys.exit(aggregate(arguments))
