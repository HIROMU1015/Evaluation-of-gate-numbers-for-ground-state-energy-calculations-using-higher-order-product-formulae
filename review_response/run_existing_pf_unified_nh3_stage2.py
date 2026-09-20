"""Plan, run, and aggregate the unified finite-time NH3 comparison.

Stage 1 is produced by ``run_existing_pf_unified_nh3_stage1.sh``.  This file
keeps the expensive stage-2 calculations separate: it selects candidates from
the fixed coarse-grid rules, reuses bit-identical coarse points, computes only
missing 1%-grid points, and then writes one unified summary.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np

import run_full_electron_nh3_higher_term_diagnosis as diagnosis


CONDITIONS = (
    "active_equilibrium",
    "active_stretch150",
    "full_equilibrium",
    "full_stretch150",
)
FORMULAE = tuple(diagnosis._formulae())
MODELS = (
    "short_time_asymptotic_one_term",
    "direct_refit_one_term",
    "two_term",
    "three_term",
)
FINE_RELATIVE_GRID = tuple(value / 100.0 for value in range(90, 111))
TIME_MATCH_RTOL = 2e-12
ISOLATED_DROP_FRACTION = 0.02
STABILITY_CONDITION_NUMBER = 1e8
BASELINE_FORMULA = "m5_best"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    diagnosis._atomic_json(path, payload)


def _condition_and_formula(path: Path) -> tuple[str, str]:
    try:
        condition, formula = path.stem.split("__", 1)
    except ValueError as exc:
        raise ValueError(f"unexpected raw filename: {path.name}") from exc
    return condition, formula


def _all_coarse_points(record: dict[str, Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = list(record.get("training_direct_points", ()))
    for result in record.get("models", {}).values():
        points.extend(result.get("direct_validation_points", ()))
    return points


def _same_time(left: float, right: float) -> bool:
    return bool(math.isclose(float(left), float(right), rel_tol=TIME_MATCH_RTOL, abs_tol=1e-14))


def _isolated_cost_drop(result: dict[str, Any]) -> bool:
    points = result.get("direct_validation_points", ())
    costs = [point.get("direct_cost") for point in points]
    for index in range(1, len(costs) - 1):
        if costs[index] is None or costs[index - 1] is None or costs[index + 1] is None:
            continue
        shoulder = min(float(costs[index - 1]), float(costs[index + 1]))
        if float(costs[index]) <= (1.0 - ISOLATED_DROP_FRACTION) * shoulder:
            return True
    return False


def _candidate_reasons(result: dict[str, Any]) -> list[str]:
    metrics = result["metrics"]
    reasons: list[str] = []
    if bool(result.get("passed")):
        reasons.append("all_four_coarse_checks_passed")
    eta_star = metrics.get("eta_star")
    eta_min = metrics.get("eta_min")
    eta_t = metrics.get("eta_t")
    residual = metrics.get("maximum_unseen_residual_over_epsilon")
    common = (
        eta_star is not None and float(eta_star) <= diagnosis.PASS_THRESHOLDS["eta_star"]
        and residual is not None
        and float(residual) <= diagnosis.PASS_THRESHOLDS["maximum_unseen_residual_over_epsilon"]
    )
    if common and eta_min is not None and eta_t is not None:
        if (
            float(eta_min) <= diagnosis.PASS_THRESHOLDS["eta_min"]
            and diagnosis.PASS_THRESHOLDS["eta_t"] < float(eta_t)
            <= 2.0 * diagnosis.PASS_THRESHOLDS["eta_t"]
        ):
            reasons.append("eta_t_only_within_twice_threshold")
        if (
            float(eta_t) <= diagnosis.PASS_THRESHOLDS["eta_t"]
            and diagnosis.PASS_THRESHOLDS["eta_min"] < float(eta_min)
            <= 2.0 * diagnosis.PASS_THRESHOLDS["eta_min"]
        ):
            reasons.append("eta_min_only_within_twice_threshold")
    if _isolated_cost_drop(result):
        reasons.append("isolated_coarse_grid_cost_drop")
    return reasons


def _find_reused_point(record: dict[str, Any], time_value: float) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    matches = [
        point for point in _all_coarse_points(record)
        if _same_time(float(point["time"]), time_value)
    ]
    if not matches:
        return None, []
    reference = matches[0]
    differences = [
        abs(float(point["signed_direct_shift_hartree"]) - float(reference["signed_direct_shift_hartree"]))
        for point in matches[1:]
    ]
    provenance = [{
        "source": "stage1_raw_json",
        "source_time": float(point["time"]),
        "signed_shift_hartree": float(point["signed_direct_shift_hartree"]),
    } for point in matches]
    reused = dict(reference)
    reused["reused"] = True
    reused["reuse_match_count"] = len(matches)
    reused["reuse_maximum_signed_shift_difference_hartree"] = max(differences, default=0.0)
    return reused, provenance


def make_plan(raw_dir: Path) -> dict[str, Any]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(raw_dir.glob("*.json")):
        condition, formula = _condition_and_formula(path)
        if condition in CONDITIONS and formula in FORMULAE:
            records[(condition, formula)] = _load(path)
    expected = {(condition, formula) for condition in CONDITIONS for formula in FORMULAE}
    if set(records) != expected:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        raise RuntimeError(f"stage1 record mismatch: missing={missing}, extra={extra}")
    if any(record.get("status") not in ("complete", "short_time_fit_failed") for record in records.values()):
        raise RuntimeError("stage1 is not complete")

    tasks: list[dict[str, Any]] = []
    model_candidates: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        for formula in FORMULAE:
            record = records[(condition, formula)]
            if record["status"] != "complete":
                continue
            selected: list[dict[str, Any]] = []
            requested: list[dict[str, Any]] = []
            for model_name in MODELS:
                result = record["models"][model_name]
                reasons = _candidate_reasons(result)
                model_candidates.append({
                    "condition": condition,
                    "formula": formula,
                    "model": model_name,
                    "selected": bool(reasons),
                    "reasons": reasons,
                    "coarse_passed": bool(result["passed"]),
                    "coarse_metrics": result["metrics"],
                })
                if not reasons:
                    continue
                optimum = float(result["model_optimum"]["time"])
                selected.append({
                    "model": model_name,
                    "reasons": reasons,
                    "model_optimum_time": optimum,
                })
                for relative in FINE_RELATIVE_GRID:
                    requested.append({
                        "model": model_name,
                        "relative_to_t_star": relative,
                        "requested_time": relative * optimum,
                    })
            if not selected:
                continue

            unique_points: list[dict[str, Any]] = []
            for request in sorted(requested, key=lambda item: float(item["requested_time"])):
                match = next(
                    (item for item in unique_points if _same_time(item["time"], request["requested_time"])),
                    None,
                )
                if match is None:
                    reused, provenance = _find_reused_point(record, float(request["requested_time"]))
                    match = {
                        "time": float(request["requested_time"]),
                        "requests": [],
                        "reused_point": reused,
                        "reuse_provenance": provenance,
                    }
                    unique_points.append(match)
                match["requests"].append(request)
            tasks.append({
                "task_id": f"{condition}__{formula}",
                "condition": condition,
                "formula": formula,
                "source_raw_json": str(raw_dir / f"{condition}__{formula}.json"),
                "candidate_models": selected,
                "requested_grid_points": len(requested),
                "unique_absolute_times": len(unique_points),
                "reused_stage1_times": sum(item["reused_point"] is not None for item in unique_points),
                "new_direct_times": sum(item["reused_point"] is None for item in unique_points),
                "points": unique_points,
            })
    return {
        "created_at": _now(),
        "status": "planned",
        "source_raw_dir": str(raw_dir),
        "conditions": list(CONDITIONS),
        "formulae": list(FORMULAE),
        "models": list(MODELS),
        "fine_relative_grid": list(FINE_RELATIVE_GRID),
        "candidate_rules": {
            "formal_pass": "all four fixed coarse checks pass",
            "near_miss": "eta_star and residual pass; exactly eta_min or eta_t is within twice its threshold",
            "isolated_drop": f"an interior coarse cost is at least {100*ISOLATED_DROP_FRACTION:.1f}% below both neighbours",
        },
        "time_deduplication_relative_tolerance": TIME_MATCH_RTOL,
        "model_candidates": model_candidates,
        "tasks": tasks,
        "totals": {
            "tasks": len(tasks),
            "selected_models": sum(len(task["candidate_models"]) for task in tasks),
            "requested_grid_points": sum(task["requested_grid_points"] for task in tasks),
            "unique_absolute_times": sum(task["unique_absolute_times"] for task in tasks),
            "reused_stage1_times": sum(task["reused_stage1_times"] for task in tasks),
            "new_direct_times": sum(task["new_direct_times"] for task in tasks),
        },
    }


def command_plan(args: argparse.Namespace) -> int:
    plan = make_plan(args.raw_dir.resolve())
    _write_json(args.output.resolve(), plan)
    print(json.dumps(plan["totals"], sort_keys=True), flush=True)
    return 0


def _plan_task(plan: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [task for task in plan["tasks"] if task["task_id"] == task_id]
    if len(matches) != 1:
        raise KeyError(f"task {task_id!r} occurs {len(matches)} times")
    return matches[0]


def command_fine_task(args: argparse.Namespace) -> int:
    plan = _load(args.plan.resolve())
    task = _plan_task(plan, args.task_id)
    source = _load(Path(task["source_raw_json"]))
    system = diagnosis._load_system(args.system_cache.resolve())
    sequence = diagnosis._formula_s2_sequence(task["formula"])
    rotations = diagnosis._rotation_count(system, sequence)
    output = args.output.resolve()
    if output.exists():
        payload = _load(output)
        completed = {float(point["time"]): point for point in payload.get("computed_points", ())}
    else:
        payload = {
            "status": "running",
            "started_at": _now(),
            "git": diagnosis._git_state(),
            "environment": diagnosis._versions(),
            "task": task,
            "source_stage1_status": source["status"],
            "physical_gpu_id": args.gpu_id,
            "backend": args.backend,
            "formula": source["formula"],
            "analytic_time": source["analytic_time"],
            "computed_points": [],
            "reused_points": [
                {"time": point["time"], "point": point["reused_point"], "requests": point["requests"]}
                for point in task["points"] if point["reused_point"] is not None
            ],
            "continuity_note": (
                "Adjacent-vector overlaps are evaluated within each uninterrupted set of newly "
                "computed times. Reused stage-1 points retain their original coarse-grid overlaps."
            ),
        }
        completed = {}
        _write_json(output, payload)

    previous = None
    for planned in task["points"]:
        if planned["reused_point"] is not None:
            previous = None
            continue
        time_value = float(planned["time"])
        existing = next((point for key, point in completed.items() if _same_time(key, time_value)), None)
        if existing is not None:
            previous = None
            continue
        point, vector = diagnosis._direct_point(
            system, sequence, time_value, rotations,
            args.backend, args.gpu_id, previous,
        )
        point.update({"requests": planned["requests"], "reused": False})
        payload["computed_points"].append(point)
        completed[time_value] = point
        previous = vector
        _write_json(output, payload)
    payload.update({"status": "complete", "completed_at": _now()})
    _write_json(output, payload)
    return 0


def _point_for_request(task: dict[str, Any], fine: dict[str, Any], model: str, relative: float) -> dict[str, Any]:
    requested_time = None
    for planned in task["points"]:
        if any(
            request["model"] == model
            and _same_time(float(request["relative_to_t_star"]), relative)
            for request in planned["requests"]
        ):
            requested_time = float(planned["time"])
            if planned["reused_point"] is not None:
                return dict(planned["reused_point"])
            break
    if requested_time is None:
        raise KeyError((task["task_id"], model, relative))
    matches = [point for point in fine["computed_points"] if _same_time(point["time"], requested_time)]
    if len(matches) != 1:
        raise RuntimeError(f"missing/duplicate fine point {task['task_id']} {model} {relative}")
    return dict(matches[0])


def _evaluate_fine_model(task: dict[str, Any], fine: dict[str, Any], record: dict[str, Any], model_name: str) -> dict[str, Any]:
    coarse = record["models"][model_name]
    model = coarse["model"]
    rotations = int(record["formula"]["rotations"])
    points = []
    for relative in FINE_RELATIVE_GRID:
        point = _point_for_request(task, fine, model_name, relative)
        prediction = diagnosis._prediction(model, float(point["time"]))
        point.update({
            "relative_to_t_star": relative,
            "model_signed_shift_hartree": prediction,
            "model_cost": diagnosis._cost(float(point["time"]), abs(prediction), rotations),
            "signed_residual_hartree": float(point["signed_direct_shift_hartree"] - prediction),
            "residual_over_epsilon": float(
                abs(point["signed_direct_shift_hartree"] - prediction) / diagnosis.EPSILON_E
            ),
        })
        points.append(point)
    at_star = points[FINE_RELATIVE_GRID.index(1.0)]
    finite = [point for point in points if point.get("direct_cost") is not None]
    direct_minimum = min(finite, key=lambda point: float(point["direct_cost"])) if finite else None
    direct_cost_at_star = at_star.get("direct_cost")
    optimum = coarse["model_optimum"]
    metrics = {
        "eta_star": (
            abs(float(optimum["cost"]) - float(direct_cost_at_star)) / float(direct_cost_at_star)
            if direct_cost_at_star is not None else None
        ),
        "eta_min": (
            float(direct_cost_at_star) / float(direct_minimum["direct_cost"]) - 1.0
            if direct_cost_at_star is not None and direct_minimum is not None else None
        ),
        "eta_t": (
            abs(float(optimum["time"]) / float(direct_minimum["time"]) - 1.0)
            if direct_minimum is not None else None
        ),
        "maximum_unseen_residual_over_epsilon": max(float(point["residual_over_epsilon"]) for point in points),
        "minimum_ground_overlap_probability": min(float(point["ground_overlap_probability"]) for point in points),
        "maximum_eigenpair_residual_2_norm": max(float(point["eigenpair_residual_2_norm"]) for point in points),
    }
    checks = {
        key: metrics[key] is not None and float(metrics[key]) <= threshold
        for key, threshold in diagnosis.PASS_THRESHOLDS.items()
    }
    return {
        "source": "stage2_fine_grid",
        "relative_grid": list(FINE_RELATIVE_GRID),
        "points": points,
        "direct_grid_minimum": direct_minimum,
        "metrics": metrics,
        "checks": checks,
        "passed": all(checks.values()),
        "training_design_condition_number": model["training_design_condition_number"],
        "stable_analytic_model": bool(
            math.isfinite(float(model["training_design_condition_number"]))
            and float(model["training_design_condition_number"]) <= STABILITY_CONDITION_NUMBER
        ),
    }


def _coarse_final(record: dict[str, Any], model_name: str) -> dict[str, Any]:
    result = record["models"][model_name]
    return {
        "source": "stage1_coarse_grid_not_selected_for_stage2",
        "direct_grid_minimum": result.get("direct_grid_minimum"),
        "metrics": result["metrics"],
        "checks": {name: result["checks"][name] for name in diagnosis.PASS_THRESHOLDS},
        "passed": bool(result["passed"]),
        "training_design_condition_number": result["model"]["training_design_condition_number"],
        "stable_analytic_model": bool(
            math.isfinite(float(result["model"]["training_design_condition_number"]))
            and float(result["model"]["training_design_condition_number"]) <= STABILITY_CONDITION_NUMBER
        ),
    }


def _fmt(value: Any, spec: str = ".5g") -> str:
    return "n/a" if value is None else format(float(value), spec)


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _pareto_rows(formula_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in formula_summary:
        dominated = any(
            other["best_fixed_model_pass_count"] >= candidate["best_fixed_model_pass_count"]
            and other["mean_direct_minimum_cost_ratio_to_m5"] <= candidate["mean_direct_minimum_cost_ratio_to_m5"]
            and (
                other["best_fixed_model_pass_count"] > candidate["best_fixed_model_pass_count"]
                or other["mean_direct_minimum_cost_ratio_to_m5"] < candidate["mean_direct_minimum_cost_ratio_to_m5"]
            )
            for other in formula_summary if other is not candidate
        )
        row = dict(candidate)
        row["pareto_nondominated"] = not dominated
        rows.append(row)
    return rows


def _write_pareto_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 760, 460
    margin = 70
    xs = [float(row["mean_direct_minimum_cost_ratio_to_m5"]) for row in rows]
    maximum_x = max(xs + [1.0]) * 1.08
    def xmap(value: float) -> float:
        return margin + (width - 2 * margin) * value / maximum_x
    def ymap(value: float) -> float:
        return height - margin - (height - 2 * margin) * value / len(CONDITIONS)
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="black"/>',
        f'<text x="{width/2}" y="{height-18}" text-anchor="middle" font-size="14">mean direct-grid minimum cost / m5</text>',
        f'<text x="18" y="{height/2}" transform="rotate(-90 18 {height/2})" text-anchor="middle" font-size="14">conditions passed by best fixed model</text>',
    ]
    for tick in range(len(CONDITIONS) + 1):
        elements.append(f'<text x="{margin-12}" y="{ymap(tick)+5}" text-anchor="end" font-size="12">{tick}</text>')
    for row in rows:
        x = xmap(float(row["mean_direct_minimum_cost_ratio_to_m5"]))
        y = ymap(float(row["best_fixed_model_pass_count"]))
        color = "#d62728" if row["pareto_nondominated"] else "#777777"
        elements.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="{color}"/>')
        elements.append(f'<text x="{x+7:.2f}" y="{y-7:.2f}" font-size="11">{row["formula"]}</text>')
    elements.append('</svg>')
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def command_aggregate(args: argparse.Namespace) -> int:
    raw_dir = args.raw_dir.resolve()
    plan = _load(args.plan.resolve())
    fine_dir = args.fine_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    task_map = {task["task_id"]: task for task in plan["tasks"]}
    fine_map = {}
    for path in fine_dir.glob("*.json"):
        payload = _load(path)
        if payload.get("status") == "complete":
            fine_map[payload["task"]["task_id"]] = payload
    missing_fine = sorted(set(task_map) - set(fine_map))
    if missing_fine:
        raise RuntimeError(f"stage2 fine tasks incomplete: {missing_fine}")

    rows: list[dict[str, Any]] = []
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(raw_dir.glob("*.json")):
        condition, formula = _condition_and_formula(path)
        if condition in CONDITIONS and formula in FORMULAE:
            records[(condition, formula)] = _load(path)
    for condition in CONDITIONS:
        for formula in FORMULAE:
            record = records[(condition, formula)]
            if record["status"] != "complete":
                rows.append({
                    "condition": condition, "formula": formula, "model": None,
                    "status": record["status"], "final_passed": False,
                })
                continue
            task_id = f"{condition}__{formula}"
            selected = {
                item["model"]: item["reasons"]
                for item in task_map.get(task_id, {}).get("candidate_models", ())
            }
            for model_name in MODELS:
                final = (
                    _evaluate_fine_model(task_map[task_id], fine_map[task_id], record, model_name)
                    if model_name in selected else _coarse_final(record, model_name)
                )
                metrics = final["metrics"]
                minimum = final.get("direct_grid_minimum")
                rows.append({
                    "condition": condition,
                    "formula": formula,
                    "display_name": record["formula"]["display_name"],
                    "formal_order": record["formula"]["formal_order"],
                    "s2_stage_count": record["formula"]["s2_stage_count"],
                    "rotations": record["formula"]["rotations"],
                    "model": model_name,
                    "status": "complete",
                    "stage2_selected": model_name in selected,
                    "stage2_reasons": selected.get(model_name, []),
                    "metric_source": final["source"],
                    "final_passed": final["passed"],
                    "stable_analytic_model": final["stable_analytic_model"],
                    "training_design_condition_number": final["training_design_condition_number"],
                    "direct_grid_minimum_cost": minimum.get("direct_cost") if minimum else None,
                    "direct_grid_minimum_time": minimum.get("time") if minimum else None,
                    **metrics,
                })

    cost_by_condition_formula: dict[tuple[str, str], float | None] = {}
    for condition in CONDITIONS:
        for formula in FORMULAE:
            costs = [
                row["direct_grid_minimum_cost"] for row in rows
                if row["condition"] == condition and row["formula"] == formula
                and row.get("direct_grid_minimum_cost") is not None
            ]
            cost_by_condition_formula[(condition, formula)] = min(costs) if costs else None
    cost_rows = []
    for condition in CONDITIONS:
        baseline = cost_by_condition_formula[(condition, BASELINE_FORMULA)]
        for formula in FORMULAE:
            cost = cost_by_condition_formula[(condition, formula)]
            cost_rows.append({
                "condition": condition,
                "formula": formula,
                "direct_grid_minimum_cost": cost,
                "ratio_to_m5": (
                    float(cost) / float(baseline)
                    if cost is not None and baseline is not None else None
                ),
            })

    formula_summary = []
    for formula in FORMULAE:
        model_counts = {
            model: sum(
                bool(row.get("final_passed"))
                for row in rows if row["formula"] == formula and row.get("model") == model
            )
            for model in MODELS
        }
        best_model = max(MODELS, key=lambda model: (model_counts[model], -MODELS.index(model)))
        ratios = [
            row["ratio_to_m5"] for row in cost_rows
            if row["formula"] == formula and row["ratio_to_m5"] is not None
        ]
        formula_summary.append({
            "formula": formula,
            "best_fixed_model": best_model,
            "best_fixed_model_pass_count": model_counts[best_model],
            "fixed_model_pass_counts": model_counts,
            "same_model_passes_all_four": any(count == len(CONDITIONS) for count in model_counts.values()),
            "active_space_both_pass_models": [
                model for model in MODELS if all(
                    any(row["condition"] == condition and row["formula"] == formula and row.get("model") == model and row.get("final_passed") for row in rows)
                    for condition in CONDITIONS[:2]
                )
            ],
            "full_electron_both_pass_models": [
                model for model in MODELS if all(
                    any(row["condition"] == condition and row["formula"] == formula and row.get("model") == model and row.get("final_passed") for row in rows)
                    for condition in CONDITIONS[2:]
                )
            ],
            "posthoc_any_model_passes_each_condition": all(
                any(row["condition"] == condition and row["formula"] == formula and row.get("final_passed") for row in rows)
                for condition in CONDITIONS
            ),
            "mean_direct_minimum_cost_ratio_to_m5": float(np.mean(ratios)) if ratios else None,
            "worst_direct_minimum_cost_ratio_to_m5": max(ratios) if ratios else None,
        })
    pareto = _pareto_rows([row for row in formula_summary if row["mean_direct_minimum_cost_ratio_to_m5"] is not None])

    same_model_all = [
        {"formula": row["formula"], "models": [model for model, count in row["fixed_model_pass_counts"].items() if count == 4]}
        for row in formula_summary if row["same_model_passes_all_four"]
    ]
    payload = {
        "created_at": _now(),
        "status": "complete",
        "development_comparison_not_independent_holdout": True,
        "source_stage1": str(raw_dir),
        "stage2_plan": str(args.plan.resolve()),
        "stage2_fine_dir": str(fine_dir),
        "thresholds": diagnosis.PASS_THRESHOLDS,
        "short_time_fit_failures": [
            {"condition": condition, "formula": formula, "failure_reason": records[(condition, formula)].get("failure_reason")}
            for condition in CONDITIONS for formula in FORMULAE
            if records[(condition, formula)]["status"] == "short_time_fit_failed"
        ],
        "same_pf_and_model_pass_all_four": same_model_all,
        "rows": rows,
        "cost_comparison": cost_rows,
        "formula_summary": formula_summary,
        "pareto": pareto,
    }
    _write_json(output_dir / "summary.json", payload)
    _write_csv(output_dir / "metrics.csv", rows)
    _write_csv(output_dir / "cost_comparison.csv", cost_rows)
    _write_csv(output_dir / "pareto.csv", pareto)
    _write_pareto_svg(output_dir / "pareto.svg", pareto)

    report = [
        "# Existing-PF unified finite-time NH3 comparison", "",
        "Status: complete", "",
        "This is a development comparison on the NH3 data used to select the short-time grid; it is not an independent hold-out.", "",
        "## Main result", "",
        ("The following fixed PF/model pairs pass all four conditions: " + ", ".join(
            f"{item['formula']} ({', '.join(item['models'])})" for item in same_model_all
        )) if same_model_all else "No fixed PF and fixed model order passes all four conditions.",
        "", "## Fixed-model predictability and cost", "",
        "| PF | best fixed model | conditions passed | all four | active both | full-electron both | post-hoc per-condition selection | mean cost/m5 | worst cost/m5 | Pareto |",
        "|---|---|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    pareto_map = {row["formula"]: row for row in pareto}
    for row in formula_summary:
        report.append(
            f"| {row['formula']} | {row['best_fixed_model']} | {row['best_fixed_model_pass_count']}/4 | "
            f"{row['same_model_passes_all_four']} | {', '.join(row['active_space_both_pass_models']) or 'none'} | "
            f"{', '.join(row['full_electron_both_pass_models']) or 'none'} | "
            f"{row['posthoc_any_model_passes_each_condition']} | "
            f"{_fmt(row['mean_direct_minimum_cost_ratio_to_m5'])} | {_fmt(row['worst_direct_minimum_cost_ratio_to_m5'])} | "
            f"{pareto_map[row['formula']]['pareto_nondominated']} |"
        )
    report.extend([
        "", "## Per-condition model checks", "",
        "| condition | PF | model | fine | pass | stable | eta* | eta_min | eta_t | max residual/eps | cond(X) | direct-grid min cost |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        if row.get("model") is None:
            report.append(f"| {row['condition']} | {row['formula']} | n/a | False | False | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        report.append(
            f"| {row['condition']} | {row['formula']} | {row['model']} | {row['stage2_selected']} | "
            f"{row['final_passed']} | {row['stable_analytic_model']} | {_fmt(row.get('eta_star'))} | "
            f"{_fmt(row.get('eta_min'))} | {_fmt(row.get('eta_t'))} | "
            f"{_fmt(row.get('maximum_unseen_residual_over_epsilon'))} | "
            f"{_fmt(row.get('training_design_condition_number'))} | {_fmt(row.get('direct_grid_minimum_cost'), '.8g')} |"
        )
    report.extend([
        "", "## Protocol notes", "",
        "- The four declared checks alone determine formal pass/fail; model conditioning is reported separately.",
        "- `post-hoc per-condition selection` is diagnostic and is not the general-candidate criterion.",
        "- Direct minima are minima on actually calculated grids, not continuous-time exact minima.",
        "- Short-time proxy fits and signed direct eigenphase errors remain separate quantities.",
        "- The baseline in cost ratios is `m5_best` under the same Hamiltonian condition.",
    ])
    (output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--raw-dir", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    fine = commands.add_parser("fine-task")
    fine.add_argument("--plan", type=Path, required=True)
    fine.add_argument("--task-id", required=True)
    fine.add_argument("--system-cache", type=Path, required=True)
    fine.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    fine.add_argument("--gpu-id", type=int, required=True)
    fine.add_argument("--output", type=Path, required=True)
    aggregate = commands.add_parser("aggregate")
    aggregate.add_argument("--raw-dir", type=Path, required=True)
    aggregate.add_argument("--plan", type=Path, required=True)
    aggregate.add_argument("--fine-dir", type=Path, required=True)
    aggregate.add_argument("--output-dir", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "plan":
        return command_plan(args)
    if args.command == "fine-task":
        return command_fine_task(args)
    if args.command == "aggregate":
        return command_aggregate(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
