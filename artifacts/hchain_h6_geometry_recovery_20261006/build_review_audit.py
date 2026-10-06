"""Read-only packaging of committed scalars; never imports a molecular runner."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from hchain_prediction_phase import verify_bundle, BUNDLE_FILES
from hchain_input_reference_preparation import sha_file, write_json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DOC = ROOT / "docs/second_study_v2/hchain_geometry_recovery_20261006"
FAILED = "e74fdec5e5085fd7c4f7a39fb4d59cec052f68f4"
STOPPED = "1633120317567e388a90c185fc7856439bb04819"


def read(path):
    return json.loads(Path(path).read_text())


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    final = read(OUT / "STOPPED/prediction.json")
    commits = {**final["freezes"], "STOPPED": STOPPED}
    checks = []
    for stage, commit in commits.items():
        verify_bundle(ROOT, OUT / stage, commit)
        changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()
        expected = {str((OUT / stage / name).relative_to(ROOT)) for name in BUNDLE_FILES}
        if set(changed) != expected:
            raise RuntimeError("freeze commit not exactly seven files: " + stage)
        checks.append({"stage": stage, "origin_result_commit": commit, "verified_snapshot_commit": STOPPED,
            "prediction_sha256": sha_file(OUT / stage / "prediction.json"),
            "manifest_sha256": sha_file(OUT / stage / "manifest.json"), "blob_gate_passed": True, "commit_files": 7})
    seal = read(DOC / "source_freeze.json")
    for row in seal["files"]:
        p = ROOT / row["path"]
        if sha_file(p) != row["sha256"] or p.read_bytes() != git("show", f"{seal['content_commit']}:{row['path']}"):
            raise RuntimeError("frozen source changed")
    for target in ("artifacts/hchain_h6_geometry_sweep_20261006", "docs/second_study_v2/hchain_supplement_execution_20261006",
                   "review_response/run_hchain_input_reference_preparation.py", "review_response/run_hchain_supplement.py"):
        git("diff", "--exit-code", FAILED, "--", target)
    pred = read(OUT / "prediction/prediction.json")
    reference = read(OUT / "reference_time/prediction.json")
    truth_workers = read(OUT / "truth/prediction.json")["workers"]
    rows, statuses = [], []
    for record in pred["workers"]:
        unit = record["unit"]
        cheap = record["cheap"]
        cores = [p["core_prediction"] if record.get("anchor_reused") else p["M1"] for p in record["M1"]]
        plan = reference["anchor_plan"][0] if record.get("anchor_reused") else cheap[0]
        for c, m in zip(cheap, cores, strict=True):
            rows.append({"geometry": unit, "origin": "saved_anchor" if record.get("anchor_reused") else "recovery",
                "candidate_id": c["candidate_id"], "time": c["time"], "time_hex": c["time_hex"],
                "delta_C_hartree": c["delta_C_hartree"], "delta_M_hartree": m.get("signed_shift_estimate_hartree"),
                "M1_width_hartree": m.get("empirical_width_hartree"), "M1_e_use_hartree": m.get("e_use_hartree"),
                "M1_abstained": m.get("abstained"), "M1_failure_reasons": json.dumps(m.get("failure_reasons")),
                "truth_safety_scored_in_recovery": False})
        statuses.append({"geometry": unit, "input_frozen": True, "reference_candidate_plan_ready": True,
            "t_ref": plan["t_ref"], "t_ref_hex": plan["t_ref_hex"],
            "candidate_times": [c["time"] for c in cheap], "candidate_time_hex": [c["time_hex"] for c in cheap],
            "M1_abstention_count": sum(bool(m.get("abstained")) for m in cores),
            "B0_B1_frozen_decisions": record["decisions"],
            "same_H_ground_status": "saved_anchor_reused" if record.get("anchor_reused") else "frozen",
            "direct_truth_status": "saved_anchor_reused_3" if record.get("anchor_reused") else "not_acquired_technical_failure",
            "recovery_performance_scoring": "not_performed"})
    parent_access = [r["access"] for stage in ("input_closure", "inputs", "reference_time", "prediction")
        for r in read(OUT / stage / "prediction.json")["workers"] if "access" in r]
    unexpected = [p for a in parent_access for p in a["allowed_repository_reads"]
        if "/ground/" in p or "/truth/" in p or "truth_scoring_20261004/truth" in p]
    if unexpected or any(a["denials"] for a in parent_access):
        raise RuntimeError("predictor access gate violation")
    resources = read(OUT / "STOPPED/resource_audit.json")
    peak = max(r["aggregate_peak_RSS_bytes"] for r in resources["monitors"])
    inventory = []
    for p in sorted((OUT / ".runtime").rglob("*")):
        if p.is_file():
            inventory.append({"path": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": sha_file(p)})
    incident = {"status": final["status"], "original_failed_commit": FAILED,
        "recovery_amendment_commit": seal["content_commit"], "source_freeze_commit": "8895102258f9e4d9e93cf96fcc8c4b7a51fdfae3",
        "prediction_commit": commits["prediction"], "stopped_commit": STOPPED,
        "source_blobs_verified": len(seal["files"]), "freeze_checks": checks,
        "original_failed_accounting": final["original_failed_run"], "recovery_actions": final["recovery_actions"],
        "cumulative_H_generation_attempts": 8, "cumulative_CISD_generation_attempts": 8,
        "unique_new_geometries": 4, "geometries_including_anchor": 5,
        "geometry_status": statuses, "new_direct_truth": 0, "saved_anchor_truth_reused": 3,
        "scoring_performed": False, "failure": final["failure"],
        "truth_worker_failures": [{k:r[k] for k in ("unit", "status", "failure_type", "failure_reason", "access")} for r in truth_workers],
        "cause": "Python import first attempts an unallowlisted __pycache__ path; source .py itself is sealed and allowlisted. PYTHONDONTWRITEBYTECODE disables writes, not attempted cache reads.",
        "source_py_is_in_allowlist": any(r["path"] == "review_response/hchain_truth_scoring.py" for r in seal["files"]),
        "pre_prediction_truth_bearing_reads": unexpected, "pre_prediction_denials": 0,
        "truth_worker_denials": sum(len(r["access"]["denials"]) for r in truth_workers),
        "truth_array_reads_in_failed_workers": 0, "exact_ground_generations_after_prediction": 4,
        "GPU_operations": 0, "workers_maximum": max(r["maximum_worker_concurrency"] for r in resources["monitors"]),
        "BLAS_PySCF_threads_per_worker": 1, "aggregate_peak_RSS_bytes": peak,
        "run_wall_seconds": final["total_wall_seconds"], "private_runtime_files": len(inventory),
        "private_runtime_bytes": sum(p["bytes"] for p in inventory), "private_runtime_manifest": inventory,
        "pre_test": read(DOC / "focused_tests.json"), "post_test": final["post_tests"],
        "second_recovery_or_resume_executed": False, "frozen_inputs_predictions_grounds_regenerated": False,
        "old_formal_records_unchanged": True, "Track_R_unchanged": final["Track_R_accepted_unchanged"],
        "review_decision_required": "Whether to authorize a separate truth-import infrastructure correction and bounded continuation from existing committed prediction/ground, with no input/reference/prediction regeneration. No such authorization is assumed.",
        "scalar_figures_scope": "prediction only; no direct truth comparisons, safety, gamma_req, coverage or performance claim"}
    write_json(OUT / "recovery_incident_audit.json", incident)
    with (OUT / "prediction_scalars.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(OUT / "geometry_status.json", statuses)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for unit in [r["geometry"] for r in statuses]:
        subset = [r for r in rows if r["geometry"] == unit]
        ratios = [.5, .65, .8]
        axes[0].plot(ratios, [abs(r["delta_C_hartree"]) for r in subset], "o-", label=unit)
        axes[1].plot(ratios, [r["M1_width_hartree"] for r in subset], "o-", label=unit)
    axes[0].set(ylabel="Absolute cheap shift (Ha)", xlabel="Frozen time / t_ref", yscale="log")
    axes[1].set(ylabel="Frozen empirical M1 width (Ha)", xlabel="Frozen time / t_ref", yscale="log")
    fig.suptitle("Frozen predictions only — new direct truth and safety scoring unavailable", fontsize=10)
    for axis in axes:
        axis.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "prediction_only.svg")
    fig.savefig(OUT / "prediction_only.png", dpi=160)
    plt.close(fig)
    print(json.dumps({"freeze_blob_gates": len(checks), "source_blobs": len(seal["files"]),
        "geometries": statuses, "aggregate_peak_RSS_GiB": peak / 1024**3,
        "private_runtime_bytes": incident["private_runtime_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
