"""Run resumable perturbative H-chain checks for the published Morales PF.

The calculation applies grouped product-formula circuits to the known ground
state and uses the phase-rotated complex-overlap estimator.  It does not
diagonalize the product-formula unitary.  One JSON file is written per system
so a larger H-chain run can be resumed safely.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from trotterlib.analysis_utils import loglog_average_coeff, loglog_fit
from trotterlib.chemistry_hamiltonian import (
    ham_ground_energy,
    jw_hamiltonian_maker,
    min_hamiltonian_grouper,
)
from trotterlib.config import (
    DECOMPO_NUM,
    QISKIT_AER_METHOD,
    QISKIT_AER_PRECISION,
    QISKIT_AER_TARGET_GPUS,
    QISKIT_SIMULATOR_DEVICE,
    pf_order,
)
from trotterlib.cost_validation import combined_time_grid
from trotterlib.processed_cost import morales_yp8m8_hchain_costs
from trotterlib.qiskit_time_evolution_grouping import tEvolution_vector_grouper
from trotterlib.qiskit_time_evolution_pyscf import (
    make_fci_vector_from_pyscf_solver_grouper,
)
from trotterlib.qiskit_time_evolution_utils import available_aer_devices


LEGACY_LABEL = "8th(Morales)"
PUBLISHED_LABEL = "8th(Morales-Y8m10b)"
PROCESSED_LABEL = "8th(Morales-YP8m8)"
DEFAULT_OUTPUT_DIR = Path("artifacts/reviewer_response/morales_qic2025")


def _prepare_system(h_chain: int) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        hamiltonian, _, ham_name, num_qubits = jw_hamiltonian_maker(h_chain)

        if h_chain in (2, 3):
            energy, state, _ = ham_ground_energy(hamiltonian)
            grouped_operators, _ = min_hamiltonian_grouper(hamiltonian, ham_name)
            groups = [[operator] for operator in grouped_operators]
        else:
            groups, num_qubits, energy, state = (
                make_fci_vector_from_pyscf_solver_grouper(h_chain)
            )

    constant = float(np.real(hamiltonian.terms.get((), 0.0)))
    return {
        "ham_name": ham_name,
        "num_qubits": int(num_qubits),
        "groups": groups,
        "energy_without_constant": float(energy - constant),
        "state": np.asarray(state, dtype=complex).reshape(-1, 1),
        "constant": constant,
    }


def _evaluate_label(
    system: dict[str, Any],
    times: np.ndarray,
    label: str,
    *,
    min_fit_error: float,
) -> dict[str, Any]:
    state_column = system["state"]
    state = state_column.reshape(-1)
    energy = float(system["energy_without_constant"])
    errors = []
    overlap_phase_errors = []
    survival_probabilities = []
    phase_rotated_overlaps = []
    pauli_rotations_per_step = None
    started = time.perf_counter()

    for evolution_time in times:
        # PauliEvolutionGate implements exp(-i H t).  Passing -t follows the
        # sign convention of the submitted calculation code.
        _, evolved, rotation_count = tEvolution_vector_grouper(
            system["groups"],
            -float(evolution_time),
            int(system["num_qubits"]),
            state_column,
            label,
        )
        if pauli_rotations_per_step is None:
            pauli_rotations_per_step = int(rotation_count)
        elif pauli_rotations_per_step != int(rotation_count):
            raise RuntimeError("The per-step rotation count changed with time.")

        evolved_state = np.asarray(evolved.data)
        ideal_phase = np.exp(1j * energy * evolution_time)
        delta_state = evolved_state - ideal_phase * state
        phase_rotated_overlap = np.exp(
            -1j * energy * evolution_time
        ) * np.vdot(state, evolved_state)
        # This is the t -> -t form of
        # -Im[e^(i E0 t) <psi0|Delta psi(t)>] / t.
        estimate = (
            np.exp(-1j * energy * evolution_time)
            * np.vdot(state, delta_state)
        ).imag / evolution_time
        errors.append(abs(float(estimate)))
        overlap_phase_errors.append(
            abs(float(np.angle(phase_rotated_overlap) / evolution_time))
        )
        survival_probabilities.append(float(abs(phase_rotated_overlap) ** 2))
        phase_rotated_overlaps.append(
            {
                "real": float(phase_rotated_overlap.real),
                "imag": float(phase_rotated_overlap.imag),
            }
        )

    errors_array = np.asarray(errors)
    fit_mask = errors_array > float(min_fit_error)
    if np.count_nonzero(fit_mask) < 2:
        raise RuntimeError(f"{label}: fewer than two points exceed min_fit_error")
    free_fit = loglog_fit(
        times[fit_mask],
        errors_array[fit_mask],
        mask_nonpositive=True,
        compute_r2=True,
    )
    order = pf_order(label)
    fixed_order_alpha = loglog_average_coeff(
        times[fit_mask],
        errors_array[fit_mask],
        order,
        mask_nonpositive=True,
    )

    processed_components = None
    if label == PROCESSED_LABEL:
        processed_components = morales_yp8m8_hchain_costs(system["h_chain"])[
            "pauli_rotations"
        ]
        expected_count = processed_components.full_single_step
    else:
        expected_count = DECOMPO_NUM[f"H{system['h_chain']}"][label]
    if pauli_rotations_per_step != expected_count:
        raise RuntimeError(
            f"{label}: generated {pauli_rotations_per_step} rotations, "
            f"expected {expected_count}"
        )

    return {
        "label": label,
        "formal_order": order,
        "elapsed_seconds": time.perf_counter() - started,
        "pauli_rotations_per_step": pauli_rotations_per_step,
        "asymptotic_pauli_rotations_per_kernel_step": (
            processed_components.kernel
            if processed_components is not None
            else pauli_rotations_per_step
        ),
        "processed_cost_components": (
            {
                "kernel": processed_components.kernel,
                "processor_pair_overhead": (
                    processed_components.processor_pair_overhead
                ),
            }
            if processed_components is not None
            else None
        ),
        "free_fit": {
            "order": free_fit.slope,
            "alpha": free_fit.coeff,
            "r2": free_fit.r2,
        },
        "fixed_order_alpha": fixed_order_alpha,
        "fit_mask": fit_mask.tolist(),
        "errors_hartree": errors,
        "overlap_phase_errors_hartree": overlap_phase_errors,
        "ground_state_survival_probabilities": survival_probabilities,
        "phase_rotated_overlaps": phase_rotated_overlaps,
    }


def run_system(
    h_chain: int,
    labels: Sequence[str],
    times: np.ndarray,
    *,
    output_dir: Path,
    min_fit_error: float,
    force: bool,
    run_name: str = "morales_qic2025",
    baseline_label: str | None = None,
) -> Path:
    safe_run_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", run_name).strip("_")
    if not safe_run_name:
        raise ValueError("run_name must contain at least one safe filename character")
    output_path = output_dir / f"H{h_chain}_{safe_run_name}.json"
    if output_path.exists() and not force:
        print(f"skip existing: {output_path}", flush=True)
        return output_path

    print(f"prepare H{h_chain}", flush=True)
    system = _prepare_system(h_chain)
    system["h_chain"] = h_chain
    print(
        f"H{h_chain}: {system['num_qubits']} qubits, "
        f"{len(system['groups'])} groups",
        flush=True,
    )
    results = []
    for label in labels:
        print(f"H{h_chain}: run {label}", flush=True)
        results.append(
            _evaluate_label(
                system,
                times,
                label,
                min_fit_error=min_fit_error,
            )
        )
        print(
            f"H{h_chain}: {label} alpha={results[-1]['fixed_order_alpha']:.6e}",
            flush=True,
        )

    comparison = None
    result_by_label = {result["label"]: result for result in results}
    if LEGACY_LABEL in result_by_label and PUBLISHED_LABEL in result_by_label:
        old = result_by_label[LEGACY_LABEL]
        new = result_by_label[PUBLISHED_LABEL]
        old_alpha = float(old["fixed_order_alpha"])
        new_alpha = float(new["fixed_order_alpha"])
        old_cost = int(old["pauli_rotations_per_step"])
        new_cost = int(new["pauli_rotations_per_step"])
        cost_ratio = (new_cost / old_cost) * (new_alpha / old_alpha) ** (1 / 8)
        comparison = {
            "old_to_new_alpha_improvement": old_alpha / new_alpha,
            "new_to_old_fixed_target_pf_cost_ratio": cost_ratio,
            "fixed_target_pf_cost_reduction": 1 - cost_ratio,
        }

    comparisons_to_baseline = None
    if baseline_label is not None:
        if baseline_label not in result_by_label:
            raise ValueError(f"baseline label was not evaluated: {baseline_label}")
        baseline = result_by_label[baseline_label]
        baseline_alpha = float(baseline["fixed_order_alpha"])
        baseline_cost = int(
            baseline["asymptotic_pauli_rotations_per_kernel_step"]
        )
        baseline_order = int(baseline["formal_order"])
        comparisons_to_baseline = {}
        for label, result in result_by_label.items():
            if int(result["formal_order"]) != baseline_order:
                continue
            alpha = float(result["fixed_order_alpha"])
            cost = int(result["asymptotic_pauli_rotations_per_kernel_step"])
            ratio = (cost / baseline_cost) * (
                alpha / baseline_alpha
            ) ** (1 / baseline_order)
            comparisons_to_baseline[label] = {
                "fixed_target_pf_cost_ratio": ratio,
                "fixed_target_pf_cost_reduction": 1 - ratio,
            }

    if any(label in (PUBLISHED_LABEL, PROCESSED_LABEL) for label in labels):
        source = {
            "doi": "10.2478/qic-2025-0001",
            "published_formulae": [
                label
                for label in labels
                if label in (PUBLISHED_LABEL, PROCESSED_LABEL)
            ],
        }
    else:
        source = {"description": "project-local product-formula candidates"}

    payload = {
        "schema_version": 1,
        "run_name": run_name,
        "source": source,
        "system": {
            "h_chain": h_chain,
            "ham_name": system["ham_name"],
            "basis": "sto-3g",
            "distance_angstrom": 1.0,
            "num_qubits": system["num_qubits"],
            "num_commuting_groups": len(system["groups"]),
            "constant_hartree": system["constant"],
            "ground_energy_without_constant_hartree": system[
                "energy_without_constant"
            ],
        },
        "calculation": {
            "method": "phase-rotated complex-overlap perturbative estimator",
            "simulator_device": QISKIT_SIMULATOR_DEVICE,
            "aer_method": (
                QISKIT_AER_METHOD if QISKIT_SIMULATOR_DEVICE == "GPU" else None
            ),
            "aer_precision": (
                QISKIT_AER_PRECISION if QISKIT_SIMULATOR_DEVICE == "GPU" else None
            ),
            "aer_target_gpus": list(QISKIT_AER_TARGET_GPUS),
            "times": times.tolist(),
            "min_fit_error": min_fit_error,
        },
        "results": results,
        "comparison": comparison,
        "comparisons_to_baseline": comparisons_to_baseline,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)
    print(f"saved: {output_path}", flush=True)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h-chains", nargs="+", type=int, required=True)
    parser.add_argument(
        "--labels",
        nargs="+",
        default=[PUBLISHED_LABEL],
    )
    parser.add_argument("--t-start", type=float, default=0.5)
    parser.add_argument("--t-stop", type=float, default=1.2)
    parser.add_argument("--num-times", type=int, default=10)
    parser.add_argument(
        "--grid-kind", choices=("linear", "geometric"), default="linear"
    )
    parser.add_argument("--dense-t-start", type=float)
    parser.add_argument("--dense-t-stop", type=float)
    parser.add_argument("--dense-num-times", type=int, default=0)
    parser.add_argument("--include-times", nargs="*", type=float, default=[])
    parser.add_argument("--min-fit-error", type=float, default=5e-15)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-name", default="morales_qic2025")
    parser.add_argument("--baseline-label")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Qiskit simulator device: {QISKIT_SIMULATOR_DEVICE}", flush=True)
    if QISKIT_SIMULATOR_DEVICE == "GPU":
        print(f"Aer devices: {available_aer_devices()}", flush=True)
    times = combined_time_grid(
        args.t_start,
        args.t_stop,
        args.num_times,
        grid_kind=args.grid_kind,
        dense_t_start=args.dense_t_start,
        dense_t_stop=args.dense_t_stop,
        dense_num_times=args.dense_num_times,
        include_times=args.include_times,
    )
    for h_chain in args.h_chains:
        run_system(
            h_chain,
            args.labels,
            times,
            output_dir=args.output_dir,
            min_fit_error=args.min_fit_error,
            force=args.force,
            run_name=args.run_name,
            baseline_label=args.baseline_label,
        )


if __name__ == "__main__":
    main()
