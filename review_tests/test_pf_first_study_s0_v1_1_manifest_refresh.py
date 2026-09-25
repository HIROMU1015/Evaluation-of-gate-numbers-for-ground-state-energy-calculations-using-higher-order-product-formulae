from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil

from review_response import refresh_pf_first_study_s0_v1_1_manifest as refresh
from review_response import run_pf_first_study_s0_exact_time_scoring_v1_1 as s0


def _write_csv(path: Path, count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row"])
        writer.writeheader()
        writer.writerows({"row": index} for index in range(count))


def test_manifest_refresh_hashes_post_run_logs_without_touching_science(tmp_path: Path) -> None:
    output = tmp_path / "result"
    output.mkdir()
    shutil.copyfile("PF_first_study_protocol_20260925.json", output / "protocol.json")
    shutil.copyfile(
        s0.ANCHOR_PROTOCOL, output / "s0_anchor_protocol.json"
    )
    shutil.copyfile(
        "artifacts/server_practical_calibration_minimal_20260923_79035cc/predictions.json",
        output / "predictions.json",
    )
    (output / "source_manifest.json").write_text("{}\n", encoding="utf-8")
    (output / "report.md").write_text("# report\n", encoding="utf-8")
    (output / "review_tests.log").write_text("207 passed\n", encoding="utf-8")
    _write_csv(output / "branch_audit.csv", 24)
    _write_csv(output / "scoring.csv", 6)
    s0._base._write_json(
        output / "audit.json",
        {"status": "complete_exact_time_scoring", "checks": {"all": True}},
    )
    s0._base._write_json(
        output / "manifest.json",
        {
            "status": "complete_exact_time_scoring",
            "s0_anchor_protocol_sha256": s0.EXPECTED_ANCHOR_PROTOCOL_SHA256,
            "artifact_sha256": {},
        },
    )
    (output / "COMPLETE").touch()
    manifest = refresh.refresh(output)
    assert manifest["manifest_refresh"]["mode"] == "metadata_only_no_truth_recomputation"
    assert manifest["artifact_sha256"]["review_tests.log"] == s0._base._sha256(
        output / "review_tests.log"
    )
    assert json.loads((output / "audit.json").read_text())["status"] == (
        "complete_exact_time_scoring"
    )
