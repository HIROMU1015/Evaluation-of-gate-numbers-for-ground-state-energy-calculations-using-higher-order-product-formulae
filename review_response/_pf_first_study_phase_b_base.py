"""Score frozen first-study predictions with direct PF truth.

This scorer is committed before Phase A is executed.  It refuses to continue
if the frozen prediction or any Phase-A input hash has changed.
"""

from __future__ import annotations

import argparse
import ast
import csv
from datetime import datetime
import json
from pathlib import Path
import platform
import resource
import shutil
import time
from typing import Any, Sequence

import numpy as np

from review_response._pf_first_study_experiment_a_support import (
    atomic_json,
    formula_registry,
    git_output,
    load_protocol,
    sha256_file,
    write_csv,
)
from review_response.pf_first_study_experiment_a import (
    build_decomposition_rows as _unused_experiment_a_decomposition,
    track_direct_branch,
)
from review_response.pf_first_study_phase_common import (
    build_unitary,
    controlled_state_family,
    evaluate_fit,
    load_h4_source,
    model_cost,
    operator_diagnostics,
    proxy_noise_hartree,
    quality_class,
    state_diagnostics,
)
from review_response.run_pf_first_study_phase_a import (
    _experiment_c_inputs,
    _proxy_rows_for_signed_times,
)


DEFAULT_OUTPUT = Path("artifacts/pf_first_study_phase_b_20260925")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _verify_phase_a(
    phase_a_dir: Path, protocol_hash: str
) -> tuple[dict[str, Any], str]:
    prediction_path = phase_a_dir / "predictions.json"
    words = (phase_a_dir / "prediction.sha256").read_text(
        encoding="utf-8"
    ).split()
    prediction_hash = sha256_file(prediction_path)
    if len(words) < 2 or words[0] != prediction_hash:
        raise ValueError("Phase A prediction SHA-256 mismatch")
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    if predictions["protocol_sha256"] != protocol_hash:
        raise ValueError("Phase A protocol hash mismatch")
    if predictions.get("truth_opened") is not False:
        raise ValueError("Phase A prediction does not assert a closed truth barrier")
    for filename, expected in predictions["phase_a_files"].items():
        if sha256_file(phase_a_dir / filename) != expected:
            raise ValueError(f"Phase A file hash mismatch: {filename}")
    manifest = json.loads((phase_a_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["prediction_sha256"] != prediction_hash:
        raise ValueError("Phase A manifest prediction hash mismatch")
    if not (phase_a_dir / "SELECTION_FROZEN").is_file():
        raise ValueError("Phase A SELECTION_FROZEN marker missing")
    return predictions, prediction_hash


def _direct_rows(
    *,
    experiment_id: str,
    case_id: str,
    formula_id: str,
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    sequence: Sequence[float],
    reference_state: np.ndarray,
    reference_energy: float,
    magnitudes: Sequence[float],
    signs: Sequence[int],
    degeneracy_gap: float,
    target_error: float,
    beta: float,
    step_cost: int,
    grid_role: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sign in signs:
        signed_times = [int(sign) * float(value) for value in magnitudes]
        unitaries = [
            build_unitary(spectra, sequence, time_value)
            for time_value in signed_times
        ]
        tracked = track_direct_branch(
            unitaries,
            signed_times,
            reference_state,
            reference_energy,
            degeneracy_gap,
        )
        for magnitude, signed_time, unitary, direct in zip(
            magnitudes, signed_times, unitaries, tracked, strict=True
        ):
            unitarity = float(
                np.linalg.norm(
                    unitary.conj().T @ unitary - np.eye(unitary.shape[0])
                )
            )
            reliable = bool(
                direct["ground_state_overlap_probability"] >= 0.9
                and direct["previous_branch_overlap_probability"] >= 0.9
                and direct["eigenpair_residual_2_norm"] <= 1e-10
            )
            cost = model_cost(
                target_error,
                beta,
                step_cost,
                abs(float(signed_time)),
                float(direct["direct_shift_hartree"]),
            )
            rows.append(
                {
                    "experiment_id": experiment_id,
                    "case_id": case_id,
                    "formula_id": formula_id,
                    "grid_role": grid_role,
                    "sign": int(sign),
                    "absolute_time": float(magnitude),
                    "time_hartree_inverse": float(signed_time),
                    **direct,
                    "unitarity_residual_frobenius": unitarity,
                    "branch_reliable": reliable,
                    "direct_cost": cost,
                    "infeasible_error_budget": cost is None,
                }
            )
    return rows


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _models_lookup(rows: Sequence[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    result: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["experiment_id"],
            row["case_id"],
            row["formula_id"],
            row["state_id"],
        )
        if row["model_id"] != "raw_positive_even_two_term":
            continue
        result[key] = {
            "powers": [int(value) for value in ast.literal_eval(row["powers"])],
            "coefficients": [
                float(value) for value in ast.literal_eval(row["coefficients"])
            ],
            "status": row["status"],
        }
    return result


def _observation_lookup(rows: Sequence[dict[str, str]]) -> dict[tuple[str, str, str, str, int, float], dict[str, str]]:
    return {
        (
            row["experiment_id"],
            row["case_id"],
            row["formula_id"],
            row["state_id"],
            int(row["sign"]),
            float(row["absolute_time"]),
        ): row
        for row in rows
    }


def _direct_lookup(rows: Sequence[dict[str, Any]]) -> dict[tuple[str, str, str, str, int, float], dict[str, Any]]:
    return {
        (
            row["experiment_id"],
            row["case_id"],
            row["formula_id"],
            row["grid_role"],
            int(row["sign"]),
            float(row["absolute_time"]),
        ): row
        for row in rows
    }


def _decomposition(
    *,
    phase_a_observations: Sequence[dict[str, str]],
    exact_observations: Sequence[dict[str, Any]],
    model_rows: Sequence[dict[str, str]],
    direct_rows: Sequence[dict[str, Any]],
    b_evaluation_times: set[float],
) -> list[dict[str, Any]]:
    approximate = _observation_lookup(phase_a_observations)
    exact = {
        (
            row["experiment_id"],
            row["case_id"],
            row["formula_id"],
            int(row["sign"]),
            float(row["absolute_time"]),
        ): row
        for row in exact_observations
    }
    models = _models_lookup(model_rows)
    direct = _direct_lookup(direct_rows)
    result: list[dict[str, Any]] = []
    for key, row in approximate.items():
        experiment_id, case_id, formula_id, state_id, sign, magnitude = key
        if experiment_id == "B" and magnitude not in b_evaluation_times:
            continue
        model = models[(experiment_id, case_id, formula_id, state_id)]
        exact_row = exact[
            (experiment_id, case_id, formula_id, sign, magnitude)
        ]
        direct_row = direct[
            (
                experiment_id,
                case_id,
                formula_id,
                "mechanism_fixed",
                sign,
                magnitude,
            )
        ]
        time_value = float(row["time_hartree_inverse"])
        fitted = evaluate_fit(model, time_value)
        g_approx = float(row["proxy_imag_hartree"])
        g_exact = float(exact_row["proxy_imag_hartree"])
        delta_direct = float(direct_row["direct_shift_hartree"])
        fit_signed = fitted - g_approx
        state_signed = g_approx - g_exact
        proxy_signed = g_exact - delta_direct
        total_signed = fitted - delta_direct
        closure = fit_signed + state_signed + proxy_signed - total_signed
        result.append(
            {
                "experiment_id": experiment_id,
                "case_id": case_id,
                "formula_id": formula_id,
                "state_id": state_id,
                "sign": sign,
                "absolute_time": magnitude,
                "time_hartree_inverse": time_value,
                "model_status": model["status"],
                "quality_class": row["quality_class"],
                "fhat_approx_hartree": fitted,
                "g_approx_hartree": g_approx,
                "g_exact_hartree": g_exact,
                "delta_direct_hartree": delta_direct,
                "E_fit_signed_hartree": fit_signed,
                "E_state_signed_hartree": state_signed,
                "E_proxy_signed_hartree": proxy_signed,
                "E_total_signed_hartree": total_signed,
                "E_fit_hartree": abs(fit_signed),
                "E_state_hartree": abs(state_signed),
                "E_proxy_hartree": abs(proxy_signed),
                "E_total_hartree": abs(total_signed),
                "closure_residual_hartree": closure,
            }
        )
    return result


def _dominance_rows(
    decomposition: Sequence[dict[str, Any]], target_error: float
) -> list[dict[str, Any]]:
    keys = sorted(
        {
            (
                row["experiment_id"],
                row["case_id"],
                row["formula_id"],
                row["state_id"],
            )
            for row in decomposition
        }
    )
    result = []
    components = ("E_fit_hartree", "E_state_hartree", "E_proxy_hartree")
    for key in keys:
        rows = [
            row
            for row in decomposition
            if (
                row["experiment_id"],
                row["case_id"],
                row["formula_id"],
                row["state_id"],
            )
            == key
            and row["quality_class"] == "resolved"
        ]
        counts = {component: 0 for component in components}
        for row in rows:
            for component in components:
                others = [row[item] for item in components if item != component]
                if row[component] >= 3.0 * max(others):
                    counts[component] += 1
        needed = len(rows) // 2 + 1
        dominant = [component for component, count in counts.items() if count >= needed]
        result.append(
            {
                "experiment_id": key[0],
                "case_id": key[1],
                "formula_id": key[2],
                "state_id": key[3],
                "resolved_point_count": len(rows),
                "majority_count_required": needed,
                "fit_dominant_count": counts["E_fit_hartree"],
                "state_dominant_count": counts["E_state_hartree"],
                "proxy_dominant_count": counts["E_proxy_hartree"],
                "dominant_component": dominant[0] if len(dominant) == 1 else "mixed",
                "maximum_component_over_target_error": max(
                    (
                        row[component] / target_error
                        for row in rows
                        for component in components
                    ),
                    default=0.0,
                ),
            }
        )
    return result


def run(
    project_root: Path,
    protocol_path: Path,
    phase_a_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    started = time.perf_counter()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {output_dir}")
    output_dir.mkdir(parents=True)
    protocol, protocol_hash = load_protocol(protocol_path)
    predictions, prediction_hash = _verify_phase_a(phase_a_dir, protocol_hash)
    system, source_manifest = load_h4_source(project_root, protocol)
    formulas = formula_registry(protocol)
    formula_by_id = {row["formula_id"]: row for row in formulas}
    target_error = float(protocol["constants"]["target_error_hartree"])
    beta = float(protocol["constants"]["qpe_beta"])
    degeneracy_gap = float(
        protocol["phase_and_branch_policy"]["degenerate_phase_gap_radians"]
    )
    mechanism = protocol["experiment_B_h4"]["fixed_time_mechanism_track"]
    b_magnitudes = sorted(
        {
            *map(float, mechanism["training_time_magnitudes_hartree_inverse"]),
            *map(float, mechanism["evaluation_time_magnitudes_hartree_inverse"]),
        }
    )
    direct_rows: list[dict[str, Any]] = []
    exact_rows: list[dict[str, Any]] = []
    for formula in formulas:
        formula_id = formula["formula_id"]
        step_cost = int(
            protocol["formulae"][formula_id]["h4_pauli_rotations_per_pf_step"]
        )
        exact_rows.extend(
            _proxy_rows_for_signed_times(
                experiment_id="B",
                case_id="H4",
                hamiltonian=system["hamiltonian"],
                spectra=system["spectra"],
                sequence=formula["sequence"],
                formula_id=formula_id,
                states={"exact": system["states"]["exact"]},
                magnitudes=b_magnitudes,
                signs=mechanism["signs"],
            )
        )
        direct_rows.extend(
            _direct_rows(
                experiment_id="B",
                case_id="H4",
                formula_id=formula_id,
                spectra=system["spectra"],
                sequence=formula["sequence"],
                reference_state=system["states"]["exact"],
                reference_energy=system["energy"],
                magnitudes=b_magnitudes,
                signs=mechanism["signs"],
                degeneracy_gap=degeneracy_gap,
                target_error=target_error,
                beta=beta,
                step_cost=step_cost,
                grid_role="mechanism_fixed",
            )
        )
        frozen_grid = predictions["experiment_B"]["truth_reference_grids_frozen"][formula_id]
        direct_rows.extend(
            _direct_rows(
                experiment_id="B",
                case_id="H4",
                formula_id=formula_id,
                spectra=system["spectra"],
                sequence=formula["sequence"],
                reference_state=system["states"]["exact"],
                reference_energy=system["energy"],
                magnitudes=frozen_grid,
                signs=[1],
                degeneracy_gap=degeneracy_gap,
                target_error=target_error,
                beta=beta,
                step_cost=step_cost,
                grid_role="decision_frozen_grid",
            )
        )

    c_spec = protocol["experiment_C_fixed_h_two_level"]
    c_hamiltonian, c_controlled = _experiment_c_inputs(protocol)
    c_energies, c_vectors = np.linalg.eigh(c_hamiltonian)
    c_exact = c_vectors[:, 0]
    yoshida = formula_by_id["yoshida4"]
    pauli_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    pauli_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    for lambda_value in c_spec["lambda_values"]:
        case_id = f"lambda_{float(lambda_value):.16g}"
        groups = [
            pauli_x + float(lambda_value) * pauli_z,
            (1.0 - float(lambda_value)) * pauli_z,
        ]
        spectra = [np.linalg.eigh(group) for group in groups]
        exact_rows.extend(
            _proxy_rows_for_signed_times(
                experiment_id="C",
                case_id=case_id,
                hamiltonian=c_hamiltonian,
                spectra=spectra,
                sequence=yoshida["sequence"],
                formula_id="yoshida4",
                states={"exact": c_exact},
                magnitudes=c_spec["absolute_time_magnitudes_hartree_inverse"],
                signs=c_spec["signs"],
            )
        )
        direct_rows.extend(
            _direct_rows(
                experiment_id="C",
                case_id=case_id,
                formula_id="yoshida4",
                spectra=spectra,
                sequence=yoshida["sequence"],
                reference_state=c_exact,
                reference_energy=float(c_energies[0]),
                magnitudes=c_spec["absolute_time_magnitudes_hartree_inverse"],
                signs=c_spec["signs"],
                degeneracy_gap=degeneracy_gap,
                target_error=target_error,
                beta=beta,
                step_cost=int(c_spec["resource_step_cost"]),
                grid_role="mechanism_fixed",
            )
        )

    phase_a_observations = _read_csv(phase_a_dir / "phase_a_proxy_observables.csv")
    model_rows = _read_csv(phase_a_dir / "phase_a_proxy_models.csv")
    decomposition = _decomposition(
        phase_a_observations=phase_a_observations,
        exact_observations=exact_rows,
        model_rows=model_rows,
        direct_rows=direct_rows,
        b_evaluation_times=set(
            map(float, mechanism["evaluation_time_magnitudes_hartree_inverse"])
        ),
    )
    maximum_closure = max(
        abs(float(row["closure_residual_hartree"])) for row in decomposition
    )
    closure_gate = max(1e-12, 1e-8 * target_error)

    state_rows = []
    exact = system["states"]["exact"]
    for state_id, state in system["states"].items():
        state_rows.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "state_id": state_id,
                **state_diagnostics(
                    system["hamiltonian"], state, exact, system["energy"]
                ),
            }
        )
    operator_rows = []
    for formula_id, operators in system["operators"].items():
        for state_id, state in system["states"].items():
            for order, operator in operators.items():
                operator_rows.append(
                    {
                        "experiment_id": "B",
                        "case_id": "H4",
                        "formula_id": formula_id,
                        "state_id": state_id,
                        "order": order,
                        **operator_diagnostics(operator, state, exact),
                    }
                )

    exact_signal_rows = []
    direct_fixed_lookup = _direct_lookup(direct_rows)
    for row in exact_rows:
        direct = direct_fixed_lookup[
            (
                row["experiment_id"],
                row["case_id"],
                row["formula_id"],
                "mechanism_fixed",
                int(row["sign"]),
                float(row["absolute_time"]),
            )
        ]
        truth_noise = max(
            float(row["proxy_noise_hartree"]),
            float(direct["eigenpair_residual_2_norm"])
            / abs(float(row["time_hartree_inverse"])),
        )
        rho, quality = quality_class(float(row["proxy_imag_hartree"]), truth_noise)
        exact_signal_rows.append(
            {
                **row,
                "truth_noise_hartree": truth_noise,
                "truth_signal_to_noise_rho": rho,
                "truth_quality_class": quality,
            }
        )
    signal_rows = [
        {
            **row,
            "truth_noise_hartree": None,
            "truth_signal_to_noise_rho": None,
            "truth_quality_class": None,
        }
        for row in phase_a_observations
    ] + exact_signal_rows

    selection = predictions["experiment_B"]["selection"]
    allocation_rows = []
    resource_rows = []
    decision_grid_rows = [
        row
        for row in direct_rows
        if row["experiment_id"] == "B"
        and row["grid_role"] == "decision_frozen_grid"
        and row["branch_reliable"]
        and row["direct_cost"] is not None
    ]
    reference = min(decision_grid_rows, key=lambda row: row["direct_cost"])
    if selection["status"] == "selected":
        selected_formula = selection["selected_formula"]
        selected_time = float(selection["selected_time_hartree_inverse"])
        selected_candidates = [
            row
            for row in decision_grid_rows
            if row["formula_id"] == selected_formula
            and abs(float(row["absolute_time"]) - selected_time) <= 1e-14
        ]
        if len(selected_candidates) != 1:
            raise ValueError("frozen selected point is absent or duplicated")
        selected_direct = selected_candidates[0]
        same_formula_best = min(
            (
                row
                for row in decision_grid_rows
                if row["formula_id"] == selected_formula
            ),
            key=lambda row: row["direct_cost"],
        )
        for gamma in protocol["constants"]["budget_multipliers"]:
            budget = float(gamma) * float(selection["predicted_cost"])
            step_cost = int(
                protocol["formulae"][selected_formula][
                    "h4_pauli_rotations_per_pf_step"
                ]
            )
            phase_estimation_error = beta * step_cost / (selected_time * budget)
            margin = (
                target_error
                - abs(float(selected_direct["direct_shift_hartree"]))
                - phase_estimation_error
            )
            allocation_rows.append(
                {
                    "experiment_id": "B",
                    "selected_formula": selected_formula,
                    "selected_time_hartree_inverse": selected_time,
                    "predicted_cost": selection["predicted_cost"],
                    "direct_cost_at_selection": selected_direct["direct_cost"],
                    "same_formula_grid_best_cost": same_formula_best["direct_cost"],
                    "joint_grid_best_formula": reference["formula_id"],
                    "joint_grid_best_time": reference["absolute_time"],
                    "joint_grid_best_cost": reference["direct_cost"],
                    "same_formula_time_regret": selected_direct["direct_cost"] / same_formula_best["direct_cost"] - 1.0,
                    "joint_selection_regret": selected_direct["direct_cost"] / reference["direct_cost"] - 1.0,
                    "budget_multiplier": gamma,
                    "frozen_budget": budget,
                    "phase_estimation_error_hartree": phase_estimation_error,
                    "direct_shift_absolute_hartree": abs(float(selected_direct["direct_shift_hartree"])),
                    "energy_margin_hartree": margin,
                    "success": margin >= 0.0,
                    "budget_over_reference_minus_one": budget / reference["direct_cost"] - 1.0,
                }
            )
    for row in decision_grid_rows:
        resource_rows.append(
            {
                "experiment_id": "B",
                "case_id": "H4",
                "formula_id": row["formula_id"],
                "state_id": "exact_truth",
                "absolute_time": row["absolute_time"],
                "direct_shift_hartree": row["direct_shift_hartree"],
                "direct_cost": row["direct_cost"],
                "resource_unit": "Pauli_rotations",
            }
        )
    c_models = _models_lookup(model_rows)
    c_direct_lookup = _direct_lookup(direct_rows)
    for row in phase_a_observations:
        if row["experiment_id"] != "C" or int(row["sign"]) != 1:
            continue
        key = ("C", row["case_id"], "yoshida4", row["state_id"])
        model = c_models[key]
        time_value = float(row["time_hartree_inverse"])
        predicted_shift = evaluate_fit(model, time_value)
        direct = c_direct_lookup[
            ("C", row["case_id"], "yoshida4", "mechanism_fixed", 1, float(row["absolute_time"]))
        ]
        resource_rows.append(
            {
                "experiment_id": "C",
                "case_id": row["case_id"],
                "formula_id": "yoshida4",
                "state_id": row["state_id"],
                "absolute_time": row["absolute_time"],
                "predicted_signed_shift_hartree": predicted_shift,
                "direct_shift_hartree": direct["direct_shift_hartree"],
                "predicted_cost": model_cost(target_error, beta, int(c_spec["resource_step_cost"]), time_value, predicted_shift),
                "direct_cost": direct["direct_cost"],
                "resource_unit": c_spec["resource_step_cost_unit"],
            }
        )

    dominance = _dominance_rows(decomposition, target_error)
    dominant_components = {
        row["dominant_component"]
        for row in dominance
        if row["dominant_component"] != "mixed"
    }
    outcome_a = len(dominant_components) == 1 and bool(dominant_components)
    outcome_b = len(dominant_components) >= 2
    selected_nearest = []
    if selection["status"] == "selected":
        selected_nearest = sorted(
            (
                row
                for row in decomposition
                if row["experiment_id"] == "B"
                and row["formula_id"] == selection["selected_formula"]
                and row["state_id"] == "cisd"
                and int(row["sign"]) == 1
            ),
            key=lambda row: abs(
                float(row["time_hartree_inverse"])
                - float(selection["selected_time_hartree_inverse"])
            ),
        )[:1]
    material_component = bool(
        selected_nearest
        and max(
            selected_nearest[0]["E_fit_hartree"],
            selected_nearest[0]["E_state_hartree"],
            selected_nearest[0]["E_proxy_hartree"],
        )
        >= 0.05 * target_error
    )
    gamma_101 = next(
        (row for row in allocation_rows if float(row["budget_multiplier"]) == 1.01),
        None,
    )
    outcome_c = bool(
        material_component
        and gamma_101
        and gamma_101["joint_selection_regret"] <= 0.10
        and gamma_101["success"]
    )

    shutil.copyfile(protocol_path, output_dir / "protocol.json")
    shutil.copyfile(phase_a_dir / "predictions.json", output_dir / "predictions.json")
    shutil.copyfile(phase_a_dir / "prediction.sha256", output_dir / "prediction.sha256")
    atomic_json(
        output_dir / "source_manifest.json",
        {
            "protocol_sha256": protocol_hash,
            "phase_a_prediction_sha256": prediction_hash,
            "phase_a_directory": str(phase_a_dir),
            "h4_source": source_manifest,
        },
    )
    observables = [dict(row) for row in phase_a_observations] + exact_rows
    write_csv(output_dir / "observables.csv", observables)
    write_csv(output_dir / "error_decomposition.csv", decomposition)
    write_csv(output_dir / "state_diagnostics.csv", state_rows)
    write_csv(output_dir / "operator_diagnostics.csv", operator_rows)
    write_csv(output_dir / "signal_quality.csv", signal_rows)
    write_csv(output_dir / "allocation_scoring.csv", allocation_rows or [{"status": "abstained"}])
    write_csv(output_dir / "branch_audit.csv", direct_rows)
    write_csv(output_dir / "resources.csv", resource_rows)
    write_csv(output_dir / "dominance_summary.csv", dominance)
    checks = {
        "prediction_hash_unchanged": sha256_file(output_dir / "predictions.json") == prediction_hash,
        "protocol_hash_unchanged": sha256_file(output_dir / "protocol.json") == protocol_hash,
        "three_way_closure_passed": maximum_closure <= closure_gate,
        "all_branch_eigenpair_residuals_passed": max(float(row["eigenpair_residual_2_norm"]) for row in direct_rows) <= float(protocol["numerical_gates"]["direct_eigenpair_residual_2_norm"]),
        "all_unitarity_residuals_passed": max(float(row["unitarity_residual_frobenius"]) for row in direct_rows) <= float(protocol["numerical_gates"]["pf_unitarity_frobenius"]),
    }
    status = "complete_with_findings" if all(checks.values()) else "failed_numerical_validation"
    audit = {
        "status": status,
        "checks": checks,
        "protocol_sha256": protocol_hash,
        "phase_a_prediction_sha256": prediction_hash,
        "phase_a_implementation_commit": predictions["implementation_commit"],
        "phase_b_execution_commit": git_output(project_root, "rev-parse", "HEAD"),
        "counts": {
            "observable_rows": len(observables),
            "decomposition_rows": len(decomposition),
            "direct_truth_rows": len(direct_rows),
            "allocation_rows": len(allocation_rows),
            "new_direct_truth_point_count": len(direct_rows),
        },
        "extrema": {
            "maximum_three_way_closure_hartree": maximum_closure,
            "maximum_eigenpair_residual_2_norm": max(float(row["eigenpair_residual_2_norm"]) for row in direct_rows),
            "maximum_unitarity_residual_frobenius": max(float(row["unitarity_residual_frobenius"]) for row in direct_rows),
        },
        "stopping_outcomes": {
            "A_single_component_dominates": outcome_a,
            "B_dominant_component_switches": outcome_b,
            "C_material_error_but_resource_robust": outcome_c,
            "null_result": not (outcome_a or outcome_b or outcome_c),
            "dominant_components_observed": sorted(dominant_components),
        },
        "elapsed_wall_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    atomic_json(output_dir / "audit.json", audit)
    report = [
        "# First-study Phase B truth scoring",
        "",
        f"Status: **{status}**",
        "",
        f"Frozen prediction SHA-256: `{prediction_hash}`.",
        "The Phase-A selector and scorer were not changed after truth was opened.",
        "Controlled states and Experiment C remain oracle/constructive mechanism diagnostics, not molecular transfer evidence.",
        "",
        "## Stopping outcomes",
        "",
        f"- Outcome A (one component dominates): {outcome_a}",
        f"- Outcome B (dominant component switches): {outcome_b}",
        f"- Outcome C (material error but resource robust): {outcome_c}",
        f"- Null result: {not (outcome_a or outcome_b or outcome_c)}",
        "",
        f"Maximum three-way closure residual: {maximum_closure:.6e} Ha.",
    ]
    if allocation_rows:
        chosen = allocation_rows[-1]
        report.extend(
            [
                "",
                "## Frozen H4 decision",
                "",
                f"Selected PF: `{chosen['selected_formula']}` at t={chosen['selected_time_hartree_inverse']:.8g}.",
                f"Joint grid regret: {chosen['joint_selection_regret']:.6%}.",
                f"Gamma=1.01 energy margin: {chosen['energy_margin_hartree']:.6e} Ha.",
            ]
        )
    (output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    required = [
        "protocol.json", "source_manifest.json", "observables.csv",
        "error_decomposition.csv", "state_diagnostics.csv",
        "operator_diagnostics.csv", "signal_quality.csv", "predictions.json",
        "prediction.sha256", "allocation_scoring.csv", "branch_audit.csv",
        "resources.csv", "dominance_summary.csv", "audit.json", "report.md",
    ]
    manifest = {
        "status": status,
        "generated_at": datetime.now().astimezone().isoformat(),
        "protocol_sha256": protocol_hash,
        "prediction_sha256": prediction_hash,
        "phase_a_commit": predictions["implementation_commit"],
        "phase_b_commit": git_output(project_root, "rev-parse", "HEAD"),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "artifact_sha256": {name: sha256_file(output_dir / name) for name in required},
    }
    atomic_json(output_dir / "manifest.json", manifest)
    if status == "complete_with_findings":
        (output_dir / "COMPLETE").write_text(
            "Phase A prediction hash preserved; Phase B numerical gates passed.\n",
            encoding="utf-8",
        )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=Path("PF_first_study_protocol_20260925.json"))
    parser.add_argument("--phase-a", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    protocol_path = arguments.protocol if arguments.protocol.is_absolute() else project_root / arguments.protocol
    phase_a_dir = arguments.phase_a if arguments.phase_a.is_absolute() else project_root / arguments.phase_a
    output_dir = arguments.output if arguments.output.is_absolute() else project_root / arguments.output
    audit = run(project_root, protocol_path, phase_a_dir, output_dir)
    print(json.dumps(audit, indent=2))
    return 0 if audit["status"] == "complete_with_findings" else 1


if __name__ == "__main__":
    raise SystemExit(main())
