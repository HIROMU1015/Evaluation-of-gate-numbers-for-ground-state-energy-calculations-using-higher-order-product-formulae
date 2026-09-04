"""Run low-storage moment/Ritz checks for H6/H7 without full-space matrices.

The existing small-system validation forms dense matrices in the full qubit
Hilbert space before restricting them to the conserved spin-population sector.
That is unnecessary for H6/H7.  This runner keeps each grouped Hamiltonian
sparse until after the sector restriction, diagonalizes only the resulting
400/735 dimensional matrices, and applies the product formula matrix-free in
that sector.

For each PF it first obtains the short-time fixed-order coefficient, uses it
to define the analytic QPE-cost schedule, and then evaluates repeated overlap
moments at that schedule.  No direct PF-unitary diagonalization is used.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh, schur

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.analysis_utils import loglog_average_coeff, loglog_fit
from trotterlib.config import BETA, DECOMPO_NUM, pf_order
from trotterlib.cost_validation import analytic_optimal_time
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.phase_moments import dominant_phase_from_moments
from trotterlib.product_formula import _get_s2_sequence
from validate_hchain_perturbative_estimator import _as_group_operator


M5_LABEL = "4th(m5_best)"
Y8_LABEL = "8th(Morales-Y8m10b)"
DEFAULT_DIMENSIONS = (1, 2, 4, 6, 8, 10, 12, 16)
DEFAULT_M5_TIMES = tuple(np.geomspace(0.15, 0.8, 9))
DEFAULT_Y8_TIMES = tuple(np.geomspace(0.8, 1.6, 9))


def _fixed_half_population_indices(
    state: np.ndarray, num_qubits: int
) -> tuple[np.ndarray, tuple[int, int]]:
    """Return the fixed alpha/beta population sector containing ``state``."""
    support = np.flatnonzero(np.abs(state) > 1e-12)
    half = num_qubits // 2
    counts = {
        (
            format(int(index), f"0{num_qubits}b")[:half].count("1"),
            format(int(index), f"0{num_qubits}b")[half:].count("1"),
        )
        for index in support
    }
    if len(counts) != 1:
        raise RuntimeError(
            "Ground state does not occupy one fixed half-population sector: "
            f"{sorted(counts)}"
        )
    population_counts = next(iter(counts))
    indices = np.asarray(
        [
            index
            for index in range(1 << num_qubits)
            if (
                format(index, f"0{num_qubits}b")[:half].count("1"),
                format(index, f"0{num_qubits}b")[half:].count("1"),
            )
            == population_counts
        ],
        dtype=int,
    )
    outside = np.setdiff1d(np.arange(1 << num_qubits), indices)
    outside_norm = float(np.linalg.norm(state[outside]))
    if outside_norm > 1e-11:
        raise RuntimeError(f"Ground-state sector leakage is {outside_norm}")
    return indices, population_counts


def _prepare_sparse_sector_system(h_chain: int) -> dict[str, Any]:
    """Prepare group spectra after sparse restriction to the occupied sector."""
    started = time.perf_counter()
    full_system = _prepare_system(h_chain)
    num_qubits = int(full_system["num_qubits"])
    full_state = np.asarray(full_system["state"], dtype=complex).reshape(-1)
    indices, populations = _fixed_half_population_indices(
        full_state, num_qubits
    )
    state = full_state[indices].copy()
    state /= np.linalg.norm(state)

    dimension = int(indices.size)
    identity = np.eye(dimension)
    hamiltonian = np.zeros((dimension, dimension), dtype=complex)
    group_spectra: list[tuple[np.ndarray, np.ndarray]] = []
    maximum_hermiticity_residual = 0.0
    maximum_group_eigenvector_orthogonality_residual = 0.0
    maximum_sector_leakage = 0.0
    all_indices = np.arange(1 << num_qubits)
    outside = np.setdiff1d(all_indices, indices)

    for group in full_system["groups"]:
        operator = _as_group_operator(group)
        constant = operator.terms.get((), 0.0)
        sparse = get_sparse_operator(operator, num_qubits)
        leakage_block = sparse[outside][:, indices]
        if leakage_block.nnz:
            maximum_sector_leakage = max(
                maximum_sector_leakage,
                float(np.linalg.norm(leakage_block.data)),
            )
        matrix = sparse[indices][:, indices].toarray()
        matrix -= constant * identity
        maximum_hermiticity_residual = max(
            maximum_hermiticity_residual,
            float(np.linalg.norm(matrix - matrix.conj().T)),
        )
        hamiltonian += matrix
        values, vectors = eigh(
            matrix,
            check_finite=False,
            overwrite_a=False,
            driver="evd",
        )
        maximum_group_eigenvector_orthogonality_residual = max(
            maximum_group_eigenvector_orthogonality_residual,
            float(np.linalg.norm(vectors.conj().T @ vectors - identity)),
        )
        group_spectra.append((values, vectors))

    reported_energy = float(full_system["energy_without_constant"])
    input_ground_residual = float(
        np.linalg.norm(hamiltonian @ state - reported_energy * state)
    )
    state_refined = input_ground_residual > 1e-10
    input_to_refined_overlap_probability = 1.0
    if state_refined:
        ground_values, ground_vectors = eigh(
            hamiltonian,
            subset_by_index=[0, 0],
            check_finite=False,
        )
        refined_state = ground_vectors[:, 0]
        input_to_refined_overlap_probability = float(
            abs(np.vdot(state, refined_state)) ** 2
        )
        state = refined_state
        energy = float(ground_values[0])
    else:
        energy = reported_energy
    ground_residual = float(np.linalg.norm(hamiltonian @ state - energy * state))
    if maximum_sector_leakage > 1e-11:
        raise RuntimeError(f"Maximum group sector leakage is {maximum_sector_leakage}")
    if maximum_group_eigenvector_orthogonality_residual > 1e-10:
        raise RuntimeError(
            "Maximum group eigenvector orthogonality residual is "
            f"{maximum_group_eigenvector_orthogonality_residual}"
        )
    if ground_residual > 1e-9:
        raise RuntimeError(f"Ground-state eigenpair residual is {ground_residual}")

    return {
        "h_chain": h_chain,
        "ham_name": full_system["ham_name"],
        "num_qubits": num_qubits,
        "num_groups": len(group_spectra),
        "energy": energy,
        "state": state,
        "group_spectra": group_spectra,
        "sector": {
            "kind": "fixed_half_populations",
            "population_counts": list(populations),
            "dimension": dimension,
            "ground_state_outside_norm": float(
                np.linalg.norm(full_state[outside])
            ),
            "maximum_group_sector_leakage_frobenius_norm": (
                maximum_sector_leakage
            ),
            "maximum_group_hermiticity_residual_frobenius_norm": (
                maximum_hermiticity_residual
            ),
            "maximum_group_eigenvector_orthogonality_residual_frobenius_norm": (
                maximum_group_eigenvector_orthogonality_residual
            ),
            "input_ground_state_eigenpair_residual": input_ground_residual,
            "ground_state_refined_by_sector_diagonalization": state_refined,
            "input_to_refined_ground_state_overlap_probability": (
                input_to_refined_overlap_probability
            ),
            "reported_to_used_ground_energy_shift_hartree": (
                energy - reported_energy
            ),
            "ground_state_eigenpair_residual": ground_residual,
        },
        "preparation_seconds": time.perf_counter() - started,
    }


def _apply_pf(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    state: np.ndarray,
) -> np.ndarray:
    """Apply one full PF step using the precomputed group eigensystems."""
    current = np.asarray(state, dtype=complex).reshape(-1).copy()
    spectra = system["group_spectra"]
    for group_index, weight in iter_s2_sequence_steps(
        len(spectra), _get_s2_sequence(label)
    ):
        values, vectors = spectra[group_index]
        current = vectors @ (
            np.exp(1j * evolution_time * weight * values)
            * (vectors.conj().T @ current)
        )
    return current


def _overlap_point(
    system: dict[str, Any], label: str, evolution_time: float
) -> dict[str, Any]:
    state = system["state"]
    evolved = _apply_pf(system, label, evolution_time, state)
    overlap = complex(np.vdot(state, evolved))
    rotated = np.exp(-1j * system["energy"] * evolution_time) * overlap
    return {
        "time": float(evolution_time),
        "phase_rotated_overlap": {
            "real": float(rotated.real),
            "imag": float(rotated.imag),
        },
        "signed_perturbative_error_hartree": float(
            rotated.imag / evolution_time
        ),
        "perturbative_error_hartree": abs(float(rotated.imag / evolution_time)),
        "overlap_phase_error_hartree": abs(
            float(np.angle(rotated) / evolution_time)
        ),
        "ground_state_survival_probability": float(abs(rotated) ** 2),
        "evolved_state_norm": float(np.linalg.norm(evolved)),
    }


def _fit_short_time(
    system: dict[str, Any],
    label: str,
    times: Sequence[float],
    min_fit_error: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    points = [
        _overlap_point(system, label, float(evolution_time))
        for evolution_time in times
    ]
    errors = np.asarray(
        [point["perturbative_error_hartree"] for point in points]
    )
    times_array = np.asarray(times, dtype=float)
    mask = errors > min_fit_error
    if np.count_nonzero(mask) < 2:
        raise RuntimeError(f"{label}: fewer than two reliable fit points")
    free_fit = loglog_fit(
        times_array[mask], errors[mask], compute_r2=True
    )
    order = int(pf_order(label))
    alpha = loglog_average_coeff(
        times_array[mask], errors[mask], order, mask_nonpositive=True
    )
    return {
        "times": times_array.tolist(),
        "points": points,
        "fit_mask": mask.tolist(),
        "minimum_fit_error_hartree": float(min_fit_error),
        "free_fit": {
            "order": free_fit.slope,
            "alpha": free_fit.coeff,
            "r2": free_fit.r2,
        },
        "fixed_order": order,
        "fixed_order_alpha": alpha,
        "elapsed_seconds": time.perf_counter() - started,
    }


def _cost(
    error: float, evolution_time: float, n_exp: int, epsilon_e: float
) -> float | None:
    if error < 0 or error >= epsilon_e:
        return None
    return float(BETA * n_exp / (evolution_time * (epsilon_e - error)))


def _moment_estimates(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    dimensions: Sequence[int],
    gram_relative_cutoff: float,
    epsilon_e: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    state = system["state"]
    current = state.copy()
    moments = [complex(np.vdot(state, current))]
    power_states = [current.copy()]
    for _ in range(max(dimensions)):
        current = _apply_pf(system, label, evolution_time, current)
        moments.append(complex(np.vdot(state, current)))
        power_states.append(current.copy())
    moment_array = np.asarray(moments)

    n_exp = int(DECOMPO_NUM[f"H{system['h_chain']}"][label])
    estimates: dict[str, Any] = {}
    for dimension in dimensions:
        estimate = dominant_phase_from_moments(
            moment_array,
            evolution_time=evolution_time,
            reference_energy=float(system["energy"]),
            subspace_dimension=int(dimension),
            gram_relative_cutoff=gram_relative_cutoff,
        )
        error = abs(float(estimate["selected"]["energy_shift_hartree"]))
        estimate["estimated_error_hartree"] = error
        estimate["estimated_cost"] = _cost(
            error, evolution_time, n_exp, epsilon_e
        )
        estimates[str(dimension)] = estimate

    explicit_krylov_estimates: dict[str, Any] = {}
    for dimension in dimensions:
        basis_powers = np.column_stack(power_states[: int(dimension)])
        shifted_powers = np.column_stack(
            power_states[1 : int(dimension) + 1]
        )
        left_vectors, singular_values, right_adjoint = np.linalg.svd(
            basis_powers, full_matrices=False
        )
        retained = (
            singular_values**2
            > gram_relative_cutoff * singular_values[0] ** 2
        )
        basis = left_vectors[:, retained]
        power_to_basis = (
            right_adjoint.conj().T[:, retained]
            / singular_values[retained]
        )
        evolved_basis = shifted_powers @ power_to_basis
        projected_unitary = basis.conj().T @ evolved_basis
        ritz_values, ritz_vectors = np.linalg.eig(projected_unitary)
        candidates = []
        for index, ritz_value in enumerate(ritz_values):
            approximate_state = basis @ ritz_vectors[:, index]
            approximate_state /= np.linalg.norm(approximate_state)
            overlap_probability = float(
                abs(np.vdot(state, approximate_state)) ** 2
            )
            rotated_value = (
                np.exp(-1j * system["energy"] * evolution_time)
                * ritz_value
            )
            energy_shift = float(np.angle(rotated_value) / evolution_time)
            candidates.append(
                {
                    "ritz_index": int(index),
                    "phase_radians": float(np.angle(rotated_value)),
                    "energy_shift_hartree": energy_shift,
                    "effective_energy_hartree": float(
                        system["energy"] + energy_shift
                    ),
                    "ritz_value_real": float(ritz_value.real),
                    "ritz_value_imag": float(ritz_value.imag),
                    "ritz_value_magnitude": float(abs(ritz_value)),
                    "estimated_reference_overlap_probability": (
                        overlap_probability
                    ),
                }
            )
        selected = max(
            candidates,
            key=lambda candidate: candidate[
                "estimated_reference_overlap_probability"
            ],
        )
        error = abs(float(selected["energy_shift_hartree"]))
        explicit_krylov_estimates[str(dimension)] = {
            "subspace_dimension": int(dimension),
            "retained_rank": int(np.count_nonzero(retained)),
            "gram_relative_cutoff": float(gram_relative_cutoff),
            "smallest_retained_singular_value_ratio": float(
                singular_values[retained][-1] / singular_values[0]
            ),
            "selected": selected,
            "candidates": candidates,
            "estimated_error_hartree": error,
            "estimated_cost": _cost(
                error, evolution_time, n_exp, epsilon_e
            ),
        }

    rotated_first = (
        np.exp(-1j * system["energy"] * evolution_time) * moment_array[1]
    )
    return {
        "moments": [
            {"real": float(value.real), "imag": float(value.imag)}
            for value in moment_array
        ],
        "one_overlap_perturbative_error_hartree": abs(
            float(rotated_first.imag / evolution_time)
        ),
        "one_overlap_phase_error_hartree": abs(
            float(np.angle(rotated_first) / evolution_time)
        ),
        "one_overlap_survival_probability": float(abs(rotated_first) ** 2),
        "estimates": estimates,
        "explicit_vector_krylov_estimates": explicit_krylov_estimates,
        "elapsed_seconds": time.perf_counter() - started,
    }


def _direct_pf_eigenphase(
    system: dict[str, Any],
    label: str,
    evolution_time: float,
    epsilon_e: float,
) -> dict[str, Any]:
    """Build and diagonalize the PF unitary in the conserved sector."""
    started = time.perf_counter()
    dimension = int(system["sector"]["dimension"])
    unitary = np.eye(dimension, dtype=complex)
    spectra = system["group_spectra"]
    for group_index, weight in iter_s2_sequence_steps(
        len(spectra), _get_s2_sequence(label)
    ):
        values, vectors = spectra[group_index]
        unitary = vectors @ (
            np.exp(1j * evolution_time * weight * values)[:, None]
            * (vectors.conj().T @ unitary)
        )

    unitarity_residual = float(
        np.linalg.norm(unitary.conj().T @ unitary - np.eye(dimension))
    )
    triangular, eigenvectors = schur(
        unitary, output="complex", check_finite=False
    )
    eigenvalues = np.diag(triangular)
    schur_off_diagonal_residual = float(
        np.linalg.norm(triangular - np.diag(eigenvalues))
    )
    overlaps = np.abs(eigenvectors.conj().T @ system["state"]) ** 2
    selected = int(np.argmax(overlaps))
    rotated_eigenvalues = (
        np.exp(-1j * system["energy"] * evolution_time) * eigenvalues
    )
    shifts = np.angle(rotated_eigenvalues) / evolution_time
    selected_shift = float(shifts[selected])
    selected_error = abs(selected_shift)
    n_exp = int(DECOMPO_NUM[f"H{system['h_chain']}"][label])
    order = np.argsort(overlaps)[::-1]
    leading_branches = [
        {
            "schur_index": int(index),
            "reference_overlap_probability": float(overlaps[index]),
            "energy_shift_hartree": float(shifts[index]),
            "error_hartree": abs(float(shifts[index])),
            "eigenvalue_real": float(eigenvalues[index].real),
            "eigenvalue_imag": float(eigenvalues[index].imag),
            "eigenvalue_magnitude": float(abs(eigenvalues[index])),
        }
        for index in order[: min(10, dimension)]
    ]
    return {
        "selected_schur_index": selected,
        "selected_energy_shift_hartree": selected_shift,
        "direct_error_hartree": selected_error,
        "selected_reference_overlap_probability": float(overlaps[selected]),
        "sum_reference_overlap_probabilities": float(np.sum(overlaps)),
        "direct_cost": _cost(
            selected_error, evolution_time, n_exp, epsilon_e
        ),
        "leading_branches": leading_branches,
        "unitarity_residual_frobenius_norm": unitarity_residual,
        "schur_off_diagonal_residual_frobenius_norm": (
            schur_off_diagonal_residual
        ),
        "elapsed_seconds": time.perf_counter() - started,
    }


def run(
    h_chains: Sequence[int],
    dimensions: Sequence[int],
    m5_times: Sequence[float],
    y8_times: Sequence[float],
    min_fit_error: float,
    gram_relative_cutoff: float,
    epsilon_e: float,
    direct_h_chains: Sequence[int],
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    direct_systems = set(int(value) for value in direct_h_chains)
    if not direct_systems.issubset(set(int(value) for value in h_chains)):
        raise ValueError("direct_h_chains must be a subset of h_chains")
    for h_chain in h_chains:
        system_started = time.perf_counter()
        print(f"prepare H{h_chain}", flush=True)
        system = _prepare_sparse_sector_system(int(h_chain))
        print(
            f"H{h_chain}: {system['num_qubits']} qubits, "
            f"sector dimension {system['sector']['dimension']}, "
            f"{system['num_groups']} groups",
            flush=True,
        )
        formula_results: dict[str, Any] = {}
        for label, times in (
            (M5_LABEL, m5_times),
            (Y8_LABEL, y8_times),
        ):
            print(f"H{h_chain}: fit {label}", flush=True)
            fit = _fit_short_time(system, label, times, min_fit_error)
            alpha = float(fit["fixed_order_alpha"])
            order = int(fit["fixed_order"])
            optimal_time = analytic_optimal_time(alpha, order, epsilon_e)
            n_exp = int(DECOMPO_NUM[f"H{h_chain}"][label])
            analytic_cost = float(
                BETA
                * n_exp
                / (
                    optimal_time
                    * (epsilon_e - alpha * optimal_time**order)
                )
            )
            print(
                f"H{h_chain}: {label} alpha={alpha:.6e}, "
                f"t_analytic={optimal_time:.6f}; moments",
                flush=True,
            )
            moment = _moment_estimates(
                system,
                label,
                optimal_time,
                dimensions,
                gram_relative_cutoff,
                epsilon_e,
            )
            direct = None
            if h_chain in direct_systems:
                print(
                    f"H{h_chain}: {label} direct sector diagonalization",
                    flush=True,
                )
                direct = _direct_pf_eigenphase(
                    system,
                    label,
                    optimal_time,
                    epsilon_e,
                )
                direct_error = float(direct["direct_error_hartree"])
                direct_cost = direct["direct_cost"]
                for key, estimate in moment["estimates"].items():
                    estimate["estimated_to_direct_error_ratio"] = float(
                        estimate["estimated_error_hartree"] / direct_error
                    )
                    estimate["estimated_to_direct_cost_ratio"] = (
                        None
                        if direct_cost is None
                        or estimate["estimated_cost"] is None
                        else float(estimate["estimated_cost"] / direct_cost)
                    )
                for key, estimate in moment[
                    "explicit_vector_krylov_estimates"
                ].items():
                    estimate["estimated_to_direct_error_ratio"] = float(
                        estimate["estimated_error_hartree"] / direct_error
                    )
                    estimate["estimated_to_direct_cost_ratio"] = (
                        None
                        if direct_cost is None
                        or estimate["estimated_cost"] is None
                        else float(estimate["estimated_cost"] / direct_cost)
                    )
            formula_results[label] = {
                "label": label,
                "pauli_rotations_per_step": n_exp,
                "short_time_fit": fit,
                "analytic_schedule": {
                    "time": optimal_time,
                    "model_error_hartree": float(alpha * optimal_time**order),
                    "model_cost": analytic_cost,
                },
                "moment_phase": moment,
                "direct_sector_diagonalization": direct,
            }

        pair_cost_ratios: dict[str, Any] = {}
        for dimension in dimensions:
            key = str(dimension)
            m5_cost = formula_results[M5_LABEL]["moment_phase"]["estimates"][
                key
            ]["estimated_cost"]
            y8_cost = formula_results[Y8_LABEL]["moment_phase"]["estimates"][
                key
            ]["estimated_cost"]
            explicit_m5_cost = formula_results[M5_LABEL]["moment_phase"][
                "explicit_vector_krylov_estimates"
            ][key]["estimated_cost"]
            explicit_y8_cost = formula_results[Y8_LABEL]["moment_phase"][
                "explicit_vector_krylov_estimates"
            ][key]["estimated_cost"]
            pair_cost_ratios[key] = {
                "y8m10b_over_m5": (
                    None
                    if m5_cost is None or y8_cost is None
                    else float(y8_cost / m5_cost)
                ),
                "explicit_vector_krylov_y8m10b_over_m5": (
                    None
                    if explicit_m5_cost is None or explicit_y8_cost is None
                    else float(explicit_y8_cost / explicit_m5_cost)
                ),
            }
        direct_pair_cost_ratio = None
        m5_direct = formula_results[M5_LABEL][
            "direct_sector_diagonalization"
        ]
        y8_direct = formula_results[Y8_LABEL][
            "direct_sector_diagonalization"
        ]
        if m5_direct is not None and y8_direct is not None:
            m5_direct_cost = m5_direct["direct_cost"]
            y8_direct_cost = y8_direct["direct_cost"]
            if m5_direct_cost is not None and y8_direct_cost is not None:
                direct_pair_cost_ratio = float(
                    y8_direct_cost / m5_direct_cost
                )
                for comparison in pair_cost_ratios.values():
                    comparison["direct_y8m10b_over_m5"] = (
                        direct_pair_cost_ratio
                    )
                    for key in (
                        "y8m10b_over_m5",
                        "explicit_vector_krylov_y8m10b_over_m5",
                    ):
                        value = comparison[key]
                        comparison[f"{key}_relative_difference_from_direct"] = (
                            None
                            if value is None
                            else float(abs(value / direct_pair_cost_ratio - 1.0))
                        )
        results[f"H{h_chain}"] = {
            "system": {
                "h_chain": h_chain,
                "ham_name": system["ham_name"],
                "num_qubits": system["num_qubits"],
                "num_groups": system["num_groups"],
                "ground_energy_without_constant_hartree": system["energy"],
                "sector": system["sector"],
                "preparation_seconds": system["preparation_seconds"],
            },
            "results": formula_results,
            "pair_cost_ratios": pair_cost_ratios,
            "direct_pair_cost_ratio": direct_pair_cost_ratio,
            "elapsed_seconds": time.perf_counter() - system_started,
        }
    return {
        "schema_version": 1,
        "purpose": (
            "H6/H7 sparse-sector repeated-overlap moment/Ritz estimates at "
            "short-time power-law analytic schedules"
        ),
        "epsilon_E_hartree": float(epsilon_e),
        "beta": float(BETA),
        "dimensions": [int(value) for value in dimensions],
        "maximum_pf_applications": int(max(dimensions)),
        "gram_relative_cutoff": float(gram_relative_cutoff),
        "direct_h_chains": sorted(direct_systems),
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-chains", nargs="+", type=int, default=[6, 7])
    parser.add_argument(
        "--dimensions", nargs="+", type=int, default=list(DEFAULT_DIMENSIONS)
    )
    parser.add_argument(
        "--m5-times", nargs="+", type=float, default=list(DEFAULT_M5_TIMES)
    )
    parser.add_argument(
        "--y8-times", nargs="+", type=float, default=list(DEFAULT_Y8_TIMES)
    )
    parser.add_argument("--min-fit-error", type=float, default=5e-12)
    parser.add_argument("--gram-relative-cutoff", type=float, default=1e-10)
    parser.add_argument("--direct-h-chains", nargs="*", type=int, default=[])
    parser.add_argument(
        "--epsilon-e", type=float, default=0.00015936001019904
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/server_cost_validity/moment_phase_H6_H7_local.json"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(
        args.h_chains,
        args.dimensions,
        args.m5_times,
        args.y8_times,
        args.min_fit_error,
        args.gram_relative_cutoff,
        args.epsilon_e,
        args.direct_h_chains,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)
    print(f"saved: {args.output}", flush=True)


if __name__ == "__main__":
    main()
