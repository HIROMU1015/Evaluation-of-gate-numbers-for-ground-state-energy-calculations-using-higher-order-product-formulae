#!/usr/bin/env python3
"""Audit and extend the first-study cost decomposition using saved data only."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PROTOCOL = Path(
    "review_response/pf_first_study_completion_analysis_protocol.json"
)
DEFAULT_OUTPUT = Path(
    "artifacts/pf_first_study_completion_analysis_20260926_940ee7f"
)


class CompletionAnalysisError(RuntimeError):
    """Raised when a fixed source or analysis gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise CompletionAnalysisError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, Any], field: str, context: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise CompletionAnalysisError(f"{context}: invalid or missing {field}") from exc
    if not math.isfinite(value):
        raise CompletionAnalysisError(f"{context}: non-finite {field}")
    return value


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise CompletionAnalysisError(f"invalid Boolean value: {value!r}")


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise CompletionAnalysisError("cannot average an empty sequence")
    return sum(values) / len(values)


def _assignment_float(path: Path, name: str) -> float:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value_node = node.value
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                value = ast.literal_eval(value_node)
                if not isinstance(value, (int, float)):
                    break
                return float(value)
    raise CompletionAnalysisError(f"could not find numeric assignment {name} in {path}")


def _validate_sources(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Path]]:
    checks: dict[str, bool] = {}
    paths: dict[str, Path] = {}
    source_manifest: dict[str, Any] = {"artifacts": {}, "implementation": {}}

    required_files = {
        "practical": ("manifest.json", "protocol.json", "predictions.json", "COMPLETE"),
        "s0": ("manifest.json", "protocol.json", "scoring.csv", "COMPLETE"),
        "s4": (
            "manifest.json",
            "protocol.json",
            "predictions.json",
            "strategy_scoring.csv",
            "decision.json",
            "COMPLETE",
        ),
        "regret": (
            "manifest.json",
            "protocol.json",
            "regret_decomposition.csv",
            "COMPLETE",
        ),
    }
    hash_fields = {
        "practical": {
            "manifest.json": "manifest_sha256",
            "protocol.json": "protocol_sha256",
            "predictions.json": "predictions_sha256",
        },
        "s0": {
            "manifest.json": "manifest_sha256",
            "protocol.json": "protocol_sha256",
            "scoring.csv": "scoring_sha256",
        },
        "s4": {
            "manifest.json": "manifest_sha256",
            "protocol.json": "protocol_sha256",
            "predictions.json": "predictions_sha256",
            "strategy_scoring.csv": "strategy_scoring_sha256",
            "decision.json": "decision_sha256",
        },
        "regret": {
            "manifest.json": "manifest_sha256",
            "protocol.json": "protocol_sha256",
            "regret_decomposition.csv": "regret_decomposition_sha256",
        },
    }
    for key, names in required_files.items():
        spec = protocol["sources"][key]
        root = project_root / spec["artifact"]
        paths[key] = root
        source_manifest["artifacts"][key] = {
            "artifact": spec["artifact"],
            "result_commit": spec["result_commit"],
            "files": {},
        }
        for name in names:
            path = root / name
            check_key = f"{key}_{name}_exists"
            checks[check_key] = path.is_file()
            if not path.is_file():
                continue
            if name != "COMPLETE":
                actual = sha256_file(path)
                source_manifest["artifacts"][key]["files"][name] = actual
                expected_field = hash_fields[key][name]
                checks[f"{key}_{name}_sha256"] = actual == spec[expected_field]

    for relative, expected in protocol["sources"]["implementation"].items():
        path = project_root / relative
        paths[f"implementation:{relative}"] = path
        checks[f"implementation_{relative}_exists"] = path.is_file()
        if path.is_file():
            actual = sha256_file(path)
            source_manifest["implementation"][relative] = actual
            checks[f"implementation_{relative}_sha256"] = actual == expected

    source_manifest["checks"] = checks
    if not all(checks.values()):
        failed = sorted(key for key, passed in checks.items() if not passed)
        raise CompletionAnalysisError(f"source identity gate failed: {failed}")
    return source_manifest, paths


def _cost_definition_audit(
    project_root: Path,
    protocol: dict[str, Any],
    paths: dict[str, Path],
    practical_predictions: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fixed = protocol["fixed_values"]
    gates = protocol["numerical_gates"]
    rel_tol = float(gates["relative_tolerance"])
    abs_tol = float(gates["absolute_tolerance"])
    epsilon = float(fixed["target_error_hartree"])
    gamma = float(fixed["budget_multiplier"])
    practical_beta_expected = float(fixed["practical_cost_beta"])
    s4_beta_expected = float(fixed["s4_saved_scoring_beta"])

    config_path = project_root / "src/trotterlib/config.py"
    practical_runner_path = project_root / "review_response/run_practical_calibration_minimal.py"
    s4_runner_path = project_root / "review_response/run_pf_first_study_s4_state_convergence.py"
    practical_beta = _assignment_float(config_path, "BETA")
    practical_runner = practical_runner_path.read_text(encoding="utf-8")
    s4_runner = s4_runner_path.read_text(encoding="utf-8")
    s4_protocol = _load_json(paths["s4"] / "protocol.json")
    s4_beta = float(s4_protocol["resource_accounting"]["qpe_beta"])
    s4_gamma = float(s4_protocol["resource_accounting"]["budget_multiplier"])

    semantic_checks = {
        "config_beta_is_expected": math.isclose(
            practical_beta, practical_beta_expected, rel_tol=0.0, abs_tol=abs_tol
        ),
        "practical_cost_uses_config_beta": (
            "diagnosis.BETA * int(rotations)" in practical_runner
        ),
        "s4_protocol_beta_is_expected": math.isclose(
            s4_beta, s4_beta_expected, rel_tol=0.0, abs_tol=abs_tol
        ),
        "s4_protocol_gamma_is_expected": math.isclose(
            s4_gamma, gamma, rel_tol=0.0, abs_tol=abs_tol
        ),
        "s4_phase_error_uses_protocol_beta": (
            'beta = float(protocol["resource_accounting"]["qpe_beta"])' in s4_runner
            and "phase_error = beta * rotations / (selected_time * budget)" in s4_runner
        ),
        "beta_values_differ": not math.isclose(
            practical_beta, s4_beta, rel_tol=0.0, abs_tol=abs_tol
        ),
    }
    if not all(semantic_checks.values()):
        raise CompletionAnalysisError(f"cost-definition semantic gate failed: {semantic_checks}")

    rotations: dict[tuple[str, str], int] = {}
    for condition in practical_predictions["conditions"]:
        for pf_row in condition["pf_predictions"]:
            rotations[(condition["condition"], pf_row["formula"])] = int(
                pf_row["rotations"]
            )

    source_rows = _read_csv(paths["s4"] / "strategy_scoring.csv")
    output_rows: list[dict[str, Any]] = []
    for source in source_rows:
        condition = source["condition"]
        strategy = source["strategy"]
        formula = source["selected_formula"]
        context = f"{condition}/{strategy}"
        time_value = _float(source, "selected_time", context)
        predicted_cost = _float(source, "predicted_cost", context)
        predicted_error = _float(source, "predicted_error_hartree", context)
        direct_error = _float(source, "exact_time_direct_error_hartree", context)
        direct_cost = _float(source, "exact_time_direct_cost", context)
        stored_budget = _float(source, "frozen_budget_gamma_1_01", context)
        stored_phase = _float(
            source, "phase_estimation_error_gamma_1_01_hartree", context
        )
        stored_margin = _float(source, "energy_margin_gamma_1_01_hartree", context)
        rotation_count = rotations.get((condition, formula))
        if rotation_count is None:
            raise CompletionAnalysisError(f"{context}: no rotation count")

        budget = gamma * predicted_cost
        protocol_phase = s4_beta * rotation_count / (time_value * budget)
        consistent_phase = practical_beta * rotation_count / (time_value * budget)
        identity_phase = (epsilon - predicted_error) / gamma
        consistent_margin = epsilon - direct_error - consistent_phase
        consistent_success = consistent_margin >= 0.0
        recomputed_direct_cost = practical_beta * rotation_count / (
            time_value * (epsilon - direct_error)
        )
        output_rows.append(
            {
                "condition": condition,
                "evaluation_group": source["evaluation_group"],
                "strategy": strategy,
                "selected_formula": formula,
                "selected_time": time_value,
                "rotations": rotation_count,
                "predicted_error_hartree": predicted_error,
                "direct_error_hartree": direct_error,
                "predicted_cost": predicted_cost,
                "stored_budget_gamma_1_01": stored_budget,
                "recomputed_budget_gamma_1_01": budget,
                "stored_s4_beta": s4_beta,
                "practical_cost_beta": practical_beta,
                "stored_phase_error_hartree": stored_phase,
                "protocol_beta_phase_error_hartree": protocol_phase,
                "consistent_phase_error_hartree": consistent_phase,
                "cost_identity_phase_error_hartree": identity_phase,
                "stored_energy_margin_hartree": stored_margin,
                "consistent_energy_margin_hartree": consistent_margin,
                "stored_success": _bool(source["success_gamma_1_01"]),
                "consistent_success": consistent_success,
                "stored_phase_matches_protocol_beta": math.isclose(
                    stored_phase, protocol_phase, rel_tol=rel_tol, abs_tol=abs_tol
                ),
                "consistent_phase_matches_cost_identity": math.isclose(
                    consistent_phase, identity_phase, rel_tol=rel_tol, abs_tol=abs_tol
                ),
                "direct_cost_matches_practical_beta": math.isclose(
                    direct_cost,
                    recomputed_direct_cost,
                    rel_tol=rel_tol,
                    abs_tol=abs_tol,
                ),
                "success_changed": (
                    _bool(source["success_gamma_1_01"]) != consistent_success
                ),
                "joint_formula_time_selection_regret": _float(
                    source, "joint_formula_time_selection_regret", context
                ),
            }
        )

    expected_rows = int(gates["expected_s4_rows"])
    if len(output_rows) != expected_rows:
        raise CompletionAnalysisError(
            f"S4 row count mismatch: {len(output_rows)} != {expected_rows}"
        )
    row_checks = {
        "budgets_reproduce": all(
            math.isclose(
                row["stored_budget_gamma_1_01"],
                row["recomputed_budget_gamma_1_01"],
                rel_tol=rel_tol,
                abs_tol=abs_tol,
            )
            for row in output_rows
        ),
        "stored_phase_reproduces_protocol_beta": all(
            row["stored_phase_matches_protocol_beta"] for row in output_rows
        ),
        "consistent_phase_reproduces_cost_identity": all(
            row["consistent_phase_matches_cost_identity"] for row in output_rows
        ),
        "direct_cost_reproduces_practical_beta": all(
            row["direct_cost_matches_practical_beta"] for row in output_rows
        ),
    }
    if not all(row_checks.values()):
        raise CompletionAnalysisError(f"S4 row audit failed: {row_checks}")

    strategy_summary: dict[str, dict[str, Any]] = {}
    for strategy in sorted(set(row["strategy"] for row in output_rows)):
        selected = [row for row in output_rows if row["strategy"] == strategy]
        strategy_summary[strategy] = {
            "condition_count": len(selected),
            "stored_safe_count": sum(row["stored_success"] for row in selected),
            "consistent_safe_count": sum(
                row["consistent_success"] for row in selected
            ),
            "minimum_consistent_energy_margin_hartree": min(
                row["consistent_energy_margin_hartree"] for row in selected
            ),
            "mean_original_grid_regret": _mean(
                row["joint_formula_time_selection_regret"] for row in selected
            ),
            "maximum_original_grid_regret": max(
                row["joint_formula_time_selection_regret"] for row in selected
            ),
        }
    decision_source = _load_json(paths["s4"] / "decision.json")
    targeted = strategy_summary["state_targeted_fallback"]
    baseline = strategy_summary["practical_baseline"]
    audit = {
        "status": "definition_mismatch_confirmed_outcome_robust",
        "practical_cost_beta": practical_beta,
        "s4_saved_scoring_beta": s4_beta,
        "beta_ratio": practical_beta / s4_beta,
        "semantic_checks": semantic_checks,
        "row_checks": row_checks,
        "row_count": len(output_rows),
        "strategy_summary": strategy_summary,
        "stored_safe_row_count": sum(row["stored_success"] for row in output_rows),
        "consistent_safe_row_count": sum(
            row["consistent_success"] for row in output_rows
        ),
        "success_changed_row_count": sum(row["success_changed"] for row in output_rows),
        "minimum_consistent_energy_margin_hartree": min(
            row["consistent_energy_margin_hartree"] for row in output_rows
        ),
        "minimum_safety_remains_passed": (
            targeted["consistent_safe_count"] == targeted["condition_count"] == 6
        ),
        "targeted_equals_baseline_regret": (
            math.isclose(
                targeted["mean_original_grid_regret"],
                baseline["mean_original_grid_regret"],
                rel_tol=rel_tol,
                abs_tol=abs_tol,
            )
            and math.isclose(
                targeted["maximum_original_grid_regret"],
                baseline["maximum_original_grid_regret"],
                rel_tol=rel_tol,
                abs_tol=abs_tol,
            )
        ),
        "saved_decision_outcome": decision_source["outcome"],
        "consistent_outcome": "no_benefit",
        "new_direct_truth_coordinate_count": 0,
        "original_artifact_modified": False,
    }
    if not (
        audit["minimum_safety_remains_passed"]
        and audit["targeted_equals_baseline_regret"]
        and audit["saved_decision_outcome"] == "no_benefit"
    ):
        raise CompletionAnalysisError("S4 outcome robustness audit failed")
    return output_rows, audit


def _decision_trace(
    protocol: dict[str, Any],
    practical_protocol: dict[str, Any],
    practical_predictions: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    interval = practical_protocol["selector"]["optimization"]["relative_interval"]
    expected_interval = protocol["fixed_values"]["original_relative_time_interval"]
    if interval != expected_interval:
        raise CompletionAnalysisError(
            f"practical time interval mismatch: {interval} != {expected_interval}"
        )
    rows: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for condition_row in practical_predictions["conditions"]:
        condition = condition_row["condition"]
        selection = condition_row["selection"]
        for pf_row in condition_row["pf_predictions"]:
            formula = pf_row["formula"]
            optimum = pf_row.get("optimum") or {}
            diagnostic = pf_row["diagnostic"]
            t_ana = float(pf_row["proxy_analytic_time"])
            allowed_max_relative = float(
                pf_row["maximum_relative_time_after_fallback"]
            )
            reasons = [
                name
                for name, active in (
                    ("cancellation", diagnostic["fallback_cancellation"]),
                    ("sign", diagnostic["fallback_sign"]),
                    ("sentinel_residual", diagnostic["fallback_sentinel_residual"]),
                )
                if active
            ]
            row = {
                "condition": condition,
                "evaluation_group": condition_row["evaluation_group"],
                "formula": formula,
                "rotations": int(pf_row["rotations"]),
                "proxy_analytic_time": t_ana,
                "original_relative_time_min": float(interval[0]),
                "original_relative_time_max": float(interval[1]),
                "original_time_min": float(interval[0]) * t_ana,
                "original_time_max": float(interval[1]) * t_ana,
                "fallback_triggered": bool(pf_row["fallback_triggered"]),
                "fallback_reasons": "+".join(reasons) if reasons else "none",
                "allowed_relative_time_max": allowed_max_relative,
                "allowed_time_cap": allowed_max_relative * t_ana,
                "formula_optimum_relative_time": optimum.get(
                    "relative_to_proxy_t_ana"
                ),
                "formula_optimum_time": optimum.get("time"),
                "formula_optimum_predicted_error_hartree": optimum.get(
                    "error_hartree"
                ),
                "formula_optimum_predicted_cost": optimum.get("cost"),
                "at_optimization_boundary": optimum.get(
                    "at_optimization_boundary"
                ),
                "eligible": bool(pf_row["eligible"]),
                "selected_formula": selection["selected_formula"] == formula,
                "condition_selected_time": (
                    selection["selected_time"]
                    if selection["selected_formula"] == formula
                    else None
                ),
                "condition_selected_predicted_cost": (
                    selection["predicted_cost"]
                    if selection["selected_formula"] == formula
                    else None
                ),
                "condition_selection_reason": (
                    selection["selection_reason"]
                    if selection["selected_formula"] == formula
                    else None
                ),
            }
            rows.append(row)
            by_key[(condition, formula)] = row
    expected = int(protocol["numerical_gates"]["expected_decision_trace_rows"])
    if len(rows) != expected:
        raise CompletionAnalysisError(
            f"decision trace count mismatch: {len(rows)} != {expected}"
        )
    return rows, by_key


def _condition_analysis(
    protocol: dict[str, Any],
    paths: dict[str, Path],
    trace_by_key: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    epsilon = float(protocol["fixed_values"]["target_error_hartree"])
    gamma = float(protocol["fixed_values"]["budget_multiplier"])
    gates = protocol["numerical_gates"]
    rel_tol = float(gates["relative_tolerance"])
    abs_tol = float(gates["absolute_tolerance"])
    s0_rows = {row["condition"]: row for row in _read_csv(paths["s0"] / "scoring.csv")}
    regret_rows = {
        row["condition"]: row
        for row in _read_csv(paths["regret"] / "regret_decomposition.csv")
    }
    if set(s0_rows) != set(regret_rows):
        raise CompletionAnalysisError("S0 and regret condition sets differ")

    output_rows: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    boundary_rows: list[dict[str, Any]] = []
    for condition, s0 in s0_rows.items():
        regret = regret_rows[condition]
        formula = s0["selected_formula"]
        context = condition
        trace = trace_by_key[(condition, formula)]
        selected_time = _float(s0, "selected_time", context)
        if not math.isclose(
            selected_time,
            float(trace["condition_selected_time"]),
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        ):
            raise CompletionAnalysisError(f"{condition}: selected time mismatch")

        e_direct = _float(s0, "exact_time_direct_error_hartree", context)
        e_hat = _float(s0, "predicted_error_hartree", context)
        bias = e_hat - e_direct
        remaining = epsilon - e_direct
        normalized_bias = bias / remaining
        factor_model_identity = 1.0 / (1.0 - normalized_bias)
        factor_model = _float(regret, "factor_model", context)
        if not math.isclose(
            factor_model_identity,
            factor_model,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        ):
            raise CompletionAnalysisError(f"{condition}: cost-bias identity failed")

        factor_time = _float(regret, "factor_time_selection", context)
        factor_domain: float | None = None
        factor_within: float | None = None
        factor_domain_lower: float | None = None
        factor_domain_upper: float | None = None
        factor_within_lower: float | None = None
        factor_within_upper: float | None = None
        reference_time = _float(s0, "original_same_formula_grid_best_time", context)
        t_ana = float(trace["proxy_analytic_time"])
        reference_relative = reference_time / t_ana
        reference_admissible = (
            float(trace["original_relative_time_min"])
            <= reference_relative
            <= float(trace["allowed_relative_time_max"])
        )
        at_cap = math.isclose(
            selected_time,
            float(trace["allowed_time_cap"]),
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        )
        if not trace["fallback_triggered"] and reference_admissible:
            coverage_status = "exact_saved_grid_only"
            factor_domain = 1.0
            factor_within = factor_time
            factor_domain_lower = factor_domain_upper = factor_domain
            factor_within_lower = factor_within_upper = factor_within
        elif trace["fallback_triggered"] and at_cap:
            coverage_status = "analytic_bound_at_cap"
            r = e_direct / epsilon
            factor_within_lower = 1.0
            factor_within_upper = 1.0 / (1.0 - r)
            factor_domain_lower = factor_time * (1.0 - r)
            factor_domain_upper = factor_time
            boundary_rows.append(
                {
                    "condition": condition,
                    "selected_formula": formula,
                    "t_cap": selected_time,
                    "proxy_analytic_time": t_ana,
                    "t_cap_relative_to_proxy_analytic": selected_time / t_ana,
                    "target_error_hartree": epsilon,
                    "direct_error_at_cap_hartree": e_direct,
                    "r_direct_error_over_target": r,
                    "saved_time_factor": factor_time,
                    "factor_within_lower": factor_within_lower,
                    "factor_within_upper": factor_within_upper,
                    "factor_domain_lower": factor_domain_lower,
                    "factor_domain_upper": factor_domain_upper,
                    "maximum_relative_direct_cost_saving_with_cap": r,
                    "reference_grid_oracle_time": reference_time,
                    "reference_grid_oracle_relative_time": reference_relative,
                }
            )
        else:
            coverage_status = "coverage_insufficient"

        factor_margin = _float(regret, "factor_margin", context)
        factor_pf = _float(regret, "factor_pf_selection", context)
        factor_total = _float(regret, "factor_total", context)
        factor_calibration = _float(regret, "factor_calibration", context)
        expanded_closure = factor_model * factor_margin * factor_time * factor_pf
        closure_error = abs(expanded_closure - factor_total)
        if closure_error > float(gates["factor_closure_absolute_tolerance"]):
            raise CompletionAnalysisError(f"{condition}: expanded factor closure failed")

        output_rows.append(
            {
                "condition": condition,
                "evaluation_group": s0["evaluation_group"],
                "selected_formula": formula,
                "selected_time": selected_time,
                "allowed_time_cap": trace["allowed_time_cap"],
                "reference_grid_oracle_time": reference_time,
                "reference_grid_oracle_relative_time": reference_relative,
                "reference_grid_oracle_admissible": reference_admissible,
                "c_star_reference_grid": _float(regret, "c_star", context),
                "c_selected_formula_star_reference_grid": _float(
                    regret, "c_selected_formula_star", context
                ),
                "c_required_selected_time": _float(
                    regret, "c_required_selected_time", context
                ),
                "c_hat": _float(regret, "c_hat", context),
                "b_frozen": _float(regret, "b_frozen", context),
                "factor_model": factor_model,
                "factor_margin": factor_margin,
                "factor_calibration": factor_calibration,
                "saved_factor_time": factor_time,
                "factor_within": factor_within,
                "factor_domain": factor_domain,
                "factor_within_lower": factor_within_lower,
                "factor_within_upper": factor_within_upper,
                "factor_domain_lower": factor_domain_lower,
                "factor_domain_upper": factor_domain_upper,
                "factor_pf": factor_pf,
                "factor_total": factor_total,
                "expanded_factor_closure_error": closure_error,
                "coverage_status": coverage_status,
                "fallback_triggered": trace["fallback_triggered"],
                "fallback_reasons": trace["fallback_reasons"],
                "selected_at_cap": at_cap,
                "success_gamma_1_01": _bool(s0["success_gamma_1_01"]),
                "energy_margin_gamma_1_01_hartree": _float(
                    s0, "energy_margin_gamma_1_01_hartree", context
                ),
            }
        )
        calibration_rows.append(
            {
                "condition": condition,
                "evaluation_group": s0["evaluation_group"],
                "selected_formula": formula,
                "direct_error_hartree": e_direct,
                "predicted_error_hartree": e_hat,
                "signed_absolute_error_bias_hartree": bias,
                "relative_bias_to_direct_error": bias / e_direct,
                "remaining_error_budget_hartree": remaining,
                "signed_bias_over_remaining_budget": normalized_bias,
                "absolute_bias_over_remaining_budget": abs(normalized_bias),
                "factor_model_from_costs": factor_model,
                "factor_model_from_bias_identity": factor_model_identity,
                "identity_absolute_error": abs(factor_model - factor_model_identity),
                "factor_margin": gamma,
                "factor_calibration": factor_calibration,
                "energy_margin_gamma_1_01_hartree": _float(
                    s0, "energy_margin_gamma_1_01_hartree", context
                ),
                "success_gamma_1_01": _bool(s0["success_gamma_1_01"]),
            }
        )

    expected = int(gates["expected_condition_rows"])
    if len(output_rows) != expected or len(boundary_rows) != 2:
        raise CompletionAnalysisError(
            f"condition/boundary row mismatch: {len(output_rows)}/{len(boundary_rows)}"
        )
    boundary = {
        "schema_version": 1,
        "status": "complete_saved_data_bounds",
        "new_direct_truth_coordinate_count": 0,
        "lemma": "For C(t)=A/[t(epsilon-e(t))], 0<t<=T, 0<=e(t)<epsilon, and feasible T: C(T)(1-r)<=inf C(t)<=C(T), r=e(T)/epsilon.",
        "assumptions": [
            "A is positive and independent of time",
            "the selected cap T is feasible under direct error",
            "the comparison uses the selected formula",
            "the wide reference is the saved truth grid, not a continuous-time global oracle",
            "no claim is made about safety outside the cap",
        ],
        "rows": boundary_rows,
    }
    return output_rows, boundary, calibration_rows


def _metric_dictionary() -> str:
    return """# 第一研究 completion analysis 指標辞書

## 費用

- `C_star_reference_grid`: 元2 PF・保存truth格子上の最小直接費用。連続時間oracleではない。
- `C_selected_formula_star_reference_grid`: 選択PFに限定した保存truth格子上の最小直接費用。
- `C_required_selected_time`: 選択PF・exact selected timeの直接誤差を用いた必要費用。
- `C_hat`: truthを使わずPhase Aで凍結した予測費用。
- `B_frozen`: `gamma * C_hat`。今回の`gamma`は1.01。

## 乗法因子

- `F_model = C_hat / C_required_selected_time`: モデル予算の局所的な保守性。
- `F_margin = B_frozen / C_hat`: 固定安全余裕。エネルギー誤差へ1%を足す操作ではない。
- `F_calibration = F_model * F_margin`。
- `F_within`: 実際の許容時刻域内での時刻選択因子。
- `F_domain`: fallback等で許容域を狭めたことによる因子。
- `saved_F_time = F_within * F_domain`。
- `F_P`: 保存2 PF格子におけるPF選択因子。
- `F_total = F_model * F_margin * F_within * F_domain * F_P`。

## coverage status

- `exact_saved_grid_only`: 保存格子oracleが許容域内にあり、保存格子を母集合とした会計では`F_domain=1`。連続時間最適を意味しない。
- `analytic_bound_at_cap`: 全域truthなし。上限補題による`F_within`上界と`F_domain`下界だけを報告する。
- `coverage_insufficient`: 既存データだけでは分離不能。補間や近傍置換をしない。

## safetyとefficiency

- `energy_margin_gamma_1_01_hartree`: target errorからdirect PF誤差と予算由来QPE誤差を引いた量。非負なら、この連続費用proxy内で安全。
- `F_total`: 保存格子基準に対する凍結予算倍率。安全性とは別の効率指標。
- `direct_time_regret`: direct必要費用の時刻選択損失。
- `frozen_budget_overhead`: 1.01倍凍結予算を基準費用で割った超過。上のregretと同一ではない。

## S4費用定義監査

- `stored_s4_beta=0.105`: S4 protocolが保存phase errorの再計算に使用した値。
- `practical_cost_beta=1.2`: practical/S0予測費用とdirect費用が使用した値。
- `consistent_phase_error`: 凍結予算を生成した費用式と同じ1.2で再計算した診断値。元S4成果物は変更しない。
"""


def _make_figures(
    output: Path,
    rows: list[dict[str, Any]],
    target_error_hartree: float,
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    labels = [
        "N2 eq",
        "N2 stretch",
        "CO eq",
        "CO stretch",
        "HF eq",
        "HF stretch",
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for row, label in zip(rows, labels):
        color = "tab:blue" if row["evaluation_group"] == "primary" else "tab:red"
        x = 100.0 * row["energy_margin_gamma_1_01_hartree"] / target_error_hartree
        y = row["factor_total"]
        ax.scatter(x, y, color=color, s=54, zorder=3)
        ax.annotate(label, (x, y), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0.0, color="black", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Energy margin / target error (%)")
    ax.set_ylabel("Frozen-budget factor $F_{total}$")
    ax.set_title("Safety and efficiency are distinct")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    safety_png = figures / "safety_efficiency.png"
    safety_pdf = figures / "safety_efficiency.pdf"
    fig.savefig(safety_png, dpi=180)
    fig.savefig(safety_pdf)
    plt.close(fig)

    x_values = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    time_values = [row["saved_factor_time"] for row in rows]
    within_values = [row["factor_within_upper"] for row in rows]
    domain_values = [row["factor_domain_lower"] for row in rows]
    ax.plot(x_values, time_values, "ko-", label="saved $F_t$")
    ax.plot(x_values, within_values, "s--", color="tab:blue", label="$F_{within}$ exact/upper")
    ax.plot(x_values, domain_values, "^--", color="tab:orange", label="$F_{domain}$ exact/lower")
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle=":")
    ax.set_xticks(x_values, labels, rotation=25, ha="right")
    ax.set_ylabel("Cost factor")
    ax.set_title("Saved-grid accounting and cap bounds")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    domain_png = figures / "time_domain_bounds.png"
    domain_pdf = figures / "time_domain_bounds.pdf"
    fig.savefig(domain_png, dpi=180)
    fig.savefig(domain_pdf)
    plt.close(fig)
    return [
        str(path.relative_to(output))
        for path in (safety_png, safety_pdf, domain_png, domain_pdf)
    ]


def _report(
    protocol_sha: str,
    condition_rows: list[dict[str, Any]],
    boundary: dict[str, Any],
    s4_audit: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# 第一研究 completion analysis：decision、費用定義、domain制約",
        "",
        f"**Status:** `{summary['status']}`",
        "**新規direct truth:** `0`",
        "**新規Hamiltonian・状態生成・fit:** `0`",
        f"**Protocol SHA-256:** `{protocol_sha}`",
        "",
        "## 結論",
        "",
        "第一研究の凍結predictionと保存truthだけを用い、費用を",
        "`F_model * F_margin * F_within * F_domain * F_P`へ整理した。",
        "主4条件のうちN2 stretchだけは保存格子会計でtime selection支配、",
        "残る3条件はcalibration/budget支配である。HF stress 2条件はfallback上限に張り付き、",
        "上限内の改善可能性よりdomain制限の下界が支配的である。",
        "",
        "またS4の保存protocolがphase error再計算に`qpe_beta=0.105`を使う一方、",
        "その予算を作ったpractical/S0費用は`BETA=1.2`を使っていたことを確認した。",
        "費用定義を1.2へ揃えた読み取り専用再集計でも7 strategyすべて6/6安全で、",
        "targeted fallbackとbaselineのregretは同じままなので`no_benefit`は変わらない。",
        "ただし元S4のphase-error値とenergy-margin値は絶対値として流用しない。",
        "",
        "## 条件別の費用会計",
        "",
        "`C*`は元2 PF・保存truth格子上の基準であり、連続時間大域oracleではない。",
        "",
        "| condition | F_model | F_margin | saved F_t | F_within | F_domain | F_P | F_total | coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in condition_rows:
        within = (
            f"{row['factor_within']:.6f}"
            if row["factor_within"] is not None
            else f"<={row['factor_within_upper']:.6f}"
        )
        domain = (
            f"{row['factor_domain']:.6f}"
            if row["factor_domain"] is not None
            else f">={row['factor_domain_lower']:.6f}"
        )
        lines.append(
            f"| {row['condition']} | {row['factor_model']:.6f} | "
            f"{row['factor_margin']:.6f} | {row['saved_factor_time']:.6f} | "
            f"{within} | {domain} | {row['factor_pf']:.6f} | "
            f"{row['factor_total']:.6f} | {row['coverage_status']} |"
        )

    lines.extend(
        [
            "",
            "## HF cap境界",
            "",
            "上限点`T`がdirect errorでもfeasibleなら、`r=e(T)/epsilon`について",
            "`F_within <= 1/(1-r)`、`F_domain >= saved_F_t*(1-r)`である。",
            "",
            "| condition | r | F_within upper | F_domain lower | maximum saving within cap |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in boundary["rows"]:
        lines.append(
            f"| {row['condition']} | {row['r_direct_error_over_target']:.6%} | "
            f"{row['factor_within_upper']:.6f} | {row['factor_domain_lower']:.6f} | "
            f"{row['maximum_relative_direct_cost_saving_with_cap']:.6%} |"
        )

    lines.extend(
        [
            "",
            "この結果は、cap外が安全であることを示さない。HFの約2.1倍を大きく改善するには、",
            "上限内のoptimum推定を精密化するだけでなく、許容域を広げられる別の根拠が必要である。",
            "",
            "## S4費用定義監査",
            "",
            f"- practical/S0 beta: `{s4_audit['practical_cost_beta']}`",
            f"- S4保存scoring beta: `{s4_audit['s4_saved_scoring_beta']}`",
            f"- beta比: `{s4_audit['beta_ratio']}`",
            f"- 保存safe rows: `{s4_audit['stored_safe_row_count']}/42`",
            f"- 整合再計算safe rows: `{s4_audit['consistent_safe_row_count']}/42`",
            f"- 判定が変化したrows: `{s4_audit['success_changed_row_count']}`",
            f"- 整合再計算の最小energy margin: `{s4_audit['minimum_consistent_energy_margin_hartree']:.12g} Ha`",
            f"- 固定判定: `{s4_audit['consistent_outcome']}`",
            "",
            "元S4 artifact、prediction、truth、regret、thresholdは変更していない。これは保存費用を",
            "同一定数で再評価したdefinition auditであり、新しいselector評価ではない。",
            "",
            "## Safetyとefficiency",
            "",
            "S0の1.01倍凍結予算は6/6で安全だったが、HFの`F_total`は約2.15と2.10である。",
            "従って、このdevelopment集合と連続費用proxyでは`safe != efficient`である。",
            "これは分子一般に対する1%余裕の保証ではない。",
            "",
            "## 停止判断",
            "",
            "- S4の`no_benefit`とS5非実施を維持する。",
            "- 新PF、追加分子、新diagnostic、係数探索を開始しない。",
            "- 次は主張台帳、図表、条件式の単体テストを論文化パッケージとして整える。",
            "- 追加truthは、既存boundsとcoverage表示で中心主張を閉じられない場合だけ別protocolで事前固定する。",
        ]
    )
    return "\n".join(lines) + "\n"


def run(project_root: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    protocol_path = (
        protocol_path
        if protocol_path.is_absolute()
        else project_root / protocol_path
    )
    output = output if output.is_absolute() else project_root / output
    if output.exists() and any(output.iterdir()):
        raise CompletionAnalysisError(f"output directory is not empty: {output}")

    protocol = _load_json(protocol_path)
    protocol_sha = sha256_file(protocol_path)
    source_manifest, paths = _validate_sources(project_root, protocol)
    practical_protocol = _load_json(paths["practical"] / "protocol.json")
    practical_predictions = _load_json(paths["practical"] / "predictions.json")
    decision_rows, trace_by_key = _decision_trace(
        protocol, practical_protocol, practical_predictions
    )
    condition_rows, boundary, calibration_rows = _condition_analysis(
        protocol, paths, trace_by_key
    )
    s4_rows, s4_audit = _cost_definition_audit(
        project_root, protocol, paths, practical_predictions
    )

    status = protocol["status_if_complete"]
    coverage_counts = dict(Counter(row["coverage_status"] for row in condition_rows))
    summary = {
        "schema_version": 1,
        "status": status,
        "condition_count": len(condition_rows),
        "decision_trace_row_count": len(decision_rows),
        "s4_definition_audit_row_count": len(s4_rows),
        "new_direct_truth_coordinate_count": 0,
        "new_hamiltonian_count": 0,
        "new_state_generation_count": 0,
        "new_fit_count": 0,
        "coverage_counts": coverage_counts,
        "s0_gamma_1_01_safe_count": sum(
            row["success_gamma_1_01"] for row in condition_rows
        ),
        "mean_frozen_budget_overhead": _mean(
            row["factor_total"] - 1.0 for row in condition_rows
        ),
        "primary_mean_frozen_budget_overhead": _mean(
            row["factor_total"] - 1.0
            for row in condition_rows
            if row["evaluation_group"] == "primary"
        ),
        "stress_mean_frozen_budget_overhead": _mean(
            row["factor_total"] - 1.0
            for row in condition_rows
            if row["evaluation_group"] == "stress_test"
        ),
        "pf_selection_loss_count": sum(
            not math.isclose(row["factor_pf"], 1.0) for row in condition_rows
        ),
        "s4_definition_audit": {
            "status": s4_audit["status"],
            "consistent_safe_row_count": s4_audit["consistent_safe_row_count"],
            "success_changed_row_count": s4_audit["success_changed_row_count"],
            "minimum_consistent_energy_margin_hartree": s4_audit[
                "minimum_consistent_energy_margin_hartree"
            ],
            "consistent_outcome": s4_audit["consistent_outcome"],
        },
        "research_decision": {
            "s4_no_benefit_preserved": True,
            "proceed_to_s5": False,
            "new_selector_started": False,
            "next_action": "paper_claim_ledger_and_reproducibility_synthesis",
        },
    }

    output.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(output / "protocol.json", protocol_path.read_text(encoding="utf-8"))
    _write_json(output / "source_manifest.json", source_manifest)
    _write_csv(output / "decision_trace.csv", decision_rows)
    _write_csv(output / "cost_factor_decomposition.csv", condition_rows)
    _write_csv(output / "calibration_precision.csv", calibration_rows)
    _write_json(output / "boundary_bounds.json", boundary)
    _write_csv(output / "s4_cost_definition_audit.csv", s4_rows)
    _write_json(output / "s4_cost_definition_audit.json", s4_audit)
    _write_json(output / "summary.json", summary)
    _atomic_write_text(output / "metric_dictionary.md", _metric_dictionary())
    figure_names = _make_figures(
        output,
        condition_rows,
        float(protocol["fixed_values"]["target_error_hartree"]),
    )
    _atomic_write_text(
        output / "report.md",
        _report(protocol_sha, condition_rows, boundary, s4_audit, summary),
    )

    checks = {
        "source_identity": all(source_manifest["checks"].values()),
        "condition_count": len(condition_rows)
        == int(protocol["numerical_gates"]["expected_condition_rows"]),
        "decision_trace_count": len(decision_rows)
        == int(protocol["numerical_gates"]["expected_decision_trace_rows"]),
        "s4_row_count": len(s4_rows)
        == int(protocol["numerical_gates"]["expected_s4_rows"]),
        "no_new_truth": summary["new_direct_truth_coordinate_count"] == 0,
        "factor_closure": all(
            row["expanded_factor_closure_error"]
            <= float(protocol["numerical_gates"]["factor_closure_absolute_tolerance"])
            for row in condition_rows
        ),
        "s4_outcome_robust": (
            s4_audit["consistent_outcome"] == "no_benefit"
            and s4_audit["consistent_safe_row_count"] == 42
        ),
        "coverage_is_explicit": "coverage_insufficient" not in coverage_counts,
    }
    audit = {
        "status": status if all(checks.values()) else "failed_validation",
        "protocol_sha256": protocol_sha,
        "checks": checks,
        "all_gates_passed": all(checks.values()),
        "accounting": {
            "condition_count": len(condition_rows),
            "decision_trace_row_count": len(decision_rows),
            "s4_definition_audit_row_count": len(s4_rows),
            "new_direct_truth_coordinate_count": 0,
        },
    }
    _write_json(output / "audit.json", audit)
    if not audit["all_gates_passed"]:
        raise CompletionAnalysisError(f"analysis gates failed: {checks}")

    artifact_names = [
        "protocol.json",
        "source_manifest.json",
        "decision_trace.csv",
        "cost_factor_decomposition.csv",
        "calibration_precision.csv",
        "boundary_bounds.json",
        "s4_cost_definition_audit.csv",
        "s4_cost_definition_audit.json",
        "summary.json",
        "metric_dictionary.md",
        "report.md",
        "audit.json",
        *figure_names,
    ]
    manifest = {
        "schema_version": 1,
        "status": status,
        "created_at": datetime.now().astimezone().isoformat(),
        "base_commit": protocol["base_commit"],
        "protocol_sha256": protocol_sha,
        "new_direct_truth_coordinate_count": 0,
        "artifact_sha256": {
            name: sha256_file(output / name) for name in artifact_names
        },
    }
    _write_json(output / "manifest.json", manifest)
    _atomic_write_text(output / "COMPLETE", "")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run(args.project_root, args.protocol, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
