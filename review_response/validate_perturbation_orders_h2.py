"""Validate the perturbative eigenvalue-error estimator across PF orders.

The submitted appendix checked system-size dependence for a second-order
formula.  This complementary reviewer-response calculation checks formula-
order dependence on H2 by comparing the overlap estimator with direct
diagonalization of each product-formula unitary.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh

from trotterlib.chemistry_hamiltonian import (
    jw_hamiltonian_maker,
    min_hamiltonian_grouper,
)
from trotterlib.config import pf_order
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.product_formula import _get_s2_sequence


OUTPUT_DIR = Path("artifacts/reviewer_response/perturbation_validation")
MANUSCRIPT_FIGURE = Path(
    "tests/overleaf/higher_order_pf_gate_cost/figures/appendix/perturbation/"
    "perturb_vs_diag_across_orders_h2.pdf"
)
LABEL_TIMES = {
    "2nd": np.geomspace(0.03, 0.40, 12),
    "4th": np.geomspace(0.08, 0.80, 12),
    "4th(m5_best)": np.geomspace(0.12, 0.90, 12),
    "8th(Morales-Y8m10b)": np.geomspace(0.45, 1.20, 12),
    "8th(Morales-YP8m8)": np.geomspace(0.45, 1.20, 12),
    "10th(Morales-QIC-m17)": np.geomspace(0.60, 1.40, 12),
}
DISPLAY_LABELS = {
    "2nd": "2nd",
    "4th": "4th (standard)",
    "4th(m5_best)": "4th (new m=5)",
    "8th(Morales-Y8m10b)": "8th (Y8m10b)",
    "8th(Morales-YP8m8)": "8th (YP8m8)",
    "10th(Morales-QIC-m17)": "10th (QIC m=17)",
}


def run_validation() -> dict[str, object]:
    with contextlib.redirect_stdout(io.StringIO()):
        hamiltonian, _, ham_name, num_qubits = jw_hamiltonian_maker(2)
    groups, _ = min_hamiltonian_grouper(hamiltonian, ham_name)

    full_matrix = get_sparse_operator(hamiltonian, num_qubits).toarray()
    energies, states = eigh(full_matrix)
    ground_energy = float(energies[0])
    ground_state = states[:, 0]
    group_spectra = [
        eigh(get_sparse_operator(group, num_qubits).toarray()) for group in groups
    ]

    def product_formula_unitary(time: float, label: str) -> np.ndarray:
        unitary = np.eye(2**num_qubits, dtype=complex)
        for group_index, weight in iter_s2_sequence_steps(
            len(groups), _get_s2_sequence(label)
        ):
            values, vectors = group_spectra[group_index]
            phases = np.exp(-1j * time * weight * values)
            unitary = ((vectors * phases) @ vectors.conj().T) @ unitary
        return unitary

    results: dict[str, object] = {}
    for label, times in LABEL_TIMES.items():
        direct_errors = []
        perturbative_errors = []
        for time in times:
            unitary = product_formula_unitary(float(time), label)
            effective_energies = -np.angle(np.linalg.eigvals(unitary)) / time
            direct_error = float(
                np.min(np.abs(effective_energies - ground_energy))
            )

            delta_state = (
                unitary @ ground_state
                - np.exp(-1j * ground_energy * time) * ground_state
            )
            perturbative_error = abs(
                float(
                    -np.imag(
                        np.exp(1j * ground_energy * time)
                        * np.vdot(ground_state, delta_state)
                    )
                    / time
                )
            )
            direct_errors.append(direct_error)
            perturbative_errors.append(perturbative_error)

        direct = np.asarray(direct_errors)
        perturbative = np.asarray(perturbative_errors)
        reliable = direct > 5e-15
        relative_difference = np.full(direct.shape, np.nan)
        relative_difference[reliable] = (
            np.abs(perturbative[reliable] - direct[reliable]) / direct[reliable]
        )
        results[label] = {
            "formal_order": pf_order(label),
            "times": times.tolist(),
            "direct_errors_hartree": direct_errors,
            "perturbative_errors_hartree": perturbative_errors,
            "relative_differences": relative_difference.tolist(),
            "num_reliable_points": int(np.count_nonzero(reliable)),
            "max_relative_difference": float(
                np.nanmax(relative_difference)
            ),
            "median_relative_difference": float(
                np.nanmedian(relative_difference)
            ),
        }

    return {
        "schema_version": 1,
        "purpose": (
            "Direct-diagonalization validation of the phase-rotated "
            "complex-overlap estimator across product-formula orders"
        ),
        "system": {
            "name": ham_name,
            "basis": "sto-3g",
            "distance_angstrom": 1.0,
            "num_qubits": num_qubits,
            "num_commuting_groups": len(groups),
            "ground_energy_hartree": ground_energy,
        },
        "results": results,
    }


def make_figure(payload: dict[str, object], output_path: Path) -> None:
    results = payload["results"]
    if not isinstance(results, dict):
        raise TypeError("results must be a mapping")

    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    minimum = float("inf")
    maximum = 0.0
    for label, result_object in results.items():
        if not isinstance(result_object, dict):
            raise TypeError("each result must be a mapping")
        times = np.asarray(result_object["times"], dtype=float)
        direct = np.asarray(result_object["direct_errors_hartree"], dtype=float)
        perturbative = np.asarray(
            result_object["perturbative_errors_hartree"], dtype=float
        )
        relative = np.asarray(result_object["relative_differences"], dtype=float)
        reliable = np.isfinite(relative)
        display_label = DISPLAY_LABELS[label]

        axes[0].scatter(
            direct[reliable], perturbative[reliable], s=17, label=display_label
        )
        axes[1].plot(
            times[reliable], relative[reliable], marker="o", ms=3, label=display_label
        )
        minimum = min(minimum, float(np.min(direct[reliable])))
        maximum = max(maximum, float(np.max(direct[reliable])))

    diagonal = np.geomspace(minimum / 1.5, maximum * 1.5, 100)
    axes[0].plot(diagonal, diagonal, color="black", lw=0.8, ls="--")
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Direct eigenvalue error (Ha)")
    axes[0].set_ylabel("Perturbative estimate (Ha)")

    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Evolution time")
    axes[1].set_ylabel("Relative difference")
    axes[1].legend(fontsize=7, frameon=False)
    for axis in axes:
        axis.grid(True, which="both", alpha=0.25)

    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    payload = run_validation()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "H2_across_pf_orders.json"
    figure_path = OUTPUT_DIR / "H2_across_pf_orders.pdf"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    make_figure(payload, figure_path)
    make_figure(payload, MANUSCRIPT_FIGURE)
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"saved: {json_path}")
    print(f"saved: {figure_path}")
    print(f"saved: {MANUSCRIPT_FIGURE}")


if __name__ == "__main__":
    main()
