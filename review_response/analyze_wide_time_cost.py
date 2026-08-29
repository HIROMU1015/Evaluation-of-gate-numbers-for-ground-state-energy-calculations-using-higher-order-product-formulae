"""Compare measured and power-law QPE costs on wide H-chain time grids."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.cost_validation import (
    analytic_minimum_cost,
    analytic_optimal_time,
    discrete_minimum,
    measured_cost_curve,
    power_law_validity_intervals,
)
from trotterlib.fit_window import (
    estimate_gpu_noise_floor,
    rolling_loglog_fits,
    select_best_rolling_fit,
)


M5_LABEL = "4th(m5_best)"
Y8_LABEL = "8th(Morales-Y8m10b)"


def _finite_list(values: np.ndarray) -> list[float | None]:
    return [float(value) if np.isfinite(value) else None for value in values]


def _load_wide_sweeps(
    paths: Sequence[Path],
) -> dict[tuple[int, str], dict[str, Any]]:
    sweeps: dict[tuple[int, str], dict[str, Any]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        h_chain = int(payload["system"]["h_chain"])
        times = np.asarray(payload["calculation"]["times"], dtype=float)
        for result in payload["results"]:
            label = str(result["label"])
            key = (h_chain, label)
            if key in sweeps:
                raise ValueError(f"Duplicate wide sweep for H{h_chain} {label}")
            sweeps[key] = {
                "source": str(path),
                "times": times,
                "errors": np.asarray(result["errors_hartree"], dtype=float),
                "overlap_phase_errors": np.asarray(
                    result["overlap_phase_errors_hartree"], dtype=float
                ),
                "survival_probabilities": np.asarray(
                    result["ground_state_survival_probabilities"], dtype=float
                ),
                "formal_order": int(result["formal_order"]),
                "n_exp": int(result["pauli_rotations_per_step"]),
                "simulator_device": payload["calculation"]["simulator_device"],
                "aer_precision": payload["calculation"]["aer_precision"],
            }
    return sweeps


def _load_initial_fits(
    fit_analysis_path: Path,
    h2_reference_path: Path,
) -> dict[tuple[int, str], dict[str, Any]]:
    fit_analysis = json.loads(fit_analysis_path.read_text(encoding="utf-8"))
    fits: dict[tuple[int, str], dict[str, Any]] = {}
    for system_label, system_results in fit_analysis["results"].items():
        h_chain = int(system_label.removeprefix("H"))
        for label in (M5_LABEL, Y8_LABEL):
            if label not in system_results:
                continue
            result = system_results[label]
            best = result["best_rolling_fit"]
            if best is None:
                raise RuntimeError(f"No initial rolling fit for H{h_chain} {label}")
            fits[(h_chain, label)] = {
                "alpha": float(best["fixed_order_alpha"]),
                "formal_order": int(result["formal_order"]),
                "noise_floor_hartree": float(result["noise_floor_hartree"]),
                "fit_window": {
                    "t_start": float(best["t_start"]),
                    "t_stop": float(best["t_stop"]),
                    "free_order": float(best["free_order"]),
                    "r2": float(best["r2"]),
                },
                "source": str(fit_analysis_path),
            }

    h2_payload = json.loads(h2_reference_path.read_text(encoding="utf-8"))
    for label in (M5_LABEL, Y8_LABEL):
        result = h2_payload["results"][label]
        times = np.asarray(result["times"], dtype=float)
        direct = np.asarray(result["direct_errors_hartree"], dtype=float)
        perturbative = np.asarray(
            result["perturbative_errors_hartree"], dtype=float
        )
        order = int(result["formal_order"])
        floor = estimate_gpu_noise_floor(perturbative, direct)
        windows = rolling_loglog_fits(
            times,
            direct,
            formal_order=order,
            noise_floor=floor,
            window_size=5,
        )
        best = select_best_rolling_fit(windows)
        if best is None:
            raise RuntimeError(f"No initial H2 rolling fit for {label}")
        fits[(2, label)] = {
            "alpha": float(best["fixed_order_alpha"]),
            "formal_order": order,
            "noise_floor_hartree": float(floor),
            "fit_window": {
                "t_start": float(best["t_start"]),
                "t_stop": float(best["t_stop"]),
                "free_order": float(best["free_order"]),
                "r2": float(best["r2"]),
            },
            "source": str(h2_reference_path),
        }
    return fits


def _load_direct_results(
    paths: Sequence[Path],
) -> dict[tuple[int, str], dict[str, Any]]:
    direct: dict[tuple[int, str], dict[str, Any]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        h_chain = int(payload["system"]["h_chain"])
        for label, result in payload["results"].items():
            direct[(h_chain, label)] = {**result, "source": str(path)}
    return direct


def _curve_summary(
    times: np.ndarray,
    errors: np.ndarray,
    *,
    beta: float,
    n_exp: int,
    epsilon_e: float,
) -> dict[str, Any]:
    costs = measured_cost_curve(
        times,
        errors,
        beta=beta,
        n_exp=n_exp,
        epsilon_e=epsilon_e,
    )
    return {
        "errors_hartree": errors.tolist(),
        "costs": _finite_list(costs),
        "num_valid_cost_points": int(np.count_nonzero(np.isfinite(costs))),
        "minimum": discrete_minimum(times, costs),
    }


def _relative_difference(left: float, right: float) -> float:
    return abs(left / right - 1.0)


def analyze(
    wide_paths: Sequence[Path],
    *,
    fit_analysis_path: Path,
    h2_reference_path: Path,
    direct_paths: Sequence[Path],
    beta: float,
    epsilon_e: float,
) -> dict[str, Any]:
    sweeps = _load_wide_sweeps(wide_paths)
    initial_fits = _load_initial_fits(fit_analysis_path, h2_reference_path)
    direct_results = _load_direct_results(direct_paths)
    expected_keys = {
        (h_chain, label)
        for h_chain in (2, 4, 5)
        for label in (M5_LABEL, Y8_LABEL)
    }
    if set(sweeps) != expected_keys:
        raise ValueError(
            f"Wide sweeps differ from expected H2/H4/H5 x m5/Y8: {set(sweeps)}"
        )

    results: dict[str, dict[str, Any]] = {}
    for (h_chain, label), sweep in sorted(sweeps.items()):
        fit = initial_fits[(h_chain, label)]
        times = sweep["times"]
        errors = sweep["errors"]
        phase_errors = sweep["overlap_phase_errors"]
        order = int(fit["formal_order"])
        alpha = float(fit["alpha"])
        floor = float(fit["noise_floor_hartree"])
        n_exp = int(sweep["n_exp"])
        analytic_time = analytic_optimal_time(alpha, order, epsilon_e)
        analytic_cost = analytic_minimum_cost(
            beta, n_exp, alpha, order, epsilon_e
        )
        model_errors = alpha * times**order
        perturbative_curve = _curve_summary(
            times,
            errors,
            beta=beta,
            n_exp=n_exp,
            epsilon_e=epsilon_e,
        )
        phase_curve = _curve_summary(
            times,
            phase_errors,
            beta=beta,
            n_exp=n_exp,
            epsilon_e=epsilon_e,
        )
        nearest = int(np.argmin(np.abs(times - analytic_time)))

        validity: dict[str, Any] = {}
        for tolerance in (0.05, 0.10):
            deviations, intervals = power_law_validity_intervals(
                times,
                errors,
                alpha=alpha,
                order=order,
                noise_floor=floor,
                relative_tolerance=tolerance,
            )
            validity[f"relative_tolerance_{tolerance:.2f}"] = {
                "deviations": _finite_list(deviations),
                "intervals": intervals,
            }

        reliable_phase = (errors > floor) & (phase_errors > floor)
        phase_relative = np.full(times.shape, np.nan)
        phase_relative[reliable_phase] = (
            np.abs(errors[reliable_phase] - phase_errors[reliable_phase])
            / phase_errors[reliable_phase]
        )
        result: dict[str, Any] = {
            "label": label,
            "formal_order": order,
            "source": sweep["source"],
            "simulator_device": sweep["simulator_device"],
            "aer_precision": sweep["aer_precision"],
            "times": times.tolist(),
            "pauli_rotations_per_step": n_exp,
            "initial_fit": fit,
            "power_law_errors_hartree": model_errors.tolist(),
            "analytic_power_law_optimum": {
                "time": analytic_time,
                "cost": analytic_cost,
                "is_inside_sampled_range": bool(times[0] <= analytic_time <= times[-1]),
                "nearest_sampled_index": nearest,
                "nearest_sampled_time": float(times[nearest]),
                "measured_to_model_error_ratio_at_nearest_point": float(
                    errors[nearest] / model_errors[nearest]
                ),
            },
            "gpu_perturbative_curve": perturbative_curve,
            "overlap_phase_curve": phase_curve,
            "minimum_ground_state_survival_probability": float(
                np.min(sweep["survival_probabilities"])
            ),
            "maximum_perturbative_vs_overlap_phase_relative_difference": (
                float(np.nanmax(phase_relative))
                if np.any(reliable_phase)
                else None
            ),
            "power_law_validity": validity,
        }

        perturbative_minimum = perturbative_curve["minimum"]
        phase_minimum = phase_curve["minimum"]
        if perturbative_minimum is not None:
            result["perturbative_minimum_vs_analytic"] = {
                "time_relative_difference": _relative_difference(
                    perturbative_minimum["time"], analytic_time
                ),
                "cost_relative_difference": _relative_difference(
                    perturbative_minimum["value"], analytic_cost
                ),
            }
        if phase_minimum is not None:
            result["phase_minimum_vs_analytic"] = {
                "time_relative_difference": _relative_difference(
                    phase_minimum["time"], analytic_time
                ),
                "cost_relative_difference": _relative_difference(
                    phase_minimum["value"], analytic_cost
                ),
            }

        direct = direct_results.get((h_chain, label))
        if direct is not None:
            direct_times = np.asarray(direct["times"], dtype=float)
            if not np.allclose(direct_times, times, rtol=0.0, atol=1e-14):
                raise ValueError(f"Direct/GPU grids differ for H{h_chain} {label}")
            direct_errors = np.asarray(direct["direct_errors_hartree"], dtype=float)
            direct_curve = _curve_summary(
                times,
                direct_errors,
                beta=beta,
                n_exp=n_exp,
                epsilon_e=epsilon_e,
            )
            direct_minimum = direct_curve["minimum"]
            result["direct_diagonalization"] = {
                "source": direct["source"],
                "curve": direct_curve,
                "minimum_selected_ground_state_overlap_probability": direct[
                    "minimum_selected_ground_state_overlap_probability"
                ],
                "minimum_phase_branch_margin_hartree": direct[
                    "minimum_phase_branch_margin_hartree"
                ],
                "phase_branch_integers": [
                    int(point["phase_branch_integer"])
                    for point in direct["points"]
                ],
            }
            if direct_minimum is not None and perturbative_minimum is not None:
                result["perturbative_minimum_vs_direct"] = {
                    "time_relative_difference": _relative_difference(
                        perturbative_minimum["time"], direct_minimum["time"]
                    ),
                    "cost_relative_difference": _relative_difference(
                        perturbative_minimum["value"], direct_minimum["value"]
                    ),
                }

        results.setdefault(f"H{h_chain}", {})[label] = result

    comparisons: dict[str, Any] = {}
    for h_chain in (2, 4, 5):
        system_results = results[f"H{h_chain}"]
        m5 = system_results[M5_LABEL]
        y8 = system_results[Y8_LABEL]
        analytic_ratio = (
            y8["analytic_power_law_optimum"]["cost"]
            / m5["analytic_power_law_optimum"]["cost"]
        )
        measured_ratio = (
            y8["gpu_perturbative_curve"]["minimum"]["value"]
            / m5["gpu_perturbative_curve"]["minimum"]["value"]
        )
        phase_ratio = (
            y8["overlap_phase_curve"]["minimum"]["value"]
            / m5["overlap_phase_curve"]["minimum"]["value"]
        )
        comparison: dict[str, Any] = {
            "ratio_definition": "Y8m10b / m5_best; values below 1 favor Y8m10b",
            "analytic_power_law_minimum_cost_ratio": float(analytic_ratio),
            "gpu_perturbative_minimum_cost_ratio": float(measured_ratio),
            "overlap_phase_minimum_cost_ratio": float(phase_ratio),
            "analytic_and_measured_ranking_agree": bool(
                (analytic_ratio < 1) == (measured_ratio < 1)
            ),
            "measured_ratio_relative_difference_from_analytic": float(
                _relative_difference(measured_ratio, analytic_ratio)
            ),
        }
        if "direct_diagonalization" in m5 and "direct_diagonalization" in y8:
            direct_ratio = (
                y8["direct_diagonalization"]["curve"]["minimum"]["value"]
                / m5["direct_diagonalization"]["curve"]["minimum"]["value"]
            )
            comparison["direct_diagonalization_minimum_cost_ratio"] = float(
                direct_ratio
            )
            comparison["perturbative_ratio_relative_difference_from_direct"] = (
                float(_relative_difference(measured_ratio, direct_ratio))
            )
        comparisons[f"H{h_chain}"] = comparison

    return {
        "schema_version": 1,
        "purpose": (
            "Validate use of asymptotic PF alpha in the total QPE cost by "
            "direct minimization on wide measured time grids"
        ),
        "cost_model": {
            "formula": "beta*N_exp/(t*(epsilon_E-e_PF(t)))",
            "beta": beta,
            "epsilon_E_hartree": epsilon_e,
            "invalid_when": "e_PF(t) >= epsilon_E",
        },
        "results": results,
        "m5_vs_y8m10b": comparisons,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wide-json", nargs="+", type=Path, required=True)
    parser.add_argument("--fit-analysis-json", type=Path, required=True)
    parser.add_argument("--h2-reference-json", type=Path, required=True)
    parser.add_argument("--direct-json", nargs="*", type=Path, default=[])
    parser.add_argument("--beta", type=float, default=BETA)
    parser.add_argument("--epsilon-e", type=float, default=TARGET_ERROR)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(
        args.wide_json,
        fit_analysis_path=args.fit_analysis_json,
        h2_reference_path=args.h2_reference_json,
        direct_paths=args.direct_json,
        beta=args.beta,
        epsilon_e=args.epsilon_e,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
