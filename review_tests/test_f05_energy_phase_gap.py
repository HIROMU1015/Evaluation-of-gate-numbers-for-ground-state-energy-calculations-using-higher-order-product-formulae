from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from review_response.audit_f05_energy_phase_gap import (
    EARLY_SLOPE_RELATIVE_TOLERANCE,
    _as_bool,
)


ARTIFACT = Path("artifacts/prevalidation_f05_energy_phase_gap_20260922")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_f05_serialized_boolean_parser_is_strict() -> None:
    assert _as_bool("True") is True
    assert _as_bool("False") is False
    assert _as_bool(True) is True


def test_f05_artifact_separates_physical_and_phase_gap_mechanisms() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "complete"
    assert audit["passed"] is True
    assert audit["scope"]["catalog_item"] == "F05"
    assert audit["scope"]["new_direct_pf_points"] == 0
    assert len(audit["condition_summaries"]) == 6
    assert len(audit["phase_rows"]) == 3360
    assert all(check["passed"] for check in audit["checks"])
    assert max(
        row["early_slope_maximum_relative_error"]
        for row in audit["condition_summaries"]
    ) <= EARLY_SLOPE_RELATIVE_TOLERANCE
    assert max(
        row["lowest_gap_group_absolute_mixing_share"]
        for row in audit["condition_summaries"]
    ) < 1e-20
    assert min(
        row["dominant_mixing_gap_over_minimum_gap"]
        for row in audit["condition_summaries"]
    ) > 3.0
    assert sum(
        row["first_phase_compression_time"] is not None
        for row in audit["condition_summaries"]
    ) == 3
    assert all(
        row["first_warning_due_ground_overlap"]
        for row in audit["condition_summaries"]
    )
    assert not any(
        row["first_warning_due_phase_gap_threshold"]
        for row in audit["condition_summaries"]
    )


def test_f05_manifest_hashes_and_csv_rows_match() -> None:
    audit = json.loads((ARTIFACT / "audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARTIFACT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == audit["status"]
    for group in ("source_sha256", "input_sha256", "artifact_sha256"):
        for path_text, expected_hash in manifest[group].items():
            assert _sha256(Path(path_text)) == expected_hash

    csv_mappings = {
        "condition_summary.csv": "condition_summaries",
        "phase_gap_points.csv": "phase_rows",
        "mixing_gap_groups.csv": "mixing_group_rows",
    }
    for filename, key in csv_mappings.items():
        with (ARTIFACT / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(audit[key])
