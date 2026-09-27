#!/usr/bin/env python3
"""Run the registered retrospective H-chain direct optimal-time study.

The scientific calculation delegates each system/PF job to the existing
conserved-sector dense direct solver.  Jobs are kept separate so a completed
job can be reused only when its embedded protocol identity and fixed grid are
exact matches.  No earlier direct-result artifact is accepted as input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

import sweep_direct_scaling_h6_h7 as direct


LABEL_BY_KEY = dict(direct.FORMULA_LABELS)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _grid_from_protocol(protocol: dict[str, Any]) -> list[float]:
    rule = protocol["time_grid"]
    start = float(rule["start"])
    stop = float(rule["stop"])
    step = float(rule["step"])
    count = int(rule["point_count"])
    grid = [round(start + index * step, 12) for index in range(count)]
    if not math.isclose(grid[-1], stop, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("time-grid endpoint does not match protocol")
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError("protocol time grid is not strictly increasing")
    return grid


def _git_value(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def _job_name(h_chain: int, formula_key: str) -> str:
    return f"H{h_chain}_{formula_key}.json"


def _job_matches(
    payload: dict[str, Any],
    *,
    protocol_sha256: str,
    grid: Sequence[float],
    h_chain: int,
    formula_key: str,
) -> bool:
    provenance = payload.get("registered_protocol", {})
    return bool(
        payload.get("status") == "complete"
        and provenance.get("sha256") == protocol_sha256
        and provenance.get("h_chain") == h_chain
        and provenance.get("formula_key") == formula_key
        and payload.get("relative_times") == list(grid)
        and payload.get("formula_keys") == [formula_key]
        and set(payload.get("results", {})) == {f"H{h_chain}"}
    )


def _run_jobs(
    protocol: dict[str, Any],
    protocol_sha256: str,
    output: Path,
    *,
    resume: bool,
) -> list[Path]:
    raw_root = output / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    runtime_root = output / ".runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    grid = _grid_from_protocol(protocol)
    paths: list[Path] = []
    for system in protocol["systems"]["included"]:
        h_chain = int(system["h_chain"])
        for formula in protocol["product_formulas"]:
            formula_key = str(formula["key"])
            destination = raw_root / _job_name(h_chain, formula_key)
            paths.append(destination)
            if destination.exists():
                existing = _load_json(destination)
                if resume and _job_matches(
                    existing,
                    protocol_sha256=protocol_sha256,
                    grid=grid,
                    h_chain=h_chain,
                    formula_key=formula_key,
                ):
                    print(f"reuse complete protocol-identical job: {destination}", flush=True)
                    continue
                raise RuntimeError(
                    f"refusing to overwrite non-reusable job: {destination}"
                )

            temporary = runtime_root / _job_name(h_chain, formula_key)
            if temporary.exists():
                raise RuntimeError(
                    "incomplete runtime file exists; preserve it and choose a new "
                    f"output or remove it explicitly: {temporary}"
                )
            print(
                f"start registered direct job H{h_chain} {formula_key} "
                f"({len(grid)} points)",
                flush=True,
            )
            started = _utc_now()
            payload = direct.run(
                [h_chain],
                [formula_key],
                grid,
                direct.DEFAULT_M5_TIMES,
                direct.DEFAULT_Y8_TIMES,
                5e-12,
                float(protocol["target"]["epsilon_E_hartree"]),
                temporary,
                str(protocol["execution"]["unitary_build_method"]),
            )
            payload["registered_protocol"] = {
                "sha256": protocol_sha256,
                "h_chain": h_chain,
                "formula_key": formula_key,
                "started_at_utc": started,
                "completed_at_utc": _utc_now(),
                "prior_direct_results_reused": False,
            }
            _write_json(destination, payload)
            temporary.unlink()
            print(f"complete registered direct job: {destination}", flush=True)
    return paths


def _connected_true_component(mask: Sequence[bool], index: int) -> tuple[int, int]:
    if not mask[index]:
        raise ValueError("selected index is outside requested component")
    left = index
    right = index
    while left > 0 and mask[left - 1]:
        left -= 1
    while right + 1 < len(mask) and mask[right + 1]:
        right += 1
    return left, right


def _sign_change_intervals(points: Sequence[dict[str, Any]]) -> list[dict[str, float]]:
    intervals: list[dict[str, float]] = []
    for left, right in zip(points[:-1], points[1:]):
        left_value = float(
            left["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"]
        )
        right_value = float(
            right["continuously_tracked_branch"]["unwrapped_energy_shift_hartree"]
        )
        if left_value == 0.0 or right_value == 0.0 or left_value * right_value < 0.0:
            intervals.append(
                {
                    "relative_time_start": float(left["relative_to_analytic_time"]),
                    "relative_time_stop": float(right["relative_to_analytic_time"]),
                    "time_start": float(left["time"]),
                    "time_stop": float(right["time"]),
                }
            )
    return intervals


def summarize_formula(
    formula_result: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    points = list(formula_result["points"])
    if len(points) != int(protocol["time_grid"]["point_count"]):
        raise ValueError("direct point count differs from fixed protocol")
    relative_times = [float(p["relative_to_analytic_time"]) for p in points]
    expected_grid = _grid_from_protocol(protocol)
    if not np.allclose(relative_times, expected_grid, rtol=0.0, atol=1e-12):
        raise ValueError("direct time grid differs from fixed protocol")

    costs = [p["continuously_tracked_branch"]["cost"] for p in points]
    finite_indices = [index for index, value in enumerate(costs) if value is not None]
    if not finite_indices:
        return {
            "status": "not_scorable_no_finite_cost",
            "point_count": len(points),
        }
    selected_index = min(finite_indices, key=lambda index: float(costs[index]))
    selected = points[selected_index]
    selected_branch = selected["continuously_tracked_branch"]
    minimum_cost = float(costs[selected_index])
    threshold = (
        float(protocol["optimum_robustness"]["near_optimal_cost_factor"])
        * minimum_cost
    )
    near_mask = [value is not None and float(value) <= threshold for value in costs]
    near_left, near_right = _connected_true_component(near_mask, selected_index)
    near_start = relative_times[near_left]
    near_stop = relative_times[near_right]
    near_width = near_stop - near_start
    sign_changes = _sign_change_intervals(points)
    zero_crossing_assisted = any(
        interval["relative_time_start"] <= near_stop
        and interval["relative_time_stop"] >= near_start
        for interval in sign_changes
    )

    gates = protocol["numerical_gates"]
    maximum_unitarity = max(
        float(point["unitarity_residual_frobenius_norm"]) for point in points
    )
    maximum_schur = max(
        float(point["schur_off_diagonal_residual_frobenius_norm"])
        for point in points
    )
    maximum_branch_disagreement = max(
        abs(
            float(point["maximum_ground_overlap_branch"]["energy_shift_hartree"])
            - float(
                point["continuously_tracked_branch"][
                    "unwrapped_energy_shift_hartree"
                ]
            )
        )
        for point in points
    )
    previous_overlaps = [
        float(point["continuously_tracked_branch"]["overlap_with_previous_probability"])
        for point in points
        if point["continuously_tracked_branch"]["overlap_with_previous_probability"]
        is not None
    ]
    boundary_minimum = selected_index in (0, len(points) - 1)
    gate_results = {
        "unitarity": maximum_unitarity
        <= float(gates["maximum_unitarity_frobenius_residual"]),
        "schur": maximum_schur
        <= float(gates["maximum_schur_off_diagonal_frobenius_residual"]),
        "branch_shift_agreement": maximum_branch_disagreement
        <= float(gates["maximum_branch_shift_disagreement_hartree"]),
        "ground_overlap_at_optimum": float(
            selected_branch["ground_overlap_probability"]
        )
        >= float(gates["minimum_ground_overlap_at_selected_optimum"]),
        "interior_minimum": not boundary_minimum,
    }
    well_localized = near_width <= float(
        protocol["optimum_robustness"][
            "maximum_near_optimal_relative_time_width_for_well_localized"
        ]
    )
    scorable = all(gate_results.values())
    left_bracket = max(0, selected_index - 1)
    right_bracket = min(len(points) - 1, selected_index + 1)
    analytic_index = min(
        range(len(points)), key=lambda index: abs(relative_times[index] - 1.0)
    )
    return {
        "status": "scorable" if scorable else "not_scorable_gate_failure",
        "point_count": len(points),
        "analytic_optimal_time": float(formula_result["analytic_optimal_time"]),
        "t_grid_star": float(selected["time"]),
        "relative_t_grid_star": relative_times[selected_index],
        "minimum_direct_cost": minimum_cost,
        "direct_error_at_t_grid_star_hartree": float(
            selected_branch["direct_error_hartree"]
        ),
        "signed_shift_at_t_grid_star_hartree": float(
            selected_branch["unwrapped_energy_shift_hartree"]
        ),
        "ground_overlap_at_t_grid_star": float(
            selected_branch["ground_overlap_probability"]
        ),
        "previous_overlap_at_t_grid_star": selected_branch[
            "overlap_with_previous_probability"
        ],
        "cost_at_nearest_analytic_time": costs[analytic_index],
        "direct_to_analytic_time_cost_ratio": (
            minimum_cost / float(costs[analytic_index])
            if costs[analytic_index] is not None
            else None
        ),
        "neighbor_bracket": {
            "relative_time_start": relative_times[left_bracket],
            "relative_time_stop": relative_times[right_bracket],
            "time_start": float(points[left_bracket]["time"]),
            "time_stop": float(points[right_bracket]["time"]),
        },
        "near_optimal_component": {
            "cost_factor": float(
                protocol["optimum_robustness"]["near_optimal_cost_factor"]
            ),
            "relative_time_start": near_start,
            "relative_time_stop": near_stop,
            "relative_time_width": near_width,
            "point_count": near_right - near_left + 1,
            "well_localized": well_localized,
        },
        "signed_error_zero_crossing_intervals": sign_changes,
        "zero_crossing_assisted_near_optimum": zero_crossing_assisted,
        "numerical": {
            "maximum_unitarity_frobenius_residual": maximum_unitarity,
            "maximum_schur_off_diagonal_frobenius_residual": maximum_schur,
            "maximum_branch_shift_disagreement_hartree": (
                maximum_branch_disagreement
            ),
            "minimum_previous_overlap": min(previous_overlaps),
            "minimum_ground_overlap": min(
                float(point["continuously_tracked_branch"]["ground_overlap_probability"])
                for point in points
            ),
            "previous_overlap_warning": min(previous_overlaps)
            < float(gates["previous_overlap_warning_threshold"]),
        },
        "gate_results": gate_results,
    }


def _fit_power_law(sizes: Sequence[float], times: Sequence[float]) -> dict[str, Any]:
    x = np.log(np.asarray(sizes, dtype=float))
    y = np.log(np.asarray(times, dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    fitted = np.exp(intercept + slope * x)
    residual = y - (intercept + slope * x)
    denominator = float(np.sum(np.square(y - np.mean(y))))
    r_squared = 1.0 if denominator == 0.0 else 1.0 - float(
        np.sum(np.square(residual)) / denominator
    )
    return {
        "a": float(np.exp(intercept)),
        "b": float(slope),
        "r_squared_log_space": r_squared,
        "fitted_times": fitted.tolist(),
    }


def _loo_predictions(
    sizes: Sequence[float], times: Sequence[float], model: str
) -> dict[str, Any]:
    sizes_array = np.asarray(sizes, dtype=float)
    times_array = np.asarray(times, dtype=float)
    rows: list[dict[str, float]] = []
    for index in range(len(sizes_array)):
        mask = np.ones(len(sizes_array), dtype=bool)
        mask[index] = False
        if model == "power_law":
            fit = _fit_power_law(sizes_array[mask], times_array[mask])
            prediction = fit["a"] * sizes_array[index] ** fit["b"]
        elif model == "constant":
            prediction = float(np.exp(np.mean(np.log(times_array[mask]))))
        else:
            raise ValueError(f"unknown model: {model}")
        relative_error = abs(float(prediction / times_array[index] - 1.0))
        rows.append(
            {
                "held_out_size": float(sizes_array[index]),
                "observed_time": float(times_array[index]),
                "predicted_time": float(prediction),
                "relative_error": relative_error,
            }
        )
    errors = [row["relative_error"] for row in rows]
    return {
        "rows": rows,
        "mean_relative_error": float(np.mean(errors)),
        "maximum_relative_error": float(np.max(errors)),
    }


def scaling_summary(
    formula_key: str,
    summaries: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    primary_sizes = [int(value) for value in protocol["scaling_analysis"]["primary_sizes"]]
    secondary_sizes = [
        int(value) for value in protocol["scaling_analysis"]["secondary_sizes"]
    ]

    def rows_for(sizes: Iterable[int]) -> list[dict[str, Any]]:
        return [
            {
                "size": size,
                "summary": summaries[f"H{size}"][formula_key],
            }
            for size in sizes
        ]

    primary_rows = rows_for(primary_sizes)
    secondary_rows = rows_for(secondary_sizes)
    primary_eligible = all(
        row["summary"].get("status") == "scorable"
        and row["summary"]["near_optimal_component"]["well_localized"]
        for row in primary_rows
    )
    result: dict[str, Any] = {
        "formula_key": formula_key,
        "primary_family": protocol["scaling_analysis"]["primary_family"],
        "primary_sizes": primary_sizes,
        "primary_eligible": primary_eligible,
        "secondary_family": protocol["scaling_analysis"]["secondary_family"],
        "secondary_sizes": secondary_sizes,
        "secondary_role": "descriptive_two_point_trend_only",
    }
    if not primary_eligible:
        result["decision"] = "not_scorable_due_to_numerical_or_boundary_gate"
    else:
        primary_times = [float(row["summary"]["t_grid_star"]) for row in primary_rows]
        power_fit = _fit_power_law(primary_sizes, primary_times)
        power_loo = _loo_predictions(primary_sizes, primary_times, "power_law")
        constant_loo = _loo_predictions(primary_sizes, primary_times, "constant")
        threshold = float(
            protocol["scaling_analysis"][
                "maximum_power_law_loo_relative_error_for_small_system_support"
            ]
        )
        result.update(
            {
                "primary_observed_times": primary_times,
                "power_law_fit": power_fit,
                "power_law_leave_one_out": power_loo,
                "constant_leave_one_out": constant_loo,
            }
        )
        if power_loo["maximum_relative_error"] <= threshold:
            result["decision"] = "small_system_predictable_requires_H8_holdout"
        else:
            result["decision"] = "no_predictable_power_law_on_current_sizes"

    if all(row["summary"].get("status") == "scorable" for row in secondary_rows):
        secondary_times = [
            float(row["summary"]["t_grid_star"]) for row in secondary_rows
        ]
        result["secondary_observed_times"] = secondary_times
        result["secondary_two_point_power_law"] = _fit_power_law(
            secondary_sizes, secondary_times
        )
    else:
        result["secondary_two_point_power_law"] = None
    return result


def _report_markdown(analysis: dict[str, Any], protocol_sha256: str) -> str:
    lines = [
        "# H-chain direct optimal-time scaling result",
        "",
        f"- Status: `{analysis['status']}`",
        f"- Decision: `{analysis['decision']}`",
        f"- Protocol SHA-256: `{protocol_sha256}`",
        "- Interpretation: retrospective small-system validation; H8 remains the independent even-chain holdout.",
        "",
        "## Direct grid optima",
        "",
        "| system | family | PF | t_ana | t_grid* | t_grid*/t_ana | min cost | 1% interval (relative) | zero-crossing assisted | scorable |",
        "|---|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for system_id, formula_map in analysis["systems"].items():
        family = analysis["system_families"][system_id]
        for formula_key, row in formula_map.items():
            if "t_grid_star" not in row:
                lines.append(
                    f"| {system_id} | {family} | {formula_key} | — | — | — | — | — | — | {row['status']} |"
                )
                continue
            interval = row["near_optimal_component"]
            lines.append(
                "| "
                f"{system_id} | {family} | {formula_key} | "
                f"{row['analytic_optimal_time']:.9g} | {row['t_grid_star']:.9g} | "
                f"{row['relative_t_grid_star']:.3f} | {row['minimum_direct_cost']:.9g} | "
                f"[{interval['relative_time_start']:.3f}, {interval['relative_time_stop']:.3f}] | "
                f"{row['zero_crossing_assisted_near_optimum']} | {row['status']} |"
            )
    lines.extend(
        [
            "",
            "## Scaling decisions",
            "",
            "| PF | power exponent b | power-law LOO max error | constant LOO max error | decision |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for formula_key, row in analysis["scaling"].items():
        if "power_law_fit" not in row:
            lines.append(f"| {formula_key} | — | — | — | {row['decision']} |")
        else:
            lines.append(
                f"| {formula_key} | {row['power_law_fit']['b']:.6g} | "
                f"{row['power_law_leave_one_out']['maximum_relative_error']:.3%} | "
                f"{row['constant_leave_one_out']['maximum_relative_error']:.3%} | "
                f"{row['decision']} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- `t_grid*` is the discrete minimum in the fixed 0.20–1.70 `t_ana` domain; it is not an all-time global optimum.",
            "- Odd and even H chains use different charge/multiplicity families and were not pooled.",
            "- Even a successful H2/H4/H6 leave-one-size-out check is not a strong scaling claim without H8.",
            "- The cost is the repository continuous QPE precision-allocation proxy, not an end-to-end QPE implementation cost.",
            "",
        ]
    )
    return "\n".join(lines)


def _manifest(output: Path, files: Sequence[Path], metadata: dict[str, Any]) -> None:
    entries = [
        {
            "path": str(path.relative_to(output)),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(files)
    ]
    _write_json(output / "manifest.json", {**metadata, "files": entries})


def analyze(
    protocol: dict[str, Any], protocol_sha256: str, output: Path, project_root: Path
) -> dict[str, Any]:
    system_summaries: dict[str, dict[str, Any]] = {}
    families: dict[str, str] = {}
    raw_paths: list[Path] = []
    all_gate_pass = True
    maximums = {
        "unitarity": 0.0,
        "schur": 0.0,
        "branch_shift_disagreement_hartree": 0.0,
    }
    minimum_previous_overlap = 1.0
    minimum_ground_overlap = 1.0
    for system in protocol["systems"]["included"]:
        h_chain = int(system["h_chain"])
        system_id = str(system["id"])
        families[system_id] = str(system["family"])
        formula_summaries: dict[str, Any] = {}
        for formula in protocol["product_formulas"]:
            formula_key = str(formula["key"])
            label = str(formula["label"])
            path = output / "raw" / _job_name(h_chain, formula_key)
            raw_paths.append(path)
            payload = _load_json(path)
            if not _job_matches(
                payload,
                protocol_sha256=protocol_sha256,
                grid=_grid_from_protocol(protocol),
                h_chain=h_chain,
                formula_key=formula_key,
            ):
                raise RuntimeError(f"raw job identity mismatch: {path}")
            summary = summarize_formula(
                payload["results"][system_id]["results"][label], protocol
            )
            formula_summaries[formula_key] = summary
            all_gate_pass &= summary.get("status") == "scorable"
            if "numerical" in summary:
                numerical = summary["numerical"]
                maximums["unitarity"] = max(
                    maximums["unitarity"],
                    numerical["maximum_unitarity_frobenius_residual"],
                )
                maximums["schur"] = max(
                    maximums["schur"],
                    numerical["maximum_schur_off_diagonal_frobenius_residual"],
                )
                maximums["branch_shift_disagreement_hartree"] = max(
                    maximums["branch_shift_disagreement_hartree"],
                    numerical["maximum_branch_shift_disagreement_hartree"],
                )
                minimum_previous_overlap = min(
                    minimum_previous_overlap, numerical["minimum_previous_overlap"]
                )
                minimum_ground_overlap = min(
                    minimum_ground_overlap, numerical["minimum_ground_overlap"]
                )
        system_summaries[system_id] = formula_summaries

    scaling = {
        formula["key"]: scaling_summary(
            str(formula["key"]), system_summaries, protocol
        )
        for formula in protocol["product_formulas"]
    }
    decisions = [row["decision"] for row in scaling.values()]
    if not all_gate_pass:
        status = "failed_numerical_or_boundary_validation"
        decision = "not_scorable_due_to_numerical_or_boundary_gate"
    elif all(
        item == "small_system_predictable_requires_H8_holdout"
        for item in decisions
    ):
        status = "complete_small_system_analysis"
        decision = "small_system_predictable_requires_H8_holdout"
    else:
        status = "complete_small_system_analysis"
        decision = "no_common_predictable_scaling_on_current_sizes"

    analysis = {
        "schema_version": "hchain_direct_optimal_time_scaling_analysis_v1",
        "status": status,
        "decision": decision,
        "protocol_sha256": protocol_sha256,
        "created_at_utc": _utc_now(),
        "systems": system_summaries,
        "system_families": families,
        "scaling": scaling,
        "audit_summary": {
            "system_count": len(system_summaries),
            "formula_count": len(protocol["product_formulas"]),
            "direct_point_count": sum(
                row["point_count"]
                for formula_map in system_summaries.values()
                for row in formula_map.values()
            ),
            "all_formula_numerical_and_boundary_gates_pass": all_gate_pass,
            "maximum_unitarity_frobenius_residual": maximums["unitarity"],
            "maximum_schur_off_diagonal_frobenius_residual": maximums["schur"],
            "maximum_branch_shift_disagreement_hartree": maximums[
                "branch_shift_disagreement_hartree"
            ],
            "minimum_previous_overlap": minimum_previous_overlap,
            "minimum_ground_overlap": minimum_ground_overlap,
            "prior_direct_results_reused": False,
            "H8_holdout_executed": False,
        },
    }
    analysis_path = output / "analysis.json"
    _write_json(analysis_path, analysis)
    report_path = output / "report.md"
    report_path.write_text(
        _report_markdown(analysis, protocol_sha256), encoding="utf-8"
    )
    audit = {
        "schema_version": "hchain_direct_optimal_time_scaling_audit_v1",
        "status": status,
        "protocol_sha256": protocol_sha256,
        "git_head": _git_value(project_root, "rev-parse", "HEAD"),
        "git_branch": _git_value(project_root, "branch", "--show-current"),
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "environment": {
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        },
        **analysis["audit_summary"],
    }
    audit_path = output / "audit.json"
    _write_json(audit_path, audit)
    protocol_copy = output / "protocol.json"
    public_files = [protocol_copy, *raw_paths, analysis_path, report_path, audit_path]
    _manifest(
        output,
        public_files,
        {
            "schema_version": "hchain_direct_optimal_time_scaling_manifest_v1",
            "status": status,
            "protocol_sha256": protocol_sha256,
            "created_at_utc": _utc_now(),
        },
    )
    if status == "complete_small_system_analysis":
        (output / "COMPLETE").write_text(status + "\n", encoding="utf-8")
    return analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path(
            "review_response/hchain_direct_optimal_time_scaling_protocol.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/hchain_direct_optimal_time_scaling_20260927"
        ),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    protocol_path = (
        args.protocol
        if args.protocol.is_absolute()
        else project_root / args.protocol
    ).resolve()
    output = (
        args.output if args.output.is_absolute() else project_root / args.output
    ).resolve()
    protocol = _load_json(protocol_path)
    protocol_sha256 = _sha256(protocol_path)
    _grid_from_protocol(protocol)
    if output.exists() and not (args.resume or args.analyze_only):
        raise RuntimeError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_copy = output / "protocol.json"
    if protocol_copy.exists():
        if _sha256(protocol_copy) != protocol_sha256:
            raise RuntimeError("output protocol copy differs from fixed protocol")
    else:
        shutil.copyfile(protocol_path, protocol_copy)
    started = time.perf_counter()
    if not args.analyze_only:
        _run_jobs(protocol, protocol_sha256, output, resume=args.resume)
    analysis = analyze(protocol, protocol_sha256, output, project_root)
    print(
        json.dumps(
            {
                "status": analysis["status"],
                "decision": analysis["decision"],
                "protocol_sha256": protocol_sha256,
                "elapsed_seconds": time.perf_counter() - started,
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
