"""Validate asymptotic PF cost rankings on directly solvable H chains.

The large-system estimate combines the number of Pauli rotations per PF step
with a short-time fixed-order error coefficient.  This script applies exactly
that workflow to H2/H4/H5 and compares the resulting analytic schedule and
cost with the ground-connected eigenphase obtained by direct sector
diagonalization at and around the analytic schedule.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from run_large_hchain_moment_phase import (
    _fit_short_time,
)
from sweep_direct_scaling_h6_h7 import _direct_point, _write_json
from trotterlib.config import BETA, DECOMPO_NUM
from trotterlib.cost_validation import analytic_optimal_time
from validate_hchain_perturbative_estimator import _prepare_sector_system


LABELS = (
    "2nd",
    "4th",
    "4th(m5_best)",
    "8th(Morales-Y8m10b)",
)
FIT_TIMES = {
    "2nd": tuple(np.geomspace(0.03, 0.40, 12)),
    "4th": tuple(np.geomspace(0.08, 0.80, 12)),
    "4th(m5_best)": tuple(np.geomspace(0.15, 0.80, 9)),
    "8th(Morales-Y8m10b)": tuple(np.geomspace(0.80, 1.60, 9)),
}
DEFAULT_RELATIVE_TIMES = (
    0.50,
    0.70,
    0.85,
    0.90,
    0.95,
    0.975,
    1.00,
    1.025,
    1.05,
    1.10,
    1.15,
)


def _analytic_cost(
    n_exp: int, alpha: float, order: int, epsilon_e: float
) -> float:
    time_opt = analytic_optimal_time(alpha, order, epsilon_e)
    return float(
        BETA
        * n_exp
        / (time_opt * (epsilon_e - alpha * time_opt**order))
    )


def _relative_difference(value: float, reference: float) -> float:
    return float(abs(value / reference - 1.0))


def _prepare_system(h_chain: int) -> dict[str, Any]:
    """Adapt the general invariant-sector builder to the sweep interface."""
    prepared = _prepare_sector_system(h_chain)
    return {
        "h_chain": h_chain,
        "ham_name": prepared["ham_name"],
        "num_qubits": prepared["num_qubits"],
        "num_groups": prepared["num_groups"],
        "energy": prepared["ground_energy_without_constant_hartree"],
        "state": prepared["ground_state"],
        "group_spectra": prepared["group_spectra"],
        "sector": prepared["sector"],
    }


def run(
    h_chains: list[int],
    relative_times: list[float],
    epsilon_e: float,
    min_fit_error: float,
    output: Path,
) -> dict[str, Any]:
    relative_grid = sorted({float(value) for value in relative_times})
    if 1.0 not in relative_grid:
        raise ValueError("relative time grid must include 1.0")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "purpose": (
            "Direct small-system validation of large-system asymptotic PF "
            "cost estimates, including the linear per-step gate-count factor"
        ),
        "epsilon_E_hartree": float(epsilon_e),
        "beta": float(BETA),
        "h_chains": h_chains,
        "excluded_systems": {
            "H3": (
                "The H3 input is now sector-corrected, but its short-time "
                "PF signal is below the double-precision fit floor."
            )
        },
        "relative_times": relative_grid,
        "results": {},
    }
    _write_json(output, payload)

    for h_chain in h_chains:
        system_started = time.perf_counter()
        print(f"prepare H{h_chain}", flush=True)
        system = _prepare_system(h_chain)
        formulas: dict[str, Any] = {}
        system_result: dict[str, Any] = {
            "system": {
                "h_chain": h_chain,
                "num_qubits": int(system["num_qubits"]),
                "num_groups": int(system["num_groups"]),
                "sector_dimension": int(system["sector"]["dimension"]),
                "ground_energy_without_constant_hartree": float(
                    system["energy"]
                ),
                "sector": system["sector"],
            },
            "formulas": formulas,
            "comparisons": {},
            "elapsed_seconds": None,
        }
        payload["results"][f"H{h_chain}"] = system_result
        _write_json(output, payload)

        for label in LABELS:
            print(f"H{h_chain}: fit {label}", flush=True)
            fit = _fit_short_time(
                system, label, FIT_TIMES[label], min_fit_error
            )
            order = int(fit["fixed_order"])
            alpha = float(fit["fixed_order_alpha"])
            alpha_effective = np.asarray(
                [
                    float(point["perturbative_error_hartree"])
                    / float(point["time"]) ** order
                    for point in fit["points"]
                    if float(point["perturbative_error_hartree"])
                    > min_fit_error
                ]
            )
            analytic_time = float(
                analytic_optimal_time(alpha, order, epsilon_e)
            )
            n_exp = int(DECOMPO_NUM[f"H{h_chain}"][label])
            model_cost = _analytic_cost(n_exp, alpha, order, epsilon_e)
            formula_result: dict[str, Any] = {
                "label": label,
                "formal_order": order,
                "pauli_rotations_per_step": n_exp,
                "short_time_fit": fit,
                "short_time_diagnostics": {
                    "free_order": float(fit["free_fit"]["order"]),
                    "free_fit_r2": float(fit["free_fit"]["r2"]),
                    "fixed_order_alpha": alpha,
                    "alpha_effective_min": float(np.min(alpha_effective)),
                    "alpha_effective_max": float(np.max(alpha_effective)),
                    "alpha_effective_max_over_min": float(
                        np.max(alpha_effective) / np.min(alpha_effective)
                    ),
                },
                "analytic_model": {
                    "time": analytic_time,
                    "error_hartree": float(
                        alpha * analytic_time**order
                    ),
                    "cost": model_cost,
                    "cost_per_pauli_rotation_factor": float(
                        model_cost / n_exp
                    ),
                },
                "direct_points": [],
            }
            formulas[label] = formula_result
            _write_json(output, payload)

            previous_vector: np.ndarray | None = None
            previous_shift: float | None = None
            for relative_time in relative_grid:
                evolution_time = relative_time * analytic_time
                model_error = alpha * evolution_time**order
                print(
                    f"H{h_chain} {label}: "
                    f"t/t_analytic={relative_time:g}",
                    flush=True,
                )
                point, previous_vector, previous_shift = _direct_point(
                    system,
                    label,
                    evolution_time,
                    model_error,
                    epsilon_e,
                    previous_vector,
                    previous_shift,
                )
                point["relative_to_analytic_time"] = relative_time
                formula_result["direct_points"].append(point)
                _write_json(output, payload)

            analytic_point = next(
                point
                for point in formula_result["direct_points"]
                if point["relative_to_analytic_time"] == 1.0
            )
            direct_branch = analytic_point["continuously_tracked_branch"]
            direct_cost = direct_branch["cost"]
            local_points = [
                point
                for point in formula_result["direct_points"]
                if 0.95 <= point["relative_to_analytic_time"] <= 1.05
            ]
            local_costs = [
                float(point["continuously_tracked_branch"]["cost"])
                for point in local_points
                if point["continuously_tracked_branch"]["cost"] is not None
            ]
            formula_result["direct_at_analytic_time"] = {
                "error_hartree": float(direct_branch["direct_error_hartree"]),
                "direct_to_model_error_ratio": float(
                    direct_branch["direct_to_model_ratio"]
                ),
                "cost": direct_cost,
                "direct_to_model_cost_ratio": (
                    None
                    if direct_cost is None
                    else float(direct_cost / model_cost)
                ),
                "ground_overlap_probability": float(
                    direct_branch["ground_overlap_probability"]
                ),
            }
            formula_result["local_schedule_sensitivity"] = {
                "relative_time_interval": [0.95, 1.05],
                "num_valid_costs": len(local_costs),
                "minimum_cost": min(local_costs) if local_costs else None,
                "median_cost": (
                    float(np.median(local_costs)) if local_costs else None
                ),
                "maximum_cost": max(local_costs) if local_costs else None,
                "max_over_min": (
                    float(max(local_costs) / min(local_costs))
                    if local_costs
                    else None
                ),
            }
            valid_grid_costs = [
                (
                    float(point["continuously_tracked_branch"]["cost"]),
                    float(point["relative_to_analytic_time"]),
                )
                for point in formula_result["direct_points"]
                if point["continuously_tracked_branch"]["cost"] is not None
            ]
            grid_minimum = min(valid_grid_costs)
            formula_result["direct_grid_minimum"] = {
                "cost": grid_minimum[0],
                "relative_time": grid_minimum[1],
            }
            _write_json(output, payload)

        model_order = sorted(
            LABELS, key=lambda label: formulas[label]["analytic_model"]["cost"]
        )
        valid_direct_labels = [
            label
            for label in LABELS
            if formulas[label]["direct_at_analytic_time"]["cost"] is not None
        ]
        direct_order = sorted(
            valid_direct_labels,
            key=lambda label: formulas[label]["direct_at_analytic_time"][
                "cost"
            ],
        )
        reference = "4th(m5_best)"
        pairwise: dict[str, Any] = {}
        for label in LABELS:
            if label == reference:
                continue
            target = formulas[label]
            base = formulas[reference]
            gate_ratio = float(
                target["pauli_rotations_per_step"]
                / base["pauli_rotations_per_step"]
            )
            non_gate_ratio = float(
                target["analytic_model"]["cost_per_pauli_rotation_factor"]
                / base["analytic_model"]["cost_per_pauli_rotation_factor"]
            )
            model_ratio = float(
                target["analytic_model"]["cost"]
                / base["analytic_model"]["cost"]
            )
            target_direct = target["direct_at_analytic_time"]["cost"]
            base_direct = base["direct_at_analytic_time"]["cost"]
            direct_ratio = (
                None
                if target_direct is None or base_direct is None
                else float(target_direct / base_direct)
            )
            pairwise[f"{label} / {reference}"] = {
                "gate_count_ratio": gate_ratio,
                "error_order_and_schedule_factor_ratio": non_gate_ratio,
                "analytic_model_cost_ratio": model_ratio,
                "factorization_residual": float(
                    model_ratio / (gate_ratio * non_gate_ratio) - 1.0
                ),
                "direct_cost_ratio_at_respective_analytic_times": direct_ratio,
                "direct_ratio_relative_difference_from_model": (
                    None
                    if direct_ratio is None
                    else _relative_difference(direct_ratio, model_ratio)
                ),
                "ranking_agrees": (
                    None
                    if direct_ratio is None
                    else bool((model_ratio < 1.0) == (direct_ratio < 1.0))
                ),
            }
        system_result["comparisons"] = {
            "analytic_model_ranking_best_to_worst": model_order,
            "direct_at_analytic_times_ranking_best_to_worst": direct_order,
            "rankings_identical": model_order == direct_order,
            "pairwise_against_m5": pairwise,
        }
        system_result["elapsed_seconds"] = float(
            time.perf_counter() - system_started
        )
        _write_json(output, payload)

    payload["status"] = "complete"
    _write_json(output, payload)
    print(f"saved: {output}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-chains", nargs="+", type=int, default=[2, 4, 5])
    parser.add_argument(
        "--relative-times",
        nargs="+",
        type=float,
        default=list(DEFAULT_RELATIVE_TIMES),
    )
    parser.add_argument(
        "--epsilon-e", type=float, default=0.00015936001019904
    )
    parser.add_argument("--min-fit-error", type=float, default=5e-12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/server_cost_validity/"
            "asymptotic_cost_small_system_validation.json"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        args.h_chains,
        args.relative_times,
        args.epsilon_e,
        args.min_fit_error,
        args.output,
    )


if __name__ == "__main__":
    main()
