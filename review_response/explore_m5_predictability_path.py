"""Explore a fixed-cost fourth-order path between m5 and an even m5 formula.

All candidates contain eleven symmetric S2 stages, so their Pauli-rotation
count is identical.  The path is only a feasibility probe: it tests whether a
small change of fourth-order coefficients can trade some short-time error for
more predictable finite-time QPE cost.  It is not a final coefficient search.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

from sweep_direct_scaling_h6_h7 import (
    _principal_energy_shifts,
    _unwrap_energy_shift,
    _write_json,
)
from trotterlib.analysis_utils import loglog_average_coeff, loglog_fit
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.cost_validation import analytic_minimum_cost, analytic_optimal_time
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.optimal_trotter import (
    fourth_order_moment_residual_float64,
    solve_nonprocessed_4th_moment_coefficients,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps, symmetric_s2_sequence
from trotterlib.product_formula import (
    actual_circuit_optimized_4th_m5_list,
    new_4th_m2_list,
    new_4th_m3_list,
)
from trotterlib.sector_pf import build_sector_pf_unitary
from validate_asymptotic_cost_small_systems import _prepare_system
from validate_pf_cost_predictability import (
    DEFAULT_FIT_TIMES,
    DEFAULT_RELATIVE_TIMES,
    _analysis_pass,
    sampled_predictability_metrics,
    select_declared_fit_window,
)


OUTPUT_DIR = Path("artifacts/pf_cost_predictability_m5_path")
EQUAL_TAIL_LAMBDAS = (0.0, 0.25, 0.50, 0.75, 1.0)
PADDED_NEW3_LAMBDAS = (0.25, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
PADDED_NEW2_LAMBDAS = (0.25, 0.50, 0.75)


def equal_tail_m5_weights() -> np.ndarray:
    """Return the equal-tail real solution of the fourth-order condition."""

    tail_value = 1.0 / (10.0 - np.cbrt(10.0))
    tail = np.full(5, tail_value)
    return np.concatenate(([1.0 - 2.0 * np.sum(tail)], tail))


def projected_m5_path(
    lambdas: Sequence[float],
    *,
    endpoint_weights: Sequence[float] | None = None,
    route: str = "equal_tail",
) -> list[dict[str, Any]]:
    """Interpolate toward an endpoint and project onto the order condition."""

    baseline = np.asarray(actual_circuit_optimized_4th_m5_list(), dtype=float)
    endpoint = (
        equal_tail_m5_weights()
        if endpoint_weights is None
        else np.asarray(endpoint_weights, dtype=float)
    )
    if endpoint.shape != baseline.shape:
        raise ValueError("endpoint_weights must contain w0 and five tail weights")
    candidates: list[dict[str, Any]] = []
    for value in lambdas:
        interpolation = (1.0 - value) * baseline[1:] + value * endpoint[1:]
        solved = solve_nonprocessed_4th_moment_coefficients(
            kernel_m=5,
            initial=interpolation,
            max_nfev=5000,
        )
        tail = np.asarray(solved.w_tail, dtype=float)
        residual = float(fourth_order_moment_residual_float64(tail)[0])
        if abs(residual) > 1e-11:
            raise RuntimeError(
                f"lambda={value}: fourth-order residual is {residual}"
            )
        weights = np.concatenate(([float(solved.w0)], tail))
        candidates.append(
            {
                "name": f"m5_to_{route}_lambda_{value:.2f}",
                "route": route,
                "lambda": float(value),
                "weights": weights.tolist(),
                "fourth_order_moment_residual": residual,
                "coefficient_l1": float(np.sum(np.abs(weights))),
                "coefficient_linf": float(np.max(np.abs(weights))),
            }
        )
    return candidates


def exploratory_candidates() -> list[dict[str, Any]]:
    """Build three simple coefficient paths without optimizing on outcomes."""

    padded_new3 = np.asarray([*new_4th_m3_list(), 0.0, 0.0])
    padded_new2 = np.asarray([*new_4th_m2_list(), 0.0, 0.0, 0.0])
    return (
        projected_m5_path(EQUAL_TAIL_LAMBDAS)
        + projected_m5_path(
            PADDED_NEW3_LAMBDAS,
            endpoint_weights=padded_new3,
            route="padded_new3",
        )
        + projected_m5_path(
            PADDED_NEW2_LAMBDAS,
            endpoint_weights=padded_new2,
            route="padded_new2",
        )
    )


def _apply_custom_pf(
    system: dict[str, Any], sequence: Sequence[float], evolution_time: float
) -> np.ndarray:
    current = np.asarray(system["state"], dtype=complex).copy()
    spectra = system["group_spectra"]
    for group_index, weight in iter_s2_sequence_steps(len(spectra), sequence):
        values, vectors = spectra[group_index]
        current = vectors @ (
            np.exp(1j * evolution_time * float(weight) * values)
            * (vectors.conj().T @ current)
        )
    return current


def _custom_short_time_fit(
    system: dict[str, Any],
    sequence: Sequence[float],
    fit_times: Sequence[float],
    *,
    noise_floor: float = 5e-13,
    window_size: int = 5,
    order_tolerance: float = 0.2,
    minimum_r2: float = 0.999,
) -> dict[str, Any]:
    errors: list[float] = []
    for evolution_time in fit_times:
        evolved = _apply_custom_pf(system, sequence, float(evolution_time))
        overlap = complex(np.vdot(system["state"], evolved))
        rotated = np.exp(-1j * system["energy"] * evolution_time) * overlap
        errors.append(abs(float(rotated.imag / evolution_time)))
    windows = rolling_loglog_fits(
        np.asarray(fit_times),
        np.asarray(errors),
        formal_order=4,
        noise_floor=noise_floor,
        window_size=window_size,
    )
    selected = select_declared_fit_window(
        windows,
        order_tolerance=order_tolerance,
        minimum_r2=minimum_r2,
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "rolling_windows": windows,
        "times": [float(value) for value in fit_times],
        "errors_hartree": errors,
        "cross_check_full_grid_free_fit": {
            "order": float(loglog_fit(fit_times, errors).slope),
            "alpha": float(loglog_fit(fit_times, errors).coeff),
            "fixed_order_alpha": float(
                loglog_average_coeff(fit_times, errors, 4)
            ),
        },
    }


def _direct_custom_points(
    system: dict[str, Any],
    sequence: Sequence[float],
    relative_times: Sequence[float],
    *,
    alpha: float,
    analytic_time: float,
    n_exp: int,
    epsilon_e: float,
) -> list[dict[str, Any]]:
    previous_vector: np.ndarray | None = None
    previous_shift: float | None = None
    records: list[dict[str, Any]] = []
    state = np.asarray(system["state"], dtype=complex)
    reference_energy = float(system["energy"])

    for relative_time in relative_times:
        evolution_time = float(relative_time * analytic_time)
        model_error = float(alpha * evolution_time**4)
        unitary = build_sector_pf_unitary(
            system["group_spectra"],
            sequence,
            evolution_time,
            method="s2-cache",
        )
        triangular, eigenvectors = schur(
            unitary, output="complex", check_finite=False
        )
        eigenvalues = np.diag(triangular)
        if previous_vector is None:
            overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
        else:
            overlaps = np.abs(eigenvectors.conj().T @ previous_vector) ** 2
        index = int(np.argmax(overlaps))
        shifts = _principal_energy_shifts(
            eigenvalues, reference_energy, evolution_time
        )
        shift = _unwrap_energy_shift(
            float(shifts[index]), previous_shift, evolution_time
        )
        error = abs(shift)
        cost = (
            None
            if error >= epsilon_e
            else float(BETA * n_exp / (evolution_time * (epsilon_e - error)))
        )
        records.append(
            {
                "relative_time": float(relative_time),
                "time": evolution_time,
                "signed_direct_shift_hartree": shift,
                "direct_error_hartree": error,
                "model_error_hartree": model_error,
                "direct_to_model_ratio": float(error / model_error),
                "direct_cost": cost,
                "ground_overlap_probability": float(
                    abs(np.vdot(state, eigenvectors[:, index])) ** 2
                ),
                "overlap_with_previous_probability": (
                    None if previous_vector is None else float(overlaps[index])
                ),
            }
        )
        previous_vector = eigenvectors[:, index].copy()
        previous_shift = shift
    return records


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Fixed-stage m5 predictability path",
        "",
        "Every evaluated candidate has five nonzero tail coefficients and is "
        "charged the same eleven-S2-stage Pauli-rotation count as m5.  The "
        "three predeclared paths point toward the equal-tail formula and "
        "zero-padded new_2/new_3 formulas; the padded endpoints themselves are "
        "not evaluated.",
        "",
        "| Candidate | H chain | fit order | alpha | t_pass/t_ana | "
        "e_direct/e_model at t_ana | t_direct*/t_ana | cost prediction error | "
        "C_direct*/m5 | pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for candidate in payload["candidates"]:
        for system_name, result in candidate["systems"].items():
            fit = result["short_time_fit"]["selected_window"]
            metrics = result.get("predictability")
            if metrics is None:
                row = [candidate["name"], system_name, "—", "—"] + ["—"] * 6
            else:
                minimum = metrics["sampled_direct_minimum"]
                row = [
                    candidate["name"],
                    system_name,
                    f"{fit['free_order']:.3f}",
                    f"{fit['fixed_order_alpha']:.4g}",
                    str(metrics["ten_percent_validity"]["t_pass_over_t_ana"]),
                    f"{metrics['direct_at_analytic_time']['direct_to_model_error_ratio']:.3f}",
                    f"{minimum['relative_time']:.2f}",
                    f"{minimum['cost_prediction_relative_error']:.3f}",
                    f"{result['direct_minimum_cost_over_m5']:.3f}",
                    "yes" if result["analysis_predictability_pass"]["passed"] else "no",
                ]
            lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## Cross-system summary",
            "",
            "| Candidate | passes | worst t_pass/t_ana | max cost prediction "
            "error | median C_direct*/m5 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for candidate in payload["candidates"]:
        summary = candidate["summary"]
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate["name"],
                    f"{summary['num_passed']}/{summary['num_systems']}",
                    f"{summary['worst_t_pass_over_t_ana']:.3f}",
                    f"{summary['maximum_cost_prediction_error']:.3f}",
                    f"{summary['median_direct_minimum_cost_over_m5']:.3f}",
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "path_results.json"
    candidates = exploratory_candidates()
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "purpose": (
            "Feasibility test for a fixed-stage fourth-order tradeoff between "
            "minimum cost and finite-time analytic predictability"
        ),
        "h_chains": [2, 4, 5],
        "fit_times": list(DEFAULT_FIT_TIMES),
        "relative_times": list(DEFAULT_RELATIVE_TIMES),
        "candidates": [{**candidate, "systems": {}} for candidate in candidates],
    }
    _write_json(output, payload)
    systems = {h_chain: _prepare_system(h_chain) for h_chain in (2, 4, 5)}

    for candidate in payload["candidates"]:
        sequence = symmetric_s2_sequence(candidate["weights"])
        print(candidate["name"], flush=True)
        for h_chain, system in systems.items():
            started = time.perf_counter()
            fit = _custom_short_time_fit(system, sequence, DEFAULT_FIT_TIMES)
            record: dict[str, Any] = {
                "short_time_fit": fit,
                "predictability": None,
                "analysis_predictability_pass": {"passed": False},
            }
            candidate["systems"][f"H{h_chain}"] = record
            selected = fit["selected_window"]
            if selected is None:
                record["elapsed_seconds"] = float(time.perf_counter() - started)
                _write_json(output, payload)
                continue
            alpha = float(selected["fixed_order_alpha"])
            n_exp = int(DECOMPO_NUM[f"H{h_chain}"]["4th(m5_best)"])
            analytic_time = analytic_optimal_time(alpha, 4, TARGET_ERROR)
            model_cost = analytic_minimum_cost(
                BETA, n_exp, alpha, 4, TARGET_ERROR
            )
            points = _direct_custom_points(
                system,
                sequence,
                DEFAULT_RELATIVE_TIMES,
                alpha=alpha,
                analytic_time=analytic_time,
                n_exp=n_exp,
                epsilon_e=TARGET_ERROR,
            )
            metrics = sampled_predictability_metrics(
                points,
                analytic_model_cost=model_cost,
                formal_order=4,
                scale_tolerance=0.1,
                scale_interval=(0.3, 1.1),
                optimization_interval=(0.2, 1.4),
            )
            record.update(
                {
                    "analytic_optimal_time": analytic_time,
                    "analytic_model_cost": model_cost,
                    "direct_points": points,
                    "predictability": metrics,
                    "analysis_predictability_pass": _analysis_pass(fit, metrics),
                    "elapsed_seconds": float(time.perf_counter() - started),
                }
            )
            _write_json(output, payload)

    baseline = payload["candidates"][0]
    for candidate in payload["candidates"]:
        t_passes: list[float] = []
        cost_errors: list[float] = []
        cost_ratios: list[float] = []
        passed = 0
        for system_name, record in candidate["systems"].items():
            metrics = record["predictability"]
            if metrics is None:
                continue
            direct_minimum = float(metrics["sampled_direct_minimum"]["cost"])
            baseline_minimum = float(
                baseline["systems"][system_name]["predictability"][
                    "sampled_direct_minimum"
                ]["cost"]
            )
            ratio = direct_minimum / baseline_minimum
            record["direct_minimum_cost_over_m5"] = ratio
            t_passes.append(
                float(metrics["ten_percent_validity"]["t_pass_over_t_ana"])
            )
            cost_errors.append(
                float(
                    metrics["sampled_direct_minimum"][
                        "cost_prediction_relative_error"
                    ]
                )
            )
            cost_ratios.append(ratio)
            passed += int(record["analysis_predictability_pass"]["passed"])
        candidate["summary"] = {
            "num_systems": len(candidate["systems"]),
            "num_passed": passed,
            "worst_t_pass_over_t_ana": min(t_passes),
            "maximum_cost_prediction_error": max(cost_errors),
            "median_direct_minimum_cost_over_m5": float(np.median(cost_ratios)),
        }

    payload["status"] = "complete"
    _write_json(output, payload)
    _write_report(OUTPUT_DIR / "report.md", payload)
    print(f"saved: {OUTPUT_DIR}", flush=True)
    return payload


if __name__ == "__main__":
    run()
