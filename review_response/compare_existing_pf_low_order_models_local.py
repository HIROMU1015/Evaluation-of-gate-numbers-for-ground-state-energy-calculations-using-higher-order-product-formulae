"""Compare one- and two-term error models across existing product formulae.

This is an apples-to-apples H-chain diagnostic.  Each formula first obtains a
leading-order analytic schedule from the same rolling short-time rule.  Five
direct ground-connected eigenphase shifts at fixed relative times are then
used for either a leading-power recalibration or a signed two-term fit.  Each
model is tested at unused times around its own predicted QPE-cost optimum.

The run is intentionally limited to H2/H4/H5.  It answers whether adding the
next even power can rescue an existing formula; it is not molecular holdout
evidence for a newly designed coefficient vector.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import time
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

from search_pf_cost_predictability_m2_m3 import (
    pauli_rotation_count,
    projected_reference_candidate,
)
from trotterlib.config import BETA, TARGET_ERROR
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import symmetric_s2_sequence
from trotterlib.product_formula import (
    actual_circuit_optimized_4th_m5_list,
    morales_2025_y8m10b_list,
    yoshida_4th_list,
    yoshida_8th_list,
)
from trotterlib.sector_pf import build_sector_pf_unitary
from validate_hchain_perturbative_estimator import _prepare_sector_system


DEFAULT_OUTPUT = Path(
    "artifacts/existing_pf_low_order_model_comparison_20260913"
)
DEFAULT_CANDIDATE_RESULTS = Path(
    "artifacts/m3_joint_full_frozen_refinement_20260913/refinement_results.json"
)

EPSILON_E = float(TARGET_ERROR)
CALIBRATION_RELATIVE_TIMES = (0.2, 0.3, 0.4, 0.5, 0.6)
VALIDATION_RELATIVE_TO_T_STAR = (0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15)
OPTIMIZATION_RELATIVE_INTERVAL = (0.1, 1.4)
OPTIMIZATION_GRID_POINTS = 26001

FIT_GRID = tuple(float(value) for value in np.geomspace(0.02, 1.8, 34))
FIT_WINDOW = 5
FIT_NOISE_FLOOR = 5e-12
FIT_ORDER_TOLERANCE = 0.2
FIT_MINIMUM_R2 = 0.999

PASS_THRESHOLDS = {
    "eta_star": 0.01,
    "eta_min": 0.01,
    "eta_t": 0.05,
    "maximum_unseen_residual_over_epsilon": 0.05,
}

YOSHIDA6_M3_WEIGHTS = (
    1.315186320683908,
    -1.177679984178871,
    0.235573213359357,
    0.78451361047756,
)
CURRENT_M3_WEIGHTS = (
    -0.4737318199452465,
    0.3316118001935053,
    0.2092246690782796,
    0.1960294407008384,
)
TWO_TERM_CENTER_WEIGHTS = (
    -0.5479746372736223,
    0.4130665734843169,
    0.1864679228988850,
    0.1744528222536092,
)

DEFAULT_FORMULA_NAMES = (
    "yoshida4",
    "paper_new4",
    "m5",
    "current_m3",
    "two_term_center",
    "joint_refine_r0_s0046",
    "yoshida6_m3",
    "morales_y8m10b",
)


def _now() -> str:
    return datetime.now().astimezone().isoformat()


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


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_joint_candidate(path: Path) -> tuple[str, tuple[float, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = payload["ranked_candidates"][0]
    return str(selected["name"]), tuple(map(float, selected["weights"]))


def _formulae(candidate_results: Path) -> list[dict[str, Any]]:
    projected_new2 = projected_reference_candidate(2)
    joint_name, joint_weights = _load_joint_candidate(candidate_results)
    return [
        {
            "name": "yoshida4",
            "display_name": "Yoshida 4th",
            "formal_order": 4,
            "weights": tuple(yoshida_4th_list()),
            "provenance": "src/trotterlib/product_formula.py:yoshida_4th_list",
        },
        {
            "name": "paper_new4",
            "display_name": "paper 4th(new)",
            "formal_order": 4,
            "weights": tuple(map(float, projected_new2["weights"])),
            "provenance": (
                "published m=2 coefficients projected back onto the exact "
                "fourth-order constraint"
            ),
        },
        {
            "name": "m5",
            "display_name": "4th(m5_best)",
            "formal_order": 4,
            "weights": tuple(actual_circuit_optimized_4th_m5_list()),
            "provenance": (
                "src/trotterlib/product_formula.py:"
                "actual_circuit_optimized_4th_m5_list"
            ),
        },
        {
            "name": "current_m3",
            "display_name": "current m=3",
            "formal_order": 4,
            "weights": CURRENT_M3_WEIGHTS,
            "provenance": "fixed comparison coefficient vector",
        },
        {
            "name": "two_term_center",
            "display_name": "two_term_center m=3",
            "formal_order": 4,
            "weights": TWO_TERM_CENTER_WEIGHTS,
            "provenance": "fixed multi-molecule two-term candidate",
        },
        {
            "name": joint_name,
            "display_name": f"latest joint m=3 ({joint_name})",
            "formal_order": 4,
            "weights": joint_weights,
            "provenance": str(candidate_results),
        },
        {
            "name": "yoshida6_m3",
            "display_name": "Yoshida 6th m=3",
            "formal_order": 6,
            "weights": YOSHIDA6_M3_WEIGHTS,
            "provenance": (
                "artifacts/two_term_pf_design_validation_20260909/yoshida6"
            ),
        },
        {
            "name": "yoshida8",
            "display_name": "Yoshida 8th",
            "formal_order": 8,
            "weights": tuple(yoshida_8th_list()),
            "provenance": "src/trotterlib/product_formula.py:yoshida_8th_list",
        },
        {
            "name": "morales_y8m10b",
            "display_name": "Morales 8th Y8m10b",
            "formal_order": 8,
            "weights": tuple(morales_2025_y8m10b_list()),
            "provenance": (
                "src/trotterlib/product_formula.py:"
                "morales_2025_y8m10b_list"
            ),
        },
    ]


def _cost(time_value: float, error: float, rotations: int) -> float | None:
    if time_value <= 0.0 or error < 0.0 or error >= EPSILON_E:
        return None
    return float(
        BETA
        * int(rotations)
        / (float(time_value) * (EPSILON_E - float(error)))
    )


def _apply_pf(
    system: dict[str, Any], sequence: Sequence[float], time_value: float
) -> np.ndarray:
    unitary = build_sector_pf_unitary(
        system["group_spectra"],
        sequence,
        float(time_value),
        method="s2-cache",
    )
    return unitary @ np.asarray(system["ground_state"], dtype=np.complex128)


def _qualify_short_time_fit(
    times: Sequence[float], errors: Sequence[float], formal_order: int
) -> dict[str, Any]:
    windows = rolling_loglog_fits(
        np.asarray(times, dtype=float),
        np.asarray(errors, dtype=float),
        formal_order=int(formal_order),
        noise_floor=FIT_NOISE_FLOOR,
        window_size=FIT_WINDOW,
    )
    eligible = [
        window
        for window in windows
        if float(window["order_deviation"]) <= FIT_ORDER_TOLERANCE
        and float(window["r2"]) >= FIT_MINIMUM_R2
    ]
    selected = min(
        eligible, key=lambda window: int(window["start_index"]), default=None
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "times": list(map(float, times)),
        "errors_hartree": list(map(float, errors)),
        "formal_order": int(formal_order),
        "noise_floor": FIT_NOISE_FLOOR,
        "window_size": FIT_WINDOW,
        "order_tolerance": FIT_ORDER_TOLERANCE,
        "minimum_r2": FIT_MINIMUM_R2,
    }


def _short_time_fit(
    system: dict[str, Any], sequence: Sequence[float], formal_order: int
) -> dict[str, Any]:
    times: list[float] = []
    errors: list[float] = []
    points: list[dict[str, Any]] = []
    fit: dict[str, Any] | None = None
    for time_value in FIT_GRID:
        started = time.perf_counter()
        evolved = _apply_pf(system, sequence, time_value)
        overlap = complex(np.vdot(system["ground_state"], evolved))
        rotated = (
            np.exp(
                -1j
                * float(system["ground_energy_without_constant_hartree"])
                * float(time_value)
            )
            * overlap
        )
        error = abs(float(rotated.imag / float(time_value)))
        times.append(float(time_value))
        errors.append(error)
        points.append(
            {
                "time": float(time_value),
                "perturbative_error_hartree": error,
                "phase_rotated_overlap": rotated,
                "survival_probability": float(abs(rotated) ** 2),
                "elapsed_seconds": float(time.perf_counter() - started),
            }
        )
        if len(times) >= FIT_WINDOW:
            fit = _qualify_short_time_fit(times, errors, formal_order)
        if fit is not None and fit["qualified"]:
            break
    if fit is None or not fit["qualified"]:
        raise RuntimeError(
            f"short-time order {formal_order} did not qualify on the common grid"
        )
    fit["points"] = points
    fit["error_definition"] = (
        "abs(imag(exp(-i*E0*t)*<psi0|U_PF(t)|psi0>)/t)"
    )
    return fit


def _analytic_time(alpha: float, order: int) -> float:
    return float((EPSILON_E / ((int(order) + 1) * alpha)) ** (1.0 / order))


def _direct_point(
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    rotations: int,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    build_started = time.perf_counter()
    unitary = build_sector_pf_unitary(
        system["group_spectra"],
        sequence,
        float(time_value),
        method="s2-cache",
    )
    build_seconds = time.perf_counter() - build_started
    schur_started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - schur_started
    eigenvalues = np.diag(triangular)
    state = np.asarray(system["ground_state"], dtype=np.complex128)
    overlaps = np.abs(vectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    shift = float(
        np.angle(
            np.exp(
                -1j
                * float(system["ground_energy_without_constant_hartree"])
                * float(time_value)
            )
            * eigenvalue
        )
        / float(time_value)
    )
    residual = float(np.linalg.norm(unitary @ vector - eigenvalue * vector))
    point = {
        "time": float(time_value),
        "signed_direct_shift_hartree": shift,
        "direct_error_hartree": abs(shift),
        "direct_cost": _cost(time_value, abs(shift), rotations),
        "ground_overlap_probability": float(overlaps[selected]),
        "eigenpair_residual_2_norm": residual,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "selection_rule": "maximum exact-ground-state overlap in invariant sector",
        "timing_seconds": {
            "unitary_build": float(build_seconds),
            "schur": float(schur_seconds),
            "total": float(time.perf_counter() - started),
        },
    }
    del unitary, triangular, vectors
    return point, vector


def _fit_models(
    points: Sequence[dict[str, Any]],
    *,
    alpha: float,
    formal_order: int,
    analytic_time: float,
) -> dict[str, dict[str, Any]]:
    ordered = sorted(points, key=lambda point: float(point["time"]))
    relative = np.asarray(
        [float(point["relative_to_t_ana"]) for point in ordered], dtype=float
    )
    times = relative * float(analytic_time)
    shifts = np.asarray(
        [float(point["signed_direct_shift_hartree"]) for point in ordered],
        dtype=float,
    )
    leading_sign = float(np.sign(np.median(shifts)))
    if leading_sign == 0.0:
        raise RuntimeError("zero leading sign in direct calibration points")
    normalized = shifts / (leading_sign * float(alpha) * times**formal_order)

    refit_b0 = float(np.linalg.lstsq(
        np.ones((relative.size, 1)), normalized, rcond=None
    )[0][0])
    two_design = np.column_stack([np.ones_like(relative), relative**2])
    two_b0, two_b2 = map(
        float, np.linalg.lstsq(two_design, normalized, rcond=None)[0]
    )

    def pack(name: str, b0: float, b2: float, source: str):
        a_p = float(leading_sign * alpha * b0)
        a_p2 = float(leading_sign * alpha * b2 / analytic_time**2)
        fitted = b0 + b2 * relative**2
        return {
            "name": name,
            "source": source,
            "formal_order": int(formal_order),
            "coefficient_powers": [int(formal_order), int(formal_order + 2)],
            "coefficient_values": [a_p, a_p2],
            "leading_sign": leading_sign,
            "normalized_b0": float(b0),
            "normalized_b2": float(b2),
            "training_relative_to_t_ana": relative.tolist(),
            "normalized_training_residual_linf": float(
                np.max(np.abs(fitted - normalized))
            ),
        }

    return {
        "asymptotic_one_term": pack(
            "asymptotic_one_term",
            1.0,
            0.0,
            "common short-time alpha; direct points used only for the sign",
        ),
        "refitted_one_term": pack(
            "refitted_one_term",
            refit_b0,
            0.0,
            "same five direct points as the two-term model",
        ),
        "two_term": pack(
            "two_term",
            two_b0,
            two_b2,
            "same five direct points as the refitted one-term control",
        ),
    }


def _prediction(model: dict[str, Any], time_value: float) -> float:
    return float(
        sum(
            coefficient * float(time_value) ** power
            for power, coefficient in zip(
                model["coefficient_powers"], model["coefficient_values"]
            )
        )
    )


def _model_optimum(
    model: dict[str, Any], analytic_time: float, rotations: int
) -> dict[str, Any]:
    relative = np.linspace(
        OPTIMIZATION_RELATIVE_INTERVAL[0],
        OPTIMIZATION_RELATIVE_INTERVAL[1],
        OPTIMIZATION_GRID_POINTS,
    )
    times = relative * float(analytic_time)
    shifts = np.zeros_like(times)
    for power, coefficient in zip(
        model["coefficient_powers"], model["coefficient_values"]
    ):
        shifts += float(coefficient) * times ** int(power)
    errors = np.abs(shifts)
    costs = np.full_like(times, np.inf)
    valid = errors < EPSILON_E
    costs[valid] = (
        BETA
        * int(rotations)
        / (times[valid] * (EPSILON_E - errors[valid]))
    )
    selected = int(np.argmin(costs))
    if not np.isfinite(costs[selected]):
        raise RuntimeError(f"{model['name']} has no finite cost in search domain")
    return {
        "relative_to_t_ana": float(relative[selected]),
        "time": float(times[selected]),
        "signed_shift_hartree": float(shifts[selected]),
        "error_hartree": float(errors[selected]),
        "cost": float(costs[selected]),
        "optimization_relative_interval": list(OPTIMIZATION_RELATIVE_INTERVAL),
        "optimization_grid_points": int(OPTIMIZATION_GRID_POINTS),
        "at_optimization_boundary": bool(selected in (0, relative.size - 1)),
    }


def _validate_model(
    system: dict[str, Any],
    sequence: Sequence[float],
    rotations: int,
    model: dict[str, Any],
    analytic_time: float,
) -> dict[str, Any]:
    optimum = _model_optimum(model, analytic_time, rotations)
    t_star = float(optimum["time"])
    points: list[dict[str, Any]] = []
    previous_vector: np.ndarray | None = None
    for relative in VALIDATION_RELATIVE_TO_T_STAR:
        point, vector = _direct_point(
            system, sequence, float(relative) * t_star, rotations
        )
        predicted = _prediction(model, float(point["time"]))
        point.update(
            {
                "relative_to_t_star": float(relative),
                "relative_to_t_ana": float(point["time"] / analytic_time),
                "model_signed_shift_hartree": predicted,
                "model_error_hartree": abs(predicted),
                "model_cost": _cost(point["time"], abs(predicted), rotations),
                "signed_residual_hartree": float(
                    point["signed_direct_shift_hartree"] - predicted
                ),
                "residual_over_epsilon": float(
                    abs(point["signed_direct_shift_hartree"] - predicted)
                    / EPSILON_E
                ),
                "selected_vector_overlap_with_previous_probability": (
                    None
                    if previous_vector is None
                    else float(abs(np.vdot(previous_vector, vector)) ** 2)
                ),
            }
        )
        points.append(point)
        previous_vector = vector

    at_star = next(
        point for point in points if float(point["relative_to_t_star"]) == 1.0
    )
    finite = [point for point in points if point["direct_cost"] is not None]
    if not finite or at_star["direct_cost"] is None:
        raise RuntimeError(f"non-finite direct cost for {model['name']}")
    direct_minimum = min(finite, key=lambda point: float(point["direct_cost"]))
    minimum_index = points.index(direct_minimum)
    local_minimum_bracketed = 0 < minimum_index < len(points) - 1
    eta_star = float(
        abs(float(optimum["cost"]) - float(at_star["direct_cost"]))
        / float(at_star["direct_cost"])
    )
    eta_min = float(
        float(at_star["direct_cost"]) / float(direct_minimum["direct_cost"]) - 1.0
    )
    eta_t = float(
        abs(float(optimum["time"]) / float(direct_minimum["time"]) - 1.0)
    )
    maximum_residual = float(
        max(float(point["residual_over_epsilon"]) for point in points)
    )
    metrics = {
        "eta_star": eta_star,
        "eta_min": eta_min,
        "eta_t": eta_t,
        "maximum_unseen_residual_over_epsilon": maximum_residual,
        "minimum_ground_overlap_probability": float(
            min(float(point["ground_overlap_probability"]) for point in points)
        ),
        "minimum_adjacent_selected_vector_overlap_probability": float(
            min(
                float(point["selected_vector_overlap_with_previous_probability"])
                for point in points
                if point["selected_vector_overlap_with_previous_probability"]
                is not None
            )
        ),
        "maximum_eigenpair_residual_2_norm": float(
            max(float(point["eigenpair_residual_2_norm"]) for point in points)
        ),
        "local_minimum_bracketed": bool(local_minimum_bracketed),
    }
    checks = {
        key: bool(metrics[key] <= threshold)
        for key, threshold in PASS_THRESHOLDS.items()
    }
    checks["model_optimum_interior"] = not bool(
        optimum["at_optimization_boundary"]
    )
    checks["direct_local_minimum_bracketed"] = bool(local_minimum_bracketed)
    return {
        "model": model,
        "model_optimum": optimum,
        "direct_validation_points": points,
        "direct_grid_minimum": direct_minimum,
        "metrics": metrics,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _summaries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for formula in payload["formulae"]:
        formula_name = formula["name"]
        for model_name in (
            "asymptotic_one_term",
            "refitted_one_term",
            "two_term",
        ):
            records = [
                payload["systems"][system_name]["formulae"][formula_name][
                    "models"
                ][model_name]
                for system_name in payload["systems"]
            ]
            rows.append(
                {
                    "formula": formula_name,
                    "display_name": formula["display_name"],
                    "formal_order": int(formula["formal_order"]),
                    "s2_stage_count": int(formula["s2_stage_count"]),
                    "model": model_name,
                    "passed": int(sum(bool(record["passed"]) for record in records)),
                    "conditions": len(records),
                    "worst_eta_star": float(
                        max(record["metrics"]["eta_star"] for record in records)
                    ),
                    "worst_eta_min": float(
                        max(record["metrics"]["eta_min"] for record in records)
                    ),
                    "worst_eta_t": float(
                        max(record["metrics"]["eta_t"] for record in records)
                    ),
                    "worst_residual_over_epsilon": float(
                        max(
                            record["metrics"][
                                "maximum_unseen_residual_over_epsilon"
                            ]
                            for record in records
                        )
                    ),
                    "minimum_ground_overlap_probability": float(
                        min(
                            record["metrics"][
                                "minimum_ground_overlap_probability"
                            ]
                            for record in records
                        )
                    ),
                    "maximum_eigenpair_residual_2_norm": float(
                        max(
                            record["metrics"][
                                "maximum_eigenpair_residual_2_norm"
                            ]
                            for record in records
                        )
                    ),
                }
            )
    return rows


def _write_report(output_dir: Path, payload: dict[str, Any]) -> None:
    by_formula_model = {
        (row["formula"], row["model"]): row for row in payload["summaries"]
    }
    already_predictable: list[str] = []
    rescued_by_two_terms: list[str] = []
    not_rescued: list[str] = []
    refit_already_sufficient: list[str] = []
    for formula in payload["formulae"]:
        key = formula["name"]
        asymptotic = by_formula_model[(key, "asymptotic_one_term")]
        refitted = by_formula_model[(key, "refitted_one_term")]
        two_term = by_formula_model[(key, "two_term")]
        conditions = int(two_term["conditions"])
        display_name = str(formula["display_name"])
        if int(asymptotic["passed"]) == conditions:
            already_predictable.append(display_name)
        elif int(two_term["passed"]) == conditions:
            rescued_by_two_terms.append(display_name)
        else:
            not_rescued.append(display_name)
        if (
            int(asymptotic["passed"]) < conditions
            and int(refitted["passed"]) == conditions
        ):
            refit_already_sufficient.append(display_name)

    lines = [
        "# Existing PF one-vs-two-term comparison",
        "",
        f"Status: {payload['status']}",
        "",
        (
            "All formulae use the same rolling short-time qualification rule, "
            "five direct calibration points at 0.2--0.6 t_ana, and seven unused "
            "direct points at 0.85--1.15 of each model's own predicted optimum."
        ),
        "",
        (
            "The next even power is t^(p+2): t4+t6 for fourth order, t6+t8 "
            "for sixth order, and t8+t10 for eighth order."
        ),
        "",
        "## Main result",
        "",
        (
            "- Already passes the asymptotic one-term protocol: "
            + (", ".join(already_predictable) or "none")
            + "."
        ),
        (
            "- Fails the asymptotic one-term protocol but passes with two "
            "terms: "
            + (", ".join(rescued_by_two_terms) or "none")
            + "."
        ),
        (
            "- Not rescued by the next even-power term: "
            + (", ".join(not_rescued) or "none")
            + "."
        ),
        (
            "- A direct refit of the leading coefficient is already sufficient "
            "for: "
            + (", ".join(refit_already_sufficient) or "none")
            + ".  For these formulae this baseline does not establish that the "
            "second term is necessary."
        ),
        "",
        (
            "| PF | p | S2 stages | asymptotic one-term pass | direct-refit "
            "one-term pass | two-term pass | two-term worst eta_* | "
            "two-term worst residual/eps |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for formula in payload["formulae"]:
        key = formula["name"]
        asymptotic = by_formula_model[(key, "asymptotic_one_term")]
        refitted = by_formula_model[(key, "refitted_one_term")]
        two_term = by_formula_model[(key, "two_term")]
        lines.append(
            f"| {formula['display_name']} | {formula['formal_order']} | "
            f"{formula['s2_stage_count']} | "
            f"{asymptotic['passed']}/{asymptotic['conditions']} | "
            f"{refitted['passed']}/{refitted['conditions']} | "
            f"{two_term['passed']}/{two_term['conditions']} | "
            f"{two_term['worst_eta_star']:.6g} | "
            f"{two_term['worst_residual_over_epsilon']:.6g} |"
        )

    lines.extend(
        [
            "",
            "## Per-system two-term result",
            "",
            (
                "| system | PF | t*/t_ana | eta_* | eta_min | eta_t | "
                "residual/eps | direct cost at t* | pass |"
            ),
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for system_name, system in payload["systems"].items():
        for formula_name, result in system["formulae"].items():
            two_term = result["models"]["two_term"]
            metrics = two_term["metrics"]
            at_star = next(
                point
                for point in two_term["direct_validation_points"]
                if float(point["relative_to_t_star"]) == 1.0
            )
            lines.append(
                f"| {system_name} | {result['display_name']} | "
                f"{two_term['model_optimum']['relative_to_t_ana']:.6g} | "
                f"{metrics['eta_star']:.6g} | {metrics['eta_min']:.6g} | "
                f"{metrics['eta_t']:.6g} | "
                f"{metrics['maximum_unseen_residual_over_epsilon']:.6g} | "
                f"{float(at_star['direct_cost']):.8g} | {two_term['passed']} |"
            )

    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            (
                "- H2/H4/H5 provide a controlled baseline comparison, not an "
                "unseen-molecule generalization claim."
            ),
            (
                "- A two-term pass demonstrates that a more expressive error "
                "model rescues cost prediction; it does not by itself show that "
                "the PF preserves a single leading-power scaling law."
            ),
            (
                "- The direct-refit one-term control separates the effect of the "
                "next even power from merely changing the leading coefficient."
            ),
            "",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    formulae = _formulae(args.candidate_results)
    for formula in formulae:
        formula["s2_sequence"] = symmetric_s2_sequence(formula["weights"])
        formula["s2_stage_count"] = len(formula["s2_sequence"])
    requested = set(args.formulae)
    unknown = requested - {formula["name"] for formula in formulae}
    if unknown:
        raise ValueError(f"unknown formulae: {sorted(unknown)}")
    formulae = [formula for formula in formulae if formula["name"] in requested]

    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "started_at": _now(),
        "purpose": (
            "Determine whether the next even-power error term rescues existing "
            "PF QPE-cost predictions under one common direct validation protocol"
        ),
        "scope": {
            "systems": [f"H{value}" for value in args.h_chains],
            "interpretation": (
                "controlled H-chain baseline comparison; not molecular holdout"
            ),
        },
        "protocol": {
            "epsilon_E_hartree": EPSILON_E,
            "beta": float(BETA),
            "short_time_fit_grid": list(FIT_GRID),
            "short_time_fit_window": FIT_WINDOW,
            "short_time_noise_floor": FIT_NOISE_FLOOR,
            "short_time_order_tolerance": FIT_ORDER_TOLERANCE,
            "short_time_minimum_r2": FIT_MINIMUM_R2,
            "calibration_relative_to_t_ana": list(
                CALIBRATION_RELATIVE_TIMES
            ),
            "validation_relative_to_t_star": list(
                VALIDATION_RELATIVE_TO_T_STAR
            ),
            "pass_thresholds": PASS_THRESHOLDS,
        },
        "formulae": formulae,
        "systems": {},
        "summaries": [],
    }
    checkpoint = output_dir / "comparison.json"
    _atomic_json(checkpoint, payload)

    for h_chain in args.h_chains:
        system_name = f"H{int(h_chain)}"
        print(f"prepare {system_name}", flush=True)
        prepared = _prepare_sector_system(int(h_chain))
        system_result: dict[str, Any] = {
            "metadata": {
                "num_qubits": int(prepared["num_qubits"]),
                "num_groups": int(prepared["num_groups"]),
                "sector": prepared["sector"],
            },
            "formulae": {},
        }
        payload["systems"][system_name] = system_result
        _atomic_json(checkpoint, payload)

        for formula in formulae:
            formula_name = str(formula["name"])
            print(f"{system_name} {formula_name}: short-time fit", flush=True)
            order = int(formula["formal_order"])
            sequence = tuple(map(float, formula["s2_sequence"]))
            rotations = pauli_rotation_count(system_name, formula["weights"])
            result: dict[str, Any] = {
                "display_name": formula["display_name"],
                "formal_order": order,
                "rotations_per_pf_step": int(rotations),
                "status": "short_time_fit",
            }
            system_result["formulae"][formula_name] = result
            _atomic_json(checkpoint, payload)

            fit = _short_time_fit(prepared, sequence, order)
            alpha = float(fit["selected_window"]["fixed_order_alpha"])
            analytic_time = _analytic_time(alpha, order)
            result.update(
                {
                    "short_time_fit": fit,
                    "alpha": alpha,
                    "analytic_time": analytic_time,
                    "calibration_direct_points": [],
                    "models": {},
                    "status": "calibration",
                }
            )
            _atomic_json(checkpoint, payload)

            previous_vector: np.ndarray | None = None
            for relative in CALIBRATION_RELATIVE_TIMES:
                point, vector = _direct_point(
                    prepared,
                    sequence,
                    float(relative) * analytic_time,
                    rotations,
                )
                point.update(
                    {
                        "relative_to_t_ana": float(relative),
                        "selected_vector_overlap_with_previous_probability": (
                            None
                            if previous_vector is None
                            else float(abs(np.vdot(previous_vector, vector)) ** 2)
                        ),
                    }
                )
                result["calibration_direct_points"].append(point)
                previous_vector = vector
                _atomic_json(checkpoint, payload)

            models = _fit_models(
                result["calibration_direct_points"],
                alpha=alpha,
                formal_order=order,
                analytic_time=analytic_time,
            )
            result["status"] = "validation"
            for model_name, model in models.items():
                print(
                    f"{system_name} {formula_name}: validate {model_name}",
                    flush=True,
                )
                result["models"][model_name] = _validate_model(
                    prepared,
                    sequence,
                    rotations,
                    model,
                    analytic_time,
                )
                _atomic_json(checkpoint, payload)
            result["status"] = "complete"
            _atomic_json(checkpoint, payload)

    payload["summaries"] = _summaries(payload)
    payload["status"] = "complete"
    payload["completed_at"] = _now()
    _atomic_json(checkpoint, payload)
    _write_report(output_dir, payload)
    print(f"saved: {output_dir}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    all_names = [formula["name"] for formula in _formulae(DEFAULT_CANDIDATE_RESULTS)]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h-chains", nargs="+", type=int, default=[2, 4, 5])
    parser.add_argument(
        "--formulae",
        nargs="+",
        choices=all_names,
        default=list(DEFAULT_FORMULA_NAMES),
    )
    parser.add_argument(
        "--candidate-results", type=Path, default=DEFAULT_CANDIDATE_RESULTS
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
