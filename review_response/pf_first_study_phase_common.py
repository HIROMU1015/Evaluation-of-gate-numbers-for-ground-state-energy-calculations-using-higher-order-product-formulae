"""Shared, preregistered helpers for first-study Phase A and Phase B."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from review_response._pf_first_study_experiment_a_support import (
    sha256_array,
    sha256_file,
)
from review_response.pf_first_study_experiment_a import echo_proxies
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.sector_pf import build_sector_pf_unitary


def canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def align_to_reference(state: np.ndarray, reference: np.ndarray) -> np.ndarray:
    result = np.asarray(state, dtype=np.complex128).copy()
    overlap = complex(np.vdot(reference, result))
    if abs(overlap) <= 1e-15:
        raise ValueError("state has zero overlap with the reference")
    result *= np.exp(-1j * np.angle(overlap))
    result /= np.linalg.norm(result)
    return result


def controlled_state_family(
    exact: np.ndarray,
    cisd: np.ndarray,
    q_values: Sequence[float],
    phase_values: Sequence[float],
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    aligned = align_to_reference(cisd, exact)
    chi_raw = aligned - exact * np.vdot(exact, aligned)
    chi = chi_raw / np.linalg.norm(chi_raw)
    pivot = int(np.argmax(np.abs(chi)))
    chi *= np.exp(-1j * np.angle(chi[pivot]))
    if chi[pivot].real < 0.0:
        chi *= -1.0
    states: dict[str, np.ndarray] = {}
    for q in q_values:
        for phase in phase_values:
            state_id = f"controlled_q{q:.3f}_phi{phase:.12f}"
            state = (
                math.sqrt(1.0 - float(q)) * exact
                + np.exp(1j * float(phase)) * math.sqrt(float(q)) * chi
            )
            states[state_id] = state / np.linalg.norm(state)
    return states, chi


def _expected_h4_array_hashes(protocol: dict[str, Any]) -> dict[str, str]:
    arrays = protocol["source_identity"]["h4_arrays"]
    states = protocol["source_identity"]["h4_states"]
    result = {
        arrays["experiment_hamiltonian_key"]: arrays[
            "experiment_hamiltonian_sha256"
        ],
        "H4_ground_energy": arrays["ground_energy_array_sha256"],
        "H4_exact_state": states["exact"]["sha256"],
        "H4_hf_state": states["rhf"]["sha256"],
        "H4_cisd_state": states["cisd"]["sha256"],
    }
    result.update(
        dict(
            zip(
                arrays["ordered_group_keys"],
                arrays["ordered_group_sha256"],
                strict=True,
            )
        )
    )
    return result


def load_h4_source(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = protocol["source_identity"]
    f01_path = project_root / source["f01_bundle"]["path"]
    state_path = project_root / source["h01_state_bundle"]["path"]
    file_hashes = {
        str(source["f01_bundle"]["path"]): sha256_file(f01_path),
        str(source["h01_state_bundle"]["path"]): sha256_file(state_path),
    }
    expected_files = {
        str(source["f01_bundle"]["path"]): source["f01_bundle"]["sha256"],
        str(source["h01_state_bundle"]["path"]): source["h01_state_bundle"][
            "sha256"
        ],
    }
    if file_hashes != expected_files:
        raise ValueError("H4 source file SHA-256 mismatch")
    f01 = np.load(f01_path)
    states_archive = np.load(state_path)
    arrays = source["h4_arrays"]
    expected = _expected_h4_array_hashes(protocol)
    observed = {
        arrays["experiment_hamiltonian_key"]: sha256_array(
            f01[arrays["experiment_hamiltonian_key"]]
        ),
        "H4_ground_energy": sha256_array(f01["H4_ground_energy"]),
        "H4_exact_state": sha256_array(states_archive["H4_exact_state"]),
        "H4_hf_state": sha256_array(states_archive["H4_hf_state"]),
        "H4_cisd_state": sha256_array(states_archive["H4_cisd_state"]),
    }
    for key in arrays["ordered_group_keys"]:
        observed[key] = sha256_array(f01[key])
    if observed != expected:
        raise ValueError("H4 source array SHA-256 mismatch")

    hamiltonian = np.asarray(
        f01[arrays["experiment_hamiltonian_key"]], dtype=np.complex128
    )
    groups = [
        np.asarray(f01[key], dtype=np.complex128)
        for key in arrays["ordered_group_keys"]
    ]
    exact = np.asarray(states_archive["H4_exact_state"], dtype=np.complex128)
    rhf = align_to_reference(states_archive["H4_hf_state"], exact)
    cisd = align_to_reference(states_archive["H4_cisd_state"], exact)
    controlled_spec = protocol["experiment_B_h4"]["controlled_state"]
    controlled, chi = controlled_state_family(
        exact,
        cisd,
        controlled_spec["q_values"],
        controlled_spec["phase_values_radians"],
    )
    formula_ids = protocol["scope"]["included_formula_ids"]
    operators = {
        formula_id: {
            order: np.asarray(
                f01[f"H4_{formula_id}_D{order}"], dtype=np.complex128
            )
            for order in (4, 6, 8)
        }
        for formula_id in formula_ids
    }
    energy = float(np.asarray(f01["H4_ground_energy"]).reshape(()))
    spectra = [np.linalg.eigh(group) for group in groups]
    group_sum_residual = float(
        np.linalg.norm(sum(groups, np.zeros_like(hamiltonian)) - hamiltonian)
    )
    exact_residual = float(np.linalg.norm(hamiltonian @ exact - energy * exact))
    if group_sum_residual > protocol["numerical_gates"]["group_sum_frobenius"]:
        raise ValueError("H4 group sum residual exceeds the frozen gate")
    if exact_residual > protocol["numerical_gates"][
        "stored_ground_energy_reproduction_hartree"
    ]:
        raise ValueError("H4 ground-state residual exceeds the frozen gate")
    system = {
        "hamiltonian": hamiltonian,
        "groups": groups,
        "spectra": spectra,
        "energy": energy,
        "states": {"exact": exact, "rhf": rhf, "cisd": cisd, **controlled},
        "controlled_state_ids": tuple(controlled),
        "chi_cisd": chi,
        "operators": operators,
    }
    manifest = {
        "source_file_sha256": file_hashes,
        "source_array_sha256": observed,
        "hamiltonian_dimension": int(hamiltonian.shape[0]),
        "group_count": len(groups),
        "group_sum_residual_frobenius": group_sum_residual,
        "exact_eigenpair_residual_2_norm": exact_residual,
        "controlled_chi_sha256": sha256_array(chi),
    }
    return system, manifest


def build_unitary(
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    sequence: Sequence[float],
    time_value: float,
) -> np.ndarray:
    return build_sector_pf_unitary(
        spectra, sequence, float(time_value), method="s2-cache"
    )


def proxy_from_unitary(
    hamiltonian: np.ndarray,
    unitary: np.ndarray,
    state: np.ndarray,
    time_value: float,
    previous_unwrapped_phase: float = 0.0,
) -> tuple[dict[str, float | int], float]:
    return echo_proxies(
        hamiltonian, unitary, state, time_value, previous_unwrapped_phase
    )


def proxy_noise_hartree(
    unitarity_residual: float,
    repeatability_error_hartree: float,
    hamiltonian_spectral_norm: float,
    time_value: float,
) -> float:
    return float(
        max(
            float(unitarity_residual) / abs(float(time_value)),
            float(repeatability_error_hartree),
            50.0
            * np.finfo(float).eps
            * max(float(hamiltonian_spectral_norm), 1.0 / abs(float(time_value))),
        )
    )


def quality_class(signal: float, noise: float) -> tuple[float, str]:
    rho = float(abs(signal) / max(float(noise), 1e-300))
    if rho >= 100.0:
        return rho, "resolved"
    if rho >= 10.0:
        return rho, "marginal"
    return rho, "unresolved"


def scaled_power_fit(
    times: Sequence[float], values: Sequence[float], powers: Sequence[int]
) -> dict[str, Any]:
    x = np.asarray(times, dtype=float)
    y = np.asarray(values, dtype=float)
    design = np.column_stack([x ** int(power) for power in powers])
    norms = np.linalg.norm(design, axis=0)
    scaled = design / norms[None, :]
    scaled_coefficients = np.linalg.lstsq(scaled, y, rcond=None)[0]
    coefficients = scaled_coefficients / norms
    prediction = design @ coefficients
    return {
        "powers": [int(power) for power in powers],
        "coefficients": [float(value) for value in coefficients],
        "scaled_design_condition_number": float(np.linalg.cond(scaled)),
        "maximum_absolute_residual_hartree": float(
            np.max(np.abs(prediction - y))
        ),
    }


def evaluate_fit(model: dict[str, Any], time_value: float) -> float:
    return float(
        sum(
            float(coefficient) * float(time_value) ** int(power)
            for power, coefficient in zip(
                model["powers"], model["coefficients"], strict=True
            )
        )
    )


def leading_fit(
    times: Sequence[float],
    signed_values: Sequence[float],
    specification: dict[str, Any],
    formal_order: int,
) -> dict[str, Any]:
    windows = rolling_loglog_fits(
        np.asarray(times, dtype=float),
        np.abs(np.asarray(signed_values, dtype=float)),
        formal_order=int(formal_order),
        noise_floor=float(specification["noise_floor_hartree"]),
        window_size=int(specification["rolling_window_points"]),
    )
    eligible = [
        window
        for window in windows
        if float(window["order_deviation"])
        <= float(specification["formal_order_tolerance"])
        and float(window["r2"]) >= float(specification["minimum_r_squared"])
    ]
    selected = min(
        eligible, key=lambda window: int(window["start_index"]), default=None
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "formal_order": int(formal_order),
    }


def model_cost(
    target_error: float,
    beta: float,
    step_cost: int,
    time_value: float,
    signed_shift: float,
) -> float | None:
    remaining = float(target_error) - abs(float(signed_shift))
    if remaining <= 0.0 or time_value <= 0.0:
        return None
    return float(beta * int(step_cost) / (float(time_value) * remaining))


def state_diagnostics(
    hamiltonian: np.ndarray,
    state: np.ndarray,
    exact: np.ndarray,
    energy: float,
) -> dict[str, float]:
    expectation = complex(np.vdot(state, hamiltonian @ state))
    centered = hamiltonian @ state - expectation * state
    residual = hamiltonian @ state - float(energy) * state
    return {
        "energy_expectation_hartree": float(expectation.real),
        "energy_error_hartree": float(expectation.real - energy),
        "variance_hartree_squared": float(np.vdot(centered, centered).real),
        "hamiltonian_residual_2_norm": float(np.linalg.norm(residual)),
        "exact_overlap_probability": float(abs(np.vdot(exact, state)) ** 2),
    }


def operator_diagnostics(
    operator: np.ndarray, state: np.ndarray, exact: np.ndarray
) -> dict[str, float]:
    expectation = complex(np.vdot(state, operator @ state))
    exact_expectation = complex(np.vdot(exact, operator @ exact))
    return {
        "state_expectation_real": float(expectation.real),
        "state_expectation_imaginary": float(expectation.imag),
        "exact_expectation_real": float(exact_expectation.real),
        "state_minus_exact_expectation_real": float(
            expectation.real - exact_expectation.real
        ),
        "operator_frobenius_norm": float(np.linalg.norm(operator)),
        "operator_action_2_norm": float(np.linalg.norm(operator @ state)),
    }
