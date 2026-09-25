"""Corrective S0 exact-time scorer with H01-native branch anchors.

This runner implements the narrowly scoped v1.1 anchor-source amendment.  It
does not rerun or alter the frozen practical selector.  The failed v1.0 run is
preserved as evidence of the cross-source anchor mismatch.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
from typing import Any, Sequence

from review_response import run_pf_first_study_s0_exact_time_scoring as v1_0


_base = v1_0._base
ANCHOR_PROTOCOL = Path(
    "review_response/pf_first_study_s0_anchor_protocol_v1_1.json"
)
EXPECTED_ANCHOR_PROTOCOL_SHA256 = (
    "8f776ded65e42b7657d5c014cf525421b95cbbfb40aa0744c69d2c11f00204b1"
)
REQUIRED_TRUTH_PROVENANCE = "new_h01_continuous_branch_calculation"
_ORIGINAL_POINT_CACHE_KEY = _base._point_cache_key
_ORIGINAL_NEAREST_LOWER_ANCHOR = _base.nearest_lower_reliable_anchor


def _load_and_verify_amendment(project_root: Path) -> dict[str, Any]:
    path = project_root / ANCHOR_PROTOCOL
    if not path.is_file():
        raise _base.S0ValidationError("S0 v1.1 anchor protocol is missing")
    if _base._sha256(path) != EXPECTED_ANCHOR_PROTOCOL_SHA256:
        raise _base.S0ValidationError("S0 v1.1 anchor protocol hash mismatch")
    amendment = _base._load_json(path)
    if (
        amendment.get("parent_first_study_protocol_sha256")
        != _base.EXPECTED_FIRST_STUDY_PROTOCOL_SHA256
        or amendment.get("frozen_practical_predictions_sha256")
        != _base.EXPECTED_PREDICTIONS_SHA256
        or amendment["anchor_source_rule"].get("required_truth_provenance")
        != REQUIRED_TRUTH_PROVENANCE
    ):
        raise _base.S0ValidationError("S0 v1.1 anchor protocol identity mismatch")
    return amendment


def _is_h01_native_truth(point: dict[str, Any]) -> bool:
    return (
        point.get("truth_provenance") == REQUIRED_TRUTH_PROVENANCE
        and "h01_saved_truth" in point.get("truth_sources", [])
    )


def nearest_lower_h01_native_anchor(
    points: Sequence[dict[str, Any]],
    first_inserted_time: float,
    gates: dict[str, Any],
) -> dict[str, Any]:
    eligible = [point for point in points if _is_h01_native_truth(point)]
    if not eligible:
        raise _base.S0ValidationError("no H01-native saved truth points")
    return _ORIGINAL_NEAREST_LOWER_ANCHOR(
        eligible, first_inserted_time, gates
    )


def _point_cache_key_v1_1(
    condition: str,
    formula: str,
    time_value: float,
    backend: str,
    system: dict[str, Any],
) -> dict[str, Any]:
    key = _ORIGINAL_POINT_CACHE_KEY(
        condition, formula, time_value, backend, system
    )
    key["s0_anchor_protocol_sha256"] = EXPECTED_ANCHOR_PROTOCOL_SHA256
    return key


def _preflight_anchor_selections(
    project_root: Path,
    practical_root: Path,
    h01_root: Path,
    p03_root: Path,
    requested_conditions: Sequence[str] | None,
) -> dict[str, dict[str, Any]]:
    protocol, predictions = v1_0._verify_with_canonical_constant_keys(
        practical_root, project_root / _base.FIRST_STUDY_PROTOCOL
    )
    configured = list(
        protocol["S0_existing_practical_exact_time_scoring"]["conditions"]
    )
    conditions = configured if not requested_conditions else list(requested_conditions)
    if any(condition not in configured for condition in conditions):
        raise _base.S0ValidationError("requested condition outside frozen S0 scope")
    prediction_by_condition = {
        row["condition"]: row for row in predictions["conditions"]
    }
    selected: dict[str, dict[str, Any]] = {}
    for condition in conditions:
        selection = prediction_by_condition[condition]["selection"]
        formula = str(selection["selected_formula"])
        first_inserted_time = 0.99 * float(selection["selected_time"])
        points, _ = _base._source_truth_points(
            h01_root, p03_root, condition, formula
        )
        anchor = nearest_lower_h01_native_anchor(
            points, first_inserted_time, protocol["numerical_gates"]
        )
        selected[condition] = {
            "condition": condition,
            "formula": formula,
            "time": float(anchor["time"]),
            "signed_direct_shift_hartree": float(
                anchor["signed_direct_shift_hartree"]
            ),
            "truth_provenance": anchor["truth_provenance"],
            "truth_sources": list(anchor["truth_sources"]),
        }
    return selected


def _augment_v1_1_outputs(
    output_dir: Path, anchor_selections: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    branch_path = output_dir / "branch_audit.csv"
    with branch_path.open(encoding="utf-8", newline="") as handle:
        branch_rows = list(csv.DictReader(handle))
    for row in branch_rows:
        if row["point_role"] != "saved_lower_anchor_recomputation":
            row["anchor_source_domain"] = ""
            row["anchor_truth_provenance"] = ""
            row["anchor_truth_sources"] = ""
            continue
        anchor = anchor_selections[row["condition"]]
        if not _base._same_time(float(row["time"]), float(anchor["time"])):
            raise _base.S0ValidationError("recorded anchor differs from v1.1 preflight")
        row["anchor_source_domain"] = "H01-native"
        row["anchor_truth_provenance"] = str(anchor["truth_provenance"])
        row["anchor_truth_sources"] = json.dumps(
            anchor["truth_sources"], separators=(",", ":")
        )
    _base._write_csv(branch_path, branch_rows)

    source_manifest_path = output_dir / "source_manifest.json"
    source_manifest = _base._load_json(source_manifest_path)
    source_manifest["s0_anchor_protocol_sha256"] = (
        EXPECTED_ANCHOR_PROTOCOL_SHA256
    )
    source_manifest["anchor_selections"] = list(anchor_selections.values())
    _base._write_json(source_manifest_path, source_manifest)

    audit_path = output_dir / "audit.json"
    audit = _base._load_json(audit_path)
    audit["s0_anchor_protocol_sha256"] = EXPECTED_ANCHOR_PROTOCOL_SHA256
    audit["checks"]["s0_anchor_protocol_hash_match"] = (
        _base._sha256(output_dir / "s0_anchor_protocol.json")
        == EXPECTED_ANCHOR_PROTOCOL_SHA256
    )
    audit["checks"]["all_anchor_sources_h01_native"] = all(
        row["anchor_source_domain"] == "H01-native"
        and row["anchor_truth_provenance"] == REQUIRED_TRUTH_PROVENANCE
        for row in branch_rows
        if row["point_role"] == "saved_lower_anchor_recomputation"
    )
    if not all(audit["checks"].values()):
        audit["status"] = "failed_numerical_validation"
    _base._write_json(audit_path, audit)

    report_path = output_dir / "report.md"
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## S0 v1.1 anchor-source amendment\n\n"
            "The six branch anchors were selected only from H01-native saved "
            "truth records with provenance `new_h01_continuous_branch_calculation`, "
            "matching the H01 pickle used to reconstruct each PF unitary. The "
            "failed v1.0 result remains preserved; no frozen selector output, "
            "time, budget, threshold, truth triplet, or regret reference changed.\n"
        )

    marker = output_dir / "COMPLETE"
    if audit["status"] != "complete_exact_time_scoring" and marker.exists():
        marker.unlink()
    manifest_path = output_dir / "manifest.json"
    manifest = _base._load_json(manifest_path)
    manifest["status"] = audit["status"]
    manifest["s0_anchor_protocol_sha256"] = EXPECTED_ANCHOR_PROTOCOL_SHA256
    manifest["artifact_sha256"] = _base._artifact_hashes(output_dir)
    _base._write_json(manifest_path, manifest)
    return audit


def run(
    project_root: Path,
    practical_root: Path,
    h01_root: Path,
    p03_root: Path,
    output_dir: Path,
    backend: str,
    gpu_id: int,
    requested_conditions: Sequence[str] | None,
) -> dict[str, Any]:
    _load_and_verify_amendment(project_root)
    anchor_selections = _preflight_anchor_selections(
        project_root,
        practical_root,
        h01_root,
        p03_root,
        requested_conditions,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    amendment_copy = output_dir / "s0_anchor_protocol.json"
    shutil.copyfile(project_root / ANCHOR_PROTOCOL, amendment_copy)
    original_anchor = _base.nearest_lower_reliable_anchor
    original_cache_key = _base._point_cache_key
    _base.nearest_lower_reliable_anchor = nearest_lower_h01_native_anchor
    _base._point_cache_key = _point_cache_key_v1_1
    try:
        _base.run(
            project_root,
            practical_root,
            h01_root,
            p03_root,
            output_dir,
            backend,
            gpu_id,
            requested_conditions,
        )
        return _augment_v1_1_outputs(output_dir, anchor_selections)
    except Exception:
        marker = output_dir / "COMPLETE"
        if marker.exists():
            marker.unlink()
        raise
    finally:
        _base.nearest_lower_reliable_anchor = original_anchor
        _base._point_cache_key = original_cache_key


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--practical-root", type=Path, required=True)
    parser.add_argument("--h01-root", type=Path, required=True)
    parser.add_argument("--p03-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    parser.add_argument("--gpu-id", type=int, default=0)
    parser.add_argument("--conditions", nargs="*")
    args = parser.parse_args()
    audit = run(
        args.project_root.resolve(),
        args.practical_root.resolve(),
        args.h01_root.resolve(),
        args.p03_root.resolve(),
        args.output.resolve(),
        args.backend,
        args.gpu_id,
        args.conditions,
    )
    print(
        json.dumps(
            {"status": audit["status"], "accounting": audit["accounting"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
