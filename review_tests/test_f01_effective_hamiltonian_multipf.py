from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_f01_effective_hamiltonian_multipf import (
    FIT_WINDOWS,
    THRESHOLDS,
    formula_registry,
)
from trotterlib.pf_decomposition import symmetric_s2_sequence


ARTIFACT = Path(
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_f01_formula_registry_uses_normalized_palindromic_s2_sequences() -> None:
    expected_blocks = {
        "yoshida4": 3,
        "current_m3": 7,
        "two_term_center": 7,
        "m5_best": 11,
    }
    registry = formula_registry()
    assert {formula["formula_id"] for formula in registry} == set(expected_blocks)
    for formula in registry:
        weights = np.asarray(formula["weights"], dtype=float)
        sequence = np.asarray(symmetric_s2_sequence(weights), dtype=float)
        assert abs(weights[0] + 2.0 * np.sum(weights[1:]) - 1.0) < 2e-15
        assert sequence.size == expected_blocks[formula["formula_id"]]
        np.testing.assert_array_equal(sequence, sequence[::-1])


def test_f01_artifact_is_complete_and_operator_data_are_self_consistent() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "F01"
    assert audit["scope"]["condition_count"] == 8
    assert len(audit["condition_summaries"]) == 8
    assert len(audit["recovery_rows"]) == 8 * len(FIT_WINDOWS)
    assert len(audit["operator_rows"]) == 8 * 3
    assert all(check["passed"] for check in audit["checks"])
    assert {check["check_id"] for check in audit["checks"]} == set(THRESHOLDS)

    arrays = np.load(ARTIFACT / "effective_operators.npz")
    operator_keys = [key for key in arrays.files if "_D" in key]
    assert len(operator_keys) == 8 * 3
    operator_by_key = {
        (row["system_id"], row["formula_id"], int(row["order"])): row
        for row in audit["operator_rows"]
    }
    for key in operator_keys:
        system_id, formula_id, order_text = key.split("_", maxsplit=2)
        # Formula identifiers contain underscores, so recover by known suffix.
        order = int(order_text.rsplit("D", maxsplit=1)[1])
        formula_id = key[len(system_id) + 1 : key.rfind("_D")]
        matrix = arrays[key]
        expected_dimension = 4 if system_id == "H2" else 36
        assert matrix.shape == (expected_dimension, expected_dimension)
        assert np.linalg.norm(matrix - matrix.conj().T) < 1e-13
        row = operator_by_key[(system_id, formula_id, order)]
        assert abs(np.linalg.norm(matrix) - row["operator_frobenius_norm"]) < 1e-14

    for system_id, dimension, group_count in (("H2", 4, 2), ("H4", 36, 13)):
        hamiltonian = arrays[f"{system_id}_hamiltonian"]
        state = arrays[f"{system_id}_ground_state"]
        energy = float(arrays[f"{system_id}_ground_energy"])
        groups = [arrays[f"{system_id}_group_{index:03d}"] for index in range(group_count)]
        assert hamiltonian.shape == (dimension, dimension)
        assert state.shape == (dimension,)
        assert np.linalg.norm(sum(groups, np.zeros_like(hamiltonian)) - hamiltonian) < 1e-13
        assert np.linalg.norm(hamiltonian @ state - energy * state) < 1e-10

    for summary in audit["condition_summaries"]:
        key4 = (summary["system_id"], summary["formula_id"], 4)
        key6 = (summary["system_id"], summary["formula_id"], 6)
        assert abs(
            summary["energy_coefficients"]["a4"]
            - operator_by_key[key4]["ground_expectation_real"]
        ) < 2e-15
        assert abs(
            summary["energy_coefficients"]["a6"]
            - operator_by_key[key6]["ground_expectation_real"]
        ) < 2e-15


def test_f01_manifest_hashes_and_csv_aggregates_match_audit() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for path_text, expected_hash in manifest["source_sha256"].items():
        assert _sha256(Path(path_text)) == expected_hash
    for path_text, expected_hash in manifest["artifact_sha256"].items():
        assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "formula_registry.csv": "formula_rows",
        "reference_validation.csv": "reference_rows",
        "window_recovery.csv": "recovery_rows",
        "holdout_validation.csv": "holdout_rows",
        "operator_decomposition.csv": "operator_rows",
    }
    for filename, audit_key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[audit_key])

    recovery_maxima = {
        order: max(float(row[f"relative_error_d{order}"]) for row in audit["recovery_rows"])
        for order in (4, 6, 8)
    }
    for order, measured in recovery_maxima.items():
        assert measured == audit["extrema"][f"fit_relative_error_d{order}"]
