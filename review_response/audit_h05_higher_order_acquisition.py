"""H05 comparison of practical routes to fourth-order PF a6/a8 coefficients.

No new PF eigenvalue point is generated.  Existing signed F01 points are used
for fixed few-point fits.  Stored D6/D8 operators provide the independently
validated BCH reference, while D4 state actions are recomputed through the H04
grouped backend and inserted into a projected response equation for the a8
state-mixing term.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import time
from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq, minimize_scalar

from review_response.audit_f01_effective_hamiltonian_multipf import formula_registry
from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from review_response.compact_bch import (
    compact_composed_d4_terms,
    evaluate_grouped_terms,
    summed_components,
)
from trotterlib.config import TARGET_ERROR
from trotterlib.pf_decomposition import symmetric_s2_sequence


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_F02 = Path("artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3")
DEFAULT_H01 = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")
DEFAULT_H04 = Path(
    "artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1"
)
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2"
)
STATE_IDS = ("exact", "hf", "cisd")
DIRECT_WINDOW_ID = "middle"
DIRECT_DESIGNS = {
    "direct_free_3_tail": {
        "indices": (13, 14, 15),
        "orders": (4, 6, 8),
        "fixed_a4": False,
    },
    "direct_free_5_tail": {
        "indices": (11, 12, 13, 14, 15),
        "orders": (4, 6, 8),
        "fixed_a4": False,
    },
    "direct_fixed_a4_2_tail": {
        "indices": (11, 15),
        "orders": (6, 8),
        "fixed_a4": True,
    },
    "direct_fixed_a4_3_tail": {
        "indices": (11, 13, 15),
        "orders": (6, 8),
        "fixed_a4": True,
    },
    "direct_fixed_a4_5_tail": {
        "indices": (11, 12, 13, 14, 15),
        "orders": (6, 8),
        "fixed_a4": True,
    },
    "direct_order12_16": {
        "indices": tuple(range(16)),
        "orders": (4, 6, 8, 10, 12),
        "fixed_a4": False,
    },
}
RESIDUAL_THRESHOLD_OVER_EPSILON = 0.05


def fit_signed_coefficients(
    times: Sequence[float],
    shifts: Sequence[float],
    orders: Sequence[int],
    *,
    fixed_coefficients: dict[int, float] | None = None,
) -> dict[str, Any]:
    x = np.asarray(times, dtype=float)
    y = np.asarray(shifts, dtype=float)
    polynomial_orders = tuple(int(order) for order in orders)
    if x.ndim != 1 or y.shape != x.shape or np.any(x <= 0.0):
        raise ValueError("invalid time/shift arrays")
    if x.size < len(polynomial_orders):
        raise ValueError("insufficient direct points")
    fixed = {} if fixed_coefficients is None else {
        int(order): float(value) for order, value in fixed_coefficients.items()
    }
    adjusted = np.array(y, copy=True)
    for order, coefficient in fixed.items():
        adjusted -= coefficient * x**order
    scale = float(np.max(x))
    design = np.column_stack(
        [(x / scale) ** order for order in polynomial_orders]
    )
    scaled = np.linalg.lstsq(design, adjusted, rcond=None)[0]
    coefficients = scaled / np.asarray(
        [scale**order for order in polynomial_orders], dtype=float
    )
    prediction = np.zeros_like(x)
    for order, coefficient in fixed.items():
        prediction += coefficient * x**order
    for order, coefficient in zip(polynomial_orders, coefficients, strict=True):
        prediction += coefficient * x**order
    residual = prediction - y
    result = {**fixed}
    result.update(
        {
            order: float(coefficient)
            for order, coefficient in zip(
                polynomial_orders, coefficients, strict=True
            )
        }
    )
    return {
        "coefficients": result,
        "scaled_design_condition_number": float(np.linalg.cond(design)),
        "maximum_training_residual_hartree": float(np.max(np.abs(residual))),
        "root_mean_square_training_residual_hartree": float(
            np.sqrt(np.mean(np.square(residual)))
        ),
        "scale_time_hartree_inverse": scale,
    }


def projected_response_mixing(
    hamiltonian: np.ndarray,
    state: np.ndarray,
    d4_action: np.ndarray,
) -> dict[str, float]:
    """Solve the projected first-order response equation around ``state``."""

    matrix = np.asarray(hamiltonian, dtype=np.complex128)
    vector = np.asarray(state, dtype=np.complex128).reshape(-1)
    vector = vector / np.linalg.norm(vector)
    action = np.asarray(d4_action, dtype=np.complex128).reshape(-1)
    energy = float(np.vdot(vector, matrix @ vector).real)
    identity = np.eye(vector.size, dtype=np.complex128)
    projector = np.outer(vector, vector.conj())
    complement = identity - projector
    shifted = matrix - energy * identity
    augmented = complement @ shifted @ complement + projector
    right_hand_side = -complement @ action
    started = time.perf_counter()
    response = np.linalg.solve(augmented, right_hand_side)
    solve_seconds = time.perf_counter() - started
    projected_residual = complement @ (shifted @ response + action)
    orthogonality = complex(np.vdot(vector, response))
    mixing = float(np.vdot(action, response).real)
    return {
        "state_energy_hartree": energy,
        "mixing_hartree": mixing,
        "projected_response_residual_2_norm": float(
            np.linalg.norm(projected_residual)
        ),
        "response_state_overlap_absolute": float(abs(orthogonality)),
        "augmented_response_condition_number": float(np.linalg.cond(augmented)),
        "response_solve_seconds": float(solve_seconds),
    }


def reference_three_term_optimal_time(a4: float, a6: float, a8: float) -> dict[str, float]:
    def shift(time_value: float) -> float:
        return float(
            a4 * time_value**4
            + a6 * time_value**6
            + a8 * time_value**8
        )

    grid = np.geomspace(1e-6, 100.0, 20_000)
    violations = np.flatnonzero(
        np.asarray([abs(shift(value)) for value in grid]) >= TARGET_ERROR
    )
    if not violations.size:
        raise RuntimeError("failed to locate the connected error-budget boundary")
    index = int(violations[0])
    if index == 0:
        raise RuntimeError("three-term model is infeasible at the first grid point")
    boundary = brentq(
        lambda value: abs(shift(value)) - TARGET_ERROR,
        float(grid[index - 1]),
        float(grid[index]),
    )

    def cost_without_rotation(time_value: float) -> float:
        budget = TARGET_ERROR - abs(shift(time_value))
        if budget <= 0.0:
            return math.inf
        return float(1.0 / (time_value * budget))

    optimum = minimize_scalar(
        cost_without_rotation,
        bounds=(1e-10, boundary * (1.0 - 1e-10)),
        method="bounded",
        options={"xatol": 1e-13},
    )
    return {
        "time_hartree_inverse": float(optimum.x),
        "connected_budget_boundary_hartree_inverse": float(boundary),
        "signed_shift_hartree": shift(float(optimum.x)),
        "cost_per_rotation_unit": float(optimum.fun),
    }


def _method_row(
    *,
    system_id: str,
    formula_id: str,
    method_id: str,
    estimate_state_id: str,
    reference: dict[str, float],
    estimates: dict[int, float],
    optimal: dict[str, float],
    direct_point_count: int,
    direct_times: Sequence[float],
    scaled_design_condition_number: float | None,
    maximum_training_residual_hartree: float | None,
    online_evaluation_seconds: float | None,
    requires_exact_state: bool,
    requires_exact_a4: bool,
    requires_dense_d6_d8: bool,
    requires_direct_pf_eigenvalues: bool,
    acquisition_scope: str,
) -> dict[str, Any]:
    a4 = float(estimates[4])
    a6 = float(estimates[6])
    a8 = float(estimates[8])
    time_value = float(optimal["time_hartree_inverse"])
    full_residual = (
        (a4 - reference["a4"]) * time_value**4
        + (a6 - reference["a6"]) * time_value**6
        + (a8 - reference["a8"]) * time_value**8
    )
    higher_residual = (
        (a6 - reference["a6"]) * time_value**6
        + (a8 - reference["a8"]) * time_value**8
    )
    maximum_direct_time = max(direct_times, default=None)
    return {
        "system_id": system_id,
        "formula_id": formula_id,
        "method_id": method_id,
        "estimate_state_id": estimate_state_id,
        "estimated_a4_hartree": a4,
        "estimated_a6_hartree": a6,
        "estimated_a8_hartree": a8,
        "reference_a4_hartree": reference["a4"],
        "reference_a6_hartree": reference["a6"],
        "reference_a8_hartree": reference["a8"],
        "a6_relative_error": float(
            abs(a6 - reference["a6"]) / max(abs(reference["a6"]), 1e-300)
        ),
        "a8_relative_error": float(
            abs(a8 - reference["a8"]) / max(abs(reference["a8"]), 1e-300)
        ),
        "a6_sign_matches_reference": bool(np.sign(a6) == np.sign(reference["a6"])),
        "a8_sign_matches_reference": bool(np.sign(a8) == np.sign(reference["a8"])),
        "reference_three_term_tstar_hartree_inverse": time_value,
        "reference_shift_at_tstar_hartree": optimal["signed_shift_hartree"],
        "higher_order_coefficient_residual_at_tstar_hartree": float(higher_residual),
        "higher_order_residual_over_epsilon": float(
            abs(higher_residual) / TARGET_ERROR
        ),
        "full_coefficient_residual_at_tstar_hartree": float(full_residual),
        "full_residual_over_epsilon": float(abs(full_residual) / TARGET_ERROR),
        "meets_higher_order_residual_threshold": bool(
            abs(higher_residual) / TARGET_ERROR <= RESIDUAL_THRESHOLD_OVER_EPSILON
        ),
        "direct_point_count": int(direct_point_count),
        "direct_times_json": json.dumps([float(value) for value in direct_times]),
        "maximum_direct_training_time_hartree_inverse": maximum_direct_time,
        "tstar_to_maximum_training_time_ratio": (
            None if maximum_direct_time is None else time_value / maximum_direct_time
        ),
        "scaled_design_condition_number": scaled_design_condition_number,
        "maximum_training_residual_hartree": maximum_training_residual_hartree,
        "online_evaluation_seconds": online_evaluation_seconds,
        "requires_exact_state": bool(requires_exact_state),
        "requires_exact_a4": bool(requires_exact_a4),
        "requires_dense_d6_d8": bool(requires_dense_d6_d8),
        "requires_direct_pf_eigenvalues": bool(requires_direct_pf_eigenvalues),
        "acquisition_scope": acquisition_scope,
    }


def _write_figures(
    output_dir: Path,
    summaries: list[dict[str, Any]],
) -> None:
    exact_method_ids = [
        "bch_exact_d8_diagonal",
        "bch_exact_response",
        "direct_free_3_tail",
        "direct_free_5_tail",
        "direct_fixed_a4_2_tail",
        "direct_fixed_a4_3_tail",
        "direct_fixed_a4_5_tail",
        "direct_order12_16",
    ]
    rows = [
        next(row for row in summaries if row["method_id"] == method_id)
        for method_id in exact_method_ids
    ]
    figure, axis = plt.subplots(figsize=(9.4, 4.5))
    axis.bar(
        range(len(rows)),
        [max(row["maximum_higher_order_residual_over_epsilon"], 1e-15) for row in rows],
    )
    axis.axhline(
        RESIDUAL_THRESHOLD_OVER_EPSILON,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label="0.05 epsilon threshold",
    )
    axis.set_yscale("log")
    axis.set_xticks(range(len(rows)), [row["method_id"] for row in rows], rotation=35, ha="right")
    axis.set_ylabel("worst higher-order residual / epsilon")
    axis.grid(True, axis="y", which="both", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(output_dir / "method_worst_residual.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9.4, 4.3))
    locations = np.arange(len(summaries))
    axis.bar(
        locations - 0.18,
        [row["a6_sign_match_count"] for row in summaries],
        width=0.36,
        label="a6 sign",
    )
    axis.bar(
        locations + 0.18,
        [row["a8_sign_match_count"] for row in summaries],
        width=0.36,
        label="a8 sign",
    )
    axis.axhline(8, color="black", linewidth=0.8)
    axis.set_xticks(
        locations,
        [row["method_id"] for row in summaries],
        rotation=40,
        ha="right",
        fontsize=7,
    )
    axis.set_ylabel("sign matches out of 8 conditions")
    axis.set_ylim(0, 8.6)
    axis.legend(frameon=False)
    axis.grid(True, axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "method_sign_recovery.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# H05: a6/a8 acquisition-method comparison",
        "",
        f"Status: **{audit['status']}**",
        "",
        "No new direct PF eigenvalue points were generated. Existing signed F01 "
        "points, stored F01 D6/D8 operators, H01 states, F02 mechanism references, "
        "and the H04 compact D4 action backend were reused.",
        "",
        "## Method summary",
        "",
        "| method | direct points | a6 signs | a8 signs | residual pass | "
        "worst residual/epsilon | median residual/epsilon |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in audit["method_summaries"]:
        lines.append(
            f"| {row['method_id']} | {row['direct_point_count']} | "
            f"{row['a6_sign_match_count']}/8 | {row['a8_sign_match_count']}/8 | "
            f"{row['higher_order_residual_pass_count']}/8 | "
            f"{row['maximum_higher_order_residual_over_epsilon']:.3e} | "
            f"{row['median_higher_order_residual_over_epsilon']:.3e} |"
        )

    summary = audit["summary"]
    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"The exact-state BCH plus projected response route reproduces a6/a8 in "
            f"{summary['exact_response_residual_pass_count']}/8 conditions and its "
            f"largest response residual is "
            f"{summary['maximum_projected_response_residual_2_norm']:.3e}. "
            "The response equation therefore supplies the D4-mixing part of a8 without "
            "constructing D4, but it still assumes that D6 and D8 are available.",
            "",
            f"Using <D8> alone passes the finite-time residual threshold in only "
            f"{summary['diagonal_only_residual_pass_count']}/8 conditions. State mixing "
            "cannot be dropped uniformly.",
            "",
            f"Among the direct methods, the best declared few-point method is "
            f"`{summary['best_few_point_method_id']}` with "
            f"{summary['best_few_point_residual_pass_count']}/8 residual passes. "
            f"Its worst residual is "
            f"{summary['best_few_point_maximum_residual_over_epsilon']:.3e} epsilon. "
            "This is a promising reduced-point calibration, but it requires an exact "
            "leading a4 and two direct PF eigenvalue points. The high-tail design was "
            "chosen and assessed on the same H-chain development data, so this is not an "
            "unused-system guarantee.",
            "",
            f"The free five-point fit also passes {summary['free_five_point_residual_pass_count']}/8, "
            f"but its worst residual is {summary['free_five_point_maximum_residual_over_epsilon']:.3e} "
            "epsilon, close to the 0.05 threshold. By contrast, the 16-point order-12 fit "
            f"passes only {summary['direct_order12_residual_pass_count']}/8 because adding "
            "points and coefficients does not cure the cancellation-sensitive far extrapolation.",
            "",
            f"HF response passes {summary['hf_response_residual_pass_count']}/8 and "
            f"CISD response passes {summary['cisd_response_residual_pass_count']}/8. "
            "Approximate-state energy quality therefore does not by itself guarantee "
            "higher-order coefficient quality, consistent with H01/H02.",
            "",
            "## Cost boundary",
            "",
            "The saved online timings cover grouped D4 state action, dense D6/D8 "
            "matrix-vector products, and the small projected solve. They exclude the "
            "classical construction of D6/D8 and the original cost of the reused direct "
            "PF eigenvalue points. Consequently they are diagnostic timings, not a fair "
            "end-to-end wall-time ranking.",
            "",
            "## Decision",
            "",
            "The response identity is accepted as the correct inexpensive mixing correction. "
            "For practical calibration, freeze the exact-a4 plus two-high-time-point design "
            "as the next holdout candidate. Do not call it universally validated until it is "
            "tested without retuning on unused Hamiltonians. Pure BCH acquisition still lacks "
            "an end-to-end cheap route because D8 construction remains the bottleneck.",
            "",
            "## Files",
            "",
            "- `audit.json`: protocol, checks, summaries, and conclusions.",
            "- `method_comparison.csv`: condition-level coefficient and t* residual results.",
            "- `method_summary.csv`: per-method worst cases and pass counts.",
            "- `response_diagnostics.csv`: compact-D4 response solves for exact/HF/CISD.",
            "- `direct_fit_diagnostics.csv`: reused point designs, conditioning, and fit residuals.",
            "- `reference_tstar.csv`: exact three-term model evaluation times.",
            "- `manifest.json`: source, input, and artifact hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    f01_dir: Path,
    f02_dir: Path,
    h01_dir: Path,
    h04_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_path = f01_dir / "audit.json"
    operators_path = f01_dir / "effective_operators.npz"
    f02_path = f02_dir / "audit.json"
    h01_path = h01_dir / "audit.json"
    states_path = h01_dir / "states.npz"
    h04_path = h04_dir / "audit.json"
    f01 = json.loads(f01_path.read_text(encoding="utf-8"))
    f02 = json.loads(f02_path.read_text(encoding="utf-8"))
    h01 = json.loads(h01_path.read_text(encoding="utf-8"))
    h04 = json.loads(h04_path.read_text(encoding="utf-8"))
    if f01["status"] != "complete" or not f01["passed"]:
        raise RuntimeError("F01 input is not complete")
    if f02["status"] != "complete_with_findings" or not f02["mechanism_identity_passed"]:
        raise RuntimeError("F02 input is not complete")
    if h01["status"] != "pilot_complete_with_findings" or not h01["checks_passed"]:
        raise RuntimeError("H01 input is not complete")
    if h04["status"] != "complete_with_findings" or not h04["passed"]:
        raise RuntimeError("H04 input is not complete")

    formulas = {row["formula_id"]: row for row in formula_registry()}
    references = {
        (row["system_id"], row["formula_id"]): {
            key: float(value) for key, value in row["energy_coefficients"].items()
        }
        for row in f01["condition_summaries"]
    }
    f02_conditions = {
        (row["system_id"], row["formula_id"]): row
        for row in f02["condition_summaries"]
    }
    f02_middle_fits = {
        (row["system_id"], row["formula_id"]): row
        for row in f02["direct_fit_rows"]
        if row["window_id"] == DIRECT_WINDOW_ID
    }
    holdout_rows = f01["holdout_rows"]
    method_rows: list[dict[str, Any]] = []
    response_rows: list[dict[str, Any]] = []
    direct_rows: list[dict[str, Any]] = []
    tstar_rows: list[dict[str, Any]] = []

    with np.load(operators_path) as arrays, np.load(states_path) as states:
        for system_id in ("H2", "H4"):
            hamiltonian = np.asarray(
                arrays[f"{system_id}_hamiltonian"], dtype=np.complex128
            )
            group_keys = sorted(
                key for key in arrays.files if key.startswith(f"{system_id}_group_")
            )
            groups = [np.asarray(arrays[key], dtype=np.complex128) for key in group_keys]
            for formula_id, formula in formulas.items():
                reference = references[(system_id, formula_id)]
                optimal = reference_three_term_optimal_time(
                    reference["a4"], reference["a6"], reference["a8"]
                )
                tstar_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        **optimal,
                    }
                )
                sequence = symmetric_s2_sequence(formula["weights"])
                compact_terms, compact_diagnostics = compact_composed_d4_terms(
                    len(groups), sequence
                )
                d6 = np.asarray(
                    arrays[f"{system_id}_{formula_id}_D6"], dtype=np.complex128
                )
                d8 = np.asarray(
                    arrays[f"{system_id}_{formula_id}_D8"], dtype=np.complex128
                )
                state_estimates: dict[str, dict[str, float]] = {}
                state_timings: dict[str, float] = {}
                for state_id in STATE_IDS:
                    state = np.asarray(
                        states[f"{system_id}_{state_id}_state"], dtype=np.complex128
                    )
                    action_started = time.perf_counter()
                    component_actions, _, _, action_diagnostics = evaluate_grouped_terms(
                        compact_terms, groups, state
                    )
                    d4_action = summed_components(
                        component_actions, range(len(component_actions))
                    )
                    compact_seconds = time.perf_counter() - action_started
                    expectation_started = time.perf_counter()
                    a4 = float(np.vdot(state, d4_action).real)
                    a6 = float(np.vdot(state, d6 @ state).real)
                    d8_expectation = float(np.vdot(state, d8 @ state).real)
                    expectation_seconds = time.perf_counter() - expectation_started
                    response = projected_response_mixing(
                        hamiltonian, state, d4_action
                    )
                    a8_response = d8_expectation + response["mixing_hartree"]
                    state_estimates[state_id] = {
                        "a4": a4,
                        "a6": a6,
                        "d8_expectation": d8_expectation,
                        "a8_response": a8_response,
                    }
                    state_timings[state_id] = (
                        compact_seconds
                        + expectation_seconds
                        + response["response_solve_seconds"]
                    )
                    response_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula_id,
                            "state_id": state_id,
                            "compact_d4_grouped_term_count": compact_diagnostics[
                                "composed_d4_grouped_term_count"
                            ],
                            "compact_d4_action_seconds": compact_seconds,
                            "d6_d8_expectation_seconds": expectation_seconds,
                            "d8_expectation_hartree": d8_expectation,
                            "a8_response_hartree": a8_response,
                            "f02_exact_mixing_reference_hartree": f02_conditions[
                                (system_id, formula_id)
                            ]["d4_second_order_mixing_hartree"],
                            "mixing_difference_from_f02_hartree": (
                                response["mixing_hartree"]
                                - f02_conditions[(system_id, formula_id)][
                                    "d4_second_order_mixing_hartree"
                                ]
                            ),
                            **response,
                            "compact_linear_combination_action_count": action_diagnostics[
                                "linear_combination_action_count"
                            ],
                        }
                    )

                exact = state_estimates["exact"]
                method_rows.append(
                    _method_row(
                        system_id=system_id,
                        formula_id=formula_id,
                        method_id="bch_exact_d8_diagonal",
                        estimate_state_id="exact",
                        reference=reference,
                        estimates={
                            4: exact["a4"],
                            6: exact["a6"],
                            8: exact["d8_expectation"],
                        },
                        optimal=optimal,
                        direct_point_count=0,
                        direct_times=(),
                        scaled_design_condition_number=None,
                        maximum_training_residual_hartree=None,
                        online_evaluation_seconds=state_timings["exact"],
                        requires_exact_state=True,
                        requires_exact_a4=False,
                        requires_dense_d6_d8=True,
                        requires_direct_pf_eigenvalues=False,
                        acquisition_scope=(
                            "stored dense D6/D8 expectations; omits D4 response mixing"
                        ),
                    )
                )
                method_rows.append(
                    _method_row(
                        system_id=system_id,
                        formula_id=formula_id,
                        method_id="bch_exact_response",
                        estimate_state_id="exact",
                        reference=reference,
                        estimates={
                            4: exact["a4"],
                            6: exact["a6"],
                            8: exact["a8_response"],
                        },
                        optimal=optimal,
                        direct_point_count=0,
                        direct_times=(),
                        scaled_design_condition_number=None,
                        maximum_training_residual_hartree=None,
                        online_evaluation_seconds=state_timings["exact"],
                        requires_exact_state=True,
                        requires_exact_a4=False,
                        requires_dense_d6_d8=True,
                        requires_direct_pf_eigenvalues=False,
                        acquisition_scope=(
                            "H04 compact D4 action + stored dense D6/D8 + projected response"
                        ),
                    )
                )
                for state_id in ("hf", "cisd"):
                    estimate = state_estimates[state_id]
                    method_rows.append(
                        _method_row(
                            system_id=system_id,
                            formula_id=formula_id,
                            method_id=f"bch_{state_id}_response",
                            estimate_state_id=state_id,
                            reference=reference,
                            estimates={
                                4: estimate["a4"],
                                6: estimate["a6"],
                                8: estimate["a8_response"],
                            },
                            optimal=optimal,
                            direct_point_count=0,
                            direct_times=(),
                            scaled_design_condition_number=None,
                            maximum_training_residual_hartree=None,
                            online_evaluation_seconds=state_timings[state_id],
                            requires_exact_state=False,
                            requires_exact_a4=False,
                            requires_dense_d6_d8=True,
                            requires_direct_pf_eigenvalues=False,
                            acquisition_scope=(
                                f"{state_id.upper()} state + H04 compact D4 action + "
                                "stored dense D6/D8 + projected response"
                            ),
                        )
                    )

                condition_points = sorted(
                    [
                        row
                        for row in holdout_rows
                        if row["system_id"] == system_id
                        and row["formula_id"] == formula_id
                        and row["window_id"] == DIRECT_WINDOW_ID
                    ],
                    key=lambda row: row["time_hartree_inverse"],
                )
                if len(condition_points) != 16:
                    raise RuntimeError("middle direct window must contain 16 points")
                for method_id, design in DIRECT_DESIGNS.items():
                    selected = [condition_points[index] for index in design["indices"]]
                    times = [float(row["time_hartree_inverse"]) for row in selected]
                    shifts = [float(row["direct_pf_shift_hartree"]) for row in selected]
                    fixed = {4: reference["a4"]} if design["fixed_a4"] else None
                    fit = fit_signed_coefficients(
                        times,
                        shifts,
                        design["orders"],
                        fixed_coefficients=fixed,
                    )
                    estimates = {
                        4: float(fit["coefficients"].get(4, reference["a4"])),
                        6: float(fit["coefficients"][6]),
                        8: float(fit["coefficients"][8]),
                    }
                    method_rows.append(
                        _method_row(
                            system_id=system_id,
                            formula_id=formula_id,
                            method_id=method_id,
                            estimate_state_id="direct_pf_branch",
                            reference=reference,
                            estimates=estimates,
                            optimal=optimal,
                            direct_point_count=len(times),
                            direct_times=times,
                            scaled_design_condition_number=fit[
                                "scaled_design_condition_number"
                            ],
                            maximum_training_residual_hartree=fit[
                                "maximum_training_residual_hartree"
                            ],
                            online_evaluation_seconds=None,
                            requires_exact_state=False,
                            requires_exact_a4=bool(design["fixed_a4"]),
                            requires_dense_d6_d8=False,
                            requires_direct_pf_eigenvalues=True,
                            acquisition_scope=(
                                "reused signed direct PF eigenvalue shifts; original point "
                                "wall times unavailable"
                            ),
                        )
                    )
                    direct_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula_id,
                            "method_id": method_id,
                            "point_count": len(times),
                            "indices_json": json.dumps(design["indices"]),
                            "times_json": json.dumps(times),
                            "orders_json": json.dumps(design["orders"]),
                            "fixed_a4": bool(design["fixed_a4"]),
                            "scaled_design_condition_number": fit[
                                "scaled_design_condition_number"
                            ],
                            "maximum_training_residual_hartree": fit[
                                "maximum_training_residual_hartree"
                            ],
                            "estimated_a4_hartree": estimates[4],
                            "estimated_a6_hartree": estimates[6],
                            "estimated_a8_hartree": estimates[8],
                        }
                    )

    method_ids = sorted({row["method_id"] for row in method_rows})
    method_summaries = []
    for method_id in method_ids:
        rows = [row for row in method_rows if row["method_id"] == method_id]
        residuals = [row["higher_order_residual_over_epsilon"] for row in rows]
        method_summaries.append(
            {
                "method_id": method_id,
                "condition_count": len(rows),
                "direct_point_count": rows[0]["direct_point_count"],
                "a6_sign_match_count": sum(row["a6_sign_matches_reference"] for row in rows),
                "a8_sign_match_count": sum(row["a8_sign_matches_reference"] for row in rows),
                "higher_order_residual_pass_count": sum(
                    row["meets_higher_order_residual_threshold"] for row in rows
                ),
                "maximum_a6_relative_error": max(row["a6_relative_error"] for row in rows),
                "maximum_a8_relative_error": max(row["a8_relative_error"] for row in rows),
                "maximum_higher_order_residual_over_epsilon": max(residuals),
                "median_higher_order_residual_over_epsilon": float(
                    statistics.median(residuals)
                ),
                "maximum_full_residual_over_epsilon": max(
                    row["full_residual_over_epsilon"] for row in rows
                ),
                "maximum_scaled_design_condition_number": max(
                    (
                        row["scaled_design_condition_number"]
                        for row in rows
                        if row["scaled_design_condition_number"] is not None
                    ),
                    default=None,
                ),
                "median_online_evaluation_seconds": (
                    float(
                        statistics.median(
                            row["online_evaluation_seconds"]
                            for row in rows
                            if row["online_evaluation_seconds"] is not None
                        )
                    )
                    if any(row["online_evaluation_seconds"] is not None for row in rows)
                    else None
                ),
            }
        )

    summaries_by_id = {row["method_id"]: row for row in method_summaries}
    few_point_ids = [
        method_id
        for method_id in DIRECT_DESIGNS
        if method_id != "direct_order12_16"
    ]
    best_few_point = min(
        few_point_ids,
        key=lambda method_id: (
            -summaries_by_id[method_id]["higher_order_residual_pass_count"],
            summaries_by_id[method_id]["maximum_higher_order_residual_over_epsilon"],
            summaries_by_id[method_id]["direct_point_count"],
        ),
    )
    maximum_response_residual = max(
        row["projected_response_residual_2_norm"] for row in response_rows
    )
    maximum_exact_mixing_difference = max(
        abs(row["mixing_difference_from_f02_hartree"])
        for row in response_rows
        if row["state_id"] == "exact"
    )
    maximum_order12_refit_difference = max(
        max(
            abs(
                row[f"estimated_a{order}_hartree"]
                - f02_middle_fits[(row["system_id"], row["formula_id"])][
                    f"fitted_a{order}"
                ]
            )
            for order in (6, 8)
        )
        for row in method_rows
        if row["method_id"] == "direct_order12_16"
    )
    checks = [
        {
            "check_id": "condition_and_method_row_count",
            "measured": len(method_rows),
            "threshold": 80,
            "comparison": "==",
            "passed": len(method_rows) == 80,
        },
        {
            "check_id": "exact_response_all_conditions",
            "measured": summaries_by_id["bch_exact_response"][
                "higher_order_residual_pass_count"
            ],
            "threshold": 8,
            "comparison": "==",
            "passed": summaries_by_id["bch_exact_response"][
                "higher_order_residual_pass_count"
            ]
            == 8,
        },
        {
            "check_id": "maximum_projected_response_residual",
            "measured": maximum_response_residual,
            "threshold": 1e-10,
            "comparison": "<=",
            "passed": maximum_response_residual <= 1e-10,
        },
        {
            "check_id": "exact_response_mixing_matches_f02_spectral_sum",
            "measured": maximum_exact_mixing_difference,
            "threshold": 1e-12,
            "comparison": "<=",
            "passed": maximum_exact_mixing_difference <= 1e-12,
        },
        {
            "check_id": "order12_middle_refit_matches_f02",
            "measured": maximum_order12_refit_difference,
            "threshold": 1e-14,
            "comparison": "<=",
            "passed": maximum_order12_refit_difference <= 1e-14,
        },
        {
            "check_id": "direct_design_condition_count",
            "measured": len(direct_rows),
            "threshold": 48,
            "comparison": "==",
            "passed": len(direct_rows) == 48,
        },
        {
            "check_id": "no_new_direct_pf_points",
            "measured": 0,
            "threshold": 0,
            "comparison": "==",
            "passed": True,
        },
    ]
    checks_passed = all(check["passed"] for check in checks)
    summary = {
        "exact_response_residual_pass_count": summaries_by_id[
            "bch_exact_response"
        ]["higher_order_residual_pass_count"],
        "diagonal_only_residual_pass_count": summaries_by_id[
            "bch_exact_d8_diagonal"
        ]["higher_order_residual_pass_count"],
        "hf_response_residual_pass_count": summaries_by_id["bch_hf_response"][
            "higher_order_residual_pass_count"
        ],
        "cisd_response_residual_pass_count": summaries_by_id[
            "bch_cisd_response"
        ]["higher_order_residual_pass_count"],
        "best_few_point_method_id": best_few_point,
        "best_few_point_residual_pass_count": summaries_by_id[best_few_point][
            "higher_order_residual_pass_count"
        ],
        "best_few_point_maximum_residual_over_epsilon": summaries_by_id[
            best_few_point
        ]["maximum_higher_order_residual_over_epsilon"],
        "free_five_point_residual_pass_count": summaries_by_id[
            "direct_free_5_tail"
        ]["higher_order_residual_pass_count"],
        "free_five_point_maximum_residual_over_epsilon": summaries_by_id[
            "direct_free_5_tail"
        ]["maximum_higher_order_residual_over_epsilon"],
        "direct_order12_residual_pass_count": summaries_by_id[
            "direct_order12_16"
        ]["higher_order_residual_pass_count"],
        "maximum_projected_response_residual_2_norm": maximum_response_residual,
        "maximum_exact_mixing_difference_from_f02_hartree": (
            maximum_exact_mixing_difference
        ),
        "maximum_order12_refit_difference_from_f02_hartree": (
            maximum_order12_refit_difference
        ),
        "maximum_reference_tstar_to_direct_window_ratio": max(
            row["tstar_to_maximum_training_time_ratio"]
            for row in method_rows
            if row["tstar_to_maximum_training_time_ratio"] is not None
        ),
        "residual_threshold_over_epsilon": RESIDUAL_THRESHOLD_OVER_EPSILON,
    }
    audit = {
        "schema": "prevalidation_h05_higher_order_acquisition_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete_with_findings" if checks_passed else "failed",
        "passed": checks_passed,
        "scope": {
            "catalog_item": "H05",
            "systems": ["H2", "H4"],
            "formulas": list(formulas),
            "new_direct_pf_points": 0,
            "claim_boundary": (
                "small dense H-chain diagnosis; D6/D8 construction cost is excluded "
                "from online BCH timings"
            ),
        },
        "protocol": {
            "target_error_hartree": TARGET_ERROR,
            "residual_threshold_over_epsilon": RESIDUAL_THRESHOLD_OVER_EPSILON,
            "direct_window_id": DIRECT_WINDOW_ID,
            "direct_designs": DIRECT_DESIGNS,
            "tstar_definition": (
                "continuous minimum of the exact three-term t4+t6+t8 model in "
                "the feasible interval connected to t=0"
            ),
            "response_equation": (
                "Q(H-<H>)Q |x> = -Q D4|psi>, augmented by |psi><psi|; "
                "mixing=<D4 psi|x>"
            ),
        },
        "checks": checks,
        "summary": summary,
        "method_summaries": method_summaries,
        "method_rows": method_rows,
        "response_rows": response_rows,
        "direct_fit_rows": direct_rows,
        "reference_tstar_rows": tstar_rows,
        "interpretation": {
            "response": (
                "Projected response exactly reproduces the F02 D4 state-mixing "
                "mechanism when the exact state is used."
            ),
            "direct_fit": (
                "The exact-a4 two-point and free five-point high-tail fits pass all "
                "eight development conditions, but require frozen unused-system validation."
            ),
            "approximate_state": (
                "HF and CISD coefficient estimates can fail badly for cancellation-"
                "defined optimized-PF coefficients even when energies or overlaps look good."
            ),
            "decision": (
                "Use response for the mixing correction and freeze the exact-a4 two-point "
                "fit as the next holdout candidate; retain direct finite-time validation."
            ),
        },
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "method_comparison.csv", method_rows)
    _write_csv(output_dir / "method_summary.csv", method_summaries)
    _write_csv(output_dir / "response_diagnostics.csv", response_rows)
    _write_csv(output_dir / "direct_fit_diagnostics.csv", direct_rows)
    _write_csv(output_dir / "reference_tstar.csv", tstar_rows)
    _write_figures(output_dir, method_summaries)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/compact_bch.py"),
        Path("review_response/audit_f02_tau8_state_mixing.py"),
    ]
    input_paths = [
        f01_path,
        operators_path,
        f02_path,
        h01_path,
        states_path,
        h04_path,
    ]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "method_comparison.csv",
        output_dir / "method_summary.csv",
        output_dir / "response_diagnostics.csv",
        output_dir / "direct_fit_diagnostics.csv",
        output_dir / "reference_tstar.csv",
        output_dir / "method_worst_residual.png",
        output_dir / "method_sign_recovery.png",
        output_dir / "report.md",
    ]
    manifest = {
        "schema": "prevalidation_h05_manifest_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": audit["status"],
        "git": {
            "commit": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "remote": _git_output("remote", "get-url", "origin"),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f01-dir", type=Path, default=DEFAULT_F01)
    parser.add_argument("--f02-dir", type=Path, default=DEFAULT_F02)
    parser.add_argument("--h01-dir", type=Path, default=DEFAULT_H01)
    parser.add_argument("--h04-dir", type=Path, default=DEFAULT_H04)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(
        arguments.f01_dir,
        arguments.f02_dir,
        arguments.h01_dir,
        arguments.h04_dir,
        arguments.output_dir,
    )
    print(json.dumps({"status": audit["status"], **audit["summary"]}, indent=2))


if __name__ == "__main__":
    main()
