"""Search m=2 and m=3 fourth-order PFs for finite-time predictability.

The search deliberately starts with the two cheapest non-trivial coefficient
families.  It reuses the exact fourth-order projection already implemented in
``trotterlib.optimal_trotter`` and evaluates candidates with the direct
ground-connected PF eigenphase.  H2 is used for broad screening; only a small
Pareto-oriented shortlist is carried to H4 and H5.  H6 and H7 are not touched
by this script, so they remain size-validation systems for a later stage.

This is an exploratory coefficient search, not a final continuous optimum.
All direct-cost minima are selected from the declared coarse time grid.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.stats import qmc

from explore_m5_predictability_path import (
    _custom_short_time_fit,
    _direct_custom_points,
)
from sweep_direct_scaling_h6_h7 import _write_json
from trotterlib.config import BETA, DECOMPO_NUM, TARGET_ERROR
from trotterlib.cost_validation import analytic_minimum_cost, analytic_optimal_time
from trotterlib.optimal_trotter import (
    fourth_order_moment_residual_float64,
    solve_nonprocessed_4th_moment_coefficients,
)
from trotterlib.pf_decomposition import symmetric_s2_sequence
from trotterlib.product_formula import new_4th_m2_list, new_4th_m3_list
from validate_asymptotic_cost_small_systems import _prepare_system
from validate_pf_cost_predictability import (
    DEFAULT_FIT_TIMES,
    DEFAULT_RELATIVE_TIMES,
    _analysis_pass,
    sampled_predictability_metrics,
)


DEFAULT_OUTPUT_DIR = Path("artifacts/pf_cost_predictability_m2_m3_search")
ZERO_STAGE_TOLERANCE = 1e-11


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def actual_s2_stage_count(weights: Sequence[float]) -> int:
    """Count nonzero S2 stages in the expanded symmetric composition."""

    compact = np.asarray(weights, dtype=float)
    if compact.ndim != 1 or compact.size < 2:
        raise ValueError("weights must contain w0 and at least one tail value")
    central = int(abs(float(compact[0])) > ZERO_STAGE_TOLERANCE)
    paired = 2 * int(np.count_nonzero(np.abs(compact[1:]) > ZERO_STAGE_TOLERANCE))
    return central + paired


def pauli_rotation_count(system_name: str, weights: Sequence[float]) -> int:
    """Return the affine merged-circuit rotation count for an S2 stage count."""

    row = DECOMPO_NUM[str(system_name)]
    one_stage = int(row["2nd"])
    three_stages = int(row["4th"])
    increment_numerator = three_stages - one_stage
    if increment_numerator % 2:
        raise ValueError(f"non-integral per-stage count for {system_name}")
    per_extra_stage = increment_numerator // 2
    stages = actual_s2_stage_count(weights)
    return int(one_stage + (stages - 1) * per_extra_stage)


def _candidate(
    name: str,
    source: str,
    tail: Sequence[float],
) -> dict[str, Any] | None:
    """Pack and conservatively filter one projected coefficient vector."""

    tail_array = np.asarray(tail, dtype=float)
    w0 = float(1.0 - 2.0 * np.sum(tail_array))
    weights = np.concatenate(([w0], tail_array))
    residual = float(fourth_order_moment_residual_float64(tail_array)[0])
    coefficient_l1 = float(np.sum(np.abs(weights)))
    coefficient_linf = float(np.max(np.abs(weights)))
    if not np.all(np.isfinite(weights)) or abs(residual) > 1e-10:
        return None
    # Huge positive/negative substeps are both expensive numerically and far
    # outside the coefficient region occupied by the useful reference PFs.
    if coefficient_linf > 1.5 or coefficient_l1 > 4.0:
        return None
    return {
        "name": str(name),
        "source": str(source),
        "m": int(tail_array.size),
        "weights": weights.tolist(),
        "fourth_order_moment_residual": residual,
        "coefficient_l1": coefficient_l1,
        "coefficient_l2": float(np.linalg.norm(weights)),
        "coefficient_linf": coefficient_linf,
        "actual_s2_stage_count": actual_s2_stage_count(weights),
        "systems": {},
    }


def _deduplicate(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[float, ...], dict[str, Any]] = {}
    for candidate in candidates:
        key = tuple(round(float(value), 10) for value in candidate["weights"])
        unique.setdefault(key, candidate)
    return list(unique.values())


def projected_reference_candidate(m: int) -> dict[str, Any]:
    """Return new_2 or new_3 after correcting printed-coefficient truncation."""

    if int(m) == 2:
        label = "new_2_projected"
        weights = new_4th_m2_list()
    elif int(m) == 3:
        label = "new_3_projected"
        weights = new_4th_m3_list()
    else:
        raise ValueError("reference is available only for m=2 or m=3")
    solved = solve_nonprocessed_4th_moment_coefficients(
        kernel_m=int(m), initial=weights[1:], max_nfev=5000
    )
    candidate = _candidate(label, "projected_existing_reference", solved.w_tail)
    if candidate is None:
        raise RuntimeError(f"failed to project {label}")
    return candidate


def generate_m2_grid_candidates(
    *,
    w1_min: float = -0.40,
    w1_max: float = 0.80,
    num_w1: int = 81,
) -> list[dict[str, Any]]:
    """Enumerate all real m=2 branches while scanning the one free coordinate."""

    candidates: list[dict[str, Any]] = [projected_reference_candidate(2)]
    for grid_index, w1 in enumerate(np.linspace(w1_min, w1_max, int(num_w1))):
        # With a=1-2*w1, the fourth-order equation as a polynomial in w2 is
        # -6*w2^3 + 12*a*w2^2 - 6*a^2*w2 + a^3 + 2*w1^3 = 0.
        a = 1.0 - 2.0 * float(w1)
        roots = np.roots([-6.0, 12.0 * a, -6.0 * a**2, a**3 + 2.0 * w1**3])
        for branch_index, root in enumerate(roots):
            if abs(float(root.imag)) > 1e-9:
                continue
            initial = [float(w1), float(root.real)]
            solved = solve_nonprocessed_4th_moment_coefficients(
                kernel_m=2, initial=initial, max_nfev=2000
            )
            packed = _candidate(
                f"m2_grid_{grid_index:03d}_branch_{branch_index}",
                "m2_complete_real_branch_grid",
                solved.w_tail,
            )
            if packed is not None:
                candidates.append(packed)
    return _deduplicate(candidates)


def generate_m3_sobol_candidates(
    *,
    num_samples: int = 128,
    lower: float = -0.55,
    upper: float = 0.65,
    seed: int = 20260905,
) -> list[dict[str, Any]]:
    """Generate a deterministic low-discrepancy m=3 candidate set."""

    if num_samples < 1:
        raise ValueError("num_samples must be positive")
    reference = projected_reference_candidate(3)
    candidates: list[dict[str, Any]] = [reference]
    exponent = int(math.ceil(math.log2(int(num_samples))))
    sampler = qmc.Sobol(d=3, scramble=True, seed=int(seed))
    unit_points = sampler.random_base2(exponent)[: int(num_samples)]
    seeds = qmc.scale(unit_points, [lower] * 3, [upper] * 3)

    # Add local perturbations around the known analyzable new_3 reference so
    # the small global sample cannot accidentally miss its neighbourhood.
    reference_tail = np.asarray(reference["weights"][1:], dtype=float)
    local_offsets = np.asarray(
        [
            [0.04, 0.00, 0.00],
            [-0.04, 0.00, 0.00],
            [0.00, 0.04, 0.00],
            [0.00, -0.04, 0.00],
            [0.00, 0.00, 0.04],
            [0.00, 0.00, -0.04],
            [0.06, -0.03, 0.02],
            [-0.06, 0.03, -0.02],
        ]
    )
    seeds = np.vstack([seeds, reference_tail + local_offsets])

    for index, initial in enumerate(seeds):
        solved = solve_nonprocessed_4th_moment_coefficients(
            kernel_m=3, initial=initial, max_nfev=3000
        )
        packed = _candidate(
            f"m3_sobol_{index:04d}",
            "m3_sobol_then_fourth_order_projection",
            solved.w_tail,
        )
        if packed is not None:
            candidates.append(packed)
    return _deduplicate(candidates)


def evaluate_candidate_system(
    candidate: dict[str, Any],
    *,
    system_name: str,
    system: dict[str, Any],
    fit_times: Sequence[float],
    relative_times: Sequence[float],
) -> dict[str, Any]:
    """Evaluate one candidate on one directly diagonalizable H chain."""

    started = time.perf_counter()
    sequence = symmetric_s2_sequence(candidate["weights"])
    fit = _custom_short_time_fit(system, sequence, fit_times)
    record: dict[str, Any] = {
        "short_time_fit": fit,
        "predictability": None,
        "analysis_predictability_pass": {"passed": False},
    }
    selected = fit["selected_window"]
    if selected is None:
        record["elapsed_seconds"] = float(time.perf_counter() - started)
        return record

    alpha = float(selected["fixed_order_alpha"])
    n_exp = pauli_rotation_count(system_name, candidate["weights"])
    analytic_time = analytic_optimal_time(alpha, 4, TARGET_ERROR)
    model_cost = analytic_minimum_cost(BETA, n_exp, alpha, 4, TARGET_ERROR)
    points = _direct_custom_points(
        system,
        sequence,
        relative_times,
        alpha=alpha,
        analytic_time=analytic_time,
        n_exp=n_exp,
        epsilon_e=TARGET_ERROR,
    )
    metrics = sampled_predictability_metrics(
        points,
        analytic_model_cost=model_cost,
        formal_order=4,
        scale_tolerance=0.1,
        scale_interval=(0.3, 1.1),
        optimization_interval=(0.2, 1.4),
    )
    record.update(
        {
            "pauli_rotations_per_step": n_exp,
            "analytic_optimal_time": analytic_time,
            "analytic_model_cost": model_cost,
            "direct_points": points,
            "predictability": metrics,
            "analysis_predictability_pass": _analysis_pass(fit, metrics),
            "elapsed_seconds": float(time.perf_counter() - started),
        }
    )
    return record


def _objective_pair(candidate: dict[str, Any], system_name: str) -> tuple[float, float]:
    record = candidate["systems"][system_name]
    metrics = record.get("predictability")
    if metrics is None or metrics["sampled_direct_minimum"] is None:
        return math.inf, math.inf
    return (
        float(metrics["sampled_direct_minimum"]["cost"]),
        float(metrics["maximum_scale_relative_deviation"]),
    )


def pareto_front(
    candidates: Sequence[dict[str, Any]], system_name: str
) -> list[dict[str, Any]]:
    """Return the non-dominated cost-versus-scaling-deviation candidates."""

    eligible = [
        candidate
        for candidate in candidates
        if candidate["systems"].get(system_name, {})
        .get("analysis_predictability_pass", {})
        .get("passed", False)
    ]
    front: list[dict[str, Any]] = []
    for candidate in eligible:
        cost, deviation = _objective_pair(candidate, system_name)
        dominated = False
        for other in eligible:
            if other is candidate:
                continue
            other_cost, other_deviation = _objective_pair(other, system_name)
            if (
                other_cost <= cost
                and other_deviation <= deviation
                and (other_cost < cost or other_deviation < deviation)
            ):
                dominated = True
                break
        if not dominated:
            front.append(candidate)
    return sorted(front, key=lambda item: _objective_pair(item, system_name))


def select_shortlist(
    candidates: Sequence[dict[str, Any]],
    *,
    system_name: str = "H2",
    maximum: int = 10,
) -> list[dict[str, Any]]:
    """Keep reference, Pareto extremes, and the lowest-cost passing points."""

    eligible = [
        candidate
        for candidate in candidates
        if candidate["systems"].get(system_name, {})
        .get("analysis_predictability_pass", {})
        .get("passed", False)
    ]
    front = pareto_front(eligible, system_name)
    selected: list[dict[str, Any]] = []

    def add(candidate: dict[str, Any]) -> None:
        if candidate not in selected and len(selected) < int(maximum):
            selected.append(candidate)

    for candidate in eligible:
        if candidate["source"] == "projected_existing_reference":
            add(candidate)
    if front:
        # Evenly retain the full range of the Pareto front rather than only
        # the cheapest end.
        indices = np.unique(
            np.linspace(0, len(front) - 1, min(len(front), maximum), dtype=int)
        )
        for index in indices:
            add(front[int(index)])
    for candidate in sorted(eligible, key=lambda item: _objective_pair(item, system_name)):
        add(candidate)
    return selected


def aggregate_candidate(
    candidate: dict[str, Any],
    *,
    baseline_minima: dict[str, float],
) -> dict[str, Any]:
    """Summarize a candidate across every system actually evaluated."""

    t_passes: list[float] = []
    scale_deviations: list[float] = []
    cost_prediction_errors: list[float] = []
    cost_ratios: list[float] = []
    passed = 0
    for system_name, record in candidate["systems"].items():
        metrics = record.get("predictability")
        if metrics is None or metrics["sampled_direct_minimum"] is None:
            continue
        bracket = metrics["ten_percent_validity"]
        t_pass = bracket["t_pass_over_t_ana"]
        if t_pass is not None:
            t_passes.append(float(t_pass))
        scale_deviations.append(float(metrics["maximum_scale_relative_deviation"]))
        minimum = metrics["sampled_direct_minimum"]
        cost_prediction_errors.append(float(minimum["cost_prediction_relative_error"]))
        baseline = baseline_minima.get(system_name)
        if baseline is not None:
            cost_ratios.append(float(minimum["cost"]) / float(baseline))
        passed += int(record["analysis_predictability_pass"]["passed"])
    return {
        "num_systems_evaluated": len(candidate["systems"]),
        "num_systems_with_metrics": len(scale_deviations),
        "num_systems_passed": passed,
        "all_evaluated_systems_passed": bool(
            candidate["systems"] and passed == len(candidate["systems"])
        ),
        "worst_t_pass_over_t_ana": min(t_passes) if t_passes else None,
        "maximum_scale_relative_deviation": (
            max(scale_deviations) if scale_deviations else None
        ),
        "maximum_cost_prediction_error": (
            max(cost_prediction_errors) if cost_prediction_errors else None
        ),
        "median_direct_minimum_cost_over_m5": (
            float(np.median(cost_ratios)) if cost_ratios else None
        ),
        "maximum_direct_minimum_cost_over_m5": (
            max(cost_ratios) if cost_ratios else None
        ),
    }


def _reference_m5_minima() -> dict[str, float]:
    """Read the already completed common-grid m5 baseline when available."""

    path = Path("artifacts/pf_cost_predictability_baseline/predictability_results.json")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    minima: dict[str, float] = {}
    for system_name, system in data.get("systems", {}).items():
        record = system.get("formulas", {}).get("4th(m5_best)")
        if not record:
            continue
        minimum = record.get("predictability", {}).get("sampled_direct_minimum")
        if minimum and minimum.get("cost") is not None:
            minima[str(system_name)] = float(minimum["cost"])
    return minima


def _write_summary_csv(path: Path, candidates: Sequence[dict[str, Any]]) -> None:
    fields = [
        "name",
        "source",
        "m",
        "actual_s2_stage_count",
        "coefficient_l1",
        "coefficient_linf",
        "num_systems_evaluated",
        "num_systems_passed",
        "all_evaluated_systems_passed",
        "worst_t_pass_over_t_ana",
        "maximum_scale_relative_deviation",
        "maximum_cost_prediction_error",
        "median_direct_minimum_cost_over_m5",
        "weights",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            summary = candidate.get("summary", {})
            row = {field: candidate.get(field, summary.get(field)) for field in fields}
            row["weights"] = json.dumps(candidate["weights"])
            writer.writerow(row)


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# m=2,3 fourth-order PF predictability search",
        "",
        "H2 was used for broad screening.  Only the declared shortlist was "
        "evaluated on H4 and H5; H6/H7 were not used.",
        "",
        "| Candidate | m | stages | systems passed | worst t_pass/t_ana | "
        "max scale deviation | max cost prediction error | median C*/m5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    completed = [
        candidate
        for candidate in payload["candidates"]
        if len(candidate["systems"]) > 1
    ]
    completed.sort(
        key=lambda item: (
            not item["summary"]["all_evaluated_systems_passed"],
            math.inf
            if item["summary"]["median_direct_minimum_cost_over_m5"] is None
            else item["summary"]["median_direct_minimum_cost_over_m5"],
        )
    )
    for candidate in completed:
        summary = candidate["summary"]
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate["name"],
                    str(candidate["m"]),
                    str(candidate["actual_s2_stage_count"]),
                    f"{summary['num_systems_passed']}/{summary['num_systems_evaluated']}",
                    "—"
                    if summary["worst_t_pass_over_t_ana"] is None
                    else f"{summary['worst_t_pass_over_t_ana']:.2f}",
                    "—"
                    if summary["maximum_scale_relative_deviation"] is None
                    else f"{summary['maximum_scale_relative_deviation']:.3f}",
                    "—"
                    if summary["maximum_cost_prediction_error"] is None
                    else f"{summary['maximum_cost_prediction_error']:.3f}",
                    "—"
                    if summary["median_direct_minimum_cost_over_m5"] is None
                    else f"{summary['median_direct_minimum_cost_over_m5']:.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Search accounting",
            "",
            f"- m=2 generated: {payload['accounting']['m2_generated']}",
            f"- m=3 generated: {payload['accounting']['m3_generated']}",
            f"- m=2 H2 passes: {payload['accounting']['m2_h2_passed']}",
            f"- m=3 H2 passes: {payload['accounting']['m3_h2_passed']}",
            f"- m=2 shortlist: {payload['accounting']['m2_shortlisted']}",
            f"- m=3 shortlist: {payload['accounting']['m3_shortlisted']}",
            "",
            "The reported minima are coarse-grid minima.  No fine search around "
            "the optimum was performed at this stage.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "search_results.json"

    candidates_by_m = {
        2: generate_m2_grid_candidates(num_w1=int(args.m2_grid_points)),
        3: generate_m3_sobol_candidates(
            num_samples=int(args.m3_sobol_samples), seed=int(args.seed)
        ),
    }
    all_candidates = candidates_by_m[2] + candidates_by_m[3]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "purpose": (
            "Cheap m=2 implementation check followed by an m=3 finite-time "
            "cost-predictability search"
        ),
        "training_systems": ["H2", "H4", "H5"],
        "reserved_size_validation_systems": ["H6", "H7"],
        "fit_times": list(DEFAULT_FIT_TIMES),
        "relative_times": list(DEFAULT_RELATIVE_TIMES),
        "args": vars(args),
        "accounting": {
            "m2_generated": len(candidates_by_m[2]),
            "m3_generated": len(candidates_by_m[3]),
        },
        "candidates": all_candidates,
    }
    _write_json(raw_path, _jsonable(payload))

    systems = {name: _prepare_system(int(name[1:])) for name in ("H2", "H4", "H5")}
    for index, candidate in enumerate(all_candidates, start=1):
        print(
            f"H2 {index}/{len(all_candidates)} {candidate['name']}", flush=True
        )
        candidate["systems"]["H2"] = evaluate_candidate_system(
            candidate,
            system_name="H2",
            system=systems["H2"],
            fit_times=DEFAULT_FIT_TIMES,
            relative_times=DEFAULT_RELATIVE_TIMES,
        )
        if index % 10 == 0:
            _write_json(raw_path, _jsonable(payload))

    shortlists = {
        m: select_shortlist(
            candidates_by_m[m], system_name="H2", maximum=int(args.shortlist_per_m)
        )
        for m in (2, 3)
    }
    shortlist_ids = {
        candidate["name"]
        for candidates in shortlists.values()
        for candidate in candidates
    }
    for candidate in all_candidates:
        candidate["shortlisted_after_h2"] = candidate["name"] in shortlist_ids

    for system_name in ("H4", "H5"):
        shortlisted = shortlists[2] + shortlists[3]
        for index, candidate in enumerate(shortlisted, start=1):
            print(
                f"{system_name} {index}/{len(shortlisted)} {candidate['name']}",
                flush=True,
            )
            candidate["systems"][system_name] = evaluate_candidate_system(
                candidate,
                system_name=system_name,
                system=systems[system_name],
                fit_times=DEFAULT_FIT_TIMES,
                relative_times=DEFAULT_RELATIVE_TIMES,
            )
            _write_json(raw_path, _jsonable(payload))

    baselines = _reference_m5_minima()
    for candidate in all_candidates:
        candidate["summary"] = aggregate_candidate(
            candidate, baseline_minima=baselines
        )
    payload["accounting"].update(
        {
            "m2_h2_passed": sum(
                item["systems"]["H2"]["analysis_predictability_pass"]["passed"]
                for item in candidates_by_m[2]
            ),
            "m3_h2_passed": sum(
                item["systems"]["H2"]["analysis_predictability_pass"]["passed"]
                for item in candidates_by_m[3]
            ),
            "m2_shortlisted": len(shortlists[2]),
            "m3_shortlisted": len(shortlists[3]),
        }
    )
    payload["status"] = "complete"
    _write_json(raw_path, _jsonable(payload))
    _write_summary_csv(output_dir / "search_summary.csv", all_candidates)
    _write_report(output_dir / "report.md", payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-grid-points", type=int, default=81)
    parser.add_argument("--m3-sobol-samples", type=int, default=128)
    parser.add_argument("--shortlist-per-m", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
