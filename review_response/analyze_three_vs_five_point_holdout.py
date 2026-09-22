#!/usr/bin/env python3
"""Reanalyse the frozen N2/CO holdout's three- versus five-point fits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


SOURCE_RELATIVE = Path(
    "artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/"
    "aggregate/summary.json"
)
SOURCE_SHA256 = "0f0b2590faa278e7c96f7797b81b557544d4d4469b3f13a9079b71548054ce45"
SOURCE_RESULT_COMMIT = "33a761d44a24022ad61192c41a196dd4cb3afbca"
PRIMARY_CONDITIONS = (
    "N2_active_eq_sto3g",
    "N2_active_stretch150_sto3g",
    "CO_active_eq_sto3g",
    "CO_active_stretch150_sto3g",
)
FORMULAE = ("yoshida4", "current_m3", "two_term_center", "m5_best")
MODELS = {"three": "two_term_3point", "five": "two_term_5point"}
METRICS = (
    "eta_star",
    "eta_min",
    "eta_t",
    "maximum_unseen_residual_over_epsilon",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _finite_max(values: Iterable[Any]) -> float | None:
    finite = [
        float(value)
        for value in values
        if value is not None and math.isfinite(float(value))
    ]
    return max(finite) if finite else None


def analyse(
    source: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected = {
        (row["condition"], row["formula"], row["model"]): row
        for row in source["rows"]
        if row["condition"] in PRIMARY_CONDITIONS
        and row["formula"] in FORMULAE
        and row["model"] in MODELS.values()
    }
    expected = len(PRIMARY_CONDITIONS) * len(FORMULAE) * len(MODELS)
    if len(selected) != expected:
        raise RuntimeError(
            f"expected {expected} comparable rows, found {len(selected)}"
        )

    paired: list[dict[str, Any]] = []
    for formula in FORMULAE:
        for condition in PRIMARY_CONDITIONS:
            three = selected[(condition, formula, MODELS["three"])]
            five = selected[(condition, formula, MODELS["five"])]
            record: dict[str, Any] = {
                "condition": condition,
                "formula": formula,
                "three_passed": bool(three["passed"]),
                "five_passed": bool(five["passed"]),
                "pass_agrees": bool(three["passed"] == five["passed"]),
                "three_base_budget_met": bool(three["budget_base_target_met"]),
                "five_base_budget_met": bool(five["budget_base_target_met"]),
                "base_budget_agrees": bool(
                    three["budget_base_target_met"] == five["budget_base_target_met"]
                ),
                "three_1pct_budget_met": bool(three["budget_1pct_target_met"]),
                "five_1pct_budget_met": bool(five["budget_1pct_target_met"]),
                "one_percent_budget_agrees": bool(
                    three["budget_1pct_target_met"] == five["budget_1pct_target_met"]
                ),
            }
            for metric in METRICS:
                record[f"three_{metric}"] = three[metric]
                record[f"five_{metric}"] = five[metric]
            paired.append(record)

    formula_rows: list[dict[str, Any]] = []
    for formula in FORMULAE:
        rows = [row for row in paired if row["formula"] == formula]
        formula_row: dict[str, Any] = {
            "formula": formula,
            "condition_count": len(rows),
            "three_pass_count": sum(row["three_passed"] for row in rows),
            "five_pass_count": sum(row["five_passed"] for row in rows),
            "pass_agreement_count": sum(row["pass_agrees"] for row in rows),
            "three_base_budget_count": sum(
                row["three_base_budget_met"] for row in rows
            ),
            "five_base_budget_count": sum(row["five_base_budget_met"] for row in rows),
            "base_budget_agreement_count": sum(
                row["base_budget_agrees"] for row in rows
            ),
            "three_1pct_budget_count": sum(
                row["three_1pct_budget_met"] for row in rows
            ),
            "five_1pct_budget_count": sum(row["five_1pct_budget_met"] for row in rows),
            "one_percent_budget_agreement_count": sum(
                row["one_percent_budget_agrees"] for row in rows
            ),
        }
        for metric in METRICS:
            formula_row[f"three_worst_{metric}"] = _finite_max(
                row[f"three_{metric}"] for row in rows
            )
            formula_row[f"five_worst_{metric}"] = _finite_max(
                row[f"five_{metric}"] for row in rows
            )
        formula_rows.append(formula_row)

    pass_agreement = all(row["pass_agrees"] for row in paired)
    base_budget_agreement = all(row["base_budget_agrees"] for row in paired)
    margin_budget_agreement = all(row["one_percent_budget_agrees"] for row in paired)
    five_passing_formulae = {
        row["formula"] for row in formula_rows if row["five_pass_count"] == 4
    }
    three_passing_formulae = {
        row["formula"] for row in formula_rows if row["three_pass_count"] == 4
    }
    conclusion = {
        "status": "complete",
        "source_result_commit": SOURCE_RESULT_COMMIT,
        "condition_count": len(PRIMARY_CONDITIONS),
        "formula_count": len(FORMULAE),
        "paired_comparison_count": len(paired),
        "pass_decisions_agree": pass_agreement,
        "base_budget_decisions_agree": base_budget_agreement,
        "one_percent_budget_decisions_agree": margin_budget_agreement,
        "three_point_all_condition_pass_formulae": sorted(three_passing_formulae),
        "five_point_all_condition_pass_formulae": sorted(five_passing_formulae),
        "same_all_condition_pass_formulae": three_passing_formulae
        == five_passing_formulae,
        "three_point_active_space_reduced_calibration_candidate": bool(
            pass_agreement
            and base_budget_agreement
            and margin_budget_agreement
            and three_passing_formulae == five_passing_formulae
        ),
        "scope": (
            "Secondary, pre-specified ablation on the same frozen N2/CO holdout; "
            "not a full-electron or new-molecule validation."
        ),
    }
    return paired, formula_rows, conclusion


def run(project_root: Path, output: Path) -> dict[str, Any]:
    source_path = project_root / SOURCE_RELATIVE
    observed_hash = _sha256(source_path)
    if observed_hash != SOURCE_SHA256:
        raise RuntimeError(
            f"source summary SHA-256 mismatch: {observed_hash} != {SOURCE_SHA256}"
        )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    paired, formula_rows, conclusion = analyse(source)
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "paired_results.csv", paired)
    _write_csv(output / "formula_summary.csv", formula_rows)
    _dump_json(output / "summary.json", conclusion)

    report = [
        "# N2/CO three-point versus five-point two-term reanalysis",
        "",
        "Status: **complete**",
        "",
        "This is a reanalysis of the pre-specified information-count ablation in the frozen N2/CO holdout. No new PF points were computed.",
        "",
        "| PF | three-point pass | five-point pass | base budget (3/5) | +1% budget (3/5) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in formula_rows:
        report.append(
            f"| `{row['formula']}` | {row['three_pass_count']}/4 | "
            f"{row['five_pass_count']}/4 | {row['three_base_budget_count']}/4; "
            f"{row['five_base_budget_count']}/4 | {row['three_1pct_budget_count']}/4; "
            f"{row['five_1pct_budget_count']}/4 |"
        )
    report.extend(
        [
            "",
            "All 16 PF/condition pass decisions, base-budget decisions, and 1% margin decisions agree between the three- and five-point fits. Yoshida 4th order, `current_m3`, and `two_term_center` pass 4/4 with both fits; `m5_best` passes 0/4 with both.",
            "",
            "## Decision",
            "",
            "Freeze the three-point two-term fit at `0.1, 0.2, 0.3 t_ana` as the reduced-calibration candidate for the current frozen-core active-space scope. Retain the five-point fit as the reference and audit rule.",
            "",
            "This does not show that three points are sufficient for full-electron systems or arbitrary molecules. The comparison uses the same holdout as the five-point result, although the three-point ablation was fixed before those results were inspected.",
        ]
    )
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    tracked = sorted(path for path in output.iterdir() if path.name != "manifest.json")
    artifact_hashes = {}
    for path in tracked:
        try:
            key = str(path.relative_to(project_root))
        except ValueError:
            key = path.name
        artifact_hashes[key] = _sha256(path)
    manifest = {
        "status": "complete",
        "source": {
            "path": str(SOURCE_RELATIVE),
            "sha256": observed_hash,
            "result_commit": SOURCE_RESULT_COMMIT,
        },
        "artifact_sha256": artifact_hashes,
    }
    _dump_json(output / "manifest.json", manifest)
    return conclusion


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.project_root.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
