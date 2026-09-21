"""X01/A03-A04 paired PF/model effects and threshold sensitivity.

The analysis reuses the independently recomputed A01/A02 rows.  It performs
no electronic-structure, product-formula, or direct-eigenvalue calculation.
Canonical pass thresholds remain the primary result; threshold sweeps vary
one criterion at a time and are diagnostic only.
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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "artifacts/prevalidation_x01_pf_model_threshold_sensitivity_20260920"
)

PFS = ("current_m3", "two_term_center")
MODELS = ("original_one_term", "refit_one_term", "two_term")
METRICS = tuple(audit_x01.CANONICAL_THRESHOLDS)
EFFECT_METRICS = METRICS + ("direct_cost_at_predicted_time",)
THRESHOLD_MULTIPLIERS = (
    0.25,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    3.0,
    5.0,
    7.5,
    10.0,
    20.0,
    50.0,
)
MODEL_CONTRASTS = (
    (
        "original_to_refit",
        "original_one_term",
        "refit_one_term",
        "legacy perturbative alpha versus direct refit; fit loss differs",
    ),
    (
        "refit_to_two_term",
        "refit_one_term",
        "two_term",
        "fair nested comparison: same three points and normalized LS loss",
    ),
    (
        "original_to_two_term",
        "original_one_term",
        "two_term",
        "overall legacy-to-two-term change; fit loss differs",
    ),
)


def _condition_metadata(condition: str) -> dict[str, str]:
    if condition in {"H6", "H7"}:
        return {
            "molecule": condition,
            "analysis_cluster": "H_chain",
            "variation_axis": "chain_length",
        }
    molecule = condition.split("_", 1)[0]
    if condition.startswith("NH3_"):
        axis = "basis"
    elif "CAS" in condition:
        axis = "active_space"
    elif "stretch" in condition and condition.count("_") >= 2:
        axis = "geometry_and_basis"
    elif "stretch" in condition:
        axis = "geometry"
    else:
        axis = "unspecified"
    return {
        "molecule": molecule,
        "analysis_cluster": molecule,
        "variation_axis": axis,
    }


def fixed_comparison_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in audit["condition_rows"]
        if row["dataset_id"]
        in {"five_condition_holdout", "twelve_condition_holdout"}
    ]
    for row in rows:
        row.update(_condition_metadata(str(row["condition"])))
    expected_conditions = 17
    expected = expected_conditions * len(PFS) * len(MODELS)
    if len(rows) != expected:
        raise ValueError(f"expected {expected} fixed-comparison rows, got {len(rows)}")
    keys = {(row["condition"], row["pf"], row["model"]) for row in rows}
    if len(keys) != expected:
        raise ValueError("fixed-comparison design is not a complete 17x2x3 grid")
    return rows


def validate_factorial_design_sources() -> dict[str, Any]:
    """Verify the saved comparison really supports the declared paired design."""
    record_count = 0
    expected_training = [0.1, 0.2, 0.3]
    for path in (audit_x01.DEFAULT_FIVE, audit_x01.DEFAULT_TWELVE):
        payload = audit_x01.load_json(path)
        if list(payload["protocol"]["training_points_excluded"]) != expected_training:
            raise ValueError(f"unexpected training-point protocol in {path}")
        for record in payload["records"]:
            record_count += 1
            models = record["models"]
            training_sets = {
                tuple(float(value) for value in model["training_points_relative_to_t_ana"])
                for model in models.values()
            }
            if training_sets != {tuple(expected_training)}:
                raise ValueError(
                    f"models use different training points for {record['condition']}"
                )
            refit_rule = str(models["refit_one_term"]["definition"]["fit_rule"])
            two_term_rule = str(models["two_term"]["definition"]["fit_rule"])
            original_rule = str(
                models["original_one_term"]["definition"]["fit_rule"]
            )
            if "same normalized least-squares objective" not in refit_rule:
                raise ValueError("refit one-term loss is not the declared nested loss")
            if "least squares after normalization" not in two_term_rule:
                raise ValueError("two-term loss is not the declared normalized loss")
            if "frozen common perturbative fit" not in original_rule:
                raise ValueError("original one-term model is not the legacy fit")
    if record_count != 34:
        raise ValueError(f"expected 34 condition/PF records, got {record_count}")
    return {
        "condition_pf_record_count": record_count,
        "common_training_points_relative_to_t_ana": expected_training,
        "refit_one_term_vs_two_term_same_normalized_loss": True,
        "original_one_term_is_legacy_perturbative_fit": True,
    }


def _index(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (str(row["condition"]), str(row["pf"]), str(row["model"])): row
        for row in rows
    }


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return numerator / denominator


def paired_effect_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = _index(rows)
    conditions = sorted({str(row["condition"]) for row in rows})
    result: list[dict[str, Any]] = []

    def add_effect(
        *,
        condition: str,
        effect_type: str,
        contrast: str,
        held_constant: str,
        metric: str,
        from_label: str,
        to_label: str,
        from_value: float,
        to_value: float,
        design_note: str,
        from_pass: bool | None,
        to_pass: bool | None,
    ) -> None:
        metadata = _condition_metadata(condition)
        result.append(
            {
                "condition": condition,
                **metadata,
                "effect_type": effect_type,
                "contrast": contrast,
                "held_constant": held_constant,
                "metric": metric,
                "from_label": from_label,
                "to_label": to_label,
                "from_value": from_value,
                "to_value": to_value,
                "difference_to_minus_from": to_value - from_value,
                "benefit_from_reduction": from_value - to_value,
                "ratio_to_over_from": _ratio(to_value, from_value),
                "from_pass": from_pass,
                "to_pass": to_pass,
                "pass_change": (
                    int(to_pass) - int(from_pass)
                    if from_pass is not None and to_pass is not None
                    else None
                ),
                "design_note": design_note,
            }
        )

    for condition in conditions:
        for model in MODELS:
            current = by_key[(condition, "current_m3", model)]
            new = by_key[(condition, "two_term_center", model)]
            for metric in EFFECT_METRICS:
                add_effect(
                    condition=condition,
                    effect_type="pf_effect",
                    contrast="current_m3_to_two_term_center",
                    held_constant=model,
                    metric=metric,
                    from_label="current_m3",
                    to_label="two_term_center",
                    from_value=float(current[metric]),
                    to_value=float(new[metric]),
                    design_note="paired condition with the same model definition",
                    from_pass=bool(current["recomputed_pass"]),
                    to_pass=bool(new["recomputed_pass"]),
                )

        for pf in PFS:
            for name, before, after, note in MODEL_CONTRASTS:
                from_row = by_key[(condition, pf, before)]
                to_row = by_key[(condition, pf, after)]
                for metric in EFFECT_METRICS:
                    add_effect(
                        condition=condition,
                        effect_type="model_effect",
                        contrast=name,
                        held_constant=pf,
                        metric=metric,
                        from_label=before,
                        to_label=after,
                        from_value=float(from_row[metric]),
                        to_value=float(to_row[metric]),
                        design_note=note,
                        from_pass=bool(from_row["recomputed_pass"]),
                        to_pass=bool(to_row["recomputed_pass"]),
                    )

        # Difference-in-differences for the fair nested model comparison.
        for metric in EFFECT_METRICS:
            current_delta = (
                float(by_key[(condition, "current_m3", "two_term")][metric])
                - float(by_key[(condition, "current_m3", "refit_one_term")][metric])
            )
            new_delta = (
                float(by_key[(condition, "two_term_center", "two_term")][metric])
                - float(
                    by_key[(condition, "two_term_center", "refit_one_term")][
                        metric
                    ]
                )
            )
            metadata = _condition_metadata(condition)
            result.append(
                {
                    "condition": condition,
                    **metadata,
                    "effect_type": "pf_by_model_interaction",
                    "contrast": "refit_to_two_term_difference_in_differences",
                    "held_constant": "none",
                    "metric": metric,
                    "from_label": "current_m3_model_delta",
                    "to_label": "two_term_center_model_delta",
                    "from_value": current_delta,
                    "to_value": new_delta,
                    "difference_to_minus_from": new_delta - current_delta,
                    "benefit_from_reduction": current_delta - new_delta,
                    "ratio_to_over_from": _ratio(new_delta, current_delta),
                    "from_pass": None,
                    "to_pass": None,
                    "pass_change": None,
                    "design_note": (
                        "same three direct training points and normalized LS loss; "
                        "positive benefit means the two-term upgrade reduces the metric "
                        "more for two_term_center"
                    ),
                }
            )
    return result


def factorial_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for pf in PFS:
        for model in MODELS:
            values = [row for row in rows if row["pf"] == pf and row["model"] == model]
            packed: dict[str, Any] = {
                "pf": pf,
                "model": model,
                "passed": sum(bool(row["recomputed_pass"]) for row in values),
                "total": len(values),
            }
            for metric in METRICS:
                samples = [float(row[metric]) for row in values]
                worst = max(values, key=lambda row: float(row[metric]))
                packed[f"mean_{metric}"] = statistics.fmean(samples)
                packed[f"median_{metric}"] = statistics.median(samples)
                packed[f"worst_{metric}"] = float(worst[metric])
                packed[f"worst_{metric}_condition"] = worst["condition"]
            result.append(packed)
    return result


def effect_summary_rows(effects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in effects:
        key = (
            str(row["effect_type"]),
            str(row["contrast"]),
            str(row["held_constant"]),
            str(row["metric"]),
        )
        groups.setdefault(key, []).append(row)
    result = []
    for key, values in sorted(groups.items()):
        benefits = [float(row["benefit_from_reduction"]) for row in values]
        ratios = [
            float(row["ratio_to_over_from"])
            for row in values
            if row["ratio_to_over_from"] is not None
            and math.isfinite(float(row["ratio_to_over_from"]))
        ]
        result.append(
            {
                "effect_type": key[0],
                "contrast": key[1],
                "held_constant": key[2],
                "metric": key[3],
                "condition_count": len(values),
                "mean_benefit_from_reduction": statistics.fmean(benefits),
                "median_benefit_from_reduction": statistics.median(benefits),
                "minimum_benefit_from_reduction": min(benefits),
                "maximum_benefit_from_reduction": max(benefits),
                "conditions_improved": sum(value > 0.0 for value in benefits),
                "conditions_tied": sum(value == 0.0 for value in benefits),
                "conditions_worsened": sum(value < 0.0 for value in benefits),
                "median_ratio_to_over_from": (
                    statistics.median(ratios) if ratios else None
                ),
            }
        )
    return result


def _passes_with_thresholds(
    row: dict[str, Any], thresholds: dict[str, float]
) -> bool:
    return all(float(row[metric]) <= thresholds[metric] for metric in METRICS)


def threshold_sensitivity_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = _index(rows)
    conditions = sorted({str(row["condition"]) for row in rows})
    sensitivity: list[dict[str, Any]] = []
    pairwise: list[dict[str, Any]] = []
    for varied_metric in METRICS:
        canonical = float(audit_x01.CANONICAL_THRESHOLDS[varied_metric])
        for multiplier in THRESHOLD_MULTIPLIERS:
            thresholds = dict(audit_x01.CANONICAL_THRESHOLDS)
            thresholds[varied_metric] = canonical * multiplier
            for pf in PFS:
                for model in MODELS:
                    selected = [by_key[(condition, pf, model)] for condition in conditions]
                    passed_conditions = [
                        str(row["condition"])
                        for row in selected
                        if _passes_with_thresholds(row, thresholds)
                    ]
                    ratios = [
                        float(row["direct_cost_at_predicted_time"])
                        / float(
                            by_key[
                                (str(row["condition"]), "current_m3", model)
                            ]["direct_cost_at_predicted_time"]
                        )
                        for row in selected
                        if str(row["condition"]) in passed_conditions
                    ]
                    sensitivity.append(
                        {
                            "varied_metric": varied_metric,
                            "threshold_multiplier": multiplier,
                            "varied_threshold": thresholds[varied_metric],
                            "other_thresholds": "canonical",
                            "pf": pf,
                            "model": model,
                            "passed": len(passed_conditions),
                            "total": len(selected),
                            "coverage": len(passed_conditions) / len(selected),
                            "failed_conditions": ";".join(
                                condition
                                for condition in conditions
                                if condition not in passed_conditions
                            ),
                            "median_direct_cost_ratio_to_current_over_covered": (
                                statistics.median(ratios) if ratios else None
                            ),
                        }
                    )
            for model in MODELS:
                current_pass = {
                    condition
                    for condition in conditions
                    if _passes_with_thresholds(
                        by_key[(condition, "current_m3", model)], thresholds
                    )
                }
                new_pass = {
                    condition
                    for condition in conditions
                    if _passes_with_thresholds(
                        by_key[(condition, "two_term_center", model)], thresholds
                    )
                }
                common = sorted(current_pass & new_pass)
                common_ratios = [
                    float(
                        by_key[(condition, "two_term_center", model)][
                            "direct_cost_at_predicted_time"
                        ]
                    )
                    / float(
                        by_key[(condition, "current_m3", model)][
                            "direct_cost_at_predicted_time"
                        ]
                    )
                    for condition in common
                ]
                pairwise.append(
                    {
                        "varied_metric": varied_metric,
                        "threshold_multiplier": multiplier,
                        "varied_threshold": thresholds[varied_metric],
                        "other_thresholds": "canonical",
                        "model": model,
                        "current_m3_passed": len(current_pass),
                        "two_term_center_passed": len(new_pass),
                        "coverage_advantage_new_minus_current": len(new_pass)
                        - len(current_pass),
                        "both_passed": len(common),
                        "new_only": len(new_pass - current_pass),
                        "current_only": len(current_pass - new_pass),
                        "neither": len(set(conditions) - (current_pass | new_pass)),
                        "median_new_over_current_direct_cost_on_common_passes": (
                            statistics.median(common_ratios)
                            if common_ratios
                            else None
                        ),
                    }
                )
    return sensitivity, pairwise


def failure_diagnostic_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        normalized = {
            metric: float(row[metric])
            / float(audit_x01.CANONICAL_THRESHOLDS[metric])
            for metric in METRICS
        }
        failed = [metric for metric in METRICS if normalized[metric] > 1.0]
        worst = max(METRICS, key=lambda metric: normalized[metric])
        result.append(
            {
                "dataset_id": row["dataset_id"],
                "condition": row["condition"],
                **_condition_metadata(str(row["condition"])),
                "pf": row["pf"],
                "model": row["model"],
                "canonical_pass": bool(row["recomputed_pass"]),
                "failed_metric_count": len(failed),
                "failed_metrics": ";".join(failed),
                "worst_normalized_metric": worst,
                "worst_normalized_value": normalized[worst],
                **{f"normalized_{metric}": value for metric, value in normalized.items()},
            }
        )
    return result


def cluster_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters = sorted({str(row["analysis_cluster"]) for row in rows})
    result = []
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
                        "passed": sum(
                            bool(row["recomputed_pass"]) for row in selected
                        ),
                        "condition_count": len(selected),
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


def make_plot(path: Path, sensitivity: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metric_titles = {
        "eta_star": "Cost prediction error",
        "eta_min": "Selection loss",
        "eta_t": "Time displacement",
        "maximum_unseen_residual_over_epsilon": "Unseen shift residual",
    }
    colors = {"current_m3": "#3b6fb6", "two_term_center": "#d05a3a"}
    styles = {
        "original_one_term": ":",
        "refit_one_term": "--",
        "two_term": "-",
    }
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.5), sharex=True, sharey=True)
    for axis, metric in zip(axes.flat, METRICS):
        for pf in PFS:
            for model in MODELS:
                selected = sorted(
                    (
                        row
                        for row in sensitivity
                        if row["varied_metric"] == metric
                        and row["pf"] == pf
                        and row["model"] == model
                    ),
                    key=lambda row: float(row["threshold_multiplier"]),
                )
                axis.plot(
                    [float(row["threshold_multiplier"]) for row in selected],
                    [int(row["passed"]) for row in selected],
                    color=colors[pf],
                    linestyle=styles[model],
                    marker="o" if model == "two_term" else None,
                    markersize=3.0,
                    linewidth=1.6,
                    label=f"{pf} / {model}",
                )
        axis.axvline(1.0, color="#555555", linewidth=1.0, alpha=0.7)
        axis.set_xscale("log")
        axis.set_title(metric_titles[metric])
        axis.set_ylim(-0.5, 17.5)
        axis.set_yticks([0, 3, 6, 9, 12, 15, 17])
        axis.grid(True, alpha=0.25)
    axes[1, 0].set_xlabel("varied threshold / canonical threshold")
    axes[1, 1].set_xlabel("varied threshold / canonical threshold")
    axes[0, 0].set_ylabel("passing conditions / 17")
    axes[1, 0].set_ylabel("passing conditions / 17")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(
        "One-at-a-time threshold sensitivity (other three thresholds canonical)"
    )
    fig.tight_layout(rect=(0, 0.11, 1, 0.96))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _canonical_lookup(factorial: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["pf"]), str(row["model"])): row for row in factorial}


def make_report(
    output: Path,
    factorial: list[dict[str, Any]],
    sensitivity: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    lookup = _canonical_lookup(factorial)
    fair_rescues = {
        pf: lookup[(pf, "two_term")]["passed"]
        - lookup[(pf, "refit_one_term")]["passed"]
        for pf in PFS
    }
    lih = next(
        row
        for row in failures
        if row["condition"] == "LiH_CAS2e4o"
        and row["pf"] == "current_m3"
        and row["model"] == "two_term"
    )
    half_threshold = {
        metric: {
            pf: next(
                int(row["passed"])
                for row in sensitivity
                if row["varied_metric"] == metric
                and float(row["threshold_multiplier"]) == 0.5
                and row["pf"] == pf
                and row["model"] == "two_term"
            )
            for pf in PFS
        }
        for metric in METRICS
    }
    lines = [
        "# X01 A03/A04: PF/model factorization and threshold sensitivity",
        "",
        "Status: complete",
        "",
        "No electronic-structure, PF-unitary, or direct-eigenvalue calculation was run. "
        "The inputs are the independently recomputed A01/A02 rows.",
        "",
        "## A03: paired PF-by-model result",
        "",
        "| PF | original one-term | refit one-term | two-term |",
        "|---|---:|---:|---:|",
    ]
    for pf in PFS:
        lines.append(
            f"| {pf} | {lookup[(pf, 'original_one_term')]['passed']}/17 | "
            f"{lookup[(pf, 'refit_one_term')]['passed']}/17 | "
            f"{lookup[(pf, 'two_term')]['passed']}/17 |"
        )
    lines += [
        "",
        "The fair nested comparison is refit one-term versus two-term: both use the "
        "same three direct training points and the same normalized least-squares loss. "
        f"It adds {fair_rescues['current_m3']} passes for `current_m3` and "
        f"{fair_rescues['two_term_center']} passes for `two_term_center`. "
        "Thus the model upgrade explains the larger part of the baseline recovery. "
        "At fixed two-term model, changing the PF adds one pass (16/17 to 17/17).",
        "",
        "The original one-term model is retained as a legacy reference, not as a "
        "same-loss causal contrast: its leading coefficient comes from the frozen "
        "short-time perturbative fit. A three-term model is not fitted here because "
        "three training points for three coefficients leave zero training-residual "
        "degrees of freedom; using saved unseen points for fitting would change the "
        "information budget and contaminate this comparison.",
        "",
        "## A04: one-at-a-time threshold sensitivity",
        "",
        "The canonical thresholds remain the primary decision. Each diagnostic curve "
        "varies exactly one threshold; the other three remain canonical. Thresholds "
        "are not relaxed simultaneously.",
        "",
        "At half the canonical threshold, two-term coverage is:",
        "",
        "| varied threshold | current_m3 | two_term_center |",
        "|---|---:|---:|",
    ]
    for metric in METRICS:
        lines.append(
            f"| {metric} | {half_threshold[metric]['current_m3']}/17 | "
            f"{half_threshold[metric]['two_term_center']}/17 |"
        )
    lines += [
        "",
        f"The sole two-term baseline failure, `LiH_CAS2e4o`, fails "
        f"{lih['failed_metric_count']} of 4 criteria: {lih['failed_metrics']}. "
        "It therefore cannot be rescued by moving only the 1% cost-prediction "
        "threshold; the observed 16/17 versus 17/17 difference is not a single "
        "near-boundary classification artifact.",
        "",
        "## Dependence and scope",
        "",
        "The 17 rows form five correlated analysis clusters: H-chain, NH3, BeH2, "
        "H2O, and LiH. Condition counts are not treated as 17 independent molecular "
        "families, and no population success interval is reported.",
        "",
        "## Interpretation",
        "",
        "The evidence supports a two-part conclusion. First, adding the t^6 term is "
        "the dominant reason both PFs become predictable. Second, the coefficient "
        "change retains a real but narrower incremental benefit: it resolves the "
        "LiH small-active-space case and produces a wider metric margin, at the "
        "previously measured direct-cost premium. Practical necessity is still not "
        "established; A05/A07 must test frozen-budget harm and cost-benefit.",
        "",
        "## Files",
        "",
        "- `factorial_summary.csv`: canonical PF x model cells.",
        "- `paired_pf_model_effects.csv`: all paired PF, model, and interaction effects.",
        "- `effect_summary.csv`: distribution summaries of paired effects.",
        "- `threshold_sensitivity.csv`: one-at-a-time coverage curves.",
        "- `threshold_pairwise.csv`: PF coverage differences and common-pass cost ratios.",
        "- `failure_diagnostics.csv`: failed criteria and normalized margins per row.",
        "- `cluster_summary.csv`: cluster-level counts without independence claims.",
        "- `threshold_sensitivity.png`: lightweight diagnostic figure.",
        "- `analysis.json` and `manifest.json`: machine-readable summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    design_validation = validate_factorial_design_sources()
    source_audit = audit_x01.run_audit(
        audit_x01.DEFAULT_FIVE,
        audit_x01.DEFAULT_TWELVE,
        audit_x01.DEFAULT_JOINT,
    )
    rows = fixed_comparison_rows(source_audit)
    effects = paired_effect_rows(rows)
    factorial = factorial_summary_rows(rows)
    effect_summary = effect_summary_rows(effects)
    sensitivity, pairwise = threshold_sensitivity_rows(rows)
    failures = failure_diagnostic_rows(rows)
    clusters = cluster_summary_rows(rows)
    canonical = _canonical_lookup(factorial)
    return {
        "status": "complete",
        "scope": "X01 A03-A04 paired PF/model and threshold sensitivity",
        "created_at": datetime.now().astimezone().isoformat(),
        "canonical_thresholds": audit_x01.CANONICAL_THRESHOLDS,
        "threshold_rule": "one criterion varied at a time; other three canonical",
        "threshold_multipliers": list(THRESHOLD_MULTIPLIERS),
        "condition_count": 17,
        "analysis_cluster_count": 5,
        "factorial_row_count": len(factorial),
        "paired_effect_row_count": len(effects),
        "threshold_sensitivity_row_count": len(sensitivity),
        "threshold_pairwise_row_count": len(pairwise),
        "canonical_pass_counts": {
            f"{pf}/{model}": int(canonical[(pf, model)]["passed"])
            for pf in PFS
            for model in MODELS
        },
        "three_term_status": (
            "not compared: three training points for three coefficients leave zero "
            "training-residual degrees of freedom"
        ),
        "factorial_design_validation": design_validation,
        "source_records": source_audit["source_records"][:2],
        "source_audit_reproduction": {
            "fixed_comparison_rows": len(rows),
            "matching_metric_rows": sum(
                bool(row["metric_reproduction_pass"]) for row in rows
            ),
            "matching_pass_rows": sum(bool(row["pass_matches"]) for row in rows),
        },
        "git": audit_x01.git_state(),
        "factorial_rows": factorial,
        "effect_summary_rows": effect_summary,
        "cluster_rows": clusters,
        "_fixed_rows": rows,
        "_effect_rows": effects,
        "_sensitivity_rows": sensitivity,
        "_pairwise_rows": pairwise,
        "_failure_rows": failures,
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
    write_csv(output / "factorial_summary.csv", result["factorial_rows"])
    write_csv(output / "paired_pf_model_effects.csv", result["_effect_rows"])
    write_csv(output / "effect_summary.csv", result["effect_summary_rows"])
    write_csv(output / "threshold_sensitivity.csv", result["_sensitivity_rows"])
    write_csv(output / "threshold_pairwise.csv", result["_pairwise_rows"])
    write_csv(output / "failure_diagnostics.csv", result["_failure_rows"])
    write_csv(output / "cluster_summary.csv", result["cluster_rows"])
    make_plot(output / "threshold_sensitivity.png", result["_sensitivity_rows"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    write_json(output / "analysis.json", machine)
    manifest = {
        "status": result["status"],
        "scope": result["scope"],
        "created_at": result["created_at"],
        "source_records": result["source_records"],
        "git": result["git"],
        "no_new_pf_or_electronic_structure_calculation": True,
        "existing_input_artifacts_overwritten": False,
        "canonical_thresholds_unchanged": True,
        "thresholds_varied_simultaneously": False,
        "three_term_fitted": False,
    }
    write_json(output / "manifest.json", manifest)
    make_report(
        output,
        result["factorial_rows"],
        result["_sensitivity_rows"],
        result["_failure_rows"],
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
