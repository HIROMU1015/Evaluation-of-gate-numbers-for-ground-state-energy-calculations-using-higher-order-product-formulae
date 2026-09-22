from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_h05_higher_order_acquisition import (
    fit_signed_coefficients,
    projected_response_mixing,
)


ARTIFACT = Path(
    "artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_h05_scaled_signed_fit_recovers_known_polynomial() -> None:
    times = np.asarray([0.31, 0.43, 0.55, 0.68, 0.82])
    coefficients = {4: -2.3e-4, 6: 7.1e-6, 8: -4.2e-8}
    shifts = sum(value * times**order for order, value in coefficients.items())
    free = fit_signed_coefficients(times, shifts, (4, 6, 8))
    fixed = fit_signed_coefficients(
        times[-2:],
        shifts[-2:],
        (6, 8),
        fixed_coefficients={4: coefficients[4]},
    )
    for order, reference in coefficients.items():
        np.testing.assert_allclose(
            free["coefficients"][order], reference, atol=1e-16, rtol=1e-10
        )
        np.testing.assert_allclose(
            fixed["coefficients"][order], reference, atol=1e-16, rtol=1e-10
        )


def test_h05_projected_response_matches_spectral_sum_for_exact_state() -> None:
    hamiltonian = np.diag([-1.2, -0.4, 0.7]).astype(np.complex128)
    state = np.asarray([1.0, 0.0, 0.0], dtype=np.complex128)
    d4 = np.asarray(
        [[0.1, 0.03 + 0.02j, -0.04], [0.03 - 0.02j, 0.2, 0.01], [-0.04, 0.01, -0.3]],
        dtype=np.complex128,
    )
    action = d4 @ state
    result = projected_response_mixing(hamiltonian, state, action)
    reference = abs(d4[1, 0]) ** 2 / (-1.2 + 0.4)
    reference += abs(d4[2, 0]) ** 2 / (-1.2 - 0.7)
    np.testing.assert_allclose(result["mixing_hartree"], reference, atol=1e-15)
    assert result["projected_response_residual_2_norm"] < 1e-14
    assert result["response_state_overlap_absolute"] < 1e-14


def test_h05_artifact_records_reduced_point_candidate_and_boundaries() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_findings"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "H05"
    assert audit["scope"]["new_direct_pf_points"] == 0
    assert all(check["passed"] for check in audit["checks"])
    assert len(audit["method_rows"]) == 80
    assert len(audit["response_rows"]) == 24
    assert len(audit["direct_fit_rows"]) == 48
    assert len(audit["reference_tstar_rows"]) == 8
    assert audit["summary"]["exact_response_residual_pass_count"] == 8
    assert audit["summary"]["diagonal_only_residual_pass_count"] < 8
    assert audit["summary"]["best_few_point_method_id"] == "direct_fixed_a4_2_tail"
    assert audit["summary"]["best_few_point_residual_pass_count"] == 8
    assert audit["summary"]["best_few_point_maximum_residual_over_epsilon"] < 0.03
    assert audit["summary"]["free_five_point_residual_pass_count"] == 8
    assert audit["summary"]["direct_order12_residual_pass_count"] < 8
    assert audit["summary"]["hf_response_residual_pass_count"] < 8
    assert audit["summary"]["cisd_response_residual_pass_count"] < 8
    assert audit["summary"]["maximum_projected_response_residual_2_norm"] < 1e-17
    assert audit["summary"]["maximum_exact_mixing_difference_from_f02_hartree"] < 1e-15
    assert audit["summary"]["maximum_order12_refit_difference_from_f02_hartree"] < 1e-16


def test_h05_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "method_comparison.csv": "method_rows",
        "method_summary.csv": "method_summaries",
        "response_diagnostics.csv": "response_rows",
        "direct_fit_diagnostics.csv": "direct_fit_rows",
        "reference_tstar.csv": "reference_tstar_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
