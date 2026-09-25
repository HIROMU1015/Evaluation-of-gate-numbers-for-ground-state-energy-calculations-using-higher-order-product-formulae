"""Frozen S4 state-convergence selector comparison and exact-time scorer.

Phase A consumes only sanitized practical-calibration inputs.  It freezes all
seven strategy predictions without accepting a truth path.  Phase B verifies
that freeze before opening H01/P03 truth and performing direct exact-time
scoring.  This is a development comparison, not an independent holdout.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import platform
import resource
import shutil
import subprocess
import time
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.sparse.linalg import expm_multiply

import run_full_electron_nh3_higher_term_diagnosis as diagnosis
import run_practical_calibration_minimal as practical
from review_response import _pf_first_study_s0_exact_time_scoring_base as s0
from review_response import run_pf_first_study_s0_exact_time_scoring_v1_1 as s0_v1_1


PROTOCOL_PATH = Path(__file__).with_name(
    "pf_first_study_s4_state_convergence_protocol.json"
)
EXPECTED_PROTOCOL_SHA256 = (
    "5c3c33fab6752b5ccf0ec9ee415e115bdf2134256e5a956f6b0e9b639f554c40"
)
EXPECTED_PRACTICAL_PROTOCOL_SHA256 = (
    "7bbe9958837a881f0247b6e72f5e80e2331e0cfe50dea18addd13a2748467d55"
)
EXPECTED_PRACTICAL_PREDICTIONS_SHA256 = (
    "fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e"
)
EXPECTED_PRACTICAL_PHASE_A_COMMIT = (
    "79035cc7c414c04cafe8b9f8bdc779a17ec57302"
)
FORMULAE = ("current_m3", "yoshida4")
STRATEGIES = (
    "practical_baseline",
    "fixed_current_m3",
    "fixed_yoshida4",
    "diagnostic_record_only",
    "universal_fallback",
    "state_targeted_fallback",
    "equal_cost_extra_points",
)
TIME_FACTORS = (0.99, 1.0, 1.01)
TIME_RTOL = 2e-12


class S4ValidationError(RuntimeError):
    """Raised when a frozen source, phase boundary, or numerical gate fails."""


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode())
    digest.update(json.dumps(array.shape).encode())
    digest.update(array.tobytes())
    return digest.hexdigest()


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _git_is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    ).returncode == 0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [{key: _jsonable(row.get(key)) for key in fields} for row in rows]
        )


def _protocol() -> dict[str, Any]:
    if _sha256(PROTOCOL_PATH) != EXPECTED_PROTOCOL_SHA256:
        raise S4ValidationError("S4 protocol hash mismatch")
    protocol = _load_json(PROTOCOL_PATH)
    if protocol.get("protocol_id") != "pf_first_study_s4_state_convergence_v1":
        raise S4ValidationError("S4 protocol identity mismatch")
    return protocol


def _conditions(protocol: dict[str, Any]) -> list[str]:
    return list(protocol["conditions"]["primary"]) + list(
        protocol["conditions"]["stress_test"]
    )


def _prepare_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    allowed = {"driver.log", "computation.log", ".gitignore"}
    unexpected = [path.name for path in output_dir.iterdir() if path.name not in allowed]
    if unexpected:
        raise FileExistsError(
            "refusing non-empty output directory: " + ", ".join(sorted(unexpected))
        )
    (output_dir / ".gitignore").write_text(
        ".runtime/\ndriver.log\n", encoding="utf-8"
    )


def truncate_cisd_state(
    state: np.ndarray, retained_squared_norm: float = 0.99
) -> tuple[np.ndarray, dict[str, Any]]:
    """Apply the frozen coefficient-only deterministic truncation."""
    vector = np.asarray(state, dtype=np.complex128)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("CISD state must be a nonempty vector")
    norm = float(np.linalg.norm(vector))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("CISD state must be normalized")
    if not 0.0 < float(retained_squared_norm) <= 1.0:
        raise ValueError("retained squared norm must be in (0, 1]")
    indices = np.arange(vector.size, dtype=np.int64)
    order = np.lexsort((indices, -np.abs(vector)))
    cumulative = np.cumsum(np.abs(vector[order]) ** 2)
    retained_count = int(np.searchsorted(cumulative, retained_squared_norm) + 1)
    retained_count = min(max(retained_count, 1), vector.size)
    kept = order[:retained_count]
    coarse = np.zeros_like(vector)
    coarse[kept] = vector[kept]
    pre_norm_squared = float(np.vdot(coarse, coarse).real)
    coarse /= math.sqrt(pre_norm_squared)
    metadata = {
        "retained_squared_norm_threshold": float(retained_squared_norm),
        "retained_coefficient_count": retained_count,
        "total_coefficient_count": int(vector.size),
        "retained_fraction": float(retained_count / vector.size),
        "pre_normalization_retained_squared_norm": pre_norm_squared,
        "fine_state_sha256": _array_sha256(vector),
        "coarse_state_sha256": _array_sha256(coarse),
        "sort_rule": "descending_absolute_coefficient_then_restricted_basis_index",
        "hamiltonian_used_for_truncation": False,
    }
    return coarse, metadata


def _proxy_point_for_state(
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    state: np.ndarray,
) -> dict[str, Any]:
    vector = np.asarray(state, dtype=np.complex128)
    started = time.perf_counter()
    pf_state, pf_timing = practical.h01._apply_pf_cpu(
        system, sequence, float(time_value), vector[:, None]
    )
    pf_vector = np.asarray(pf_state[:, 0])
    reference_started = time.perf_counter()
    exact_vector = expm_multiply(
        (1j * float(time_value)) * system["hamiltonian"], vector
    )
    reference_seconds = time.perf_counter() - reference_started
    overlap = complex(np.vdot(exact_vector, pf_vector))
    state_error = float(np.linalg.norm(pf_vector - exact_vector))
    diagonal_signal = abs(float(overlap.imag))
    return {
        "time": float(time_value),
        "echo_real": float(overlap.real),
        "echo_imaginary": float(overlap.imag),
        "echo_imag_hartree": float(overlap.imag / float(time_value)),
        "state_error": state_error,
        "cancellation_index": diagonal_signal
        / max(state_error, np.finfo(float).tiny),
        "pf_state_norm": float(np.linalg.norm(pf_vector)),
        "exact_state_norm": float(np.linalg.norm(exact_vector)),
        "pf_action_seconds": float(pf_timing["total"]),
        "hamiltonian_evolution_seconds": float(reference_seconds),
        "proxy_point_seconds": float(time.perf_counter() - started),
    }


def _state_proxy_cache(
    output_dir: Path,
    condition: str,
    formula: str,
    state_role: str,
    relative: float,
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    state: np.ndarray,
    sanitized_sha256: str,
) -> tuple[dict[str, Any], bool]:
    key = {
        "s4_protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "condition": condition,
        "formula": formula,
        "state_role": state_role,
        "state_sha256": _array_sha256(state),
        "sanitized_sha256": sanitized_sha256,
        "relative_time": float(relative),
        "absolute_time": float(time_value),
    }
    digest = hashlib.sha256(
        json.dumps(key, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path = output_dir / ".runtime/s4_proxy_cache" / condition / formula / f"{digest}.json"
    if path.is_file():
        payload = _load_json(path)
        if payload.get("cache_key") != key:
            raise S4ValidationError(f"stale S4 proxy cache: {path}")
        return payload["point"], True
    point = _proxy_point_for_state(system, sequence, time_value, state)
    _write_json(path, {"cache_key": key, "point": point})
    return point, False


def assess_state_risk(
    full_values: Sequence[float],
    coarse_values: Sequence[float],
    epsilon: float,
    risk_threshold: float,
    sign_floor: float,
) -> dict[str, Any]:
    if len(full_values) != len(coarse_values) or not full_values:
        raise ValueError("full/coarse proxy sequences must be nonempty and aligned")
    differences = [float(full - coarse) for full, coarse in zip(full_values, coarse_values, strict=True)]
    score = max(abs(value) for value in differences) / float(epsilon)
    sign_mismatches = [
        bool(
            abs(float(full)) > float(sign_floor)
            and abs(float(coarse)) > float(sign_floor)
            and np.sign(full) != np.sign(coarse)
        )
        for full, coarse in zip(full_values, coarse_values, strict=True)
    ]
    magnitude_risk = bool(score > float(risk_threshold))
    sign_risk = any(sign_mismatches)
    return {
        "primary_score": float(score),
        "risk_threshold": float(risk_threshold),
        "maximum_absolute_proxy_difference_hartree": max(abs(value) for value in differences),
        "signed_proxy_differences_hartree": differences,
        "sign_noise_floor_hartree": float(sign_floor),
        "sign_mismatch_by_point": sign_mismatches,
        "magnitude_risk": magnitude_risk,
        "sign_risk": sign_risk,
        "state_risk": bool(magnitude_risk or sign_risk),
    }


def _fit_two_term(
    points: Sequence[dict[str, Any]], t_ana: float, name: str
) -> dict[str, Any]:
    times = np.asarray([float(point["time"]) for point in points])
    values = np.asarray([float(point["echo_imag_hartree"]) for point in points])
    relative = times / float(t_ana)
    scale = float(np.max(np.abs(values))) or 1.0
    design = np.column_stack((relative**4, relative**6))
    scaled = np.linalg.lstsq(design, values / scale, rcond=None)[0]
    coefficients = [
        float(scale * scaled[0] / t_ana**4),
        float(scale * scaled[1] / t_ana**6),
    ]
    fitted = coefficients[0] * times**4 + coefficients[1] * times**6
    return {
        "name": name,
        "formal_order": 4,
        "coefficient_powers": [4, 6],
        "coefficient_values": coefficients,
        "coefficient_signs": [int(np.sign(value)) for value in coefficients],
        "training_relative_to_t_ana": relative.tolist(),
        "training_maximum_absolute_residual_hartree": float(
            np.max(np.abs(fitted - values))
        ),
        "training_design_condition_number": float(np.linalg.cond(design)),
        "coefficient_source": "unweighted signed least squares of full-CISD proxy",
    }


def _optimum(
    model: dict[str, Any],
    t_ana: float,
    rotations: int,
    maximum_relative: float | None,
) -> dict[str, Any] | None:
    protocol = _protocol()
    lower, upper = map(float, protocol["base_selector"]["optimization_relative_interval"])
    if maximum_relative is not None:
        upper = min(upper, float(maximum_relative))
    relative = np.linspace(
        lower, upper, int(protocol["base_selector"]["optimization_grid_points"])
    )
    times = relative * float(t_ana)
    shifts = np.asarray([practical._prediction(model, value) for value in times])
    epsilon = float(protocol["target_error_hartree"])
    costs = np.full(times.shape, np.inf)
    valid = np.abs(shifts) < epsilon
    costs[valid] = diagnosis.BETA * int(rotations) / (
        times[valid] * (epsilon - np.abs(shifts[valid]))
    )
    selected = int(np.argmin(costs))
    if not np.isfinite(costs[selected]):
        return None
    return {
        "time": float(times[selected]),
        "relative_to_proxy_t_ana": float(relative[selected]),
        "signed_shift_hartree": float(shifts[selected]),
        "error_hartree": float(abs(shifts[selected])),
        "cost": float(costs[selected]),
        "at_optimization_boundary": selected in (0, len(times) - 1),
    }


def _selection(
    pf_rows: Sequence[dict[str, Any]],
    allowed_formula: str | None = None,
) -> dict[str, Any]:
    eligible = [
        row for row in pf_rows
        if row.get("eligible") and (allowed_formula is None or row["formula"] == allowed_formula)
    ]
    if not eligible:
        return {
            "status": "abstain",
            "selected_formula": None,
            "selected_time": None,
            "predicted_signed_shift_hartree": None,
            "predicted_error_hartree": None,
            "predicted_cost": None,
            "fallback_triggered": True,
            "selection_reason": "no_proxy_feasible_allowed_pf",
        }
    selected = min(eligible, key=lambda row: float(row["optimum"]["cost"]))
    optimum = selected["optimum"]
    return {
        "status": "selected",
        "selected_formula": selected["formula"],
        "selected_time": optimum["time"],
        "predicted_signed_shift_hartree": optimum["signed_shift_hartree"],
        "predicted_error_hartree": optimum["error_hartree"],
        "predicted_cost": optimum["cost"],
        "fallback_triggered": bool(selected.get("fallback_triggered", False)),
        "selection_reason": "minimum_predicted_cost_among_allowed_feasible_pfs",
    }


def _strategy_pf_rows(
    baseline: dict[str, Any],
    state_risk: dict[str, bool],
    equal_models: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for strategy in STRATEGIES:
        rows: list[dict[str, Any]] = []
        for original in baseline["pf_predictions"]:
            row = dict(original)
            formula = str(row["formula"])
            model = row.get("model")
            t_ana = row.get("proxy_analytic_time")
            rotations = row.get("rotations")
            if model is None or t_ana is None or rotations is None:
                rows.append(row)
                continue
            maximum: float | None = 0.5 if row.get("fallback_triggered") else None
            if strategy == "universal_fallback":
                maximum = 0.5
            elif strategy == "state_targeted_fallback" and state_risk[formula]:
                maximum = 0.5
            if strategy == "equal_cost_extra_points":
                model = equal_models[formula]
                row["model"] = model
            optimum = _optimum(model, float(t_ana), int(rotations), maximum)
            row.update({
                "optimum": optimum,
                "eligible": optimum is not None,
                "rejection_reason": None if optimum is not None else "no_proxy_feasible_time",
                "state_risk": bool(state_risk[formula]),
                "maximum_relative_time_after_fallback": maximum if maximum is not None else 1.8,
                "fallback_triggered": maximum is not None,
            })
            rows.append(row)
        result[strategy] = rows
    return result


def _verify_practical_frozen(practical_root: Path) -> dict[str, Any]:
    if _sha256(practical_root / "protocol.json") != EXPECTED_PRACTICAL_PROTOCOL_SHA256:
        raise S4ValidationError("practical protocol hash mismatch")
    if _sha256(practical_root / "predictions.json") != EXPECTED_PRACTICAL_PREDICTIONS_SHA256:
        raise S4ValidationError("practical predictions hash mismatch")
    marker = _load_json(practical_root / "SELECTION_FROZEN")
    if (
        marker.get("prediction_sha256") != EXPECTED_PRACTICAL_PREDICTIONS_SHA256
        or marker.get("protocol_sha256") != EXPECTED_PRACTICAL_PROTOCOL_SHA256
        or marker.get("phase_a_commit") != EXPECTED_PRACTICAL_PHASE_A_COMMIT
    ):
        raise S4ValidationError("practical selection freeze mismatch")
    return _load_json(practical_root / "predictions.json")


def _load_practical_proxy_points(output_dir: Path) -> dict[tuple[str, str, float], dict[str, Any]]:
    rows: dict[tuple[str, str, float], dict[str, Any]] = {}
    with (output_dir / "practical_proxy_points.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        for raw in csv.DictReader(handle):
            relative = raw.get("relative_to_proxy_t_ana")
            if relative in (None, "", "None"):
                continue
            key = (raw["condition"], raw["formula"], float(relative))
            rows[key] = {
                name: float(value)
                for name, value in raw.items()
                if value not in (None, "", "None")
                and name not in {"condition", "formula", "point_role"}
                and name != "short_grid_index"
            }
            rows[key].update({
                "condition": raw["condition"],
                "formula": raw["formula"],
                "point_role": raw.get("point_role"),
            })
    return rows


def run_phase_a_selector(output_dir: Path) -> dict[str, Any]:
    """Freeze S4 predictions; deliberately accepts no source or truth path."""
    protocol = _protocol()
    practical_predictions = _load_json(output_dir / "practical_predictions.json")
    if _sha256(output_dir / "practical_predictions.json") != EXPECTED_PRACTICAL_PREDICTIONS_SHA256:
        raise S4ValidationError("copied practical predictions hash mismatch")
    practical_proxy_points = _load_practical_proxy_points(output_dir)
    manifest = _load_json(output_dir / "sanitized_input_manifest.json")
    if manifest.get("truth_paths_exposed_to_selector") is not False:
        raise S4ValidationError("truth path barrier not active")
    practical_by_condition = {
        row["condition"]: row for row in practical_predictions["conditions"]
    }
    epsilon = float(protocol["target_error_hartree"])
    diagnostic_spec = protocol["operator_sensitive_diagnostic"]
    sign_spec = diagnostic_spec["sign_noise_floor_hartree"]
    sign_floor = max(
        float(sign_spec["absolute_minimum"]),
        float(sign_spec["target_error_multiplier"]) * epsilon,
    )
    diagnostic_rows: list[dict[str, Any]] = []
    proxy_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    cache_counts = {"computed": 0, "reused": 0}
    started = time.perf_counter()
    for entry in manifest["entries"]:
        condition = entry["condition"]
        if condition not in practical_by_condition:
            raise S4ValidationError(f"missing practical prediction: {condition}")
        system = practical._load_sanitized(output_dir, entry)
        full_state = np.asarray(system["cisd_state"], dtype=np.complex128)
        coarse_state, truncation = truncate_cisd_state(
            full_state, float(protocol["state_pair"]["retained_squared_norm"])
        )
        baseline = practical_by_condition[condition]
        baseline_pf = {row["formula"]: row for row in baseline["pf_predictions"]}
        state_risk: dict[str, bool] = {}
        equal_models: dict[str, dict[str, Any]] = {}
        for formula in FORMULAE:
            source = baseline_pf[formula]
            if not source.get("eligible"):
                raise S4ValidationError(
                    f"S4 requires eligible practical PF prediction: {condition}/{formula}"
                )
            t_ana = float(source["proxy_analytic_time"])
            sequence = practical._formula_sequence(formula)
            by_relative: dict[float, dict[str, Any]] = {}
            full_values: list[float] = []
            coarse_values: list[float] = []
            for relative in diagnostic_spec["relative_times_to_full_cisd_t_ana"]:
                relative = float(relative)
                try:
                    full = practical_proxy_points[(condition, formula, relative)]
                except KeyError as error:
                    raise S4ValidationError(
                        f"missing frozen practical proxy point: {condition}/{formula}/{relative}"
                    ) from error
                if not _same_time(float(full["time"]), relative * t_ana):
                    raise S4ValidationError(
                        f"practical proxy coordinate mismatch: {condition}/{formula}/{relative}"
                    )
                coarse, reused = _state_proxy_cache(
                    output_dir, condition, formula, "truncated_cisd", relative,
                    system, sequence, relative * t_ana, coarse_state,
                    entry["sanitized_sha256"],
                )
                cache_counts["reused" if reused else "computed"] += 1
                by_relative[relative] = full
                full_values.append(float(full["echo_imag_hartree"]))
                coarse_values.append(float(coarse["echo_imag_hartree"]))
                for role, point in (("full_cisd", full), ("truncated_cisd", coarse)):
                    proxy_rows.append({
                        "condition": condition,
                        "formula": formula,
                        "state_role": role,
                        "point_role": "state_convergence_diagnostic",
                        "relative_to_full_cisd_t_ana": relative,
                        **point,
                    })
            risk = assess_state_risk(
                full_values,
                coarse_values,
                epsilon,
                float(diagnostic_spec["risk_threshold"]),
                sign_floor,
            )
            state_risk[formula] = bool(risk["state_risk"])
            diagnostic_rows.append({
                "condition": condition,
                "evaluation_group": baseline["evaluation_group"],
                "formula": formula,
                **truncation,
                **risk,
            })
            fit_relatives = [
                float(value)
                for value in protocol["strategies"]["equal_cost_extra_points"]["fit_relative_times"]
            ]
            fit_points: list[dict[str, Any]] = []
            for relative in fit_relatives:
                if relative in by_relative:
                    point = by_relative[relative]
                else:
                    point, reused = _state_proxy_cache(
                        output_dir, condition, formula, "full_cisd", relative,
                        system, sequence, relative * t_ana, full_state,
                        entry["sanitized_sha256"],
                    )
                    cache_counts["reused" if reused else "computed"] += 1
                    proxy_rows.append({
                        "condition": condition,
                        "formula": formula,
                        "state_role": "full_cisd",
                        "point_role": "equal_cost_extra_training",
                        "relative_to_full_cisd_t_ana": relative,
                        **point,
                    })
                fit_points.append(point)
            equal_models[formula] = _fit_two_term(
                fit_points, t_ana, "echo_imag_7point_equal_cost"
            )
        strategy_pf = _strategy_pf_rows(baseline, state_risk, equal_models)
        strategy_predictions: dict[str, Any] = {}
        for strategy, rows in strategy_pf.items():
            allowed = (
                "current_m3" if strategy == "fixed_current_m3"
                else "yoshida4" if strategy == "fixed_yoshida4"
                else None
            )
            selection = _selection(rows, allowed)
            if strategy in {"practical_baseline", "diagnostic_record_only"}:
                frozen = dict(baseline["selection"])
                for key in ("selected_formula", "selected_time", "predicted_cost", "predicted_error_hartree"):
                    left, right = selection.get(key), frozen.get(key)
                    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                        matched = math.isclose(float(left), float(right), rel_tol=2e-12, abs_tol=1e-14)
                    else:
                        matched = left == right
                    if not matched:
                        raise S4ValidationError(
                            f"base-selector reproduction mismatch: {condition}/{strategy}/{key}"
                        )
                selection = frozen
            selection["additional_proxy_action_count"] = int(
                protocol["strategies"][strategy]["additional_proxy_actions_per_condition_formula"]
                * len(FORMULAE)
            )
            strategy_predictions[strategy] = {
                "pf_predictions": rows,
                "selection": selection,
            }
        condition_rows.append({
            "condition": condition,
            "evaluation_group": baseline["evaluation_group"],
            "truncation": truncation,
            "state_risk_by_formula": state_risk,
            "strategies": strategy_predictions,
        })
    predictions = {
        "schema": "pf_first_study_s4_state_convergence_predictions_v1",
        "created_at": _now(),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "phase_a_commit": _git_head(),
        "practical_predictions_sha256": EXPECTED_PRACTICAL_PREDICTIONS_SHA256,
        "oracle_information_used": False,
        "truth_paths_exposed_to_selector": False,
        "existing_direct_coordinates_used": False,
        "new_direct_truth_point_count": 0,
        "proxy_cache_counts": cache_counts,
        "selector_wall_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "conditions": condition_rows,
    }
    _write_csv(output_dir / "state_diagnostics.csv", diagnostic_rows)
    _write_csv(output_dir / "proxy_points.csv", proxy_rows)
    _write_json(output_dir / "predictions.json", predictions)
    prediction_hash = _sha256(output_dir / "predictions.json")
    (output_dir / "prediction.sha256").write_text(
        f"{prediction_hash}  predictions.json\n", encoding="utf-8"
    )
    marker = {
        "schema": "pf_first_study_s4_phase_a_freeze_v1",
        "frozen_at": _now(),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "prediction_sha256": prediction_hash,
        "phase_a_commit": predictions["phase_a_commit"],
        "truth_opened": False,
    }
    _write_json(output_dir / "PHASE_A_FROZEN", marker)
    return predictions


def run_phase_a(
    project_root: Path,
    practical_root: Path,
    h01_root: Path,
    p03_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Sanitize sources, then call the truth-path-free selector entry point."""
    _prepare_output(output_dir)
    protocol = _protocol()
    shutil.copyfile(PROTOCOL_PATH, output_dir / "protocol.json")
    _verify_practical_frozen(practical_root)
    shutil.copyfile(
        practical_root / "predictions.json", output_dir / "practical_predictions.json"
    )
    shutil.copyfile(
        practical_root / "proxy_points.csv", output_dir / "practical_proxy_points.csv"
    )
    sanitation = practical.sanitize_inputs(h01_root, p03_root, output_dir)
    predictions = run_phase_a_selector(output_dir)
    source_manifest = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "practical_root_absolute": str(practical_root.resolve()),
        "h01_root_absolute": str(h01_root.resolve()),
        "p03_root_absolute": str(p03_root.resolve()),
        "source_checks": sanitation["source_validation"]["checks"],
        "source_records": sanitation["source_validation"]["records"],
        "selector_received_source_paths": False,
        "selector_received_truth_paths": False,
    }
    _write_json(output_dir / "source_manifest.json", source_manifest)
    audit = {
        "status": "selection_frozen",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "prediction_sha256": _sha256(output_dir / "predictions.json"),
        "phase_a_commit": predictions["phase_a_commit"],
        "condition_count": len(predictions["conditions"]),
        "strategy_count": len(STRATEGIES),
        "new_direct_truth_point_count": 0,
        "truth_opened": False,
    }
    _write_json(output_dir / "phase_a_audit.json", audit)
    return audit


def verify_phase_a_freeze(phase_a_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if _sha256(phase_a_root / "protocol.json") != EXPECTED_PROTOCOL_SHA256:
        raise S4ValidationError("frozen S4 protocol hash mismatch")
    marker = _load_json(phase_a_root / "PHASE_A_FROZEN")
    actual = _sha256(phase_a_root / "predictions.json")
    checksum = (phase_a_root / "prediction.sha256").read_text(encoding="utf-8").strip()
    if (
        marker.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256
        or marker.get("prediction_sha256") != actual
        or checksum != f"{actual}  predictions.json"
        or marker.get("truth_opened") is not False
    ):
        raise S4ValidationError("S4 prediction freeze mismatch")
    if not _git_is_ancestor(str(marker["phase_a_commit"]), _git_head()):
        raise S4ValidationError("Phase-B commit is not a descendant of Phase A")
    repository_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    )
    for name in ("protocol.json", "predictions.json", "prediction.sha256", "PHASE_A_FROZEN"):
        path = (phase_a_root / name).resolve()
        try:
            relative = path.relative_to(repository_root)
        except ValueError as error:
            raise S4ValidationError("Phase-A artifact is outside the repository") from error
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(relative)],
            check=False, capture_output=True, text=True,
        )
        if tracked.returncode != 0:
            raise S4ValidationError(f"Phase-A artifact is not committed: {relative}")
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            check=True, capture_output=True,
        ).stdout
        if hashlib.sha256(committed).hexdigest() != _sha256(path):
            raise S4ValidationError(f"Phase-A artifact differs from HEAD: {relative}")
    return marker, _load_json(phase_a_root / "predictions.json")


def _same_time(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=TIME_RTOL, abs_tol=1e-14)


def unique_selected_coordinates(
    predictions: dict[str, Any]
) -> dict[tuple[str, str], list[float]]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for condition_row in predictions["conditions"]:
        condition = str(condition_row["condition"])
        for strategy in STRATEGIES:
            selection = condition_row["strategies"][strategy]["selection"]
            if selection["status"] != "selected":
                continue
            key = (condition, str(selection["selected_formula"]))
            value = float(selection["selected_time"])
            if not any(_same_time(value, old) for old in grouped.setdefault(key, [])):
                grouped[key].append(value)
    for values in grouped.values():
        values.sort()
    return grouped


def _direct_cache_key(
    prediction_sha256: str,
    condition: str,
    formula: str,
    time_value: float,
    backend: str,
    system: dict[str, Any],
) -> dict[str, Any]:
    return {
        "s4_protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "s4_prediction_sha256": prediction_sha256,
        "condition": condition,
        "formula": formula,
        "absolute_time": float(time_value),
        "backend": backend,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
    }


def _compute_direct_point(
    output_dir: Path,
    prediction_sha256: str,
    condition: str,
    formula: str,
    time_value: float,
    backend: str,
    gpu_id: int,
    system: dict[str, Any],
    sequence: Sequence[float],
    rotations: int,
    epsilon: float,
    previous_vector: np.ndarray | None,
    degeneracy_gap: float,
) -> tuple[dict[str, Any], np.ndarray, bool]:
    key = _direct_cache_key(
        prediction_sha256, condition, formula, time_value, backend, system
    )
    digest = hashlib.sha256(
        json.dumps(key, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    root = output_dir / ".runtime/direct_cache" / condition / formula
    point_path = root / f"{digest}.json"
    vector_path = root / f"{digest}.npy"
    if point_path.is_file() and vector_path.is_file():
        cached = _load_json(point_path)
        if cached.get("cache_key") == key and cached.get("selected_vector_sha256") == _sha256(vector_path):
            vector = np.load(vector_path)
            return cached["point"], np.asarray(vector, dtype=np.complex128), True
    started = time.perf_counter()
    unitary, build = (
        diagnosis._build_gpu(system, sequence, float(time_value), int(gpu_id))
        if backend == "gpu"
        else diagnosis._build_cpu(system, sequence, float(time_value))
    )
    point, vector = s0.direct_branch_point(
        unitary,
        np.asarray(system["state"], dtype=np.complex128),
        float(system["energy"]),
        float(time_value),
        rotations,
        epsilon,
        previous_vector,
        degeneracy_gap,
    )
    point["timing_seconds"].update(build)
    point["timing_seconds"]["total"] = float(time.perf_counter() - started)
    point["peak_cpu_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    root.mkdir(parents=True, exist_ok=True)
    temporary = vector_path.with_suffix(".npy.tmp")
    with temporary.open("wb") as handle:
        np.save(handle, vector)
    os.replace(temporary, vector_path)
    _write_json(point_path, {
        "status": "complete",
        "cache_key": key,
        "selected_vector_sha256": _sha256(vector_path),
        "point": point,
    })
    del unitary
    return point, vector, False


def _original_reference(
    h01_root: Path,
    p03_root: Path,
    condition: str,
    epsilon: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    validation = _protocol()["numerical_gates"]
    for formula in FORMULAE:
        points, provenance = s0._source_truth_points(h01_root, p03_root, condition, formula)
        sources.extend({"condition": condition, "formula": formula, **row} for row in provenance)
        rotations = None
        for point in points:
            if rotations is None:
                rotations = int(point.get("rotations", 0)) or None
            error = abs(float(point["signed_direct_shift_hartree"]))
            # Rotation counts are filled by the caller if absent; retain raw truth here.
            rows.append({
                "condition": condition,
                "formula": formula,
                "time": float(point["time"]),
                "error": error,
                "source_point": point,
                "reliable": s0._source_point_reliable(point, validation),
            })
    return {"rows": rows}, sources


def evaluate_benefit(scoring_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_strategy: dict[str, list[dict[str, Any]]] = {
        strategy: [row for row in scoring_rows if row["strategy"] == strategy]
        for strategy in STRATEGIES
    }
    summary: dict[str, dict[str, Any]] = {}
    for strategy, rows in by_strategy.items():
        regrets = [float(row["joint_formula_time_selection_regret"]) for row in rows]
        summary[strategy] = {
            "condition_count": len(rows),
            "unsafe_gamma_1_01_count": sum(not bool(row["success_gamma_1_01"]) for row in rows),
            "primary_coverage": sum(
                row["evaluation_group"] == "primary" for row in rows
            ),
            "mean_regret": float(np.mean(regrets)) if regrets else None,
            "maximum_regret": max(regrets) if regrets else None,
        }
    targeted = summary["state_targeted_fallback"]
    baseline = summary["practical_baseline"]
    targeted_rows = {
        row["condition"]: row for row in by_strategy["state_targeted_fallback"]
    }
    baseline_rows = {
        row["condition"]: row for row in by_strategy["practical_baseline"]
    }
    no_large_condition_loss = all(
        float(targeted_rows[key]["joint_formula_time_selection_regret"])
        - float(baseline_rows[key]["joint_formula_time_selection_regret"])
        <= 0.10
        for key in baseline_rows
    )
    baseline_mean = float(baseline["mean_regret"])
    targeted_mean = float(targeted["mean_regret"])
    efficiency_relative = (
        (baseline_mean - targeted_mean) / abs(baseline_mean)
        if abs(baseline_mean) > np.finfo(float).tiny else -math.inf
    )
    specificity_options: dict[str, Any] = {}
    specificity = False
    for competitor in ("universal_fallback", "equal_cost_extra_points"):
        other = summary[competitor]
        other_mean = float(other["mean_regret"])
        other_max = float(other["maximum_regret"])
        mean_gain = (
            (other_mean - targeted_mean) / abs(other_mean)
            if abs(other_mean) > np.finfo(float).tiny else -math.inf
        )
        target_max = float(targeted["maximum_regret"])
        max_gain = (
            (other_max - target_max) / abs(other_max)
            if abs(other_max) > np.finfo(float).tiny else -math.inf
        )
        passed = bool(mean_gain >= 0.05 or max_gain >= 0.10)
        specificity_options[competitor] = {
            "relative_mean_regret_gain": mean_gain,
            "relative_maximum_regret_gain": max_gain,
            "passed": passed,
        }
        specificity = specificity or passed
    minimum_safety = bool(
        targeted["unsafe_gamma_1_01_count"] == 0
        and targeted["primary_coverage"] == 4
        and targeted["condition_count"] == 6
    )
    efficiency = bool(efficiency_relative >= 0.10 and no_large_condition_loss)
    benefit = bool(minimum_safety and efficiency and specificity)
    return {
        "strategy_summary": summary,
        "minimum_safety": minimum_safety,
        "efficiency_gain": efficiency,
        "efficiency_relative_mean_regret_gain": efficiency_relative,
        "no_condition_regret_increase_over_0p10": no_large_condition_loss,
        "diagnostic_specificity": specificity,
        "specificity_options": specificity_options,
        "outcome_benefit": benefit,
        "outcome": "benefit" if benefit else "no_benefit",
    }


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    return {
        path.name: _sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE"}
    }


def run_phase_b(
    project_root: Path,
    phase_a_root: Path,
    h01_root: Path,
    p03_root: Path,
    output_dir: Path,
    backend: str,
    gpu_id: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    protocol = _protocol()
    marker, predictions = verify_phase_a_freeze(phase_a_root)
    _prepare_output(output_dir)
    shutil.copyfile(PROTOCOL_PATH, output_dir / "protocol.json")
    shutil.copyfile(phase_a_root / "predictions.json", output_dir / "predictions.json")
    shutil.copyfile(phase_a_root / "prediction.sha256", output_dir / "prediction.sha256")
    shutil.copyfile(phase_a_root / "PHASE_A_FROZEN", output_dir / "PHASE_A_FROZEN")
    prediction_hash = str(marker["prediction_sha256"])
    validation = practical.validate_sources(h01_root, p03_root)
    systems = validation["systems"]
    epsilon = float(protocol["target_error_hartree"])
    beta = float(protocol["resource_accounting"]["qpe_beta"])
    gamma = float(protocol["resource_accounting"]["budget_multiplier"])
    gates = protocol["numerical_gates"]
    coordinates = unique_selected_coordinates(predictions)
    if sum(len(values) for values in coordinates.values()) > int(
        protocol["phase_b"]["maximum_unique_selected_coordinates"]
    ):
        raise S4ValidationError("unique selected-coordinate cap exceeded")
    branch_rows: list[dict[str, Any]] = []
    exact_lookup: dict[tuple[str, str], list[dict[str, Any]]] = {}
    source_manifest: list[dict[str, Any]] = []
    cache_reuse_count = 0
    for (condition, formula), selected_times in sorted(coordinates.items()):
        system = systems[condition]
        sequence = practical._formula_sequence(formula)
        rotations = practical._rotation_count(system, sequence)
        source_points, provenance = s0._source_truth_points(
            h01_root, p03_root, condition, formula
        )
        source_manifest.extend(
            {"condition": condition, "formula": formula, **row} for row in provenance
        )
        inserted_times: list[float] = []
        for selected_time in selected_times:
            for factor in TIME_FACTORS:
                value = selected_time * factor
                if not any(_same_time(value, old) for old in inserted_times):
                    inserted_times.append(value)
        inserted_times.sort()
        anchor = s0_v1_1.nearest_lower_h01_native_anchor(
            source_points, inserted_times[0], gates
        )
        anchor_point, previous, reused = _compute_direct_point(
            output_dir, prediction_hash, condition, formula,
            float(anchor["time"]), backend, gpu_id, system, sequence,
            rotations, epsilon, None, float(gates["degenerate_phase_gap_radians"]),
        )
        cache_reuse_count += int(reused)
        anchor_difference = abs(
            float(anchor_point["signed_direct_shift_hartree"])
            - float(anchor["signed_direct_shift_hartree"])
        )
        branch_rows.append({
            "condition": condition,
            "formula": formula,
            "point_role": "h01_native_anchor_recomputation",
            "new_direct_truth_coordinate": False,
            "source_truth_provenance": anchor.get("truth_provenance"),
            "source_signed_direct_shift_hartree": float(anchor["signed_direct_shift_hartree"]),
            "source_reproduction_absolute_difference_hartree": anchor_difference,
            **anchor_point,
        })
        for time_value in inserted_times:
            point, previous, reused = _compute_direct_point(
                output_dir, prediction_hash, condition, formula, time_value,
                backend, gpu_id, system, sequence, rotations, epsilon, previous,
                float(gates["degenerate_phase_gap_radians"]),
            )
            cache_reuse_count += int(reused)
            branch_rows.append({
                "condition": condition,
                "formula": formula,
                "point_role": "inserted_exact_time_triplet",
                "new_direct_truth_coordinate": True,
                "source_truth_provenance": None,
                "source_signed_direct_shift_hartree": None,
                "source_reproduction_absolute_difference_hartree": None,
                **point,
            })
            exact_lookup.setdefault((condition, formula), []).append(point)
    condition_predictions = {
        row["condition"]: row for row in predictions["conditions"]
    }
    scoring_rows: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []
    for condition in _conditions(protocol):
        system = systems[condition]
        original_candidates: list[dict[str, Any]] = []
        for formula in FORMULAE:
            sequence = practical._formula_sequence(formula)
            rotations = practical._rotation_count(system, sequence)
            source_points, _ = s0._source_truth_points(
                h01_root, p03_root, condition, formula
            )
            for point in source_points:
                error = abs(float(point["signed_direct_shift_hartree"]))
                cost = practical._cost(float(point["time"]), error, rotations, epsilon)
                if cost is not None and s0._source_point_reliable(point, gates):
                    original_candidates.append({
                        "formula": formula, "time": float(point["time"]),
                        "cost": float(cost), "error": error,
                    })
        if not original_candidates:
            raise S4ValidationError(f"no feasible original reference: {condition}")
        original_best = min(original_candidates, key=lambda row: row["cost"])
        inserted_candidates = [
            {
                "formula": row["formula"], "time": float(row["time"]),
                "cost": float(row["direct_cost"]),
                "error": float(row["direct_error_hartree"]),
            }
            for row in branch_rows
            if row["condition"] == condition
            and row["point_role"] == "inserted_exact_time_triplet"
            and row["direct_cost"] is not None
        ]
        extended_best = min(
            original_candidates + inserted_candidates, key=lambda row: row["cost"]
        )
        reference_rows.extend([
            {"condition": condition, "reference": "original_two_pf_saved_grid", **original_best},
            {"condition": condition, "reference": "expanded_with_inserted_points", **extended_best},
        ])
        condition_row = condition_predictions[condition]
        for strategy in STRATEGIES:
            selection = condition_row["strategies"][strategy]["selection"]
            if selection["status"] != "selected":
                raise S4ValidationError(f"unscorable abstention: {condition}/{strategy}")
            formula = str(selection["selected_formula"])
            selected_time = float(selection["selected_time"])
            matching = [
                point for point in exact_lookup[(condition, formula)]
                if _same_time(float(point["time"]), selected_time)
            ]
            if len(matching) != 1:
                raise S4ValidationError(
                    f"exact-time lookup is not unique: {condition}/{strategy}"
                )
            exact = matching[0]
            direct_cost = exact["direct_cost"]
            if direct_cost is None:
                raise S4ValidationError(f"infeasible exact-time point: {condition}/{strategy}")
            rotations = practical._rotation_count(
                system, practical._formula_sequence(formula)
            )
            predicted_cost = float(selection["predicted_cost"])
            budget = gamma * predicted_cost
            phase_error = beta * rotations / (selected_time * budget)
            margin = epsilon - float(exact["direct_error_hartree"]) - phase_error
            scoring_rows.append({
                "condition": condition,
                "evaluation_group": condition_row["evaluation_group"],
                "strategy": strategy,
                "selected_formula": formula,
                "selected_time": selected_time,
                "predicted_cost": predicted_cost,
                "predicted_error_hartree": float(selection["predicted_error_hartree"]),
                "additional_proxy_action_count": int(selection["additional_proxy_action_count"]),
                "exact_time_direct_signed_shift_hartree": float(exact["signed_direct_shift_hartree"]),
                "exact_time_direct_error_hartree": float(exact["direct_error_hartree"]),
                "exact_time_direct_cost": float(direct_cost),
                "original_joint_grid_best_formula": original_best["formula"],
                "original_joint_grid_best_time": original_best["time"],
                "original_joint_grid_best_cost": original_best["cost"],
                "expanded_grid_best_formula": extended_best["formula"],
                "expanded_grid_best_time": extended_best["time"],
                "expanded_grid_best_cost": extended_best["cost"],
                "joint_formula_time_selection_regret": float(direct_cost) / float(original_best["cost"]) - 1.0,
                "expanded_grid_joint_regret": float(direct_cost) / float(extended_best["cost"]) - 1.0,
                "frozen_budget_gamma_1_01": budget,
                "phase_estimation_error_gamma_1_01_hartree": phase_error,
                "energy_margin_gamma_1_01_hartree": margin,
                "success_gamma_1_01": margin >= 0.0,
            })
    anchor_rows = [row for row in branch_rows if row["point_role"] == "h01_native_anchor_recomputation"]
    inserted_rows = [row for row in branch_rows if row["point_role"] == "inserted_exact_time_triplet"]
    checks = {
        "protocol_hash_match": _sha256(output_dir / "protocol.json") == EXPECTED_PROTOCOL_SHA256,
        "prediction_hash_unchanged": _sha256(output_dir / "predictions.json") == prediction_hash,
        "all_six_conditions_scored_for_all_strategies": len(scoring_rows) == 6 * len(STRATEGIES),
        "new_direct_coordinate_cap": len(inserted_rows) <= int(protocol["phase_b"]["maximum_new_direct_truth_coordinates"]),
        "anchor_recomputation_cap": len(anchor_rows) <= int(protocol["phase_b"]["maximum_anchor_recomputations"]),
        "all_anchors_h01_native": all(row["source_truth_provenance"] == protocol["source_identity"]["required_h01_truth_provenance_for_anchor"] for row in anchor_rows),
        "anchor_shift_reproduction_passed": max(row["source_reproduction_absolute_difference_hartree"] for row in anchor_rows) <= float(gates["anchor_shift_absolute_tolerance_hartree"]),
        "all_eigenpair_residuals_passed": max(row["eigenpair_residual_2_norm"] for row in branch_rows) <= float(gates["direct_eigenpair_residual_2_norm"]),
        "all_unitarity_residuals_passed": max(row["unitarity_residual_frobenius"] for row in branch_rows) <= float(gates["pf_unitarity_frobenius"]),
        "all_inserted_previous_overlaps_passed": min(row["previous_branch_overlap_probability"] for row in inserted_rows) >= float(gates["branch_warning_previous_overlap_below"]),
        "all_inserted_ground_overlaps_passed": min(row["ground_state_overlap_probability"] for row in inserted_rows) >= float(gates["branch_warning_ground_overlap_below"]),
        "all_inserted_phase_gaps_resolved": min(row["minimum_selected_phase_gap_radians"] for row in inserted_rows) > float(gates["degenerate_phase_gap_radians"]),
    }
    decision = evaluate_benefit(scoring_rows) if all(checks.values()) else {
        "outcome": "inconclusive", "outcome_benefit": False,
    }
    status = (
        "failed_numerical_validation" if not all(checks.values())
        else "complete_with_benefit" if decision["outcome_benefit"]
        else "complete_no_benefit"
    )
    _write_csv(output_dir / "branch_audit.csv", branch_rows)
    _write_csv(output_dir / "strategy_scoring.csv", scoring_rows)
    _write_csv(output_dir / "reference_costs.csv", reference_rows)
    _write_json(output_dir / "decision.json", decision)
    source_payload = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "prediction_sha256": prediction_hash,
        "phase_a_commit": marker["phase_a_commit"],
        "h01_root_absolute": str(h01_root.resolve()),
        "p03_root_absolute": str(p03_root.resolve()),
        "source_checks": validation["checks"],
        "source_records": validation["records"],
        "truth_files": source_manifest,
    }
    _write_json(output_dir / "source_manifest.json", source_payload)
    audit = {
        "status": status,
        "created_at": _now(),
        "execution_commit": _git_head(),
        "backend": backend,
        "gpu_id": int(gpu_id) if backend == "gpu" else None,
        "checks": checks,
        "decision": decision,
        "accounting": {
            "unique_selected_coordinate_count": sum(len(values) for values in coordinates.values()),
            "new_direct_truth_coordinate_count": len(inserted_rows),
            "anchor_recomputation_count": len(anchor_rows),
            "cache_reuse_count": cache_reuse_count,
            "strategy_scoring_row_count": len(scoring_rows),
        },
        "extrema": {
            "maximum_anchor_difference_hartree": max(row["source_reproduction_absolute_difference_hartree"] for row in anchor_rows),
            "maximum_eigenpair_residual_2_norm": max(row["eigenpair_residual_2_norm"] for row in branch_rows),
            "maximum_unitarity_residual_frobenius": max(row["unitarity_residual_frobenius"] for row in branch_rows),
            "minimum_previous_branch_overlap": min(row["previous_branch_overlap_probability"] for row in inserted_rows),
            "minimum_ground_state_overlap": min(row["ground_state_overlap_probability"] for row in inserted_rows),
            "minimum_phase_gap_radians": min(row["minimum_selected_phase_gap_radians"] for row in inserted_rows),
        },
        "runtime": {
            "wall_seconds": float(time.perf_counter() - started),
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
    }
    _write_json(output_dir / "audit.json", audit)
    targeted = decision.get("strategy_summary", {}).get("state_targeted_fallback", {})
    lines = [
        "# First-study S4 state-convergence diagnostic",
        "",
        f"Status: **{status}**",
        "",
        "This is a fixed development comparison, not an independent holdout.",
        "The truncated/full-CISD disagreement is a local CISD-tail diagnostic and not a rigorous exact-state error bound.",
        "",
        f"- Frozen prediction SHA-256: `{prediction_hash}`.",
        f"- New direct truth coordinates: {len(inserted_rows)}.",
        f"- H01-native anchor recomputations: {len(anchor_rows)}.",
        f"- Decision: **{decision.get('outcome')}**.",
        f"- Targeted gamma=1.01 unsafe count: {targeted.get('unsafe_gamma_1_01_count')}.",
        f"- Targeted mean original-grid regret: {targeted.get('mean_regret')}.",
        "",
        "S5 is permitted only when the fixed S4 outcome is benefit.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "status": status,
        "created_at": _now(),
        "execution_commit": _git_head(),
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "prediction_sha256": prediction_hash,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "artifact_sha256": _artifact_hashes(output_dir),
    }
    _write_json(output_dir / "manifest.json", manifest)
    if status.startswith("complete_"):
        (output_dir / "COMPLETE").touch(exist_ok=False)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    phase_a = subparsers.add_parser("phase-a")
    phase_a.add_argument("--project-root", type=Path, required=True)
    phase_a.add_argument("--practical-root", type=Path, required=True)
    phase_a.add_argument("--h01-root", type=Path, required=True)
    phase_a.add_argument("--p03-root", type=Path, required=True)
    phase_a.add_argument("--output", type=Path, required=True)
    phase_b = subparsers.add_parser("phase-b")
    phase_b.add_argument("--project-root", type=Path, required=True)
    phase_b.add_argument("--phase-a-root", type=Path, required=True)
    phase_b.add_argument("--h01-root", type=Path, required=True)
    phase_b.add_argument("--p03-root", type=Path, required=True)
    phase_b.add_argument("--output", type=Path, required=True)
    phase_b.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    phase_b.add_argument("--gpu-id", type=int, default=0)
    args = parser.parse_args()
    if args.command == "phase-a":
        result = run_phase_a(
            args.project_root.resolve(), args.practical_root.resolve(),
            args.h01_root.resolve(), args.p03_root.resolve(), args.output.resolve(),
        )
    else:
        result = run_phase_b(
            args.project_root.resolve(), args.phase_a_root.resolve(),
            args.h01_root.resolve(), args.p03_root.resolve(), args.output.resolve(),
            args.backend, args.gpu_id,
        )
    print(json.dumps(_jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
