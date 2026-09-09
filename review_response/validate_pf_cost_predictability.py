"""Compare fourth-order PFs by finite-time cost predictability.

This is the first-stage test for designing a product formula that is easy to
extrapolate, rather than merely minimizing its short-time error coefficient.
For each directly solvable H chain and PF, the script

* selects a short-time fit by one common, predeclared rolling-window rule;
* computes the ground-connected PF eigenphase on a grid around the analytic
  power-law optimum;
* brackets the end of the contiguous 10% leading-power regime; and
* compares the analytic optimum and cost with the sampled direct optimum.

Only small systems are used.  The purpose is to determine whether
predictability varies systematically between existing fourth-order formulas
before optimizing any new coefficients.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from run_large_hchain_moment_phase import _overlap_point
from sweep_direct_scaling_h6_h7 import _direct_point, _write_json
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR, pf_order
from trotterlib.cost_validation import (
    analytic_minimum_cost,
    analytic_optimal_time,
)
from trotterlib.fit_window import rolling_loglog_fits
from validate_asymptotic_cost_small_systems import _prepare_system


DEFAULT_LABELS = (
    "4th",
    "4th(new_2)",
    "4th(new_3)",
    "4th(m5_best)",
    "4th(m6)",
)
DEFAULT_H_CHAINS = (2, 4, 5)
DEFAULT_FIT_TIMES = tuple(np.geomspace(0.06, 0.80, 15))
DEFAULT_RELATIVE_TIMES = tuple(np.round(np.arange(0.1, 1.41, 0.1), 10))
DEFAULT_OUTPUT_DIR = Path("artifacts/pf_cost_predictability_baseline")


def select_declared_fit_window(
    windows: Sequence[dict[str, Any]],
    *,
    order_tolerance: float,
    minimum_r2: float,
) -> dict[str, Any] | None:
    """Select the earliest reliable window satisfying the declared tests.

    Choosing the earliest qualifying window avoids selecting a finite-time
    window after looking at the analytic optimum.  No formula-specific rule is
    used.  If no window qualifies, the caller reports the formula as not
    analyzable by the common leading-power rule.
    """

    qualified = [
        window
        for window in windows
        if float(window["order_deviation"]) <= order_tolerance
        and float(window["r2"]) >= minimum_r2
    ]
    if not qualified:
        return None
    return min(
        qualified,
        key=lambda window: (
            int(window["start_index"]),
            int(window["stop_index_exclusive"]),
        ),
    )


def contiguous_validity_bracket(
    relative_times: Sequence[float],
    ratios: Sequence[float],
    *,
    tolerance: float,
) -> dict[str, Any]:
    """Bracket the first failure of a leading-power model on an ordered grid."""

    times = np.asarray(relative_times, dtype=float)
    values = np.asarray(ratios, dtype=float)
    if times.shape != values.shape or times.size == 0:
        raise ValueError("relative_times and ratios must have the same size")
    if np.any(np.diff(times) <= 0.0):
        raise ValueError("relative_times must be strictly increasing")
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")

    passed_indices: list[int] = []
    first_failed_index: int | None = None
    for index, ratio in enumerate(values):
        if not np.isfinite(ratio) or abs(float(ratio) - 1.0) > tolerance:
            first_failed_index = index
            break
        passed_indices.append(index)

    return {
        "num_contiguous_passed_points": len(passed_indices),
        "t_pass_over_t_ana": (
            None if not passed_indices else float(times[passed_indices[-1]])
        ),
        "t_fail_over_t_ana": (
            None
            if first_failed_index is None
            else float(times[first_failed_index])
        ),
        "right_censored": first_failed_index is None,
    }


def sampled_predictability_metrics(
    points: Sequence[dict[str, Any]],
    *,
    analytic_model_cost: float,
    formal_order: int,
    scale_tolerance: float,
    scale_interval: tuple[float, float],
    optimization_interval: tuple[float, float],
) -> dict[str, Any]:
    """Summarize scaling and QPE-cost predictability from direct points."""

    if not points:
        raise ValueError("points must not be empty")
    ordered = sorted(points, key=lambda point: float(point["relative_time"]))
    relative_times = np.asarray(
        [float(point["relative_time"]) for point in ordered]
    )
    ratios = np.asarray(
        [float(point["direct_to_model_ratio"]) for point in ordered]
    )
    signed_shifts = np.asarray(
        [float(point["signed_direct_shift_hartree"]) for point in ordered]
    )
    costs = np.asarray(
        [
            np.nan if point["direct_cost"] is None else float(point["direct_cost"])
            for point in ordered
        ]
    )

    bracket = contiguous_validity_bracket(
        relative_times, ratios, tolerance=scale_tolerance
    )
    scale_mask = (
        (relative_times >= scale_interval[0])
        & (relative_times <= scale_interval[1])
    )
    scale_deviations = np.abs(ratios[scale_mask] - 1.0)

    effective_orders: list[float] = []
    scale_indices = np.flatnonzero(scale_mask)
    for left, right in zip(scale_indices[:-1], scale_indices[1:]):
        left_error = abs(signed_shifts[left])
        right_error = abs(signed_shifts[right])
        if left_error == 0.0 or right_error == 0.0:
            continue
        effective_orders.append(
            float(
                np.log(right_error / left_error)
                / np.log(relative_times[right] / relative_times[left])
            )
        )

    nonzero_signs = np.sign(signed_shifts[scale_mask])
    nonzero_signs = nonzero_signs[nonzero_signs != 0.0]
    sign_changes = int(np.count_nonzero(nonzero_signs[1:] != nonzero_signs[:-1]))

    optimization_mask = (
        (relative_times >= optimization_interval[0])
        & (relative_times <= optimization_interval[1])
        & np.isfinite(costs)
    )
    valid_indices = np.flatnonzero(optimization_mask)
    direct_minimum: dict[str, Any] | None
    if valid_indices.size:
        minimum_index = int(valid_indices[np.argmin(costs[valid_indices])])
        direct_minimum = {
            "relative_time": float(relative_times[minimum_index]),
            "cost": float(costs[minimum_index]),
            "time_prediction_relative_error": float(
                abs(relative_times[minimum_index] - 1.0)
            ),
            "cost_prediction_relative_error": float(
                abs(analytic_model_cost / costs[minimum_index] - 1.0)
            ),
            "is_boundary_of_optimization_grid": bool(
                minimum_index in (valid_indices[0], valid_indices[-1])
            ),
        }
    else:
        direct_minimum = None

    analytic_indices = np.flatnonzero(np.isclose(relative_times, 1.0))
    if analytic_indices.size != 1:
        raise ValueError("points must contain exactly one t/t_ana = 1 point")
    analytic_index = int(analytic_indices[0])
    direct_cost_at_analytic = costs[analytic_index]

    effective_array = np.asarray(effective_orders, dtype=float)
    return {
        "ten_percent_validity": bracket,
        "scale_interval": list(scale_interval),
        "maximum_scale_relative_deviation": (
            None if scale_deviations.size == 0 else float(np.max(scale_deviations))
        ),
        "median_effective_order": (
            None if effective_array.size == 0 else float(np.median(effective_array))
        ),
        "maximum_effective_order_deviation": (
            None
            if effective_array.size == 0
            else float(np.max(np.abs(effective_array - formal_order)))
        ),
        "signed_error_sign_changes_in_scale_interval": sign_changes,
        "direct_at_analytic_time": {
            "direct_to_model_error_ratio": float(ratios[analytic_index]),
            "direct_cost": (
                None
                if not np.isfinite(direct_cost_at_analytic)
                else float(direct_cost_at_analytic)
            ),
            "model_to_direct_cost_relative_error": (
                None
                if not np.isfinite(direct_cost_at_analytic)
                else float(
                    abs(analytic_model_cost / direct_cost_at_analytic - 1.0)
                )
            ),
        },
        "sampled_direct_minimum": direct_minimum,
    }


def _short_time_fit(
    system: dict[str, Any],
    label: str,
    fit_times: Sequence[float],
    *,
    noise_floor: float,
    rolling_window_size: int,
    order_tolerance: float,
    minimum_r2: float,
) -> dict[str, Any]:
    points = [
        _overlap_point(system, label, float(evolution_time))
        for evolution_time in fit_times
    ]
    errors = np.asarray(
        [point["perturbative_error_hartree"] for point in points], dtype=float
    )
    windows = rolling_loglog_fits(
        np.asarray(fit_times, dtype=float),
        errors,
        formal_order=int(pf_order(label)),
        noise_floor=noise_floor,
        window_size=rolling_window_size,
    )
    selected = select_declared_fit_window(
        windows,
        order_tolerance=order_tolerance,
        minimum_r2=minimum_r2,
    )
    diagnostic_best = (
        None
        if not windows
        else min(
            windows,
            key=lambda window: (
                float(window["order_deviation"]),
                -float(window["r2"]),
            ),
        )
    )
    qualified_alphas = [
        float(window["fixed_order_alpha"])
        for window in windows
        if float(window["order_deviation"]) <= order_tolerance
        and float(window["r2"]) >= minimum_r2
    ]
    return {
        "times": [float(value) for value in fit_times],
        "errors_hartree": errors.tolist(),
        "noise_floor_hartree": float(noise_floor),
        "rolling_window_size": int(rolling_window_size),
        "order_tolerance": float(order_tolerance),
        "minimum_r2": float(minimum_r2),
        "rolling_windows": windows,
        "selected_window": selected,
        "diagnostic_best_window_when_unqualified": (
            None if selected is not None else diagnostic_best
        ),
        "qualified": selected is not None,
        "qualified_alpha_max_over_min": (
            None
            if not qualified_alphas
            else float(max(qualified_alphas) / min(qualified_alphas))
        ),
        "points": points,
    }


def _direct_points(
    system: dict[str, Any],
    label: str,
    relative_times: Sequence[float],
    *,
    alpha: float,
    analytic_time: float,
    epsilon_e: float,
) -> list[dict[str, Any]]:
    order = int(pf_order(label))
    previous_vector: np.ndarray | None = None
    previous_shift: float | None = None
    records: list[dict[str, Any]] = []
    for relative_time in relative_times:
        evolution_time = float(relative_time * analytic_time)
        model_error = float(alpha * evolution_time**order)
        raw, previous_vector, previous_shift = _direct_point(
            system,
            label,
            evolution_time,
            model_error,
            epsilon_e,
            previous_vector,
            previous_shift,
            "s2-cache",
        )
        branch = raw["continuously_tracked_branch"]
        records.append(
            {
                "relative_time": float(relative_time),
                "time": evolution_time,
                "model_error_hartree": model_error,
                "signed_direct_shift_hartree": float(
                    branch["unwrapped_energy_shift_hartree"]
                ),
                "direct_error_hartree": float(branch["direct_error_hartree"]),
                "direct_to_model_ratio": float(branch["direct_to_model_ratio"]),
                "direct_cost": branch["cost"],
                "ground_overlap_probability": float(
                    branch["ground_overlap_probability"]
                ),
                "overlap_with_previous_probability": branch[
                    "overlap_with_previous_probability"
                ],
                "one_overlap_phase_error_hartree": float(
                    raw["one_overlap_phase_error_hartree"]
                ),
                "unitarity_residual_frobenius_norm": float(
                    raw["unitarity_residual_frobenius_norm"]
                ),
                "elapsed_seconds": float(raw["elapsed_seconds"]),
            }
        )
    return records


def _analysis_pass(
    fit: dict[str, Any], metrics: dict[str, Any]
) -> dict[str, Any]:
    minimum = metrics["sampled_direct_minimum"]
    bracket = metrics["ten_percent_validity"]
    checks = {
        "short_time_fit_qualified": bool(fit["qualified"]),
        "confirmed_scaling_through_1p1_t_ana": bool(
            bracket["t_pass_over_t_ana"] is not None
            and float(bracket["t_pass_over_t_ana"]) >= 1.1
        ),
        "direct_optimum_time_within_15_percent": bool(
            minimum is not None
            and float(minimum["time_prediction_relative_error"]) <= 0.15
        ),
        "minimum_cost_prediction_within_10_percent": bool(
            minimum is not None
            and float(minimum["cost_prediction_relative_error"]) <= 0.10
        ),
        "no_signed_error_zero_crossing_near_schedule": bool(
            metrics["signed_error_sign_changes_in_scale_interval"] == 0
        ),
    }
    return {"checks": checks, "passed": all(checks.values())}


def _flatten_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for system_name, system in payload["systems"].items():
        for label, result in system["formulas"].items():
            fit = result["short_time_fit"]
            metrics = result.get("predictability")
            selected = fit["selected_window"]
            row: dict[str, Any] = {
                "system": system_name,
                "pf": label,
                "fit_qualified": fit["qualified"],
                "free_order": None if selected is None else selected["free_order"],
                "alpha": None
                if selected is None
                else selected["fixed_order_alpha"],
                "alpha_window_max_over_min": fit[
                    "qualified_alpha_max_over_min"
                ],
                "rotations": result["pauli_rotations_per_step"],
                "t_ana": result.get("analytic_optimal_time"),
                "analytic_model_cost": result.get("analytic_model_cost"),
            }
            if metrics is not None:
                minimum = metrics["sampled_direct_minimum"]
                row.update(
                    {
                        "t_pass_over_t_ana": metrics["ten_percent_validity"][
                            "t_pass_over_t_ana"
                        ],
                        "t_fail_over_t_ana": metrics["ten_percent_validity"][
                            "t_fail_over_t_ana"
                        ],
                        "max_scale_deviation": metrics[
                            "maximum_scale_relative_deviation"
                        ],
                        "error_ratio_at_t_ana": metrics[
                            "direct_at_analytic_time"
                        ]["direct_to_model_error_ratio"],
                        "direct_optimum_over_t_ana": (
                            None if minimum is None else minimum["relative_time"]
                        ),
                        "direct_minimum_cost": (
                            None if minimum is None else minimum["cost"]
                        ),
                        "time_prediction_error": (
                            None
                            if minimum is None
                            else minimum["time_prediction_relative_error"]
                        ),
                        "minimum_cost_prediction_error": (
                            None
                            if minimum is None
                            else minimum["cost_prediction_relative_error"]
                        ),
                        "sign_changes": metrics[
                            "signed_error_sign_changes_in_scale_interval"
                        ],
                        "analysis_pass": result["analysis_predictability_pass"][
                            "passed"
                        ],
                    }
                )
            rows.append(row)
    reference_by_system = {
        str(row["system"]): float(row["direct_minimum_cost"])
        for row in rows
        if row["pf"] == "4th(m5_best)"
        and row.get("direct_minimum_cost") is not None
    }
    for row in rows:
        reference = reference_by_system.get(str(row["system"]))
        direct_minimum = row.get("direct_minimum_cost")
        row["direct_minimum_cost_over_m5"] = (
            None
            if reference is None or direct_minimum is None
            else float(direct_minimum) / reference
        )
    return rows


def _aggregate(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted({str(row["pf"]) for row in rows})
    result: dict[str, Any] = {}
    for label in labels:
        selected = [row for row in rows if row["pf"] == label]

        def finite_values(key: str) -> list[float]:
            return [
                float(row[key])
                for row in selected
                if row.get(key) is not None and np.isfinite(float(row[key]))
            ]

        t_pass = finite_values("t_pass_over_t_ana")
        cost_errors = finite_values("minimum_cost_prediction_error")
        time_errors = finite_values("time_prediction_error")
        cost_ratios = finite_values("direct_minimum_cost_over_m5")
        result[label] = {
            "num_systems": len(selected),
            "num_fit_qualified": sum(bool(row["fit_qualified"]) for row in selected),
            "num_analysis_passed": sum(bool(row.get("analysis_pass")) for row in selected),
            "all_systems_analysis_passed": all(
                bool(row.get("analysis_pass")) for row in selected
            ),
            "worst_confirmed_t_pass_over_t_ana": min(t_pass) if t_pass else None,
            "maximum_minimum_cost_prediction_error": (
                max(cost_errors) if cost_errors else None
            ),
            "median_minimum_cost_prediction_error": (
                float(np.median(cost_errors)) if cost_errors else None
            ),
            "maximum_time_prediction_error": (
                max(time_errors) if time_errors else None
            ),
            "median_direct_minimum_cost_over_m5": (
                float(np.median(cost_ratios)) if cost_ratios else None
            ),
            "maximum_direct_minimum_cost_over_m5": (
                max(cost_ratios) if cost_ratios else None
            ),
        }
    return result


def _format(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}g}"
    return str(value)


def _write_report(
    path: Path, payload: dict[str, Any], rows: Sequence[dict[str, Any]]
) -> None:
    lines = [
        "# Finite-time PF cost-predictability baseline",
        "",
        "This is an exploratory small-system test.  The pass thresholds were "
        "declared before inspecting the direct finite-time results; they are "
        "not yet publication-level certification criteria.",
        "",
        "## Per-system results",
        "",
        "| System | PF | fit order | alpha | rotations | t_pass/t_ana | "
        "t_fail/t_ana | e_direct/e_model at t_ana | t_direct*/t_ana | "
        "minimum-cost prediction error | C_direct*/C_direct,m5* | pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["system"]),
                    str(row["pf"]),
                    _format(row["free_order"]),
                    _format(row["alpha"]),
                    _format(row["rotations"]),
                    _format(row.get("t_pass_over_t_ana")),
                    _format(row.get("t_fail_over_t_ana")),
                    _format(row.get("error_ratio_at_t_ana")),
                    _format(row.get("direct_optimum_over_t_ana")),
                    _format(row.get("minimum_cost_prediction_error")),
                    _format(row.get("direct_minimum_cost_over_m5")),
                    _format(row.get("analysis_pass")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Cross-system summary",
            "",
            "| PF | qualified fits | predictability passes | worst "
            "t_pass/t_ana | max cost-prediction error | max time-prediction "
            "error | median C_direct*/C_direct,m5* |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, aggregate in payload["aggregate"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    f"{aggregate['num_fit_qualified']}/{aggregate['num_systems']}",
                    f"{aggregate['num_analysis_passed']}/{aggregate['num_systems']}",
                    _format(aggregate["worst_confirmed_t_pass_over_t_ana"]),
                    _format(aggregate["maximum_minimum_cost_prediction_error"]),
                    _format(aggregate["maximum_time_prediction_error"]),
                    _format(aggregate["median_direct_minimum_cost_over_m5"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    fully_passing = [
        label
        for label, result in payload["aggregate"].items()
        if result["all_systems_analysis_passed"]
    ]
    if fully_passing:
        lines.append(
            "- Existing formulas passing every exploratory criterion: "
            + ", ".join(fully_passing)
            + "."
        )
    else:
        lines.append(
            "- No existing fourth-order formula passes every exploratory "
            "predictability criterion on all tested systems."
        )
    unqualified = [
        label
        for label, result in payload["aggregate"].items()
        if result["num_fit_qualified"] < result["num_systems"]
    ]
    if unqualified:
        lines.append(
            "- The common short-time fit rule itself fails for: "
            + ", ".join(unqualified)
            + ".  A tiny or system-specific leading coefficient can therefore "
            "make an ostensibly fourth-order formula difficult to analyze."
        )
    lines.extend(
        [
            "- A useful new formula should improve the worst-system "
            "t_pass/t_ana and both prediction errors, not only alpha.",
            "- H2/H4/H5 are an exploratory set.  Any coefficient optimization "
            "must reserve H6/H7 and non-hydrogen-chain geometries as holdouts.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    *,
    h_chains: Sequence[int],
    labels: Sequence[str],
    fit_times: Sequence[float],
    relative_times: Sequence[float],
    output_dir: Path,
    epsilon_e: float,
    noise_floor: float,
    rolling_window_size: int,
    order_tolerance: float,
    minimum_r2: float,
    scale_tolerance: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "predictability_results.json"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "purpose": (
            "Baseline test of finite-time scaling and QPE-cost predictability "
            "for existing fourth-order product formulas"
        ),
        "epsilon_E_hartree": float(epsilon_e),
        "beta": float(BETA),
        "h_chains": [int(value) for value in h_chains],
        "labels": list(labels),
        "fit_times": [float(value) for value in fit_times],
        "relative_times": [float(value) for value in relative_times],
        "declared_rules": {
            "noise_floor_hartree": float(noise_floor),
            "rolling_window_size": int(rolling_window_size),
            "free_order_tolerance": float(order_tolerance),
            "minimum_loglog_r2": float(minimum_r2),
            "leading_power_relative_tolerance": float(scale_tolerance),
            "scale_evaluation_interval_t_over_t_ana": [0.3, 1.1],
            "direct_cost_optimization_interval_t_over_t_ana": [0.2, 1.4],
            "exploratory_pass": {
                "confirmed_t_pass_over_t_ana_at_least": 1.1,
                "direct_optimum_time_relative_error_at_most": 0.15,
                "minimum_cost_prediction_relative_error_at_most": 0.10,
                "signed_error_zero_crossings_near_schedule": 0,
            },
        },
        "systems": {},
        "aggregate": {},
        "elapsed_seconds": None,
    }
    _write_json(json_path, payload)
    total_started = time.perf_counter()

    for h_chain in h_chains:
        print(f"prepare H{h_chain}", flush=True)
        system = _prepare_system(int(h_chain))
        system_result: dict[str, Any] = {
            "sector_dimension": int(system["sector"]["dimension"]),
            "num_qubits": int(system["num_qubits"]),
            "formulas": {},
        }
        payload["systems"][f"H{h_chain}"] = system_result
        _write_json(json_path, payload)

        for label in labels:
            print(f"H{h_chain} {label}: short-time fit", flush=True)
            formula_started = time.perf_counter()
            fit = _short_time_fit(
                system,
                label,
                fit_times,
                noise_floor=noise_floor,
                rolling_window_size=rolling_window_size,
                order_tolerance=order_tolerance,
                minimum_r2=minimum_r2,
            )
            selected = fit["selected_window"]
            n_exp = int(DECOMPO_NUM[f"H{h_chain}"][label])
            formula_result: dict[str, Any] = {
                "formal_order": int(pf_order(label)),
                "pauli_rotations_per_step": n_exp,
                "short_time_fit": fit,
                "analytic_optimal_time": None,
                "analytic_model_cost": None,
                "direct_points": [],
                "predictability": None,
                "analysis_predictability_pass": {
                    "passed": False,
                    "checks": {"short_time_fit_qualified": False},
                },
                "elapsed_seconds": None,
            }
            system_result["formulas"][label] = formula_result
            if selected is None:
                formula_result["elapsed_seconds"] = float(
                    time.perf_counter() - formula_started
                )
                _write_json(json_path, payload)
                continue

            alpha = float(selected["fixed_order_alpha"])
            order = int(pf_order(label))
            analytic_time = analytic_optimal_time(alpha, order, epsilon_e)
            model_cost = analytic_minimum_cost(
                BETA, n_exp, alpha, order, epsilon_e
            )
            formula_result["analytic_optimal_time"] = analytic_time
            formula_result["analytic_model_cost"] = model_cost
            print(
                f"H{h_chain} {label}: direct grid around t_ana={analytic_time:.6g}",
                flush=True,
            )
            direct_points = _direct_points(
                system,
                label,
                relative_times,
                alpha=alpha,
                analytic_time=analytic_time,
                epsilon_e=epsilon_e,
            )
            metrics = sampled_predictability_metrics(
                direct_points,
                analytic_model_cost=model_cost,
                formal_order=order,
                scale_tolerance=scale_tolerance,
                scale_interval=(0.3, 1.1),
                optimization_interval=(0.2, 1.4),
            )
            formula_result["direct_points"] = direct_points
            formula_result["predictability"] = metrics
            formula_result["analysis_predictability_pass"] = _analysis_pass(
                fit, metrics
            )
            formula_result["elapsed_seconds"] = float(
                time.perf_counter() - formula_started
            )
            _write_json(json_path, payload)

    rows = _flatten_rows(payload)
    payload["aggregate"] = _aggregate(rows)
    payload["status"] = "complete"
    payload["elapsed_seconds"] = float(time.perf_counter() - total_started)
    _write_json(json_path, payload)

    csv_path = output_dir / "predictability_summary.csv"
    fieldnames = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    _write_report(output_dir / "report.md", payload, rows)
    print(f"saved: {output_dir}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h-chains", nargs="+", type=int, default=DEFAULT_H_CHAINS)
    parser.add_argument("--labels", nargs="+", default=DEFAULT_LABELS)
    parser.add_argument("--fit-times", nargs="+", type=float, default=DEFAULT_FIT_TIMES)
    parser.add_argument(
        "--relative-times", nargs="+", type=float, default=DEFAULT_RELATIVE_TIMES
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--epsilon-e", type=float, default=TARGET_ERROR)
    parser.add_argument("--noise-floor", type=float, default=5e-13)
    parser.add_argument("--rolling-window-size", type=int, default=5)
    parser.add_argument("--order-tolerance", type=float, default=0.20)
    parser.add_argument("--minimum-r2", type=float, default=0.999)
    parser.add_argument("--scale-tolerance", type=float, default=0.10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        h_chains=args.h_chains,
        labels=args.labels,
        fit_times=args.fit_times,
        relative_times=args.relative_times,
        output_dir=args.output_dir,
        epsilon_e=args.epsilon_e,
        noise_floor=args.noise_floor,
        rolling_window_size=args.rolling_window_size,
        order_tolerance=args.order_tolerance,
        minimum_r2=args.minimum_r2,
        scale_tolerance=args.scale_tolerance,
    )


if __name__ == "__main__":
    main()
