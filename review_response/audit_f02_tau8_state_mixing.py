"""F02 audit: split fourth-order PF a8 into D8 and state mixing.

This audit consumes the F01 D4/D8 operators.  It evaluates the non-degenerate
perturbation identity

    a8 = <0|D8|0> + sum_n |<n|D4|0>|^2 / (E0 - En)

for H2/H4 and four fixed fourth-order formulas.  It also compares the exact
operator result with signed direct-eigenvalue fits in the three F01 windows.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
import json
from pathlib import Path
import platform
import resource
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from trotterlib.config import TARGET_ERROR


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_OUTPUT = Path(
    "artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3"
)
FIT_ORDERS = (4, 6, 8, 10, 12)
FIT_STABILITY_RELATIVE_THRESHOLD = 0.5
DEGENERACY_TOLERANCE_HARTREE = 1e-10
REFERENCE_TIME = 0.8
IDENTITY_ABSOLUTE_TOLERANCE = 1e-12


def fit_signed_energy_coefficients(
    times: Sequence[float],
    shifts: Sequence[float],
    orders: Sequence[int] = FIT_ORDERS,
) -> dict[str, Any]:
    """Least-squares fit signed shifts with scaled monomial columns."""

    x = np.asarray(times, dtype=float)
    y = np.asarray(shifts, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or np.any(x <= 0.0):
        raise ValueError("invalid time/shift arrays")
    if x.size < len(orders):
        raise ValueError("insufficient points for requested orders")
    scale = float(np.max(x))
    design = np.column_stack([(x / scale) ** int(order) for order in orders])
    scaled_coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
    coefficients = scaled_coefficients / np.asarray(
        [scale ** int(order) for order in orders], dtype=float
    )
    residuals = design @ scaled_coefficients - y
    return {
        "orders": tuple(int(order) for order in orders),
        "coefficients": coefficients,
        "scaled_design_condition_number": float(np.linalg.cond(design)),
        "maximum_absolute_residual_hartree": float(np.max(np.abs(residuals))),
        "root_mean_square_residual_hartree": float(
            np.sqrt(np.mean(np.square(residuals)))
        ),
    }


def decompose_a8_state_mixing(
    hamiltonian: np.ndarray,
    reference_state: np.ndarray,
    d4: np.ndarray,
    d8: np.ndarray,
    *,
    degeneracy_tolerance_hartree: float = DEGENERACY_TOLERANCE_HARTREE,
) -> dict[str, Any]:
    """Return state- and degenerate-subspace-resolved a8 contributions."""

    hamiltonian = np.asarray(hamiltonian, dtype=np.complex128)
    state = np.asarray(reference_state, dtype=np.complex128)
    d4 = np.asarray(d4, dtype=np.complex128)
    d8 = np.asarray(d8, dtype=np.complex128)
    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    overlaps = np.abs(eigenvectors.conj().T @ state) ** 2
    selected = int(np.argmax(overlaps))
    if selected != 0 and abs(float(energies[selected] - energies[0])) > 1e-12:
        raise ValueError("reference state does not select the ground eigenstate")
    d4_basis = eigenvectors.conj().T @ d4 @ eigenvectors
    d8_basis = eigenvectors.conj().T @ d8 @ eigenvectors
    e0 = float(energies[selected])

    state_rows = []
    for index, energy in enumerate(energies):
        if index == selected:
            continue
        denominator = e0 - float(energy)
        coupling = complex(d4_basis[index, selected])
        contribution = float(abs(coupling) ** 2 / denominator)
        state_rows.append(
            {
                "excited_state_index": int(index),
                "excited_energy_hartree": float(energy),
                "excitation_gap_hartree": float(energy - e0),
                "d4_coupling_real": float(coupling.real),
                "d4_coupling_imaginary": float(coupling.imag),
                "d4_coupling_absolute": float(abs(coupling)),
                "mixing_contribution_hartree": contribution,
            }
        )

    group_rows = []
    for row in state_rows:
        matching = next(
            (
                group
                for group in group_rows
                if abs(
                    group["excited_energy_hartree"]
                    - row["excited_energy_hartree"]
                )
                <= degeneracy_tolerance_hartree
            ),
            None,
        )
        if matching is None:
            matching = {
                "degenerate_group_index": len(group_rows),
                "excited_energy_hartree": row["excited_energy_hartree"],
                "excitation_gap_hartree": row["excitation_gap_hartree"],
                "state_count": 0,
                "first_state_index": row["excited_state_index"],
                "last_state_index": row["excited_state_index"],
                "squared_d4_coupling": 0.0,
                "mixing_contribution_hartree": 0.0,
            }
            group_rows.append(matching)
        matching["state_count"] += 1
        matching["last_state_index"] = row["excited_state_index"]
        matching["squared_d4_coupling"] += row["d4_coupling_absolute"] ** 2
        matching["mixing_contribution_hartree"] += row[
            "mixing_contribution_hartree"
        ]

    expectation_d8 = float(complex(d8_basis[selected, selected]).real)
    mixing = float(sum(row["mixing_contribution_hartree"] for row in state_rows))
    return {
        "selected_ground_index": selected,
        "selected_reference_overlap_probability": float(overlaps[selected]),
        "ground_energy_hartree": e0,
        "minimum_excitation_gap_hartree": min(
            row["excitation_gap_hartree"] for row in state_rows
        ),
        "d8_expectation_hartree": expectation_d8,
        "d4_second_order_mixing_hartree": mixing,
        "a8_from_components_hartree": expectation_d8 + mixing,
        "state_rows": state_rows,
        "group_rows": group_rows,
    }


def _write_figures(output_dir: Path, summaries: Sequence[dict[str, Any]]) -> None:
    labels = [
        f"{row['system_id']}\n{row['formula_id']}" for row in summaries
    ]
    locations = np.arange(len(summaries))
    width = 0.36
    scale = 1e6
    figure, axis = plt.subplots(figsize=(9.2, 4.6))
    axis.bar(
        locations - width / 2,
        [row["d8_expectation_hartree"] * scale for row in summaries],
        width,
        label=r"$\langle D_8\rangle$",
    )
    axis.bar(
        locations + width / 2,
        [row["d4_second_order_mixing_hartree"] * scale for row in summaries],
        width,
        label="D4 state mixing",
    )
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_xticks(locations, labels, rotation=35, ha="right", fontsize=8)
    axis.set_ylabel(r"component ($10^{-6}$ Hartree coefficient)")
    axis.legend(frameon=False)
    axis.grid(True, axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "a8_component_decomposition.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.0, 4.3))
    axis.bar(
        locations,
        [row["net_to_absolute_components_ratio"] for row in summaries],
        color=["C0" if row["formula_id"] == "yoshida4" else "C1" for row in summaries],
    )
    axis.set_xticks(locations, labels, rotation=35, ha="right", fontsize=8)
    axis.set_ylabel(r"$|a_8|/(|\langle D_8\rangle|+|a_8^{mix}|)$")
    axis.set_ylim(bottom=0.0)
    axis.grid(True, axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "a8_cancellation_ratio.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    summaries = audit["condition_summaries"]
    stable_count = sum(row["direct_a8_fit_stable"] for row in summaries)
    unstable_count = len(summaries) - stable_count
    lines = [
        "# F02: fourth-order PF tau^8 state-mixing audit",
        "",
        f"Status: **{audit['status']}**",
        "",
        "F01で抽出・独立検証したD4/D8を使い、a8をD8期待値とD4の二次状態混合へ分解した。"
        "H2/H4×4 PFの8条件を対象とする。",
        "",
        "## Component identity",
        "",
        "| system | PF | <D8> | D4 mixing | a8 | net/absolute components | "
        "largest excitation-group share |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{row['d8_expectation_hartree']:.6e} | "
            f"{row['d4_second_order_mixing_hartree']:.6e} | "
            f"{row['reference_a8_hartree']:.6e} | "
            f"{row['net_to_absolute_components_ratio']:.4f} | "
            f"{row['largest_group_absolute_mixing_share']:.4f} |"
        )

    lines.extend(
        [
            "",
            "The mixing denominator is negative for every excited state, so the "
            "D4 second-order contribution is non-positive. Degenerate-state "
            "rows are also aggregated by energy because individual eigenvectors "
            "inside a degenerate subspace are basis-dependent.",
            "",
            "## Direct signed-shift fit",
            "",
            f"The a8 coefficient is stable across all three direct-fit windows in "
            f"**{stable_count}/8** conditions under the declared 50% relative "
            "coefficient criterion.",
            "",
            "| system | PF | stable | worst rel. a8 error | rel. window spread | "
            "max disagreement contribution / epsilon at t=0.8 |",
            "|---|---|:---:|---:|---:|---:|",
        ]
    )
    for row in summaries:
        lines.append(
            f"| {row['system_id']} | {row['formula_id']} | "
            f"{'yes' if row['direct_a8_fit_stable'] else 'no'} | "
            f"{row['direct_fit_a8_maximum_relative_error']:.3e} | "
            f"{row['direct_fit_a8_relative_window_spread']:.3e} | "
            f"{row['direct_fit_a8_maximum_disagreement_over_epsilon_at_reference_time']:.3e} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            audit["interpretation"]["yoshida"],
            "",
            audit["interpretation"]["optimized_formulas"],
            "",
            audit["interpretation"]["direct_fit"],
            "",
            "## Decision",
            "",
            "F02の機構分解は完了した。ただし、相殺後のa8を通常の倍精度直接fitから"
            f"相対精度よく取り出せない条件が{unstable_count}/8あるため、statusは"
            "`complete_with_findings`とする。これは恒等式の不成立ではなく、"
            "大きい二成分の差として残る小係数をfitする識別性の問題である。",
            "",
            "次は保存済みの物理ギャップ・PF位相ギャップと本監査の励起状態別寄与を結合し、"
            "F05で真の小ギャップと位相折り返しを分離する。",
            "",
            "## Files",
            "",
            "- `audit.json`: complete summary and checks.",
            "- `condition_summary.csv`: component ratios and direct-fit stability.",
            "- `excited_state_contributions.csv`: state-resolved D4 mixing.",
            "- `degenerate_group_contributions.csv`: basis-invariant energy-group sums.",
            "- `direct_fit_comparison.csv`: three-window signed direct fits.",
            "- `manifest.json`: input/source/artifact hashes and runtime.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(f01_dir: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_audit_path = f01_dir / "audit.json"
    f01_operators_path = f01_dir / "effective_operators.npz"
    f01_audit = json.loads(f01_audit_path.read_text(encoding="utf-8"))
    if f01_audit["status"] != "complete" or not f01_audit["passed"]:
        raise RuntimeError("F01 input is not a completed passing audit")
    operators = np.load(f01_operators_path)
    direct_rows = f01_audit["holdout_rows"]
    reference_by_condition = {
        (row["system_id"], row["formula_id"]): row
        for row in f01_audit["condition_summaries"]
    }

    condition_summaries: list[dict[str, Any]] = []
    state_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    direct_fit_rows: list[dict[str, Any]] = []
    identity_residuals: list[float] = []
    stored_ground_state_residuals: list[float] = []

    for h_chain in (2, 4):
        system_id = f"H{h_chain}"
        hamiltonian = np.asarray(
            operators[f"{system_id}_hamiltonian"], dtype=np.complex128
        )
        state = np.asarray(
            operators[f"{system_id}_ground_state"], dtype=np.complex128
        )
        stored_energy = float(operators[f"{system_id}_ground_energy"])
        stored_ground_state_residuals.append(
            float(np.linalg.norm(hamiltonian @ state - stored_energy * state))
        )
        formula_ids = f01_audit["scope"]["formula_ids"]
        for formula_id in formula_ids:
            d4 = operators[f"{system_id}_{formula_id}_D4"]
            d8 = operators[f"{system_id}_{formula_id}_D8"]
            decomposition = decompose_a8_state_mixing(
                hamiltonian, state, d4, d8
            )
            reference = reference_by_condition[(system_id, formula_id)]
            reference_a8 = float(reference["energy_coefficients"]["a8"])
            identity_residual = float(
                decomposition["a8_from_components_hartree"] - reference_a8
            )
            identity_residuals.append(abs(identity_residual))
            mixing = decomposition["d4_second_order_mixing_hartree"]
            d8_expectation = decomposition["d8_expectation_hartree"]
            component_scale = abs(mixing) + abs(d8_expectation)

            condition_state_rows = []
            for row in decomposition["state_rows"]:
                enriched = {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    **row,
                }
                condition_state_rows.append(enriched)
                state_rows.append(enriched)
            absolute_mixing = sum(
                abs(row["mixing_contribution_hartree"])
                for row in condition_state_rows
            )
            condition_group_rows = []
            for row in decomposition["group_rows"]:
                enriched = {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    **row,
                    "absolute_mixing_share": (
                        abs(row["mixing_contribution_hartree"])
                        / max(absolute_mixing, 1e-300)
                    ),
                }
                condition_group_rows.append(enriched)
                group_rows.append(enriched)

            formula_direct_rows = [
                row
                for row in direct_rows
                if row["system_id"] == system_id
                and row["formula_id"] == formula_id
            ]
            a8_fits = []
            relative_errors = []
            signs = []
            disagreement_at_reference = []
            for window in f01_audit["protocol"]["fit_windows"]:
                rows = [
                    row
                    for row in formula_direct_rows
                    if row["window_id"] == window["window_id"]
                ]
                fit = fit_signed_energy_coefficients(
                    [row["time_hartree_inverse"] for row in rows],
                    [row["direct_pf_shift_hartree"] for row in rows],
                )
                coefficients = {
                    order: float(fit["coefficients"][index])
                    for index, order in enumerate(FIT_ORDERS)
                }
                fitted_a8 = coefficients[8]
                relative_error = abs(fitted_a8 - reference_a8) / max(
                    abs(reference_a8), 1e-300
                )
                a8_fits.append(fitted_a8)
                relative_errors.append(relative_error)
                signs.append(int(np.sign(fitted_a8)))
                disagreement_at_reference.append(
                    abs(fitted_a8 - reference_a8)
                    * REFERENCE_TIME**8
                    / TARGET_ERROR
                )
                direct_fit_rows.append(
                    {
                        "system_id": system_id,
                        "formula_id": formula_id,
                        "window_id": window["window_id"],
                        "point_count": len(rows),
                        "minimum_time": min(
                            row["time_hartree_inverse"] for row in rows
                        ),
                        "maximum_time": max(
                            row["time_hartree_inverse"] for row in rows
                        ),
                        "scaled_design_condition_number": fit[
                            "scaled_design_condition_number"
                        ],
                        "maximum_fit_residual_hartree": fit[
                            "maximum_absolute_residual_hartree"
                        ],
                        "maximum_fit_residual_over_epsilon": fit[
                            "maximum_absolute_residual_hartree"
                        ]
                        / TARGET_ERROR,
                        **{f"fitted_a{order}": coefficients[order] for order in FIT_ORDERS},
                        "reference_a8": reference_a8,
                        "a8_relative_error": relative_error,
                        "a8_disagreement_over_epsilon_at_reference_time": (
                            disagreement_at_reference[-1]
                        ),
                    }
                )

            relative_spread = (max(a8_fits) - min(a8_fits)) / max(
                abs(reference_a8), 1e-300
            )
            direct_stable = bool(
                max(relative_errors) <= FIT_STABILITY_RELATIVE_THRESHOLD
                and relative_spread <= FIT_STABILITY_RELATIVE_THRESHOLD
                and all(sign == int(np.sign(reference_a8)) for sign in signs)
            )
            condition_summaries.append(
                {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    "sector_dimension": int(state.size),
                    "minimum_excitation_gap_hartree": decomposition[
                        "minimum_excitation_gap_hartree"
                    ],
                    "d8_expectation_hartree": d8_expectation,
                    "d4_second_order_mixing_hartree": mixing,
                    "reference_a8_hartree": reference_a8,
                    "component_identity_residual_hartree": identity_residual,
                    "mixing_absolute_fraction_of_components": abs(mixing)
                    / max(component_scale, 1e-300),
                    "net_to_absolute_components_ratio": abs(reference_a8)
                    / max(component_scale, 1e-300),
                    "mixing_to_net_a8_absolute_ratio": abs(mixing)
                    / max(abs(reference_a8), 1e-300),
                    "largest_group_absolute_mixing_share": max(
                        row["absolute_mixing_share"]
                        for row in condition_group_rows
                    ),
                    "dominant_group_excitation_gap_hartree": max(
                        condition_group_rows,
                        key=lambda row: row["absolute_mixing_share"],
                    )["excitation_gap_hartree"],
                    "direct_a8_fit_stable": direct_stable,
                    "direct_fit_a8_maximum_relative_error": max(relative_errors),
                    "direct_fit_a8_relative_window_spread": relative_spread,
                    "direct_fit_a8_signs": signs,
                    "direct_fit_a8_maximum_disagreement_over_epsilon_at_reference_time": max(
                        disagreement_at_reference
                    ),
                }
            )

    stable_count = sum(row["direct_a8_fit_stable"] for row in condition_summaries)
    maximum_identity_residual = max(identity_residuals)
    all_mixing_nonpositive = all(
        row["d4_second_order_mixing_hartree"] <= 1e-18
        for row in condition_summaries
    )
    checks = [
        {
            "check_id": "stored_hamiltonian_ground_state_residual",
            "measured": max(stored_ground_state_residuals),
            "threshold": 1e-10,
            "comparison": "<=",
            "passed": max(stored_ground_state_residuals) <= 1e-10,
        },
        {
            "check_id": "a8_component_identity_absolute_residual",
            "measured": maximum_identity_residual,
            "threshold": IDENTITY_ABSOLUTE_TOLERANCE,
            "comparison": "<=",
            "passed": maximum_identity_residual <= IDENTITY_ABSOLUTE_TOLERANCE,
        },
        {
            "check_id": "all_excited_state_mixing_contributions_nonpositive",
            "measured": int(all_mixing_nonpositive),
            "threshold": 1,
            "comparison": "==",
            "passed": all_mixing_nonpositive,
        },
        {
            "check_id": "condition_count",
            "measured": len(condition_summaries),
            "threshold": 8,
            "comparison": "==",
            "passed": len(condition_summaries) == 8,
        },
    ]
    mechanism_passed = all(check["passed"] for check in checks)
    yoshida_rows = [
        row for row in condition_summaries if row["formula_id"] == "yoshida4"
    ]
    optimized_rows = [
        row for row in condition_summaries if row["formula_id"] != "yoshida4"
    ]
    center_rows = [
        row
        for row in condition_summaries
        if row["formula_id"] == "two_term_center"
    ]
    unstable_rows = [
        row for row in condition_summaries if not row["direct_a8_fit_stable"]
    ]
    maximum_unstable_disagreement = max(
        row[
            "direct_fit_a8_maximum_disagreement_over_epsilon_at_reference_time"
        ]
        for row in unstable_rows
    )
    interpretation = {
        "yoshida": (
            "Yoshida 4次ではD4状態混合が相殺前成分絶対値和の"
            f"{min(row['mixing_absolute_fraction_of_components'] for row in yoshida_rows):.1%}–"
            f"{max(row['mixing_absolute_fraction_of_components'] for row in yoshida_rows):.1%}を占め、"
            "D8期待値と同符号でa8を増強する。"
        ),
        "optimized_formulas": (
            "3つの最適化PFではD8期待値が正、D4状態混合が負で、"
            "状態混合は相殺前成分絶対値和の"
            f"{min(row['mixing_absolute_fraction_of_components'] for row in optimized_rows):.1%}–"
            f"{max(row['mixing_absolute_fraction_of_components'] for row in optimized_rows):.1%}を占める。"
            "two_term_centerの正味a8は成分絶対値和の"
            f"{min(row['net_to_absolute_components_ratio'] for row in center_rows):.1%}–"
            f"{max(row['net_to_absolute_components_ratio'] for row in center_rows):.1%}しか残らない。"
        ),
        "direct_fit": (
            f"直接固有値シフトの5項fitでa8が窓間安定したのは{stable_count}/8条件。"
            f"不安定{len(unstable_rows)}条件でもt=0.8での係数不一致の寄与は"
            f"最大{maximum_unstable_disagreement:.3e} epsilonであり、"
            "曲線再現の良さだけでは相殺後a8の機構成分を同定できない。"
        ),
    }
    audit = {
        "schema": "prevalidation_f02_tau8_state_mixing_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": (
            "complete_with_findings"
            if mechanism_passed and stable_count < len(condition_summaries)
            else "complete"
            if mechanism_passed
            else "failed"
        ),
        "mechanism_identity_passed": mechanism_passed,
        "scope": {
            "catalog_item": "F02",
            "input_f01": str(f01_dir),
            "input_basis_rule": (
                "consume H, ground state, and D operators from the same F01 NPZ; "
                "do not regenerate molecular orbitals in a new process"
            ),
            "systems": ["H2", "H4"],
            "formula_ids": f01_audit["scope"]["formula_ids"],
            "condition_count": len(condition_summaries),
            "not_completed": ["F05", "full-electron HF mechanism application"],
        },
        "protocol": {
            "identity": (
                "a8=<0|D8|0>+sum_n |<n|D4|0>|^2/(E0-En)"
            ),
            "degeneracy_tolerance_hartree": DEGENERACY_TOLERANCE_HARTREE,
            "direct_fit_orders": list(FIT_ORDERS),
            "direct_fit_windows": f01_audit["protocol"]["fit_windows"],
            "direct_fit_stability_relative_threshold": (
                FIT_STABILITY_RELATIVE_THRESHOLD
            ),
            "reference_time_hartree_inverse": REFERENCE_TIME,
            "target_error_hartree": TARGET_ERROR,
            "identity_absolute_tolerance": IDENTITY_ABSOLUTE_TOLERANCE,
        },
        "checks": checks,
        "direct_a8_fit_stable_condition_count": stable_count,
        "maximum_unstable_direct_fit_a8_disagreement_over_epsilon_at_reference_time": (
            maximum_unstable_disagreement
        ),
        "condition_summaries": condition_summaries,
        "excited_state_rows": state_rows,
        "degenerate_group_rows": group_rows,
        "direct_fit_rows": direct_fit_rows,
        "interpretation": interpretation,
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "condition_summary.csv", condition_summaries)
    _write_csv(output_dir / "excited_state_contributions.csv", state_rows)
    _write_csv(output_dir / "degenerate_group_contributions.csv", group_rows)
    _write_csv(output_dir / "direct_fit_comparison.csv", direct_fit_rows)
    _write_figures(output_dir, condition_summaries)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/audit_f01_effective_hamiltonian_multipf.py"),
        Path("review_response/bch_matrix_series.py"),
    ]
    input_paths = [f01_audit_path, f01_operators_path]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "condition_summary.csv",
        output_dir / "excited_state_contributions.csv",
        output_dir / "degenerate_group_contributions.csv",
        output_dir / "direct_fit_comparison.csv",
        output_dir / "a8_component_decomposition.png",
        output_dir / "a8_cancellation_ratio.png",
        output_dir / "report.md",
    ]
    manifest = {
        "status": audit["status"],
        "git": {
            "head": _git_output("rev-parse", "HEAD"),
            "branch": _git_output("branch", "--show-current"),
            "dirty": bool(_git_output("status", "--porcelain")),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "source_sha256": {str(path): _sha256(path) for path in source_paths},
        "input_sha256": {str(path): _sha256(path) for path in input_paths},
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
        "output_directory": str(output_dir),
        "runtime": audit["runtime"],
    }
    _atomic_json(output_dir / "manifest.json", manifest)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f01-dir", type=Path, default=DEFAULT_F01)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(arguments.f01_dir, arguments.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(arguments.output_dir),
                "status": audit["status"],
                "mechanism_identity_passed": audit[
                    "mechanism_identity_passed"
                ],
                "direct_a8_fit_stable_condition_count": audit[
                    "direct_a8_fit_stable_condition_count"
                ],
                "runtime": audit["runtime"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
