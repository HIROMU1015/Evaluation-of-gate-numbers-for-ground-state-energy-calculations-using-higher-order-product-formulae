"""B03 audit of S2 expansion, product order, and adjacent-step merging.

The audit uses deterministic two-qubit Hamiltonian groups.  It compares an
independent, explicitly expanded S2 reference with the repository's merged
iterator, both dense sector builders, and the Qiskit grouped-circuit path.
An intentionally non-palindromic S2 sequence is included because reversing a
time-symmetric PF cannot expose a left/right multiplication mistake.
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
import subprocess
from typing import Any, Sequence

import numpy as np
from openfermion.ops import QubitOperator
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.linalg import eigh, expm

from trotterlib.pf_decomposition import (
    inverse_s2_sequence,
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import (
    _get_s2_sequence,
    morales_2025_y8m10b_list,
    yoshida_4th_list,
)
from trotterlib.qiskit_time_evolution_grouping import (
    add_precomputed_clique_to_circuit_grouper,
    build_clique_hamiltonians,
    w_trotter_grouper,
    w_trotter_grouper_precomputed,
)
from trotterlib.sector_pf import (
    build_sector_pf_unitary_cached_s2,
    build_sector_pf_unitary_sequential,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_b03_s2_order_merge_equivalence_20260921"
TIME_VALUE = 0.37
ABSOLUTE_TOLERANCE = 3e-12
STEP_TOLERANCE = 2e-15
ORDER_CONTROL_MINIMUM = 1e-3
CURRENT_M3_WEIGHTS = (
    -0.4737318199452465,
    0.3316118001935053,
    0.2092246690782796,
    0.1960294407008384,
)
# Deliberately non-palindromic and moderately scaled so that the wrong-order
# control is separated from roundoff by more than nine orders of magnitude.
DIRECTION_PROBE_SEQUENCE = (3.0, -2.0, 0.5)


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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _git_state() -> dict[str, Any]:
    def run(*command: str) -> str:
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()

    status = run("git", "status", "--porcelain").splitlines()
    return {
        "commit": run("git", "rev-parse", "HEAD") or None,
        "branch": run("git", "branch", "--show-current") or None,
        "dirty": bool(status),
        "status": status,
    }


def _package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in ("numpy", "scipy", "qiskit", "openfermion"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def formula_definitions() -> dict[str, dict[str, Any]]:
    """Return compact coefficients from the production sources under audit."""
    return {
        "second_order": {
            "weights": (1.0,),
            "source": "src/trotterlib/product_formula.py:trotter_2nd_list",
            "qiskit_label": "2nd",
        },
        "yoshida4": {
            "weights": tuple(yoshida_4th_list()),
            "source": "src/trotterlib/product_formula.py:yoshida_4th_list",
            "qiskit_label": "4th",
        },
        "current_m3": {
            "weights": CURRENT_M3_WEIGHTS,
            "source": (
                "review_response/compare_existing_pf_low_order_models_local.py:"
                "CURRENT_M3_WEIGHTS"
            ),
            "qiskit_label": None,
        },
        "morales_y8m10b": {
            "weights": tuple(morales_2025_y8m10b_list()),
            "source": (
                "src/trotterlib/product_formula.py:"
                "morales_2025_y8m10b_list"
            ),
            "qiskit_label": "8th(Morales-Y8m10b)",
        },
        "zero_middle_control": {
            # Normalized compact representation with an exact zero S2 block.
            "weights": (0.4, 0.0, 0.3),
            "source": "B03 synthetic zero-coefficient control",
            "qiskit_label": None,
        },
    }


def fixture_cliques() -> tuple[tuple[QubitOperator, ...], ...]:
    """Commuting terms within each group, noncommuting between groups."""
    return (
        (
            QubitOperator("X0", 0.31),
            QubitOperator("Z1", -0.17),
        ),
        (
            QubitOperator("Z0 Z1", 0.23),
            QubitOperator("Y0 Y1", 0.11),
        ),
        (QubitOperator("Y0", -0.19),),
    )


def _explicit_s2_steps(
    number_of_groups: int, sequence: Sequence[float]
) -> list[tuple[int, float]]:
    """Independent unmerged expansion of a written S2-block sequence."""
    steps: list[tuple[int, float]] = []
    for raw_weight in sequence:
        weight = float(raw_weight)
        for group_index in range(number_of_groups - 1):
            steps.append((group_index, weight / 2.0))
        steps.append((number_of_groups - 1, weight))
        for group_index in reversed(range(number_of_groups - 1)):
            steps.append((group_index, weight / 2.0))
    return steps


def _independent_adjacent_merge(
    steps: Sequence[tuple[int, float]],
) -> list[tuple[int, float]]:
    merged: list[tuple[int, float]] = []
    for group_index, weight in steps:
        if merged and merged[-1][0] == group_index:
            previous_index, previous_weight = merged[-1]
            merged[-1] = (previous_index, previous_weight + float(weight))
        else:
            merged.append((int(group_index), float(weight)))
    return merged


def _step_residual(
    first: Sequence[tuple[int, float]], second: Sequence[tuple[int, float]]
) -> float:
    if len(first) != len(second):
        return math.inf
    if any(left[0] != right[0] for left, right in zip(first, second)):
        return math.inf
    return max(
        (abs(float(left[1]) - float(right[1])) for left, right in zip(first, second)),
        default=0.0,
    )


def _left_action_product(
    matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    time_value: float,
) -> np.ndarray:
    """Apply written steps to states: U = F_last ... F_second F_first."""
    result = np.eye(matrices[0].shape[0], dtype=np.complex128)
    for group_index, weight in steps:
        factor = expm(
            1j * float(time_value) * float(weight) * matrices[group_index]
        )
        result = factor @ result
    return result


def _wrong_right_product(
    matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    time_value: float,
) -> np.ndarray:
    """Deliberate control: U = F_first F_second ... F_last."""
    result = np.eye(matrices[0].shape[0], dtype=np.complex128)
    for group_index, weight in steps:
        factor = expm(
            1j * float(time_value) * float(weight) * matrices[group_index]
        )
        result = result @ factor
    return result


def _state_action(
    matrices: Sequence[np.ndarray],
    steps: Sequence[tuple[int, float]],
    time_value: float,
    initial: np.ndarray,
) -> np.ndarray:
    state = np.asarray(initial, dtype=np.complex128)
    for group_index, weight in steps:
        state = expm(
            1j * float(time_value) * float(weight) * matrices[group_index]
        ) @ state
    return state


def _circuit_unitary(circuit: QuantumCircuit) -> np.ndarray:
    dimension = 2 ** circuit.num_qubits
    columns: list[np.ndarray] = []
    for index in range(dimension):
        basis = np.zeros(dimension, dtype=np.complex128)
        basis[index] = 1.0
        columns.append(np.asarray(Statevector(basis).evolve(circuit).data))
    return np.column_stack(columns)


def _arbitrary_sequence_qiskit_unitary(
    cliques: Sequence[Sequence[QubitOperator]],
    sequence: Sequence[float],
    time_value: float,
) -> tuple[np.ndarray, int]:
    precomputed = build_clique_hamiltonians(cliques, 2)
    circuit = QuantumCircuit(2)
    rotation_count = 0
    for group_index, weight in iter_s2_sequence_steps(len(cliques), sequence):
        rotation_count += add_precomputed_clique_to_circuit_grouper(
            precomputed[group_index],
            -float(time_value),  # native Qiskit gate is exp(-i H t)
            2,
            float(weight),
            circuit,
        )
    return _circuit_unitary(circuit), rotation_count


def _signed_ground_bias(
    unitary: np.ndarray,
    ground_state: np.ndarray,
    reference_energy: float,
    time_value: float,
) -> tuple[float, float]:
    eigenvalues, eigenvectors = np.linalg.eig(unitary)
    eigenvectors /= np.linalg.norm(eigenvectors, axis=0)
    overlaps = np.abs(eigenvectors.conj().T @ ground_state) ** 2
    selected = int(np.argmax(overlaps))
    rotated = np.exp(-1j * reference_energy * time_value) * eigenvalues[selected]
    return float(np.angle(rotated) / time_value), float(overlaps[selected])


def _fixture_data(number_of_groups: int):
    cliques = fixture_cliques()[:number_of_groups]
    precomputed = build_clique_hamiltonians(cliques, 2)
    matrices = [
        np.asarray(clique.hamiltonian.to_matrix(), dtype=np.complex128)
        for clique in precomputed
        if clique.hamiltonian is not None
    ]
    spectra = [eigh(matrix, check_finite=False) for matrix in matrices]
    full_hamiltonian = sum(matrices, np.zeros_like(matrices[0]))
    energies, vectors = eigh(full_hamiltonian, check_finite=False)
    term_counts = [int(clique.exp_term_count) for clique in precomputed]
    return cliques, precomputed, matrices, spectra, term_counts, energies, vectors


def sequence_and_matrix_checks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    detail: dict[str, Any] = {}
    initial = np.asarray([1.0, 1.0j, -0.4, 0.2j], dtype=np.complex128)
    initial /= np.linalg.norm(initial)

    for formula_id, definition in formula_definitions().items():
        compact = tuple(float(value) for value in definition["weights"])
        explicit_sequence = list(reversed(compact[1:])) + [compact[0]] + list(compact[1:])
        production_sequence = symmetric_s2_sequence(compact)
        sequence_residual = max(
            (abs(a - b) for a, b in zip(explicit_sequence, production_sequence)),
            default=0.0,
        )
        detail[formula_id] = {
            "compact_weights": compact,
            "explicit_s2_sequence": explicit_sequence,
            "production_s2_sequence": production_sequence,
            "source": definition["source"],
            "palindromic": production_sequence == list(reversed(production_sequence)),
            "normalization": float(sum(production_sequence)),
            "groups": {},
        }
        for number_of_groups in (1, 2, 3):
            (
                _cliques,
                _precomputed,
                matrices,
                spectra,
                term_counts,
                energies,
                vectors,
            ) = _fixture_data(number_of_groups)
            raw_steps = _explicit_s2_steps(number_of_groups, explicit_sequence)
            independent_merged = _independent_adjacent_merge(raw_steps)
            production_merged = list(
                iter_s2_sequence_steps(number_of_groups, production_sequence)
            )
            step_residual = _step_residual(independent_merged, production_merged)
            unmerged_unitary = _left_action_product(matrices, raw_steps, TIME_VALUE)
            merged_unitary = _left_action_product(
                matrices, independent_merged, TIME_VALUE
            )
            sequential = build_sector_pf_unitary_sequential(
                spectra, production_sequence, TIME_VALUE
            )
            cached = build_sector_pf_unitary_cached_s2(
                spectra, production_sequence, TIME_VALUE
            )
            negative = build_sector_pf_unitary_sequential(
                spectra, production_sequence, -TIME_VALUE
            )
            inverse = build_sector_pf_unitary_sequential(
                spectra, inverse_s2_sequence(production_sequence), TIME_VALUE
            )
            direct_state = _state_action(
                matrices, raw_steps, TIME_VALUE, initial
            )
            matrix_state = unmerged_unitary @ initial
            raw_rotations = int(sum(term_counts[index] for index, _ in raw_steps))
            merged_rotations = int(
                sum(term_counts[index] for index, _ in production_merged)
            )
            nonzero_merged_rotations = int(
                sum(
                    term_counts[index]
                    for index, weight in production_merged
                    if float(weight) != 0.0
                )
            )
            delta_unmerged, ground_overlap = _signed_ground_bias(
                unmerged_unitary, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            delta_merged, _ = _signed_ground_bias(
                merged_unitary, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            delta_sequential, _ = _signed_ground_bias(
                sequential, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            delta_cached, _ = _signed_ground_bias(
                cached, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            metrics = {
                "formula_id": formula_id,
                "number_of_groups": number_of_groups,
                "compact_weight_count": len(compact),
                "s2_block_count": len(production_sequence),
                "sequence_expansion_residual": sequence_residual,
                "merged_step_residual": step_residual,
                "raw_group_exponential_count": len(raw_steps),
                "merged_group_exponential_count": len(production_merged),
                "effective_nonzero_merged_exponential_count": sum(
                    float(weight) != 0.0 for _, weight in production_merged
                ),
                "raw_rotation_count": raw_rotations,
                "merged_rotation_count": merged_rotations,
                "effective_nonzero_merged_rotation_count": nonzero_merged_rotations,
                "unmerged_vs_merged_unitary_residual": float(
                    np.linalg.norm(unmerged_unitary - merged_unitary)
                ),
                "sequential_vs_explicit_unitary_residual": float(
                    np.linalg.norm(sequential - unmerged_unitary)
                ),
                "cached_vs_explicit_unitary_residual": float(
                    np.linalg.norm(cached - unmerged_unitary)
                ),
                "negative_time_vs_adjoint_residual": float(
                    np.linalg.norm(negative - unmerged_unitary.conj().T)
                ),
                "inverse_sequence_vs_adjoint_residual": float(
                    np.linalg.norm(inverse - unmerged_unitary.conj().T)
                ),
                "explicit_state_vs_matrix_action_residual": float(
                    np.linalg.norm(direct_state - matrix_state)
                ),
                "unitarity_residual": float(
                    np.linalg.norm(
                        sequential.conj().T @ sequential
                        - np.eye(sequential.shape[0])
                    )
                ),
                "delta_e_explicit": delta_unmerged,
                "delta_e_merged": delta_merged,
                "delta_e_sequential": delta_sequential,
                "delta_e_cached": delta_cached,
                "maximum_delta_e_path_difference": float(
                    max(
                        abs(delta_unmerged - delta_merged),
                        abs(delta_unmerged - delta_sequential),
                        abs(delta_unmerged - delta_cached),
                    )
                ),
                "ground_branch_overlap_probability": ground_overlap,
            }
            residual_keys = (
                "sequence_expansion_residual",
                "merged_step_residual",
                "unmerged_vs_merged_unitary_residual",
                "sequential_vs_explicit_unitary_residual",
                "cached_vs_explicit_unitary_residual",
                "negative_time_vs_adjoint_residual",
                "inverse_sequence_vs_adjoint_residual",
                "explicit_state_vs_matrix_action_residual",
                "unitarity_residual",
            )
            metrics["passed"] = bool(
                all(float(metrics[key]) <= ABSOLUTE_TOLERANCE for key in residual_keys)
                and metrics["maximum_delta_e_path_difference"] <= ABSOLUTE_TOLERANCE
            )
            rows.append(metrics)
            detail[formula_id]["groups"][str(number_of_groups)] = {
                "raw_steps": raw_steps,
                "independently_merged_steps": independent_merged,
                "production_merged_steps": production_merged,
                "metrics": metrics,
            }
    return rows, detail


def order_direction_checks() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number_of_groups in (1, 2, 3):
        cliques, _, matrices, spectra, _, _, _ = _fixture_data(number_of_groups)
        raw = _explicit_s2_steps(number_of_groups, DIRECTION_PROBE_SEQUENCE)
        merged = list(
            iter_s2_sequence_steps(number_of_groups, DIRECTION_PROBE_SEQUENCE)
        )
        reference = _left_action_product(matrices, raw, TIME_VALUE)
        wrong = _wrong_right_product(matrices, raw, TIME_VALUE)
        sequential = build_sector_pf_unitary_sequential(
            spectra, DIRECTION_PROBE_SEQUENCE, TIME_VALUE
        )
        inverse = build_sector_pf_unitary_sequential(
            spectra,
            inverse_s2_sequence(DIRECTION_PROBE_SEQUENCE),
            TIME_VALUE,
        )
        negative_same_order = build_sector_pf_unitary_sequential(
            spectra, DIRECTION_PROBE_SEQUENCE, -TIME_VALUE
        )
        qiskit_unitary, qiskit_count = _arbitrary_sequence_qiskit_unitary(
            cliques, DIRECTION_PROBE_SEQUENCE, TIME_VALUE
        )
        row = {
            "number_of_groups": number_of_groups,
            "sequence": json.dumps(DIRECTION_PROBE_SEQUENCE),
            "sequence_is_palindromic": False,
            "merged_step_count": len(merged),
            "sequential_matches_left_action_residual": float(
                np.linalg.norm(sequential - reference)
            ),
            "qiskit_compensated_matches_left_action_residual": float(
                np.linalg.norm(qiskit_unitary - reference)
            ),
            "inverse_sequence_vs_adjoint_residual": float(
                np.linalg.norm(inverse - reference.conj().T)
            ),
            "same_sequence_negative_time_vs_adjoint_residual": float(
                np.linalg.norm(negative_same_order - reference.conj().T)
            ),
            "wrong_right_product_control_residual": float(
                np.linalg.norm(wrong - reference)
            ),
            "qiskit_rotation_count": qiskit_count,
        }
        if number_of_groups == 1:
            control_passed = row["wrong_right_product_control_residual"] <= ABSOLUTE_TOLERANCE
            negative_interpretation_passed = (
                row["same_sequence_negative_time_vs_adjoint_residual"]
                <= ABSOLUTE_TOLERANCE
            )
        else:
            control_passed = (
                row["wrong_right_product_control_residual"]
                >= ORDER_CONTROL_MINIMUM
            )
            negative_interpretation_passed = (
                row["same_sequence_negative_time_vs_adjoint_residual"]
                >= ORDER_CONTROL_MINIMUM
            )
        row["passed"] = bool(
            row["sequential_matches_left_action_residual"] <= ABSOLUTE_TOLERANCE
            and row["qiskit_compensated_matches_left_action_residual"]
            <= ABSOLUTE_TOLERANCE
            and row["inverse_sequence_vs_adjoint_residual"]
            <= ABSOLUTE_TOLERANCE
            and control_passed
            and negative_interpretation_passed
        )
        rows.append(row)
    return rows


def qiskit_registry_checks() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    definitions = formula_definitions()
    for formula_id in ("second_order", "yoshida4", "morales_y8m10b"):
        definition = definitions[formula_id]
        label = str(definition["qiskit_label"])
        expected_sequence = symmetric_s2_sequence(definition["weights"])
        registry_sequence = _get_s2_sequence(label)
        for number_of_groups in (1, 2, 3):
            (
                cliques,
                precomputed,
                matrices,
                _,
                term_counts,
                energies,
                vectors,
            ) = _fixture_data(number_of_groups)
            raw_steps = _explicit_s2_steps(number_of_groups, expected_sequence)
            reference = _left_action_product(matrices, raw_steps, TIME_VALUE)
            legacy_circuit = QuantumCircuit(2)
            legacy_count = w_trotter_grouper(
                legacy_circuit,
                cliques,
                -TIME_VALUE,
                2,
                label,
            )
            precomputed_circuit = QuantumCircuit(2)
            precomputed_count = w_trotter_grouper_precomputed(
                precomputed_circuit,
                precomputed,
                -TIME_VALUE,
                2,
                label,
            )
            legacy = _circuit_unitary(legacy_circuit)
            optimized = _circuit_unitary(precomputed_circuit)
            merged_steps = list(
                iter_s2_sequence_steps(number_of_groups, expected_sequence)
            )
            expected_count = int(
                sum(term_counts[index] for index, _ in merged_steps)
            )
            delta_reference, _ = _signed_ground_bias(
                reference, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            delta_qiskit, overlap = _signed_ground_bias(
                optimized, vectors[:, 0], float(energies[0]), TIME_VALUE
            )
            sequence_residual = max(
                (
                    abs(float(first) - float(second))
                    for first, second in zip(expected_sequence, registry_sequence)
                ),
                default=0.0,
            )
            row = {
                "formula_id": formula_id,
                "qiskit_label": label,
                "number_of_groups": number_of_groups,
                "sequence_length": len(expected_sequence),
                "registry_sequence_residual": sequence_residual,
                "legacy_vs_explicit_unitary_residual": float(
                    np.linalg.norm(legacy - reference)
                ),
                "precomputed_vs_explicit_unitary_residual": float(
                    np.linalg.norm(optimized - reference)
                ),
                "legacy_vs_precomputed_unitary_residual": float(
                    np.linalg.norm(legacy - optimized)
                ),
                "expected_rotation_count": expected_count,
                "legacy_rotation_count": legacy_count,
                "precomputed_rotation_count": precomputed_count,
                "delta_e_explicit": delta_reference,
                "delta_e_qiskit": delta_qiskit,
                "delta_e_difference": abs(delta_qiskit - delta_reference),
                "ground_branch_overlap_probability": overlap,
            }
            row["passed"] = bool(
                len(expected_sequence) == len(registry_sequence)
                and sequence_residual <= STEP_TOLERANCE
                and row["legacy_vs_explicit_unitary_residual"]
                <= ABSOLUTE_TOLERANCE
                and row["precomputed_vs_explicit_unitary_residual"]
                <= ABSOLUTE_TOLERANCE
                and row["legacy_vs_precomputed_unitary_residual"]
                <= ABSOLUTE_TOLERANCE
                and legacy_count == expected_count
                and precomputed_count == expected_count
                and row["delta_e_difference"] <= ABSOLUTE_TOLERANCE
            )
            rows.append(row)
    return rows


def source_path_checks() -> list[dict[str, Any]]:
    paths = {
        "pf_decomposition": ROOT / "src/trotterlib/pf_decomposition.py",
        "sector_pf": ROOT / "src/trotterlib/sector_pf.py",
        "qiskit_grouping": ROOT / "src/trotterlib/qiskit_time_evolution_grouping.py",
        "product_formula": ROOT / "src/trotterlib/product_formula.py",
    }
    sentinels = {
        "pf_decomposition": (
            "list(reversed(weights[1:])) + [weights[0]] + weights[1:]",
            "pending_weight += term_weight",
        ),
        "sector_pf": (
            "unitary = _left_apply_group_exponential(",
            "unitary = block @ unitary",
        ),
        "qiskit_grouping": (
            "for term_idx, weight in iter_s2_sequence_steps(",
            "PauliEvolutionGate(",
        ),
        "product_formula": (
            'if num_w == "8th(Morales-Y8m10b)":',
            "return symmetric_s2_sequence(_get_w_list(num_w))",
        ),
    }
    rows: list[dict[str, Any]] = []
    for path_id, path in paths.items():
        text = path.read_text(encoding="utf-8")
        for sentinel in sentinels[path_id]:
            rows.append(
                {
                    "path_id": path_id,
                    "relative_path": str(path.relative_to(ROOT)),
                    "sha256": _source_sha256(path),
                    "sentinel": sentinel,
                    "sentinel_present": sentinel in text,
                }
            )
    return rows


def run_analysis() -> dict[str, Any]:
    matrix_rows, detail = sequence_and_matrix_checks()
    direction_rows = order_direction_checks()
    qiskit_rows = qiskit_registry_checks()
    source_rows = source_path_checks()
    all_passed = bool(
        all(row["passed"] for row in matrix_rows)
        and all(row["passed"] for row in direction_rows)
        and all(row["passed"] for row in qiskit_rows)
        and all(row["sentinel_present"] for row in source_rows)
    )
    maximum_unitary_residual = max(
        max(
            row["unmerged_vs_merged_unitary_residual"],
            row["sequential_vs_explicit_unitary_residual"],
            row["cached_vs_explicit_unitary_residual"],
            row["negative_time_vs_adjoint_residual"],
            row["inverse_sequence_vs_adjoint_residual"],
        )
        for row in matrix_rows
    )
    maximum_qiskit_residual = max(
        max(
            row["legacy_vs_explicit_unitary_residual"],
            row["precomputed_vs_explicit_unitary_residual"],
            row["legacy_vs_precomputed_unitary_residual"],
        )
        for row in qiskit_rows
    )
    zero_rows = [
        row for row in matrix_rows if row["formula_id"] == "zero_middle_control"
    ]
    return {
        "status": "complete" if all_passed else "failed",
        "audit_id": "B03",
        "scope": (
            "deterministic small-system equivalence audit; no molecular PF "
            "benchmark and no coefficient optimization"
        ),
        "created_at": datetime.now().astimezone().isoformat(),
        "time_hartree_inverse": TIME_VALUE,
        "tolerances": {
            "absolute_matrix_and_energy": ABSOLUTE_TOLERANCE,
            "step_weight": STEP_TOLERANCE,
            "wrong_order_control_minimum": ORDER_CONTROL_MINIMUM,
        },
        "formula_count": len(formula_definitions()),
        "matrix_case_count": len(matrix_rows),
        "qiskit_registry_case_count": len(qiskit_rows),
        "direction_probe_case_count": len(direction_rows),
        "all_matrix_cases_passed": all(row["passed"] for row in matrix_rows),
        "all_qiskit_cases_passed": all(row["passed"] for row in qiskit_rows),
        "all_direction_cases_passed": all(row["passed"] for row in direction_rows),
        "maximum_dense_unitary_residual": maximum_unitary_residual,
        "maximum_qiskit_unitary_residual": maximum_qiskit_residual,
        "maximum_delta_e_path_difference": max(
            row["maximum_delta_e_path_difference"] for row in matrix_rows
        ),
        "minimum_noncommuting_wrong_order_control_residual": min(
            row["wrong_right_product_control_residual"]
            for row in direction_rows
            if row["number_of_groups"] > 1
        ),
        "zero_coefficient_identity_rotations_retained": any(
            row["merged_rotation_count"]
            > row["effective_nonzero_merged_rotation_count"]
            for row in zero_rows
        ),
        "interpretation": {
            "written_vs_action_order": (
                "iterator steps F1,F2,... act on a state in that order, so the "
                "matrix is ... F2 F1; the non-palindromic control detects reversal"
            ),
            "negative_time": (
                "U(-tau)=U(tau)^dagger for the palindromic production sequences; "
                "for arbitrary sequences the inverse is obtained by negating and "
                "reversing the S2-block sequence"
            ),
            "qiskit_sign": (
                "Qiskit PauliEvolutionGate is exp(-iHt), so -tau is passed to "
                "compare with the repository dense exp(+iHtau) convention"
            ),
            "merge_decision": (
                "adjacent equal-group merging and repeated-S2 caching are exact "
                "within the recorded numerical tolerance"
                if all_passed
                else "at least one implementation path failed equivalence"
            ),
            "zero_weight_cost_note": (
                "the current iterator retains zero-weight steps; reported circuit "
                "rotation counts therefore include identity rotations unless a "
                "later compilation removes them"
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
        },
        "git": _git_state(),
        "_matrix_rows": matrix_rows,
        "_direction_rows": direction_rows,
        "_qiskit_rows": qiskit_rows,
        "_source_rows": source_rows,
        "_sequence_detail": detail,
    }


def _make_report(output: Path, result: dict[str, Any]) -> None:
    matrix_rows = result["_matrix_rows"]
    qiskit_rows = result["_qiskit_rows"]
    zero_rows = [
        row for row in matrix_rows if row["formula_id"] == "zero_middle_control"
    ]
    lines = [
        "# B03: S2列・積順序・隣接マージの等価性",
        "",
        f"- 状態: **{result['status']}**",
        f"- 評価時刻: `{TIME_VALUE}` Hartree^-1",
        f"- 密行列ケース: {len(matrix_rows)}（合格 {sum(row['passed'] for row in matrix_rows)}）",
        f"- Qiskit registryケース: {len(qiskit_rows)}（合格 {sum(row['passed'] for row in qiskit_rows)}）",
        f"- 最大密行列ユニタリ差: `{result['maximum_dense_unitary_residual']:.3e}`",
        f"- 最大Qiskitユニタリ差: `{result['maximum_qiskit_unitary_residual']:.3e}`",
        f"- 最大δE経路差: `{result['maximum_delta_e_path_difference']:.3e}` Hartree",
        "",
        "## 結論",
        "",
        (
            "明示展開したS2列、隣接同群をマージした列、逐次密行列builder、"
            "S2-cache builder、Qiskit grouped circuitは、検査した1〜3群と全係数列で"
            "同じユニタリおよび固有値シフトを与えた。したがって隣接マージとS2ブロック"
            "cacheは、この範囲では近似ではなく安全な高速化として採用できる。"
            if result["status"] == "complete"
            else "少なくとも一つの経路に不一致があり、高速化を同値とは判定できない。"
        ),
        "",
        "積順序は、iteratorが `F1, F2, ...` を返すとき状態にはその順で作用し、"
        "行列表現は `... F2 F1` となる。通常の対称PFは列を逆転しても同じため、"
        "非回文の診断列を別に使って誤った右乗算を検出した。",
        "",
        "`U(-τ)=U(τ)†` は回文のproduction列で成立した。一般の非回文列では、"
        "逆演算子は同じ列への負時刻ではなく `inverse_s2_sequence`（逆順かつ符号反転）"
        "で得られることも確認した。",
        "",
        "## 回転数",
        "",
        "| PF | 群数 | マージ前 | マージ後 | 非ゼロのみ |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in matrix_rows:
        lines.append(
            f"| {row['formula_id']} | {row['number_of_groups']} | "
            f"{row['raw_rotation_count']} | {row['merged_rotation_count']} | "
            f"{row['effective_nonzero_merged_rotation_count']} |"
        )
    lines.extend(
        [
            "",
            "ゼロ係数controlでは、現在のiteratorは重み0のステップを保持する。"
            "ユニタリは正しいが、runnerが返すrotation数はコンパイラ前のidentity rotationも"
            "数える。これは物理的不一致ではなく、コスト計数上の保守的な余分である。",
            "",
            "## ゼロ係数controlの要約",
            "",
        ]
    )
    for row in zero_rows:
        lines.append(
            f"- {row['number_of_groups']}群: merged rotation "
            f"{row['merged_rotation_count']}、非ゼロのみ "
            f"{row['effective_nonzero_merged_rotation_count']}、ユニタリ差 "
            f"{row['unmerged_vs_merged_unitary_residual']:.3e}"
        )
    lines.extend(
        [
            "",
            "## 範囲",
            "",
            "これは決定論的小行列監査であり、分子Hamiltonianの新規計算、係数探索、"
            "GPU計算は行っていない。詳細なstep列は `step_sequences.json`、全数値はCSVに保存した。",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    result = run_analysis()
    _write_csv(output / "matrix_equivalence.csv", result["_matrix_rows"])
    _write_csv(output / "order_direction_checks.csv", result["_direction_rows"])
    _write_csv(output / "qiskit_registry_equivalence.csv", result["_qiskit_rows"])
    _write_csv(output / "implementation_paths.csv", result["_source_rows"])
    _write_json(output / "step_sequences.json", result["_sequence_detail"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    _write_json(output / "audit.json", machine)
    _write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "audit_id": result["audit_id"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "git": result["git"],
            "environment": result["environment"],
            "existing_artifacts_overwritten": False,
            "new_molecular_pf_benchmark_performed": False,
            "gpu_used": False,
        },
    )
    _make_report(output, result)
    print(output)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
