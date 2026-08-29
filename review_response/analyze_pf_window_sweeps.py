"""Analyze paired CPU/GPU PF sweeps with per-system numerical floors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from trotterlib.analysis_utils import loglog_average_coeff, loglog_fit
from trotterlib.fit_window import (
    estimate_gpu_noise_floor,
    rolling_loglog_fits,
    select_best_rolling_fit,
)


def _load_sweeps(paths: list[Path]) -> dict[tuple[int, str], dict[str, Any]]:
    sweeps: dict[tuple[int, str], dict[str, Any]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        h_chain = int(payload["system"]["h_chain"])
        times = np.asarray(payload["calculation"]["times"], dtype=float)
        for result in payload["results"]:
            label = str(result["label"])
            sweeps[(h_chain, label)] = {
                "source": str(path),
                "times": times,
                "errors": np.asarray(result["errors_hartree"], dtype=float),
                "formal_order": int(result["formal_order"]),
            }
    return sweeps


def _masked_fit(
    times: np.ndarray,
    errors: np.ndarray,
    *,
    formal_order: int,
    noise_floor: float,
) -> dict[str, Any] | None:
    mask = np.isfinite(errors) & (errors > noise_floor)
    if np.count_nonzero(mask) < 2:
        return None
    fit = loglog_fit(
        times[mask], errors[mask], mask_nonpositive=False, compute_r2=True
    )
    return {
        "num_points": int(np.count_nonzero(mask)),
        "fit_mask": mask.tolist(),
        "free_order": float(fit.slope),
        "free_alpha": float(fit.coeff),
        "r2": float(fit.r2),
        "fixed_order_alpha": loglog_average_coeff(
            times[mask],
            errors[mask],
            formal_order,
            mask_nonpositive=False,
        ),
    }


def analyze_paired_sweeps(
    cpu_paths: list[Path],
    gpu_paths: list[Path],
    *,
    safety_factor: float,
    low_error_points: int,
    rolling_window_size: int,
) -> dict[str, Any]:
    cpu_sweeps = _load_sweeps(cpu_paths)
    gpu_sweeps = _load_sweeps(gpu_paths)
    shared_keys = sorted(set(cpu_sweeps) & set(gpu_sweeps))
    if not shared_keys:
        raise ValueError("No matching H-chain/PF labels in CPU and GPU inputs")

    results: dict[str, dict[str, Any]] = {}
    for h_chain, label in shared_keys:
        cpu = cpu_sweeps[(h_chain, label)]
        gpu = gpu_sweeps[(h_chain, label)]
        if not np.array_equal(cpu["times"], gpu["times"]):
            raise ValueError(f"CPU/GPU time grids differ for H{h_chain} {label}")
        if cpu["errors"].shape != gpu["errors"].shape:
            raise ValueError(f"CPU/GPU error shapes differ for H{h_chain} {label}")
        if cpu["formal_order"] != gpu["formal_order"]:
            raise ValueError(f"CPU/GPU formal orders differ for H{h_chain} {label}")

        times = gpu["times"]
        cpu_errors = cpu["errors"]
        gpu_errors = gpu["errors"]
        formal_order = int(gpu["formal_order"])
        noise_floor = estimate_gpu_noise_floor(
            cpu_errors,
            gpu_errors,
            safety_factor=safety_factor,
            low_error_points=low_error_points,
        )
        windows = rolling_loglog_fits(
            times,
            gpu_errors,
            formal_order=formal_order,
            noise_floor=noise_floor,
            window_size=rolling_window_size,
        )
        system_results = results.setdefault(f"H{h_chain}", {})
        system_results[label] = {
            "formal_order": formal_order,
            "times": times.tolist(),
            "cpu_errors_hartree": cpu_errors.tolist(),
            "gpu_errors_hartree": gpu_errors.tolist(),
            "cpu_source": cpu["source"],
            "gpu_source": gpu["source"],
            "max_cpu_gpu_absolute_difference": float(
                np.max(np.abs(gpu_errors - cpu_errors))
            ),
            "noise_floor_hartree": noise_floor,
            "noise_floor_method": {
                "kind": "scaled_max_cpu_gpu_difference_at_lowest_error_points",
                "safety_factor": safety_factor,
                "low_error_points": low_error_points,
            },
            "masked_full_grid_fit": _masked_fit(
                times,
                gpu_errors,
                formal_order=formal_order,
                noise_floor=noise_floor,
            ),
            "rolling_window_size": rolling_window_size,
            "rolling_fits": windows,
            "best_rolling_fit": select_best_rolling_fit(windows),
        }

    return {
        "schema_version": 1,
        "purpose": (
            "PF-family time-window analysis using paired CPU/GPU numerical "
            "floors and consecutive rolling log-log fits"
        ),
        "results": results,
    }


def add_h2_diagonalization(
    analysis: dict[str, Any],
    path: Path,
    *,
    rolling_window_size: int,
    safety_factor: float,
    low_error_points: int,
) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    direct_results: dict[str, Any] = {}
    for label, result in payload["results"].items():
        formal_order = int(result["formal_order"])
        times = np.asarray(result["times"], dtype=float)
        errors = np.asarray(result["direct_errors_hartree"], dtype=float)
        perturbative = np.asarray(
            result["perturbative_errors_hartree"], dtype=float
        )
        noise_floor = estimate_gpu_noise_floor(
            perturbative,
            errors,
            safety_factor=safety_factor,
            low_error_points=low_error_points,
        )
        reliable = np.isfinite(errors) & (errors > noise_floor)
        relative_difference = np.full(errors.shape, np.nan)
        relative_difference[reliable] = (
            np.abs(perturbative[reliable] - errors[reliable])
            / errors[reliable]
        )
        windows = rolling_loglog_fits(
            times,
            errors,
            formal_order=formal_order,
            noise_floor=noise_floor,
            window_size=rolling_window_size,
        )
        direct_results[label] = {
            "formal_order": formal_order,
            "times": times.tolist(),
            "direct_errors_hartree": errors.tolist(),
            "perturbative_errors_hartree": perturbative.tolist(),
            "estimator_relative_differences": [
                float(value) if np.isfinite(value) else None
                for value in relative_difference
            ],
            "noise_floor_hartree": noise_floor,
            "noise_floor_method": {
                "kind": (
                    "scaled_max_direct_perturbative_difference_at_"
                    "lowest_error_points"
                ),
                "safety_factor": safety_factor,
                "low_error_points": low_error_points,
            },
            "num_reliable_estimator_comparison_points": int(
                np.count_nonzero(reliable)
            ),
            "max_estimator_relative_difference": float(
                np.nanmax(relative_difference)
            ),
            "median_estimator_relative_difference": float(
                np.nanmedian(relative_difference)
            ),
            "rolling_fits": windows,
            "best_rolling_fit": select_best_rolling_fit(windows),
        }
    analysis["h2_direct_diagonalization"] = {
        "source": str(path),
        "results": direct_results,
    }


def add_targeted_gpu_sweeps(
    analysis: dict[str, Any],
    paths: list[Path],
    *,
    rolling_window_size: int,
) -> None:
    """Analyze targeted GPU grids using floors from the paired broad sweeps."""
    targeted = _load_sweeps(paths)
    for (h_chain, label), sweep in sorted(targeted.items()):
        result = analysis["results"][f"H{h_chain}"][label]
        noise_floor = float(result["noise_floor_hartree"])
        windows = rolling_loglog_fits(
            sweep["times"],
            sweep["errors"],
            formal_order=int(sweep["formal_order"]),
            noise_floor=noise_floor,
            window_size=rolling_window_size,
        )
        result.setdefault("targeted_gpu_sweeps", []).append(
            {
                "source": sweep["source"],
                "times": sweep["times"].tolist(),
                "gpu_errors_hartree": sweep["errors"].tolist(),
                "noise_floor_hartree": noise_floor,
                "rolling_fits": windows,
                "best_rolling_fit": select_best_rolling_fit(windows),
            }
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu-json", nargs="+", type=Path, required=True)
    parser.add_argument("--gpu-json", nargs="+", type=Path, required=True)
    parser.add_argument("--h2-diagonalization-json", type=Path)
    parser.add_argument("--targeted-gpu-json", nargs="*", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--noise-safety-factor", type=float, default=5.0)
    parser.add_argument("--low-error-points", type=int, default=3)
    parser.add_argument("--rolling-window-size", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis = analyze_paired_sweeps(
        args.cpu_json,
        args.gpu_json,
        safety_factor=args.noise_safety_factor,
        low_error_points=args.low_error_points,
        rolling_window_size=args.rolling_window_size,
    )
    if args.h2_diagonalization_json is not None:
        add_h2_diagonalization(
            analysis,
            args.h2_diagonalization_json,
            rolling_window_size=args.rolling_window_size,
            safety_factor=args.noise_safety_factor,
            low_error_points=args.low_error_points,
        )
    if args.targeted_gpu_json:
        add_targeted_gpu_sweeps(
            analysis,
            args.targeted_gpu_json,
            rolling_window_size=args.rolling_window_size,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
