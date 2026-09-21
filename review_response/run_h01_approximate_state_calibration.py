"""H01 approximate-state calibration for the frozen unused-molecule holdout.

The fixed protocol is deliberately data driven: molecule/PF/time choices are
read from ``h01_approximate_state_calibration_protocol.json`` and the audited
source artifact.  Approximate-state construction never reads the exact ground
state; exact-state data enter only the explicitly labelled evaluation fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import resource
import time
from typing import Any, Iterable, Sequence

import numpy as np
from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import jordan_wigner
from pyscf import ao2mo, ci, fci, gto, mcscf, scf
from scipy.linalg import eigh, schur
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

import run_full_electron_nh3_higher_term_diagnosis as diagnosis
import run_unused_molecule_frozen_holdout as source_runner
from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
from trotterlib.component_sector_pf import (
    component_exponential,
    find_balanced_z2_symmetry,
    prepare_component_spectra,
    qubit_operator_sector_matrix,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps


PROTOCOL_PATH = Path(__file__).with_name("h01_approximate_state_calibration_protocol.json")
EXPECTED_PROTOCOL_SHA256 = "e0e2649db1f8d109779ab1db26822f45c92c2a660569caa643f5f363e3ce27a6"
SOURCE_RELATIVE = Path("artifacts/server_unused_molecule_frozen_holdout_20260921_d288797")
FORMULAE = ("current_m3", "yoshida4")
STATE_METHODS = ("exact_ground", "rhf_determinant", "cisd")
MODEL_SPECS = (
    ("echo_phase_5point", "echo_phase_hartree", 5),
    ("echo_phase_3point", "echo_phase_hartree", 3),
    ("echo_imag_5point", "echo_imag_hartree", 5),
    ("echo_imag_3point", "echo_imag_hartree", 3),
)
TIME_RTOL = 2e-12


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    diagnosis._atomic_json(path, value)


def _protocol() -> dict[str, Any]:
    return _load(PROTOCOL_PATH)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _conditions() -> list[str]:
    protocol = _protocol()
    return list(protocol["conditions"]["primary_development"]) + list(
        protocol["conditions"]["auxiliary_failure_diagnostic"]
    )


def _condition_specs() -> dict[str, dict[str, Any]]:
    source_protocol = _load(
        Path(__file__).with_name("unused_molecule_frozen_holdout_protocol.json")
    )
    return {entry["name"]: entry for entry in source_protocol["conditions"]}


def _same_time(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=TIME_RTOL, abs_tol=1e-14)


def _reverse_bits(value: int, width: int) -> int:
    result = 0
    for index in range(int(width)):
        result |= ((int(value) >> index) & 1) << (int(width) - 1 - index)
    return result


def determinant_pair_to_basis_integer(alpha: int, beta: int, norb: int) -> int:
    """Map PySCF alpha/beta strings to this repository's up-then-down JW bits."""
    return (_reverse_bits(alpha, norb) << int(norb)) | _reverse_bits(beta, norb)


def fcivec_to_population(
    fcivec: np.ndarray,
    norb: int,
    nelec: tuple[int, int],
    population_basis: np.ndarray,
) -> np.ndarray:
    alpha_strings = fci.cistring.make_strings(range(int(norb)), int(nelec[0]))
    beta_strings = fci.cistring.make_strings(range(int(norb)), int(nelec[1]))
    expected = (len(alpha_strings), len(beta_strings))
    coefficients = np.asarray(fcivec)
    if coefficients.shape != expected:
        raise ValueError(f"FCI coefficient shape {coefficients.shape} != {expected}")
    lookup = {int(value): index for index, value in enumerate(population_basis)}
    result = np.zeros(population_basis.size, dtype=np.complex128)
    # Moving all beta creators past all alpha creators is a fixed global sign
    # in a fixed (Nalpha,Nbeta) sector.  Retaining it documents the convention.
    global_sign = -1.0 if (int(nelec[0]) * int(nelec[1])) % 2 else 1.0
    for ia, alpha in enumerate(alpha_strings):
        for ib, beta in enumerate(beta_strings):
            basis_integer = determinant_pair_to_basis_integer(
                int(alpha), int(beta), int(norb)
            )
            result[lookup[basis_integer]] = global_sign * coefficients[ia, ib]
    return result


def rhf_population_state(
    norb: int, nelec: tuple[int, int], population_basis: np.ndarray
) -> np.ndarray:
    alpha = (1 << int(nelec[0])) - 1
    beta = (1 << int(nelec[1])) - 1
    target = determinant_pair_to_basis_integer(alpha, beta, norb)
    matches = np.flatnonzero(population_basis == target)
    if matches.size != 1:
        raise RuntimeError("RHF determinant is absent from the population basis")
    result = np.zeros(population_basis.size, dtype=np.complex128)
    result[int(matches[0])] = 1.0
    return result


def _sparse_hash(matrix: csr_matrix) -> str:
    digest = hashlib.sha256()
    digest.update(np.asarray(matrix.shape, dtype=np.int64).tobytes())
    for array in (matrix.indptr, matrix.indices, matrix.data):
        digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def _group_hashes(groups: Sequence[QubitOperator]) -> list[str]:
    hashes = []
    for group in groups:
        canonical = [
            [list(map(list, term)), float(complex(value).real), float(complex(value).imag)]
            for term, value in sorted(group.terms.items())
        ]
        hashes.append(hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest())
    return hashes


def _state_diagnostics(
    state: np.ndarray,
    hamiltonian: csr_matrix,
    exact_state: np.ndarray,
    exact_energy: float,
) -> dict[str, float]:
    vector = np.asarray(state, dtype=np.complex128)
    action = np.asarray(hamiltonian @ vector)
    energy = float(np.vdot(vector, action).real)
    centered = action - energy * vector
    return {
        "normalization": float(np.linalg.norm(vector)),
        "energy_expectation_hartree": energy,
        "energy_error_hartree": float(energy - exact_energy),
        "energy_variance_hartree2": float(np.vdot(centered, centered).real),
        "hamiltonian_residual_2_norm": float(np.linalg.norm(centered)),
        "overlap_probability_with_exact_ground_for_evaluation_only": float(
            abs(np.vdot(exact_state, vector)) ** 2
        ),
    }


def prepare_condition(name: str, work_dir: Path, component_processes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol_hash = _sha256(PROTOCOL_PATH)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError(f"H01 protocol hash mismatch: {protocol_hash}")
    spec = _condition_specs()[name]
    started = time.perf_counter()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    work_dir.mkdir(parents=True, exist_ok=True)

    molecule = gto.Mole()
    molecule.atom = [(atom, xyz) for atom, xyz in spec["geometry_angstrom"]]
    molecule.unit = "Angstrom"
    molecule.basis = str(spec["basis"])
    molecule.spin = int(spec["multiplicity"]) - 1
    molecule.charge = int(spec["charge"])
    molecule.symmetry = False
    molecule.verbose = 3
    molecule.output = str(work_dir / "pyscf.log")
    molecule.build()
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-12
    mean_field.max_cycle = 200
    mean_field.kernel()
    if not mean_field.converged:
        raise RuntimeError(f"{name}: RHF did not converge")

    ncore = int(spec["frozen_core_spatial_orbitals"])
    ncas = int(spec["active_spatial_orbitals"])
    nelecas = int(molecule.nelectron - 2 * ncore)
    nelec = (nelecas // 2, nelecas - nelecas // 2)
    if int(mean_field.mo_coeff.shape[1]) != ncore + ncas:
        raise RuntimeError(f"{name}: unexpected MO count")
    if nelecas != int(spec["active_electrons"]):
        raise RuntimeError(f"{name}: unexpected active electron count")

    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = ncore
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    active_coefficients = np.asarray(mean_field.mo_coeff[:, ncore:ncore + ncas])
    eri_compact = ao2mo.kernel(molecule, active_coefficients)
    eri_active = ao2mo.restore(1, eri_compact, ncas)
    two_body = np.asarray(eri_active.transpose(0, 2, 3, 1), order="C")
    grouper = Almost_optimal_grouper(
        float(core_energy), np.asarray(h1_effective), two_body,
        fermion_qubit_mapping=jordan_wigner, validation=True,
    )
    grouped = grouper.group_term_list
    grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
    groups = [
        source_runner._hermitize(jordan_wigner(sum(group, FermionOperator())))[0]
        for group in grouped
    ]
    hamiltonian_operator, hermitization = source_runner._hermitize(
        sum(groups, QubitOperator())
    )
    constant = float(complex(hamiltonian_operator.terms.get((), 0.0)).real)

    population_basis = diagnosis._population_basis(ncas, *nelec)
    sector_hamiltonian = qubit_operator_sector_matrix(
        groups[0], 2 * ncas, population_basis, remove_constant=True
    )
    for group in groups[1:]:
        sector_hamiltonian += qubit_operator_sector_matrix(
            group, 2 * ncas, population_basis, remove_constant=True
        )
    dense = sector_hamiltonian.toarray()
    values, vectors = eigh(dense, subset_by_index=[0, 0], check_finite=False, driver="evr")
    exact_energy = float(values[0])
    population_exact = np.asarray(vectors[:, 0], dtype=np.complex128)
    population_exact /= np.linalg.norm(population_exact)
    del dense

    try:
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, 2 * ncas, population_basis, population_exact, support_cutoff=1e-9
        )
    except RuntimeError as exc:
        if "No nonconstant exact diagonal-Z symmetry" not in str(exc):
            raise
        mask, target = 0, 0
        selected = np.arange(population_basis.size, dtype=np.int64)
        symmetry = {
            "kind": "no_nonconstant_exact_diagonal_Z2",
            "population_sector_dimension": int(population_basis.size),
            "restricted_dimension": int(population_basis.size),
        }
    selected = np.asarray(selected, dtype=np.int64)
    selected_mask = np.zeros(population_basis.size, dtype=bool)
    selected_mask[selected] = True
    restricted_basis = population_basis[selected]
    restricted_hamiltonian = sector_hamiltonian[selected, :][:, selected].tocsr()
    exact_state = population_exact[selected].copy()
    exact_outside = float(np.linalg.norm(population_exact[~selected_mask]))
    exact_state /= np.linalg.norm(exact_state)

    rhf_started = time.perf_counter()
    population_rhf = rhf_population_state(ncas, nelec, population_basis)
    rhf_seconds = time.perf_counter() - rhf_started

    cisd_started = time.perf_counter()
    frozen = list(range(ncore)) if ncore else None
    cisd_solver = ci.CISD(mean_field, frozen=frozen)
    cisd_solver.conv_tol = 1e-10
    cisd_solver.max_cycle = 200
    cisd_correlation_energy, cisd_vector = cisd_solver.kernel()
    cisd_total_energy = float(cisd_solver.e_tot)
    if not cisd_solver.converged:
        raise RuntimeError(f"{name}: CISD did not converge")
    active_fcivec = ci.cisd.to_fcivec(cisd_vector, ncas, nelec)
    population_cisd = fcivec_to_population(
        active_fcivec, ncas, nelec, population_basis
    )
    population_cisd /= np.linalg.norm(population_cisd)
    cisd_seconds = time.perf_counter() - cisd_started

    states: dict[str, np.ndarray] = {}
    state_metadata: dict[str, Any] = {}
    for method, population_state, seconds in (
        ("exact_ground", population_exact, 0.0),
        ("rhf_determinant", population_rhf, rhf_seconds),
        ("cisd", population_cisd, cisd_seconds),
    ):
        outside = float(np.linalg.norm(population_state[~selected_mask]))
        if outside > 1e-8:
            raise RuntimeError(f"{name}/{method}: Z2-sector outside norm {outside}")
        restricted = population_state[selected].copy()
        restricted_norm = float(np.linalg.norm(restricted))
        restricted /= restricted_norm
        states[method] = restricted
        state_metadata[method] = {
            **_state_diagnostics(
                restricted, restricted_hamiltonian, exact_state, exact_energy
            ),
            "population_sector_outside_norm": 0.0,
            "additional_z2_sector_outside_norm": outside,
            "restricted_norm_before_normalization": restricted_norm,
            "state_generation_wall_seconds": float(seconds),
            "state_generation_peak_memory_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            ),
            "uses_exact_ground_in_construction": method == "exact_ground",
        }
    cisd_total_from_matrix = (
        state_metadata["cisd"]["energy_expectation_hartree"] + constant
    )
    state_metadata["cisd"].update({
        "pyscf_cisd_total_energy_hartree": float(cisd_total_energy),
        "pyscf_cisd_correlation_energy_hartree": float(cisd_correlation_energy),
        "matrix_plus_constant_energy_hartree": float(cisd_total_from_matrix),
        "pyscf_vs_matrix_energy_difference_hartree": float(
            cisd_total_from_matrix - cisd_total_energy
        ),
        "pyscf_converged": bool(cisd_solver.converged),
        "pyscf_iterations": int(getattr(cisd_solver, "iterations", 0) or 0),
        "frozen_spatial_orbitals": [] if frozen is None else frozen,
        "active_fcivec_shape": list(active_fcivec.shape),
    })
    if abs(cisd_total_from_matrix - float(cisd_total_energy)) > 1e-8:
        raise RuntimeError(
            f"{name}: CISD determinant mapping energy mismatch "
            f"{cisd_total_from_matrix - float(cisd_total_energy):.3e}"
        )

    spectra, compact = prepare_component_spectra(
        groups, 2 * ncas, restricted_basis,
        validation_state=exact_state, processes=int(component_processes),
    )
    summed_action = np.asarray(compact.pop("summed_group_action"))
    component_residual = float(
        np.linalg.norm(summed_action - exact_energy * exact_state)
    )
    if component_residual > 1e-8:
        raise RuntimeError(f"{name}: component Hamiltonian residual {component_residual}")
    term_counts = [sum(1 for term in group.terms if term) for group in groups]
    system = {
        "condition": name,
        "states": states,
        "state": exact_state,
        "energy": exact_energy,
        "hamiltonian": restricted_hamiltonian,
        "component_spectra": spectra,
        "term_counts": term_counts,
        "restricted_basis": restricted_basis,
        "protocol_sha256": protocol_hash,
        "hamiltonian_sha256": _sparse_hash(restricted_hamiltonian),
    }
    metadata = {
        "condition": name,
        "geometry_angstrom": spec["geometry_angstrom"],
        "basis": spec["basis"],
        "charge": int(spec["charge"]),
        "multiplicity": int(spec["multiplicity"]),
        "total_spatial_orbitals": int(mean_field.mo_coeff.shape[1]),
        "total_electron_count": int(molecule.nelectron),
        "active_electron_count": nelecas,
        "frozen_core_spatial_orbitals": ncore,
        "active_spatial_orbitals": ncas,
        "n_alpha": nelec[0],
        "n_beta": nelec[1],
        "population_sector_dimension": int(population_basis.size),
        "restricted_dimension": int(restricted_basis.size),
        "group_count": len(groups),
        "term_counts": term_counts,
        "group_sha256": _group_hashes(groups),
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "ground_energy_without_constant_hartree": exact_energy,
        "removed_constant_hartree": constant,
        "exact_ground_z2_outside_norm": exact_outside,
        "z2_mask": int(mask),
        "z2_target": int(target),
        "z2_symmetry": symmetry,
        "component_representation": compact,
        "component_ground_residual_2_norm": component_residual,
        "numerical_hermitization": hermitization,
        "scf_energy_hartree": float(mean_field.e_tot),
        "scf_converged": bool(mean_field.converged),
        "states": state_metadata,
        "preparation_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "peak_cpu_rss_increment_kib": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss_before
        ),
        "protocol_sha256": protocol_hash,
    }
    return system, metadata


def _source_root(project_root: Path) -> Path:
    return project_root / SOURCE_RELATIVE


def _source_raw(source_root: Path, condition: str, formula: str) -> tuple[Path, dict[str, Any]]:
    path = source_root / "raw" / f"{condition}__{formula}.json"
    return path, _load(path)


def _source_metadata(source_root: Path, condition: str) -> tuple[Path, dict[str, Any]]:
    path = source_root / "cache" / f"{condition}.metadata.json"
    return path, _load(path)["system"]


def _validate_source_metadata(local: dict[str, Any], source: dict[str, Any]) -> dict[str, bool]:
    keys = (
        "geometry_angstrom", "basis", "charge", "multiplicity",
        "total_spatial_orbitals", "total_electron_count", "active_electron_count",
        "frozen_core_spatial_orbitals", "active_spatial_orbitals", "n_alpha",
        "n_beta", "population_sector_dimension", "restricted_dimension", "group_count",
    )
    return {key: local.get(key) == source.get(key) for key in keys}


def _rotation_count(system: dict[str, Any], sequence: Sequence[float]) -> int:
    return int(sum(
        system["term_counts"][group]
        for group, _ in iter_s2_sequence_steps(len(system["term_counts"]), sequence)
    ))


def _apply_pf_cpu(
    system: dict[str, Any], sequence: Sequence[float], time_value: float,
    states: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    started = time.perf_counter()
    current = np.asarray(states, dtype=np.complex128).copy()
    gates: dict[tuple[int, float], Any] = {}
    materialize = 0.0
    multiply = 0.0
    for group_index, raw_weight in iter_s2_sequence_steps(
        len(system["component_spectra"]), sequence
    ):
        key = (int(group_index), float(raw_weight))
        gate = gates.get(key)
        if gate is None:
            step = time.perf_counter()
            gate = component_exponential(
                system["component_spectra"][group_index],
                float(time_value) * float(raw_weight),
            )
            materialize += time.perf_counter() - step
            gates[key] = gate
        step = time.perf_counter()
        current = gate @ current
        multiply += time.perf_counter() - step
    return current, {
        "total": float(time.perf_counter() - started),
        "component_gate_materialization": materialize,
        "sparse_state_multiply": multiply,
    }


def _apply_pf_gpu(
    system: dict[str, Any], sequence: Sequence[float], time_value: float,
    states: np.ndarray, physical_gpu: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as gpu_csr_matrix

    started = time.perf_counter()
    pool = cp.get_default_memory_pool()
    pool.free_all_blocks()
    current = cp.asarray(states)
    gates: dict[tuple[int, float], Any] = {}
    materialize = transfer = multiply = 0.0
    with diagnosis.GpuMemoryMonitor(int(physical_gpu)) as monitor:
        for group_index, raw_weight in iter_s2_sequence_steps(
            len(system["component_spectra"]), sequence
        ):
            key = (int(group_index), float(raw_weight))
            gate = gates.get(key)
            if gate is None:
                step = time.perf_counter()
                cpu_gate = component_exponential(
                    system["component_spectra"][group_index],
                    float(time_value) * float(raw_weight),
                )
                materialize += time.perf_counter() - step
                step = time.perf_counter()
                gate = gpu_csr_matrix(cpu_gate)
                cp.cuda.Stream.null.synchronize()
                transfer += time.perf_counter() - step
                gates[key] = gate
            step = time.perf_counter()
            current = gate @ current
            cp.cuda.Stream.null.synchronize()
            multiply += time.perf_counter() - step
        step = time.perf_counter()
        host = cp.asnumpy(current)
        cp.cuda.Stream.null.synchronize()
        transfer += time.perf_counter() - step
        peak = int(pool.total_bytes())
    del current, gates
    pool.free_all_blocks()
    return host, {
        "total": float(time.perf_counter() - started),
        "component_gate_materialization": materialize,
        "host_device_transfer": transfer,
        "gpu_sparse_state_multiply": multiply,
        "cupy_pool_peak_reserved_mib": float(peak / 2**20),
        "gpu_memory": monitor.summary(),
    }


def _fit_proxy(points: Sequence[dict[str, Any]], field: str, count: int, t_ana: float, name: str) -> dict[str, Any]:
    selected = list(points[: int(count)])
    times = np.asarray([float(point["time"]) for point in selected])
    values = np.asarray([float(point[field]) for point in selected])
    relative = times / float(t_ana)
    scale = float(np.max(np.abs(values))) or 1.0
    design = np.column_stack((relative**4, relative**6))
    scaled = np.linalg.lstsq(design, values / scale, rcond=None)[0]
    coefficients = [
        float(scale * scaled[0] / t_ana**4),
        float(scale * scaled[1] / t_ana**6),
    ]
    fitted = coefficients[0] * times**4 + coefficients[1] * times**6
    return {
        "name": name,
        "formal_order": 4,
        "coefficient_powers": [4, 6],
        "coefficient_values": coefficients,
        "coefficient_signs": [int(np.sign(value)) for value in coefficients],
        "training_relative_to_t_ana": relative.tolist(),
        "training_maximum_absolute_residual_hartree": float(
            np.max(np.abs(fitted - values))
        ),
        "training_design_condition_number": float(np.linalg.cond(design)),
        "coefficient_source": f"unweighted signed least squares of {field}",
    }


def _echo_points(
    system: dict[str, Any], sequence: Sequence[float], t_ana: float,
    backend: str, physical_gpu: int,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    state_matrix = np.column_stack([system["states"][key] for key in STATE_METHODS])
    energies = np.asarray([
        np.vdot(state_matrix[:, index], system["hamiltonian"] @ state_matrix[:, index]).real
        for index in range(len(STATE_METHODS))
    ])
    records = {method: [] for method in STATE_METHODS}
    timing = []
    relative_grid = _protocol()["calibration"]["primary_relative_to_source_t_ana"]
    for relative in relative_grid:
        time_value = float(relative) * float(t_ana)
        if backend == "gpu":
            evolved, pf_timing = _apply_pf_gpu(
                system, sequence, time_value, state_matrix, physical_gpu
            )
        else:
            evolved, pf_timing = _apply_pf_cpu(
                system, sequence, time_value, state_matrix
            )
        step = time.perf_counter()
        referenced = expm_multiply(
            (-1j * time_value) * system["hamiltonian"], evolved
        )
        reference_seconds = time.perf_counter() - step
        overlaps = np.sum(state_matrix.conj() * referenced, axis=0)
        legacy = np.exp(-1j * energies * time_value) * np.sum(
            state_matrix.conj() * evolved, axis=0
        )
        for index, method in enumerate(STATE_METHODS):
            records[method].append({
                "time": time_value,
                "relative_to_source_t_ana": float(relative),
                "echo_amplitude": complex(overlaps[index]),
                "echo_principal_phase_radians": float(np.angle(overlaps[index])),
                "echo_imag_hartree": float(overlaps[index].imag / time_value),
                "echo_magnitude": float(abs(overlaps[index])),
                "legacy_energy_rotated_overlap_diagnostic_only": complex(legacy[index]),
                "pf_state_norm": float(np.linalg.norm(evolved[:, index])),
                "exact_reference_state_norm": float(np.linalg.norm(referenced[:, index])),
            })
        timing.append({
            "time": time_value,
            "pf": pf_timing,
            "exact_reference_expm_multiply_seconds": float(reference_seconds),
        })
    for method in STATE_METHODS:
        principal = np.asarray([
            point["echo_principal_phase_radians"] for point in records[method]
        ])
        unwrapped = np.unwrap(principal)
        for point, phase in zip(records[method], unwrapped):
            point["echo_unwrapped_phase_radians"] = float(phase)
            point["echo_phase_hartree"] = float(phase / point["time"])
    return records, {"points": timing, "backend": backend}


def _artificial_echo_sanity(system: dict[str, Any], time_value: float) -> dict[str, Any]:
    states = np.column_stack([system["states"][key] for key in STATE_METHODS])
    forward = expm_multiply((1j * time_value) * system["hamiltonian"], states)
    echoed = expm_multiply((-1j * time_value) * system["hamiltonian"], forward)
    overlaps = np.sum(states.conj() * echoed, axis=0)
    return {
        "time": float(time_value),
        "overlaps": {key: complex(value) for key, value in zip(STATE_METHODS, overlaps)},
        "maximum_abs_echo_minus_one": float(np.max(np.abs(overlaps - 1.0))),
        "passed": bool(np.max(np.abs(overlaps - 1.0)) <= 1e-10),
    }


def command_prepare(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = output.with_suffix(".metadata.json")
    payload = {
        "status": "preparing", "condition": args.condition,
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "git": diagnosis._git_state(), "environment": diagnosis._versions(),
    }
    _write(metadata_path, payload)
    try:
        system, metadata = prepare_condition(
            args.condition, output.parent / f"{output.stem}_work",
            args.component_processes,
        )
        source_path, source_metadata = _source_metadata(
            args.project_root.resolve() / SOURCE_RELATIVE, args.condition
        )
        checks = _validate_source_metadata(metadata, source_metadata)
        if not all(checks.values()):
            raise RuntimeError(f"{args.condition}: source metadata mismatch: {checks}")
        with output.open("wb") as stream:
            pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
        payload.update({
            "status": "complete", "system": metadata,
            "source_metadata": str(source_path.relative_to(args.project_root.resolve())),
            "source_metadata_sha256": _sha256(source_path),
            "source_metadata_checks": checks,
            "cache_bytes": output.stat().st_size,
        })
        _write(metadata_path, payload)
        return 0
    except Exception as exc:
        payload.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
        _write(metadata_path, payload)
        raise


def _load_system(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        system = pickle.load(stream)
    if system.get("protocol_sha256") != _sha256(PROTOCOL_PATH):
        raise RuntimeError(f"stale H01 cache: {path}")
    if system.get("hamiltonian_sha256") != _sparse_hash(system["hamiltonian"]):
        raise RuntimeError(f"Hamiltonian hash mismatch: {path}")
    return system


def command_echo(args: argparse.Namespace) -> int:
    system = _load_system(args.cache.resolve())
    source_root = args.project_root.resolve() / SOURCE_RELATIVE
    source_path, source = _source_raw(source_root, args.condition, args.formula)
    sequence = diagnosis._formula_s2_sequence(args.formula)
    rotations = _rotation_count(system, sequence)
    if sequence != source["formula"]["s2_sequence"] or rotations != source["formula"]["rotations"]:
        raise RuntimeError("PF sequence or rotation count disagrees with audited source")
    t_ana = float(source["analytic_time"])
    points, timing = _echo_points(
        system, sequence, t_ana, args.backend, args.gpu_id
    )
    models: dict[str, Any] = {}
    for method, method_points in points.items():
        models[method] = {}
        for model_name, field, count in MODEL_SPECS:
            model = _fit_proxy(method_points, field, count, t_ana, model_name)
            model["optimum"] = diagnosis._model_optimum(model, t_ana, rotations)
            models[method][model_name] = model
    direct_model = source["models"]["two_term_5point"]["model"]
    smallest_direct = source["training_direct_points"][0]["signed_direct_shift_hartree"]
    exact_smallest_proxy = points["exact_ground"][0]["echo_phase_hartree"]
    sign_match = bool(np.sign(smallest_direct) == np.sign(exact_smallest_proxy))
    artificial = _artificial_echo_sanity(system, 0.1 * t_ana)
    payload = {
        "status": "complete",
        "condition": args.condition, "formula": args.formula,
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "source_raw": str(source_path.relative_to(args.project_root.resolve())),
        "source_raw_sha256": _sha256(source_path),
        "source_commit": _protocol()["source"]["numerical_result_commit"],
        "analytic_time": t_ana, "rotations": rotations,
        "s2_sequence": sequence, "states": points, "models": models,
        "direct_reference_model": direct_model,
        "sanity": {
            "artificial_exact_echo": artificial,
            "smallest_time_exact_echo_sign_matches_direct_shift": sign_match,
            "smallest_time_exact_echo_phase_hartree": exact_smallest_proxy,
            "smallest_time_direct_signed_shift_hartree": smallest_direct,
            "passed_before_approximate_state_interpretation": bool(
                artificial["passed"] and sign_match
            ),
        },
        "timing": timing,
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }
    _write(args.output.resolve(), payload)
    if not payload["sanity"]["passed_before_approximate_state_interpretation"]:
        raise RuntimeError("exact-state echo identity/sign sanity failed")
    return 0


def command_pilot(args: argparse.Namespace) -> int:
    system = _load_system(args.cache.resolve())
    source_path, source = _source_raw(
        args.project_root.resolve() / SOURCE_RELATIVE,
        "CO_active_eq_sto3g", "current_m3",
    )
    sequence = diagnosis._formula_s2_sequence("current_m3")
    t_value = 0.1 * float(source["analytic_time"])
    cisd = system["states"]["cisd"][:, None]
    cpu, cpu_timing = _apply_pf_cpu(system, sequence, t_value, cisd)
    gpu_error = None
    gpu = None
    gpu_timing = None
    try:
        gpu, gpu_timing = _apply_pf_gpu(
            system, sequence, t_value, cisd, args.gpu_id
        )
    except Exception as exc:  # GPU is optional for echo calibration
        gpu_error = f"{type(exc).__name__}: {exc}"
    cpu_ref_started = time.perf_counter()
    cpu_echoed = expm_multiply((-1j * t_value) * system["hamiltonian"], cpu)
    reference_seconds = time.perf_counter() - cpu_ref_started
    relative_difference = (
        None if gpu is None else float(np.linalg.norm(cpu - gpu) / np.linalg.norm(cpu))
    )
    passed = gpu is None or relative_difference <= 1e-10
    payload = {
        "status": "complete" if passed else "failed",
        "condition": "CO_active_eq_sto3g", "formula": "current_m3",
        "state_method": "cisd", "time": t_value,
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "source_raw_sha256": _sha256(source_path),
        "cpu": {"pf": cpu_timing, "exact_reference_seconds": reference_seconds},
        "gpu": gpu_timing, "gpu_error": gpu_error,
        "cpu_gpu_relative_2_norm_difference": relative_difference,
        "cpu_result_norm": float(np.linalg.norm(cpu)),
        "gpu_result_norm": None if gpu is None else float(np.linalg.norm(gpu)),
        "echo_amplitude_cpu": complex(np.vdot(cisd[:, 0], cpu_echoed[:, 0])),
        "selected_batch_backend": "cpu" if gpu is None or cpu_timing["total"] <= gpu_timing["total"] else "gpu",
        "source_direct_schur_point_timing": source["training_direct_points"][0]["timing_seconds"],
    }
    _write(args.output.resolve(), payload)
    if not passed:
        raise RuntimeError("representative CPU/GPU PF action mismatch")
    return 0


def _iter_truth_points(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "time" in value and "signed_direct_shift_hartree" in value:
            yield value
        for item in value.values():
            yield from _iter_truth_points(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_truth_points(item)


def _source_truth_lookup(source_root: Path, condition: str, formula: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    paths = [source_root / "raw" / f"{condition}__{formula}.json"]
    fine = source_root / "fine" / "raw" / f"{condition}__{formula}.json"
    if fine.exists():
        paths.append(fine)
    points: list[dict[str, Any]] = []
    provenance = []
    for path in paths:
        payload = _load(path)
        provenance.append({"path": str(path), "sha256": _sha256(path)})
        for point in _iter_truth_points(payload):
            if not any(_same_time(point["time"], old["time"]) for old in points):
                points.append(dict(point))
    return points, provenance


def _branch_schur_point(
    unitary: np.ndarray, exact_state: np.ndarray, energy: float,
    time_value: float, rotations: int, previous_vector: np.ndarray | None,
) -> tuple[dict[str, Any], np.ndarray]:
    started = time.perf_counter()
    triangular, vectors = schur(unitary, output="complex", check_finite=False)
    schur_seconds = time.perf_counter() - started
    eigenvalues = np.diag(triangular)
    exact_overlaps = np.abs(vectors.conj().T @ exact_state) ** 2
    independent = int(np.argmax(exact_overlaps))
    if previous_vector is None:
        selected = independent
        adjacent = None
        selection = "initial maximum exact-ground overlap"
    else:
        adjacent_overlaps = np.abs(vectors.conj().T @ previous_vector) ** 2
        selected = int(np.argmax(adjacent_overlaps))
        adjacent = float(adjacent_overlaps[selected])
        selection = "continuous maximum previous-selected-vector overlap"
    eigenvalue = complex(eigenvalues[selected])
    vector = np.asarray(vectors[:, selected], dtype=np.complex128)
    shift = float(
        np.angle(np.exp(-1j * float(energy) * float(time_value)) * eigenvalue)
        / float(time_value)
    )
    result = {
        "time": float(time_value),
        "signed_direct_shift_hartree": shift,
        "direct_error_hartree": abs(shift),
        "direct_cost": diagnosis._cost(time_value, abs(shift), rotations),
        "ground_overlap_probability": float(exact_overlaps[selected]),
        "adjacent_selected_vector_overlap_probability": adjacent,
        "selected_eigenvalue": eigenvalue,
        "selected_eigenvalue_magnitude": float(abs(eigenvalue)),
        "eigenpair_residual_2_norm": float(
            np.linalg.norm(unitary @ vector - eigenvalue * vector)
        ),
        "schur_seconds": float(schur_seconds),
        "selection_rule": selection,
        "independent_maximum_exact_overlap_index": independent,
        "continuous_selected_index": selected,
        "branch_selection_disagrees_with_independent_rule": bool(selected != independent),
        "independent_ground_overlap_probability": float(exact_overlaps[independent]),
    }
    return result, vector


def _compute_truth(
    system: dict[str, Any], sequence: Sequence[float], rotations: int,
    times: Sequence[float], backend: str, gpu_id: int,
    source_points: Sequence[dict[str, Any]],
    checkpoint_dir: Path,
    cache_key_prefix: dict[str, Any],
) -> list[dict[str, Any]]:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    previous: np.ndarray | None = None
    for time_value in sorted(set(map(float, times))):
        reused = next(
            (dict(item) for item in source_points if _same_time(item["time"], time_value)),
            None,
        )
        if reused is not None:
            reused["truth_provenance"] = "audited_source_artifact"
            reused["branch_continuity_note"] = (
                "source point reused after hash/metadata/PF validation; source did not retain eigenvector"
            )
            results.append(reused)
            continue
        cache_key = {**cache_key_prefix, "absolute_time": float(time_value)}
        key_sha256 = hashlib.sha256(
            json.dumps(cache_key, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        point_path = checkpoint_dir / f"{key_sha256}.json"
        vector_path = checkpoint_dir / f"{key_sha256}.npy"
        if point_path.exists() and vector_path.exists():
            checkpoint = _load(point_path)
            if (
                checkpoint.get("status") == "complete"
                and checkpoint.get("cache_key") == cache_key
                and checkpoint.get("selected_vector_sha256") == _sha256(vector_path)
            ):
                vector = np.load(vector_path)
                results.append(dict(checkpoint["point"]))
                previous = np.asarray(vector, dtype=np.complex128)
                continue
        started = time.perf_counter()
        if backend == "gpu":
            unitary, build = diagnosis._build_gpu(system, sequence, time_value, gpu_id)
        else:
            unitary, build = diagnosis._build_cpu(system, sequence, time_value)
        point, vector = _branch_schur_point(
            unitary, system["state"], system["energy"], time_value,
            rotations, previous,
        )
        point["timing_seconds"] = {
            **build,
            "schur": point.pop("schur_seconds"),
            "total": float(time.perf_counter() - started),
        }
        point["peak_cpu_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        point["truth_provenance"] = "new_h01_continuous_branch_calculation"
        results.append(point)
        previous = vector
        temporary_vector = vector_path.with_suffix(".npy.tmp")
        with temporary_vector.open("wb") as stream:
            np.save(stream, vector)
        os.replace(temporary_vector, vector_path)
        _write(point_path, {
            "status": "complete", "cache_key": cache_key,
            "selected_vector_sha256": _sha256(vector_path), "point": point,
        })
        del unitary
    return results


def _truth_at(points: Sequence[dict[str, Any]], time_value: float) -> dict[str, Any]:
    matches = [point for point in points if _same_time(point["time"], time_value)]
    if not matches:
        raise RuntimeError(f"expected a truth point at {time_value}, found none")
    reference = matches[0]
    for duplicate in matches[1:]:
        shift_difference = abs(
            float(duplicate["signed_direct_shift_hartree"])
            - float(reference["signed_direct_shift_hartree"])
        )
        if shift_difference > 1e-11:
            raise RuntimeError(
                f"inconsistent duplicate truth at {time_value}: "
                f"signed-shift difference {shift_difference}"
            )
    # Reuse can make the same audited point appear in the source, coarse, and
    # fine collections.  Identical duplicates are one physical truth point.
    preferred = next(
        (
            point for point in reversed(matches)
            if point.get("truth_provenance")
            == "new_h01_continuous_branch_calculation"
        ),
        matches[-1],
    )
    return dict(preferred)


def _model_metrics(
    model: dict[str, Any], optimum: dict[str, Any], relative_grid: Sequence[float],
    truth: Sequence[dict[str, Any]], rotations: int,
) -> dict[str, Any]:
    rows = []
    for relative in relative_grid:
        time_value = float(relative) * float(optimum["time"])
        point = _truth_at(truth, time_value)
        prediction = diagnosis._prediction(model, time_value)
        point.update({
            "relative_to_t_star": float(relative),
            "model_signed_shift_hartree": prediction,
            "model_cost": diagnosis._cost(time_value, abs(prediction), rotations),
            "signed_residual_hartree": float(
                point["signed_direct_shift_hartree"] - prediction
            ),
            "residual_over_epsilon": float(
                abs(point["signed_direct_shift_hartree"] - prediction)
                / _protocol()["target_error_hartree"]
            ),
        })
        rows.append(point)
    at_star = next(point for point in rows if _same_time(point["relative_to_t_star"], 1.0))
    finite = [point for point in rows if point.get("direct_cost") is not None]
    minimum = min(finite, key=lambda point: float(point["direct_cost"])) if finite else None
    metrics = {
        "eta_star": None if at_star.get("direct_cost") is None else float(
            abs(optimum["cost"] - at_star["direct_cost"]) / at_star["direct_cost"]
        ),
        "eta_min": None if minimum is None or at_star.get("direct_cost") is None else float(
            at_star["direct_cost"] / minimum["direct_cost"] - 1.0
        ),
        "eta_t": None if minimum is None else float(
            abs(optimum["time"] / minimum["time"] - 1.0)
        ),
        "maximum_unseen_residual_over_epsilon": max(
            float(point["residual_over_epsilon"]) for point in rows
        ),
    }
    checks = {
        key: metrics[key] is not None and metrics[key] <= threshold
        for key, threshold in _protocol()["pass_thresholds"].items()
    }
    epsilon_model = _protocol()["target_error_hartree"] - abs(
        diagnosis._prediction(model, optimum["time"])
    )
    budget = []
    for multiplier in _protocol()["frozen_budget_cost_multipliers"]:
        epsilon_qpe = epsilon_model / float(multiplier)
        total = abs(at_star["signed_direct_shift_hartree"]) + epsilon_qpe
        budget.append({
            "cost_multiplier": float(multiplier),
            "epsilon_qpe_hartree": float(epsilon_qpe),
            "total_error_hartree": float(total),
            "target_met": bool(total <= _protocol()["target_error_hartree"]),
        })
    return {
        "model": model, "model_optimum": optimum,
        "direct_validation_points": rows,
        "direct_grid_minimum": minimum,
        "metrics": metrics, "checks": checks,
        "passed": all(checks.values()), "frozen_budget": budget,
    }


def _fine_candidate(coarse: dict[str, Any]) -> list[str]:
    if coarse["passed"]:
        return ["all_four_coarse_checks_passed"]
    metrics = coarse["metrics"]
    thresholds = _protocol()["pass_thresholds"]
    failed = [key for key, passed in coarse["checks"].items() if not passed]
    reasons = []
    if len(failed) == 1 and metrics[failed[0]] is not None:
        if metrics[failed[0]] <= 2.0 * thresholds[failed[0]]:
            reasons.append(f"single_near_threshold_failure:{failed[0]}")
    costs = [point.get("direct_cost") for point in coarse["direct_validation_points"]]
    for index in range(1, len(costs) - 1):
        if all(cost is not None for cost in costs[index - 1:index + 2]):
            if costs[index] <= 0.98 * min(costs[index - 1], costs[index + 1]):
                reasons.append("conclusion_changing_isolated_minimum")
                break
    return reasons


def command_truth(args: argparse.Namespace) -> int:
    system = _load_system(args.cache.resolve())
    echo = _load(args.echo.resolve())
    if echo["status"] != "complete" or not echo["sanity"]["passed_before_approximate_state_interpretation"]:
        raise RuntimeError("echo stage incomplete or sanity failed")
    sequence = diagnosis._formula_s2_sequence(args.formula)
    rotations = _rotation_count(system, sequence)
    source_root = args.project_root.resolve() / SOURCE_RELATIVE
    source_points, provenance = _source_truth_lookup(
        source_root, args.condition, args.formula
    )
    coarse_grid = _protocol()["direct_validation"]["coarse_relative_to_proxy_t_star"]
    requests = []
    for method in STATE_METHODS:
        for model_name, model in echo["models"][method].items():
            optimum = model["optimum"]
            for relative in coarse_grid:
                requests.append(float(relative) * float(optimum["time"]))
    coarse_truth = _compute_truth(
        system, sequence, rotations, requests, args.backend, args.gpu_id,
        source_points,
        args.output.resolve().parent / "checkpoints" / args.output.stem / "coarse",
        {
            "protocol_sha256": _sha256(PROTOCOL_PATH),
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "state_method": "exact_ground_direct_truth",
            "pf": args.formula, "kind": "direct_truth_coarse",
            "numeric_backend": f"complex128_{args.backend}_dense_cpu_schur",
        },
    )
    results: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = []
    for method in STATE_METHODS:
        results[method] = {}
        for model_name, model in echo["models"][method].items():
            coarse = _model_metrics(
                model, model["optimum"], coarse_grid, coarse_truth, rotations
            )
            reasons = _fine_candidate(coarse)
            coarse["fine_candidate_reasons"] = reasons
            results[method][model_name] = {"coarse": coarse}
            if reasons:
                candidates.append({
                    "method": method, "model": model_name,
                    "optimum": model["optimum"], "reasons": reasons,
                })
    fine_spec = _protocol()["direct_validation"]["fine_relative_to_proxy_t_star"]
    fine_grid = np.arange(
        float(fine_spec["start"]), float(fine_spec["stop"]) + 0.5 * float(fine_spec["step"]),
        float(fine_spec["step"]),
    ).tolist()
    fine_requests = [
        float(relative) * float(candidate["optimum"]["time"])
        for candidate in candidates for relative in fine_grid
    ]
    fine_truth = _compute_truth(
        system, sequence, rotations, fine_requests, args.backend, args.gpu_id,
        list(source_points) + list(coarse_truth),
        args.output.resolve().parent / "checkpoints" / args.output.stem / "fine",
        {
            "protocol_sha256": _sha256(PROTOCOL_PATH),
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "state_method": "exact_ground_direct_truth",
            "pf": args.formula, "kind": "direct_truth_fine",
            "numeric_backend": f"complex128_{args.backend}_dense_cpu_schur",
        },
    ) if fine_requests else []
    combined_truth = list(source_points) + list(coarse_truth) + list(fine_truth)
    for candidate in candidates:
        method, model_name = candidate["method"], candidate["model"]
        model = echo["models"][method][model_name]
        results[method][model_name]["fine"] = _model_metrics(
            model, model["optimum"], fine_grid, combined_truth, rotations
        )
    payload = {
        "status": "complete", "condition": args.condition,
        "formula": args.formula, "protocol_sha256": _sha256(PROTOCOL_PATH),
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "backend": args.backend, "physical_gpu_id": args.gpu_id,
        "source_truth_provenance": provenance,
        "coarse_unique_truth_points": coarse_truth,
        "fine_unique_truth_points": fine_truth,
        "fine_candidates": candidates, "models": results,
        "branch_rule": _protocol()["direct_validation"]["branch_rule"],
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }
    _write(args.output.resolve(), payload)
    return 0


def command_manifest(args: argparse.Namespace) -> int:
    protocol_hash = _sha256(PROTOCOL_PATH)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("fixed H01 protocol SHA-256 mismatch")
    source_root = args.project_root.resolve() / SOURCE_RELATIVE
    audit = source_root / "post_run_audit.json"
    payload = {
        "status": "running", "protocol_id": _protocol()["protocol_id"],
        "protocol_sha256": protocol_hash,
        "protocol_expected_sha256": EXPECTED_PROTOCOL_SHA256,
        "protocol_hash_matches": True,
        "git": diagnosis._git_state(), "environment": diagnosis._versions(),
        "source": {
            **_protocol()["source"],
            "post_run_audit_sha256": _sha256(audit),
            "post_run_audit_path": str(audit.relative_to(args.project_root.resolve())),
        },
        "conditions": _conditions(), "formulae": list(FORMULAE),
        "state_methods": list(STATE_METHODS),
        "known_incomplete": [
            "H05 end-to-end time-scale determination is outside H01 scope",
            "exact analytic_time is deliberately reused as an oracle query scale",
        ],
    }
    _write(args.output.resolve(), payload)
    return 0


def command_aggregate(args: argparse.Namespace) -> int:
    root = args.artifact_root.resolve()
    rows = []
    for condition in _conditions():
        for formula in FORMULAE:
            truth = _load(root / "truth" / f"{condition}__{formula}.json")
            for method in STATE_METHODS:
                for model_name, result in truth["models"][method].items():
                    selected = result.get("fine") or result["coarse"]
                    rows.append({
                        "condition": condition, "formula": formula,
                        "state_method": method, "model": model_name,
                        "grid": "fine" if result.get("fine") else "coarse",
                        "passed": bool(selected["passed"]),
                        "budget_1_01_met": next(
                            entry["target_met"] for entry in selected["frozen_budget"]
                            if _same_time(entry["cost_multiplier"], 1.01)
                        ),
                        **selected["metrics"],
                        "predicted_time": selected["model_optimum"]["time"],
                        "direct_minimum_time": None if selected["direct_grid_minimum"] is None else selected["direct_grid_minimum"]["time"],
                        "direct_minimum_cost": None if selected["direct_grid_minimum"] is None else selected["direct_grid_minimum"]["direct_cost"],
                    })
    primary = set(_protocol()["conditions"]["primary_development"])
    decisions = {}
    for method in STATE_METHODS:
        decisions[method] = {}
        for formula in FORMULAE:
            selected = [
                row for row in rows
                if row["condition"] in primary and row["state_method"] == method
                and row["formula"] == formula and row["model"] == "echo_phase_5point"
            ]
            decisions[method][formula] = {
                "conditions": len(selected),
                "all_four_pass": len(selected) == 4 and all(row["passed"] for row in selected),
                "budget_1_01_all_four": len(selected) == 4 and all(row["budget_1_01_met"] for row in selected),
            }
    exact_sanity = all(
        _load(root / "echo" / f"{condition}__{formula}.json")["sanity"]
        ["passed_before_approximate_state_interpretation"]
        for condition in _conditions() for formula in FORMULAE
    )
    summary = {
        "status": "complete", "protocol_sha256": _sha256(PROTOCOL_PATH),
        "exact_echo_identity_and_sign_sanity": exact_sanity,
        "decisions": decisions, "rows": rows,
        "scope_note": "Development state-substitution diagnostic using oracle-derived analytic times; not end-to-end calibration.",
    }
    (root / "aggregate").mkdir(parents=True, exist_ok=True)
    _write(root / "aggregate" / "summary.json", summary)
    report = [
        "# H01 approximate-state calibration", "",
        f"- Exact echo identity/sign sanity: **{'PASS' if exact_sanity else 'FAIL'}**",
        "- The source analytic times are intentionally reused; this is not end-to-end calibration.",
        "", "## Primary echo-phase five-point decision", "",
        "| State | PF | Four-condition pass | 1% frozen-budget pass |",
        "|---|---|---:|---:|",
    ]
    for method in STATE_METHODS:
        for formula in FORMULAE:
            item = decisions[method][formula]
            report.append(
                f"| {method} | {formula} | {item['all_four_pass']} | {item['budget_1_01_all_four']} |"
            )
    report += [
        "", "## Scope", "",
        "HF is auxiliary only. No coefficients, thresholds, molecules, model powers, or time grids were adapted.",
    ]
    (root / "aggregate" / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest = _load(manifest_path)
    manifest.update({"status": "complete", "aggregate": "aggregate/summary.json"})
    _write(manifest_path, manifest)
    (root / "COMPLETE").touch()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    manifest = sub.add_parser("manifest")
    manifest.add_argument("--project-root", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(func=command_manifest)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--condition", choices=_conditions(), required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--component-processes", type=int, default=4)
    prepare.set_defaults(func=command_prepare)
    echo = sub.add_parser("echo")
    echo.add_argument("--project-root", type=Path, required=True)
    echo.add_argument("--condition", choices=_conditions(), required=True)
    echo.add_argument("--formula", choices=FORMULAE, required=True)
    echo.add_argument("--cache", type=Path, required=True)
    echo.add_argument("--output", type=Path, required=True)
    echo.add_argument("--backend", choices=("cpu", "gpu"), default="cpu")
    echo.add_argument("--gpu-id", type=int, default=0)
    echo.set_defaults(func=command_echo)
    pilot = sub.add_parser("pilot")
    pilot.add_argument("--project-root", type=Path, required=True)
    pilot.add_argument("--cache", type=Path, required=True)
    pilot.add_argument("--output", type=Path, required=True)
    pilot.add_argument("--gpu-id", type=int, required=True)
    pilot.set_defaults(func=command_pilot)
    truth = sub.add_parser("truth")
    truth.add_argument("--project-root", type=Path, required=True)
    truth.add_argument("--condition", choices=_conditions(), required=True)
    truth.add_argument("--formula", choices=FORMULAE, required=True)
    truth.add_argument("--cache", type=Path, required=True)
    truth.add_argument("--echo", type=Path, required=True)
    truth.add_argument("--output", type=Path, required=True)
    truth.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    truth.add_argument("--gpu-id", type=int, default=0)
    truth.set_defaults(func=command_truth)
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--artifact-root", type=Path, required=True)
    aggregate.set_defaults(func=command_aggregate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
