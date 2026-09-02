"""Calibrate and apply the time-independent Aer/transpile global phase.

The calibration path evaluates the same parameterized PF template at t=0.
The analysis path applies only that measured unit-modulus correction to raw
overlaps already stored by ``run_morales_y8m10b_hchain.py``.  Uncorrected
overlap-phase costs are retained for diagnostics but are never used as a
physical cost estimate.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import time
from typing import Any

import numpy as np

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.qiskit_time_evolution_grouping import (
    tEvolution_vectors_grouper_optimized,
)
from trotterlib.qiskit_time_evolution_utils import available_aer_devices


LABELS = {
    "m5": "4th(m5_best)",
    "y8": "8th(Morales-Y8m10b)",
}
RUN_NAMES = {
    "m5": "h9_h11_m5_tana",
    "y8": "h9_h11_y8_tana",
}
CALIBRATION_CHAINS = (2, 4, 5, 6, 7, 9, 10, 11)
ANALYSIS_CHAINS = (9, 10, 11)


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _complex_payload(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _as_complex(value: dict[str, Any]) -> complex:
    return complex(float(value["real"]), float(value["imag"]))


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return None


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in ("numpy", "qiskit", "qiskit-aer", "qiskit-aer-gpu", "pyscf"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def phase_correction_from_t0(overlap_t0: complex) -> complex:
    """Return a unit phasor that maps the measured t=0 overlap to +real."""
    magnitude = abs(overlap_t0)
    if not math.isfinite(magnitude) or magnitude <= 0:
        raise ValueError("t=0 overlap must be finite and nonzero")
    return np.conjugate(overlap_t0 / magnitude)


def correct_overlap_series(
    overlap_t0: complex,
    overlaps: np.ndarray,
) -> dict[str, Any]:
    """Apply the t=0 phase and unwrap the corrected time series."""
    values = np.asarray(overlaps, dtype=complex)
    correction = phase_correction_from_t0(overlap_t0)
    corrected = correction * values
    corrected_t0 = correction * overlap_t0
    principal = np.angle(corrected)
    unwrapped_with_origin = np.unwrap(
        np.concatenate(([float(np.angle(corrected_t0))], principal))
    )
    unwrapped = unwrapped_with_origin[1:] - unwrapped_with_origin[0]
    jumps = np.diff(unwrapped_with_origin)
    return {
        "correction": correction,
        "corrected_t0": corrected_t0,
        "corrected": corrected,
        "principal_phases": principal,
        "unwrapped_phases": unwrapped,
        "maximum_adjacent_unwrapped_phase_jump": (
            float(np.max(np.abs(jumps))) if jumps.size else 0.0
        ),
    }


def _cost(time_value: float, error: float, *, rotations: int) -> float | None:
    if not math.isfinite(error) or error < 0 or error >= TARGET_ERROR:
        return None
    return float(BETA * rotations / (time_value * (TARGET_ERROR - error)))


def calibrate(
    *,
    h_chain: int,
    slug: str,
    output: Path,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    label = LABELS[slug]
    started = time.perf_counter()
    devices = available_aer_devices()
    if "GPU" not in devices:
        raise RuntimeError(f"Aer GPU is unavailable: {devices}")
    system = _prepare_system(h_chain)
    state = np.asarray(system["state"], dtype=complex).reshape(-1)
    evolution_results, profile = tEvolution_vectors_grouper_optimized(
        system["groups"],
        [-0.0],
        int(system["num_qubits"]),
        system["state"],
        label,
        device="GPU",
        processes=1,
    )
    _, evolved, rotations = evolution_results[0]
    evolved_state = np.asarray(evolved.data, dtype=complex)
    overlap = complex(np.vdot(state, evolved_state))
    correction = phase_correction_from_t0(overlap)
    corrected = correction * overlap
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "same-template t=0 global-phase calibration",
        "created_at": _now(),
        "git_commit": _git_commit(),
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
            "aer_devices": list(devices),
        },
        "system": {
            "h_chain": int(h_chain),
            "num_qubits": int(system["num_qubits"]),
            "ground_energy_without_constant_hartree": float(
                system["energy_without_constant"]
            ),
            "ground_state_diagnostics": system.get("ground_state_diagnostics"),
        },
        "product_formula": {
            "slug": slug,
            "label": label,
            "pauli_rotations_per_step": int(rotations),
        },
        "calibration": {
            "time": 0.0,
            "raw_overlap": _complex_payload(overlap),
            "raw_overlap_magnitude": float(abs(overlap)),
            "raw_phase_rad": float(np.angle(overlap)),
            "correction_phasor": _complex_payload(correction),
            "correction_phase_rad": float(np.angle(correction)),
            "corrected_overlap": _complex_payload(corrected),
            "corrected_phase_rad": float(np.angle(corrected)),
            "evolved_state_norm": float(np.linalg.norm(evolved_state)),
            "zero_phase_pass": bool(abs(np.angle(corrected)) <= 1e-12),
        },
        "execution_profile": profile,
        "elapsed_seconds": float(time.perf_counter() - started),
    }
    _atomic_json(output, payload)
    print(f"saved: {output}", flush=True)
    return payload


def _source_times(path: Path, *, maximum_points: int | None) -> np.ndarray:
    source = json.loads(path.read_text(encoding="utf-8"))
    times = np.asarray(source["calculation"]["times"], dtype=float)
    if times.ndim != 1 or times.size == 0 or np.any(times <= 0):
        raise ValueError(f"{path}: expected a nonempty positive time grid")
    if maximum_points is not None:
        times = times[: int(maximum_points)]
    return times


def same_template_sweep(
    *,
    h_chain: int,
    slug: str,
    source_json: Path,
    maximum_points: int | None,
    output: Path,
) -> dict[str, Any]:
    """Evaluate t=0 and positive diagnostic times with one Aer template."""
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    label = LABELS[slug]
    times = _source_times(source_json, maximum_points=maximum_points)
    started = time.perf_counter()
    devices = available_aer_devices()
    if "GPU" not in devices:
        raise RuntimeError(f"Aer GPU is unavailable: {devices}")
    system = _prepare_system(h_chain)
    state_column = system["state"]
    state = np.asarray(state_column, dtype=complex).reshape(-1)
    energy = float(system["energy_without_constant"])
    requested_times = np.concatenate(([0.0], times))
    evolution_results, profile = tEvolution_vectors_grouper_optimized(
        system["groups"],
        [-float(value) for value in requested_times],
        int(system["num_qubits"]),
        state_column,
        label,
        device="GPU",
        processes=1,
    )
    overlaps: list[complex] = []
    norms: list[float] = []
    rotations: int | None = None
    for time_value, (_, evolved, rotation_count) in zip(
        requested_times, evolution_results, strict=True
    ):
        if rotations is None:
            rotations = int(rotation_count)
        elif rotations != int(rotation_count):
            raise RuntimeError("The per-step rotation count changed with time")
        evolved_state = np.asarray(evolved.data, dtype=complex)
        overlaps.append(
            complex(
                np.exp(-1j * energy * float(time_value))
                * np.vdot(state, evolved_state)
            )
        )
        norms.append(float(np.linalg.norm(evolved_state)))
    overlap_t0 = overlaps[0]
    raw = np.asarray(overlaps[1:], dtype=complex)
    corrected_data = correct_overlap_series(overlap_t0, raw)
    corrected = np.asarray(corrected_data["corrected"], dtype=complex)
    corrected_phases = np.asarray(
        corrected_data["unwrapped_phases"], dtype=float
    )
    points = []
    for index, time_value in enumerate(times):
        points.append(
            {
                "time": float(time_value),
                "raw_phase_rotated_overlap": _complex_payload(raw[index]),
                "raw_phase_rad": float(np.angle(raw[index])),
                "corrected_phase_rotated_overlap": _complex_payload(
                    corrected[index]
                ),
                "corrected_principal_phase_rad": float(
                    corrected_data["principal_phases"][index]
                ),
                "corrected_unwrapped_phase_rad": float(
                    corrected_phases[index]
                ),
                "e_proxy_corrected_hartree": float(
                    abs(corrected_phases[index] / time_value)
                ),
                "ground_state_survival_probability": float(abs(raw[index]) ** 2),
                "evolved_state_norm": norms[index + 1],
            }
        )
    calibration = {
        "time": 0.0,
        "raw_overlap": _complex_payload(overlap_t0),
        "raw_overlap_magnitude": float(abs(overlap_t0)),
        "raw_phase_rad": float(np.angle(overlap_t0)),
        "correction_phasor": _complex_payload(
            corrected_data["correction"]
        ),
        "correction_phase_rad": float(
            np.angle(corrected_data["correction"])
        ),
        "corrected_overlap": _complex_payload(
            corrected_data["corrected_t0"]
        ),
        "corrected_phase_rad": float(
            np.angle(corrected_data["corrected_t0"])
        ),
        "evolved_state_norm": norms[0],
        "zero_phase_pass": bool(
            abs(np.angle(corrected_data["corrected_t0"])) <= 1e-12
        ),
    }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "same-template t=0 calibrated overlap proxy sweep",
        "created_at": _now(),
        "git_commit": _git_commit(),
        "source_time_grid_json": str(source_json),
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
            "aer_devices": list(devices),
        },
        "system": {
            "h_chain": int(h_chain),
            "num_qubits": int(system["num_qubits"]),
            "ground_energy_without_constant_hartree": energy,
            "ground_state_diagnostics": system.get("ground_state_diagnostics"),
        },
        "product_formula": {
            "slug": slug,
            "label": label,
            "pauli_rotations_per_step": int(rotations or 0),
        },
        "calibration": calibration,
        "phase_checks": {
            "zero_phase_pass": calibration["zero_phase_pass"],
            "maximum_adjacent_unwrapped_phase_jump_rad": corrected_data[
                "maximum_adjacent_unwrapped_phase_jump"
            ],
            "continuity_pass": bool(
                corrected_data["maximum_adjacent_unwrapped_phase_jump"] < np.pi
            ),
        },
        "times": [float(value) for value in times],
        "points": points,
        "execution_profile": profile,
        "elapsed_seconds": float(time.perf_counter() - started),
    }
    _atomic_json(output, payload)
    print(f"saved: {output}", flush=True)
    return payload


def _source_path(source_dir: Path, h_chain: int, slug: str) -> Path:
    return source_dir / f"H{h_chain}_{RUN_NAMES[slug]}.json"


def _calibration_path(calibration_dir: Path, h_chain: int, slug: str) -> Path:
    return calibration_dir / f"H{h_chain}_{slug}_t0.json"


def _schedule_task(
    schedule: dict[str, Any], h_chain: int, label: str
) -> dict[str, Any]:
    return schedule["tasks"][f"H{h_chain}"][label]


def _nearest_index(times: np.ndarray, target: float) -> int:
    index = int(np.argmin(np.abs(times - target)))
    if not np.isclose(times[index], target, rtol=1e-12, atol=1e-13):
        raise RuntimeError(f"t_ana={target:.17g} is absent from the grid")
    return index


def analyze(
    *,
    source_dir: Path,
    calibration_dir: Path,
    output_json: Path,
    output_markdown: Path,
) -> dict[str, Any]:
    if output_json.exists() or output_markdown.exists():
        raise FileExistsError("refusing to overwrite corrected analysis output")
    schedule_path = source_dir / "analytic_schedule.json"
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    warnings: list[str] = []
    all_phase_checks_pass = True
    for h_chain in ANALYSIS_CHAINS:
        results[f"H{h_chain}"] = {}
        for slug, label in LABELS.items():
            source_path = _source_path(source_dir, h_chain, slug)
            calibration_path = _calibration_path(
                calibration_dir, h_chain, slug
            )
            source = json.loads(source_path.read_text(encoding="utf-8"))
            calibration = json.loads(
                calibration_path.read_text(encoding="utf-8")
            )
            matches = [item for item in source["results"] if item["label"] == label]
            if len(matches) != 1:
                raise ValueError(f"{source_path}: expected one {label} result")
            result = matches[0]
            times = np.asarray(source["calculation"]["times"], dtype=float)
            raw = np.asarray(
                [_as_complex(item) for item in result["phase_rotated_overlaps"]],
                dtype=complex,
            )
            overlap_t0 = _as_complex(
                calibration["calibration"]["raw_overlap"]
            )
            corrected_data = correct_overlap_series(overlap_t0, raw)
            corrected = np.asarray(corrected_data["corrected"], dtype=complex)
            corrected_phases = np.asarray(
                corrected_data["unwrapped_phases"], dtype=float
            )
            corrected_proxy = np.abs(corrected_phases / times)
            raw_proxy = np.abs(np.angle(raw) / times)
            task = _schedule_task(schedule, h_chain, label)
            alpha = float(task["alpha"])
            order = int(task["formal_order"])
            model = alpha * times**order
            perturbative = np.asarray(result["errors_hartree"], dtype=float)
            survival = np.asarray(
                result["ground_state_survival_probabilities"], dtype=float
            )
            rotations = int(result["pauli_rotations_per_step"])
            t_ana = float(task["t_ana"])
            t_ana_index = _nearest_index(times, t_ana)
            continuity_pass = bool(
                corrected_data["maximum_adjacent_unwrapped_phase_jump"] < np.pi
            )
            zero_phase_pass = bool(
                calibration["calibration"]["zero_phase_pass"]
            )
            phase_pass = zero_phase_pass and continuity_pass
            all_phase_checks_pass = all_phase_checks_pass and phase_pass
            points = []
            for index, time_value in enumerate(times):
                e_model = float(model[index])
                e_pert = float(perturbative[index])
                e_proxy = float(corrected_proxy[index])
                points.append(
                    {
                        "time": float(time_value),
                        "time_over_t_ana": float(time_value / t_ana),
                        "raw_phase_rotated_overlap": _complex_payload(raw[index]),
                        "raw_phase_rad": float(np.angle(raw[index])),
                        "raw_overlap_phase_error_hartree_not_physical": float(
                            raw_proxy[index]
                        ),
                        "corrected_phase_rotated_overlap": _complex_payload(
                            corrected[index]
                        ),
                        "corrected_principal_phase_rad": float(
                            corrected_data["principal_phases"][index]
                        ),
                        "corrected_unwrapped_phase_rad": float(
                            corrected_phases[index]
                        ),
                        "e_model_hartree": e_model,
                        "e_pert_hartree": e_pert,
                        "e_proxy_corrected_hartree": e_proxy,
                        "e_pert_over_e_model": float(e_pert / e_model),
                        "e_proxy_over_e_model": float(e_proxy / e_model),
                        "ground_state_survival_probability": float(
                            survival[index]
                        ),
                        "C_model": _cost(
                            float(time_value), e_model, rotations=rotations
                        ),
                        "C_pert": _cost(
                            float(time_value), e_pert, rotations=rotations
                        ),
                        "C_proxy_corrected": _cost(
                            float(time_value), e_proxy, rotations=rotations
                        ),
                    }
                )
            main = points[t_ana_index]
            if main["C_proxy_corrected"] is None:
                warnings.append(
                    f"H{h_chain} {label}: corrected proxy cost invalid at t_ana"
                )
            results[f"H{h_chain}"][label] = {
                "status": "complete" if phase_pass else "failed",
                "source_raw_json": str(source_path),
                "source_calibration_json": str(calibration_path),
                "formal_order": order,
                "fixed_order_alpha": alpha,
                "t_ana": t_ana,
                "pauli_rotations_per_step": rotations,
                "t0_calibration": calibration["calibration"],
                "phase_checks": {
                    "zero_phase_pass": zero_phase_pass,
                    "continuity_pass": continuity_pass,
                    "maximum_adjacent_unwrapped_phase_jump_rad": corrected_data[
                        "maximum_adjacent_unwrapped_phase_jump"
                    ],
                },
                "points": points,
                "at_t_ana": main,
                "uncorrected_overlap_phase_cost_used": False,
            }

    status = "complete" if all_phase_checks_pass else "failed"
    payload = {
        "schema_version": 1,
        "purpose": "H9-H11 t=0 global-phase-corrected overlap proxy cost",
        "created_at": _now(),
        "git_commit": _git_commit(),
        "status": status,
        "source_schedule": str(schedule_path),
        "phase_correction_definition": (
            "z_corrected(t)=conj(z_raw(0)/abs(z_raw(0)))*z_raw(t)"
        ),
        "cost_model": {
            "formula": "BETA*N_rotation/[t*(epsilon_E-e(t))]",
            "BETA": float(BETA),
            "epsilon_E_hartree": float(TARGET_ERROR),
        },
        "results": results,
        "warnings": warnings,
        "uncorrected_overlap_phase_cost_used": False,
    }
    _atomic_json(output_json, payload)

    lines = [
        "# H9--H11 global-phase-corrected overlap validation",
        "",
        f"Status: `{status}`",
        "",
        "Uncorrected overlap-phase errors and costs are diagnostic only.",
        "",
        "| System | PF | phase0 raw | phase continuity | t_ana | e_pert/e_model | e_proxy/e_model | C_pert/C_model | C_proxy/C_model | survival |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for h_chain in ANALYSIS_CHAINS:
        for label in LABELS.values():
            case = results[f"H{h_chain}"][label]
            point = case["at_t_ana"]
            c_model = point["C_model"]
            c_pert = point["C_pert"]
            c_proxy = point["C_proxy_corrected"]
            lines.append(
                f"| H{h_chain} | {label} | "
                f"{case['t0_calibration']['raw_phase_rad']:.9g} | "
                f"{'pass' if case['phase_checks']['continuity_pass'] else 'fail'} | "
                f"{case['t_ana']:.8g} | "
                f"{point['e_pert_over_e_model']:.6g} | "
                f"{point['e_proxy_over_e_model']:.6g} | "
                f"{(c_pert / c_model) if c_pert is not None else float('nan'):.6g} | "
                f"{(c_proxy / c_model) if c_proxy is not None else float('nan'):.6g} | "
                f"{point['ground_state_survival_probability']:.9f} |"
            )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved: {output_json}", flush=True)
    print(f"saved: {output_markdown}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibration_parser = subparsers.add_parser("calibrate")
    calibration_parser.add_argument(
        "--h-chain", type=int, choices=CALIBRATION_CHAINS, required=True
    )
    calibration_parser.add_argument("--slug", choices=tuple(LABELS), required=True)
    calibration_parser.add_argument("--output", type=Path, required=True)
    sweep_parser = subparsers.add_parser("sweep")
    sweep_parser.add_argument(
        "--h-chain", type=int, choices=CALIBRATION_CHAINS, required=True
    )
    sweep_parser.add_argument("--slug", choices=tuple(LABELS), required=True)
    sweep_parser.add_argument("--source-json", type=Path, required=True)
    sweep_parser.add_argument("--maximum-points", type=int)
    sweep_parser.add_argument("--output", type=Path, required=True)
    analysis_parser = subparsers.add_parser("analyze")
    analysis_parser.add_argument("--source-dir", type=Path, required=True)
    analysis_parser.add_argument("--calibration-dir", type=Path, required=True)
    analysis_parser.add_argument("--output-json", type=Path, required=True)
    analysis_parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "calibrate":
        calibrate(h_chain=args.h_chain, slug=args.slug, output=args.output)
    elif args.command == "sweep":
        same_template_sweep(
            h_chain=args.h_chain,
            slug=args.slug,
            source_json=args.source_json,
            maximum_points=args.maximum_points,
            output=args.output,
        )
    else:
        analyze(
            source_dir=args.source_dir,
            calibration_dir=args.calibration_dir,
            output_json=args.output_json,
            output_markdown=args.output_markdown,
        )


if __name__ == "__main__":
    main()
