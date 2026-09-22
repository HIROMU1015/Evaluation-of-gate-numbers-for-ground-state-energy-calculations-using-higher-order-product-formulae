from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_f01_effective_hamiltonian_multipf import formula_registry
from review_response.bch_matrix_series import effective_hamiltonian_series_numpy
from review_response.compact_bch import (
    compact_composed_d4_terms,
    compact_s2_base_terms,
    evaluate_grouped_terms,
    summed_components,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps, symmetric_s2_sequence


ARTIFACT = Path(
    "artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _random_hermitian_groups(
    count: int, dimension: int = 5, seed: int = 20260922
) -> tuple[list[np.ndarray], np.ndarray]:
    generator = np.random.default_rng(seed + count)
    groups = []
    for _ in range(count):
        raw = generator.normal(size=(dimension, dimension)) + 1j * generator.normal(
            size=(dimension, dimension)
        )
        groups.append((raw + raw.conj().T) / (2.0 * np.sqrt(dimension)))
    state = generator.normal(size=dimension) + 1j * generator.normal(size=dimension)
    state = state / np.linalg.norm(state)
    return groups, np.asarray(state, dtype=np.complex128)


def test_h04_compact_grouped_action_matches_ordered_product_series() -> None:
    groups, state = _random_hermitian_groups(3)
    for formula in formula_registry():
        sequence = symmetric_s2_sequence(formula["weights"])
        terms, diagnostics = compact_composed_d4_terms(len(groups), sequence)
        actions, _, _, _ = evaluate_grouped_terms(terms, groups, state)
        compact_action = summed_components(actions, range(len(actions)))
        steps = list(iter_s2_sequence_steps(len(groups), sequence))
        dense_d4 = effective_hamiltonian_series_numpy(
            groups, steps, maximum_effective_order=4
        )["effective_hamiltonian"][4]
        reference = dense_d4 @ state
        np.testing.assert_allclose(compact_action, reference, atol=2e-12, rtol=2e-10)
        assert abs(diagnostics["first_order_x"] - 1.0) < 2e-13
        assert diagnostics["third_order_l1"] < 2e-13
        assert diagnostics["fifth_order_model_residual_l1"] < 2e-13


def test_h04_grouped_term_counts_follow_linear_quadratic_formulas() -> None:
    for fragment_count in (1, 2, 5, 13):
        y3_terms, y5_terms, _ = compact_s2_base_terms(fragment_count)
        assert len(y3_terms) == 2 * (fragment_count - 1)
        assert len(y5_terms) == 3 * (fragment_count - 1) ** 2


def test_h04_artifact_validates_full_actions_and_records_pruning_findings() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_findings"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "H04"
    assert audit["scope"]["new_direct_pf_points"] == 0
    assert all(check["passed"] for check in audit["checks"])
    assert len(audit["method_rows"]) == 8
    assert len(audit["state_action_rows"]) == 24
    assert len(audit["pruning_rows"]) == 180
    assert len(audit["selection_rows"]) == 90
    assert audit["summary"]["maximum_full_action_relative_error"] < 2e-11
    assert audit["summary"]["maximum_expectation_absolute_error_hartree"] < 3e-15
    assert audit["summary"]["h4_grouped_term_count"] == 456
    assert audit["summary"]["h4_term_count_reduction_factor"] > 300.0
    assert audit["summary"]["nonmonotone_accuracy_curve_count"] > 0
    assert audit["summary"]["maximum_component_cancellation_ratio"] > 5.0
    assert audit["summary"]["full_grouped_h4_selection_stable"] is True
    assert audit["summary"]["minimum_selection_stable_count_all_states"] == {
        "H2": 4,
        "H4": 25,
    }
    assert (
        audit["summary"][
            "maximum_exact_state_direct_formula_regret_from_truncation"
        ]
        > 0.14
    )


def test_h04_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    assert manifest["literature"]["arxiv"] == "2606.30738v1"
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "method_comparison.csv": "method_rows",
        "state_action_summary.csv": "state_action_rows",
        "importance_truncation.csv": "pruning_rows",
        "selection_regret.csv": "selection_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])

    with (ARTIFACT / "grouped_components.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        component_rows = list(csv.DictReader(handle))
    expected_components = sum(
        row["grouped_term_count"] for row in audit["state_action_rows"]
    )
    assert len(component_rows) == expected_components
