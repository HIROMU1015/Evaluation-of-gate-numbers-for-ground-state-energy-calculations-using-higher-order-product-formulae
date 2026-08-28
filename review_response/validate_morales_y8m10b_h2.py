"""Validate the published Morales Y8m10b formula on the grouped H2 Hamiltonian.

This is a small, deterministic reviewer-response calculation.  It compares
the legacy arXiv-v2 m=8 coefficients used by the submitted manuscript with
the published QIC-2025 Y8m10b coefficients.  No artifact is written; JSON is
printed to stdout.
"""

from __future__ import annotations

import contextlib
import io
import json

import numpy as np
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh

from trotterlib.chemistry_hamiltonian import (
    jw_hamiltonian_maker,
    min_hamiltonian_grouper,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.product_formula import (
    _get_kernel_s2_sequence,
    _get_processor_s2_sequence,
    _get_s2_sequence,
)


LEGACY_LABEL = "8th(Morales)"
PUBLISHED_LABEL = "8th(Morales-Y8m10b)"
PROCESSED_LABEL = "8th(Morales-YP8m8)"


def _fit_power_law(times: np.ndarray, errors: np.ndarray) -> tuple[float, float]:
    mask = errors > 5e-15
    if np.count_nonzero(mask) < 2:
        raise RuntimeError("Not enough points above the numerical-noise threshold.")
    slope, intercept = np.polyfit(np.log(times[mask]), np.log(errors[mask]), 1)
    return float(slope), float(np.exp(intercept))


def run_validation() -> dict[str, object]:
    times = np.linspace(0.45, 1.20, 16)
    with contextlib.redirect_stdout(io.StringIO()):
        hamiltonian, _, ham_name, num_qubits = jw_hamiltonian_maker(2)
    groups, _ = min_hamiltonian_grouper(hamiltonian, ham_name)

    matrix = get_sparse_operator(hamiltonian, num_qubits).toarray()
    energies, states = eigh(matrix)
    ground_energy = float(energies[0])
    ground_state = states[:, 0]
    group_spectra = [
        eigh(get_sparse_operator(group, num_qubits).toarray()) for group in groups
    ]
    group_rotation_costs = [
        sum(1 for term in group.terms if term) for group in groups
    ]

    def product_formula_unitary(time: float, label: str) -> np.ndarray:
        unitary = np.eye(2**num_qubits, dtype=complex)
        for group_index, weight in iter_s2_sequence_steps(
            len(groups), _get_s2_sequence(label)
        ):
            values, vectors = group_spectra[group_index]
            gate = (vectors * np.exp(-1j * time * weight * values)) @ vectors.conj().T
            unitary = gate @ unitary
        return unitary

    results: dict[str, object] = {}
    for label in (LEGACY_LABEL, PUBLISHED_LABEL, PROCESSED_LABEL):
        diagonalization_errors = []
        perturbative_errors = []
        for time in times:
            unitary = product_formula_unitary(float(time), label)
            effective_energies = -np.angle(np.linalg.eigvals(unitary)) / time
            diagonalization_errors.append(
                float(np.min(np.abs(effective_energies - ground_energy)))
            )

            delta_state = (
                unitary @ ground_state
                - np.exp(-1j * ground_energy * time) * ground_state
            )
            estimate = -(
                np.exp(1j * ground_energy * time)
                * np.vdot(ground_state, delta_state)
            ).imag / time
            perturbative_errors.append(abs(float(estimate)))

        diagonalization_errors_array = np.asarray(diagonalization_errors)
        perturbative_errors_array = np.asarray(perturbative_errors)
        diagonalization_order, diagonalization_alpha = _fit_power_law(
            times, diagonalization_errors_array
        )
        perturbative_order, perturbative_alpha = _fit_power_law(
            times, perturbative_errors_array
        )
        kernel_sequence = _get_kernel_s2_sequence(label)
        processor_sequence = _get_processor_s2_sequence(label)
        full_sequence = _get_s2_sequence(label)
        kernel_rotation_count = sum(
            group_rotation_costs[group_index]
            for group_index, _ in iter_s2_sequence_steps(
                len(groups), kernel_sequence
            )
        )
        full_rotation_count = sum(
            group_rotation_costs[group_index]
            for group_index, _ in iter_s2_sequence_steps(
                len(groups), full_sequence
            )
        )
        results[label] = {
            "kernel_s2_blocks": len(kernel_sequence),
            "processor_s2_blocks_per_side": len(processor_sequence),
            "full_s2_blocks_for_one_kernel_step": len(full_sequence),
            "kernel_pauli_rotations_per_step": kernel_rotation_count,
            "full_pauli_rotations_for_one_kernel_step": full_rotation_count,
            "diagonalization_fit": {
                "order": diagonalization_order,
                "alpha": diagonalization_alpha,
            },
            "perturbative_fit": {
                "order": perturbative_order,
                "alpha": perturbative_alpha,
            },
            "diagonalization_errors": diagonalization_errors,
            "perturbative_errors": perturbative_errors,
        }

    old = results[LEGACY_LABEL]
    new = results[PUBLISHED_LABEL]
    old_alpha = old["diagonalization_fit"]["alpha"]  # type: ignore[index]
    new_alpha = new["diagonalization_fit"]["alpha"]  # type: ignore[index]
    old_cost = old["kernel_pauli_rotations_per_step"]  # type: ignore[index]
    new_cost = new["kernel_pauli_rotations_per_step"]  # type: ignore[index]
    fixed_target_cost_ratio = (new_cost / old_cost) * (new_alpha / old_alpha) ** (1 / 8)

    return {
        "source": {
            "title": (
                "Selection and Improvement of Product Formulae for Best "
                "Performance of Quantum Simulation"
            ),
            "doi": "10.2478/qic-2025-0001",
            "published_table": 1,
        },
        "system": {
            "name": ham_name,
            "num_qubits": num_qubits,
            "num_commuting_groups": len(groups),
            "ground_energy_hartree": ground_energy,
            "times": times.tolist(),
        },
        "results": results,
        "comparison": {
            "old_to_new_alpha_improvement": old_alpha / new_alpha,
            "new_to_old_fixed_target_pf_cost_ratio": fixed_target_cost_ratio,
            "fixed_target_pf_cost_reduction": 1 - fixed_target_cost_ratio,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_validation(), indent=2, sort_keys=True))
