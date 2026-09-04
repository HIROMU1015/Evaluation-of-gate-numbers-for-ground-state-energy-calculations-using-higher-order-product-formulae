"""Validate fixed global-phase correction and Aer template reuse.

This is a deliberately small follow-up to ``benchmark_sparse_pf_smoke.py``.
It performs no PF eigensolve and never materializes a dense H8 PF unitary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import time
import traceback
from typing import Any, Sequence

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

from benchmark_sparse_pf_smoke import (
    GpuMemoryMonitor,
    LABEL,
    STATE_TOLERANCE,
    _atomic_json,
    _atomic_text,
    _build_cpu_unitary,
    _environment,
    _full_state,
    _git_commit,
    _gpu_info,
    _jsonable,
    _load_shared_h6,
    _now,
    _prepare_source,
    _warmup_aer,
)
from trotterlib.config import DECOMPO_NUM
from trotterlib.qiskit_time_evolution_grouping import (
    build_clique_hamiltonians,
    w_trotter_grouper_precomputed,
)
from trotterlib.qiskit_time_evolution_utils import (
    build_parameterized_aer_template,
    run_parameterized_aer_template,
)


def _check_gpu(physical_gpu_id: int) -> dict[str, Any]:
    visible = [
        value
        for value in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
        if value
    ]
    if visible != [str(physical_gpu_id)]:
        raise RuntimeError(
            f"Expected CUDA_VISIBLE_DEVICES={physical_gpu_id}, got {visible}"
        )
    info = _gpu_info(physical_gpu_id)
    if 2 * int(info["memory_used_mib"]) > int(info["memory_total_mib"]):
        raise RuntimeError("Assigned GPU no longer has at least half its memory free")
    return info


def _make_template(groups: Sequence[Any], num_qubits: int) -> tuple[Any, dict[str, Any]]:
    clique_started = time.perf_counter()
    cliques = build_clique_hamiltonians(groups, num_qubits, processes=1)
    clique_seconds = time.perf_counter() - clique_started

    circuit_started = time.perf_counter()
    parameter = Parameter("tau")
    body = QuantumCircuit(num_qubits)
    rotation_count = w_trotter_grouper_precomputed(
        body, cliques, parameter, num_qubits, LABEL
    )
    circuit_seconds = time.perf_counter() - circuit_started
    expected = int(DECOMPO_NUM[f"H{num_qubits // 2}"][LABEL])
    if int(rotation_count) != expected:
        raise RuntimeError(f"PF has {rotation_count} rotations, expected {expected}")

    template = build_parameterized_aer_template(
        body,
        parameter_name=parameter.name,
        device="GPU",
        optimization_level=0,
    )
    return template, {
        "clique_precompute_seconds": float(clique_seconds),
        "circuit_build_seconds": float(circuit_seconds),
        "input_circuit_instructions": int(len(body.data)),
        "pauli_rotations_per_application": int(rotation_count),
        "body_global_phase": _jsonable(body.global_phase),
        "transpiled_global_phase": _jsonable(template.circuit.global_phase),
        "template_profile": template.prepare_profile,
    }


def _phase_comparison(
    reference: np.ndarray, candidate: np.ndarray, fixed_phase: complex
) -> dict[str, Any]:
    raw_overlap = complex(np.vdot(reference, candidate))
    corrected = candidate / fixed_phase
    corrected_overlap = complex(np.vdot(reference, corrected))
    relative_difference = float(
        np.linalg.norm(corrected - reference) / np.linalg.norm(reference)
    )
    raw_unit_phase = raw_overlap / abs(raw_overlap)
    drift = float(np.angle(raw_unit_phase / fixed_phase))
    return {
        "raw_overlap": _jsonable(raw_overlap),
        "raw_overlap_phase_rad": float(np.angle(raw_overlap)),
        "fixed_correction_phase_rad": float(np.angle(fixed_phase)),
        "corrected_overlap": _jsonable(corrected_overlap),
        "corrected_overlap_phase_rad": float(np.angle(corrected_overlap)),
        "phase_drift_from_t0_rad": drift,
        "fixed_phase_corrected_relative_2_norm": relative_difference,
        "passes_1e-10": bool(relative_difference <= STATE_TOLERANCE),
    }


def _initial_payload(purpose: str, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "purpose": purpose,
        "status": "running",
        "started_at": _now(),
        "git_commit": _git_commit(),
        "configuration": {
            "label": LABEL,
            "t_ana": float(args.t_ana),
            "t_ana_source": args.t_ana_source,
            "physical_gpu_id": int(args.physical_gpu_id),
            "precision": "double",
            "iterative_pf_eigensolver_used": False,
        },
    }


def run_h6_phase(args: argparse.Namespace) -> int:
    payload = _initial_payload(
        "H6 fixed t=0 global-phase correction against dense sector PF", args
    )
    _atomic_json(args.output, payload)
    try:
        _check_gpu(args.physical_gpu_id)
        payload["environment"] = _environment(args.physical_gpu_id)
        with GpuMemoryMonitor(args.physical_gpu_id) as monitor:
            warmup_started = time.perf_counter()
            warmup_profile = _warmup_aer()
            warmup_seconds = time.perf_counter() - warmup_started

            measured_started = time.perf_counter()
            dense = _load_shared_h6(args.shared_input, dense=True)
            source = dense["source"]
            template, preparation = _make_template(
                source["groups"], int(source["num_qubits"])
            )
            fractions = (0.0, 0.5, 0.7)
            points: list[dict[str, Any]] = []
            phase0: complex | None = None
            for fraction in fractions:
                time_value = float(fraction * args.t_ana)
                unitary, dense_profile = _build_cpu_unitary(
                    dense["spectra"], time_value
                )
                dense_sector_state = unitary @ dense["sector_state"]
                dense_state = _full_state(
                    dense_sector_state,
                    dense["sector_indices"],
                    int(source["num_qubits"]),
                )
                evolved, run_profile = run_parameterized_aer_template(
                    template,
                    source["state"],
                    parameter_value=-time_value,
                    device="GPU",
                    target_gpus=(),
                )
                aer_state = np.asarray(evolved.data, dtype=np.complex128)
                raw_overlap = complex(np.vdot(dense_state, aer_state))
                if phase0 is None:
                    if abs(raw_overlap) == 0.0:
                        raise RuntimeError("The t=0 dense/Aer overlap is zero")
                    phase0 = raw_overlap / abs(raw_overlap)
                comparison = _phase_comparison(dense_state, aer_state, phase0)
                points.append(
                    {
                        "relative_time": float(fraction),
                        "time": time_value,
                        "dense_unitary_build_seconds": float(
                            dense_profile["seconds"]
                        ),
                        "aer_profile": run_profile,
                        "dense_state_norm": float(np.linalg.norm(dense_state)),
                        "aer_state_norm": float(np.linalg.norm(aer_state)),
                        "comparison": comparison,
                    }
                )
                del unitary, dense_sector_state, dense_state, aer_state, evolved

            assert phase0 is not None
            measured_seconds = time.perf_counter() - measured_started

        max_difference = max(
            point["comparison"]["fixed_phase_corrected_relative_2_norm"]
            for point in points
        )
        max_drift = max(
            abs(point["comparison"]["phase_drift_from_t0_rad"])
            for point in points
        )
        passed = bool(max_difference <= STATE_TOLERANCE)
        payload.update(
            {
                "status": "complete" if passed else "validation_failed",
                "system": {
                    "h_chain": 6,
                    "num_qubits": int(source["num_qubits"]),
                    "full_state_dimension": int(source["state"].size),
                    "sector": dense["sector"],
                    "ground_state_diagnostics": source.get(
                        "ground_state_diagnostics"
                    ),
                },
                "template": {
                    **preparation,
                    "build_and_transpile_count": 1,
                    "parameter_bind_run_count": len(points),
                    "same_parameterized_template_used_for_all_times": True,
                },
                "phase_correction": {
                    "source_time": 0.0,
                    "unit_complex_phase": _jsonable(phase0),
                    "phase_rad": float(np.angle(phase0)),
                    "application": "Aer state divided by the t=0 overlap phase",
                },
                "points": points,
                "validation": {
                    "tolerance": STATE_TOLERANCE,
                    "maximum_fixed_phase_corrected_relative_2_norm": max_difference,
                    "maximum_phase_drift_from_t0_rad": max_drift,
                    "time_independent_phase_supported": passed,
                },
                "timing_seconds": {
                    "warmup_separate": float(warmup_seconds),
                    "measured_total_excluding_warmup": float(measured_seconds),
                },
                "warmup_profile": warmup_profile,
                "gpu_memory": monitor.summary(),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                "completed_at": _now(),
            }
        )
        _atomic_json(args.output, payload)
        return 0 if passed else 1
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


def run_h8_reuse(args: argparse.Namespace) -> int:
    payload = _initial_payload(
        "H8 two-time Aer parameterized-template reuse timing", args
    )
    _atomic_json(args.output, payload)
    try:
        _check_gpu(args.physical_gpu_id)
        payload["environment"] = _environment(args.physical_gpu_id)
        with GpuMemoryMonitor(args.physical_gpu_id) as monitor:
            warmup_started = time.perf_counter()
            warmup_profile = _warmup_aer()
            warmup_seconds = time.perf_counter() - warmup_started

            measured_started = time.perf_counter()
            source, chemistry_seconds = _prepare_source(8)
            template, preparation = _make_template(
                source["groups"], int(source["num_qubits"])
            )
            points: list[dict[str, Any]] = []
            for run_index, fraction in enumerate((0.5, 0.7), start=1):
                time_value = float(fraction * args.t_ana)
                evolved, run_profile = run_parameterized_aer_template(
                    template,
                    source["state"],
                    parameter_value=-time_value,
                    device="GPU",
                    target_gpus=(),
                )
                state = np.asarray(evolved.data, dtype=np.complex128)
                overlap = complex(np.vdot(source["state"], state))
                points.append(
                    {
                        "run_index": run_index,
                        "relative_time": float(fraction),
                        "time": time_value,
                        "aer_profile": run_profile,
                        "state_norm": float(np.linalg.norm(state)),
                        "initial_state_overlap": _jsonable(overlap),
                        "survival_probability": float(abs(overlap) ** 2),
                    }
                )
                del evolved, state
            measured_seconds = time.perf_counter() - measured_started

        first_seconds = float(points[0]["aer_profile"]["simulator_run_seconds"])
        second_seconds = float(points[1]["aer_profile"]["simulator_run_seconds"])
        payload.update(
            {
                "status": "complete",
                "system": {
                    "h_chain": 8,
                    "num_qubits": int(source["num_qubits"]),
                    "full_state_dimension": int(source["state"].size),
                    "ground_state_diagnostics": source.get(
                        "ground_state_diagnostics"
                    ),
                },
                "template": {
                    **preparation,
                    "build_and_transpile_count": 1,
                    "parameter_bind_run_count": len(points),
                    "same_parameterized_template_used_for_all_times": True,
                },
                "points": points,
                "timing_seconds": {
                    "warmup_separate": float(warmup_seconds),
                    "chemistry_and_fci": float(chemistry_seconds),
                    "measured_total_excluding_warmup": float(measured_seconds),
                    "first_time_aer_run": first_seconds,
                    "second_time_aer_run": second_seconds,
                    "second_over_first": float(second_seconds / first_seconds),
                },
                "warmup_profile": warmup_profile,
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


def summarize(args: argparse.Namespace) -> int:
    h6 = json.loads(args.h6_json.read_text(encoding="utf-8"))
    h8 = json.loads(args.h8_json.read_text(encoding="utf-8"))
    h6_pass = bool(
        h6.get("status") == "complete"
        and h6.get("validation", {}).get("time_independent_phase_supported")
    )
    h8_pass = h8.get("status") == "complete"
    status = "complete" if h6_pass and h8_pass else "failed"
    summary = {
        "schema_version": 1,
        "status": status,
        "created_at": _now(),
        "git_commit": _git_commit(),
        "h6_global_phase": {
            "status": h6.get("status"),
            "phase_correction": h6.get("phase_correction"),
            "validation": h6.get("validation"),
            "points": [
                {
                    "relative_time": point["relative_time"],
                    "time": point["time"],
                    "aer_run_seconds": point["aer_profile"][
                        "simulator_run_seconds"
                    ],
                    "comparison": point["comparison"],
                }
                for point in h6.get("points", [])
            ],
        },
        "h8_template_reuse": {
            "status": h8.get("status"),
            "template": h8.get("template"),
            "timing_seconds": h8.get("timing_seconds"),
            "points": h8.get("points"),
            "gpu_memory": h8.get("gpu_memory"),
        },
        "raw_files": {
            "h6": str(args.h6_json),
            "h8": str(args.h8_json),
        },
    }
    _atomic_json(args.output_dir / "summary.json", summary)

    h6_rows = []
    for point in h6.get("points", []):
        comparison = point["comparison"]
        h6_rows.append(
            "| {relative_time:.2g} | {time:.12g} | {raw:.12g} | {corrected:.3e} | {drift:.3e} | {seconds:.6g} | {passed} |".format(
                relative_time=point["relative_time"],
                time=point["time"],
                raw=comparison["raw_overlap_phase_rad"],
                corrected=comparison["fixed_phase_corrected_relative_2_norm"],
                drift=comparison["phase_drift_from_t0_rad"],
                seconds=point["aer_profile"]["simulator_run_seconds"],
                passed="PASS" if comparison["passes_1e-10"] else "FAIL",
            )
        )
    h8_rows = []
    for point in h8.get("points", []):
        profile = point["aer_profile"]
        h8_rows.append(
            "| {run_index} | {relative_time:.2g} | {time:.12g} | {bind:.6g} | {run:.6g} | {total:.6g} | {norm:.12g} |".format(
                run_index=point["run_index"],
                relative_time=point["relative_time"],
                time=point["time"],
                bind=profile["bind_seconds"],
                run=profile["simulator_run_seconds"],
                total=profile["total_seconds"],
                norm=point["state_norm"],
            )
        )
    h6_memory = h6.get("gpu_memory", {})
    h8_memory = h8.get("gpu_memory", {})
    report = "\n".join(
        [
            "# GPU template phase and reuse validation",
            "",
            f"Status: **{status}**",
            "",
            "## H6 fixed t=0 global-phase correction",
            "",
            f"Correction phase: `{h6.get('phase_correction', {}).get('phase_rad')}` rad. The same parameterized template was built/transpiled once and bound at all three times.",
            "",
            "| t/t_ana | t | raw phase (rad) | corrected relative 2-norm | phase drift (rad) | Aer run (s) | result |",
            "|---:|---:|---:|---:|---:|---:|---|",
            *h6_rows,
            "",
            "## H8 parameterized-template reuse",
            "",
            "The H6 validated analytic time remains a runtime-only surrogate because no saved H8-specific t_ana exists. No dense H8 PF unitary was built.",
            "",
            "| run | t/t_ana | t | bind (s) | Aer run (s) | bind+run (s) | state norm |",
            "|---:|---:|---:|---:|---:|---:|---:|",
            *h8_rows,
            "",
            f"Template build/transpile count: `{h8.get('template', {}).get('build_and_transpile_count')}`; parameter-bind runs: `{h8.get('template', {}).get('parameter_bind_run_count')}`.",
            f"Warm-up was recorded separately (`{h8.get('timing_seconds', {}).get('warmup_separate')}` s) and is excluded from the measured total.",
            f"Device-wide sampled peaks were H6 `{h6_memory.get('peak_device_used_mib')} MiB` and H8 `{h8_memory.get('peak_device_used_mib')} MiB`. Per-process samples were unavailable, and unrelated jobs started while this run was active, so these are upper bounds rather than attributable benchmark memory.",
            "",
            "This validates state application and timing only; it is not a PF eigenphase or e_direct calculation.",
            "",
        ]
    )
    _atomic_text(args.output_dir / "report.md", report)
    marker = "COMPLETE" if status == "complete" else "FAILED"
    _atomic_text(
        args.output_dir / marker,
        f"status={status}\ncommit={_git_commit()}\n",
    )
    return 0 if status == "complete" else 1


def _worker_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--physical-gpu-id", type=int, required=True)
    parser.add_argument("--t-ana", type=float, required=True)
    parser.add_argument("--t-ana-source", required=True)
    parser.add_argument("--output", type=Path, required=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    h6 = subparsers.add_parser("h6-phase")
    _worker_arguments(h6)
    h6.add_argument("--shared-input", type=Path, required=True)
    h8 = subparsers.add_parser("h8-reuse")
    _worker_arguments(h8)
    report = subparsers.add_parser("summarize")
    report.add_argument("--h6-json", type=Path, required=True)
    report.add_argument("--h8-json", type=Path, required=True)
    report.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "h6-phase":
        status = run_h6_phase(args)
    elif args.command == "h8-reuse":
        status = run_h8_reuse(args)
    else:
        status = summarize(args)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
