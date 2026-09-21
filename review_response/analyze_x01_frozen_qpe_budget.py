"""X01/A05 audit of frozen QPE budgets at model-selected schedules.

For every saved fixed-PF/model comparison, this analysis freezes the time and
continuous QPE cost selected from the error model.  It then substitutes the
saved direct PF eigenvalue error and checks the additive error budget without
re-optimizing the schedule or QPE precision.

No electronic-structure, PF-unitary, eigensolver, or QPE sampling calculation
is performed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import statistics
from typing import Any, Iterable

import audit_existing_results_x01 as audit_x01
import analyze_x01_pf_model_threshold_sensitivity as a03_a04


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_x01_frozen_qpe_budget_20260921"

EPSILON_E = 1.5936001019904e-4
BETA = 1.2
ARITHMETIC_TOLERANCE_HARTREE = EPSILON_E * 1e-12
PFS = a03_a04.PFS
MODELS = a03_a04.MODELS
SOURCE_DATASETS = (
    (audit_x01.DEFAULT_FIVE, "five_condition_holdout"),
    (audit_x01.DEFAULT_TWELVE, "twelve_condition_holdout"),
)


def score_frozen_budget(
    *,
    time: float,
    rotations: int,
    model_signed_shift: float,
    direct_signed_shift: float,
    frozen_cost: float,
    target_error: float = EPSILON_E,
    beta: float = BETA,
) -> dict[str, Any]:
    """Score one frozen continuous-cost allocation under the additive model."""
    if time <= 0.0 or rotations <= 0 or frozen_cost <= 0.0:
        raise ValueError("time, rotations, and frozen cost must be positive")
    model_error = abs(float(model_signed_shift))
    direct_error = abs(float(direct_signed_shift))
    if model_error >= target_error:
        raise ValueError("model PF error leaves no QPE error budget")
    frozen_qpe_error = float(beta) * int(rotations) / (time * frozen_cost)
    predicted_qpe_allowance = target_error - model_error
    actual_total_error_bound = direct_error + frozen_qpe_error
    budget_margin = target_error - actual_total_error_bound
    strict_pass = actual_total_error_bound <= target_error
    tolerance_pass = budget_margin >= -ARITHMETIC_TOLERANCE_HARTREE
    if direct_error > model_error + ARITHMETIC_TOLERANCE_HARTREE:
        direction = "underestimated_pf_error"
    elif model_error > direct_error + ARITHMETIC_TOLERANCE_HARTREE:
        direction = "conservative_pf_error"
    else:
        direction = "matched_within_arithmetic_tolerance"
    required_cost = (
        float(beta)
        * int(rotations)
        / (time * (target_error - direct_error))
        if direct_error < target_error
        else None
    )
    cost_ratio = frozen_cost / required_cost if required_cost is not None else None
    return {
        "model_error_hartree": model_error,
        "direct_error_hartree": direct_error,
        "predicted_qpe_allowance_hartree": predicted_qpe_allowance,
        "frozen_qpe_error_hartree": frozen_qpe_error,
        "qpe_allowance_reproduction_difference_hartree": abs(
            predicted_qpe_allowance - frozen_qpe_error
        ),
        "actual_total_error_bound_hartree": actual_total_error_bound,
        "actual_total_error_over_target": actual_total_error_bound / target_error,
        "budget_margin_hartree": budget_margin,
        "target_excess_hartree": max(-budget_margin, 0.0),
        "target_excess_over_epsilon": max(-budget_margin, 0.0) / target_error,
        "strict_frozen_budget_pass": strict_pass,
        "tolerance_frozen_budget_pass": tolerance_pass,
        "pf_error_direction": direction,
        "required_direct_cost": required_cost,
        "frozen_over_required_cost_ratio": cost_ratio,
        "additional_cost_fraction_needed": (
            max(required_cost / frozen_cost - 1.0, 0.0)
            if required_cost is not None
            else None
        ),
        "avoidable_cost_fraction_vs_direct": (
            max(frozen_cost / required_cost - 1.0, 0.0)
            if required_cost is not None
            else None
        ),
        "pf_error_underestimate_hartree": max(direct_error - model_error, 0.0),
        "pf_error_overestimate_hartree": max(model_error - direct_error, 0.0),
    }


def _relative_difference(left: float, right: float) -> float:
    return abs(left - right) / abs(right)


def collect_budget_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    a03_a04.validate_factorial_design_sources()
    source_audit = audit_x01.run_audit(
        audit_x01.DEFAULT_FIVE,
        audit_x01.DEFAULT_TWELVE,
        audit_x01.DEFAULT_JOINT,
    )
    fixed = a03_a04.fixed_comparison_rows(source_audit)
    audit_index = {
        (row["dataset_id"], row["condition"], row["pf"], row["model"]): row
        for row in fixed
    }
    rows: list[dict[str, Any]] = []
    for source_path, dataset_id in SOURCE_DATASETS:
        payload = audit_x01.load_json(source_path)
        for record in payload["records"]:
            rotations = int(record["rotations_per_pf_step"])
            for model_name in MODELS:
                model = record["models"][model_name]
                point = model["predicted_time_direct_point"]
                time = float(point["time"])
                model_shift = float(model["predicted_time_model_shift_hartree"])
                direct_shift = float(point["signed_direct_shift_hartree"])
                frozen_cost = float(model["predicted_time_model_cost"])
                stored_direct_cost = float(point["direct_cost"])
                scored = score_frozen_budget(
                    time=time,
                    rotations=rotations,
                    model_signed_shift=model_shift,
                    direct_signed_shift=direct_shift,
                    frozen_cost=frozen_cost,
                )
                model_cost_recomputed = (
                    BETA
                    * rotations
                    / (time * (EPSILON_E - abs(model_shift)))
                )
                direct_cost_recomputed = (
                    BETA
                    * rotations
                    / (time * (EPSILON_E - abs(direct_shift)))
                )
                model_cost_difference = _relative_difference(
                    model_cost_recomputed, frozen_cost
                )
                direct_cost_difference = _relative_difference(
                    direct_cost_recomputed, stored_direct_cost
                )
                if model_cost_difference > 5e-12 or direct_cost_difference > 5e-12:
                    raise ValueError(
                        f"cost identity mismatch for {record['condition']} / "
                        f"{record['formula']} / {model_name}"
                    )
                audit_row = audit_index[
                    (dataset_id, record["condition"], record["formula"], model_name)
                ]
                eta_star = float(audit_row["eta_star"])
                cost_prediction_pass = (
                    eta_star <= audit_x01.CANONICAL_THRESHOLDS["eta_star"]
                )
                metadata = a03_a04._condition_metadata(str(record["condition"]))
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "condition": record["condition"],
                        **metadata,
                        "pf": record["formula"],
                        "model": model_name,
                        "target_error_hartree": EPSILON_E,
                        "beta": BETA,
                        "rotations_per_pf_step": rotations,
                        "selected_time": time,
                        "model_signed_shift_hartree": model_shift,
                        "direct_signed_shift_hartree": direct_shift,
                        "signed_shift_residual_hartree": direct_shift - model_shift,
                        "frozen_model_cost": frozen_cost,
                        "stored_direct_required_cost": stored_direct_cost,
                        **scored,
                        "model_cost_reproduction_relative_difference": (
                            model_cost_difference
                        ),
                        "direct_cost_reproduction_relative_difference": (
                            direct_cost_difference
                        ),
                        "stored_eta_star": eta_star,
                        "eta_star_1pct_pass": cost_prediction_pass,
                        "four_metric_pass": bool(audit_row["recomputed_pass"]),
                        "eta_min": float(audit_row["eta_min"]),
                        "eta_t": float(audit_row["eta_t"]),
                        "maximum_unseen_residual_over_epsilon": float(
                            audit_row["maximum_unseen_residual_over_epsilon"]
                        ),
                        "source": str(source_path.relative_to(ROOT)),
                    }
                )
    if len(rows) != 102:
        raise ValueError(f"expected 102 frozen-budget rows, got {len(rows)}")
    provenance = {
        "source_records": source_audit["source_records"][:2],
        "fixed_metric_rows_reproduced": sum(
            bool(row["metric_reproduction_pass"]) for row in fixed
        ),
        "fixed_pass_rows_reproduced": sum(bool(row["pass_matches"]) for row in fixed),
        "git": audit_x01.git_state(),
    }
    return rows, provenance


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for pf in PFS:
        for model in MODELS:
            selected = [row for row in rows if row["pf"] == pf and row["model"] == model]
            worst_excess = max(
                selected, key=lambda row: float(row["target_excess_over_epsilon"])
            )
            worst_additional = max(
                selected,
                key=lambda row: float(row["additional_cost_fraction_needed"]),
            )
            worst_avoidable = max(
                selected,
                key=lambda row: float(row["avoidable_cost_fraction_vs_direct"]),
            )
            maximum_excess = float(worst_excess["target_excess_over_epsilon"])
            maximum_additional = float(
                worst_additional["additional_cost_fraction_needed"]
            )
            maximum_avoidable = float(
                worst_avoidable["avoidable_cost_fraction_vs_direct"]
            )
            result.append(
                {
                    "pf": pf,
                    "model": model,
                    "total": len(selected),
                    "four_metric_passed": sum(
                        bool(row["four_metric_pass"]) for row in selected
                    ),
                    "eta_star_1pct_passed": sum(
                        bool(row["eta_star_1pct_pass"]) for row in selected
                    ),
                    "strict_frozen_budget_passed": sum(
                        bool(row["strict_frozen_budget_pass"]) for row in selected
                    ),
                    "tolerance_frozen_budget_passed": sum(
                        bool(row["tolerance_frozen_budget_pass"]) for row in selected
                    ),
                    "conservative_pf_error_count": sum(
                        row["pf_error_direction"] == "conservative_pf_error"
                        for row in selected
                    ),
                    "underestimated_pf_error_count": sum(
                        row["pf_error_direction"] == "underestimated_pf_error"
                        for row in selected
                    ),
                    "metric_fail_but_frozen_safe": sum(
                        not bool(row["four_metric_pass"])
                        and bool(row["strict_frozen_budget_pass"])
                        for row in selected
                    ),
                    "metric_pass_but_frozen_fail": sum(
                        bool(row["four_metric_pass"])
                        and not bool(row["strict_frozen_budget_pass"])
                        for row in selected
                    ),
                    "eta_star_fail_but_frozen_safe": sum(
                        not bool(row["eta_star_1pct_pass"])
                        and bool(row["strict_frozen_budget_pass"])
                        for row in selected
                    ),
                    "eta_star_pass_but_frozen_fail": sum(
                        bool(row["eta_star_1pct_pass"])
                        and not bool(row["strict_frozen_budget_pass"])
                        for row in selected
                    ),
                    "maximum_target_excess_over_epsilon": maximum_excess,
                    "maximum_target_excess_condition": (
                        worst_excess["condition"] if maximum_excess > 0.0 else None
                    ),
                    "maximum_additional_cost_fraction_needed": maximum_additional,
                    "maximum_additional_cost_condition": (
                        worst_additional["condition"]
                        if maximum_additional > 0.0
                        else None
                    ),
                    "maximum_avoidable_cost_fraction_vs_direct": maximum_avoidable,
                    "maximum_avoidable_cost_condition": (
                        worst_avoidable["condition"]
                        if maximum_avoidable > 0.0
                        else None
                    ),
                    "required_uniform_cost_multiplier_on_saved_conditions": max(
                        1.0,
                        max(
                            float(row["required_direct_cost"])
                            / float(row["frozen_model_cost"])
                            for row in selected
                        ),
                    ),
                    "required_uniform_pf_error_margin_hartree": max(
                        float(row["pf_error_underestimate_hartree"])
                        for row in selected
                    ),
                    "required_uniform_pf_error_margin_over_epsilon": max(
                        float(row["pf_error_underestimate_hartree"]) / EPSILON_E
                        for row in selected
                    ),
                    "median_frozen_over_required_cost_ratio": statistics.median(
                        float(row["frozen_over_required_cost_ratio"])
                        for row in selected
                    ),
                }
            )
    return result


def contingency_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    criteria = (
        ("four_metric", "four_metric_pass"),
        ("eta_star_1pct", "eta_star_1pct_pass"),
    )
    for criterion_name, criterion_key in criteria:
        for pf in PFS:
            for model in MODELS:
                selected = [
                    row for row in rows if row["pf"] == pf and row["model"] == model
                ]
                result.append(
                    {
                        "criterion": criterion_name,
                        "pf": pf,
                        "model": model,
                        "criterion_pass_and_frozen_pass": sum(
                            bool(row[criterion_key])
                            and bool(row["strict_frozen_budget_pass"])
                            for row in selected
                        ),
                        "criterion_pass_but_frozen_fail": sum(
                            bool(row[criterion_key])
                            and not bool(row["strict_frozen_budget_pass"])
                            for row in selected
                        ),
                        "criterion_fail_but_frozen_pass": sum(
                            not bool(row[criterion_key])
                            and bool(row["strict_frozen_budget_pass"])
                            for row in selected
                        ),
                        "criterion_fail_and_frozen_fail": sum(
                            not bool(row[criterion_key])
                            and not bool(row["strict_frozen_budget_pass"])
                            for row in selected
                        ),
                        "total": len(selected),
                    }
                )
    return result


def cluster_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    clusters = sorted({str(row["analysis_cluster"]) for row in rows})
    for cluster in clusters:
        for pf in PFS:
            for model in MODELS:
                selected = [
                    row
                    for row in rows
                    if row["analysis_cluster"] == cluster
                    and row["pf"] == pf
                    and row["model"] == model
                ]
                result.append(
                    {
                        "analysis_cluster": cluster,
                        "pf": pf,
                        "model": model,
                        "condition_count": len(selected),
                        "four_metric_passed": sum(
                            bool(row["four_metric_pass"]) for row in selected
                        ),
                        "strict_frozen_budget_passed": sum(
                            bool(row["strict_frozen_budget_pass"]) for row in selected
                        ),
                        "maximum_target_excess_over_epsilon": max(
                            float(row["target_excess_over_epsilon"])
                            for row in selected
                        ),
                        "conditions": ";".join(
                            sorted(str(row["condition"]) for row in selected)
                        ),
                    }
                )
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def make_plot(path: Path, aggregates: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [
        f"{row['pf']}\n{row['model'].replace('_', ' ')}" for row in aggregates
    ]
    x = np.arange(len(aggregates))
    width = 0.25
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0))
    axes[0].bar(
        x - width,
        [row["four_metric_passed"] for row in aggregates],
        width,
        label="four-metric pass",
        color="#6a8fd5",
    )
    axes[0].bar(
        x,
        [row["eta_star_1pct_passed"] for row in aggregates],
        width,
        label="eta* <= 1%",
        color="#79b59b",
    )
    axes[0].bar(
        x + width,
        [row["strict_frozen_budget_passed"] for row in aggregates],
        width,
        label="strict frozen-budget pass",
        color="#d1765d",
    )
    axes[0].set_ylabel("conditions / 17")
    axes[0].set_ylim(0, 18)
    axes[0].set_title("Prediction criteria versus frozen-budget outcome")
    axes[0].legend(fontsize=8)

    axes[1].bar(
        x - width / 2,
        [100.0 * row["maximum_avoidable_cost_fraction_vs_direct"] for row in aggregates],
        width,
        label="maximum avoidable overbudget",
        color="#6a8fd5",
    )
    axes[1].bar(
        x + width / 2,
        [100.0 * row["maximum_additional_cost_fraction_needed"] for row in aggregates],
        width,
        label="maximum extra cost needed",
        color="#d1765d",
    )
    axes[1].set_ylabel("cost difference (%)")
    axes[1].set_yscale("log")
    axes[1].set_ylim(0.005, 10.0)
    axes[1].set_title("Magnitude under the continuous cost model (log scale)")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_report(
    output: Path,
    aggregates: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> None:
    lookup = {(row["pf"], row["model"]): row for row in aggregates}
    failures = [row for row in rows if not row["strict_frozen_budget_pass"]]
    worst = max(failures, key=lambda row: float(row["target_excess_over_epsilon"]))
    safe_rejections = sum(
        not bool(row["eta_star_1pct_pass"])
        and bool(row["strict_frozen_budget_pass"])
        for row in rows
    )
    false_assurances = sum(
        bool(row["eta_star_1pct_pass"])
        and not bool(row["strict_frozen_budget_pass"])
        for row in rows
    )
    center_two = lookup[("two_term_center", "two_term")]
    lines = [
        "# X01 A05: frozen QPE budget audit",
        "",
        "Status: complete",
        "",
        "The model-selected time and continuous QPE cost are frozen before the saved "
        "direct PF eigenvalue error is substituted. No schedule or budget is repaired "
        "using the direct value.",
        "",
        "## Definition",
        "",
        "For frozen model cost `C_model`, the implied QPE error is "
        "`beta*N_rot/(t*C_model)`. The strict score is "
        "`abs(deltaE_direct) + epsilon_QPE <= epsilon_E`, with "
        f"`epsilon_E={EPSILON_E:.16g}` Hartree and `beta={BETA}`. This is the "
        "repository's additive continuous-cost proxy, not a stochastic QPE run or "
        "a hardware-level success guarantee.",
        "",
        "## Results",
        "",
        "| PF | model | four-metric pass | eta* pass | frozen-budget pass | conservative / underestimated | max target excess / eps | max extra cost needed | max avoidable overbudget |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregates:
        lines.append(
            f"| {row['pf']} | {row['model']} | {row['four_metric_passed']}/17 | "
            f"{row['eta_star_1pct_passed']}/17 | "
            f"{row['strict_frozen_budget_passed']}/17 | "
            f"{row['conservative_pf_error_count']} / {row['underestimated_pf_error_count']} | "
            f"{row['maximum_target_excess_over_epsilon']:.6g} | "
            f"{100.0 * row['maximum_additional_cost_fraction_needed']:.6g}% | "
            f"{100.0 * row['maximum_avoidable_cost_fraction_vs_direct']:.6g}% |"
        )
    lines += [
        "",
        f"Across all 102 rows, {safe_rejections} fail the symmetric 1% cost-prediction "
        "test but still meet the strict frozen additive budget because their PF error "
        f"was overestimated. Conversely, {false_assurances} pass the 1% test but miss "
        "the strict frozen budget because even a small underestimation consumes more "
        "than the allocated PF-error share.",
        "",
        "All 51 `current_m3` rows are conservative and meet the frozen budget, even "
        "though many fail the prediction criteria. The `two_term_center` one-term rows "
        "are also conservative. For `two_term_center` plus the two-term model, "
        f"{center_two['strict_frozen_budget_passed']}/17 pass strictly and "
        f"{center_two['underestimated_pf_error_count']}/17 underestimate the PF error.",
        "",
        "All eight strict misses occur in stretched BeH2 or H2O conditions, "
        "including their basis variants; the saved equilibrium, active-space, "
        "H-chain, and NH3 conditions do not show this under-budget direction.",
        "",
        f"The worst strict miss is `{worst['condition']}`: target excess "
        f"{worst['target_excess_hartree']:.6g} Hartree "
        f"({worst['target_excess_over_epsilon']:.6g} epsilon), requiring only "
        f"{100.0 * worst['additional_cost_fraction_needed']:.6g}% more continuous "
        "cost than frozen. Over all 17 saved conditions, a uniform multiplier of "
        f"{center_two['required_uniform_cost_multiplier_on_saved_conditions']:.9f} "
        "would remove these strict misses. This is an empirical margin for these "
        "saved conditions, not an unseen-system guarantee.",
        "",
        "## A05 conclusion",
        "",
        "The symmetric prediction thresholds do not directly measure operational "
        "harm. Many formally failed, conservative predictions remain safe but spend "
        "up to about 5.3% extra cost. The most accurate PF/model cell has the opposite "
        "issue: tiny one-sided underestimates create strict budget misses, although "
        "their maximum repair cost is about 0.0124%. Therefore model ranking should "
        "report direction and frozen-budget margin, not only absolute cost error.",
        "",
        "## Scope",
        "",
        "The 17 conditions are five correlated development clusters. QPE integer "
        "rounding, synthesis error, stochastic success probability, and state "
        "preparation are outside this saved-data audit.",
        "",
        "## Files",
        "",
        "- `frozen_budget_rows.csv`: all 102 frozen allocations and direct scores.",
        "- `aggregate.csv`: PF/model outcomes and required empirical margins.",
        "- `decision_contingency.csv`: prediction-pass versus frozen-pass tables.",
        "- `frozen_budget_failures.csv`: the strict budget misses.",
        "- `safe_prediction_rejections.csv`: prediction failures that remain safe.",
        "- `cluster_summary.csv`: correlated-cluster summaries.",
        "- `frozen_budget_outcomes.png`: lightweight comparison figure.",
        "- `analysis.json` and `manifest.json`: summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    rows, provenance = collect_budget_rows()
    aggregates = aggregate_rows(rows)
    contingencies = contingency_rows(rows)
    clusters = cluster_summary_rows(rows)
    failures = [row for row in rows if not row["strict_frozen_budget_pass"]]
    safe_rejections = [
        row
        for row in rows
        if not row["eta_star_1pct_pass"] and row["strict_frozen_budget_pass"]
    ]
    return {
        "status": "complete",
        "scope": "X01 A05 frozen continuous-QPE-budget audit",
        "created_at": datetime.now().astimezone().isoformat(),
        "target_error_hartree": EPSILON_E,
        "beta": BETA,
        "arithmetic_tolerance_hartree": ARITHMETIC_TOLERANCE_HARTREE,
        "budget_model": "beta*N_rot/(t*(epsilon_E-abs(deltaE_model)))",
        "score_rule": "abs(deltaE_direct)+beta*N_rot/(t*C_frozen) <= epsilon_E",
        "row_count": len(rows),
        "strict_frozen_budget_pass_count": sum(
            bool(row["strict_frozen_budget_pass"]) for row in rows
        ),
        "strict_frozen_budget_failure_count": len(failures),
        "eta_star_fail_but_frozen_safe_count": len(safe_rejections),
        "eta_star_pass_but_frozen_fail_count": sum(
            bool(row["eta_star_1pct_pass"])
            and not bool(row["strict_frozen_budget_pass"])
            for row in rows
        ),
        "maximum_model_cost_reproduction_relative_difference": max(
            float(row["model_cost_reproduction_relative_difference"])
            for row in rows
        ),
        "maximum_direct_cost_reproduction_relative_difference": max(
            float(row["direct_cost_reproduction_relative_difference"])
            for row in rows
        ),
        "maximum_qpe_allowance_reproduction_difference_hartree": max(
            float(row["qpe_allowance_reproduction_difference_hartree"])
            for row in rows
        ),
        **provenance,
        "aggregate_rows": aggregates,
        "contingency_rows": contingencies,
        "cluster_rows": clusters,
        "_rows": rows,
        "_failure_rows": failures,
        "_safe_rejection_rows": safe_rejections,
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
    write_csv(output / "frozen_budget_rows.csv", result["_rows"])
    write_csv(output / "aggregate.csv", result["aggregate_rows"])
    write_csv(output / "decision_contingency.csv", result["contingency_rows"])
    write_csv(output / "frozen_budget_failures.csv", result["_failure_rows"])
    write_csv(
        output / "safe_prediction_rejections.csv",
        result["_safe_rejection_rows"],
    )
    write_csv(output / "cluster_summary.csv", result["cluster_rows"])
    make_plot(output / "frozen_budget_outcomes.png", result["aggregate_rows"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    write_json(output / "analysis.json", machine)
    write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "source_records": result["source_records"],
            "git": result["git"],
            "no_new_pf_or_electronic_structure_calculation": True,
            "schedule_reoptimized_with_direct_error": False,
            "qpe_budget_repaired_with_direct_error": False,
            "continuous_cost_proxy_only": True,
            "existing_input_artifacts_overwritten": False,
        },
    )
    make_report(output, result["aggregate_rows"], result["_rows"])
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
