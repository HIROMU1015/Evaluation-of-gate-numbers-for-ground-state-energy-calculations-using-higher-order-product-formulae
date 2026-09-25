"""S4 Phase-B v1.1 with a frozen uniform new-anchor rule.

The parent Phase-A predictions are reused byte-for-byte.  This wrapper changes
only Phase-B branch initialization after the v1 saved-anchor availability
preflight failed before any direct calculation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from review_response import run_pf_first_study_s4_state_convergence as s4


AMENDMENT_PATH = Path(__file__).with_name(
    "pf_first_study_s4_uniform_anchor_protocol_v1_1.json"
)
EXPECTED_AMENDMENT_SHA256 = (
    "9ce996b2732e02a7bb2fa4f1d6f8a4e09fd503896a4eda7a9a4496be0f402150"
)
EXPECTED_PHASE_A_COMMIT = "95ed24c74bb29d883bbaf76d4578ff7af08ed995"
EXPECTED_PREDICTION_SHA256 = (
    "47cdef9b52ea73feef0c005229cb9a482ee8e95afff87f038ff8461549f1c729"
)


def _load_and_verify_amendment() -> dict[str, Any]:
    if not AMENDMENT_PATH.is_file():
        raise s4.S4ValidationError("S4 v1.1 anchor amendment is missing")
    if s4._sha256(AMENDMENT_PATH) != EXPECTED_AMENDMENT_SHA256:
        raise s4.S4ValidationError("S4 v1.1 anchor amendment hash mismatch")
    amendment = s4._load_json(AMENDMENT_PATH)
    if (
        amendment.get("protocol_id")
        != "pf_first_study_s4_uniform_anchor_v1_1"
        or amendment.get("parent_s4_protocol_sha256")
        != s4.EXPECTED_PROTOCOL_SHA256
        or amendment["frozen_phase_a"].get("result_commit")
        != EXPECTED_PHASE_A_COMMIT
        or amendment["frozen_phase_a"].get("prediction_sha256")
        != EXPECTED_PREDICTION_SHA256
    ):
        raise s4.S4ValidationError("S4 v1.1 amendment identity mismatch")
    return amendment


def preflight(
    phase_a_root: Path, failed_phase_b_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    amendment = _load_and_verify_amendment()
    marker, predictions = s4.verify_phase_a_freeze(phase_a_root)
    if s4._sha256(phase_a_root / "predictions.json") != EXPECTED_PREDICTION_SHA256:
        raise s4.S4ValidationError("parent Phase-A prediction hash mismatch")
    if not s4._git_is_ancestor(EXPECTED_PHASE_A_COMMIT, s4._git_head()):
        raise s4.S4ValidationError("parent Phase-A result commit is not an ancestor")
    coordinates = s4.unique_selected_coordinates(predictions)
    accounting = amendment["fixed_accounting"]
    if sum(len(values) for values in coordinates.values()) != int(
        accounting["expected_unique_selected_coordinate_count"]
    ):
        raise s4.S4ValidationError("Phase-A unique-selection count mismatch")
    if len(coordinates) != int(accounting["condition_formula_group_count"]):
        raise s4.S4ValidationError("Phase-A condition/formula group count mismatch")
    if not failed_phase_b_root.is_dir():
        raise s4.S4ValidationError("preserved v1 incomplete Phase-B directory is missing")
    if (failed_phase_b_root / "COMPLETE").exists():
        raise s4.S4ValidationError("v1 Phase-B unexpectedly has COMPLETE")
    direct_cache = failed_phase_b_root / ".runtime/direct_cache"
    if direct_cache.exists() and any(direct_cache.rglob("*")):
        raise s4.S4ValidationError("v1 direct cache is not empty")
    frozen_factor = float(
        amendment["uniform_anchor_rule"][
            "anchor_time_factor_of_minimum_inserted_coordinate"
        ]
    )
    planned_anchors = []
    for (condition, formula), selected_times in sorted(coordinates.items()):
        inserted = sorted(
            {
                float(time_value) * float(factor)
                for time_value in selected_times
                for factor in s4.TIME_FACTORS
            }
        )
        planned_anchors.append({
            "condition": condition,
            "formula": formula,
            "minimum_inserted_time": inserted[0],
            "uniform_anchor_time": frozen_factor * inserted[0],
            "uniform_anchor_factor": frozen_factor,
            "inserted_coordinate_count": len(inserted),
        })
    record = {
        "status": "ready_for_phase_b_v1_1",
        "amendment_sha256": EXPECTED_AMENDMENT_SHA256,
        "parent_phase_a_commit": EXPECTED_PHASE_A_COMMIT,
        "prediction_sha256": EXPECTED_PREDICTION_SHA256,
        "phase_a_marker": marker,
        "failed_v1_phase_b_root_absolute": str(failed_phase_b_root.resolve()),
        "failed_v1_complete_absent": True,
        "failed_v1_direct_cache_empty": True,
        "unique_selected_coordinate_count": sum(
            len(values) for values in coordinates.values()
        ),
        "condition_formula_group_count": len(coordinates),
        "planned_anchors": planned_anchors,
        "truth_opened_by_preflight": False,
    }
    return amendment, record


def run(
    project_root: Path,
    phase_a_root: Path,
    failed_phase_b_root: Path,
    h01_root: Path,
    p03_root: Path,
    output_dir: Path,
    backend: str,
    gpu_id: int,
) -> dict[str, Any]:
    amendment, preflight_record = preflight(
        phase_a_root, failed_phase_b_root
    )
    audit = s4.run_phase_b(
        project_root,
        phase_a_root,
        h01_root,
        p03_root,
        output_dir,
        backend,
        gpu_id,
        phase_b_amendment=amendment,
        phase_b_amendment_path=AMENDMENT_PATH,
        phase_b_amendment_sha256=EXPECTED_AMENDMENT_SHA256,
        defer_complete_marker=True,
    )
    s4._write_json(output_dir / "v1_1_preflight.json", preflight_record)
    stored_audit = s4._load_json(output_dir / "audit.json")
    stored_audit["v1_1_preflight"] = preflight_record
    s4._write_json(output_dir / "audit.json", stored_audit)
    report_path = output_dir / "report.md"
    report = report_path.read_text(encoding="utf-8")
    report += (
        "\n## v1.1 anchor amendment\n\n"
        "The parent Phase-A predictions were reused byte-for-byte. The v1 "
        "saved-anchor availability preflight failed before direct calculation. "
        "All 12 condition/formula groups therefore use the preregistered new "
        "anchor at 0.5 times their minimum inserted coordinate; each anchor is "
        "counted as a new direct coordinate.\n"
    )
    report_path.write_text(report, encoding="utf-8")
    manifest = s4._load_json(output_dir / "manifest.json")
    manifest["phase_b_amendment_sha256"] = EXPECTED_AMENDMENT_SHA256
    manifest["parent_phase_a_commit"] = EXPECTED_PHASE_A_COMMIT
    manifest["prediction_sha256"] = EXPECTED_PREDICTION_SHA256
    manifest["artifact_sha256"] = s4._artifact_hashes(output_dir)
    s4._write_json(output_dir / "manifest.json", manifest)
    if str(audit["status"]).startswith("complete_"):
        (output_dir / "COMPLETE").touch(exist_ok=False)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--phase-a-root", type=Path, required=True)
    parser.add_argument("--failed-phase-b-root", type=Path, required=True)
    parser.add_argument("--h01-root", type=Path, required=True)
    parser.add_argument("--p03-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    parser.add_argument("--gpu-id", type=int, default=0)
    args = parser.parse_args()
    result = run(
        args.project_root.resolve(),
        args.phase_a_root.resolve(),
        args.failed_phase_b_root.resolve(),
        args.h01_root.resolve(),
        args.p03_root.resolve(),
        args.output.resolve(),
        args.backend,
        args.gpu_id,
    )
    print(json.dumps(s4._jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
