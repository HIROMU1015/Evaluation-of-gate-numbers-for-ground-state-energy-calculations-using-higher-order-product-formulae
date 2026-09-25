"""S0 exact-time scoring for the frozen practical selector.

This runner is truth-only.  It verifies and copies the already frozen
practical predictions, inserts the fixed 0.99/1.00/1.01 triplet around each
selected time, and connects it to the nearest lower reliable point of the
saved continuous branch.  It never reruns or changes the selector.
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
import platform
import resource
import shutil
import subprocess
import time
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.linalg import schur

import run_full_electron_nh3_higher_term_diagnosis as diagnosis
import run_practical_calibration_minimal as practical


FIRST_STUDY_PROTOCOL = Path("PF_first_study_protocol_20260925.json")
EXPECTED_FIRST_STUDY_PROTOCOL_SHA256 = (
    "410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565"
)
EXPECTED_PRACTICAL_PROTOCOL_SHA256 = (
    "7bbe9958837a881f0247b6e72f5e80e2331e0cfe50dea18addd13a2748467d55"
)
EXPECTED_PREDICTIONS_SHA256 = (
    "fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e"
)
EXPECTED_PHASE_A_COMMIT = "79035cc7c414c04cafe8b9f8bdc779a17ec57302"
TIME_FACTORS = (0.99, 1.0, 1.01)
ANCHOR_SHIFT_ABSOLUTE_TOLERANCE_HARTREE = 1e-9
TIME_RTOL = 2e-12


class S0ValidationError(RuntimeError):
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


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
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


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _same_time(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=TIME_RTOL, abs_tol=1e-14)


def _walk_truth(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "time" in value and "signed_direct_shift_hartree" in value:
            yield value
        for child in value.values():
            yield from _walk_truth(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_truth(child)


def _source_truth_points(
    h01_root: Path, p03_root: Path, condition: str, formula: str
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    candidates = (
        (h01_root / "truth" / f"{condition}__{formula}.json", "h01_saved_truth"),
        (p03_root / "raw" / f"{condition}__{formula}.json", "p03_raw"),
        (p03_root / "fine/raw" / f"{condition}__{formula}.json", "p03_fine"),
    )
    points: list[dict[str, Any]] = []
    provenance: list[dict[str, str]] = []
    for path, source in candidates:
        if not path.is_file():
            continue
        provenance.append({"source": source, "path": str(path.resolve()), "sha256": _sha256(path)})
        for raw in _walk_truth(_load_json(path)):
            time_value = float(raw["time"])
            duplicate = next(
                (old for old in points if _same_time(old["time"], time_value)), None
            )
            if duplicate is not None:
                if abs(
                    float(duplicate["signed_direct_shift_hartree"])
                    - float(raw["signed_direct_shift_hartree"])
                ) > ANCHOR_SHIFT_ABSOLUTE_TOLERANCE_HARTREE:
                    raise S0ValidationError(
                        f"inconsistent saved truth: {condition}/{formula}/{time_value}"
                    )
                duplicate["truth_sources"].append(source)
                continue
            point = dict(raw)
            point["time"] = time_value
            point["signed_direct_shift_hartree"] = float(
                raw["signed_direct_shift_hartree"]
            )
            point["direct_error_hartree"] = abs(
                point["signed_direct_shift_hartree"]
            )
            point["truth_sources"] = [source]
            points.append(point)
    return sorted(points, key=lambda row: row["time"]), provenance


def _source_point_reliable(point: dict[str, Any], gates: dict[str, Any]) -> bool:
    residual = point.get("eigenpair_residual_2_norm")
    overlap = point.get("ground_overlap_probability")
    if residual is not None and float(residual) > float(
        gates["direct_eigenpair_residual_2_norm"]
    ):
        return False
    if overlap is not None and float(overlap) < 0.9:
        return False
    return not bool(point.get("branch_warning", False))


def nearest_lower_reliable_anchor(
    points: Sequence[dict[str, Any]], first_inserted_time: float, gates: dict[str, Any]
) -> dict[str, Any]:
    eligible = [
        point
        for point in points
        if float(point["time"]) < float(first_inserted_time)
        and _source_point_reliable(point, gates)
    ]
    if not eligible:
        raise S0ValidationError("no reliable saved branch point below inserted triplet")
    return max(eligible, key=lambda row: float(row["time"]))


def _phase_distance(left: complex, right: complex) -> float:
    return abs(float(np.angle(complex(left) / complex(right))))


def direct_branch_point(
    unitary: np.ndarray,
    exact_state: np.ndarray,
    energy: float,
    time_value: float,
    rotations: int,
    epsilon: float,
    previous_vector: np.ndarray | None,
    degeneracy_gap: float,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - started
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(vectors.conj().T @ exact_state) ** 2
    comparator = int(np.argmax(ground_overlaps))
    continuity_overlaps = (
        ground_overlaps
        if previous_vector is None
        else np.abs(vectors.conj().T @ previous_vector) ** 2
    )
    selected = int(np.argmax(continuity_overlaps))
    phase_distances = np.asarray(
        [_phase_distance(value, eigenvalues[selected]) for value in eigenvalues]
    )
    nonzero = phase_distances[np.arange(eigenvalues.size) != selected]
    phase_gap = float(np.min(nonzero)) if nonzero.size else float("inf")
    cluster = np.flatnonzero(phase_distances <= float(degeneracy_gap))
    projector_overlap = float(np.sum(continuity_overlaps[cluster]))
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    shift = float(
        np.angle(np.exp(-1j * float(energy) * float(time_value)) * eigenvalue)
        / float(time_value)
    )
    error = abs(shift)
    direct_cost = practical._cost(float(time_value), error, rotations, epsilon)
    identity = np.eye(unitary.shape[0], dtype=np.complex128)
    unitarity_started = time.perf_counter()
    unitarity = float(np.linalg.norm(unitary.conj().T @ unitary - identity, ord="fro"))
    unitarity_seconds = time.perf_counter() - unitarity_started
    point = {
        "time": float(time_value),
        "signed_direct_shift_hartree": shift,
        "direct_error_hartree": error,
        "direct_cost": direct_cost,
        "ground_state_overlap_probability": float(ground_overlaps[selected]),
        "previous_branch_overlap_probability": float(continuity_overlaps[selected]),
        "degenerate_subspace_projector_overlap_probability": projector_overlap,
        "minimum_selected_phase_gap_radians": phase_gap,
        "phase_cluster_size": int(cluster.size),
        "branch_quality": (
            "resolved"
            if phase_gap > float(degeneracy_gap)
            else "unresolved_degenerate_phase_cluster"
        ),
        "selected_eigenvalue": eigenvalue,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "eigenpair_residual_2_norm": float(
            np.linalg.norm(unitary @ vector - eigenvalue * vector)
        ),
        "unitarity_residual_frobenius": unitarity,
        "selected_eigenbranch_id": selected,
        "maximum_ground_overlap_comparator_id": comparator,
        "branch_selection_disagrees_with_comparator": bool(selected != comparator),
        "phase_unwrap_integer": 0,
        "selection_rule": (
            "maximum exact-ground overlap at saved lower anchor"
            if previous_vector is None
            else "maximum previous-selected-vector overlap from saved lower anchor"
        ),
        "timing_seconds": {
            "schur": float(schur_seconds),
            "unitarity": float(unitarity_seconds),
        },
    }
    return point, vector


def _point_cache_key(
    condition: str,
    formula: str,
    time_value: float,
    backend: str,
    system: dict[str, Any],
) -> dict[str, Any]:
    return {
        "first_study_protocol_sha256": EXPECTED_FIRST_STUDY_PROTOCOL_SHA256,
        "practical_predictions_sha256": EXPECTED_PREDICTIONS_SHA256,
        "condition": condition,
        "formula": formula,
        "absolute_time": float(time_value),
        "backend": backend,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
    }


def _compute_point(
    output_dir: Path,
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
    cache_key = _point_cache_key(
        condition, formula, time_value, backend, system
    )
    digest = hashlib.sha256(
        json.dumps(cache_key, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    root = output_dir / ".runtime/direct_cache" / condition / formula
    point_path = root / f"{digest}.json"
    vector_path = root / f"{digest}.npy"
    if point_path.is_file() and vector_path.is_file():
        cached = _load_json(point_path)
        if (
            cached.get("cache_key") == cache_key
            and cached.get("selected_vector_sha256") == _sha256(vector_path)
        ):
            vector = np.load(vector_path)
            return cached["point"], np.asarray(vector, dtype=np.complex128), True
    started = time.perf_counter()
    if backend == "gpu":
        unitary, build = diagnosis._build_gpu(
            system, sequence, float(time_value), int(gpu_id)
        )
    else:
        unitary, build = diagnosis._build_cpu(system, sequence, float(time_value))
    point, vector = direct_branch_point(
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
    point["peak_cpu_rss_kib"] = int(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    )
    root.mkdir(parents=True, exist_ok=True)
    temporary_vector = vector_path.with_suffix(".npy.tmp")
    with temporary_vector.open("wb") as handle:
        np.save(handle, vector)
    os.replace(temporary_vector, vector_path)
    _write_json(
        point_path,
        {
            "status": "complete",
            "cache_key": cache_key,
            "selected_vector_sha256": _sha256(vector_path),
            "point": point,
        },
    )
    del unitary
    return point, vector, False


def _formula_prediction(condition: dict[str, Any], formula: str) -> dict[str, Any]:
    return next(row for row in condition["pf_predictions"] if row["formula"] == formula)


def _reference_costs(
    h01_root: Path,
    p03_root: Path,
    condition_prediction: dict[str, Any],
    epsilon: float,
    inserted_points: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    selected_formula = condition_prediction["selection"]["selected_formula"]
    original_rows: list[dict[str, Any]] = []
    for formula in practical.FORMULAE:
        prediction = _formula_prediction(condition_prediction, formula)
        rotations = int(prediction["rotations"])
        points, _ = _source_truth_points(
            h01_root, p03_root, condition_prediction["condition"], formula
        )
        for point in points:
            cost = practical._cost(
                float(point["time"]),
                abs(float(point["signed_direct_shift_hartree"])),
                rotations,
                epsilon,
            )
            if cost is not None and _source_point_reliable(
                point, {"direct_eigenpair_residual_2_norm": 1e-10}
            ):
                original_rows.append(
                    {"formula": formula, "time": float(point["time"]), "cost": cost}
                )
    if not original_rows:
        raise S0ValidationError("original two-formula reference grid has no feasible point")
    same_rows = [row for row in original_rows if row["formula"] == selected_formula]
    original_same = min(same_rows, key=lambda row: row["cost"])
    original_joint = min(original_rows, key=lambda row: row["cost"])
    extended_rows = list(original_rows)
    extended_rows.extend(
        {
            "formula": selected_formula,
            "time": float(point["time"]),
            "cost": float(point["direct_cost"]),
        }
        for point in inserted_points
        if point["direct_cost"] is not None
    )
    extended_joint = min(extended_rows, key=lambda row: row["cost"])
    return {
        "original_same_formula": original_same,
        "original_joint": original_joint,
        "extended_joint": extended_joint,
    }


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    return {
        path.name: _sha256(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE"}
    }


def _verify_frozen_inputs(
    practical_root: Path, first_study_protocol: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    if _sha256(first_study_protocol) != EXPECTED_FIRST_STUDY_PROTOCOL_SHA256:
        raise S0ValidationError("first-study protocol hash mismatch")
    protocol = _load_json(first_study_protocol)
    if _sha256(practical_root / "protocol.json") != EXPECTED_PRACTICAL_PROTOCOL_SHA256:
        raise S0ValidationError("practical protocol hash mismatch")
    if _sha256(practical_root / "predictions.json") != EXPECTED_PREDICTIONS_SHA256:
        raise S0ValidationError("frozen predictions hash mismatch")
    marker = _load_json(practical_root / "SELECTION_FROZEN")
    if (
        marker.get("prediction_sha256") != EXPECTED_PREDICTIONS_SHA256
        or marker.get("protocol_sha256") != EXPECTED_PRACTICAL_PROTOCOL_SHA256
        or marker.get("phase_a_commit") != EXPECTED_PHASE_A_COMMIT
    ):
        raise S0ValidationError("selection freeze identity mismatch")
    predictions = _load_json(practical_root / "predictions.json")
    if predictions.get("phase_a_commit") != EXPECTED_PHASE_A_COMMIT:
        raise S0ValidationError("prediction Phase-A commit mismatch")
    return protocol, predictions


def run(
    project_root: Path,
    practical_root: Path,
    h01_root: Path,
    p03_root: Path,
    output_dir: Path,
    backend: str,
    gpu_id: int,
    requested_conditions: Sequence[str] | None,
) -> dict[str, Any]:
    started = time.perf_counter()
    protocol, predictions = _verify_frozen_inputs(
        practical_root, project_root / FIRST_STUDY_PROTOCOL
    )
    configured = list(protocol["S0_existing_practical_exact_time_scoring"]["conditions"])
    conditions = configured if not requested_conditions else list(requested_conditions)
    if any(condition not in configured for condition in conditions):
        raise S0ValidationError("requested condition outside frozen S0 scope")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".gitignore").write_text(".runtime/\n", encoding="utf-8")
    shutil.copyfile(project_root / FIRST_STUDY_PROTOCOL, output_dir / "protocol.json")
    shutil.copyfile(practical_root / "predictions.json", output_dir / "predictions.json")
    shutil.copyfile(practical_root / "prediction.sha256", output_dir / "prediction.sha256")

    validation = practical.validate_sources(h01_root, p03_root)
    systems = validation["systems"]
    gates = protocol["numerical_gates"]
    epsilon = float(protocol["resource_metrics"]["target_error_hartree"])
    beta = float(protocol["resource_metrics"]["qpe_beta"])
    degeneracy_gap = float(protocol["phase_and_branch_policy"]["degenerate_phase_gap_radians"])
    prediction_by_condition = {
        row["condition"]: row for row in predictions["conditions"]
    }
    practical_scoring = {
        row["condition"]: row
        for row in csv.DictReader(
            (practical_root / "scoring_results.csv").open(encoding="utf-8", newline="")
        )
    }
    branch_rows: list[dict[str, Any]] = []
    scoring_rows: list[dict[str, Any]] = []
    source_truth_manifest: list[dict[str, Any]] = []
    cache_reuse_count = 0
    for condition in conditions:
        condition_prediction = prediction_by_condition[condition]
        selection = condition_prediction["selection"]
        if selection["status"] != "selected":
            raise S0ValidationError(f"frozen selection is not executable: {condition}")
        formula = str(selection["selected_formula"])
        selected_time = float(selection["selected_time"])
        predicted_cost = float(selection["predicted_cost"])
        pf_prediction = _formula_prediction(condition_prediction, formula)
        rotations = int(pf_prediction["rotations"])
        system = systems[condition]
        sequence = practical._formula_sequence(formula)
        source_points, source_files = _source_truth_points(
            h01_root, p03_root, condition, formula
        )
        source_truth_manifest.extend(
            {"condition": condition, "formula": formula, **row}
            for row in source_files
        )
        inserted_times = [selected_time * factor for factor in TIME_FACTORS]
        anchor = nearest_lower_reliable_anchor(source_points, inserted_times[0], gates)
        anchor_point, previous, reused = _compute_point(
            output_dir,
            condition,
            formula,
            float(anchor["time"]),
            backend,
            gpu_id,
            system,
            sequence,
            rotations,
            epsilon,
            None,
            degeneracy_gap,
        )
        cache_reuse_count += int(reused)
        anchor_difference = abs(
            float(anchor_point["signed_direct_shift_hartree"])
            - float(anchor["signed_direct_shift_hartree"])
        )
        anchor_point.update(
            {
                "condition": condition,
                "formula": formula,
                "point_role": "saved_lower_anchor_recomputation",
                "time_factor": float(anchor["time"]) / selected_time,
                "source_signed_direct_shift_hartree": float(
                    anchor["signed_direct_shift_hartree"]
                ),
                "source_reproduction_absolute_difference_hartree": anchor_difference,
                "new_direct_truth_coordinate": False,
            }
        )
        branch_rows.append(anchor_point)
        inserted: list[dict[str, Any]] = []
        for factor, time_value in zip(TIME_FACTORS, inserted_times, strict=True):
            point, previous, reused = _compute_point(
                output_dir,
                condition,
                formula,
                time_value,
                backend,
                gpu_id,
                system,
                sequence,
                rotations,
                epsilon,
                previous,
                degeneracy_gap,
            )
            cache_reuse_count += int(reused)
            point.update(
                {
                    "condition": condition,
                    "formula": formula,
                    "point_role": "inserted_exact_time_triplet",
                    "time_factor": factor,
                    "source_signed_direct_shift_hartree": None,
                    "source_reproduction_absolute_difference_hartree": None,
                    "new_direct_truth_coordinate": True,
                }
            )
            inserted.append(point)
            branch_rows.append(point)
        exact_point = inserted[1]
        if exact_point["direct_cost"] is None:
            raise S0ValidationError(f"selected exact time is infeasible: {condition}")
        references = _reference_costs(
            h01_root, p03_root, condition_prediction, epsilon, inserted
        )
        direct_cost = float(exact_point["direct_cost"])
        original_joint = float(references["original_joint"]["cost"])
        original_same = float(references["original_same_formula"]["cost"])
        extended_joint = float(references["extended_joint"]["cost"])
        row: dict[str, Any] = {
            "condition": condition,
            "evaluation_group": condition_prediction["evaluation_group"],
            "selected_formula": formula,
            "selected_time": selected_time,
            "predicted_cost": predicted_cost,
            "predicted_error_hartree": float(selection["predicted_error_hartree"]),
            "exact_time_direct_signed_shift_hartree": float(
                exact_point["signed_direct_shift_hartree"]
            ),
            "exact_time_direct_error_hartree": float(
                exact_point["direct_error_hartree"]
            ),
            "exact_time_direct_cost": direct_cost,
            "original_same_formula_grid_best_time": references["original_same_formula"]["time"],
            "original_same_formula_grid_best_cost": original_same,
            "original_joint_grid_best_formula": references["original_joint"]["formula"],
            "original_joint_grid_best_time": references["original_joint"]["time"],
            "original_joint_grid_best_cost": original_joint,
            "extended_joint_grid_best_formula": references["extended_joint"]["formula"],
            "extended_joint_grid_best_time": references["extended_joint"]["time"],
            "extended_joint_grid_best_cost": extended_joint,
            "same_formula_time_selection_regret": direct_cost / original_same - 1.0,
            "joint_formula_time_selection_regret": direct_cost / original_joint - 1.0,
            "extended_grid_joint_regret": direct_cost / extended_joint - 1.0,
            "selected_time_shift_from_original_joint_best": abs(
                selected_time / float(references["original_joint"]["time"]) - 1.0
            ),
            "new_direct_truth_points": len(inserted),
            "anchor_recomputations": 1,
            "old_nearest_grid_scored_time": practical_scoring[condition]["scored_time"],
            "old_nearest_grid_selection_regret": practical_scoring[condition]["selection_regret"],
        }
        for multiplier in protocol["resource_metrics"]["budget_multipliers"]:
            gamma = float(multiplier)
            label = "1_00" if gamma == 1.0 else "1_01"
            budget = gamma * predicted_cost
            phase_error = beta * rotations / (selected_time * budget)
            margin = epsilon - abs(
                float(exact_point["signed_direct_shift_hartree"])
            ) - phase_error
            row[f"frozen_budget_gamma_{label}"] = budget
            row[f"phase_estimation_error_gamma_{label}_hartree"] = phase_error
            row[f"energy_margin_gamma_{label}_hartree"] = margin
            row[f"success_gamma_{label}"] = margin >= 0.0
            row[f"budget_over_original_reference_gamma_{label}_minus_one"] = (
                budget / original_joint - 1.0
            )
        scoring_rows.append(row)

    new_point_count = sum(
        bool(row["new_direct_truth_coordinate"]) for row in branch_rows
    )
    anchor_rows = [
        row for row in branch_rows if row["point_role"] == "saved_lower_anchor_recomputation"
    ]
    inserted_rows = [
        row for row in branch_rows if row["point_role"] == "inserted_exact_time_triplet"
    ]
    checks = {
        "first_study_protocol_hash_match": _sha256(output_dir / "protocol.json")
        == EXPECTED_FIRST_STUDY_PROTOCOL_SHA256,
        "practical_prediction_hash_unchanged": _sha256(output_dir / "predictions.json")
        == EXPECTED_PREDICTIONS_SHA256,
        "all_requested_conditions_scored": len(scoring_rows) == len(conditions),
        "three_new_truth_points_per_condition": new_point_count == 3 * len(conditions),
        "one_anchor_recomputation_per_condition": len(anchor_rows) == len(conditions),
        "anchor_shift_reproduction_passed": max(
            row["source_reproduction_absolute_difference_hartree"] for row in anchor_rows
        )
        <= ANCHOR_SHIFT_ABSOLUTE_TOLERANCE_HARTREE,
        "all_eigenpair_residuals_passed": max(
            row["eigenpair_residual_2_norm"] for row in branch_rows
        )
        <= float(gates["direct_eigenpair_residual_2_norm"]),
        "all_unitarity_residuals_passed": max(
            row["unitarity_residual_frobenius"] for row in branch_rows
        )
        <= float(gates["pf_unitarity_frobenius"]),
        "all_inserted_branch_overlaps_passed": min(
            row["previous_branch_overlap_probability"] for row in inserted_rows
        )
        >= float(protocol["phase_and_branch_policy"]["branch_warning_previous_overlap_below"]),
        "all_inserted_ground_overlaps_passed": min(
            row["ground_state_overlap_probability"] for row in inserted_rows
        )
        >= float(protocol["phase_and_branch_policy"]["branch_warning_ground_overlap_below"]),
        "all_inserted_branches_resolved": all(
            row["branch_quality"] == "resolved" for row in inserted_rows
        ),
    }
    status = (
        "complete_exact_time_scoring"
        if conditions == configured and all(checks.values())
        else "partial_validation" if all(checks.values()) else "failed_numerical_validation"
    )
    _write_csv(output_dir / "branch_audit.csv", branch_rows)
    _write_csv(output_dir / "scoring.csv", scoring_rows)
    source_manifest = {
        "first_study_protocol_sha256": EXPECTED_FIRST_STUDY_PROTOCOL_SHA256,
        "practical_protocol_sha256": EXPECTED_PRACTICAL_PROTOCOL_SHA256,
        "practical_predictions_sha256": EXPECTED_PREDICTIONS_SHA256,
        "practical_phase_a_commit": EXPECTED_PHASE_A_COMMIT,
        "h01_root_absolute": str(h01_root.resolve()),
        "p03_root_absolute": str(p03_root.resolve()),
        "practical_root_absolute": str(practical_root.resolve()),
        "h01_p03_source_checks": validation["checks"],
        "h01_cache_records": validation["records"],
        "truth_files": source_truth_manifest,
    }
    _write_json(output_dir / "source_manifest.json", source_manifest)
    audit = {
        "status": status,
        "created_at": _now(),
        "execution_commit": _git_head(),
        "backend": backend,
        "gpu_id": int(gpu_id) if backend == "gpu" else None,
        "conditions": conditions,
        "checks": checks,
        "accounting": {
            "new_direct_truth_point_count": int(new_point_count),
            "anchor_recomputation_count": len(anchor_rows),
            "cache_reuse_count": cache_reuse_count,
            "scoring_row_count": len(scoring_rows),
            "branch_audit_row_count": len(branch_rows),
        },
        "extrema": {
            "maximum_anchor_shift_reproduction_difference_hartree": max(
                row["source_reproduction_absolute_difference_hartree"] for row in anchor_rows
            ),
            "maximum_eigenpair_residual_2_norm": max(
                row["eigenpair_residual_2_norm"] for row in branch_rows
            ),
            "maximum_unitarity_residual_frobenius": max(
                row["unitarity_residual_frobenius"] for row in branch_rows
            ),
            "minimum_inserted_previous_branch_overlap_probability": min(
                row["previous_branch_overlap_probability"] for row in inserted_rows
            ),
            "minimum_inserted_ground_state_overlap_probability": min(
                row["ground_state_overlap_probability"] for row in inserted_rows
            ),
            "minimum_inserted_phase_gap_radians": min(
                row["minimum_selected_phase_gap_radians"] for row in inserted_rows
            ),
            "maximum_exact_time_joint_regret": max(
                row["joint_formula_time_selection_regret"] for row in scoring_rows
            ),
        },
        "runtime": {
            "wall_seconds": float(time.perf_counter() - started),
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
    }
    _write_json(output_dir / "audit.json", audit)
    lines = [
        "# First-study S0 exact-time practical scoring",
        "",
        f"Status: **{status}**",
        "",
        "The frozen practical selector was not rerun or modified. Each selected time was scored directly at the fixed 0.99/1.00/1.01 triplet.",
        "",
        f"- Conditions: {len(scoring_rows)}/{len(configured)}.",
        f"- New direct truth coordinates: {new_point_count}.",
        f"- Saved lower-anchor recomputations: {len(anchor_rows)} (not new coordinates).",
        f"- Maximum exact-time joint regret: {audit['extrema']['maximum_exact_time_joint_regret']:.6%}.",
        f"- Gamma=1.01 successes: {sum(bool(row['success_gamma_1_01']) for row in scoring_rows)}/{len(scoring_rows)}.",
        "",
        "Primary regret uses the original two-PF saved grid. The extended-grid comparator is reported separately.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "status": status,
        "created_at": _now(),
        "execution_commit": audit["execution_commit"],
        "first_study_protocol_sha256": EXPECTED_FIRST_STUDY_PROTOCOL_SHA256,
        "practical_predictions_sha256": EXPECTED_PREDICTIONS_SHA256,
        "new_direct_truth_point_count": int(new_point_count),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "artifact_sha256": _artifact_hashes(output_dir),
    }
    _write_json(output_dir / "manifest.json", manifest)
    if status == "complete_exact_time_scoring":
        (output_dir / "COMPLETE").touch(exist_ok=False)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--practical-root", type=Path, required=True)
    parser.add_argument("--h01-root", type=Path, required=True)
    parser.add_argument("--p03-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    parser.add_argument("--gpu-id", type=int, default=0)
    parser.add_argument("--conditions", nargs="*")
    args = parser.parse_args()
    audit = run(
        args.project_root.resolve(),
        args.practical_root.resolve(),
        args.h01_root.resolve(),
        args.p03_root.resolve(),
        args.output.resolve(),
        args.backend,
        args.gpu_id,
        args.conditions,
    )
    print(json.dumps({"status": audit["status"], "accounting": audit["accounting"]}, indent=2))


if __name__ == "__main__":
    main()
