from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from review_response.audit_h01_approximate_state_pilot import (
    determinant_cisd_state,
    determinant_excitation_rank,
    hartree_fock_full_basis_index,
    sector_basis_indices,
)
from review_response.search_pf_cost_predictability_m2_m3 import (
    projected_reference_candidate,
)


ARTIFACT = Path("artifacts/prevalidation_h01_approximate_state_pilot_20260922")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_h01_sector_and_hf_indices_match_stored_determinant_conventions() -> None:
    h2_indices = sector_basis_indices(
        4, "fixed_interleaved_spin_populations", (1, 1)
    )
    h4_indices = sector_basis_indices(8, "fixed_half_populations", (2, 2))
    assert h2_indices.size == 4
    assert h4_indices.size == 36
    assert hartree_fock_full_basis_index(
        4, "fixed_interleaved_spin_populations", (1, 1)
    ) == 12
    assert hartree_fock_full_basis_index(
        8, "fixed_half_populations", (2, 2)
    ) == 204
    assert 12 in h2_indices
    assert 204 in h4_indices


def test_h01_determinant_cisd_uses_excitation_rank_at_most_two() -> None:
    sector_indices = np.asarray([0b11110000, 0b11101000, 0b11001100, 0b00001111])
    reference = int(sector_indices[0])
    assert determinant_excitation_rank(reference, reference) == 0
    assert determinant_excitation_rank(int(sector_indices[1]), reference) == 1
    assert determinant_excitation_rank(int(sector_indices[2]), reference) == 2
    assert determinant_excitation_rank(int(sector_indices[3]), reference) == 4

    hamiltonian = np.diag([-2.0, -1.0, 0.0, -3.0]).astype(np.complex128)
    state, metadata = determinant_cisd_state(
        hamiltonian, sector_indices, reference
    )
    assert metadata["subspace_dimension"] == 3
    np.testing.assert_array_equal(metadata["subspace_positions"], [0, 1, 2])
    np.testing.assert_allclose(state, [1.0, 0.0, 0.0, 0.0])


def test_h01_artifact_records_hf_failure_and_cisd_recovery() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "pilot_complete_with_findings"
    assert audit["checks_passed"] is True
    assert audit["scope"]["catalog_item"] == "H01 pilot"
    assert len(audit["state_rows"]) == 6
    assert len(audit["expectation_rows"]) == 24
    assert len(audit["selection_rows"]) == 12
    assert all(check["passed"] for check in audit["checks"])

    h4_cisd = next(
        row
        for row in audit["state_rows"]
        if row["system_id"] == "H4" and row["state_id"] == "cisd"
    )
    assert h4_cisd["subspace_dimension"] == 27
    assert h4_cisd["full_sector_dimension"] == 36
    assert h4_cisd["exact_state_overlap_probability"] > 0.999

    operational = [
        row
        for row in audit["selection_rows"]
        if row["candidate_set_id"] == "operational_x02_three"
    ]
    hf_rows = [row for row in operational if row["state_id"] == "hf"]
    cisd_rows = [row for row in operational if row["state_id"] == "cisd"]
    assert len(hf_rows) == len(cisd_rows) == 2
    assert all(row["selected_formula_id"] == "two_term_center" for row in hf_rows)
    assert all(row["exact_reference_formula_id"] == "current_m3" for row in hf_rows)
    assert min(row["direct_joint_sampled_regret"] for row in hf_rows) > 0.20
    assert all(row["selected_formula_id"] == "current_m3" for row in cisd_rows)
    assert max(row["direct_joint_sampled_regret"] for row in cisd_rows) < 0.003


def test_h01_npz_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "state_metrics.csv": "state_rows",
        "operator_expectations.csv": "expectation_rows",
        "selection_summary.csv": "selection_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])

    with np.load(ARTIFACT / "states.npz") as arrays:
        assert int(arrays["H2_hf_full_index"]) == 12
        assert int(arrays["H4_hf_full_index"]) == 204
        assert arrays["H2_cisd_subspace_positions"].size == 4
        assert arrays["H4_cisd_subspace_positions"].size == 27
        for system_id in ("H2", "H4"):
            for state_id in ("exact", "hf", "cisd"):
                assert abs(np.linalg.norm(arrays[f"{system_id}_{state_id}_state"]) - 1.0) < 1e-12


def test_publication_projection_reproduces_generation_coefficients() -> None:
    expected = {
        2: [-0.6581584493683974, 0.420087292300873, 0.4089919323833257],
        3: [
            -0.5443397179019291,
            0.4065366597899938,
            0.21638705960015756,
            0.14924613956081323,
        ],
    }
    for kernel_m, weights in expected.items():
        np.testing.assert_array_equal(
            projected_reference_candidate(kernel_m)["weights"], weights
        )

    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    compatibility = manifest["publication_compatibility"]
    assert compatibility["projected_reference_weights_bytewise_equal_for_m"] == [2, 3]
    assert compatibility["scientific_outputs_changed"] is False
