"""Finite-time H02 diagnosis using controlled approximate-state mixtures.

This is deliberately an oracle mechanism test.  It reuses the H01 analytic
time scale and exact-ground direct cost curves, while changing only the state
used in the five-point echo calibration.  No new direct PF eigenvalue points
are generated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import pickle
import resource
import time
from typing import Any, Iterable, Sequence

import numpy as np
from scipy.sparse.linalg import expm_multiply
from scipy.stats import pearsonr, spearmanr

import run_h01_approximate_state_calibration as h01


PROTOCOL_PATH = Path(__file__).with_name(
    "h02_finite_time_controlled_state_protocol.json"
)
EXPECTED_PROTOCOL_SHA256 = (
    "46345041b0da6449ff33d87f242ba8dade6ebf330eb1994426b063674bbfe4d9"
)
H01_ARTIFACT_RELATIVE = Path(
    "artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, value: Any) -> None:
    h01._write(path, value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _protocol() -> dict[str, Any]:
    return _load(PROTOCOL_PATH)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def controlled_state(
    ground: np.ndarray,
    direction: np.ndarray,
    excited_weight: float,
    phase: float,
) -> np.ndarray:
    """Construct sqrt(1-q)|0> + exp(i phi)sqrt(q)|chi>."""

    q = float(excited_weight)
    if not 0.0 < q <= 0.25:
        raise ValueError(f"invalid controlled excited weight: {q}")
    vector = (
        math.sqrt(1.0 - q) * np.asarray(ground, dtype=np.complex128)
        + np.exp(1j * float(phase))
        * math.sqrt(q)
        * np.asarray(direction, dtype=np.complex128)
    )
    return vector / np.linalg.norm(vector)


def orthogonal_component(
    ground: np.ndarray, approximate: np.ndarray
) -> tuple[np.ndarray, float]:
    """Return a phase-aligned normalized component orthogonal to ground."""

    overlap = complex(np.vdot(ground, approximate))
    if abs(overlap) == 0.0:
        aligned = np.asarray(approximate, dtype=np.complex128)
    else:
        aligned = np.asarray(approximate, dtype=np.complex128) * np.exp(
            -1j * np.angle(overlap)
        )
    component = aligned - ground * np.vdot(ground, aligned)
    norm = float(np.linalg.norm(component))
    if norm <= 1e-12:
        raise ValueError("approximate state has no resolvable orthogonal component")
    return component / norm, float(abs(overlap) ** 2)


def state_metrics(
    hamiltonian: Any,
    state: np.ndarray,
    ground: np.ndarray,
    ground_energy: float,
) -> dict[str, float]:
    action = hamiltonian @ state
    energy = float(np.vdot(state, action).real)
    variance = max(0.0, float(np.vdot(action, action).real - energy**2))
    return {
        "normalization": float(np.linalg.norm(state)),
        "energy_error_hartree": float(energy - ground_energy),
        "energy_variance_hartree2": variance,
        "hamiltonian_residual_2_norm": float(math.sqrt(variance)),
        "exact_ground_overlap_probability": float(abs(np.vdot(ground, state)) ** 2),
    }


def _load_or_prepare_system(
    project_root: Path,
    source_artifact: Path,
    output_root: Path,
    condition: str,
    component_processes: int,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    source_cache_path = source_artifact / "cache" / f"{condition}.pkl"
    source_metadata_path = (
        source_artifact / "cache" / f"{condition}.metadata.json"
    )
    cache_dir = output_root / "server_only_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{condition}.pkl"
    metadata_path = cache_dir / f"{condition}.metadata.json"
    if source_cache_path.exists():
        system = h01._load_system(source_cache_path)
        metadata = _load(source_metadata_path)
        provenance = "audited_h01_server_cache"
    elif cache_path.exists() and metadata_path.exists():
        with cache_path.open("rb") as stream:
            system = pickle.load(stream)
        metadata = _load(metadata_path)
        provenance = "resumed_h02_cache"
    else:
        system, metadata = h01.prepare_condition(
            condition,
            cache_dir / f"{condition}_work",
            int(component_processes),
        )
        with cache_path.open("wb") as stream:
            pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
        _dump(metadata_path, metadata)
        provenance = "fresh_h01_compatible_reconstruction"

    source_metadata = _load(source_metadata_path)
    source_system = source_metadata["system"]
    local_system_metadata = metadata.get("system", metadata)
    identity_checks = {
        key: local_system_metadata.get(key) == source_system.get(key)
        for key in (
            "condition",
            "geometry_angstrom",
            "basis",
            "frozen_core_spatial_orbitals",
            "active_electron_count",
            "active_spatial_orbitals",
            "n_alpha",
            "n_beta",
            "restricted_dimension",
            "group_count",
            "term_counts",
        )
    }
    numeric_differences = {
        key: abs(float(local_system_metadata[key]) - float(source_system[key]))
        for key in (
            "scf_energy_hartree",
            "ground_energy_without_constant_hartree",
            "removed_constant_hartree",
        )
    }
    state_numeric_differences = {
        f"{method}.{key}": abs(
            float(local_system_metadata["states"][method][key])
            - float(source_system["states"][method][key])
        )
        for method in ("cisd", "rhf_determinant")
        for key in (
            "energy_error_hartree",
            "energy_variance_hartree2",
            "overlap_probability_with_exact_ground_for_evaluation_only",
        )
    }
    if (
        not all(identity_checks.values())
        or max(numeric_differences.values())
        > float(
            _protocol()["evaluation"][
                "reconstruction_metadata_absolute_tolerance_hartree"
            ]
        )
        or max(state_numeric_differences.values())
        > float(
            _protocol()["evaluation"][
                "reconstruction_state_diagnostic_absolute_tolerance"
            ]
        )
    ):
        raise RuntimeError(
            f"{condition}: reconstructed H01 system mismatch: "
            f"identity={identity_checks}, numeric={numeric_differences}, "
            f"states={state_numeric_differences}"
        )
    metadata["h01_source_reconstruction_audit"] = {
        "identity_checks": identity_checks,
        "numeric_absolute_differences": numeric_differences,
        "state_numeric_absolute_differences": state_numeric_differences,
        "local_hamiltonian_sha256": local_system_metadata["hamiltonian_sha256"],
        "source_hamiltonian_sha256": source_system["hamiltonian_sha256"],
        "bytewise_hamiltonian_hash_matches": (
            local_system_metadata["hamiltonian_sha256"]
            == source_system["hamiltonian_sha256"]
        ),
        "gate_level_validation": "exact-ground echo five-point comparison follows",
    }
    return system, metadata, provenance


def _condition_states(
    condition: str, system: dict[str, Any]
) -> tuple[list[dict[str, Any]], np.ndarray]:
    protocol = _protocol()["controlled_state_construction"]
    ground = np.asarray(system["states"]["exact_ground"], dtype=np.complex128)
    ground_energy = float(system["energy"])
    hamiltonian = system["hamiltonian"]
    records: list[dict[str, Any]] = []
    vectors: list[np.ndarray] = []
    direction_map = {
        "cisd_orthogonal_component": "cisd",
        "rhf_orthogonal_component": "rhf_determinant",
    }
    for direction_id in protocol["directions"]:
        source_method = direction_map[direction_id]
        direction, source_overlap = orthogonal_component(
            ground, system["states"][source_method]
        )
        direction_energy = float(
            np.vdot(direction, hamiltonian @ direction).real - ground_energy
        )
        if direction_energy <= 0.0:
            raise RuntimeError(
                f"{condition}/{direction_id}: non-positive excitation energy"
            )
        for target in protocol["target_energy_errors_hartree"]:
            q = float(target) / direction_energy
            if q > float(protocol["maximum_excited_weight"]):
                raise RuntimeError(
                    f"{condition}/{direction_id}: q={q} exceeds fixed maximum"
                )
            for phase_index, phase in enumerate(protocol["relative_phases_radians"]):
                vector = controlled_state(ground, direction, q, float(phase))
                state_id = (
                    f"{direction_id}__de{float(target):.6g}__phase{phase_index}"
                )
                records.append({
                    "condition": condition,
                    "state_id": state_id,
                    "direction_id": direction_id,
                    "source_state_method": source_method,
                    "source_state_exact_overlap_probability": source_overlap,
                    "target_energy_error_hartree": float(target),
                    "direction_excitation_energy_hartree": direction_energy,
                    "excited_weight": q,
                    "phase_index": int(phase_index),
                    "relative_phase_radians": float(phase),
                    **state_metrics(
                        hamiltonian, vector, ground, ground_energy
                    ),
                })
                vectors.append(vector)
    return records, np.column_stack(vectors)


def _echo_models(
    system: dict[str, Any],
    sequence: Sequence[float],
    t_ana: float,
    controlled_vectors: np.ndarray,
    state_rows: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ground = np.asarray(system["states"]["exact_ground"], dtype=np.complex128)
    states = np.column_stack((ground, controlled_vectors))
    relative_times = _protocol()["calibration"]["relative_times"]
    amplitudes: list[np.ndarray] = []
    timing_rows = []
    for relative in relative_times:
        time_value = float(relative) * float(t_ana)
        evolved, pf_timing = h01._apply_pf_cpu(
            system, sequence, time_value, states
        )
        started = time.perf_counter()
        referenced = expm_multiply(
            (-1j * time_value) * system["hamiltonian"], evolved
        )
        reference_seconds = time.perf_counter() - started
        amplitudes.append(np.sum(states.conj() * referenced, axis=0))
        timing_rows.append({
            "time": time_value,
            "pf": pf_timing,
            "exact_reference_expm_multiply_seconds": reference_seconds,
        })
    amplitude_array = np.asarray(amplitudes)
    unwrapped = np.unwrap(np.angle(amplitude_array), axis=0)
    model_rows = []
    all_state_rows = [{"state_id": "exact_ground"}, *state_rows]
    for index, state_row in enumerate(all_state_rows):
        points = []
        for time_index, relative in enumerate(relative_times):
            time_value = float(relative) * float(t_ana)
            amplitude = complex(amplitude_array[time_index, index])
            points.append({
                "time": time_value,
                "relative_to_source_t_ana": float(relative),
                "echo_phase_hartree": float(unwrapped[time_index, index] / time_value),
                "echo_magnitude": float(abs(amplitude)),
            })
        model = h01._fit_proxy(
            points, "echo_phase_hartree", 5, t_ana, "echo_phase_5point"
        )
        model["optimum"] = h01.diagnosis._model_optimum(
            model, t_ana, h01._rotation_count(system, sequence)
        )
        model_rows.append({
            "state_id": state_row["state_id"],
            "points": points,
            "model": model,
        })
    return model_rows, {"backend": "cpu", "points": timing_rows}


def _relative_norm_error(values: Sequence[float], reference: Sequence[float]) -> float:
    left = np.asarray(values, dtype=float)
    right = np.asarray(reference, dtype=float)
    denominator = float(np.linalg.norm(right))
    return float(np.linalg.norm(left - right) / denominator) if denominator else math.inf


def _correlation(
    rows: Sequence[dict[str, Any]], predictor: str, response: str
) -> tuple[float | None, float | None]:
    x = np.asarray([float(row[predictor]) for row in rows])
    y = np.asarray([float(row[response]) for row in rows])
    x = np.log10(np.maximum(np.abs(x), 1e-300))
    y = np.log10(np.maximum(np.abs(y), 1e-300))
    if len(x) < 3 or len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return None, None
    return float(pearsonr(x, y).statistic), float(spearmanr(x, y).statistic)


def _span(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    scale = max(float(np.min(np.abs(array))), 1e-300)
    return float((np.max(array) - np.min(array)) / scale)


def run(
    project_root: Path,
    output_root: Path,
    component_processes: int,
    h01_source_artifact: Path | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    protocol_hash = _sha256(PROTOCOL_PATH)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("fixed H02 protocol SHA-256 mismatch")
    protocol = _protocol()
    source_root = (
        (project_root / H01_ARTIFACT_RELATIVE)
        if h01_source_artifact is None
        else h01_source_artifact.resolve()
    )
    source_summary = _load(source_root / "aggregate/summary.json")
    source_main_rows = [
        row for row in source_summary["rows"]
        if row["model"] == "echo_phase_5point"
        and row["state_method"] == "exact_ground"
    ]
    if (output_root / "COMPLETE").exists():
        raise FileExistsError(f"completed output already exists: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / ".gitignore").write_text(
        "server_only_cache/\n", encoding="utf-8"
    )

    states_out: list[dict[str, Any]] = []
    models_out: list[dict[str, Any]] = []
    exact_checks: list[dict[str, Any]] = []
    timing_out: list[dict[str, Any]] = []
    reconstruction_rows: list[dict[str, Any]] = []

    for condition in protocol["conditions"]:
        system, metadata, reconstruction = _load_or_prepare_system(
            project_root,
            source_root,
            output_root,
            condition,
            component_processes,
        )
        state_rows, state_vectors = _condition_states(condition, system)
        states_out.extend(state_rows)
        reconstruction_rows.append({
            "condition": condition,
            "provenance": reconstruction,
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "restricted_dimension": int(system["hamiltonian"].shape[0]),
            "peak_cpu_rss_kib": int(
                metadata.get("system", metadata)["peak_cpu_rss_kib"]
            ),
            "bytewise_hamiltonian_hash_matches": metadata[
                "h01_source_reconstruction_audit"
            ]["bytewise_hamiltonian_hash_matches"],
            "maximum_metadata_numeric_difference": max(
                metadata["h01_source_reconstruction_audit"][
                    "numeric_absolute_differences"
                ].values()
            ),
            "maximum_state_numeric_difference": max(
                metadata["h01_source_reconstruction_audit"][
                    "state_numeric_absolute_differences"
                ].values()
            ),
        })
        for formula in protocol["formulae"]:
            source_echo_path = source_root / "echo" / f"{condition}__{formula}.json"
            source_echo = _load(source_echo_path)
            sequence = h01.diagnosis._formula_s2_sequence(formula)
            if sequence != source_echo["s2_sequence"]:
                raise RuntimeError(f"{condition}/{formula}: PF sequence mismatch")
            model_rows, timing = _echo_models(
                system,
                sequence,
                float(source_echo["analytic_time"]),
                state_vectors,
                state_rows,
            )
            computed_exact = model_rows[0]
            saved_exact = source_echo["models"]["exact_ground"][
                "echo_phase_5point"
            ]
            saved_points = source_echo["states"]["exact_ground"]
            maximum_point_difference = max(
                abs(
                    float(left["echo_phase_hartree"])
                    - float(right["echo_phase_hartree"])
                )
                for left, right in zip(
                    computed_exact["points"], saved_points, strict=True
                )
            )
            exact_checks.append({
                "condition": condition,
                "formula": formula,
                "source_echo_sha256": _sha256(source_echo_path),
                "maximum_echo_phase_difference_hartree": maximum_point_difference,
                "coefficient_relative_2_norm_error": _relative_norm_error(
                    computed_exact["model"]["coefficient_values"],
                    saved_exact["coefficient_values"],
                ),
                "passed": maximum_point_difference
                <= float(
                    protocol["evaluation"][
                        "exact_echo_reproduction_absolute_tolerance_hartree"
                    ]
                ),
            })
            reference_coefficients = saved_exact["coefficient_values"]
            reference_optimum = saved_exact["optimum"]
            state_lookup = {row["state_id"]: row for row in state_rows}
            for item in model_rows[1:]:
                state = state_lookup[item["state_id"]]
                model = item["model"]
                optimum = model["optimum"]
                models_out.append({
                    "condition": condition,
                    "formula": formula,
                    "state_id": item["state_id"],
                    "direction_id": state["direction_id"],
                    "target_energy_error_hartree": state[
                        "target_energy_error_hartree"
                    ],
                    "phase_index": state["phase_index"],
                    "relative_phase_radians": state["relative_phase_radians"],
                    "a4": float(model["coefficient_values"][0]),
                    "a6": float(model["coefficient_values"][1]),
                    "coefficient_relative_2_norm_error": _relative_norm_error(
                        model["coefficient_values"], reference_coefficients
                    ),
                    "predicted_time": float(optimum["time"]),
                    "exact_echo_predicted_time": float(reference_optimum["time"]),
                    "predicted_time_relative_error": float(
                        abs(optimum["time"] / reference_optimum["time"] - 1.0)
                    ),
                    "predicted_model_cost": float(optimum["cost"]),
                    "exact_echo_predicted_model_cost": float(
                        reference_optimum["cost"]
                    ),
                    "predicted_model_cost_relative_error": float(
                        abs(optimum["cost"] / reference_optimum["cost"] - 1.0)
                    ),
                    "minimum_echo_magnitude": min(
                        float(point["echo_magnitude"])
                        for point in item["points"]
                    ),
                    "training_design_condition_number": float(
                        model["training_design_condition_number"]
                    ),
                    "training_maximum_absolute_residual_hartree": float(
                        model["training_maximum_absolute_residual_hartree"]
                    ),
                })
            timing_out.append({
                "condition": condition,
                "formula": formula,
                "total_pf_seconds": sum(
                    float(point["pf"]["total"])
                    for point in timing["points"]
                ),
                "total_exact_reference_seconds": sum(
                    float(point["exact_reference_expm_multiply_seconds"])
                    for point in timing["points"]
                ),
            })

    direct_costs = {
        (row["condition"], row["formula"]): float(row["direct_minimum_cost"])
        for row in source_main_rows
        if row["condition"] in protocol["conditions"]
        and row["formula"] in protocol["formulae"]
    }
    selection_rows = []
    model_by_key = {
        (row["condition"], row["state_id"], row["formula"]): row
        for row in models_out
    }
    for state in states_out:
        condition, state_id = state["condition"], state["state_id"]
        candidates = [
            model_by_key[(condition, state_id, formula)]
            for formula in protocol["formulae"]
        ]
        selected = min(candidates, key=lambda row: row["predicted_model_cost"])[
            "formula"
        ]
        reference = min(
            protocol["formulae"], key=lambda formula: direct_costs[(condition, formula)]
        )
        selection_rows.append({
            "condition": condition,
            "state_id": state_id,
            "direction_id": state["direction_id"],
            "target_energy_error_hartree": state[
                "target_energy_error_hartree"
            ],
            "phase_index": state["phase_index"],
            "relative_phase_radians": state["relative_phase_radians"],
            "selected_formula": selected,
            "direct_reference_formula": reference,
            "selection_matches_direct_reference": selected == reference,
            "direct_formula_choice_regret": float(
                direct_costs[(condition, selected)]
                / direct_costs[(condition, reference)]
                - 1.0
            ),
        })

    phase_group_rows = []
    thresholds = protocol["evaluation"]
    for condition in protocol["conditions"]:
        for direction in protocol["controlled_state_construction"]["directions"]:
            for target in protocol["controlled_state_construction"][
                "target_energy_errors_hartree"
            ]:
                states = [
                    row for row in states_out
                    if row["condition"] == condition
                    and row["direction_id"] == direction
                    and row["target_energy_error_hartree"] == float(target)
                ]
                choices = [
                    row for row in selection_rows
                    if row["condition"] == condition
                    and row["direction_id"] == direction
                    and row["target_energy_error_hartree"] == float(target)
                ]
                formula_time_spans = {}
                formula_cost_spans = {}
                for formula in protocol["formulae"]:
                    models = [
                        row for row in models_out
                        if row["condition"] == condition
                        and row["direction_id"] == direction
                        and row["target_energy_error_hartree"] == float(target)
                        and row["formula"] == formula
                    ]
                    formula_time_spans[formula] = _span(
                        row["predicted_time"] for row in models
                    )
                    formula_cost_spans[formula] = _span(
                        row["predicted_model_cost"] for row in models
                    )
                selection_changes = len(
                    {row["selected_formula"] for row in choices}
                ) > 1
                time_exceeds = max(formula_time_spans.values()) >= float(
                    thresholds["meaningful_relative_optimum_time_spread"]
                )
                cost_exceeds = max(formula_cost_spans.values()) >= float(
                    thresholds["meaningful_relative_model_cost_spread"]
                )
                phase_group_rows.append({
                    "condition": condition,
                    "direction_id": direction,
                    "target_energy_error_hartree": float(target),
                    "state_count": len(states),
                    "energy_error_spread_hartree": float(
                        np.ptp([row["energy_error_hartree"] for row in states])
                    ),
                    "variance_spread_hartree2": float(
                        np.ptp([row["energy_variance_hartree2"] for row in states])
                    ),
                    "residual_spread": float(
                        np.ptp(
                            [row["hamiltonian_residual_2_norm"] for row in states]
                        )
                    ),
                    "overlap_probability_spread": float(
                        np.ptp(
                            [row["exact_ground_overlap_probability"] for row in states]
                        )
                    ),
                    "selected_formulae": ";".join(
                        sorted({row["selected_formula"] for row in choices})
                    ),
                    "selection_changes_with_phase": selection_changes,
                    "maximum_direct_formula_choice_regret": max(
                        row["direct_formula_choice_regret"] for row in choices
                    ),
                    "current_m3_relative_time_span": formula_time_spans["current_m3"],
                    "yoshida4_relative_time_span": formula_time_spans["yoshida4"],
                    "current_m3_relative_model_cost_span": formula_cost_spans[
                        "current_m3"
                    ],
                    "yoshida4_relative_model_cost_span": formula_cost_spans[
                        "yoshida4"
                    ],
                    "constructive_counterexample": bool(
                        selection_changes or time_exceeds or cost_exceeds
                    ),
                })

    state_lookup = {(row["condition"], row["state_id"]): row for row in states_out}
    joined = [
        {**row, **state_lookup[(row["condition"], row["state_id"])]}
        for row in models_out
    ]
    correlation_rows = []
    for formula in protocol["formulae"]:
        rows = [row for row in joined if row["formula"] == formula]
        for predictor in (
            "energy_error_hartree",
            "energy_variance_hartree2",
            "hamiltonian_residual_2_norm",
            "exact_ground_overlap_probability",
        ):
            predictor_key = predictor
            if predictor == "exact_ground_overlap_probability":
                for row in rows:
                    row["one_minus_exact_ground_overlap"] = 1.0 - float(
                        row[predictor]
                    )
                predictor_key = "one_minus_exact_ground_overlap"
            for response in (
                "coefficient_relative_2_norm_error",
                "predicted_time_relative_error",
                "predicted_model_cost_relative_error",
            ):
                pearson, spearman = _correlation(rows, predictor_key, response)
                correlation_rows.append({
                    "formula": formula,
                    "predictor": predictor_key,
                    "response": response,
                    "sample_count": len(rows),
                    "log10_pearson": pearson,
                    "rank_spearman": spearman,
                })

    scalar_tolerance = float(
        protocol["evaluation"]["state_scalar_invariance_absolute_tolerance"]
    )
    maximum_scalar_spreads = {
        "energy_error_hartree": max(
            row["energy_error_spread_hartree"] for row in phase_group_rows
        ),
        "energy_variance_hartree2": max(
            row["variance_spread_hartree2"] for row in phase_group_rows
        ),
        "residual": max(row["residual_spread"] for row in phase_group_rows),
        "overlap_probability": max(
            row["overlap_probability_spread"] for row in phase_group_rows
        ),
    }
    checks = {
        "protocol_hash_matches": protocol_hash == EXPECTED_PROTOCOL_SHA256,
        "exact_echo_reproduction": all(row["passed"] for row in exact_checks),
        "all_phase_groups_have_four_states": all(
            row["state_count"] == 4 for row in phase_group_rows
        ),
        "phase_group_scalar_invariance": all(
            value <= scalar_tolerance for value in maximum_scalar_spreads.values()
        ),
        "no_new_direct_truth": True,
    }
    counterexamples = [
        row for row in phase_group_rows if row["constructive_counterexample"]
    ]
    selection_flip_groups = [
        row for row in phase_group_rows if row["selection_changes_with_phase"]
    ]
    checks_passed = all(checks.values())
    summary = {
        "controlled_state_count": len(states_out),
        "proxy_model_count": len(models_out),
        "phase_group_count": len(phase_group_rows),
        "constructive_counterexample_group_count": len(counterexamples),
        "selection_flip_group_count": len(selection_flip_groups),
        "maximum_direct_formula_choice_regret": max(
            row["direct_formula_choice_regret"] for row in selection_rows
        ),
        "maximum_scalar_spreads": maximum_scalar_spreads,
        "scalar_metrics_sufficient_for_finite_time_calibration": (
            None if not checks_passed else not bool(counterexamples)
        ),
    }
    status = (
        "complete_with_findings" if checks_passed
        else "failed_numerical_validation"
    )
    audit = {
        "status": status,
        "protocol_sha256": protocol_hash,
        "source_h01_commit": protocol["source"]["h01_result_commit"],
        "checks": checks,
        "checks_passed": checks_passed,
        "summary": summary,
        "exact_echo_reproduction": exact_checks,
        "reconstruction": reconstruction_rows,
        "timing": timing_out,
        "scope": {
            "catalog_item": "H02",
            "new_direct_pf_points": 0,
            "oracle_controlled_state_construction": True,
        },
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }
    _write_csv(output_root / "controlled_states.csv", states_out)
    _write_csv(output_root / "proxy_models.csv", models_out)
    _write_csv(output_root / "selection_results.csv", selection_rows)
    _write_csv(output_root / "phase_group_summary.csv", phase_group_rows)
    _write_csv(output_root / "correlations.csv", correlation_rows)
    _dump(output_root / "audit.json", audit)

    report_lines = [
        "# H02 finite-time controlled-state diagnosis",
        "",
        f"Status: **{status}**",
        "",
        "This is an oracle mechanism diagnostic built on the fixed H01 N2/CO result. "
        "It changes only the calibration state and adds no direct PF eigenvalue points.",
        "",
        "## Result",
        "",
        f"- Controlled states: `{summary['controlled_state_count']}`; finite-time proxy models: `{summary['proxy_model_count']}`.",
        f"- Scalar-invariant phase groups: `{summary['phase_group_count']}`.",
        f"- Constructive counterexample groups: `{summary['constructive_counterexample_group_count']}`.",
        f"- Groups changing the selected PF: `{summary['selection_flip_group_count']}`.",
        f"- Maximum direct PF-choice regret: `{100.0 * summary['maximum_direct_formula_choice_regret']:.4f}%`.",
        f"- Scalar metrics sufficient for finite-time calibration: **{summary['scalar_metrics_sufficient_for_finite_time_calibration']}**.",
        "",
        "Each phase quartet has the same state energy error, variance, residual norm, and exact-ground overlap by construction. "
        "Its scientific interpretation is accepted only if every numerical check below passes.",
        "",
        "## Numerical checks",
        "",
    ]
    report_lines.extend(
        f"- {key}: **{'PASS' if value else 'FAIL'}**"
        for key, value in checks.items()
    )
    if not checks_passed:
        report_lines.extend([
            "",
            "## Blocking numerical validation failure",
            "",
            "This run is a failed reconstruction pilot, not an H02 scientific result. "
            "Do not interpret the apparent phase counterexamples until the original H01 server caches reproduce the saved exact-ground echo within tolerance.",
        ])
    report_lines.extend([
        "",
        "## Interpretation and scope",
        "",
        "- This directly bridges the earlier H2/H4 leading-order H02 counterexample to the H01 finite-time two-term N2/CO setting.",
        "- Energy error, variance, residual norm, or overlap alone must not qualify an approximate state for PF cost calibration.",
        "- The result does not yet provide an operational qualifier; an error-operator-sensitive diagnostic is still required.",
        "- H01 oracle analytic times and exact direct costs remain evaluation-only inputs, so this is not end-to-end cheap calibration.",
    ])
    (output_root / "report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    tracked = [
        path for path in sorted(output_root.iterdir())
        if path.is_file() and path.name != "manifest.json"
    ]
    manifest = {
        "status": audit["status"],
        "protocol_sha256": protocol_hash,
        "source": {
            "h01_result_commit": protocol["source"]["h01_result_commit"],
            "h01_summary_sha256": _sha256(source_root / "aggregate/summary.json"),
            "h01_artifact_path": str(source_root),
        },
        "artifact_files": {
            str(path.relative_to(project_root)): _sha256(path) for path in tracked
        },
        "server_only_excluded": ["server_only_cache/"],
        "runtime": audit["runtime"],
    }
    _dump(output_root / "manifest.json", manifest)
    complete = output_root / "COMPLETE"
    if checks_passed:
        complete.touch()
    else:
        complete.unlink(missing_ok=True)
    return audit


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--component-processes", type=int, default=1)
    parser.add_argument(
        "--h01-server-artifact",
        type=Path,
        help="Original H01 artifact directory containing excluded cache/*.pkl files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    run(
        args.project_root.resolve(),
        args.output.resolve(),
        int(args.component_processes),
        None
        if args.h01_server_artifact is None
        else args.h01_server_artifact.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
