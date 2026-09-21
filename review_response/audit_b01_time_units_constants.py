"""B01 audit of evolution signs, units, coordinates, and constant energies.

The audit combines deterministic small-matrix checks with one H2/STO-3G
PySCF unit-conversion sentinel.  It does not run a molecular PF benchmark or
modify any previously saved result.
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
from pyscf import ao2mo, fci, gto, scf
from pyscf.data import nist as pyscf_nist
from qiskit import QuantumCircuit
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy import constants
from scipy.linalg import eigh, expm

from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.sector_pf import build_sector_pf_unitary


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/prevalidation_b01_time_units_constants_20260921_retry1"
ABSOLUTE_TOLERANCE = 2e-12
SCIPY_BOHR_ANGSTROM = constants.physical_constants["Bohr radius"][0] * 1e10
PYSCF_BOHR_ANGSTROM = float(pyscf_nist.BOHR)


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
    fieldnames = list(rows[0])
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
    for name in ("numpy", "scipy", "pyscf", "qiskit", "openfermion"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _fixture_groups() -> list[np.ndarray]:
    first = np.asarray(
        [
            [-0.71, 0.17 + 0.03j, -0.04j],
            [0.17 - 0.03j, 0.23, 0.09],
            [0.04j, 0.09, 0.56],
        ],
        dtype=np.complex128,
    )
    second = np.asarray(
        [
            [0.19, -0.08j, 0.12],
            [0.08j, -0.37, -0.05 + 0.02j],
            [0.12, -0.05 - 0.02j, 0.41],
        ],
        dtype=np.complex128,
    )
    return [first, second]


def _spectra(groups: Sequence[np.ndarray]):
    return [eigh(np.asarray(group), check_finite=False) for group in groups]


def _manual_pf(
    groups: Sequence[np.ndarray], sequence: Sequence[float], time_value: float
) -> np.ndarray:
    result = np.eye(groups[0].shape[0], dtype=np.complex128)
    for group_index, weight in iter_s2_sequence_steps(len(groups), sequence):
        result = expm(
            1j * float(time_value) * float(weight) * groups[group_index]
        ) @ result
    return result


def _qiskit_native_unitary(time_value: float) -> np.ndarray:
    circuit = QuantumCircuit(1)
    circuit.append(
        PauliEvolutionGate(
            SparsePauliOp.from_list([("Z", 1.0)]),
            time=float(time_value),
            synthesis=None,
        ),
        [0],
    )
    columns = []
    for state in (np.asarray([1.0, 0.0]), np.asarray([0.0, 1.0])):
        columns.append(np.asarray(Statevector(state).evolve(circuit).data))
    return np.column_stack(columns)


def small_matrix_checks() -> list[dict[str, Any]]:
    groups = _fixture_groups()
    spectra = _spectra(groups)
    sequence = [1.0]
    positive_time = 0.37
    plus = build_sector_pf_unitary(spectra, sequence, positive_time)
    minus = build_sector_pf_unitary(spectra, sequence, -positive_time)
    full = sum(groups, np.zeros_like(groups[0]))
    single_group = build_sector_pf_unitary(
        _spectra([full]), sequence, positive_time
    )
    manual_plus = _manual_pf(groups, sequence, positive_time)
    manual_minus = _manual_pf(groups, sequence, -positive_time)
    wrong_sign = manual_minus
    qiskit = _qiskit_native_unitary(positive_time)
    qiskit_minus_time = _qiskit_native_unitary(-positive_time)
    z_matrix = np.diag([1.0, -1.0])
    derivative_step = 1e-5
    derivative = (
        build_sector_pf_unitary(spectra, sequence, derivative_step)
        - build_sector_pf_unitary(spectra, sequence, -derivative_step)
    ) / (2.0 * derivative_step)
    rows = [
        {
            "check_id": "sector_pf_positive_time_matches_manual_plus_i",
            "measured_residual": float(np.linalg.norm(plus - manual_plus)),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "exp(+i H tau)",
        },
        {
            "check_id": "sector_pf_negative_time_matches_manual_plus_i",
            "measured_residual": float(np.linalg.norm(minus - manual_minus)),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "exp(+i H (-tau))",
        },
        {
            "check_id": "symmetric_pf_negative_time_is_adjoint",
            "measured_residual": float(np.linalg.norm(minus - plus.conj().T)),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "U(-tau)=U(tau)^dagger",
        },
        {
            "check_id": "single_group_sector_pf_matches_exact_plus_i",
            "measured_residual": float(
                np.linalg.norm(single_group - expm(1j * positive_time * full))
            ),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "exp(+i H tau)",
        },
        {
            "check_id": "sector_pf_central_derivative_matches_plus_i_H",
            "measured_residual": float(np.linalg.norm(derivative - 1j * full)),
            "tolerance": 2e-10,
            "expected_convention": "dU/dtau at zero = +i H",
        },
        {
            "check_id": "wrong_sign_control_is_distinguishable",
            "measured_residual": float(np.linalg.norm(plus - wrong_sign)),
            "tolerance": 0.1,
            "expected_convention": "residual must exceed control threshold",
        },
        {
            "check_id": "qiskit_native_positive_time_matches_minus_i",
            "measured_residual": float(
                np.linalg.norm(qiskit - expm(-1j * positive_time * z_matrix))
            ),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "PauliEvolutionGate is exp(-i H tau)",
        },
        {
            "check_id": "qiskit_negative_time_matches_repository_plus_i",
            "measured_residual": float(
                np.linalg.norm(
                    qiskit_minus_time - expm(1j * positive_time * z_matrix)
                )
            ),
            "tolerance": ABSOLUTE_TOLERANCE,
            "expected_convention": "native gate at -tau is exp(+i H tau)",
        },
    ]
    for row in rows:
        if row["check_id"] == "wrong_sign_control_is_distinguishable":
            row["passed"] = bool(row["measured_residual"] > row["tolerance"])
        else:
            row["passed"] = bool(row["measured_residual"] <= row["tolerance"])
    return rows


def _signed_ground_connected_bias(
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


def constant_shift_checks() -> list[dict[str, Any]]:
    groups = _fixture_groups()
    sequence = [1.0]
    hamiltonian = sum(groups, np.zeros_like(groups[0]))
    energies, states = eigh(hamiltonian, check_finite=False)
    ground_energy = float(energies[0])
    ground_state = np.asarray(states[:, 0])
    constant = 0.731
    identity = np.eye(hamiltonian.shape[0])
    shifted_groups = [groups[0] + constant * identity, groups[1]]
    rows = []
    for time_value in (0.43, -0.43):
        base_unitary = build_sector_pf_unitary(
            _spectra(groups), sequence, time_value
        )
        shifted_unitary = build_sector_pf_unitary(
            _spectra(shifted_groups), sequence, time_value
        )
        base_bias, base_overlap = _signed_ground_connected_bias(
            base_unitary, ground_state, ground_energy, time_value
        )
        shifted_bias, shifted_overlap = _signed_ground_connected_bias(
            shifted_unitary,
            ground_state,
            ground_energy + constant,
            time_value,
        )
        uncorrected_bias, _ = _signed_ground_connected_bias(
            shifted_unitary, ground_state, ground_energy, time_value
        )
        global_phase_residual = float(
            np.linalg.norm(
                shifted_unitary
                - np.exp(1j * constant * time_value) * base_unitary
            )
        )
        bias_difference = abs(shifted_bias - base_bias)
        uncorrected_constant_difference = abs(
            (uncorrected_bias - base_bias) - constant
        )
        rows.append(
            {
                "time_hartree_inverse": float(time_value),
                "constant_hartree": constant,
                "base_signed_pf_bias_hartree": base_bias,
                "shifted_corrected_signed_pf_bias_hartree": shifted_bias,
                "corrected_bias_absolute_difference_hartree": bias_difference,
                "shifted_uncorrected_signed_bias_hartree": uncorrected_bias,
                "uncorrected_shift_minus_constant_residual_hartree": (
                    uncorrected_constant_difference
                ),
                "global_phase_matrix_residual": global_phase_residual,
                "base_ground_overlap_probability": base_overlap,
                "shifted_ground_overlap_probability": shifted_overlap,
                "passed": bool(
                    bias_difference <= ABSOLUTE_TOLERANCE
                    and uncorrected_constant_difference <= ABSOLUTE_TOLERANCE
                    and global_phase_residual <= ABSOLUTE_TOLERANCE
                ),
            }
        )
    return rows


def energy_time_unit_checks() -> list[dict[str, Any]]:
    hartree_joule = constants.physical_constants["Hartree energy"][0]
    derived_atomic_time_second = constants.hbar / hartree_joule
    published_atomic_time_second = constants.physical_constants[
        "atomic unit of time"
    ][0]
    energy_hartree = -1.2345
    rows = []
    for time_atomic in (0.47, -0.47):
        phase_atomic = np.exp(1j * energy_hartree * time_atomic)
        phase_si = np.exp(
            1j
            * (energy_hartree * hartree_joule)
            * (time_atomic * derived_atomic_time_second)
            / constants.hbar
        )
        residual = float(abs(phase_atomic - phase_si))
        rows.append(
            {
                "check_id": f"hartree_atomic_time_phase_{time_atomic:+.2f}",
                "input_value": time_atomic,
                "reference_value": derived_atomic_time_second,
                "measured_residual": residual,
                "tolerance": 2e-15,
                "passed": bool(residual <= 2e-15),
                "note": "tau fields are atomic time units (Hartree^-1) when H is in Hartree",
            }
        )
    definition_residual = abs(
        published_atomic_time_second - derived_atomic_time_second
    )
    rows.append(
        {
            "check_id": "atomic_time_equals_hbar_over_hartree",
            "input_value": derived_atomic_time_second,
            "reference_value": published_atomic_time_second,
            "measured_residual": definition_residual,
            "tolerance": 2e-28,
            "passed": bool(definition_residual <= 2e-28),
            "note": "SI seconds per atomic time unit",
        }
    )
    return rows


def _h2_molecule(unit: str, bond_length: float):
    molecule = gto.Mole()
    molecule.atom = [
        ("H", (0.0, 0.0, -bond_length / 2.0)),
        ("H", (0.0, 0.0, bond_length / 2.0)),
    ]
    molecule.unit = unit
    molecule.basis = "sto-3g"
    molecule.charge = 0
    molecule.spin = 0
    molecule.verbose = 0
    molecule.build()
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-13
    mean_field.max_cycle = 100
    mean_field.verbose = 0
    mean_field.kernel()
    if not mean_field.converged:
        raise RuntimeError(f"H2 RHF did not converge for unit={unit}")
    return molecule, mean_field


def coordinate_and_nuclear_checks() -> list[dict[str, Any]]:
    bond_angstrom = 0.74
    molecule_a, mean_field_a = _h2_molecule("Angstrom", bond_angstrom)
    molecule_b, mean_field_b = _h2_molecule(
        "Bohr", bond_angstrom / PYSCF_BOHR_ANGSTROM
    )
    coordinate_residual = float(
        np.max(
            np.abs(
                molecule_a.atom_coords(unit="Bohr")
                - molecule_b.atom_coords(unit="Bohr")
            )
        )
    )
    overlap_residual = float(
        np.linalg.norm(
            molecule_a.intor("int1e_ovlp") - molecule_b.intor("int1e_ovlp")
        )
    )
    core_residual = float(
        np.linalg.norm(mean_field_a.get_hcore() - mean_field_b.get_hcore())
    )
    nuclear_residual = abs(molecule_a.energy_nuc() - molecule_b.energy_nuc())
    scf_residual = abs(mean_field_a.e_tot - mean_field_b.e_tot)

    coefficients = np.asarray(mean_field_a.mo_coeff)
    one_body = coefficients.T @ mean_field_a.get_hcore() @ coefficients
    compact_eri = ao2mo.kernel(molecule_a, coefficients)
    two_body = ao2mo.restore(1, compact_eri, coefficients.shape[1])
    electronic_fci, _ = fci.direct_spin1.kernel(
        one_body,
        two_body,
        coefficients.shape[1],
        molecule_a.nelec,
        ecore=0.0,
    )
    total_fci, _ = fci.direct_spin1.kernel(
        one_body,
        two_body,
        coefficients.shape[1],
        molecule_a.nelec,
        ecore=float(molecule_a.energy_nuc()),
    )
    restored_total = float(electronic_fci + molecule_a.energy_nuc())
    restoration_residual = abs(float(total_fci) - restored_total)
    bohr_table_difference = abs(PYSCF_BOHR_ANGSTROM - SCIPY_BOHR_ANGSTROM)

    return [
        {
            "check_id": "pyscf_vs_scipy_bohr_constant",
            "measured_residual": bohr_table_difference,
            "tolerance": 5e-11,
            "passed": bool(bohr_table_difference <= 5e-11),
            "note": (
                f"PySCF={PYSCF_BOHR_ANGSTROM:.16g}, "
                f"SciPy={SCIPY_BOHR_ANGSTROM:.16g} Angstrom"
            ),
        },
        {
            "check_id": "angstrom_to_bohr_coordinates",
            "measured_residual": coordinate_residual,
            "tolerance": 2e-14,
            "passed": bool(coordinate_residual <= 2e-14),
            "note": (
                f"0.74 Angstrom = "
                f"{bond_angstrom / PYSCF_BOHR_ANGSTROM:.16g} Bohr in PySCF"
            ),
        },
        {
            "check_id": "angstrom_to_bohr_ao_overlap",
            "measured_residual": overlap_residual,
            "tolerance": 2e-13,
            "passed": bool(overlap_residual <= 2e-13),
            "note": "H2/STO-3G AO overlap",
        },
        {
            "check_id": "angstrom_to_bohr_core_hamiltonian",
            "measured_residual": core_residual,
            "tolerance": 2e-12,
            "passed": bool(core_residual <= 2e-12),
            "note": "H2/STO-3G AO core Hamiltonian",
        },
        {
            "check_id": "angstrom_to_bohr_nuclear_repulsion",
            "measured_residual": nuclear_residual,
            "tolerance": 2e-14,
            "passed": bool(nuclear_residual <= 2e-14),
            "note": f"E_nuc={molecule_a.energy_nuc():.16g} Hartree",
        },
        {
            "check_id": "angstrom_to_bohr_rhf_total_energy",
            "measured_residual": scf_residual,
            "tolerance": 2e-12,
            "passed": bool(scf_residual <= 2e-12),
            "note": f"E_RHF={mean_field_a.e_tot:.16g} Hartree",
        },
        {
            "check_id": "nuclear_repulsion_remove_restore_fci",
            "measured_residual": restoration_residual,
            "tolerance": 2e-13,
            "passed": bool(restoration_residual <= 2e-13),
            "note": (
                f"E_elec={float(electronic_fci):.16g}, "
                f"E_nuc={molecule_a.energy_nuc():.16g}, "
                f"E_total={float(total_fci):.16g} Hartree"
            ),
        },
    ]


def _source_location(relative_path: str, needle: str) -> tuple[int, str]:
    path = ROOT / relative_path
    lines = path.read_text(encoding="utf-8").splitlines()
    matches = [index + 1 for index, line in enumerate(lines) if needle in line]
    if not matches:
        raise RuntimeError(f"source sentinel not found: {relative_path}: {needle}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return matches[0], digest


def implementation_path_checks() -> list[dict[str, Any]]:
    definitions = [
        (
            "dense_sector_pf",
            "src/trotterlib/sector_pf.py",
            "np.exp(1j * scaled_time * values)",
            "exp(+i H tau)",
            "direct small-matrix runtime check",
            "constant is excluded by molecular preparation",
        ),
        (
            "component_sector_pf",
            "src/trotterlib/component_sector_pf.py",
            "np.exp(1j * float(scaled_time) * batch.eigenvalues)",
            "exp(+i H tau)",
            "current molecular runner",
            "qubit_operator_sector_matrix(remove_constant=True)",
        ),
        (
            "legacy_sparse_matrix_pf",
            "src/trotterlib/matrix_pf_build.py",
            "expm(1j * eye(2**n_qubits, format=\"csc\") * coefficient * t * w)",
            "exp(+i H tau)",
            "legacy diagonalization path",
            "identity is retained as a global phase",
        ),
        (
            "qiskit_gate_native",
            "src/trotterlib/qiskit_time_evolution_grouping.py",
            "PauliEvolutionGate(",
            "exp(-i H tau)",
            "native sign confirmed at runtime; current callers pass -tau",
            "grouped circuit builder skips identity terms",
        ),
        (
            "current_molecular_geometry",
            "review_response/run_two_term_pf_m3_holdout_server2.py",
            "molecule.unit = \"Angstrom\"",
            "not applicable",
            "explicit coordinate unit",
            "metadata stores geometry_angstrom",
        ),
        (
            "current_molecular_energy_reference",
            "review_response/run_two_term_pf_m3_holdout_server2.py",
            "\"ground_energy_without_constant_hartree\": energy",
            "exp(-i E0 tau) phase correction",
            "same constant-free reference as PF groups",
            "removed_constant_hartree is stored separately",
        ),
        (
            "qiskit_plus_i_compensation",
            "review_response/run_morales_y8m10b_hchain.py",
            "[-float(evolution_time) for evolution_time in times]",
            "native exp(-i H (-tau)) = exp(+i H tau)",
            "explicit negative-time compensation",
            "energy_without_constant is used",
        ),
    ]
    rows = []
    for path_id, relative, needle, sign, handling, constant_handling in definitions:
        line, digest = _source_location(relative, needle)
        rows.append(
            {
                "path_id": path_id,
                "source_path": relative,
                "source_line": line,
                "source_sha256": digest,
                "evolution_convention": sign,
                "caller_or_unit_handling": handling,
                "constant_handling": constant_handling,
                "sentinel_present": True,
            }
        )
    return rows


def _make_report(output: Path, result: dict[str, Any]) -> None:
    maxima = result["maximum_residuals"]
    lines = [
        "# B01: time-evolution sign, unit, and constant audit",
        "",
        f"Status: {result['status']}",
        "",
        "The current dense/component PF path is numerically consistent with "
        "`exp(+i H tau)`. The native Qiskit `PauliEvolutionGate` uses "
        "`exp(-i H tau)`; current Qiskit diagnostics that target the repository "
        "convention explicitly pass `-tau`. These two conventions must not be "
        "mixed without the corresponding phase-reference change.",
        "",
        "## Numerical checks",
        "",
        f"- Small-matrix sign/negative-time checks: {result['small_matrix_passed']}/"
        f"{result['small_matrix_check_count']} passed; maximum ordinary residual "
        f"{maxima['small_matrix_ordinary']:.3g}.",
        f"- Constant-shift checks: {result['constant_shift_passed']}/"
        f"{result['constant_shift_check_count']} passed; maximum corrected bias "
        f"change {maxima['constant_corrected_bias_hartree']:.3g} Hartree.",
        f"- Hartree/atomic-time checks: {result['energy_time_unit_passed']}/"
        f"{result['energy_time_unit_check_count']} passed.",
        f"- Angstrom/Bohr and nuclear restoration checks: "
        f"{result['coordinate_nuclear_passed']}/"
        f"{result['coordinate_nuclear_check_count']} passed; maximum residual "
        f"{maxima['coordinate_and_nuclear']:.3g}.",
        "",
        "For `H -> H + c I`, the PF unitary acquires `exp(+i c tau)` and the "
        "signed PF eigenvalue bias is unchanged when the reference energy is "
        "also shifted by `c`. Omitting that energy correction reproduces the "
        "constant shift, confirming that it would remain observable in a "
        "controlled-unitary phase.",
        "",
        "## Unit and constant interpretation",
        "",
        f"The coordinate sentinel used H2/STO-3G at 0.74 Angstrom = "
        f"{result['bond_length_bohr']:.16g} Bohr. Nuclear repulsion was removed "
        "and restored independently in an FCI calculation. Evolution times are "
        "atomic time units (`Hartree^-1` with hbar=1); one unit is "
        f"{result['atomic_time_second']:.16g} seconds.",
        "",
        "The current molecular runner explicitly sets `molecule.unit = "
        "\"Angstrom\"`, removes the complete JW identity coefficient from every "
        "PF group, uses the matching constant-free ground energy, and records "
        "the removed coefficient. Nuclear repulsion and the final JW identity "
        "coefficient are conceptually distinct because fermion-to-qubit "
        "transformation can add further identity contributions.",
        "",
        "## Caveats",
        "",
        "- Many saved fields are named only `time`; their atomic-unit meaning is "
        "implicit rather than encoded in every field name.",
        "- Legacy Qiskit plotting uses the native `-i` convention consistently, "
        "while current direct-eigenphase work uses `+i`. Cross-path data require "
        "an explicit convention tag.",
        "- This B01 test validates conventions and exact constant cancellation, "
        "not PF accuracy on an additional molecule.",
        "",
        "## Files",
        "",
        "- `small_matrix_checks.csv`: sign, negative-time, and Qiskit sentinels.",
        "- `constant_shift_checks.csv`: corrected and uncorrected identity shifts.",
        "- `energy_time_unit_checks.csv`: Hartree and atomic-time conversion.",
        "- `coordinate_nuclear_checks.csv`: Angstrom/Bohr and nuclear restoration.",
        "- `implementation_paths.csv`: source paths, conventions, and hashes.",
        "- `audit.json` and `manifest.json`: complete summary and provenance.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    small = small_matrix_checks()
    constant_rows = constant_shift_checks()
    energy_time = energy_time_unit_checks()
    coordinate = coordinate_and_nuclear_checks()
    paths = implementation_path_checks()
    ordinary_small = [
        row
        for row in small
        if row["check_id"] != "wrong_sign_control_is_distinguishable"
    ]
    result = {
        "status": "complete"
        if all(
            row["passed"]
            for rows in (small, constant_rows, energy_time, coordinate)
            for row in rows
        )
        and all(row["sentinel_present"] for row in paths)
        else "failed",
        "scope": "B01 time-evolution sign, unit, coordinate, and constant audit",
        "created_at": datetime.now().astimezone().isoformat(),
        "small_matrix_check_count": len(small),
        "small_matrix_passed": sum(bool(row["passed"]) for row in small),
        "constant_shift_check_count": len(constant_rows),
        "constant_shift_passed": sum(
            bool(row["passed"]) for row in constant_rows
        ),
        "energy_time_unit_check_count": len(energy_time),
        "energy_time_unit_passed": sum(
            bool(row["passed"]) for row in energy_time
        ),
        "coordinate_nuclear_check_count": len(coordinate),
        "coordinate_nuclear_passed": sum(
            bool(row["passed"]) for row in coordinate
        ),
        "implementation_path_count": len(paths),
        "implementation_path_sentinels_passed": sum(
            bool(row["sentinel_present"]) for row in paths
        ),
        "maximum_residuals": {
            "small_matrix_ordinary": max(
                float(row["measured_residual"]) for row in ordinary_small
            ),
            "wrong_sign_control": next(
                float(row["measured_residual"])
                for row in small
                if row["check_id"] == "wrong_sign_control_is_distinguishable"
            ),
            "constant_corrected_bias_hartree": max(
                float(row["corrected_bias_absolute_difference_hartree"])
                for row in constant_rows
            ),
            "constant_global_phase_matrix": max(
                float(row["global_phase_matrix_residual"])
                for row in constant_rows
            ),
            "coordinate_and_nuclear": max(
                float(row["measured_residual"]) for row in coordinate
            ),
        },
        "atomic_time_second": constants.physical_constants[
            "atomic unit of time"
        ][0],
        "scipy_bohr_angstrom": SCIPY_BOHR_ANGSTROM,
        "pyscf_bohr_angstrom": PYSCF_BOHR_ANGSTROM,
        "bond_length_angstrom": 0.74,
        "bond_length_bohr": 0.74 / PYSCF_BOHR_ANGSTROM,
        "interpretation": {
            "current_pf_convention": "exp(+i H tau)",
            "native_qiskit_convention": "exp(-i H tau)",
            "qiskit_repository_compensation": "pass -tau when matching current PF convention",
            "time_unit": "atomic time = Hartree^-1 with hbar=1",
            "coordinate_unit_current_molecular_runner": "Angstrom (explicit)",
            "constant_policy": (
                "remove full identity coefficient from PF groups and reference "
                "the matching constant-free ground energy; retain the removed "
                "constant in metadata and restore it for absolute energies"
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "packages": _package_versions(),
        },
        "git": _git_state(),
        "_small_matrix_checks": small,
        "_constant_shift_checks": constant_rows,
        "_energy_time_unit_checks": energy_time,
        "_coordinate_nuclear_checks": coordinate,
        "_implementation_paths": paths,
    }
    return result


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
    _write_csv(output / "small_matrix_checks.csv", result["_small_matrix_checks"])
    _write_csv(
        output / "constant_shift_checks.csv", result["_constant_shift_checks"]
    )
    _write_csv(
        output / "energy_time_unit_checks.csv", result["_energy_time_unit_checks"]
    )
    _write_csv(
        output / "coordinate_nuclear_checks.csv",
        result["_coordinate_nuclear_checks"],
    )
    _write_csv(
        output / "implementation_paths.csv", result["_implementation_paths"]
    )
    machine = {key: value for key, value in result.items() if not key.startswith("_")}
    _write_json(output / "audit.json", machine)
    _write_json(
        output / "manifest.json",
        {
            "status": result["status"],
            "scope": result["scope"],
            "created_at": result["created_at"],
            "git": result["git"],
            "environment": result["environment"],
            "new_molecular_pf_benchmark_performed": False,
            "small_h2_unit_sentinel_performed": True,
            "existing_artifacts_overwritten": False,
            "gpu_used": False,
        },
    )
    _make_report(output, result)
    print(output)
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
