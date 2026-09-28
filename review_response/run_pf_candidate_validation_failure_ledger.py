#!/usr/bin/env python3
"""Build the D2R R0 ledger from frozen second-study artifacts only."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pf_candidate_validation as validation


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(project_root: Path, source_commit: str, output_dir: Path) -> dict[str, object]:
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise validation.CandidateValidationError(f"output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    manifest = validation.source_manifest(project_root, source_commit)
    result = validation.build_failure_ledger(project_root)
    validation.write_json(output_dir / "source_manifest.json", manifest)
    validation.write_csv(output_dir / "failure_ledger.csv", result["ledger"])
    validation.write_csv(
        output_dir / "selected_coordinate_plan.csv", result["coordinate_plan"]
    )
    derived = {
        "schema": "pf_candidate_validation_r0_checks_v1",
        "created_at": now(),
        "source_commit": source_commit,
        "protocol_sha256": result["protocol_sha256"],
        **result["checks"],
        "coordinate_plan_sha256": validation.canonical_json_sha256(
            result["coordinate_plan"]
        ),
        "ledger_sha256": validation.canonical_json_sha256(result["ledger"]),
        "new_molecular_calculation_count": 0,
        "new_proxy_evaluation_count": 0,
        "new_direct_truth_coordinate_count": 0,
        "exact_state_generation_count": 0,
        "gpu_operation_count": 0,
    }
    validation.write_json(output_dir / "derived_metric_checks.json", derived)
    unsafe = [row for row in result["ledger"] if row["unsafe_execution"]]
    lines = [
        "# D2R R0 failure ledger",
        "",
        f"- Source commit: `{source_commit}`",
        f"- Protocol SHA-256: `{result['protocol_sha256']}`",
        f"- Strategy-condition rows: {len(result['ledger'])}",
        f"- Deduplicated selected coordinates: {len(result['coordinate_plan'])}",
        f"- Saved selected-time CISD proxies: {result['checks']['saved_selected_coordinate_proxy_count']}",
        f"- Missing selected-time CISD proxies: {result['checks']['missing_selected_coordinate_proxy_count']}",
        f"- Unsafe strategy-condition rows: {len(unsafe)}",
        "",
        "## Unsafe rows",
        "",
        "| Condition | Strategy | Required/frozen | Underestimate/allowance |",
        "|---|---|---:|---:|",
    ]
    for row in unsafe:
        lines.append(
            f"| {row['condition']} | {row['strategy']} | "
            f"{row['required_cost_over_frozen_budget']:.9f} | "
            f"{row['underestimation_over_allowance']:.6f} |"
        )
    lines.extend(
        [
            "",
            "All quantities in this report are read-only derivations from the closed "
            "second study. They are post-hoc development diagnostics and do not change "
            "its `complete_no_benefit` decision.",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    complete = {
        "schema": "pf_candidate_validation_r0_complete_v1",
        "created_at": now(),
        "status": "r0_complete_r1_protocol_required",
        "source_commit": source_commit,
        "execution_head": head,
        "protocol_sha256": result["protocol_sha256"],
        "ledger_sha256": derived["ledger_sha256"],
        "coordinate_plan_sha256": derived["coordinate_plan_sha256"],
        "r1_authorized": False,
        "r2_authorized": False,
    }
    validation.write_json(output_dir / "RUN_COMPLETE.json", complete)
    return complete


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--project-root", type=Path, required=True)
    value.add_argument("--source-commit", default=validation.SOURCE_COMMIT)
    value.add_argument("--output-dir", type=Path, required=True)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = run(args.project_root, args.source_commit, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
