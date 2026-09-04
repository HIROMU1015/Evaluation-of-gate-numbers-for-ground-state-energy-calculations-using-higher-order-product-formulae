"""Validate low-storage moment/Ritz PF eigenphase estimates on H chains."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.config import BETA
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.phase_moments import dominant_phase_from_moments
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.qiskit_time_evolution_grouping import tEvolution_vector_grouper
from validate_hchain_perturbative_estimator import _prepare_sector_system


M5_LABEL = "4th(m5_best)"
Y8_LABEL = "8th(Morales-Y8m10b)"
DEFAULT_DIMENSIONS = (1, 2, 4, 6, 8, 10, 12, 16)


def _sector_unitary(
    system: dict[str, Any], label: str, evolution_time: float
) -> np.ndarray:
    dimension = int(system["ground_state"].size)
    unitary = np.eye(dimension, dtype=complex)
    for group_index, weight in iter_s2_sequence_steps(
        int(system["num_groups"]), _get_s2_sequence(label)
    ):
        values, vectors = system["group_spectra"][group_index]
        phases = np.exp(1j * evolution_time * weight * values)
        unitary = ((vectors * phases) @ vectors.conj().T) @ unitary
    return unitary


def _moments_from_matrix(
    unitary: np.ndarray, state: np.ndarray, maximum_power: int
) -> np.ndarray:
    reference = np.asarray(state, dtype=complex).reshape(-1)
    current = reference.copy()
    moments = [complex(np.vdot(reference, current))]
    for _ in range(maximum_power):
        current = unitary @ current
        moments.append(complex(np.vdot(reference, current)))
    return np.asarray(moments)


def _moments_from_qiskit(
    h_chain: int,
    label: str,
    evolution_time: float,
    maximum_power: int,
) -> tuple[np.ndarray, int]:
    system = _prepare_system(h_chain)
    reference = np.asarray(system["state"], dtype=complex).reshape(-1)
    current = np.asarray(system["state"], dtype=complex).reshape(-1, 1)
    moments = [complex(np.vdot(reference, current.reshape(-1)))]
    rotation_count: int | None = None
    for _ in range(maximum_power):
        _, evolved, current_count = tEvolution_vector_grouper(
            system["groups"],
            -float(evolution_time),
            int(system["num_qubits"]),
            current,
            label,
        )
        if rotation_count is None:
            rotation_count = int(current_count)
        elif rotation_count != int(current_count):
            raise RuntimeError("The PF rotation count changed between powers")
        current = np.asarray(evolved.data, dtype=complex).reshape(-1, 1)
        moments.append(complex(np.vdot(reference, current.reshape(-1))))
    assert rotation_count is not None
    return np.asarray(moments), rotation_count


def _complex_payload(values: Sequence[complex]) -> list[dict[str, float]]:
    return [
        {"real": float(value.real), "imag": float(value.imag)}
        for value in values
    ]


def _cost(
    error: float, *, evolution_time: float, n_exp: int, epsilon_e: float
) -> float | None:
    if error < 0 or error >= epsilon_e:
        return None
    return float(
        BETA * n_exp / (evolution_time * (epsilon_e - error))
    )


def _estimate_dimensions(
    moments: np.ndarray,
    *,
    dimensions: Sequence[int],
    evolution_time: float,
    reference_energy: float,
    direct_error: float,
    direct_cost: float,
    n_exp: int,
    epsilon_e: float,
    gram_relative_cutoff: float,
) -> dict[str, Any]:
    estimates: dict[str, Any] = {}
    for dimension in dimensions:
        estimate = dominant_phase_from_moments(
            moments,
            evolution_time=evolution_time,
            reference_energy=reference_energy,
            subspace_dimension=int(dimension),
            gram_relative_cutoff=gram_relative_cutoff,
        )
        estimated_error = abs(
            float(estimate["selected"]["energy_shift_hartree"])
        )
        estimated_cost = _cost(
            estimated_error,
            evolution_time=evolution_time,
            n_exp=n_exp,
            epsilon_e=epsilon_e,
        )
        estimate["estimated_error_hartree"] = estimated_error
        estimate["estimated_to_direct_error_ratio"] = float(
            estimated_error / direct_error
        )
        estimate["estimated_cost"] = estimated_cost
        estimate["estimated_to_direct_cost_ratio"] = (
            None
            if estimated_cost is None
            else float(estimated_cost / direct_cost)
        )
        estimates[str(dimension)] = estimate
    return estimates


def run_validation(
    analysis_path: Path,
    *,
    h_chains: Sequence[int],
    dimensions: Sequence[int],
    gram_relative_cutoff: float,
    qiskit_h_chains: Sequence[int],
) -> dict[str, Any]:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    epsilon_e = float(analysis["cost_model"]["epsilon_E_hartree"])
    maximum_power = max(dimensions)
    qiskit_systems = set(int(value) for value in qiskit_h_chains)
    if not qiskit_systems.issubset(set(int(value) for value in h_chains)):
        raise ValueError("qiskit_h_chains must be a subset of h_chains")
    results: dict[str, Any] = {}

    for h_chain in h_chains:
        system_label = f"H{h_chain}"
        system_results = analysis["results"][system_label]
        started = time.perf_counter()
        sector_system = _prepare_sector_system(h_chain)
        formula_results: dict[str, Any] = {}
        for label in (M5_LABEL, Y8_LABEL):
            source = system_results[label]
            target = source["analytic_power_law_optimum"]
            target_index = int(target["nearest_sampled_index"])
            evolution_time = float(target["nearest_sampled_time"])
            direct = source["direct_diagonalization"]
            direct_error = float(
                direct["curve"]["errors_hartree"][target_index]
            )
            direct_cost = float(
                direct["at_nearest_analytic_optimum"]["direct_cost"]
            )
            n_exp = int(source["pauli_rotations_per_step"])

            unitary_started = time.perf_counter()
            unitary = _sector_unitary(
                sector_system, label, evolution_time
            )
            moments = _moments_from_matrix(
                unitary,
                sector_system["ground_state"],
                maximum_power,
            )
            unitary_seconds = time.perf_counter() - unitary_started
            reference_energy = float(
                sector_system["ground_energy_without_constant_hartree"]
            )
            estimates = _estimate_dimensions(
                moments,
                dimensions=dimensions,
                evolution_time=evolution_time,
                reference_energy=reference_energy,
                direct_error=direct_error,
                direct_cost=direct_cost,
                n_exp=n_exp,
                epsilon_e=epsilon_e,
                gram_relative_cutoff=gram_relative_cutoff,
            )

            qiskit_comparison = None
            if h_chain in qiskit_systems:
                qiskit_started = time.perf_counter()
                qiskit_moments, rotation_count = _moments_from_qiskit(
                    h_chain,
                    label,
                    evolution_time,
                    maximum_power,
                )
                qiskit_estimates = _estimate_dimensions(
                    qiskit_moments,
                    dimensions=dimensions,
                    evolution_time=evolution_time,
                    reference_energy=reference_energy,
                    direct_error=direct_error,
                    direct_cost=direct_cost,
                    n_exp=n_exp,
                    epsilon_e=epsilon_e,
                    gram_relative_cutoff=gram_relative_cutoff,
                )
                qiskit_comparison = {
                    "moments": _complex_payload(qiskit_moments),
                    "pauli_rotations_per_step": rotation_count,
                    "maximum_absolute_moment_difference": float(
                        np.max(np.abs(qiskit_moments - moments))
                    ),
                    "estimates": qiskit_estimates,
                    "elapsed_seconds": time.perf_counter() - qiskit_started,
                }

            formula_results[label] = {
                "label": label,
                "evolution_time": evolution_time,
                "direct_error_hartree": direct_error,
                "direct_cost": direct_cost,
                "direct_selected_ground_state_overlap_probability": float(
                    direct["at_nearest_analytic_optimum"][
                        "selected_ground_state_overlap_probability"
                    ]
                ),
                "pauli_rotations_per_step": n_exp,
                "moments": _complex_payload(moments),
                "estimates": estimates,
                "qiskit_comparison": qiskit_comparison,
                "sector_unitary_and_moments_seconds": unitary_seconds,
            }

        pair_results: dict[str, Any] = {}
        qiskit_pair_results: dict[str, Any] | None = (
            {} if h_chain in qiskit_systems else None
        )
        direct_ratio = (
            formula_results[Y8_LABEL]["direct_cost"]
            / formula_results[M5_LABEL]["direct_cost"]
        )
        for dimension in dimensions:
            key = str(dimension)
            m5_cost = formula_results[M5_LABEL]["estimates"][key][
                "estimated_cost"
            ]
            y8_cost = formula_results[Y8_LABEL]["estimates"][key][
                "estimated_cost"
            ]
            if m5_cost is None or y8_cost is None:
                estimated_ratio = None
                relative_difference = None
            else:
                estimated_ratio = float(y8_cost / m5_cost)
                relative_difference = float(
                    abs(estimated_ratio / direct_ratio - 1.0)
                )
            pair_results[key] = {
                "estimated_y8m10b_over_m5_cost_ratio": estimated_ratio,
                "direct_y8m10b_over_m5_cost_ratio": direct_ratio,
                "relative_difference_from_direct": relative_difference,
            }
            if qiskit_pair_results is not None:
                qiskit_m5_cost = formula_results[M5_LABEL][
                    "qiskit_comparison"
                ]["estimates"][key]["estimated_cost"]
                qiskit_y8_cost = formula_results[Y8_LABEL][
                    "qiskit_comparison"
                ]["estimates"][key]["estimated_cost"]
                if qiskit_m5_cost is None or qiskit_y8_cost is None:
                    qiskit_ratio = None
                    qiskit_relative_difference = None
                else:
                    qiskit_ratio = float(qiskit_y8_cost / qiskit_m5_cost)
                    qiskit_relative_difference = float(
                        abs(qiskit_ratio / direct_ratio - 1.0)
                    )
                qiskit_pair_results[key] = {
                    "estimated_y8m10b_over_m5_cost_ratio": qiskit_ratio,
                    "direct_y8m10b_over_m5_cost_ratio": direct_ratio,
                    "relative_difference_from_direct": (
                        qiskit_relative_difference
                    ),
                }
        results[system_label] = {
            "sector": sector_system["sector"],
            "results": formula_results,
            "pair_cost_ratios": pair_results,
            "qiskit_pair_cost_ratios": qiskit_pair_results,
            "elapsed_seconds": time.perf_counter() - started,
        }

    summary: dict[str, Any] = {}
    for dimension in dimensions:
        key = str(dimension)
        error_differences = []
        pair_differences = []
        for system in results.values():
            for formula in system["results"].values():
                ratio = formula["estimates"][key][
                    "estimated_to_direct_error_ratio"
                ]
                error_differences.append(abs(float(ratio) - 1.0))
            pair_difference = system["pair_cost_ratios"][key][
                "relative_difference_from_direct"
            ]
            if pair_difference is not None:
                pair_differences.append(float(pair_difference))
        summary[key] = {
            "maximum_eigenvalue_error_relative_difference": max(
                error_differences
            ),
            "maximum_pair_cost_ratio_relative_difference": max(
                pair_differences
            ),
        }

    return {
        "schema_version": 1,
        "purpose": (
            "Low-storage repeated-overlap moment/Ritz validation against "
            "direct PF eigenvalue errors at analytic schedules"
        ),
        "source_analysis": str(analysis_path),
        "epsilon_E_hartree": epsilon_e,
        "dimensions": [int(value) for value in dimensions],
        "maximum_pf_applications": maximum_power,
        "gram_relative_cutoff": gram_relative_cutoff,
        "results": results,
        "summary_by_dimension": summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-json",
        type=Path,
        default=Path(
            "artifacts/server_cost_validity/wide_time_cost_analysis.json"
        ),
    )
    parser.add_argument("--h-chains", nargs="+", type=int, default=[2, 4, 5])
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=list(DEFAULT_DIMENSIONS),
    )
    parser.add_argument("--gram-relative-cutoff", type=float, default=1e-10)
    parser.add_argument(
        "--qiskit-h-chains", nargs="*", type=int, default=[]
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_validation(
        args.analysis_json,
        h_chains=args.h_chains,
        dimensions=args.dimensions,
        gram_relative_cutoff=args.gram_relative_cutoff,
        qiskit_h_chains=args.qiskit_h_chains,
    )
    print(json.dumps(payload["summary_by_dimension"], indent=2))
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
        print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
