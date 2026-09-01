"""Plan and summarize H9--H11 GPU overlap-phase cost validation.

The module consumes GPU statevector sweeps from the existing H-chain runner.
It never diagonalizes a product-formula unitary.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
from typing import Any, Sequence

import numpy as np

from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.cost_validation import analytic_optimal_time
from trotterlib.fit_window import rolling_loglog_fits, select_best_rolling_fit


CHAINS = (9, 10, 11)
M5_LABEL = "4th(m5_best)"
Y8_LABEL = "8th(Morales-Y8m10b)"
LABELS = (M5_LABEL, Y8_LABEL)
SLUGS = {M5_LABEL: "m5", Y8_LABEL: "y8"}
PILOT_RUN_NAMES = {
    M5_LABEL: "h9_h11_m5_pilot",
    Y8_LABEL: "h9_h11_y8_pilot",
}
REFINE_RUN_NAMES = {
    M5_LABEL: "h9_h11_m5_tana",
    Y8_LABEL: "h9_h11_y8_tana",
}
SCHEDULE_FACTORS = (0.5, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5)


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _result_path(
    output_dir: Path, h_chain: int, label: str, *, refine: bool
) -> Path:
    names = REFINE_RUN_NAMES if refine else PILOT_RUN_NAMES
    return output_dir / f"H{h_chain}_{names[label]}.json"


def _load_single_sweep(
    path: Path, *, h_chain: int, label: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload["system"]["h_chain"]) != h_chain:
        raise ValueError(f"{path} is not H{h_chain}")
    calculation = payload["calculation"]
    if calculation["simulator_device"] != "GPU":
        raise ValueError(f"{path} was not calculated on GPU")
    if calculation["aer_precision"] != "double":
        raise ValueError(f"{path} was not calculated in double precision")
    matches = [item for item in payload["results"] if item["label"] == label]
    if len(matches) != 1:
        raise ValueError(f"{path}: expected one result for {label}")
    result = matches[0]
    size = len(calculation["times"])
    for field in (
        "errors_hartree",
        "overlap_phase_errors_hartree",
        "ground_state_survival_probabilities",
        "phase_rotated_overlaps",
    ):
        if len(result[field]) != size:
            raise ValueError(f"{path}: {field} has the wrong length")
    return payload, result


def _fit_pilot(
    payload: dict[str, Any],
    result: dict[str, Any],
    *,
    noise_floor: float,
    window_sizes: Sequence[int],
) -> dict[str, Any]:
    times = np.asarray(payload["calculation"]["times"], dtype=float)
    errors = np.asarray(result["errors_hartree"], dtype=float)
    order = int(result["formal_order"])
    windows: list[dict[str, Any]] = []
    for size in window_sizes:
        if 2 <= size <= times.size:
            windows.extend(
                {**window, "window_size": int(size)}
                for window in rolling_loglog_fits(
                    times,
                    errors,
                    formal_order=order,
                    noise_floor=noise_floor,
                    window_size=size,
                )
            )
    best = select_best_rolling_fit(windows)
    if best is None:
        raise RuntimeError(
            f"no rolling fit remains above {noise_floor:.3e} Hartree"
        )
    stable = [
        window
        for window in windows
        if float(window["order_deviation"])
        <= max(0.25, float(best["order_deviation"]) + 0.05)
        and float(window["r2"]) >= 0.99
    ] or [best]
    alphas = np.asarray(
        [float(window["fixed_order_alpha"]) for window in stable]
    )
    return {
        "noise_floor_hartree": float(noise_floor),
        "selected_window": best,
        "candidate_windows": windows,
        "stable_candidate_count": len(stable),
        "fixed_order_alpha_sensitivity": {
            "minimum": float(np.min(alphas)),
            "maximum": float(np.max(alphas)),
            "median": float(np.median(alphas)),
            "max_to_min_ratio": float(np.max(alphas) / np.min(alphas)),
        },
        "runner_full_grid_fixed_order_alpha": float(
            result["fixed_order_alpha"]
        ),
        "runner_full_grid_free_fit": result["free_fit"],
    }


def plan(
    output_dir: Path,
    *,
    schedule_path: Path,
    noise_floor: float,
    window_sizes: Sequence[int],
    epsilon_e: float,
    max_time: float,
) -> dict[str, Any]:
    tasks: dict[str, Any] = {}
    for h_chain in CHAINS:
        tasks[f"H{h_chain}"] = {}
        for label in LABELS:
            source = _result_path(output_dir, h_chain, label, refine=False)
            payload, result = _load_single_sweep(
                source, h_chain=h_chain, label=label
            )
            task: dict[str, Any] = {
                "label": label,
                "slug": SLUGS[label],
                "source_pilot": str(source),
                "formal_order": int(result["formal_order"]),
                "pauli_rotations_per_step": int(
                    result["pauli_rotations_per_step"]
                ),
            }
            try:
                fit = _fit_pilot(
                    payload,
                    result,
                    noise_floor=noise_floor,
                    window_sizes=window_sizes,
                )
                alpha = float(fit["selected_window"]["fixed_order_alpha"])
                t_ana = analytic_optimal_time(
                    alpha, int(result["formal_order"]), epsilon_e
                )
                times = [factor * t_ana for factor in SCHEDULE_FACTORS]
                schedulable = (
                    math.isfinite(t_ana)
                    and t_ana > 0
                    and times[-1] <= max_time
                )
                task.update(
                    {
                        "status": (
                            "scheduled"
                            if schedulable
                            else "skipped_extreme_time"
                        ),
                        "fit": fit,
                        "alpha": float(alpha),
                        "t_ana": float(t_ana),
                        "schedule_factors": list(SCHEDULE_FACTORS),
                        "times": [float(value) for value in times],
                        "max_allowed_time": float(max_time),
                    }
                )
            except Exception as exc:
                task.update(
                    {
                        "status": "fit_failed",
                        "error": {
                            "type": type(exc).__name__,
                            "message": str(exc),
                        },
                    }
                )
            tasks[f"H{h_chain}"][label] = task
    payload = {
        "schema_version": 1,
        "purpose": "H9-H11 overlap-phase analytic-time GPU schedule",
        "created_at": _now(),
        "epsilon_E_hartree": float(epsilon_e),
        "requested_noise_floor_hartree": float(noise_floor),
        "window_sizes": [int(value) for value in window_sizes],
        "tasks": tasks,
    }
    _atomic_json(schedule_path, payload)
    print(f"saved: {schedule_path}", flush=True)
    return payload


def emit_times(
    schedule_path: Path, *, h_chain: int, label: str
) -> None:
    task = json.loads(schedule_path.read_text(encoding="utf-8"))[
        "tasks"
    ][f"H{h_chain}"][label]
    if task["status"] != "scheduled":
        raise RuntimeError(
            f"H{h_chain} {label} is not scheduled: {task['status']}"
        )
    print(" ".join(format(float(value), ".17g") for value in task["times"]))


def _cost(
    time_value: float,
    error: float,
    *,
    beta: float,
    n_rotation: int,
    epsilon_e: float,
) -> float | None:
    if not math.isfinite(error) or error < 0 or error >= epsilon_e:
        return None
    return float(
        beta
        * n_rotation
        / (time_value * (epsilon_e - error))
    )


def _task_timing(output_dir: Path, task_id: str) -> dict[str, Any] | None:
    path = output_dir / "timings" / f"{task_id}.tsv"
    if not path.exists():
        return None
    fields = path.read_text(encoding="utf-8").strip().split("\t")
    if len(fields) != 3:
        return {"source": str(path), "parse_error": True}
    started, finished, status = fields
    return {
        "source": str(path),
        "started_epoch": float(started),
        "finished_epoch": float(finished),
        "elapsed_seconds": float(finished) - float(started),
        "exit_status": int(status),
    }


def _gpu_memory_summary(
    output_dir: Path, task_id: str
) -> dict[str, Any]:
    by_gpu: dict[str, Any] = {}
    for path in sorted((output_dir / "memory").glob(f"{task_id}_gpu*.csv")):
        rows: list[tuple[int, int, int, int]] = []
        with path.open(encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if len(row) < 4:
                    continue
                try:
                    rows.append(tuple(int(value.strip()) for value in row[:4]))
                except ValueError:
                    continue
        label = path.stem.rsplit("_gpu", 1)[-1]
        by_gpu[label] = {
            "physical_gpu_id": rows[0][0] if rows else int(label),
            "samples": len(rows),
            "peak_used_mib": max(row[1] for row in rows) if rows else None,
            "memory_total_mib": max(row[2] for row in rows) if rows else None,
            "maximum_utilization_percent": (
                max(row[3] for row in rows) if rows else None
            ),
            "source": str(path),
        }
    peaks = [
        int(item["peak_used_mib"])
        for item in by_gpu.values()
        if item["peak_used_mib"] is not None
    ]
    return {
        "by_physical_gpu": by_gpu,
        "maximum_peak_used_mib": max(peaks) if peaks else None,
    }


def _nearest_index(times: np.ndarray, target: float) -> int:
    index = int(np.argmin(np.abs(times - target)))
    if not np.isclose(times[index], target, rtol=1e-12, atol=1e-13):
        raise RuntimeError(f"t_ana={target:.17g} is absent from the grid")
    return index


def _environment() -> dict[str, Any]:
    packages = {}
    for name in (
        "numpy",
        "scipy",
        "qiskit",
        "qiskit-aer",
        "qiskit-aer-gpu",
        "pyscf",
        "openfermion",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    try:
        gpu_query = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,uuid,driver_version,memory.total",
                "--format=csv,noheader",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
        gpu_inventory = gpu_query.stdout.strip().splitlines()
        gpu_query_error = None
    except Exception as exc:
        gpu_inventory = []
        gpu_query_error = f"{type(exc).__name__}: {exc}"
    return {
        "timestamp": _now(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
        "nvidia_smi_gpu_inventory": gpu_inventory,
        "nvidia_smi_query_error": gpu_query_error,
    }


def finalize(
    output_dir: Path,
    *,
    schedule_path: Path,
    summary_path: Path,
    readme_path: Path,
    complete_path: Path,
    beta: float,
    epsilon_e: float,
) -> dict[str, Any]:
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    warnings: list[str] = []
    failed = False
    for h_chain in CHAINS:
        results[f"H{h_chain}"] = {}
        for label in LABELS:
            slug = SLUGS[label]
            planned = schedule["tasks"][f"H{h_chain}"][label]
            if planned["status"] != "scheduled":
                results[f"H{h_chain}"][label] = {
                    "status": planned["status"],
                    "plan": planned,
                }
                warnings.append(f"H{h_chain} {label}: {planned['status']}")
                continue
            pilot_path = _result_path(
                output_dir, h_chain, label, refine=False
            )
            refine_path = _result_path(
                output_dir, h_chain, label, refine=True
            )
            if not refine_path.exists():
                failed = True
                results[f"H{h_chain}"][label] = {
                    "status": "missing_refinement",
                    "source_pilot": str(pilot_path),
                    "source_refinement": str(refine_path),
                }
                continue
            pilot_payload, pilot_result = _load_single_sweep(
                pilot_path, h_chain=h_chain, label=label
            )
            refine_payload, refine_result = _load_single_sweep(
                refine_path, h_chain=h_chain, label=label
            )
            times = np.asarray(
                refine_payload["calculation"]["times"], dtype=float
            )
            perturbative = np.asarray(
                refine_result["errors_hartree"], dtype=float
            )
            overlap_phase = np.asarray(
                refine_result["overlap_phase_errors_hartree"], dtype=float
            )
            survival = np.asarray(
                refine_result["ground_state_survival_probabilities"],
                dtype=float,
            )
            alpha = float(planned["alpha"])
            order = int(planned["formal_order"])
            t_ana = float(planned["t_ana"])
            n_rotation = int(planned["pauli_rotations_per_step"])
            index = _nearest_index(times, t_ana)
            model_errors = alpha * times**order
            model_error = float(model_errors[index])
            e_pert = float(perturbative[index])
            e_ov = float(overlap_phase[index])
            c_model = _cost(
                t_ana,
                model_error,
                beta=beta,
                n_rotation=n_rotation,
                epsilon_e=epsilon_e,
            )
            c_pert = _cost(
                t_ana,
                e_pert,
                beta=beta,
                n_rotation=n_rotation,
                epsilon_e=epsilon_e,
            )
            c_ov = _cost(
                t_ana,
                e_ov,
                beta=beta,
                n_rotation=n_rotation,
                epsilon_e=epsilon_e,
            )
            ov_model_ratio = overlap_phase / model_errors
            angles = np.asarray(
                [
                    np.angle(complex(float(item["real"]), float(item["imag"])))
                    for item in refine_result["phase_rotated_overlaps"]
                ]
            )
            task_id = f"H{h_chain}_{slug}_refine"
            pilot_memory = _gpu_memory_summary(
                output_dir, f"H{h_chain}_{slug}_pilot"
            )
            refinement_memory = _gpu_memory_summary(output_dir, task_id)
            memory_peaks = [
                int(value)
                for value in (
                    pilot_memory["maximum_peak_used_mib"],
                    refinement_memory["maximum_peak_used_mib"],
                )
                if value is not None
            ]
            result = {
                "status": "complete",
                "formal_order": order,
                "pauli_rotations_per_step": n_rotation,
                "pilot_fit": planned["fit"],
                "fixed_order_alpha": alpha,
                "pilot_free_fit": pilot_result["free_fit"],
                "t_ana": t_ana,
                "e_model_t_ana_hartree": model_error,
                "e_pert_t_ana_hartree": e_pert,
                "e_ov_t_ana_hartree": e_ov,
                "C_model_t_ana": c_model,
                "C_pert_t_ana": c_pert,
                "C_ov_t_ana": c_ov,
                "C_ov_over_C_model": (
                    None
                    if c_ov is None or c_model is None
                    else float(c_ov / c_model)
                ),
                "ground_state_survival_probability_t_ana": float(
                    survival[index]
                ),
                "minimum_ground_state_survival_probability": float(
                    np.min(survival)
                ),
                "local_schedule": {
                    "times": times.tolist(),
                    "e_model_hartree": model_errors.tolist(),
                    "e_pert_hartree": perturbative.tolist(),
                    "e_ov_hartree": overlap_phase.tolist(),
                    "ground_state_survival_probabilities": survival.tolist(),
                    "e_ov_over_alpha_t_to_p": ov_model_ratio.tolist(),
                    "e_ov_over_alpha_t_to_p_variation": {
                        "minimum": float(np.min(ov_model_ratio)),
                        "maximum": float(np.max(ov_model_ratio)),
                        "median": float(np.median(ov_model_ratio)),
                        "max_to_min_ratio": float(
                            np.max(ov_model_ratio) / np.min(ov_model_ratio)
                        ),
                        "relative_span_about_median": float(
                            (np.max(ov_model_ratio) - np.min(ov_model_ratio))
                            / np.median(ov_model_ratio)
                        ),
                    },
                    "phase_rotated_overlap_angles": angles.tolist(),
                    "minimum_principal_phase_branch_margin": float(
                        np.pi - np.max(np.abs(angles))
                    ),
                },
                "runtime": {
                    "pilot_result_elapsed_seconds": float(
                        pilot_result["elapsed_seconds"]
                    ),
                    "refinement_result_elapsed_seconds": float(
                        refine_result["elapsed_seconds"]
                    ),
                    "pilot_task": _task_timing(
                        output_dir, f"H{h_chain}_{slug}_pilot"
                    ),
                    "refinement_task": _task_timing(output_dir, task_id),
                    "refinement_execution_profile": refine_result[
                        "execution_profile"
                    ],
                },
                "gpu_memory": {
                    "pilot": pilot_memory,
                    "refinement": refinement_memory,
                    "maximum_peak_used_mib": (
                        max(memory_peaks) if memory_peaks else None
                    ),
                },
                "simulator_device": refine_payload["calculation"][
                    "simulator_device"
                ],
                "aer_precision": refine_payload["calculation"][
                    "aer_precision"
                ],
                "source_pilot": str(pilot_path),
                "source_refinement": str(refine_path),
                "overlap_phase_cost_interpretation": (
                    "proxy based on the ground-state overlap phase; not a "
                    "direct PF eigenvalue error"
                ),
            }
            results[f"H{h_chain}"][label] = result
            if c_ov is None:
                warnings.append(
                    f"H{h_chain} {label}: C_ov invalid because "
                    "e_ov(t_ana) >= epsilon_E"
                )

    status = (
        "failed_or_partial"
        if failed
        else ("complete_with_documented_skips" if warnings else "complete")
    )
    payload = {
        "schema_version": 1,
        "purpose": (
            "H9-H11 system-size dependence of the overlap-phase proxy cost "
            "relative to the short-time power-law model"
        ),
        "status": status,
        "created_at": _now(),
        "environment": _environment(),
        "cost_model": {
            "formula": "BETA*N_rotation/[t*(epsilon_E-e(t))]",
            "BETA": float(beta),
            "epsilon_E_hartree": float(epsilon_e),
            "invalid_when": "e(t) >= epsilon_E",
        },
        "system_convention": {
            "H9": "H9+, triplet, STO-3G, 18 qubits",
            "H10": "neutral H10, singlet, STO-3G, 20 qubits",
            "H11": "H11+, triplet, STO-3G, 22 qubits",
        },
        "schedule_source": str(schedule_path),
        "results": results,
        "warnings": warnings,
        "direct_pf_unitary_diagonalization_used": False,
        "C_ov_is_exact_pf_eigenvalue_cost": False,
    }
    _atomic_json(summary_path, payload)

    lines = [
        "# H9--H11 GPU overlap-phase cost validation",
        "",
        f"Status: {status}",
        "",
        "| System | PF | alpha | t_ana | e_pert | e_ov | C_ov/C_model | survival | peak GPU MiB |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for h_chain in CHAINS:
        for label in LABELS:
            item = results[f"H{h_chain}"][label]
            if item["status"] != "complete":
                lines.append(
                    f"| H{h_chain} | {label} | - | - | - | - | "
                    f"{item['status']} | - | - |"
                )
                continue
            ratio = item["C_ov_over_C_model"]
            peak = item["gpu_memory"]["maximum_peak_used_mib"]
            ratio_text = "-" if ratio is None else f"{ratio:.6g}"
            peak_text = "-" if peak is None else str(peak)
            lines.append(
                f"| H{h_chain} | {label} | "
                f"{item['fixed_order_alpha']:.6e} | "
                f"{item['t_ana']:.6g} | "
                f"{item['e_pert_t_ana_hartree']:.6e} | "
                f"{item['e_ov_t_ana_hartree']:.6e} | "
                f"{ratio_text} | "
                f"{item['ground_state_survival_probability_t_ana']:.9f} | "
                f"{peak_text} |"
            )
    lines.extend(
        [
            "",
            "C_ov is an overlap-phase proxy, not a direct PF eigenvalue cost.",
            "No direct PF-unitary diagonalization was performed.",
            "",
        ]
    )
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    if failed:
        raise RuntimeError("refusing to create COMPLETE: results are missing")
    complete_path.write_text(
        f"{status} {_now()}\nsummary={summary_path}\n",
        encoding="utf-8",
    )
    print(f"saved: {summary_path}", flush=True)
    print(f"saved: {readme_path}", flush=True)
    print(f"saved: {complete_path}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--output-dir", type=Path, required=True)
    plan_parser.add_argument("--schedule", type=Path, required=True)
    plan_parser.add_argument("--noise-floor", type=float, default=5e-12)
    plan_parser.add_argument(
        "--window-sizes", nargs="+", type=int, default=[4, 5, 6]
    )
    plan_parser.add_argument("--epsilon-e", type=float, default=TARGET_ERROR)
    plan_parser.add_argument("--max-time", type=float, default=10.0)
    emit_parser = subparsers.add_parser("emit-times")
    emit_parser.add_argument("--schedule", type=Path, required=True)
    emit_parser.add_argument("--h-chain", type=int, choices=CHAINS, required=True)
    emit_parser.add_argument("--label", choices=LABELS, required=True)
    final_parser = subparsers.add_parser("finalize")
    final_parser.add_argument("--output-dir", type=Path, required=True)
    final_parser.add_argument("--schedule", type=Path, required=True)
    final_parser.add_argument("--summary", type=Path, required=True)
    final_parser.add_argument("--readme", type=Path, required=True)
    final_parser.add_argument("--complete", type=Path, required=True)
    final_parser.add_argument("--beta", type=float, default=BETA)
    final_parser.add_argument("--epsilon-e", type=float, default=TARGET_ERROR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "plan":
        plan(
            args.output_dir,
            schedule_path=args.schedule,
            noise_floor=args.noise_floor,
            window_sizes=args.window_sizes,
            epsilon_e=args.epsilon_e,
            max_time=args.max_time,
        )
    elif args.command == "emit-times":
        emit_times(
            args.schedule, h_chain=args.h_chain, label=args.label
        )
    elif args.command == "finalize":
        finalize(
            args.output_dir,
            schedule_path=args.schedule,
            summary_path=args.summary,
            readme_path=args.readme,
            complete_path=args.complete,
            beta=args.beta,
            epsilon_e=args.epsilon_e,
        )


if __name__ == "__main__":
    main()
