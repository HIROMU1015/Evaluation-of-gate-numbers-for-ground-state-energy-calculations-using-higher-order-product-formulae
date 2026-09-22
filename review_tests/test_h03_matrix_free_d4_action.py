from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.pennylane_bch import (
    effective_hamiltonian_action_from_bch,
    effective_hamiltonian_matrices_from_bch,
)


ARTIFACT = Path("artifacts/prevalidation_h03_matrix_free_d4_action_20260922")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_h03_streaming_and_cached_actions_match_dense_nested_commutator() -> None:
    matrices = [
        np.asarray([[0.2, 0.3], [0.3, -0.1]], dtype=np.complex128),
        np.asarray([[0.7, -0.2j], [0.2j, -0.4]], dtype=np.complex128),
    ]
    expansion = [{}, {}, {}, {}, {(0, 0, 0, 0, 1): 0.125}]
    state = np.asarray([0.6 + 0.1j, 0.7 - 0.2j], dtype=np.complex128)
    state /= np.linalg.norm(state)
    dense = effective_hamiltonian_matrices_from_bch(expansion, matrices)[4]
    reference = dense @ state

    streaming, stream_diagnostics = effective_hamiltonian_action_from_bch(
        expansion, matrices, state, 4, cache_prefixes=False
    )
    cached, cache_diagnostics = effective_hamiltonian_action_from_bch(
        expansion, matrices, state, 4, cache_prefixes=True
    )
    np.testing.assert_allclose(streaming, reference, atol=1e-15, rtol=1e-13)
    np.testing.assert_allclose(cached, reference, atol=1e-15, rtol=1e-13)
    assert stream_diagnostics["logical_peak_statevector_count"] == 3
    assert cache_diagnostics["actual_group_action_count"] < stream_diagnostics[
        "actual_group_action_count"
    ]
    assert cache_diagnostics["logical_peak_statevector_count"] > stream_diagnostics[
        "logical_peak_statevector_count"
    ]


def test_h03_artifact_validates_h2_action_and_records_h4_blocker() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete_with_scaling_blocker"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "H03"
    assert audit["scope"]["new_direct_pf_points"] == 0
    assert len(audit["h2_formula_rows"]) == 4
    assert len(audit["h2_state_action_rows"]) == 24
    assert len(audit["synthetic_scaling_rows"]) == 5
    assert len(audit["h4_symbolic_boundary_rows"]) == 1
    assert all(check["passed"] for check in audit["checks"])
    assert audit["summary"]["maximum_action_relative_error"] < 3e-15
    assert audit["summary"]["maximum_expectation_absolute_error_hartree"] < 2e-18
    assert audit["summary"]["streaming_group_actions"] == 150
    assert audit["summary"]["cached_group_actions"] == 60
    assert audit["summary"]["streaming_peak_statevectors"] == 3
    assert audit["summary"]["cached_peak_statevectors"] == 62

    h4 = audit["h4_symbolic_boundary_rows"][0]
    assert h4["symbolic_expansion_seconds"] > 30.0
    assert h4["d4_raw_commutator_term_count"] == 168560
    assert h4["maximum_rss_increment_upper_bound_kib"] > 4_000_000
    assert h4["stop_before_word_expansion_and_action"] is True
    assert h4["action_attempted"] is False


def test_h03_synthetic_scaling_shows_time_memory_tradeoff() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    rows = {row["dimension"]: row for row in audit["synthetic_scaling_rows"]}
    assert set(rows) == {4, 16, 32, 64, 128}
    assert max(
        max(row["streaming_action_relative_error"], row["cached_action_relative_error"])
        for row in rows.values()
    ) < 1e-14
    assert all(row["cached_group_action_count"] == 60 for row in rows.values())
    assert all(row["streaming_group_action_count"] == 150 for row in rows.values())
    assert rows[4]["cached_logical_vector_bytes"] > rows[4]["dense_d4_matrix_bytes"]
    assert rows[128]["cached_logical_vector_bytes"] < rows[128]["dense_d4_matrix_bytes"]
    assert rows[128]["streaming_action_median_seconds"] < rows[128][
        "dense_d4_construction_seconds"
    ]
    assert rows[128]["cached_action_median_seconds"] < rows[128][
        "streaming_action_median_seconds"
    ]
    assert rows[128]["input_group_matrix_bytes"] > rows[128]["dense_d4_matrix_bytes"]


def test_h03_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "h2_formula_summary.csv": "h2_formula_rows",
        "h2_state_actions.csv": "h2_state_action_rows",
        "synthetic_scaling.csv": "synthetic_scaling_rows",
        "h4_symbolic_boundary.csv": "h4_symbolic_boundary_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
