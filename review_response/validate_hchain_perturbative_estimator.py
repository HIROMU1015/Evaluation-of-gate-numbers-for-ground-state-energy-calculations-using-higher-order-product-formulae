"""Compare H-chain PF perturbative errors with sector diagonalization."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from openfermion.linalg import get_sparse_operator
from openfermion.ops import QubitOperator
from scipy.linalg import eigh

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.analysis_utils import loglog_average_coeff
from trotterlib.fit_window import estimate_gpu_noise_floor
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.product_formula import _get_s2_sequence


FOURTH_PAIR = ("4th(new_2)", "4th(m5_best)")
EIGHTH_PAIR = ("8th(Morales)", "8th(Morales-Y8m10b)")


def _as_group_operator(group: Any) -> QubitOperator:
    if isinstance(group, QubitOperator):
        return group
    result = QubitOperator()
    for operator in group:
        result += operator
    return result


def _basis_indices(
    num_qubits: int,
    ground_state: np.ndarray,
    full_group_matrices: Sequence[np.ndarray],
) -> tuple[np.ndarray, dict[str, Any]]:
    support = np.flatnonzero(np.abs(ground_state) > 1e-12)
    all_indices = np.arange(1 << num_qubits)
    bitstrings = [format(index, f"0{num_qubits}b") for index in all_indices]
    candidates: list[tuple[str, tuple[int, ...], np.ndarray]] = []

    half = num_qubits // 2
    support_half_counts = {
        (
            bitstrings[int(index)][:half].count("1"),
            bitstrings[int(index)][half:].count("1"),
        )
        for index in support
    }
    if len(support_half_counts) == 1:
        counts = next(iter(support_half_counts))
        indices = np.asarray(
            [
                index
                for index, bits in enumerate(bitstrings)
                if (
                    bits[:half].count("1"),
                    bits[half:].count("1"),
                )
                == counts
            ],
            dtype=int,
        )
        candidates.append(("fixed_half_populations", counts, indices))

    support_total_counts = {
        bitstrings[int(index)].count("1") for index in support
    }
    if len(support_total_counts) == 1:
        total = next(iter(support_total_counts))
        indices = np.asarray(
            [
                index
                for index, bits in enumerate(bitstrings)
                if bits.count("1") == total
            ],
            dtype=int,
        )
        candidates.append(("fixed_total_population", (total,), indices))

    candidates.append(("full_hilbert_space", (), all_indices))
    for kind, counts, indices in candidates:
        outside = np.setdiff1d(all_indices, indices)
        leakage = max(
            (
                float(np.linalg.norm(matrix[np.ix_(outside, indices)]))
                for matrix in full_group_matrices
            ),
            default=0.0,
        )
        state_outside_norm = float(
            np.linalg.norm(ground_state[outside]) if outside.size else 0.0
        )
        if leakage <= 1e-11 and state_outside_norm <= 1e-11:
            return indices, {
                "kind": kind,
                "population_counts": list(counts),
                "dimension": int(indices.size),
                "max_group_leakage_frobenius_norm": leakage,
                "ground_state_outside_norm": state_outside_norm,
            }
    raise RuntimeError("No invariant basis sector contains the ground state")


def _prepare_sector_system(h_chain: int) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        system = _prepare_system(h_chain)
    num_qubits = int(system["num_qubits"])
    ground_state = np.asarray(system["state"], dtype=complex).reshape(-1)
    group_operators = [_as_group_operator(group) for group in system["groups"]]
    identity = np.eye(1 << num_qubits)
    full_group_matrices = []
    for operator in group_operators:
        constant = operator.terms.get((), 0.0)
        matrix = get_sparse_operator(operator, num_qubits).toarray()
        full_group_matrices.append(matrix - constant * identity)

    indices, sector = _basis_indices(
        num_qubits, ground_state, full_group_matrices
    )
    sector_state = ground_state[indices]
    sector_state /= np.linalg.norm(sector_state)
    group_matrices = [
        matrix[np.ix_(indices, indices)] for matrix in full_group_matrices
    ]
    group_spectra = [eigh(matrix) for matrix in group_matrices]
    hamiltonian = sum(group_matrices, np.zeros_like(group_matrices[0]))
    energy = float(system["energy_without_constant"])
    residual = float(np.linalg.norm(hamiltonian @ sector_state - energy * sector_state))
    sector["ground_state_eigenpair_residual"] = residual
    if residual > 1e-9:
        raise RuntimeError(f"H{h_chain} sector ground-state residual is {residual}")

    return {
        "ham_name": system["ham_name"],
        "num_qubits": num_qubits,
        "num_groups": len(group_matrices),
        "ground_energy_without_constant_hartree": energy,
        "ground_state": sector_state,
        "group_spectra": group_spectra,
        "sector": sector,
    }


def _direct_point(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    *,
    previous_eigenvector: np.ndarray | None,
    previous_effective_energy: float | None,
) -> tuple[dict[str, Any], np.ndarray, float]:
    state = system["ground_state"]
    energy = float(system["ground_energy_without_constant_hartree"])
    dimension = state.size
    unitary = np.eye(dimension, dtype=complex)
    for group_index, weight in iter_s2_sequence_steps(
        int(system["num_groups"]), _get_s2_sequence(label)
    ):
        values, vectors = system["group_spectra"][group_index]
        phases = np.exp(1j * evolution_time * weight * values)
        unitary = ((vectors * phases) @ vectors.conj().T) @ unitary

    eigenvalues, eigenvectors = np.linalg.eig(unitary)
    eigenvectors /= np.linalg.norm(eigenvectors, axis=0)
    ground_overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
    tracking_reference = (
        state if previous_eigenvector is None else previous_eigenvector
    )
    tracking_overlaps = np.abs(
        eigenvectors.conj().T @ tracking_reference
    ) ** 2
    selected = int(np.argmax(tracking_overlaps))
    raw_phase = float(np.angle(eigenvalues[selected]))
    branch_reference_energy = (
        energy
        if previous_effective_energy is None
        else previous_effective_energy
    )
    branch = int(
        np.rint(
            (branch_reference_energy * evolution_time - raw_phase)
            / (2 * np.pi)
        )
    )
    effective_energy = (raw_phase + 2 * np.pi * branch) / evolution_time
    direct_error = abs(float(effective_energy - energy))

    evolved = unitary @ state
    phase_rotated_overlap = (
        np.exp(-1j * energy * evolution_time) * np.vdot(state, evolved)
    )
    perturbative_error = abs(float(phase_rotated_overlap.imag / evolution_time))
    overlap_phase_error = abs(
        float(np.angle(phase_rotated_overlap) / evolution_time)
    )
    unitarity_residual = float(
        np.linalg.norm(unitary.conj().T @ unitary - np.eye(dimension))
    )
    point = {
        "direct_error_hartree": direct_error,
        "matrix_perturbative_error_hartree": perturbative_error,
        "matrix_overlap_phase_error_hartree": overlap_phase_error,
        "selected_effective_energy_hartree": float(effective_energy),
        "selected_ground_state_overlap_probability": float(
            ground_overlaps[selected]
        ),
        "tracking_overlap_probability": float(tracking_overlaps[selected]),
        "ground_state_survival_probability": float(abs(phase_rotated_overlap) ** 2),
        "raw_eigenphase_radians": raw_phase,
        "phase_branch_integer": branch,
        "phase_branch_reference_energy_hartree": float(
            branch_reference_energy
        ),
        "phase_branch_margin_hartree": float(
            np.pi / evolution_time
            - abs(effective_energy - branch_reference_energy)
        ),
        "effective_energy_step_change_hartree": (
            None
            if previous_effective_energy is None
            else float(effective_energy - previous_effective_energy)
        ),
        "unitarity_residual_frobenius_norm": unitarity_residual,
    }
    return point, eigenvectors[:, selected], float(effective_energy)


def _direct_points(
    system: dict[str, Any], label: str, times: np.ndarray
) -> list[dict[str, Any]]:
    if np.any(np.diff(times) <= 0):
        raise ValueError("Direct-diagonalization times must be strictly increasing")
    previous_eigenvector = None
    previous_effective_energy = None
    points = []
    for evolution_time in times:
        point, previous_eigenvector, previous_effective_energy = _direct_point(
            system,
            label,
            float(evolution_time),
            previous_eigenvector=previous_eigenvector,
            previous_effective_energy=previous_effective_energy,
        )
        points.append(point)
    return points


def _noise_floors(path: Path | None, h_chain: int) -> dict[str, float]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        label: float(result["noise_floor_hartree"])
        for label, result in payload["results"][f"H{h_chain}"].items()
    }


def run_validation(
    sweep_paths: Sequence[Path],
    *,
    noise_analysis_path: Path | None,
    relative_difference_threshold: float,
    alpha_difference_threshold: float,
    cost_ratio_difference_threshold: float,
) -> dict[str, Any]:
    payloads = [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sweep_paths
    ]
    h_chains = {int(payload["system"]["h_chain"]) for _, payload in payloads}
    if len(h_chains) != 1:
        raise ValueError("All sweep JSON files must describe one H-chain")
    h_chain = next(iter(h_chains))
    system = _prepare_sector_system(h_chain)
    external_floors = _noise_floors(noise_analysis_path, h_chain)

    results: dict[str, Any] = {}
    for source_path, payload in payloads:
        times = np.asarray(payload["calculation"]["times"], dtype=float)
        for sweep_result in payload["results"]:
            label = str(sweep_result["label"])
            gpu_errors = np.asarray(sweep_result["errors_hartree"], dtype=float)
            points = _direct_points(system, label, times)
            direct_errors = np.asarray(
                [point["direct_error_hartree"] for point in points]
            )
            matrix_perturbative = np.asarray(
                [point["matrix_perturbative_error_hartree"] for point in points]
            )
            floor = external_floors.get(label)
            floor_kind = "external_paired_cpu_gpu_floor"
            if floor is None:
                floor = estimate_gpu_noise_floor(matrix_perturbative, direct_errors)
                floor_kind = "scaled_direct_matrix_perturbative_difference"
            reliable = (gpu_errors > floor) & (direct_errors > floor)
            if np.count_nonzero(reliable) < 2:
                raise RuntimeError(f"{label}: fewer than two reliable points")

            relative = np.full(times.shape, np.nan)
            relative[reliable] = (
                np.abs(gpu_errors[reliable] - direct_errors[reliable])
                / direct_errors[reliable]
            )
            formal_order = int(sweep_result["formal_order"])
            direct_alpha = loglog_average_coeff(
                times[reliable],
                direct_errors[reliable],
                formal_order,
                mask_nonpositive=False,
            )
            perturbative_alpha = loglog_average_coeff(
                times[reliable],
                gpu_errors[reliable],
                formal_order,
                mask_nonpositive=False,
            )
            alpha_relative_difference = abs(
                perturbative_alpha / direct_alpha - 1.0
            )
            result = {
                "label": label,
                "formal_order": formal_order,
                "source": str(source_path),
                "times": times.tolist(),
                "gpu_perturbative_errors_hartree": gpu_errors.tolist(),
                "direct_errors_hartree": direct_errors.tolist(),
                "matrix_perturbative_errors_hartree": matrix_perturbative.tolist(),
                "noise_floor_hartree": float(floor),
                "noise_floor_kind": floor_kind,
                "reliable_mask": reliable.tolist(),
                "relative_differences": [
                    float(value) if np.isfinite(value) else None
                    for value in relative
                ],
                "max_relative_difference": float(np.nanmax(relative)),
                "median_relative_difference": float(np.nanmedian(relative)),
                "direct_fixed_order_alpha": float(direct_alpha),
                "perturbative_fixed_order_alpha": float(perturbative_alpha),
                "alpha_relative_difference": float(alpha_relative_difference),
                "max_gpu_matrix_perturbative_absolute_difference": float(
                    np.max(np.abs(gpu_errors - matrix_perturbative))
                ),
                "minimum_selected_ground_state_overlap_probability": float(
                    min(
                        point["selected_ground_state_overlap_probability"]
                        for point in points
                    )
                ),
                "minimum_tracking_overlap_probability": float(
                    min(point["tracking_overlap_probability"] for point in points)
                ),
                "minimum_phase_branch_margin_hartree": float(
                    min(point["phase_branch_margin_hartree"] for point in points)
                ),
                "maximum_unitarity_residual_frobenius_norm": float(
                    max(
                        point["unitarity_residual_frobenius_norm"]
                        for point in points
                    )
                ),
                "points": points,
                "passes_relative_difference_threshold": bool(
                    np.nanmax(relative) <= relative_difference_threshold
                ),
                "passes_alpha_difference_threshold": bool(
                    alpha_relative_difference <= alpha_difference_threshold
                ),
                "pauli_rotations_per_step": int(
                    sweep_result["pauli_rotations_per_step"]
                ),
            }
            results[label] = result

    pair_comparisons: dict[str, Any] = {}
    for old_label, new_label in (FOURTH_PAIR, EIGHTH_PAIR):
        if old_label not in results or new_label not in results:
            continue
        old = results[old_label]
        new = results[new_label]
        order = int(old["formal_order"])
        direct_ratio = (
            new["pauli_rotations_per_step"] / old["pauli_rotations_per_step"]
        ) * (new["direct_fixed_order_alpha"] / old["direct_fixed_order_alpha"]) ** (
            1.0 / order
        )
        perturbative_ratio = (
            new["pauli_rotations_per_step"] / old["pauli_rotations_per_step"]
        ) * (
            new["perturbative_fixed_order_alpha"]
            / old["perturbative_fixed_order_alpha"]
        ) ** (
            1.0 / order
        )
        relative_difference = abs(perturbative_ratio / direct_ratio - 1.0)
        pair_comparisons[f"{new_label} / {old_label}"] = {
            "formal_order": order,
            "direct_fixed_target_pf_cost_ratio": float(direct_ratio),
            "perturbative_fixed_target_pf_cost_ratio": float(perturbative_ratio),
            "relative_difference": float(relative_difference),
            "passes_cost_ratio_difference_threshold": bool(
                relative_difference <= cost_ratio_difference_threshold
            ),
        }

    criteria = {
        "max_pointwise_relative_difference": relative_difference_threshold,
        "max_alpha_relative_difference": alpha_difference_threshold,
        "max_pair_cost_ratio_relative_difference": cost_ratio_difference_threshold,
    }
    overall_pass = all(
        result["passes_relative_difference_threshold"]
        and result["passes_alpha_difference_threshold"]
        for result in results.values()
    ) and all(
        comparison["passes_cost_ratio_difference_threshold"]
        for comparison in pair_comparisons.values()
    )
    return {
        "schema_version": 1,
        "purpose": (
            "Direct sector-diagonalization validation of the H-chain "
            "phase-rotated perturbative PF eigenvalue-error estimator"
        ),
        "system": {
            "h_chain": h_chain,
            "ham_name": system["ham_name"],
            "num_qubits": system["num_qubits"],
            "num_commuting_groups": system["num_groups"],
            "ground_energy_without_constant_hartree": system[
                "ground_energy_without_constant_hartree"
            ],
            "sector": system["sector"],
        },
        "criteria": criteria,
        "results": results,
        "pair_cost_comparisons": pair_comparisons,
        "overall_pass": overall_pass,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep-json", nargs="+", type=Path, required=True)
    parser.add_argument("--noise-analysis-json", type=Path)
    parser.add_argument("--relative-difference-threshold", type=float, default=0.05)
    parser.add_argument("--alpha-difference-threshold", type=float, default=0.05)
    parser.add_argument("--cost-ratio-difference-threshold", type=float, default=0.02)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_validation(
        args.sweep_json,
        noise_analysis_path=args.noise_analysis_json,
        relative_difference_threshold=args.relative_difference_threshold,
        alpha_difference_threshold=args.alpha_difference_threshold,
        cost_ratio_difference_threshold=args.cost_ratio_difference_threshold,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"overall_pass: {result['overall_pass']}")
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
