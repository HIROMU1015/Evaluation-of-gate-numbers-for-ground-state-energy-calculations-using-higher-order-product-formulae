"""Freeze proxy-only first-study predictions before opening direct truth."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
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
from review_response.pf_first_study_phase_common import (
    build_unitary,
    controlled_state_family,
    evaluate_fit,
    leading_fit,
    load_h4_source,
    model_cost,
    proxy_from_unitary,
    proxy_noise_hartree,
    quality_class,
    scaled_power_fit,
)


DEFAULT_OUTPUT = Path("artifacts/pf_first_study_phase_a_20260925")


def _proxy_rows_for_signed_times(
    *,
    experiment_id: str,
    case_id: str,
    hamiltonian: np.ndarray,
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    sequence: Sequence[float],
    formula_id: str,
    states: dict[str, np.ndarray],
    magnitudes: Sequence[float],
    signs: Sequence[int],
) -> list[dict[str, Any]]:
    h_norm = float(np.linalg.norm(hamiltonian, 2))
    rows: list[dict[str, Any]] = []
    for sign in signs:
        previous_phase = {state_id: 0.0 for state_id in states}
        for magnitude in magnitudes:
            signed_time = float(sign) * float(magnitude)
            unitary = build_unitary(spectra, sequence, signed_time)
            repeated = build_unitary(spectra, sequence, signed_time)
            unitarity = float(
                np.linalg.norm(
                    unitary.conj().T @ unitary - np.eye(unitary.shape[0])
                )
            )
            unitary_repeat = float(np.linalg.norm(repeated - unitary))
            for state_id, state in states.items():
                proxy, previous_phase[state_id] = proxy_from_unitary(
                    hamiltonian,
                    unitary,
                    state,
                    signed_time,
                    previous_phase[state_id],
                )
                repeat_proxy, _ = proxy_from_unitary(
                    hamiltonian,
                    repeated,
                    state,
                    signed_time,
                    0.0,
                )
                repeatability = abs(
                    float(proxy["proxy_imag_hartree"])
                    - float(repeat_proxy["proxy_imag_hartree"])
                )
                noise = proxy_noise_hartree(
                    unitarity, repeatability, h_norm, signed_time
                )
                rho, quality = quality_class(
                    float(proxy["proxy_imag_hartree"]), noise
                )
                rows.append(
                    {
                        "experiment_id": experiment_id,
                        "case_id": case_id,
                        "formula_id": formula_id,
                        "state_id": state_id,
                        "sign": int(sign),
                        "absolute_time": float(magnitude),
                        "time_hartree_inverse": signed_time,
                        **proxy,
                        "unitarity_residual_frobenius": unitarity,
                        "unitary_cold_repeatability_frobenius": unitary_repeat,
                        "proxy_repeatability_error_hartree": repeatability,
                        "proxy_noise_hartree": noise,
                        "signal_to_noise_rho": rho,
                        "quality_class": quality,
                    }
                )
    return rows


def _paired_values(
    rows: Sequence[dict[str, Any]], state_id: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    selected = [row for row in rows if row["state_id"] == state_id]
    magnitudes = sorted({float(row["absolute_time"]) for row in selected})
    lookup = {
        (int(row["sign"]), float(row["absolute_time"])): float(
            row["proxy_imag_hartree"]
        )
        for row in selected
    }
    positive = np.asarray([lookup[(1, value)] for value in magnitudes])
    negative = np.asarray([lookup[(-1, value)] for value in magnitudes])
    return np.asarray(magnitudes), positive, negative


def _mechanism_models(
    rows: Sequence[dict[str, Any]],
    state_ids: Sequence[str],
    maximum_condition: float,
) -> list[dict[str, Any]]:
    result = []
    for state_id in state_ids:
        times, positive, negative = _paired_values(rows, state_id)
        even = (positive + negative) / 2.0
        odd = (positive - negative) / 2.0
        quality_rows = [
            row
            for row in rows
            if row["state_id"] == state_id and int(row["sign"]) == 1
        ]
        quality_rows.sort(key=lambda row: float(row["absolute_time"]))
        quality_gate = (
            all(row["quality_class"] in {"marginal", "resolved"} for row in quality_rows)
            and sum(row["quality_class"] == "resolved" for row in quality_rows) >= 3
        )
        for model_id, values, powers, selection_active in (
            ("raw_positive_even_two_term", positive, (4, 6), True),
            ("evenized_two_term", even, (4, 6), False),
            ("odd_diagnostic", odd, (5, 7), False),
        ):
            model = scaled_power_fit(times, values, powers)
            stable = (
                model["scaled_design_condition_number"] <= maximum_condition
            )
            result.append(
                {
                    "state_id": state_id,
                    "model_id": model_id,
                    "selection_active": selection_active,
                    "signal_quality_gate_passed": quality_gate,
                    "stable": stable,
                    "status": (
                        "fit_ok"
                        if quality_gate and stable
                        else "not_identifiable"
                    ),
                    **model,
                }
            )
    return result


def _single_positive_proxy(
    hamiltonian: np.ndarray,
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    sequence: Sequence[float],
    state: np.ndarray,
    time_value: float,
) -> dict[str, Any]:
    unitary = build_unitary(spectra, sequence, time_value)
    repeated = build_unitary(spectra, sequence, time_value)
    proxy, _ = proxy_from_unitary(
        hamiltonian, unitary, state, time_value, 0.0
    )
    repeated_proxy, _ = proxy_from_unitary(
        hamiltonian, repeated, state, time_value, 0.0
    )
    unitarity = float(
        np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]))
    )
    repeatability = abs(
        float(proxy["proxy_imag_hartree"])
        - float(repeated_proxy["proxy_imag_hartree"])
    )
    noise = proxy_noise_hartree(
        unitarity,
        repeatability,
        float(np.linalg.norm(hamiltonian, 2)),
        time_value,
    )
    rho, quality = quality_class(float(proxy["proxy_imag_hartree"]), noise)
    return {
        "time_hartree_inverse": float(time_value),
        **proxy,
        "unitarity_residual_frobenius": unitarity,
        "proxy_repeatability_error_hartree": repeatability,
        "proxy_noise_hartree": noise,
        "signal_to_noise_rho": rho,
        "quality_class": quality,
    }


def _decision_prediction(
    *,
    protocol: dict[str, Any],
    system: dict[str, Any],
    formula: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    decision = protocol["experiment_B_h4"]["decision_track"]
    leading_spec = decision["short_time_leading_fit"]
    times = np.geomspace(
        float(leading_spec["minimum_hartree_inverse"]),
        float(leading_spec["maximum_hartree_inverse"]),
        int(leading_spec["count"]),
    )
    cisd = system["states"]["cisd"]
    sequence = formula["sequence"]
    point_rows = []
    for time_value in times:
        point = _single_positive_proxy(
            system["hamiltonian"],
            system["spectra"],
            sequence,
            cisd,
            float(time_value),
        )
        point_rows.append(
            {
                "formula_id": formula["formula_id"],
                "point_role": "leading_grid",
                "relative_to_proxy_t_ana": None,
                **point,
            }
        )
    lead = leading_fit(
        times,
        [row["proxy_imag_hartree"] for row in point_rows],
        leading_spec,
        formula["formal_order"],
    )
    prediction: dict[str, Any] = {
        "formula_id": formula["formula_id"],
        "formal_order": formula["formal_order"],
        "leading_fit": lead,
        "status": "not_identifiable",
        "eligible": False,
        "rejection_reason": "short_time_leading_fit_failed",
    }
    if not lead["qualified"]:
        return prediction, point_rows
    alpha = float(lead["selected_window"]["fixed_order_alpha"])
    target_error = float(protocol["constants"]["target_error_hartree"])
    proxy_t_ana = float((target_error / (5.0 * abs(alpha))) ** 0.25)
    training_relative = decision["training_relative_to_proxy_t_ana"]
    training_rows = []
    for relative in training_relative:
        point = _single_positive_proxy(
            system["hamiltonian"],
            system["spectra"],
            sequence,
            cisd,
            float(relative) * proxy_t_ana,
        )
        row = {
            "formula_id": formula["formula_id"],
            "point_role": "primary_training",
            "relative_to_proxy_t_ana": float(relative),
            **point,
        }
        point_rows.append(row)
        training_rows.append(row)
    quality_gate = (
        all(
            row["quality_class"] in {"marginal", "resolved"}
            for row in training_rows
        )
        and sum(row["quality_class"] == "resolved" for row in training_rows)
        >= 3
    )
    model = scaled_power_fit(
        [row["time_hartree_inverse"] for row in training_rows],
        [row["proxy_imag_hartree"] for row in training_rows],
        decision["selection_model"]["powers"],
    )
    reduced_count = len(decision["reduced_ablation_relative_to_proxy_t_ana"])
    reduced_model = scaled_power_fit(
        [row["time_hartree_inverse"] for row in training_rows[:reduced_count]],
        [row["proxy_imag_hartree"] for row in training_rows[:reduced_count]],
        decision["selection_model"]["powers"],
    )
    stable = (
        model["scaled_design_condition_number"]
        <= protocol["experiment_B_h4"]["fixed_time_mechanism_track"][
            "maximum_scaled_design_condition_number"
        ]
    )
    selection_grid = np.geomspace(
        float(decision["selection_grid"]["minimum_relative_to_proxy_t_ana"]),
        float(decision["selection_grid"]["maximum_relative_to_proxy_t_ana"]),
        int(decision["selection_grid"]["count"]),
    ) * proxy_t_ana
    step_cost = int(
        protocol["formulae"][formula["formula_id"]][
            "h4_pauli_rotations_per_pf_step"
        ]
    )
    candidates = []
    for time_value in selection_grid:
        shift = evaluate_fit(model, float(time_value))
        cost = model_cost(
            target_error,
            float(protocol["constants"]["qpe_beta"]),
            step_cost,
            float(time_value),
            shift,
        )
        if cost is not None:
            candidates.append((cost, float(time_value), shift))
    if quality_gate and stable and candidates:
        cost, selected_time, shift = min(candidates)
        prediction.update(
            {
                "status": "eligible",
                "eligible": True,
                "rejection_reason": None,
                "selected_time_hartree_inverse": selected_time,
                "predicted_signed_shift_hartree": shift,
                "predicted_cost": cost,
            }
        )
    else:
        reasons = []
        if not quality_gate:
            reasons.append("signal_quality_gate_failed")
        if not stable:
            reasons.append("design_condition_failed")
        if not candidates:
            reasons.append("no_feasible_grid_point")
        prediction["rejection_reason"] = ";".join(reasons)
    prediction.update(
        {
            "proxy_leading_alpha": alpha,
            "proxy_t_ana_hartree_inverse": proxy_t_ana,
            "primary_model": model,
            "reduced_three_point_ablation_model": reduced_model,
            "primary_signal_quality_gate_passed": quality_gate,
            "primary_resolved_point_count": sum(
                row["quality_class"] == "resolved" for row in training_rows
            ),
            "selection_grid_hartree_inverse": [
                float(value) for value in selection_grid
            ],
            "step_cost_pauli_rotations": step_cost,
        }
    )
    return prediction, point_rows


def _experiment_c_inputs(protocol: dict[str, Any]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    pauli_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    pauli_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    hamiltonian = pauli_x + pauli_z
    energies, vectors = np.linalg.eigh(hamiltonian)
    exact = vectors[:, 0]
    excited = vectors[:, 1]
    pivot = int(np.argmax(np.abs(excited)))
    excited *= np.exp(-1j * np.angle(excited[pivot]))
    controlled, _ = controlled_state_family(
        exact,
        exact * math.sqrt(0.99) + excited * math.sqrt(0.01),
        protocol["experiment_C_fixed_h_two_level"]["q_values"],
        protocol["experiment_C_fixed_h_two_level"]["phase_values_radians"],
    )
    return hamiltonian, controlled


def run(project_root: Path, protocol_path: Path, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {output_dir}")
    output_dir.mkdir(parents=True)
    protocol, protocol_hash = load_protocol(protocol_path)
    system, source_manifest = load_h4_source(project_root, protocol)
    formulas = formula_registry(protocol)
    mechanism = protocol["experiment_B_h4"]["fixed_time_mechanism_track"]
    approximate_state_ids = [
        "rhf",
        "cisd",
        *system["controlled_state_ids"],
    ]
    approximate_states = {
        state_id: system["states"][state_id] for state_id in approximate_state_ids
    }
    mechanism_rows: list[dict[str, Any]] = []
    mechanism_models: list[dict[str, Any]] = []
    decision_points: list[dict[str, Any]] = []
    formula_predictions = []
    magnitudes = sorted(
        {
            *map(float, mechanism["training_time_magnitudes_hartree_inverse"]),
            *map(float, mechanism["evaluation_time_magnitudes_hartree_inverse"]),
        }
    )
    for formula in formulas:
        rows = _proxy_rows_for_signed_times(
            experiment_id="B",
            case_id="H4",
            hamiltonian=system["hamiltonian"],
            spectra=system["spectra"],
            sequence=formula["sequence"],
            formula_id=formula["formula_id"],
            states=approximate_states,
            magnitudes=magnitudes,
            signs=mechanism["signs"],
        )
        mechanism_rows.extend(rows)
        models = _mechanism_models(
            rows,
            approximate_state_ids,
            float(mechanism["maximum_scaled_design_condition_number"]),
        )
        for model in models:
            mechanism_models.append(
                {"experiment_id": "B", "case_id": "H4", "formula_id": formula["formula_id"], **model}
            )
        prediction, points = _decision_prediction(
            protocol=protocol, system=system, formula=formula
        )
        formula_predictions.append(prediction)
        decision_points.extend(points)

    eligible = [row for row in formula_predictions if row["eligible"]]
    selection = (
        {
            "status": "selected",
            "selected_formula": min(eligible, key=lambda row: row["predicted_cost"])["formula_id"],
            "selected_time_hartree_inverse": min(eligible, key=lambda row: row["predicted_cost"])["selected_time_hartree_inverse"],
            "predicted_signed_shift_hartree": min(eligible, key=lambda row: row["predicted_cost"])["predicted_signed_shift_hartree"],
            "predicted_cost": min(eligible, key=lambda row: row["predicted_cost"])["predicted_cost"],
        }
        if eligible
        else {"status": "abstained", "reason": "no_valid_feasible_formula"}
    )

    c_spec = protocol["experiment_C_fixed_h_two_level"]
    c_hamiltonian, c_states = _experiment_c_inputs(protocol)
    c_rows: list[dict[str, Any]] = []
    c_models: list[dict[str, Any]] = []
    yoshida = next(row for row in formulas if row["formula_id"] == "yoshida4")
    pauli_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    pauli_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    for lambda_value in c_spec["lambda_values"]:
        groups = [
            pauli_x + float(lambda_value) * pauli_z,
            (1.0 - float(lambda_value)) * pauli_z,
        ]
        rows = _proxy_rows_for_signed_times(
            experiment_id="C",
            case_id=f"lambda_{float(lambda_value):.16g}",
            hamiltonian=c_hamiltonian,
            spectra=[np.linalg.eigh(group) for group in groups],
            sequence=yoshida["sequence"],
            formula_id="yoshida4",
            states=c_states,
            magnitudes=c_spec["absolute_time_magnitudes_hartree_inverse"],
            signs=c_spec["signs"],
        )
        c_rows.extend(rows)
        models = _mechanism_models(
            rows,
            list(c_states),
            float(mechanism["maximum_scaled_design_condition_number"]),
        )
        for model in models:
            c_models.append(
                {
                    "experiment_id": "C",
                    "case_id": f"lambda_{float(lambda_value):.16g}",
                    "lambda": float(lambda_value),
                    "formula_id": "yoshida4",
                    **model,
                }
            )

    write_csv(output_dir / "phase_a_proxy_observables.csv", mechanism_rows + c_rows)
    write_csv(output_dir / "phase_a_proxy_models.csv", mechanism_models + c_models)
    write_csv(output_dir / "decision_proxy_points.csv", decision_points)
    copied_protocol = output_dir / "protocol.json"
    shutil.copyfile(protocol_path, copied_protocol)
    source_payload = {
        "protocol_sha256": protocol_hash,
        "source": source_manifest,
        "oracle_barrier": {
            "direct_pf_shift_used": False,
            "direct_optimum_used": False,
            "exact_ground_proxy_used": False,
            "past_h4_pass_fail_used": False,
            "controlled_states_use_exact_information": True,
            "controlled_states_role": "oracle_mechanism_diagnostic_only",
        },
    }
    atomic_json(output_dir / "source_manifest.json", source_payload)
    predictions = {
        "schema": "pf_first_study_phase_a_predictions_v1",
        "protocol_sha256": protocol_hash,
        "implementation_commit": git_output(project_root, "rev-parse", "HEAD"),
        "created_at": datetime.now().astimezone().isoformat(),
        "truth_opened": False,
        "experiment_B": {
            "formula_predictions": formula_predictions,
            "selection": selection,
            "truth_reference_grids_frozen": {
                row["formula_id"]: row.get("selection_grid_hartree_inverse", [])
                for row in formula_predictions
            },
        },
        "experiment_C": {
            "selection_active": False,
            "fixed_point_resource_scoring_only": True,
            "lambda_values": c_spec["lambda_values"],
        },
        "phase_a_files": {
            "phase_a_proxy_observables.csv": sha256_file(output_dir / "phase_a_proxy_observables.csv"),
            "phase_a_proxy_models.csv": sha256_file(output_dir / "phase_a_proxy_models.csv"),
            "decision_proxy_points.csv": sha256_file(output_dir / "decision_proxy_points.csv"),
            "source_manifest.json": sha256_file(output_dir / "source_manifest.json"),
            "protocol.json": sha256_file(copied_protocol),
        },
    }
    atomic_json(output_dir / "predictions.json", predictions)
    prediction_hash = sha256_file(output_dir / "predictions.json")
    (output_dir / "prediction.sha256").write_text(
        f"{prediction_hash}  predictions.json\n", encoding="utf-8"
    )
    audit = {
        "status": "selection_frozen",
        "protocol_sha256": protocol_hash,
        "prediction_sha256": prediction_hash,
        "selection": selection,
        "formula_eligible_count": len(eligible),
        "oracle_barrier_passed": True,
        "exact_ground_proxy_row_count": 0,
        "direct_truth_point_count": 0,
        "phase_a_proxy_observable_count": len(mechanism_rows) + len(c_rows),
        "decision_proxy_point_count": len(decision_points),
        "elapsed_wall_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    atomic_json(output_dir / "audit.json", audit)
    (output_dir / "SELECTION_FROZEN").write_text(
        f"prediction_sha256={prediction_hash}\n", encoding="utf-8"
    )
    report = [
        "# First-study Phase A selector freeze",
        "",
        "Status: **selection_frozen**",
        "",
        "Direct PF eigenvalue shifts, direct optima, and exact-ground proxies were not opened.",
        "Controlled states are exact-informed oracle mechanism diagnostics and are not practical-selector evidence.",
        "",
        f"Selected result: `{json.dumps(selection, sort_keys=True)}`",
        "",
        f"Eligible PFs: {len(eligible)}/4.",
        f"Prediction SHA-256: `{prediction_hash}`.",
    ]
    (output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_files = [
        "protocol.json",
        "source_manifest.json",
        "phase_a_proxy_observables.csv",
        "phase_a_proxy_models.csv",
        "decision_proxy_points.csv",
        "predictions.json",
        "prediction.sha256",
        "audit.json",
        "SELECTION_FROZEN",
        "report.md",
    ]
    manifest = {
        "status": "selection_frozen",
        "generated_at": datetime.now().astimezone().isoformat(),
        "implementation_commit": git_output(project_root, "rev-parse", "HEAD"),
        "protocol_sha256": protocol_hash,
        "prediction_sha256": prediction_hash,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "artifact_sha256": {
            name: sha256_file(output_dir / name) for name in manifest_files
        },
    }
    atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--protocol", type=Path, default=Path("PF_first_study_protocol_20260925.json")
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    protocol_path = arguments.protocol
    if not protocol_path.is_absolute():
        protocol_path = project_root / protocol_path
    output_dir = arguments.output
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    audit = run(project_root, protocol_path, output_dir)
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
