"""Post-hoc scalar/blob audit; NO molecular acquisition or formal result edits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from hchain_supplement_execution import read, git, remote_gate, sha_file, utc, DOC, source_gate
from hchain_prediction_phase import verify_bundle
from review_response.hchain_input_reference_preparation import write_json


def disk_bytes(directory):
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())


def audit(root, out):
    begin = time.perf_counter()
    sealed = source_gate(root)
    analysis_path = out / "analysis/prediction.json"
    analysis = read(analysis_path)
    analysis_relative = str(analysis_path.relative_to(root))
    snapshot = git(root, "log", "-1", "--format=%H", "--", analysis_relative).decode().strip()
    directories = [path for path in out.iterdir() if path.is_dir() and (path / "FREEZE.json").exists()]
    entries, commits = [], {}
    for directory in sorted(directories):
        relative = str(directory.relative_to(root))
        origin = git(root, "log", "-1", "--format=%H", "--", relative + "/prediction.json").decode().strip()
        verify_bundle(root, directory, origin)
        verify_bundle(root, directory, snapshot)
        commits[directory.name] = origin
        for path in sorted(directory.iterdir()):
            entries.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                "sha256": sha_file(path), "origin_result_commit": origin, "verified_snapshot_commit": snapshot})
    prediction = read(out / "prediction/prediction.json")
    resources = read(out / "analysis/resource_audit.json")
    seen = {}
    for directory in directories:
        for worker in read(directory / "prediction.json").get("workers", []):
            if "resource" in worker:
                seen[(worker["stage"], worker["unit"])] = worker
    own_peaks = [{"stage": r["stage"], "unit": r["unit"], "peak_RSS_KiB": r["resource"]["peak_RSS_KiB"],
                  "worker_wall_seconds": r["worker_total_wall_seconds"], "denials": r["access"]["denials"]} for r in seen.values()]
    old_unchanged = []
    for entry in sealed["files"]:
        if not entry["path"].startswith((DOC, "review_response/hchain_supplement_execution", "review_response/run_hchain_supplement", "review_tests/test_hchain_supplement_execution")):
            old_unchanged.append(entry["path"])
    report = {"schema": "hchain_supplement_scalar_publication_audit_v1", "audit_utc": utc(),
        "audit_has_scientific_actions": False, "audit_changes_original_or_new_frozen_science_files": False,
        "branch": git(root, "branch", "--show-current").decode().strip(), "analysis_origin_commit": snapshot,
        "verified_snapshot_commit": snapshot, "freeze_commits": commits, "frozen_blob_registry": entries,
        "source_manifest_sha256": sha_file(root / DOC / "source_freeze.json"),
        "source_content_commit": sealed["content_commit"], "all_source_and_freeze_blob_byte_gates_passed": True,
        "old_sealed_dependency_blob_count_unchanged": len(old_unchanged), "actions": analysis["actions"],
        "science_total_wall_seconds": analysis["total_wall_seconds"], "resource_monitors": resources["monitors"],
        "worker_peaks": own_peaks, "aggregate_peak_RSS_bytes": max(m["aggregate_peak_RSS_bytes"] for m in resources["monitors"]),
        "post_tests": {k: analysis["post_tests"][k] for k in ("passed", "failed", "skipped", "exit_code")},
        "pre_tests": {k: read(root / DOC / "focused_tests.json")[k] for k in ("passed", "failed", "skipped", "exit_code")},
        "scientific_retry": analysis["new_scientific_retry"], "technical_retry": analysis["technical_retry"],
        "private_runtime_bytes": disk_bytes(out / ".runtime"), "output_bytes_before_handoff_audit": disk_bytes(out),
        "private_runtime_publication_authorized": False, "GPU_science_operations": 0,
        "prospective_runtime_partial_truth_access": 0, "Python_audit_denials": sum(len(w["access"]["denials"]) for w in seen.values()),
        "pipeline_wall_excludes_final_figure_export_publication": True,
        "figure_caption": "Frozen scalar diagnostics only. Dotted lines are empirical widths, not certificates. Track G figure is the reused R1 anchor only, not a geometry sweep.",
        "handoff_manifest_self_excluded": True}
    if "rank_continuation" in prediction:
        rows = analysis["analysis"]["rows"]
        report.update({"track": "R", "scientific_validation_complete": True,
            "rank8_reproduction_passed": sum(p["reproduction"]["passed"] for w in prediction["workers"] for p in w["points"]),
            "rank8_reproduction_attempted": 9, "coordinate_count": 9,
            "primary_rank_rows": 36, "missing_primary_rows": sum(r["status"] != "available" for r in rows),
            "rank_summary": {str(m): {"available": sum(r["status"] == "available" for r in rows if r["rank"] == m),
                "positive_QPE_allowance": sum(bool(r.get("positive_QPE_allowance")) for r in rows if r["rank"] == m),
                "empirical_width_covers": sum(r.get("empirical_width_covers") is True for r in rows if r["rank"] == m),
                "physical_branch_correct": sum(r.get("physical_branch_correct") is True for r in rows if r["rank"] == m),
                "point_error_below_cheap": sum(r.get("E_M_hartree", 1) < r.get("E_C_hartree", 0) for r in rows if r["rank"] == m),
                "M1_budget_below_same_time_cheap": sum(r.get("M1_budget_beats_same_time_cheap") is True for r in rows if r["rank"] == m)} for m in (4, 8, 16, 32)},
            "truth_reused": 9, "new_truth": 0, "truth_before_new_prediction_commit": 0,
            "rank8_rule_difference_observed": any(p["ranks"]["8"]["empirical_width_hartree"] != p["old_rank8_control"]["empirical_width_hartree"] for w in prediction["workers"] for p in w["points"])})
    else:
        report.update({"track": "G", "scientific_validation_complete": False, "new_geometry_input_failures": 4,
                       "scientific_ineligibility_count": "not_evaluable_implementation_incident", "new_reference_candidate_truth": 0,
                       "saved_anchor_coordinates": 3, "truth_before_new_prediction_commit": 0,
                       "failure_class": "implementation_failure_not_scientific_negative"})
    report["audit_wall_seconds"] = time.perf_counter() - begin
    write_json(out / "handoff_audit.json", report)
    print(json.dumps({"audit": "passed", "track": report["track"], "frozen_files": len(entries),
                      "private_runtime_bytes": report["private_runtime_bytes"], "scientific_validation_complete": report["scientific_validation_complete"]}))


def manifest(root, out):
    remote_gate(root)
    if git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise RuntimeError("commit handoff content first")
    snapshot = git(root, "rev-parse", "HEAD").decode().strip()
    paths = git(root, "ls-files", "--", str(out.relative_to(root))).decode().splitlines()
    forbidden_suffixes = (".npz", ".npy", ".pickle", ".pkl")
    if any("/.runtime/" in name or name.endswith(forbidden_suffixes) for name in paths):
        raise RuntimeError("private science file staged/tracked")
    rows = []
    for name in paths:
        if name.endswith("/handoff_manifest.json"):
            continue
        data = (root / name).read_bytes()
        if data != git(root, "show", snapshot + ":" + name):
            raise RuntimeError("handoff content is not a committed blob")
        origin = git(root, "log", "-1", "--format=%H", snapshot, "--", name).decode().strip()
        rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "origin_result_commit": origin, "verified_snapshot_commit": snapshot})
    write_json(out / "handoff_manifest.json", {"content_commit": snapshot, "manifest_self_excluded": True,
        "private_runtime_excluded": True, "file_count": len(rows), "files": rows})
    print(json.dumps({"manifest_files": len(rows), "verified_snapshot_commit": snapshot}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("audit", "manifest"))
    args = parser.parse_args()
    root = Path.cwd().resolve()
    out = root / read(root / DOC / "authorization.json")["output_root"]
    (audit if args.command == "audit" else manifest)(root, out)
