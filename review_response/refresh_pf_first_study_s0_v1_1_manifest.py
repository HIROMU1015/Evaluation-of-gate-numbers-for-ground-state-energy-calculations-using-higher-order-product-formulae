"""Refresh only the non-scientific artifact hashes of a completed S0 v1.1 run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from review_response import run_pf_first_study_s0_exact_time_scoring_v1_1 as s0


def refresh(output_dir: Path) -> dict[str, object]:
    required = (
        "protocol.json",
        "s0_anchor_protocol.json",
        "predictions.json",
        "source_manifest.json",
        "branch_audit.csv",
        "scoring.csv",
        "audit.json",
        "manifest.json",
        "report.md",
    )
    missing = [name for name in required if not (output_dir / name).is_file()]
    if missing:
        raise s0._base.S0ValidationError(f"missing S0 v1.1 artifacts: {missing}")
    if (
        s0._base._sha256(output_dir / "protocol.json")
        != s0._base.EXPECTED_FIRST_STUDY_PROTOCOL_SHA256
        or s0._base._sha256(output_dir / "s0_anchor_protocol.json")
        != s0.EXPECTED_ANCHOR_PROTOCOL_SHA256
        or s0._base._sha256(output_dir / "predictions.json")
        != s0._base.EXPECTED_PREDICTIONS_SHA256
    ):
        raise s0._base.S0ValidationError("S0 v1.1 immutable artifact hash mismatch")
    audit = s0._base._load_json(output_dir / "audit.json")
    if audit.get("status") != "complete_exact_time_scoring" or not all(
        audit.get("checks", {}).values()
    ):
        raise s0._base.S0ValidationError("S0 v1.1 audit is not complete")
    if not (output_dir / "COMPLETE").is_file():
        raise s0._base.S0ValidationError("S0 v1.1 COMPLETE marker is missing")
    with (output_dir / "branch_audit.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        branch_rows = list(csv.DictReader(handle))
    with (output_dir / "scoring.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        scoring_rows = list(csv.DictReader(handle))
    if len(branch_rows) != 24 or len(scoring_rows) != 6:
        raise s0._base.S0ValidationError("S0 v1.1 CSV row count mismatch")
    manifest = s0._base._load_json(output_dir / "manifest.json")
    if (
        manifest.get("status") != "complete_exact_time_scoring"
        or manifest.get("s0_anchor_protocol_sha256")
        != s0.EXPECTED_ANCHOR_PROTOCOL_SHA256
    ):
        raise s0._base.S0ValidationError("S0 v1.1 manifest identity mismatch")
    manifest["artifact_sha256"] = s0._base._artifact_hashes(output_dir)
    manifest["manifest_refresh"] = {
        "at": s0._base._now(),
        "mode": "metadata_only_no_truth_recomputation",
    }
    s0._base._write_json(output_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = refresh(args.output.resolve())
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "artifact_count": len(manifest["artifact_sha256"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
