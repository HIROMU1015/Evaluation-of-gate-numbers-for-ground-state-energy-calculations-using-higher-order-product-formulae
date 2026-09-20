"""Fixed, unused-molecule hold-out for finite-time PF cost models.

The protocol is loaded from ``unused_molecule_frozen_holdout_protocol.json``;
the molecular conditions, PF/model pairs, time grids, thresholds, and budget
multipliers are never inferred from numerical results.  Dense PF unitaries are
built in the fixed-population (and, when available, exact diagonal-Z2) sector.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import pickle
import resource
import time
from typing import Any, Iterable, Sequence

import numpy as np
from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import jordan_wigner
from pyscf import ao2mo, gto, mcscf, scf
from scipy.linalg import eigh

import run_full_electron_nh3_higher_term_diagnosis as diagnosis
from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
from trotterlib.component_sector_pf import (
    find_balanced_z2_symmetry,
    prepare_component_spectra,
    qubit_operator_sector_matrix,
)


PROTOCOL_PATH = Path(__file__).with_name("unused_molecule_frozen_holdout_protocol.json")
FORMULAE = ("yoshida4", "current_m3", "two_term_center", "m5_best", "yoshida6_m3")
FINE_GRID = tuple(value / 100.0 for value in range(90, 111))
TIME_RTOL = 2e-12
ISOLATED_DROP_FRACTION = 0.02


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    diagnosis._atomic_json(path, payload)


def _protocol() -> dict[str, Any]:
    return _load(PROTOCOL_PATH)


def _protocol_sha256() -> str:
    return hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()


def _condition_map() -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in _protocol()["conditions"]}


def _expected_dimension(spec: dict[str, Any]) -> int:
    from math import comb

    orbitals = int(spec["active_spatial_orbitals"])
    electrons = int(spec["active_electrons"])
    n_alpha = electrons // 2
    n_beta = electrons - n_alpha
    return int(comb(orbitals, n_alpha) * comb(orbitals, n_beta))


def _fmt(value: Any, spec: str = ".5g") -> str:
    return "n/a" if value is None else format(float(value), spec)


def command_manifest(args: argparse.Namespace) -> int:
    protocol = _protocol()
    expected_pairs = {(item["pf"], tuple(item["powers"])) for item in protocol["primary_pf_model_pairs"]}
    declared_pairs = {("yoshida4", (4, 6)), ("current_m3", (4, 6)), ("two_term_center", (4, 6)), ("m5_best", (4, 6)), ("yoshida6_m3", (6, 8, 10))}
    if expected_pairs != declared_pairs:
        raise RuntimeError("runner PF/model pairs conflict with frozen protocol")
    payload = {
        "status": "preflight_complete", "created_at": _now(),
        "protocol_id": protocol["protocol_id"], "protocol_sha256": _protocol_sha256(),
        "base_result_commit": protocol["base_result_commit"],
        "git": diagnosis._git_state(), "environment": diagnosis._versions(),
        "conditions": list(_condition_map()), "formulae": list(FORMULAE),
        "independence_search": {
            "conclusion": "no pre-existing HF/N2/CO PF-error or QPE-cost numerical result found",
            "search_log": str(args.independence_search_log.resolve()),
            "matches": args.independence_search_log.read_text(encoding="utf-8").splitlines(),
            "note": "matches are plan/protocol mentions only; no numerical raw result was identified",
        },
        "forbidden_adaptation": protocol["scope"]["forbidden_adaptation"],
    }
    _write(args.output.resolve(), payload)
    return 0


def command_validate_prepared(args: argparse.Namespace) -> int:
    rows = []
    for name, spec in _condition_map().items():
        path = args.metadata_dir.resolve() / f"{name}.metadata.json"
        payload = _load(path)
        metadata = payload.get("system", {})
        checks = {
            "status_complete": payload.get("status") == "complete",
            "scf_converged": metadata.get("scf_converged") is True,
            "active_electrons": metadata.get("active_electron_count") == spec["active_electrons"],
            "active_orbitals": metadata.get("active_spatial_orbitals") == spec["active_spatial_orbitals"],
            "frozen_core": metadata.get("frozen_core_spatial_orbitals") == spec["frozen_core_spatial_orbitals"],
            "population_dimension": metadata.get("population_sector_dimension") == _expected_dimension(spec),
            "ground_residual": metadata.get("ground_residual_2_norm", math.inf) <= 1e-8,
            "restricted_residual": metadata.get("restricted_ground_residual_2_norm", math.inf) <= 1e-8,
        }
        rows.append({"condition": name, "metadata": metadata, "checks": checks, "passed": all(checks.values())})
    result = {"status": "complete" if all(row["passed"] for row in rows) else "failed", "created_at": _now(), "protocol_sha256": _protocol_sha256(), "conditions": rows}
    _write(args.output.resolve(), result)
    if result["status"] != "complete":
        raise RuntimeError("prepared Hamiltonian preflight failed; refusing long calculation")
    return 0


def _same_time(left: float, right: float) -> bool:
    return bool(math.isclose(float(left), float(right), rel_tol=TIME_RTOL, abs_tol=1e-14))


def _formula_models(formula: str, training: Sequence[dict[str, Any]], order: int, t_ana: float) -> dict[str, dict[str, Any]]:
    if formula == "yoshida6_m3":
        return {
            "three_term_5point": diagnosis._fit_model(
                training, order, t_ana, [6, 8, 10], "three_term_5point"
            )
        }
    result = {
        "two_term_5point": diagnosis._fit_model(
            training, order, t_ana, [4, 6], "two_term_5point"
        ),
        "two_term_3point": diagnosis._fit_model(
            training[:3], order, t_ana, [4, 6], "two_term_3point"
        ),
    }
    if formula == "yoshida4":
        result["three_term_5point"] = diagnosis._fit_model(
            training, order, t_ana, [4, 6, 8], "three_term_5point"
        )
    return result


def _primary_model_name(formula: str) -> str:
    return "three_term_5point" if formula == "yoshida6_m3" else "two_term_5point"


def _hermitize(operator: QubitOperator) -> tuple[QubitOperator, dict[str, float]]:
    result = QubitOperator()
    removed: list[float] = []
    for term, raw in operator.terms.items():
        coefficient = complex(raw)
        removed.append(float(coefficient.imag))
        if abs(coefficient.imag) > 1e-9:
            raise RuntimeError(f"unexpected imaginary Pauli coefficient {coefficient}")
        result += QubitOperator(term, float(coefficient.real))
    return result, {
        "maximum_removed_imaginary_pauli_coefficient": max(
            (abs(value) for value in removed), default=0.0
        )
    }


def prepare_condition(name: str, work_dir: Path, processes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = _condition_map()[name]
    started = time.perf_counter()
    work_dir.mkdir(parents=True, exist_ok=True)
    molecule = gto.Mole()
    molecule.atom = [(atom, coordinates) for atom, coordinates in spec["geometry_angstrom"]]
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
    available = int(mean_field.mo_coeff.shape[1])
    if available != ncore + ncas:
        raise RuntimeError(
            f"{name}: expected {ncore+ncas} spatial orbitals but PySCF returned {available}"
        )
    if nelecas != int(spec["active_electrons"]):
        raise RuntimeError(
            f"{name}: expected {spec['active_electrons']} active electrons but obtained {nelecas}"
        )
    active_indices = list(range(ncore, ncore + ncas))
    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = ncore
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    active_coefficients = np.asarray(mean_field.mo_coeff[:, active_indices])
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
        _hermitize(jordan_wigner(sum(group, FermionOperator())))[0]
        for group in grouped
    ]
    hamiltonian, hermitization = _hermitize(sum(groups, QubitOperator()))
    constant = float(complex(hamiltonian.terms.get((), 0.0)).real)

    n_alpha = nelecas // 2
    n_beta = nelecas - n_alpha
    basis = diagnosis._population_basis(ncas, n_alpha, n_beta)
    expected_dimension = _expected_dimension(spec)
    if int(basis.size) != expected_dimension:
        raise RuntimeError(
            f"{name}: expected population dimension {expected_dimension}, got {basis.size}"
        )
    sector_sparse = qubit_operator_sector_matrix(
        groups[0], 2 * ncas, basis, remove_constant=True
    )
    for group in groups[1:]:
        sector_sparse = sector_sparse + qubit_operator_sector_matrix(
            group, 2 * ncas, basis, remove_constant=True
        )
    sector_hamiltonian = sector_sparse.toarray()
    values, vectors = eigh(
        sector_hamiltonian, subset_by_index=[0, 0], check_finite=False, driver="evr"
    )
    energy = float(values[0])
    state = np.asarray(vectors[:, 0], dtype=np.complex128)
    state /= np.linalg.norm(state)
    ground_residual = float(np.linalg.norm(sector_hamiltonian @ state - energy * state))
    del sector_hamiltonian

    try:
        mask, target, selected, symmetry = find_balanced_z2_symmetry(
            groups, 2 * ncas, basis, state, support_cutoff=1e-9
        )
    except RuntimeError as exc:
        if "No nonconstant exact diagonal-Z symmetry" not in str(exc):
            raise
        mask, target = 0, 0
        selected = np.arange(basis.size, dtype=np.int64)
        symmetry = {
            "kind": "no_nonconstant_exact_diagonal_Z2",
            "population_sector_dimension": int(basis.size),
            "restricted_dimension": int(basis.size),
        }
    restricted_basis = basis[selected]
    restricted_state = state[selected].copy()
    restricted_state /= np.linalg.norm(restricted_state)
    spectra, compact = prepare_component_spectra(
        groups, 2 * ncas, restricted_basis,
        validation_state=restricted_state, processes=int(processes),
    )
    summed_action = np.asarray(compact.pop("summed_group_action"))
    restricted_residual = float(np.linalg.norm(summed_action - energy * restricted_state))
    if restricted_residual > 1e-8:
        raise RuntimeError(f"{name}: restricted ground residual is {restricted_residual}")
    term_counts = [sum(1 for term in group.terms if term) for group in groups]
    system = {
        "geometry": name,
        "state": restricted_state,
        "energy": energy,
        "component_spectra": spectra,
        "term_counts": term_counts,
    }
    metadata = {
        "condition": name,
        "geometry_angstrom": spec["geometry_angstrom"],
        "basis": spec["basis"],
        "charge": int(spec["charge"]),
        "multiplicity": int(spec["multiplicity"]),
        "total_spatial_orbitals": available,
        "total_electron_count": int(molecule.nelectron),
        "active_electron_count": nelecas,
        "frozen_core_spatial_orbitals": ncore,
        "active_spatial_orbitals": ncas,
        "active_spatial_orbital_indices": active_indices,
        "n_alpha": n_alpha,
        "n_beta": n_beta,
        "num_qubits": 2 * ncas,
        "population_sector_dimension": int(basis.size),
        "expected_population_sector_dimension": expected_dimension,
        "restricted_dimension": int(restricted_basis.size),
        "group_count": len(groups),
        "nonidentity_pauli_term_count": sum(term_counts),
        "ground_energy_without_constant_hartree": energy,
        "removed_constant_hartree": constant,
        "ground_residual_2_norm": ground_residual,
        "restricted_ground_residual_2_norm": restricted_residual,
        "z2_mask": int(mask),
        "z2_target": int(target),
        "z2_symmetry": symmetry,
        "component_representation": compact,
        "numerical_hermitization": hermitization,
        "scf_energy_hartree": float(mean_field.e_tot),
        "scf_converged": bool(mean_field.converged),
        "preparation_seconds": float(time.perf_counter() - started),
        "preflight_passed": True,
    }
    return system, metadata


def command_prepare(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    payload = {
        "status": "preparing", "started_at": _now(), "condition": args.condition,
        "protocol_sha256": _protocol_sha256(), "git": diagnosis._git_state(),
        "environment": diagnosis._versions(),
    }
    _write(output.with_suffix(".metadata.json"), payload)
    try:
        system, metadata = prepare_condition(
            args.condition, output.parent / f"{output.stem}_work", args.component_processes
        )
        with output.open("wb") as stream:
            pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
        payload.update({
            "status": "complete", "completed_at": _now(), "system": metadata,
            "cache_path": str(output), "cache_bytes": output.stat().st_size,
        })
        _write(output.with_suffix(".metadata.json"), payload)
        print(json.dumps(diagnosis._jsonable(metadata), indent=2), flush=True)
        return 0
    except Exception as exc:
        payload.update({
            "status": "failed", "completed_at": _now(),
            "error_type": type(exc).__name__, "error": str(exc),
        })
        _write(output.with_suffix(".metadata.json"), payload)
        raise


def _annotate_point(point: dict[str, Any]) -> None:
    point["phase_unwrap_integer"] = 0
    point["phase_unwrap_status"] = "principal relative phase; no wrap required in local branch"


def _evaluate_model(
    system: dict[str, Any], sequence: Sequence[float], rotations: int,
    model: dict[str, Any], t_ana: float, backend: str, gpu_id: int,
    training_times: Sequence[float],
) -> dict[str, Any]:
    optimum = diagnosis._model_optimum(model, t_ana, rotations)
    points: list[dict[str, Any]] = []
    previous = None
    for relative in _protocol()["stage1_validation_relative_to_t_star"]:
        point, vector = diagnosis._direct_point(
            system, sequence, float(relative) * float(optimum["time"]), rotations,
            backend, gpu_id, previous,
        )
        _annotate_point(point)
        prediction = diagnosis._prediction(model, point["time"])
        point.update({
            "relative_to_t_star": float(relative),
            "relative_to_t_ana": float(point["time"] / t_ana),
            "model_signed_shift_hartree": prediction,
            "model_cost": diagnosis._cost(point["time"], abs(prediction), rotations),
            "signed_residual_hartree": float(point["signed_direct_shift_hartree"] - prediction),
            "residual_over_epsilon": float(
                abs(point["signed_direct_shift_hartree"] - prediction) / diagnosis.EPSILON_E
            ),
            "coincides_with_training_time": any(
                _same_time(point["time"], value) for value in training_times
            ),
        })
        points.append(point)
        previous = vector
    return _model_result(model, optimum, points, rotations)


def _budget_diagnostics(
    model: dict[str, Any], optimum: dict[str, Any], at_star: dict[str, Any], rotations: int,
) -> list[dict[str, Any]]:
    epsilon_qpe_model = diagnosis.EPSILON_E - abs(
        diagnosis._prediction(model, float(optimum["time"]))
    )
    direct_error = abs(float(at_star["signed_direct_shift_hartree"]))
    results = []
    for multiplier in _protocol()["frozen_budget_cost_multipliers"]:
        epsilon_qpe = epsilon_qpe_model / float(multiplier)
        total_error = direct_error + epsilon_qpe
        available = diagnosis.EPSILON_E - direct_error
        required_multiplier = (
            epsilon_qpe_model / available if available > 0.0 else None
        )
        results.append({
            "cost_multiplier": float(multiplier),
            "epsilon_qpe_hartree": float(epsilon_qpe),
            "direct_pf_error_hartree": direct_error,
            "total_error_hartree": float(total_error),
            "target_met": bool(total_error <= diagnosis.EPSILON_E),
            "target_excess_hartree": max(0.0, float(total_error - diagnosis.EPSILON_E)),
            "required_cost_multiplier_vs_model": required_multiplier,
            "additional_cost_fraction_required": (
                None if required_multiplier is None
                else max(0.0, float(required_multiplier) - float(multiplier))
            ),
            "unnecessary_cost_fraction": (
                None if required_multiplier is None
                else max(0.0, float(multiplier) - float(required_multiplier))
            ),
            "model_error_direction": (
                "underestimates_absolute_pf_error" if direct_error > abs(diagnosis._prediction(model, float(optimum["time"])))
                else "overestimates_absolute_pf_error"
            ),
        })
    return results


def _model_result(
    model: dict[str, Any], optimum: dict[str, Any], points: Sequence[dict[str, Any]], rotations: int,
) -> dict[str, Any]:
    at_star = next(point for point in points if _same_time(point["relative_to_t_star"], 1.0))
    finite = [point for point in points if point.get("direct_cost") is not None]
    minimum = min(finite, key=lambda point: float(point["direct_cost"])) if finite else None
    unseen = [point for point in points if not point.get("coincides_with_training_time", False)]
    direct_at_star = at_star.get("direct_cost")
    metrics = {
        "eta_star": (
            abs(float(optimum["cost"]) - float(direct_at_star)) / float(direct_at_star)
            if direct_at_star is not None else None
        ),
        "eta_min": (
            float(direct_at_star) / float(minimum["direct_cost"]) - 1.0
            if direct_at_star is not None and minimum is not None else None
        ),
        "eta_t": (
            abs(float(optimum["time"]) / float(minimum["time"]) - 1.0)
            if minimum is not None else None
        ),
        "maximum_unseen_residual_over_epsilon": (
            max(float(point["residual_over_epsilon"]) for point in unseen)
            if unseen else None
        ),
        "minimum_ground_overlap_probability": min(
            float(point["ground_overlap_probability"]) for point in points
        ),
        "minimum_adjacent_vector_overlap_probability": min(
            (float(point["adjacent_selected_vector_overlap_probability"])
             for point in points if point.get("adjacent_selected_vector_overlap_probability") is not None),
            default=None,
        ),
        "maximum_eigenpair_residual_2_norm": max(
            float(point["eigenpair_residual_2_norm"]) for point in points
        ),
    }
    thresholds = _protocol()["pass_thresholds"]
    checks = {
        key: metrics[key] is not None and float(metrics[key]) <= float(threshold)
        for key, threshold in thresholds.items()
    }
    return {
        "model": model, "model_optimum": optimum,
        "direct_validation_points": list(points), "direct_grid_minimum": minimum,
        "metrics": metrics, "checks": checks, "passed": all(checks.values()),
        "frozen_budget": _budget_diagnostics(model, optimum, at_star, rotations),
    }


def command_formula(args: argparse.Namespace) -> int:
    system = diagnosis._load_system(args.system_cache.resolve())
    formula = diagnosis._formulae()[args.formula]
    sequence = diagnosis._formula_s2_sequence(args.formula)
    rotations = diagnosis._rotation_count(system, sequence)
    output = args.output.resolve()
    payload: dict[str, Any] = {
        "status": "short_time_fit", "started_at": _now(),
        "condition": args.condition, "formula_name": args.formula,
        "formula": {**formula, "s2_sequence": sequence,
                    "s2_stage_count": len(sequence), "rotations": rotations},
        "backend": args.backend, "physical_gpu_id": args.gpu_id,
        "protocol_sha256": _protocol_sha256(), "protocol_id": _protocol()["protocol_id"],
        "git": diagnosis._git_state(), "environment": diagnosis._versions(),
    }
    _write(output, payload)
    try:
        fit = diagnosis._short_time_fit(system, sequence, int(formula["formal_order"]))
        payload["short_time_fit"] = fit
        if not fit["qualified"]:
            payload.update({
                "status": "short_time_fit_failed", "completed_at": _now(),
                "failure_reason": "no qualifying window; frozen protocol not changed",
            })
            _write(output, payload)
            return 0
        alpha = float(fit["selected_window"]["fixed_order_alpha"])
        t_ana = diagnosis._analytic_time(alpha, int(formula["formal_order"]))
        training: list[dict[str, Any]] = []
        previous = None
        for relative in _protocol()["primary_training_relative_to_t_ana"]:
            point, vector = diagnosis._direct_point(
                system, sequence, float(relative) * t_ana, rotations,
                args.backend, args.gpu_id, previous,
            )
            _annotate_point(point)
            point.update({"relative_to_t_ana": float(relative), "used_for_direct_model_fit": True})
            training.append(point)
            previous = vector
            payload.update({
                "status": "training_direct_points", "alpha": alpha,
                "analytic_time": t_ana, "training_direct_points": training,
            })
            _write(output, payload)
        models = _formula_models(args.formula, training, int(formula["formal_order"]), t_ana)
        payload.update({"status": "model_validation", "models": {}})
        _write(output, payload)
        training_times = [float(point["time"]) for point in training]
        for name, model in models.items():
            payload["models"][name] = _evaluate_model(
                system, sequence, rotations, model, t_ana, args.backend,
                args.gpu_id, training_times,
            )
            _write(output, payload)
        payload.update({
            "status": "complete", "completed_at": _now(),
            "primary_model": _primary_model_name(args.formula),
        })
        _write(output, payload)
        return 0
    except Exception as exc:
        payload.update({
            "status": "failed", "completed_at": _now(),
            "error_type": type(exc).__name__, "error": str(exc),
        })
        _write(output, payload)
        raise


def command_pilot(args: argparse.Namespace) -> int:
    system = diagnosis._load_system(args.system_cache.resolve())
    sequence = diagnosis._formula_s2_sequence("yoshida4")
    formula = diagnosis._formulae()["yoshida4"]
    rotations = diagnosis._rotation_count(system, sequence)
    started = time.perf_counter()
    fit = diagnosis._short_time_fit(system, sequence, int(formula["formal_order"]))
    if not fit["qualified"]:
        raise RuntimeError("CO equilibrium Yoshida4 pilot short-time fit failed")
    alpha = float(fit["selected_window"]["fixed_order_alpha"])
    t_ana = diagnosis._analytic_time(alpha, 4)
    point, _ = diagnosis._direct_point(
        system, sequence, t_ana, rotations, args.backend, args.gpu_id, None
    )
    _annotate_point(point)
    payload = {
        "status": "complete", "completed_at": _now(), "condition": args.condition,
        "formula": "yoshida4", "protocol_sha256": _protocol_sha256(),
        "short_time_fit": fit, "alpha": alpha, "analytic_time": t_ana,
        "direct_point": point, "elapsed_seconds": time.perf_counter() - started,
        "projected_stage1_direct_points": 570,
        "projection_note": "upper-bound count before absolute-time deduplication; stage2 is data-dependent",
    }
    _write(args.output.resolve(), payload)
    return 0


def _isolated_drop(result: dict[str, Any]) -> bool:
    costs = [point.get("direct_cost") for point in result["direct_validation_points"]]
    return any(
        costs[index] is not None and costs[index - 1] is not None and costs[index + 1] is not None
        and float(costs[index]) <= (1.0 - ISOLATED_DROP_FRACTION) * min(
            float(costs[index - 1]), float(costs[index + 1])
        )
        for index in range(1, len(costs) - 1)
    )


def _candidate_reasons(result: dict[str, Any]) -> list[str]:
    thresholds = _protocol()["pass_thresholds"]
    metrics = result["metrics"]
    reasons: list[str] = []
    if result["passed"]:
        reasons.append("all_four_coarse_checks_passed")
    common = (
        metrics["eta_star"] is not None
        and metrics["eta_star"] <= thresholds["eta_star"]
        and metrics["maximum_unseen_residual_over_epsilon"] is not None
        and metrics["maximum_unseen_residual_over_epsilon"]
        <= thresholds["maximum_unseen_residual_over_epsilon"]
    )
    if common and metrics["eta_min"] is not None and metrics["eta_t"] is not None:
        if metrics["eta_min"] <= thresholds["eta_min"] and (
            thresholds["eta_t"] < metrics["eta_t"] <= 2 * thresholds["eta_t"]
        ):
            reasons.append("eta_t_only_within_twice_threshold")
        if metrics["eta_t"] <= thresholds["eta_t"] and (
            thresholds["eta_min"] < metrics["eta_min"] <= 2 * thresholds["eta_min"]
        ):
            reasons.append("eta_min_only_within_twice_threshold")
    if _isolated_drop(result):
        reasons.append("isolated_coarse_grid_cost_drop")
    return reasons


def _coarse_points(record: dict[str, Any]) -> list[dict[str, Any]]:
    points = list(record.get("training_direct_points", ()))
    for result in record.get("models", {}).values():
        points.extend(result.get("direct_validation_points", ()))
    return points


def command_plan(args: argparse.Namespace) -> int:
    raw = args.raw_dir.resolve()
    tasks = []
    candidates = []
    for condition in _condition_map():
        for formula in FORMULAE:
            path = raw / f"{condition}__{formula}.json"
            record = _load(path)
            if record["status"] == "short_time_fit_failed":
                continue
            if record["status"] != "complete":
                raise RuntimeError(f"incomplete stage1 record: {path}")
            selected = []
            requests = []
            for model_name, result in record["models"].items():
                reasons = _candidate_reasons(result)
                candidates.append({
                    "condition": condition, "formula": formula, "model": model_name,
                    "selected": bool(reasons), "reasons": reasons,
                    "coarse_passed": bool(result["passed"]),
                })
                if not reasons:
                    continue
                optimum = float(result["model_optimum"]["time"])
                selected.append({"model": model_name, "reasons": reasons, "model_optimum_time": optimum})
                for relative in FINE_GRID:
                    requests.append({
                        "model": model_name, "relative_to_t_star": relative,
                        "requested_time": relative * optimum,
                    })
            if not selected:
                continue
            unique: list[dict[str, Any]] = []
            coarse = _coarse_points(record)
            for request in sorted(requests, key=lambda item: item["requested_time"]):
                entry = next((item for item in unique if _same_time(item["time"], request["requested_time"])), None)
                if entry is None:
                    matches = [point for point in coarse if _same_time(point["time"], request["requested_time"])]
                    entry = {
                        "time": float(request["requested_time"]), "requests": [],
                        "reused_point": dict(matches[0]) if matches else None,
                    }
                    unique.append(entry)
                entry["requests"].append(request)
            tasks.append({
                "task_id": f"{condition}__{formula}", "condition": condition,
                "formula": formula, "source_raw_json": str(path),
                "candidate_models": selected, "points": unique,
                "new_direct_times": sum(item["reused_point"] is None for item in unique),
            })
    payload = {
        "status": "planned", "created_at": _now(), "protocol_sha256": _protocol_sha256(),
        "fine_relative_grid": FINE_GRID, "model_candidates": candidates, "tasks": tasks,
        "totals": {
            "tasks": len(tasks),
            "selected_models": sum(len(task["candidate_models"]) for task in tasks),
            "new_direct_times": sum(task["new_direct_times"] for task in tasks),
        },
    }
    _write(args.output.resolve(), payload)
    print(json.dumps(payload["totals"], sort_keys=True), flush=True)
    return 0


def command_fine(args: argparse.Namespace) -> int:
    plan = _load(args.plan.resolve())
    task = next(item for item in plan["tasks"] if item["task_id"] == args.task_id)
    source = _load(Path(task["source_raw_json"]))
    system = diagnosis._load_system(args.system_cache.resolve())
    sequence = diagnosis._formula_s2_sequence(task["formula"])
    rotations = diagnosis._rotation_count(system, sequence)
    output = args.output.resolve()
    payload = _load(output) if output.exists() else {
        "status": "running", "started_at": _now(), "task": task,
        "protocol_sha256": _protocol_sha256(), "git": diagnosis._git_state(),
        "computed_points": [],
    }
    completed = {float(point["time"]): point for point in payload["computed_points"]}
    previous = None
    for item in sorted(task["points"], key=lambda point: point["time"]):
        if item["reused_point"] is not None:
            continue
        if any(_same_time(time_value, item["time"]) for time_value in completed):
            continue
        point, vector = diagnosis._direct_point(
            system, sequence, item["time"], rotations, args.backend, args.gpu_id, previous
        )
        _annotate_point(point)
        point["requests"] = item["requests"]
        payload["computed_points"].append(point)
        previous = vector
        _write(output, payload)
    payload.update({"status": "complete", "completed_at": _now()})
    _write(output, payload)
    return 0


def _fine_point(task: dict[str, Any], fine: dict[str, Any], model: str, relative: float) -> dict[str, Any]:
    for item in task["points"]:
        if any(req["model"] == model and _same_time(req["relative_to_t_star"], relative) for req in item["requests"]):
            if item["reused_point"] is not None:
                return dict(item["reused_point"])
            return dict(next(point for point in fine["computed_points"] if _same_time(point["time"], item["time"])))
    raise KeyError((task["task_id"], model, relative))


def _fine_result(task: dict[str, Any], fine: dict[str, Any], record: dict[str, Any], model_name: str) -> dict[str, Any]:
    coarse = record["models"][model_name]
    model = coarse["model"]
    rotations = int(record["formula"]["rotations"])
    training_times = [float(point["time"]) for point in record["training_direct_points"]]
    points = []
    for relative in FINE_GRID:
        point = _fine_point(task, fine, model_name, relative)
        prediction = diagnosis._prediction(model, point["time"])
        point.update({
            "relative_to_t_star": relative,
            "model_signed_shift_hartree": prediction,
            "model_cost": diagnosis._cost(point["time"], abs(prediction), rotations),
            "signed_residual_hartree": point["signed_direct_shift_hartree"] - prediction,
            "residual_over_epsilon": abs(point["signed_direct_shift_hartree"] - prediction) / diagnosis.EPSILON_E,
            "coincides_with_training_time": any(_same_time(point["time"], value) for value in training_times),
        })
        points.append(point)
    return _model_result(model, coarse["model_optimum"], points, rotations)


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    fields = sorted({key for row in materialized for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(materialized)


def command_aggregate(args: argparse.Namespace) -> int:
    raw_dir = args.raw_dir.resolve()
    fine_dir = args.fine_dir.resolve()
    plan = _load(args.plan.resolve())
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tasks = {task["task_id"]: task for task in plan["tasks"]}
    rows = []
    for condition in _condition_map():
        for formula in FORMULAE:
            record = _load(raw_dir / f"{condition}__{formula}.json")
            if record["status"] != "complete":
                rows.append({
                    "condition": condition, "formula": formula, "model": None,
                    "status": record["status"], "primary": True, "passed": False,
                })
                continue
            task = tasks.get(f"{condition}__{formula}")
            fine = _load(fine_dir / f"{condition}__{formula}.json") if task else None
            selected = {item["model"] for item in task["candidate_models"]} if task else set()
            for model_name, coarse in record["models"].items():
                result = _fine_result(task, fine, record, model_name) if model_name in selected else coarse
                budget = {item["cost_multiplier"]: item for item in result["frozen_budget"]}
                minimum = result.get("direct_grid_minimum")
                rows.append({
                    "condition": condition, "formula": formula, "model": model_name,
                    "status": "complete", "primary": model_name == record["primary_model"],
                    "fine_selected": model_name in selected, "passed": bool(result["passed"]),
                    **result["metrics"],
                    "direct_grid_minimum_cost": minimum.get("direct_cost") if minimum else None,
                    "direct_grid_minimum_time": minimum.get("time") if minimum else None,
                    "budget_base_target_met": budget[1.0]["target_met"],
                    "budget_1pct_target_met": budget[1.01]["target_met"],
                    "budget_base_excess_hartree": budget[1.0]["target_excess_hartree"],
                    "budget_1pct_excess_hartree": budget[1.01]["target_excess_hartree"],
                    "training_design_condition_number": coarse["model"]["training_design_condition_number"],
                })
    primary_conditions = set(_protocol()["scope"]["primary_conditions"])
    primary_rows = [row for row in rows if row.get("primary") and row["condition"] in primary_conditions]
    summary = []
    for formula in FORMULAE:
        selected = [row for row in primary_rows if row["formula"] == formula]
        summary.append({
            "formula": formula,
            "primary_conditions_passed": sum(bool(row["passed"]) for row in selected),
            "all_four_primary_conditions_passed": len(selected) == 4 and all(row["passed"] for row in selected),
            "base_budget_conditions_met": sum(bool(row["budget_base_target_met"]) for row in selected),
            "one_percent_budget_conditions_met": sum(bool(row["budget_1pct_target_met"]) for row in selected),
        })
    payload = {
        "status": "complete", "created_at": _now(), "protocol_sha256": _protocol_sha256(),
        "protocol_id": _protocol()["protocol_id"], "oracle_assisted_target_calibration": True,
        "rows": rows, "primary_summary": summary,
    }
    _write(output / "summary.json", payload)
    _write_csv(output / "metrics.csv", rows)
    lines = [
        "# Unused-molecule frozen hold-out", "", "Status: complete", "",
        "The five-point direct calibration is oracle-assisted; this does not validate a cheap practical estimator.", "",
        "## Pre-registered primary comparison", "",
        "| PF | primary conditions passed | all four | frozen budget | budget with 1% cost margin |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['formula']} | {row['primary_conditions_passed']}/4 | "
            f"{row['all_four_primary_conditions_passed']} | "
            f"{row['base_budget_conditions_met']}/4 | {row['one_percent_budget_conditions_met']}/4 |"
        )
    lines.extend([
        "", "## Per-condition metrics", "",
        "| condition | PF | model | primary | fine | pass | eta* | eta_min | eta_t | residual/eps | budget | +1% budget |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        if row.get("model") is None:
            lines.append(f"| {row['condition']} | {row['formula']} | n/a | True | False | False | n/a | n/a | n/a | n/a | n/a | n/a |")
        else:
            lines.append(
                f"| {row['condition']} | {row['formula']} | {row['model']} | {row['primary']} | "
                f"{row['fine_selected']} | {row['passed']} | {_fmt(row['eta_star'])} | "
                f"{_fmt(row['eta_min'])} | {_fmt(row['eta_t'])} | "
                f"{_fmt(row['maximum_unseen_residual_over_epsilon'])} | "
                f"{row['budget_base_target_met']} | {row['budget_1pct_target_met']} |"
            )
    lines.extend([
        "", "Local-grid minima are minima over calculated points, not exact continuous-time minima.",
        "The run stops after the six frozen conditions; no coefficient or molecule adaptation was performed.",
    ])
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--independence-search-log", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--condition", choices=tuple(_condition_map()), required=True)
    prepare.add_argument("--component-processes", type=int, default=8)
    prepare.add_argument("--output", type=Path, required=True)
    validate = commands.add_parser("validate-prepared")
    validate.add_argument("--metadata-dir", type=Path, required=True)
    validate.add_argument("--output", type=Path, required=True)
    pilot = commands.add_parser("pilot")
    pilot.add_argument("--condition", default="CO_active_eq_sto3g")
    pilot.add_argument("--system-cache", type=Path, required=True)
    pilot.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    pilot.add_argument("--gpu-id", type=int, required=True)
    pilot.add_argument("--output", type=Path, required=True)
    formula = commands.add_parser("formula")
    formula.add_argument("--condition", choices=tuple(_condition_map()), required=True)
    formula.add_argument("--system-cache", type=Path, required=True)
    formula.add_argument("--formula", choices=FORMULAE, required=True)
    formula.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    formula.add_argument("--gpu-id", type=int, required=True)
    formula.add_argument("--output", type=Path, required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--raw-dir", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    fine = commands.add_parser("fine")
    fine.add_argument("--plan", type=Path, required=True)
    fine.add_argument("--task-id", required=True)
    fine.add_argument("--system-cache", type=Path, required=True)
    fine.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    fine.add_argument("--gpu-id", type=int, required=True)
    fine.add_argument("--output", type=Path, required=True)
    aggregate = commands.add_parser("aggregate")
    aggregate.add_argument("--raw-dir", type=Path, required=True)
    aggregate.add_argument("--plan", type=Path, required=True)
    aggregate.add_argument("--fine-dir", type=Path, required=True)
    aggregate.add_argument("--output-dir", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    return {
        "manifest": command_manifest, "prepare": command_prepare,
        "validate-prepared": command_validate_prepared, "pilot": command_pilot,
        "formula": command_formula, "plan": command_plan,
        "fine": command_fine, "aggregate": command_aggregate,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
