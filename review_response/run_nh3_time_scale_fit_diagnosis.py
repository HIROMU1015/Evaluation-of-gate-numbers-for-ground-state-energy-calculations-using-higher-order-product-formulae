"""Diagnose absolute and dimensionless short-time scales for NH3 PF fits.

The two historical overlap/perturbative fit protocols are reproduced
separately.  Signed direct PF eigenphase shifts are computed on a small
halving ladder and are never conflated with those proxy fits.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import pickle
import resource
import time
from typing import Any, Sequence

import numpy as np
from scipy.linalg import eigh
from scipy.sparse import coo_matrix, csr_matrix

import run_full_electron_nh3_higher_term_diagnosis as full
import run_full_electron_nh3_followup_diagnostics as followup
import run_two_term_pf_m3_holdout_server2 as active
from trotterlib.fit_window import rolling_loglog_fits
from trotterlib.pf_decomposition import symmetric_s2_sequence


PROTOCOLS = {
    "shared_molecular": {
        "grid": tuple(float(x) for x in np.geomspace(0.06, 0.80, 15)),
        "noise_floor": 5e-13,
        "role": "declared shared molecular protocol",
    },
    "legacy_molecular_sensitivity": {
        "grid": tuple(float(x) for x in np.geomspace(0.02, 1.8, 34)),
        "noise_floor": 5e-12,
        "role": "sensitivity-only legacy molecular comparison protocol",
    },
}
FIT_WINDOW = 5
ORDER_TOLERANCE = 0.2
MINIMUM_R2 = 0.999
DIRECT_TIMES = (0.0075, 0.015, 0.03, 0.06)
FINE_RATIOS = tuple(float(round(0.90 + 0.01 * i, 2)) for i in range(16))
ADDED_FINE_RATIOS = (0.91, 1.03, 1.04)
FORMULAE = (
    "yoshida4",
    "paper_new4",
    "m5_best",
    "two_term_center",
    "joint_refine_r0_s0046",
    "yoshida6_m3",
)
CONDITIONS = (
    "active_equilibrium",
    "active_stretch150",
    "full_equilibrium",
    "full_stretch150",
)
SOURCE_RESULT = Path(
    "artifacts/full_electron_nh3_higher_term_diagnosis_20260919_230358_605384c"
)
SOURCE_FOLLOWUP = Path(
    "artifacts/full_electron_nh3_followup_diagnostics_20260920_014548_b26159c"
)


def now() -> str:
    return datetime.now().astimezone().isoformat()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    full._atomic_json(path, payload)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def condition_spec(name: str) -> dict[str, Any]:
    stretched = name.endswith("stretch150")
    geometry = full._geometry("stretch150" if stretched else "equilibrium")
    is_active = name.startswith("active_")
    return {
        "geometry": geometry,
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "frozen_core_spatial_orbitals": 1 if is_active else 0,
        "active_spatial_orbitals": 7 if is_active else 8,
        "selection_role": (
            "frozen-core CAS(8e,7o) NH3 time-scale diagnosis"
            if is_active else "full-electron NH3/STO-3G time-scale diagnosis"
        ),
    }


def spectrum_matrix(spectrum: Any) -> csr_matrix:
    rows = []
    columns = []
    values = []
    for batch in spectrum.batches:
        indices = batch.indices
        if batch.eigenvectors is None:
            blocks = batch.eigenvalues[:, :, None]
        else:
            blocks = (
                batch.eigenvectors * batch.eigenvalues[:, None, :]
            ) @ np.swapaxes(batch.eigenvectors.conj(), -1, -2)
        size = batch.component_size
        rows.append(np.repeat(indices, size, axis=1).reshape(-1))
        columns.append(np.tile(indices, (1, size)).reshape(-1))
        values.append(blocks.reshape(-1))
    return coo_matrix(
        (
            np.concatenate(values),
            (np.concatenate(rows), np.concatenate(columns)),
        ),
        shape=(spectrum.dimension, spectrum.dimension),
        dtype=np.complex128,
    ).tocsr()


def energy_scales(system: dict[str, Any]) -> dict[str, Any]:
    spectra = system["component_spectra"]
    group_ranges = []
    hamiltonian = csr_matrix(
        (spectra[0].dimension, spectra[0].dimension), dtype=np.complex128
    )
    for spectrum in spectra:
        eigenvalues = np.concatenate(
            [np.asarray(batch.eigenvalues).reshape(-1) for batch in spectrum.batches]
        )
        minimum = float(np.min(eigenvalues))
        maximum = float(np.max(eigenvalues))
        group_ranges.append(
            {
                "minimum": minimum,
                "maximum": maximum,
                "half_width": 0.5 * (maximum - minimum),
            }
        )
        hamiltonian = hamiltonian + spectrum_matrix(spectrum)
    dense = hamiltonian.toarray()
    dimension = dense.shape[0]
    minimum = float(
        eigh(
            dense,
            eigvals_only=True,
            subset_by_index=[0, 0],
            check_finite=False,
            driver="evr",
        )[0]
    )
    maximum = float(
        eigh(
            dense,
            eigvals_only=True,
            subset_by_index=[dimension - 1, dimension - 1],
            check_finite=False,
            driver="evr",
        )[0]
    )
    ground_difference = abs(minimum - float(system["energy"]))
    pauli_l1 = float(
        sum(
            abs(complex(coefficient))
            for group in system["groups"]
            for term, coefficient in group.terms.items()
            if term
        )
    )
    del dense, hamiltonian
    return {
        "lambda_h_sector_centered_half_width": 0.5 * (maximum - minimum),
        "lambda_h_sector_minimum": minimum,
        "lambda_h_sector_maximum": maximum,
        "lambda_h_ground_energy_difference": ground_difference,
        "lambda_group_half_width_sum": float(
            sum(item["half_width"] for item in group_ranges)
        ),
        "lambda_pauli_nonidentity_l1": pauli_l1,
        "group_ranges": group_ranges,
        "definitions": {
            "lambda_h_sector_centered_half_width": "(Emax-Emin)/2 in the exact restricted sector",
            "lambda_group_half_width_sum": "sum_g (lambda_g,max-lambda_g,min)/2",
            "lambda_pauli_nonidentity_l1": "sum of absolute nonidentity Pauli coefficients",
        },
    }


def command_prepare(args: argparse.Namespace) -> int:
    args.work_dir.mkdir(parents=True, exist_ok=True)
    spec = condition_spec(args.condition)
    started = time.perf_counter()
    system, metadata = active._prepare_system(
        args.condition, spec, args.work_dir, args.component_processes
    )
    system["condition"] = args.condition
    system["geometry"] = (
        "stretch150" if args.condition.endswith("stretch150") else "equilibrium"
    )
    system["term_counts"] = [
        sum(1 for term in group.terms if term) for group in system["groups"]
    ]
    scales = energy_scales(system)
    system["energy_scales"] = scales
    metadata["energy_scales"] = scales
    metadata["total_preparation_and_scale_seconds"] = float(
        time.perf_counter() - started
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as stream:
        pickle.dump(system, stream, protocol=pickle.HIGHEST_PROTOCOL)
    atomic_json(args.output.with_suffix(".metadata.json"), {
        "status": "complete",
        "created_at": now(),
        "condition": args.condition,
        "system": metadata,
        "cache_bytes": args.output.stat().st_size,
        "git": full._git_state(),
    })
    print(json.dumps(full._jsonable(metadata), indent=2), flush=True)
    return 0


def qualify(
    times: Sequence[float],
    errors: Sequence[float],
    formal_order: int,
    noise_floor: float,
) -> dict[str, Any]:
    windows = rolling_loglog_fits(
        np.asarray(times),
        np.asarray(errors),
        formal_order=int(formal_order),
        noise_floor=float(noise_floor),
        window_size=FIT_WINDOW,
    )
    eligible = [
        window for window in windows
        if float(window["order_deviation"]) <= ORDER_TOLERANCE
        and float(window["r2"]) >= MINIMUM_R2
    ]
    selected = min(
        eligible, key=lambda x: (int(x["start_index"]), int(x["stop_index_exclusive"])),
        default=None,
    )
    return {
        "qualified": selected is not None,
        "selected_window": selected,
        "evaluated_windows": windows,
        "formal_order": int(formal_order),
        "noise_floor": float(noise_floor),
        "window_size": FIT_WINDOW,
        "order_tolerance": ORDER_TOLERANCE,
        "minimum_r2": MINIMUM_R2,
    }


def failure_reasons(
    points: Sequence[dict[str, Any]],
    fit: dict[str, Any],
    formal_order: int,
    noise_floor: float,
) -> list[str]:
    if fit["qualified"]:
        return []
    errors = np.asarray([point["proxy_error_hartree"] for point in points])
    signed = np.asarray([point["signed_proxy_shift_hartree"] for point in points])
    reasons = []
    if np.any(errors <= noise_floor):
        reasons.append("small-time points enter the declared proxy noise floor")
    windows = fit["evaluated_windows"]
    if any(
        float(w["order_deviation"]) <= ORDER_TOLERANCE
        and float(w["r2"]) < MINIMUM_R2
        for w in windows
    ):
        reasons.append("formal-order condition is met but R2 is below threshold")
    if any(
        float(w["r2"]) >= MINIMUM_R2
        and float(w["order_deviation"]) > ORDER_TOLERANCE
        for w in windows
    ):
        reasons.append("R2 is high but fitted order is outside tolerance")
    if np.any(signed[1:] * signed[:-1] < 0.0):
        reasons.append("sign reversal or cancellation occurs inside the grid")
    if not reasons:
        reasons.append(
            "formal-order plateau is not reached before the current grid ends"
        )
    return reasons


def state_action(
    system: dict[str, Any],
    sequence: Sequence[float],
    time_value: float,
    backend: str,
    gpu_id: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    started = time.perf_counter()
    if backend == "gpu":
        return followup.apply_pf_gpu(system, sequence, time_value, gpu_id)
    evolved = full._apply_pf(system, sequence, time_value)
    return evolved, {
        "backend": "cpu_exact_sector_matrix_free_state_action",
        "elapsed_seconds": float(time.perf_counter() - started),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }


def benchmark_state_action(
    system: dict[str, Any],
    sequence: Sequence[float],
    gpu_id: int,
) -> tuple[str, dict[str, Any]]:
    time_value = 0.06
    started = time.perf_counter()
    cpu = full._apply_pf(system, sequence, time_value)
    cpu_seconds = time.perf_counter() - started
    gpu, gpu_profile = followup.apply_pf_gpu(system, sequence, time_value, gpu_id)
    difference = float(
        np.linalg.norm(cpu - gpu)
        / max(np.linalg.norm(cpu), np.finfo(float).tiny)
    )
    if difference > 1e-10:
        raise RuntimeError(f"CPU/GPU state action mismatch: {difference}")
    gpu_seconds = float(gpu_profile["elapsed_seconds"])
    selected = "gpu" if gpu_seconds < cpu_seconds else "cpu"
    return selected, {
        "time": time_value,
        "cpu_seconds": float(cpu_seconds),
        "gpu_seconds": gpu_seconds,
        "cpu_gpu_relative_2_norm_difference": difference,
        "selected_backend": selected,
        "gpu_profile": gpu_profile,
    }


def proxy_protocol(
    system: dict[str, Any],
    sequence: Sequence[float],
    formal_order: int,
    protocol: dict[str, Any],
    backend: str,
    gpu_id: int,
) -> dict[str, Any]:
    points = []
    for time_value in protocol["grid"]:
        evolved, profile = state_action(
            system, sequence, time_value, backend, gpu_id
        )
        overlap = complex(np.vdot(system["state"], evolved))
        rotated = np.exp(-1j * system["energy"] * time_value) * overlap
        signed = float(rotated.imag / time_value)
        points.append({
            "time": time_value,
            "signed_proxy_shift_hartree": signed,
            "proxy_error_hartree": abs(signed),
            "phase_rotated_overlap": rotated,
            "survival_probability": float(abs(rotated) ** 2),
            "evolved_state_norm": float(np.linalg.norm(evolved)),
            "profile": profile,
        })
    fit = qualify(
        [point["time"] for point in points],
        [point["proxy_error_hartree"] for point in points],
        formal_order,
        protocol["noise_floor"],
    )
    fit["failure_reasons"] = failure_reasons(
        points, fit, formal_order, protocol["noise_floor"]
    )
    fit["points"] = points
    fit["error_definition"] = (
        "signed Im(exp(-i E0 t)<psi0|U_PF(t)|psi0>)/t; "
        "absolute value used for log-log fit"
    )
    return fit


def direct_ladder(
    system: dict[str, Any],
    sequence: Sequence[float],
    formal_order: int,
    rotations: int,
    gpu_id: int,
) -> dict[str, Any]:
    points = []
    previous = None
    for time_value in DIRECT_TIMES:
        point, vector = full._direct_point(
            system, sequence, time_value, rotations, "gpu", gpu_id, previous
        )
        eigenvalue = complex(
            point["selected_eigenvalue"]["real"],
            point["selected_eigenvalue"]["imag"],
        ) if isinstance(point["selected_eigenvalue"], dict) else complex(
            point["selected_eigenvalue"]
        )
        corrected = np.exp(-1j * system["energy"] * time_value) * eigenvalue
        principal_phase = float(np.angle(corrected))
        floor = max(
            64.0 * np.finfo(np.float64).eps / time_value,
            float(point["eigenpair_residual_2_norm"]) / time_value,
            abs(1.0 - float(point["selected_eigenvalue_magnitude"])) / time_value,
        )
        point.update({
            "principal_corrected_phase": principal_phase,
            "unwrapped_corrected_phase": principal_phase,
            "phase_unwrap_branch_integer": 0,
            "phase_unwrap_status": "principal branch; |E0*t| and corrected phase are far below pi",
            "direct_numerical_floor_estimate_hartree": float(floor),
            "direct_signal_to_floor": float(
                abs(point["signed_direct_shift_hartree"])
                / max(floor, np.finfo(float).tiny)
            ),
            "roundoff_risk": (
                abs(point["signed_direct_shift_hartree"]) <= 10.0 * floor
            ),
        })
        points.append(point)
        previous = vector
    effective = []
    for left, right in zip(points[:-1], points[1:]):
        e1 = abs(float(left["signed_direct_shift_hartree"]))
        e2 = abs(float(right["signed_direct_shift_hartree"]))
        order = None
        if e1 > 0.0 and e2 > 0.0:
            order = float(
                math.log(e2 / e1)
                / math.log(float(right["time"]) / float(left["time"]))
            )
        effective.append({
            "left_time": left["time"],
            "right_time": right["time"],
            "geometric_mean_time": float(
                math.sqrt(float(left["time"]) * float(right["time"]))
            ),
            "effective_order": order,
            "sign_reversal": (
                float(left["signed_direct_shift_hartree"])
                * float(right["signed_direct_shift_hartree"]) < 0.0
            ),
            "roundoff_risk": bool(left["roundoff_risk"] or right["roundoff_risk"]),
        })
    valid_orders = [
        item["effective_order"] for item in effective
        if item["effective_order"] is not None and not item["roundoff_risk"]
    ]
    if any(item["sign_reversal"] for item in effective):
        diagnosis = "sign_reversal_or_cancellation_on_direct_ladder"
    elif any(point["roundoff_risk"] for point in points):
        diagnosis = "direct_small_time_values_reach_numerical_floor"
    elif (
        valid_orders
        and min(abs(x - float(formal_order)) for x in valid_orders)
        <= ORDER_TOLERANCE
    ):
        diagnosis = (
            f"direct_effective_order_reaches_formal_order_{formal_order}"
        )
    else:
        diagnosis = "formal_order_plateau_not_reached_on_direct_ladder"
    return {
        "times": list(DIRECT_TIMES),
        "points": points,
        "effective_orders": effective,
        "diagnosis": diagnosis,
        "noise_floor_policy": (
            "No proxy-fit floor is reused. A per-point conservative floor is "
            "estimated from float64 epsilon, eigenpair residual/t, and eigenvalue "
            "magnitude defect/t."
        ),
    }


def add_tau_ranges(
    fit: dict[str, Any], scales: dict[str, Any]
) -> dict[str, Any] | None:
    selected = fit["selected_window"]
    if selected is None:
        return None
    result = {}
    for name in (
        "lambda_h_sector_centered_half_width",
        "lambda_group_half_width_sum",
        "lambda_pauli_nonidentity_l1",
    ):
        value = float(scales[name])
        result[name] = {
            "lambda": value,
            "tau_start": value * float(selected["t_start"]),
            "tau_stop": value * float(selected["t_stop"]),
        }
    return result


def command_condition(args: argparse.Namespace) -> int:
    with args.system_cache.open("rb") as stream:
        system = pickle.load(stream)
    formulae = full._formulae()
    output = {
        "status": "running",
        "started_at": now(),
        "condition": args.condition,
        "physical_gpu_id": args.gpu_id,
        "system_cache": str(args.system_cache),
        "energy_scales": system["energy_scales"],
        "protocol_definitions": PROTOCOLS,
        "direct_times": list(DIRECT_TIMES),
        "formulae": {},
        "git": full._git_state(),
    }
    atomic_json(args.output, output)
    for name in FORMULAE:
        formula = formulae[name]
        sequence = symmetric_s2_sequence(formula["weights"])
        rotations = full._rotation_count(system, sequence)
        selected_backend, benchmark = benchmark_state_action(
            system, sequence, args.gpu_id
        )
        record = {
            "formula": formula,
            "s2_sequence": sequence,
            "rotations": rotations,
            "state_action_benchmark": benchmark,
            "proxy_protocols": {},
        }
        for protocol_name, protocol in PROTOCOLS.items():
            fit = proxy_protocol(
                system,
                sequence,
                protocol,
                selected_backend,
                args.gpu_id,
            )
            fit["tau_ranges"] = add_tau_ranges(
                fit, system["energy_scales"]
            )
            record["proxy_protocols"][protocol_name] = fit
            output["formulae"][name] = record
            atomic_json(args.output, output)
        record["direct_effective_order_diagnosis"] = direct_ladder(
            system, sequence, int(formula["formal_order"]), rotations, args.gpu_id
        )
        # Correct the generic diagnosis for sixth order.
        ladder = record["direct_effective_order_diagnosis"]
        valid = [
            item["effective_order"] for item in ladder["effective_orders"]
            if item["effective_order"] is not None and not item["roundoff_risk"]
        ]
        formal = float(formula["formal_order"])
        if (
            not any(item["sign_reversal"] for item in ladder["effective_orders"])
            and not any(point["roundoff_risk"] for point in ladder["points"])
            and valid
            and min(abs(value - formal) for value in valid) <= ORDER_TOLERANCE
        ):
            ladder["diagnosis"] = (
                f"direct_effective_order_reaches_formal_order_{int(formal)}"
            )
        output["formulae"][name] = record
        atomic_json(args.output, output)
    output.update({
        "status": "complete",
        "completed_at": now(),
        "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    })
    atomic_json(args.output, output)
    return 0


def command_fine(args: argparse.Namespace) -> int:
    with args.system_cache.open("rb") as stream:
        system = pickle.load(stream)
    source = load_json(args.source_json)
    formula = full._formulae()["joint_refine_r0_s0046"]
    sequence = symmetric_s2_sequence(formula["weights"])
    rotations = full._rotation_count(system, sequence)
    model_result = source["models"]["three_term"]
    t_star = float(model_result["model_optimum"]["time"])
    point, vector = full._direct_point(
        system, sequence, args.ratio * t_star, rotations,
        "gpu", args.gpu_id, None,
    )
    prediction = full._prediction(model_result["model"], point["time"])
    point.update({
        "status": "complete",
        "created_at": now(),
        "diagnostic_kind": "post_hoc_fine_optimum_scan",
        "post_hoc": True,
        "ratio_to_predicted_t_star": args.ratio,
        "predicted_t_star": t_star,
        "model_signed_shift_hartree": prediction,
        "signed_residual_hartree": float(
            point["signed_direct_shift_hartree"] - prediction
        ),
        "residual_over_epsilon": float(
            abs(point["signed_direct_shift_hartree"] - prediction)
            / full.EPSILON_E
        ),
        "physical_gpu_id": args.gpu_id,
        "precision": "complex128/double",
        "source_json": str(args.source_json),
    })
    atomic_json(args.output, point)
    args.vector_output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.vector_output, vector)
    return 0


def protocol_rows(records: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for condition, record in records.items():
        scales = record["energy_scales"]
        for formula_name, formula in record["formulae"].items():
            for protocol_name, fit in formula["proxy_protocols"].items():
                selected = fit["selected_window"]
                row = {
                    "condition": condition,
                    "formula": formula_name,
                    "formal_order": formula["formula"]["formal_order"],
                    "protocol": protocol_name,
                    "qualified": fit["qualified"],
                    "failure_reasons": "; ".join(fit["failure_reasons"]),
                    "t_start": None if selected is None else selected["t_start"],
                    "t_stop": None if selected is None else selected["t_stop"],
                    "free_order": None if selected is None else selected["free_order"],
                    "r2": None if selected is None else selected["r2"],
                }
                for scale_name in (
                    "lambda_h_sector_centered_half_width",
                    "lambda_group_half_width_sum",
                    "lambda_pauli_nonidentity_l1",
                ):
                    row[scale_name] = scales[scale_name]
                    row["tau_start__" + scale_name] = (
                        None if selected is None
                        else float(selected["t_start"]) * float(scales[scale_name])
                    )
                    row["tau_stop__" + scale_name] = (
                        None if selected is None
                        else float(selected["t_stop"]) * float(scales[scale_name])
                    )
                rows.append(row)
    return rows


def fine_grid(
    source: dict[str, Any],
    added_dir: Path,
) -> dict[str, Any]:
    result = source["models"]["three_term"]
    optimum = result["model_optimum"]
    source_points = {
        round(float(point["relative_to_t_star"]), 2): point
        for point in result["direct_validation_points"]
    }
    partial_points = {}
    partial_vectors = {}
    for path in SOURCE_FOLLOWUP.joinpath("fine_raw").glob("r*.json"):
        point = load_json(path)
        ratio = round(float(point["ratio_to_predicted_t_star"]), 2)
        partial_points[ratio] = point
        vector_path = SOURCE_FOLLOWUP / "runtime" / "vectors" / (path.stem + ".npy")
        if vector_path.exists():
            partial_vectors[ratio] = np.load(vector_path)
    added_points = {}
    added_vectors = {}
    for ratio in ADDED_FINE_RATIOS:
        key = followup.ratio_key(ratio)
        added_points[ratio] = load_json(added_dir / (key + ".json"))
        vector_path = added_dir.parent / "runtime" / "vectors" / (key + ".npy")
        added_vectors[ratio] = np.load(vector_path)

    duplicate_checks = []
    for ratio in (0.95, 1.0):
        a = source_points[ratio]
        b = partial_points[ratio]
        duplicate_checks.append({
            "ratio": ratio,
            "signed_shift_absolute_difference_hartree": abs(
                float(a["signed_direct_shift_hartree"])
                - float(b["signed_direct_shift_hartree"])
            ),
            "direct_cost_relative_difference": abs(
                float(a["direct_cost"]) / float(b["direct_cost"]) - 1.0
            ),
        })
    points = []
    source_labels = {}
    vectors = {**partial_vectors, **added_vectors}
    for ratio in FINE_RATIOS:
        if ratio in (0.90, 0.95, 1.0, 1.05):
            point = dict(source_points[ratio])
            label = "original_model_validation"
        elif ratio in added_points:
            point = dict(added_points[ratio])
            label = "new_direct_point"
        else:
            point = dict(partial_points[ratio])
            label = "prior_post_hoc_fine_scan"
        point["ratio_to_predicted_t_star"] = ratio
        point["reuse_source"] = label
        model_value = full._prediction(result["model"], float(point["time"]))
        point["model_signed_shift_hartree"] = model_value
        point["residual_over_epsilon"] = float(
            abs(float(point["signed_direct_shift_hartree"]) - model_value)
            / full.EPSILON_E
        )
        points.append(point)
        source_labels[str(ratio)] = label
    for index, point in enumerate(points):
        left_ratio = FINE_RATIOS[index - 1] if index else None
        ratio = FINE_RATIOS[index]
        if left_ratio in vectors and ratio in vectors:
            point["fine_adjacent_vector_overlap_probability"] = float(
                abs(np.vdot(vectors[left_ratio], vectors[ratio])) ** 2
            )
        else:
            point["fine_adjacent_vector_overlap_probability"] = None
    finite = [point for point in points if point["direct_cost"] is not None]
    minimum = min(finite, key=lambda point: float(point["direct_cost"]))
    at_star = next(
        point for point in points
        if math.isclose(point["ratio_to_predicted_t_star"], 1.0)
    )
    metrics = {
        "eta_star": float(
            abs(float(optimum["cost"]) - float(at_star["direct_cost"]))
            / float(at_star["direct_cost"])
        ),
        "eta_min": float(
            float(at_star["direct_cost"]) / float(minimum["direct_cost"]) - 1.0
        ),
        "eta_t": float(
            abs(float(optimum["time"]) / float(minimum["time"]) - 1.0)
        ),
        "maximum_unseen_residual_over_epsilon": max(
            point["residual_over_epsilon"] for point in points
            if not math.isclose(point["ratio_to_predicted_t_star"], 1.0)
        ),
        "maximum_eigenpair_residual_2_norm": max(
            float(point["eigenpair_residual_2_norm"]) for point in points
        ),
        "minimum_ground_overlap_probability": min(
            float(point["ground_overlap_probability"]) for point in points
        ),
        "minimum_available_adjacent_vector_overlap_probability": min(
            float(point["fine_adjacent_vector_overlap_probability"])
            for point in points
            if point["fine_adjacent_vector_overlap_probability"] is not None
        ),
    }
    checks = {
        "eta_star": metrics["eta_star"] <= 0.01,
        "eta_min": metrics["eta_min"] <= 0.01,
        "eta_t": metrics["eta_t"] <= 0.05,
        "maximum_unseen_residual_over_epsilon": (
            metrics["maximum_unseen_residual_over_epsilon"] <= 0.05
        ),
    }
    reuse_passed = all(
        item["signed_shift_absolute_difference_hartree"] <= 1e-10
        and item["direct_cost_relative_difference"] <= 1e-8
        for item in duplicate_checks
    )
    return {
        "status": "complete",
        "post_hoc": True,
        "ratios": list(FINE_RATIOS),
        "reuse_sources": source_labels,
        "reuse_precision_checks": duplicate_checks,
        "reuse_precision_passed": reuse_passed,
        "points": points,
        "direct_grid_minimum": minimum,
        "metrics": metrics,
        "checks": checks,
        "passed_post_hoc_diagnostic": reuse_passed and all(checks.values()),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def make_plots(output_dir: Path, records: dict[str, Any], fine: dict[str, Any]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {name: f"C{index}" for index, name in enumerate(FORMULAE)}
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for axis, condition in zip(axes.flat, CONDITIONS):
        for name in FORMULAE:
            items = records[condition]["formulae"][name][
                "direct_effective_order_diagnosis"
            ]["effective_orders"]
            x = [item["geometric_mean_time"] for item in items]
            y = [item["effective_order"] for item in items]
            axis.plot(x, y, "o-", label=name, color=colors[name], ms=3)
        axis.set_xscale("log")
        axis.set_title(condition)
        axis.set_xlabel("t")
        axis.set_ylabel("p_eff")
        axis.grid(True, alpha=0.3)
    axes.flat[0].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(output_dir / "peff_vs_t.png", dpi=140)
    plt.close(fig)

    scale_names = (
        "lambda_h_sector_centered_half_width",
        "lambda_group_half_width_sum",
        "lambda_pauli_nonidentity_l1",
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for axis, scale_name in zip(axes, scale_names):
        for condition in CONDITIONS:
            scale = float(records[condition]["energy_scales"][scale_name])
            for name in FORMULAE:
                items = records[condition]["formulae"][name][
                    "direct_effective_order_diagnosis"
                ]["effective_orders"]
                x = [scale * item["geometric_mean_time"] for item in items]
                y = [item["effective_order"] for item in items]
                axis.plot(x, y, "o-", color=colors[name], alpha=0.55, ms=2)
        axis.set_xscale("log")
        axis.set_xlabel("tau")
        axis.set_ylabel("p_eff")
        axis.set_title(scale_name.replace("lambda_", ""))
        axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "peff_vs_tau.png", dpi=140)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7, 4.5))
    points = [
        point for point in fine["points"] if point["direct_cost"] is not None
    ]
    axis.plot(
        [point["ratio_to_predicted_t_star"] for point in points],
        [point["direct_cost"] for point in points],
        "o-",
    )
    axis.axvline(1.0, color="black", linestyle="--", label="model t*")
    axis.set_xlabel("t / model t*")
    axis.set_ylabel("direct cost")
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "fine_grid_direct_cost.png", dpi=140)
    plt.close(fig)


def command_aggregate(args: argparse.Namespace) -> int:
    records = {
        condition: load_json(args.raw_dir / (condition + ".json"))
        for condition in CONDITIONS
    }
    if not all(record["status"] == "complete" for record in records.values()):
        raise RuntimeError("one or more condition workers are incomplete")
    fine = fine_grid(
        load_json(
            SOURCE_RESULT / "stretch150_raw" / "joint_refine_r0_s0046.json"
        ),
        args.fine_dir,
    )
    rows = protocol_rows(records)
    write_csv(args.output_dir / "protocol_comparison.csv", rows)
    direct_rows = []
    for condition, record in records.items():
        scales = record["energy_scales"]
        for name, formula in record["formulae"].items():
            ladder = formula["direct_effective_order_diagnosis"]
            for item in ladder["effective_orders"]:
                direct_rows.append({
                    "condition": condition,
                    "formula": name,
                    **item,
                    **{
                        "tau__" + scale_name: (
                            float(item["geometric_mean_time"])
                            * float(scales[scale_name])
                        )
                        for scale_name in (
                            "lambda_h_sector_centered_half_width",
                            "lambda_group_half_width_sum",
                            "lambda_pauli_nonidentity_l1",
                        )
                    },
                    "diagnosis": ladder["diagnosis"],
                })
    write_csv(args.output_dir / "direct_peff.csv", direct_rows)
    scales_rows = [
        {
            "condition": condition,
            **{
                key: value for key, value in record["energy_scales"].items()
                if key != "group_ranges" and key != "definitions"
            },
        }
        for condition, record in records.items()
    ]
    write_csv(args.output_dir / "energy_scales.csv", scales_rows)
    make_plots(args.output_dir, records, fine)

    summary = {
        "status": "complete",
        "created_at": now(),
        "scope": {
            "coefficient_reoptimization": False,
            "new_molecules": False,
            "morales_8th": False,
            "development_diagnostic_not_independent_holdout": True,
        },
        "protocols_are_separate": True,
        "proxy_fit_note": (
            "The two historical rules are reproduced with overlap/perturbative "
            "proxy errors. The 0.02--1.8 / 5e-12 rule is sensitivity-only."
        ),
        "direct_peff_note": (
            "Signed direct PF eigenphase shifts use an independently estimated "
            "per-point numerical floor; proxy-fit floors are not reused."
        ),
        "conditions": records,
        "protocol_comparison_rows": rows,
        "direct_peff_rows": direct_rows,
        "fine_joint_stretch150": fine,
    }
    atomic_json(args.output_dir / "summary.json", summary)

    lines = [
        "# NH3 short-time fit time-scale diagnosis",
        "",
        "Status: complete",
        "",
        "This is a development diagnostic, not an independent hold-out.",
        "",
        "## Protocol comparison",
        "",
        "| condition | PF | shared protocol | legacy sensitivity | direct diagnosis |",
        "|---|---|---:|---:|---|",
    ]
    for condition in CONDITIONS:
        for name in FORMULAE:
            formula = records[condition]["formulae"][name]
            shared = formula["proxy_protocols"]["shared_molecular"]["qualified"]
            legacy = formula["proxy_protocols"][
                "legacy_molecular_sensitivity"
            ]["qualified"]
            diagnosis = formula["direct_effective_order_diagnosis"]["diagnosis"]
            lines.append(
                f"| {condition} | {name} | {shared} | {legacy} | {diagnosis} |"
            )
    lines.extend([
        "",
        "## Fine-grid post-hoc diagnosis",
        "",
        f"- eta_star: {fine['metrics']['eta_star']:.6%}",
        f"- eta_min: {fine['metrics']['eta_min']:.6%}",
        f"- eta_t: {fine['metrics']['eta_t']:.6%}",
        "- maximum unseen residual / epsilon_E: "
        f"{fine['metrics']['maximum_unseen_residual_over_epsilon']:.6g}",
        f"- result: {fine['passed_post_hoc_diagnostic']}",
        f"- reuse precision check: {fine['reuse_precision_passed']}",
        "",
        "The proxy-fit and direct-eigenphase diagnostics are reported separately.",
        "No PF coefficients were changed and no new molecule was evaluated.",
    ])
    (args.output_dir / "report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--condition", choices=CONDITIONS, required=True)
    prepare.add_argument("--component-processes", type=int, default=4)
    prepare.add_argument("--work-dir", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)

    condition = sub.add_parser("condition")
    condition.add_argument("--condition", choices=CONDITIONS, required=True)
    condition.add_argument("--system-cache", type=Path, required=True)
    condition.add_argument("--gpu-id", type=int, required=True)
    condition.add_argument("--output", type=Path, required=True)

    fine = sub.add_parser("fine")
    fine.add_argument("--system-cache", type=Path, required=True)
    fine.add_argument("--source-json", type=Path, required=True)
    fine.add_argument("--ratio", type=float, choices=ADDED_FINE_RATIOS, required=True)
    fine.add_argument("--gpu-id", type=int, required=True)
    fine.add_argument("--output", type=Path, required=True)
    fine.add_argument("--vector-output", type=Path, required=True)

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--raw-dir", type=Path, required=True)
    aggregate.add_argument("--fine-dir", type=Path, required=True)
    aggregate.add_argument("--output-dir", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "prepare":
        return command_prepare(args)
    if args.command == "condition":
        return command_condition(args)
    if args.command == "fine":
        return command_fine(args)
    if args.command == "aggregate":
        return command_aggregate(args)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
