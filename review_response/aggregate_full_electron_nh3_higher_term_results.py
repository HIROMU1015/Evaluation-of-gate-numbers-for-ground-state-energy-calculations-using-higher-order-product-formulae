"""Aggregate both NH3 geometries and assign the declared diagnosis category."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any


FORMULAE = (
    "yoshida4",
    "paper_new4",
    "m5_best",
    "two_term_center",
    "joint_refine_r0_s0046",
    "yoshida6_m3",
)
MODELS = (
    "one_term",
    "two_term",
    "three_term",
    "legacy_two_term_0p1_0p3",
)
GEOMETRIES = ("equilibrium", "stretch150")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display(value: Any, format_spec: str = ".6g") -> str:
    return "n/a" if value is None else format(float(value), format_spec)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_dir

    formula_records: dict[str, dict[str, dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    for geometry in GEOMETRIES:
        raw_dir = root / (geometry + "_raw")
        formula_records[geometry] = {}
        for formula in FORMULAE:
            record = load_json(raw_dir / (formula + ".json"))
            formula_records[geometry][formula] = record
            if record["status"] != "complete":
                rows.append({
                    "geometry": geometry,
                    "formula": formula,
                    "model": None,
                    "status": record["status"],
                    "passed": False,
                })
                continue
            for model in MODELS:
                result = record["models"][model]
                direct_minimum = result["direct_grid_minimum"]
                at_star = next(
                    point for point in result["direct_validation_points"]
                    if point["relative_to_t_star"] == 1.0
                )
                rows.append({
                    "geometry": geometry,
                    "formula": formula,
                    "display_name": record["formula"]["display_name"],
                    "formal_order": record["formula"]["formal_order"],
                    "s2_stage_count": record["formula"]["s2_stage_count"],
                    "rotations": record["formula"]["rotations"],
                    "model": model,
                    "status": "complete",
                    "passed": result["passed"],
                    "predicted_time": result["model_optimum"]["time"],
                    "predicted_cost": result["model_optimum"]["cost"],
                    "direct_cost_at_prediction": at_star["direct_cost"],
                    "direct_local_grid_minimum_cost": (
                        direct_minimum["direct_cost"] if direct_minimum is not None else None
                    ),
                    **result["metrics"],
                })

    passes_both: dict[str, list[str]] = {}
    for model in MODELS:
        passed = []
        for formula in FORMULAE:
            records = [
                formula_records[geometry][formula] for geometry in GEOMETRIES
            ]
            if all(
                record["status"] == "complete"
                and record["models"][model]["passed"]
                for record in records
            ):
                passed.append(formula)
        passes_both[model] = passed

    three_term = passes_both["three_term"]
    fourth_order_others = {
        "yoshida4", "paper_new4", "m5_best", "two_term_center"
    }
    if (
        "joint_refine_r0_s0046" in three_term
        and not fourth_order_others.intersection(three_term)
    ):
        category = 4
        conclusion = (
            "Only the joint full-electron/frozen-core candidate improves enough "
            "to pass both geometries with the three-term model."
        )
    elif len(three_term) >= 3:
        category = 1
        conclusion = (
            "At least half of the fixed PF set passes both geometries after "
            "including the third error term; omitted higher terms are the main diagnosis."
        )
    elif three_term:
        category = 2
        conclusion = (
            "Only a subset of fixed PFs passes both geometries; finite-time "
            "predictability depends strongly on the PF coefficients."
        )
    else:
        category = 3
        conclusion = (
            "No PF passes both geometries even with the three-term model; "
            "the low-order polynomial model or coefficient search must be revisited."
        )

    payload = {
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete",
        "geometries": list(GEOMETRIES),
        "formulae": list(FORMULAE),
        "models": list(MODELS),
        "pass_on_both_geometries": passes_both,
        "classification": {
            "category": category,
            "conclusion": conclusion,
            "automatic_category_1_rule": "three-term passes on both geometries for at least 3 of 6 PFs",
            "automatic_category_4_rule": "joint candidate passes and no other tested fourth-order PF passes",
        },
        "rows": rows,
    }
    json_path = root / "summary.json"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Full-electron NH3 higher-term diagnosis",
        "",
        "Status: complete",
        "",
        "## Main conclusion",
        "",
        "Category " + str(category) + ": " + conclusion,
        "",
        "## Passes on both geometries",
        "",
        "| model | passing PFs |",
        "|---|---|",
    ]
    for model in MODELS:
        joined = ", ".join(passes_both[model]) or "none"
        lines.append("| " + model + " | " + joined + " |")
    lines.extend([
        "",
        "## Per-condition metrics",
        "",
        "| geometry | PF | model | pass | eta* | eta_min | eta_t | max residual/eps | direct cost at predicted time | stages | rotations |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        if row["model"] is None:
            lines.append(
                "| " + row["geometry"] + " | " + row["formula"]
                + " | n/a | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
            )
            continue
        lines.append(
            f"| {row['geometry']} | {row['formula']} | {row['model']} | "
            f"{row['passed']} | {display(row['eta_star'])} | "
            f"{display(row['eta_min'])} | {display(row['eta_t'])} | "
            f"{row['maximum_unseen_residual_over_epsilon']:.6g} | "
            f"{display(row['direct_cost_at_prediction'], '.8g')} | "
            f"{row['s2_stage_count']} | {row['rotations']} |"
        )
    lines.extend([
        "",
        "PF direct cost and model prediction accuracy are reported separately.",
        "The legacy two-term model uses only 0.1, 0.2, and 0.3 t_ana.",
        "All other direct models use 0.1 through 0.5 t_ana.",
    ])
    (root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
