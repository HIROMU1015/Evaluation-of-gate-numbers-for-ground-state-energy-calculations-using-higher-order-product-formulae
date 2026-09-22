"""F01 pilot: recover the H2/Yoshida-4 effective-Hamiltonian operators.

The high-precision formal logarithm of the ordered PF product is the reference.
Independently, finite-time PF unitaries are converted to a continuous principal
matrix logarithm on a phase-safe interval and fitted in three disjoint time
windows.  Training and holdout times are interlaced but never identical.
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

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import expm, logm, schur

from review_response.bch_matrix_series import effective_hamiltonian_series
from review_response.validate_hchain_perturbative_estimator import (
    _prepare_sector_system,
)
from trotterlib.config import TARGET_ERROR
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import yoshida_4th_list
from trotterlib.sector_pf import build_sector_pf_unitary


DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_pilot_20260921"
)
REFERENCE_DIGITS = (60, 80, 100)
FIT_ORDERS = (4, 6, 8, 10, 12)
FIT_WINDOWS = (
    {"window_id": "short", "minimum": 0.05, "maximum": 0.40, "bins": 13},
    {"window_id": "central", "minimum": 0.08, "maximum": 0.60, "bins": 15},
    {"window_id": "wide", "minimum": 0.10, "maximum": 0.80, "bins": 17},
)
PILOT_THRESHOLDS = {
    "h0_frobenius_error": 1e-13,
    "forbidden_order_max_frobenius": 1e-12,
    "precision_relative_difference_d4_d6_d8": 1e-10,
    "fit_relative_error_d4": 1e-5,
    "fit_relative_error_d6": 1e-3,
    "fit_relative_error_d8": 5e-3,
    "window_pair_relative_difference_d8": 5e-3,
    "log_unitary_reconstruction_frobenius": 1e-12,
    "minimum_branch_cut_margin_radians": 0.5,
    "holdout_shift_residual_over_epsilon": 1e-4,
}


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_output(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def group_matrices(system: dict[str, Any]) -> list[np.ndarray]:
    """Reconstruct dense group matrices from the cached eigendecompositions."""

    matrices = []
    for eigenvalues, eigenvectors in system["group_spectra"]:
        values = np.asarray(eigenvalues, dtype=float)
        vectors = np.asarray(eigenvectors, dtype=np.complex128)
        matrices.append((vectors * values[None, :]) @ vectors.conj().T)
    return matrices


def fit_even_effective_operators(
    times: np.ndarray,
    corrections: np.ndarray,
    orders: Sequence[int] = FIT_ORDERS,
) -> dict[str, Any]:
    """Fit matrix-valued even-power coefficients with a scaled design."""

    x = np.asarray(times, dtype=float)
    y = np.asarray(corrections, dtype=np.complex128)
    if x.ndim != 1 or y.shape[0] != x.size or np.any(x <= 0.0):
        raise ValueError("invalid time/correction arrays")
    if x.size < len(orders):
        raise ValueError("insufficient times for requested operator orders")
    reference_time = float(np.max(x))
    scaled_design = np.column_stack(
        [(x / reference_time) ** int(order) for order in orders]
    )
    flattened = y.reshape(x.size, -1)
    scaled_coefficients = np.linalg.lstsq(
        scaled_design, flattened, rcond=None
    )[0]
    coefficients = []
    for index, order in enumerate(orders):
        matrix = (
            scaled_coefficients[index].reshape(y.shape[1:])
            / reference_time ** int(order)
        )
        coefficients.append((matrix + matrix.conj().T) / 2.0)
    prediction = scaled_design @ scaled_coefficients
    residuals = prediction.reshape(y.shape) - y
    return {
        "orders": tuple(int(order) for order in orders),
        "reference_time": reference_time,
        "condition_number": float(np.linalg.cond(scaled_design)),
        "coefficients": coefficients,
        "training_residual_frobenius_max": float(
            max(np.linalg.norm(matrix) for matrix in residuals)
        ),
    }


def evaluate_operator_polynomial(
    hamiltonian: np.ndarray,
    orders: Sequence[int],
    coefficients: Sequence[np.ndarray],
    time_value: float,
) -> np.ndarray:
    result = np.array(hamiltonian, copy=True, dtype=np.complex128)
    for order, coefficient in zip(orders, coefficients, strict=True):
        result += np.asarray(coefficient) * float(time_value) ** int(order)
    return (result + result.conj().T) / 2.0


def _phase_cut_margin(unitary: np.ndarray) -> float:
    phases = np.angle(np.linalg.eigvals(unitary))
    return float(np.min(np.pi - np.abs(phases)))


def continuous_effective_hamiltonian(
    system: dict[str, Any], sequence: Sequence[float], time_value: float
) -> dict[str, Any]:
    """Return the principal-log H_eff inside a checked phase-safe interval."""

    unitary = build_sector_pf_unitary(
        system["group_spectra"], sequence, float(time_value), method="s2-cache"
    )
    logarithm, estimate = logm(unitary, disp=False)
    raw_effective = logarithm / (1j * float(time_value))
    hermitian_effective = (raw_effective + raw_effective.conj().T) / 2.0
    return {
        "unitary": unitary,
        "effective_hamiltonian": hermitian_effective,
        "raw_hermiticity_residual_frobenius": float(
            np.linalg.norm(raw_effective - raw_effective.conj().T)
        ),
        "logm_error_estimate": float(estimate),
        "unitary_reconstruction_residual_frobenius": float(
            np.linalg.norm(expm(1j * float(time_value) * hermitian_effective) - unitary)
        ),
        "branch_cut_margin_radians": _phase_cut_margin(unitary),
    }


def _selected_energy(
    matrix: np.ndarray, reference_state: np.ndarray
) -> tuple[float, float]:
    energies, vectors = np.linalg.eigh(matrix)
    overlaps = np.abs(vectors.conj().T @ reference_state) ** 2
    selected = int(np.argmax(overlaps))
    return float(energies[selected]), float(overlaps[selected])


def _direct_pf_shift(
    unitary: np.ndarray,
    reference_state: np.ndarray,
    reference_energy: float,
    time_value: float,
) -> dict[str, float]:
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    eigenvalues = np.diag(triangular)
    overlaps = np.abs(vectors.conj().T @ reference_state) ** 2
    selected = int(np.argmax(overlaps))
    phase = float(np.angle(eigenvalues[selected]))
    unwrap = int(
        np.rint((float(reference_energy) * float(time_value) - phase) / (2.0 * np.pi))
    )
    effective_energy = (phase + 2.0 * np.pi * unwrap) / float(time_value)
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    return {
        "shift": float(effective_energy - reference_energy),
        "overlap_probability": float(overlaps[selected]),
        "unwrap_integer": unwrap,
        "eigenpair_residual": float(
            np.linalg.norm(unitary @ vector - eigenvalues[selected] * vector)
        ),
    }


def _log_interlaced_times(
    minimum: float, maximum: float, bins: int
) -> tuple[np.ndarray, np.ndarray]:
    edges = np.geomspace(float(minimum), float(maximum), int(bins) + 1)
    holdout = np.sqrt(edges[:-1] * edges[1:])
    return edges, holdout


def operator_decomposition(
    hamiltonian: np.ndarray,
    reference_state: np.ndarray,
    operator: np.ndarray,
    order: int,
) -> dict[str, Any]:
    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    overlaps = np.abs(eigenvectors.conj().T @ reference_state) ** 2
    selected = int(np.argmax(overlaps))
    transformed = eigenvectors.conj().T @ operator @ eigenvectors
    diagonal = np.diag(np.diag(transformed))
    off_diagonal = transformed - diagonal
    ground_expectation = complex(transformed[selected, selected])
    couplings = np.delete(transformed[:, selected], selected)
    centered_action = operator @ reference_state - ground_expectation * reference_state
    return {
        "order": int(order),
        "operator_frobenius_norm": float(np.linalg.norm(operator)),
        "operator_spectral_norm": float(np.linalg.norm(operator, 2)),
        "diagonal_frobenius_norm_in_h_basis": float(np.linalg.norm(diagonal)),
        "off_diagonal_frobenius_norm_in_h_basis": float(
            np.linalg.norm(off_diagonal)
        ),
        "ground_expectation_real": float(ground_expectation.real),
        "ground_expectation_imaginary": float(ground_expectation.imag),
        "ground_to_excited_coupling_norm": float(np.linalg.norm(couplings)),
        "centered_action_norm": float(np.linalg.norm(centered_action)),
        "selected_ground_index": selected,
        "selected_reference_overlap_probability": float(overlaps[selected]),
        "minimum_excitation_gap_hartree": float(
            min(
                abs(float(energy - energies[selected]))
                for index, energy in enumerate(energies)
                if index != selected
            )
        ),
    }


def _relative_matrix_error(value: np.ndarray, reference: np.ndarray) -> float:
    return float(
        np.linalg.norm(value - reference) / max(np.linalg.norm(reference), 1e-300)
    )


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in ("numpy", "scipy", "matplotlib", "mpmath", "pyscf", "openfermion"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _write_figure(path: Path, window_rows: Sequence[dict[str, Any]]) -> None:
    orders = (4, 6, 8)
    figure, axis = plt.subplots(figsize=(6.4, 4.0))
    for row in window_rows:
        values = [row[f"relative_error_d{order}"] for order in orders]
        axis.semilogy(orders, values, marker="o", label=row["window_id"])
    axis.axhline(
        PILOT_THRESHOLDS["fit_relative_error_d8"],
        color="black",
        linestyle="--",
        linewidth=0.9,
        label="D8 pilot threshold",
    )
    axis.set_xlabel("effective-Hamiltonian coefficient order")
    axis.set_ylabel("relative matrix error")
    axis.set_xticks(orders)
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    checks = audit["checks"]
    lines = [
        "# F01 effective-Hamiltonian pilot: H2 / Yoshida 4th",
        "",
        f"Status: **{audit['status']}**",
        "",
        "This is the local small-matrix gate for F01. It does not complete F01 "
        "for H4, multiple PFs, or the new HF hold-out failure.",
        "",
        "## Result",
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
            "## Finite-time matrix-log recovery",
            "",
            "| window | scaled cond. | rel. D4 | rel. D6 | rel. D8 | "
            "max holdout shift residual / epsilon |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    holdout_by_window: dict[str, list[dict[str, Any]]] = {}
    for row in audit["holdout_rows"]:
        holdout_by_window.setdefault(row["window_id"], []).append(row)
    for row in audit["window_rows"]:
        holdouts = holdout_by_window[row["window_id"]]
        lines.append(
            "| {window_id} | {condition_number:.4g} | {relative_error_d4:.3e} | "
            "{relative_error_d6:.3e} | {relative_error_d8:.3e} | {shift:.3e} |".format(
                **row,
                shift=max(item["shift_residual_over_epsilon"] for item in holdouts),
            )
        )
    d4 = next(row for row in audit["operator_rows"] if row["order"] == 4)
    lines.extend(
        [
            "",
            "## Leading operator",
            "",
            f"- `||D4||_F = {d4['operator_frobenius_norm']:.8e}`.",
            f"- `<0|D4|0> = {d4['ground_expectation_real']:.8e}`.",
            "- `||D4|0>-<D4>|0>|| = "
            f"{d4['centered_action_norm']:.8e}`.",
            "- The principal-log phase-cut margin stayed above "
            f"{audit['extrema']['minimum_branch_cut_margin_radians']:.6f} rad.",
            "",
            "The formal ordered-product logarithm is independent of finite-time "
            "PF eigenphase data. The numerical matrix-log fits use interlaced "
            "training/holdout times and recover D4, D6, and D8 in every declared "
            "window. D10 and D12 are retained as diagnostics but are not pilot "
            "pass criteria.",
            "",
            "## Decision",
            "",
        ]
    )
    if audit["passed"]:
        lines.append(
            "The H2/Yoshida-4 extraction gate passes. The next F01 step is the "
            "predeclared H2/H4 multi-PF comparison; F02 is not yet marked complete."
        )
    else:
        lines.append(
            "The extraction gate does not pass. Do not proceed to F02; diagnose "
            "the failed stability check first."
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `audit.json`: complete machine-readable result.",
            "- `precision_stability.csv`: formal-log precision comparison.",
            "- `window_recovery.csv`: coefficient recovery by time window.",
            "- `holdout_reconstruction.csv`: unseen-time matrix/eigenvalue checks.",
            "- `operator_decomposition.csv`: H-eigenbasis diagonal/off-diagonal data.",
            "- `coefficient_recovery.png`: lightweight recovery summary.",
            "- `manifest.json`: source and runtime provenance.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    system = _prepare_sector_system(2)
    matrices = group_matrices(system)
    hamiltonian = sum(matrices, np.zeros_like(matrices[0]))
    reference_state = np.asarray(system["ground_state"], dtype=np.complex128)
    reference_energy = float(system["ground_energy_without_constant_hartree"])
    sequence = tuple(float(value) for value in symmetric_s2_sequence(yoshida_4th_list()))
    steps = list(iter_s2_sequence_steps(len(matrices), sequence))

    references: dict[int, list[np.ndarray]] = {}
    for digits in REFERENCE_DIGITS:
        references[digits] = effective_hamiltonian_series(
            matrices,
            steps,
            maximum_effective_order=max(FIT_ORDERS),
            decimal_digits=digits,
        )["effective_hamiltonian"]
    reference = references[max(REFERENCE_DIGITS)]

    precision_rows: list[dict[str, Any]] = []
    for digits in REFERENCE_DIGITS[:-1]:
        for order in (4, 6, 8):
            precision_rows.append(
                {
                    "decimal_digits": digits,
                    "reference_decimal_digits": max(REFERENCE_DIGITS),
                    "order": order,
                    "relative_matrix_difference": _relative_matrix_error(
                        references[digits][order], reference[order]
                    ),
                }
            )

    window_rows: list[dict[str, Any]] = []
    holdout_rows: list[dict[str, Any]] = []
    fitted_by_window: dict[str, list[np.ndarray]] = {}
    all_log_records: list[dict[str, Any]] = []
    for specification in FIT_WINDOWS:
        training_times, holdout_times = _log_interlaced_times(
            specification["minimum"],
            specification["maximum"],
            specification["bins"],
        )
        corrections = []
        for time_value in training_times:
            result = continuous_effective_hamiltonian(system, sequence, float(time_value))
            corrections.append(result["effective_hamiltonian"] - hamiltonian)
            all_log_records.append(result)
        fit = fit_even_effective_operators(
            training_times, np.asarray(corrections), FIT_ORDERS
        )
        fitted_by_window[specification["window_id"]] = fit["coefficients"]
        row: dict[str, Any] = {
            "window_id": specification["window_id"],
            "minimum_time": specification["minimum"],
            "maximum_time": specification["maximum"],
            "training_point_count": int(training_times.size),
            "holdout_point_count": int(holdout_times.size),
            "condition_number": fit["condition_number"],
            "training_residual_frobenius_max": fit[
                "training_residual_frobenius_max"
            ],
        }
        for index, order in enumerate(FIT_ORDERS):
            row[f"relative_error_d{order}"] = _relative_matrix_error(
                fit["coefficients"][index], reference[order]
            )
        window_rows.append(row)

        for time_value in holdout_times:
            direct = continuous_effective_hamiltonian(
                system, sequence, float(time_value)
            )
            predicted = evaluate_operator_polynomial(
                hamiltonian,
                fit["orders"],
                fit["coefficients"],
                float(time_value),
            )
            direct_energy, direct_overlap = _selected_energy(
                direct["effective_hamiltonian"], reference_state
            )
            predicted_energy, predicted_overlap = _selected_energy(
                predicted, reference_state
            )
            pf_shift = _direct_pf_shift(
                direct["unitary"],
                reference_state,
                reference_energy,
                float(time_value),
            )
            direct_shift = direct_energy - reference_energy
            predicted_shift = predicted_energy - reference_energy
            correction_norm = np.linalg.norm(
                direct["effective_hamiltonian"] - hamiltonian
            )
            holdout_rows.append(
                {
                    "window_id": specification["window_id"],
                    "time_hartree_inverse": float(time_value),
                    "matrix_residual_frobenius": float(
                        np.linalg.norm(predicted - direct["effective_hamiltonian"])
                    ),
                    "matrix_residual_relative_to_correction": float(
                        np.linalg.norm(predicted - direct["effective_hamiltonian"])
                        / max(float(correction_norm), 1e-300)
                    ),
                    "unitary_from_predicted_heff_residual_frobenius": float(
                        np.linalg.norm(
                            expm(1j * float(time_value) * predicted)
                            - direct["unitary"]
                        )
                    ),
                    "direct_heff_shift_hartree": direct_shift,
                    "predicted_heff_shift_hartree": predicted_shift,
                    "direct_pf_shift_hartree": pf_shift["shift"],
                    "heff_vs_pf_shift_residual_hartree": float(
                        abs(direct_shift - pf_shift["shift"])
                    ),
                    "shift_residual_hartree": float(
                        abs(predicted_shift - pf_shift["shift"])
                    ),
                    "shift_residual_over_epsilon": float(
                        abs(predicted_shift - pf_shift["shift"])
                        / float(TARGET_ERROR)
                    ),
                    "direct_ground_overlap_probability": direct_overlap,
                    "predicted_ground_overlap_probability": predicted_overlap,
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
                    "principal_log_unitary_reconstruction_frobenius": direct[
                        "unitary_reconstruction_residual_frobenius"
                    ],
                }
            )
            all_log_records.append(direct)

    pairwise_d8 = []
    for left_index, left in enumerate(FIT_WINDOWS):
        for right in FIT_WINDOWS[left_index + 1 :]:
            left_d8 = fitted_by_window[left["window_id"]][FIT_ORDERS.index(8)]
            right_d8 = fitted_by_window[right["window_id"]][FIT_ORDERS.index(8)]
            pairwise_d8.append(
                _relative_matrix_error(left_d8, right_d8)
            )

    operator_rows = [
        operator_decomposition(
            hamiltonian, reference_state, reference[order], order
        )
        for order in (4, 6, 8)
    ]
    forbidden_orders = (1, 2, 3, 5, 7, 9, 11)
    extrema = {
        "h0_frobenius_error": float(np.linalg.norm(reference[0] - hamiltonian)),
        "forbidden_order_max_frobenius": float(
            max(np.linalg.norm(reference[order]) for order in forbidden_orders)
        ),
        "precision_relative_difference_d4_d6_d8": float(
            max(row["relative_matrix_difference"] for row in precision_rows)
        ),
        "fit_relative_error_d4": float(
            max(row["relative_error_d4"] for row in window_rows)
        ),
        "fit_relative_error_d6": float(
            max(row["relative_error_d6"] for row in window_rows)
        ),
        "fit_relative_error_d8": float(
            max(row["relative_error_d8"] for row in window_rows)
        ),
        "window_pair_relative_difference_d8": float(max(pairwise_d8)),
        "log_unitary_reconstruction_frobenius": float(
            max(
                record["unitary_reconstruction_residual_frobenius"]
                for record in all_log_records
            )
        ),
        "minimum_branch_cut_margin_radians": float(
            min(record["branch_cut_margin_radians"] for record in all_log_records)
        ),
        "holdout_shift_residual_over_epsilon": float(
            max(row["shift_residual_over_epsilon"] for row in holdout_rows)
        ),
    }

    checks = []
    for check_id, threshold in PILOT_THRESHOLDS.items():
        measured = extrema[check_id]
        if check_id == "minimum_branch_cut_margin_radians":
            passed = measured >= threshold
        else:
            passed = measured <= threshold
        checks.append(
            {
                "check_id": check_id,
                "measured": measured,
                "threshold": threshold,
                "comparison": ">=" if check_id == "minimum_branch_cut_margin_radians" else "<=",
                "passed": bool(passed),
            }
        )
    passed = all(check["passed"] for check in checks)
    audit = {
        "schema": "prevalidation_f01_effective_hamiltonian_pilot_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete" if passed else "complete_with_findings",
        "passed": passed,
        "scope": {
            "catalog_item": "F01 pilot only",
            "system": "H2/STO-3G repository H-chain instance",
            "formula": "Yoshida 4th",
            "formal_order": 4,
            "sector_dimension": int(reference_state.size),
            "number_of_groups": len(matrices),
            "sign_convention": "U_PF(t)=exp(+i t H_eff(t))",
            "not_completed": ["H4", "multi-PF F01", "F02", "F05", "HF failure"],
        },
        "protocol": {
            "reference_decimal_digits": list(REFERENCE_DIGITS),
            "fit_orders": list(FIT_ORDERS),
            "fit_windows": FIT_WINDOWS,
            "training_holdout_rule": "log-bin edges for training; geometric midpoints for holdout",
            "finite_time_logarithm": "SciPy principal matrix log inside explicitly checked branch-cut margin",
            "thresholds": PILOT_THRESHOLDS,
        },
        "checks": checks,
        "extrema": extrema,
        "precision_rows": precision_rows,
        "window_rows": window_rows,
        "holdout_rows": holdout_rows,
        "operator_rows": operator_rows,
        "reference_coefficients": {
            str(order): {
                "matrix": reference[order],
                "frobenius_norm": float(np.linalg.norm(reference[order])),
                "hermiticity_residual_frobenius": float(
                    np.linalg.norm(reference[order] - reference[order].conj().T)
                ),
            }
            for order in (0, 4, 6, 8, 10, 12)
        },
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "precision_stability.csv", precision_rows)
    _write_csv(output_dir / "window_recovery.csv", window_rows)
    _write_csv(output_dir / "holdout_reconstruction.csv", holdout_rows)
    _write_csv(output_dir / "operator_decomposition.csv", operator_rows)
    _write_figure(output_dir / "coefficient_recovery.png", window_rows)

    source_paths = [
        Path(__file__),
        Path("review_response/bch_matrix_series.py"),
        Path("review_response/validate_hchain_perturbative_estimator.py"),
        Path("src/trotterlib/pf_decomposition.py"),
        Path("src/trotterlib/product_formula.py"),
        Path("src/trotterlib/sector_pf.py"),
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
        "source_sha256": {
            str(path): _sha256(path) for path in source_paths
        },
        "output_directory": str(output_dir),
        "runtime": audit["runtime"],
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    _write_report(output_dir / "report.md", audit)
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
