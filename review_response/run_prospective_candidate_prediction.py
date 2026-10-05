#!/usr/bin/env python3
"""One-shot CPU candidate acquisition and prediction seal; no truth phase."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import prospective_candidate_prediction as p
import prospective_input_reference as prep

TESTS = ("review_tests/test_prospective_input_reference.py",
         "review_tests/test_prospective_candidate_prediction.py")
CHEAP_FILES = ("prediction.json", "CHEAP_FROZEN.json", "resource_audit.json", "access_audit.json", "source_audit.json")
M1_FILES = ("prediction.json", "M1_FROZEN.json", "resource_audit.json", "access_audit.json", "source_audit.json")
FINAL_FILES = ("prediction.json", "PREDICTION_FROZEN.json", "candidate_plan.json", "source_audit.json",
               "resource_audit.json", "access_audit.json", "test_audit.json", "COMPLETE.json", "handoff.md")


def frozen_phase(root, output, phase, commit=None):
    directory = output / phase
    names = CHEAP_FILES if phase == "cheap" else M1_FILES
    p.require_members(p.verify_package(root, directory, commit), names)
    marker = prep.read(directory / ("CHEAP_FROZEN.json" if phase == "cheap" else "M1_FROZEN.json"))
    if marker["prediction_sha256"] != prep.sha_file(directory / "prediction.json") or marker["coordinate_count"] != 39 or marker["truth_opened"] is not False:
        raise prep.PreparationError("phase prediction SHA/truth/count seal differs")
    return prep.read(directory / "prediction.json")


def one_shot(directory, phase):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "STARTED.json").open("x") as stream:
        json.dump({"phase": phase, "started_UTC": prep.utc(), "scientific_retry_authorized": False}, stream)


def passed_tests(root, output, label):
    path = output / f"{label}_tests.json"
    record = prep.read(path)
    if record["label"] != label or record["returncode"] != 0 or record["failures_or_skips"] or record["passed"] <= 0:
        raise prep.PreparationError("focused tests require positive passes, fail/skip/error zero")
    if record["HEAD"] != p.git(root, "rev-parse", "HEAD").decode().strip():
        raise prep.PreparationError("focused tests must cover current execution commit")
    for row in record["test_sources"]:
        if prep.sha_file(root / row["path"]) != row["sha256"]:
            raise prep.PreparationError("tested source differs")
    if prep.sha_file(output / record["log"]) != record["log_sha256"]:
        raise prep.PreparationError("focused test log hash differs")
    return record


def run_tests(root, output, label):
    output.mkdir(parents=True, exist_ok=True)
    if (output / f"{label}_tests.json").exists():
        raise prep.PreparationError("test record already exists; preserve it and stop")
    command = [sys.executable, "-m", "pytest", "-q", "-rs", *TESTS, "-p", "no:cacheprovider"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=600)
    log = result.stdout + result.stderr
    name = f"{label}_tests.log"
    (output / name).write_text(log)
    match = re.search(r"(\d+) passed", log)
    record = {"label": label, "HEAD": p.git(root, "rev-parse", "HEAD").decode().strip(),
              "created_UTC": prep.utc(), "command": command, "returncode": result.returncode,
              "passed": int(match[1]) if match else 0,
              "failures_or_skips": bool(re.search(r"\b\d+ (?:failed|skipped|error|errors|xfailed|xpassed)\b", log)),
              "log": name, "log_sha256": prep.sha_file(output / name),
              "test_sources": [{"path": n, "sha256": prep.sha_file(root / n)} for n in TESTS]}
    prep.write(output / f"{label}_tests.json", record)
    passed_tests(root, output, label)
    print(log, end="")


def disk_bytes(roots):
    seen, total = set(), 0
    for directory in roots:
        for parent, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(parent) / d).is_symlink()]
            for name in files:
                path = Path(parent) / name
                if path.is_symlink():
                    continue
                stat = path.stat()
                inode = (stat.st_dev, stat.st_ino)
                if inode not in seen:
                    total += stat.st_size
                    seen.add(inode)
    return total


def allocation(root, runtime, output, path):
    if path is None:
        raise prep.PreparationError("fresh actual allocation and approved new output required")
    data = prep.read(path)
    prep.allocation_gate(data, output, evidence_root=path.parent)
    # This implementation deliberately runs one worker, never an unallocated host-wide pool.
    if data["workers"] != 1 or data["usable_cpu_quota"] > 16 or data["usable_ram_bytes"] > 128 * 2**30:
        raise prep.PreparationError("single-worker inherited CPU/RAM ceiling exceeded")
    if data["worker_rss_limit_bytes"] > 12 * 2**30 or data["worker_wall_seconds"] > 7200 or data["job_wall_seconds"] > 43200:
        raise prep.PreparationError("inherited worker/wall ceiling exceeded")
    if data["writable_disk_quota_bytes"] > 2 * 2**30:
        raise prep.PreparationError("cumulative disk quota exceeds inherited 2 GiB")
    start = datetime.fromisoformat(data["starts_UTC"])
    now = datetime.now(timezone.utc)
    if start.tzinfo is None or start > now or (now - start).total_seconds() >= data["job_wall_seconds"]:
        raise prep.PreparationError("job start/deadline gate failed")
    disk_roots = [Path(s).resolve() for s in data["cumulative_disk_roots"]]
    old = runtime.parent.resolve()
    if set(disk_roots) != {old, output.resolve()}:
        raise prep.PreparationError("disk accounting must include old P3 artifact and new output, controls inside either")
    expiry = datetime.fromisoformat(data["expires_UTC"])
    def guard():
        current = datetime.now(timezone.utc)
        if current >= expiry or (current - start).total_seconds() >= data["job_wall_seconds"]:
            raise prep.PreparationError("allocation deadline reached; stop without retry")
        used = disk_bytes(disk_roots)
        reserve = max(128 * 2**20, data.get("reserved_disk_bytes", 0))
        fs = os.statvfs(output)
        if used + reserve > data["writable_disk_quota_bytes"] or fs.f_bavail * fs.f_frsize < reserve:
            raise prep.PreparationError("cumulative disk quota/reserve gate failed")
    guard()
    return data, guard


def environment(identities):
    actual = prep.environment_readiness()
    for identity in identities.values():
        expected = identity["environment"]
        for key in ("python", "numpy", "scipy", "pyscf", "openfermion", "BLAS", "pyscf_threads"):
            if actual[key] != expected[key]:
                raise prep.PreparationError("P3 server environment identity differs: " + key)
    return actual


def runtime_gate(runtime, identities):
    paths = []
    for cid, identity in identities.items():
        if cid in p.TERMINAL:
            continue
        for row in identity["runtime_files"]:
            path = p.safe_member(runtime / cid, row["path"])
            if prep.sha_file(path) != row["sha256"]:
                raise prep.PreparationError("P3 frozen runtime differs")
            paths.append(path)
    return paths


def acquire(args, root, output, source, protocol, plan, identities):
    runtime = args.runtime_root
    if runtime is None or runtime.name != ".runtime" or runtime.is_symlink():
        raise prep.PreparationError("original P3 .runtime required; no transfer/regeneration")
    if runtime.parent.name != Path(p.PREP).name or (runtime.parent / "INPUT_FROZEN.json").read_bytes() != (root / p.PREP / "INPUT_FROZEN.json").read_bytes():
        raise prep.PreparationError("runtime must belong to the original frozen P3 artifact")
    data, guard = allocation(root, runtime, output, args.allocation)
    actual = environment(identities)
    runtime_files = runtime_gate(runtime, identities)
    passed_tests(root, output, "pre" if args.phase == "cheap" else "mid")
    cheap = None
    if args.phase == "m1":
        if not args.cheap_commit:
            raise prep.PreparationError("cheap commit/hash freeze required before M1")
        cheap = frozen_phase(root, output, "cheap", args.cheap_commit)
        p.check_rows(cheap["rows"], plan)
    directory = output / args.phase
    one_shot(directory, args.phase)
    allowed = runtime_files + [root / f for f in p.NEW_SOURCES]
    audit = p.ReadBoundary(root, runtime, allowed, output)
    sys.addaudithook(audit.hook)
    ledger = p.ActionLedger(data["worker_rss_limit_bytes"], args.phase, directory / "action_checkpoint.json", guard)
    rows, condition_resources = [], []
    started = time.monotonic()
    try:
        with prep.bounded_process(ledger, prep.remaining_worker_wall(data)):
            for cid, identity in identities.items():
                if cid in p.TERMINAL:
                    continue
                before = dict(ledger.counts)
                clock = time.perf_counter()
                h, state, groups = prep.load_input(identity, runtime / cid)
                ledger.counts["input_cache_bytes_verified"] += sum(r["bytes"] if "bytes" in r else
                    (runtime / cid / r["path"]).stat().st_size for r in identity.get("runtime_files", []))
                sequence = [float.fromhex(w) for w in identity["PF_sequence_hex"]]
                adapter_started = time.perf_counter()
                adapter = p.CandidateAdapter(h, groups, sequence, ledger)
                ledger.timings["group_component_spectrum_preprocessing"] += time.perf_counter() - adapter_started
                previous = None
                for coordinate in [c for c in p.coordinate_rows(plan) if c["condition_id"] == cid]:
                    ledger.new_coordinate()
                    if args.phase == "cheap":
                        raw = adapter.point(state, coordinate["time"])
                        if raw["time_hex"] != coordinate["time_hex"]:
                            raise prep.PreparationError("candidate time differs after acquisition")
                        row = {**coordinate, **raw, "actions": dict(ledger.coordinate_counts)}
                    else:
                        m1_started = time.perf_counter()
                        row, previous = p.spectral_coordinate(adapter, state, coordinate, protocol, previous)
                        ledger.timings["M1_total_including_projection_decision"] += time.perf_counter() - m1_started
                    rows.append(row)
                    prep.write(directory / "progress.json", {"rows": rows, "resource": ledger.payload()})
                condition_resources.append({"condition_id": cid, "wall_seconds": time.perf_counter() - clock,
                    "counts": {k: v - before.get(k, 0) for k, v in ledger.counts.items()}})
                del adapter, groups, h, state, previous
                gc.collect()
                guard()
        p.check_rows(rows, plan)
        if args.phase == "cheap" and any(ledger.counts[k] != 39 for k in ("candidate_pf_vector_actions", "candidate_h_exponential_actions")):
            raise prep.PreparationError("cheap action totals must equal 39/39")
        resource_audit = {**ledger.payload(), "phase": args.phase, "phase_wall_seconds": time.monotonic() - started,
                          "conditions": condition_resources, "environment": actual,
                          "cumulative_disk_bytes_at_phase_end": disk_bytes([runtime.parent, output]),
                          "allocation_sha256": prep.sha_file(args.allocation),
                          "allocation_authority": data["authority"], "expires_UTC": data["expires_UTC"],
                          "workers": 1, "BLAS_threads": 1, "scientific_retries": 0,
                          "resource_monitor_limit": "periodic own-process checks; native allocations not hard-cgroup certified"}
        prediction = {"phase": args.phase, "rows": rows, "attempted_conditions": 16, "terminal": p.TERMINAL}
        if args.phase == "cheap":
            prediction["decisions"] = {cid: p.cheap_decisions([r for r in rows if r["condition_id"] == cid], protocol)
                                       for cid in identities if cid not in p.TERMINAL}
        else:
            prediction["cheap_commit"] = args.cheap_commit
            prediction["cheap_manifest_sha256"] = prep.sha_file(output / "cheap/manifest.json")
            prediction["acquisition_policy"] = "all_39_unconditional_independent_of_cheap"
        prep.write(directory / "prediction.json", prediction)
        marker = "CHEAP_FROZEN.json" if args.phase == "cheap" else "M1_FROZEN.json"
        prep.write(directory / marker, {"prediction_sha256": prep.sha_file(directory / "prediction.json"),
                    "coordinate_count": 39, "created_UTC": prep.utc(), "truth_opened": False})
        prep.write(directory / "resource_audit.json", resource_audit)
        prep.write(directory / "access_audit.json", audit.payload())
        prep.write(directory / "source_audit.json", source)
        p.make_manifest(directory, CHEAP_FILES if args.phase == "cheap" else M1_FILES)
    except BaseException as error:
        # Do not call the failing quota/RSS gate again while preserving failure evidence.
        snapshot = {"counts": dict(ledger.counts), "named_stage_wall_seconds": dict(ledger.timings),
                    "peak_rss_bytes": ledger.peak_rss_bytes}
        prep.write(directory / "STOPPED.json", {"reason": str(error), "resource": snapshot,
                                              "no_scientific_retry": True, "truth_opened": False})
        raise
    finally:
        audit.enabled = False


def seal(args, root, output, source, protocol, specs, plan, identities):
    if not args.cheap_commit:
        raise prep.PreparationError("cheap commit required")
    cheap = frozen_phase(root, output, "cheap", args.cheap_commit)
    m1 = frozen_phase(root, output, "m1")
    tests = [passed_tests(root, output, name) for name in ("mid", "post")]
    # pre tests ran at the source commit before cheap commit; preserve their evidence.
    pre = prep.read(output / "pre_tests.json")
    p.git(root, "merge-base", "--is-ancestor", pre["HEAD"], "HEAD")
    if pre["returncode"] != 0 or pre["failures_or_skips"] or pre["passed"] <= 0 or prep.sha_file(output / pre["log"]) != pre["log_sha256"]:
        raise prep.PreparationError("pre-test evidence differs")
    if m1["cheap_commit"] != args.cheap_commit or m1["cheap_manifest_sha256"] != prep.sha_file(output / "cheap/manifest.json"):
        raise prep.PreparationError("M1 consumed different cheap freeze")
    final = output / "global"
    one_shot(final, "global_seal")
    result = p.global_prediction(root, protocol, specs, plan, identities, cheap, m1)
    resources = {phase: prep.read(output / phase / "resource_audit.json") for phase in ("cheap", "m1")}
    counts = {k: sum(r["counts"].get(k, 0) for r in resources.values()) for k in (*p.LIMITS, *p.FORBIDDEN)}
    if any(counts[k] for k in p.FORBIDDEN) or any(counts[k] > cap for k, cap in p.LIMITS.items()):
        raise prep.PreparationError("final action/truth ceilings differ")
    if counts["candidate_pf_vector_actions"] != 39 or counts["candidate_h_exponential_actions"] != 39:
        raise prep.PreparationError("missing cheap actions")
    if counts["M1_pf_vector_actions"] != counts["M1_h_matvecs"] or counts["M1_pf_vector_actions"] != sum(r["actual_M1_rank"] for r in m1["rows"]):
        raise prep.PreparationError("M1 aggregate accounting differs")
    accesses = {phase: prep.read(output / phase / "access_audit.json") for phase in ("cheap", "m1")}
    if any(r["denied_accesses"] for r in accesses.values()):
        raise prep.PreparationError("denied data access occurred")
    prep.write(final / "prediction.json", result)
    (final / "candidate_plan.json").write_bytes((root / p.PREP / "candidate_plan.json").read_bytes())
    prep.write(final / "source_audit.json", {**source, "cheap_commit": args.cheap_commit,
               "P3_candidate_plan_sha256": prep.sha_file(root / p.PREP / "candidate_plan.json"),
               "P3_review_bundle_manifest_sha256": prep.sha_file(root / p.PREP / "review_bundle_manifest.json"),
               "phase_manifests": {phase: prep.sha_file(output / phase / "manifest.json") for phase in ("cheap", "m1")}})
    prep.write(final / "resource_audit.json", {"new_actions": counts, "separate_phases": resources,
                "P3_reference_actions_not_new_candidate_actions": {"PF": 510, "H_exponential": 510},
                "peak_RSS_aggregation": "max_not_sum", "combined_H1_cost": "not_run_not_evaluable"})
    prep.write(final / "access_audit.json", accesses)
    prep.write(final / "test_audit.json", {"pre": pre, **{r["label"]: r for r in tests}, "legacy_truth_tests_run": 0})
    marker = {"status": p.SUCCESS, "created_UTC": prep.utc(), "truth_opened": False,
              "prediction_sha256": prep.sha_file(final / "prediction.json"), "cheap_commit": args.cheap_commit,
              "condition_count": 16, "family_units": 4, "ready_count": 13, "coordinate_count": 39}
    prep.write(final / "PREDICTION_FROZEN.json", marker)
    prep.write(final / "COMPLETE.json", marker)
    (final / "handoff.md").write_text(
        "# Prospective prediction freeze — truth not opened\n\n"
        f"Status: `{p.SUCCESS}`.\n\nRead PREDICTION_FROZEN.json, source_audit.json, prediction.json, "
        "resource_audit.json, access_audit.json, test_audit.json, manifest.json, in that order.\n\n"
        f"Preparation snapshot: `{p.BASE}`. Cheap commit: `{args.cheap_commit}`. "
        "Global publication commit is the commit containing this handoff (no self-reference).\n\n"
        f"16 attempted / 4 families; 13 ready / 39 coordinates; 3 terminal records retained. "
        f"M1 candidate abstentions: {result['M1_candidate_abstentions']}; condition abstentions: "
        f"{result['M1_condition_abstentions']}; missing predictions: 0.\n\n"
        f"New action counts: `{json.dumps(counts, sort_keys=True)}`.\n\n"
        "B0 is not assumed safe. No B2/H1, safety/branch/width-coverage scoring or certificate. "
        "CH2 is fixed-population triplet-sector feasibility, not a global ground claim. "
        "No truth acquisition is authorized. Stop here and return to GPT review.\n")
    p.make_manifest(final, FINAL_FILES)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("verify-source", "tests", "cheap", "m1", "seal", "verify-freeze"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--allocation", type=Path)
    parser.add_argument("--cheap-commit")
    parser.add_argument("--prediction-commit")
    parser.add_argument("--label", choices=("pre", "mid", "post"))
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    output = root / p.OUTPUT
    source = p.source_gate(root)
    protocol, specs, plan, identities = p.preparation_gate(root)
    if args.phase == "verify-source":
        print(json.dumps({"source": source, "conditions": 16, "coordinates": 39, "science_actions": 0}, sort_keys=True))
    elif args.phase == "tests":
        if not args.label:
            parser.error("tests requires --label")
        run_tests(root, output, args.label)
    elif args.phase in ("cheap", "m1"):
        acquire(args, root, output, source, protocol, plan, identities)
    elif args.phase == "seal":
        seal(args, root, output, source, protocol, specs, plan, identities)
    else:
        if not args.prediction_commit or p.git(root, "rev-parse", "HEAD").decode().strip() != args.prediction_commit:
            raise prep.PreparationError("verify-freeze requires HEAD equal final prediction commit")
        for phase, names in (("cheap", CHEAP_FILES), ("m1", M1_FILES), ("global", FINAL_FILES)):
            p.require_members(p.verify_package(root, output / phase, args.prediction_commit), names)
        frozen_phase(root, output, "cheap", args.prediction_commit)
        frozen_phase(root, output, "m1", args.prediction_commit)
        marker = prep.read(output / "global/PREDICTION_FROZEN.json")
        if marker["prediction_sha256"] != prep.sha_file(output / "global/prediction.json") or marker["status"] != p.SUCCESS or marker["truth_opened"] is not False:
            raise prep.PreparationError("global prediction seal differs")
        test_audit = prep.read(output / "global/test_audit.json")
        for label in ("pre", "mid", "post"):
            for name in (f"{label}_tests.json", f"{label}_tests.log"):
                p.verify_blob(root, f"{p.OUTPUT}/{name}", args.prediction_commit)
            if prep.read(output / f"{label}_tests.json") != test_audit[label] or prep.sha_file(output / f"{label}_tests.log") != test_audit[label]["log_sha256"]:
                raise prep.PreparationError("final test evidence hash/blob differs")
        print(json.dumps({"status": p.SUCCESS, "commit": args.prediction_commit, "blob_hash_gate": "PASS", "truth_opened": False}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (prep.PreparationError, FileExistsError, subprocess.CalledProcessError, KeyError, ValueError) as error:
        print("STOP:", error, file=sys.stderr)
        raise SystemExit(2)
