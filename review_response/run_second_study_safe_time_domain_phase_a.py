"""Oracle-free Phase A runner for the frozen safe-time-domain study."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import resource
import shutil
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np

from review_response import second_study_safe_time_domain_execution as execution
from review_response import second_study_safe_time_domain_guard as guard


PREFLIGHT_RESULT_COMMIT = "2b37191594d7f79565314a5dad0d889f78aec504"
PREFLIGHT_RELATIVE_ROOT = Path(
    "artifacts/"
    "server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0"
)
PREFLIGHT_ENVIRONMENT_SHA256 = (
    "2e5cc1e8f476393c1e6dff4ed481bf723a83545d4a50f432cfb229215e71bf2d"
)
EXPECTED_PYTHON = "/home/AbeHiromu/venvs/trotter-common/bin/python"
EXPECTED_PYTHONPATH_SUFFIX = (
    "/home/AbeHiromu/projects/"
    "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
    "using-higher-order-product-formulae/venv/lib/python3.12/site-packages"
)
EXPECTED_LD_LIBRARY_PATH = ":".join(
    [
        "/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib",
        "/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib",
        "/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib",
        "/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib",
        "/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib",
    ]
)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise execution.ExecutionError("non-finite value in committed JSON")
        return value
    if isinstance(value, complex):
        return {"real": float(value.real), "imaginary": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    execution.atomic_write_json(path, _jsonable(payload))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise execution.ExecutionError(f"refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(str(key))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows([_jsonable(dict(row)) for row in rows])


def _git_blob_sha256(project_root: Path, commit: str, relative: Path) -> str:
    content = __import__("subprocess").run(
        ["git", "show", f"{commit}:{relative.as_posix()}"],
        cwd=project_root,
        check=True,
        capture_output=True,
    ).stdout
    return execution.sha256_bytes(content)


def validate_preflight(project_root: Path, preflight_root: Path) -> dict[str, Any]:
    expected_root = (project_root / PREFLIGHT_RELATIVE_ROOT).resolve()
    if preflight_root.resolve() != expected_root:
        raise execution.ExecutionError(
            f"preflight root must be the fixed v1.4 artifact: {expected_root}"
        )
    ancestor = __import__("subprocess").run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            PREFLIGHT_RESULT_COMMIT,
            "HEAD",
        ],
        cwd=project_root,
        check=False,
    ).returncode
    if ancestor != 0:
        raise execution.ExecutionError(
            "formal v1.4 preflight result commit is not an ancestor of HEAD"
        )
    required = {
        "decision.json",
        "manifest.json",
        "python_environment_identity.json",
        "PREFLIGHT_ONLY_COMPLETE",
    }
    if not all((preflight_root / name).is_file() for name in required):
        raise execution.ExecutionError("formal v1.4 preflight artifact is incomplete")
    manifest = execution.load_json(preflight_root / "manifest.json")
    for row in manifest.get("files", []):
        path = preflight_root / str(row["path"])
        if not path.is_file() or execution.sha256_file(path) != row["sha256"]:
            raise execution.ExecutionError(f"preflight manifest mismatch: {path}")
        relative = PREFLIGHT_RELATIVE_ROOT / str(row["path"])
        if execution.sha256_file(path) != _git_blob_sha256(
            project_root, PREFLIGHT_RESULT_COMMIT, relative
        ):
            raise execution.ExecutionError(
                f"preflight file differs from result commit: {relative}"
            )
    decision = execution.load_json(preflight_root / "decision.json")
    if decision.get("status") != "preflight_pass_phase_a_not_authorized":
        raise execution.ExecutionError("v1.4 preflight status is not passed")
    if decision.get("phase_b_authorized") is not False:
        raise execution.ExecutionError("unexpected Phase B authorization in preflight")
    gates = decision.get("gates", {})
    if not gates or any(
        row.get("status") not in {
            "passed",
            "passed_no_numeric_contamination_hits",
        }
        for row in gates.values()
    ):
        raise execution.ExecutionError("not all v1.4 preflight gates passed")
    if decision["independence_search"]["suspicious_hit_count"] != 0:
        raise execution.ExecutionError("independence preflight has suspicious hits")
    if decision["independence_search"]["independent_condition_numeric_result_hits"] != 0:
        raise execution.ExecutionError("independent-condition result contamination")
    if execution.sha256_file(
        preflight_root / "python_environment_identity.json"
    ) != PREFLIGHT_ENVIRONMENT_SHA256:
        raise execution.ExecutionError("preflight environment identity hash mismatch")
    return {
        "result_commit": PREFLIGHT_RESULT_COMMIT,
        "root": str(preflight_root.resolve()),
        "decision_sha256": execution.sha256_file(preflight_root / "decision.json"),
        "manifest_sha256": execution.sha256_file(preflight_root / "manifest.json"),
        "python_environment_identity_sha256": PREFLIGHT_ENVIRONMENT_SHA256,
        "status": decision["status"],
    }


def validate_process_environment(project_root: Path) -> dict[str, Any]:
    requested = Path(EXPECTED_PYTHON)
    if Path(sys.executable).resolve() != requested.resolve():
        raise execution.ExecutionError(
            f"Phase A requires {EXPECTED_PYTHON}; obtained {sys.executable}"
        )
    pythonpath = os.environ.get("PYTHONPATH", "")
    entries = pythonpath.split(":")
    if entries[:3] != ["src", "review_response", "."] or entries[3:] != [
        EXPECTED_PYTHONPATH_SUFFIX
    ]:
        raise execution.ExecutionError("Phase A PYTHONPATH differs from v1.4 overlay")
    if os.environ.get("LD_LIBRARY_PATH") != EXPECTED_LD_LIBRARY_PATH:
        raise execution.ExecutionError(
            "Phase A LD_LIBRARY_PATH differs from v1.4 overlay"
        )
    if os.environ.get("PYTHONNOUSERSITE") != "1":
        raise execution.ExecutionError("PYTHONNOUSERSITE=1 is required")
    if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise execution.ExecutionError("PYTHONDONTWRITEBYTECODE=1 is required")
    if Path.cwd().resolve() != project_root.resolve():
        raise execution.ExecutionError("Phase A must run from --project-root")
    return {
        "sys_executable": sys.executable,
        "realpath": str(Path(sys.executable).resolve()),
        "python_version": sys.version,
        "pythonpath": pythonpath,
        "ld_library_path": os.environ["LD_LIBRARY_PATH"],
        "python_no_user_site": os.environ["PYTHONNOUSERSITE"],
        "python_dont_write_bytecode": os.environ["PYTHONDONTWRITEBYTECODE"],
    }


def _expected_dimension(spec: Mapping[str, Any]) -> int:
    from math import comb

    orbitals = int(spec["active_spatial_orbitals"])
    electrons = int(spec["active_electrons"])
    alpha = electrons // 2
    beta = electrons - alpha
    return int(comb(orbitals, alpha) * comb(orbitals, beta))


def prepare_condition(
    spec: Mapping[str, Any],
    protocol_sha256: str,
    work_dir: Path,
    processes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one selector input without diagonalizing the Hamiltonian."""

    from openfermion.ops import FermionOperator, QubitOperator
    from openfermion.transforms import jordan_wigner
    from pyscf import ao2mo, ci, gto, mcscf, scf
    import run_full_electron_nh3_higher_term_diagnosis as diagnosis
    import run_h01_approximate_state_calibration as h01
    import run_unused_molecule_frozen_holdout as source_runner
    from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
    from trotterlib.component_sector_pf import (
        find_balanced_z2_symmetry,
        prepare_component_spectra,
        qubit_operator_sector_matrix,
    )

    name = str(spec["name"])
    started = time.perf_counter()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    work_dir.mkdir(parents=True, exist_ok=False)
    molecule = gto.Mole()
    molecule.atom = [
        (atom, coordinates) for atom, coordinates in spec["geometry_angstrom"]
    ]
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
        raise execution.ExecutionError(f"{name}: RHF did not converge")

    ncore = int(spec["frozen_core_spatial_orbitals"])
    ncas = int(spec["active_spatial_orbitals"])
    nelecas = int(molecule.nelectron - 2 * ncore)
    nelec = (nelecas // 2, nelecas - nelecas // 2)
    if int(mean_field.mo_coeff.shape[1]) != ncore + ncas:
        raise execution.ExecutionError(f"{name}: unexpected spatial-orbital count")
    if nelecas != int(spec["active_electrons"]):
        raise execution.ExecutionError(f"{name}: unexpected active-electron count")

    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = ncore
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    active_coefficients = np.asarray(
        mean_field.mo_coeff[:, ncore : ncore + ncas]
    )
    eri_compact = ao2mo.kernel(molecule, active_coefficients)
    eri_active = ao2mo.restore(1, eri_compact, ncas)
    two_body = np.asarray(eri_active.transpose(0, 2, 3, 1), order="C")
    grouper = Almost_optimal_grouper(
        float(core_energy),
        np.asarray(h1_effective),
        two_body,
        fermion_qubit_mapping=jordan_wigner,
        validation=True,
    )
    grouped = grouper.group_term_list
    grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
    groups = [
        source_runner._hermitize(
            jordan_wigner(sum(group, FermionOperator()))
        )[0]
        for group in grouped
    ]
    hamiltonian_operator, hermitization = source_runner._hermitize(
        sum(groups, QubitOperator())
    )
    constant = float(complex(hamiltonian_operator.terms.get((), 0.0)).real)
    population_basis = diagnosis._population_basis(ncas, *nelec)
    if int(population_basis.size) != _expected_dimension(spec):
        raise execution.ExecutionError(f"{name}: population dimension mismatch")
    population_hamiltonian = qubit_operator_sector_matrix(
        groups[0], 2 * ncas, population_basis, remove_constant=True
    )
    for group in groups[1:]:
        population_hamiltonian += qubit_operator_sector_matrix(
            group, 2 * ncas, population_basis, remove_constant=True
        )

    rhf_started = time.perf_counter()
    population_rhf = h01.rhf_population_state(ncas, nelec, population_basis)
    rhf_seconds = time.perf_counter() - rhf_started
    cisd_started = time.perf_counter()
    frozen = list(range(ncore)) if ncore else None
    cisd_solver = ci.CISD(mean_field, frozen=frozen)
    cisd_solver.conv_tol = 1e-10
    cisd_solver.max_cycle = 200
    cisd_correlation_energy, cisd_vector = cisd_solver.kernel()
    if not cisd_solver.converged:
        raise execution.ExecutionError(f"{name}: CISD did not converge")
    active_fcivec = ci.cisd.to_fcivec(cisd_vector, ncas, nelec)
    population_cisd = h01.fcivec_to_population(
        active_fcivec, ncas, nelec, population_basis
    )
    population_cisd /= np.linalg.norm(population_cisd)
    cisd_seconds = time.perf_counter() - cisd_started

    try:
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups,
            2 * ncas,
            population_basis,
            population_cisd,
            support_cutoff=0.0,
        )
        symmetry = {
            key.replace("ground_state", "cisd_state"): value
            for key, value in symmetry.items()
        }
        symmetry["target_source"] = "cisd_support_only"
        symmetry["cisd_support_cutoff"] = 0.0
    except RuntimeError as exc:
        if "No nonconstant exact diagonal-Z symmetry" not in str(exc):
            raise
        mask, target = 0, 0
        selected = np.arange(population_basis.size, dtype=np.int64)
        symmetry = {
            "kind": "full_fixed_population_sector",
            "target_source": "no_nonconstant_cisd_support_symmetry",
            "population_sector_dimension": int(population_basis.size),
            "restricted_dimension": int(population_basis.size),
        }
    selected = np.asarray(selected, dtype=np.int64)
    selected_mask = np.zeros(population_basis.size, dtype=bool)
    selected_mask[selected] = True
    cisd_outside = float(np.linalg.norm(population_cisd[~selected_mask]))
    rhf_outside = float(np.linalg.norm(population_rhf[~selected_mask]))
    if max(cisd_outside, rhf_outside) > 1e-8:
        raise execution.ExecutionError(
            f"{name}: RHF/CISD support is not contained in selected sector"
        )
    restricted_basis = population_basis[selected]
    hamiltonian = population_hamiltonian[selected, :][:, selected].tocsr()
    cisd_state = population_cisd[selected].copy()
    cisd_state /= np.linalg.norm(cisd_state)
    rhf_state = population_rhf[selected].copy()
    rhf_state /= np.linalg.norm(rhf_state)
    cisd_action = np.asarray(hamiltonian @ cisd_state)
    cisd_energy = float(np.vdot(cisd_state, cisd_action).real)
    cisd_centered = cisd_action - cisd_energy * cisd_state
    cisd_total_from_matrix = cisd_energy + constant
    if abs(cisd_total_from_matrix - float(cisd_solver.e_tot)) > 1e-8:
        raise execution.ExecutionError(
            f"{name}: CISD determinant mapping energy mismatch"
        )
    spectra_started = time.perf_counter()
    spectra, compact = prepare_component_spectra(
        groups,
        2 * ncas,
        restricted_basis,
        validation_state=cisd_state,
        processes=int(processes),
    )
    spectra_seconds = time.perf_counter() - spectra_started
    summed_action = np.asarray(compact.pop("summed_group_action"))
    component_action_residual = float(
        np.linalg.norm(summed_action - cisd_action)
    )
    if component_action_residual > 1e-10:
        raise execution.ExecutionError(
            f"{name}: component-sum action residual {component_action_residual}"
        )
    term_counts = [
        sum(1 for term in group.terms if term) for group in groups
    ]
    system = {
        "schema": "second_study_safe_time_domain_phase_a_system_v1",
        "condition": name,
        "protocol_sha256": protocol_sha256,
        "hamiltonian_sha256": h01._sparse_hash(hamiltonian),
        "hamiltonian": hamiltonian,
        "component_spectra": spectra,
        "term_counts": term_counts,
        "cisd_state": cisd_state,
        "rhf_state": rhf_state,
        "restricted_basis": restricted_basis,
        "num_qubits": 2 * ncas,
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
        "group_sha256": h01._group_hashes(groups),
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "removed_constant_hartree": constant,
        "z2_mask": int(mask),
        "z2_target": int(target),
        "z2_symmetry": symmetry,
        "rhf_sector_outside_norm": rhf_outside,
        "cisd_sector_outside_norm": cisd_outside,
        "cisd_normalization": float(np.linalg.norm(cisd_state)),
        "cisd_energy_expectation_without_constant_hartree": cisd_energy,
        "cisd_hamiltonian_residual_2_norm": float(np.linalg.norm(cisd_centered)),
        "cisd_pyscf_total_energy_hartree": float(cisd_solver.e_tot),
        "cisd_pyscf_correlation_energy_hartree": float(
            cisd_correlation_energy
        ),
        "cisd_matrix_plus_constant_energy_hartree": cisd_total_from_matrix,
        "cisd_generation_seconds": float(cisd_seconds),
        "rhf_state_generation_seconds": float(rhf_seconds),
        "component_spectrum_build_seconds": float(spectra_seconds),
        "component_sum_cisd_action_residual_2_norm": component_action_residual,
        "component_representation": compact,
        "numerical_hermitization": hermitization,
        "scf_energy_hartree": float(mean_field.e_tot),
        "scf_converged": bool(mean_field.converged),
        "preparation_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "peak_cpu_rss_increment_kib": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss_before
        ),
        "exact_diagonalization_count": 0,
        "direct_pf_eigenpair_count": 0,
    }
    return system, metadata


def _rotation_count(
    system: Mapping[str, Any], sequence: Sequence[float]
) -> int:
    import run_h01_approximate_state_calibration as h01

    return h01._rotation_count(dict(system), sequence)


def proxy_point(
    system: Mapping[str, Any],
    sequence: Sequence[float],
    time_value: float,
) -> dict[str, Any]:
    import run_h01_approximate_state_calibration as h01
    from scipy.sparse.linalg import expm_multiply

    state = np.asarray(system["cisd_state"], dtype=np.complex128)
    started = time.perf_counter()
    pf_state, pf_timing = h01._apply_pf_cpu(
        dict(system), sequence, float(time_value), state[:, None]
    )
    pf_vector = np.asarray(pf_state[:, 0])
    reference_started = time.perf_counter()
    backward_state = expm_multiply(
        (1j * float(time_value)) * system["hamiltonian"], state
    )
    reference_seconds = time.perf_counter() - reference_started
    echo = complex(np.vdot(backward_state, pf_vector))
    state_error = float(np.linalg.norm(pf_vector - backward_state))
    diagonal_signal = abs(float(echo.imag))
    return {
        "time_hartree_inverse": float(time_value),
        "proxy_hartree": float(echo.imag / float(time_value)),
        "echo_real": float(echo.real),
        "echo_imaginary": float(echo.imag),
        "state_error_2_norm": state_error,
        "cancellation_index": diagonal_signal
        / max(state_error, np.finfo(float).tiny),
        "pf_state_norm": float(np.linalg.norm(pf_vector)),
        "backward_hamiltonian_state_norm": float(np.linalg.norm(backward_state)),
        "pf_action_seconds": float(pf_timing["total"]),
        "hamiltonian_exponential_action_seconds": float(reference_seconds),
        "proxy_point_seconds": float(time.perf_counter() - started),
    }


def _proxy_cache_path(
    output_dir: Path, condition: str, time_value: float
) -> Path:
    digest = hashlib.sha256(float(time_value).hex().encode("ascii")).hexdigest()
    return output_dir / ".runtime/proxy_cache" / condition / f"{digest}.json"


def cached_proxy_point(
    *,
    output_dir: Path,
    condition: str,
    system: Mapping[str, Any],
    sequence: Sequence[float],
    time_value: float,
    protocol_sha256: str,
    formula_sha256: str,
    counters: dict[str, int],
) -> dict[str, Any]:
    path = _proxy_cache_path(output_dir, condition, time_value)
    cache_key = {
        "protocol_sha256": protocol_sha256,
        "condition": condition,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "formula_sha256": formula_sha256,
        "absolute_time_hex": float(time_value).hex(),
        "backend": "cpu",
        "dtype": "complex128",
        "calculation": "cisd_echo_proxy",
    }
    if path.is_file():
        payload = execution.load_json(path)
        if payload.get("cache_key") != cache_key:
            raise execution.ExecutionError(f"stale Phase A proxy cache: {path}")
        counters["reused"] += 1
        return dict(payload["point"])
    point = proxy_point(system, sequence, time_value)
    _write_json(path, {"cache_key": cache_key, "point": point})
    counters["computed"] += 1
    return point


def proxy_analytic_scale(
    *,
    output_dir: Path,
    condition: str,
    system: Mapping[str, Any],
    sequence: Sequence[float],
    protocol: Mapping[str, Any],
    protocol_sha256: str,
    formula_sha256: str,
    counters: dict[str, int],
) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    from trotterlib.fit_window import rolling_loglog_fits

    spec = protocol["phase_a"]["time_scale"]
    grid = np.geomspace(
        float(spec["absolute_minimum_hartree_inverse"]),
        float(spec["absolute_maximum_hartree_inverse"]),
        int(spec["grid_count"]),
    )
    points: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    windows: list[dict[str, Any]] = []
    for time_value in grid:
        point = cached_proxy_point(
            output_dir=output_dir,
            condition=condition,
            system=system,
            sequence=sequence,
            time_value=float(time_value),
            protocol_sha256=protocol_sha256,
            formula_sha256=formula_sha256,
            counters=counters,
        )
        points.append(point)
        if len(points) < int(spec["rolling_window_points"]):
            continue
        windows = rolling_loglog_fits(
            np.asarray(
                [row["time_hartree_inverse"] for row in points], dtype=float
            ),
            np.asarray([abs(row["proxy_hartree"]) for row in points], dtype=float),
            formal_order=int(spec["formal_order"]),
            noise_floor=float(spec["noise_floor_hartree"]),
            window_size=int(spec["rolling_window_points"]),
        )
        eligible = [
            row
            for row in windows
            if float(row["order_deviation"])
            <= float(spec["formal_order_tolerance"])
            and float(row["r2"]) >= float(spec["minimum_r_squared"])
        ]
        if eligible:
            selected = min(eligible, key=lambda row: int(row["start_index"]))
            break
    if selected is None:
        raise execution.ExecutionError(
            f"{condition}: no qualifying short-time proxy window"
        )
    alpha = abs(float(selected["fixed_order_alpha"]))
    if not math.isfinite(alpha) or alpha <= 0.0:
        raise execution.ExecutionError(f"{condition}: invalid proxy alpha")
    epsilon = float(protocol["scope"]["target_error_hartree"])
    t_ana = float((epsilon / (5.0 * alpha)) ** 0.25)
    return t_ana, {
        "selected_window": selected,
        "evaluated_windows": windows,
        "alpha_proxy": alpha,
        "proxy_analytic_time_hartree_inverse": t_ana,
        "selection_rule": spec["selection_rule"],
    }, points


def run_condition_selector(
    *,
    output_dir: Path,
    condition: str,
    system: Mapping[str, Any],
    protocol: Mapping[str, Any],
    protocol_sha256: str,
    sequence: Sequence[float],
    formula_sha256: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    counters = {"computed": 0, "reused": 0}
    rotations = _rotation_count(system, sequence)
    selector_payload = {
        "schema": execution.PHASE_A_INPUT_SCHEMA,
        "condition": condition,
        "protocol_sha256": protocol_sha256,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "hamiltonian": system["hamiltonian"],
        "component_spectra": system["component_spectra"],
        "term_counts": system["term_counts"],
        "cisd_state": system["cisd_state"],
        "current_m3": {
            "id": execution.FORMULA_ID,
            "s2_sequence": list(sequence),
            "formula_sha256": formula_sha256,
        },
        "target_error_hartree": protocol["scope"]["target_error_hartree"],
        "measurement_costs": {
            "rotation_count_per_pf_step": rotations,
            "beta": protocol["cost_model"]["beta"],
            "gamma": protocol["scope"]["budget_multiplier_gamma"],
        },
        "runtime_cache_key": {
            "protocol_sha256": protocol_sha256,
            "condition": condition,
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "formula_sha256": formula_sha256,
            "backend": "cpu",
            "dtype": "complex128",
        },
    }
    guard.validate_phase_a_selector_payload(selector_payload)
    t_ana, scale_fit, short_points = proxy_analytic_scale(
        output_dir=output_dir,
        condition=condition,
        system=system,
        sequence=sequence,
        protocol=protocol,
        protocol_sha256=protocol_sha256,
        formula_sha256=formula_sha256,
        counters=counters,
    )
    roles: dict[str, list[str]] = {}
    point_lookup: dict[str, dict[str, Any]] = {}

    def acquire(relative: float, role: str) -> dict[str, Any]:
        point = cached_proxy_point(
            output_dir=output_dir,
            condition=condition,
            system=system,
            sequence=sequence,
            time_value=float(relative) * t_ana,
            protocol_sha256=protocol_sha256,
            formula_sha256=formula_sha256,
            counters=counters,
        )
        key = float(point["time_hartree_inverse"]).hex()
        point_lookup[key] = point
        roles.setdefault(key, []).append(role)
        return point

    original = protocol["phase_a"]["original_current_m3_rule"]
    base_relative = sorted(
        set(
            float(value)
            for value in (
                list(original["model_training_relative_to_t_ana"])
                + [
                    original["cancellation_primary_relative_to_t_ana"],
                    original["cancellation_robustness_relative_to_t_ana"],
                    original["sentinel_relative_to_t_ana"],
                ]
            )
        )
    )
    observations: dict[float, dict[str, Any]] = {}
    for relative in base_relative:
        observations[relative] = acquire(relative, f"base_{relative:g}")
    strategies, diagnostics = execution.select_phase_a_strategies(
        t_ana=t_ana,
        observations_by_relative_time=observations,
        pooled_extra_points=short_points,
        rotations=rotations,
        protocol=protocol,
    )
    if diagnostics["fallback_triggered"]:
        for relative in protocol["phase_a"]["extension"][
            "candidate_sequence_relative_to_t_ana"
        ]:
            relative = float(relative)
            observations[relative] = acquire(relative, f"extension_{relative:g}")
            strategies, diagnostics = execution.select_phase_a_strategies(
                t_ana=t_ana,
                observations_by_relative_time=observations,
                pooled_extra_points=short_points,
                rotations=rotations,
                protocol=protocol,
            )
            if diagnostics.get("extension_stop_reason") is not None:
                break
    proxy_rows = [
        {
            "condition": condition,
            "point_role": "short_time_scale",
            "relative_to_t_ana": float(
                point["time_hartree_inverse"] / t_ana
            ),
            **point,
        }
        for point in short_points
    ]
    for key, point in sorted(
        point_lookup.items(), key=lambda item: item[1]["time_hartree_inverse"]
    ):
        proxy_rows.append(
            {
                "condition": condition,
                "point_role": "+".join(roles[key]),
                "relative_to_t_ana": float(
                    point["time_hartree_inverse"] / t_ana
                ),
                **point,
            }
        )
    proxy_count = len(
        {
            float(row["time_hartree_inverse"]).hex()
            for row in proxy_rows
        }
    )
    maximum = int(
        protocol["phase_a"]["maximum_information_counts_per_condition"][
            "total_proxy_points"
        ]
    )
    if proxy_count > maximum:
        raise execution.ExecutionError(
            f"{condition}: proxy coordinate count {proxy_count}/{maximum}"
        )
    base_time_hexes = {
        float(point["time_hartree_inverse"]).hex()
        for point in short_points
    }
    base_time_hexes.update(
        (float(relative) * t_ana).hex() for relative in base_relative
    )
    all_time_hexes = {
        float(row["time_hartree_inverse"]).hex() for row in proxy_rows
    }
    base_count = len(base_time_hexes)
    extension_count = len(all_time_hexes - base_time_hexes)
    shared_counts = {
        "state_generations": 1,
        "group_spectrum_builds": 1,
        "proxy_points": proxy_count,
        "hamiltonian_exponential_actions": proxy_count,
        "current_m3_pf_state_actions": proxy_count,
        "explicit_hamiltonian_vector_actions_for_state_diagnostics": 1,
    }
    information_counts = {
        "current_fallback": {
            **shared_counts,
            "proxy_points": base_count,
            "hamiltonian_exponential_actions": base_count,
            "current_m3_pf_state_actions": base_count,
            "extension_proxy_points": 0,
        },
        "equal_information_pooled_fit": {
            **shared_counts,
            "extension_proxy_points": extension_count,
        },
        "multiple_window_rule": {
            **shared_counts,
            "extension_proxy_points": extension_count,
        },
        "uncapped_counterfactual": {
            **shared_counts,
            "proxy_points": base_count,
            "hamiltonian_exponential_actions": base_count,
            "current_m3_pf_state_actions": base_count,
            "extension_proxy_points": 0,
        },
    }
    return {
        "condition": condition,
        "hamiltonian_sha256": system["hamiltonian_sha256"],
        "proxy_analytic_time_hartree_inverse": t_ana,
        "proxy_scale_fit": scale_fit,
        "rotation_count_per_pf_step": rotations,
        "strategies": strategies,
        "selector_diagnostics": diagnostics,
        "information_counts": information_counts,
        "proxy_cache_counts": counters,
        "proxy_unique_coordinate_count": proxy_count,
    }, proxy_rows


def _manifest(output_dir: Path, required: Sequence[str]) -> dict[str, Any]:
    files = []
    for name in required:
        path = output_dir / name
        if not path.is_file():
            raise execution.ExecutionError(f"missing Phase A artifact: {name}")
        files.append(
            {
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": execution.sha256_file(path),
            }
        )
    payload = {
        "schema": "second_study_safe_time_domain_phase_a_manifest_v1",
        "created_at": execution.now(),
        "files": files,
        "excluded_from_commit": ["*.pkl", "*.npy", ".runtime/"],
    }
    _write_json(output_dir / "manifest.json", payload)
    return payload


def run(
    *,
    project_root: Path,
    protocol_path: Path,
    preflight_root: Path,
    processes: int,
    output_dir: Path,
) -> dict[str, Any]:
    if int(processes) != 1:
        raise execution.ExecutionError("Phase A requires --processes 1")
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise execution.ExecutionError(f"refusing to overwrite output: {output_dir}")
    protocol, protocol_sha = execution.load_frozen_protocol(protocol_path)
    if int(protocol["scope"]["processes"]) != 1:
        raise execution.ExecutionError("protocol process count changed")
    environment = validate_process_environment(project_root)
    preflight = validate_preflight(project_root, preflight_root.resolve())
    output_dir.mkdir(parents=True)
    started = time.perf_counter()
    shutil.copy2(protocol_path, output_dir / "protocol.json")
    source_audit = project_root / protocol["source_identity"]["audit_path"]
    shutil.copy2(source_audit, output_dir / "source_leakage_audit.json")
    sequence = execution.formula_sequence(protocol)
    formula_hash = execution.formula_sha256(protocol)
    specs = execution.condition_specs(protocol)
    condition_predictions = []
    proxy_rows: list[dict[str, Any]] = []
    sanitized_entries = []
    system_root = output_dir / ".runtime/system_cache"
    for condition in execution.condition_names(protocol):
        cache_path = system_root / f"{condition}.pkl"
        metadata_path = system_root / f"{condition}.metadata.json"
        system, metadata = prepare_condition(
            specs[condition],
            protocol_sha,
            output_dir / ".runtime/work" / condition,
            processes,
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as stream:
            pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
        _write_json(metadata_path, metadata)
        cache_hash = execution.sha256_file(cache_path)
        sanitized_entries.append(
            {
                "condition": condition,
                "runtime_system_cache": str(
                    cache_path.relative_to(output_dir)
                ),
                "runtime_system_cache_sha256": cache_hash,
                "metadata": str(metadata_path.relative_to(output_dir)),
                "metadata_sha256": execution.sha256_file(metadata_path),
                "hamiltonian_sha256": system["hamiltonian_sha256"],
                "selector_allowlist_validated": True,
                "truth_path_exposed": False,
                "past_label_exposed": False,
            }
        )
        prediction, rows = run_condition_selector(
            output_dir=output_dir,
            condition=condition,
            system=system,
            protocol=protocol,
            protocol_sha256=protocol_sha,
            sequence=sequence,
            formula_sha256=formula_hash,
        )
        condition_predictions.append(prediction)
        proxy_rows.extend(rows)
    sanitized_manifest = {
        "schema": "second_study_safe_time_domain_sanitized_inputs_v1",
        "created_at": execution.now(),
        "protocol_sha256": protocol_sha,
        "entries": sanitized_entries,
        "selector_allowlist_only": True,
        "truth_paths_exposed": False,
        "existing_direct_coordinates_exposed": False,
    }
    _write_json(output_dir / "sanitized_input_manifest.json", sanitized_manifest)
    _write_csv(output_dir / "proxy_points.csv", proxy_rows)
    predictions = {
        "schema": execution.PHASE_A_SCHEMA,
        "created_at": execution.now(),
        "protocol_sha256": protocol_sha,
        "implementation_commit": execution.git_output(
            project_root, "rev-parse", "HEAD"
        ),
        "preflight_result_commit": PREFLIGHT_RESULT_COMMIT,
        "oracle_access": {key: 0 for key in guard.ORACLE_ACCESS_COUNTERS},
        "new_direct_truth_coordinate_count": 0,
        "exact_diagonalization_count": 0,
        "conditions": condition_predictions,
    }
    guard.validate_phase_a_predictions(predictions)
    _write_json(output_dir / guard.PREDICTION_FILE, predictions)
    marker = guard.freeze_phase_a(
        output_dir,
        predictions["implementation_commit"],
    )
    aggregate_counts = {
        key: sum(
            int(
                row["information_counts"]["multiple_window_rule"][key]
            )
            for row in condition_predictions
        )
        for key in (
            "state_generations",
            "group_spectrum_builds",
            "proxy_points",
            "hamiltonian_exponential_actions",
            "current_m3_pf_state_actions",
            "explicit_hamiltonian_vector_actions_for_state_diagnostics",
        )
    }
    maximum_counts = protocol["phase_a"][
        "maximum_information_counts_all_four_conditions"
    ]
    count_mapping = {
        "new_state_generations": "state_generations",
        "group_spectrum_builds": "group_spectrum_builds",
        "proxy_points": "proxy_points",
        "hamiltonian_exponential_actions": "hamiltonian_exponential_actions",
        "current_m3_pf_state_actions": "current_m3_pf_state_actions",
        "explicit_hamiltonian_vector_actions_for_state_diagnostics": (
            "explicit_hamiltonian_vector_actions_for_state_diagnostics"
        ),
    }
    for protocol_key, aggregate_key in count_mapping.items():
        limit = int(maximum_counts[protocol_key])
        if aggregate_counts[aggregate_key] > limit:
            raise execution.ExecutionError(
                f"Phase A count exceeds protocol: {aggregate_key} "
                f"{aggregate_counts[aggregate_key]}/{limit}"
            )
    audit = {
        "schema": "second_study_safe_time_domain_phase_a_audit_v1",
        "status": "phase_a_frozen_phase_b_not_authorized",
        "created_at": execution.now(),
        "protocol_sha256": protocol_sha,
        "formula_sha256": formula_hash,
        "implementation_commit": predictions["implementation_commit"],
        "preflight": preflight,
        "environment": environment,
        "oracle_access": predictions["oracle_access"],
        "condition_count": len(condition_predictions),
        "strategy_count": len(guard.STRATEGIES),
        "aggregate_information_counts": aggregate_counts,
        "prediction_sha256": marker["prediction_sha256"],
        "phase_b_coordinate_count": marker["phase_b_coordinate_count"],
        "phase_a_wall_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "phase_b_authorized": False,
    }
    _write_json(output_dir / "phase_a_audit.json", audit)
    required = list(protocol["phase_a"]["freeze"]["required_files"])
    _manifest(output_dir, required)
    return audit


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--preflight-root", type=Path, required=True)
    parser.add_argument("--processes", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    audit = run(
        project_root=arguments.project_root,
        protocol_path=arguments.protocol,
        preflight_root=arguments.preflight_root,
        processes=arguments.processes,
        output_dir=arguments.output,
    )
    print(json.dumps(audit, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
