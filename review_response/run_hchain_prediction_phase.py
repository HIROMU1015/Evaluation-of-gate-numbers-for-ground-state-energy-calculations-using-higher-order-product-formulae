"""One bounded truth-free candidate run with real Git q/H1 barriers."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

import numpy as np

from review_response.hchain_input_reference_preparation import (
    AllowlistedArchive, Ledger, PreparationError, VectorAdapter, bounded_stage,
    canonical_hash, sha_array, sha_file, write_json,
)
from review_response.hchain_prediction_phase import (
    BASE, DOC, OLD, PREP, PREP_DOC, NEW_SOURCES, CoordinateActions, ReadBoundary,
    check_remote, commit_bundle, finite_json, git, load_plan, make_bundle,
    preparation_gate, seal_source, source_gate, verify_bundle,
)
from review_response.hchain_selective_calibration_schedule import (
    BETA, EPSILON, run_shared_schedule, spectral_policy,
)
from review_response.pf_spectral_recoverability_d2 import analyze_coordinate


def utc():
    return datetime.now(timezone.utc).isoformat()


def fixed_environment(authorization):
    expected = authorization["environment"]
    actual = {"python": sys.executable, "python_version": platform.python_version(),
              "packages": {name: version(name) for name in expected["packages"]},
              "variables": {key: os.environ.get(key) for key in expected["variables"]}}
    if actual != expected or "cupy" in sys.modules:
        raise PreparationError("fixed CPU environment mismatch")
    return actual


def load_inputs(root, identity, ledger, access, sequence):
    runtime = root / PREP / ".runtime"
    entries = json.loads((root / PREP / "runtime_manifest.json").read_text())["files"]
    hashes = {entry["path"]: entry["sha256"] for entry in entries}
    systems = {}
    for system in ("H2", "H4", "H6"):
        spec = identity[system]
        keys = ["hamiltonian", "cisd", "sector_indices", *[
            f"group_{index:03d}" for index in range(len(spec["group_sha256_numpy_v1"]))]]
        name = f"{system}_predictor_input.npz"
        archive = AllowlistedArchive(runtime / name, hashes[name], keys, access)
        try:
            if set(archive.archive.files) != set(keys):
                raise PreparationError("sanitized archive member set mismatch")
            h = archive.read("hamiltonian")
            state = archive.read("cisd")
            indices = archive.read("sector_indices")
            groups = [archive.read(key) for key in keys[3:]]
        finally:
            archive.close()
        if (sha_array(h) != spec["H_sha256_numpy_v1"]
                or sha_array(state) != spec["CISD_sha256_numpy_v1"]
                or sha_array(indices) != spec["sector_indices_sha256_numpy_v1"]
                or [sha_array(group) for group in groups] != spec["group_sha256_numpy_v1"]):
            raise PreparationError("individual frozen input array identity mismatch")
        if h.shape != (spec["sector_dimension"],) * 2 or state.shape != (spec["sector_dimension"],):
            raise PreparationError("population sector dimension mismatch")
        if abs(float(np.linalg.norm(state)) - 1.0) > 1e-12:
            raise PreparationError("frozen CISD normalization mismatch")
        systems[system] = {"state": state, "identity": spec,
                           "adapter": VectorAdapter(h, groups, sequence, ledger,
                                                    allowed_kinds=("candidate", "m1"))}
        ledger.check_memory()
    return systems


def execute(root):
    started = time.perf_counter()
    start_utc = utc()
    authorization = json.loads((root / DOC / "authorization.json").read_text())
    if str(root) != authorization["worktree"] or git(root, "branch", "--show-current").decode().strip() != authorization["branch"]:
        raise PreparationError("same-worktree/runtime prediction branch required")
    check_remote(root)
    environment = fixed_environment(authorization)
    source = source_gate(root)
    runtime_identity = preparation_gate(root)
    output = root / authorization["output_root"]
    if output.exists():
        raise PreparationError("candidate run already started; no repeat or alternative output")
    inherited = json.loads((root / PREP_DOC / "implementation_manifest.json").read_text())
    allowed = [root / row["path"] for row in inherited["files"]]
    allowed += [root / name for name in NEW_SOURCES]
    allowed += [root / DOC / "implementation_manifest.json", root / PREP_DOC / "implementation_manifest.json"]
    allowed += list((root / OLD).glob("*"))
    allowed += [path for path in (root / PREP).iterdir() if path.is_file()]
    allowed += [root / PREP / ".runtime" / row["path"] for row in runtime_identity["files"]]
    boundary = ReadBoundary(root, allowed, output)
    sys.addaudithook(boundary.hook)
    ledger, member_reads = Ledger(), []
    output.mkdir()
    write_json(output / "STARTED.json", {"utc": start_utc, "HEAD": source["execution_HEAD"],
                                         "scope": "one_truth_free_prediction_run_no_scoring"})
    stage_commits, freeze_costs, action_inventory = {}, {}, {}
    nonfinite_fields = []
    observed_spectral = {}
    arm_wall = Counter()
    try:
        identity = json.loads((root / PREP / "input_identity.json").read_text())
        plan = load_plan(root / PREP / "candidate_plan.csv")
        pf_contract = json.loads((root / OLD / "system_and_pf_contract.json").read_text())["PF"]
        rank = json.loads((root / OLD / "rank_aware_M1_amendment.json").read_text())
        if any(row["K"] != pf_contract["K_by_system"][row["system"]]
               or row["primary_m"] != rank["fixed_by_system"][row["system"]]["primary"] for row in plan):
            raise PreparationError("K/primary does not match fixed contracts")
        sequence = [float.fromhex(value) for value in pf_contract["canonical_sequence_hex"]]
        if [float(value).hex() for value in pf_contract["s2_sequence"]] != pf_contract["canonical_sequence_hex"]:
            raise PreparationError("current_m3 coefficient identity mismatch")
        with bounded_stage(ledger, "shared_input_and_group_preprocessing", 1800):
            systems = load_inputs(root, identity, ledger, member_reads, sequence)
        events = []

        def resources():
            payload = ledger.payload()
            payload["combined_H1_cost"] = "measured_shared_path_inherited_schedule"
            return {**payload, "arm_wall_seconds": dict(arm_wall),
                    "coordinate_actions": dict(action_inventory), "freeze_overhead_seconds": dict(freeze_costs)}

        def cheap_acquire(system):
            remaining = 1800 - arm_wall["cheap"]
            if remaining <= 0:
                raise PreparationError("cheap arm total wall ceiling exceeded")
            before = time.perf_counter()
            points = []
            with bounded_stage(ledger, f"{system}_cheap", remaining):
                for row in [row for row in plan if row["system"] == system]:
                    point = systems[system]["adapter"].cheap(systems[system]["state"], row["time"], kind="candidate")
                    points.append({**point, "candidate_id": row["candidate_id"], "ratio": row["ratio"]})
            arm_wall["cheap"] += time.perf_counter() - before
            events.append({"event": "cheap_acquired", "system": system, "utc": utc()})
            return points, identity[system]["K"]

        def spectral_acquire(system):
            # Physical Git barrier checks occur BEFORE actions, not just a saved JSON flag.
            verify_bundle(root, output / "acquisition", stage_commits["ACQUISITION_FROZEN"])
            q_payload = json.loads((output / "acquisition" / "prediction.json").read_text())
            q = q_payload[system]["q"]
            if q == 0:
                verify_bundle(root, output / "h1", stage_commits["H1_FROZEN"])
            if system in observed_spectral:
                raise PreparationError("M1 system already acquired; no comparator rerun")
            remaining = 1800 - arm_wall["M1"]
            if remaining <= 0:
                raise PreparationError("M1 arm total wall ceiling exceeded")
            before = time.perf_counter()
            predictions, previous = [], None
            spec = rank["fixed_by_system"][system]
            with bounded_stage(ledger, f"{system}_M1", remaining):
                for row in [row for row in plan if row["system"] == system]:
                    ledger.charge("Arnoldi_chains", 9)
                    actions = CoordinateActions(systems[system]["adapter"], row["time"], spec["primary"])
                    prediction, previous = analyze_coordinate(
                        start=systems[system]["state"], apply_u=actions.pf, apply_h=actions.h,
                        time_value=row["time"], prefix_dimensions=spec["prefixes"],
                        primary_dimension=spec["primary"], previous_vector=previous,
                        numerical_rules=rank["numerical_rules"], epsilon_hartree=EPSILON,
                        beta=BETA, rotations_per_step=identity[system]["K"])
                    if actions.pf_count != actions.h_count or actions.pf_count != prediction["available_dimension"]:
                        raise PreparationError("one chain/prefix action accounting mismatch")
                    action_inventory[row["candidate_id"]] = {"PF_vector_actions": actions.pf_count,
                        "H_matvecs": actions.h_count, "path": "conditional_H1" if q else "comparator_only"}
                    finite = finite_json(prediction, row["candidate_id"], nonfinite_fields)
                    predictions.append({"candidate_id": row["candidate_id"], "time": row["time"],
                        "time_hex": row["time_hex"], "system": system, "q": q,
                        "e_use": finite["e_use_hartree"], "abstain": finite["abstained"],
                        "delta_M_hartree": finite["signed_shift_estimate_hartree"],
                        "width_M_hartree": finite["empirical_width_hartree"],
                        "claim_class": "empirical_width_not_certificate",
                        "H2_projected_solve_equals_sector": system == "H2",
                        "core_prediction": finite})
                    write_json(output / "checkpoints" / f"{row['candidate_id']}.json", predictions[-1])
            arm_wall["M1"] += time.perf_counter() - before
            observed_spectral[system] = predictions
            events.append({"event": "M1_acquired", "system": system, "q": q, "utc": utc()})
            return predictions

        def freeze(name, payload, digest):
            before = time.perf_counter()
            source_checkpoint = source_gate(root)
            preparation_gate(root)
            directory = output / ("acquisition" if name == "ACQUISITION_FROZEN" else "h1")
            saved_payload = payload if name == "ACQUISITION_FROZEN" else {
                "H1": payload, "conditional_M1": observed_spectral,
                "acquisition_commit": stage_commits["ACQUISITION_FROZEN"]}
            marker = {"kind": name, "payload_canonical_sha256": digest, "utc": utc(),
                      "truth_opened": False, "scoring_authorized": False}
            make_bundle(directory, saved_payload, marker, source_checkpoint,
                        boundary.payload(member_reads), resources())
            stage_commits[name] = commit_bundle(root, directory, f"Freeze H-chain {name} truth-free decisions")
            freeze_costs[name] = time.perf_counter() - before
            source_gate(root)
            events.append({"event": name, "commit": stage_commits[name], "utc": utc()})
            print(json.dumps(events[-1]), flush=True)

        replay = run_shared_schedule(("H2", "H4", "H6"), cheap_acquire, spectral_acquire, freeze)
        # Verify that comparator completion never changed either earlier decision snapshot.
        for name, directory in (("ACQUISITION_FROZEN", "acquisition"), ("H1_FROZEN", "h1")):
            verify_bundle(root, output / directory, stage_commits[name])
        if canonical_hash(replay["cheap"]) != replay["acquisition_hash"] or canonical_hash(replay["H1"]) != replay["H1_hash"]:
            raise PreparationError("final q/H1 decisions no longer frozen")
        comparator = {system: {"selected": spectral_policy(rows, replay["cheap"][system])[0],
                               "candidate_rows": spectral_policy(rows, replay["cheap"][system])[1]}
                      for system, rows in replay["always_M1_predictions"].items()}
        runtime_after = preparation_gate(root)
        if runtime_after != runtime_identity:
            raise PreparationError("original runtime/coordinates changed during run")
        source_after = source_gate(root)
        if "cupy" in sys.modules or boundary.denials:
            raise PreparationError("access/environment gate failed")
        counts = ledger.payload()["counts"]
        if counts["candidate_cheap_pf_actions"] != 9 or counts["candidate_h_exponential_actions"] != 9 or counts["Arnoldi_chains"] != 9:
            raise PreparationError("candidate count gate failed")
        resources_final = resources()
        resources_final["schedule"] = replay["resource"]
        combined = replay["resource"]["H1_combined_wall_seconds"]
        resources_final["H1_shared_path_net_of_freeze_seconds"] = combined - sum(freeze_costs.values())
        resources_final["H1_net_interval_excludes_shared_preprocessing"] = True
        resources_final["process_elapsed_before_final_write_seconds"] = time.perf_counter() - started
        resources_final["combined_cost_is_rigorous_envelope"] = False
        payload = {"status": authorization["success_status"], "cheap_B0_B1_B2_q": replay["cheap"],
                   "M1": replay["always_M1_predictions"], "always_M1_decisions": comparator,
                   "H1": replay["H1"], "stage_commits": stage_commits,
                   "acquisition_payload_sha256": replay["acquisition_hash"], "H1_payload_sha256": replay["H1_hash"],
                   "candidate_plan_sha256": runtime_identity["candidate_plan_sha256"],
                   "input_identity": identity, "runtime_identity": runtime_identity,
                   "nonfinite_fields": nonfinite_fields, "events": events,
                   "unmeasured": ["exact_ground", "direct_truth", "target_phase_gap", "branch_correctness",
                                  "width_coverage", "budget_safety", "holdout_performance"],
                   "scoring_authorized": False, "next_stage_authorized": False, "environment": environment}
        digest = make_bundle(output / "final", payload,
            {"kind": "PREDICTION_FROZEN", "status": authorization["success_status"],
             "utc": utc(), "truth_opened": False, "scoring_authorized": False,
             "acquisition_commit": stage_commits["ACQUISITION_FROZEN"], "H1_commit": stage_commits["H1_FROZEN"]},
            source_after, boundary.payload(member_reads), resources_final)
        write_json(output / "PREDICTION_FROZEN.json", {"status": authorization["success_status"],
            "prediction_sha256": digest, "final_manifest_sha256": sha_file(output / "final" / "manifest.json"),
            "stage_commits": stage_commits, "truth_opened": False, "scoring_authorized": False})
        print(json.dumps({"status": authorization["success_status"], "prediction_sha256": digest,
                          "q": {key: value["q"] for key, value in replay["cheap"].items()},
                          "stage_commits": stage_commits}), flush=True)
    except BaseException as error:
        write_json(output / "FAILURE.json", {"status": "prediction_integrity_or_resource_failure_stop",
            "utc": utc(), "error_type": type(error).__name__, "message": str(error),
            "stage_commits": stage_commits, "resources": ledger.payload(),
            "access": boundary.payload(member_reads), "no_retry_or_rescue_authorized": True})
        raise
    finally:
        boundary.enabled = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal-source", action="store_true")
    parser.add_argument("--test-log-dir", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.seal_source and args.test_log_dir:
        parser.error("choose one diagnostic mode")
    if args.test_log_dir:
        test_log(root, args.test_log_dir)
    elif args.seal_source:
        seal_source(root)
    else:
        execute(root)


def test_log(root, directory):
    """A fixed truth-free test allowlist; never run the legacy full suite here."""
    directory = directory.resolve()
    if directory.exists():
        raise PreparationError("test log directory exists")
    authorization = json.loads((root / DOC / "authorization.json").read_text())
    environment = fixed_environment(authorization)
    command = [sys.executable, "-m", "pytest", "-q", "-rs",
               "review_tests/test_hchain_prediction_phase.py",
               "review_tests/test_hchain_input_reference_preparation.py", "-p", "no:cacheprovider"]
    started_utc, before = utc(), time.perf_counter()
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=1800)
    finished_utc, seconds = utc(), time.perf_counter() - before
    directory.mkdir(parents=True)
    log = completed.stdout + completed.stderr
    (directory / "pytest.log").write_text(log)
    counts = {key: sum(int(value) for value in re.findall(rf"(\d+) {key}\b", log))
              for key in ("passed", "failed", "skipped", "error", "errors")}
    write_json(directory / "audit.json", {"command": command, "environment": environment,
        "started_utc": started_utc, "finished_utc": finished_utc, "wall_seconds": seconds,
        "exit_code": completed.returncode, "counts": counts, "log_sha256": sha_file(directory / "pytest.log"),
        "scope": "synthetic/source/access truth-free tests only; full legacy suite deferred"})
    print(log, end="")
    if completed.returncode or any(counts[key] for key in ("failed", "skipped", "error", "errors")) or counts["passed"] != 57:
        raise PreparationError("truth-free test gate failed")


if __name__ == "__main__":
    main()
