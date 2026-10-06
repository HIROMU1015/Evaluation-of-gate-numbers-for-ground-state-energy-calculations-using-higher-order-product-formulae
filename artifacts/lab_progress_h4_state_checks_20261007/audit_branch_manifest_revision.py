"""Verify unchanged frozen H4 artifacts and publish a revised hash manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    protocol = json.loads((HERE / "branch_diagnostic_protocol.json").read_text())
    previous = json.loads((HERE / "manifest_before_branch_diagnostic.json").read_text())
    assert digest(HERE / "manifest_before_branch_diagnostic.json") == protocol["manifest_revision"]["previous_manifest_sha256"]
    old_report = "artifacts/lab_progress_h4_state_checks_20261007/report.md"
    assert digest(HERE / "report_before_branch_diagnostic.md") == previous["files"][old_report]
    for rel, expected in previous["files"].items():
        if rel != old_report:
            assert digest(ROOT / rel) == expected, f"prior artifact changed: {rel}"
    assert digest(HERE / "classification_and_audit.json") == protocol["input_classification_sha256"]
    assert digest(HERE / "protocol.json") == protocol["input_protocol_sha256"]
    assert digest(HERE / "predictions.json") == protocol["input_predictions_sha256"]
    assert digest(HERE / "direct_grid.csv") == protocol["input_direct_grid_sha256"]
    new_runner = ROOT / "review_response/audit_lab_progress_h4_branch_correspondence_20261007.py"
    assert digest(new_runner) == protocol["runner_sha256"]
    checks = json.loads((HERE / "branch_diagnostic_checks.json").read_text())
    assert checks["protocol_sha256"] == digest(HERE / "branch_diagnostic_protocol.json")
    assert checks["new_pf_diagonalizations"] == 3
    rows = checks["rows"]
    assert [r["same_PF_eigencomponent_as_continuation"] for r in rows] == [True, False, False]
    assert [r["auxiliary_target_met"] for r in rows] == [True, False, False]
    assert all(not r["is_replacement_formal_scoring"] for r in rows)
    source = json.loads((HERE / "protocol.json").read_text())["source_registry"]
    for row in source:
        assert digest(ROOT / row["path"]) == row["sha256"]
    artifact_paths = sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "manifest.json")
    runner_paths = [ROOT / "review_response/run_lab_progress_h4_state_checks_20261007.py",
                    ROOT / "review_response/audit_lab_progress_h4_spectral_proxy_20261007.py", new_runner]
    manifest = {
        "self_excluded": ["artifacts/lab_progress_h4_state_checks_20261007/manifest.json"],
        "publication_policy": "code, scalar data, metadata, prose and plots derived from saved scalars; no new matrices/vectors/unitaries",
        "source_registry": "protocol.json: source origin_result_commit and verified_snapshot_commit remain separate",
        "revision": {
            "previous_manifest": "manifest_before_branch_diagnostic.json",
            "previous_manifest_sha256": digest(HERE / "manifest_before_branch_diagnostic.json"),
            "previous_report": "report_before_branch_diagnostic.md",
            "previous_report_sha256": digest(HERE / "report_before_branch_diagnostic.md"),
            "prior_frozen_numerical_files_unchanged": True,
            "changed_prior_files": [old_report],
            "added_diagnostic": "independent frozen three-point maximum-overlap branch correspondence audit",
        },
        "files": {str(path.relative_to(ROOT)): digest(path) for path in artifact_paths + runner_paths},
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"prior_frozen_files_unchanged": True,
                      "manifest_files": len(manifest["files"]),
                      "branch_diagnostic_diagonalizations": 3,
                      "checks_passed": True}, indent=2))


if __name__ == "__main__":
    main()
