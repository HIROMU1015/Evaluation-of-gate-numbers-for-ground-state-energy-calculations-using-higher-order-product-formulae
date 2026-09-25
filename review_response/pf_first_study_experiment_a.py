"""Core logic for the preregistered first-study Experiment A."""

from __future__ import annotations

from datetime import datetime
import importlib.metadata
from pathlib import Path
import platform
import resource
import time
from typing import Any, Sequence

import numpy as np
from scipy.linalg import expm, schur

from review_response._pf_first_study_experiment_a_support import (
    atomic_json,
    formula_registry,
    git_output,
    load_h2_system,
    load_protocol,
    pf_unitary,
    pf_unitary_high_precision,
    propagator_minus,
    sha256_file,
    two_level_systems,
    write_csv,
)
from review_response.bch_matrix_series import (
    effective_hamiltonian_series,
    ordered_exponential_product_series,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps


def track_direct_branch(
    unitaries: Sequence[np.ndarray],
    signed_times: Sequence[float],
    reference_state: np.ndarray,
    reference_energy: float,
    degeneracy_gap: float,
) -> list[dict[str, Any]]:
    """Continue one signed-time branch independently outward from zero."""

    previous_vector = np.asarray(reference_state, dtype=np.complex128)
    previous_energy = float(reference_energy)
    rows: list[dict[str, Any]] = []
    for point_index, (unitary, time_value) in enumerate(
        zip(unitaries, signed_times, strict=True)
    ):
        triangular, vectors = schur(unitary, output="complex", check_finite=False)
        eigenvalues = np.diag(triangular)
        previous_overlaps = np.abs(vectors.conj().T @ previous_vector) ** 2
        selected = int(np.argmax(previous_overlaps))
        vector = np.asarray(vectors[:, selected], dtype=np.complex128)
        principal_phase = float(np.angle(eigenvalues[selected]))
        target_energy = reference_energy if point_index == 0 else previous_energy
        unwrap_integer = int(
            np.rint(
                (float(target_energy) * float(time_value) - principal_phase)
                / (2.0 * np.pi)
            )
        )
        unwrapped_phase = principal_phase + 2.0 * np.pi * unwrap_integer
        effective_energy = unwrapped_phase / float(time_value)
        phase_distances = np.abs(
            np.angle(np.exp(1j * (np.angle(eigenvalues) - principal_phase)))
        )
        cluster = phase_distances <= float(degeneracy_gap)
        rows.append(
            {
                "selected_eigenbranch_id": selected,
                "principal_phase_radians": principal_phase,
                "unwrapped_phase_radians": unwrapped_phase,
                "unwrap_integer": unwrap_integer,
                "direct_shift_hartree": float(
                    effective_energy - reference_energy
                ),
                "ground_state_overlap_probability": float(
                    abs(np.vdot(reference_state, vector)) ** 2
                ),
                "previous_branch_overlap_probability": float(
                    previous_overlaps[selected]
                ),
                "degenerate_subspace_projector_overlap_probability": float(
                    np.sum(previous_overlaps[cluster])
                ),
                "eigenpair_residual_2_norm": float(
                    np.linalg.norm(
                        unitary @ vector - eigenvalues[selected] * vector
                    )
                ),
            }
        )
        previous_vector = vector
        previous_energy = effective_energy
    return rows


def echo_proxies(
    hamiltonian: np.ndarray,
    unitary: np.ndarray,
    state: np.ndarray,
    time_value: float,
    previous_unwrapped_phase: float,
) -> tuple[dict[str, float | int], float]:
    echo = propagator_minus(hamiltonian, time_value) @ unitary
    amplitude = complex(np.vdot(state, echo @ state))
    principal_phase = float(np.angle(amplitude))
    unwrap_integer = int(
        np.rint((previous_unwrapped_phase - principal_phase) / (2.0 * np.pi))
    )
    unwrapped_phase = principal_phase + 2.0 * np.pi * unwrap_integer
    return (
        {
            "echo_real": float(amplitude.real),
            "echo_imaginary": float(amplitude.imag),
            "echo_overlap_magnitude": float(abs(amplitude)),
            "echo_principal_phase_radians": principal_phase,
            "echo_unwrapped_phase_radians": unwrapped_phase,
            "echo_unwrap_integer": unwrap_integer,
            "proxy_imag_hartree": float(amplitude.imag / time_value),
            "proxy_arg_hartree": float(unwrapped_phase / time_value),
        },
        unwrapped_phase,
    )


def scaled_even_fit(
    times: np.ndarray, values: np.ndarray
) -> tuple[np.ndarray, float]:
    design = np.column_stack([times**4, times**6])
    norms = np.linalg.norm(design, axis=0)
    scaled_design = design / norms[None, :]
    scaled_coefficients = np.linalg.lstsq(
        scaled_design, values, rcond=None
    )[0]
    return scaled_coefficients / norms, float(np.linalg.cond(scaled_design))


def build_decomposition_rows(
    observables: Sequence[dict[str, Any]], target_error: float
) -> tuple[list[dict[str, Any]], float]:
    """Apply the fixed signed decomposition and verify algebraic closure."""

    exact_lookup = {
        (
            row["system_id"],
            row["formula_id"],
            row["sign"],
            row["absolute_time"],
        ): float(row["proxy_imag_hartree"])
        for row in observables
        if row["state_id"] == "exact_ground"
    }
    keys = sorted(
        {
            (row["system_id"], row["formula_id"], row["state_id"])
            for row in observables
        }
    )
    result: list[dict[str, Any]] = []
    maximum_closure = 0.0
    for system_id, formula_id, state_id in keys:
        selected = [
            row
            for row in observables
            if (row["system_id"], row["formula_id"], row["state_id"])
            == (system_id, formula_id, state_id)
        ]
        positive = sorted(
            (row for row in selected if row["sign"] == 1),
            key=lambda row: row["absolute_time"],
        )
        times = np.asarray([row["absolute_time"] for row in positive], dtype=float)
        values = np.asarray(
            [row["proxy_imag_hartree"] for row in positive], dtype=float
        )
        coefficients, condition_number = scaled_even_fit(times, values)
        for row in selected:
            time_value = float(row["time_hartree_inverse"])
            fitted = float(
                coefficients[0] * time_value**4
                + coefficients[1] * time_value**6
            )
            exact_proxy = exact_lookup[
                (
                    system_id,
                    formula_id,
                    row["sign"],
                    row["absolute_time"],
                )
            ]
            direct = float(row["direct_shift_hartree"])
            approximate_proxy = float(row["proxy_imag_hartree"])
            fit_signed = fitted - approximate_proxy
            state_signed = approximate_proxy - exact_proxy
            proxy_signed = exact_proxy - direct
            total_signed = fitted - direct
            closure = fit_signed + state_signed + proxy_signed - total_signed
            maximum_closure = max(maximum_closure, abs(closure))
            result.append(
                {
                    "system_id": system_id,
                    "formula_id": formula_id,
                    "state_id": state_id,
                    "sign": row["sign"],
                    "time_hartree_inverse": time_value,
                    "auxiliary_fit_a4": float(coefficients[0]),
                    "auxiliary_fit_a6": float(coefficients[1]),
                    "scaled_design_condition_number": condition_number,
                    "fhat_approx_hartree": fitted,
                    "g_approx_hartree": approximate_proxy,
                    "g_exact_hartree": exact_proxy,
                    "delta_direct_hartree": direct,
                    "E_fit_signed_hartree": fit_signed,
                    "E_state_signed_hartree": state_signed,
                    "E_proxy_signed_hartree": proxy_signed,
                    "E_total_signed_hartree": total_signed,
                    "closure_residual_hartree": closure,
                    "closure_over_target_error": abs(closure) / target_error,
                }
            )
    return result, maximum_closure


def formal_proxy_coefficients(
    groups: Sequence[np.ndarray],
    sequence: Sequence[float],
    hamiltonian: np.ndarray,
    states: dict[str, np.ndarray],
    decimal_digits: int,
) -> tuple[float, list[dict[str, Any]]]:
    steps = list(iter_s2_sequence_steps(len(groups), sequence))
    generators = [
        1j * float(weight) * np.asarray(groups[index], dtype=np.complex128)
        for index, weight in steps
    ]
    maximum_degree = 8
    unitary_series = ordered_exponential_product_series(
        generators, maximum_degree, decimal_digits=decimal_digits
    )
    exact_series = [np.eye(hamiltonian.shape[0], dtype=np.complex128)]
    generator = -1j * np.asarray(hamiltonian, dtype=np.complex128)
    for degree in range(1, maximum_degree + 1):
        exact_series.append(exact_series[-1] @ generator / degree)
    echo_series = []
    for degree in range(maximum_degree + 1):
        coefficient = np.zeros_like(hamiltonian, dtype=np.complex128)
        for left_degree in range(degree + 1):
            coefficient += (
                exact_series[left_degree]
                @ unitary_series[degree - left_degree]
            )
        echo_series.append(coefficient)
    rows: list[dict[str, Any]] = []
    maximum_lower_order = 0.0
    for state_id, state in states.items():
        for degree in range(1, maximum_degree + 1):
            proxy_power = degree - 1
            coefficient = float(
                np.imag(np.vdot(state, echo_series[degree] @ state))
            )
            rows.append(
                {
                    "state_id": state_id,
                    "proxy_power": proxy_power,
                    "coefficient": coefficient,
                }
            )
            if proxy_power < 4:
                maximum_lower_order = max(maximum_lower_order, abs(coefficient))
    return maximum_lower_order, rows


def _relative_hermiticity(matrix: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(matrix)), 1e-300)
    return float(np.linalg.norm(matrix - matrix.conj().T) / denominator)


def package_versions() -> dict[str, str]:
    return {
        name: importlib.metadata.version(name)
        for name in ("numpy", "scipy", "mpmath")
    }


def run(
    project_root: Path, protocol_path: Path, output_dir: Path
) -> dict[str, Any]:
    started = time.perf_counter()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    output_dir.mkdir(parents=True)
    protocol, protocol_hash = load_protocol(protocol_path)
    gates = protocol["numerical_gates"]
    experiment = protocol["experiment_A"]
    formulas = formula_registry(protocol)
    systems = two_level_systems()
    h2, h2_source = load_h2_system(project_root, protocol)
    systems["H2_stored"] = h2
    magnitudes = [
        float(value)
        for value in experiment["absolute_time_magnitudes_hartree_inverse"]
    ]
    signs = [int(value) for value in experiment["signs"]]
    digits = int(experiment["high_precision_decimal_digits"])
    target_error = float(protocol["constants"]["target_error_hartree"])
    degeneracy_gap = float(
        protocol["phase_and_branch_policy"]["degenerate_phase_gap_radians"]
    )

    observable_rows: list[dict[str, Any]] = []
    branch_rows: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []
    formula_rows: list[dict[str, Any]] = []
    extrema = {
        "high_precision": 0.0,
        "commuting_exact": 0.0,
        "time_reversal": 0.0,
        "unitarity": 0.0,
        "eigenpair": 0.0,
        "repeatability": 0.0,
        "forbidden_effective_order": 0.0,
        "low_proxy_order": 0.0,
        "state_normalization": 0.0,
        "ground_energy": 0.0,
        "hermiticity": 0.0,
        "group_sum": 0.0,
        "sequence_normalization": 0.0,
        "third_moment": 0.0,
        "palindrome": 0.0,
    }

    for formula in formulas:
        sequence = formula["sequence"]
        sequence_array = np.asarray(sequence, dtype=float)
        extrema["sequence_normalization"] = max(
            extrema["sequence_normalization"], abs(float(np.sum(sequence_array)) - 1.0)
        )
        extrema["third_moment"] = max(
            extrema["third_moment"], abs(float(np.sum(sequence_array**3)))
        )
        extrema["palindrome"] = max(
            extrema["palindrome"],
            float(np.max(np.abs(sequence_array - sequence_array[::-1]))),
        )
        formula_rows.append(
            {
                "formula_id": formula["formula_id"],
                "formal_order": formula["formal_order"],
                "s2_block_count": len(sequence),
                "sequence_sum_residual": float(np.sum(sequence_array) - 1.0),
                "third_moment_residual": float(np.sum(sequence_array**3)),
                "palindrome_max_absolute": float(
                    np.max(np.abs(sequence_array - sequence_array[::-1]))
                ),
                "provenance": formula["provenance"],
            }
        )
        for system_id, system in systems.items():
            groups = system["groups"]
            hamiltonian = system["hamiltonian"]
            states = system["states"]
            dimension = hamiltonian.shape[0]
            extrema["state_normalization"] = max(
                extrema["state_normalization"],
                *(abs(float(np.linalg.norm(state)) - 1.0) for state in states.values()),
            )
            extrema["ground_energy"] = max(
                extrema["ground_energy"],
                float(
                    np.linalg.norm(
                        hamiltonian @ system["ground_state"]
                        - system["energy"] * system["ground_state"]
                    )
                ),
            )
            extrema["hermiticity"] = max(
                extrema["hermiticity"],
                _relative_hermiticity(hamiltonian),
                *(_relative_hermiticity(group) for group in groups),
            )
            extrema["group_sum"] = max(
                extrema["group_sum"],
                float(
                    np.linalg.norm(
                        sum(groups, np.zeros_like(hamiltonian)) - hamiltonian
                    )
                ),
            )
            if system_id.startswith("two_level"):
                steps = list(iter_s2_sequence_steps(len(groups), sequence))
                effective = effective_hamiltonian_series(
                    groups,
                    steps,
                    maximum_effective_order=3,
                    decimal_digits=digits,
                )["effective_hamiltonian"]
                extrema["forbidden_effective_order"] = max(
                    extrema["forbidden_effective_order"],
                    *(float(np.linalg.norm(effective[order])) for order in (1, 2, 3)),
                )
                low_order, formal_rows = formal_proxy_coefficients(
                    groups, sequence, hamiltonian, states, digits
                )
                extrema["low_proxy_order"] = max(
                    extrema["low_proxy_order"], low_order
                )
                for row in formal_rows:
                    coefficient_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula["formula_id"],
                            **row,
                        }
                    )

            unitary_by_time: dict[float, np.ndarray] = {}
            for magnitude in magnitudes:
                positive = pf_unitary(groups, sequence, magnitude)
                negative = pf_unitary(groups, sequence, -magnitude)
                unitary_by_time[magnitude] = positive
                unitary_by_time[-magnitude] = negative
                extrema["time_reversal"] = max(
                    extrema["time_reversal"],
                    float(
                        np.linalg.norm(negative - positive.conj().T)
                        / max(np.linalg.norm(positive), 1e-300)
                    ),
                )
                extrema["unitarity"] = max(
                    extrema["unitarity"],
                    float(
                        np.linalg.norm(
                            positive.conj().T @ positive - np.eye(dimension)
                        )
                    ),
                )
                repeated = pf_unitary(groups, sequence, magnitude)
                extrema["repeatability"] = max(
                    extrema["repeatability"],
                    float(np.linalg.norm(repeated - positive)),
                )
                if system_id.startswith("two_level"):
                    high_precision = pf_unitary_high_precision(
                        groups, sequence, magnitude, digits
                    )
                    extrema["high_precision"] = max(
                        extrema["high_precision"],
                        float(np.max(np.abs(high_precision - positive))),
                    )
                    if system["commuting"]:
                        exact = expm(1j * magnitude * hamiltonian)
                        extrema["commuting_exact"] = max(
                            extrema["commuting_exact"],
                            float(np.max(np.abs(positive - exact))),
                        )

            for sign in signs:
                signed_times = [float(sign) * value for value in magnitudes]
                unitaries = [unitary_by_time[value] for value in signed_times]
                direct_rows = track_direct_branch(
                    unitaries,
                    signed_times,
                    system["ground_state"],
                    system["energy"],
                    degeneracy_gap,
                )
                proxy_previous = {state_id: 0.0 for state_id in states}
                for magnitude, signed_time, unitary, direct in zip(
                    magnitudes,
                    signed_times,
                    unitaries,
                    direct_rows,
                    strict=True,
                ):
                    extrema["eigenpair"] = max(
                        extrema["eigenpair"],
                        float(direct["eigenpair_residual_2_norm"]),
                    )
                    branch_rows.append(
                        {
                            "system_id": system_id,
                            "formula_id": formula["formula_id"],
                            "sign": sign,
                            "absolute_time": magnitude,
                            "time_hartree_inverse": signed_time,
                            **direct,
                        }
                    )
                    unitarity = float(
                        np.linalg.norm(
                            unitary.conj().T @ unitary - np.eye(dimension)
                        )
                    )
                    for state_id, state in states.items():
                        proxy, proxy_previous[state_id] = echo_proxies(
                            hamiltonian,
                            unitary,
                            state,
                            signed_time,
                            proxy_previous[state_id],
                        )
                        observable_rows.append(
                            {
                                "system_id": system_id,
                                "formula_id": formula["formula_id"],
                                "state_id": state_id,
                                "sign": sign,
                                "absolute_time": magnitude,
                                "time_hartree_inverse": signed_time,
                                **proxy,
                                "direct_shift_hartree": direct[
                                    "direct_shift_hartree"
                                ],
                                "unitarity_residual_frobenius": unitarity,
                            }
                        )

    decomposition, maximum_closure = build_decomposition_rows(
        observable_rows, target_error
    )
    paired_direct: dict[tuple[str, str, float], dict[int, float]] = {}
    for row in branch_rows:
        key = (row["system_id"], row["formula_id"], row["absolute_time"])
        paired_direct.setdefault(key, {})[row["sign"]] = float(
            row["direct_shift_hartree"]
        )
    maximum_direct_parity = max(
        abs(values[1] - values[-1]) for values in paired_direct.values()
    )
    coefficient_gate = float(gates["high_precision_two_level_absolute"])
    checks = [
        ("source_state_normalization", extrema["state_normalization"], float(gates["state_normalization_absolute"])),
        ("source_ground_energy", extrema["ground_energy"], float(gates["stored_ground_energy_reproduction_hartree"])),
        ("source_hermiticity", extrema["hermiticity"], float(gates["hamiltonian_relative_hermiticity"])),
        ("source_group_sum", extrema["group_sum"], float(gates["group_sum_frobenius"])),
        ("sequence_normalization", extrema["sequence_normalization"], coefficient_gate),
        ("sequence_third_moment", extrema["third_moment"], coefficient_gate),
        ("sequence_palindrome", extrema["palindrome"], coefficient_gate),
        ("high_precision_two_level", extrema["high_precision"], coefficient_gate),
        ("commuting_exact_control", extrema["commuting_exact"], coefficient_gate),
        ("time_reversal", extrema["time_reversal"], float(gates["U_minus_t_minus_U_t_dagger_relative_frobenius"])),
        ("unitarity", extrema["unitarity"], float(gates["pf_unitarity_frobenius"])),
        ("eigenpair_residual", extrema["eigenpair"], float(gates["direct_eigenpair_residual_2_norm"])),
        ("three_way_closure", maximum_closure, max(1e-12, 1e-8 * target_error)),
        ("direct_shift_even_parity", maximum_direct_parity, coefficient_gate),
        ("proxy_no_power_below_four", extrema["low_proxy_order"], coefficient_gate),
        ("stored_coefficient_precision_no_lower_order", extrema["forbidden_effective_order"], coefficient_gate),
        ("cold_repeatability", extrema["repeatability"], coefficient_gate),
    ]
    check_rows = [
        {
            "check_id": check_id,
            "measured": measured,
            "threshold": threshold,
            "passed": bool(measured <= threshold),
        }
        for check_id, measured, threshold in checks
    ]
    passed = all(row["passed"] for row in check_rows)
    source_manifest = {
        "protocol_path": str(protocol_path.relative_to(project_root)),
        "protocol_sha256": protocol_hash,
        "protocol_freeze_commit": "d3fadde",
        "h2_source": h2_source,
        "source_identity_passed": True,
        "new_molecular_hamiltonian_count": 0,
    }
    atomic_json(output_dir / "source_manifest.json", source_manifest)
    write_csv(output_dir / "formula_registry.csv", formula_rows)
    write_csv(output_dir / "observables.csv", observable_rows)
    write_csv(output_dir / "error_decomposition.csv", decomposition)
    write_csv(output_dir / "branch_audit.csv", branch_rows)
    write_csv(output_dir / "formal_proxy_coefficients.csv", coefficient_rows)
    write_csv(output_dir / "validation_checks.csv", check_rows)
    audit = {
        "status": (
            "complete_validation" if passed else "failed_numerical_validation"
        ),
        "passed": passed,
        "scope": {
            "experiment": "A",
            "scientific_generality_result": False,
            "system_count": len(systems),
            "formula_count": len(formulas),
            "observable_row_count": len(observable_rows),
            "branch_row_count": len(branch_rows),
            "decomposition_row_count": len(decomposition),
        },
        "checks": check_rows,
        "source_manifest": source_manifest,
        "notes": {
            "auxiliary_fit": (
                "closure-only OLS t^4+t^6 fit over all six positive fixed "
                "times; not a scientific model comparison"
            ),
            "branch_policy": (
                "positive and negative branches independently continued from "
                "the exact ground state at zero"
            ),
            "high_precision_scope": (
                "all four formulas, both fixed two-level controls, and all six "
                "positive magnitudes"
            ),
        },
    }
    atomic_json(output_dir / "audit.json", audit)
    elapsed = time.perf_counter() - started
    report = [
        "# First-study Experiment A validation",
        "",
        f"Status: **{audit['status']}**",
        "",
        "This is an implementation validation, not evidence of molecular generality.",
        "",
        "| gate | measured | threshold | pass |",
        "|---|---:|---:|:---:|",
    ]
    for row in check_rows:
        report.append(
            f"| {row['check_id']} | {row['measured']:.6e} | "
            f"{row['threshold']:.6e} | {'yes' if row['passed'] else 'no'} |"
        )
    report.extend(
        [
            "",
            "The commuting control, complex128/80-digit comparison, signed-time branch tracking, formal low-order cancellation, and three-way closure were evaluated before Experiment B/C.",
            "",
            f"Elapsed wall time: {elapsed:.3f} s. Peak RSS: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss} KiB.",
        ]
    )
    (output_dir / "report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    artifact_names = [
        "source_manifest.json",
        "formula_registry.csv",
        "observables.csv",
        "error_decomposition.csv",
        "branch_audit.csv",
        "formal_proxy_coefficients.csv",
        "validation_checks.csv",
        "audit.json",
        "report.md",
    ]
    manifest = {
        "status": audit["status"],
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_commit_at_execution": git_output(project_root, "rev-parse", "HEAD"),
        "project_status_at_execution": git_output(project_root, "status", "--short"),
        "protocol_sha256": protocol_hash,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(),
        },
        "timing": {
            "elapsed_wall_seconds": elapsed,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "artifact_sha256": {
            name: sha256_file(output_dir / name) for name in artifact_names
        },
    }
    atomic_json(output_dir / "manifest.json", manifest)
    if passed:
        (output_dir / "COMPLETE").write_text(
            "Experiment A numerical validation passed.\n", encoding="utf-8"
        )
    return audit
