"""Sweep finite-time PF errors and track the ground-connected eigenbranch.

This is a small-system calibration run for H6/H7.  At each fraction of the
short-time-model analytic optimum it compares

* the leading model ``alpha * t**p``;
* the phase of one ground-state overlap; and
* direct diagonalization of the PF unitary in the conserved population sector.

The direct calculation reports both the maximum-ground-overlap eigenbranch at
each time and a branch connected between adjacent times by eigenvector overlap.
The latter prevents an avoided crossing or a maximum-overlap branch switch from
being mistaken for a failure of the asymptotic power law.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.linalg import schur

from run_large_hchain_moment_phase import (
    DEFAULT_M5_TIMES,
    DEFAULT_Y8_TIMES,
    M5_LABEL,
    Y8_LABEL,
    _cost,
    _fit_short_time,
    _prepare_sparse_sector_system,
)
from trotterlib.config import DECOMPO_NUM, pf_order
from trotterlib.cost_validation import analytic_optimal_time
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.sector_pf import build_sector_pf_unitary


DEFAULT_RELATIVE_TIMES = (0.2, 0.35, 0.5, 0.7, 0.85, 1.0, 1.15)
FORMULA_LABELS = {
    "m5": M5_LABEL,
    "y8": Y8_LABEL,
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _build_pf_unitary(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    build_method: str = "s2-cache",
) -> np.ndarray:
    return build_sector_pf_unitary(
        system["group_spectra"],
        _get_s2_sequence(label),
        evolution_time,
        method=build_method,
    )


def _principal_energy_shifts(
    eigenvalues: np.ndarray, reference_energy: float, evolution_time: float
) -> np.ndarray:
    rotated = np.exp(-1j * reference_energy * evolution_time) * eigenvalues
    return np.angle(rotated) / evolution_time


def _unwrap_energy_shift(
    principal_shift: float, previous_shift: float | None, evolution_time: float
) -> float:
    if previous_shift is None:
        return float(principal_shift)
    period = 2.0 * np.pi / evolution_time
    winding = round((previous_shift - principal_shift) / period)
    return float(principal_shift + winding * period)


def _effective_orders(
    points: Sequence[dict[str, Any]], error_key: str
) -> list[dict[str, float]]:
    estimates: list[dict[str, float]] = []
    for left, right in zip(points[:-1], points[1:]):
        left_error = float(left[error_key])
        right_error = float(right[error_key])
        if left_error <= 0.0 or right_error <= 0.0:
            continue
        left_time = float(left["time"])
        right_time = float(right["time"])
        estimates.append(
            {
                "left_time": left_time,
                "right_time": right_time,
                "geometric_midpoint_time": float(
                    np.sqrt(left_time * right_time)
                ),
                "effective_order": float(
                    np.log(right_error / left_error)
                    / np.log(right_time / left_time)
                ),
            }
        )
    return estimates


def _direct_point(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    model_error: float,
    epsilon_e: float,
    previous_vector: np.ndarray | None,
    previous_unwrapped_shift: float | None,
    build_method: str,
) -> tuple[dict[str, Any], np.ndarray, float]:
    started = time.perf_counter()
    build_started = time.perf_counter()
    unitary = _build_pf_unitary(
        system, label, evolution_time, build_method=build_method
    )
    unitary_build_seconds = time.perf_counter() - build_started
    dimension = unitary.shape[0]
    state = np.asarray(system["state"], dtype=complex)
    reference_energy = float(system["energy"])

    overlap = complex(np.vdot(state, unitary @ state))
    rotated_overlap = np.exp(-1j * reference_energy * evolution_time) * overlap
    signed_phase_shift = float(np.angle(rotated_overlap) / evolution_time)
    signed_perturbative_shift = float(rotated_overlap.imag / evolution_time)
    phase_error = abs(signed_phase_shift)
    perturbative_error = abs(signed_perturbative_shift)

    triangular, eigenvectors = schur(
        unitary, output="complex", check_finite=False
    )
    eigenvalues = np.diag(triangular)
    ground_overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
    maximum_ground_index = int(np.argmax(ground_overlaps))

    if previous_vector is None:
        tracked_index = maximum_ground_index
        tracked_to_previous_overlap = None
    else:
        continuation_overlaps = (
            np.abs(eigenvectors.conj().T @ previous_vector) ** 2
        )
        tracked_index = int(np.argmax(continuation_overlaps))
        tracked_to_previous_overlap = float(
            continuation_overlaps[tracked_index]
        )

    shifts = _principal_energy_shifts(
        eigenvalues, reference_energy, evolution_time
    )
    maximum_ground_shift = float(shifts[maximum_ground_index])
    tracked_principal_shift = float(shifts[tracked_index])
    tracked_unwrapped_shift = _unwrap_energy_shift(
        tracked_principal_shift,
        previous_unwrapped_shift,
        evolution_time,
    )
    n_exp = int(DECOMPO_NUM[f"H{system['h_chain']}"][label])

    leading_indices = np.argsort(ground_overlaps)[::-1][
        : min(6, dimension)
    ]
    point = {
        "time": float(evolution_time),
        "model_error_hartree": float(model_error),
        "one_overlap_phase_error_hartree": phase_error,
        "one_overlap_perturbative_error_hartree": perturbative_error,
        "one_overlap_signed_phase_shift_hartree": signed_phase_shift,
        "one_overlap_signed_perturbative_shift_hartree": (
            signed_perturbative_shift
        ),
        "one_overlap_survival_probability": float(abs(rotated_overlap) ** 2),
        "one_overlap_phase_to_model_ratio": float(phase_error / model_error),
        "maximum_ground_overlap_branch": {
            "schur_index": maximum_ground_index,
            "ground_overlap_probability": float(
                ground_overlaps[maximum_ground_index]
            ),
            "energy_shift_hartree": maximum_ground_shift,
            "direct_error_hartree": abs(maximum_ground_shift),
            "direct_to_model_ratio": float(
                abs(maximum_ground_shift) / model_error
            ),
            "cost": _cost(
                abs(maximum_ground_shift),
                evolution_time,
                n_exp,
                epsilon_e,
            ),
        },
        "continuously_tracked_branch": {
            "schur_index": tracked_index,
            "ground_overlap_probability": float(ground_overlaps[tracked_index]),
            "overlap_with_previous_probability": tracked_to_previous_overlap,
            "principal_energy_shift_hartree": tracked_principal_shift,
            "unwrapped_energy_shift_hartree": tracked_unwrapped_shift,
            "direct_error_hartree": abs(tracked_unwrapped_shift),
            "direct_to_model_ratio": float(
                abs(tracked_unwrapped_shift) / model_error
            ),
            "cost": _cost(
                abs(tracked_unwrapped_shift),
                evolution_time,
                n_exp,
                epsilon_e,
            ),
        },
        "leading_ground_overlap_branches": [
            {
                "schur_index": int(index),
                "ground_overlap_probability": float(ground_overlaps[index]),
                "principal_energy_shift_hartree": float(shifts[index]),
            }
            for index in leading_indices
        ],
        "unitarity_residual_frobenius_norm": float(
            np.linalg.norm(unitary.conj().T @ unitary - np.eye(dimension))
        ),
        "schur_off_diagonal_residual_frobenius_norm": float(
            np.linalg.norm(triangular - np.diag(eigenvalues))
        ),
        "elapsed_seconds": float(time.perf_counter() - started),
        "unitary_build_seconds": float(unitary_build_seconds),
        "unitary_build_method": build_method,
    }
    return point, eigenvectors[:, tracked_index].copy(), tracked_unwrapped_shift


def _flatten_direct_error(
    points: Sequence[dict[str, Any]], branch_key: str
) -> list[dict[str, Any]]:
    return [
        {
            **point,
            "selected_direct_error_hartree": float(
                point[branch_key]["direct_error_hartree"]
            ),
        }
        for point in points
    ]


def run(
    h_chains: Sequence[int],
    formula_keys: Sequence[str],
    relative_times: Sequence[float],
    m5_fit_times: Sequence[float],
    y8_fit_times: Sequence[float],
    min_fit_error: float,
    epsilon_e: float,
    output: Path,
    unitary_build_method: str = "s2-cache",
) -> dict[str, Any]:
    relative_grid = sorted({float(value) for value in relative_times})
    if not relative_grid or relative_grid[0] <= 0.0:
        raise ValueError("relative times must be positive")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "purpose": (
            "H6/H7 direct finite-time PF scaling and continuous eigenbranch "
            "tracking calibration"
        ),
        "epsilon_E_hartree": float(epsilon_e),
        "relative_times": relative_grid,
        "formula_keys": list(formula_keys),
        "unitary_build_method": unitary_build_method,
        "results": {},
    }
    _write_json(output, payload)

    for h_chain in h_chains:
        system_started = time.perf_counter()
        print(f"prepare H{h_chain}", flush=True)
        system = _prepare_sparse_sector_system(int(h_chain))
        system_result: dict[str, Any] = {
            "system": {
                "h_chain": int(h_chain),
                "ham_name": system["ham_name"],
                "num_qubits": int(system["num_qubits"]),
                "num_groups": int(system["num_groups"]),
                "ground_energy_without_constant_hartree": float(
                    system["energy"]
                ),
                "sector": system["sector"],
                "preparation_seconds": float(system["preparation_seconds"]),
            },
            "results": {},
            "elapsed_seconds": None,
        }
        payload["results"][f"H{h_chain}"] = system_result
        _write_json(output, payload)

        print(
            f"H{h_chain}: {system['num_qubits']} qubits, "
            f"sector dimension {system['sector']['dimension']}",
            flush=True,
        )
        fit_times_by_label = {
            M5_LABEL: m5_fit_times,
            Y8_LABEL: y8_fit_times,
        }
        for formula_key in formula_keys:
            label = FORMULA_LABELS[formula_key]
            fit_times = fit_times_by_label[label]
            fit = _fit_short_time(system, label, fit_times, min_fit_error)
            alpha = float(fit["fixed_order_alpha"])
            order = int(pf_order(label))
            analytic_time = float(
                analytic_optimal_time(alpha, order, epsilon_e)
            )
            formula_result: dict[str, Any] = {
                "label": label,
                "formal_order": order,
                "fixed_order_alpha": alpha,
                "short_time_fit": fit,
                "analytic_optimal_time": analytic_time,
                "points": [],
                "effective_orders": {},
                "elapsed_seconds": None,
            }
            system_result["results"][label] = formula_result
            _write_json(output, payload)

            formula_started = time.perf_counter()
            previous_vector: np.ndarray | None = None
            previous_shift: float | None = None
            for relative_time in relative_grid:
                evolution_time = relative_time * analytic_time
                model_error = alpha * evolution_time**order
                print(
                    f"H{h_chain} {label}: t/t_analytic={relative_time:g}, "
                    f"t={evolution_time:.9g}",
                    flush=True,
                )
                point, previous_vector, previous_shift = _direct_point(
                    system,
                    label,
                    evolution_time,
                    model_error,
                    epsilon_e,
                    previous_vector,
                    previous_shift,
                    unitary_build_method,
                )
                point["relative_to_analytic_time"] = relative_time
                formula_result["points"].append(point)
                formula_result["elapsed_seconds"] = float(
                    time.perf_counter() - formula_started
                )
                system_result["elapsed_seconds"] = float(
                    time.perf_counter() - system_started
                )
                _write_json(output, payload)

            points = formula_result["points"]
            formula_result["effective_orders"] = {
                "one_overlap_phase": _effective_orders(
                    points, "one_overlap_phase_error_hartree"
                ),
                "maximum_ground_overlap_direct": _effective_orders(
                    _flatten_direct_error(
                        points, "maximum_ground_overlap_branch"
                    ),
                    "selected_direct_error_hartree",
                ),
                "continuously_tracked_direct": _effective_orders(
                    _flatten_direct_error(
                        points, "continuously_tracked_branch"
                    ),
                    "selected_direct_error_hartree",
                ),
            }
            formula_result["elapsed_seconds"] = float(
                time.perf_counter() - formula_started
            )
            _write_json(output, payload)

        system_result["elapsed_seconds"] = float(
            time.perf_counter() - system_started
        )
        _write_json(output, payload)

    payload["status"] = "complete"
    _write_json(output, payload)
    print(f"saved: {output}", flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-chains", nargs="+", type=int, default=[6, 7])
    parser.add_argument(
        "--formulas",
        nargs="+",
        choices=sorted(FORMULA_LABELS),
        default=sorted(FORMULA_LABELS),
    )
    parser.add_argument(
        "--relative-times",
        nargs="+",
        type=float,
        default=list(DEFAULT_RELATIVE_TIMES),
    )
    parser.add_argument(
        "--m5-fit-times",
        nargs="+",
        type=float,
        default=list(DEFAULT_M5_TIMES),
    )
    parser.add_argument(
        "--y8-fit-times",
        nargs="+",
        type=float,
        default=list(DEFAULT_Y8_TIMES),
    )
    parser.add_argument("--min-fit-error", type=float, default=5e-12)
    parser.add_argument(
        "--epsilon-e", type=float, default=0.00015936001019904
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/server_cost_validity/"
            "direct_scaling_sweep_H6_H7.json"
        ),
    )
    parser.add_argument(
        "--unitary-build-method",
        choices=["sequential", "s2-cache"],
        default="s2-cache",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        args.h_chains,
        args.formulas,
        args.relative_times,
        args.m5_fit_times,
        args.y8_fit_times,
        args.min_fit_error,
        args.epsilon_e,
        args.output,
        args.unitary_build_method,
    )


if __name__ == "__main__":
    main()
