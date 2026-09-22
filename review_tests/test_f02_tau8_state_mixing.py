from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_f02_tau8_state_mixing import (
    decompose_a8_state_mixing,
    fit_signed_energy_coefficients,
)


ARTIFACT = Path(
    "artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_f02_two_component_identity_on_synthetic_three_level_system() -> None:
    hamiltonian = np.diag([-1.0, 0.0, 2.0]).astype(np.complex128)
    state = np.asarray([1.0, 0.0, 0.0], dtype=np.complex128)
    d4 = np.asarray(
        [[0.1, 0.2, -0.3j], [0.2, 0.0, 0.0], [0.3j, 0.0, 0.0]],
        dtype=np.complex128,
    )
    d8 = np.diag([0.05, -0.02, 0.01]).astype(np.complex128)
    result = decompose_a8_state_mixing(hamiltonian, state, d4, d8)
    expected_mixing = 0.2**2 / (-1.0) + 0.3**2 / (-3.0)
    assert abs(result["d8_expectation_hartree"] - 0.05) < 1e-15
    assert abs(result["d4_second_order_mixing_hartree"] - expected_mixing) < 1e-15
    assert abs(result["a8_from_components_hartree"] + 0.02) < 1e-15
    assert len(result["state_rows"]) == 2


def test_f02_scaled_signed_fit_recovers_declared_coefficients() -> None:
    times = np.geomspace(0.08, 0.8, 20)
    expected = {4: -2e-3, 6: 4e-4, 8: -7e-5, 10: 2e-6, 12: -3e-8}
    shifts = np.asarray(
        [sum(expected[order] * time**order for order in expected) for time in times]
    )
    result = fit_signed_energy_coefficients(times, shifts)
    for index, order in enumerate(result["orders"]):
        assert abs(result["coefficients"][index] - expected[order]) < 2e-13
    assert result["maximum_absolute_residual_hartree"] < 1e-17


def test_f02_artifact_identity_direct_fit_finding_and_hashes() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_findings"
    assert audit["mechanism_identity_passed"] is True
    assert len(audit["condition_summaries"]) == 8
    assert len(audit["direct_fit_rows"]) == 24
    assert audit["direct_a8_fit_stable_condition_count"] < 8
    assert all(check["passed"] for check in audit["checks"])
    assert max(
        abs(row["component_identity_residual_hartree"])
        for row in audit["condition_summaries"]
    ) < 1e-12
    assert all(
        row["d4_second_order_mixing_hartree"] <= 0.0
        for row in audit["condition_summaries"]
    )
    center = [
        row
        for row in audit["condition_summaries"]
        if row["formula_id"] == "two_term_center"
    ]
    assert len(center) == 2
    assert max(row["net_to_absolute_components_ratio"] for row in center) < 0.04

    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "condition_summary.csv": "condition_summaries",
        "excited_state_contributions.csv": "excited_state_rows",
        "degenerate_group_contributions.csv": "degenerate_group_rows",
        "direct_fit_comparison.csv": "direct_fit_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
