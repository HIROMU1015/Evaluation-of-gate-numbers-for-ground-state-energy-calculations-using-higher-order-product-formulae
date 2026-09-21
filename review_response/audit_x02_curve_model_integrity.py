"""Shared finite-time truth curves for C01/C06/C08 and E01--E04/E06.

The molecular calculation is intentionally restricted to H2 and H4.  Each
Hamiltonian/group eigendecomposition is reused for four fixed product
formulas.  The resulting signed curves are then reused by every audit in this
batch; no coefficient search is performed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import schur

from compare_existing_pf_low_order_models_local import (
    CURRENT_M3_WEIGHTS,
    TWO_TERM_CENTER_WEIGHTS,
)
from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import symmetric_s2_sequence
from trotterlib.product_formula import (
    morales_2025_y8m10b_list,
    yoshida_4th_list,
)
from trotterlib.sector_pf import build_sector_pf_unitary
from validate_hchain_perturbative_estimator import _prepare_sector_system


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / (
    "artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3"
)
SHORT_GRID = np.geomspace(0.02, 1.8, 34)
NOISE_FLOOR = 5e-13
WINDOW_SIZE = 5
ORDER_TOLERANCE = 0.2
MINIMUM_R2 = 0.999
TRAINING_RELATIVE_TIMES = np.asarray([0.1, 0.2, 0.3, 0.4, 0.5])
MODEL_RESIDUAL_LIMIT_OVER_EPSILON = 0.05
MAX_DECLARED_TIME = 8.0


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_state() -> dict[str, Any]:
    def run(*command: str) -> str:
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()

    status = run("git", "status", "--porcelain").splitlines()
    return {
        "commit": run("git", "rev-parse", "HEAD") or None,
        "branch": run("git", "branch", "--show-current") or None,
        "dirty": bool(status),
        "status": status,
    }


def _package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in ("numpy", "scipy", "matplotlib", "pyscf", "openfermion"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def formula_definitions() -> list[dict[str, Any]]:
    return [
        {
            "formula_id": "yoshida4",
            "formal_order": 4,
            "weights": tuple(float(x) for x in yoshida_4th_list()),
            "coefficient_source": "trotterlib.product_formula:yoshida_4th_list",
        },
        {
            "formula_id": "current_m3",
            "formal_order": 4,
            "weights": tuple(float(x) for x in CURRENT_M3_WEIGHTS),
            "coefficient_source": (
                "compare_existing_pf_low_order_models_local:CURRENT_M3_WEIGHTS"
            ),
        },
        {
            "formula_id": "two_term_center",
            "formal_order": 4,
            "weights": tuple(float(x) for x in TWO_TERM_CENTER_WEIGHTS),
            "coefficient_source": (
                "compare_existing_pf_low_order_models_local:TWO_TERM_CENTER_WEIGHTS"
            ),
        },
        {
            "formula_id": "morales_y8m10b",
            "formal_order": 8,
            "weights": tuple(float(x) for x in morales_2025_y8m10b_list()),
            "coefficient_source": (
                "trotterlib.product_formula:morales_2025_y8m10b_list"
            ),
        },
    ]


def _circular_phase_gap(phases: np.ndarray, selected: int) -> float:
    differences = np.abs(
        np.angle(np.exp(1j * (np.asarray(phases) - phases[selected])))
    )
    differences[selected] = np.inf
    return float(np.min(differences)) if differences.size > 1 else math.inf


def _cost_per_pf_unit(time_value: float, error: float) -> float | None:
    if time_value <= 0.0 or error < 0.0 or error >= TARGET_ERROR:
        return None
    return float(BETA / (time_value * (TARGET_ERROR - error)))


def _curve(
    system: dict[str, Any], sequence: Sequence[float], times: np.ndarray
) -> tuple[list[dict[str, Any]], float]:
    state = np.asarray(system["ground_state"], dtype=np.complex128)
    energy = float(system["ground_energy_without_constant_hartree"])
    dimension = int(state.size)
    previous_vector: np.ndarray | None = None
    previous_energy: float | None = None
    points: list[dict[str, Any]] = []
    started_curve = time.perf_counter()
    for index, raw_time in enumerate(times):
        time_value = float(raw_time)
        build_started = time.perf_counter()
        unitary = build_sector_pf_unitary(
            system["group_spectra"], sequence, time_value, method="s2-cache"
        )
        build_seconds = time.perf_counter() - build_started

        schur_started = time.perf_counter()
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        schur_seconds = time.perf_counter() - schur_started
        eigenvalues = np.diag(triangular)
        phases = np.angle(eigenvalues)
        ground_overlaps = np.abs(vectors.conj().T @ state) ** 2
        tracking_reference = state if previous_vector is None else previous_vector
        tracking_overlaps = np.abs(vectors.conj().T @ tracking_reference) ** 2
        ground_selected = int(np.argmax(ground_overlaps))
        selected = int(np.argmax(tracking_overlaps))
        raw_phase = float(phases[selected])
        branch_reference = energy if previous_energy is None else previous_energy
        unwrap_integer = int(
            np.rint((branch_reference * time_value - raw_phase) / (2.0 * np.pi))
        )
        effective_energy = (
            raw_phase + 2.0 * np.pi * unwrap_integer
        ) / time_value
        signed_direct = float(effective_energy - energy)
        selected_vector = np.asarray(vectors[:, selected], dtype=np.complex128)
        eigenpair_residual = float(
            np.linalg.norm(
                unitary @ selected_vector - eigenvalues[selected] * selected_vector
            )
        )
        evolved = unitary @ state
        rotated_overlap = complex(
            np.exp(-1j * energy * time_value) * np.vdot(state, evolved)
        )
        signed_imaginary = float(rotated_overlap.imag / time_value)
        signed_overlap_phase = float(np.angle(rotated_overlap) / time_value)
        unitarity_residual = float(
            np.linalg.norm(unitary.conj().T @ unitary - np.eye(dimension))
        )
        phase_gap = _circular_phase_gap(phases, selected)
        previous_probability = float(tracking_overlaps[selected])
        branch_warning = bool(
            selected != ground_selected
            or previous_probability < 0.9
            or float(ground_overlaps[selected]) < 0.9
            or phase_gap < 1e-6
        )
        point = {
            "point_index": index,
            "time_hartree_inverse": time_value,
            "signed_direct_shift_hartree": signed_direct,
            "direct_absolute_error_hartree": abs(signed_direct),
            "signed_imaginary_proxy_hartree": signed_imaginary,
            "signed_overlap_phase_hartree": signed_overlap_phase,
            "direct_cost_per_pf_step_unit": _cost_per_pf_unit(
                time_value, abs(signed_direct)
            ),
            "continuous_branch_index": selected,
            "maximum_ground_overlap_branch_index": ground_selected,
            "selection_rules_agree": selected == ground_selected,
            "selected_ground_overlap_probability": float(
                ground_overlaps[selected]
            ),
            "previous_branch_overlap_probability": previous_probability,
            "ground_state_survival_probability": float(abs(rotated_overlap) ** 2),
            "selected_phase_gap_radians": phase_gap,
            "raw_eigenphase_radians": raw_phase,
            "phase_unwrap_integer": unwrap_integer,
            "selected_effective_energy_hartree": float(effective_energy),
            "eigenpair_residual_2_norm": eigenpair_residual,
            "unitarity_residual_frobenius_norm": unitarity_residual,
            "branch_warning": branch_warning,
            "timing_unitary_build_seconds": float(build_seconds),
            "timing_schur_seconds": float(schur_seconds),
        }
        points.append(point)
        previous_vector = selected_vector
        previous_energy = float(effective_energy)
    return points, float(time.perf_counter() - started_curve)


def _ground_selected_shift(
    unitary: np.ndarray,
    state: np.ndarray,
    reference_energy: float,
    time_value: float,
) -> tuple[float, float, float]:
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    shift = float(
        np.angle(np.exp(-1j * reference_energy * time_value) * eigenvalue)
        / time_value
    )
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    return shift, float(overlaps[selected]), residual


def _point_lookup(points: Sequence[dict[str, Any]], target: float) -> dict[str, Any]:
    return min(
        points,
        key=lambda point: abs(float(point["time_hartree_inverse"]) - float(target)),
    )


def _earliest_qualified_window(
    times: np.ndarray,
    errors: np.ndarray,
    formal_order: int,
    *,
    window_size: int = WINDOW_SIZE,
    order_tolerance: float = ORDER_TOLERANCE,
    minimum_r2: float = MINIMUM_R2,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    windows = rolling_loglog_fits(
        times,
        errors,
        formal_order=formal_order,
        noise_floor=NOISE_FLOOR,
        window_size=window_size,
    )
    eligible = [
        window
        for window in windows
        if float(window["order_deviation"]) <= order_tolerance
        and float(window["r2"]) >= minimum_r2
    ]
    return (
        min(eligible, key=lambda row: int(row["start_index"]), default=None),
        windows,
    )


def _fit_signed_coefficients(
    times: np.ndarray,
    values: np.ndarray,
    formal_order: int,
    number_of_terms: int,
    *,
    reference_time: float | None = None,
) -> dict[str, Any]:
    x_times = np.asarray(times, dtype=float)
    y_values = np.asarray(values, dtype=float)
    if x_times.size < number_of_terms or x_times.shape != y_values.shape:
        raise ValueError("insufficient or mismatched fit arrays")
    if np.any(x_times <= 0) or not np.all(np.isfinite(y_values)):
        raise ValueError("fit data must be finite and times positive")
    order = int(formal_order)
    t_ref = float(np.max(x_times) if reference_time is None else reference_time)
    scaled_x = (x_times / t_ref) ** 2
    normalized_target = y_values / x_times**order
    scaled_design = np.column_stack(
        [scaled_x**power for power in range(number_of_terms)]
    )
    scaled_coefficients = np.linalg.lstsq(
        scaled_design, normalized_target, rcond=None
    )[0]
    physical_coefficients = np.asarray(
        [
            scaled_coefficients[index] / t_ref ** (2 * index)
            for index in range(number_of_terms)
        ],
        dtype=float,
    )
    powers = np.asarray(
        [order + 2 * index for index in range(number_of_terms)], dtype=int
    )
    raw_design = np.column_stack([x_times**power for power in powers])
    prediction = raw_design @ physical_coefficients
    singular_values = np.linalg.svd(scaled_design, compute_uv=False)

    perturbation_scale = max(float(np.max(np.abs(y_values))), TARGET_ERROR)
    perturbation = (
        1e-10
        * perturbation_scale
        * np.where(np.arange(y_values.size) % 2 == 0, 1.0, -1.0)
    )
    perturbed_target = (y_values + perturbation) / x_times**order
    perturbed_scaled = np.linalg.lstsq(
        scaled_design, perturbed_target, rcond=None
    )[0]
    perturbed_physical = np.asarray(
        [
            perturbed_scaled[index] / t_ref ** (2 * index)
            for index in range(number_of_terms)
        ]
    )
    coefficient_scale = max(float(np.linalg.norm(physical_coefficients)), 1e-300)
    return {
        "formal_order": order,
        "number_of_terms": int(number_of_terms),
        "powers": powers.tolist(),
        "coefficients": physical_coefficients.tolist(),
        "scaled_coefficients": scaled_coefficients.tolist(),
        "reference_time": t_ref,
        "raw_design_condition_number": float(np.linalg.cond(raw_design)),
        "scaled_design_condition_number": float(np.linalg.cond(scaled_design)),
        "scaled_design_singular_values": singular_values.tolist(),
        "training_residual_linf_hartree": float(
            np.max(np.abs(prediction - y_values))
        ),
        "coefficient_relative_sensitivity_to_1e_10_output_perturbation": float(
            np.linalg.norm(perturbed_physical - physical_coefficients)
            / coefficient_scale
        ),
    }


def _model_prediction(model: dict[str, Any], times: np.ndarray) -> np.ndarray:
    values = np.zeros(np.asarray(times).shape, dtype=float)
    for power, coefficient in zip(model["powers"], model["coefficients"]):
        values += float(coefficient) * np.asarray(times, dtype=float) ** int(power)
    return values


def _analytic_time_from_leading(coefficient: float, formal_order: int) -> float | None:
    alpha = abs(float(coefficient))
    if not math.isfinite(alpha) or alpha <= 0.0:
        return None
    return float((TARGET_ERROR / ((formal_order + 1) * alpha)) ** (1.0 / formal_order))


def _sign_change_count(values: np.ndarray) -> int:
    array = np.asarray(values, dtype=float)
    signs = np.sign(array)
    return int(
        sum(
            signs[index] == 0
            or signs[index + 1] == 0
            or signs[index] != signs[index + 1]
            for index in range(len(signs) - 1)
        )
    )


def _resolved_sign_change_count(
    values: np.ndarray, *, noise_floor: float = NOISE_FLOOR
) -> int:
    array = np.asarray(values, dtype=float)
    return int(
        sum(
            min(abs(array[index]), abs(array[index + 1])) > noise_floor
            and array[index] * array[index + 1] < 0.0
            for index in range(len(array) - 1)
        )
    )


def _sampled_model_optimum(
    coefficients: Sequence[float],
    formal_order: int,
    interval: tuple[float, float],
    *,
    number_of_points: int = 40001,
) -> dict[str, Any]:
    times = np.linspace(float(interval[0]), float(interval[1]), number_of_points)
    model = {
        "powers": [formal_order + 2 * i for i in range(len(coefficients))],
        "coefficients": list(map(float, coefficients)),
    }
    signed = _model_prediction(model, times)
    errors = np.abs(signed)
    feasible = errors < TARGET_ERROR
    costs = np.full(times.shape, np.inf)
    costs[feasible] = BETA / (
        times[feasible] * (TARGET_ERROR - errors[feasible])
    )
    if not np.any(feasible):
        return {
            "status": "infeasible_error_budget",
            "feasible_point_count": 0,
            "minimum_time": None,
            "minimum_cost": None,
            "boundary_minimum": False,
            "root_bracket_count": _sign_change_count(signed),
        }
    selected = int(np.argmin(costs))
    return {
        "status": "complete",
        "feasible_point_count": int(np.count_nonzero(feasible)),
        "minimum_time": float(times[selected]),
        "minimum_cost": float(costs[selected]),
        "boundary_minimum": selected in {0, number_of_points - 1},
        "root_bracket_count": _sign_change_count(signed),
    }


def evaluate_synthetic_controls() -> list[dict[str, Any]]:
    cases = [
        {
            "case_id": "two_roots",
            "formal_order": 4,
            "coefficients": [3e-4, -1e-3, 8e-4],
            "interval": (0.2, 1.2),
            "expected_status": "complete",
            "minimum_root_brackets": 2,
            "expected_boundary": False,
        },
        {
            "case_id": "near_zero_leading",
            "formal_order": 4,
            "coefficients": [1e-14, 5e-4],
            "interval": (0.02, 2.0),
            "expected_status": "complete",
            "minimum_root_brackets": 0,
            "expected_boundary": False,
        },
        {
            "case_id": "all_infeasible",
            "formal_order": 4,
            "coefficients": [1e-2],
            "interval": (0.5, 2.0),
            "expected_status": "infeasible_error_budget",
            "minimum_root_brackets": 0,
            "expected_boundary": False,
        },
        {
            "case_id": "upper_boundary",
            "formal_order": 4,
            "coefficients": [1e-12],
            "interval": (0.02, 2.0),
            "expected_status": "complete",
            "minimum_root_brackets": 0,
            "expected_boundary": True,
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        optimum = _sampled_model_optimum(
            case["coefficients"], case["formal_order"], case["interval"]
        )
        leading_time = _analytic_time_from_leading(
            case["coefficients"][0], case["formal_order"]
        )
        passed = bool(
            optimum["status"] == case["expected_status"]
            and optimum["root_bracket_count"] >= case["minimum_root_brackets"]
            and optimum["boundary_minimum"] == case["expected_boundary"]
        )
        rows.append(
            {
                "case_id": case["case_id"],
                "formal_order": case["formal_order"],
                "coefficients": json.dumps(case["coefficients"]),
                "interval": json.dumps(case["interval"]),
                "leading_only_analytic_time": leading_time,
                **optimum,
                "passed": passed,
            }
        )
    return rows


def _estimator_fits(
    points: Sequence[dict[str, Any]], formal_order: int
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    short_points = [
        _point_lookup(points, float(time_value)) for time_value in SHORT_GRID
    ]
    times = np.asarray(
        [point["time_hartree_inverse"] for point in short_points], dtype=float
    )
    imaginary = np.asarray(
        [point["signed_imaginary_proxy_hartree"] for point in short_points]
    )
    selected, windows = _earliest_qualified_window(
        times, np.abs(imaginary), formal_order
    )
    if selected is None:
        raise RuntimeError("canonical imaginary-proxy window did not qualify")
    start = int(selected["start_index"])
    stop = int(selected["stop_index_exclusive"])
    fit_times = times[start:stop]
    quantities = {
        "direct_eigenvalue_shift": np.asarray(
            [point["signed_direct_shift_hartree"] for point in short_points]
        ),
        "imaginary_proxy": imaginary,
        "overlap_phase": np.asarray(
            [point["signed_overlap_phase_hartree"] for point in short_points]
        ),
    }
    fits: dict[str, dict[str, Any]] = {}
    for name, values in quantities.items():
        model = _fit_signed_coefficients(
            fit_times, values[start:stop], formal_order, 2
        )
        model["analytic_time_from_leading"] = _analytic_time_from_leading(
            model["coefficients"][0], formal_order
        )
        fits[name] = model
    return fits, selected, windows


def _flatten_truth_rows(truth: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for system_id, system in truth["systems"].items():
        for formula_id, formula in system["formulas"].items():
            training_times = np.asarray(formula["training_times"], dtype=float)
            for point in formula["points"]:
                time_value = float(point["time_hartree_inverse"])
                is_training = bool(
                    np.any(np.isclose(time_value, training_times, rtol=0, atol=1e-13))
                )
                rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "formal_order": formula["formal_order"],
                        "role": "train" if is_training else "validation",
                        **point,
                    }
                )
    return rows


def _build_truth() -> tuple[dict[str, Any], dict[str, Any]]:
    definitions = formula_definitions()
    truth: dict[str, Any] = {
        "schema_version": 1,
        "protocol": {
            "short_grid": SHORT_GRID.tolist(),
            "noise_floor_hartree": NOISE_FLOOR,
            "rolling_window_size": WINDOW_SIZE,
            "formal_order_tolerance": ORDER_TOLERANCE,
            "minimum_r2": MINIMUM_R2,
            "training_relative_to_imaginary_proxy_analytic_time": (
                TRAINING_RELATIVE_TIMES.tolist()
            ),
            "target_error_hartree": TARGET_ERROR,
            "direct_optimum_kind": "sampled_grid_only",
        },
        "formulas": definitions,
        "systems": {},
    }
    timing: dict[str, Any] = {}
    for h_chain in (2, 4):
        system_id = f"H{h_chain}"
        setup_started = time.perf_counter()
        system = _prepare_sector_system(h_chain)
        setup_seconds = time.perf_counter() - setup_started
        preliminary: dict[str, Any] = {}
        candidate_times: list[float] = list(map(float, SHORT_GRID))
        estimator_times: list[float] = []
        for definition in definitions:
            formula_id = str(definition["formula_id"])
            sequence = symmetric_s2_sequence(definition["weights"])
            points, elapsed = _curve(system, sequence, SHORT_GRID)
            fits, selected_window, windows = _estimator_fits(
                points, int(definition["formal_order"])
            )
            imaginary_time = fits["imaginary_proxy"]["analytic_time_from_leading"]
            if imaginary_time is None:
                raise RuntimeError(f"{system_id}/{formula_id}: no analytic time")
            training_times = TRAINING_RELATIVE_TIMES * float(imaginary_time)
            candidate_times.extend(map(float, training_times))
            for fit in fits.values():
                analytic_time = fit["analytic_time_from_leading"]
                if analytic_time is not None and analytic_time <= MAX_DECLARED_TIME:
                    estimator_times.append(float(analytic_time))
                    candidate_times.append(float(analytic_time))
                    candidate_times.extend(
                        map(
                            float,
                            np.linspace(0.9 * analytic_time, 1.1 * analytic_time, 21),
                        )
                    )
            preliminary[formula_id] = {
                "sequence": sequence,
                "fits": fits,
                "selected_window": selected_window,
                "windows": windows,
                "training_times": training_times.tolist(),
                "preliminary_curve_seconds": elapsed,
            }

        derived_maximum = max([1.8] + [1.15 * value for value in estimator_times])
        declared_maximum = min(MAX_DECLARED_TIME, derived_maximum)
        coarse_times = np.geomspace(0.02, declared_maximum, 41)
        dense_times = np.linspace(0.02, declared_maximum, 161)
        candidate_times.extend(map(float, coarse_times))
        candidate_times.extend(map(float, dense_times))
        final_times = np.unique(
            np.asarray(
                [
                    value
                    for value in candidate_times
                    if 0.02 <= value <= declared_maximum
                ],
                dtype=float,
            )
        )
        formulas: dict[str, Any] = {}
        for definition in definitions:
            formula_id = str(definition["formula_id"])
            points, elapsed = _curve(
                system, preliminary[formula_id]["sequence"], final_times
            )
            final_fits, selected_window, windows = _estimator_fits(
                points, int(definition["formal_order"])
            )
            formulas[formula_id] = {
                "formal_order": int(definition["formal_order"]),
                "weights": list(definition["weights"]),
                "s2_sequence": preliminary[formula_id]["sequence"],
                "coefficient_source": definition["coefficient_source"],
                "training_times": preliminary[formula_id]["training_times"],
                "canonical_selected_window": selected_window,
                "all_canonical_windows": windows,
                "estimator_fits": final_fits,
                "points": points,
                "final_curve_seconds": elapsed,
            }

        root_refinement_times: list[float] = []
        for formula in formulas.values():
            points = formula["points"]
            warning_index = next(
                (
                    index
                    for index, point in enumerate(points)
                    if point["branch_warning"]
                ),
                len(points),
            )
            reliable_points = points[:warning_index]
            for left, right in zip(reliable_points[:-1], reliable_points[1:]):
                left_shift = float(left["signed_direct_shift_hartree"])
                right_shift = float(right["signed_direct_shift_hartree"])
                resolved_sign_change = bool(
                    min(abs(left_shift), abs(right_shift)) > NOISE_FLOOR
                    and left_shift * right_shift < 0.0
                )
                if resolved_sign_change:
                    root_refinement_times.extend(
                        map(
                            float,
                            np.linspace(
                                float(left["time_hartree_inverse"]),
                                float(right["time_hartree_inverse"]),
                                21,
                            ),
                        )
                    )
        refined_times = np.unique(
            np.concatenate(
                [final_times, np.asarray(root_refinement_times, dtype=float)]
            )
        )
        root_points_added = int(refined_times.size - final_times.size)
        if root_points_added:
            final_times = refined_times
            for definition in definitions:
                formula_id = str(definition["formula_id"])
                points, elapsed = _curve(
                    system, preliminary[formula_id]["sequence"], final_times
                )
                final_fits, selected_window, windows = _estimator_fits(
                    points, int(definition["formal_order"])
                )
                formulas[formula_id].update(
                    {
                        "canonical_selected_window": selected_window,
                        "all_canonical_windows": windows,
                        "estimator_fits": final_fits,
                        "points": points,
                        "final_curve_seconds": float(
                            formulas[formula_id]["final_curve_seconds"] + elapsed
                        ),
                    }
                )

        state = np.asarray(system["ground_state"], dtype=np.complex128)
        reference_energy = float(system["ground_energy_without_constant_hartree"])
        for formula_id, formula in formulas.items():
            points = formula["points"]
            warning_index = next(
                (
                    index
                    for index, point in enumerate(points)
                    if point["branch_warning"]
                ),
                len(points),
            )
            reliable_points = points[: max(1, warning_index)]
            feasible_points = [
                point
                for point in reliable_points
                if point["direct_cost_per_pf_step_unit"] is not None
            ]
            minimum_point = min(
                feasible_points,
                key=lambda point: float(point["direct_cost_per_pf_step_unit"]),
            )
            minimum_time = float(minimum_point["time_hartree_inverse"])
            cached = build_sector_pf_unitary(
                system["group_spectra"],
                formula["s2_sequence"],
                minimum_time,
                method="s2-cache",
            )
            sequential = build_sector_pf_unitary(
                system["group_spectra"],
                formula["s2_sequence"],
                minimum_time,
                method="sequential",
            )
            sequential_shift, sequential_overlap, sequential_residual = (
                _ground_selected_shift(
                    sequential, state, reference_energy, minimum_time
                )
            )
            formula["sequential_minimum_spot_check"] = {
                "time_hartree_inverse": minimum_time,
                "cached_continuous_shift_hartree": minimum_point[
                    "signed_direct_shift_hartree"
                ],
                "sequential_ground_selected_shift_hartree": sequential_shift,
                "absolute_shift_difference_hartree": abs(
                    sequential_shift
                    - float(minimum_point["signed_direct_shift_hartree"])
                ),
                "cached_sequential_unitary_frobenius_difference": float(
                    np.linalg.norm(cached - sequential)
                ),
                "sequential_ground_overlap_probability": sequential_overlap,
                "sequential_eigenpair_residual_2_norm": sequential_residual,
            }
        truth["systems"][system_id] = {
            "h_chain": h_chain,
            "num_qubits": int(system["num_qubits"]),
            "num_groups": int(system["num_groups"]),
            "sector": system["sector"],
            "ground_energy_without_constant_hartree": float(
                system["ground_energy_without_constant_hartree"]
            ),
            "declared_time_interval": [0.02, float(declared_maximum)],
            "coarse_grid": coarse_times.tolist(),
            "final_grid_point_count": int(final_times.size),
            "root_refinement_added_point_count": root_points_added,
            "formulas": formulas,
        }
        timing[system_id] = {
            "setup_seconds": float(setup_seconds),
            "preliminary_curve_seconds": float(
                sum(
                    item["preliminary_curve_seconds"]
                    for item in preliminary.values()
                )
            ),
            "final_curve_seconds": float(
                sum(item["final_curve_seconds"] for item in formulas.values())
            ),
        }
    return truth, timing


def _analyze_truth(truth: dict[str, Any]) -> dict[str, Any]:
    c01_rows: list[dict[str, Any]] = []
    c06_rows: list[dict[str, Any]] = []
    e01_rows: list[dict[str, Any]] = []
    e02_rows: list[dict[str, Any]] = []
    e03_rows: list[dict[str, Any]] = []
    e04_rows: list[dict[str, Any]] = []
    e06_rows: list[dict[str, Any]] = []
    branch_rows: list[dict[str, Any]] = []
    branch_summary_rows: list[dict[str, Any]] = []

    for system_id, system in truth["systems"].items():
        coarse_times = np.asarray(system["coarse_grid"], dtype=float)
        reliable_prefix_end: dict[str, float] = {}
        first_warning_time: dict[str, float | None] = {}
        for formula_id, formula in system["formulas"].items():
            points = formula["points"]
            warning_index = next(
                (
                    index
                    for index, point in enumerate(points)
                    if point["branch_warning"]
                ),
                None,
            )
            first_warning_time[formula_id] = (
                None
                if warning_index is None
                else float(points[warning_index]["time_hartree_inverse"])
            )
            reliable_prefix_end[formula_id] = float(
                points[-1 if warning_index is None else max(0, warning_index - 1)][
                    "time_hartree_inverse"
                ]
            )
        common_reliable_end = min(reliable_prefix_end.values())
        for formula_id, formula in system["formulas"].items():
            order = int(formula["formal_order"])
            points = formula["points"]
            all_times = np.asarray(
                [point["time_hartree_inverse"] for point in points], dtype=float
            )
            direct = np.asarray(
                [point["signed_direct_shift_hartree"] for point in points]
            )
            direct_errors = np.abs(direct)
            costs = np.asarray(
                [
                    math.inf
                    if point["direct_cost_per_pf_step_unit"] is None
                    else float(point["direct_cost_per_pf_step_unit"])
                    for point in points
                ]
            )
            warning_points = [point for point in points if point["branch_warning"]]
            branch_summary_rows.append(
                {
                    "system": system_id,
                    "formula": formula_id,
                    "curve_point_count": len(points),
                    "branch_warning_count": len(warning_points),
                    "first_branch_warning_time": first_warning_time[formula_id],
                    "branch_reliable_prefix_end": reliable_prefix_end[formula_id],
                    "system_common_reliable_prefix_end": common_reliable_end,
                    "selection_rule_disagreement_count": sum(
                        not point["selection_rules_agree"] for point in points
                    ),
                    "minimum_ground_overlap_probability": min(
                        point["selected_ground_overlap_probability"]
                        for point in points
                    ),
                    "minimum_previous_branch_overlap_probability": min(
                        point["previous_branch_overlap_probability"] for point in points
                    ),
                    "minimum_phase_gap_radians": min(
                        point["selected_phase_gap_radians"] for point in points
                    ),
                }
            )
            full_grid_index = int(np.argmin(costs))
            full_grid_minimum = points[full_grid_index]
            trusted_points = [
                point
                for point in points
                if float(point["time_hartree_inverse"])
                <= common_reliable_end * (1.0 + 1e-13)
            ]
            trusted_costs = np.asarray(
                [
                    math.inf
                    if point["direct_cost_per_pf_step_unit"] is None
                    else float(point["direct_cost_per_pf_step_unit"])
                    for point in trusted_points
                ]
            )
            refined_index = int(np.argmin(trusted_costs))
            refined_minimum = trusted_points[refined_index]
            trusted_coarse_times = coarse_times[
                coarse_times <= common_reliable_end * (1.0 + 1e-13)
            ]
            coarse_points = [
                _point_lookup(points, value) for value in trusted_coarse_times
            ]
            coarse_costs = np.asarray(
                [
                    math.inf
                    if point["direct_cost_per_pf_step_unit"] is None
                    else float(point["direct_cost_per_pf_step_unit"])
                    for point in coarse_points
                ]
            )
            coarse_index = int(np.argmin(coarse_costs))
            coarse_minimum = coarse_points[coarse_index]
            c06_rows.append(
                {
                    "system": system_id,
                    "formula": formula_id,
                    "declared_t_min": system["declared_time_interval"][0],
                    "declared_t_max": system["declared_time_interval"][1],
                    "formula_reliable_prefix_end": reliable_prefix_end[formula_id],
                    "system_common_reliable_prefix_end": common_reliable_end,
                    "first_branch_warning_time": first_warning_time[formula_id],
                    "coarse_grid_point_count": len(coarse_points),
                    "refined_grid_point_count": len(trusted_points),
                    "coarse_minimum_time": coarse_minimum["time_hartree_inverse"],
                    "coarse_minimum_cost_per_pf_step_unit": coarse_minimum[
                        "direct_cost_per_pf_step_unit"
                    ],
                    "refined_sampled_minimum_time": refined_minimum[
                        "time_hartree_inverse"
                    ],
                    "refined_sampled_minimum_cost_per_pf_step_unit": refined_minimum[
                        "direct_cost_per_pf_step_unit"
                    ],
                    "coarse_cost_over_refined_minus_one": float(
                        coarse_costs[coarse_index] / trusted_costs[refined_index] - 1.0
                    ),
                    "coarse_time_relative_difference": abs(
                        float(coarse_minimum["time_hartree_inverse"])
                        / float(refined_minimum["time_hartree_inverse"])
                        - 1.0
                    ),
                    "refined_minimum_on_common_reliable_boundary": refined_index
                    in {0, len(trusted_points) - 1},
                    "resolved_direct_sign_change_bracket_count_in_common_prefix": _resolved_sign_change_count(
                        np.asarray(
                            [
                                point["signed_direct_shift_hartree"]
                                for point in trusted_points
                            ]
                        )
                    ),
                    "infeasible_grid_point_count_in_common_prefix": int(
                        np.count_nonzero(~np.isfinite(trusted_costs))
                    ),
                    "unrestricted_full_grid_minimum_time_diagnostic": full_grid_minimum[
                        "time_hartree_inverse"
                    ],
                    "unrestricted_full_grid_minimum_cost_diagnostic": full_grid_minimum[
                        "direct_cost_per_pf_step_unit"
                    ],
                    "unrestricted_minimum_outside_formula_reliable_prefix": bool(
                        float(full_grid_minimum["time_hartree_inverse"])
                        > reliable_prefix_end[formula_id] * (1.0 + 1e-13)
                    ),
                    "root_refinement_added_point_count_for_system": system[
                        "root_refinement_added_point_count"
                    ],
                    "sequential_spot_shift_absolute_difference_hartree": formula[
                        "sequential_minimum_spot_check"
                    ]["absolute_shift_difference_hartree"],
                    "sequential_spot_unitary_frobenius_difference": formula[
                        "sequential_minimum_spot_check"
                    ]["cached_sequential_unitary_frobenius_difference"],
                    "optimum_kind": (
                        "common-branch-reliable sampled grid; not a continuous minimum"
                    ),
                }
            )

            formula_reliable_costs = np.asarray(
                [
                    cost
                    for point, cost in zip(points, costs)
                    if float(point["time_hartree_inverse"])
                    <= reliable_prefix_end[formula_id] * (1.0 + 1e-13)
                ]
            )
            direct_minimum_cost = float(np.min(formula_reliable_costs))
            direct_fit = formula["estimator_fits"]["direct_eigenvalue_shift"]
            for estimator_name, fit in formula["estimator_fits"].items():
                analytic_time = fit["analytic_time_from_leading"]
                selected_point = (
                    None
                    if analytic_time is None
                    else _point_lookup(points, float(analytic_time))
                )
                selected_cost = (
                    None
                    if selected_point is None
                    else selected_point["direct_cost_per_pf_step_unit"]
                )
                c01_rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "formal_order": order,
                        "estimator": estimator_name,
                        "shared_fit_t_start": formula["canonical_selected_window"][
                            "t_start"
                        ],
                        "shared_fit_t_stop": formula["canonical_selected_window"][
                            "t_stop"
                        ],
                        "a_p": fit["coefficients"][0],
                        "a_p_plus_2": fit["coefficients"][1],
                        "a_p_relative_difference_from_direct": abs(
                            float(fit["coefficients"][0])
                            - float(direct_fit["coefficients"][0])
                        )
                        / max(abs(float(direct_fit["coefficients"][0])), 1e-300),
                        "analytic_time_from_leading": analytic_time,
                        "nearest_direct_time": (
                            None
                            if selected_point is None
                            else selected_point["time_hartree_inverse"]
                        ),
                        "nearest_time_absolute_difference": (
                            None
                            if selected_point is None
                            else abs(
                                float(selected_point["time_hartree_inverse"])
                                - float(analytic_time)
                            )
                        ),
                        "direct_cost_at_selected_time": selected_cost,
                        "selected_time_within_branch_reliable_prefix": bool(
                            analytic_time is not None
                            and float(analytic_time)
                            <= reliable_prefix_end[formula_id] * (1.0 + 1e-13)
                        ),
                        "direct_sampled_selection_regret": (
                            None
                            if selected_cost is None
                            or analytic_time is None
                            or float(analytic_time)
                            > reliable_prefix_end[formula_id] * (1.0 + 1e-13)
                            else float(selected_cost / direct_minimum_cost - 1.0)
                        ),
                    }
                )

            short_points = [_point_lookup(points, value) for value in SHORT_GRID]
            short_times = np.asarray(
                [point["time_hartree_inverse"] for point in short_points]
            )
            short_imaginary = np.asarray(
                [abs(point["signed_imaginary_proxy_hartree"]) for point in short_points]
            )
            for window_size in (4, 5, 6):
                for order_tolerance in (0.1, 0.2, 0.3):
                    for minimum_r2 in (0.995, 0.999):
                        selected, windows = _earliest_qualified_window(
                            short_times,
                            short_imaginary,
                            order,
                            window_size=window_size,
                            order_tolerance=order_tolerance,
                            minimum_r2=minimum_r2,
                        )
                        e01_rows.append(
                            {
                                "system": system_id,
                                "formula": formula_id,
                                "window_size": window_size,
                                "order_tolerance": order_tolerance,
                                "minimum_r2": minimum_r2,
                                "qualified": selected is not None,
                                "eligible_window_count": sum(
                                    row["order_deviation"] <= order_tolerance
                                    and row["r2"] >= minimum_r2
                                    for row in windows
                                ),
                                "selected_start_index": (
                                    None if selected is None else selected["start_index"]
                                ),
                                "selected_t_start": (
                                    None if selected is None else selected["t_start"]
                                ),
                                "selected_t_stop": (
                                    None if selected is None else selected["t_stop"]
                                ),
                                "selected_free_order": (
                                    None if selected is None else selected["free_order"]
                                ),
                                "selected_fixed_order_alpha": (
                                    None
                                    if selected is None
                                    else selected["fixed_order_alpha"]
                                ),
                                "selected_analytic_time": (
                                    None
                                    if selected is None
                                    else _analytic_time_from_leading(
                                        selected["fixed_order_alpha"], order
                                    )
                                ),
                            }
                        )

            training_times = np.asarray(formula["training_times"], dtype=float)
            training_points = [_point_lookup(points, value) for value in training_times]
            training_shifts = np.asarray(
                [point["signed_direct_shift_hartree"] for point in training_points]
            )
            proxy_analytic_time = float(
                formula["estimator_fits"]["imaginary_proxy"][
                    "analytic_time_from_leading"
                ]
            )
            practical_holdout_end = min(
                reliable_prefix_end[formula_id], 1.2 * proxy_analytic_time
            )
            practical_mask = (
                all_times > float(np.max(training_times)) * (1.0 + 1e-12)
            ) & (all_times <= practical_holdout_end * (1.0 + 1e-13))
            practical_times = all_times[practical_mask]
            practical_shifts = direct[practical_mask]
            broad_mask = (
                all_times > float(np.max(training_times)) * (1.0 + 1e-12)
            ) & (
                all_times
                <= reliable_prefix_end[formula_id] * (1.0 + 1e-13)
            )
            broad_times = all_times[broad_mask]
            broad_shifts = direct[broad_mask]
            if practical_times.size < 10 or broad_times.size < 10:
                raise RuntimeError(f"{system_id}/{formula_id}: too few holdout times")

            signed_models: dict[int, dict[str, Any]] = {}
            absolute_models: dict[int, dict[str, Any]] = {}
            for number_of_terms in (1, 2, 3):
                signed_model = _fit_signed_coefficients(
                    training_times,
                    training_shifts,
                    order,
                    number_of_terms,
                    reference_time=float(np.max(training_times)),
                )
                absolute_model = _fit_signed_coefficients(
                    training_times,
                    np.abs(training_shifts),
                    order,
                    number_of_terms,
                    reference_time=float(np.max(training_times)),
                )
                signed_models[number_of_terms] = signed_model
                absolute_models[number_of_terms] = absolute_model
                signed_prediction = _model_prediction(signed_model, practical_times)
                absolute_prediction = _model_prediction(
                    absolute_model, practical_times
                )
                signed_residual = np.abs(signed_prediction - practical_shifts)
                signed_error_residual = np.abs(
                    np.abs(signed_prediction) - np.abs(practical_shifts)
                )
                absolute_error_residual = np.abs(
                    absolute_prediction - np.abs(practical_shifts)
                )
                e02_rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "model_terms": number_of_terms,
                        "powers": json.dumps(signed_model["powers"]),
                        "raw_design_condition_number": signed_model[
                            "raw_design_condition_number"
                        ],
                        "scaled_design_condition_number": signed_model[
                            "scaled_design_condition_number"
                        ],
                        "condition_number_improvement_factor": float(
                            signed_model["raw_design_condition_number"]
                            / signed_model["scaled_design_condition_number"]
                        ),
                        "coefficient_sensitivity": signed_model[
                            "coefficient_relative_sensitivity_to_1e_10_output_perturbation"
                        ],
                    }
                )
                e03_rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "model_terms": number_of_terms,
                        "signed_fit_max_abs_error_residual_over_epsilon": float(
                            np.max(signed_error_residual) / TARGET_ERROR
                        ),
                        "absolute_fit_max_abs_error_residual_over_epsilon": float(
                            np.max(absolute_error_residual) / TARGET_ERROR
                        ),
                        "signed_fit_better": bool(
                            np.max(signed_error_residual)
                            < np.max(absolute_error_residual)
                        ),
                        "signed_fit_predicted_root_brackets": _sign_change_count(
                            signed_prediction
                        ),
                        "absolute_fit_negative_prediction_count": int(
                            np.count_nonzero(absolute_prediction < 0.0)
                        ),
                    }
                )
                e04_rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "model_terms": number_of_terms,
                        "powers": json.dumps(signed_model["powers"]),
                        "coefficients": json.dumps(signed_model["coefficients"]),
                        "training_point_count": len(training_times),
                        "holdout_scope": (
                            "independent points through min(1.2*t_ana, "
                            "branch-reliable-prefix)"
                        ),
                        "holdout_end_time": practical_holdout_end,
                        "holdout_point_count": len(practical_times),
                        "training_residual_linf_over_epsilon": float(
                            signed_model["training_residual_linf_hartree"]
                            / TARGET_ERROR
                        ),
                        "holdout_signed_residual_linf_over_epsilon": float(
                            np.max(signed_residual) / TARGET_ERROR
                        ),
                        "holdout_signed_residual_rmse_over_epsilon": float(
                            np.sqrt(np.mean(signed_residual**2)) / TARGET_ERROR
                        ),
                        "holdout_passes_0p05_epsilon": bool(
                            np.max(signed_residual)
                            <= MODEL_RESIDUAL_LIMIT_OVER_EPSILON * TARGET_ERROR
                        ),
                        "overfit_warning": bool(
                            signed_model["training_residual_linf_hartree"]
                            <= MODEL_RESIDUAL_LIMIT_OVER_EPSILON * TARGET_ERROR
                            and np.max(signed_residual)
                            > MODEL_RESIDUAL_LIMIT_OVER_EPSILON * TARGET_ERROR
                        ),
                    }
                )

                broad_prediction = _model_prediction(signed_model, broad_times)
                broad_residual = np.abs(broad_prediction - broad_shifts)
                pass_mask = broad_residual <= (
                    MODEL_RESIDUAL_LIMIT_OVER_EPSILON * TARGET_ERROR
                )
                first_failure = next(
                    (index for index, passed in enumerate(pass_mask) if not passed),
                    len(pass_mask),
                )
                last_contiguous_time = (
                    float(np.max(training_times))
                    if first_failure == 0
                    else float(broad_times[first_failure - 1])
                )
                later_reentry = bool(
                    first_failure < len(pass_mask) - 1
                    and np.any(pass_mask[first_failure + 1 :])
                )
                underprediction = (
                    np.abs(broad_shifts) - np.abs(broad_prediction)
                ) > MODEL_RESIDUAL_LIMIT_OVER_EPSILON * TARGET_ERROR
                first_under = next(
                    (index for index, value in enumerate(underprediction) if value),
                    None,
                )
                e06_rows.append(
                    {
                        "system": system_id,
                        "formula": formula_id,
                        "model_terms": number_of_terms,
                        "maximum_training_time": float(np.max(training_times)),
                        "branch_reliable_prefix_end": reliable_prefix_end[
                            formula_id
                        ],
                        "first_holdout_time": float(broad_times[0]),
                        "contiguous_validity_end_time": last_contiguous_time,
                        "contiguous_validity_factor": float(
                            last_contiguous_time / np.max(training_times)
                        ),
                        "first_failure_time": (
                            None
                            if first_failure == len(pass_mask)
                            else float(broad_times[first_failure])
                        ),
                        "later_pass_reentry_after_first_failure": later_reentry,
                        "first_material_underprediction_time": (
                            None
                            if first_under is None
                            else float(broad_times[first_under])
                        ),
                        "first_material_underprediction_factor": (
                            None
                            if first_under is None
                            else float(
                                broad_times[first_under]
                                / np.max(training_times)
                            )
                        ),
                    }
                )

            for point in points:
                if point["branch_warning"]:
                    branch_rows.append(
                        {
                            "system": system_id,
                            "formula": formula_id,
                            "time_hartree_inverse": point[
                                "time_hartree_inverse"
                            ],
                            "selection_rules_agree": point[
                                "selection_rules_agree"
                            ],
                            "ground_overlap_probability": point[
                                "selected_ground_overlap_probability"
                            ],
                            "previous_overlap_probability": point[
                                "previous_branch_overlap_probability"
                            ],
                            "phase_gap_radians": point[
                                "selected_phase_gap_radians"
                            ],
                        }
                    )

    c08_rows = evaluate_synthetic_controls()
    summaries = {
        "C01": {
            "status": "complete",
            "curve_count": len(truth["systems"]) * len(truth["formulas"]),
            "estimator_comparison_row_count": len(c01_rows),
            "maximum_leading_coefficient_relative_difference_from_direct": max(
                row["a_p_relative_difference_from_direct"] for row in c01_rows
            ),
            "maximum_finite_estimator_selection_regret": max(
                row["direct_sampled_selection_regret"]
                for row in c01_rows
                if row["direct_sampled_selection_regret"] is not None
            ),
        },
        "C06": {
            "status": "complete",
            "comparison_count": len(c06_rows),
            "boundary_minimum_count": sum(
                row["refined_minimum_on_common_reliable_boundary"]
                for row in c06_rows
            ),
            "unrestricted_minimum_outside_reliable_prefix_count": sum(
                row["unrestricted_minimum_outside_formula_reliable_prefix"]
                for row in c06_rows
            ),
            "maximum_coarse_cost_regret": max(
                row["coarse_cost_over_refined_minus_one"] for row in c06_rows
            ),
            "optimum_policy": "all reported direct minima are sampled-grid minima",
        },
        "C08": {
            "status": (
                "complete" if all(row["passed"] for row in c08_rows) else "failed"
            ),
            "control_count": len(c08_rows),
            "controls_passed": sum(row["passed"] for row in c08_rows),
        },
        "E01": {
            "status": "complete",
            "sensitivity_row_count": len(e01_rows),
            "qualified_count": sum(row["qualified"] for row in e01_rows),
            "unqualified_count": sum(not row["qualified"] for row in e01_rows),
        },
        "E02": {
            "status": "complete",
            "model_fit_count": len(e02_rows),
            "maximum_scaled_condition_number": max(
                row["scaled_design_condition_number"] for row in e02_rows
            ),
            "minimum_condition_number_improvement_factor": min(
                row["condition_number_improvement_factor"] for row in e02_rows
            ),
        },
        "E03": {
            "status": "complete",
            "comparison_count": len(e03_rows),
            "signed_fit_better_count": sum(row["signed_fit_better"] for row in e03_rows),
            "absolute_fit_negative_prediction_case_count": sum(
                row["absolute_fit_negative_prediction_count"] > 0 for row in e03_rows
            ),
        },
        "E04": {
            "status": "complete",
            "model_count": len(e04_rows),
            "holdout_pass_count_by_terms": {
                str(terms): sum(
                    row["holdout_passes_0p05_epsilon"]
                    for row in e04_rows
                    if row["model_terms"] == terms
                )
                for terms in (1, 2, 3)
            },
            "overfit_warning_count": sum(row["overfit_warning"] for row in e04_rows),
        },
        "E06": {
            "status": "complete",
            "validity_row_count": len(e06_rows),
            "minimum_contiguous_validity_factor_by_terms": {
                str(terms): min(
                    row["contiguous_validity_factor"]
                    for row in e06_rows
                    if row["model_terms"] == terms
                )
                for terms in (1, 2, 3)
            },
            "later_reentry_count": sum(
                row["later_pass_reentry_after_first_failure"] for row in e06_rows
            ),
        },
        "F05_data_only": {
            "status": "data_collected_not_formally_complete",
            "phase_gap_and_overlap_saved_for_every_truth_point": True,
            "blocking_dependencies": ["F01", "F02"],
        },
        "branch_warning_count": len(branch_rows),
        "maximum_sequential_spot_shift_difference_hartree": max(
            row["sequential_spot_shift_absolute_difference_hartree"]
            for row in c06_rows
        ),
        "maximum_sequential_spot_unitary_difference": max(
            row["sequential_spot_unitary_frobenius_difference"]
            for row in c06_rows
        ),
    }
    return {
        "summaries": summaries,
        "c01_rows": c01_rows,
        "c06_rows": c06_rows,
        "c08_rows": c08_rows,
        "e01_rows": e01_rows,
        "e02_rows": e02_rows,
        "e03_rows": e03_rows,
        "e04_rows": e04_rows,
        "e06_rows": e06_rows,
        "branch_rows": branch_rows,
        "branch_summary_rows": branch_summary_rows,
    }


def _make_figures(output: Path, truth: dict[str, Any], analysis: dict[str, Any]) -> None:
    system = truth["systems"]["H4"]
    figure, axes = plt.subplots(2, 2, figsize=(11, 8), dpi=160, sharex=True)
    for axis, (formula_id, formula) in zip(axes.ravel(), system["formulas"].items()):
        times = np.asarray(
            [point["time_hartree_inverse"] for point in formula["points"]]
        )
        axis.loglog(
            times,
            [abs(point["signed_direct_shift_hartree"]) for point in formula["points"]],
            label="direct eigenvalue",
        )
        axis.loglog(
            times,
            [abs(point["signed_imaginary_proxy_hartree"]) for point in formula["points"]],
            label="Im(z)/t",
        )
        axis.loglog(
            times,
            [abs(point["signed_overlap_phase_hartree"]) for point in formula["points"]],
            label="arg(z)/t",
        )
        axis.axhline(TARGET_ERROR, color="black", linestyle=":", linewidth=0.8)
        axis.set_title(formula_id)
        axis.grid(True, which="both", alpha=0.2)
    axes[1, 0].set_xlabel("time (Hartree$^{-1}$)")
    axes[1, 1].set_xlabel("time (Hartree$^{-1}$)")
    axes[0, 0].set_ylabel("absolute shift (Hartree)")
    axes[1, 0].set_ylabel("absolute shift (Hartree)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3)
    figure.tight_layout(rect=(0, 0.05, 1, 1))
    figure.savefig(output / "c01_h4_proxy_comparison.png")
    plt.close(figure)

    rows = analysis["e04_rows"]
    labels = [f"{row['system']}/{row['formula']}" for row in rows if row["model_terms"] == 1]
    x = np.arange(len(labels))
    width = 0.24
    figure, axis = plt.subplots(figsize=(12, 5), dpi=160)
    for offset, terms in zip((-1, 0, 1), (1, 2, 3)):
        selected = [row for row in rows if row["model_terms"] == terms]
        axis.bar(
            x + offset * width,
            [row["holdout_signed_residual_linf_over_epsilon"] for row in selected],
            width,
            label=f"{terms} term",
        )
    axis.axhline(MODEL_RESIDUAL_LIMIT_OVER_EPSILON, color="black", linestyle=":")
    axis.set_yscale("log")
    axis.set_ylabel("max signed holdout residual / epsilon")
    axis.set_xticks(x, labels, rotation=40, ha="right")
    axis.legend()
    axis.grid(True, axis="y", which="both", alpha=0.2)
    figure.tight_layout()
    figure.savefig(output / "e04_holdout_residuals.png")
    plt.close(figure)


def _make_report(output: Path, result: dict[str, Any]) -> None:
    summaries = result["summaries"]
    c01 = summaries["C01"]
    c06 = summaries["C06"]
    c08 = summaries["C08"]
    e01 = summaries["E01"]
    e02 = summaries["E02"]
    e03 = summaries["E03"]
    e04 = summaries["E04"]
    e06 = summaries["E06"]
    lines = [
        "# X02 finite-time curve/model integrity batch",
        "",
        f"- Overall status: **{result['status']}**",
        "- Formal audit IDs: C01, C06, C08, E01, E02, E03, E04, E06",
        "- Systems: H2 and H4; formulas: Yoshida4, current_m3, two_term_center, Morales Y8m10b",
        "- All direct minima below are sampled-grid minima, not continuous-time global minima.",
        "- No coefficient search and no new molecule were used.",
        "",
        "## Shared truth data",
        "",
        f"Eight molecular PF curves were generated. Total direct points: {result['truth_point_count']}. "
        f"Branch warnings: {summaries['branch_warning_count']}.",
        "Every point stores the signed direct eigenvalue shift, signed Im(z)/t, signed arg(z)/t, "
        "ground/previous-branch overlaps, phase gap, unwrap integer, residuals, and timings.",
        "Primary minima and extrapolation scores stop at the first branch warning. The wider curves "
        "remain diagnostic data and are not silently treated as reliable target-branch truth.",
        "",
        "## C01: proxy versus direct eigenvalue shift",
        "",
        f"The maximum leading-coefficient relative difference from the direct fit was "
        f"`{c01['maximum_leading_coefficient_relative_difference_from_direct']:.6g}`. "
        f"The largest finite direct sampled-grid regret from an estimator's one-term analytic time "
        f"was `{c01['maximum_finite_estimator_selection_regret']:.6g}`.",
        "Estimator coefficients use the same five times selected by the canonical imaginary-proxy "
        "rolling window, so the comparison does not give one estimator extra points.",
        "",
        "## C06: minima and grid scope",
        "",
        f"Across {c06['comparison_count']} PF/system curves, the largest coarse-grid cost regret "
        f"relative to the refined sampled grid was `{c06['maximum_coarse_cost_regret']:.6g}`. "
        f"Common reliable-prefix boundary minima: {c06['boundary_minimum_count']}. "
        f"Unrestricted minima outside a formula's reliable branch prefix: "
        f"{c06['unrestricted_minimum_outside_reliable_prefix_count']}.",
        "The declared interval and both grids are saved. No interpolation value is promoted to a "
        "direct minimum.",
        f"Reliable-prefix sign-change brackets were locally refined. At each resulting minimum, "
        f"the cached and sequential builders agreed within "
        f"`{summaries['maximum_sequential_spot_shift_difference_hartree']:.3e}` Hartree in the "
        f"selected shift and `{summaries['maximum_sequential_spot_unitary_difference']:.3e}` in "
        "unitary Frobenius norm.",
        "",
        "## C08: singular and boundary controls",
        "",
        f"Synthetic controls passed {c08['controls_passed']}/{c08['control_count']}. "
        "Infeasible error budgets remain explicit; they are not clipped to a small positive denominator.",
        "",
        "## E01/E02: fit-window and conditioning",
        "",
        f"E01 evaluated {e01['sensitivity_row_count']} window/threshold combinations; "
        f"{e01['unqualified_count']} did not qualify and remain explicit. "
        f"E02's maximum scaled design condition number was "
        f"`{e02['maximum_scaled_condition_number']:.6g}`; the smallest raw/scaled improvement factor "
        f"was `{e02['minimum_condition_number_improvement_factor']:.6g}`.",
        "",
        "## E03/E04/E06: representation, term count, extrapolation",
        "",
        "E03/E04 score independent practical holdout points only through "
        "`min(1.2*t_ana, branch-reliable-prefix)`. E06 separately follows each model through the "
        "full leading branch-reliable prefix.",
        "",
        f"Signed fitting had the smaller maximum absolute-error residual in "
        f"{e03['signed_fit_better_count']}/{e03['comparison_count']} comparisons. "
        f"Absolute-error fits produced negative holdout predictions in "
        f"{e03['absolute_fit_negative_prediction_case_count']} comparisons.",
        "",
        "Holdout pass counts at max signed residual <= 0.05 epsilon:",
        "",
        "| model | passes / 8 curves | minimum contiguous validity factor |",
        "|---|---:|---:|",
    ]
    for terms in (1, 2, 3):
        lines.append(
            f"| {terms} term | {e04['holdout_pass_count_by_terms'][str(terms)]}/8 | "
            f"{e06['minimum_contiguous_validity_factor_by_terms'][str(terms)]:.6g} |"
        )
    lines.extend(
        [
            "",
            f"Training-fit/holdout overfit warnings: {e04['overfit_warning_count']}; "
            f"post-failure pass reentries: {e06['later_reentry_count']}. A later reentry does not "
            "extend the leading validity interval.",
            "",
            "## F05 data and next decision",
            "",
            "Physical energy and PF phase-gap fields were collected to avoid recomputation, but F05 "
            "is not marked complete because F01/F02 remain dependencies. The next choice is between "
            "the F01/F02/F05 mechanism batch and the C04/C05 frozen-QPE-budget batch.",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run_analysis() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    truth, timing = _build_truth()
    analysis = _analyze_truth(truth)
    component_status = {
        key: analysis["summaries"][key]["status"]
        for key in ("C01", "C06", "C08", "E01", "E02", "E03", "E04", "E06")
    }
    failed = any(value == "failed" for value in component_status.values())
    scientific_findings = bool(
        analysis["summaries"]["branch_warning_count"]
        or analysis["summaries"]["C06"]["boundary_minimum_count"]
        or analysis["summaries"]["E04"]["overfit_warning_count"]
        or analysis["summaries"]["E01"]["unqualified_count"]
    )
    status = "failed" if failed else "complete_with_findings" if scientific_findings else "complete"
    truth_rows = _flatten_truth_rows(truth)
    result = {
        "status": status,
        "audit_ids": ["C01", "C06", "C08", "E01", "E02", "E03", "E04", "E06"],
        "component_status": component_status,
        "created_at": datetime.now().astimezone().isoformat(),
        "scope": "H2/H4 shared signed finite-time curves; no PF coefficient search",
        "truth_point_count": len(truth_rows),
        "summaries": analysis["summaries"],
        "timing_seconds": {
            **timing,
            "total": float(time.perf_counter() - started),
        },
        "peak_cpu_memory_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        ),
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
            "gpu_used": False,
        },
        "git": _git_state(),
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (
                ROOT / "review_response/audit_x02_curve_model_integrity.py",
                ROOT / "review_response/validate_hchain_perturbative_estimator.py",
                ROOT / "src/trotterlib/sector_pf.py",
                ROOT / "src/trotterlib/fit_window.py",
            )
        },
    }
    analysis["truth_rows"] = truth_rows
    return result, truth, analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    result, truth, analysis = run_analysis()
    _write_json(output / "truth_curves.json", truth)
    _write_csv(output / "truth_points.csv", analysis["truth_rows"])
    for filename, key in (
        ("c01_estimator_comparison.csv", "c01_rows"),
        ("c06_grid_minima.csv", "c06_rows"),
        ("c08_synthetic_controls.csv", "c08_rows"),
        ("e01_window_sensitivity.csv", "e01_rows"),
        ("e02_conditioning.csv", "e02_rows"),
        ("e03_signed_vs_absolute.csv", "e03_rows"),
        ("e04_model_selection.csv", "e04_rows"),
        ("e06_extrapolation_distance.csv", "e06_rows"),
    ):
        _write_csv(output / filename, analysis[key])
    if analysis["branch_rows"]:
        _write_csv(output / "branch_warnings.csv", analysis["branch_rows"])
    _write_csv(output / "branch_summary.csv", analysis["branch_summary_rows"])
    _make_figures(output, truth, analysis)
    _write_json(output / "audit.json", result)
    _write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "audit_ids": result["audit_ids"],
            "component_status": result["component_status"],
            "created_at": result["created_at"],
            "scope": result["scope"],
            "git": result["git"],
            "environment": result["environment"],
            "timing_seconds": result["timing_seconds"],
            "peak_cpu_memory_bytes": result["peak_cpu_memory_bytes"],
            "prior_artifacts_overwritten": False,
            "coefficient_search_performed": False,
            "new_molecule_added": False,
        },
    )
    _make_report(output, result)
    print(output)
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
