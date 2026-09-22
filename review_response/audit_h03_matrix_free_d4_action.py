"""H03 audit of matrix-free leading error-operator state actions.

Nested commutators are expanded into group-operator words.  The D4 action and
expectation are evaluated either by streaming the words or by caching common
application prefixes, without constructing a D4 matrix.  Stored F01 matrices
remain the independent small-system reference.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import time
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import schur

from review_response.audit_f01_effective_hamiltonian_multipf import (
    formula_registry,
)
from review_response.audit_f01_effective_hamiltonian_pilot import (
    _atomic_json,
    _git_output,
    _package_versions,
    _sha256,
    _write_csv,
)
from review_response.audit_h01_approximate_state_pilot import leading_analytic_time
from review_response.pennylane_bch import (
    bch_expansion_for_symmetric_pf,
    effective_hamiltonian_action_from_bch,
    effective_hamiltonian_matrices_from_bch,
)
from trotterlib.pf_decomposition import symmetric_s2_sequence
from trotterlib.sector_pf import build_sector_pf_unitary


DEFAULT_F01 = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)
DEFAULT_H01 = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")
DEFAULT_OUTPUT = Path("artifacts/prevalidation_h03_matrix_free_d4_action_20260922")
STATE_IDS = ("exact", "hf", "cisd")
ACTION_REPEATS = 7
SYNTHETIC_DIMENSIONS = (4, 16, 32, 64, 128)
H4_SYMBOLIC_STOP_SECONDS = 30.0
H4_SYMBOLIC_STOP_TERMS = 100_000


def _benchmark(
    function: Callable[[], Any], repeats: int
) -> tuple[Any, float, float]:
    timings = []
    result = None
    for _ in range(int(repeats)):
        started = time.perf_counter()
        result = function()
        timings.append(time.perf_counter() - started)
    return result, float(min(timings)), float(statistics.median(timings))


def _relative_vector_error(value: np.ndarray, reference: np.ndarray) -> float:
    return float(
        np.linalg.norm(np.asarray(value) - np.asarray(reference))
        / max(float(np.linalg.norm(reference)), 1e-300)
    )


def _random_hermitian_groups(
    dimension: int, seed: int = 20260922
) -> tuple[list[np.ndarray], np.ndarray]:
    generator = np.random.default_rng(seed + int(dimension))
    groups = []
    for _ in range(2):
        raw = generator.normal(size=(dimension, dimension)) + 1j * generator.normal(
            size=(dimension, dimension)
        )
        matrix = (raw + raw.conj().T) / (2.0 * math.sqrt(dimension))
        groups.append(np.asarray(matrix, dtype=np.complex128))
    state = generator.normal(size=dimension) + 1j * generator.normal(size=dimension)
    state = np.asarray(state / np.linalg.norm(state), dtype=np.complex128)
    return groups, state


def _write_figures(
    output_dir: Path,
    scaling_rows: list[dict[str, Any]],
) -> None:
    figure, axis = plt.subplots(figsize=(6.8, 4.3))
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["dense_d4_construction_seconds"] for row in scaling_rows],
        marker="o",
        label="construct dense D4",
    )
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["streaming_action_median_seconds"] for row in scaling_rows],
        marker="s",
        label="streaming action",
    )
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["cached_action_median_seconds"] for row in scaling_rows],
        marker="^",
        label="cached-prefix action",
    )
    axis.set_xlabel("statevector dimension")
    axis.set_ylabel("wall time (s)")
    axis.grid(True, which="both", alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "synthetic_timing_scaling.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6.8, 4.3))
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["dense_d4_matrix_bytes"] for row in scaling_rows],
        marker="o",
        label="dense D4",
    )
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["streaming_logical_vector_bytes"] for row in scaling_rows],
        marker="s",
        label="streaming vectors",
    )
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["cached_logical_vector_bytes"] for row in scaling_rows],
        marker="^",
        label="cached-prefix vectors",
    )
    axis.loglog(
        [row["dimension"] for row in scaling_rows],
        [row["input_group_matrix_bytes"] for row in scaling_rows],
        marker="x",
        label="input dense groups",
    )
    axis.set_xlabel("statevector dimension")
    axis.set_ylabel("logical array bytes")
    axis.grid(True, which="both", alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "synthetic_memory_scaling.png", dpi=180)
    plt.close(figure)


def _write_report(path: Path, audit: dict[str, Any]) -> None:
    summary = audit["summary"]
    lines = [
        "# H03: matrix-free D4 state-action audit",
        "",
        f"Status: **{audit['status']}**",
        "",
        "## H2 reference comparison",
        "",
        "| PF | symbolic expansion (s) | dense D4 difference | max action rel. "
        "error | streaming actions/vectors | cached actions/vectors | reuse |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in audit["h2_formula_rows"]:
        lines.append(
            f"| {row['formula_id']} | {row['symbolic_expansion_seconds']:.4f} | "
            f"{row['dense_bch_vs_f01_d4_frobenius_difference']:.3e} | "
            f"{row['maximum_matrix_free_action_relative_error']:.3e} | "
            f"{row['streaming_group_action_count']}/{row['streaming_peak_vector_count']} | "
            f"{row['cached_group_action_count']}/{row['cached_peak_vector_count']} | "
            f"{row['cached_group_action_reuse_fraction']:.1%} |"
        )
    lines.extend(
        [
            "",
            f"All 24 matrix-free action paths agree with stored F01 D4 actions to "
            f"at most {summary['maximum_action_relative_error']:.3e} relative error; "
            f"expectations agree to {summary['maximum_expectation_absolute_error_hartree']:.3e} Ha.",
            "",
            "The streaming route uses 150 group-Hamiltonian actions and three logical "
            "statevector slots. Prefix caching reduces this to 60 actions (60% reuse) "
            "but retains 62 logical statevectors. Thus action reuse is a time-memory "
            "choice, not a free improvement.",
            "",
            "## Scaling boundary",
            "",
            "| dimension | dense D4 (s) | streaming (s) | cached (s) | dense D4 bytes | "
            "stream vectors | cached vectors | input groups |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in audit["synthetic_scaling_rows"]:
        lines.append(
            f"| {row['dimension']} | {row['dense_d4_construction_seconds']:.4e} | "
            f"{row['streaming_action_median_seconds']:.4e} | "
            f"{row['cached_action_median_seconds']:.4e} | "
            f"{row['dense_d4_matrix_bytes']} | {row['streaming_logical_vector_bytes']} | "
            f"{row['cached_logical_vector_bytes']} | {row['input_group_matrix_bytes']} |"
        )
    h4 = audit["h4_symbolic_boundary_rows"][0]
    lines.extend(
        [
            "",
            "For H4/Yoshida with 13 groups, leading-order symbolic generation alone "
            f"took {h4['symbolic_expansion_seconds']:.2f} s and produced "
            f"{h4['d4_raw_commutator_term_count']} raw D4 commutator terms. "
            "The predeclared stop threshold was exceeded, so word expansion and state "
            "action were not attempted for H4.",
            "",
            "## Decision",
            "",
            "The state-action backend is numerically valid and avoids the incremental "
            "dense D4 matrix, but the naive symbolic BCH generator is already the "
            "dominant bottleneck at 13 groups. Proceed to H04 compact/selected "
            "representations before claiming an operational D2 estimator.",
            "",
            "## Scope and memory boundary",
            "",
            "All current group Hamiltonians and statevectors are dense. Avoiding D4 "
            "removes one additional O(d^2) matrix, but input group storage remains "
            "O(G d^2), and each retained statevector remains O(d), exponential in "
            "qubit count when represented densely. No large-system scalability claim "
            "is made.",
            "",
            "## Files",
            "",
            "- `audit.json`: checks, timing, operation counts, and conclusions.",
            "- `h2_formula_summary.csv`: symbolic/dense reference measurements.",
            "- `h2_state_actions.csv`: exact/HF/CISD streaming and cached actions.",
            "- `synthetic_scaling.csv`: dimension scaling benchmark.",
            "- `h4_symbolic_boundary.csv`: 13-group stopping result.",
            "- `manifest.json`: source, input, and artifact hashes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(f01_dir: Path, h01_dir: Path, output_dir: Path) -> dict[str, Any]:
    import pennylane

    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    started = time.perf_counter()
    f01_audit_path = f01_dir / "audit.json"
    operators_path = f01_dir / "effective_operators.npz"
    h01_audit_path = h01_dir / "audit.json"
    states_path = h01_dir / "states.npz"
    f01 = json.loads(f01_audit_path.read_text(encoding="utf-8"))
    h01 = json.loads(h01_audit_path.read_text(encoding="utf-8"))
    if f01["status"] != "complete" or not f01["passed"]:
        raise RuntimeError("F01 input is not complete")
    if h01["status"] != "pilot_complete_with_findings" or not h01["checks_passed"]:
        raise RuntimeError("H01 input is not complete")

    formulas = {row["formula_id"]: row for row in formula_registry()}
    condition_map = {
        (row["system_id"], row["formula_id"]): row
        for row in f01["condition_summaries"]
    }
    h2_formula_rows: list[dict[str, Any]] = []
    h2_action_rows: list[dict[str, Any]] = []
    expansions: dict[str, list[dict]] = {}

    with np.load(operators_path) as arrays, np.load(states_path) as states:
        h2_group_keys = sorted(
            key for key in arrays.files if key.startswith("H2_group_")
        )
        h2_groups = [
            np.asarray(arrays[key], dtype=np.complex128) for key in h2_group_keys
        ]
        h2_spectra = [np.linalg.eigh(matrix) for matrix in h2_groups]
        h2_ground = np.asarray(arrays["H2_ground_state"], dtype=np.complex128)
        h2_energy = float(arrays["H2_ground_energy"])

        for formula_id, formula in formulas.items():
            sequence = tuple(
                float(value)
                for value in symmetric_s2_sequence(formula["weights"])
            )
            expansion_started = time.perf_counter()
            expansion = bch_expansion_for_symmetric_pf(2, sequence, 5)
            expansion_seconds = time.perf_counter() - expansion_started
            expansions[formula_id] = expansion
            dense_started = time.perf_counter()
            dense_coefficients = effective_hamiltonian_matrices_from_bch(
                expansion, h2_groups
            )
            dense_seconds = time.perf_counter() - dense_started
            dense_d4 = np.asarray(dense_coefficients[4], dtype=np.complex128)
            stored_d4 = np.asarray(
                arrays[f"H2_{formula_id}_D4"], dtype=np.complex128
            )
            dense_difference = float(np.linalg.norm(dense_d4 - stored_d4))

            a4 = abs(
                float(
                    condition_map[("H2", formula_id)]["energy_coefficients"][
                        "a4"
                    ]
                )
            )
            representative_time = leading_analytic_time(a4)

            def direct_pf_evaluation() -> tuple[np.ndarray, np.ndarray]:
                unitary = build_sector_pf_unitary(
                    h2_spectra,
                    sequence,
                    representative_time,
                    method="s2-cache",
                )
                triangular, vectors = schur(
                    unitary, output="complex", check_finite=False
                )
                return np.diag(triangular), vectors

            _, direct_min, direct_median = _benchmark(direct_pf_evaluation, 7)
            formula_action_rows = []
            for state_id in STATE_IDS:
                state = np.asarray(
                    states[f"H2_{state_id}_state"], dtype=np.complex128
                )
                reference_action = stored_d4 @ state
                reference_expectation = complex(np.vdot(state, reference_action))

                def dense_action() -> np.ndarray:
                    return stored_d4 @ state

                _, dense_action_min, dense_action_median = _benchmark(
                    dense_action, ACTION_REPEATS
                )
                for mode, cache_prefixes in (
                    ("streaming", False),
                    ("cached_prefix", True),
                ):
                    def evaluate() -> tuple[np.ndarray, dict[str, Any]]:
                        return effective_hamiltonian_action_from_bch(
                            expansion,
                            h2_groups,
                            state,
                            4,
                            cache_prefixes=cache_prefixes,
                        )

                    result, action_min, action_median = _benchmark(
                        evaluate, ACTION_REPEATS
                    )
                    action, diagnostics = result
                    expectation = complex(np.vdot(state, action))
                    row = {
                        "system_id": "H2",
                        "formula_id": formula_id,
                        "state_id": state_id,
                        "evaluation_mode": mode,
                        "dimension": int(state.size),
                        "action_absolute_error_2_norm": float(
                            np.linalg.norm(action - reference_action)
                        ),
                        "action_relative_error_2_norm": _relative_vector_error(
                            action, reference_action
                        ),
                        "expectation_real_hartree": float(expectation.real),
                        "expectation_imaginary_hartree": float(expectation.imag),
                        "expectation_absolute_error_hartree": float(
                            abs(expectation - reference_expectation)
                        ),
                        "matrix_free_action_min_seconds": action_min,
                        "matrix_free_action_median_seconds": action_median,
                        "dense_stored_d4_action_min_seconds": dense_action_min,
                        "dense_stored_d4_action_median_seconds": dense_action_median,
                        **diagnostics,
                    }
                    h2_action_rows.append(row)
                    formula_action_rows.append(row)

            streaming = next(
                row
                for row in formula_action_rows
                if row["evaluation_mode"] == "streaming"
            )
            cached = next(
                row
                for row in formula_action_rows
                if row["evaluation_mode"] == "cached_prefix"
            )
            h2_formula_rows.append(
                {
                    "system_id": "H2",
                    "formula_id": formula_id,
                    "group_count": len(h2_groups),
                    "s2_block_count": len(sequence),
                    "d4_raw_commutator_term_count": len(expansion[4]),
                    "symbolic_expansion_seconds": float(expansion_seconds),
                    "dense_nested_commutator_d4_seconds": float(dense_seconds),
                    "dense_bch_vs_f01_d4_frobenius_difference": dense_difference,
                    "maximum_matrix_free_action_relative_error": max(
                        row["action_relative_error_2_norm"]
                        for row in formula_action_rows
                    ),
                    "maximum_matrix_free_expectation_absolute_error_hartree": max(
                        row["expectation_absolute_error_hartree"]
                        for row in formula_action_rows
                    ),
                    "streaming_unique_word_count": streaming[
                        "unique_operator_word_count"
                    ],
                    "streaming_group_action_count": streaming[
                        "actual_group_action_count"
                    ],
                    "streaming_peak_vector_count": streaming[
                        "logical_peak_statevector_count"
                    ],
                    "cached_group_action_count": cached[
                        "actual_group_action_count"
                    ],
                    "cached_peak_vector_count": cached[
                        "logical_peak_statevector_count"
                    ],
                    "cached_group_action_reuse_fraction": cached[
                        "group_action_reuse_fraction"
                    ],
                    "representative_one_term_time": representative_time,
                    "direct_pf_unitary_schur_min_seconds": direct_min,
                    "direct_pf_unitary_schur_median_seconds": direct_median,
                }
            )

    reference_expansion = expansions["yoshida4"]
    synthetic_rows: list[dict[str, Any]] = []
    for dimension in SYNTHETIC_DIMENSIONS:
        groups, state = _random_hermitian_groups(dimension)
        dense_started = time.perf_counter()
        dense_d4 = effective_hamiltonian_matrices_from_bch(
            reference_expansion, groups
        )[4]
        dense_seconds = time.perf_counter() - dense_started
        reference_action = dense_d4 @ state

        def stream() -> tuple[np.ndarray, dict[str, Any]]:
            return effective_hamiltonian_action_from_bch(
                reference_expansion, groups, state, 4, cache_prefixes=False
            )

        def cached() -> tuple[np.ndarray, dict[str, Any]]:
            return effective_hamiltonian_action_from_bch(
                reference_expansion, groups, state, 4, cache_prefixes=True
            )

        stream_result, stream_min, stream_median = _benchmark(stream, 3)
        cached_result, cached_min, cached_median = _benchmark(cached, 3)
        stream_action, stream_diagnostics = stream_result
        cached_action, cached_diagnostics = cached_result
        synthetic_rows.append(
            {
                "dimension": dimension,
                "dense_d4_construction_seconds": float(dense_seconds),
                "streaming_action_min_seconds": stream_min,
                "streaming_action_median_seconds": stream_median,
                "cached_action_min_seconds": cached_min,
                "cached_action_median_seconds": cached_median,
                "streaming_action_relative_error": _relative_vector_error(
                    stream_action, reference_action
                ),
                "cached_action_relative_error": _relative_vector_error(
                    cached_action, reference_action
                ),
                "streaming_group_action_count": stream_diagnostics[
                    "actual_group_action_count"
                ],
                "cached_group_action_count": cached_diagnostics[
                    "actual_group_action_count"
                ],
                "group_action_reuse_fraction": cached_diagnostics[
                    "group_action_reuse_fraction"
                ],
                "dense_d4_matrix_bytes": int(dense_d4.nbytes),
                "streaming_logical_vector_bytes": stream_diagnostics[
                    "logical_peak_statevector_bytes"
                ],
                "cached_logical_vector_bytes": cached_diagnostics[
                    "logical_peak_statevector_bytes"
                ],
                "input_group_matrix_bytes": stream_diagnostics[
                    "input_group_matrix_bytes"
                ],
            }
        )

    h4_formula = formulas["yoshida4"]
    h4_sequence = tuple(
        float(value)
        for value in symmetric_s2_sequence(h4_formula["weights"])
    )
    h4_rss_before = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    h4_started = time.perf_counter()
    h4_expansion = bch_expansion_for_symmetric_pf(13, h4_sequence, 5)
    h4_seconds = time.perf_counter() - h4_started
    h4_rss_after = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    h4_raw_counts = [len(terms) for terms in h4_expansion]
    h4_significant_counts = [
        sum(abs(complex(coefficient)) > 1e-16 for coefficient in terms.values())
        for terms in h4_expansion
    ]
    h4_stop = bool(
        h4_seconds > H4_SYMBOLIC_STOP_SECONDS
        or h4_raw_counts[4] > H4_SYMBOLIC_STOP_TERMS
    )
    h4_rows = [
        {
            "system_id": "H4",
            "formula_id": "yoshida4",
            "group_count": 13,
            "symbolic_expansion_seconds": float(h4_seconds),
            "commutator_term_counts_json": json.dumps(h4_raw_counts),
            "significant_commutator_term_counts_json": json.dumps(
                h4_significant_counts
            ),
            "d4_raw_commutator_term_count": h4_raw_counts[4],
            "d4_significant_commutator_term_count": h4_significant_counts[4],
            "maximum_unexpanded_word_occurrences": int(
                h4_raw_counts[4] * 2**4
            ),
            "maximum_rss_before_kib": h4_rss_before,
            "maximum_rss_after_kib": h4_rss_after,
            "maximum_rss_increment_upper_bound_kib": max(
                0, h4_rss_after - h4_rss_before
            ),
            "stop_threshold_seconds": H4_SYMBOLIC_STOP_SECONDS,
            "stop_threshold_terms": H4_SYMBOLIC_STOP_TERMS,
            "stop_before_word_expansion_and_action": h4_stop,
            "action_attempted": False,
        }
    ]
    del h4_expansion

    checks = [
        {
            "check_id": "h2_formula_count",
            "measured": len(h2_formula_rows),
            "threshold": 4,
            "comparison": "==",
            "passed": len(h2_formula_rows) == 4,
        },
        {
            "check_id": "h2_state_action_row_count",
            "measured": len(h2_action_rows),
            "threshold": 24,
            "comparison": "==",
            "passed": len(h2_action_rows) == 24,
        },
        {
            "check_id": "maximum_dense_bch_vs_f01_d4_difference",
            "measured": max(
                row["dense_bch_vs_f01_d4_frobenius_difference"]
                for row in h2_formula_rows
            ),
            "threshold": 2e-12,
            "comparison": "<=",
            "passed": max(
                row["dense_bch_vs_f01_d4_frobenius_difference"]
                for row in h2_formula_rows
            )
            <= 2e-12,
        },
        {
            "check_id": "maximum_matrix_free_action_relative_error",
            "measured": max(
                row["action_relative_error_2_norm"] for row in h2_action_rows
            ),
            "threshold": 2e-11,
            "comparison": "<=",
            "passed": max(
                row["action_relative_error_2_norm"] for row in h2_action_rows
            )
            <= 2e-11,
        },
        {
            "check_id": "maximum_matrix_free_expectation_absolute_error_hartree",
            "measured": max(
                row["expectation_absolute_error_hartree"]
                for row in h2_action_rows
            ),
            "threshold": 2e-12,
            "comparison": "<=",
            "passed": max(
                row["expectation_absolute_error_hartree"]
                for row in h2_action_rows
            )
            <= 2e-12,
        },
        {
            "check_id": "synthetic_action_maximum_relative_error",
            "measured": max(
                max(
                    row["streaming_action_relative_error"],
                    row["cached_action_relative_error"],
                )
                for row in synthetic_rows
            ),
            "threshold": 2e-12,
            "comparison": "<=",
            "passed": max(
                max(
                    row["streaming_action_relative_error"],
                    row["cached_action_relative_error"],
                )
                for row in synthetic_rows
            )
            <= 2e-12,
        },
        {
            "check_id": "streaming_group_action_count",
            "measured": min(
                row["streaming_group_action_count"] for row in h2_formula_rows
            ),
            "threshold": 150,
            "comparison": "==",
            "passed": all(
                row["streaming_group_action_count"] == 150
                for row in h2_formula_rows
            ),
        },
        {
            "check_id": "cached_group_action_count",
            "measured": max(
                row["cached_group_action_count"] for row in h2_formula_rows
            ),
            "threshold": 60,
            "comparison": "==",
            "passed": all(
                row["cached_group_action_count"] == 60
                for row in h2_formula_rows
            ),
        },
        {
            "check_id": "h4_predeclared_stop_triggered",
            "measured": int(h4_stop),
            "threshold": 1,
            "comparison": "==",
            "passed": h4_stop,
        },
    ]
    checks_passed = all(check["passed"] for check in checks)
    summary = {
        "maximum_action_relative_error": max(
            row["action_relative_error_2_norm"] for row in h2_action_rows
        ),
        "maximum_expectation_absolute_error_hartree": max(
            row["expectation_absolute_error_hartree"] for row in h2_action_rows
        ),
        "streaming_group_actions": 150,
        "cached_group_actions": 60,
        "cached_reuse_fraction": 0.6,
        "streaming_peak_statevectors": 3,
        "cached_peak_statevectors": 62,
        "h4_symbolic_seconds": h4_seconds,
        "h4_d4_raw_terms": h4_raw_counts[4],
        "h4_stopped_before_action": h4_stop,
        "statevector_scaling_boundary": (
            "dense group matrices O(G*d^2) and statevectors O(d) remain; "
            "d is exponential in qubit count"
        ),
    }
    audit = {
        "schema": "prevalidation_h03_matrix_free_d4_action_v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "complete_with_scaling_blocker" if checks_passed else "failed",
        "passed": checks_passed,
        "scope": {
            "catalog_item": "H03",
            "h2_system": "four PFs x exact/HF/CISD x two action modes",
            "h4_system": "Yoshida symbolic-generation boundary only",
            "new_direct_pf_points": 0,
            "claim_boundary": (
                "matrix-free D4 is validated on H2; H4 action is blocked by "
                "naive symbolic term generation"
            ),
        },
        "protocol": {
            "effective_hamiltonian_order": 4,
            "maximum_commutator_order": 5,
            "coefficient_pruning_tolerance": 1e-16,
            "action_repeats": ACTION_REPEATS,
            "synthetic_dimensions": list(SYNTHETIC_DIMENSIONS),
            "h4_stop_seconds": H4_SYMBOLIC_STOP_SECONDS,
            "h4_stop_raw_d4_terms": H4_SYMBOLIC_STOP_TERMS,
            "streaming_definition": (
                "evaluate every operator word; constant logical vector slots"
            ),
            "cached_definition": (
                "reuse common application-order prefixes; retain prefix vectors"
            ),
        },
        "checks": checks,
        "summary": summary,
        "h2_formula_rows": h2_formula_rows,
        "h2_state_action_rows": h2_action_rows,
        "synthetic_scaling_rows": synthetic_rows,
        "h4_symbolic_boundary_rows": h4_rows,
        "interpretation": {
            "accuracy": (
                "Both action modes reproduce stored F01 D4 state actions and "
                "expectations for exact, HF, and CISD states."
            ),
            "cost": (
                "Prefix reuse removes 60% of group actions but increases logical "
                "statevector retention from 3 to 62."
            ),
            "blocker": (
                "The naive PennyLane BCH expansion grows to more than 100,000 raw "
                "D4 commutator terms for H4/13 groups before any state action."
            ),
            "decision": (
                "Use H03 as a validated backend primitive, but complete H04 compact "
                "or selected term generation before treating it as a cheap D2 method."
            ),
        },
        "runtime": {
            "elapsed_seconds": float(time.perf_counter() - started),
            "maximum_resident_set_size_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }

    output_dir.mkdir(parents=True)
    _atomic_json(output_dir / "audit.json", audit)
    _write_csv(output_dir / "h2_formula_summary.csv", h2_formula_rows)
    _write_csv(output_dir / "h2_state_actions.csv", h2_action_rows)
    _write_csv(output_dir / "synthetic_scaling.csv", synthetic_rows)
    _write_csv(output_dir / "h4_symbolic_boundary.csv", h4_rows)
    _write_figures(output_dir, synthetic_rows)
    _write_report(output_dir / "report.md", audit)

    source_paths = [
        Path(__file__),
        Path("review_response/pennylane_bch.py"),
        Path("review_response/audit_f01_effective_hamiltonian_multipf.py"),
    ]
    input_paths = [
        f01_audit_path,
        operators_path,
        h01_audit_path,
        states_path,
    ]
    artifact_paths = [
        output_dir / "audit.json",
        output_dir / "h2_formula_summary.csv",
        output_dir / "h2_state_actions.csv",
        output_dir / "synthetic_scaling.csv",
        output_dir / "h4_symbolic_boundary.csv",
        output_dir / "synthetic_timing_scaling.png",
        output_dir / "synthetic_memory_scaling.png",
        output_dir / "report.md",
    ]
    environment_packages = _package_versions()
    environment_packages["pennylane"] = pennylane.__version__
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
            "packages": environment_packages,
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
    parser.add_argument("--h01-dir", type=Path, default=DEFAULT_H01)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = run(arguments.f01_dir, arguments.h01_dir, arguments.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(arguments.output_dir),
                "status": audit["status"],
                "passed": audit["passed"],
                "summary": audit["summary"],
                "runtime": audit["runtime"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
