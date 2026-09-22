"""H04 audit of compact BCH grouping and norm-importance truncation.

This audit compares the H03 naive commutator expansion with the grouped
partial-sum recurrences of Maxwell et al. (arXiv:2606.30738v1).  It validates
full grouped D4 state actions against the independently stored F01 matrices,
then measures whether the paper's norm-product importance heuristic preserves
signed expectations and PF selection when only the top grouped terms are kept.
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
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from review_response.audit_f01_effective_hamiltonian_multipf import formula_registry
from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from review_response.audit_h01_approximate_state_pilot import (
    CANDIDATE_SETS,
    leading_analytic_cost,
    leading_analytic_time,
)
from review_response.compact_bch import (
    compact_composed_d4_terms,
    evaluate_grouped_terms,
    rank_terms_by_norm_bound,
    summed_components,
)
from review_response.search_pf_cost_predictability_m2_m3 import pauli_rotation_count
from trotterlib.pf_decomposition import symmetric_s2_sequence


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_H01 = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")
DEFAULT_H03 = Path("artifacts/prevalidation_h03_matrix_free_d4_action_20260922")
DEFAULT_X02 = Path("artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3")
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1"
)
STATE_IDS = ("exact", "hf", "cisd")
SELECTION_COUNTS = {
    "H2": (1, 2, 3, 4, 5),
    "H4": (1, 5, 10, 25, 50, 100, 200, 300, 400, 456),
}
LITERATURE = {
    "title": "Practical Estimation of Trotter Error for Hamiltonian Simulation",
    "authors_short": "Maxwell et al.",
    "arxiv": "2606.30738v1",
    "date": "2026-06-29",
    "url": "https://arxiv.org/html/2606.30738v1",
    "equations_used": [19, 20, 21],
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _relative_vector_error(value: np.ndarray, reference: np.ndarray) -> float:
    return float(
        np.linalg.norm(np.asarray(value) - np.asarray(reference))
        / max(float(np.linalg.norm(reference)), 1e-300)
    )


def _rank_correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2:
        return None
    left_order = np.argsort(np.argsort(np.asarray(left, dtype=float)))
    right_order = np.argsort(np.argsort(np.asarray(right, dtype=float)))
    if np.std(left_order) == 0 or np.std(right_order) == 0:
        return None
    return float(np.corrcoef(left_order, right_order)[0, 1])


def _write_figures(
    output_dir: Path,
    pruning_rows: list[dict[str, Any]],
    selection_rows: list[dict[str, Any]],
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    for axis, system_id in zip(axes, ("H2", "H4"), strict=True):
        for formula_id in ("yoshida4", "current_m3", "two_term_center", "m5_best"):
            rows = [
                row
                for row in pruning_rows
                if row["system_id"] == system_id
                and row["state_id"] == "exact"
                and row["formula_id"] == formula_id
            ]
            axis.semilogy(
                [row["selected_grouped_term_count"] for row in rows],
                [max(row["expectation_relative_error"], 1e-15) for row in rows],
                marker="o",
                markersize=3,
                label=formula_id,
            )
        axis.set_title(system_id)
        axis.set_xlabel("selected grouped terms")
        axis.set_ylabel("relative signed-expectation error")
        axis.grid(True, which="both", alpha=0.25)
    axes[1].legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(output_dir / "importance_accuracy.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    for axis, system_id in zip(axes, ("H2", "H4"), strict=True):
        rows = [
            row
            for row in selection_rows
            if row["system_id"] == system_id
            and row["state_id"] == "exact"
            and row["candidate_set_id"] == "operational_x02_three"
        ]
        axis.plot(
            [row["selected_grouped_terms_per_formula"] for row in rows],
            [100.0 * row["exact_leading_model_selection_regret"] for row in rows],
            marker="o",
            label="leading-model regret",
        )
        axis.plot(
            [row["selected_grouped_terms_per_formula"] for row in rows],
            [100.0 * row["direct_formula_choice_regret"] for row in rows],
            marker="s",
            label="direct formula regret",
        )
        axis.set_title(system_id)
        axis.set_xlabel("selected grouped terms per PF")
        axis.set_ylabel("selection regret (%)")
        axis.grid(True, alpha=0.25)
    axes[1].legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(output_dir / "importance_selection_regret.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    summary = audit["summary"]
    lines = [
        "# H04: compact BCH and importance-selection audit",
        "",
        f"Status: **{audit['status']}**",
        "",
        "## Outcome",
        "",
        f"The grouped partial-sum representation reproduces all stored H2/H4 D4 "
        f"state actions with maximum relative error "
        f"{summary['maximum_full_action_relative_error']:.3e}. For H4/Yoshida, "
        f"the representation reduces the leading grouped objects from "
        f"{summary['h4_yoshida_naive_raw_commutator_terms']} raw commutators to "
        f"{summary['h4_grouped_term_count']} grouped terms "
        f"({summary['h4_term_count_reduction_factor']:.1f}x fewer).",
        "",
        "This removes the H03 symbolic-generation blocker. It does not remove dense "
        "input group matrices or the exponential statevector representation.",
        "",
        "## Method comparison",
        "",
        "| system | PF | raw BCH terms | raw symbolic time (s) | grouped terms | "
        "grouped full action time (s, median over states) | max action rel. error |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in audit["method_rows"]:
        raw_count = row["naive_raw_d4_commutator_count"]
        raw_seconds = row["naive_symbolic_expansion_seconds"]
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{'n/a' if raw_count is None else raw_count} | "
            f"{'n/a' if raw_seconds is None else f'{raw_seconds:.6f}'} | "
            f"{row['grouped_d4_term_count']} | "
            f"{row['median_grouped_action_seconds']:.6f} | "
            f"{row['maximum_full_action_relative_error']:.3e} |"
        )

    lines.extend(
        [
            "",
            "## Importance truncation",
            "",
            f"The norm-product heuristic is not monotone in signed-error accuracy: "
            f"{summary['nonmonotone_accuracy_curve_count']} of "
            f"{summary['importance_curve_count']} PF/state curves worsen at least once "
            "when more terms are added. This is caused by cancellation between signed "
            "grouped components, so top-k truncation needs an a-posteriori remainder or "
            "sign-stability check.",
            "",
            f"The largest grouped-component cancellation ratio was "
            f"{summary['maximum_component_cancellation_ratio']:.3e}. The maximum "
            f"exact-state direct formula-choice regret attributable to truncation was "
            f"{summary['maximum_exact_state_direct_formula_regret_from_truncation']:.2%}. "
            f"All PF choices match the full grouped result from "
            f"{summary['minimum_selection_stable_count_all_states']['H2']}/5 H2 terms "
            f"and {summary['minimum_selection_stable_count_all_states']['H4']}/456 H4 terms onward, "
            "but this rank stability is not an error bound.",
            "",
            "## Literature and applicability",
            "",
            "The grouped Y3/Y5 recurrence and norm-product importance score follow "
            "Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian "
            "Simulation*, arXiv:2606.30738v1, Eqs. (19)--(21). The paper derives the "
            "compact form for symmetric BCH and recursively defined formulas. Yoshida4 "
            "fits that setting. The three optimized repository formulas are arbitrary "
            "palindromic S2 compositions, so this audit derives their universal fifth-order "
            "composition coefficients independently and validates them against F01; it does "
            "not assume that their labels imply Suzuki recursion.",
            "",
            "The paper's electronic-structure application uses CDF fragments with a "
            "strong norm hierarchy. The present H-chain groups and PF-selection target do "
            "not share that partition assumption. Failure of aggressive top-k pruning here "
            "does not contradict the paper's application result.",
            "",
            "## Decision",
            "",
            "Adopt the full grouped representation as the H03/H04 D2 backend candidate. "
            "Do not use norm-only top-k pruning as a selector guarantee. If pruning is "
            "needed at larger scale, require signed partial-sum convergence and PF-ranking "
            "stability, or evaluate a certified remainder.",
            "",
            "## Files",
            "",
            "- `audit.json`: protocol, checks, summaries, and conclusions.",
            "- `method_comparison.csv`: naive versus grouped counts, time, and accuracy.",
            "- `state_action_summary.csv`: full compact action validation.",
            "- `grouped_components.csv`: signed grouped contributions and importance ranks.",
            "- `importance_truncation.csv`: top-k accuracy and cancellation diagnostics.",
            "- `selection_regret.csv`: top-k PF choice and regret.",
            "- `manifest.json`: source, input, and artifact hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    f01_dir: Path,
    h01_dir: Path,
    h03_dir: Path,
    x02_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_path = f01_dir / "audit.json"
    operators_path = f01_dir / "effective_operators.npz"
    h01_path = h01_dir / "audit.json"
    states_path = h01_dir / "states.npz"
    h03_path = h03_dir / "audit.json"
    x02_path = x02_dir / "audit.json"
    minima_path = x02_dir / "c06_grid_minima.csv"
    f01 = json.loads(f01_path.read_text(encoding="utf-8"))
    h01 = json.loads(h01_path.read_text(encoding="utf-8"))
    h03 = json.loads(h03_path.read_text(encoding="utf-8"))
    x02 = json.loads(x02_path.read_text(encoding="utf-8"))
    if f01["status"] != "complete" or not f01["passed"]:
        raise RuntimeError("F01 input is not complete")
    if h01["status"] != "pilot_complete_with_findings" or not h01["checks_passed"]:
        raise RuntimeError("H01 input is not complete")
    if h03["status"] != "complete_with_scaling_blocker" or not h03["passed"]:
        raise RuntimeError("H03 input is not complete")
    if x02["component_status"]["C06"] != "complete":
        raise RuntimeError("X02 direct minima input is not complete")

    formulas = {row["formula_id"]: row for row in formula_registry()}
    minima_rows = _read_csv(minima_path)
    naive_h2 = {
        row["formula_id"]: row for row in h03["h2_formula_rows"]
    }
    naive_h4_yoshida = h03["h4_symbolic_boundary_rows"][0]

    method_rows: list[dict[str, Any]] = []
    state_rows: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    pruning_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    values: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    full_values: dict[tuple[str, str, str], dict[str, Any]] = {}

    with np.load(operators_path) as arrays, np.load(states_path) as states:
        for system_id in ("H2", "H4"):
            group_keys = sorted(
                key for key in arrays.files if key.startswith(f"{system_id}_group_")
            )
            groups = [np.asarray(arrays[key], dtype=np.complex128) for key in group_keys]
            for formula_id, formula in formulas.items():
                sequence = tuple(
                    float(value)
                    for value in symmetric_s2_sequence(formula["weights"])
                )
                construction_started = time.perf_counter()
                terms, term_diagnostics = compact_composed_d4_terms(
                    len(groups), sequence
                )
                construction_seconds = time.perf_counter() - construction_started
                ranking, importance_scores = rank_terms_by_norm_bound(terms, groups)
                rank_by_index = {
                    index: rank + 1 for rank, index in enumerate(ranking)
                }
                state_method_rows = []
                for state_id in STATE_IDS:
                    state = np.asarray(
                        states[f"{system_id}_{state_id}_state"], dtype=np.complex128
                    )
                    reference_action = (
                        np.asarray(
                            arrays[f"{system_id}_{formula_id}_D4"],
                            dtype=np.complex128,
                        )
                        @ state
                    )
                    reference_expectation = complex(np.vdot(state, reference_action))
                    actions, expectations, term_counts, action_diagnostics = (
                        evaluate_grouped_terms(terms, groups, state)
                    )
                    full_action = summed_components(actions, range(len(actions)))
                    full_expectation = complex(np.vdot(state, full_action))
                    action_relative_error = _relative_vector_error(
                        full_action, reference_action
                    )
                    expectation_absolute_error = float(
                        abs(full_expectation - reference_expectation)
                    )
                    cancellation_ratio = float(
                        sum(abs(value) for value in expectations)
                        / max(abs(full_expectation), 1e-300)
                    )
                    actual_importances = [abs(value) for value in expectations]
                    correlation = _rank_correlation(
                        importance_scores, actual_importances
                    )
                    state_row = {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "state_id": state_id,
                        "dimension": int(state.size),
                        "group_count": len(groups),
                        "grouped_term_count": len(terms),
                        "full_action_relative_error": action_relative_error,
                        "reference_expectation_real_hartree": float(
                            reference_expectation.real
                        ),
                        "compact_expectation_real_hartree": float(
                            full_expectation.real
                        ),
                        "compact_expectation_imaginary_hartree": float(
                            full_expectation.imag
                        ),
                        "expectation_absolute_error_hartree": expectation_absolute_error,
                        "component_cancellation_ratio": cancellation_ratio,
                        "norm_importance_actual_rank_correlation": correlation,
                        **action_diagnostics,
                    }
                    state_rows.append(state_row)
                    state_method_rows.append(state_row)

                    for index, ((coefficient, _, kind), expectation, counts) in enumerate(
                        zip(terms, expectations, term_counts, strict=True)
                    ):
                        component_rows.append(
                            {
                                "system_id": system_id,
                                "formula_id": formula_id,
                                "state_id": state_id,
                                "component_index": index,
                                "importance_rank": rank_by_index[index],
                                "component_kind": kind,
                                "coefficient_real": float(coefficient.real),
                                "coefficient_imaginary": float(coefficient.imag),
                                "norm_bound_importance_score": importance_scores[index],
                                "expectation_real_hartree": float(expectation.real),
                                "expectation_imaginary_hartree": float(expectation.imag),
                                "expectation_absolute_hartree": float(abs(expectation)),
                                **counts,
                            }
                        )

                    full_rotations = pauli_rotation_count(
                        system_id, formula["weights"]
                    )
                    full_alpha = abs(float(full_expectation.real))
                    full_time = leading_analytic_time(full_alpha)
                    full_cost = leading_analytic_cost(
                        full_alpha, full_time, full_rotations
                    )
                    full_values[(system_id, state_id, formula_id)] = {
                        "expectation": float(full_expectation.real),
                        "analytic_time": full_time,
                        "analytic_cost": full_cost,
                        "rotations": full_rotations,
                    }
                    total_score = float(sum(importance_scores))
                    full_l1 = float(sum(abs(value) for value in expectations))
                    previous_error = None
                    for requested_count in SELECTION_COUNTS[system_id]:
                        selected_count = min(int(requested_count), len(terms))
                        selected_indices = ranking[:selected_count]
                        approximate_action = summed_components(
                            actions, selected_indices
                        )
                        approximate_expectation = complex(
                            np.vdot(state, approximate_action)
                        )
                        expectation_relative_error = float(
                            abs(approximate_expectation - full_expectation)
                            / max(abs(full_expectation), 1e-300)
                        )
                        selected_l1 = float(
                            sum(abs(expectations[index]) for index in selected_indices)
                        )
                        selected_linear_actions = int(
                            sum(
                                term_counts[index]["linear_combination_actions"]
                                for index in selected_indices
                            )
                        )
                        selected_equivalent_actions = int(
                            sum(
                                term_counts[index]["equivalent_fragment_actions"]
                                for index in selected_indices
                            )
                        )
                        alpha = abs(float(approximate_expectation.real))
                        analytic_time = (
                            leading_analytic_time(alpha) if alpha > 1e-300 else math.inf
                        )
                        analytic_cost = (
                            leading_analytic_cost(alpha, analytic_time, full_rotations)
                            if math.isfinite(analytic_time)
                            else math.inf
                        )
                        row = {
                            "system_id": system_id,
                            "formula_id": formula_id,
                            "state_id": state_id,
                            "requested_grouped_term_count": requested_count,
                            "selected_grouped_term_count": selected_count,
                            "selected_fraction": selected_count / len(terms),
                            "approximate_expectation_real_hartree": float(
                                approximate_expectation.real
                            ),
                            "full_expectation_real_hartree": float(
                                full_expectation.real
                            ),
                            "expectation_relative_error": expectation_relative_error,
                            "action_relative_error": _relative_vector_error(
                                approximate_action, full_action
                            ),
                            "expectation_sign_matches_full": bool(
                                np.sign(approximate_expectation.real)
                                == np.sign(full_expectation.real)
                            ),
                            "selected_importance_score_fraction": float(
                                sum(importance_scores[index] for index in selected_indices)
                                / max(total_score, 1e-300)
                            ),
                            "selected_actual_absolute_contribution_fraction": (
                                selected_l1 / max(full_l1, 1e-300)
                            ),
                            "dropped_signed_expectation_real_hartree": float(
                                full_expectation.real - approximate_expectation.real
                            ),
                            "selected_linear_combination_action_count": selected_linear_actions,
                            "selected_equivalent_fragment_action_count": selected_equivalent_actions,
                            "analytic_time_from_truncated_expectation": analytic_time,
                            "analytic_cost_from_truncated_expectation": analytic_cost,
                            "accuracy_worsened_from_previous_count": bool(
                                previous_error is not None
                                and expectation_relative_error > previous_error + 1e-13
                            ),
                        }
                        pruning_rows.append(row)
                        values[(system_id, state_id, formula_id, selected_count)] = row
                        previous_error = expectation_relative_error

                if system_id == "H2":
                    naive = naive_h2[formula_id]
                    raw_count = naive["d4_raw_commutator_term_count"]
                    raw_seconds = naive["symbolic_expansion_seconds"]
                elif formula_id == "yoshida4":
                    raw_count = naive_h4_yoshida["d4_raw_commutator_term_count"]
                    raw_seconds = naive_h4_yoshida["symbolic_expansion_seconds"]
                else:
                    raw_count = None
                    raw_seconds = None
                method_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "group_count": len(groups),
                        "s2_block_count": len(sequence),
                        "naive_raw_d4_commutator_count": raw_count,
                        "naive_symbolic_expansion_seconds": raw_seconds,
                        "grouped_construction_seconds": float(construction_seconds),
                        "grouped_d4_term_count": len(terms),
                        "base_y3_grouped_term_count": term_diagnostics[
                            "base_y3_grouped_term_count"
                        ],
                        "base_y5_grouped_term_count": term_diagnostics[
                            "base_y5_grouped_term_count"
                        ],
                        "composition_c5": term_diagnostics["c5"],
                        "composition_c13": term_diagnostics["c13"],
                        "composition_first_order_x": term_diagnostics[
                            "first_order_x"
                        ],
                        "composition_third_order_l1": term_diagnostics[
                            "third_order_l1"
                        ],
                        "composition_fifth_order_model_residual_l1": term_diagnostics[
                            "fifth_order_model_residual_l1"
                        ],
                        "median_grouped_action_seconds": float(
                            statistics.median(
                                row["component_evaluation_seconds"]
                                for row in state_method_rows
                            )
                        ),
                        "maximum_full_action_relative_error": max(
                            row["full_action_relative_error"]
                            for row in state_method_rows
                        ),
                        "maximum_expectation_absolute_error_hartree": max(
                            row["expectation_absolute_error_hartree"]
                            for row in state_method_rows
                        ),
                        "linear_combination_action_count_per_state": state_method_rows[
                            0
                        ]["linear_combination_action_count"],
                        "unique_partial_sum_operator_count": state_method_rows[0][
                            "unique_partial_sum_operator_count"
                        ],
                    }
                )

    direct_costs_by_system: dict[str, dict[str, float]] = {}
    for system_id in ("H2", "H4"):
        direct_costs_by_system[system_id] = {}
        for formula_id in CANDIDATE_SETS["operational_x02_three"]:
            minimum = next(
                row
                for row in minima_rows
                if row["system"] == system_id and row["formula"] == formula_id
            )
            direct_costs_by_system[system_id][formula_id] = float(
                minimum["refined_sampled_minimum_cost_per_pf_step_unit"]
            ) * full_values[(system_id, "exact", formula_id)]["rotations"]

    for system_id in ("H2", "H4"):
        for state_id in STATE_IDS:
            for candidate_set_id, formula_ids in CANDIDATE_SETS.items():
                full_costs = {
                    formula_id: full_values[(system_id, state_id, formula_id)][
                        "analytic_cost"
                    ]
                    for formula_id in formula_ids
                }
                full_reference = min(full_costs, key=full_costs.get)
                full_best = full_costs[full_reference]
                direct_costs = (
                    direct_costs_by_system[system_id]
                    if candidate_set_id == "operational_x02_three"
                    else None
                )
                direct_reference = (
                    min(direct_costs, key=direct_costs.get)
                    if direct_costs is not None
                    else None
                )
                direct_best = (
                    direct_costs[direct_reference]
                    if direct_costs is not None and direct_reference is not None
                    else None
                )
                for selected_count in SELECTION_COUNTS[system_id]:
                    approximate_costs = {
                        formula_id: values[
                            (system_id, state_id, formula_id, selected_count)
                        ]["analytic_cost_from_truncated_expectation"]
                        for formula_id in formula_ids
                    }
                    selected_formula = min(
                        approximate_costs, key=approximate_costs.get
                    )
                    direct_regret = (
                        direct_costs[selected_formula] / direct_best - 1.0
                        if direct_costs is not None and direct_best is not None
                        else None
                    )
                    selection_rows.append(
                        {
                            "system_id": system_id,
                            "state_id": state_id,
                            "candidate_set_id": candidate_set_id,
                            "candidate_formula_ids_json": json.dumps(formula_ids),
                            "selected_grouped_terms_per_formula": selected_count,
                            "selected_formula_id": selected_formula,
                            "full_compact_reference_formula_id": full_reference,
                            "selection_matches_full_compact": bool(
                                selected_formula == full_reference
                            ),
                            "exact_leading_model_selection_regret": float(
                                full_costs[selected_formula] / full_best - 1.0
                            ),
                            "direct_reference_formula_id": direct_reference,
                            "direct_formula_choice_regret": direct_regret,
                            "total_grouped_expectation_evaluations": int(
                                selected_count * len(formula_ids)
                            ),
                        }
                    )

    checks = [
        {
            "check_id": "maximum_full_action_relative_error",
            "measured": max(row["full_action_relative_error"] for row in state_rows),
            "threshold": 5e-10,
            "comparison": "<=",
            "passed": max(row["full_action_relative_error"] for row in state_rows)
            <= 5e-10,
        },
        {
            "check_id": "maximum_expectation_absolute_error_hartree",
            "measured": max(
                row["expectation_absolute_error_hartree"] for row in state_rows
            ),
            "threshold": 5e-12,
            "comparison": "<=",
            "passed": max(
                row["expectation_absolute_error_hartree"] for row in state_rows
            )
            <= 5e-12,
        },
        {
            "check_id": "composition_order_conditions",
            "measured": max(
                max(
                    abs(row["composition_first_order_x"] - 1.0),
                    row["composition_third_order_l1"],
                    row["composition_fifth_order_model_residual_l1"],
                )
                for row in method_rows
            ),
            "threshold": 2e-13,
            "comparison": "<=",
            "passed": max(
                max(
                    abs(row["composition_first_order_x"] - 1.0),
                    row["composition_third_order_l1"],
                    row["composition_fifth_order_model_residual_l1"],
                )
                for row in method_rows
            )
            <= 2e-13,
        },
        {
            "check_id": "grouped_term_formula",
            "measured": max(
                abs(row["grouped_d4_term_count"] - (5 if row["system_id"] == "H2" else 456))
                for row in method_rows
            ),
            "threshold": 0,
            "comparison": "==",
            "passed": all(
                row["grouped_d4_term_count"]
                == (5 if row["system_id"] == "H2" else 456)
                for row in method_rows
            ),
        },
        {
            "check_id": "full_selection_recovers_reference",
            "measured": sum(
                not row["selection_matches_full_compact"]
                for row in selection_rows
                if row["selected_grouped_terms_per_formula"]
                == (5 if row["system_id"] == "H2" else 456)
            ),
            "threshold": 0,
            "comparison": "==",
            "passed": all(
                row["selection_matches_full_compact"]
                for row in selection_rows
                if row["selected_grouped_terms_per_formula"]
                == (5 if row["system_id"] == "H2" else 456)
            ),
        },
    ]
    checks_passed = all(check["passed"] for check in checks)
    curve_keys = {
        (row["system_id"], row["formula_id"], row["state_id"])
        for row in pruning_rows
    }
    nonmonotone_curves = sum(
        any(
            row["accuracy_worsened_from_previous_count"]
            for row in pruning_rows
            if (row["system_id"], row["formula_id"], row["state_id"]) == key
        )
        for key in curve_keys
    )
    h4_yoshida_method = next(
        row
        for row in method_rows
        if row["system_id"] == "H4" and row["formula_id"] == "yoshida4"
    )
    exact_truncation_direct_regrets = [
        row["direct_formula_choice_regret"]
        for row in selection_rows
        if row["state_id"] == "exact"
        and not row["selection_matches_full_compact"]
        and row["direct_formula_choice_regret"] is not None
    ]
    minimum_stable_counts: dict[str, int] = {}
    maximum_error_at_stable_count: dict[str, float] = {}
    for system_id in ("H2", "H4"):
        counts = list(SELECTION_COUNTS[system_id])
        stable_count = counts[-1]
        for candidate_count in counts:
            later_rows = [
                row
                for row in selection_rows
                if row["system_id"] == system_id
                and row["selected_grouped_terms_per_formula"] >= candidate_count
            ]
            if later_rows and all(
                row["selection_matches_full_compact"] for row in later_rows
            ):
                stable_count = candidate_count
                break
        minimum_stable_counts[system_id] = stable_count
        maximum_error_at_stable_count[system_id] = max(
            row["expectation_relative_error"]
            for row in pruning_rows
            if row["system_id"] == system_id
            and row["selected_grouped_term_count"] == stable_count
        )
    summary = {
        "maximum_full_action_relative_error": max(
            row["full_action_relative_error"] for row in state_rows
        ),
        "maximum_expectation_absolute_error_hartree": max(
            row["expectation_absolute_error_hartree"] for row in state_rows
        ),
        "h4_yoshida_naive_raw_commutator_terms": h4_yoshida_method[
            "naive_raw_d4_commutator_count"
        ],
        "h4_grouped_term_count": h4_yoshida_method["grouped_d4_term_count"],
        "h4_term_count_reduction_factor": float(
            h4_yoshida_method["naive_raw_d4_commutator_count"]
            / h4_yoshida_method["grouped_d4_term_count"]
        ),
        "maximum_component_cancellation_ratio": max(
            row["component_cancellation_ratio"] for row in state_rows
        ),
        "importance_curve_count": len(curve_keys),
        "nonmonotone_accuracy_curve_count": nonmonotone_curves,
        "maximum_exact_state_direct_formula_regret_from_truncation": max(
            exact_truncation_direct_regrets
        ),
        "minimum_selection_stable_count_all_states": minimum_stable_counts,
        "maximum_expectation_relative_error_at_selection_stable_count": (
            maximum_error_at_stable_count
        ),
        "full_grouped_h4_selection_stable": all(
            row["selection_matches_full_compact"]
            for row in selection_rows
            if row["system_id"] == "H4"
            and row["selected_grouped_terms_per_formula"] == 456
        ),
    }
    audit = {
        "schema": "prevalidation_h04_compact_bch_importance_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete_with_findings" if checks_passed else "failed",
        "passed": checks_passed,
        "scope": {
            "catalog_item": "H04",
            "systems": ["H2", "H4"],
            "formulas": list(formulas),
            "states": list(STATE_IDS),
            "new_direct_pf_points": 0,
            "claim_boundary": (
                "full grouped D4 actions and diagnostic norm-ranked truncations; "
                "no large-system tensor-network claim"
            ),
        },
        "literature": LITERATURE,
        "protocol": {
            "base_s2_grouping": "Maxwell et al. Eqs. (19)-(20)",
            "importance_score": (
                "absolute term coefficient times recursive norm-product bound, "
                "using fragment spectral norms; Eq. (21)"
            ),
            "composition_extension": (
                "noncommutative formal series gives c5*Y5 + "
                "c13*[Y1,[Y1,Y3]] for each stored palindromic S2 sequence"
            ),
            "selection_counts": {key: list(value) for key, value in SELECTION_COUNTS.items()},
            "reference": "stored F01 dense D4 in the identical sector basis",
        },
        "checks": checks,
        "summary": summary,
        "method_rows": method_rows,
        "state_action_rows": state_rows,
        "pruning_rows": pruning_rows,
        "selection_rows": selection_rows,
        "interpretation": {
            "compact_representation": (
                "The O(n^2) grouped recurrence removes the H03 symbolic bottleneck "
                "and remains valid for all four stored S2 compositions after the "
                "independently checked composition adapter."
            ),
            "importance_selection": (
                "Norm-ranked top-k truncation can worsen as terms are added and can "
                "change PF selection because the target is a small signed remainder."
            ),
            "novelty_boundary": (
                "BCH grouping and norm importance are prior art; the project-specific "
                "result is their behavior for high-order finite-time QPE PF selection."
            ),
            "decision": (
                "Use full grouped actions for H05. Do not accept norm-only pruning "
                "without signed convergence and selection-stability diagnostics."
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
    _write_csv(output_dir / "state_action_summary.csv", state_rows)
    _write_csv(output_dir / "grouped_components.csv", component_rows)
    _write_csv(output_dir / "importance_truncation.csv", pruning_rows)
    _write_csv(output_dir / "selection_regret.csv", selection_rows)
    _write_figures(output_dir, pruning_rows, selection_rows)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/compact_bch.py"),
        Path("review_response/audit_h03_matrix_free_d4_action.py"),
    ]
    input_paths = [
        f01_path,
        operators_path,
        h01_path,
        states_path,
        h03_path,
        x02_path,
        minima_path,
    ]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "method_comparison.csv",
        output_dir / "state_action_summary.csv",
        output_dir / "grouped_components.csv",
        output_dir / "importance_truncation.csv",
        output_dir / "selection_regret.csv",
        output_dir / "importance_accuracy.png",
        output_dir / "importance_selection_regret.png",
        output_dir / "report.md",
    ]
    manifest = {
        "schema": "prevalidation_h04_manifest_v1",
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
        "literature": LITERATURE,
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f01-dir", type=Path, default=DEFAULT_F01)
    parser.add_argument("--h01-dir", type=Path, default=DEFAULT_H01)
    parser.add_argument("--h03-dir", type=Path, default=DEFAULT_H03)
    parser.add_argument("--x02-dir", type=Path, default=DEFAULT_X02)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(
        arguments.f01_dir,
        arguments.h01_dir,
        arguments.h03_dir,
        arguments.x02_dir,
        arguments.output_dir,
    )
    print(json.dumps({"status": audit["status"], **audit["summary"]}, indent=2))


if __name__ == "__main__":
    main()
