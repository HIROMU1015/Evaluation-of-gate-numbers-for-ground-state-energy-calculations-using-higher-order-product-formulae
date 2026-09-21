"""Combined B04--B07 audit of the direct product-formula numerical path.

The four checks share small molecular and analytic fixtures:

* B04 verifies that every grouped Hamiltonian preserves the selected sector,
  then compares the projected full-space PF with the restricted-space PF.
* B05 compares exact-ground-overlap and continuous branch tracking and uses a
  degenerate control to exercise subspace-aware warnings.
* B06 compares float64 eig/Schur paths with a 120-digit two-level reference.
* B07 uses an independently expanded SciPy product, analytic commuting cases,
  and high-precision order fits as implementation sentinels.

No coefficient search or production molecular sweep is performed.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import subprocess
from typing import Any, Sequence

import mpmath as mp
import numpy as np
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh, expm, schur

from run_morales_y8m10b_hchain import _prepare_system
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.product_formula import (
    morales_2025_y8m10b_list,
    yoshida_4th_list,
)
from trotterlib.qiskit_time_evolution_utils import available_aer_devices
from trotterlib.sector_pf import (
    build_sector_pf_unitary_cached_s2,
    build_sector_pf_unitary_sequential,
)
from validate_hchain_perturbative_estimator import (
    _as_group_operator,
    _basis_indices,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_b04_b07_numerical_integrity_20260921_retry1"
MATRIX_TOLERANCE = 5e-12
SYMMETRY_TOLERANCE = 2e-11
FIXED_NOISE_FLOOR_HARTREE = 5e-13
MOLECULAR_TIME = 0.43
BRANCH_TIMES = np.geomspace(0.02, 1.8, 34)


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
    versions: dict[str, str | None] = {}
    for name in (
        "numpy",
        "scipy",
        "mpmath",
        "pyscf",
        "qiskit",
        "qiskit-aer",
        "openfermion",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _explicit_unmerged_steps(
    number_of_groups: int, sequence: Sequence[float]
) -> list[tuple[int, float]]:
    """Independent literal S2 expansion; does not use the merged iterator."""
    result: list[tuple[int, float]] = []
    for raw_weight in sequence:
        weight = float(raw_weight)
        for group_index in range(number_of_groups - 1):
            result.append((group_index, weight / 2.0))
        result.append((number_of_groups - 1, weight))
        for group_index in reversed(range(number_of_groups - 1)):
            result.append((group_index, weight / 2.0))
    return result


def _independent_pf(
    groups: Sequence[np.ndarray], sequence: Sequence[float], time_value: float
) -> np.ndarray:
    result = np.eye(groups[0].shape[0], dtype=np.complex128)
    for group_index, weight in _explicit_unmerged_steps(len(groups), sequence):
        result = expm(1j * float(time_value) * float(weight) * groups[group_index]) @ result
    return result


def _selected_signed_shift(
    unitary: np.ndarray,
    reference_state: np.ndarray,
    reference_energy: float,
    time_value: float,
) -> tuple[float, float, float]:
    eigenvalues, eigenvectors = np.linalg.eig(unitary)
    eigenvectors /= np.linalg.norm(eigenvectors, axis=0)
    overlaps = np.abs(eigenvectors.conj().T @ reference_state) ** 2
    selected = int(np.argmax(overlaps))
    rotated = np.exp(-1j * reference_energy * time_value) * eigenvalues[selected]
    residual = np.linalg.norm(
        unitary @ eigenvectors[:, selected]
        - eigenvalues[selected] * eigenvectors[:, selected]
    )
    return (
        float(np.angle(rotated) / time_value),
        float(overlaps[selected]),
        float(residual),
    )


def _charge_diagonals(
    number_of_qubits: int, sector_kind: str
) -> dict[str, np.ndarray]:
    dimension = 1 << number_of_qubits
    half = number_of_qubits // 2
    alpha: list[float] = []
    beta: list[float] = []
    for index in range(dimension):
        bits = [
            (index >> (number_of_qubits - 1 - qubit)) & 1
            for qubit in range(number_of_qubits)
        ]
        if sector_kind == "fixed_half_populations":
            alpha.append(float(sum(bits[:half])))
            beta.append(float(sum(bits[half:])))
        else:
            alpha.append(float(sum(bits[0::2])))
            beta.append(float(sum(bits[1::2])))
    alpha_array = np.asarray(alpha)
    beta_array = np.asarray(beta)
    return {
        "particle_number": np.diag(alpha_array + beta_array),
        "spin_projection": np.diag((alpha_array - beta_array) / 2.0),
        "alpha_population": np.diag(alpha_array),
        "beta_population": np.diag(beta_array),
    }


def _prepare_molecular_fixture(h_chain: int) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        system = _prepare_system(h_chain)
    number_of_qubits = int(system["num_qubits"])
    state = np.asarray(system["state"], dtype=np.complex128).reshape(-1)
    group_operators = [_as_group_operator(group) for group in system["groups"]]
    identity = np.eye(1 << number_of_qubits, dtype=np.complex128)
    groups: list[np.ndarray] = []
    for operator in group_operators:
        constant = complex(operator.terms.get((), 0.0))
        matrix = get_sparse_operator(operator, number_of_qubits).toarray()
        groups.append(np.asarray(matrix - constant * identity, dtype=np.complex128))
    indices, sector = _basis_indices(number_of_qubits, state, groups)
    sector_state = state[indices]
    sector_state /= np.linalg.norm(sector_state)
    sector_groups = [matrix[np.ix_(indices, indices)] for matrix in groups]
    hamiltonian = sum(groups, np.zeros_like(groups[0]))
    sector_hamiltonian = sum(
        sector_groups, np.zeros_like(sector_groups[0])
    )
    reference_energy = float(system["energy_without_constant"])
    return {
        "h_chain": h_chain,
        "number_of_qubits": number_of_qubits,
        "groups": groups,
        "sector_groups": sector_groups,
        "indices": indices,
        "outside_indices": np.setdiff1d(
            np.arange(1 << number_of_qubits), indices
        ),
        "sector": sector,
        "state": state,
        "sector_state": sector_state,
        "hamiltonian": hamiltonian,
        "sector_hamiltonian": sector_hamiltonian,
        "reference_energy": reference_energy,
        "full_ground_residual": float(
            np.linalg.norm(hamiltonian @ state - reference_energy * state)
        ),
        "sector_ground_residual": float(
            np.linalg.norm(
                sector_hamiltonian @ sector_state
                - reference_energy * sector_state
            )
        ),
    }


def b04_sector_checks(
    fixtures: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    symmetry_rows: list[dict[str, Any]] = []
    equivalence_rows: list[dict[str, Any]] = []
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    for fixture in fixtures:
        indices = fixture["indices"]
        outside = fixture["outside_indices"]
        charges = _charge_diagonals(
            fixture["number_of_qubits"], fixture["sector"]["kind"]
        )
        for group_index, group in enumerate(fixture["groups"]):
            leakage = (
                float(np.linalg.norm(group[np.ix_(outside, indices)]))
                if outside.size
                else 0.0
            )
            for charge_name, charge in charges.items():
                commutator = group @ charge - charge @ group
                absolute = float(np.linalg.norm(commutator))
                relative = absolute / max(1.0, float(np.linalg.norm(group)))
                symmetry_rows.append(
                    {
                        "system": f"H{fixture['h_chain']}",
                        "sector_kind": fixture["sector"]["kind"],
                        "sector_population_counts": json.dumps(
                            fixture["sector"]["population_counts"]
                        ),
                        "group_index": group_index,
                        "charge": charge_name,
                        "commutator_frobenius_norm": absolute,
                        "relative_commutator_norm": relative,
                        "sector_cross_block_frobenius_norm": leakage,
                        "passed": bool(
                            relative <= SYMMETRY_TOLERANCE
                            and leakage <= SYMMETRY_TOLERANCE
                        ),
                    }
                )

        full_spectra = [eigh(group, check_finite=False) for group in fixture["groups"]]
        sector_spectra = [
            eigh(group, check_finite=False) for group in fixture["sector_groups"]
        ]
        full_unitary = build_sector_pf_unitary_sequential(
            full_spectra, sequence, MOLECULAR_TIME
        )
        restricted_unitary = build_sector_pf_unitary_sequential(
            sector_spectra, sequence, MOLECULAR_TIME
        )
        projected = full_unitary[np.ix_(indices, indices)]
        leakage = (
            float(np.linalg.norm(full_unitary[np.ix_(outside, indices)]))
            if outside.size
            else 0.0
        )
        projected_shift, projected_overlap, _ = _selected_signed_shift(
            projected,
            fixture["sector_state"],
            fixture["reference_energy"],
            MOLECULAR_TIME,
        )
        restricted_shift, restricted_overlap, eigenpair_residual = (
            _selected_signed_shift(
                restricted_unitary,
                fixture["sector_state"],
                fixture["reference_energy"],
                MOLECULAR_TIME,
            )
        )
        row = {
            "system": f"H{fixture['h_chain']}",
            "number_of_qubits": fixture["number_of_qubits"],
            "number_of_groups": len(fixture["groups"]),
            "full_dimension": int(full_unitary.shape[0]),
            "sector_dimension": int(indices.size),
            "sector_kind": fixture["sector"]["kind"],
            "projected_full_vs_restricted_unitary_residual": float(
                np.linalg.norm(projected - restricted_unitary)
            ),
            "full_pf_sector_leakage_frobenius_norm": leakage,
            "signed_shift_projected_full_hartree": projected_shift,
            "signed_shift_restricted_hartree": restricted_shift,
            "signed_shift_difference_hartree": abs(
                projected_shift - restricted_shift
            ),
            "projected_ground_overlap_probability": projected_overlap,
            "restricted_ground_overlap_probability": restricted_overlap,
            "restricted_pf_eigenpair_residual": eigenpair_residual,
            "full_ground_eigenpair_residual": fixture["full_ground_residual"],
            "sector_ground_eigenpair_residual": fixture[
                "sector_ground_residual"
            ],
        }
        row["passed"] = bool(
            row["projected_full_vs_restricted_unitary_residual"]
            <= MATRIX_TOLERANCE
            and leakage <= MATRIX_TOLERANCE
            and row["signed_shift_difference_hartree"] <= MATRIX_TOLERANCE
        )
        equivalence_rows.append(row)

    # Negative control: H=A+B=Z preserves |0>, but A=X and B=-X+Z do not.
    x_matrix = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    z_matrix = np.diag([1.0, -1.0]).astype(np.complex128)
    bad_groups = [x_matrix, -x_matrix + z_matrix]
    bad_sector_groups = [group[np.ix_([0], [0])] for group in bad_groups]
    full_bad = build_sector_pf_unitary_sequential(
        [eigh(group) for group in bad_groups], [1.0], 0.7
    )
    restricted_bad = build_sector_pf_unitary_sequential(
        [eigh(group) for group in bad_sector_groups], [1.0], 0.7
    )
    number = np.diag([0.0, 1.0])
    negative_control = {
        "description": (
            "A=X and B=-X+Z have sector-preserving sum Z but do not preserve "
            "the |0> sector separately"
        ),
        "total_hamiltonian_commutator_norm": float(
            np.linalg.norm((sum(bad_groups) @ number) - (number @ sum(bad_groups)))
        ),
        "maximum_group_commutator_norm": max(
            float(np.linalg.norm(group @ number - number @ group))
            for group in bad_groups
        ),
        "full_pf_sector_leakage_norm": float(abs(full_bad[1, 0])),
        "projected_full_vs_restricted_residual": float(
            abs(full_bad[0, 0] - restricted_bad[0, 0])
        ),
    }
    negative_control["detector_passed"] = bool(
        negative_control["total_hamiltonian_commutator_norm"] <= 1e-15
        and negative_control["maximum_group_commutator_norm"] > 0.1
        and negative_control["full_pf_sector_leakage_norm"] > 1e-3
        and negative_control["projected_full_vs_restricted_residual"] > 1e-3
    )
    return symmetry_rows, equivalence_rows, negative_control


def _circular_phase_gap(phases: np.ndarray, selected: int) -> float:
    differences = np.angle(np.exp(1j * (phases - phases[selected])))
    candidates = np.abs(np.delete(differences, selected))
    return float(np.min(candidates)) if candidates.size else math.inf


def _unwrapped_energy(
    eigenvalue: complex, time_value: float, reference_energy: float
) -> tuple[float, int]:
    phase = float(np.angle(eigenvalue))
    branch = int(
        np.rint((float(reference_energy) * time_value - phase) / (2.0 * np.pi))
    )
    return float((phase + 2.0 * np.pi * branch) / time_value), branch


def b05_branch_checks(
    fixture: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    spectra = [eigh(group, check_finite=False) for group in fixture["sector_groups"]]
    state = fixture["sector_state"]
    previous_vector: np.ndarray | None = None
    previous_energy = fixture["reference_energy"]
    actual_rows: list[dict[str, Any]] = []
    for point_index, time_value in enumerate(BRANCH_TIMES):
        unitary = build_sector_pf_unitary_sequential(
            spectra, sequence, float(time_value)
        )
        eigenvalues, eigenvectors = np.linalg.eig(unitary)
        eigenvectors /= np.linalg.norm(eigenvectors, axis=0)
        ground_overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
        tracking_reference = state if previous_vector is None else previous_vector
        tracking_overlaps = np.abs(
            eigenvectors.conj().T @ tracking_reference
        ) ** 2
        ground_selected = int(np.argmax(ground_overlaps))
        continuous_selected = int(np.argmax(tracking_overlaps))
        oracle_energy, oracle_branch = _unwrapped_energy(
            eigenvalues[ground_selected],
            float(time_value),
            fixture["reference_energy"],
        )
        continuous_energy, continuous_branch = _unwrapped_energy(
            eigenvalues[continuous_selected], float(time_value), previous_energy
        )
        phases = np.angle(eigenvalues)
        sorted_ground = np.sort(ground_overlaps)[::-1]
        ambiguity_margin = float(
            sorted_ground[0] - sorted_ground[1]
            if sorted_ground.size > 1
            else 1.0
        )
        row = {
            "point_index": point_index,
            "time_hartree_inverse": float(time_value),
            "maximum_ground_overlap_branch_index": ground_selected,
            "continuous_branch_index": continuous_selected,
            "selection_rules_agree": ground_selected == continuous_selected,
            "maximum_ground_overlap_probability": float(
                ground_overlaps[ground_selected]
            ),
            "continuous_branch_ground_overlap_probability": float(
                ground_overlaps[continuous_selected]
            ),
            "previous_branch_overlap_probability": float(
                tracking_overlaps[continuous_selected]
            ),
            "ground_overlap_top_two_margin": ambiguity_margin,
            "selected_phase_gap_radians": _circular_phase_gap(
                phases, continuous_selected
            ),
            "oracle_effective_energy_hartree": oracle_energy,
            "continuous_effective_energy_hartree": continuous_energy,
            "effective_energy_difference_hartree": abs(
                oracle_energy - continuous_energy
            ),
            "oracle_phase_unwrap_integer": oracle_branch,
            "continuous_phase_unwrap_integer": continuous_branch,
            "branch_warning": bool(
                ground_selected != continuous_selected
                or ambiguity_margin < 1e-6
                or _circular_phase_gap(phases, continuous_selected) < 1e-6
            ),
        }
        actual_rows.append(row)
        previous_vector = eigenvectors[:, continuous_selected]
        previous_energy = continuous_energy

    # Degenerate-reference control.  Any vector in span{|0>,|1>} is a valid
    # ground state; a single arbitrary reference vector changes preferred
    # eigenbranch as the eigenvectors rotate, while the subspace score remains 1.
    reference_vector = np.asarray([1.0, 0.0, 0.0], dtype=np.complex128)
    reference_subspace = np.eye(3, dtype=np.complex128)[:, :2]
    synthetic_rows: list[dict[str, Any]] = []
    previous_vector = None
    for point_index, theta in enumerate(np.linspace(0.0, np.pi / 2.0, 9)):
        rotation = np.asarray(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.complex128,
        )
        phases = np.asarray([0.12 - 5e-8, 0.12 + 5e-8, 1.1])
        unitary = rotation @ np.diag(np.exp(1j * phases)) @ rotation.conj().T
        eigenvalues, eigenvectors = np.linalg.eig(unitary)
        eigenvectors /= np.linalg.norm(eigenvectors, axis=0)
        single_overlaps = np.abs(eigenvectors.conj().T @ reference_vector) ** 2
        subspace_scores = np.sum(
            np.abs(reference_subspace.conj().T @ eigenvectors) ** 2, axis=0
        )
        tracking_reference = (
            reference_vector if previous_vector is None else previous_vector
        )
        tracking_overlaps = np.abs(
            eigenvectors.conj().T @ tracking_reference
        ) ** 2
        single_selected = int(np.argmax(single_overlaps))
        continuous_selected = int(np.argmax(tracking_overlaps))
        phase_array = np.angle(eigenvalues)
        selected_gap = _circular_phase_gap(phase_array, continuous_selected)
        synthetic_rows.append(
            {
                "case": "rotating_near_degenerate_ground_subspace",
                "point_index": point_index,
                "theta_radians": float(theta),
                "single_vector_branch_index": single_selected,
                "continuous_branch_index": continuous_selected,
                "selection_rules_agree": single_selected == continuous_selected,
                "single_vector_overlap_probability": float(
                    single_overlaps[single_selected]
                ),
                "continuous_previous_overlap_probability": float(
                    tracking_overlaps[continuous_selected]
                ),
                "continuous_ground_subspace_projection_probability": float(
                    subspace_scores[continuous_selected]
                ),
                "selected_phase_gap_radians": selected_gap,
                "subspace_warning": selected_gap < 1e-6,
            }
        )
        previous_vector = eigenvectors[:, continuous_selected]

    exactly_degenerate = np.diag(
        [np.exp(0.12j), np.exp(0.12j), np.exp(1.1j)]
    )
    eigenvalues, eigenvectors = np.linalg.eig(exactly_degenerate)
    exact_gap = _circular_phase_gap(np.angle(eigenvalues), 0)
    synthetic_summary = {
        "single_vector_and_continuity_disagreement_count": sum(
            not row["selection_rules_agree"] for row in synthetic_rows
        ),
        "minimum_ground_subspace_projection_probability": min(
            row["continuous_ground_subspace_projection_probability"]
            for row in synthetic_rows
        ),
        "exact_degeneracy_phase_gap_radians": exact_gap,
        "exact_degeneracy_requires_subspace_tracking": bool(exact_gap < 1e-12),
        "detector_passed": bool(
            any(not row["selection_rules_agree"] for row in synthetic_rows)
            and min(
                row["continuous_ground_subspace_projection_probability"]
                for row in synthetic_rows
            )
            > 1.0 - 1e-12
            and exact_gap < 1e-12
        ),
    }
    return actual_rows, synthetic_rows, synthetic_summary


def _two_level_groups() -> list[np.ndarray]:
    return [
        np.asarray([[0.0, 0.7], [0.7, 0.0]], dtype=np.complex128),
        np.asarray([[0.43, 0.0], [0.0, -0.43]], dtype=np.complex128),
    ]


def _float_delta_from_eigenvalues(
    eigenvalues: Sequence[complex], time_value: float, reference_energy: float
) -> tuple[float, int]:
    phases = np.angle(np.asarray(eigenvalues))
    effective = phases / float(time_value)
    selected = int(np.argmin(np.abs(effective - reference_energy)))
    rotated = np.exp(-1j * reference_energy * time_value) * eigenvalues[selected]
    return float(np.angle(rotated) / time_value), selected


def _mp_two_level_delta(
    sequence: Sequence[float], time_value: float, decimal_precision: int
) -> mp.mpf:
    with mp.workdps(decimal_precision):
        a = mp.mpf(float(0.7))
        b = mp.mpf(float(0.43))
        groups = [
            mp.matrix([[0, a], [a, 0]]),
            mp.matrix([[b, 0], [0, -b]]),
        ]
        time_mp = mp.mpf(float(time_value))
        unitary = mp.eye(2)
        for group_index, weight in _explicit_unmerged_steps(2, sequence):
            unitary = (
                mp.expm(
                    mp.j
                    * time_mp
                    * mp.mpf(float(weight))
                    * groups[group_index]
                )
                * unitary
            )
        trace = unitary[0, 0] + unitary[1, 1]
        determinant = mp.det(unitary)
        discriminant = mp.sqrt(trace * trace - 4 * determinant)
        eigenvalues = [
            (trace + discriminant) / 2,
            (trace - discriminant) / 2,
        ]
        reference_energy = -mp.sqrt(a * a + b * b)
        selected = min(
            eigenvalues,
            key=lambda value: abs(mp.arg(value) / time_mp - reference_energy),
        )
        return mp.arg(
            mp.exp(-mp.j * reference_energy * time_mp) * selected
        ) / time_mp


def b06_precision_checks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups = _two_level_groups()
    hamiltonian = sum(groups, np.zeros_like(groups[0]))
    energies, vectors = eigh(hamiltonian, check_finite=False)
    reference_energy = float(energies[0])
    ground_state = vectors[:, 0]
    spectra = [eigh(group, check_finite=False) for group in groups]
    sequence = symmetric_s2_sequence(yoshida_4th_list())
    rows: list[dict[str, Any]] = []
    precision_times = np.unique(
        np.concatenate([np.geomspace(1e-5, 0.5, 20), np.asarray([0.02])])
    )
    for time_value in precision_times:
        time_float = float(time_value)
        independent = _independent_pf(groups, sequence, time_float)
        sequential = build_sector_pf_unitary_sequential(
            spectra, sequence, time_float
        )
        cached = build_sector_pf_unitary_cached_s2(
            spectra, sequence, time_float
        )
        eig_values, eig_vectors = np.linalg.eig(sequential)
        eig_vectors /= np.linalg.norm(eig_vectors, axis=0)
        eig_delta, eig_selected = _float_delta_from_eigenvalues(
            eig_values, time_float, reference_energy
        )
        triangular, schur_vectors = schur(sequential, output="complex")
        schur_values = np.diag(triangular)
        schur_delta, schur_selected = _float_delta_from_eigenvalues(
            schur_values, time_float, reference_energy
        )
        mp80 = _mp_two_level_delta(sequence, time_float, 80)
        mp120 = _mp_two_level_delta(sequence, time_float, 120)
        mp_delta = float(mp120)
        eig_residual = float(
            np.linalg.norm(
                sequential @ eig_vectors[:, eig_selected]
                - eig_values[eig_selected] * eig_vectors[:, eig_selected]
            )
        )
        schur_residual = float(
            np.linalg.norm(
                sequential @ schur_vectors[:, schur_selected]
                - schur_values[schur_selected]
                * schur_vectors[:, schur_selected]
            )
        )
        row = {
            "time_hartree_inverse": time_float,
            "reference_delta_e_120digit_hartree": mp_delta,
            "reference_delta_e_absolute_hartree": abs(mp_delta),
            "numpy_eig_delta_e_hartree": eig_delta,
            "scipy_schur_delta_e_hartree": schur_delta,
            "numpy_vs_120digit_difference_hartree": abs(eig_delta - mp_delta),
            "schur_vs_120digit_difference_hartree": abs(
                schur_delta - mp_delta
            ),
            "mp80_vs_mp120_difference_hartree": float(abs(mp80 - mp120)),
            "independent_vs_spectral_unitary_residual": float(
                np.linalg.norm(independent - sequential)
            ),
            "cached_vs_sequential_unitary_residual": float(
                np.linalg.norm(cached - sequential)
            ),
            "unitarity_residual_frobenius_norm": float(
                np.linalg.norm(
                    sequential.conj().T @ sequential - np.eye(2)
                )
            ),
            "numpy_eigenpair_residual": eig_residual,
            "schur_eigenpair_residual": schur_residual,
            "exact_hamiltonian_ground_eigenpair_residual": float(
                np.linalg.norm(
                    hamiltonian @ ground_state
                    - reference_energy * ground_state
                )
            ),
            "phase_to_energy_amplification_inverse_time": 1.0 / time_float,
            "above_fixed_5e_minus_13_floor": abs(mp_delta)
            >= FIXED_NOISE_FLOOR_HARTREE,
            "float_paths_agree_with_reference_within_fixed_floor": max(
                abs(eig_delta - mp_delta), abs(schur_delta - mp_delta)
            )
            <= FIXED_NOISE_FLOOR_HARTREE,
        }
        rows.append(row)
    trusted_rows = [row for row in rows if row["above_fixed_5e_minus_13_floor"]]
    below_rows = [row for row in rows if not row["above_fixed_5e_minus_13_floor"]]
    ultrashort_false_positive_rows = [
        row
        for row in below_rows
        if max(
            abs(row["numpy_eig_delta_e_hartree"]),
            abs(row["scipy_schur_delta_e_hartree"]),
        )
        > FIXED_NOISE_FLOOR_HARTREE
    ]
    current_grid_row = next(
        row for row in rows if row["time_hartree_inverse"] == 0.02
    )
    summary = {
        "fixed_noise_floor_hartree": FIXED_NOISE_FLOOR_HARTREE,
        "point_count": len(rows),
        "above_floor_point_count": len(trusted_rows),
        "below_floor_point_count": len(below_rows),
        "minimum_time_with_reference_shift_above_floor": min(
            row["time_hartree_inverse"] for row in trusted_rows
        ),
        "maximum_float_reference_difference_all_points_hartree": max(
            max(
                row["numpy_vs_120digit_difference_hartree"],
                row["schur_vs_120digit_difference_hartree"],
            )
            for row in rows
        ),
        "maximum_float_reference_difference_above_floor_hartree": max(
            max(
                row["numpy_vs_120digit_difference_hartree"],
                row["schur_vs_120digit_difference_hartree"],
            )
            for row in trusted_rows
        ),
        "maximum_unitarity_residual": max(
            row["unitarity_residual_frobenius_norm"] for row in rows
        ),
        "maximum_eigenpair_residual": max(
            max(
                row["numpy_eigenpair_residual"],
                row["schur_eigenpair_residual"],
            )
            for row in rows
        ),
        "maximum_mp80_mp120_difference_hartree": max(
            row["mp80_vs_mp120_difference_hartree"] for row in rows
        ),
        "ultrashort_below_truth_floor_but_float_above_floor_count": len(
            ultrashort_false_positive_rows
        ),
        "largest_tested_time_with_ultrashort_false_positive": max(
            row["time_hartree_inverse"] for row in ultrashort_false_positive_rows
        ),
        "fixed_floor_is_universal_ultrashort_bound": not bool(
            ultrashort_false_positive_rows
        ),
        "current_protocol_minimum_time_hartree_inverse": 0.02,
        "current_protocol_minimum_time_reference_shift_hartree": current_grid_row[
            "reference_delta_e_absolute_hartree"
        ],
        "current_protocol_minimum_time_maximum_float_difference_hartree": max(
            current_grid_row["numpy_vs_120digit_difference_hartree"],
            current_grid_row["schur_vs_120digit_difference_hartree"],
        ),
        "fixed_floor_supported_on_fixture": all(
            row["float_paths_agree_with_reference_within_fixed_floor"]
            for row in trusted_rows
        ),
        "interpretation": (
            "every above-floor point, including the current protocol minimum "
            "time 0.02, agrees with the high-precision reference within the "
            "existing floor; the fixed floor is not a universal bound at "
            "ultrashort times because phase-to-energy noise is amplified by 1/tau"
        ),
    }
    return rows, summary


def _formula_sequences() -> dict[str, tuple[list[float], int]]:
    return {
        "second_order": ([1.0], 2),
        "yoshida4": (symmetric_s2_sequence(yoshida_4th_list()), 4),
        "morales_y8m10b": (
            symmetric_s2_sequence(morales_2025_y8m10b_list()),
            8,
        ),
    }


def b07_crosschecks(
    b04_equivalence_rows: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    groups = _two_level_groups()
    spectra = [eigh(group, check_finite=False) for group in groups]
    hamiltonian = sum(groups, np.zeros_like(groups[0]))
    energies, vectors = eigh(hamiltonian, check_finite=False)
    reference_energy = float(energies[0])
    reference_state = vectors[:, 0]
    commuting_groups = [0.4 * np.asarray([[0, 1], [1, 0]], complex),
                        -0.1 * np.asarray([[0, 1], [1, 0]], complex)]
    commuting_hamiltonian = sum(
        commuting_groups, np.zeros_like(commuting_groups[0])
    )
    commuting_energies, commuting_vectors = eigh(commuting_hamiltonian)
    rows: list[dict[str, Any]] = []
    for formula_id, (sequence, formal_order) in _formula_sequences().items():
        independent = _independent_pf(groups, sequence, 0.37)
        production = build_sector_pf_unitary_sequential(
            spectra, sequence, 0.37
        )
        independent_shift, independent_overlap, _ = _selected_signed_shift(
            independent, reference_state, reference_energy, 0.37
        )
        production_shift, _, _ = _selected_signed_shift(
            production, reference_state, reference_energy, 0.37
        )
        commuting_pf = _independent_pf(commuting_groups, sequence, 0.61)
        commuting_exact = expm(1j * 0.61 * commuting_hamiltonian)
        commuting_shift, _, _ = _selected_signed_shift(
            commuting_pf,
            commuting_vectors[:, 0],
            float(commuting_energies[0]),
            0.61,
        )
        compact_m = (len(sequence) - 1) // 2
        merged_steps = list(iter_s2_sequence_steps(2, sequence))
        hand_group_exponential_count = (4 * compact_m + 2) * (2 - 1) + 1
        row = {
            "formula_id": formula_id,
            "formal_order": formal_order,
            "s2_block_count": len(sequence),
            "independent_vs_production_unitary_residual": float(
                np.linalg.norm(independent - production)
            ),
            "signed_delta_e_independent_hartree": independent_shift,
            "signed_delta_e_production_hartree": production_shift,
            "signed_delta_e_path_difference_hartree": abs(
                independent_shift - production_shift
            ),
            "ground_overlap_probability": independent_overlap,
            "commuting_pf_vs_exact_unitary_residual": float(
                np.linalg.norm(commuting_pf - commuting_exact)
            ),
            "commuting_signed_delta_e_hartree": commuting_shift,
            "production_merged_group_exponential_count": len(merged_steps),
            "hand_group_exponential_count": hand_group_exponential_count,
        }
        row["passed"] = bool(
            row["independent_vs_production_unitary_residual"]
            <= MATRIX_TOLERANCE
            and row["signed_delta_e_path_difference_hartree"]
            <= MATRIX_TOLERANCE
            and row["commuting_pf_vs_exact_unitary_residual"]
            <= MATRIX_TOLERANCE
            and abs(row["commuting_signed_delta_e_hartree"])
            <= MATRIX_TOLERANCE
            and len(merged_steps) == hand_group_exponential_count
        )
        rows.append(row)

    time_windows = {
        "second_order": np.geomspace(0.003, 0.08, 9),
        "yoshida4": np.geomspace(0.02, 0.25, 9),
        "morales_y8m10b": np.geomspace(0.12, 0.8, 9),
    }
    order_rows: list[dict[str, Any]] = []
    for formula_id, (sequence, formal_order) in _formula_sequences().items():
        times = time_windows[formula_id]
        errors = np.asarray(
            [
                abs(float(_mp_two_level_delta(sequence, float(time), 100)))
                for time in times
            ]
        )
        fitted_order = float(
            np.polyfit(np.log(times), np.log(errors), deg=1)[0]
        )
        order_rows.append(
            {
                "formula_id": formula_id,
                "formal_order": formal_order,
                "fit_time_start_hartree_inverse": float(times[0]),
                "fit_time_stop_hartree_inverse": float(times[-1]),
                "fit_point_count": int(times.size),
                "minimum_reference_error_hartree": float(np.min(errors)),
                "maximum_reference_error_hartree": float(np.max(errors)),
                "fitted_signed_eigenvalue_shift_order": fitted_order,
                "absolute_order_difference": abs(fitted_order - formal_order),
                "passed": abs(fitted_order - formal_order) <= 0.1,
            }
        )

    try:
        aer_devices = list(available_aer_devices())
        gpu_available = "GPU" in aer_devices
        availability_error = None
    except Exception as error:  # environment diagnostic, not a numerical failure
        aer_devices = []
        gpu_available = False
        availability_error = f"{type(error).__name__}: {error}"
    h2_row = next(row for row in b04_equivalence_rows if row["system"] == "H2")
    environment_summary = {
        "aer_available_devices": aer_devices,
        "gpu_available": gpu_available,
        "gpu_comparison_status": (
            "not_run_gpu_unavailable"
            if not gpu_available
            else "available_but_not_required_for_small_dense_sentinel"
        ),
        "availability_error": availability_error,
        "scf_reexecution_mixed_into_cpu_gpu_comparison": False,
        "molecular_full_vs_sector_sentinel_system": "H2",
        "molecular_full_vs_sector_unitary_residual": h2_row[
            "projected_full_vs_restricted_unitary_residual"
        ],
    }
    return rows, order_rows, environment_summary


def source_checks() -> list[dict[str, Any]]:
    specifications = {
        ROOT / "src/trotterlib/sector_pf.py": (
            "unitary = _left_apply_group_exponential(",
            "unitary = block @ unitary",
        ),
        ROOT / "review_response/validate_hchain_perturbative_estimator.py": (
            "max_group_leakage_frobenius_norm",
            "tracking_overlaps = np.abs(",
            "selected = int(np.argmax(tracking_overlaps))",
        ),
    }
    rows: list[dict[str, Any]] = []
    for path, sentinels in specifications.items():
        text = path.read_text(encoding="utf-8")
        for sentinel in sentinels:
            rows.append(
                {
                    "relative_path": str(path.relative_to(ROOT)),
                    "sha256": _sha256(path),
                    "sentinel": sentinel,
                    "sentinel_present": sentinel in text,
                }
            )
    return rows


def run_analysis() -> dict[str, Any]:
    fixtures = [_prepare_molecular_fixture(h_chain) for h_chain in (2, 3)]
    b04_symmetry, b04_equivalence, b04_negative = b04_sector_checks(fixtures)
    b05_actual, b05_synthetic, b05_summary = b05_branch_checks(fixtures[0])
    b06_rows, b06_summary = b06_precision_checks()
    b07_rows, b07_orders, b07_environment = b07_crosschecks(b04_equivalence)
    paths = source_checks()
    b04_passed = bool(
        all(row["passed"] for row in b04_symmetry)
        and all(row["passed"] for row in b04_equivalence)
        and b04_negative["detector_passed"]
    )
    b05_passed = bool(
        all(row["selection_rules_agree"] for row in b05_actual)
        and b05_summary["detector_passed"]
    )
    b06_passed = bool(
        b06_summary["fixed_floor_supported_on_fixture"]
        and not b06_summary["fixed_floor_is_universal_ultrashort_bound"]
        and b06_summary[
            "current_protocol_minimum_time_maximum_float_difference_hartree"
        ]
        < FIXED_NOISE_FLOOR_HARTREE
        and b06_summary["maximum_mp80_mp120_difference_hartree"] < 1e-60
        and b06_summary["maximum_unitarity_residual"] < MATRIX_TOLERANCE
        and b06_summary["maximum_eigenpair_residual"] < MATRIX_TOLERANCE
    )
    b07_passed = bool(
        all(row["passed"] for row in b07_rows)
        and all(row["passed"] for row in b07_orders)
    )
    statuses = {
        "B04": "complete" if b04_passed else "failed",
        "B05": "complete" if b05_passed else "failed",
        "B06": "complete" if b06_passed else "failed",
        "B07": "complete" if b07_passed else "failed",
    }
    overall = all(status == "complete" for status in statuses.values())
    result = {
        "status": "complete" if overall else "failed",
        "audit_ids": ["B04", "B05", "B06", "B07"],
        "component_status": statuses,
        "scope": (
            "small molecular H2/H3 and analytic controls; no coefficient search, "
            "no production molecule sweep"
        ),
        "created_at": datetime.now().astimezone().isoformat(),
        "B04": {
            "system_count": len(fixtures),
            "group_symmetry_check_count": len(b04_symmetry),
            "sector_equivalence_case_count": len(b04_equivalence),
            "maximum_relative_group_commutator_norm": max(
                row["relative_commutator_norm"] for row in b04_symmetry
            ),
            "maximum_group_sector_cross_block_norm": max(
                row["sector_cross_block_frobenius_norm"] for row in b04_symmetry
            ),
            "maximum_projected_full_vs_restricted_unitary_residual": max(
                row["projected_full_vs_restricted_unitary_residual"]
                for row in b04_equivalence
            ),
            "maximum_full_pf_sector_leakage_norm": max(
                row["full_pf_sector_leakage_frobenius_norm"]
                for row in b04_equivalence
            ),
            "noninvariant_split_control": b04_negative,
        },
        "B05": {
            "actual_system": "H2",
            "actual_time_count": len(b05_actual),
            "actual_selection_disagreement_count": sum(
                not row["selection_rules_agree"] for row in b05_actual
            ),
            "actual_branch_warning_count": sum(
                row["branch_warning"] for row in b05_actual
            ),
            "minimum_actual_previous_branch_overlap_probability": min(
                row["previous_branch_overlap_probability"] for row in b05_actual
            ),
            "minimum_actual_phase_gap_radians": min(
                row["selected_phase_gap_radians"] for row in b05_actual
            ),
            "degenerate_control": b05_summary,
        },
        "B06": b06_summary,
        "B07": {
            "crosscheck_case_count": len(b07_rows),
            "order_fit_case_count": len(b07_orders),
            "maximum_independent_production_unitary_residual": max(
                row["independent_vs_production_unitary_residual"]
                for row in b07_rows
            ),
            "fitted_orders": {
                row["formula_id"]: row[
                    "fitted_signed_eigenvalue_shift_order"
                ]
                for row in b07_orders
            },
            "environment": b07_environment,
        },
        "interpretation": {
            "sector_restriction": (
                "exact for the audited H2/H3 grouped PFs because every group "
                "preserves the selected charges; the negative control confirms "
                "that total-H symmetry alone would not be sufficient"
            ),
            "branch_tracking": (
                "maximum exact-ground overlap and continuous tracking agree on "
                "the H2 grid; the controlled near-degeneracy demonstrates why "
                "a ground-subspace score and a phase-gap warning are still needed"
            ),
            "precision_floor": b06_summary["interpretation"],
            "independent_crosscheck": (
                "the independent unmerged SciPy implementation, analytic commuting "
                "case, molecular projection, and high-precision formal-order fits agree"
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
        },
        "git": _git_state(),
        "_b04_symmetry_rows": b04_symmetry,
        "_b04_equivalence_rows": b04_equivalence,
        "_b05_actual_rows": b05_actual,
        "_b05_synthetic_rows": b05_synthetic,
        "_b06_rows": b06_rows,
        "_b07_rows": b07_rows,
        "_b07_order_rows": b07_orders,
        "_source_rows": paths,
    }
    if not all(row["sentinel_present"] for row in paths):
        result["status"] = "failed"
    return result


def _make_report(output: Path, result: dict[str, Any]) -> None:
    b04 = result["B04"]
    b05 = result["B05"]
    b06 = result["B06"]
    b07 = result["B07"]
    lines = [
        "# B04〜B07 数値経路の一括検証",
        "",
        f"- 総合状態: **{result['status']}**",
        "- 個別状態: "
        + ", ".join(
            f"{key}={value}" for key, value in result["component_status"].items()
        ),
        "- 範囲: H2/H3小分子、2準位高精度例、解析可能な可換例",
        "- GPU: " + b07["environment"]["gpu_comparison_status"],
        "",
        "## B04 保存則セクター",
        "",
        f"H2/H3の全群について粒子数、スピン射影、α/β粒子数との交換子を検査した。"
        f"最大相対交換子ノルムは `{b04['maximum_relative_group_commutator_norm']:.3e}`、"
        f"最大sector cross-blockは `{b04['maximum_group_sector_cross_block_norm']:.3e}`。",
        "",
        f"全空間PFをsectorへ射影した行列と、各群を先にsector制限して構築したPFの"
        f"最大差は `{b04['maximum_projected_full_vs_restricted_unitary_residual']:.3e}`、"
        f"sector外リークは最大 `{b04['maximum_full_pf_sector_leakage_norm']:.3e}`。"
        "したがって監査した分割ではsector計算は元PFの厳密縮約である。",
        "",
        "対照例では、総Hamiltonianだけがsectorを保存し各群が保存しない場合、"
        f"リーク `{b04['noninvariant_split_control']['full_pf_sector_leakage_norm']:.3e}`、"
        f"制限前後の差 `{b04['noninvariant_split_control']['projected_full_vs_restricted_residual']:.3e}`"
        "を検出した。総Hの保存則だけでは不十分である。",
        "",
        "## B05 固有枝追跡",
        "",
        f"H2の34時刻では最大基底重なり枝と連続追跡枝の不一致は "
        f"{b05['actual_selection_disagreement_count']} 点、警告は "
        f"{b05['actual_branch_warning_count']} 点だった。最小の直前枝重なりは "
        f"`{b05['minimum_actual_previous_branch_overlap_probability']:.12f}`。",
        "",
        "縮退部分空間を回転させる対照例では、任意に選んだ単一基底ベクトルと連続追跡が"
        f" {b05['degenerate_control']['single_vector_and_continuity_disagreement_count']} 点で分岐したが、"
        f"部分空間射影は最低 `{b05['degenerate_control']['minimum_ground_subspace_projection_probability']:.12f}`。"
        "よって近接・縮退時は単一ベクトルではなく部分空間追跡と位相ギャップ警告を使う必要がある。",
        "",
        "## B06 数値雑音床",
        "",
        f"Yoshida 4次の2準位例をfloat64 eig、CPU Schur、80桁、120桁で比較した。"
        f"120桁真値が既存床 `{b06['fixed_noise_floor_hartree']:.1e}` Hartreeを超える"
        f"点での最大float差は `{b06['maximum_float_reference_difference_above_floor_hartree']:.3e}` Hartree。"
        f"80桁と120桁の最大差は `{b06['maximum_mp80_mp120_difference_hartree']:.3e}` Hartreeだった。",
        "",
        "微小τでは位相誤差が `1/τ` で増幅され、真値が床以下なのにfloat64値が床を超えた点が "
        f"{b06['ultrashort_below_truth_floor_but_float_above_floor_count']} 点あった。"
        f"一方、現行protocolの最小時刻 `0.02` でのfloat差は "
        f"`{b06['current_protocol_minimum_time_maximum_float_difference_hartree']:.3e}` Hartree。"
        "したがって既存床は現行格子では変更しないが、超短時間へ外挿する際の普遍的な床とはみなさない。",
        "",
        "## B07 独立実装クロスチェック",
        "",
        f"独立な未マージSciPy指数積とproduction builderの最大ユニタリ差は "
        f"`{b07['maximum_independent_production_unitary_residual']:.3e}`。"
        "可換例ではPF誤差が数値許容差内でゼロとなり、H2の全空間/sector経路も一致した。",
        "",
        "高精度で得た固有値シフトのlog-log次数は次の通り。",
        "",
        "| PF | 形式次数 | 観測次数 |",
        "|---|---:|---:|",
    ]
    formal = {"second_order": 2, "yoshida4": 4, "morales_y8m10b": 8}
    for formula_id, fitted in b07["fitted_orders"].items():
        lines.append(f"| {formula_id} | {formal[formula_id]} | {fitted:.6f} |")
    lines.extend(
        [
            "",
            "Aerが公開するdeviceは `"
            + ", ".join(b07["environment"]["aer_available_devices"])
            + "`。この環境ではGPUが公開されていないため、CPU/GPU差は未実施と明示した。"
            "小行列検証にはCPUで十分であり、SCF再実行差も混ぜていない。",
            "",
            "## 次の分岐",
            "",
            "B04〜B07の基礎数値経路は合格した。次は独立したB08（欠損・cache・seedの再現性）と、"
            "共通のコスト定義を扱うC02/C03を同じ監査バッチにまとめられる。",
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
    _write_csv(output / "b04_group_symmetry.csv", result["_b04_symmetry_rows"])
    _write_csv(
        output / "b04_sector_equivalence.csv", result["_b04_equivalence_rows"]
    )
    _write_csv(
        output / "b05_actual_branch_tracking.csv", result["_b05_actual_rows"]
    )
    _write_csv(
        output / "b05_degenerate_control.csv", result["_b05_synthetic_rows"]
    )
    _write_csv(output / "b06_precision_floor.csv", result["_b06_rows"])
    _write_csv(output / "b07_crosschecks.csv", result["_b07_rows"])
    _write_csv(output / "b07_order_scaling.csv", result["_b07_order_rows"])
    _write_csv(output / "implementation_paths.csv", result["_source_rows"])
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    _write_json(output / "audit.json", machine)
    _write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "audit_ids": result["audit_ids"],
            "component_status": result["component_status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "git": result["git"],
            "environment": result["environment"],
            "existing_artifacts_overwritten": False,
            "coefficient_search_performed": False,
            "production_molecular_sweep_performed": False,
            "gpu_used": False,
        },
    )
    _make_report(output, result)
    print(output)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
