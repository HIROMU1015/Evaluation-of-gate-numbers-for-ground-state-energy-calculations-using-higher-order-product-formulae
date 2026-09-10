"""Compare original, refitted, and two-term error models on saved holdouts.

The primary validation set is frozen to the seven saved local direct points.
Exact direct points at the original and refitted one-term optima are added.
Each saved two-term optimum is also recomputed as a numerical reproduction
sentinel; the source JSON files are never modified.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import traceback
from typing import Any

import numpy as np

import run_two_term_pf_m3_holdout_server2 as holdout
from trotterlib.pf_decomposition import symmetric_s2_sequence

SOURCE_COMMIT = "92df2dbda9de5f41183af551b7acec06d88a3ada"
BASELINE_COMMIT = "d2360f49f9a754d1850eab60cd483f684bd8bffb"
SOURCE_DIR = Path(
    "artifacts/two_term_pf_m3_holdout_server2_20260910_d2360f4_cpu"
)
MODEL_NAMES = ("original_one_term", "refit_one_term", "two_term")
HASH_FIELDS = (
    "hamiltonian_term_order_sha256",
    "ordered_grouping_structure_sha256",
    "unordered_grouping_structure_sha256",
)
STRUCTURE_HASH_FIELDS = (
    "ordered_grouping_structure_sha256",
    "unordered_grouping_structure_sha256",
)
REPRODUCTION_ENERGY_TOLERANCE_HARTREE = 1e-12
REPRODUCTION_SHIFT_TOLERANCE_HARTREE = 1e-10
REPRODUCTION_COST_RELATIVE_TOLERANCE = 1e-6
PASS_THRESHOLDS = {
    "predicted_time_cost_relative_error": 0.01,
    "direct_cost_loss_against_saved_local_grid": 0.01,
    "predicted_time_difference_from_saved_local_grid_minimum": 0.05,
    "maximum_saved_unseen_residual_over_epsilon": 0.05,
}

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

def _git_state() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]

    def run(*command: str) -> str:
        return subprocess.run(
            command, cwd=root, text=True, capture_output=True, check=False
        ).stdout.strip()

    status = run("git", "status", "--porcelain").splitlines()
    return {
        "commit": run("git", "rev-parse", "HEAD") or None,
        "branch": run("git", "branch", "--show-current") or None,
        "dirty": bool(status),
        "status": status,
    }

def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _source_files(source_dir: Path) -> dict[str, Path]:
    result = {
        condition: source_dir / f"{condition}.json"
        for condition in holdout.CONDITIONS
    }
    missing = [str(path) for path in result.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing source JSON: {missing}")
    return result

def _model_shift(model: dict[str, Any], time_value: float) -> float:
    return float(
        float(model["a4"]) * float(time_value) ** 4
        + float(model["a6"]) * float(time_value) ** 6
    )

def _model_definitions(formula: dict[str, Any]) -> dict[str, dict[str, Any]]:
    training = sorted(
        formula["training_direct_points"],
        key=lambda point: float(point["relative_to_t_ana"]),
    )
    observed_relative = tuple(
        float(point["relative_to_t_ana"]) for point in training
    )
    if not np.allclose(
        observed_relative,
        holdout.TRAINING_RELATIVE_TIMES,
        atol=1e-14,
        rtol=0.0,
    ):
        raise RuntimeError(f"training grid changed: {observed_relative}")
    times = np.asarray([float(point["time"]) for point in training])
    shifts = np.asarray(
        [float(point["signed_direct_shift_hartree"]) for point in training]
    )
    scaled = shifts / times**holdout.FORMAL_ORDER
    sign = float(np.sign(np.median(scaled)))
    if sign == 0.0:
        raise RuntimeError("training shifts have zero median sign")
    alpha = float(formula["alpha"])
    analytic_time = float(formula["analytic_time"])
    refit_a4 = float(np.mean(scaled))
    refit_time = float(
        (holdout.EPSILON_E / (5.0 * abs(refit_a4))) ** 0.25
    )
    recomputed_two_term = holdout._fit_two_term(
        training, alpha, analytic_time
    )
    stored_two_term = formula["two_term_model"]
    consistency = {
        key: abs(float(recomputed_two_term[key]) - float(stored_two_term[key]))
        for key in ("a4", "a6", "normalized_b0", "normalized_b2")
    }
    if max(consistency.values()) > 1e-13:
        raise RuntimeError(
            f"stored two-term coefficients do not reproduce: {consistency}"
        )
    rotations = int(formula["rotations_per_pf_step"])
    two_term_optimum = holdout._model_optimum(
        recomputed_two_term, analytic_time, rotations
    )
    stored_optimum = formula["two_term_model_optimum"]
    if abs(
        float(two_term_optimum["time"]) - float(stored_optimum["time"])
    ) > 1e-12:
        raise RuntimeError("stored two-term optimum does not reproduce")
    definitions = {
        "original_one_term": {
            "formula": "delta_E_original(t) = s*alpha*t^4",
            "fit_rule": (
                "alpha from the frozen common perturbative fit; sign is the "
                "median sign of delta_E_direct/t^4 on the three training points"
            ),
            "a4": float(sign * alpha),
            "a6": 0.0,
            "sign": sign,
            "predicted_optimal_time": analytic_time,
        },
        "refit_one_term": {
            "formula": "delta_E_refit(t) = b4*t^4",
            "fit_rule": (
                "same normalized least-squares objective as the two-term fit, "
                "with only an intercept: b4 = mean(delta_E_direct/t^4)"
            ),
            "a4": refit_a4,
            "a6": 0.0,
            "sign": float(np.sign(refit_a4)),
            "predicted_optimal_time": refit_time,
        },
        "two_term": {
            "formula": "delta_E_2term(t) = a4*t^4 + a6*t^6",
            "fit_rule": stored_two_term["fit_rule"],
            "a4": float(recomputed_two_term["a4"]),
            "a6": float(recomputed_two_term["a6"]),
            "sign": float(recomputed_two_term["leading_sign"]),
            "normalized_b0": float(recomputed_two_term["normalized_b0"]),
            "normalized_b2": float(recomputed_two_term["normalized_b2"]),
            "predicted_optimal_time": float(two_term_optimum["time"]),
            "optimization_domain_relative_to_t_ana": list(
                holdout.MODEL_OPTIMIZATION_INTERVAL
            ),
            "stored_recalculation_absolute_differences": consistency,
        },
    }
    for model in definitions.values():
        prediction = _model_shift(model, model["predicted_optimal_time"])
        model["predicted_shift_hartree"] = prediction
        model["predicted_error_hartree"] = abs(prediction)
        model["predicted_cost"] = holdout._cost(
            model["predicted_optimal_time"], abs(prediction), rotations
        )
    return definitions

def _accepted_sampled_intervals(
    predictions: Sequence[dict[str, Any]], threshold: float
) -> dict[str, Any]:
    ordered = sorted(predictions, key=lambda point: float(point["time"]))
    intervals: list[list[float]] = []
    current: list[float] = []
    accepted_points = []
    for point in ordered:
        relative = float(point["relative_to_t_ana"])
        if float(point["residual_over_epsilon"]) <= float(threshold):
            current.append(relative)
            accepted_points.append(relative)
        elif current:
            intervals.append([current[0], current[-1]])
            current = []
    if current:
        intervals.append([current[0], current[-1]])
    return {
        "criterion": (
            "abs(delta_E_direct-delta_E_model)/epsilon_E <= 0.05"
        ),
        "sampled_points_relative_to_t_ana": accepted_points,
        "sampled_contiguous_intervals_relative_to_t_ana": intervals,
        "accepted_count": len(accepted_points),
        "total_count": len(ordered),
        "all_saved_unseen_points_accepted": len(accepted_points) == len(ordered),
        "not_a_continuous_time_claim": True,
    }

def _saved_model_comparison(
    condition: str,
    formula_name: str,
    formula: dict[str, Any],
) -> dict[str, Any]:
    definitions = _model_definitions(formula)
    validation = sorted(
        formula["local_direct_points"], key=lambda point: float(point["time"])
    )
    observed_grid = tuple(
        float(point["relative_to_t_star"]) for point in validation
    )
    expected_grid = (0.9, 0.95, 0.975, 1.0, 1.025, 1.05, 1.1)
    if not np.allclose(observed_grid, expected_grid, atol=1e-14, rtol=0.0):
        raise RuntimeError(
            f"{condition}/{formula_name}: local grid changed: {observed_grid}"
        )
    direct_minimum = min(
        (point for point in validation if point["direct_cost"] is not None),
        key=lambda point: float(point["direct_cost"]),
    )
    model_records = {}
    for model_name, definition in definitions.items():
        predictions = []
        for point in validation:
            predicted_shift = _model_shift(definition, float(point["time"]))
            predicted_cost = holdout._cost(
                float(point["time"]),
                abs(predicted_shift),
                int(formula["rotations_per_pf_step"]),
            )
            direct_cost = point["direct_cost"]
            predictions.append(
                {
                    "time": float(point["time"]),
                    "relative_to_t_ana": float(point["relative_to_t_ana"]),
                    "relative_to_t_star": float(point["relative_to_t_star"]),
                    "signed_direct_shift_hartree": float(
                        point["signed_direct_shift_hartree"]
                    ),
                    "signed_model_shift_hartree": predicted_shift,
                    "signed_residual_hartree": float(
                        point["signed_direct_shift_hartree"] - predicted_shift
                    ),
                    "residual_over_epsilon": float(
                        abs(
                            float(point["signed_direct_shift_hartree"])
                            - predicted_shift
                        )
                        / holdout.EPSILON_E
                    ),
                    "direct_cost": direct_cost,
                    "model_cost": predicted_cost,
                    "cost_relative_error": (
                        None
                        if direct_cost is None or predicted_cost is None
                        else abs(float(predicted_cost) - float(direct_cost))
                        / float(direct_cost)
                    ),
                }
            )
        maximum_residual = max(
            float(point["residual_over_epsilon"]) for point in predictions
        )
        model_records[model_name] = {
            "definition": definition,
            "saved_unseen_predictions": predictions,
            "maximum_saved_unseen_residual_over_epsilon": maximum_residual,
            "maximum_saved_unseen_cost_relative_error": max(
                float(point["cost_relative_error"])
                for point in predictions
                if point["cost_relative_error"] is not None
            ),
            "accepted_sampled_time_range": _accepted_sampled_intervals(
                predictions,
                PASS_THRESHOLDS[
                    "maximum_saved_unseen_residual_over_epsilon"
                ],
            ),
            "formal_predicted_time_direct_evaluation": (
                "already_saved"
                if model_name == "two_term"
                else "additional_exact_direct_point_required"
            ),
        }
    return {
        "condition": condition,
        "formula": formula_name,
        "weights": formula["weights"],
        "rotations_per_pf_step": int(formula["rotations_per_pf_step"]),
        "training_points_relative_to_t_ana": list(
            holdout.TRAINING_RELATIVE_TIMES
        ),
        "training_points_excluded_from_validation": True,
        "saved_unseen_grid_relative_to_t_star": list(expected_grid),
        "saved_unseen_point_count": len(validation),
        "saved_local_direct_minimum": {
            "time": float(direct_minimum["time"]),
            "relative_to_t_ana": float(direct_minimum["relative_to_t_ana"]),
            "relative_to_t_star": float(direct_minimum["relative_to_t_star"]),
            "direct_cost": float(direct_minimum["direct_cost"]),
        },
        "models": model_records,
    }

def reaggregate_saved(source_dir: Path, output: Path) -> dict[str, Any]:
    records = []
    for condition, path in _source_files(source_dir).items():
        source = _load(path)
        if source.get("status") != "complete":
            raise RuntimeError(f"source is not complete: {path}")
        for formula_name in holdout.FORMULAS:
            records.append(
                _saved_model_comparison(
                    condition, formula_name, source["formulas"][formula_name]
                )
            )
    payload = {
        "status": "complete",
        "completed_at": _now(),
        "phase": "saved-points-only reaggregation before new PF action",
        "source_commit": SOURCE_COMMIT,
        "baseline_commit": BASELINE_COMMIT,
        "source_directory": str(source_dir.resolve()),
        "source_json_overwritten": False,
        "primary_validation_definition": {
            "points": "seven saved local_direct_points for each condition/PF",
            "training_points_excluded": list(holdout.TRAINING_RELATIVE_TIMES),
            "same_points_and_direct_denominators_for_all_three_models": True,
        },
        "refit_fairness_rule": (
            "one- and two-term refits use the same normalized least-squares "
            "objective; model complexity is the only fit difference"
        ),
        "records": records,
    }
    _atomic_json(output, payload)
    return payload

def _point_with_all_model_predictions(
    point: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    rotations: int,
):
    predictions = {}
    for name, definition in definitions.items():
        shift = _model_shift(definition, float(point["time"]))
        predictions[name] = {
            "signed_shift_hartree": shift,
            "error_hartree": abs(shift),
            "cost": holdout._cost(float(point["time"]), abs(shift), rotations),
            "signed_residual_hartree": float(
                point["signed_direct_shift_hartree"] - shift
            ),
            "residual_over_epsilon": float(
                abs(float(point["signed_direct_shift_hartree"]) - shift)
                / holdout.EPSILON_E
            ),
        }
    result = dict(point)
    result["all_model_predictions"] = predictions
    return result

def additional_worker(args: argparse.Namespace) -> int:
    condition = str(args.condition)
    source_path = Path(args.source_dir) / f"{condition}.json"
    source = _load(source_path)
    output = Path(args.output)
    work_dir = output.parent / (output.stem + "_work")
    work_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "status": "running",
        "started_at": _now(),
        "condition": condition,
        "source": str(source_path.resolve()),
        "source_overwritten": False,
        "environment": {
            "python": platform.python_version(),
            "python_executable": os.path.realpath(sys.executable),
            "blas_threads": int(args.blas_threads),
            "component_processes": int(args.component_processes),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
        "system_reproduction": None,
        "formulas": {},
    }

    def checkpoint() -> None:
        _atomic_json(output, payload)

    checkpoint()
    started = time.perf_counter()
    try:
        print(f"{condition}: reproduce system", flush=True)
        system, metadata = holdout._prepare_system(
            condition,
            holdout.CONDITIONS[condition],
            work_dir,
            int(args.component_processes),
        )
        hashes_match = {
            key: metadata[key] == source["system"][key] for key in HASH_FIELDS
        }
        energy_differences = {
            key: abs(float(metadata[key]) - float(source["system"][key]))
            for key in (
                "ground_energy_without_constant_hartree",
                "removed_constant_hartree",
                "scf_energy_hartree",
            )
        }
        reproduction_checks = {
            "structure_hashes_exact": all(
                hashes_match[key] for key in STRUCTURE_HASH_FIELDS
            ),
            "energies_within_tolerance": all(
                value <= REPRODUCTION_ENERGY_TOLERANCE_HARTREE
                for value in energy_differences.values()
            ),
            "active_orbitals_exact": (
                metadata["active_spatial_orbital_indices"]
                == source["system"]["active_spatial_orbital_indices"]
            ),
            "group_count_exact": (
                metadata["group_count"] == source["system"]["group_count"]
            ),
            "term_count_exact": (
                metadata["nonidentity_pauli_term_count"]
                == source["system"]["nonidentity_pauli_term_count"]
            ),
            "sector_dimensions_exact": (
                metadata["population_sector_dimension"]
                == source["system"]["population_sector_dimension"]
                and metadata["restricted_dimension"]
                == source["system"]["restricted_dimension"]
            ),
        }
        payload["system_reproduction"] = {
            "metadata": metadata,
            "source_hashes": {
                key: source["system"][key] for key in HASH_FIELDS
            },
            "exact_hashes_match": hashes_match,
            "energy_absolute_differences_hartree": energy_differences,
            "energy_tolerance_hartree": REPRODUCTION_ENERGY_TOLERANCE_HARTREE,
            "checks": reproduction_checks,
            "numerically_equivalent": all(reproduction_checks.values()),
            "exact_coefficient_hash_note": (
                "The coefficient-inclusive hash may differ because rerunning "
                "SCF changes last-bit floating-point coefficients. Exact "
                "group structures, metadata, energies, and a saved direct-point "
                "sentinel are independently gated."
            ),
        }
        checkpoint()
        if not all(reproduction_checks.values()):
            raise RuntimeError(
                f"{condition}: system reproduction failed: {reproduction_checks}"
            )
        payload["status"] = "direct_points"
        checkpoint()
        for formula_name in holdout.FORMULAS:
            source_formula = source["formulas"][formula_name]
            definitions = _model_definitions(source_formula)
            sequence = symmetric_s2_sequence(source_formula["weights"])
            rotations = holdout._rotation_count(system, sequence)
            if rotations != int(source_formula["rotations_per_pf_step"]):
                raise RuntimeError(
                    f"{condition}/{formula_name}: rotation count changed"
                )
            formula_payload = {
                "status": "running",
                "weights": source_formula["weights"],
                "rotations_per_pf_step": rotations,
                "model_definitions": definitions,
                "reproduction_sentinel": None,
                "additional_direct_points": {},
            }
            payload["formulas"][formula_name] = formula_payload
            checkpoint()
            source_sentinel = min(
                source_formula["local_direct_points"],
                key=lambda point: abs(
                    float(point["relative_to_t_star"]) - 1.0
                ),
            )
            print(
                f"{condition}/{formula_name}: reproduce saved direct sentinel",
                flush=True,
            )
            recomputed_sentinel = holdout._direct_point(
                system,
                sequence,
                float(source_sentinel["time"]),
                rotations,
            )
            signed_shift_difference = abs(
                float(recomputed_sentinel["signed_direct_shift_hartree"])
                - float(source_sentinel["signed_direct_shift_hartree"])
            )
            source_cost = float(source_sentinel["direct_cost"])
            recomputed_cost = float(recomputed_sentinel["direct_cost"])
            direct_cost_relative_difference = abs(
                recomputed_cost / source_cost - 1.0
            )
            sentinel_checks = {
                "signed_shift_within_tolerance": (
                    signed_shift_difference
                    <= REPRODUCTION_SHIFT_TOLERANCE_HARTREE
                ),
                "direct_cost_within_tolerance": (
                    direct_cost_relative_difference
                    <= REPRODUCTION_COST_RELATIVE_TOLERANCE
                ),
                "eigenpair_residual_within_1e-10": (
                    float(recomputed_sentinel["eigenpair_residual_2_norm"])
                    <= 1e-10
                ),
                "ground_overlap_at_least_0_99": (
                    float(recomputed_sentinel["ground_overlap_probability"])
                    >= 0.99
                ),
            }
            formula_payload["reproduction_sentinel"] = {
                "source_point": source_sentinel,
                "recomputed_point": recomputed_sentinel,
                "signed_shift_absolute_difference_hartree": (
                    signed_shift_difference
                ),
                "direct_cost_relative_difference": (
                    direct_cost_relative_difference
                ),
                "tolerances": {
                    "signed_shift_absolute_difference_hartree": (
                        REPRODUCTION_SHIFT_TOLERANCE_HARTREE
                    ),
                    "direct_cost_relative_difference": (
                        REPRODUCTION_COST_RELATIVE_TOLERANCE
                    ),
                },
                "checks": sentinel_checks,
                "passed": all(sentinel_checks.values()),
            }
            checkpoint()
            if not all(sentinel_checks.values()):
                raise RuntimeError(
                    f"{condition}/{formula_name}: direct sentinel "
                    f"reproduction failed: {sentinel_checks}"
                )
            for model_name in ("original_one_term", "refit_one_term"):
                target_time = float(
                    definitions[model_name]["predicted_optimal_time"]
                )
                if any(
                    abs(float(point["time"]) - target_time)
                    <= 1e-12 * max(1.0, abs(target_time))
                    for point in (
                        source_formula["training_direct_points"]
                        + source_formula["local_direct_points"]
                    )
                ):
                    raise RuntimeError(
                        f"{condition}/{formula_name}/{model_name}: "
                        "point unexpectedly already exists"
                    )
                print(
                    f"{condition}/{formula_name}: exact {model_name} optimum",
                    flush=True,
                )
                point = holdout._direct_point(
                    system, sequence, target_time, rotations
                )
                point.update(
                    {
                        "schedule_for_model": model_name,
                        "relative_to_t_ana": target_time
                        / float(source_formula["analytic_time"]),
                    }
                )
                formula_payload["additional_direct_points"][model_name] = (
                    _point_with_all_model_predictions(
                        point, definitions, rotations
                    )
                )
                checkpoint()
            formula_payload["status"] = "complete"
            checkpoint()
        payload.update(
            {
                "status": "complete",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        checkpoint()
        print(f"{condition}: complete", flush=True)
        return 0
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "peak_cpu_rss_kib": int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
            }
        )
        checkpoint()
        traceback.print_exc()
        return 1

def _predicted_direct_point(
    model_name: str,
    formula: dict[str, Any],
    additions: dict[str, Any],
):
    if model_name in ("original_one_term", "refit_one_term"):
        return additions["additional_direct_points"][model_name]
    return min(
        formula["local_direct_points"],
        key=lambda point: abs(float(point["relative_to_t_star"]) - 1.0),
    )

def _final_model_record(
    saved_record: dict[str, Any],
    formula: dict[str, Any],
    additions: dict[str, Any],
    model_name: str,
):
    saved_model = saved_record["models"][model_name]
    definition = saved_model["definition"]
    schedule_point = _predicted_direct_point(
        model_name, formula, additions
    )
    prediction = _model_shift(definition, float(schedule_point["time"]))
    model_cost = holdout._cost(
        float(schedule_point["time"]),
        abs(prediction),
        int(formula["rotations_per_pf_step"]),
    )
    direct_cost = schedule_point["direct_cost"]
    predicted_cost_error = (
        None
        if model_cost is None or direct_cost is None
        else abs(float(model_cost) - float(direct_cost)) / float(direct_cost)
    )
    direct_minimum = saved_record["saved_local_direct_minimum"]
    eta_min = (
        None
        if direct_cost is None
        else float(direct_cost) / float(direct_minimum["direct_cost"]) - 1.0
    )
    eta_t = abs(
        float(definition["predicted_optimal_time"])
        / float(direct_minimum["time"])
        - 1.0
    )
    metrics = {
        "predicted_time_cost_relative_error": predicted_cost_error,
        "direct_cost_loss_against_saved_local_grid": eta_min,
        "predicted_time_difference_from_saved_local_grid_minimum": eta_t,
        "maximum_saved_unseen_residual_over_epsilon": saved_model[
            "maximum_saved_unseen_residual_over_epsilon"
        ],
    }
    checks = {
        key: value is not None and float(value) <= PASS_THRESHOLDS[key]
        for key, value in metrics.items()
    }
    return {
        "definition": definition,
        "training_points_relative_to_t_ana": list(
            holdout.TRAINING_RELATIVE_TIMES
        ),
        "saved_unseen_points_relative_to_t_star": (
            saved_record["saved_unseen_grid_relative_to_t_star"]
        ),
        "saved_unseen_predictions": saved_model[
            "saved_unseen_predictions"
        ],
        "accepted_sampled_time_range": saved_model[
            "accepted_sampled_time_range"
        ],
        "predicted_time_direct_point": schedule_point,
        "predicted_time_model_shift_hartree": prediction,
        "predicted_time_model_cost": model_cost,
        "saved_local_direct_minimum": direct_minimum,
        "metrics": metrics,
        "threshold_checks": checks,
        "passed": all(checks.values()),
        "eta_t_scope": (
            "comparison with the frozen seven-point saved local-grid minimum; "
            "not a continuous optimum claim"
        ),
    }

def aggregate_final(
    source_dir: Path,
    output_dir: Path,
    saved_reaggregation: dict[str, Any],
) -> dict[str, Any]:
    saved_index = {
        (record["condition"], record["formula"]): record
        for record in saved_reaggregation["records"]
    }
    records = []
    additional_diagnostics = []
    reproduction_sentinels = []
    for condition, source_path in _source_files(source_dir).items():
        source = _load(source_path)
        addition_path = output_dir / "additional_direct" / f"{condition}.json"
        addition = _load(addition_path)
        if addition.get("status") != "complete":
            raise RuntimeError(
                f"additional calculation incomplete: {addition_path}"
            )
        for formula_name in holdout.FORMULAS:
            formula = source["formulas"][formula_name]
            saved = saved_index[(condition, formula_name)]
            formula_additions = addition["formulas"][formula_name]
            models = {
                model_name: _final_model_record(
                    saved, formula, formula_additions, model_name
                )
                for model_name in MODEL_NAMES
            }
            for point in formula_additions["additional_direct_points"].values():
                additional_diagnostics.append(point)
            reproduction_sentinels.append(
                formula_additions["reproduction_sentinel"]
            )
            records.append(
                {
                    "condition": condition,
                    "formula": formula_name,
                    "weights": formula["weights"],
                    "rotations_per_pf_step": int(
                        formula["rotations_per_pf_step"]
                    ),
                    "source": str(source_path.resolve()),
                    "source_system_hashes": {
                        key: source["system"][key] for key in HASH_FIELDS
                    },
                    "system_reproduction": addition["system_reproduction"],
                    "reproduction_sentinel": formula_additions[
                        "reproduction_sentinel"
                    ],
                    "models": models,
                }
            )

    pass_counts = {}
    aggregates = {}
    for formula_name in holdout.FORMULAS:
        pass_counts[formula_name] = {}
        aggregates[formula_name] = {}
        rows = [row for row in records if row["formula"] == formula_name]
        for model_name in MODEL_NAMES:
            passed = sum(
                bool(row["models"][model_name]["passed"]) for row in rows
            )
            pass_counts[formula_name][model_name] = {
                "passed": passed,
                "total": len(rows),
            }
            metrics = [
                row["models"][model_name]["metrics"] for row in rows
            ]
            aggregates[formula_name][model_name] = {
                "maximum_predicted_time_cost_relative_error": max(
                    float(item["predicted_time_cost_relative_error"])
                    for item in metrics
                ),
                "maximum_direct_cost_loss_against_saved_local_grid": max(
                    float(item["direct_cost_loss_against_saved_local_grid"])
                    for item in metrics
                ),
                "maximum_predicted_time_difference_from_saved_local_grid_minimum": max(
                    float(
                        item[
                            "predicted_time_difference_from_saved_local_grid_minimum"
                        ]
                    )
                    for item in metrics
                ),
                "maximum_saved_unseen_residual_over_epsilon": max(
                    float(
                        item["maximum_saved_unseen_residual_over_epsilon"]
                    )
                    for item in metrics
                ),
                "passed": passed,
                "total": len(rows),
            }
    total_pass_counts = {
        model_name: {
            "passed": sum(
                bool(row["models"][model_name]["passed"])
                for row in records
            ),
            "total": len(records),
        }
        for model_name in MODEL_NAMES
    }
    original_fail_two_pass = [
        {"condition": row["condition"], "formula": row["formula"]}
        for row in records
        if not row["models"]["original_one_term"]["passed"]
        and row["models"]["two_term"]["passed"]
    ]
    refit_fail_two_pass = [
        {"condition": row["condition"], "formula": row["formula"]}
        for row in records
        if not row["models"]["refit_one_term"]["passed"]
        and row["models"]["two_term"]["passed"]
    ]
    if total_pass_counts["original_one_term"]["passed"] == len(records):
        conclusion = {
            "category": 1,
            "statement": (
                "The original one-term model is sufficient under all declared "
                "thresholds on these holdouts; adding t^6 may improve numerical "
                "accuracy but is not required for pass/fail coverage."
            ),
        }
    elif total_pass_counts["refit_one_term"]["passed"] == len(records):
        conclusion = {
            "category": 2,
            "statement": (
                "Direct recalibration of the fourth-order coefficient is "
                "sufficient under all declared thresholds on these holdouts."
            ),
        }
    else:
        conclusion = {
            "category": 3,
            "statement": (
                "Adding the t^6 term is required to stabilize declared coverage "
                "or prediction accuracy on these holdouts."
            ),
        }

    cost_ratios = {}
    for condition, source_path in _source_files(source_dir).items():
        source = _load(source_path)
        cost_ratios[condition] = source["comparison"][
            "direct_cost_at_each_formulas_own_predicted_optimum_ratio_new_over_current"
        ]
    payload = {
        "status": "complete",
        "completed_at": _now(),
        "source_commit": SOURCE_COMMIT,
        "baseline_commit": BASELINE_COMMIT,
        "git": _git_state(),
        "protocol": {
            "primary_common_unseen_points": (
                "the seven saved local direct points for each condition/PF"
            ),
            "training_points_excluded": list(
                holdout.TRAINING_RELATIVE_TIMES
            ),
            "additional_schedule_points": (
                "exact original-one-term and refitted-one-term predicted optima"
            ),
            "additional_schedule_point_count": len(additional_diagnostics),
            "reproduction_sentinels": (
                "recomputed saved two-term optimum for every condition/PF "
                "before accepting newly calculated points"
            ),
            "reproduction_sentinel_count": len(reproduction_sentinels),
            "local_minimum_denominator": (
                "frozen seven-point saved local direct grid"
            ),
            "pass_thresholds": PASS_THRESHOLDS,
        },
        "aggregates_by_formula_and_model": aggregates,
        "pass_counts_by_formula": pass_counts,
        "pass_counts_all_condition_formula_records": total_pass_counts,
        "original_one_term_failed_but_two_term_passed": original_fail_two_pass,
        "refit_one_term_failed_but_two_term_passed": refit_fail_two_pass,
        "additional_direct_diagnostics": {
            "minimum_ground_overlap_probability": min(
                float(point["ground_overlap_probability"])
                for point in additional_diagnostics
            ),
            "maximum_eigenpair_residual_2_norm": max(
                float(point["eigenpair_residual_2_norm"])
                for point in additional_diagnostics
            ),
        },
        "reproduction_sentinel_diagnostics": {
            "all_passed": all(
                bool(sentinel["passed"]) for sentinel in reproduction_sentinels
            ),
            "maximum_signed_shift_absolute_difference_hartree": max(
                float(sentinel["signed_shift_absolute_difference_hartree"])
                for sentinel in reproduction_sentinels
            ),
            "maximum_direct_cost_relative_difference": max(
                float(sentinel["direct_cost_relative_difference"])
                for sentinel in reproduction_sentinels
            ),
            "minimum_recomputed_ground_overlap_probability": min(
                float(sentinel["recomputed_point"]["ground_overlap_probability"])
                for sentinel in reproduction_sentinels
            ),
            "maximum_recomputed_eigenpair_residual_2_norm": max(
                float(sentinel["recomputed_point"]["eigenpair_residual_2_norm"])
                for sentinel in reproduction_sentinels
            ),
        },
        "direct_cost_ratio_new_over_current_at_each_pf_own_two_term_optimum": (
            cost_ratios
        ),
        "cost_ratio_is_separate_from_model_accuracy": True,
        "conclusion": conclusion,
        "scope_limit": (
            "Conclusions apply only to H6/H7 and NH3 in three bases over the "
            "saved finite-time neighborhood; they are not a claim for arbitrary "
            "molecules or continuous time."
        ),
        "records": records,
    }
    _atomic_json(output_dir / "summary.json", payload)
    return payload

def _format(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.6g}"

def _accepted_range_text(model: dict[str, Any]) -> str:
    accepted = model["accepted_sampled_time_range"]
    intervals = accepted["sampled_contiguous_intervals_relative_to_t_ana"]
    if not intervals:
        return "none"
    ranges = [
        _format(interval[0])
        if abs(float(interval[0]) - float(interval[1])) < 1e-15
        else f"{_format(interval[0])}-{_format(interval[1])}"
        for interval in intervals
    ]
    return ", ".join(ranges) + (
        f" ({accepted['accepted_count']}/{accepted['total_count']})"
    )

def write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    sentinel_diagnostics = summary["reproduction_sentinel_diagnostics"]
    maximum_sentinel_shift = _format(
        sentinel_diagnostics["maximum_signed_shift_absolute_difference_hartree"]
    )
    maximum_sentinel_cost_error = _format(
        sentinel_diagnostics["maximum_direct_cost_relative_difference"]
    )
    lines = [
        "# One-term versus two-term m=3 PF error models",
        "",
        f"Source result commit: {summary['source_commit']}",
        f"Pre-validation baseline: {summary['baseline_commit']}",
        "",
        (
            "All models use the same three training points "
            "(0.1, 0.2, 0.3) t_ana. Those points are excluded from validation. "
            "The primary unseen set is the same seven saved local direct points "
            "for all three models."
        ),
        "",
        (
            "The refitted one-term model uses the same normalized least-squares "
            "objective as the stored two-term model. Therefore the comparison "
            "isolates the effect of adding the t^6 term."
        ),
        "",
        (
            "Before accepting added schedule points, each saved two-term optimum "
            "was recomputed as a reproduction sentinel. "
            f"{summary['protocol']['reproduction_sentinel_count']} sentinels passed; "
            "the maximum signed-shift difference was "
            f"{maximum_sentinel_shift} Ha "
            "and the maximum direct-cost relative difference was "
            f"{maximum_sentinel_cost_error}."
        ),
        "",
        (
            "Exact grouping-structure hashes, active-space metadata, dimensions, "
            "and energies were gated. The coefficient-inclusive hash may differ "
            "when rerunning SCF because of last-bit floating-point variation; "
            "the direct sentinel is the additional numerical equivalence check."
        ),
        "",
        "## Model coefficients and predicted schedules",
        "",
        (
            "| condition | PF | model | a4 | a6 | train t/t_ana | "
            "unseen t/t_* | t_pred | sampled accepted t/t_ana |"
        ),
        "|---|---|---|---:|---:|---|---|---:|---|",
    ]
    for row in summary["records"]:
        for model_name in MODEL_NAMES:
            model = row["models"][model_name]
            definition = model["definition"]
            training_grid = ",".join(
                _format(value)
                for value in model["training_points_relative_to_t_ana"]
            )
            unseen_grid = ",".join(
                _format(value)
                for value in model["saved_unseen_points_relative_to_t_star"]
            )
            lines.append(
                f"| {row['condition']} | {row['formula']} | {model_name} | "
                f"{_format(definition['a4'])} | {_format(definition['a6'])} | "
                f"{training_grid} | {unseen_grid} | "
                f"{_format(definition['predicted_optimal_time'])} | "
                f"{_accepted_range_text(model)} |"
            )
    lines.extend(
        [
            "",
            "## Accuracy and pass/fail",
            "",
            (
                "| condition | PF | model | R_max | eta_C(t_pred) | "
                "eta_min | eta_t | pass |"
            ),
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in summary["records"]:
        for model_name in MODEL_NAMES:
            model = row["models"][model_name]
            metrics = model["metrics"]
            predicted_time_difference = _format(
                metrics["predicted_time_difference_from_saved_local_grid_minimum"]
            )
            lines.append(
                f"| {row['condition']} | {row['formula']} | {model_name} | "
                f"{_format(metrics['maximum_saved_unseen_residual_over_epsilon'])} | "
                f"{_format(metrics['predicted_time_cost_relative_error'])} | "
                f"{_format(metrics['direct_cost_loss_against_saved_local_grid'])} | "
                f"{predicted_time_difference} | "
                f"{model['passed']} |"
            )
    lines.extend(["", "## Pass counts", ""])
    for formula_name, models in summary["pass_counts_by_formula"].items():
        lines.append(f"- {formula_name}:")
        for model_name in MODEL_NAMES:
            count = models[model_name]
            lines.append(
                f"  - {model_name}: {count['passed']}/{count['total']}"
            )
    lines.extend(
        [
            "",
            (
                "Original one-term failed but two-term passed: "
                f"{summary['original_one_term_failed_but_two_term_passed']}"
            ),
            (
                "Refitted one-term failed but two-term passed: "
                f"{summary['refit_one_term_failed_but_two_term_passed']}"
            ),
            "",
            "## PF direct-cost comparison",
            "",
            (
                "These ratios compare the new PF with current_m3 at each PF's "
                "own two-term predicted optimum. They are separate from model accuracy."
            ),
            "",
            "| condition | direct cost ratio new/current |",
            "|---|---:|",
        ]
    )
    for condition, ratio in (
        summary[
            "direct_cost_ratio_new_over_current_at_each_pf_own_two_term_optimum"
        ].items()
    ):
        lines.append(f"| {condition} | {_format(ratio)} |")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            (
                f"Category {summary['conclusion']['category']}: "
                f"{summary['conclusion']['statement']}"
            ),
            "",
            summary["scope_limit"],
            "",
            (
                "eta_t and eta_min use the frozen saved local grid and do not "
                "establish a continuous optimum."
            ),
            "",
        ]
    )
    (output_dir / "report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

def _additional_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "queued"}
    try:
        payload = _load(path)
    except Exception as exc:
        return {"status": "temporarily_unreadable", "error": str(exc)}
    return {
        "status": payload.get("status"),
        "formula_status": {
            name: formula.get("status")
            for name, formula in payload.get("formulas", {}).items()
        },
        "additional_point_counts": {
            name: len(formula.get("additional_direct_points", {}))
            for name, formula in payload.get("formulas", {}).items()
        },
        "error": payload.get("error"),
    }

def launch(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    output_dir = Path(args.output_dir).resolve()
    source_dir = Path(args.source_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "additional_direct").mkdir()
    (output_dir / "tmp").mkdir()
    manifest = {
        "status": "saved_point_reaggregation",
        "started_at": _now(),
        "git": _git_state(),
        "source_commit": SOURCE_COMMIT,
        "baseline_commit": BASELINE_COMMIT,
        "source_directory": str(source_dir),
        "source_json_overwritten": False,
        "execution_strategy": {
            "saved_reaggregation": "CPU; no PF action or diagonalization",
            "additional_direct_backend": (
                "CPU exact sector PF build plus CPU complex Schur"
            ),
            "condition_workers": int(args.condition_workers),
            "blas_threads_per_worker": int(args.blas_threads),
            "component_processes_per_condition": int(
                args.component_processes
            ),
            "gpu_decision": (
                "CUDA disabled for this run; no other process is stopped or displaced"
            ),
        },
        "resource_snapshot": holdout._resource_snapshot(),
    }
    _atomic_json(output_dir / "run_manifest.json", manifest)
    saved_path = output_dir / "saved_point_reaggregation.json"
    saved = reaggregate_saved(source_dir, saved_path)
    manifest["status"] = "additional_direct_points"
    manifest["saved_point_reaggregation"] = str(saved_path)
    _atomic_json(output_dir / "run_manifest.json", manifest)
    print("saved-point-only reaggregation complete", flush=True)

    queue = list(holdout.CONDITIONS)
    running: dict[str, tuple[subprocess.Popen[Any], Any]] = {}
    failures: dict[str, int] = {}
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": str(int(args.blas_threads)),
            "OMP_NUM_THREADS": str(int(args.blas_threads)),
            "MKL_NUM_THREADS": str(int(args.blas_threads)),
            "NUMEXPR_NUM_THREADS": str(int(args.blas_threads)),
            "CUDA_VISIBLE_DEVICES": "",
            "TMPDIR": str(output_dir / "tmp"),
        }
    )
    while queue or running:
        while queue and len(running) < int(args.condition_workers):
            condition = queue.pop(0)
            log_handle = (
                output_dir / "additional_direct" / f"{condition}.log"
            ).open("a", encoding="utf-8", buffering=1)
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "worker",
                "--condition",
                condition,
                "--source-dir",
                str(source_dir),
                "--output",
                str(
                    output_dir
                    / "additional_direct"
                    / f"{condition}.json"
                ),
                "--blas-threads",
                str(int(args.blas_threads)),
                "--component-processes",
                str(int(args.component_processes)),
            ]
            process = subprocess.Popen(
                command,
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=False,
            )
            running[condition] = (process, log_handle)
            print(f"started {condition}: pid={process.pid}", flush=True)
        progress = {
            "status": "running",
            "updated_at": _now(),
            "queued": list(queue),
            "running": {
                condition: process.pid
                for condition, (process, _) in running.items()
            },
            "failures": failures,
            "conditions": {
                condition: _additional_status(
                    output_dir / "additional_direct" / f"{condition}.json"
                )
                for condition in holdout.CONDITIONS
            },
        }
        _atomic_json(output_dir / "progress.json", progress)
        if not running:
            continue
        time.sleep(float(args.poll_seconds))
        for condition, (process, log_handle) in list(running.items()):
            returncode = process.poll()
            if returncode is None:
                continue
            log_handle.close()
            del running[condition]
            if returncode != 0:
                failures[condition] = int(returncode)
            print(
                f"finished {condition}: returncode={returncode}", flush=True
            )
    progress = {
        "status": "failed" if failures else "complete",
        "updated_at": _now(),
        "queued": [],
        "running": {},
        "failures": failures,
        "conditions": {
            condition: _additional_status(
                output_dir / "additional_direct" / f"{condition}.json"
            )
            for condition in holdout.CONDITIONS
        },
    }
    _atomic_json(output_dir / "progress.json", progress)

    if failures:
        manifest.update(
            {
                "status": "failed",
                "completed_at": _now(),
                "elapsed_seconds": float(time.perf_counter() - started),
                "failures": failures,
            }
        )
        _atomic_json(output_dir / "run_manifest.json", manifest)
        return 1
    summary = aggregate_final(source_dir, output_dir, saved)
    write_report(output_dir, summary)
    manifest.update(
        {
            "status": "complete",
            "completed_at": _now(),
            "elapsed_seconds": float(time.perf_counter() - started),
            "failures": {},
            "summary": str(output_dir / "summary.json"),
            "report": str(output_dir / "report.md"),
        }
    )
    _atomic_json(output_dir / "run_manifest.json", manifest)
    print(
        f"complete: category {summary['conclusion']['category']}", flush=True
    )
    return 0

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    reaggregate = subparsers.add_parser("reaggregate")
    reaggregate.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    reaggregate.add_argument("--output", type=Path, required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument(
        "--condition", choices=list(holdout.CONDITIONS), required=True
    )
    worker_parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    worker_parser.add_argument("--output", type=Path, required=True)
    worker_parser.add_argument("--blas-threads", type=int, default=2)
    worker_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    launch_parser.add_argument("--output-dir", type=Path, required=True)
    launch_parser.add_argument(
        "--condition-workers", type=int, default=2
    )
    launch_parser.add_argument("--blas-threads", type=int, default=2)
    launch_parser.add_argument(
        "--component-processes", type=int, default=1
    )
    launch_parser.add_argument("--poll-seconds", type=float, default=10.0)
    return parser.parse_args()

if __name__ == "__main__":
    parsed = parse_args()
    if parsed.command == "reaggregate":
        reaggregate_saved(parsed.source_dir.resolve(), parsed.output.resolve())
        raise SystemExit(0)
    if parsed.command == "worker":
        raise SystemExit(additional_worker(parsed))
    raise SystemExit(launch(parsed))
