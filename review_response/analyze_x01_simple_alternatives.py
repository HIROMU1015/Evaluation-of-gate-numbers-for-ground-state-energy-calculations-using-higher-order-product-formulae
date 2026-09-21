"""X01/A08 comparison with simple fixed and small-local-search baselines.

The comparison reuses saved current_m3 and two_term_center direct points.  It
separates rules that can be fixed without validation truth (a 1% budget margin
and a 0.9*t_star cap) from direct-point diagnostics that use oracle PF errors.
No new numerical physics calculation is performed.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import statistics
from typing import Any

import audit_existing_results_x01 as audit_x01
import analyze_x01_frozen_qpe_budget as a05
import analyze_x01_cost_benefit as a07


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_x01_simple_alternatives_20260921"

FIXED_BUDGET_MARGIN = 1.01
FIXED_TIME_CAP_RELATIVE_TO_T_STAR = 0.9
LOCAL_SEARCH_RELATIVE_TIMES = (0.9, 1.0, 1.1)

STRATEGY_METADATA = {
    "current_two_term_tstar": {
        "implementation_complexity": "low",
        "required_input": "saved exact-state short-time proxy and three signed direct fit points",
    },
    "current_two_term_plus_1pct_budget": {
        "implementation_complexity": "low",
        "required_input": "current two-term calibration plus a fixed scalar cost margin",
    },
    "current_two_term_time_cap_0p9": {
        "implementation_complexity": "low",
        "required_input": "current two-term calibration; no validation truth for the decision",
    },
    "current_one_direct_check_tstar": {
        "implementation_complexity": "moderate",
        "required_input": "current two-term calibration plus one exact direct PF point",
    },
    "current_three_point_local_search": {
        "implementation_complexity": "moderate",
        "required_input": "current two-term calibration plus three exact direct PF points",
    },
    "current_full_saved_grid_oracle_reference": {
        "implementation_complexity": "high diagnostic reference",
        "required_input": "current calibration plus the complete saved adaptive direct grid",
    },
    "new_two_term_plus_1pct_budget": {
        "implementation_complexity": "moderate",
        "required_input": "separate PF implementation and calibration plus a fixed cost margin",
    },
}


def _point_at(formula: dict[str, Any], relative: float) -> dict[str, Any]:
    point = min(
        formula["local_direct_points"],
        key=lambda value: abs(float(value["relative_to_t_star"]) - relative),
    )
    if abs(float(point["relative_to_t_star"]) - relative) > 1e-10:
        raise ValueError(f"saved local grid has no point at {relative}")
    return point


def _score_cost(
    *,
    time: float,
    rotations: int,
    direct_error: float,
    cost: float,
) -> dict[str, Any]:
    qpe_error = a05.BETA * rotations / (time * cost)
    total = direct_error + qpe_error
    return {
        "qpe_error_hartree": qpe_error,
        "actual_total_error_bound_hartree": total,
        "target_excess_hartree": max(total - a05.EPSILON_E, 0.0),
        "target_excess_over_epsilon": max(total - a05.EPSILON_E, 0.0)
        / a05.EPSILON_E,
        "saved_condition_pass": total
        <= a05.EPSILON_E + a05.ARITHMETIC_TOLERANCE_HARTREE,
    }


def strategy_rows(
    budget_rows: list[dict[str, Any]],
    calibration_rows: list[dict[str, Any]],
    raw_sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    budget = {
        (row["condition"], row["pf"], row["model"]): row for row in budget_rows
    }
    calibration = {
        (row["condition"], row["pf"]): row for row in calibration_rows
    }
    raw = {
        source["condition"]: audit_x01.load_json(ROOT / str(source["path"]))
        for source in raw_sources
    }
    conditions = sorted({str(row["condition"]) for row in budget_rows})
    result: list[dict[str, Any]] = []

    def append(
        *,
        condition: str,
        strategy_id: str,
        strategy_label: str,
        pf: str,
        selected_relative_time: float,
        time: float,
        rotations: int,
        direct_error: float,
        quantum_cost: float,
        baseline_cost: float,
        base_calibration_points: int,
        base_calibration_seconds: float,
        extra_direct_points: int,
        extra_direct_seconds: float,
        validation_truth_used_for_decision: bool,
        pre_fixed_rule: bool,
        information_class: str,
        note: str,
    ) -> None:
        scored = _score_cost(
            time=time,
            rotations=rotations,
            direct_error=direct_error,
            cost=quantum_cost,
        )
        reference = budget[(condition, "current_m3", "two_term")]
        metadata = STRATEGY_METADATA[strategy_id]
        result.append(
            {
                "dataset_id": reference["dataset_id"],
                "condition": condition,
                "analysis_cluster": reference["analysis_cluster"],
                "strategy_id": strategy_id,
                "strategy_label": strategy_label,
                "pf": pf,
                "selected_relative_to_t_star": selected_relative_time,
                "selected_time": time,
                "direct_error_hartree": direct_error,
                "quantum_cost": quantum_cost,
                "quantum_cost_ratio_to_current_two_term_t_star": quantum_cost
                / baseline_cost,
                **scored,
                "base_calibration_points": base_calibration_points,
                "extra_direct_diagnostic_points": extra_direct_points,
                "total_points": base_calibration_points + extra_direct_points,
                "base_calibration_seconds": base_calibration_seconds,
                "extra_direct_diagnostic_seconds": extra_direct_seconds,
                "total_saved_classical_seconds": base_calibration_seconds
                + extra_direct_seconds,
                "validation_truth_used_for_decision": (
                    validation_truth_used_for_decision
                ),
                "pre_fixed_rule": pre_fixed_rule,
                "information_class": information_class,
                **metadata,
                "note": note,
            }
        )

    for condition in conditions:
        current_budget = budget[(condition, "current_m3", "two_term")]
        new_budget = budget[(condition, "two_term_center", "two_term")]
        current_formula = raw[condition]["formulas"]["current_m3"]
        new_formula = raw[condition]["formulas"]["two_term_center"]
        current_cal = calibration[(condition, "current_m3")]
        new_cal = calibration[(condition, "two_term_center")]
        baseline_cost = float(current_budget["frozen_model_cost"])

        append(
            condition=condition,
            strategy_id="current_two_term_tstar",
            strategy_label="current_m3 two-term at model t_star",
            pf="current_m3",
            selected_relative_time=1.0,
            time=float(current_budget["selected_time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(current_budget["direct_error_hartree"]),
            quantum_cost=baseline_cost,
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=0,
            extra_direct_seconds=0.0,
            validation_truth_used_for_decision=False,
            pre_fixed_rule=True,
            information_class="oracle-assisted target calibration; no validation truth in rule",
            note="A05 baseline",
        )
        append(
            condition=condition,
            strategy_id="current_two_term_plus_1pct_budget",
            strategy_label="current_m3 two-term plus fixed 1% budget margin",
            pf="current_m3",
            selected_relative_time=1.0,
            time=float(current_budget["selected_time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(current_budget["direct_error_hartree"]),
            quantum_cost=baseline_cost * FIXED_BUDGET_MARGIN,
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=0,
            extra_direct_seconds=0.0,
            validation_truth_used_for_decision=False,
            pre_fixed_rule=True,
            information_class="pre-fixed safety rule after target calibration",
            note="1% multiplier fixed from the declared canonical accuracy scale",
        )

        current_shrunk = _point_at(
            current_formula, FIXED_TIME_CAP_RELATIVE_TO_T_STAR
        )
        append(
            condition=condition,
            strategy_id="current_two_term_time_cap_0p9",
            strategy_label="current_m3 two-term at fixed 0.9 t_star cap",
            pf="current_m3",
            selected_relative_time=FIXED_TIME_CAP_RELATIVE_TO_T_STAR,
            time=float(current_shrunk["time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(current_shrunk["direct_error_hartree"]),
            quantum_cost=float(current_shrunk["two_term_cost"]),
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=0,
            extra_direct_seconds=0.0,
            validation_truth_used_for_decision=False,
            pre_fixed_rule=True,
            information_class="pre-fixed conservative time rule after target calibration",
            note="0.9 is the largest common predeclared shrink tested here; not optimized per condition",
        )

        current_at_star = _point_at(current_formula, 1.0)
        append(
            condition=condition,
            strategy_id="current_one_direct_check_tstar",
            strategy_label="current_m3 plus one direct check at t_star",
            pf="current_m3",
            selected_relative_time=1.0,
            time=float(current_at_star["time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(current_at_star["direct_error_hartree"]),
            quantum_cost=float(current_at_star["direct_cost"]),
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=1,
            extra_direct_seconds=float(current_at_star["timing_seconds"]["total"]),
            validation_truth_used_for_decision=True,
            pre_fixed_rule=True,
            information_class="one additional exact direct PF point",
            note="uses the checked direct error to set the QPE budget exactly",
        )

        three_points = [
            _point_at(current_formula, relative)
            for relative in LOCAL_SEARCH_RELATIVE_TIMES
        ]
        best_three = min(three_points, key=lambda point: float(point["direct_cost"]))
        append(
            condition=condition,
            strategy_id="current_three_point_local_search",
            strategy_label="current_m3 direct search at 0.9,1.0,1.1 t_star",
            pf="current_m3",
            selected_relative_time=float(best_three["relative_to_t_star"]),
            time=float(best_three["time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(best_three["direct_error_hartree"]),
            quantum_cost=float(best_three["direct_cost"]),
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=3,
            extra_direct_seconds=sum(
                float(point["timing_seconds"]["total"]) for point in three_points
            ),
            validation_truth_used_for_decision=True,
            pre_fixed_rule=True,
            information_class="three additional exact direct PF points",
            note="chooses the lowest directly evaluated cost; not a model-only selector",
        )

        full_points = list(current_formula["local_direct_points"])
        best_full = min(full_points, key=lambda point: float(point["direct_cost"]))
        append(
            condition=condition,
            strategy_id="current_full_saved_grid_oracle_reference",
            strategy_label="current_m3 full saved adaptive-grid oracle reference",
            pf="current_m3",
            selected_relative_time=float(best_full["relative_to_t_star"]),
            time=float(best_full["time"]),
            rotations=int(current_budget["rotations_per_pf_step"]),
            direct_error=float(best_full["direct_error_hartree"]),
            quantum_cost=float(best_full["direct_cost"]),
            baseline_cost=baseline_cost,
            base_calibration_points=int(current_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(current_cal["total_calibration_seconds"]),
            extra_direct_points=len(full_points),
            extra_direct_seconds=sum(
                float(point["timing_seconds"]["total"]) for point in full_points
            ),
            validation_truth_used_for_decision=True,
            pre_fixed_rule=False,
            information_class="adaptive saved direct-grid oracle reference",
            note="finite saved-grid minimum, not a continuous optimum",
        )

        new_cost = float(new_budget["frozen_model_cost"]) * FIXED_BUDGET_MARGIN
        append(
            condition=condition,
            strategy_id="new_two_term_plus_1pct_budget",
            strategy_label="two_term_center two-term plus fixed 1% budget margin",
            pf="two_term_center",
            selected_relative_time=1.0,
            time=float(new_budget["selected_time"]),
            rotations=int(new_budget["rotations_per_pf_step"]),
            direct_error=float(new_budget["direct_error_hartree"]),
            quantum_cost=new_cost,
            baseline_cost=baseline_cost,
            base_calibration_points=int(new_cal["total_calibration_point_count"]),
            base_calibration_seconds=float(new_cal["total_calibration_seconds"]),
            extra_direct_points=0,
            extra_direct_seconds=0.0,
            validation_truth_used_for_decision=False,
            pre_fixed_rule=True,
            information_class="pre-fixed safety rule after target calibration",
            note="same fixed 1% multiplier as the current-PF safety baseline",
        )
    return result


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = list(dict.fromkeys(str(row["strategy_id"]) for row in rows))
    result = []
    for strategy_id in ids:
        selected = [row for row in rows if row["strategy_id"] == strategy_id]
        ratios = [
            float(row["quantum_cost_ratio_to_current_two_term_t_star"])
            for row in selected
        ]
        minimum_ratio_row = min(
            selected,
            key=lambda row: float(
                row["quantum_cost_ratio_to_current_two_term_t_star"]
            ),
        )
        maximum_ratio_row = max(
            selected,
            key=lambda row: float(
                row["quantum_cost_ratio_to_current_two_term_t_star"]
            ),
        )
        result.append(
            {
                "strategy_id": strategy_id,
                "strategy_label": selected[0]["strategy_label"],
                "pf": selected[0]["pf"],
                "condition_count": len(selected),
                "saved_condition_passed": sum(
                    bool(row["saved_condition_pass"]) for row in selected
                ),
                "maximum_target_excess_over_epsilon": max(
                    float(row["target_excess_over_epsilon"]) for row in selected
                ),
                "minimum_quantum_cost_ratio": min(ratios),
                "minimum_quantum_cost_ratio_condition": minimum_ratio_row[
                    "condition"
                ],
                "median_quantum_cost_ratio": statistics.median(ratios),
                "maximum_quantum_cost_ratio": max(ratios),
                "maximum_quantum_cost_ratio_condition": maximum_ratio_row[
                    "condition"
                ],
                "equal_one_run_basket_quantum_cost": sum(
                    float(row["quantum_cost"]) for row in selected
                ),
                "base_calibration_points_over_17": sum(
                    int(row["base_calibration_points"]) for row in selected
                ),
                "extra_direct_diagnostic_points_over_17": sum(
                    int(row["extra_direct_diagnostic_points"]) for row in selected
                ),
                "total_points_over_17": sum(int(row["total_points"]) for row in selected),
                "base_calibration_seconds_over_17": sum(
                    float(row["base_calibration_seconds"]) for row in selected
                ),
                "extra_direct_diagnostic_seconds_over_17": sum(
                    float(row["extra_direct_diagnostic_seconds"]) for row in selected
                ),
                "validation_truth_used_for_decision": selected[0][
                    "validation_truth_used_for_decision"
                ],
                "pre_fixed_rule": selected[0]["pre_fixed_rule"],
                "information_class": selected[0]["information_class"],
                "implementation_complexity": selected[0][
                    "implementation_complexity"
                ],
                "required_input": selected[0]["required_input"],
                "conditions_selecting_nonunit_relative_time": sum(
                    abs(float(row["selected_relative_to_t_star"]) - 1.0) > 1e-12
                    for row in selected
                ),
            }
        )
    baseline = next(row for row in result if row["strategy_id"] == "current_two_term_tstar")
    basket = float(baseline["equal_one_run_basket_quantum_cost"])
    for row in result:
        row["equal_one_run_basket_cost_ratio"] = (
            float(row["equal_one_run_basket_quantum_cost"]) / basket
        )
    return result


def availability_rows() -> list[dict[str, Any]]:
    return [
        {
            "baseline": "existing PF plus two-term model",
            "status": "complete on all 17 saved conditions",
            "same_hamiltonians": True,
            "same_target_error": True,
            "reason_if_unavailable": None,
        },
        {
            "baseline": "pre-fixed 1% QPE-budget margin",
            "status": "complete by saved-data rescoring",
            "same_hamiltonians": True,
            "same_target_error": True,
            "reason_if_unavailable": None,
        },
        {
            "baseline": "pre-fixed 0.9 t_star cap",
            "status": "complete at a common saved point",
            "same_hamiltonians": True,
            "same_target_error": True,
            "reason_if_unavailable": None,
        },
        {
            "baseline": "one- and three-point direct diagnostics",
            "status": "complete as oracle-assisted saved-data diagnostics",
            "same_hamiltonians": True,
            "same_target_error": True,
            "reason_if_unavailable": None,
        },
        {
            "baseline": "one-order-higher PF",
            "status": "not compared",
            "same_hamiltonians": False,
            "same_target_error": None,
            "reason_if_unavailable": (
                "no complete sixth- or higher-order result on the same 17 "
                "Hamiltonians with the same calibration and direct-scoring protocol"
            ),
        },
    ]


def make_plot(path: Path, aggregates: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row["strategy_id"].replace("_", " ") for row in aggregates]
    x = np.arange(len(aggregates))
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.5))
    axes[0].bar(
        x,
        [float(row["equal_one_run_basket_cost_ratio"]) for row in aggregates],
        color=[
            "#6a8fd5" if not row["validation_truth_used_for_decision"] else "#8a7db5"
            for row in aggregates
        ],
    )
    axes[0].axhline(1.0, color="#333333", linewidth=1.0)
    axes[0].set_ylabel("basket quantum cost / current two-term")
    axes[0].set_title("Saved-condition quantum cost")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].bar(
        x,
        [int(row["extra_direct_diagnostic_points_over_17"]) for row in aggregates],
        color="#d1765d",
    )
    axes[1].set_ylabel("extra exact direct points over 17 conditions")
    axes[1].set_title("Additional oracle information")
    axes[1].grid(axis="y", alpha=0.25)
    for axis in axes:
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=48, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_report(
    output: Path,
    aggregates: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> None:
    index = {row["strategy_id"]: row for row in aggregates}
    local_lih = next(
        row
        for row in rows
        if row["condition"] == "LiH_CAS2e4o"
        and row["strategy_id"] == "current_three_point_local_search"
    )
    full_lih = next(
        row
        for row in rows
        if row["condition"] == "LiH_CAS2e4o"
        and row["strategy_id"] == "current_full_saved_grid_oracle_reference"
    )
    lines = [
        "# X01 A08: simple-alternative comparison",
        "",
        "Status: complete",
        "",
        "All rules are scored on the same 17 saved development conditions. The fixed "
        "1% budget multiplier and 0.9*t_star cap are declared before inspecting "
        "condition outcomes. Direct-point searches are reported separately because "
        "they consume exact PF-error truth.",
        "",
        "## Results",
        "",
        "| strategy | pass | basket cost ratio | min/median/max condition ratio | base points | extra direct points | validation truth used |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in aggregates:
        lines.append(
            f"| {row['strategy_label']} | {row['saved_condition_passed']}/17 | "
            f"{row['equal_one_run_basket_cost_ratio']:.6f} | "
            f"{row['minimum_quantum_cost_ratio']:.6f}/"
            f"{row['median_quantum_cost_ratio']:.6f}/"
            f"{row['maximum_quantum_cost_ratio']:.6f} | "
            f"{row['base_calibration_points_over_17']} | "
            f"{row['extra_direct_diagnostic_points_over_17']} | "
            f"{row['validation_truth_used_for_decision']} |"
        )
    lines += [
        "",
        "## Inputs, complexity, and worst saved case",
        "",
        "| strategy | implementation | required input | worst condition cost ratio |",
        "|---|---|---|---:|",
    ]
    for row in aggregates:
        lines.append(
            f"| {row['strategy_label']} | {row['implementation_complexity']} | "
            f"{row['required_input']} | {row['maximum_quantum_cost_ratio']:.6f} "
            f"(`{row['maximum_quantum_cost_ratio_condition']}`) |"
        )
    fixed_margin = index["current_two_term_plus_1pct_budget"]
    time_cap = index["current_two_term_time_cap_0p9"]
    new_margin = index["new_two_term_plus_1pct_budget"]
    one_point = index["current_one_direct_check_tstar"]
    three_point = index["current_three_point_local_search"]
    lines += [
        "",
        "## Pre-fixed rules without validation truth",
        "",
        "The unmodified `current_m3` two-term schedule already passes the strict "
        "saved frozen budget on 17/17. Adding a fixed 1% QPE-budget margin also passes "
        f"17/17 at an exact basket premium of {100.0 * (fixed_margin['equal_one_run_basket_cost_ratio'] - 1.0):.6g}%. "
        "The fixed 0.9*t_star cap passes 17/17 but costs "
        f"{100.0 * (time_cap['equal_one_run_basket_cost_ratio'] - 1.0):.6g}% more in "
        "the equal-one-run basket. Neither simple safeguard is needed to repair a "
        "saved baseline failure, but both remain much cheaper than changing PF.",
        "",
        "Applying the same pre-fixed 1% budget margin to `two_term_center` also passes "
        f"17/17, with basket cost ratio {new_margin['equal_one_run_basket_cost_ratio']:.6f} "
        "relative to unmodified `current_m3` two-term.",
        "",
        "## Additional direct-point alternatives",
        "",
        "One exact direct check at t_star permits direct budget repair and has basket "
        f"ratio {one_point['equal_one_run_basket_cost_ratio']:.6f}, but adds 17 exact "
        "PF-eigenvalue points. The three-point search adds 51 points and changes the "
        f"selected time only on {three_point['conditions_selecting_nonunit_relative_time']} "
        "condition. That condition is `LiH_CAS2e4o`, where it selects "
        f"{local_lih['selected_relative_to_t_star']:.1f}*t_star and reduces cost to "
        f"{local_lih['quantum_cost_ratio_to_current_two_term_t_star']:.6f} of the "
        "model-schedule baseline.",
        "",
        "The full adaptive saved grid finds the LiH endpoint at "
        f"{full_lih['selected_relative_to_t_star']:.1f}*t_star with ratio "
        f"{full_lih['quantum_cost_ratio_to_current_two_term_t_star']:.6f}, but this is "
        "an oracle finite-grid reference with many extra exact points, not a simple "
        "model-only rule or a continuous optimum claim.",
        "",
        "## Higher-order baseline",
        "",
        "A one-order-higher PF is not scored here because no complete result exists on "
        "the same 17 Hamiltonians with the same target, calibration budget, and direct "
        "scoring protocol. Results from different H-chain or probe sets are not mixed "
        "into this comparison.",
        "",
        "## A08 conclusion",
        "",
        "On the saved development conditions, the new PF does not beat the simplest "
        "strong baseline. `current_m3` plus the two-term model is already 17/17 under "
        "the operational frozen-budget score and is cheaper than both pre-fixed safety "
        "variants and the safety-adjusted new PF. Additional direct points can lower "
        "cost, especially for LiH, but they rely on the exact-state oracle identified "
        "in A06 and increase classical calibration effort.",
        "",
        "This is not an unseen-system guarantee: the rules are scored on correlated "
        "development conditions, and the absence of a common high-order dataset "
        "leaves the order-raising alternative unresolved.",
        "",
        "## Files",
        "",
        "- `strategy_rows.csv`: condition-level scores and information budgets.",
        "- `strategy_summary.csv`: aggregate simple-baseline comparison.",
        "- `baseline_availability.csv`: completed and unavailable baselines.",
        "- `simple_alternatives.png`: quantum cost versus extra direct information.",
        "- `raw_sources.csv`: hashes of the 17 reused raw files.",
        "- `analysis.json` and `manifest.json`: summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    budget = a05.run_analysis()
    cost_benefit = a07.run_analysis()
    rows = strategy_rows(
        budget["_rows"],
        cost_benefit["_calibration_rows"],
        cost_benefit["_raw_sources"],
    )
    aggregates = aggregate_rows(rows)
    availability = availability_rows()
    truth_free = [
        row
        for row in rows
        if not row["validation_truth_used_for_decision"]
        and row["saved_condition_pass"]
    ]
    conditions = sorted({str(row["condition"]) for row in rows})
    truth_free_winners = {
        condition: min(
            (row for row in truth_free if row["condition"] == condition),
            key=lambda row: float(row["quantum_cost"]),
        )["strategy_id"]
        for condition in conditions
    }
    return {
        "status": "complete",
        "scope": "X01 A08 simple-alternative comparison",
        "created_at": datetime.now().astimezone().isoformat(),
        "condition_count": len(conditions),
        "strategy_count": len(aggregates),
        "strategy_row_count": len(rows),
        "fixed_budget_margin": FIXED_BUDGET_MARGIN,
        "fixed_time_cap_relative_to_t_star": FIXED_TIME_CAP_RELATIVE_TO_T_STAR,
        "local_search_relative_times": list(LOCAL_SEARCH_RELATIVE_TIMES),
        "truth_free_current_two_term_winner_count": sum(
            value == "current_two_term_tstar" for value in truth_free_winners.values()
        ),
        "higher_order_status": "not compared on the same 17-condition protocol",
        "source_records": budget["source_records"],
        "raw_source_count": len(cost_benefit["_raw_sources"]),
        "git": audit_x01.git_state(),
        "strategy_summary_rows": aggregates,
        "availability_rows": availability,
        "_strategy_rows": rows,
        "_raw_sources": cost_benefit["_raw_sources"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_analysis()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    a05.write_csv(output / "strategy_rows.csv", result["_strategy_rows"])
    a05.write_csv(output / "strategy_summary.csv", result["strategy_summary_rows"])
    a05.write_csv(output / "baseline_availability.csv", result["availability_rows"])
    a05.write_csv(output / "raw_sources.csv", result["_raw_sources"])
    make_plot(output / "simple_alternatives.png", result["strategy_summary_rows"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    a05.write_json(output / "analysis.json", machine)
    a05.write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "source_records": result["source_records"],
            "raw_source_count": result["raw_source_count"],
            "git": result["git"],
            "no_new_pf_or_electronic_structure_calculation": True,
            "fixed_safety_rules_optimized_on_condition_truth": False,
            "oracle_direct_searches_separately_labeled": True,
            "higher_order_result_mixed_from_other_conditions": False,
            "existing_input_artifacts_overwritten": False,
        },
    )
    make_report(output, result["strategy_summary_rows"], result["_strategy_rows"])
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
