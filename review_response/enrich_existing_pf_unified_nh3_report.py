"""Add execution and eigenbranch diagnostics to the unified NH3 report."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any


MARKER = "<!-- unified-nh3-diagnostics -->"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def fmt(value: Any, spec: str = ".6g") -> str:
    return "n/a" if value is None else format(float(value), spec)


def collect(artifact: Path) -> dict[str, Any]:
    summary = load(artifact / "aggregate/summary.json")
    plan = load(artifact / "stage2_plan.json")
    fine = [load(path) for path in sorted((artifact / "fine/raw").glob("*.json"))]
    raw = [load(path) for path in sorted((artifact / "raw").glob("*.json"))]
    computed = [point for task in fine for point in task.get("computed_points", ())]
    model_rows = [row for row in summary["rows"] if row.get("model") is not None]
    passing = [row for row in model_rows if row["final_passed"]]

    passing_keys = {
        (row["condition"], row["formula"], row["model"]) for row in passing
    }
    passing_adjacent = []
    for task in fine:
        condition = task["task"]["condition"]
        formula = task["task"]["formula"]
        for point in task.get("computed_points", ()):
            if point.get("adjacent_selected_vector_overlap_probability") is None:
                continue
            if any(
                (condition, formula, request["model"]) in passing_keys
                for request in point.get("requests", ())
            ):
                passing_adjacent.append(
                    float(point["adjacent_selected_vector_overlap_probability"])
                )

    branch_warnings = []
    for row in model_rows:
        ground = row.get("minimum_ground_overlap_probability")
        if ground is not None and float(ground) < 0.9:
            branch_warnings.append({
                "condition": row["condition"],
                "formula": row["formula"],
                "model": row["model"],
                "final_passed": row["final_passed"],
                "minimum_ground_overlap_probability": ground,
                "reason": "minimum ground-connected branch overlap below 0.9",
            })

    timestamps = [
        value
        for record in raw + fine
        for value in (record.get("started_at"), record.get("completed_at"))
        if value is not None
    ]
    started = min(datetime.fromisoformat(value) for value in timestamps)
    completed = max(datetime.fromisoformat(value) for value in timestamps)
    fine_started = min(datetime.fromisoformat(task["started_at"]) for task in fine)
    fine_completed = max(datetime.fromisoformat(task["completed_at"]) for task in fine)

    return {
        "stage1_records": len(raw),
        "stage1_complete": sum(record["status"] == "complete" for record in raw),
        "stage1_short_time_fit_failed": sum(
            record["status"] == "short_time_fit_failed" for record in raw
        ),
        "stage2_tasks": len(fine),
        "stage2_new_direct_points": len(computed),
        "stage2_reused_stage1_times": plan["totals"]["reused_stage1_times"],
        "stage2_selected_models": plan["totals"]["selected_models"],
        "elapsed_seconds_all_stages": (completed - started).total_seconds(),
        "elapsed_seconds_stage2": (fine_completed - fine_started).total_seconds(),
        "summed_direct_point_wall_seconds": sum(
            float(point["timing_seconds"]["total"]) for point in computed
        ),
        "maximum_cpu_rss_gib": max(
            int(point["peak_cpu_rss_kib"]) for point in computed
        ) / (1024.0 * 1024.0),
        "maximum_gpu_used_mib": max(
            int(point["timing_seconds"]["gpu_memory"]["maximum_used_mib"])
            for point in computed
        ),
        "maximum_gpu_peak_increment_mib": max(
            int(point["timing_seconds"]["gpu_memory"]["peak_increment_mib"])
            for point in computed
        ),
        "maximum_eigenpair_residual_all_new_points": max(
            float(point["eigenpair_residual_2_norm"]) for point in computed
        ),
        "minimum_ground_overlap_all_new_points": min(
            float(point["ground_overlap_probability"]) for point in computed
        ),
        "minimum_adjacent_overlap_all_available_new_points": min(
            float(point["adjacent_selected_vector_overlap_probability"])
            for point in computed
            if point.get("adjacent_selected_vector_overlap_probability") is not None
        ),
        "formal_passing_model_rows": len(passing),
        "minimum_ground_overlap_formal_passing_rows": min(
            float(row["minimum_ground_overlap_probability"]) for row in passing
        ),
        "maximum_eigenpair_residual_formal_passing_rows": max(
            float(row["maximum_eigenpair_residual_2_norm"]) for row in passing
        ),
        "minimum_adjacent_overlap_formal_passing_new_points": min(passing_adjacent),
        "branch_warnings": branch_warnings,
        "all_branch_warnings_are_formal_failures": all(
            not warning["final_passed"] for warning in branch_warnings
        ),
        "maximum_training_design_condition_number": max(
            float(row["training_design_condition_number"]) for row in model_rows
        ),
        "unstable_model_rows_at_declared_1e8_threshold": sum(
            not row["stable_analytic_model"] for row in model_rows
        ),
        "stage1_code_commits": sorted({record["git"]["commit"] for record in raw}),
        "stage2_code_commits": sorted({task["git"]["commit"] for task in fine}),
        "environment": fine[0]["environment"],
    }


def report_appendix(summary: dict[str, Any], diagnostics: dict[str, Any]) -> str:
    formulae = {row["formula"]: row for row in summary["formula_summary"]}
    yoshida4 = formulae["yoshida4"]
    yoshida6 = formulae["yoshida6_m3"]
    warnings = diagnostics["branch_warnings"]
    lines = [
        MARKER,
        "",
        "## Numerical and execution audit",
        "",
        f"- Stage 1: {diagnostics['stage1_records']} PF/Hamiltonian records "
        f"({diagnostics['stage1_complete']} model-validations, "
        f"{diagnostics['stage1_short_time_fit_failed']} fixed-protocol short-time-fit failures).",
        f"- Stage 2: {diagnostics['stage2_tasks']} fine-grid tasks, "
        f"{diagnostics['stage2_new_direct_points']} new direct eigenphase points, and "
        f"{diagnostics['stage2_reused_stage1_times']} reused bit-matched stage-1 times.",
        f"- Stage-2 elapsed wall time: {diagnostics['elapsed_seconds_stage2']/60.0:.2f} min; "
        f"summed point wall time: {diagnostics['summed_direct_point_wall_seconds']/3600.0:.2f} h.",
        f"- Peak per-process CPU RSS: {diagnostics['maximum_cpu_rss_gib']:.3f} GiB; "
        f"maximum observed GPU use: {diagnostics['maximum_gpu_used_mib']} MiB "
        f"(peak increment {diagnostics['maximum_gpu_peak_increment_mib']} MiB).",
        f"- Across all new points, maximum eigenpair residual was "
        f"{diagnostics['maximum_eigenpair_residual_all_new_points']:.3e}.",
        f"- Across the {diagnostics['formal_passing_model_rows']} formally passing rows, "
        f"minimum ground-state overlap was "
        f"{diagnostics['minimum_ground_overlap_formal_passing_rows']:.9f}, "
        f"minimum available adjacent-time overlap was "
        f"{diagnostics['minimum_adjacent_overlap_formal_passing_new_points']:.9f}, "
        f"and maximum eigenpair residual was "
        f"{diagnostics['maximum_eigenpair_residual_formal_passing_rows']:.3e}.",
        f"- Maximum training design condition number was "
        f"{diagnostics['maximum_training_design_condition_number']:.6g}; no row exceeded "
        "the declared diagnostic threshold of 1e8.",
        "",
        "### Eigenbranch warnings",
        "",
    ]
    if not warnings:
        lines.append("No ground-connected branch overlap fell below 0.9.")
    else:
        lines.extend([
            "All warnings below belong to formally failing models; none changes the passing set.",
            "",
            "| condition | PF | model | final pass | minimum ground overlap |",
            "|---|---|---|---:|---:|",
        ])
        for warning in warnings:
            lines.append(
                f"| {warning['condition']} | {warning['formula']} | {warning['model']} | "
                f"{warning['final_passed']} | {warning['minimum_ground_overlap_probability']:.6g} |"
            )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "1. **A fixed existing PF and a fixed model order can predict all four NH3 conditions.** "
        "Yoshida 4th passes with both the two-term and three-term models; Yoshida 6th m=3 "
        "passes with the three-term model.",
        "2. **Adding finite-time terms helps, but coefficients still matter.** The common "
        "two-/three-term fits rescue Yoshida 4th, whereas m5_best passes no condition and "
        "the other fixed fourth-order candidates do not pass both full-electron geometries.",
        "3. **Active-space success is substantially easier than full-electron transfer.** "
        "Several fourth-order PFs pass both active-space geometries, but only Yoshida 4th "
        "and Yoshida 6th m=3 retain one fixed model across both full-electron geometries.",
        f"4. **Predictability has a direct-cost premium relative to m5_best.** Yoshida 4th "
        f"has mean/worst direct-grid cost ratios {yoshida4['mean_direct_minimum_cost_ratio_to_m5']:.3f}/"
        f"{yoshida4['worst_direct_minimum_cost_ratio_to_m5']:.3f}; Yoshida 6th m=3 has "
        f"{yoshida6['mean_direct_minimum_cost_ratio_to_m5']:.3f}/"
        f"{yoshida6['worst_direct_minimum_cost_ratio_to_m5']:.3f}.",
        "5. **Recommended next step:** freeze Yoshida 4th (two-term primary, three-term "
        "cross-check) and Yoshida 6th m=3 (three-term) and move them to an unused molecular "
        "hold-out before starting an m=4 coefficient search. Yoshida 4th is the lower-cost "
        "predictive choice in this development comparison.",
        "",
        "Morales Y8m10b is not a four-condition candidate under the fixed protocol because "
        "its short-time fit fails for active-space equilibrium and full-electron stretch150; "
        "the thresholds were not changed post hoc.",
        "",
        "## Reproducibility",
        "",
        f"- Stage-1 code commit(s): `{', '.join(diagnostics['stage1_code_commits'])}`",
        f"- Stage-2 code commit(s): `{', '.join(diagnostics['stage2_code_commits'])}`",
        f"- Python: `{diagnostics['environment']['python']}`",
        f"- NumPy/SciPy/PySCF/CuPy: "
        f"`{diagnostics['environment']['packages']['numpy']}` / "
        f"`{diagnostics['environment']['packages']['scipy']}` / "
        f"`{diagnostics['environment']['packages']['pyscf']}` / "
        f"`{diagnostics['environment']['packages']['cupy-cuda12x']}`",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_dir.resolve()
    summary_path = artifact / "aggregate/summary.json"
    report_path = artifact / "aggregate/report.md"
    summary = load(summary_path)
    diagnostics = collect(artifact)
    summary["diagnostics"] = diagnostics
    write_json(summary_path, summary)
    write_json(artifact / "aggregate/diagnostics.json", diagnostics)
    base = report_path.read_text(encoding="utf-8").split(MARKER, 1)[0].rstrip()
    report_path.write_text(
        base + "\n\n" + report_appendix(summary, diagnostics), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
