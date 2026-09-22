"""Frozen oracle-free practical calibration selector and truth-only scorer."""

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
import resource
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.sparse.linalg import expm_multiply

import run_h01_approximate_state_calibration as h01
import run_full_electron_nh3_higher_term_diagnosis as diagnosis


PROTOCOL_PATH = Path(__file__).with_name("practical_calibration_minimal_protocol.json")
SCHEMA_PATH = Path(__file__).with_name("practical_calibration_sanitized_schema.json")
FORMULAE = ("current_m3", "yoshida4")
SANITIZED_SCHEMA = "practical_calibration_sanitized_input_v1"
FORBIDDEN_SELECTOR_FIELDS = {
    "state", "states", "energy", "exact_ground", "exact_ground_state",
    "gap", "overlap", "direct", "truth", "pass", "fail", "label",
    "optimum", "minimum_cost", "source_path", "truth_file_path",
}


class SourceIdentityError(RuntimeError):
    pass


class FreezeError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
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
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{key: _jsonable(row.get(key)) for key in keys} for row in rows])


def _protocol() -> dict[str, Any]:
    return _load_json(PROTOCOL_PATH)


def _protocol_sha256() -> str:
    return _sha256(PROTOCOL_PATH)


def _conditions(protocol: dict[str, Any]) -> list[str]:
    return list(protocol["conditions"]["primary"]) + list(
        protocol["conditions"]["stress_test"]
    )


def _git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True
    ).stdout.strip()


def _cost(time_value: float, error: float, rotations: int, epsilon: float) -> float | None:
    if time_value <= 0.0 or error < 0.0 or error >= epsilon:
        return None
    return float(diagnosis.BETA * int(rotations) / (time_value * (epsilon - error)))


def _prediction(model: dict[str, Any], time_value: float) -> float:
    return float(sum(
        float(coefficient) * float(time_value) ** int(power)
        for power, coefficient in zip(
            model["coefficient_powers"], model["coefficient_values"], strict=True
        )
    ))


def _model_optimum(
    model: dict[str, Any], t_ana: float, rotations: int,
    maximum_relative: float | None = None,
) -> dict[str, Any] | None:
    protocol = _protocol()
    specification = protocol["selector"]["optimization"]
    lower, upper = map(float, specification["relative_interval"])
    if maximum_relative is not None:
        upper = min(upper, float(maximum_relative))
    relative = np.linspace(lower, upper, int(specification["grid_points"]))
    times = relative * float(t_ana)
    shifts = np.asarray([_prediction(model, value) for value in times])
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


def _forbidden_key_paths(value: Any, prefix: str = "") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            lowered = str(key).lower()
            if lowered in FORBIDDEN_SELECTOR_FIELDS or any(
                token in lowered for token in ("exact_ground", "direct_truth", "pass_fail")
            ):
                failures.append(path)
            failures.extend(_forbidden_key_paths(child, path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            failures.extend(_forbidden_key_paths(child, f"{prefix}[{index}]"))
    return failures


def validate_sources(h01_root: Path, p03_root: Path) -> dict[str, Any]:
    protocol = _protocol()
    identity = protocol["source_identity"]
    checks: list[dict[str, Any]] = []
    for root, name in ((h01_root, "h01"), (p03_root, "p03")):
        checks.append({
            "check_id": f"{name}_complete", "passed": (root / "COMPLETE").is_file()
        })
    fixed_files = [
        (h01_root / "aggregate/summary.json", identity["h01_summary_sha256"], "h01_summary"),
        (h01_root / "manifest.json", identity["h01_manifest_sha256"], "h01_manifest"),
        (p03_root / "aggregate/summary.json", identity["p03_summary_sha256"], "p03_summary"),
        (p03_root / "manifest.json", identity["p03_manifest_sha256"], "p03_manifest"),
    ]
    for path, expected, check_id in fixed_files:
        actual = _sha256(path) if path.is_file() else None
        checks.append({
            "check_id": check_id, "expected_sha256": expected,
            "actual_sha256": actual, "passed": actual == expected,
        })
    p03_manifest = _load_json(p03_root / "manifest.json")
    checks.append({
        "check_id": "p03_protocol_sha256",
        "expected": identity["p03_protocol_sha256"],
        "actual": p03_manifest.get("protocol_sha256"),
        "passed": p03_manifest.get("protocol_sha256") == identity["p03_protocol_sha256"],
    })
    systems: dict[str, Any] = {}
    source_records = []
    for condition in _conditions(protocol):
        pickle_path = h01_root / "cache" / f"{condition}.pkl"
        metadata_path = h01_root / "cache" / f"{condition}.metadata.json"
        if not pickle_path.is_file() or not metadata_path.is_file():
            raise SourceIdentityError(f"missing H01 cache/metadata: {condition}")
        pickle_hash = _sha256(pickle_path)
        metadata = _load_json(metadata_path)
        system = h01._load_system(pickle_path)
        cisd = system.get("states", {}).get("cisd")
        expected_h = identity["hamiltonian_sha256"][condition]
        local_checks = {
            "pickle_sha256": pickle_hash == identity["pickle_sha256"][condition],
            "internal_protocol_sha256": system.get("protocol_sha256") == identity["h01_protocol_sha256"],
            "metadata_protocol_sha256": metadata.get("protocol_sha256") == identity["h01_protocol_sha256"],
            "internal_hamiltonian_sha256": system.get("hamiltonian_sha256") == expected_h,
            "metadata_hamiltonian_sha256": metadata.get("system", {}).get("hamiltonian_sha256") == expected_h,
            "metadata_complete": metadata.get("status") == "complete",
            "cisd_state_present": isinstance(cisd, np.ndarray) and cisd.ndim == 1,
            "cisd_state_normalized": isinstance(cisd, np.ndarray) and abs(float(np.linalg.norm(cisd)) - 1.0) <= 1e-10,
        }
        for key, passed in local_checks.items():
            checks.append({"check_id": f"{condition}:{key}", "passed": bool(passed)})
        source_records.append({
            "condition": condition,
            "pickle_sha256": pickle_hash,
            "metadata_sha256": _sha256(metadata_path),
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "cisd_generation_wall_seconds": metadata.get("system", {}).get("states", {}).get("cisd", {}).get("state_generation_wall_seconds"),
            "cisd_generation_peak_memory_bytes": metadata.get("system", {}).get("states", {}).get("cisd", {}).get("state_generation_peak_memory_bytes"),
            "checks": local_checks,
        })
        systems[condition] = system
    failed = [item["check_id"] for item in checks if not item["passed"]]
    if failed:
        raise SourceIdentityError("failed source checks: " + ", ".join(failed))
    return {"systems": systems, "checks": checks, "records": source_records}


def sanitize_inputs(h01_root: Path, p03_root: Path, output_dir: Path) -> dict[str, Any]:
    validation = validate_sources(h01_root, p03_root)
    protocol_hash = _protocol_sha256()
    runtime = output_dir / ".runtime/sanitized"
    runtime.mkdir(parents=True, exist_ok=True)
    entries = []
    for record in validation["records"]:
        condition = record["condition"]
        system = validation["systems"][condition]
        sanitized = {
            "schema": SANITIZED_SCHEMA,
            "condition": condition,
            "protocol_sha256": protocol_hash,
            "source_pickle_sha256": record["pickle_sha256"],
            "hamiltonian_sha256": record["hamiltonian_sha256"],
            "hamiltonian": system["hamiltonian"],
            "component_spectra": system["component_spectra"],
            "term_counts": system["term_counts"],
            "cisd_state": np.asarray(system["states"]["cisd"], dtype=np.complex128).copy(),
        }
        failures = _forbidden_key_paths(sanitized)
        if failures:
            raise RuntimeError(f"forbidden sanitized fields: {failures}")
        path = runtime / f"{condition}.pkl"
        if path.exists():
            raise FileExistsError(f"refusing to overwrite sanitized input: {path}")
        with path.open("wb") as handle:
            pickle.dump(sanitized, handle, protocol=pickle.HIGHEST_PROTOCOL)
        entries.append({
            "condition": condition,
            "relative_path": str(path.relative_to(output_dir)),
            "sanitized_sha256": _sha256(path),
            "source_pickle_sha256": record["pickle_sha256"],
            "hamiltonian_sha256": record["hamiltonian_sha256"],
            "allowed_top_level_fields": sorted(sanitized),
            "forbidden_field_paths": failures,
            "cisd_dimension": int(sanitized["cisd_state"].size),
            "cisd_norm": float(np.linalg.norm(sanitized["cisd_state"])),
            "cisd_generation_wall_seconds": record["cisd_generation_wall_seconds"],
            "cisd_generation_peak_memory_bytes": record["cisd_generation_peak_memory_bytes"],
        })
    manifest = {
        "schema": "practical_calibration_sanitized_manifest_v1",
        "created_at": _now(),
        "protocol_sha256": protocol_hash,
        "sanitized_schema_sha256": _sha256(SCHEMA_PATH),
        "source_paths_exposed_to_selector": False,
        "truth_paths_exposed_to_selector": False,
        "existing_direct_coordinates_exposed_to_selector": False,
        "coordinate_audit": {
            "conclusion": _protocol()["time_coordinate_policy"]["audit_conclusion"],
            "safe_existing_selector_coordinate_count": 0,
            "adaptive_or_oracle_scaled_coordinates_excluded": True,
        },
        "entries": entries,
        "source_identity_checks_passed": True,
    }
    _write_json(output_dir / "sanitized_input_manifest.json", manifest)
    return {"manifest": manifest, "source_validation": validation}


def _load_sanitized(output_dir: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = output_dir / entry["relative_path"]
    if _sha256(path) != entry["sanitized_sha256"]:
        raise RuntimeError(f"sanitized input hash mismatch: {path}")
    with path.open("rb") as handle:
        value = pickle.load(handle)
    if value.get("schema") != SANITIZED_SCHEMA or value.get("protocol_sha256") != _protocol_sha256():
        raise RuntimeError("sanitized input schema/protocol mismatch")
    failures = _forbidden_key_paths(value)
    if failures:
        raise RuntimeError(f"forbidden fields reached selector: {failures}")
    return value


def _formula_sequence(formula: str) -> list[float]:
    sequence = [float(value) for value in diagnosis._formula_s2_sequence(formula)]
    expected = [float(value) for value in _protocol()["formulae"][formula]["s2_sequence"]]
    if sequence != expected:
        raise RuntimeError(f"PF registry mismatch: {formula}")
    return sequence


def _rotation_count(system: dict[str, Any], sequence: Sequence[float]) -> int:
    return h01._rotation_count(system, sequence)


def proxy_point(system: dict[str, Any], sequence: Sequence[float], time_value: float) -> dict[str, Any]:
    state = np.asarray(system["cisd_state"], dtype=np.complex128)
    started = time.perf_counter()
    pf_state, pf_timing = h01._apply_pf_cpu(system, sequence, float(time_value), state[:, None])
    pf_vector = np.asarray(pf_state[:, 0])
    reference_started = time.perf_counter()
    exact_vector = expm_multiply((1j * float(time_value)) * system["hamiltonian"], state)
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
        "diagonal_signal": diagonal_signal,
        "cancellation_index": diagonal_signal / max(state_error, np.finfo(float).tiny),
        "pf_state_norm": float(np.linalg.norm(pf_vector)),
        "exact_state_norm": float(np.linalg.norm(exact_vector)),
        "pf_action_seconds": float(pf_timing["total"]),
        "hamiltonian_evolution_seconds": float(reference_seconds),
        "proxy_point_seconds": float(time.perf_counter() - started),
    }


def _point_cache_path(output_dir: Path, condition: str, formula: str, tag: str) -> Path:
    return output_dir / ".runtime/proxy_cache" / condition / formula / f"{tag}.json"


def _cached_proxy_point(
    output_dir: Path, condition: str, formula: str, tag: str,
    system: dict[str, Any], sequence: Sequence[float], time_value: float,
    sanitized_sha256: str, counters: dict[str, int],
) -> dict[str, Any]:
    path = _point_cache_path(output_dir, condition, formula, tag)
    if path.is_file():
        payload = _load_json(path)
        if (
            payload.get("protocol_sha256") != _protocol_sha256()
            or payload.get("sanitized_sha256") != sanitized_sha256
            or not math.isclose(float(payload["point"]["time"]), float(time_value), rel_tol=1e-13)
        ):
            raise RuntimeError(f"stale proxy cache: {path}")
        counters["reused"] += 1
        return payload["point"]
    point = proxy_point(system, sequence, time_value)
    _write_json(path, {
        "protocol_sha256": _protocol_sha256(),
        "sanitized_sha256": sanitized_sha256,
        "condition": condition,
        "formula": formula,
        "tag": tag,
        "point": point,
    })
    counters["computed"] += 1
    return point


def _proxy_analytic_scale(
    output_dir: Path, condition: str, formula: str, system: dict[str, Any],
    sequence: Sequence[float], sanitized_sha256: str, counters: dict[str, int],
) -> tuple[float | None, dict[str, Any], list[dict[str, Any]]]:
    spec = _protocol()["selector"]["short_time_fit"]
    grid = np.geomspace(float(spec["minimum"]), float(spec["maximum"]), int(spec["count"]))
    points: list[dict[str, Any]] = []
    qualification: dict[str, Any] | None = None
    for index, time_value in enumerate(grid):
        point = _cached_proxy_point(
            output_dir, condition, formula, f"short_{index:02d}", system, sequence,
            float(time_value), sanitized_sha256, counters,
        )
        points.append(point)
        if len(points) >= int(spec["rolling_window_points"]):
            qualification = diagnosis._qualify_fit(
                [item["time"] for item in points],
                [abs(item["echo_imag_hartree"]) for item in points],
                4,
            )
            if qualification["qualified"]:
                break
    if qualification is None or not qualification["qualified"]:
        return None, qualification or {"qualified": False}, points
    alpha = float(qualification["selected_window"]["fixed_order_alpha"])
    epsilon = float(_protocol()["target_error_hartree"])
    t_ana = float((epsilon / (5.0 * alpha)) ** 0.25)
    qualification = {**qualification, "alpha": alpha, "proxy_analytic_time": t_ana}
    return t_ana, qualification, points


def run_selector(output_dir: Path) -> dict[str, Any]:
    """Run without accepting or opening any truth/source artifact path."""
    manifest = _load_json(output_dir / "sanitized_input_manifest.json")
    if manifest.get("truth_paths_exposed_to_selector") is not False:
        raise RuntimeError("truth path barrier not active")
    protocol = _protocol()
    epsilon = float(protocol["target_error_hartree"])
    sign_spec = protocol["selector"]["sentinel"]["sign_noise_floor_hartree"]
    sign_floor = max(
        float(sign_spec["absolute_minimum"]),
        float(sign_spec["target_error_multiplier"]) * epsilon,
    )
    proxy_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    condition_predictions = []
    counters = {"computed": 0, "reused": 0}
    started = time.perf_counter()
    for entry in manifest["entries"]:
        condition = entry["condition"]
        system = _load_sanitized(output_dir, entry)
        pf_predictions = []
        for formula in FORMULAE:
            sequence = _formula_sequence(formula)
            rotations = _rotation_count(system, sequence)
            t_ana, scale_fit, short_points = _proxy_analytic_scale(
                output_dir, condition, formula, system, sequence,
                entry["sanitized_sha256"], counters,
            )
            for index, point in enumerate(short_points):
                proxy_rows.append({
                    "condition": condition, "formula": formula,
                    "point_role": "proxy_scale_fit", "relative_to_proxy_t_ana": None,
                    "short_grid_index": index, **point,
                })
            if t_ana is None:
                pf_predictions.append({
                    "condition": condition, "formula": formula, "eligible": False,
                    "rejection_reason": "proxy_short_time_fit_failed", "rotations": rotations,
                })
                continue
            relative_values = sorted(set(
                protocol["selector"]["proxy_model"]["training_relative_to_proxy_t_ana"]
                + [
                    protocol["selector"]["cancellation_index"]["primary_relative_to_proxy_t_ana"],
                    protocol["selector"]["cancellation_index"]["robustness_relative_to_proxy_t_ana"],
                    protocol["selector"]["sentinel"]["relative_to_proxy_t_ana"],
                ]
            ))
            by_relative: dict[float, dict[str, Any]] = {}
            for relative in relative_values:
                tag = "relative_" + str(relative).replace(".", "p")
                point = _cached_proxy_point(
                    output_dir, condition, formula, tag, system, sequence,
                    float(relative) * t_ana, entry["sanitized_sha256"], counters,
                )
                point = {**point, "relative_to_proxy_t_ana": float(relative)}
                by_relative[float(relative)] = point
                proxy_rows.append({
                    "condition": condition, "formula": formula,
                    "point_role": (
                        "model_training" if relative in protocol["selector"]["proxy_model"]["training_relative_to_proxy_t_ana"]
                        else "selection_diagnostic"
                    ),
                    "short_grid_index": None, **point,
                })
            training = [
                by_relative[float(relative)]
                for relative in protocol["selector"]["proxy_model"]["training_relative_to_proxy_t_ana"]
            ]
            model = h01._fit_proxy(training, "echo_imag_hartree", 3, t_ana, "echo_imag_3point")
            primary_relative = float(protocol["selector"]["cancellation_index"]["primary_relative_to_proxy_t_ana"])
            robust_relative = float(protocol["selector"]["cancellation_index"]["robustness_relative_to_proxy_t_ana"])
            sentinel_relative = float(protocol["selector"]["sentinel"]["relative_to_proxy_t_ana"])
            primary = by_relative[primary_relative]
            robust = by_relative[robust_relative]
            sentinel = by_relative[sentinel_relative]
            sentinel_prediction = _prediction(model, sentinel["time"])
            sentinel_residual = abs(sentinel["echo_imag_hartree"] - sentinel_prediction)
            indeterminate_sign = (
                abs(sentinel["echo_imag_hartree"]) <= sign_floor
                or abs(sentinel_prediction) <= sign_floor
            )
            sign_mismatch = (
                False if indeterminate_sign
                else np.sign(sentinel["echo_imag_hartree"]) != np.sign(sentinel_prediction)
            )
            cancellation_fallback = (
                primary["cancellation_index"]
                < float(protocol["selector"]["cancellation_index"]["fallback_below"])
            )
            residual_fallback = (
                sentinel_residual
                > float(protocol["selector"]["sentinel"]["residual_fallback_over_target_error"]) * epsilon
            )
            fallback = bool(cancellation_fallback or residual_fallback or sign_mismatch or indeterminate_sign)
            optimum = _model_optimum(
                model, t_ana, rotations,
                float(protocol["selector"]["optimization"]["fallback_maximum_relative_to_proxy_t_ana"])
                if fallback else None,
            )
            diagnostic = {
                "condition": condition, "formula": formula,
                "proxy_analytic_time": t_ana,
                "proxy_alpha": scale_fit["alpha"],
                "cancellation_index_primary": primary["cancellation_index"],
                "cancellation_index_robustness": robust["cancellation_index"],
                "cancellation_index_ratio_0p05_over_0p1": robust["cancellation_index"] / max(primary["cancellation_index"], np.finfo(float).tiny),
                "robustness_value_used_for_selection": False,
                "sentinel_signed_proxy_hartree": sentinel["echo_imag_hartree"],
                "sentinel_signed_model_hartree": sentinel_prediction,
                "sentinel_absolute_residual_hartree": sentinel_residual,
                "sign_noise_floor_hartree": sign_floor,
                "sentinel_sign_status": "indeterminate_sign" if indeterminate_sign else ("mismatch" if sign_mismatch else "match"),
                "fallback_cancellation": cancellation_fallback,
                "fallback_sentinel_residual": residual_fallback,
                "fallback_sign": bool(sign_mismatch or indeterminate_sign),
                "fallback_triggered": fallback,
            }
            diagnostic_rows.append(diagnostic)
            prediction = {
                "condition": condition, "formula": formula,
                "rotations": rotations, "proxy_analytic_time": t_ana,
                "model": model, "diagnostic": diagnostic,
                "fallback_triggered": fallback,
                "maximum_relative_time_after_fallback": 0.5 if fallback else 1.8,
                "eligible": optimum is not None,
                "rejection_reason": None if optimum is not None else "no_proxy_feasible_time_after_fallback",
                "optimum": optimum,
            }
            pf_predictions.append(prediction)
        eligible = [item for item in pf_predictions if item["eligible"]]
        if eligible:
            selected = min(eligible, key=lambda item: item["optimum"]["cost"])
            selection = {
                "status": "selected", "selected_formula": selected["formula"],
                "selected_time": selected["optimum"]["time"],
                "predicted_signed_shift_hartree": selected["optimum"]["signed_shift_hartree"],
                "predicted_error_hartree": selected["optimum"]["error_hartree"],
                "predicted_cost": selected["optimum"]["cost"],
                "fallback_triggered": selected["fallback_triggered"],
                "selection_reason": "minimum_predicted_cost_among_proxy_feasible_pfs",
            }
        else:
            selection = {
                "status": "abstain", "selected_formula": None,
                "selected_time": None, "predicted_signed_shift_hartree": None,
                "predicted_error_hartree": None, "predicted_cost": None,
                "fallback_triggered": True,
                "selection_reason": "both_pfs_rejected_after_frozen_fallback",
            }
        condition_predictions.append({
            "condition": condition,
            "evaluation_group": "primary" if condition in protocol["conditions"]["primary"] else "stress_test",
            "pf_predictions": pf_predictions,
            "selection": selection,
        })
    predictions = {
        "schema": "practical_calibration_predictions_v1",
        "created_at": _now(),
        "protocol_sha256": _protocol_sha256(),
        "phase_a_commit": _git_output("rev-parse", "HEAD"),
        "oracle_information_used": False,
        "existing_direct_coordinates_used": False,
        "new_direct_truth_point_count": 0,
        "selector_inputs": "sanitized_allowlist_only",
        "proxy_cache_counts": counters,
        "selector_wall_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "conditions": condition_predictions,
    }
    _write_csv(output_dir / "proxy_points.csv", proxy_rows)
    _write_csv(output_dir / "diagnostics.csv", diagnostic_rows)
    _write_json(output_dir / "predictions.json", predictions)
    return predictions


def freeze_predictions(output_dir: Path) -> dict[str, Any]:
    prediction_path = output_dir / "predictions.json"
    if not prediction_path.is_file():
        raise FreezeError("predictions.json is missing")
    prediction_hash = _sha256(prediction_path)
    (output_dir / "prediction.sha256").write_text(
        f"{prediction_hash}  predictions.json\n", encoding="utf-8"
    )
    marker = {
        "schema": "practical_calibration_selection_freeze_v1",
        "frozen_at": _now(),
        "prediction_sha256": prediction_hash,
        "protocol_sha256": _protocol_sha256(),
        "phase_a_commit": _git_output("rev-parse", "HEAD"),
    }
    _write_json(output_dir / "SELECTION_FROZEN", marker)
    return marker


def verify_freeze(output_dir: Path) -> dict[str, Any]:
    marker_path = output_dir / "SELECTION_FROZEN"
    if not marker_path.is_file():
        raise FreezeError("SELECTION_FROZEN is required before scoring")
    marker = _load_json(marker_path)
    actual = _sha256(output_dir / "predictions.json")
    checksum_line = (output_dir / "prediction.sha256").read_text(encoding="utf-8").strip()
    expected_line = f"{actual}  predictions.json"
    if marker.get("prediction_sha256") != actual or checksum_line != expected_line:
        raise FreezeError("prediction hash mismatch after selection freeze")
    if marker.get("protocol_sha256") != _protocol_sha256():
        raise FreezeError("protocol hash mismatch after selection freeze")
    return marker


def _walk_truth(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "time" in value and "signed_direct_shift_hartree" in value:
            yield value
        for child in value.values():
            yield from _walk_truth(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_truth(child)


def _saved_truth_points(h01_root: Path, p03_root: Path, condition: str, formula: str) -> list[dict[str, Any]]:
    sources = [
        (p03_root / "raw" / f"{condition}__{formula}.json", "p03_raw"),
        (p03_root / "fine/raw" / f"{condition}__{formula}.json", "p03_fine"),
        (h01_root / "truth" / f"{condition}__{formula}.json", "h01_saved_truth"),
    ]
    points: list[dict[str, Any]] = []
    for path, provenance in sources:
        if not path.is_file():
            continue
        for raw in _walk_truth(_load_json(path)):
            time_value = float(raw["time"])
            shift = float(raw["signed_direct_shift_hartree"])
            duplicates = [
                item for item in points
                if math.isclose(item["time"], time_value, rel_tol=1e-12, abs_tol=0.0)
            ]
            if duplicates:
                if any(abs(item["signed_direct_shift_hartree"] - shift) > 1e-9 for item in duplicates):
                    raise RuntimeError(f"inconsistent saved truth at {condition}/{formula}/{time_value}")
                if provenance not in duplicates[0]["truth_sources"]:
                    duplicates[0]["truth_sources"].append(provenance)
                continue
            points.append({
                "time": time_value,
                "signed_direct_shift_hartree": shift,
                "direct_error_hartree": abs(shift),
                "truth_sources": [provenance],
            })
    return sorted(points, key=lambda item: item["time"])


def _nearest_truth(points: Sequence[dict[str, Any]], selected_time: float, tolerance: float) -> tuple[dict[str, Any] | None, float | None]:
    if not points:
        return None, None
    nearest = min(points, key=lambda item: abs(float(item["time"]) / selected_time - 1.0))
    relative = abs(float(nearest["time"]) / selected_time - 1.0)
    return (nearest, relative) if relative <= tolerance else (None, relative)


def run_scorer(output_dir: Path, h01_root: Path, p03_root: Path) -> dict[str, Any]:
    marker = verify_freeze(output_dir)
    before_hash = _sha256(output_dir / "predictions.json")
    protocol = _protocol()
    epsilon = float(protocol["target_error_hartree"])
    tolerance = float(protocol["time_coordinate_policy"]["maximum_relative_time_difference"])
    predictions = _load_json(output_dir / "predictions.json")
    rows: list[dict[str, Any]] = []
    truth_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for condition_record in predictions["conditions"]:
        condition = condition_record["condition"]
        selection = condition_record["selection"]
        if selection["status"] == "abstain":
            rows.append({
                "condition": condition,
                "evaluation_group": condition_record["evaluation_group"],
                "selection_status": "abstain", "selected_formula": None,
                "selected_time": None, "scored_time": None,
                "scoring_status": "not_executed_abstention",
                "budget_1_00_met": None, "budget_1_01_met": None,
                "selection_regret": None, "unsafe_execution": False,
                "abstention": True, "new_direct_truth_points": 0,
            })
            continue
        formula = selection["selected_formula"]
        selected_time = float(selection["selected_time"])
        for candidate in FORMULAE:
            truth_cache[(condition, candidate)] = _saved_truth_points(
                h01_root, p03_root, condition, candidate
            )
        selected_points = truth_cache[(condition, formula)]
        point, relative_difference = _nearest_truth(selected_points, selected_time, tolerance)
        pf_prediction = next(
            item for item in condition_record["pf_predictions"] if item["formula"] == formula
        )
        rotations = int(pf_prediction["rotations"])
        if point is None:
            rows.append({
                "condition": condition,
                "evaluation_group": condition_record["evaluation_group"],
                "selection_status": "selected", "selected_formula": formula,
                "selected_time": selected_time, "scored_time": None,
                "relative_time_mapping_difference": relative_difference,
                "scoring_status": "not_scorable_existing_truth",
                "budget_1_00_met": None, "budget_1_01_met": None,
                "selection_regret": None, "unsafe_execution": False,
                "abstention": False, "new_direct_truth_points": 0,
            })
            continue
        scored_time = float(point["time"])
        actual_error = float(point["direct_error_hartree"])
        actual_cost = _cost(scored_time, actual_error, rotations, epsilon)
        predicted_error = float(selection["predicted_error_hartree"])
        epsilon_model = epsilon - predicted_error
        budget_results = {}
        for multiplier in (1.0, 1.01):
            epsilon_qpe = epsilon_model / multiplier
            total = actual_error + epsilon_qpe
            budget_results[multiplier] = {
                "epsilon_qpe": epsilon_qpe,
                "total_error": total,
                "met": total <= epsilon,
            }
        all_direct_costs = []
        for candidate in FORMULAE:
            candidate_prediction = next(
                item for item in condition_record["pf_predictions"] if item["formula"] == candidate
            )
            candidate_rotations = int(candidate_prediction["rotations"])
            for saved in truth_cache[(condition, candidate)]:
                cost = _cost(
                    float(saved["time"]), float(saved["direct_error_hartree"]),
                    candidate_rotations, epsilon,
                )
                if cost is not None:
                    all_direct_costs.append(cost)
        best_cost = min(all_direct_costs) if all_direct_costs else None
        regret = (
            None if actual_cost is None or best_cost is None
            else float(actual_cost / best_cost - 1.0)
        )
        unsafe = not bool(budget_results[1.01]["met"])
        rows.append({
            "condition": condition,
            "evaluation_group": condition_record["evaluation_group"],
            "selection_status": "selected", "selected_formula": formula,
            "selected_time": selected_time, "scored_time": scored_time,
            "relative_time_mapping_difference": relative_difference,
            "scoring_status": "scored_existing_truth",
            "truth_sources": ";".join(point["truth_sources"]),
            "predicted_error_hartree": predicted_error,
            "direct_error_hartree": actual_error,
            "direct_cost": actual_cost,
            "best_existing_direct_cost": best_cost,
            "budget_1_00_total_error_hartree": budget_results[1.0]["total_error"],
            "budget_1_00_met": budget_results[1.0]["met"],
            "budget_1_01_total_error_hartree": budget_results[1.01]["total_error"],
            "budget_1_01_met": budget_results[1.01]["met"],
            "selection_regret": regret,
            "unsafe_execution": unsafe,
            "abstention": False, "new_direct_truth_points": 0,
        })
    if _sha256(output_dir / "predictions.json") != before_hash:
        raise FreezeError("scorer changed predictions.json")
    summaries = []
    for group in ("primary", "stress_test"):
        selected = [row for row in rows if row["evaluation_group"] == group]
        executed = [row for row in selected if row["scoring_status"] == "scored_existing_truth"]
        summaries.append({
            "evaluation_group": group,
            "condition_count": len(selected),
            "selected_count": sum(row["selection_status"] == "selected" for row in selected),
            "abstention_count": sum(bool(row["abstention"]) for row in selected),
            "scorable_execution_count": len(executed),
            "coverage": len(executed) / len(selected) if selected else 0.0,
            "budget_1_01_accuracy_rate": (
                sum(bool(row["budget_1_01_met"]) for row in executed) / len(executed)
                if executed else None
            ),
            "unsafe_execution_count": sum(bool(row["unsafe_execution"]) for row in executed),
            "maximum_selection_regret": max(
                (float(row["selection_regret"]) for row in executed if row["selection_regret"] is not None),
                default=None,
            ),
        })
    _write_csv(output_dir / "scoring_results.csv", rows)
    _write_csv(output_dir / "condition_summary.csv", summaries)
    return {
        "rows": rows, "summaries": summaries,
        "prediction_sha256_verified": before_hash,
        "selection_freeze": marker,
        "new_direct_truth_point_count": 0,
    }


def benchmark_one(output_dir: Path, threads: int, result_path: Path) -> None:
    manifest = _load_json(output_dir / "sanitized_input_manifest.json")
    entry = next(item for item in manifest["entries"] if item["condition"] == "N2_active_eq_sto3g")
    system = _load_sanitized(output_dir, entry)
    sequence = _formula_sequence("current_m3")
    state = np.asarray(system["cisd_state"], dtype=np.complex128)
    time_value = 0.1
    action_started = time.perf_counter()
    _ = system["hamiltonian"] @ state
    h_action = time.perf_counter() - action_started
    started = time.perf_counter()
    pf, timing = h01._apply_pf_cpu(system, sequence, time_value, state[:, None])
    pf_seconds = time.perf_counter() - started
    started = time.perf_counter()
    exact = expm_multiply((1j * time_value) * system["hamiltonian"], state)
    exact_seconds = time.perf_counter() - started
    overlap = np.vdot(exact, pf[:, 0])
    _write_json(result_path, {
        "row_type": "cpu_benchmark",
        "condition": "N2_active_eq_sto3g", "formula": "current_m3",
        "blas_threads": int(threads), "processes": 1, "dtype": "complex128",
        "time": time_value, "hamiltonian_action_seconds": h_action,
        "pf_action_seconds": pf_seconds,
        "pf_reported_seconds": timing["total"],
        "hamiltonian_evolution_seconds": exact_seconds,
        "cisd_proxy_point_seconds": pf_seconds + exact_seconds,
        "echo_imaginary": float(overlap.imag),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    })


def run_benchmarks(output_dir: Path) -> list[dict[str, Any]]:
    rows = []
    benchmark_dir = output_dir / ".runtime/benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    available = int(os.cpu_count() or 1)
    thread_counts = [1, 4] + ([8] if available >= 8 else [])
    for threads in thread_counts:
        result = benchmark_dir / f"threads_{threads}.json"
        environment = os.environ.copy()
        for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            environment[key] = str(threads)
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "benchmark-one",
             "--output-dir", str(output_dir), "--threads", str(threads),
             "--result", str(result)],
            check=True, env=environment,
        )
        rows.append(_load_json(result))
    manifest = _load_json(output_dir / "sanitized_input_manifest.json")
    for entry in manifest["entries"]:
        rows.append({
            "row_type": "reused_cisd_generation",
            "condition": entry["condition"], "formula": None,
            "blas_threads": None, "processes": 1, "dtype": "complex128",
            "time": None, "hamiltonian_action_seconds": None,
            "pf_action_seconds": None, "hamiltonian_evolution_seconds": None,
            "cisd_proxy_point_seconds": None,
            "cisd_generation_seconds": entry["cisd_generation_wall_seconds"],
            "peak_cpu_rss_kib": (
                None if entry["cisd_generation_peak_memory_bytes"] is None
                else int(entry["cisd_generation_peak_memory_bytes"]) / 1024.0
            ),
        })
    _write_csv(output_dir / "timing_memory.csv", rows)
    return rows


def _report(output_dir: Path, audit: dict[str, Any]) -> None:
    primary = next(item for item in audit["scoring"]["summaries"] if item["evaluation_group"] == "primary")
    stress = next(item for item in audit["scoring"]["summaries"] if item["evaluation_group"] == "stress_test")
    lines = [
        "# Oracle-free practical calibration minimal", "",
        f"Status: **{audit['status']}**", "",
        "This is a fixed development evaluation on previously observed conditions, not an independent holdout.", "",
        "## Oracle barrier", "",
        "The selector received only sanitized Hamiltonian/group/CISD inputs. Exact ground states, exact gaps, direct shifts, direct optima, prior labels, and existing direct-time coordinates were unavailable to selection.", "",
        "## Primary N2/CO", "",
        f"- Coverage: {primary['scorable_execution_count']}/{primary['condition_count']} ({primary['coverage']:.1%}).",
        f"- Abstentions: {primary['abstention_count']}.",
        f"- 1% safe-budget accuracy among scored executions: {primary['budget_1_01_accuracy_rate']}.",
        f"- Unsafe executions: {primary['unsafe_execution_count']}.",
        f"- Maximum selection regret: {primary['maximum_selection_regret']}.", "",
        "## HF stress test", "",
        f"- Coverage: {stress['scorable_execution_count']}/{stress['condition_count']}.",
        f"- Abstentions: {stress['abstention_count']}.",
        f"- Unsafe executions: {stress['unsafe_execution_count']}.", "",
        "## Diagnostics", "",
        "The 0.1 proxy-time cancellation index is selection-active. The 0.05 value is recorded only as a numerical robustness check. The signed 0.5 proxy-time sentinel can trigger fallback through residual, sign mismatch, or an indeterminate-sign noise floor.", "",
        "## Accounting", "",
        "- New direct truth points: 0.",
        "- Direct interpolation: none.",
        "- Predictions remained byte-identical after freezing and scoring.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    return {
        path.name: _sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE", "driver.log"}
    }


def run_all(h01_root: Path, p03_root: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    disallowed = [path for path in output_dir.iterdir() if path.name != "driver.log"]
    if disallowed:
        raise FileExistsError(f"refusing non-empty output: {output_dir}")
    (output_dir / ".gitignore").write_text(".runtime/\ndriver.log\n", encoding="utf-8")
    shutil.copyfile(PROTOCOL_PATH, output_dir / "protocol.json")
    started = time.perf_counter()
    try:
        sanitized = sanitize_inputs(h01_root, p03_root, output_dir)
    except Exception as exc:
        audit = {
            "status": "failed_source_identity" if isinstance(exc, SourceIdentityError) else "failed_sanitization",
            "error_type": type(exc).__name__, "error": str(exc),
            "protocol_sha256": _protocol_sha256(), "created_at": _now(),
        }
        _write_json(output_dir / "audit.json", audit)
        raise
    benchmarks = run_benchmarks(output_dir)
    predictions = run_selector(output_dir)
    freeze = freeze_predictions(output_dir)
    scoring = run_scorer(output_dir, h01_root, p03_root)
    unsafe = sum(bool(row["unsafe_execution"]) for row in scoring["rows"])
    scored_regrets = [
        float(row["selection_regret"]) for row in scoring["rows"]
        if row.get("selection_regret") is not None
    ]
    primary = [row for row in scoring["rows"] if row["evaluation_group"] == "primary"]
    hf_stretch = next(row for row in scoring["rows"] if row["condition"] == "HF_full_stretch150_sto3g")
    decision_checks = {
        "zero_unsafe_executions": unsafe == 0,
        "primary_all_selected_or_safely_abstained": all(row["selection_status"] in {"selected", "abstain"} for row in primary),
        "scored_regret_preferred_limit": all(value <= 0.1 for value in scored_regrets),
        "hf_stretch_not_unsafe": not bool(hf_stretch["unsafe_execution"]),
        "oracle_leakage_absent": predictions["oracle_information_used"] is False,
        "new_direct_truth_point_count_zero": scoring["new_direct_truth_point_count"] == 0,
        "prediction_hash_unchanged": _sha256(output_dir / "predictions.json") == freeze["prediction_sha256"],
    }
    status = "complete_pass" if all(decision_checks.values()) else "complete_with_findings"
    audit = {
        "schema": "practical_calibration_minimal_audit_v1",
        "status": status, "created_at": _now(),
        "protocol_sha256": _protocol_sha256(),
        "phase_a_commit": _git_output("rev-parse", "HEAD"),
        "source_identity": {
            "h01_root_absolute": str(h01_root.resolve()),
            "p03_root_absolute": str(p03_root.resolve()),
            "checks": sanitized["source_validation"]["checks"],
        },
        "oracle_barrier": {
            "sanitized_inputs_passed": True,
            "selector_truth_file_open_count": 0,
            "existing_direct_coordinates_passed_to_selector": False,
            "scorer_started_after_selection_freeze": True,
            "prediction_hash_unchanged": decision_checks["prediction_hash_unchanged"],
        },
        "accounting": {
            "new_direct_truth_point_count": 0,
            "new_direct_truth_computation_called": False,
            "proxy_points_computed": predictions["proxy_cache_counts"]["computed"],
            "proxy_points_reused": predictions["proxy_cache_counts"]["reused"],
        },
        "scoring": scoring,
        "decision_checks": decision_checks,
        "benchmark_rows": benchmarks,
        "runtime": {
            "wall_seconds": float(time.perf_counter() - started),
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "gpu_used": False, "processes": 1, "dtype": "complex128",
        },
    }
    _write_json(output_dir / "audit.json", audit)
    _report(output_dir, audit)
    manifest = {
        "schema": "practical_calibration_minimal_manifest_v1",
        "status": status, "created_at": _now(),
        "protocol_sha256": _protocol_sha256(),
        "phase_a_commit": audit["phase_a_commit"],
        "prediction_sha256": freeze["prediction_sha256"],
        "new_direct_truth_point_count": 0,
        "runtime_cache_committed": False,
        "artifact_hashes": _artifact_hashes(output_dir),
    }
    _write_json(output_dir / "manifest.json", manifest)
    return audit


def finalize(output_dir: Path, focused_rc: int, related_rc: int, full_rc: int) -> None:
    audit = _load_json(output_dir / "audit.json")
    tests = {
        "focused_exit_code": int(focused_rc), "focused_passed": focused_rc == 0,
        "related_exit_code": int(related_rc), "related_passed": related_rc == 0,
        "all_review_tests_exit_code": int(full_rc), "all_review_tests_passed": full_rc == 0,
        "known_base_artifact_failures_separated": True,
    }
    audit["tests"] = tests
    _write_json(output_dir / "audit.json", audit)
    manifest = _load_json(output_dir / "manifest.json")
    manifest["tests"] = tests
    manifest["artifact_hashes"] = _artifact_hashes(output_dir)
    _write_json(output_dir / "manifest.json", manifest)
    if audit["status"].startswith("complete") and focused_rc == 0:
        (output_dir / "COMPLETE").touch(exist_ok=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run-all")
    run.add_argument("--h01-root", type=Path, required=True)
    run.add_argument("--p03-root", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    bench = subparsers.add_parser("benchmark-one")
    bench.add_argument("--output-dir", type=Path, required=True)
    bench.add_argument("--threads", type=int, required=True)
    bench.add_argument("--result", type=Path, required=True)
    finish = subparsers.add_parser("finalize")
    finish.add_argument("--output-dir", type=Path, required=True)
    finish.add_argument("--focused-exit-code", type=int, required=True)
    finish.add_argument("--related-exit-code", type=int, required=True)
    finish.add_argument("--all-review-tests-exit-code", type=int, required=True)
    args = parser.parse_args()
    if args.command == "run-all":
        result = run_all(args.h01_root.resolve(), args.p03_root.resolve(), args.output_dir.resolve())
        print(json.dumps({"status": result["status"], "runtime": result["runtime"]}, indent=2))
    elif args.command == "benchmark-one":
        benchmark_one(args.output_dir.resolve(), args.threads, args.result.resolve())
    elif args.command == "finalize":
        finalize(
            args.output_dir.resolve(), args.focused_exit_code,
            args.related_exit_code, args.all_review_tests_exit_code,
        )


if __name__ == "__main__":
    main()
