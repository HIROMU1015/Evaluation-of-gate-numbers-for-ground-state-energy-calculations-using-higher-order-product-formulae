"""Synthetic and saved truth-free P3 metadata tests only; no molecular acquisition."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix, save_npz

import prospective_candidate_prediction as p
import prospective_input_reference as prep
import run_prospective_candidate_prediction as runner

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = prep.read(ROOT / prep.DOC / "protocol.json")
SPECS = prep.read(ROOT / prep.DOC / "conditions.json")
PLAN = prep.read(ROOT / p.PREP / "candidate_plan.json")


def point(t=.5, error=1e-6, ratio=.8):
    return {"time": t, "time_hex": t.hex(), "delta_C_hartree": error,
            "K": 9108, "ratio": ratio, "coordinate_id": str(t)}


def test_inventory():
    assert len(p.validate_plan(PLAN, SPECS)) == 13
    assert len(p.coordinate_rows(PLAN)) == 39
    assert len({r["coordinate_id"] for r in p.coordinate_rows(PLAN)}) == 39
    assert [r["condition_id"] for r in PLAN["all_conditions"] if r["status"] != "reference_candidate_plan_ready"] == list(p.TERMINAL)


@pytest.mark.parametrize("mutation", ("hex", "time", "ratio", "missing", "duplicate", "terminal", "domain"))
def test_plan_rejects_change(mutation):
    changed = deepcopy(PLAN)
    if mutation == "hex":
        changed["candidates"][0]["time_hex"] = .7.hex()
    elif mutation == "time":
        changed["candidates"][0]["time"] += 1e-12
    elif mutation == "ratio":
        changed["candidates"][0]["ratio"] = .65
    elif mutation == "missing":
        changed["all_conditions"].pop()
    elif mutation == "duplicate":
        changed["candidates"][1] = changed["candidates"][0]
    elif mutation == "terminal":
        changed["all_conditions"][0]["status"] = "reference_candidate_plan_ready"
    else:
        changed["candidates"][0]["time"] = 2.
        changed["candidates"][0]["time_hex"] = 2..hex()
    with pytest.raises(prep.PreparationError):
        p.validate_plan(changed, SPECS)


@pytest.mark.parametrize("gamma", (1., 1.01, 1.02, 1.05, 1.10))
def test_gamma_multiplies_budget_not_error(gamma):
    c = PROTOCOL["resource"]["epsilon_E"] * .5
    base = PROTOCOL["resource"]["beta"] * 9108 / (.5 * (PROTOCOL["resource"]["epsilon_E"] - c))
    assert p.budget(.5, c, 9108, PROTOCOL, gamma) == gamma * base


@pytest.mark.parametrize("t,c", ((0., 1e-6), (-1., 1e-6), (.5, -1.), (.5, float("inf")),
                                 (.5, float("nan")), (.5, PROTOCOL["resource"]["epsilon_E"])))
def test_allowance(t, c):
    assert p.budget(t, c, 1, PROTOCOL) is None


def test_earliest_exact_budget_tie_and_no_fallback():
    rows = [{"eligible": True, "budget": 10., "time": t} for t in (1.2, .8, 1.)]
    assert p.select(rows, "abstain")["selected"]["time"] == .8
    assert p.select([], "abstain") == {"status": "abstain", "selected": None, "fallback": False}


def test_four_gamma_and_anchor_not_assumed_safe():
    decisions = p.cheap_decisions([point(), point(.7, ratio=1.), point(.8, ratio=1.2)], PROTOCOL)
    assert [r["gamma"] for r in decisions["B1"]] == [1.01, 1.02, 1.05, 1.10]
    assert decisions["B0"]["role"] == "benchmark_only_not_safe_or_fallback"
    assert decisions["B0"]["safety"] == "not_evaluated"
    assert decisions["B0"]["time_hex"] == .5.hex()


def test_nonfinite_serialization_does_not_zero_width():
    missing = []
    row = p.finite_json({"width": float("inf"), "abstained": True}, missing)
    assert row == {"width": None, "abstained": True}
    assert missing[0]["original"] == "inf"


@pytest.mark.parametrize("phase,name", (("cheap", "reference_pf_actions"), ("cheap", "reference_h_exponential_actions"),
                                       ("m1", "M1_pf_vector_actions"), ("m1", "M1_h_matvecs")))
def test_per_coordinate_cap_and_attempt_checkpoint(tmp_path, phase, name):
    ledger = p.ActionLedger(2**40, phase, tmp_path / "checkpoint.json")
    cap = 1 if phase == "cheap" else 8
    for _ in range(cap):
        ledger.charge(name)
    with pytest.raises(prep.PreparationError):
        ledger.charge(name)
    key = {"reference_pf_actions": "candidate_pf_vector_actions", "reference_h_exponential_actions": "candidate_h_exponential_actions"}.get(name, name)
    assert prep.read(tmp_path / "checkpoint.json")["counts"][key] == cap
    assert ledger.counts[key] == cap


@pytest.mark.parametrize("name", p.FORBIDDEN)
def test_forbidden_actions(tmp_path, name):
    ledger = p.ActionLedger(2**40, "m1", tmp_path / "checkpoint.json")
    with pytest.raises(prep.PreparationError):
        ledger.charge(name)
    assert sum(ledger.counts.values()) == 0


def test_global_cap(tmp_path):
    ledger = p.ActionLedger(2**40, "cheap", tmp_path / "checkpoint.json")
    ledger.counts["candidate_pf_vector_actions"] = 39
    with pytest.raises(prep.PreparationError):
        ledger.charge("reference_pf_actions")


@pytest.mark.parametrize("dimension", (2, 8))
def test_shared_prefix_actions_and_breakdown_no_rescue(tmp_path, dimension):
    # Analytic synthetic diagonal U/H; never load a molecular ground/truth state.
    values = np.linspace(0., .03, dimension)
    h = csr_matrix(np.diag(values))
    ledger = p.ActionLedger(2**40, "m1", tmp_path / "checkpoint.json")
    adapter = p.CandidateAdapter(h, iter([h]), [1.], ledger)
    state = np.ones(dimension, dtype=complex) / np.sqrt(dimension)
    coordinate = {**point(), "coordinate_id": "synthetic", "time": .5, "time_hex": .5.hex()}
    row, _ = p.spectral_coordinate(adapter, state, coordinate, PROTOCOL, None)
    assert row["actual_M1_rank"] <= dimension
    assert ledger.counts["M1_pf_vector_actions"] == ledger.counts["M1_h_matvecs"] == row["actual_M1_rank"]
    core = row["core_prediction"]
    assert row["width_M_hartree"] == max(core["local_residual_width_hartree"], core["prefix_width_hartree"])
    state = np.eye(dimension, dtype=complex)[0]
    ledger.new_coordinate()
    row, _ = p.spectral_coordinate(adapter, state, coordinate, PROTOCOL, None)
    assert not row["eligible"]
    assert "primary_dimension_unavailable" in row["failure_reasons"]
    assert row["budget"] is None


def test_vector_only_before_charge(tmp_path):
    ledger = p.ActionLedger(2**40, "m1", tmp_path / "checkpoint.json")
    adapter = p.CandidateAdapter(csr_matrix(np.eye(2)), iter([csr_matrix(np.eye(2))]), [1.], ledger)
    for action in (lambda: adapter.pf(np.eye(2), .5), lambda: adapter.h_matvec(np.eye(2))):
        with pytest.raises(prep.PreparationError):
            action()
    assert ledger.counts["M1_pf_vector_actions"] == ledger.counts["M1_h_matvecs"] == 0


def test_open_boundary(tmp_path):
    root, runtime, output = tmp_path / "repo", tmp_path / "old/.runtime", tmp_path / "out"
    allowed = runtime / "state.npz"
    boundary = p.ReadBoundary(root, runtime, [allowed], output)
    boundary.hook("open", (str(allowed), "r", os.O_RDONLY))
    boundary.hook("open", (str(output / "result.json"), "w", os.O_WRONLY | os.O_CREAT))
    for path in (root / "truth.json", runtime / "exact.npz", runtime.parent / "truth.json"):
        with pytest.raises(prep.PreparationError):
            boundary.hook("open", (str(path), "r", os.O_RDONLY))
    with pytest.raises(prep.PreparationError):
        boundary.hook("open", (str(allowed), "w", os.O_WRONLY))
    assert not boundary.payload()["OS_hermeticity_claim"]


@pytest.mark.parametrize("name", ("../escape", "/absolute", "linked"))
def test_manifest_path_guard(tmp_path, name):
    (tmp_path / "target").write_text("scalar")
    (tmp_path / "linked").symlink_to(tmp_path / "target")
    with pytest.raises(prep.PreparationError):
        p.safe_member(tmp_path, name)


def test_seal_tampering_and_membership(tmp_path):
    prep.write(tmp_path / "prediction.json", {"truth_opened": False})
    p.make_manifest(tmp_path, ["prediction.json"])
    manifest = p.verify_package(tmp_path, tmp_path)
    with pytest.raises(prep.PreparationError):
        p.require_members(manifest, ["prediction.json", "extra"])
    (tmp_path / "prediction.json").write_text("changed")
    with pytest.raises(prep.PreparationError):
        p.verify_package(tmp_path, tmp_path)


def test_one_shot_preserves_failed_attempt(tmp_path):
    runner.one_shot(tmp_path, "cheap")
    with pytest.raises(FileExistsError):
        runner.one_shot(tmp_path, "cheap")


def test_global_inventory_and_no_truth_claim():
    identities = {s["condition_id"]: prep.read(ROOT / p.PREP / "conditions" / s["condition_id"] / "input_identity.json") for s in SPECS}
    rows = [{**r, "delta_C_hartree": 1e-6} for r in p.coordinate_rows(PLAN)]
    cheap = {"rows": rows, "decisions": {cid: p.cheap_decisions([r for r in rows if r["condition_id"] == cid], PROTOCOL) for cid in identities if cid not in p.TERMINAL}}
    m1 = {"rows": [{**r, "budget": None, "eligible": False} for r in p.coordinate_rows(PLAN)]}
    result = p.global_prediction(ROOT, PROTOCOL, SPECS, PLAN, identities, cheap, m1)
    assert len(result["conditions"]) == 16
    assert result["M1_condition_abstentions"] == 13
    assert result["M1_candidate_abstentions"] == 39
    assert result["missing_candidate_predictions"] == 0
    assert sum(r["predictions"] is None for r in result["conditions"]) == 3
    assert result["safety_branch_accuracy_width_coverage"].startswith("not_evaluated")
    changed = deepcopy(cheap)
    changed["decisions"]["LiH_R1.80"]["B0"]["gamma"] = 1.01
    with pytest.raises(prep.PreparationError):
        p.global_prediction(ROOT, PROTOCOL, SPECS, PLAN, identities, changed, m1)


def test_runner_has_no_truth_or_input_generation_entrypoint():
    tree = ast.parse((ROOT / "review_response/run_prospective_candidate_prediction.py").read_text())
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"create_input", "cisd_state", "eigsh", "eigh", "eig", "build_full_pf", "score", "run_pyscf"}
    assert runner.TESTS == ("review_tests/test_prospective_input_reference.py", "review_tests/test_prospective_candidate_prediction.py")


def test_runtime_no_terminal_access(tmp_path):
    identities = {cid: {"runtime_files": [{"path": "forbidden"}]} for cid in p.TERMINAL}
    assert runner.runtime_gate(tmp_path, identities) == []


@pytest.mark.parametrize("failed", (True, False))
def test_test_report_gate(tmp_path, monkeypatch, failed):
    monkeypatch.setattr(p, "git", lambda *_: b"fixed_head")
    (tmp_path / "pre_tests.log").write_text("1 passed\n")
    report = {"label": "pre", "HEAD": "fixed_head", "returncode": 0, "failures_or_skips": failed,
              "passed": 1, "test_sources": [], "log": "pre_tests.log", "log_sha256": prep.sha_file(tmp_path / "pre_tests.log")}
    prep.write(tmp_path / "pre_tests.json", report)
    if failed:
        with pytest.raises(prep.PreparationError):
            runner.passed_tests(tmp_path, tmp_path, "pre")
    else:
        assert runner.passed_tests(tmp_path, tmp_path, "pre")["passed"] == 1


def test_synthetic_all_coordinate_acquisition_schedule(tmp_path, monkeypatch):
    # Real phase orchestration, but every molecular loader/allocation is replaced
    # with an explicitly synthetic eight-dimensional fixture. No P3 runtime read.
    output = tmp_path / "new_output"
    frozen = tmp_path / p.PREP / "INPUT_FROZEN.json"
    frozen.parent.mkdir(parents=True)
    frozen.write_text("synthetic fixture, not operational P3")
    runtime = frozen.parent / ".runtime"
    runtime.mkdir()
    identities = {s["condition_id"]: {"PF_sequence_hex": [1..hex()]} for s in SPECS}
    h = csr_matrix(np.diag(np.linspace(0., .03, 8)))
    state = np.ones(8, dtype=complex) / np.sqrt(8)
    monkeypatch.setattr(runner, "allocation", lambda *_: ({"worker_rss_limit_bytes": 2**40,
        "worker_wall_seconds": 600, "authority": "synthetic_only", "expires_UTC": "synthetic"}, lambda: None))
    monkeypatch.setattr(runner, "environment", lambda *_: {"synthetic_only": True})
    monkeypatch.setattr(runner, "runtime_gate", lambda *_: [])
    monkeypatch.setattr(runner, "passed_tests", lambda *_: {"synthetic_only": True})
    monkeypatch.setattr(prep, "remaining_worker_wall", lambda *_: 600.)
    monkeypatch.setattr(prep, "load_input", lambda *_: (h.copy(), state.copy(), iter([h.copy()])))
    monkeypatch.setattr(runner.sys, "addaudithook", lambda *_: None)
    monkeypatch.setattr(p, "git", lambda *_: b"synthetic_commit")
    monkeypatch.setattr(p, "verify_blob", lambda *_: None)
    allocation_path = output / ".private/allocation.json"
    prep.write(allocation_path, {"synthetic_only": True})
    args = SimpleNamespace(phase="cheap", runtime_root=runtime, allocation=allocation_path, cheap_commit=None)
    runner.acquire(args, tmp_path, output, {}, PROTOCOL, PLAN, identities)
    cheap = prep.read(output / "cheap/prediction.json")
    assert len(cheap["rows"]) == 39
    assert len(cheap["decisions"]) == 13
    assert prep.read(output / "cheap/resource_audit.json")["counts"]["candidate_pf_vector_actions"] == 39
    cheap_hash = prep.sha_file(output / "cheap/prediction.json")
    args.phase, args.cheap_commit = "m1", "synthetic_commit"
    runner.acquire(args, tmp_path, output, {}, PROTOCOL, PLAN, identities)
    assert prep.sha_file(output / "cheap/prediction.json") == cheap_hash
    m1 = prep.read(output / "m1/prediction.json")
    assert len(m1["rows"]) == 39
    counts = prep.read(output / "m1/resource_audit.json")["counts"]
    assert counts["M1_pf_vector_actions"] == counts["M1_h_matvecs"] <= 312
    assert all(counts[k] == 0 for k in p.FORBIDDEN)
    assert counts["candidate_pf_vector_actions"] == counts["candidate_h_exponential_actions"] == 0
    with pytest.raises(FileExistsError):
        runner.acquire(args, tmp_path, output, {}, PROTOCOL, PLAN, identities)


def test_failed_action_keeps_attempt_count_and_no_frozen_marker(tmp_path, monkeypatch):
    output = tmp_path / "new_output"
    frozen = tmp_path / p.PREP / "INPUT_FROZEN.json"
    frozen.parent.mkdir(parents=True)
    frozen.write_text("synthetic")
    runtime = frozen.parent / ".runtime"
    runtime.mkdir()
    identities = {"LiH_R1.80": {"PF_sequence_hex": [1..hex()]}}
    monkeypatch.setattr(runner, "allocation", lambda *_: ({"worker_rss_limit_bytes": 2**40, "worker_wall_seconds": 600}, lambda: None))
    monkeypatch.setattr(runner, "environment", lambda *_: {})
    monkeypatch.setattr(runner, "runtime_gate", lambda *_: [])
    monkeypatch.setattr(runner, "passed_tests", lambda *_: {})
    monkeypatch.setattr(prep, "remaining_worker_wall", lambda *_: 600.)
    h = csr_matrix(np.eye(2))
    monkeypatch.setattr(prep, "load_input", lambda *_: (h, np.ones(2)/np.sqrt(2), iter([h])))
    monkeypatch.setattr(runner.sys, "addaudithook", lambda *_: None)
    def fail_after_charge(adapter, state, t):
        adapter.ledger.charge("reference_pf_actions")
        raise prep.PreparationError("synthetic dispatch failed")
    monkeypatch.setattr(p.CandidateAdapter, "point", fail_after_charge)
    args = SimpleNamespace(phase="cheap", runtime_root=runtime, allocation=None, cheap_commit=None)
    with pytest.raises(prep.PreparationError, match="dispatch failed"):
        runner.acquire(args, tmp_path, output, {}, PROTOCOL, PLAN, identities)
    assert prep.read(output / "cheap/STOPPED.json")["resource"]["counts"]["candidate_pf_vector_actions"] == 1
    assert not (output / "cheap/CHEAP_FROZEN.json").exists()


@pytest.mark.parametrize("change", ("valid", "expired", "pool", "job_wall", "disk_roots", "disk_full"))
def test_actual_allocation_renewal_and_cumulative_disk(tmp_path, monkeypatch, change):
    runtime = tmp_path / "old" / p.PREP / ".runtime"
    runtime.mkdir(parents=True)
    output = tmp_path / "new" / p.OUTPUT
    private = output / ".private"
    private.mkdir(parents=True)
    (private / "approval.txt").write_text("synthetic allocation fixture; not a server renewal")
    now = datetime.now(timezone.utc)
    allocation = {
        "verified": True, "authority": "user_explicit_quota", "usable_cpu_quota": 16,
        "usable_ram_bytes": 128 * 2**30, "job_wall_seconds": 43200,
        "writable_disk_quota_bytes": 2 * 2**30, "approved_output_root": str(output),
        "workers": 1, "worker_rss_limit_bytes": 12 * 2**30, "worker_wall_seconds": 7200,
        "coordinator_reserved_ram_bytes": 32 * 2**30, "reserved_disk_bytes": 128 * 2**20,
        "starts_UTC": (now - timedelta(seconds=5)).isoformat(),
        "expires_UTC": (now + timedelta(seconds=300)).isoformat(),
        "evidence": [{"path": "approval.txt", "sha256": prep.sha_file(private / "approval.txt")}],
        "cumulative_disk_roots": [str(runtime.parent), str(output)]}
    if change == "expired":
        allocation["expires_UTC"] = (now - timedelta(seconds=1)).isoformat()
    elif change == "pool":
        allocation["workers"] = 2
    elif change == "job_wall":
        allocation["job_wall_seconds"] = 43201
    elif change == "disk_roots":
        allocation["cumulative_disk_roots"] = [str(output)]
    elif change == "disk_full":
        monkeypatch.setattr(runner, "disk_bytes", lambda *_: 2 * 2**30)
    path = private / "allocation.json"
    prep.write(path, allocation)
    if change != "valid":
        with pytest.raises(prep.PreparationError):
            runner.allocation(tmp_path, runtime, output, path)
    else:
        data, guard = runner.allocation(tmp_path, runtime, output, path)
        guard()
        assert data["workers"] == 1


def test_global_seal_with_synthetic_scalar_packages(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "git", lambda *_: b"synthetic_head")
    monkeypatch.setattr(p, "verify_blob", lambda *_: None)
    output = tmp_path / p.OUTPUT
    prep_dir = tmp_path / p.PREP
    prep.write(prep_dir / "candidate_plan.json", PLAN)
    prep.write(prep_dir / "review_bundle_manifest.json", {"synthetic_only": True})
    identities = {}
    for spec in SPECS:
        cid = spec["condition_id"]
        original = ROOT / p.PREP / "conditions" / cid
        identities[cid] = prep.read(original / "input_identity.json")
        for name in ("reference_result.json", "input_identity.json"):
            prep.write(prep_dir / "conditions" / cid / name, prep.read(original / name))
    rows = [{**r, "delta_C_hartree": 1e-6} for r in p.coordinate_rows(PLAN)]
    cheap = {"rows": rows, "decisions": {cid: p.cheap_decisions([r for r in rows if r["condition_id"] == cid], PROTOCOL) for cid in identities if cid not in p.TERMINAL}}
    m1 = {"rows": [{**r, "actual_M1_rank": 8, "eligible": False, "budget": None} for r in p.coordinate_rows(PLAN)], "cheap_commit": "synthetic_head"}
    for phase, payload, names, marker_name in (("cheap", cheap, runner.CHEAP_FILES, "CHEAP_FROZEN.json"), ("m1", m1, runner.M1_FILES, "M1_FROZEN.json")):
        if phase == "m1":
            payload["cheap_manifest_sha256"] = prep.sha_file(output / "cheap/manifest.json")
        directory = output / phase
        prep.write(directory / "prediction.json", payload)
        prep.write(directory / marker_name, {"prediction_sha256": prep.sha_file(directory / "prediction.json"), "coordinate_count": 39, "truth_opened": False})
        counts = {k: 0 for k in (*p.LIMITS, *p.FORBIDDEN)}
        for key in p.LIMITS:
            if (phase == "cheap" and key.startswith("candidate")) or (phase == "m1" and key.startswith("M1")):
                counts[key] = p.LIMITS[key]
        prep.write(directory / "resource_audit.json", {"counts": counts, "synthetic_only": True})
        prep.write(directory / "access_audit.json", {"denied_accesses": [], "synthetic_only": True})
        prep.write(directory / "source_audit.json", {"synthetic_only": True})
        p.make_manifest(directory, names)
    for label in ("pre", "mid", "post"):
        (output / f"{label}_tests.log").write_text("1 passed\n")
        prep.write(output / f"{label}_tests.json", {"label": label, "HEAD": "synthetic_head", "returncode": 0,
            "failures_or_skips": False, "passed": 1, "test_sources": [], "log": f"{label}_tests.log",
            "log_sha256": prep.sha_file(output / f"{label}_tests.log")})
    args = SimpleNamespace(cheap_commit="synthetic_head")
    runner.seal(args, tmp_path, output, {"synthetic_only": True}, PROTOCOL, SPECS, PLAN, identities)
    p.require_members(p.verify_package(tmp_path, output / "global"), runner.FINAL_FILES)
    assert (output / "global/candidate_plan.json").read_bytes() == (prep_dir / "candidate_plan.json").read_bytes()
    result = prep.read(output / "global/prediction.json")
    assert result["attempted_conditions"] == 16 and result["terminal_conditions"] == p.TERMINAL
    assert result["M1_condition_abstentions"] == 13
    assert prep.read(output / "global/COMPLETE.json")["status"] == p.SUCCESS
