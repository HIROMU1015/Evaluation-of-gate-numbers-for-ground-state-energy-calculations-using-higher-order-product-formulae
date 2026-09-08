"""Estimate fixed-m3 H10/H11 costs with calibrated GPU proxy diagnostics.

No dense product-formula unitary is constructed here.  The frozen m=3
coefficient sequence is applied to the full statevector through one reusable
Qiskit Aer template.  H2--H7 direct results calibrate an extrapolation which
is held out against H8/H9 before it is reported for H10/H11.
"""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from typing import Any, Sequence

import numpy as np

import run_gpu_m3_predictability_h7 as base
import run_m3_h8_h9 as fit_protocol
from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.qiskit_time_evolution_grouping import (
    tEvolution_vectors_grouper_optimized,
)


CANDIDATE = "m3_local_c1_r2_s007"
REGISTERED_COUNT_LABEL = "4th(new_3)"
FIT_GRID = tuple(float(value) for value in np.geomspace(0.06, 0.80, 15))
DIAGNOSTIC_RATIOS = (0.90, 1.00, 1.03, 1.10)
DIRECT_ROOT = Path(
    "artifacts/m3_m5_valid_cost_refinement_20260908_2225e35_retry1"
)
MINIMUM_FREE_GPU_MIB = 4096


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


def _gpu_rows(gpu_ids: Sequence[int]) -> list[dict[str, Any]]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.used,memory.free,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True, capture_output=True, check=True, timeout=90,
    )
    requested = {int(value) for value in gpu_ids}
    rows = []
    for line in completed.stdout.splitlines():
        fields = [item.strip() for item in line.split(",")]
        if len(fields) != 8 or int(fields[0]) not in requested:
            continue
        rows.append(
            {
                "physical_gpu_id": int(fields[0]), "name": fields[1],
                "uuid": fields[2], "driver_version": fields[3],
                "memory_used_mib": int(fields[4]),
                "memory_free_mib": int(fields[5]),
                "memory_total_mib": int(fields[6]),
                "utilization_percent": int(fields[7]),
            }
        )
    if {row["physical_gpu_id"] for row in rows} != requested:
        raise RuntimeError(f"Could not query every requested GPU: {gpu_ids}")
    return sorted(rows, key=lambda row: row["physical_gpu_id"])


def _environment(gpu_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    from trotterlib.qiskit_time_evolution_utils import available_aer_devices

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "qiskit": _package_version("qiskit"),
        "qiskit_aer": _package_version("qiskit-aer"),
        "qiskit_aer_gpu": _package_version("qiskit-aer-gpu"),
        "aer_devices": list(available_aer_devices()),
        "precision": os.environ.get("TROTTER_QISKIT_AER_PRECISION", "double"),
        "physical_gpus": list(gpu_rows),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }


def _overlap_point(
    state: np.ndarray,
    evolved: np.ndarray,
    energy: float,
    time_value: float,
    phase_correction: complex,
    alpha: float | None,
    rotations: int,
) -> dict[str, Any]:
    overlap = complex(np.vdot(state, evolved))
    corrected_overlap = overlap * phase_correction
    rotated = np.exp(-1j * energy * time_value) * corrected_overlap
    perturbative = abs(float(rotated.imag / time_value))
    overlap_error = abs(float(np.angle(rotated) / time_value))
    model_error = None if alpha is None else float(alpha * time_value**4)
    return {
        "time": float(time_value),
        "raw_overlap": overlap,
        "global_phase_corrected_overlap": corrected_overlap,
        "phase_rotated_overlap": rotated,
        "perturbative_proxy_error_hartree": perturbative,
        "overlap_phase_proxy_error_hartree": overlap_error,
        "model_error_hartree": model_error,
        "perturbative_to_model_ratio": (
            None if model_error is None else float(perturbative / model_error)
        ),
        "overlap_to_model_ratio": (
            None if model_error is None else float(overlap_error / model_error)
        ),
        "perturbative_proxy_cost": base._cost(time_value, perturbative, rotations),
        "overlap_phase_proxy_cost": base._cost(time_value, overlap_error, rotations),
        "survival_probability": float(abs(corrected_overlap) ** 2),
        "evolved_state_norm": float(np.linalg.norm(evolved)),
    }


def _run_grid(
    system: dict[str, Any],
    positive_times: Sequence[float],
    sequence: Sequence[float],
    gpu_ids: Sequence[int],
    *,
    alpha: float | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before = _gpu_rows(gpu_ids)
    too_full = [
        row for row in before if row["memory_free_mib"] < MINIMUM_FREE_GPU_MIB
    ]
    if too_full:
        raise RuntimeError(
            "Refusing to start on GPUs with less than "
            f"{MINIMUM_FREE_GPU_MIB} MiB free: {too_full}"
        )
    state = np.asarray(system["state"], dtype=np.complex128).reshape(-1)
    times_with_zero = [0.0, *[float(value) for value in positive_times]]
    logical_gpu_ids = tuple(range(len(gpu_ids)))
    started = time.perf_counter()
    monitors = [base.GpuMemoryMonitor(gpu_id) for gpu_id in gpu_ids]
    with contextlib.ExitStack() as stack:
        for monitor in monitors:
            stack.enter_context(monitor)
        results, profile = tEvolution_vectors_grouper_optimized(
            system["groups"],
            [-value for value in times_with_zero],
            int(system["num_qubits"]),
            state,
            REGISTERED_COUNT_LABEL,
            device="GPU",
            target_gpus=logical_gpu_ids,
            processes=len(logical_gpu_ids),
            optimization_level=0,
            s2_sequence=sequence,
        )
    total_seconds = time.perf_counter() - started
    zero_state = np.asarray(results[0][1].data, dtype=np.complex128)
    zero_overlap = complex(np.vdot(state, zero_state))
    if abs(zero_overlap) == 0.0:
        raise RuntimeError("The t=0 overlap is zero; global phase is undefined")
    phase_correction = np.exp(-1j * np.angle(zero_overlap))
    corrected_zero = zero_overlap * phase_correction
    rotations = int(DECOMPO_NUM[f"H{system['h_chain']}"][REGISTERED_COUNT_LABEL])
    if int(results[0][2]) != rotations:
        raise RuntimeError(
            f"Generated {results[0][2]} rotations, expected {rotations}"
        )
    points = []
    for time_value, result in zip(positive_times, results[1:], strict=True):
        points.append(
            _overlap_point(
                state, np.asarray(result[1].data),
                float(system["energy_without_constant"]), float(time_value),
                phase_correction, alpha, rotations,
            )
        )
    profile = dict(profile)
    profile.update(
        {
            "wall_clock_seconds": float(total_seconds),
            "physical_gpu_ids": [int(value) for value in gpu_ids],
            "gpu_state_before": before,
            "gpu_state_after": _gpu_rows(gpu_ids),
            "gpu_memory_samples": {
                str(gpu_id): monitor.summary(before[index]["memory_used_mib"])
                for index, (gpu_id, monitor) in enumerate(zip(gpu_ids, monitors))
            },
            "t_zero": {
                "raw_overlap": zero_overlap,
                "phase_correction_radians": float(np.angle(phase_correction)),
                "corrected_overlap": corrected_zero,
                "corrected_phase_radians": float(np.angle(corrected_zero)),
                "state_norm": float(np.linalg.norm(zero_state)),
            },
        }
    )
    return points, profile


def _fit(system: dict[str, Any], sequence: Sequence[float], gpu_ids: Sequence[int]):
    points, profile = _run_grid(
        system, FIT_GRID[:5], sequence, gpu_ids, alpha=None
    )
    fit = fit_protocol.qualify(
        [point["time"] for point in points],
        [point["perturbative_proxy_error_hartree"] for point in points],
    )
    profiles = [profile]
    if not fit["qualified"]:
        extra, extra_profile = _run_grid(
            system, FIT_GRID[5:], sequence, gpu_ids, alpha=None
        )
        points.extend(extra)
        profiles.append(extra_profile)
        fit = fit_protocol.qualify(
            [point["time"] for point in points],
            [point["perturbative_proxy_error_hartree"] for point in points],
        )
    return fit, points, profiles


def worker(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    record: dict[str, Any] = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "h_chain": int(args.h_chain), "candidate": CANDIDATE,
        "physical_gpu_ids": list(args.gpu_ids),
        "method": "Aer full-statevector matrix-free PF action; no PF unitary",
    }
    _atomic_json(output, record)
    try:
        gpu_rows = _gpu_rows(args.gpu_ids)
        record["environment"] = _environment(gpu_rows)
        if "GPU" not in record["environment"]["aer_devices"]:
            raise RuntimeError("Qiskit Aer does not report a GPU device")
        prepare_started = time.perf_counter()
        system = _prepare_system(int(args.h_chain))
        system["h_chain"] = int(args.h_chain)
        record["system_preparation_seconds"] = time.perf_counter() - prepare_started
        record["system"] = {
            "hamiltonian_name": system["ham_name"],
            "num_qubits": int(system["num_qubits"]),
            "state_dimension": int(np.asarray(system["state"]).size),
            "group_count": len(system["groups"]),
            "ground_energy_without_constant_hartree": float(
                system["energy_without_constant"]
            ),
            "ground_state_diagnostics": system["ground_state_diagnostics"],
        }
        candidate = base._candidate_records()[CANDIDATE]
        sequence = base._sequence(candidate["weights"])
        record["formula"] = {
            "weights": candidate["weights"], "s2_sequence": sequence,
            "s2_stage_count": len(sequence),
            "pauli_rotations_per_step": int(
                DECOMPO_NUM[f"H{args.h_chain}"][REGISTERED_COUNT_LABEL]
            ),
        }
        _atomic_json(output, record)

        fit, fit_points, fit_profiles = _fit(system, sequence, args.gpu_ids)
        record["short_time_fit"] = fit
        record["short_time_points"] = fit_points
        record["short_time_execution_profiles"] = fit_profiles
        if not fit["qualified"]:
            raise RuntimeError("Frozen short-time fit protocol did not qualify")
        alpha = float(fit["selected_window"]["fixed_order_alpha"])
        t_ana = float(base._analytic_time(alpha))
        rotations = int(record["formula"]["pauli_rotations_per_step"])
        record["alpha"] = alpha
        record["t_ana"] = t_ana
        record["analytic_model_cost"] = base._cost(
            t_ana, alpha * t_ana**4, rotations
        )
        _atomic_json(output, record)

        diagnostic_times = [ratio * t_ana for ratio in DIAGNOSTIC_RATIOS]
        points, profile = _run_grid(
            system, diagnostic_times, sequence, args.gpu_ids, alpha=alpha
        )
        for ratio, point in zip(DIAGNOSTIC_RATIOS, points, strict=True):
            point["relative_time"] = float(ratio)
        record["diagnostic_points"] = points
        record["diagnostic_execution_profile"] = profile
        record.update(status="complete", completed_at=_now())
        _atomic_json(output, record)
        print(
            f"H{args.h_chain} complete: alpha={alpha:.8e}, t_ana={t_ana:.8f}",
            flush=True,
        )
        return 0
    except Exception as exc:
        record.update(
            status="failed", completed_at=_now(),
            error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc(),
        )
        _atomic_json(output, record)
        traceback.print_exc()
        return 1


def _direct_calibration(root: Path) -> dict[str, Any]:
    records = []
    for h_chain in (2, 4, 5, 6, 7, 8, 9):
        path = root / f"H{h_chain}_m3.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        alpha = float(source["alpha"])
        t_ana = float(source["t_ana"])
        rotations = int(source["pauli_rotations_per_step"])
        model_cost = base._cost(t_ana, alpha * t_ana**4, rotations)
        result = source["result"]
        t_star = result["t_star"]
        at_t_ana = result["C_direct_at_t_ana"]
        records.append(
            {
                "h_chain": h_chain, "source": str(path),
                "t_star_over_t_ana": float(t_star["relative_time"]),
                "direct_minimum_to_model_cost_ratio": float(
                    t_star["direct_cost"] / model_cost
                ),
                "direct_at_t_ana_to_model_cost_ratio": float(
                    at_t_ana["direct_cost"] / model_cost
                ),
                "ground_overlap_probability_at_t_star": float(
                    t_star["ground_overlap_probability"]
                ),
                "eigenpair_residual_at_t_star": float(
                    t_star["eigenpair_residual_2_norm"]
                ),
            }
        )
    training = [item for item in records if item["h_chain"] <= 7]
    holdout = [item for item in records if item["h_chain"] >= 8]
    ratio_fields = (
        "t_star_over_t_ana", "direct_minimum_to_model_cost_ratio",
        "direct_at_t_ana_to_model_cost_ratio",
    )
    learned = {}
    for field in ratio_fields:
        values = np.asarray([item[field] for item in training], dtype=float)
        learned[field] = {
            "median": float(np.median(values)), "minimum": float(values.min()),
            "maximum": float(values.max()),
        }
    holdout_checks = []
    for item in holdout:
        t_prediction = learned["t_star_over_t_ana"]["median"]
        cost_prediction = learned["direct_minimum_to_model_cost_ratio"]["median"]
        t_error = abs(t_prediction - item["t_star_over_t_ana"])
        cost_error = abs(
            cost_prediction / item["direct_minimum_to_model_cost_ratio"] - 1.0
        )
        holdout_checks.append(
            {
                "h_chain": item["h_chain"],
                "absolute_t_star_ratio_error": float(t_error),
                "relative_minimum_cost_error": float(cost_error),
                "t_star_within_0_01_t_ana": bool(t_error <= 0.01 + 1e-12),
                "minimum_cost_within_2_percent": bool(cost_error <= 0.02),
                "passed": bool(t_error <= 0.01 + 1e-12 and cost_error <= 0.02),
            }
        )
    return {
        "training_systems": [2, 4, 5, 6, 7], "holdout_systems": [8, 9],
        "records": records, "learned_from_training_only": learned,
        "holdout_checks": holdout_checks,
        "passed": all(check["passed"] for check in holdout_checks),
        "scope": (
            "Calibrates a cost extrapolation, not a direct PF eigenvalue "
            "calculation for larger systems."
        ),
    }


def aggregate(
    output_dir: Path,
    direct_root: Path,
    h_chains: Sequence[int] = (10, 11),
) -> bool:
    calibration = _direct_calibration(direct_root)
    workers = []
    for h_chain in h_chains:
        path = output_dir / f"H{h_chain}_m3.json"
        workers.append(json.loads(path.read_text(encoding="utf-8")))
    complete = calibration["passed"] and all(
        record.get("status") == "complete" for record in workers
    )
    learned = calibration["learned_from_training_only"]
    factor = learned["direct_minimum_to_model_cost_ratio"]
    t_ratio = learned["t_star_over_t_ana"]
    estimates = []
    for record in workers:
        if record.get("status") != "complete":
            estimates.append(
                {"h_chain": record.get("h_chain"), "status": record.get("status")}
            )
            continue
        model_cost = float(record["analytic_model_cost"])
        points = {point["relative_time"]: point for point in record["diagnostic_points"]}
        estimates.append(
            {
                "h_chain": record["h_chain"], "status": "complete",
                "alpha": record["alpha"], "t_ana": record["t_ana"],
                "C_model": model_cost,
                "predicted_t_star_over_t_ana": t_ratio["median"],
                "predicted_t_star": t_ratio["median"] * float(record["t_ana"]),
                "C_extrapolated": model_cost * factor["median"],
                "C_extrapolated_training_envelope": [
                    model_cost * factor["minimum"], model_cost * factor["maximum"]
                ],
                "proxy_at_1_03_t_ana": points[1.03],
                "classification": (
                    "calibrated extrapolation with GPU proxy diagnostics"
                    if calibration["passed"]
                    else "uncalibrated proxy only"
                ),
                "not_direct_eigenvalue_error": True,
            }
        )
    system_label = "/".join(f"H{value}" for value in h_chains)
    payload = {
        "status": "complete" if complete else "incomplete",
        "created_at": _now(), "git": _git_state(),
        "systems": [int(value) for value in h_chains],
        "direct_calibration": calibration, "estimates": estimates,
    }
    if tuple(h_chains) == (10, 11):
        payload["h10_h11_estimates"] = estimates
    _atomic_json(output_dir / "summary.json", payload)
    lines = [
        f"# {system_label} fixed-m3 cost validation", "",
        f"{system_label} does not use dense PF unitaries. Values below distinguish the "
        "analytic model, the H2-H7-calibrated extrapolation, and GPU overlap "
        f"proxies; none is labelled as a direct {system_label} eigenvalue error.", "",
        f"H8/H9 hold-out calibration: **{'PASS' if calibration['passed'] else 'FAIL'}**", "",
        "| System | alpha | t_ana | C_model | C_extrapolated | e_pert/e_model at 1.03 | e_ov/e_model at 1.03 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in estimates:
        if item.get("status") != "complete":
            lines.append(f"| H{item['h_chain']} | failed | | | | | |")
            continue
        point = item["proxy_at_1_03_t_ana"]
        lines.append(
            f"| H{item['h_chain']} | {item['alpha']:.8e} | {item['t_ana']:.8f} "
            f"| {item['C_model']:.8e} | {item['C_extrapolated']:.8e} "
            f"| {point['perturbative_to_model_ratio']:.6f} "
            f"| {point['overlap_to_model_ratio']:.6f} |"
        )
    lines.extend(
        ["", "The extrapolated cost is conditional on H8/H9 hold-out transferability; "
         "the GPU proxies diagnose it but do not prove a PF eigenphase."]
    )
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if complete:
        (output_dir / "COMPLETE").write_text(_now() + "\n", encoding="utf-8")
    return complete


def launch(args: argparse.Namespace) -> int:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    launch_record = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "workers": {
            "H10": {"physical_gpu_ids": [0, 1, 2, 3]},
            "H11": {"physical_gpu_ids": [4, 5, 6, 7]},
        },
        "safety": "No other process is stopped; each worker checks free memory.",
    }
    _atomic_json(output_dir / "launch_state.json", launch_record)
    processes = []
    for h_chain, gpu_ids in ((10, (0, 1, 2, 3)), (11, (4, 5, 6, 7))):
        env = dict(os.environ)
        env.update(
            CUDA_VISIBLE_DEVICES=",".join(str(value) for value in gpu_ids),
            TROTTER_QISKIT_DEVICE="GPU",
            TROTTER_QISKIT_AER_METHOD="statevector",
            TROTTER_QISKIT_AER_PRECISION="double",
            TROTTER_POOL_PROCESSES=str(len(gpu_ids)),
            TROTTER_QISKIT_TARGET_GPUS=",".join(str(i) for i in range(len(gpu_ids))),
            OMP_NUM_THREADS="32", MKL_NUM_THREADS="32", OPENBLAS_NUM_THREADS="32",
        )
        command = [
            sys.executable, "-u", str(Path(__file__).resolve()), "worker",
            "--h-chain", str(h_chain), "--gpu-ids", *map(str, gpu_ids),
            "--output", str(output_dir / f"H{h_chain}_m3.json"),
        ]
        log = (output_dir / f"H{h_chain}_m3.log").open("x", encoding="utf-8")
        process = subprocess.Popen(
            command, cwd=Path(__file__).resolve().parents[1], env=env,
            stdout=log, stderr=subprocess.STDOUT, text=True,
        )
        processes.append((h_chain, process, log))
        print(f"H{h_chain} worker pid={process.pid}, GPUs={gpu_ids}", flush=True)
    exit_codes = {}
    for h_chain, process, log in processes:
        exit_codes[f"H{h_chain}"] = process.wait()
        log.close()
    complete = aggregate(output_dir, args.direct_root.resolve())
    launch_record.update(
        status="complete" if complete else "incomplete", completed_at=_now(),
        worker_exit_codes=exit_codes,
    )
    _atomic_json(output_dir / "launch_state.json", launch_record)
    return 0 if complete else 1


def launch_large_system(args: argparse.Namespace) -> int:
    """Run one H-chain and distribute independent time points over all GPUs."""
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    h_chain = int(args.h_chain)
    gpu_ids = tuple(range(8))
    launch_record = {
        "status": "running", "started_at": _now(), "git": _git_state(),
        "workers": {f"H{h_chain}": {"physical_gpu_ids": list(gpu_ids)}},
        "parallelism_note": (
            "At most one GPU process per independent time point; unused GPUs "
            "are not given duplicate work."
        ),
        "safety": "No other process is stopped; the worker checks free memory.",
    }
    _atomic_json(output_dir / "launch_state.json", launch_record)
    env = dict(os.environ)
    env.update(
        CUDA_VISIBLE_DEVICES=",".join(str(value) for value in gpu_ids),
        TROTTER_QISKIT_DEVICE="GPU",
        TROTTER_QISKIT_AER_METHOD="statevector",
        TROTTER_QISKIT_AER_PRECISION="double",
        TROTTER_POOL_PROCESSES=str(len(gpu_ids)),
        TROTTER_QISKIT_TARGET_GPUS=",".join(str(i) for i in range(len(gpu_ids))),
        OMP_NUM_THREADS="32", MKL_NUM_THREADS="32", OPENBLAS_NUM_THREADS="32",
    )
    command = [
        sys.executable, "-u", str(Path(__file__).resolve()), "worker",
        "--h-chain", str(h_chain), "--gpu-ids", *map(str, gpu_ids),
        "--output", str(output_dir / f"H{h_chain}_m3.json"),
    ]
    log_path = output_dir / f"H{h_chain}_m3.log"
    with log_path.open("x", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=Path(__file__).resolve().parents[1], env=env,
            stdout=log, stderr=subprocess.STDOUT, text=True,
        )
        launch_record["worker_pid"] = int(process.pid)
        _atomic_json(output_dir / "launch_state.json", launch_record)
        print(f"H{h_chain} worker pid={process.pid}, GPUs={gpu_ids}", flush=True)
        exit_code = process.wait()
    complete = exit_code == 0 and aggregate(
        output_dir, args.direct_root.resolve(), (h_chain,)
    )
    launch_record.update(
        status="complete" if complete else "incomplete", completed_at=_now(),
        worker_exit_codes={f"H{h_chain}": int(exit_code)},
    )
    _atomic_json(output_dir / "launch_state.json", launch_record)
    return 0 if complete else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--output-dir", type=Path, required=True)
    launch_parser.add_argument("--direct-root", type=Path, default=DIRECT_ROOT)
    h12_parser = subparsers.add_parser("launch-h12")
    h12_parser.add_argument("--output-dir", type=Path, required=True)
    h12_parser.add_argument("--direct-root", type=Path, default=DIRECT_ROOT)
    h12_parser.set_defaults(h_chain=12)
    h13_parser = subparsers.add_parser("launch-h13")
    h13_parser.add_argument("--output-dir", type=Path, required=True)
    h13_parser.add_argument("--direct-root", type=Path, default=DIRECT_ROOT)
    h13_parser.set_defaults(h_chain=13)
    h14_parser = subparsers.add_parser("launch-h14")
    h14_parser.add_argument("--output-dir", type=Path, required=True)
    h14_parser.add_argument("--direct-root", type=Path, default=DIRECT_ROOT)
    h14_parser.set_defaults(h_chain=14)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument(
        "--h-chain", type=int, choices=[10, 11, 12, 13, 14], required=True
    )
    worker_parser.add_argument("--gpu-ids", type=int, nargs="+", required=True)
    worker_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "launch":
        return launch(args)
    if args.mode in {"launch-h12", "launch-h13", "launch-h14"}:
        return launch_large_system(args)
    return worker(args)


if __name__ == "__main__":
    raise SystemExit(main())
