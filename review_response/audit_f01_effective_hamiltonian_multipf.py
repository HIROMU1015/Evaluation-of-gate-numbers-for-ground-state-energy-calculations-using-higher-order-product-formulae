"""F01 multi-PF audit of molecular effective-Hamiltonian error operators.

The audit expands the actual ordered PF product through D12 and independently
recovers D4, D6, and D8 from continuous principal matrix logarithms at finite
times.  All formulas use the same three predeclared windows.  Interlaced
holdout times are never used in the operator fits.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import resource
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _direct_pf_shift,
    _git_output,
    _log_interlaced_times,
    _package_versions,
    _relative_matrix_error,
    _selected_energy,
    _sha256,
    _write_csv,
    continuous_effective_hamiltonian,
    evaluate_operator_polynomial,
    fit_even_effective_operators,
    group_matrices,
    operator_decomposition,
)
from review_response.bch_matrix_series import (
    effective_hamiltonian_series,
    effective_hamiltonian_series_numpy,
    eigenenergy_perturbation_series,
)
from review_response.compare_existing_pf_low_order_models_local import (
    CURRENT_M3_WEIGHTS,
    TWO_TERM_CENTER_WEIGHTS,
)
from review_response.validate_hchain_perturbative_estimator import (
    _prepare_sector_system,
)
from trotterlib.config import TARGET_ERROR
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import (
    actual_circuit_optimized_4th_m5_list,
    yoshida_4th_list,
)


DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
SYSTEM_SIZES = (2, 4)
FORMAL_MAXIMUM_ORDER = 12
FIT_ORDERS = (4, 6, 8, 10, 12)
REFERENCE_ORDERS = (4, 6, 8)
HIGH_PRECISION_DIGITS = (70, 100)
FIT_WINDOWS = (
    {"window_id": "lower", "minimum": 0.08, "maximum": 0.60, "bins": 15},
    {"window_id": "middle", "minimum": 0.09, "maximum": 0.70, "bins": 16},
    {"window_id": "upper", "minimum": 0.10, "maximum": 0.80, "bins": 17},
)
THRESHOLDS = {
    "h0_frobenius_error": 5e-13,
    "forbidden_order_max_frobenius": 1e-10,
    "h2_numpy_relative_difference_d4_d6_d8": 1e-7,
    "reference_relative_hermiticity_d4_d6_d8": 1e-8,
    "fit_relative_error_d4": 1e-5,
    "fit_relative_error_d6": 1e-3,
    "fit_relative_error_d8": 1e-2,
    "window_pair_relative_difference_d8": 1.5e-2,
    "holdout_fit_relative_to_correction": 1e-3,
    "log_unitary_reconstruction_frobenius": 1e-10,
    "minimum_branch_cut_margin_radians": 0.5,
}


def formula_registry() -> tuple[dict[str, Any], ...]:
    """Return fixed existing fourth-order formulas and their provenance."""

    return (
        {
            "formula_id": "yoshida4",
            "label": "Yoshida 4th",
            "weights": tuple(float(value) for value in yoshida_4th_list()),
            "provenance": "src/trotterlib/product_formula.py:yoshida_4th_list",
        },
        {
            "formula_id": "current_m3",
            "label": "current_m3",
            "weights": tuple(float(value) for value in CURRENT_M3_WEIGHTS),
            "provenance": (
                "review_response/compare_existing_pf_low_order_models_local.py:"
                "CURRENT_M3_WEIGHTS"
            ),
        },
        {
            "formula_id": "two_term_center",
            "label": "two_term_center",
            "weights": tuple(float(value) for value in TWO_TERM_CENTER_WEIGHTS),
            "provenance": (
                "review_response/compare_existing_pf_low_order_models_local.py:"
                "TWO_TERM_CENTER_WEIGHTS"
            ),
        },
        {
            "formula_id": "m5_best",
            "label": "m5_best",
            "weights": tuple(
                float(value) for value in actual_circuit_optimized_4th_m5_list()
            ),
            "provenance": (
                "src/trotterlib/product_formula.py:"
                "actual_circuit_optimized_4th_m5_list"
            ),
        },
    )


def _hermitian(matrix: np.ndarray) -> np.ndarray:
    array = np.asarray(matrix, dtype=np.complex128)
    return (array + array.conj().T) / 2.0


def _relative_hermiticity_residual(matrix: np.ndarray) -> float:
    array = np.asarray(matrix, dtype=np.complex128)
    return float(
        np.linalg.norm(array - array.conj().T)
        / max(float(np.linalg.norm(array)), 1e-300)
    )


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    x = np.asarray(left, dtype=float)
    y = np.asarray(right, dtype=float)
    if x.size < 2 or np.std(x) <= 1e-300 or np.std(y) <= 1e-300:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _energy_series_prediction(
    energy_coefficients: np.ndarray, time_value: float, maximum_order: int
) -> float:
    return float(
        sum(
            complex(energy_coefficients[order]).real * float(time_value) ** order
            for order in range(1, maximum_order + 1)
        )
    )


def _write_npz(
    path: Path, operator_matrices: dict[str, np.ndarray]
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **operator_matrices)
    temporary.replace(path)


def _write_figures(
    output_dir: Path,
    operator_rows: Sequence[dict[str, Any]],
    recovery_rows: Sequence[dict[str, Any]],
) -> None:
    d4_rows = [row for row in operator_rows if row["order"] == 4]
    figure, axis = plt.subplots(figsize=(6.6, 4.4))
    markers = {"H2": "o", "H4": "s"}
    for row in d4_rows:
        axis.scatter(
            abs(row["ground_expectation_real"])
            / max(row["operator_frobenius_norm"], 1e-300),
            row["ground_to_excited_coupling_norm"]
            / max(row["operator_frobenius_norm"], 1e-300),
            marker=markers[row["system_id"]],
            s=48,
        )
        axis.annotate(
            f"{row['system_id']}:{row['formula_id']}",
            (
                abs(row["ground_expectation_real"])
                / max(row["operator_frobenius_norm"], 1e-300),
                row["ground_to_excited_coupling_norm"]
                / max(row["operator_frobenius_norm"], 1e-300),
            ),
            fontsize=7,
            xytext=(3, 3),
            textcoords="offset points",
        )
    axis.set_xlabel(r"$|\langle0|D_4|0\rangle|/\|D_4\|_F$")
    axis.set_ylabel(r"$\|Q D_4|0\rangle\|/\|D_4\|_F$")
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "d4_diagonal_vs_coupling.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7.0, 4.4))
    labels = []
    for system_id in ("H2", "H4"):
        for formula in formula_registry():
            rows = [
                row
                for row in recovery_rows
                if row["system_id"] == system_id
                and row["formula_id"] == formula["formula_id"]
            ]
            labels.append(f"{system_id}:{formula['formula_id']}")
            axis.plot(
                range(len(FIT_WINDOWS)),
                [row["relative_error_d8"] for row in rows],
                marker="o",
                linewidth=1.0,
                label=labels[-1],
            )
    axis.axhline(
        THRESHOLDS["fit_relative_error_d8"],
        color="black",
        linestyle="--",
        linewidth=0.9,
        label="D8 threshold",
    )
    axis.set_xticks(
        range(len(FIT_WINDOWS)),
        [window["window_id"] for window in FIT_WINDOWS],
    )
    axis.set_yscale("log")
    axis.set_ylabel("relative D8 matrix error")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(frameon=False, fontsize=7, ncol=2)
    figure.tight_layout()
    figure.savefig(output_dir / "d8_window_recovery.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    checks = audit["checks"]
    lines = [
        "# F01 multi-PF effective-Hamiltonian audit",
        "",
        f"Status: **{audit['status']}**",
        "",
        "H2/H4の固定Hamiltonian分割に対し、4種類の既存4次PFを同じ有限時刻窓で検証した。"
        "これはF01の小系最小検証であり、F02の状態混合分解やHF holdoutの機構診断は含まない。",
        "",
        "## Gate checks",
        "",
        "| check | measured | threshold | pass |",
        "|---|---:|---:|:---:|",
    ]
    for check in checks:
        lines.append(
            f"| {check['check_id']} | {check['measured']:.6e} | "
            f"{check['threshold']:.6e} | {'yes' if check['passed'] else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## D4 structure",
            "",
            "| system | PF | ||D4||F | <0|D4|0> | ||Q D4|0>|| | "
            "diagonal fraction | coupling fraction |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in audit["operator_rows"]:
        if row["order"] != 4:
            continue
        norm = max(row["operator_frobenius_norm"], 1e-300)
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{row['operator_frobenius_norm']:.6e} | "
            f"{row['ground_expectation_real']:.6e} | "
            f"{row['ground_to_excited_coupling_norm']:.6e} | "
            f"{abs(row['ground_expectation_real']) / norm:.4f} | "
            f"{row['ground_to_excited_coupling_norm'] / norm:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Finite-log recovery and energy correlation",
            "",
            "| system | PF | max rel D4 | max rel D6 | max rel D8 | "
            "min branch margin | D8 energy-series corr. |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for summary in audit["condition_summaries"]:
        correlation = summary["energy_series_d8_pearson_correlation"]
        correlation_text = "n/a" if correlation is None else f"{correlation:.8f}"
        lines.append(
            f"| {summary['system_id']} | {summary['formula_id']} | "
            f"{summary['maximum_relative_error_d4']:.3e} | "
            f"{summary['maximum_relative_error_d6']:.3e} | "
            f"{summary['maximum_relative_error_d8']:.3e} | "
            f"{summary['minimum_branch_cut_margin_radians']:.3f} | "
            f"{correlation_text} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            audit["interpretation"]["operator_result"],
            "",
            audit["interpretation"]["numerical_result"],
            "",
            "The finite-log fits use identical windows for every PF. H2 also "
            "cross-checks the complex128 formal series against 70- and "
            "100-decimal-digit ordered-product logarithms. H4 uses complex128 "
            "formal series, independently checked by finite-time matrix logs; "
            "this backend limitation is retained in the audit metadata.",
            "",
            "## Decision",
            "",
        ]
    )
    if audit["passed"]:
        lines.append(
            "F01の小系・複数PFゲートは合格とする。次は同じ保存済みD4/D6/D8を使い、"
            "F02でa8を直接D8期待値とD4による二次状態混合へ分離する。"
        )
    else:
        lines.append(
            "F01ゲートには未解決の数値不安定性がある。F02へ進む前に失敗した検査を診断する。"
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `audit.json`: complete machine-readable summary.",
            "- `formula_registry.csv`: exact PF weights and expanded S2 metadata.",
            "- `reference_validation.csv`: formal-series precision/backend checks.",
            "- `window_recovery.csv`: D4/D6/D8 recovery in the three common windows.",
            "- `holdout_validation.csv`: interlaced unseen-time operator/eigenvalue checks.",
            "- `operator_decomposition.csv`: diagonal and off-diagonal operator diagnostics.",
            "- `effective_operators.npz`: complex D4/D6/D8 matrices plus the "
            "exact Hamiltonian, ground state, ground energy, and group matrices "
            "in the same stored basis.",
            "- `manifest.json`: source hashes, environment, runtime, and artifact hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    formulas = formula_registry()
    reference_rows: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    holdout_rows: list[dict[str, Any]] = []
    operator_rows: list[dict[str, Any]] = []
    formula_rows: list[dict[str, Any]] = []
    condition_summaries: list[dict[str, Any]] = []
    matrices_to_save: dict[str, np.ndarray] = {}
    pairwise_d8_differences: list[float] = []
    log_reconstruction_residuals: list[float] = []
    branch_margins: list[float] = []
    h0_errors: list[float] = []
    forbidden_norms: list[float] = []
    reference_hermiticity: list[float] = []
    numpy_h2_differences: list[float] = []

    for h_chain in SYSTEM_SIZES:
        system_id = f"H{h_chain}"
        system = _prepare_sector_system(h_chain)
        matrices = group_matrices(system)
        hamiltonian = sum(matrices, np.zeros_like(matrices[0]))
        reference_state = np.asarray(system["ground_state"], dtype=np.complex128)
        reference_energy = float(system["ground_energy_without_constant_hartree"])
        # D operators are basis-dependent.  Persist their exact H/state/group
        # basis so downstream F02/F05 audits never regenerate a merely
        # isospectral molecular representation in another process.
        matrices_to_save[f"{system_id}_hamiltonian"] = hamiltonian
        matrices_to_save[f"{system_id}_ground_state"] = reference_state
        matrices_to_save[f"{system_id}_ground_energy"] = np.asarray(
            reference_energy, dtype=float
        )
        for group_index, group_matrix in enumerate(matrices):
            matrices_to_save[
                f"{system_id}_group_{group_index:03d}"
            ] = group_matrix

        for formula in formulas:
            sequence = tuple(
                float(value) for value in symmetric_s2_sequence(formula["weights"])
            )
            steps = list(iter_s2_sequence_steps(len(matrices), sequence))
            numpy_raw = effective_hamiltonian_series_numpy(
                matrices, steps, FORMAL_MAXIMUM_ORDER
            )["effective_hamiltonian"]

            if h_chain == 2:
                high_precision_by_digits = {
                    digits: effective_hamiltonian_series(
                        matrices,
                        steps,
                        FORMAL_MAXIMUM_ORDER,
                        decimal_digits=digits,
                    )["effective_hamiltonian"]
                    for digits in HIGH_PRECISION_DIGITS
                }
                formal_raw = high_precision_by_digits[max(HIGH_PRECISION_DIGITS)]
                for order in REFERENCE_ORDERS:
                    precision_difference = _relative_matrix_error(
                        high_precision_by_digits[min(HIGH_PRECISION_DIGITS)][order],
                        formal_raw[order],
                    )
                    backend_difference = _relative_matrix_error(
                        numpy_raw[order], formal_raw[order]
                    )
                    numpy_h2_differences.append(backend_difference)
                    reference_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula["formula_id"],
                            "order": order,
                            "reference_backend": "mpmath_ordered_product_log_100d",
                            "precision_70d_vs_100d_relative_difference": (
                                precision_difference
                            ),
                            "numpy_vs_100d_relative_difference": backend_difference,
                            "raw_relative_hermiticity_residual": (
                                _relative_hermiticity_residual(formal_raw[order])
                            ),
                        }
                    )
            else:
                formal_raw = numpy_raw
                for order in REFERENCE_ORDERS:
                    reference_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula["formula_id"],
                            "order": order,
                            "reference_backend": "complex128_ordered_product_log",
                            "precision_70d_vs_100d_relative_difference": "",
                            "numpy_vs_100d_relative_difference": "",
                            "raw_relative_hermiticity_residual": (
                                _relative_hermiticity_residual(formal_raw[order])
                            ),
                        }
                    )

            formal = [_hermitian(matrix) for matrix in formal_raw]
            h0_errors.append(float(np.linalg.norm(formal[0] - hamiltonian)))
            forbidden_norms.extend(
                float(np.linalg.norm(formal_raw[order]))
                for order in (1, 2, 3, 5, 7, 9, 11)
            )
            reference_hermiticity.extend(
                _relative_hermiticity_residual(formal_raw[order])
                for order in REFERENCE_ORDERS
            )

            for order in REFERENCE_ORDERS:
                key = f"{system_id}_{formula['formula_id']}_D{order}"
                matrices_to_save[key] = formal[order]
                row = operator_decomposition(
                    hamiltonian, reference_state, formal[order], order
                )
                row.update(
                    {"system_id": system_id, "formula_id": formula["formula_id"]}
                )
                operator_rows.append(row)

            perturbation = eigenenergy_perturbation_series(
                formal, reference_state, maximum_order=FORMAL_MAXIMUM_ORDER
            )
            energy_coefficients = np.asarray(
                perturbation["energy_coefficients"], dtype=np.complex128
            )
            fitted_by_window: dict[str, list[np.ndarray]] = {}
            direct_for_correlation: dict[float, float] = {}
            d4_for_correlation: dict[float, float] = {}
            d8_for_correlation: dict[float, float] = {}
            d12_for_correlation: dict[float, float] = {}
            formula_recovery_rows: list[dict[str, Any]] = []
            formula_branch_margins: list[float] = []

            for window in FIT_WINDOWS:
                training_times, holdout_times = _log_interlaced_times(
                    window["minimum"], window["maximum"], window["bins"]
                )
                corrections = []
                training_records = []
                for time_value in training_times:
                    record = continuous_effective_hamiltonian(
                        system, sequence, float(time_value)
                    )
                    corrections.append(
                        record["effective_hamiltonian"] - hamiltonian
                    )
                    training_records.append(record)
                    log_reconstruction_residuals.append(
                        record["unitary_reconstruction_residual_frobenius"]
                    )
                    branch_margins.append(record["branch_cut_margin_radians"])
                    formula_branch_margins.append(
                        record["branch_cut_margin_radians"]
                    )
                fit = fit_even_effective_operators(
                    training_times, np.asarray(corrections), FIT_ORDERS
                )
                fitted_by_window[window["window_id"]] = fit["coefficients"]
                recovery_row: dict[str, Any] = {
                    "system_id": system_id,
                    "formula_id": formula["formula_id"],
                    "window_id": window["window_id"],
                    "minimum_time": window["minimum"],
                    "maximum_time": window["maximum"],
                    "training_point_count": int(training_times.size),
                    "holdout_point_count": int(holdout_times.size),
                    "scaled_design_condition_number": fit["condition_number"],
                    "training_residual_frobenius_max": fit[
                        "training_residual_frobenius_max"
                    ],
                }
                for index, order in enumerate(FIT_ORDERS):
                    recovery_row[f"relative_error_d{order}"] = (
                        _relative_matrix_error(
                            fit["coefficients"][index], formal[order]
                        )
                    )
                recovery_rows.append(recovery_row)
                formula_recovery_rows.append(recovery_row)

                for time_value in holdout_times:
                    direct = continuous_effective_hamiltonian(
                        system, sequence, float(time_value)
                    )
                    fitted_matrix = evaluate_operator_polynomial(
                        hamiltonian,
                        fit["orders"],
                        fit["coefficients"],
                        float(time_value),
                    )
                    formal_matrix = evaluate_operator_polynomial(
                        hamiltonian,
                        range(1, FORMAL_MAXIMUM_ORDER + 1),
                        formal[1:],
                        float(time_value),
                    )
                    fitted_energy, fitted_overlap = _selected_energy(
                        fitted_matrix, reference_state
                    )
                    formal_energy, formal_overlap = _selected_energy(
                        formal_matrix, reference_state
                    )
                    direct_energy, direct_overlap = _selected_energy(
                        direct["effective_hamiltonian"], reference_state
                    )
                    pf_shift = _direct_pf_shift(
                        direct["unitary"],
                        reference_state,
                        reference_energy,
                        float(time_value),
                    )
                    correction_norm = float(
                        np.linalg.norm(
                            direct["effective_hamiltonian"] - hamiltonian
                        )
                    )
                    fit_residual = float(
                        np.linalg.norm(
                            fitted_matrix - direct["effective_hamiltonian"]
                        )
                    )
                    direct_shift = float(pf_shift["shift"])
                    d4_shift = _energy_series_prediction(
                        energy_coefficients, float(time_value), 4
                    )
                    d8_shift = _energy_series_prediction(
                        energy_coefficients, float(time_value), 8
                    )
                    d12_shift = _energy_series_prediction(
                        energy_coefficients, float(time_value), 12
                    )
                    key = round(float(time_value), 15)
                    direct_for_correlation[key] = direct_shift
                    d4_for_correlation[key] = d4_shift
                    d8_for_correlation[key] = d8_shift
                    d12_for_correlation[key] = d12_shift
                    holdout_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula["formula_id"],
                            "window_id": window["window_id"],
                            "time_hartree_inverse": float(time_value),
                            "fit_matrix_residual_frobenius": fit_residual,
                            "fit_matrix_residual_relative_to_correction": (
                                fit_residual / max(correction_norm, 1e-300)
                            ),
                            "formal_d12_matrix_residual_frobenius": float(
                                np.linalg.norm(
                                    formal_matrix
                                    - direct["effective_hamiltonian"]
                                )
                            ),
                            "direct_heff_shift_hartree": float(
                                direct_energy - reference_energy
                            ),
                            "direct_pf_shift_hartree": direct_shift,
                            "fitted_heff_shift_hartree": float(
                                fitted_energy - reference_energy
                            ),
                            "formal_d12_heff_shift_hartree": float(
                                formal_energy - reference_energy
                            ),
                            "energy_series_d4_shift_hartree": d4_shift,
                            "energy_series_d8_shift_hartree": d8_shift,
                            "energy_series_d12_shift_hartree": d12_shift,
                            "energy_series_d8_residual_over_epsilon": float(
                                abs(d8_shift - direct_shift) / TARGET_ERROR
                            ),
                            "energy_series_d12_residual_over_epsilon": float(
                                abs(d12_shift - direct_shift) / TARGET_ERROR
                            ),
                            "direct_ground_overlap_probability": direct_overlap,
                            "fitted_ground_overlap_probability": fitted_overlap,
                            "formal_ground_overlap_probability": formal_overlap,
                            "pf_ground_overlap_probability": pf_shift[
                                "overlap_probability"
                            ],
                            "pf_eigenpair_residual_2_norm": pf_shift[
                                "eigenpair_residual"
                            ],
                            "phase_unwrap_integer": pf_shift["unwrap_integer"],
                            "principal_log_branch_cut_margin_radians": direct[
                                "branch_cut_margin_radians"
                            ],
                            "principal_log_unitary_reconstruction_frobenius": (
                                direct[
                                    "unitary_reconstruction_residual_frobenius"
                                ]
                            ),
                        }
                    )
                    log_reconstruction_residuals.append(
                        direct["unitary_reconstruction_residual_frobenius"]
                    )
                    branch_margins.append(direct["branch_cut_margin_radians"])
                    formula_branch_margins.append(
                        direct["branch_cut_margin_radians"]
                    )

            window_ids = [window["window_id"] for window in FIT_WINDOWS]
            for left_index, left in enumerate(window_ids):
                for right in window_ids[left_index + 1 :]:
                    left_d8 = fitted_by_window[left][FIT_ORDERS.index(8)]
                    right_d8 = fitted_by_window[right][FIT_ORDERS.index(8)]
                    pairwise_d8_differences.append(
                        _relative_matrix_error(left_d8, right_d8)
                    )

            sorted_times = sorted(direct_for_correlation)
            direct_values = [direct_for_correlation[value] for value in sorted_times]
            condition_summaries.append(
                {
                    "system_id": system_id,
                    "formula_id": formula["formula_id"],
                    "sector_dimension": int(reference_state.size),
                    "number_of_groups": len(matrices),
                    "maximum_relative_error_d4": max(
                        row["relative_error_d4"] for row in formula_recovery_rows
                    ),
                    "maximum_relative_error_d6": max(
                        row["relative_error_d6"] for row in formula_recovery_rows
                    ),
                    "maximum_relative_error_d8": max(
                        row["relative_error_d8"] for row in formula_recovery_rows
                    ),
                    "minimum_branch_cut_margin_radians": min(
                        formula_branch_margins
                    ),
                    "energy_series_d4_pearson_correlation": _pearson(
                        direct_values,
                        [d4_for_correlation[value] for value in sorted_times],
                    ),
                    "energy_series_d8_pearson_correlation": _pearson(
                        direct_values,
                        [d8_for_correlation[value] for value in sorted_times],
                    ),
                    "energy_series_d12_pearson_correlation": _pearson(
                        direct_values,
                        [d12_for_correlation[value] for value in sorted_times],
                    ),
                    "maximum_energy_series_d8_residual_over_epsilon": max(
                        abs(d8_for_correlation[value] - direct_for_correlation[value])
                        / TARGET_ERROR
                        for value in sorted_times
                    ),
                    "maximum_energy_series_d12_residual_over_epsilon": max(
                        abs(
                            d12_for_correlation[value]
                            - direct_for_correlation[value]
                        )
                        / TARGET_ERROR
                        for value in sorted_times
                    ),
                    "energy_coefficients": {
                        f"a{order}": float(energy_coefficients[order].real)
                        for order in REFERENCE_ORDERS
                    },
                }
            )

            formula_rows.append(
                {
                    "system_id": system_id,
                    "formula_id": formula["formula_id"],
                    "label": formula["label"],
                    "provenance": formula["provenance"],
                    "weights_json": json.dumps(formula["weights"]),
                    "s2_sequence_json": json.dumps(sequence),
                    "s2_block_count": len(sequence),
                    "expanded_step_count": len(steps),
                    "normalization": float(
                        formula["weights"][0]
                        + 2.0 * sum(formula["weights"][1:])
                    ),
                }
            )

    extrema = {
        "h0_frobenius_error": max(h0_errors),
        "forbidden_order_max_frobenius": max(forbidden_norms),
        "h2_numpy_relative_difference_d4_d6_d8": max(
            numpy_h2_differences
        ),
        "reference_relative_hermiticity_d4_d6_d8": max(
            reference_hermiticity
        ),
        "fit_relative_error_d4": max(
            row["relative_error_d4"] for row in recovery_rows
        ),
        "fit_relative_error_d6": max(
            row["relative_error_d6"] for row in recovery_rows
        ),
        "fit_relative_error_d8": max(
            row["relative_error_d8"] for row in recovery_rows
        ),
        "window_pair_relative_difference_d8": max(pairwise_d8_differences),
        "holdout_fit_relative_to_correction": max(
            row["fit_matrix_residual_relative_to_correction"]
            for row in holdout_rows
        ),
        "log_unitary_reconstruction_frobenius": max(
            log_reconstruction_residuals
        ),
        "minimum_branch_cut_margin_radians": min(branch_margins),
    }
    checks = []
    for check_id, threshold in THRESHOLDS.items():
        measured = float(extrema[check_id])
        minimum_check = check_id == "minimum_branch_cut_margin_radians"
        checks.append(
            {
                "check_id": check_id,
                "measured": measured,
                "threshold": threshold,
                "comparison": ">=" if minimum_check else "<=",
                "passed": bool(
                    measured >= threshold if minimum_check else measured <= threshold
                ),
            }
        )
    passed = all(check["passed"] for check in checks)

    d4_rows = [row for row in operator_rows if row["order"] == 4]
    expectation_fractions = [
        abs(row["ground_expectation_real"])
        / max(row["operator_frobenius_norm"], 1e-300)
        for row in d4_rows
    ]
    coupling_fractions = [
        row["ground_to_excited_coupling_norm"]
        / max(row["operator_frobenius_norm"], 1e-300)
        for row in d4_rows
    ]
    interpretation = {
        "operator_result": (
            "D4の基底状態期待値は演算子Frobeniusノルムの"
            f"{min(expectation_fractions):.3%}–{max(expectation_fractions):.3%}、"
            "基底状態から励起空間への結合ノルムは"
            f"{min(coupling_fractions):.3%}–{max(coupling_fractions):.3%}である。"
            "したがって、全演算子ノルム、固有値シフト、状態混合を同一量とは扱えない。"
        ),
        "numerical_result": (
            "全8条件で共通の3窓からD4/D6/D8を回収し、"
            f"最悪D8相対誤差は{extrema['fit_relative_error_d8']:.3%}、"
            "最小位相枝余裕は"
            f"{extrema['minimum_branch_cut_margin_radians']:.3f} radだった。"
        ),
    }
    audit = {
        "schema": "prevalidation_f01_effective_hamiltonian_multipf_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete" if passed else "complete_with_findings",
        "passed": passed,
        "scope": {
            "catalog_item": "F01",
            "systems": ["H2/STO-3G repository H-chain", "H4/STO-3G repository H-chain"],
            "formula_ids": [formula["formula_id"] for formula in formulas],
            "condition_count": len(SYSTEM_SIZES) * len(formulas),
            "sign_convention": "U_PF(t)=exp(+i t H_eff(t))",
            "completed": "F01 small-system multi-PF minimum validation",
            "not_completed": ["F02", "F05", "full-electron HF mechanism application"],
        },
        "protocol": {
            "formal_maximum_order": FORMAL_MAXIMUM_ORDER,
            "fit_orders": list(FIT_ORDERS),
            "fit_windows": FIT_WINDOWS,
            "training_holdout_rule": (
                "log-bin edges for training; geometric midpoints for holdout"
            ),
            "h2_reference": "70/100 decimal digit ordered-product formal logarithm",
            "h4_reference": (
                "complex128 ordered-product formal logarithm, independently "
                "checked by finite-time matrix logarithms"
            ),
            "basis_persistence": (
                "Hamiltonian, ground state, ground energy, and every group "
                "matrix are stored in effective_operators.npz with D4/D6/D8"
            ),
            "thresholds": THRESHOLDS,
        },
        "checks": checks,
        "extrema": extrema,
        "formula_rows": formula_rows,
        "reference_rows": reference_rows,
        "recovery_rows": recovery_rows,
        "holdout_rows": holdout_rows,
        "operator_rows": operator_rows,
        "condition_summaries": condition_summaries,
        "interpretation": interpretation,
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _write_npz(output_dir / "effective_operators.npz", matrices_to_save)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "formula_registry.csv", formula_rows)
    _write_csv(output_dir / "reference_validation.csv", reference_rows)
    _write_csv(output_dir / "window_recovery.csv", recovery_rows)
    _write_csv(output_dir / "holdout_validation.csv", holdout_rows)
    _write_csv(output_dir / "operator_decomposition.csv", operator_rows)
    _write_figures(output_dir, operator_rows, recovery_rows)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/audit_f01_effective_hamiltonian_pilot.py"),
        Path("review_response/bch_matrix_series.py"),
        Path("review_response/compare_existing_pf_low_order_models_local.py"),
        Path("review_response/validate_hchain_perturbative_estimator.py"),
        Path("src/trotterlib/pf_decomposition.py"),
        Path("src/trotterlib/product_formula.py"),
        Path("src/trotterlib/sector_pf.py"),
    ]
    output_paths = [
        output_dir / "audit.json",
        output_dir / "formula_registry.csv",
        output_dir / "reference_validation.csv",
        output_dir / "window_recovery.csv",
        output_dir / "holdout_validation.csv",
        output_dir / "operator_decomposition.csv",
        output_dir / "effective_operators.npz",
        output_dir / "d4_diagonal_vs_coupling.png",
        output_dir / "d8_window_recovery.png",
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
        "artifact_sha256": {str(path): _sha256(path) for path in output_paths},
        "output_directory": str(output_dir),
        "runtime": audit["runtime"],
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(arguments.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(arguments.output_dir),
                "status": audit["status"],
                "passed": audit["passed"],
                "extrema": audit["extrema"],
                "runtime": audit["runtime"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
