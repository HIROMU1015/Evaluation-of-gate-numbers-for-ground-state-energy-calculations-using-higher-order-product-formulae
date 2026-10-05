"""Private P3 coordinator: bounded inputs -> explicit input commit -> references -> stop.

Uses the approved P2 implementation unchanged. Publication is local; the user pushes.
No candidate, M1, ground, truth, gap, scoring, GPU, or shared configuration operations.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import time

from bounded_supervisor import CONTROL, ROOT, footprint, read, run_worker, write

HANDOFF = "376190c41338d64554cee3e4f07b2f605d64ab95"
P1 = "dc10db0e2b9be860239cb18b0c9275bdd24617d2"
P2 = "e9b0981ec4e809c0dbcc77bfcf5a6efa653f7bdc"
BRANCH = "gpu-pf-study2-prospective-preparation-20261005"
REMOTE = "https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae.git"
ZERO_KEYS = ("candidate_cheap_actions", "M1_actions", "exact_ground_solves",
             "full_PF_materializations", "direct_truth_actions", "gap_actions",
             "performance_scoring", "GPU_operations")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(ROOT), *args])


def status(phase, **details):
    payload = {"status": phase, "updated_UTC": datetime.now(timezone.utc).isoformat(),
               "coordinator_pid": os.getpid(), "branch": BRANCH,
               "handoff_commit": HANDOFF, "P1_commit": P1, "P2_commit": P2,
               "output_root": str(OUTPUT), "workers": 1,
               "disk_quota_bytes": ALLOCATION["writable_disk_quota_bytes"],
               "expires_UTC": ALLOCATION["expires_UTC"], "push_responsibility": "user",
               **details}
    write(CONTROL / "run_status.json", payload)
    print(json.dumps(payload), flush=True)


def technical_gate():
    if datetime.now(timezone.utc) >= datetime.fromisoformat(ALLOCATION["expires_UTC"]):
        raise RuntimeError("global allocation expired; no further work")
    if footprint((CONTROL, OUTPUT)) >= ALLOCATION["writable_disk_quota_bytes"] - 128 * 2**20:
        raise RuntimeError("cumulative disk reservation exhausted")
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > ALLOCATION["coordinator_reserved_ram_bytes"]:
        raise RuntimeError("own coordinator RSS exceeds reserved RAM")


def verify_remote():
    if git("remote", "get-url", "origin").decode().strip() != REMOTE:
        raise RuntimeError("unapproved origin fetch URL")
    if git("remote", "get-url", "--push", "origin").decode().strip() != REMOTE:
        raise RuntimeError("unapproved origin push URL")
    if git("branch", "--show-current").decode().strip() != BRANCH:
        raise RuntimeError("research branch changed")


def commit_exact(paths, message):
    technical_gate()
    verify_remote()
    if git("diff", "--cached", "--name-only").strip():
        raise RuntimeError("unexpected preexisting staged files; refusing commit")
    expected = sorted(Path(p).relative_to(ROOT).as_posix() for p in paths)
    for path in expected:
        if ".runtime" in Path(path).parts or Path(path).suffix.lower() in {".npz", ".npy", ".pkl", ".pickle"}:
            raise RuntimeError("non-lightweight publication path")
    subprocess.run(["git", "-C", str(ROOT), "add", "--", *expected], check=True)
    actual = git("diff", "--cached", "--name-only").decode().splitlines()
    if sorted(actual) != expected:
        raise RuntimeError("index does not exactly match explicit lightweight allowlist")
    subprocess.run(["git", "-C", str(ROOT), "commit", "-m", message], check=True,
                   timeout=min(120, max(1, int((datetime.fromisoformat(ALLOCATION["expires_UTC"]) - datetime.now(timezone.utc)).total_seconds()))))
    commit = git("rev-parse", "HEAD").decode().strip()
    for path in expected:
        if git("show", commit + ":" + path) != (ROOT / path).read_bytes():
            raise RuntimeError("committed review blob does not match prepared bytes")
    return commit


def check_root_preserved():
    repo = ROOT.parents[1]
    baseline = read(CONTROL / "root_preservation_baseline.json")
    def original_git(*args):
        return subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), *args])
    checks = {"HEAD": original_git("rev-parse", "HEAD").decode().strip() == baseline["HEAD"],
              "branch": original_git("branch", "--show-current").decode().strip() == baseline["branch"],
              "index": sha(repo / ".git/index") == baseline["index_sha256"],
              "tracked_edit_hashes": all(sha(repo / p) == h for p, h in baseline["modified_tracked_files"].items()),
              "cached_diff": hashlib.sha256(original_git("diff", "--cached", "--binary")).hexdigest() == baseline["cached_diff_sha256"]}
    if not all(checks.values()):
        raise RuntimeError("root preservation verification failed; no unrelated edits made by this job")
    return checks


def publish_review(input_commit):
    technical_gate()
    report = read(OUTPUT / "report.json")
    if report["status"] != "prospective_input_reference_preparation_complete_review_required":
        raise RuntimeError("unexpected completion status")
    if report["condition_count"] != 16 or any(report["total_counts"].get(k, 0) for k in ZERO_KEYS):
        raise RuntimeError("scientific scope/action gate failed")
    for key in ("reference_pf_actions", "reference_h_exponential_actions"):
        if report["total_counts"].get(key, 0) > 544:
            raise RuntimeError("cumulative reference cap exceeded")
    review = OUTPUT / "review"
    review.mkdir(exist_ok=False)
    env = os.environ.copy()
    env.update(PYTHONPATH="src:review_response:.", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", TMPDIR=str(CONTROL / "tmp"))
    with (CONTROL / "focused_tests_after.log").open("x") as log:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rs",
                                 "review_tests/test_prospective_input_reference.py", "-p", "no:cacheprovider"],
                                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                timeout=min(120, max(1, int((datetime.fromisoformat(ALLOCATION["expires_UTC"]) - datetime.now(timezone.utc)).total_seconds()))))
    after = (CONTROL / "focused_tests_after.log").read_text()
    if result.returncode or "41 passed" not in after or " skipped" in after or " failed" in after:
        raise RuntimeError("post-preparation focused test gate failed")
    rows = []
    for spec in CONDITIONS:
        name = spec["condition_id"]
        directory = OUTPUT / "conditions" / name
        identity, reference = read(directory / "input_identity.json"), read(directory / "reference_result.json")
        rows.append({"condition_id": name, "family": spec["family"], "stratum": spec["stratum"],
                     "input_status": identity["status"], "input_failure_reason": identity.get("failure_reason"),
                     "reference_status": reference["status"], "reference_failure_reason": reference.get("failure_reason"),
                     "K": identity.get("K"), "sector_dimension": identity.get("sector_dimension"),
                     "CISD_dimension": identity.get("CISD", {}).get("dimension"),
                     "t_ref": reference.get("t_ref"), "t_ref_hex": reference.get("t_ref_hex"),
                     "candidate_plan_arithmetic": reference.get("candidate_plan", []),
                     "candidate_execution_ready": reference["status"] == "reference_candidate_plan_ready",
                     "input_resource": identity["resource"], "reference_resource": reference["resource"],
                     "input_command_resource": read(CONTROL / ("input_" + name + ".command_resource.json")),
                     "reference_command_resource": read(CONTROL / ("references_" + name + ".command_resource.json")),
                     "input_history_certificate_sha256": identity["server_history_certificate_sha256"],
                     "private_runtime_files": identity["runtime_files"]})
    summary = {"status": report["status"], "condition_denominator": 16, "family_units": 4,
               "family_condition_denominators": dict(Counter(c["family"] for c in CONDITIONS)),
               "origin_protocol_commit": P1, "verified_protocol_commit": P1,
               "origin_implementation_commit": P2, "verified_source_snapshot_commit": HANDOFF,
               "input_freeze_result_commit": input_commit,
               "verified_input_snapshot_commit": input_commit,
               "publication_snapshot": "commit containing this review; 40-character SHA recorded separately in private run_status.json",
               "total_counts": report["total_counts"], "conditions": rows,
               "focused_tests_before": {"passed": 41, "failed": 0, "skipped": 0},
               "focused_tests_after": {"passed": 41, "failed": 0, "skipped": 0},
               "loaded_backend_readiness": read(CONTROL / "source_environment_gate.json"),
               "root_preservation": check_root_preserved(), "shared_environment_changes": 0,
               "sequential_max_worker_RSS_bytes": max(r[p]["own_worker_peak_RSS_bytes"] for r in rows for p in ("input_command_resource", "reference_command_resource")),
               "coordinator_peak_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
               "coordinator_memory_reservation_bytes": ALLOCATION["coordinator_reserved_ram_bytes"],
               "actual_concurrent_total_RSS_bytes": "not_instrumented; process peaks are not summed as a measured concurrent peak",
               "cumulative_disk_bytes_before_publication": footprint((CONTROL, OUTPUT)),
               "disk_quota_bytes": ALLOCATION["writable_disk_quota_bytes"],
               "runtime_location": "${WORKTREE}/" + OUTPUT.relative_to(ROOT).as_posix() + "/.runtime/<condition_id>",
               "internal_expm_multiply_H_matvecs": "unknown_not_counted_as_one",
               "limitations": "preparation only; no candidate performance, holdout success, ground-state, safety or certification claim",
               "next_science_authorized": False, "push_status": "pending_user_push"}
    write(review / "preparation_summary.json", summary)
    allocation_summary = {**ALLOCATION, "approved_output_root": "${WORKTREE}/" + OUTPUT.relative_to(ROOT).as_posix(),
                          "raw_allocation_sha256": sha(CONTROL / "allocation.json"),
                          "sanitization": "absolute worktree path replaced with WORKTREE; quota/time/hash evidence unchanged"}
    write(review / "allocation_summary.json", allocation_summary)
    shutil.copyfile(CONTROL / "allocation_evidence.txt", review / "allocation_evidence.txt")
    shutil.copyfile(CONTROL / "source_environment_gate.json", review / "source_environment_gate.json")
    shutil.copyfile(CONTROL / "bounded_supervisor.py", review / "bounded_supervisor.py")
    shutil.copyfile(CONTROL / "preparation_pipeline.py", review / "preparation_pipeline.py")
    history_files = set()
    for certificate_file in CONTROL.glob("server_history_certificate*.json"):
        certificate = read(certificate_file)
        history_files.add(certificate_file)
        history_files.add(CONTROL / certificate["inventory_path"])
    for path in sorted(history_files):
        shutil.copyfile(path, review / path.name)
    log_metadata = []
    for name in ("focused_tests_before.log", "focused_tests_after.log"):
        original = CONTROL / name
        (review / name).write_text(original.read_text().replace(str(ROOT), "${WORKTREE}"))
        log_metadata.append({"file": name, "raw_sha256": sha(original), "sanitized_sha256": sha(review / name)})
    write(review / "test_log_provenance.json", {"logs": log_metadata, "sanitization": "absolute worktree path replaced"})
    complete_status = report["status"]
    handoff = f"""# Prospective P3 preparation handoff

Status: `{complete_status}`. Stop here; further scientific actions are not authorized.

Branch: `{BRANCH}`. Source handoff snapshot: `{HANDOFF}`.
Protocol origin/verified freeze: `{P1}`.
Implementation origin: `{P2}`; verified source snapshot: `{HANDOFF}`.
Input result/verified freeze commit: `{input_commit}`.
Result publication snapshot: the commit containing this document (40-character SHA is recorded in private run_status.json).
Publication: `pending_user_push`; this job performs local commits only, following the user's push instruction.

Read preparation_summary.json -> ../report.json -> ../candidate_plan.json -> allocation_summary.json -> server_history_certificate.json.
All16 conditions remain in the denominator; family inference units4. Detailed failures, fit/eligibility,
absolute candidate times/binary64 hex, sector/K/CISD dimensions, and command/stage resources are in preparation_summary.json.
Reference actions are cumulatively bounded by34/34 per condition and544/544 overall.
CISD-subspace and group-component eigensolves are separately counted; exact ground remains0.
Candidate/M1/full PF/direct truth/gap/scoring/GPU remain0. Internal expm_multiply matvec count is unknown.
Focused synthetic/stub tests before/after:41 passed, fail/skip0. Frozen source/protocol are unchanged.

CH2 scope is repository_tracked_family_unseen. Every matching blob was manually reviewed before science.
Private/untracked/archive payload/binary/unreachable/opaque unnamed dynamic geometries are outside this claim.
When internal refs change, a complete audit may reuse that manual review only for identical blob SHA256/OID
and previously reviewed paths; any unknown content stops for manual review.
Allocation authority: explicit user quota; one sequential worker, BLAS1, RSS12GiB, coordinator reserve32GiB,
usable RAM128GiB, CPU ceiling16, each phase2h, whole job12h, cumulative saved disk2GiB.
The watchdog signals only this job's worker process group. Periodic RSS/disk monitoring is not a native-cgroup guarantee.
Runtime files stay private in ../.runtime and are individually byte-hashed in frozen input identities.
GPT should review fit failures, domain eligibility, candidate plans and resource evidence before separately approving candidate/M1.
No protocol/grid/gamma/rank/geometry/state/claim change or failure rescue was performed.
"""
    (review / "handoff.md").write_text(handoff)
    reference_files = [OUTPUT / "conditions" / c["condition_id"] / "reference_result.json" for c in CONDITIONS]
    payload_files = reference_files + [OUTPUT / name for name in ("candidate_plan.json", "report.json", "manifest.json", "COMPLETE.json")]
    review_files = sorted(p for p in review.iterdir() if p.is_file())
    input_files = [OUTPUT / "INPUT_FROZEN.json"] + [OUTPUT / "conditions" / c["condition_id"] / "input_identity.json" for c in CONDITIONS]
    bundle = {"schema": "prospective_P3_review_bundle_v1", "manifest_self_excluded": True,
              "excluded": [".runtime", "private logs/checkpoints/controls outside review", "matrix/vector/state bytes"],
              "input_commit": input_commit, "files": [{"path": p.relative_to(OUTPUT).as_posix(), "sha256": sha(p)} for p in input_files + payload_files + review_files]}
    write(OUTPUT / "review_bundle_manifest.json", bundle)
    technical_gate()
    result_commit = commit_exact(payload_files + review_files + [OUTPUT / "review_bundle_manifest.json"],
                                "Publish prospective P3 input/reference preparation review")
    return result_commit, sha(OUTPUT / "manifest.json"), sha(OUTPUT / "review_bundle_manifest.json"), report


def main():
    with (CONTROL / "pipeline_started.json").open("x") as stream:
        json.dump({"created_UTC": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(), "science_retries": 0}, stream)
    verify_remote()
    if git("rev-parse", "HEAD").decode().strip() != HANDOFF:
        raise RuntimeError("initial source HEAD is not the approved handoff")
    if len(CONDITIONS) != 16 or len({c["condition_id"] for c in CONDITIONS}) != 16:
        raise RuntimeError("condition inventory differs")
    if read(CONTROL / "allocation.json")["workers"] != 1:
        raise RuntimeError("this coordinator reserves one worker")
    (CONTROL / "tmp").mkdir(exist_ok=True)
    status("prospective_P3_inputs_running")
    for spec in CONDITIONS:
        technical_gate()
        status("prospective_P3_inputs_running", active_condition=spec["condition_id"])
        run_worker("input", spec["condition_id"], None, ALLOCATION)
    run_worker("seal-inputs", None, None, ALLOCATION)
    input_files = [OUTPUT / "INPUT_FROZEN.json"] + [OUTPUT / "conditions" / c["condition_id"] / "input_identity.json" for c in CONDITIONS]
    input_commit = commit_exact(input_files, "Freeze prospective 16-condition input identities before reference")
    write(CONTROL / "input_commit.json", {"commit": input_commit})
    status("prospective_P3_references_running", input_commit=input_commit)
    for spec in CONDITIONS:
        technical_gate()
        status("prospective_P3_references_running", input_commit=input_commit, active_condition=spec["condition_id"])
        run_worker("references", spec["condition_id"], input_commit, ALLOCATION)
    run_worker("seal-references", None, input_commit, ALLOCATION)
    status("prospective_P3_local_review_publication_running", input_commit=input_commit)
    result_commit, manifest_hash, bundle_hash, report = publish_review(input_commit)
    status(report["status"], input_commit=input_commit, result_commit=result_commit,
           manifest_sha256=manifest_hash, review_bundle_manifest_sha256=bundle_hash,
           total_counts=report["total_counts"], phase_status_counts=report["phase_status_counts"],
           next_science_authorized=False, push_status="pending_user_push",
           push_command=f'git -C "{ROOT}" push origin {result_commit}:refs/heads/{BRANCH}')


ALLOCATION = read(CONTROL / "allocation.json")
OUTPUT = Path(ALLOCATION["approved_output_root"])
CONDITIONS = read(ROOT / "docs/second_study_v2/prospective_core_protocol_20261005/conditions.json")

if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        status("prospective_preparation_stopped_review_required", failure_type=type(error).__name__,
               failure_reason=str(error), scientific_retries=0,
               next_science_authorized=False, preserved_artifacts=True)
        raise
