"""Read-only helpers for the D2R candidate-validation study.

This module deliberately contains no molecular construction or eigensolver calls.
R0 uses only committed Phase A/Phase B artifacts from the closed second study.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SOURCE_COMMIT = "05649f1a7b6e405eadc2dbbdc0897836e0fa2f02"
PHASE_A_RELATIVE = Path(
    "artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694"
)
PHASE_B_RELATIVE = Path(
    "artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f"
)
PROTOCOL_RELATIVE = Path(
    "review_response/second_study_safe_time_domain_protocol.json"
)

SOURCE_PATHS = (
    Path("review_response/second_study_safe_time_domain_completion_report.md"),
    Path("review_response/second_study_safe_time_domain_completion_audit.json"),
    PROTOCOL_RELATIVE,
    Path("review_response/second_study_safe_time_domain_phase_a_boundary_audit.json"),
    PHASE_A_RELATIVE / "predictions.json",
    PHASE_A_RELATIVE / "proxy_points.csv",
    PHASE_A_RELATIVE / "phase_a_audit.json",
    PHASE_A_RELATIVE / "sanitized_input_manifest.json",
    PHASE_B_RELATIVE / "strategy_scoring.csv",
    PHASE_B_RELATIVE / "direct_points.csv",
    PHASE_B_RELATIVE / "decision.json",
    PHASE_B_RELATIVE / "manifest.json",
    Path("review_response/second_study_safe_time_domain_execution.py"),
    Path("review_response/run_second_study_safe_time_domain_phase_a.py"),
    Path("review_response/run_second_study_safe_time_domain_phase_b.py"),
    Path("review_tests/test_second_study_safe_time_domain_execution.py"),
    Path("PF_first_study_paper_claim_ledger_20260926.md"),
)


class CandidateValidationError(RuntimeError):
    """Raised when a frozen input or algebraic identity does not match."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: Mapping[str, Any] | Sequence[Any]) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise CandidateValidationError(f"expected JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def git_blob(project_root: Path, commit: str, relative: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative.as_posix()}"],
        cwd=project_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise CandidateValidationError(
            f"source missing from {commit}: {relative}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return result.stdout


def source_manifest(
    project_root: Path,
    commit: str = SOURCE_COMMIT,
    permitted_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    overrides = dict(permitted_overrides or {})
    entries: list[dict[str, Any]] = []
    observed_overrides: set[str] = set()
    for relative in SOURCE_PATHS:
        path = project_root / relative
        if not path.is_file():
            raise CandidateValidationError(f"working-tree source missing: {relative}")
        blob = git_blob(project_root, commit, relative)
        working_hash = sha256_file(path)
        blob_hash = sha256_bytes(blob)
        matches = working_hash == blob_hash
        override = overrides.get(relative.as_posix())
        if not matches and (
            override is None
            or override.get("frozen_blob_sha256") != blob_hash
            or override.get("authorized_current_sha256") != working_hash
        ):
            raise CandidateValidationError(
                f"working-tree source differs from frozen blob: {relative}"
            )
        entry = {
            "path": relative.as_posix(),
            "sha256": working_hash,
            "source_commit": commit,
            "byte_count": path.stat().st_size,
            "working_tree_matches_source_blob": matches,
        }
        if not matches:
            observed_overrides.add(relative.as_posix())
            entry["frozen_blob_sha256"] = blob_hash
            entry["authorized_override"] = True
        entries.append(entry)
    if observed_overrides != set(overrides):
        raise CandidateValidationError(
            "source manifest contains an unused or unchanged override"
        )
    result = {
        "schema": "pf_candidate_validation_source_manifest_v1",
        "source_commit": commit,
        "entry_count": len(entries),
        "entries": entries,
    }
    if overrides:
        result["authorized_override_count"] = len(observed_overrides)
    return result


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=2e-12, abs_tol=1e-14)


def _one_match(
    rows: Iterable[Mapping[str, Any]],
    *,
    condition: str,
    time_value: float,
    label: str,
) -> Mapping[str, Any]:
    matches = [
        row
        for row in rows
        if str(row["condition"]) == condition
        and _close(float(row["time_hartree_inverse"]), time_value)
    ]
    if len(matches) != 1:
        raise CandidateValidationError(
            f"{condition}/{time_value.hex()}: expected one {label}, got {len(matches)}"
        )
    return matches[0]


def positive_two_term_zero(model: Mapping[str, Any] | None) -> float | None:
    """Return the positive nonzero root of a4*t^4+a6*t^6, if present."""

    if model is None:
        return None
    powers = [int(value) for value in model.get("coefficient_powers", [])]
    values = [float(value) for value in model.get("coefficient_values", [])]
    if powers != [4, 6] or len(values) != 2:
        return None
    a4, a6 = values
    scale = max(abs(a4), abs(a6), 1.0)
    if abs(a4) <= 1e-15 * scale or abs(a6) <= 1e-15 * scale:
        return None
    ratio = -a4 / a6
    if not math.isfinite(ratio) or ratio <= 0.0:
        return None
    return math.sqrt(ratio)


def selected_coordinate_plan(predictions: Mapping[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for condition_row in predictions["conditions"]:
        condition = str(condition_row["condition"])
        candidates: list[dict[str, Any]] = []
        for strategy, row in condition_row["strategies"].items():
            time_value = float(row["selected_time_hartree_inverse"])
            matching = next(
                (
                    item
                    for item in candidates
                    if _close(float(item["time_hartree_inverse"]), time_value)
                ),
                None,
            )
            if matching is None:
                matching = {
                    "condition": condition,
                    "time_hartree_inverse": time_value,
                    "time_hex": time_value.hex(),
                    "selected_relative_to_t_ana": float(
                        row["selected_relative_to_t_ana"]
                    ),
                    "strategies": [],
                }
                candidates.append(matching)
            matching["strategies"].append(str(strategy))
        plan.extend(sorted(candidates, key=lambda item: item["time_hartree_inverse"]))
    return plan


def _optional_proxy(
    rows: Sequence[Mapping[str, Any]], condition: str, time_value: float
) -> Mapping[str, Any] | None:
    matches = [
        row
        for row in rows
        if str(row["condition"]) == condition
        and _close(float(row["time_hartree_inverse"]), time_value)
    ]
    if len(matches) > 1:
        raise CandidateValidationError(
            f"duplicate saved proxy: {condition}/{time_value.hex()}"
        )
    return matches[0] if matches else None


def build_failure_ledger(project_root: Path) -> dict[str, Any]:
    protocol = read_json(project_root / PROTOCOL_RELATIVE)
    predictions = read_json(project_root / PHASE_A_RELATIVE / "predictions.json")
    scoring_json = read_json(project_root / PHASE_B_RELATIVE / "strategy_scoring.json")
    direct_json = read_json(project_root / PHASE_B_RELATIVE / "direct_points.json")
    proxy_rows = read_csv(project_root / PHASE_A_RELATIVE / "proxy_points.csv")

    protocol_hash = sha256_file(project_root / PROTOCOL_RELATIVE)
    if predictions.get("protocol_sha256") != protocol_hash:
        raise CandidateValidationError("prediction protocol hash mismatch")
    if direct_json.get("protocol_sha256") != protocol_hash:
        raise CandidateValidationError("direct-point protocol hash mismatch")
    if len(scoring_json.get("rows", [])) != 16:
        raise CandidateValidationError("expected exactly 16 strategy rows")

    epsilon = float(protocol["scope"]["target_error_hartree"])
    beta = float(protocol["cost_model"]["beta"])
    gamma = float(protocol["cost_model"]["gamma"])
    expected_constants = (0.00015936001019904, 1.2, 1.01)
    for actual, expected, name in zip(
        (epsilon, beta, gamma), expected_constants, ("epsilon", "beta", "gamma")
    ):
        if actual != expected:
            raise CandidateValidationError(
                f"frozen {name} changed: {actual!r} != {expected!r}"
            )

    direct_rows = list(direct_json["points"])
    score_rows = list(scoring_json["rows"])
    ledger: list[dict[str, Any]] = []
    for condition_row in predictions["conditions"]:
        condition = str(condition_row["condition"])
        diagnostics = condition_row["selector_diagnostics"]
        original_zero = positive_two_term_zero(diagnostics.get("original_model"))
        pooled_zero = positive_two_term_zero(diagnostics.get("pooled_model"))
        fallback_triggered = bool(diagnostics["fallback_triggered"])
        for strategy, frozen_row in condition_row["strategies"].items():
            time_value = float(frozen_row["selected_time_hartree_inverse"])
            direct = _one_match(
                direct_rows,
                condition=condition,
                time_value=time_value,
                label="direct point",
            )
            score_matches = [
                row
                for row in score_rows
                if row["condition"] == condition and row["strategy"] == strategy
            ]
            if len(score_matches) != 1:
                raise CandidateValidationError(
                    f"{condition}/{strategy}: scoring row count {len(score_matches)}"
                )
            score = score_matches[0]
            proxy = _optional_proxy(proxy_rows, condition, time_value)
            e_hat = float(frozen_row["guarded_error_hartree"])
            direct_error = float(direct["direct_error_hartree"])
            frozen_budget = float(frozen_row["frozen_pauli_rotation_budget"])
            rotations = int(frozen_row["rotation_count_per_pf_step"])
            invalid = None
            if time_value <= 0.0 or frozen_budget <= 0.0:
                invalid = "nonpositive_time_or_budget"
            elif e_hat >= epsilon:
                invalid = "predicted_error_not_feasible"
            elif not all(
                math.isfinite(value)
                for value in (time_value, frozen_budget, e_hat, direct_error)
            ):
                invalid = "nonfinite"
            qpe_error = beta * rotations / (time_value * frozen_budget)
            allowed = (1.0 - 1.0 / gamma) * (epsilon - e_hat)
            actual = direct_error - e_hat
            margin = epsilon - direct_error - qpe_error
            expected_budget = (
                gamma * beta * rotations / (time_value * (epsilon - e_hat))
            )
            direct_cost = direct.get("direct_required_cost")
            row = {
                "condition": condition,
                "strategy": strategy,
                "operational": bool(frozen_row["operational"]),
                "selected_time_hartree_inverse": time_value,
                "selected_time_hex": time_value.hex(),
                "selected_relative_to_t_ana": float(
                    frozen_row["selected_relative_to_t_ana"]
                ),
                "selection_source": str(frozen_row["selection_source"]),
                "fallback_triggered_for_condition": fallback_triggered,
                "extension_selected": bool(frozen_row["extension_selected"]),
                "signed_model_or_central_prediction_hartree": float(
                    frozen_row["predicted_signed_shift_hartree"]
                ),
                "absolute_central_prediction_hartree": float(
                    frozen_row["predicted_error_hartree"]
                ),
                "budget_error_used_hartree": e_hat,
                "guard_premium_over_central_hartree": e_hat
                - float(frozen_row["predicted_error_hartree"]),
                "saved_proxy_at_selected_time": proxy is not None,
                "saved_proxy_role": None if proxy is None else proxy["point_role"],
                "saved_proxy_signed_hartree": (
                    None if proxy is None else float(proxy["proxy_hartree"])
                ),
                "direct_signed_shift_hartree": float(
                    direct["signed_direct_shift_hartree"]
                ),
                "direct_absolute_error_hartree": direct_error,
                "direct_required_cost": direct_cost,
                "frozen_pauli_rotation_budget": frozen_budget,
                "rotation_count_per_pf_step": rotations,
                "candidate_grid_oracle_cost": float(
                    score["candidate_grid_oracle_cost"]
                ),
                "selection_regret": score["selection_regret"],
                "frozen_budget_regret": float(score["frozen_budget_regret"]),
                "qpe_error_hartree": qpe_error,
                "energy_margin_hartree": margin,
                "allowed_underestimation_hartree": allowed,
                "actual_underestimation_hartree": actual,
                "underestimation_over_allowance": actual / allowed,
                "required_cost_over_frozen_budget": (
                    None if direct_cost is None else float(direct_cost) / frozen_budget
                ),
                "accuracy_target_met": bool(score["accuracy_target_met"]),
                "unsafe_execution": bool(score["unsafe_execution"]),
                "expected_budget_from_identity": expected_budget,
                "budget_identity_relative_error": abs(expected_budget - frozen_budget)
                / frozen_budget,
                "margin_identity_residual_hartree": margin - (allowed - actual),
                "original_model_positive_zero_hartree_inverse": original_zero,
                "distance_to_original_model_zero": (
                    None if original_zero is None else abs(time_value - original_zero)
                ),
                "pooled_model_positive_zero_hartree_inverse": pooled_zero,
                "distance_to_pooled_model_zero": (
                    None if pooled_zero is None else abs(time_value - pooled_zero)
                ),
                "status": "valid" if invalid is None else invalid,
                "evidence_class": "post_hoc_truth_diagnostic",
            }
            ledger.append(row)

    plan = selected_coordinate_plan(predictions)
    for item in plan:
        direct = _one_match(
            direct_rows,
            condition=str(item["condition"]),
            time_value=float(item["time_hartree_inverse"]),
            label="direct point",
        )
        proxy = _optional_proxy(
            proxy_rows, str(item["condition"]), float(item["time_hartree_inverse"])
        )
        item.update(
            {
                "direct_truth_available": True,
                "direct_signed_shift_hartree": float(
                    direct["signed_direct_shift_hartree"]
                ),
                "direct_absolute_error_hartree": float(
                    direct["direct_error_hartree"]
                ),
                "saved_cisd_proxy_available": proxy is not None,
                "saved_cisd_proxy_signed_hartree": (
                    None if proxy is None else float(proxy["proxy_hartree"])
                ),
                "saved_cisd_proxy_role": None if proxy is None else proxy["point_role"],
            }
        )

    condition_counts: dict[str, int] = {}
    for item in plan:
        condition_counts[item["condition"]] = condition_counts.get(item["condition"], 0) + 1
    checks = {
        "ledger_row_count": len(ledger),
        "selected_coordinate_count": len(plan),
        "selected_coordinate_counts_by_condition": condition_counts,
        "saved_selected_coordinate_proxy_count": sum(
            int(item["saved_cisd_proxy_available"]) for item in plan
        ),
        "missing_selected_coordinate_proxy_count": sum(
            int(not item["saved_cisd_proxy_available"]) for item in plan
        ),
        "maximum_budget_identity_relative_error": max(
            float(row["budget_identity_relative_error"]) for row in ledger
        ),
        "maximum_margin_identity_absolute_residual_hartree": max(
            abs(float(row["margin_identity_residual_hartree"])) for row in ledger
        ),
    }
    if checks["ledger_row_count"] != 16:
        raise CandidateValidationError("R0 ledger is not 16 rows")
    if checks["selected_coordinate_count"] != 10:
        raise CandidateValidationError("R1 coordinate plan is not 10 rows")
    if condition_counts != {
        "LiF_active_eq_sto3g": 2,
        "LiF_active_stretch150_sto3g": 2,
        "HCl_full_eq_sto3g": 3,
        "HCl_full_stretch150_sto3g": 3,
    }:
        raise CandidateValidationError(f"unexpected coordinate counts: {condition_counts}")
    if checks["maximum_budget_identity_relative_error"] > 5e-15:
        raise CandidateValidationError("frozen-budget identity failed")
    if checks["maximum_margin_identity_absolute_residual_hartree"] > 5e-18:
        raise CandidateValidationError("energy-margin identity failed")
    return {
        "protocol": protocol,
        "protocol_sha256": protocol_hash,
        "predictions": predictions,
        "ledger": ledger,
        "coordinate_plan": plan,
        "checks": checks,
    }


def proxy_signed_from_echo(echo_imaginary: float, time_value: float) -> float:
    if not math.isfinite(time_value) or time_value <= 0.0:
        raise CandidateValidationError("proxy time must be positive and finite")
    if not math.isfinite(echo_imaginary):
        raise CandidateValidationError("echo imaginary part must be finite")
    return float(echo_imaginary / time_value)


def classify_components(
    components: Mapping[str, float], allowed_underestimation: float
) -> dict[str, Any]:
    """Apply the preregistered R1 materiality/dominance rule."""

    if allowed_underestimation <= 0.0 or not math.isfinite(allowed_underestimation):
        raise CandidateValidationError("allowed underestimation must be positive")
    values = {name: float(value) for name, value in components.items()}
    if not values or not all(math.isfinite(value) for value in values.values()):
        raise CandidateValidationError("components must be finite and nonempty")
    ordered = sorted(values, key=lambda name: abs(values[name]), reverse=True)
    largest = ordered[0]
    second = abs(values[ordered[1]]) if len(ordered) > 1 else 0.0
    largest_abs = abs(values[largest])
    material = {
        name: abs(value) > allowed_underestimation
        for name, value in values.items()
    }
    sole_dominant = material[largest] and (
        second == 0.0 or largest_abs >= 2.0 * second
    )
    return {
        "material_by_original_budget_allowance": material,
        "component_over_original_budget_allowance": {
            name: abs(value) / allowed_underestimation
            for name, value in values.items()
        },
        "largest_absolute_component": largest,
        "largest_over_second_largest": (
            None if second == 0.0 else largest_abs / second
        ),
        "attribution": largest if sole_dominant else "mixed_or_none",
    }


def csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise CandidateValidationError(f"refusing to write empty CSV: {path}")
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(value) for key, value in row.items()})


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
