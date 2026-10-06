#!/usr/bin/env python3
"""Finalize saved scalar truth records without restarting scientific acquisition."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import prospective_candidate_prediction as p
import prospective_input_reference as prep
import prospective_truth_scoring as s
import run_prospective_truth_scoring as runner

ACQUISITION_COMMIT = "014383636248cff06e4d7a307759550deb4543b0"
DOC = s.DOC + "/post_acquisition_continuation.md"
SOURCES = ("review_response/continue_prospective_truth_scoring.py",
           "review_tests/test_prospective_truth_scoring_continuation.py", DOC)
SEAL = s.DOC + "/continuation_manifest.json"
TESTS = (*runner.TESTS, SOURCES[1])


def deny_science(*args, **kwargs):
    raise prep.PreparationError("post-acquisition continuation forbids scientific acquisition")


@contextmanager
def scalar_only():
    """Block acquisition entry points and opening private array/runtime files."""
    targets = [(runner, "worker"), (runner, "execute"), (runner, "preflight"),
               (s, "ground_point"), (s, "full_unitary"), (s, "direct_helper"),
               (s, "eigh"), (s, "schur"), (prep, "load_input"),
               (prep, "ReferenceAdapter"), (prep, "component_exponential")]
    original = [(module, name, getattr(module, name)) for module, name in targets]
    active = [True]

    def hook(event, args):
        if active[0] and event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0]))
            if ".runtime" in path.parts or path.suffix.lower() in {".npz", ".npy", ".pkl", ".pickle"}:
                raise prep.PreparationError("post-acquisition continuation forbids array/runtime reads")

    sys.addaudithook(hook)
    try:
        for module, name, _ in original:
            setattr(module, name, deny_science)
        yield
    finally:
        active[0] = False
        for module, name, value in original:
            setattr(module, name, value)


def verify_saved(private, snapshot):
    if (snapshot["acquisition_execution_commit"] != ACQUISITION_COMMIT or
            snapshot["scientific_acquisition_completed_conditions"] != 13 or
            snapshot["completed_resolved_coordinates"] != 39 or
            snapshot["prior_technical_acquisition_retries"] != 1):
        raise prep.PreparationError("saved acquisition identity/counts differ")
    names = [row["path"] for row in snapshot["files"]]
    expected = {f"workers/{cid}/result.json" for cid in
                prep.read(private/"technical_retry_token.json")["ready_conditions"]}
    if len(names) != len(set(names)) or {n for n in names if n.endswith("/result.json")} != expected:
        raise prep.PreparationError("saved result file set differs")
    for row in snapshot["files"]:
        path = p.safe_member(private, row["path"])
        if path.stat().st_size != row["bytes"] or prep.sha_file(path) != row["sha256"]:
            raise prep.PreparationError("saved acquisition evidence changed: " + row["path"])


def continuation_source(root):
    manifest = prep.read(root/SEAL)
    if not manifest["manifest_self_excluded"] or {r["path"] for r in manifest["files"]} != set(SOURCES):
        raise prep.PreparationError("continuation source manifest differs")
    content = manifest["content_commit"]
    p.git(root, "merge-base", "--is-ancestor", ACQUISITION_COMMIT, content)
    p.git(root, "merge-base", "--is-ancestor", content, "HEAD")
    p.verify_blob(root, SEAL, "HEAD")
    p.verify_manifest(root, manifest["files"])
    for row in manifest["files"]:
        p.verify_blob(root, row["path"], content)
    return {"continuation_origin_result_commit": content,
            "verified_continuation_snapshot_commit": p.git(root, "rev-parse", "HEAD").decode().strip(),
            "continuation_manifest_sha256": prep.sha_file(root/SEAL), "continuation_sources": manifest["files"],
            "acquisition_execution_commit": ACQUISITION_COMMIT,
            "acquisition_and_scoring_sources_modified": False}


def aggregate_saved(root, private, prediction, protocol, specs, data):
    """Only JSON records; the unchanged identity verifier does no eigensolves."""
    expected = {r["condition"]["condition_id"]: r for r in prediction["conditions"]}
    records, counts = [], Counter({key: 0 for key in (*s.LIMITS, *s.ZERO, "target_phase_gap_diagnostics")})
    if len(specs) != 16 or {r["condition_id"] for r in specs} != set(expected):
        raise prep.PreparationError("attempted condition inventory differs")
    ready = set(expected)-set(p.TERMINAL)
    workers = private/"workers"
    if {d.name for d in workers.iterdir() if d.is_dir()} != ready:
        raise prep.PreparationError("saved worker inventory differs; terminal science forbidden")
    for spec in specs:
        cid = spec["condition_id"]
        if cid in p.TERMINAL:
            records.append({"condition_id": cid, "condition": spec, "status": p.TERMINAL[cid],
                            "ground": None, "points": [], "resource": {"counts": {}}, "truth_attempted": False})
            continue
        directory = workers/cid
        if (directory/"STOPPED.json").exists() or prep.read(directory/"current_phase.json")["stage"] != "condition_complete":
            raise prep.PreparationError("incomplete saved worker; never retry acquisition")
        row = prep.read(directory/"result.json")
        if row["condition_id"] != cid or row["condition"] != spec:
            raise prep.PreparationError("saved condition identity differs")
        if row["status"] != "truth_complete_valid" or len(row["points"]) != 3:
            raise prep.PreparationError("continuation requires the existing complete 39-coordinate acquisition")
        s.verify_truth_identity(expected[cid], row, protocol)
        resource, action = row["resource"], row["resource"]["counts"]
        checkpoint = prep.read(directory/"action_checkpoint.json")["counts"]
        for key, ceiling in {"exact_ground_solves": 1, "full_PF_materializations": 3, "direct_Schur_solves": 3}.items():
            if action.get(key) != ceiling or checkpoint.get(key) != ceiling:
                raise prep.PreparationError("saved action checkpoint/complete count differs")
        if any(action.get(k, 0) for k in s.ZERO) or any(checkpoint.get(k, 0) for k in s.ZERO):
            raise prep.PreparationError("forbidden saved acquisition action")
        if any(type(v) is not int or v < 0 for v in action.values()):
            raise prep.PreparationError("invalid saved action count")
        if (resource["BLAS_threads"] != 1 or resource["peak_rss_bytes"] > data["worker_rss_limit_bytes"] or
                resource["condition_wall_seconds"] > data["worker_wall_seconds"] or
                any(x["coordinate_wall_seconds"] > data["direct_coordinate_wall_seconds"] for x in row["points"])):
            raise prep.PreparationError("saved acquisition exceeded approved resource caps")
        counts.update(action)
        records.append(row)
    if any(counts[k] != cap for k, cap in s.LIMITS.items()) or any(counts[k] for k in s.ZERO):
        raise prep.PreparationError("aggregate action ceiling/forbidden action failed")
    return records, dict(counts)


def frozen_score(root, directory, truth_commit, prediction, protocol):
    """Commit/blob barrier must pass before any immutable scoring call."""
    s.verify_bundle(root, directory, truth_commit)
    return s.score_all(prediction, prep.read(directory/"truth.json"), protocol)


def state(control, status, **fields):
    prep.write(control/"run_status.json", {"status": status, "updated_UTC": prep.utc(),
               "continuation_pid": os.getpid(), "additional_scientific_actions": 0,
               "additional_acquisition_retries": 0, "next_science_authorized": False, **fields})


def finalize(root, private, runtime, allocation):
    control = private/"continuation"
    snapshot = prep.read(control/"saved_result_snapshot.json")
    verify_saved(private, snapshot)
    source = continuation_source(root)
    with scalar_only():
        prediction, protocol, specs, _, _, original_source = s.source_gate(root)
        data = runner.allocated(root, runtime, allocation)
        gate = prep.read(private/"pre_truth_gate.json")
        token = prep.read(private/"technical_retry_token.json")
        if (gate["status"] != "PASS" or gate["execution_HEAD"] != ACQUISITION_COMMIT or
                gate["truth_opened"] is not False or gate["fresh_allocation_sha256"] != prep.sha_file(allocation) or
                token["allocation_sha256"] != prep.sha_file(allocation) or
                token["pre_truth_gate_sha256"] != prep.sha_file(private/"pre_truth_gate.json")):
            raise prep.PreparationError("original pre-truth/allocation bytes differ")
        pre = prep.read(private/"pre_tests.json")
        if pre["HEAD"] != ACQUISITION_COMMIT or pre["returncode"] != 0 or pre["failures_or_skips"] or pre["passed"] != 190:
            raise prep.PreparationError("original pre-truth tests differ")
        for row in pre["test_sources"]:
            p.verify_blob(root, row["path"], ACQUISITION_COMMIT)
        for name in s.SOURCES:
            p.verify_blob(root, name, ACQUISITION_COMMIT)
        stopped = prep.read(private/"run_status.json")
        launch = prep.read(private/"background_launch.json")
        if stopped["status"] != "prospective_truth_scoring_stopped_review_required" or stopped["reason"] != "name 'Counter' is not defined":
            raise prep.PreparationError("unexpected acquisition stop; review required")
        for pid in (launch["coordinator_pid"], launch["outer_supervisor_pid"]):
            if Path(f"/proc/{pid}").exists():
                raise prep.PreparationError("previous acquisition process still exists; no concurrent finalization")
        continuation_pre = runner.passed_tests(root, control, "continuation_pre")
        if {r["path"] for r in continuation_pre["test_sources"]} != set(TESTS):
            raise prep.PreparationError("continuation pre-tests must include the inherited and continuation suites")
        records, counts = aggregate_saved(root, private, prediction, protocol, specs, data)
        if counts != snapshot["scientific_counts"]:
            raise prep.PreparationError("saved aggregate action counts changed")
        retry = {**token, "total_technical_acquisition_retries": 1, "scientific_retries": 0,
                 "additional_acquisition_retries": 0, "post_acquisition_scalar_continuation": True,
                 "authorization": snapshot["user_continuation_authorization"],
                 "authorization_scope": snapshot["authorization_scope"],
                 "snapshot_sha256": prep.sha_file(control/"saved_result_snapshot.json"),
                 "saved_acquisition_bytes_preserved": True,
                 "inner_frozen_runner_technical_retries": 0,
                 "accounting_note": "new_actions technical_retries is the unchanged inner acquisition ledger; the one outer pre-action retry is recorded separately here",
                 "original_stop": stopped, "original_launch_UTC": launch["launched_UTC"],
                 "worker_CPU_pool": launch["worker_allowed_CPU_pool"],
                 "shared_environment_modified": False}
        resource = {"new_actions": counts, "additional_actions_during_continuation": {k: 0 for k in (*s.LIMITS, *s.ZERO)},
                    "technical_retry_accounting": retry, "fresh_allocation_sha256": prep.sha_file(allocation),
                    "authority": data["authority"], "starts_UTC": data["starts_UTC"], "expires_UTC": data["expires_UTC"],
                    "deadline_renewed": False, "concurrent_worker_maximum": data["workers"], "BLAS_threads_per_worker": 1,
                    "worker_peak_RSS_bytes_from_saved_ledger": max(r["resource"]["peak_rss_bytes"] for r in records if r["ground"]),
                    "actual_total_peak_RSS_bytes": None, "total_peak_RSS_not_reconstructed_after_coordinator_stop": True,
                    "acquisition_wall_seconds_from_launch_to_stop": (datetime.fromisoformat(stopped["updated_UTC"])-datetime.fromisoformat(launch["launched_UTC"])).total_seconds(),
                    "approved_output_root_absolute": data["approved_output_root"],
                    "cumulative_disk_bytes": s.resource_guard(data), "disk_quota_bytes": data["writable_disk_quota_bytes"],
                    "stop_reserve_bytes": data["reserved_disk_bytes"],
                    "resource_monitor_limit": "periodic own-process watchdog; no native cgroup certificate; aggregate peak unavailable after original coordinator stopped"}
        access = {"workers": {r["condition_id"]: r["access"] for r in records if r["ground"]},
                  "terminal_condition_ground_truth_reads": 0, "historical_truth_array_reads": 0,
                  "prediction_modified": False, "continuation_array_runtime_reads": 0,
                  "continuation_acquisition_entry_points": "blocked; scalar JSON only"}
        truth = {"prediction_origin_result_commit": s.BASE, "prediction_sha256": s.PREDICTION_SHA,
                 "attempted_conditions": 16, "family_units": 4, "candidate_ready_conditions": 13,
                 "frozen_coordinates": 39, "conditions": records, "all_attempt_or_terminal_records_present": True,
                 "prediction_modified": False}
        runner.one_shot(control/"FINALIZATION_STARTED.json", "saved_scalar_truth_freeze_and_scoring")
        state(control, "prospective_truth_freezing", new_actions=counts)
        directory = root/s.OUTPUT/"truth"
        names = s.write_bundle(directory, "truth.json", "TRUTH_FROZEN.json", truth,
                   {**original_source, **source, "continuation_pre_tests": continuation_pre}, resource, access,
                   {"pre_truth_gate.json": gate, "pre_tests.json": pre, "pre_tests.log": (private/"pre_tests.log").read_bytes()})
        truth_commit = s.commit_bundle(root, directory, names, "Freeze saved prospective truth without additional scientific acquisition")
        prep.write(control/"truth_commit.json", {"commit": truth_commit})
        state(control, "prospective_immutable_scoring", truth_commit=truth_commit)
        scored = frozen_score(root, directory, truth_commit, prediction, protocol)
        verify_saved(private, snapshot)
        s.resource_guard(data)
    # Focused tests use synthetic fixtures only; no molecular acquisition occurs.
    original_tests = runner.TESTS
    try:
        runner.TESTS = TESTS
        post = runner.tests(root, control, "post")
    finally:
        runner.TESTS = original_tests
    with scalar_only():
        s.source_gate(root)
        s.verify_bundle(root, directory, truth_commit)
        verify_saved(private, snapshot)
        preservation = runner.root_preservation(root, private)
        state(control, "prospective_scoring_freezing", truth_commit=truth_commit)
        source = {**s.source_gate(root)[-1], **continuation_source(root), "truth_origin_result_commit": truth_commit}
        summary = runner.summary_markdown(scored, truth_commit, resource)
        summary += ("\nThe acquisition finished all 13 grounds and 39 PF/Schur coordinates, then stopped on a missing Counter import in aggregation. "
                    "The frozen acquisition/scorer sources and all saved worker bytes are preserved. "
                    "User-authorized scalar finalization resumed without any acquisition retry, array read or rule change. "
                    "The one prior pre-action technical acquisition retry remains separately accounted; scientific retries are zero.\n")
        complete = {"status": s.SUCCESS, "truth_origin_result_commit": truth_commit,
                    "prediction_origin_result_commit": s.BASE, "acquisition_execution_commit": ACQUISITION_COMMIT,
                    "denominators": scored["denominators"], "new_actions": counts,
                    "additional_scientific_actions": 0, "technical_acquisition_retries_total": 1,
                    "prediction_modified": False, "M1_adoption_modified": False, "next_science_authorized": False,
                    "publication_requires_remote_SHA_verification": True, "root_preservation": preservation}
        handoff = ("# Prospective truth/scoring handoff\n\n"
                   f"Status: `{s.SUCCESS}`. Prediction origin: `{s.BASE}`. Truth origin: `{truth_commit}`.\n\n"
                   "The final result origin commit is the commit containing this handoff. Manifest excludes itself. "
                   "Publication is complete only after a separate remote SHA/fetched-blob check.\n\n"
                   "Read summary.md, COMPLETE.json, scoring.json, ../truth/TRUTH_FROZEN.json, ../truth/truth.json, "
                   "source_audit.json, resource_audit.json, access_audit.json, test_audit.json and manifest.json. "
                   f"Then read {DOC} for the zero-acquisition continuation and limitations.\n\n"
                   "GPT review: evaluate frozen B0/B1 safety and cost-free oracle headroom. Compare raw M1 point/width/branch diagnostics "
                   "while preserving all abstentions and both h_ritz exclusions; retain 16/13/39/4 denominators and CH2 sector/stratum. "
                   "PF/H decomposition remains indeterminate without confirmed physical absolute-target correspondence. "
                   "The stopped coordinator's aggregate peak RSS cannot be reconstructed, and no cgroup certificate is claimed. "
                   "No new science, rescue, candidate/rank/width/gamma/gate modification or certificate is authorized.\n")
        final = root/s.OUTPUT/"final"
        names = s.write_bundle(final, "scoring.json", "SCORING_FROZEN.json", scored, source,
                   {**resource, "cumulative_disk_bytes_at_scoring": s.resource_guard(data)}, access,
                   {"COMPLETE.json": complete, "summary.md": summary, "handoff.md": handoff,
                    "test_audit.json": {"pre": pre, "continuation_pre": continuation_pre,
                                        "post": post, "legacy_molecular_truth_tests": 0},
                    "post_tests.json": post, "post_tests.log": (control/"post_tests.log").read_bytes()})
        final_commit = s.commit_bundle(root, final, names, "Freeze immutable prospective scoring and zero-acquisition continuation audit")
        s.source_gate(root)
        continuation_source(root)
        s.verify_bundle(root, directory, truth_commit)
        s.verify_bundle(root, final, final_commit)
        verify_saved(private, snapshot)
        preservation = runner.root_preservation(root, private)
        state(control, s.SUCCESS, truth_commit=truth_commit, result_commit=final_commit,
              denominators=scored["denominators"], new_actions=counts, focused_tests={"pre": pre["passed"], "post": post["passed"]},
              technical_acquisition_retries_total=1, root_preservation=preservation, blob_hash_gate="PASS",
              cumulative_disk_bytes=s.resource_guard(data), publication_status="pending")
        print(json.dumps({"status": s.SUCCESS, "truth_commit": truth_commit, "result_commit": final_commit,
                          "denominators": scored["denominators"], "additional_scientific_actions": 0}, sort_keys=True), flush=True)
    return final_commit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--allocation", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    private = root/s.OUTPUT/".private"
    try:
        finalize(root, private, args.runtime_root, args.allocation)
    except Exception as error:
        state(private/"continuation", "prospective_truth_scoring_stopped_review_required", reason=str(error))
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
