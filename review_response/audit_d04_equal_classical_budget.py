"""D04 equal-point, equal-wall-time, and equal-memory comparison.

This audit remeasures the direct PF points already selected by H05.  It does
not choose a new time design or generate a new scientific validation set.  The
small H2/H4 development conditions are used to separate shared preparation,
per-time PF construction, Schur decomposition, fitting, compact-D4 leading
coefficient acquisition, and dense D6/D8 BCH construction.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import time
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import schur

from review_response.audit_f01_effective_hamiltonian_multipf import formula_registry
from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from review_response.audit_h05_higher_order_acquisition import (
    DIRECT_DESIGNS,
    fit_signed_coefficients,
)
from review_response.bch_matrix_series import (
    effective_hamiltonian_series_numpy,
    eigenenergy_perturbation_series,
)
from trotterlib.pf_decomposition import (
    iter_s2_sequence_steps,
    symmetric_s2_sequence,
)
from trotterlib.sector_pf import build_sector_pf_unitary


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_H01 = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")
DEFAULT_H04 = Path(
    "artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1"
)
DEFAULT_H05 = Path(
    "artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2"
)
DEFAULT_X02 = Path(
    "artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3"
)
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_d04_equal_classical_budget_20260922"
)
DIRECT_METHOD_IDS = (
    "direct_fixed_a4_2_tail",
    "direct_fixed_a4_3_tail",
    "direct_fixed_a4_5_tail",
    "direct_free_3_tail",
    "direct_free_5_tail",
)
DIRECT_REPEATS = 7
FIT_REPEATS = 101
FORMULAE_PER_SYSTEM = 4


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _median(values: Sequence[float]) -> float:
    return float(statistics.median(float(value) for value in values))


def direct_incremental_working_bytes(dimension: int) -> int:
    """Conservative three-complex-matrix PF+Schur incremental workspace."""

    return int(3 * int(dimension) ** 2 * np.dtype(np.complex128).itemsize)


def compact_d4_incremental_working_bytes(
    dimension: int, grouped_term_count: int, group_count: int
) -> int:
    """Conservative retained-vector estimate for the current grouped backend."""

    retained_vectors = int(grouped_term_count) + 2 * int(group_count) + 5
    return int(retained_vectors * int(dimension) * np.dtype(np.complex128).itemsize)


def dense_bch_incremental_working_bytes(dimension: int, maximum_order: int = 8) -> int:
    """Conservative live-series estimate for the current dense BCH backend."""

    matrices_per_series = int(maximum_order) + 2
    live_series = 6
    return int(
        live_series
        * matrices_per_series
        * int(dimension) ** 2
        * np.dtype(np.complex128).itemsize
    )


def choose_best_under_budget(
    rows: Sequence[dict[str, Any]], budget_seconds: float
) -> dict[str, Any] | None:
    eligible = [
        row
        for row in rows
        if float(row["marginal_seconds_warm_cache"]) <= float(budget_seconds) * (1 + 1e-12)
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda row: (
            float(row["higher_order_residual_over_epsilon"]),
            float(row["marginal_seconds_warm_cache"]),
            int(row["direct_point_count"]),
            str(row["method_id"]),
        ),
    )


def _shared_input_bytes(
    hamiltonian: np.ndarray,
    groups: Sequence[np.ndarray],
    spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    state: np.ndarray,
) -> int:
    arrays: list[np.ndarray] = [hamiltonian, state, *groups]
    for values, vectors in spectra:
        arrays.extend((values, vectors))
    return int(sum(np.asarray(array).nbytes for array in arrays))


def _direct_point_benchmark(
    *,
    group_spectra: Sequence[tuple[np.ndarray, np.ndarray]],
    sequence: Sequence[float],
    state: np.ndarray,
    energy: float,
    time_value: float,
    repeats: int,
) -> dict[str, Any]:
    # One unmeasured call warms SciPy/BLAS allocations.
    warm = build_sector_pf_unitary(
        group_spectra, sequence, float(time_value), method="s2-cache"
    )
    schur(warm, output="complex", check_finite=False)

    build_times: list[float] = []
    schur_times: list[float] = []
    total_times: list[float] = []
    shifts: list[float] = []
    overlaps: list[float] = []
    residuals: list[float] = []
    for _ in range(int(repeats)):
        total_started = time.perf_counter()
        build_started = time.perf_counter()
        unitary = build_sector_pf_unitary(
            group_spectra, sequence, float(time_value), method="s2-cache"
        )
        build_seconds = time.perf_counter() - build_started
        schur_started = time.perf_counter()
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        schur_seconds = time.perf_counter() - schur_started
        total_seconds = time.perf_counter() - total_started

        eigenvalues = np.diag(triangular)
        state_overlaps = np.abs(vectors.conj().T @ state) ** 2
        selected = int(np.argmax(state_overlaps))
        phase = float(np.angle(eigenvalues[selected]))
        unwrap = int(
            np.rint((float(energy) * float(time_value) - phase) / (2.0 * np.pi))
        )
        effective_energy = (phase + 2.0 * np.pi * unwrap) / float(time_value)
        vector = np.asarray(vectors[:, selected], dtype=np.complex128)
        shifts.append(float(effective_energy - energy))
        overlaps.append(float(state_overlaps[selected]))
        residuals.append(
            float(np.linalg.norm(unitary @ vector - eigenvalues[selected] * vector))
        )
        build_times.append(build_seconds)
        schur_times.append(schur_seconds)
        total_times.append(total_seconds)
    return {
        "median_unitary_build_seconds": _median(build_times),
        "median_schur_seconds": _median(schur_times),
        "median_total_seconds": _median(total_times),
        "minimum_total_seconds": float(min(total_times)),
        "maximum_total_seconds": float(max(total_times)),
        "signed_direct_shift_hartree": _median(shifts),
        "shift_repeat_spread_hartree": float(max(shifts) - min(shifts)),
        "minimum_ground_overlap_probability": float(min(overlaps)),
        "maximum_eigenpair_residual_2_norm": float(max(residuals)),
    }


def _benchmark_fit(
    times: Sequence[float],
    shifts: Sequence[float],
    orders: Sequence[int],
    fixed_a4: float | None,
) -> float:
    fixed = None if fixed_a4 is None else {4: float(fixed_a4)}
    timings = []
    for _ in range(FIT_REPEATS):
        started = time.perf_counter()
        fit_signed_coefficients(
            times, shifts, orders, fixed_coefficients=fixed
        )
        timings.append(time.perf_counter() - started)
    return _median(timings)


def _plot(output_dir: Path, summaries: Sequence[dict[str, Any]]) -> None:
    direct = [row for row in summaries if row["method_id"] in DIRECT_METHOD_IDS]
    labels = [str(row["method_id"]) for row in direct]
    figure, left = plt.subplots(figsize=(9.0, 4.6))
    locations = np.arange(len(direct))
    left.bar(
        locations - 0.18,
        [float(row["median_marginal_seconds_warm_cache"]) for row in direct],
        width=0.36,
        label="median warm wall time",
    )
    left.set_ylabel("seconds")
    left.set_yscale("log")
    left.set_xticks(locations, labels, rotation=32, ha="right")
    right = left.twinx()
    right.bar(
        locations + 0.18,
        [float(row["maximum_higher_order_residual_over_epsilon"]) for row in direct],
        width=0.36,
        color="tab:orange",
        label="worst residual / epsilon",
    )
    right.axhline(0.05, color="black", linestyle="--", linewidth=0.9)
    right.set_ylabel("worst residual / epsilon")
    left.grid(True, axis="y", alpha=0.25)
    handles_left, labels_left = left.get_legend_handles_labels()
    handles_right, labels_right = right.get_legend_handles_labels()
    left.legend(handles_left + handles_right, labels_left + labels_right, frameon=False)
    figure.tight_layout()
    figure.savefig(output_dir / "wall_time_vs_residual.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    summary = audit["summary"]
    lines = [
        "# D04: equal classical-budget comparison",
        "",
        f"Status: **{audit['status']}**",
        "",
        "This is a cost audit on the existing H2/H4 development data. The H05 "
        "time designs and coefficients were not changed. All direct methods remain "
        "oracle-assisted because the saved branch rule uses the exact ground state.",
        "",
        "## End-to-end method summary",
        "",
        "| method | direct points | residual pass | worst residual/epsilon | median warm s | "
        "median cold s | median PF exponentials | median estimated peak MiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in audit["method_summaries"]:
        lines.append(
            f"| {row['method_id']} | {row['direct_point_count']} | "
            f"{row['residual_pass_count']}/8 | "
            f"{row['maximum_higher_order_residual_over_epsilon']:.4e} | "
            f"{row['median_marginal_seconds_warm_cache']:.4e} | "
            f"{row['median_cold_seconds_no_reuse']:.4e} | "
            f"{row['median_pf_exponential_action_count']:.0f} | "
            f"{row['median_estimated_peak_bytes'] / 2**20:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Same-point comparison",
            "",
            "| points | fixed-a4 method | free method | fixed/free median-time ratio | "
            "fixed/free worst residual |",
            "|---:|---|---|---:|---:|",
        ]
    )
    for row in audit["same_point_rows"]:
        lines.append(
            f"| {row['point_count']} | {row['fixed_method_id']} | {row['free_method_id']} | "
            f"{row['fixed_to_free_median_time_ratio']:.4f} | "
            f"{row['fixed_worst_residual_over_epsilon']:.4e} / "
            f"{row['free_worst_residual_over_epsilon']:.4e} |"
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"The fixed-a4 two-point design retains the H05 result of "
            f"{summary['fixed_two_point_residual_pass_count']}/8 residual passes. "
            f"After charging compact-D4 acquisition, it is faster than the free "
            f"five-point fit in {summary['fixed_two_faster_than_free_five_count']}/8 "
            "conditions and uses no more estimated peak memory in "
            f"{summary['fixed_two_no_more_memory_than_free_five_count']}/8.",
            "",
            f"At the same three direct points, fixed a4 passes "
            f"{summary['fixed_three_residual_pass_count']}/8 versus "
            f"{summary['free_three_residual_pass_count']}/8 for the free fit, but the "
            f"fixed route has median wall-time ratio "
            f"{summary['fixed_three_to_free_three_median_time_ratio']:.3f}. "
            "The extra prior coefficient is therefore an additional classical "
            "resource, not a free reduction in information.",
            "",
            f"The zero-direct-point dense order-8 BCH route passes "
            f"{summary['dense_bch_residual_pass_count']}/8, but its median marginal "
            f"time is {summary['dense_bch_to_free_five_median_time_ratio']:.2f} times "
            "the free five-point route and it materializes dense operator series. "
            "This is a small-system mechanism reference, not a scalable acquisition route.",
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "Report point-count, warm-cache time, cold preparation-inclusive time, PF "
            "exponential count, compact group-matvec count, and estimated memory "
            "separately. Do not convert unlike group matvecs and matrix exponentials "
            "into a single operation count.",
            "",
            "## Scope",
            "",
            "The two-point time design was selected on these same H-chain development "
            "conditions. Timing it does not turn it into an independent hold-out result. "
            "The measured CPU results do not override or retrofit the frozen P0-3 protocol.",
            "",
            "## Files",
            "",
            "- `direct_point_timing.csv`: repeated unitary-build and Schur timings.",
            "- `method_resources.csv`: condition-level end-to-end resource ledger.",
            "- `method_summary.csv`: method-level accuracy/resource summary.",
            "- `same_point_comparison.csv`: fixed versus free fits at equal point count.",
            "- `equal_time_frontier.csv`: best method under predeclared method budgets.",
            "- `dense_bch_timing.csv`: D4/D6/D8 dense construction timing and checks.",
            "- `audit.json`, `manifest.json`: machine-readable conclusions and hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    f01_dir: Path,
    h01_dir: Path,
    h04_dir: Path,
    h05_dir: Path,
    x02_dir: Path,
    output_dir: Path,
    *,
    direct_repeats: int = DIRECT_REPEATS,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_path = f01_dir / "audit.json"
    operators_path = f01_dir / "effective_operators.npz"
    states_path = h01_dir / "states.npz"
    h04_path = h04_dir / "audit.json"
    h05_path = h05_dir / "audit.json"
    x02_path = x02_dir / "audit.json"
    f01 = json.loads(f01_path.read_text(encoding="utf-8"))
    h04 = json.loads(h04_path.read_text(encoding="utf-8"))
    h05 = json.loads(h05_path.read_text(encoding="utf-8"))
    x02 = json.loads(x02_path.read_text(encoding="utf-8"))
    if f01["status"] != "complete" or not f01["passed"]:
        raise RuntimeError("F01 input is not complete")
    if h04["status"] != "complete_with_findings" or not h04["passed"]:
        raise RuntimeError("H04 input is not complete")
    if h05["status"] != "complete_with_findings" or not h05["passed"]:
        raise RuntimeError("H05 input is not complete")
    if x02["status"] != "complete_with_findings":
        raise RuntimeError("X02 input is not complete")

    formulae = {row["formula_id"]: row for row in formula_registry()}
    h04_methods = {
        (row["system_id"], row["formula_id"]): row for row in h04["method_rows"]
    }
    h05_methods = {
        (row["system_id"], row["formula_id"], row["method_id"]): row
        for row in h05["method_rows"]
    }
    response_rows = {
        (row["system_id"], row["formula_id"]): row
        for row in h05["response_rows"]
        if row["state_id"] == "exact"
    }
    f01_points = {
        (
            row["system_id"],
            row["formula_id"],
            round(float(row["time_hartree_inverse"]), 14),
        ): row
        for row in f01["holdout_rows"]
        if row["window_id"] == "middle"
    }
    setup_seconds = {
        system_id: float(values["setup_seconds"])
        for system_id, values in x02["timing_seconds"].items()
        if system_id in ("H2", "H4")
    }
    direct_point_rows: list[dict[str, Any]] = []
    resource_rows: list[dict[str, Any]] = []
    dense_bch_rows: list[dict[str, Any]] = []

    with np.load(operators_path) as operators, np.load(states_path) as states:
        for system_id in ("H2", "H4"):
            hamiltonian = np.asarray(
                operators[f"{system_id}_hamiltonian"], dtype=np.complex128
            )
            group_keys = sorted(
                key for key in operators.files if key.startswith(f"{system_id}_group_")
            )
            groups = [
                np.asarray(operators[key], dtype=np.complex128) for key in group_keys
            ]
            spectra = [np.linalg.eigh(group) for group in groups]
            state = np.asarray(states[f"{system_id}_exact_state"], dtype=np.complex128)
            state /= np.linalg.norm(state)
            energy = float(np.vdot(state, hamiltonian @ state).real)
            dimension = int(state.size)
            shared_bytes = _shared_input_bytes(
                hamiltonian, groups, spectra, state
            )

            for formula_id, formula in formulae.items():
                sequence = symmetric_s2_sequence(formula["weights"])
                expanded_steps = list(iter_s2_sequence_steps(len(groups), sequence))
                direct_method = h05_methods[
                    (system_id, formula_id, "direct_free_5_tail")
                ]
                all_times = [
                    float(value)
                    for value in json.loads(direct_method["direct_times_json"])
                ]
                timing_by_time: dict[float, dict[str, Any]] = {}
                shift_by_time: dict[float, float] = {}
                for time_value in all_times:
                    measured = _direct_point_benchmark(
                        group_spectra=spectra,
                        sequence=sequence,
                        state=state,
                        energy=energy,
                        time_value=time_value,
                        repeats=direct_repeats,
                    )
                    reference = f01_points[
                        (system_id, formula_id, round(time_value, 14))
                    ]
                    reference_shift = float(reference["direct_pf_shift_hartree"])
                    measured["absolute_shift_difference_hartree"] = abs(
                        float(measured["signed_direct_shift_hartree"])
                        - reference_shift
                    )
                    row = {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "time_hartree_inverse": time_value,
                        "repeat_count": int(direct_repeats),
                        "reference_signed_shift_hartree": reference_shift,
                        **measured,
                    }
                    direct_point_rows.append(row)
                    timing_by_time[round(time_value, 14)] = measured
                    shift_by_time[round(time_value, 14)] = reference_shift

                h04_row = h04_methods[(system_id, formula_id)]
                a4_seconds = float(h04_row["grouped_construction_seconds"]) + float(
                    h04_row["median_grouped_action_seconds"]
                )
                compact_bytes = compact_d4_incremental_working_bytes(
                    dimension,
                    int(h04_row["grouped_d4_term_count"]),
                    len(groups),
                )
                direct_bytes = direct_incremental_working_bytes(dimension)
                compact_actions = int(
                    response_rows[(system_id, formula_id)][
                        "compact_linear_combination_action_count"
                    ]
                )
                reference_a4 = float(
                    h05_methods[(system_id, formula_id, "bch_exact_response")][
                        "reference_a4_hartree"
                    ]
                )

                for method_id in DIRECT_METHOD_IDS:
                    h05_row = h05_methods[(system_id, formula_id, method_id)]
                    selected_times = [
                        float(value)
                        for value in json.loads(h05_row["direct_times_json"])
                    ]
                    selected_timings = [
                        timing_by_time[round(value, 14)] for value in selected_times
                    ]
                    selected_shifts = [
                        shift_by_time[round(value, 14)] for value in selected_times
                    ]
                    design = DIRECT_DESIGNS[method_id]
                    fixed = bool(design["fixed_a4"])
                    fit_seconds = _benchmark_fit(
                        selected_times,
                        selected_shifts,
                        design["orders"],
                        reference_a4 if fixed else None,
                    )
                    build_seconds = float(
                        sum(row["median_unitary_build_seconds"] for row in selected_timings)
                    )
                    schur_seconds = float(
                        sum(row["median_schur_seconds"] for row in selected_timings)
                    )
                    direct_seconds = float(
                        sum(row["median_total_seconds"] for row in selected_timings)
                    )
                    leading_seconds = a4_seconds if fixed else 0.0
                    marginal = leading_seconds + direct_seconds + fit_seconds
                    incremental_bytes = max(
                        direct_bytes, compact_bytes if fixed else 0
                    )
                    resource_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula_id,
                            "method_id": method_id,
                            "direct_point_count": len(selected_times),
                            "requires_compact_a4": fixed,
                            "shared_preparation_seconds": setup_seconds[system_id],
                            "compact_a4_seconds": leading_seconds,
                            "direct_unitary_build_seconds": build_seconds,
                            "direct_schur_seconds": schur_seconds,
                            "direct_point_total_seconds": direct_seconds,
                            "fit_seconds": fit_seconds,
                            "marginal_seconds_warm_cache": marginal,
                            "cold_seconds_no_reuse": setup_seconds[system_id] + marginal,
                            "batched_seconds_setup_amortized": (
                                setup_seconds[system_id] / FORMULAE_PER_SYSTEM + marginal
                            ),
                            "pf_exponential_action_count": (
                                len(expanded_steps) * len(selected_times)
                            ),
                            "compact_group_matvec_action_count": (
                                compact_actions if fixed else 0
                            ),
                            "shared_input_bytes": shared_bytes,
                            "incremental_working_bytes": incremental_bytes,
                            "estimated_peak_bytes": shared_bytes + incremental_bytes,
                            "higher_order_residual_over_epsilon": float(
                                h05_row["higher_order_residual_over_epsilon"]
                            ),
                            "meets_residual_threshold": bool(
                                h05_row["meets_higher_order_residual_threshold"]
                            ),
                        }
                    )

                bch_started = time.perf_counter()
                bch = effective_hamiltonian_series_numpy(
                    groups, expanded_steps, maximum_effective_order=8
                )["effective_hamiltonian"]
                bch_series_seconds = time.perf_counter() - bch_started
                perturbation_started = time.perf_counter()
                perturbation = eigenenergy_perturbation_series(
                    bch, state, maximum_order=8
                )
                perturbation_seconds = time.perf_counter() - perturbation_started
                coefficients = np.asarray(
                    perturbation["energy_coefficients"], dtype=np.complex128
                )
                bch_reference = h05_methods[
                    (system_id, formula_id, "bch_exact_response")
                ]
                coefficient_differences = {
                    order: abs(
                        float(coefficients[order].real)
                        - float(bch_reference[f"reference_a{order}_hartree"])
                    )
                    for order in (4, 6, 8)
                }
                bch_incremental = dense_bch_incremental_working_bytes(dimension)
                bch_total = bch_series_seconds + perturbation_seconds
                dense_bch_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "dimension": dimension,
                        "group_count": len(groups),
                        "expanded_step_count": len(expanded_steps),
                        "series_seconds": bch_series_seconds,
                        "perturbation_seconds": perturbation_seconds,
                        "marginal_seconds_warm_cache": bch_total,
                        "cold_seconds_no_reuse": setup_seconds[system_id] + bch_total,
                        "shared_input_bytes": shared_bytes,
                        "incremental_working_bytes": bch_incremental,
                        "estimated_peak_bytes": shared_bytes + bch_incremental,
                        "a4_absolute_difference_hartree": coefficient_differences[4],
                        "a6_absolute_difference_hartree": coefficient_differences[6],
                        "a8_absolute_difference_hartree": coefficient_differences[8],
                        "higher_order_residual_over_epsilon": float(
                            bch_reference["higher_order_residual_over_epsilon"]
                        ),
                        "meets_residual_threshold": bool(
                            bch_reference["meets_higher_order_residual_threshold"]
                        ),
                    }
                )

    method_summaries: list[dict[str, Any]] = []
    for method_id in (*DIRECT_METHOD_IDS, "dense_bch_order8"):
        rows = (
            [row for row in resource_rows if row["method_id"] == method_id]
            if method_id != "dense_bch_order8"
            else dense_bch_rows
        )
        residuals = [float(row["higher_order_residual_over_epsilon"]) for row in rows]
        method_summaries.append(
            {
                "method_id": method_id,
                "condition_count": len(rows),
                "direct_point_count": (
                    int(rows[0]["direct_point_count"])
                    if method_id != "dense_bch_order8"
                    else 0
                ),
                "residual_pass_count": sum(
                    bool(row["meets_residual_threshold"]) for row in rows
                ),
                "maximum_higher_order_residual_over_epsilon": max(residuals),
                "median_higher_order_residual_over_epsilon": _median(residuals),
                "median_marginal_seconds_warm_cache": _median(
                    [float(row["marginal_seconds_warm_cache"]) for row in rows]
                ),
                "maximum_marginal_seconds_warm_cache": max(
                    float(row["marginal_seconds_warm_cache"]) for row in rows
                ),
                "median_cold_seconds_no_reuse": _median(
                    [float(row["cold_seconds_no_reuse"]) for row in rows]
                ),
                "median_estimated_peak_bytes": _median(
                    [float(row["estimated_peak_bytes"]) for row in rows]
                ),
                "median_pf_exponential_action_count": (
                    _median(
                        [float(row["pf_exponential_action_count"]) for row in rows]
                    )
                    if method_id != "dense_bch_order8"
                    else 0.0
                ),
                "median_compact_group_matvec_action_count": (
                    _median(
                        [
                            float(row["compact_group_matvec_action_count"])
                            for row in rows
                        ]
                    )
                    if method_id != "dense_bch_order8"
                    else 0.0
                ),
            }
        )
    summaries = {row["method_id"]: row for row in method_summaries}

    same_point_rows = []
    for points in (3, 5):
        fixed_id = f"direct_fixed_a4_{points}_tail"
        free_id = f"direct_free_{points}_tail"
        fixed_summary = summaries[fixed_id]
        free_summary = summaries[free_id]
        same_point_rows.append(
            {
                "point_count": points,
                "fixed_method_id": fixed_id,
                "free_method_id": free_id,
                "fixed_to_free_median_time_ratio": (
                    fixed_summary["median_marginal_seconds_warm_cache"]
                    / free_summary["median_marginal_seconds_warm_cache"]
                ),
                "fixed_worst_residual_over_epsilon": fixed_summary[
                    "maximum_higher_order_residual_over_epsilon"
                ],
                "free_worst_residual_over_epsilon": free_summary[
                    "maximum_higher_order_residual_over_epsilon"
                ],
                "fixed_residual_pass_count": fixed_summary["residual_pass_count"],
                "free_residual_pass_count": free_summary["residual_pass_count"],
            }
        )

    frontier_rows = []
    for system_id in ("H2", "H4"):
        for formula_id in formulae:
            condition_rows = [
                row
                for row in resource_rows
                if row["system_id"] == system_id and row["formula_id"] == formula_id
            ]
            by_method = {row["method_id"]: row for row in condition_rows}
            for budget_source in (
                "direct_fixed_a4_2_tail",
                "direct_free_3_tail",
                "direct_free_5_tail",
            ):
                budget = float(
                    by_method[budget_source]["marginal_seconds_warm_cache"]
                )
                selected = choose_best_under_budget(condition_rows, budget)
                if selected is None:
                    raise RuntimeError("budget source must make at least itself feasible")
                frontier_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "budget_source_method_id": budget_source,
                        "budget_seconds": budget,
                        "selected_method_id": selected["method_id"],
                        "selected_seconds": selected["marginal_seconds_warm_cache"],
                        "selected_direct_point_count": selected["direct_point_count"],
                        "selected_residual_over_epsilon": selected[
                            "higher_order_residual_over_epsilon"
                        ],
                        "selected_meets_residual_threshold": selected[
                            "meets_residual_threshold"
                        ],
                    }
                )

    fixed_two_rows = [
        row for row in resource_rows if row["method_id"] == "direct_fixed_a4_2_tail"
    ]
    free_five_rows = {
        (row["system_id"], row["formula_id"]): row
        for row in resource_rows
        if row["method_id"] == "direct_free_5_tail"
    }
    faster_count = sum(
        float(row["marginal_seconds_warm_cache"])
        <= float(free_five_rows[(row["system_id"], row["formula_id"])]["marginal_seconds_warm_cache"])
        for row in fixed_two_rows
    )
    no_more_memory_count = sum(
        int(row["estimated_peak_bytes"])
        <= int(free_five_rows[(row["system_id"], row["formula_id"])]["estimated_peak_bytes"])
        for row in fixed_two_rows
    )
    fixed_three_ratio = next(
        row["fixed_to_free_median_time_ratio"]
        for row in same_point_rows
        if row["point_count"] == 3
    )
    dense_ratio = (
        summaries["dense_bch_order8"]["median_marginal_seconds_warm_cache"]
        / summaries["direct_free_5_tail"]["median_marginal_seconds_warm_cache"]
    )
    uniform_time_advantage = faster_count == 8
    uniform_memory_advantage = no_more_memory_count == 8
    if uniform_time_advantage and uniform_memory_advantage:
        decision = (
            "On these development conditions, the fixed-a4 two-point route reduces "
            "direct points, warm-cache wall time, and estimated peak memory uniformly. "
            "This supports a resource-saving candidate, subject to a frozen unused-system test."
        )
    else:
        decision = (
            "The fixed-a4 two-point route is a valid few-direct-point claim, but it is "
            "not a uniform end-to-end resource reduction after charging a4 acquisition. "
            "Use point count, wall time, and memory as separate claims and carry the "
            "two-point design only as a preregistered future hold-out candidate."
        )

    maximum_shift_difference = max(
        float(row["absolute_shift_difference_hartree"]) for row in direct_point_rows
    )
    maximum_bch_difference = max(
        float(row[key])
        for row in dense_bch_rows
        for key in (
            "a4_absolute_difference_hartree",
            "a6_absolute_difference_hartree",
            "a8_absolute_difference_hartree",
        )
    )
    checks = [
        {
            "check_id": "remeasured_direct_shifts_match_h05_inputs",
            "measured": maximum_shift_difference,
            "threshold": 2e-13,
            "passed": maximum_shift_difference <= 2e-13,
        },
        {
            "check_id": "dense_order8_coefficients_match_f01_h05_reference",
            "measured": maximum_bch_difference,
            "threshold": 2e-12,
            "passed": maximum_bch_difference <= 2e-12,
        },
        {
            "check_id": "all_direct_methods_have_eight_conditions",
            "measured": min(
                row["condition_count"]
                for row in method_summaries
                if row["method_id"] in DIRECT_METHOD_IDS
            ),
            "threshold": 8,
            "passed": all(
                row["condition_count"] == 8
                for row in method_summaries
                if row["method_id"] in DIRECT_METHOD_IDS
            ),
        },
        {
            "check_id": "fixed_two_point_accuracy_reproduced",
            "measured": summaries["direct_fixed_a4_2_tail"]["residual_pass_count"],
            "threshold": 8,
            "passed": summaries["direct_fixed_a4_2_tail"]["residual_pass_count"] == 8,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    summary = {
        "fixed_two_point_residual_pass_count": summaries[
            "direct_fixed_a4_2_tail"
        ]["residual_pass_count"],
        "fixed_three_residual_pass_count": summaries[
            "direct_fixed_a4_3_tail"
        ]["residual_pass_count"],
        "free_three_residual_pass_count": summaries["direct_free_3_tail"][
            "residual_pass_count"
        ],
        "fixed_two_faster_than_free_five_count": int(faster_count),
        "fixed_two_no_more_memory_than_free_five_count": int(
            no_more_memory_count
        ),
        "fixed_three_to_free_three_median_time_ratio": float(fixed_three_ratio),
        "dense_bch_residual_pass_count": summaries["dense_bch_order8"][
            "residual_pass_count"
        ],
        "dense_bch_to_free_five_median_time_ratio": float(dense_ratio),
        "maximum_remeasured_shift_difference_hartree": maximum_shift_difference,
        "maximum_dense_bch_coefficient_difference_hartree": maximum_bch_difference,
        "point_saving_is_uniform_wall_time_saving": uniform_time_advantage,
        "point_saving_is_uniform_memory_saving": uniform_memory_advantage,
        "decision": decision,
    }
    audit = {
        "schema": "prevalidation_d04_equal_classical_budget_v1",
        "status": "complete_with_findings" if passed else "failed_checks",
        "passed": passed,
        "scope": {
            "catalog_item": "D04",
            "systems": ["H2", "H4"],
            "formulae": list(formulae),
            "new_scientific_direct_points": 0,
            "remeasured_existing_h05_points": len(direct_point_rows),
            "direct_timing_repeats": int(direct_repeats),
            "information_access": "oracle-assisted exact-state branch timing",
            "gpu_used": False,
            "claim_boundary": (
                "small dense H-chain development timing; not an independent molecular holdout"
            ),
        },
        "checks": checks,
        "summary": summary,
        "direct_point_rows": direct_point_rows,
        "resource_rows": resource_rows,
        "dense_bch_rows": dense_bch_rows,
        "method_summaries": method_summaries,
        "same_point_rows": same_point_rows,
        "frontier_rows": frontier_rows,
        "peak_process_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
        "elapsed_seconds": float(time.perf_counter() - started),
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "direct_point_timing.csv", direct_point_rows)
    _write_csv(output_dir / "method_resources.csv", resource_rows)
    _write_csv(output_dir / "dense_bch_timing.csv", dense_bch_rows)
    _write_csv(output_dir / "method_summary.csv", method_summaries)
    _write_csv(output_dir / "same_point_comparison.csv", same_point_rows)
    _write_csv(output_dir / "equal_time_frontier.csv", frontier_rows)
    _plot(output_dir, method_summaries)
    _write_report(output_dir / "report.md", audit)

    source_paths = [Path(__file__)]
    input_paths = [f01_path, operators_path, states_path, h04_path, h05_path, x02_path]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "direct_point_timing.csv",
        output_dir / "method_resources.csv",
        output_dir / "dense_bch_timing.csv",
        output_dir / "method_summary.csv",
        output_dir / "same_point_comparison.csv",
        output_dir / "equal_time_frontier.csv",
        output_dir / "wall_time_vs_residual.png",
        output_dir / "report.md",
    ]
    manifest = {
        "schema": "prevalidation_d04_manifest_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": audit["status"],
        "git": {
            "commit": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "remote": _git_output("remote", "get-url", "origin"),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f01-dir", type=Path, default=DEFAULT_F01)
    parser.add_argument("--h01-dir", type=Path, default=DEFAULT_H01)
    parser.add_argument("--h04-dir", type=Path, default=DEFAULT_H04)
    parser.add_argument("--h05-dir", type=Path, default=DEFAULT_H05)
    parser.add_argument("--x02-dir", type=Path, default=DEFAULT_X02)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--direct-repeats", type=int, default=DIRECT_REPEATS)
    arguments = parser.parse_args()
    audit = run(
        arguments.f01_dir,
        arguments.h01_dir,
        arguments.h04_dir,
        arguments.h05_dir,
        arguments.x02_dir,
        arguments.output_dir,
        direct_repeats=arguments.direct_repeats,
    )
    print(json.dumps({"status": audit["status"], **audit["summary"]}, indent=2))


if __name__ == "__main__":
    main()
