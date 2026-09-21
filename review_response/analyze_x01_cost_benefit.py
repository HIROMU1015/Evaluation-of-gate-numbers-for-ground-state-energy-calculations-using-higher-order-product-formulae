"""X01/A07 cost-benefit audit for current_m3 versus two_term_center.

This analysis compares saved calibration effort and margin-adjusted continuous
QPE cost after equalizing frozen-budget success on the 17 saved development
conditions.  It performs no new PF, electronic-structure, eigensolver, or QPE
calculation.  Quantum cost units and classical seconds are kept separate.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import statistics
from typing import Any

import audit_existing_results_x01 as audit_x01
import analyze_x01_frozen_qpe_budget as a05


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_x01_cost_benefit_20260921"

RAW_DIR_BY_DATASET = {
    "five_condition_holdout": (
        ROOT / "artifacts/two_term_pf_m3_holdout_server2_20260910_d2360f4_cpu"
    ),
    "twelve_condition_holdout": (
        ROOT / "artifacts/two_term_pf_geometry_local_20260911"
    ),
}
REUSE_COUNTS = (1, 2, 5, 10, 50, 100, 1000)


def collect_calibration_rows(
    budget_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    budget_index = {
        (row["dataset_id"], row["condition"], row["pf"], row["model"]): row
        for row in budget_rows
    }
    conditions_by_dataset: dict[str, set[str]] = {}
    for row in budget_rows:
        conditions_by_dataset.setdefault(str(row["dataset_id"]), set()).add(
            str(row["condition"])
        )
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for dataset_id, conditions in sorted(conditions_by_dataset.items()):
        root = RAW_DIR_BY_DATASET[dataset_id]
        for condition in sorted(conditions):
            path = root / f"{condition}.json"
            payload = audit_x01.load_json(path)
            if payload.get("status") != "complete":
                raise ValueError(f"raw calibration source is incomplete: {path}")
            sources.append(
                {
                    "dataset_id": dataset_id,
                    "condition": condition,
                    "path": str(path.relative_to(ROOT)),
                    "sha256": audit_x01.sha256_file(path),
                    "status": payload.get("status"),
                }
            )
            for pf in a05.PFS:
                formula = payload["formulas"][pf]
                short_points = formula["short_time_fit"]["points"]
                direct_points = formula["training_direct_points"]
                selected_window_points = int(
                    formula["short_time_fit"]["selected_window"]["num_points"]
                )
                if (
                    len(short_points) < 5
                    or selected_window_points != 5
                    or len(direct_points) != 3
                ):
                    raise ValueError(
                        f"unexpected calibration point count for {condition}/{pf}"
                    )
                if not all(point.get("used_for_two_term_fit") for point in direct_points):
                    raise ValueError(f"not all direct points were used for {condition}/{pf}")
                short_seconds = float(formula["short_time_fit"]["elapsed_seconds"])
                direct_seconds = sum(
                    float(point["timing_seconds"]["total"])
                    for point in direct_points
                )
                reference = budget_index[(dataset_id, condition, pf, "two_term")]
                if int(formula["rotations_per_pf_step"]) != int(
                    reference["rotations_per_pf_step"]
                ):
                    raise ValueError(f"rotation mismatch for {condition}/{pf}")
                optimum = formula["two_term_model_optimum"]
                if not (
                    abs(float(optimum["time"]) - float(reference["selected_time"]))
                    <= 1e-12
                    and abs(
                        float(optimum["cost"])
                        - float(reference["frozen_model_cost"])
                    )
                    <= 1e-6
                ):
                    raise ValueError(f"two-term optimum mismatch for {condition}/{pf}")
                rows.append(
                    {
                        "dataset_id": dataset_id,
                        "condition": condition,
                        "analysis_cluster": reference["analysis_cluster"],
                        "pf": pf,
                        "short_time_proxy_point_count": len(short_points),
                        "selected_short_time_window_point_count": (
                            selected_window_points
                        ),
                        "direct_fit_point_count": len(direct_points),
                        "total_calibration_point_count": len(short_points)
                        + len(direct_points),
                        "short_time_proxy_seconds": short_seconds,
                        "direct_fit_seconds": direct_seconds,
                        "total_calibration_seconds": short_seconds + direct_seconds,
                        "shared_system_preparation_seconds": float(
                            payload["system"].get("preparation_seconds", 0.0)
                        ),
                        "shared_system_preparation_included": False,
                        "timing_scope": (
                            "saved PF-specific short-time fit plus three direct "
                            "training points; shared system preparation and validation "
                            "points excluded"
                        ),
                        "source": str(path.relative_to(ROOT)),
                    }
                )
    if len(rows) != 34 or len(sources) != 17:
        raise ValueError(
            f"expected 34 calibration rows and 17 sources, got {len(rows)} and "
            f"{len(sources)}"
        )
    return rows, sources


def strategy_rows(
    budget_rows: list[dict[str, Any]],
    budget_aggregates: list[dict[str, Any]],
    calibration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate_index = {
        (row["pf"], row["model"]): row for row in budget_aggregates
    }
    calibration_index = {
        (row["condition"], row["pf"]): row for row in calibration_rows
    }
    budget_index = {
        (row["condition"], row["pf"], row["model"]): row for row in budget_rows
    }
    conditions = sorted({str(row["condition"]) for row in budget_rows})
    result: list[dict[str, Any]] = []
    for condition in conditions:
        baseline = budget_index[(condition, "current_m3", "two_term")]
        baseline_cost = float(baseline["frozen_model_cost"])
        for pf in a05.PFS:
            calibration = calibration_index[(condition, pf)]
            for model in a05.MODELS:
                budget = budget_index[(condition, pf, model)]
                aggregate = aggregate_index[(pf, model)]
                multiplier = float(
                    aggregate[
                        "required_uniform_cost_multiplier_on_saved_conditions"
                    ]
                )
                adjusted_cost = float(budget["frozen_model_cost"]) * multiplier
                adjusted_qpe_error = (
                    a05.BETA
                    * int(budget["rotations_per_pf_step"])
                    / (float(budget["selected_time"]) * adjusted_cost)
                )
                adjusted_total_error = (
                    float(budget["direct_error_hartree"]) + adjusted_qpe_error
                )
                result.append(
                    {
                        "dataset_id": budget["dataset_id"],
                        "condition": condition,
                        "analysis_cluster": budget["analysis_cluster"],
                        "pf": pf,
                        "model": model,
                        "four_metric_pass": bool(budget["four_metric_pass"]),
                        "strict_frozen_budget_pass_before_margin": bool(
                            budget["strict_frozen_budget_pass"]
                        ),
                        "empirical_uniform_cost_multiplier": multiplier,
                        "margin_adjusted_frozen_cost": adjusted_cost,
                        "margin_adjusted_total_error_hartree": adjusted_total_error,
                        "margin_adjusted_pass_on_saved_conditions": bool(
                            adjusted_total_error
                            <= a05.EPSILON_E + a05.ARITHMETIC_TOLERANCE_HARTREE
                        ),
                        "margin_adjusted_cost_ratio_to_current_m3_two_term": (
                            adjusted_cost / baseline_cost
                        ),
                        "oracle_direct_required_cost": budget[
                            "stored_direct_required_cost"
                        ],
                        "oracle_direct_cost_ratio_to_current_m3_two_term": (
                            float(budget["stored_direct_required_cost"])
                            / float(baseline["stored_direct_required_cost"])
                        ),
                        "short_time_proxy_point_count": calibration[
                            "short_time_proxy_point_count"
                        ],
                        "direct_fit_point_count": calibration[
                            "direct_fit_point_count"
                        ],
                        "total_calibration_point_count": calibration[
                            "total_calibration_point_count"
                        ],
                        "total_calibration_seconds": calibration[
                            "total_calibration_seconds"
                        ],
                        "calibration_source": calibration["source"],
                        "margin_scope": (
                            "post-hoc uniform margin over the same 17 saved development "
                            "conditions; not an unseen-system guarantee"
                        ),
                    }
                )
    if len(result) != 102:
        raise ValueError(f"expected 102 strategy rows, got {len(result)}")
    return result


def aggregate_strategy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for pf in a05.PFS:
        for model in a05.MODELS:
            selected = [row for row in rows if row["pf"] == pf and row["model"] == model]
            ratios = [
                float(row["margin_adjusted_cost_ratio_to_current_m3_two_term"])
                for row in selected
            ]
            result.append(
                {
                    "pf": pf,
                    "model": model,
                    "condition_count": len(selected),
                    "four_metric_passed": sum(
                        bool(row["four_metric_pass"]) for row in selected
                    ),
                    "strict_frozen_budget_passed_before_margin": sum(
                        bool(row["strict_frozen_budget_pass_before_margin"])
                        for row in selected
                    ),
                    "margin_adjusted_passed_on_saved_conditions": sum(
                        bool(row["margin_adjusted_pass_on_saved_conditions"])
                        for row in selected
                    ),
                    "empirical_uniform_cost_multiplier": selected[0][
                        "empirical_uniform_cost_multiplier"
                    ],
                    "short_time_proxy_points_over_17_conditions": sum(
                        int(row["short_time_proxy_point_count"]) for row in selected
                    ),
                    "direct_fit_points_over_17_conditions": sum(
                        int(row["direct_fit_point_count"]) for row in selected
                    ),
                    "total_calibration_points_over_17_conditions": sum(
                        int(row["total_calibration_point_count"]) for row in selected
                    ),
                    "minimum_calibration_points_per_condition": min(
                        int(row["total_calibration_point_count"]) for row in selected
                    ),
                    "maximum_calibration_points_per_condition": max(
                        int(row["total_calibration_point_count"]) for row in selected
                    ),
                    "total_calibration_seconds_over_17_conditions": sum(
                        float(row["total_calibration_seconds"]) for row in selected
                    ),
                    "median_calibration_seconds_per_condition": statistics.median(
                        float(row["total_calibration_seconds"]) for row in selected
                    ),
                    "equal_one_run_basket_quantum_cost": sum(
                        float(row["margin_adjusted_frozen_cost"]) for row in selected
                    ),
                    "minimum_quantum_cost_ratio_to_current_m3_two_term": min(ratios),
                    "median_quantum_cost_ratio_to_current_m3_two_term": statistics.median(
                        ratios
                    ),
                    "maximum_quantum_cost_ratio_to_current_m3_two_term": max(ratios),
                    "condition_count_cheaper_than_current_m3_two_term": sum(
                        ratio < 1.0 for ratio in ratios
                    ),
                }
            )
    baseline = next(
        row
        for row in result
        if row["pf"] == "current_m3" and row["model"] == "two_term"
    )
    baseline_basket = float(baseline["equal_one_run_basket_quantum_cost"])
    for row in result:
        row["equal_one_run_basket_cost_ratio_to_current_m3_two_term"] = (
            float(row["equal_one_run_basket_quantum_cost"]) / baseline_basket
        )
    return result


def paired_two_term_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (row["condition"], row["pf"], row["model"]): row for row in rows
    }
    conditions = sorted({str(row["condition"]) for row in rows})
    result = []
    for condition in conditions:
        current = index[(condition, "current_m3", "two_term")]
        new = index[(condition, "two_term_center", "two_term")]
        current_calibration = float(current["total_calibration_seconds"])
        new_calibration = float(new["total_calibration_seconds"])
        result.append(
            {
                "dataset_id": current["dataset_id"],
                "condition": condition,
                "analysis_cluster": current["analysis_cluster"],
                "current_m3_four_metric_pass": current["four_metric_pass"],
                "two_term_center_four_metric_pass": new["four_metric_pass"],
                "current_m3_margin_adjusted_pass": current[
                    "margin_adjusted_pass_on_saved_conditions"
                ],
                "two_term_center_margin_adjusted_pass": new[
                    "margin_adjusted_pass_on_saved_conditions"
                ],
                "margin_adjusted_quantum_cost_ratio_new_over_current": (
                    float(new["margin_adjusted_frozen_cost"])
                    / float(current["margin_adjusted_frozen_cost"])
                ),
                "oracle_direct_cost_ratio_new_over_current": (
                    float(new["oracle_direct_required_cost"])
                    / float(current["oracle_direct_required_cost"])
                ),
                "current_m3_calibration_seconds": current_calibration,
                "two_term_center_calibration_seconds": new_calibration,
                "calibration_seconds_new_minus_current": new_calibration
                - current_calibration,
                "calibration_time_ratio_new_over_current": new_calibration
                / current_calibration,
                "current_m3_calibration_points": current[
                    "total_calibration_point_count"
                ],
                "two_term_center_calibration_points": new[
                    "total_calibration_point_count"
                ],
            }
        )
    return result


def amortization_rows(
    aggregates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index = {(row["pf"], row["model"]): row for row in aggregates}
    current = index[("current_m3", "two_term")]
    new = index[("two_term_center", "two_term")]
    current_quantum = float(current["equal_one_run_basket_quantum_cost"])
    new_quantum = float(new["equal_one_run_basket_quantum_cost"])
    current_classical = float(current["total_calibration_seconds_over_17_conditions"])
    new_classical = float(new["total_calibration_seconds_over_17_conditions"])
    result = []
    for reuse in REUSE_COUNTS:
        result.append(
            {
                "qpe_runs_per_condition": reuse,
                "current_m3_total_quantum_cost": reuse * current_quantum,
                "two_term_center_total_quantum_cost": reuse * new_quantum,
                "quantum_cost_ratio_new_over_current": new_quantum / current_quantum,
                "incremental_quantum_cost_units_for_new_pf": reuse
                * (new_quantum - current_quantum),
                "current_m3_one_time_calibration_seconds": current_classical,
                "two_term_center_one_time_calibration_seconds": new_classical,
                "calibration_seconds_new_minus_current": new_classical
                - current_classical,
                "current_m3_amortized_calibration_seconds_per_run": current_classical
                / reuse,
                "two_term_center_amortized_calibration_seconds_per_run": new_classical
                / reuse,
                "aggregate_dominance": (
                    "current_m3 lower quantum cost and lower saved calibration time"
                    if current_quantum < new_quantum
                    and current_classical < new_classical
                    else "tradeoff"
                ),
                "unit_separation_note": (
                    "quantum cost units and classical seconds are not added"
                ),
            }
        )
    return result


def make_plot(path: Path, paired: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ordered = sorted(
        paired,
        key=lambda row: float(
            row["margin_adjusted_quantum_cost_ratio_new_over_current"]
        ),
    )
    labels = [str(row["condition"]) for row in ordered]
    x = np.arange(len(ordered))
    fig, axes = plt.subplots(2, 1, figsize=(12.0, 8.0), sharex=True)
    axes[0].bar(
        x,
        [
            float(row["margin_adjusted_quantum_cost_ratio_new_over_current"])
            for row in ordered
        ],
        color="#d1765d",
    )
    axes[0].axhline(1.0, color="#333333", linewidth=1.0)
    axes[0].set_ylabel("new/current safe quantum cost")
    axes[0].set_ylim(1.0, 1.23)
    axes[0].set_title(
        "two_term_center versus current_m3: equal saved-condition frozen-budget success"
    )
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].bar(
        x,
        [float(row["calibration_time_ratio_new_over_current"]) for row in ordered],
        color="#6a8fd5",
    )
    axes[1].axhline(1.0, color="#333333", linewidth=1.0)
    axes[1].set_ylabel("new/current calibration time")
    axes[1].set_ylim(0.75, 1.08)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=55, ha="right", fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_report(
    output: Path,
    aggregates: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    amortization: list[dict[str, Any]],
) -> None:
    index = {(row["pf"], row["model"]): row for row in aggregates}
    current = index[("current_m3", "two_term")]
    new = index[("two_term_center", "two_term")]
    quantum_ratios = [
        float(row["margin_adjusted_quantum_cost_ratio_new_over_current"])
        for row in paired
    ]
    direct_ratios = [
        float(row["oracle_direct_cost_ratio_new_over_current"]) for row in paired
    ]
    calibration_ratios = [
        float(row["calibration_time_ratio_new_over_current"]) for row in paired
    ]
    total_current_calibration = float(
        current["total_calibration_seconds_over_17_conditions"]
    )
    total_new_calibration = float(new["total_calibration_seconds_over_17_conditions"])
    lines = [
        "# X01 A07: cost-benefit and calibration amortization",
        "",
        "Status: complete",
        "",
        "This audit equalizes frozen-budget success on the same 17 saved development "
        "conditions using the A05 empirical uniform margins. It performs no new PF or "
        "molecular calculation. The safety margins are post-hoc diagnostics, not "
        "unseen-system guarantees.",
        "",
        "## Strategy comparison",
        "",
        "| PF | model | four-metric pass | frozen pass before margin | after empirical margin | calibration points over 17 | per-condition range | saved calibration seconds | median safe quantum ratio vs current two-term | basket ratio |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregates:
        lines.append(
            f"| {row['pf']} | {row['model']} | {row['four_metric_passed']}/17 | "
            f"{row['strict_frozen_budget_passed_before_margin']}/17 | "
            f"{row['margin_adjusted_passed_on_saved_conditions']}/17 | "
            f"{row['total_calibration_points_over_17_conditions']} | "
            f"{row['minimum_calibration_points_per_condition']}--"
            f"{row['maximum_calibration_points_per_condition']} | "
            f"{row['total_calibration_seconds_over_17_conditions']:.6g} | "
            f"{row['median_quantum_cost_ratio_to_current_m3_two_term']:.6f} | "
            f"{row['equal_one_run_basket_cost_ratio_to_current_m3_two_term']:.6f} |"
        )
    lines += [
        "",
        "Both PFs use a selected five-point short-time window and three direct fit "
        "points. `current_m3` requires one extra evaluated short-time point for "
        "`LiH_CAS2e4o`, so its total is 137 points versus 136 for "
        "`two_term_center`. This is one saved proxy evaluation over 17 conditions, "
        "not a reduction in direct calibration points.",
        "",
        "## Paired two-term comparison",
        "",
        "After applying the empirical A05 margin to `two_term_center`, its continuous "
        "quantum cost relative to `current_m3` ranges from "
        f"{min(quantum_ratios):.6f} to {max(quantum_ratios):.6f}, with median "
        f"{statistics.median(quantum_ratios):.6f}. The equal-one-run 17-condition "
        f"basket ratio is {new['equal_one_run_basket_cost_ratio_to_current_m3_two_term']:.6f}.",
        "",
        "Using oracle direct required costs instead gives a range of "
        f"{min(direct_ratios):.6f} to {max(direct_ratios):.6f}, with median "
        f"{statistics.median(direct_ratios):.6f}. These oracle ratios are diagnostic "
        "and are not available to a deployment-time selector.",
        "",
        f"Saved PF-specific calibration time totals {total_current_calibration:.6f} s "
        f"for `current_m3` and {total_new_calibration:.6f} s for `two_term_center` "
        f"(ratio {total_new_calibration / total_current_calibration:.6f}). The paired "
        f"per-condition timing ratio has median {statistics.median(calibration_ratios):.6f} "
        f"and range {min(calibration_ratios):.6f}--{max(calibration_ratios):.6f}. "
        "These small differences are wall-time measurements, not evidence of a "
        "different asymptotic calibration cost.",
        "",
        "## Amortization",
        "",
        "Calibration is paid once while the quantum premium repeats for every QPE "
        "run. In the aggregate 17-condition basket, `two_term_center` has both higher "
        "saved calibration time and higher quantum cost. Consequently there is no "
        "positive reuse count at which it breaks even in these two separate resource "
        "coordinates. Quantum cost units and classical seconds are not added without "
        "an external conversion rule.",
        "",
        "| QPE runs/condition | new/current quantum ratio | current calibration s/run | new calibration s/run | dominance |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in amortization:
        lines.append(
            f"| {row['qpe_runs_per_condition']} | "
            f"{row['quantum_cost_ratio_new_over_current']:.6f} | "
            f"{row['current_m3_amortized_calibration_seconds_per_run']:.6g} | "
            f"{row['two_term_center_amortized_calibration_seconds_per_run']:.6g} | "
            f"{row['aggregate_dominance']} |"
        )
    lines += [
        "",
        "## A07 conclusion",
        "",
        "Under the saved additive cost model, `current_m3` plus the two-term model is "
        "the preferred operational strategy among these six cells: it already meets "
        "the frozen budget on all 17 saved conditions and has lower margin-adjusted "
        "quantum cost on every condition. The new PF saves one short-time proxy "
        "evaluation across all 17 conditions, but not a direct fit point or aggregate "
        "saved calibration time. The "
        "new PF's remaining benefit is a wider symmetric prediction margin and the "
        "LiH four-metric pass, but A05 shows that this does not translate into a saved "
        "precision failure for the baseline. The current evidence therefore does not "
        "justify paying the new PF's quantum premium for operational reliability.",
        "",
        "This conclusion is limited to correlated development conditions and the "
        "continuous proxy. Unseen-family transfer, calibration without exact states, "
        "integer QPE rounds, and hardware-level depth remain untested.",
        "",
        "## Files",
        "",
        "- `calibration_rows.csv`: saved point counts and PF-specific timings.",
        "- `strategy_rows.csv`: condition-level margin-adjusted strategies.",
        "- `strategy_summary.csv`: six PF/model cells.",
        "- `paired_two_term.csv`: direct paired PF comparison.",
        "- `amortization.csv`: reuse-count analysis with separated units.",
        "- `raw_sources.csv`: hashes of the 17 raw calibration sources.",
        "- `cost_benefit.png`: quantum and calibration ratios.",
        "- `analysis.json` and `manifest.json`: machine-readable summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    budget = a05.run_analysis()
    calibration, raw_sources = collect_calibration_rows(budget["_rows"])
    strategies = strategy_rows(
        budget["_rows"], budget["aggregate_rows"], calibration
    )
    aggregates = aggregate_strategy_rows(strategies)
    paired = paired_two_term_rows(strategies)
    amortization = amortization_rows(aggregates)
    return {
        "status": "complete",
        "scope": "X01 A07 saved cost-benefit and calibration amortization",
        "created_at": datetime.now().astimezone().isoformat(),
        "condition_count": 17,
        "analysis_cluster_count": 5,
        "calibration_row_count": len(calibration),
        "strategy_row_count": len(strategies),
        "paired_two_term_row_count": len(paired),
        "calibration_protocol": {
            "selected_short_time_window_points": 5,
            "evaluated_short_time_proxy_points": (
                "five except current_m3/LiH_CAS2e4o, which evaluates six"
            ),
            "direct_fit_points_per_pf_condition": 3,
            "shared_system_preparation_included": False,
            "validation_points_included": False,
        },
        "margin_scope": (
            "post-hoc over the same 17 saved development conditions; not an "
            "unseen-system guarantee"
        ),
        "quantum_and_classical_units_combined": False,
        "source_records": budget["source_records"],
        "raw_source_count": len(raw_sources),
        "git": audit_x01.git_state(),
        "strategy_summary_rows": aggregates,
        "amortization_rows": amortization,
        "_calibration_rows": calibration,
        "_strategy_rows": strategies,
        "_paired_rows": paired,
        "_raw_sources": raw_sources,
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
    a05.write_csv(output / "calibration_rows.csv", result["_calibration_rows"])
    a05.write_csv(output / "strategy_rows.csv", result["_strategy_rows"])
    a05.write_csv(output / "strategy_summary.csv", result["strategy_summary_rows"])
    a05.write_csv(output / "paired_two_term.csv", result["_paired_rows"])
    a05.write_csv(output / "amortization.csv", result["amortization_rows"])
    a05.write_csv(output / "raw_sources.csv", result["_raw_sources"])
    make_plot(output / "cost_benefit.png", result["_paired_rows"])
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
            "post_hoc_margin_used_for_saved_condition_equalization": True,
            "unseen_system_safety_claimed": False,
            "quantum_and_classical_units_combined": False,
            "existing_input_artifacts_overwritten": False,
        },
    )
    make_report(
        output,
        result["strategy_summary_rows"],
        result["_paired_rows"],
        result["amortization_rows"],
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
