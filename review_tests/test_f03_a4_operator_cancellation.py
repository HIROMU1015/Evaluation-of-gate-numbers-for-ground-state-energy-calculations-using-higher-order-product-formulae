from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_f03_a4_operator_cancellation import (
    _artificial_operators,
    error_operator_state_metrics,
)


ARTIFACT = Path(
    "artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_f03_error_operator_state_metrics_separate_expectation_and_action() -> None:
    operator = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    state = np.asarray([1.0, 0.0], dtype=np.complex128)
    metrics = error_operator_state_metrics(operator, state)
    assert metrics["d4_expectation_hartree"] == 0.0
    assert metrics["d4_spectral_norm_hartree"] == 1.0
    assert metrics["centered_d4_action_norm_hartree"] == 1.0
    assert metrics["expectation_over_spectral_norm"] == 0.0


def test_f03_artificial_root_has_zero_a4_but_finite_d4_norm() -> None:
    root = -2.5773502691896355
    data = _artificial_operators(root)
    a4 = float(data["energy_coefficients"][4].real)
    metrics = error_operator_state_metrics(data["formal"][4], data["ground_state"])
    assert abs(a4) < 1e-12
    assert metrics["d4_spectral_norm_hartree"] > 0.1
    assert metrics["centered_d4_action_norm_hartree"] > 0.1


def test_f03_artifact_distinguishes_expectation_cancellation_from_operator_size() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_findings"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "F03"
    assert len(audit["exact_condition_rows"]) == 8
    assert len(audit["state_operator_rows"]) == 24
    assert len(audit["artificial_family_rows"]) == 12
    assert all(check["passed"] for check in audit["checks"])

    m5_rows = [
        row
        for row in audit["exact_condition_rows"]
        if row["formula_id"] == "m5_best"
    ]
    assert len(m5_rows) == 2
    assert max(row["expectation_over_spectral_norm"] for row in m5_rows) < 0.025
    assert min(row["centered_action_over_expectation"] for row in m5_rows) > 40.0
    assert min(abs(row["signed_a6_contribution_over_epsilon"]) for row in m5_rows) > 0.045
    assert max(row["direct_pf_absolute_error_over_epsilon"] for row in m5_rows) < 0.15

    hf_rows = [row for row in audit["state_operator_rows"] if row["state_id"] == "hf"]
    cisd_rows = [
        row for row in audit["state_operator_rows"] if row["state_id"] == "cisd"
    ]
    assert max(
        row["d4_expectation_relative_error_vs_exact_state"] for row in hf_rows
    ) > 14.0
    assert max(
        row["d4_expectation_relative_error_vs_exact_state"] for row in cisd_rows
    ) < 0.31


def test_f03_artificial_family_breakdown_is_not_a_branch_warning() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    rows = audit["artificial_family_rows"]
    closest = [
        row for row in rows if abs(row["parameter_offset_from_root"]) == 0.001
    ]
    distance_001 = [
        row for row in rows if abs(row["parameter_offset_from_root"]) == 0.01
    ]
    distance_003 = [
        row for row in rows if abs(row["parameter_offset_from_root"]) == 0.03
    ]
    assert len(closest) == len(distance_001) == len(distance_003) == 2
    assert min(row["direct_pf_absolute_error_over_epsilon"] for row in closest) > 100.0
    assert min(row["direct_pf_absolute_error_over_epsilon"] for row in distance_001) > 5.0
    assert min(row["direct_pf_absolute_error_over_epsilon"] for row in distance_003) < 1.0
    assert max(row["direct_pf_absolute_error_over_epsilon"] for row in distance_003) > 1.0
    assert not any(row["tracking_warning_count"] for row in rows)
    assert all(row["selection_rules_agree"] for row in rows)


def test_f03_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "exact_condition_metrics.csv": "exact_condition_rows",
        "state_operator_metrics.csv": "state_operator_rows",
        "artificial_family.csv": "artificial_family_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
