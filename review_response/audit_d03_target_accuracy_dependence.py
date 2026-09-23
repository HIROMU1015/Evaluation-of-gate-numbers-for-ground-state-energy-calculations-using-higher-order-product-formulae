"""Audit target-accuracy dependence using only committed direct curves.

This is the local, zero-new-truth first stage of D03.  It transfers the model
coefficients fitted at CA/10 to CA and CA/100, recomputes the QPE cost, audits
whether saved direct points bracket the new optima, and emits a manifest of
direct points that would be needed for a conclusive follow-up.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = Path(__file__).with_name(
    "d03_target_accuracy_dependence_protocol.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def qpe_cost(
    time_value: float,
    absolute_error: float,
    rotations: int,
    target_error: float,
    beta: float = 1.2,
) -> float | None:
    if time_value <= 0.0 or absolute_error < 0.0:
        return None
    budget = float(target_error) - float(absolute_error)
    if budget <= 0.0:
        return None
    return float(beta) * int(rotations) / (float(time_value) * budget)


def leading_analytic_time(alpha: float, order: int, target_error: float) -> float:
    if alpha <= 0.0 or order <= 0 or target_error <= 0.0:
        raise ValueError("alpha, order, and target_error must be positive")
    return float((target_error / ((order + 1) * alpha)) ** (1.0 / order))


def model_prediction(model: dict[str, Any], time_value: float) -> float:
    return float(
        sum(
            float(coefficient) * float(time_value) ** int(power)
            for power, coefficient in zip(
                model["coefficient_powers"], model["coefficient_values"]
            )
        )
    )


def optimize_model(
    model: dict[str, Any],
    analytic_time: float,
    rotations: int,
    target_error: float,
    beta: float,
    relative_interval: Sequence[float],
    grid_points: int,
) -> dict[str, Any]:
    lower, upper = map(float, relative_interval)
    best: dict[str, Any] | None = None
    for index in range(int(grid_points)):
        relative = lower + (upper - lower) * index / (int(grid_points) - 1)
        time_value = relative * float(analytic_time)
        signed = model_prediction(model, time_value)
        cost = qpe_cost(time_value, abs(signed), rotations, target_error, beta)
        if cost is None:
            continue
        if best is None or cost < best["model_cost"]:
            best = {
                "model_time": time_value,
                "model_relative_to_target_t_ana": relative,
                "model_signed_shift_hartree": signed,
                "model_absolute_error_hartree": abs(signed),
                "model_cost": cost,
                "model_optimum_at_search_boundary": index
                in (0, int(grid_points) - 1),
            }
    if best is None:
        return {"model_status": "no_feasible_model_time"}
    best["model_status"] = "complete"
    return best


def _point_time_key(time_value: float) -> str:
    return f"{float(time_value):.14e}"


def consolidate_direct_points(
    raw: dict[str, Any], fine: dict[str, Any] | None
) -> list[dict[str, Any]]:
    packed: dict[str, dict[str, Any]] = {}

    def add(point: dict[str, Any], source: str, training: bool) -> None:
        if point.get("time") is None or point.get("signed_direct_shift_hartree") is None:
            return
        key = _point_time_key(float(point["time"]))
        current = packed.get(key)
        value = {
            "time": float(point["time"]),
            "signed_direct_shift_hartree": float(
                point["signed_direct_shift_hartree"]
            ),
            "absolute_direct_error_hartree": abs(
                float(point["signed_direct_shift_hartree"])
            ),
            "ground_overlap_probability": point.get(
                "ground_overlap_probability"
            ),
            "eigenpair_residual_2_norm": point.get("eigenpair_residual_2_norm"),
            "used_for_original_training": bool(training),
            "sources": [source],
        }
        if current is None:
            packed[key] = value
            return
        if abs(
            current["signed_direct_shift_hartree"]
            - value["signed_direct_shift_hartree"]
        ) > 1e-9:
            raise ValueError(f"inconsistent direct shift at time {point['time']}")
        current["used_for_original_training"] = bool(
            current["used_for_original_training"] or training
        )
        if source not in current["sources"]:
            current["sources"].append(source)

    for point in raw.get("training_direct_points", []):
        add(point, "training_direct_points", True)
    for model_name, result in raw.get("models", {}).items():
        for point in result.get("direct_validation_points", []):
            add(point, f"stage1:{model_name}", False)
        minimum = result.get("direct_grid_minimum")
        if isinstance(minimum, dict):
            add(minimum, f"stage1_minimum:{model_name}", False)
    if fine is not None:
        for point in fine.get("computed_points", []):
            add(point, "stage2_computed", False)
        for point in fine.get("reused_points", []):
            add(point, "stage2_reused", bool(point.get("used_for_direct_model_fit")))
    return sorted(packed.values(), key=lambda item: item["time"])


def _nearest_point(
    points: Sequence[dict[str, Any]], requested_time: float
) -> tuple[dict[str, Any] | None, float | None]:
    if not points:
        return None, None
    point = min(points, key=lambda item: abs(item["time"] - requested_time))
    difference = abs(float(point["time"]) / float(requested_time) - 1.0)
    return point, float(difference)


def direct_minimum_bracket(
    points: Sequence[dict[str, Any]],
    rotations: int,
    target_error: float,
    beta: float,
    maximum_neighbor_gap_fraction: float,
) -> dict[str, Any]:
    feasible: list[dict[str, Any]] = []
    for point in points:
        cost = qpe_cost(
            point["time"],
            point["absolute_direct_error_hartree"],
            rotations,
            target_error,
            beta,
        )
        if cost is not None:
            feasible.append({**point, "direct_cost": cost})
    if not feasible:
        return {"direct_grid_status": "no_feasible_saved_point"}
    feasible.sort(key=lambda item: item["time"])
    selected = min(range(len(feasible)), key=lambda index: feasible[index]["direct_cost"])
    minimum = feasible[selected]
    lower = feasible[selected - 1] if selected > 0 else None
    upper = feasible[selected + 1] if selected + 1 < len(feasible) else None
    lower_gap = (
        (minimum["time"] - lower["time"]) / minimum["time"]
        if lower is not None
        else None
    )
    upper_gap = (
        (upper["time"] - minimum["time"]) / minimum["time"]
        if upper is not None
        else None
    )
    bracketed = bool(
        lower is not None
        and upper is not None
        and lower_gap is not None
        and upper_gap is not None
        and lower_gap <= maximum_neighbor_gap_fraction
        and upper_gap <= maximum_neighbor_gap_fraction
        and lower["direct_cost"] >= minimum["direct_cost"]
        and upper["direct_cost"] >= minimum["direct_cost"]
    )
    return {
        "direct_grid_status": "complete",
        "direct_grid_minimum_time": minimum["time"],
        "direct_grid_minimum_cost": minimum["direct_cost"],
        "direct_grid_minimum_error_hartree": minimum[
            "absolute_direct_error_hartree"
        ],
        "direct_grid_minimum_bracketed": bracketed,
        "direct_grid_minimum_lower_gap_fraction": lower_gap,
        "direct_grid_minimum_upper_gap_fraction": upper_gap,
        "feasible_saved_point_count": len(feasible),
    }


def _fine_path(root: Path, stem: str) -> Path:
    return root / "fine" / "raw" / f"{stem}.json"


def _iter_records(
    protocol: dict[str, Any], project_root: Path
) -> Iterable[dict[str, Any]]:
    for dataset, spec in protocol["datasets"].items():
        root = project_root / spec["root"]
        for condition in spec["conditions"]:
            for formula in spec["formulas"]:
                stem = f"{condition}__{formula}"
                raw_path = root / "raw" / f"{stem}.json"
                if not raw_path.is_file():
                    yield {
                        "dataset": dataset,
                        "condition": condition,
                        "formula": formula,
                        "status": "missing_raw_record",
                        "raw_path": str(raw_path.relative_to(project_root)),
                    }
                    continue
                raw = _read_json(raw_path)
                fine_path = _fine_path(root, stem)
                fine = _read_json(fine_path) if fine_path.is_file() else None
                model_name = spec["model_mapping"][formula]
                if raw.get("status") != "complete":
                    yield {
                        "dataset": dataset,
                        "condition": condition,
                        "formula": formula,
                        "status": raw.get("status", "incomplete"),
                        "failure_reason": raw.get("failure_reason"),
                        "raw_path": str(raw_path.relative_to(project_root)),
                        "fine_path": (
                            str(fine_path.relative_to(project_root))
                            if fine_path.is_file()
                            else None
                        ),
                    }
                    continue
                if model_name not in raw.get("models", {}):
                    yield {
                        "dataset": dataset,
                        "condition": condition,
                        "formula": formula,
                        "status": "missing_model",
                        "model_name": model_name,
                        "raw_path": str(raw_path.relative_to(project_root)),
                    }
                    continue
                yield {
                    "dataset": dataset,
                    "condition": condition,
                    "formula": formula,
                    "status": "complete",
                    "model_name": model_name,
                    "raw": raw,
                    "fine": fine,
                    "raw_path": raw_path,
                    "fine_path": fine_path if fine_path.is_file() else None,
                    "points": consolidate_direct_points(raw, fine),
                }


def analyze_record(
    record: dict[str, Any], protocol: dict[str, Any], target_name: str, epsilon: float
) -> dict[str, Any]:
    base = {
        "dataset": record["dataset"],
        "condition": record["condition"],
        "formula": record["formula"],
        "target_name": target_name,
        "target_error_hartree": epsilon,
        "source_status": record["status"],
    }
    if record["status"] != "complete":
        return {**base, "analysis_status": record["status"]}

    raw = record["raw"]
    model = raw["models"][record["model_name"]]["model"]
    order = int(raw["formula"]["formal_order"])
    rotations = int(raw["formula"]["rotations"])
    alpha = float(raw["alpha"])
    transfer = protocol["fixed_model_transfer"]
    beta = float(protocol["cost"]["beta"])
    target_t_ana = leading_analytic_time(alpha, order, epsilon)
    optimum = optimize_model(
        model,
        target_t_ana,
        rotations,
        epsilon,
        beta,
        transfer["optimization_relative_to_target_analytic_time"],
        int(transfer["optimization_grid_points"]),
    )
    result = {
        **base,
        "analysis_status": optimum["model_status"],
        "model_name": record["model_name"],
        "formal_order": order,
        "rotations": rotations,
        "alpha": alpha,
        "source_analytic_time_ca_div_10": float(raw["analytic_time"]),
        "target_analytic_time": target_t_ana,
        "saved_direct_point_count": len(record["points"]),
        **optimum,
    }
    if optimum["model_status"] != "complete":
        return result

    coverage = protocol["direct_curve_coverage"]
    nearest, mismatch = _nearest_point(record["points"], optimum["model_time"])
    nearest_covered = bool(
        nearest is not None
        and mismatch is not None
        and mismatch
        <= float(coverage["model_time_nearest_point_relative_tolerance"])
    )
    result["nearest_direct_time"] = nearest["time"] if nearest else None
    result["nearest_direct_time_relative_mismatch"] = mismatch
    result["model_time_direct_point_covered"] = nearest_covered
    if nearest is not None:
        result["nearest_direct_error_hartree"] = nearest[
            "absolute_direct_error_hartree"
        ]
        result["nearest_direct_cost"] = qpe_cost(
            nearest["time"],
            nearest["absolute_direct_error_hartree"],
            rotations,
            epsilon,
            beta,
        )

    minimum = direct_minimum_bracket(
        record["points"],
        rotations,
        epsilon,
        beta,
        float(coverage["direct_minimum_maximum_neighbor_gap_fraction"]),
    )
    result.update(minimum)
    lower_band, upper_band = coverage["validation_band_relative_to_model_time"]
    local = [
        point
        for point in record["points"]
        if float(lower_band) * optimum["model_time"]
        <= point["time"]
        <= float(upper_band) * optimum["model_time"]
        and not point["used_for_original_training"]
    ]
    result["local_unseen_point_count"] = len(local)
    result["local_unseen_coverage"] = len(local) >= int(
        coverage["minimum_validation_points"]
    )
    if local:
        result["maximum_local_unseen_residual_over_target_error"] = max(
            abs(
                point["signed_direct_shift_hartree"]
                - model_prediction(model, point["time"])
            )
            / epsilon
            for point in local
        )

    if (
        nearest_covered
        and result.get("nearest_direct_cost") is not None
        and minimum.get("direct_grid_status") == "complete"
    ):
        result["eta_star"] = abs(
            optimum["model_cost"] - result["nearest_direct_cost"]
        ) / result["nearest_direct_cost"]
        result["eta_min"] = (
            result["nearest_direct_cost"] / minimum["direct_grid_minimum_cost"]
            - 1.0
        )
        result["eta_t"] = abs(
            optimum["model_time"] / minimum["direct_grid_minimum_time"] - 1.0
        )

    full_coverage = bool(
        nearest_covered
        and minimum.get("direct_grid_minimum_bracketed")
        and result["local_unseen_coverage"]
    )
    result["full_existing_curve_coverage"] = full_coverage
    thresholds = protocol["pass_thresholds"]
    checks = {
        "eta_star": result.get("eta_star") is not None
        and result["eta_star"] <= float(thresholds["eta_star"]),
        "eta_min": result.get("eta_min") is not None
        and result["eta_min"] <= float(thresholds["eta_min"]),
        "eta_t": result.get("eta_t") is not None
        and result["eta_t"] <= float(thresholds["eta_t"]),
        "maximum_local_unseen_residual_over_target_error": result.get(
            "maximum_local_unseen_residual_over_target_error"
        )
        is not None
        and result["maximum_local_unseen_residual_over_target_error"]
        <= float(thresholds["maximum_local_unseen_residual_over_target_error"]),
    }
    result.update({f"check_{key}": value for key, value in checks.items()})
    result["fixed_model_passed"] = bool(full_coverage and all(checks.values()))
    result["analysis_status"] = (
        "validated_existing_curve" if full_coverage else "insufficient_existing_curve"
    )
    return result


def missing_points_for_record(
    record: dict[str, Any], metric: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    if record["status"] != "complete" or metric.get("model_time") is None:
        return []
    coverage = protocol["direct_curve_coverage"]
    tolerance = float(coverage["model_time_nearest_point_relative_tolerance"])
    recommended = protocol["recommended_additional_point_subset"]
    if record["dataset"] == "p03":
        preferred = bool(
            record["condition"] in recommended["p03_conditions"]
            and record["formula"] in recommended["p03_formulas"]
        )
    else:
        preferred = bool(
            record["condition"] in recommended["nh3_conditions"]
            and record["formula"] in recommended["nh3_formulas"]
        )
    rows: list[dict[str, Any]] = []
    for relative in coverage["coarse_relative_grid"]:
        requested = float(relative) * float(metric["model_time"])
        _, mismatch = _nearest_point(record["points"], requested)
        if mismatch is not None and mismatch <= tolerance:
            continue
        rows.append(
            {
                "dataset": record["dataset"],
                "condition": record["condition"],
                "formula": record["formula"],
                "target_name": metric["target_name"],
                "target_error_hartree": metric["target_error_hartree"],
                "point_role": "direct_coarse_validation",
                "relative_to_model_time": relative,
                "requested_time": requested,
                "recommended_stage1": preferred,
                "existing_nearest_relative_mismatch": mismatch,
            }
        )
    training_spec = protocol["optional_target_specific_refit_audit"]
    for relative in training_spec["training_relative_to_target_analytic_time"]:
        requested = float(relative) * float(metric["target_analytic_time"])
        _, mismatch = _nearest_point(record["points"], requested)
        if mismatch is not None and mismatch <= tolerance:
            continue
        rows.append(
            {
                "dataset": record["dataset"],
                "condition": record["condition"],
                "formula": record["formula"],
                "target_name": metric["target_name"],
                "target_error_hartree": metric["target_error_hartree"],
                "point_role": "optional_target_specific_refit_training",
                "relative_to_target_analytic_time": relative,
                "requested_time": requested,
                "recommended_stage1": False,
                "existing_nearest_relative_mismatch": mismatch,
            }
        )
    return rows


def _ranking_rows(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[(row["dataset"], row["condition"], row["target_name"])].append(row)
    output: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        covered = [
            row
            for row in rows
            if row.get("direct_grid_minimum_bracketed")
            and row.get("direct_grid_minimum_cost") is not None
        ]
        ranked = sorted(covered, key=lambda row: row["direct_grid_minimum_cost"])
        best = ranked[0] if ranked else None
        for position, row in enumerate(ranked, start=1):
            output.append(
                {
                    "dataset": key[0],
                    "condition": key[1],
                    "target_name": key[2],
                    "formula": row["formula"],
                    "rank_among_covered": position,
                    "covered_formula_count": len(ranked),
                    "direct_grid_minimum_cost": row["direct_grid_minimum_cost"],
                    "cost_ratio_to_best_covered": row["direct_grid_minimum_cost"]
                    / best["direct_grid_minimum_cost"],
                    "best_covered_formula": best["formula"],
                    "ranking_status": (
                        "complete_all_declared_formulas"
                        if len(ranked) == len(rows)
                        else "partial_coverage"
                    ),
                }
            )
        if not ranked:
            output.append(
                {
                    "dataset": key[0],
                    "condition": key[1],
                    "target_name": key[2],
                    "formula": None,
                    "rank_among_covered": None,
                    "covered_formula_count": 0,
                    "direct_grid_minimum_cost": None,
                    "cost_ratio_to_best_covered": None,
                    "best_covered_formula": None,
                    "ranking_status": "insufficient_existing_curve",
                }
            )
    return output


def _coverage_rows(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[(row["dataset"], row["target_name"])].append(row)
    output: list[dict[str, Any]] = []
    for (dataset, target), rows in sorted(grouped.items()):
        complete = [row for row in rows if row.get("source_status") == "complete"]
        covered = [row for row in complete if row.get("full_existing_curve_coverage")]
        passed = [row for row in covered if row.get("fixed_model_passed")]
        output.append(
            {
                "dataset": dataset,
                "target_name": target,
                "declared_rows": len(rows),
                "source_complete_rows": len(complete),
                "fully_covered_rows": len(covered),
                "fixed_model_pass_rows": len(passed),
                "coverage_fraction_of_source_complete": (
                    len(covered) / len(complete) if complete else None
                ),
            }
        )
    return output


def _report(
    path: Path,
    audit: dict[str, Any],
    coverage: Sequence[dict[str, Any]],
    rankings: Sequence[dict[str, Any]],
) -> None:
    lines = [
        "# D03 target-accuracy dependence: existing-curve audit",
        "",
        f"Status: **{audit['status']}**",
        "",
        "This is a retrospective fixed-model transfer and coverage audit, not an independent holdout. No new direct PF eigenvalue point was computed.",
        "",
        "## Existing-curve coverage",
        "",
        "| dataset | target | complete source rows | fully covered | fixed-model passes |",
        "|---|---|---:|---:|---:|",
    ]
    for row in coverage:
        lines.append(
            f"| {row['dataset']} | {row['target_name']} | {row['source_complete_rows']} | {row['fully_covered_rows']} | {row['fixed_model_pass_rows']} |"
        )
    lines.extend(
        [
            "",
            "A row is fully covered only when a saved direct point lies within 0.5% of the transferred model optimum, at least three unseen points cover 0.85--1.15 of that optimum, and the observed direct-grid minimum is bracketed by saved neighbors no farther than 3% in time. Sparse-grid minima are not called continuous global minima.",
            "",
            "## Covered direct rankings",
            "",
            "| dataset | condition | target | best covered PF | coverage status |",
            "|---|---|---|---|---|",
        ]
    )
    seen: set[tuple[str, str, str]] = set()
    for row in rankings:
        key = (row["dataset"], row["condition"], row["target_name"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"| {row['dataset']} | {row['condition']} | {row['target_name']} | {row.get('best_covered_formula') or 'not determined'} | {row['ranking_status']} |"
        )
    lines.extend(
        [
            "",
            "## Additional-point decision",
            "",
            f"- Recommended coarse direct points for a conclusive follow-up: **{audit['recommended_new_direct_point_count']}**.",
            f"- Optional target-specific refit points inventoried but not authorized: **{audit['optional_refit_point_count']}**.",
            "- Fine 1% grids remain deferred until the coarse points identify a local minimum.",
            "- Morales Y8m10b has no N2/CO direct curve in the source holdout and is audited only where the NH3 source run qualified its fixed short-time protocol.",
            "",
            "## Interpretation limit",
            "",
            "Only targets with full saved-curve coverage support a PF ranking or fixed-model pass/fail statement. Other rows are missing-data findings, not model failures. The next step is the recommended coarse-point manifest, preferably on the GPU server; coefficients, molecules, bases, and thresholds remain frozen.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(project_root: Path, output_dir: Path) -> dict[str, Any]:
    protocol = _read_json(PROTOCOL_PATH)
    output_dir.mkdir(parents=True, exist_ok=False)
    records = list(_iter_records(protocol, project_root))
    metrics: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    source_paths: set[Path] = {PROTOCOL_PATH}
    for record in records:
        inventory.append(
            {
                "dataset": record["dataset"],
                "condition": record["condition"],
                "formula": record["formula"],
                "status": record["status"],
                "model_name": record.get("model_name"),
                "saved_direct_point_count": len(record.get("points", [])),
                "raw_path": (
                    str(record["raw_path"].relative_to(project_root))
                    if isinstance(record.get("raw_path"), Path)
                    else record.get("raw_path")
                ),
                "fine_path": (
                    str(record["fine_path"].relative_to(project_root))
                    if isinstance(record.get("fine_path"), Path)
                    else record.get("fine_path")
                ),
                "failure_reason": record.get("failure_reason"),
            }
        )
        if isinstance(record.get("raw_path"), Path):
            source_paths.add(record["raw_path"])
        if isinstance(record.get("fine_path"), Path):
            source_paths.add(record["fine_path"])
        for target_name, epsilon in protocol["target_errors_hartree"].items():
            metric = analyze_record(record, protocol, target_name, float(epsilon))
            metrics.append(metric)
            if target_name != "CA_div_10":
                missing.extend(missing_points_for_record(record, metric, protocol))

    rankings = _ranking_rows(metrics)
    coverage = _coverage_rows(metrics)
    recommended = [
        row
        for row in missing
        if row["point_role"] == "direct_coarse_validation"
        and row["recommended_stage1"]
    ]
    optional = [
        row
        for row in missing
        if row["point_role"] == "optional_target_specific_refit_training"
    ]
    status = (
        "complete_existing_curve_audit"
        if not recommended
        else "complete_existing_curve_audit_requires_additional_direct_points"
    )
    audit = {
        "schema": "d03_target_accuracy_dependence_existing_curve_audit_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "new_direct_truth_point_count": 0,
        "metric_row_count": len(metrics),
        "recommended_new_direct_point_count": len(recommended),
        "optional_refit_point_count": len(optional),
        "coverage": coverage,
        "scope": protocol["scope_limits"],
    }
    _write_csv(output_dir / "curve_inventory.csv", inventory)
    _write_csv(output_dir / "multi_accuracy_metrics.csv", metrics)
    _write_csv(output_dir / "condition_rankings.csv", rankings)
    _write_csv(output_dir / "coverage_summary.csv", coverage)
    _write_csv(output_dir / "missing_direct_points.csv", missing)
    _atomic_json(
        output_dir / "missing_direct_points.json",
        {
            "status": "planning_only_no_points_computed",
            "protocol_sha256": audit["protocol_sha256"],
            "recommended_count": len(recommended),
            "optional_refit_count": len(optional),
            "points": missing,
        },
    )
    _atomic_json(output_dir / "audit.json", audit)
    _report(output_dir / "report.md", audit, coverage, rankings)
    source_hashes = {
        str(path.relative_to(project_root)): _sha256(path)
        for path in sorted(source_paths)
    }
    artifact_hashes = {
        path.name: _sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "manifest.json"
    }
    _atomic_json(
        output_dir / "manifest.json",
        {
            "schema": "d03_target_accuracy_dependence_manifest_v1",
            "status": status,
            "protocol_sha256": audit["protocol_sha256"],
            "new_direct_truth_point_count": 0,
            "source_hashes": source_hashes,
            "artifact_hashes": artifact_hashes,
        },
    )
    (output_dir / "AUDIT_COMPLETE").touch()
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    audit = run(args.project_root.resolve(), args.output_dir.resolve())
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
