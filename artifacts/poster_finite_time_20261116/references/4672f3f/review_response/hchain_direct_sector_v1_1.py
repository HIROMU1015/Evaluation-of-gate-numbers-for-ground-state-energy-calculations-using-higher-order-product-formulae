"""Ordering-aware conserved-sector preparation for direct scaling v1.1."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh

from run_large_hchain_moment_phase import _prepare_system
from validate_hchain_perturbative_estimator import _as_group_operator


def _counts_for_positions(
    index: int,
    num_qubits: int,
    first_positions: tuple[int, ...],
    second_positions: tuple[int, ...],
) -> tuple[int, int]:
    bits = format(int(index), f"0{num_qubits}b")
    return (
        sum(bits[position] == "1" for position in first_positions),
        sum(bits[position] == "1" for position in second_positions),
    )


def fixed_population_indices(
    state: np.ndarray, num_qubits: int
) -> tuple[np.ndarray, tuple[int, int], str]:
    """Infer the unique supported block or interleaved population convention."""
    if num_qubits % 2:
        raise ValueError("population-sector inference requires an even qubit count")
    support = np.flatnonzero(np.abs(np.asarray(state).reshape(-1)) > 1e-12)
    if not support.size:
        raise RuntimeError("input state has empty numerical support")
    half = num_qubits // 2
    conventions = {
        "block_alpha_beta": (
            tuple(range(half)),
            tuple(range(half, num_qubits)),
        ),
        "interleaved_even_odd": (
            tuple(range(0, num_qubits, 2)),
            tuple(range(1, num_qubits, 2)),
        ),
    }
    candidates: list[tuple[np.ndarray, tuple[int, int], str]] = []
    for name, (first_positions, second_positions) in conventions.items():
        support_counts = {
            _counts_for_positions(
                int(index), num_qubits, first_positions, second_positions
            )
            for index in support
        }
        if len(support_counts) != 1:
            continue
        populations = next(iter(support_counts))
        indices = np.asarray(
            [
                index
                for index in range(1 << num_qubits)
                if _counts_for_positions(
                    index, num_qubits, first_positions, second_positions
                )
                == populations
            ],
            dtype=int,
        )
        candidates.append((indices, populations, name))

    if not candidates:
        raise RuntimeError(
            "ground-state support occupies neither one block nor one "
            "interleaved population sector"
        )
    if len(candidates) > 1:
        first_indices = candidates[0][0]
        if not all(np.array_equal(first_indices, item[0]) for item in candidates[1:]):
            descriptions = [
                {"convention": item[2], "populations": list(item[1]), "dimension": len(item[0])}
                for item in candidates
            ]
            raise RuntimeError(
                "population ordering is ambiguous and defines different sectors: "
                f"{descriptions}"
            )
        # If the sectors are identical, retain a deterministic label while
        # explicitly recording that both encodings were equivalent.
        indices, populations, _ = candidates[0]
        return indices, populations, "block_and_interleaved_equivalent"
    return candidates[0]


def prepare_sparse_sector_system_v1_1(h_chain: int) -> dict[str, Any]:
    """Prepare the exact conserved sector after ordering-aware inference."""
    started = time.perf_counter()
    full_system = _prepare_system(h_chain)
    num_qubits = int(full_system["num_qubits"])
    full_state = np.asarray(full_system["state"], dtype=complex).reshape(-1)
    indices, populations, convention = fixed_population_indices(
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
        raise RuntimeError(f"maximum group sector leakage is {maximum_sector_leakage}")
    if maximum_group_eigenvector_orthogonality_residual > 1e-10:
        raise RuntimeError(
            "maximum group eigenvector orthogonality residual is "
            f"{maximum_group_eigenvector_orthogonality_residual}"
        )
    if ground_residual > 1e-9:
        raise RuntimeError(f"ground-state eigenpair residual is {ground_residual}")

    return {
        "h_chain": h_chain,
        "ham_name": full_system["ham_name"],
        "num_qubits": num_qubits,
        "num_groups": len(group_spectra),
        "energy": energy,
        "state": state,
        "group_spectra": group_spectra,
        "sector": {
            "kind": "fixed_populations_ordering_aware_v1_1",
            "state_vector_ordering_convention": convention,
            "population_counts": list(populations),
            "dimension": dimension,
            "ground_state_outside_norm": float(np.linalg.norm(full_state[outside])),
            "maximum_group_sector_leakage_frobenius_norm": maximum_sector_leakage,
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
            "reported_to_used_ground_energy_shift_hartree": energy
            - reported_energy,
            "ground_state_eigenpair_residual": ground_residual,
        },
        "preparation_seconds": time.perf_counter() - started,
    }
