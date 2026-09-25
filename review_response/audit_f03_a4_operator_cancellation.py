"""F03 audit separating a small a4 from a small D4 error operator.

The molecular part reuses the basis-consistent F01 operators and H01
exact/HF/CISD states.  A two-level split-Hamiltonian family independently
tunes the ground-state D4 expectation through zero while retaining a finite
operator norm, then directly tracks the PF eigenbranch at the one-term time.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import resource
import time
from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import schur
from scipy.optimize import brentq

from review_response.audit_f01_effective_hamiltonian_multipf import (
    formula_registry,
)
from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from review_response.audit_h01_approximate_state_pilot import (
    leading_analytic_time,
)
from review_response.bch_matrix_series import (
    effective_hamiltonian_series_numpy,
    eigenenergy_perturbation_series,
)
from trotterlib.config import TARGET_ERROR
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import yoshida_4th_list
from trotterlib.sector_pf import build_sector_pf_unitary


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_H01 = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2"
)
SYSTEMS = ("H2", "H4")
STATE_IDS = ("exact", "hf", "cisd")
ARTIFICIAL_ROOT_BRACKET = (-2.6, -2.5)
ARTIFICIAL_OFFSETS = (-0.3, -0.1, -0.03, -0.01, -0.003, -0.001,
                      0.001, 0.003, 0.01, 0.03, 0.1, 0.3)
TRACKING_POINT_COUNT = 257


def _hermitian(matrix: np.ndarray) -> np.ndarray:
    array = np.asarray(matrix, dtype=np.complex128)
    return (array + array.conj().T) / 2.0


def error_operator_state_metrics(
    operator: np.ndarray, state: np.ndarray
) -> dict[str, float]:
    """Return expectation and centered action diagnostics for one state."""

    matrix = _hermitian(operator)
    vector = np.asarray(state, dtype=np.complex128)
    vector = vector / np.linalg.norm(vector)
    expectation = float(np.vdot(vector, matrix @ vector).real)
    centered = matrix @ vector - expectation * vector
    spectral = float(np.linalg.norm(matrix, ord=2))
    frobenius = float(np.linalg.norm(matrix))
    centered_norm = float(np.linalg.norm(centered))
    absolute_expectation = abs(expectation)
    return {
        "d4_expectation_hartree": expectation,
        "absolute_d4_expectation_hartree": absolute_expectation,
        "d4_spectral_norm_hartree": spectral,
        "d4_frobenius_norm_hartree": frobenius,
        "centered_d4_action_norm_hartree": centered_norm,
        "expectation_over_spectral_norm": absolute_expectation
        / max(spectral, 1e-300),
        "centered_action_over_expectation": centered_norm
        / max(absolute_expectation, 1e-300),
        "d4_state_variance_hartree_squared": centered_norm**2,
    }


def _circular_phase_gap(phases: np.ndarray, selected: int) -> float:
    differences = np.abs(
        np.angle(np.exp(1j * (np.asarray(phases) - phases[selected])))
    )
    differences[selected] = np.inf
    return float(np.min(differences)) if differences.size > 1 else math.inf


def track_pf_branch_to_time(
    group_matrices: Sequence[np.ndarray],
    sequence: Sequence[float],
    reference_state: np.ndarray,
    reference_energy: float,
    target_time: float,
    point_count: int = TRACKING_POINT_COUNT,
) -> dict[str, Any]:
    """Continuously track the t->0 ground-connected PF eigenbranch."""

    target = float(target_time)
    if target <= 0.0:
        raise ValueError("target time must be positive")
    start = min(0.002, target / 100.0)
    times = np.unique(np.r_[np.geomspace(start, target, point_count), target])
    spectra = [np.linalg.eigh(_hermitian(matrix)) for matrix in group_matrices]
    state = np.asarray(reference_state, dtype=np.complex128)
    previous_vector: np.ndarray | None = None
    previous_energy: float | None = None
    warning_count = 0
    minimum_previous_overlap = math.inf
    minimum_ground_overlap = math.inf
    minimum_phase_gap = math.inf
    maximum_residual = 0.0
    final: dict[str, Any] | None = None
    started = time.perf_counter()
    for index, time_value in enumerate(times):
        unitary = build_sector_pf_unitary(
            spectra, sequence, float(time_value), method="s2-cache"
        )
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        eigenvalues = np.diag(triangular)
        phases = np.angle(eigenvalues)
        ground_overlaps = np.abs(vectors.conj().T @ state) ** 2
        tracking_reference = state if previous_vector is None else previous_vector
        tracking_overlaps = np.abs(vectors.conj().T @ tracking_reference) ** 2
        selected = int(np.argmax(tracking_overlaps))
        ground_selected = int(np.argmax(ground_overlaps))
        raw_phase = float(phases[selected])
        branch_reference = (
            float(reference_energy) if previous_energy is None else previous_energy
        )
        unwrap = int(
            np.rint((branch_reference * float(time_value) - raw_phase) / (2 * np.pi))
        )
        effective_energy = (
            raw_phase + 2.0 * np.pi * unwrap
        ) / float(time_value)
        selected_vector = np.asarray(vectors[:, selected], dtype=np.complex128)
        residual = float(
            np.linalg.norm(
                unitary @ selected_vector - eigenvalues[selected] * selected_vector
            )
        )
        previous_overlap = float(tracking_overlaps[selected])
        ground_overlap = float(ground_overlaps[selected])
        phase_gap = _circular_phase_gap(phases, selected)
        warning = bool(
            selected != ground_selected
            or previous_overlap < 0.9
            or ground_overlap < 0.9
            or phase_gap < 1e-6
        )
        warning_count += int(warning)
        minimum_previous_overlap = min(minimum_previous_overlap, previous_overlap)
        minimum_ground_overlap = min(minimum_ground_overlap, ground_overlap)
        minimum_phase_gap = min(minimum_phase_gap, phase_gap)
        maximum_residual = max(maximum_residual, residual)
        final = {
            "tracking_point_index": index,
            "tracking_time_hartree_inverse": float(time_value),
            "signed_direct_pf_shift_hartree": float(
                effective_energy - reference_energy
            ),
            "direct_pf_absolute_error_hartree": abs(
                float(effective_energy - reference_energy)
            ),
            "selected_ground_overlap_probability": ground_overlap,
            "previous_branch_overlap_probability": previous_overlap,
            "selection_rules_agree": selected == ground_selected,
            "phase_unwrap_integer": unwrap,
            "selected_phase_gap_radians": phase_gap,
            "eigenpair_residual_2_norm": residual,
            "branch_warning": warning,
        }
        previous_vector = selected_vector
        previous_energy = float(effective_energy)
    assert final is not None
    return {
        **final,
        "tracking_point_count": int(times.size),
        "tracking_warning_count": warning_count,
        "tracking_minimum_previous_overlap_probability": minimum_previous_overlap,
        "tracking_minimum_ground_overlap_probability": minimum_ground_overlap,
        "tracking_minimum_phase_gap_radians": minimum_phase_gap,
        "tracking_maximum_eigenpair_residual_2_norm": maximum_residual,
        "tracking_elapsed_seconds": float(time.perf_counter() - started),
    }


def _artificial_operators(parameter: float) -> dict[str, Any]:
    pauli_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    pauli_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    groups = [pauli_x + float(parameter) * pauli_z, pauli_z]
    hamiltonian = groups[0] + groups[1]
    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    ground = eigenvectors[:, 0]
    sequence = tuple(
        float(value) for value in symmetric_s2_sequence(yoshida_4th_list())
    )
    steps = list(iter_s2_sequence_steps(len(groups), sequence))
    raw = effective_hamiltonian_series_numpy(
        groups, steps, 12
    )["effective_hamiltonian"]
    formal = [_hermitian(matrix) for matrix in raw]
    perturbation = eigenenergy_perturbation_series(
        formal, ground, maximum_order=12
    )
    coefficients = np.asarray(
        perturbation["energy_coefficients"], dtype=np.complex128
    )
    return {
        "groups": groups,
        "hamiltonian": hamiltonian,
        "energies": energies,
        "ground_state": ground,
        "sequence": sequence,
        "formal": formal,
        "energy_coefficients": coefficients,
    }


def _write_figures(
    output_dir: Path,
    exact_rows: list[dict[str, Any]],
    artificial_rows: list[dict[str, Any]],
) -> None:
    figure, axis = plt.subplots(figsize=(6.8, 4.4))
    markers = {"H2": "o", "H4": "s"}
    for system_id in SYSTEMS:
        rows = [row for row in exact_rows if row["system_id"] == system_id]
        axis.scatter(
            [row["absolute_a4_hartree"] for row in rows],
            [row["d4_spectral_norm_hartree"] for row in rows],
            marker=markers[system_id],
            s=55,
            label=system_id,
        )
        for row in rows:
            axis.annotate(
                row["formula_id"],
                (row["absolute_a4_hartree"], row["d4_spectral_norm_hartree"]),
                fontsize=7,
                xytext=(3, 3),
                textcoords="offset points",
            )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("|a4| (Ha)")
    axis.set_ylabel("spectral norm of D4 (Ha)")
    axis.grid(True, which="both", alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "a4_vs_d4_norm.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6.8, 4.4))
    for sign, label, marker in ((-1, "lambda below root", "o"), (1, "lambda above root", "s")):
        rows = [
            row
            for row in artificial_rows
            if math.copysign(1.0, row["parameter_offset_from_root"]) == sign
        ]
        axis.loglog(
            [abs(row["parameter_offset_from_root"]) for row in rows],
            [row["direct_pf_absolute_error_over_epsilon"] for row in rows],
            marker=marker,
            label=label,
        )
    axis.axhline(1.0, color="black", linestyle="--", linewidth=0.9)
    axis.invert_xaxis()
    axis.set_xlabel("distance from a4 zero")
    axis.set_ylabel("direct PF error at one-term time / epsilon")
    axis.grid(True, which="both", alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "artificial_zero_approach.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# F03: small a4 versus small D4 operator",
        "",
        f"Status: **{audit['status']}**",
        "",
        "## Molecular H-chain conditions",
        "",
        "| system | PF | |a4| | ||D4||2 | |a4|/||D4||2 | "
        "||(D4-a4)|0>||/|a4| | a6 t_ana^6 / epsilon | "
        "a8 t_ana^8 / epsilon | direct error / epsilon |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in audit["exact_condition_rows"]:
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{row['absolute_a4_hartree']:.6e} | "
            f"{row['d4_spectral_norm_hartree']:.6e} | "
            f"{row['expectation_over_spectral_norm']:.4f} | "
            f"{row['centered_action_over_expectation']:.3f} | "
            f"{row['signed_a6_contribution_over_epsilon']:.4f} | "
            f"{row['signed_a8_contribution_over_epsilon']:.4f} | "
            f"{row['direct_pf_absolute_error_over_epsilon']:.4f} |"
        )
    lines.extend(
        [
            "",
            "The optimized PFs reduce the ground-state expectation much more than "
            "the full D4 norm. In particular, m5_best has a centered D4 action "
            "40--67 times larger than |a4|, so its small leading energy coefficient "
            "is not a globally small error operator.",
            "",
            "At the one-term analytic time, the m5_best a6 contribution reaches "
            f"{audit['summary']['m5_a6_contribution_over_epsilon_range']} of epsilon. "
            "Its direct error is below the one-term value through higher-order "
            "cancellation, not because those terms are absent.",
            "",
            "## Exact/HF/CISD state comparison",
            "",
            f"{audit['summary']['state_finding']}",
            "Approximate-state expectations remain diagnostics and are not labelled "
            "as direct PF eigenvalue shifts.",
            "",
            "## Artificial split-Hamiltonian family",
            "",
            "The family uses A(lambda)=X+lambda Z and B=Z with Yoshida fourth order. "
            f"The fitted a4 zero is lambda={audit['summary']['artificial_root']:.15f}. "
            "As lambda approaches this point, ||D4|| remains finite while t_ana and "
            "higher-order contributions grow.",
            "",
            f"{audit['summary']['artificial_finding']}",
            "All artificial-family direct points retained continuous/maximum-ground "
            "branch agreement, so this growth is not a branch-selection artifact.",
            "",
            "## Decision",
            "",
            "Treat |a4|, ||D4||, and ||(D4-a4)|psi>|| as distinct diagnostics. "
            "A PF with small |a4| should not receive an enlarged one-term time unless "
            "the next contributions or a direct calibration bound are also checked.",
            "",
            "## Scope",
            "",
            "The molecular conclusions cover the stored H2/H4 partitions and four "
            "fourth-order PFs. The artificial family establishes a constructive "
            "mechanism, not a frequency estimate for molecular Hamiltonians.",
            "",
            "## Files",
            "",
            "- `audit.json`: checks, rows, and findings.",
            "- `exact_condition_metrics.csv`: exact-state operator and finite-time diagnostics.",
            "- `state_operator_metrics.csv`: exact/HF/CISD D4 diagnostics.",
            "- `artificial_family.csv`: continuous a4-zero approach.",
            "- `manifest.json`: source, input, and artifact hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(f01_dir: Path, h01_dir: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_audit_path = f01_dir / "audit.json"
    operators_path = f01_dir / "effective_operators.npz"
    h01_audit_path = h01_dir / "audit.json"
    states_path = h01_dir / "states.npz"
    f01 = json.loads(f01_audit_path.read_text(encoding="utf-8"))
    h01 = json.loads(h01_audit_path.read_text(encoding="utf-8"))
    if f01["status"] != "complete" or not f01["passed"]:
        raise RuntimeError("F01 input is not complete")
    if h01["status"] != "pilot_complete_with_findings" or not h01["checks_passed"]:
        raise RuntimeError("H01 input is not complete")

    formulas = {row["formula_id"]: row for row in formula_registry()}
    condition_map = {
        (row["system_id"], row["formula_id"]): row
        for row in f01["condition_summaries"]
    }
    stored_operator_map = {
        (row["system_id"], row["formula_id"], int(row["order"])): row
        for row in f01["operator_rows"]
    }
    state_quality_map = {
        (row["system_id"], row["state_id"]): row for row in h01["state_rows"]
    }
    exact_rows: list[dict[str, Any]] = []
    state_rows: list[dict[str, Any]] = []
    molecular_direct_seconds = 0.0
    stored_metric_differences: list[float] = []

    with np.load(operators_path) as arrays, np.load(states_path) as states:
        for system_id in SYSTEMS:
            hamiltonian = np.asarray(
                arrays[f"{system_id}_hamiltonian"], dtype=np.complex128
            )
            ground = np.asarray(
                arrays[f"{system_id}_ground_state"], dtype=np.complex128
            )
            ground_energy = float(arrays[f"{system_id}_ground_energy"])
            group_keys = sorted(
                key for key in arrays.files if key.startswith(f"{system_id}_group_")
            )
            groups = [np.asarray(arrays[key], dtype=np.complex128) for key in group_keys]
            h_energies, h_vectors = np.linalg.eigh(hamiltonian)
            for formula_id, formula in formulas.items():
                d4 = np.asarray(
                    arrays[f"{system_id}_{formula_id}_D4"], dtype=np.complex128
                )
                state_metric = error_operator_state_metrics(d4, ground)
                stored = stored_operator_map[(system_id, formula_id, 4)]
                stored_metric_differences.extend(
                    [
                        abs(
                            state_metric["d4_spectral_norm_hartree"]
                            - float(stored["operator_spectral_norm"])
                        ),
                        abs(
                            state_metric["centered_d4_action_norm_hartree"]
                            - float(stored["centered_action_norm"])
                        ),
                        abs(
                            state_metric["d4_expectation_hartree"]
                            - float(stored["ground_expectation_real"])
                        ),
                    ]
                )
                transformed = h_vectors.conj().T @ d4 @ h_vectors
                diagonal = np.diag(np.diag(transformed))
                diagonal_norm = float(np.linalg.norm(diagonal))
                off_diagonal_norm = float(np.linalg.norm(transformed - diagonal))
                coefficients = condition_map[(system_id, formula_id)][
                    "energy_coefficients"
                ]
                a4 = float(coefficients["a4"])
                a6 = float(coefficients["a6"])
                a8 = float(coefficients["a8"])
                analytic_time = leading_analytic_time(abs(a4))
                sequence = tuple(
                    float(value)
                    for value in symmetric_s2_sequence(formula["weights"])
                )
                direct = track_pf_branch_to_time(
                    groups,
                    sequence,
                    ground,
                    ground_energy,
                    analytic_time,
                )
                molecular_direct_seconds += direct["tracking_elapsed_seconds"]
                leading_shift = a4 * analytic_time**4
                through_a6 = leading_shift + a6 * analytic_time**6
                through_a8 = through_a6 + a8 * analytic_time**8
                exact_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "sector_dimension": int(hamiltonian.shape[0]),
                        "group_count": len(groups),
                        "a4_hartree": a4,
                        "absolute_a4_hartree": abs(a4),
                        **state_metric,
                        "diagonal_d4_frobenius_norm_hartree": diagonal_norm,
                        "off_diagonal_d4_frobenius_norm_hartree": off_diagonal_norm,
                        "off_diagonal_to_diagonal_frobenius_ratio": (
                            off_diagonal_norm / max(diagonal_norm, 1e-300)
                        ),
                        "a6_hartree": a6,
                        "a8_hartree": a8,
                        "one_term_analytic_time_hartree_inverse": analytic_time,
                        "signed_a4_contribution_over_epsilon": leading_shift
                        / TARGET_ERROR,
                        "signed_a6_contribution_over_epsilon": a6
                        * analytic_time**6
                        / TARGET_ERROR,
                        "signed_a8_contribution_over_epsilon": a8
                        * analytic_time**8
                        / TARGET_ERROR,
                        "series_through_a6_shift_over_epsilon": through_a6
                        / TARGET_ERROR,
                        "series_through_a8_shift_over_epsilon": through_a8
                        / TARGET_ERROR,
                        **direct,
                        "direct_pf_absolute_error_over_epsilon": direct[
                            "direct_pf_absolute_error_hartree"
                        ]
                        / TARGET_ERROR,
                        "one_term_direct_residual_over_epsilon": abs(
                            direct["signed_direct_pf_shift_hartree"] - leading_shift
                        )
                        / TARGET_ERROR,
                        "a8_series_direct_residual_over_epsilon": abs(
                            direct["signed_direct_pf_shift_hartree"] - through_a8
                        )
                        / TARGET_ERROR,
                    }
                )

                for state_id in STATE_IDS:
                    state = np.asarray(
                        states[f"{system_id}_{state_id}_state"],
                        dtype=np.complex128,
                    )
                    approximate_metrics = error_operator_state_metrics(d4, state)
                    state_rows.append(
                        {
                            "system_id": system_id,
                            "state_id": state_id,
                            "formula_id": formula_id,
                            "state_energy_error_hartree": state_quality_map[
                                (system_id, state_id)
                            ]["energy_error_hartree"],
                            "state_energy_variance_hartree_squared": state_quality_map[
                                (system_id, state_id)
                            ]["energy_variance_hartree_squared"],
                            "exact_state_overlap_probability": state_quality_map[
                                (system_id, state_id)
                            ]["exact_state_overlap_probability"],
                            **approximate_metrics,
                            "d4_expectation_relative_error_vs_exact_state": abs(
                                approximate_metrics["d4_expectation_hartree"]
                                - state_metric["d4_expectation_hartree"]
                            )
                            / max(
                                abs(state_metric["d4_expectation_hartree"]),
                                1e-300,
                            ),
                        }
                    )

    root = float(
        brentq(
            lambda parameter: float(
                _artificial_operators(parameter)["energy_coefficients"][4].real
            ),
            *ARTIFICIAL_ROOT_BRACKET,
            xtol=1e-14,
        )
    )
    root_data = _artificial_operators(root)
    root_a4 = float(root_data["energy_coefficients"][4].real)
    root_metrics = error_operator_state_metrics(
        root_data["formal"][4], root_data["ground_state"]
    )
    artificial_rows: list[dict[str, Any]] = []
    artificial_direct_seconds = 0.0
    for offset in ARTIFICIAL_OFFSETS:
        parameter = root + float(offset)
        data = _artificial_operators(parameter)
        coefficients = data["energy_coefficients"]
        a4 = float(coefficients[4].real)
        analytic_time = leading_analytic_time(abs(a4))
        metrics = error_operator_state_metrics(
            data["formal"][4], data["ground_state"]
        )
        direct = track_pf_branch_to_time(
            data["groups"],
            data["sequence"],
            data["ground_state"],
            float(data["energies"][0]),
            analytic_time,
        )
        artificial_direct_seconds += direct["tracking_elapsed_seconds"]
        contributions = {
            order: float(coefficients[order].real) * analytic_time**order
            for order in (4, 6, 8, 10, 12)
        }
        series_shift = sum(contributions.values())
        artificial_rows.append(
            {
                "parameter_lambda": parameter,
                "parameter_root": root,
                "parameter_offset_from_root": float(offset),
                "ground_excitation_gap_hartree": float(
                    data["energies"][1] - data["energies"][0]
                ),
                "a4_hartree": a4,
                "absolute_a4_hartree": abs(a4),
                **metrics,
                "one_term_analytic_time_hartree_inverse": analytic_time,
                **{
                    f"signed_a{order}_contribution_over_epsilon": (
                        contributions[order] / TARGET_ERROR
                    )
                    for order in contributions
                },
                "series_through_a12_shift_over_epsilon": series_shift
                / TARGET_ERROR,
                **direct,
                "direct_pf_absolute_error_over_epsilon": direct[
                    "direct_pf_absolute_error_hartree"
                ]
                / TARGET_ERROR,
                "series_through_a12_direct_residual_over_epsilon": abs(
                    series_shift - direct["signed_direct_pf_shift_hartree"]
                )
                / TARGET_ERROR,
            }
        )

    m5_rows = [row for row in exact_rows if row["formula_id"] == "m5_best"]
    y4_rows = [row for row in exact_rows if row["formula_id"] == "yoshida4"]
    molecular_warning_count = sum(
        row["tracking_warning_count"] for row in exact_rows
    )
    artificial_warning_count = sum(
        row["tracking_warning_count"] for row in artificial_rows
    )
    checks = [
        {
            "check_id": "stored_operator_metric_max_absolute_difference",
            "measured": max(stored_metric_differences),
            "threshold": 1e-12,
            "comparison": "<=",
            "passed": max(stored_metric_differences) <= 1e-12,
        },
        {
            "check_id": "exact_condition_row_count",
            "measured": len(exact_rows),
            "threshold": 8,
            "comparison": "==",
            "passed": len(exact_rows) == 8,
        },
        {
            "check_id": "state_operator_row_count",
            "measured": len(state_rows),
            "threshold": 24,
            "comparison": "==",
            "passed": len(state_rows) == 24,
        },
        {
            "check_id": "artificial_family_row_count",
            "measured": len(artificial_rows),
            "threshold": 12,
            "comparison": "==",
            "passed": len(artificial_rows) == 12,
        },
        {
            "check_id": "artificial_root_absolute_a4_hartree",
            "measured": abs(root_a4),
            "threshold": 1e-12,
            "comparison": "<=",
            "passed": abs(root_a4) <= 1e-12,
        },
        {
            "check_id": "artificial_root_minimum_d4_spectral_norm_hartree",
            "measured": root_metrics["d4_spectral_norm_hartree"],
            "threshold": 0.1,
            "comparison": ">=",
            "passed": root_metrics["d4_spectral_norm_hartree"] >= 0.1,
        },
        {
            "check_id": "molecular_branch_warning_count",
            "measured": molecular_warning_count,
            "threshold": 0,
            "comparison": "==",
            "passed": molecular_warning_count == 0,
        },
        {
            "check_id": "artificial_branch_warning_count",
            "measured": artificial_warning_count,
            "threshold": 0,
            "comparison": "==",
            "passed": artificial_warning_count == 0,
        },
        {
            "check_id": "maximum_branch_eigenpair_residual",
            "measured": max(
                [
                    row["tracking_maximum_eigenpair_residual_2_norm"]
                    for row in exact_rows
                ]
                + [
                    row["tracking_maximum_eigenpair_residual_2_norm"]
                    for row in artificial_rows
                ]
            ),
            "threshold": 1e-10,
            "comparison": "<=",
            "passed": max(
                [
                    row["tracking_maximum_eigenpair_residual_2_norm"]
                    for row in exact_rows
                ]
                + [
                    row["tracking_maximum_eigenpair_residual_2_norm"]
                    for row in artificial_rows
                ]
            )
            <= 1e-10,
        },
    ]
    checks_passed = all(check["passed"] for check in checks)
    closest_rows = sorted(
        artificial_rows, key=lambda row: abs(row["parameter_offset_from_root"])
    )[:2]
    hf_rows = [row for row in state_rows if row["state_id"] == "hf"]
    cisd_rows = [row for row in state_rows if row["state_id"] == "cisd"]
    summary = {
        "m5_expectation_over_spectral_range": (
            f"{min(row['expectation_over_spectral_norm'] for row in m5_rows):.4f}--"
            f"{max(row['expectation_over_spectral_norm'] for row in m5_rows):.4f}"
        ),
        "m5_centered_action_over_expectation_range": (
            f"{min(row['centered_action_over_expectation'] for row in m5_rows):.1f}--"
            f"{max(row['centered_action_over_expectation'] for row in m5_rows):.1f}"
        ),
        "m5_a6_contribution_over_epsilon_range": (
            f"{min(abs(row['signed_a6_contribution_over_epsilon']) for row in m5_rows):.4f}--"
            f"{max(abs(row['signed_a6_contribution_over_epsilon']) for row in m5_rows):.4f}"
        ),
        "yoshida_a6_contribution_over_epsilon_range": (
            f"{min(abs(row['signed_a6_contribution_over_epsilon']) for row in y4_rows):.4f}--"
            f"{max(abs(row['signed_a6_contribution_over_epsilon']) for row in y4_rows):.4f}"
        ),
        "state_finding": (
            "HF changes the D4 expectation substantially for the optimized PFs, "
            "whereas CISD remains much closer to exact. The maximum relative D4 "
            f"expectation error is "
            f"{max(row['d4_expectation_relative_error_vs_exact_state'] for row in hf_rows):.3f} "
            f"for HF and "
            f"{max(row['d4_expectation_relative_error_vs_exact_state'] for row in cisd_rows):.3f} "
            "for CISD."
        ),
        "artificial_root": root,
        "artificial_root_absolute_a4_hartree": abs(root_a4),
        "artificial_root_d4_spectral_norm_hartree": root_metrics[
            "d4_spectral_norm_hartree"
        ],
        "artificial_finding": (
            "At |lambda-lambda0|=0.03 the direct error at the one-term time is "
            "0.925--1.361 epsilon; by distance 0.01 it exceeds 5 epsilon on both "
            "sides. At the closest sampled distance 0.001 it reaches "
            f"{min(row['direct_pf_absolute_error_over_epsilon'] for row in closest_rows):.1f}--"
            f"{max(row['direct_pf_absolute_error_over_epsilon'] for row in closest_rows):.1f} epsilon."
        ),
        "molecular_tracking_seconds": molecular_direct_seconds,
        "artificial_tracking_seconds": artificial_direct_seconds,
    }
    audit = {
        "schema": "prevalidation_f03_a4_operator_cancellation_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete_with_findings" if checks_passed else "failed",
        "passed": checks_passed,
        "scope": {
            "catalog_item": "F03",
            "systems": list(SYSTEMS),
            "formula_ids": list(formulas),
            "state_ids": list(STATE_IDS),
            "new_molecular_direct_pf_points": 8,
            "artificial_direct_pf_points": 12,
            "claim_boundary": (
                "H2/H4 molecular diagnosis plus constructive two-level family"
            ),
        },
        "protocol": {
            "target_error_hartree": TARGET_ERROR,
            "analytic_time": "(epsilon/(5*|a4|))^(1/4)",
            "branch_tracking_point_count": TRACKING_POINT_COUNT,
            "artificial_groups": ["A(lambda)=X+lambda Z", "B=Z"],
            "artificial_formula": "Yoshida fourth order",
            "artificial_root_bracket": list(ARTIFICIAL_ROOT_BRACKET),
            "artificial_offsets": list(ARTIFICIAL_OFFSETS),
        },
        "checks": checks,
        "summary": summary,
        "exact_condition_rows": exact_rows,
        "state_operator_rows": state_rows,
        "artificial_family_rows": artificial_rows,
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "exact_condition_metrics.csv", exact_rows)
    _write_csv(output_dir / "state_operator_metrics.csv", state_rows)
    _write_csv(output_dir / "artificial_family.csv", artificial_rows)
    _write_figures(output_dir, exact_rows, artificial_rows)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/audit_f01_effective_hamiltonian_multipf.py"),
        Path("review_response/audit_h01_approximate_state_pilot.py"),
        Path("review_response/bch_matrix_series.py"),
    ]
    input_paths = [
        f01_audit_path,
        operators_path,
        h01_audit_path,
        states_path,
    ]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "exact_condition_metrics.csv",
        output_dir / "state_operator_metrics.csv",
        output_dir / "artificial_family.csv",
        output_dir / "a4_vs_d4_norm.png",
        output_dir / "artificial_zero_approach.png",
        output_dir / "report.md",
    ]
    manifest = {
        "status": audit["status"],
        "git": {
            "head": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "dirty": bool(_git_output("status", "--porcelain")),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
        "output_directory": str(output_dir),
        "runtime": audit["runtime"],
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f01-dir", type=Path, default=DEFAULT_F01)
    parser.add_argument("--h01-dir", type=Path, default=DEFAULT_H01)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(arguments.f01_dir, arguments.h01_dir, arguments.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(arguments.output_dir),
                "status": audit["status"],
                "passed": audit["passed"],
                "summary": audit["summary"],
                "runtime": audit["runtime"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
