"""Real source import under the repository guard; only synthetic truth fixtures."""
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import hchain_supplement_execution as core
import hchain_truth_continuation as continuation

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module_name", ["hchain_truth_scoring", "review_response.hchain_truth_scoring"])
def test_real_sealed_truth_import_under_access_guard(tmp_path, monkeypatch, module_name):
    entries = continuation.import_entries(ROOT)
    allowed = [ROOT / row["path"] for row in entries]
    guard = core.AccessGuard(ROOT.parents[1], tmp_path, allowed)
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    sys.addaudithook(guard.hook)
    try:
        with continuation.source_only_imports(ROOT, entries) as finder:
            module = importlib.import_module(module_name)
            assert callable(module.truth_quality)
        assert finder.events
        event = next(e for e in finder.events if e["module"] == module_name)
        assert event["path"] == str(ROOT / "review_response/hchain_truth_scoring.py")
        assert event["source_only"] and event["pyc_reads"] == event["pyc_writes"] == 0
        assert not guard.denials
        assert all("__pycache__" not in p and not p.endswith(".pyc") for p in guard.reads)
    finally:
        guard.enabled = False


def test_source_loader_ignores_existing_poisoned_pyc(tmp_path):
    source = tmp_path / "toy.py"
    source.write_text("value = 73\n")
    cached = Path(importlib.util.cache_from_source(str(source)))
    cached.parent.mkdir()
    cached.write_bytes(b"poisoned bytecode never opened")
    events = []
    guard = core.AccessGuard(tmp_path, tmp_path / "output", [source])
    sys.addaudithook(guard.hook)
    try:
        loader = continuation.SealedSourceLoader("toy", source, core.sha_file(source), events)
        scope = {}
        exec(loader.get_code("toy"), scope)
        assert scope["value"] == 73 and not guard.denials
        assert str(cached) not in guard.reads
    finally:
        guard.enabled = False


def test_source_hash_mismatch_stops_before_execution(tmp_path):
    source = tmp_path / "toy.py"
    source.write_text("raise AssertionError('must not execute')\n")
    loader = continuation.SealedSourceLoader("toy", source, "0" * 64, [])
    with pytest.raises(core.PreparationError, match="hash changed"):
        loader.get_code("toy")


@pytest.mark.parametrize("name", continuation.FORBIDDEN)
def test_all_front_end_actions_disabled(name):
    ledger = continuation.TruthOnlyLedger()
    with pytest.raises(core.PreparationError, match="action cap"):
        ledger.charge(name, 999)
    assert ledger.counts[name] == 0


def test_truth_coordinate_cap_three_per_geometry():
    ledger = continuation.TruthOnlyLedger()
    for _ in range(3):
        ledger.charge("direct_truth_coordinates", 999)
    with pytest.raises(core.PreparationError):
        ledger.charge("direct_truth_coordinates", 999)


def test_unchanged_full_PF_Schur_and_quality_on_two_state_fixture():
    from trotterlib.component_sector_pf import component_exponential
    h = np.diag([0., .7]).astype(complex)
    ledger = continuation.TruthOnlyLedger()
    adapter = core.VectorAdapter(h, [h], [1.], ledger, allowed_kinds=())
    full = core.checked_functions(ROOT / "review_response/run_hchain_truth_scoring.py", core.GROUND_SHA,
        ("full_unitary",), {"component_exponential": component_exponential, "PreparationError": core.PreparationError})["full_unitary"]
    direct = core.checked_functions(ROOT / "review_response/_pf_first_study_s0_exact_time_scoring_base.py", core.DIRECT_SHA,
        ("_phase_distance", "direct_branch_point"),
        {"schur": core.schur, "practical": SimpleNamespace(_cost=lambda t,e,k,eps: core.budget(t,e,k))})["direct_branch_point"]
    entries = continuation.import_entries(ROOT)
    with continuation.source_only_imports(ROOT, entries):
        quality = importlib.import_module("hchain_truth_scoring").truth_quality
    previous = None
    for t in (.5,.65,.8):
        unitary = full(adapter, t, ledger)
        point, previous = direct(unitary, np.array([1.,0.]), 0., t, 1, core.EPS, previous, 1e-8)
        assert abs(point["signed_direct_shift_hartree"]) < 1e-14
        assert quality(point, core.read(ROOT / core.METHOD))["physical_branch_valid"]
    assert ledger.counts["full_pf_unitary_builds"] == 3
    assert all(ledger.counts[k] == 0 for k in continuation.FORBIDDEN)


@pytest.mark.parametrize("stage", ["G_inputs", "G_reference", "G_prediction", "G_ground", "R_prediction"])
def test_wrapper_rejects_other_stages(stage):
    with pytest.raises(core.PreparationError, match="truth-only"):
        continuation.truth_worker({"stage": stage, "unit": "H6_R0.80"})


def test_real_truth_worker_import_and_serialization_with_synthetic_solver(tmp_path, monkeypatch):
    entries = continuation.import_entries(ROOT)
    input_path, ground_path = tmp_path / "groups.npz", tmp_path / "ground.npz"
    np.savez_compressed(input_path, **{f"group_{i:03d}": np.diag([0., .01]) for i in range(57)})
    np.savez_compressed(ground_path, vector=np.array([1., 0.], dtype=complex))
    original_read = core.read
    monkeypatch.setattr(core, "read", lambda p: {"files": entries} if str(p).endswith(continuation.DOC + "/source_freeze.json") else original_read(p))
    def guard_factory(root, out, *, extra=()):
        guard = core.AccessGuard(ROOT.parents[1], out, [ROOT / e["path"] for e in entries] + list(extra))
        sys.addaudithook(guard.hook)
        return guard
    monkeypatch.setattr(core, "make_guard", guard_factory)
    monkeypatch.setattr(core, "load_new_input", lambda *a: (np.diag([0., .57]), np.array([1., 0.]), np.arange(2), None))
    monkeypatch.setattr(core, "VectorAdapter", lambda h, *a, **kw: SimpleNamespace(h=h))
    history = []
    original_functions = core.checked_functions
    def checked(path, digest, names, namespace=None):
        if names == ("full_unitary",):
            def full(adapter, t, ledger):
                ledger.charge("full_pf_unitary_builds", 3)
                return np.eye(2, dtype=complex)
            return {"full_unitary": full}
        if names == ("_phase_distance", "direct_branch_point"):
            def direct(u, vector, energy, t, k, eps, previous, tolerance):
                history.append((t, previous))
                return {"signed_direct_shift_hartree": 0., "minimum_selected_phase_gap_radians": .2,
                    "ground_state_overlap_probability": 1., "previous_branch_overlap_probability": 1.,
                    "unitarity_residual_frobenius": 0., "eigenpair_residual_2_norm": 0.,
                    "selected_eigenvalue": 1+0j}, vector
            return {"direct_branch_point": direct, "_phase_distance": lambda a,b: 0.}
        return original_functions(path, digest, names, namespace)
    monkeypatch.setattr(core, "checked_functions", checked)
    monkeypatch.delitem(sys.modules, "hchain_truth_scoring", raising=False)
    plans = [{"time": t, "time_hex": t.hex(), "candidate_id": f"mock_{i}"} for i,t in enumerate((.5,.65,.8))]
    result = continuation.truth_worker({"root": str(ROOT), "output": str(tmp_path / "output"), "stage": "G_truth",
        "unit": "H6_R0.80", "input": {"runtime_file": str(input_path)}, "plan": plans,
        "ground": {"ground_runtime": str(ground_path), "ground_runtime_sha256": core.sha_file(ground_path), "ground": {"energy_hartree": 0.}}})
    assert result["status"] == "complete", result
    assert not result["access"]["denials"] and result["sealed_source_imports"]
    assert len(result["points"]) == 3 and result["new_front_end_actions"] == 0
    assert result["resource"]["counts"]["full_pf_unitary_builds"] == 3
    assert history[0][1] is None and all(v is not None for t,v in history[1:])
    assert [t for t,v in history] == [.5,.65,.8]
    saved = tmp_path / "output/.runtime/G_truth/H6_R0.80/worker_result.json"
    assert json.loads(saved.read_text())["status"] == "complete"
