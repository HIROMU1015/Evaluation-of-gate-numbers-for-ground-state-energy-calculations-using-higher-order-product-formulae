"""Synthetic/source/access tests only. Never read saved molecular truth."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from review_response.hchain_input_reference_preparation import PreparationError, canonical_hash, sha_file
from review_response.hchain_prediction_phase import (
    BUNDLE_FILES, DOC, CoordinateActions, ReadBoundary, commit_bundle, finite_json,
    git, load_plan, make_bundle, verify_bundle, verify_entries,
)
from review_response.hchain_selective_calibration_schedule import cheap_policy, run_shared_schedule


ROOT = Path(__file__).resolve().parents[1]


def test_permission_is_prediction_only():
    contract = json.loads((ROOT / DOC / "authorization.json").read_text())
    assert contract["permissions"]["candidate_M1"]
    for key in ("exact_ground", "direct_truth", "target_phase_gap", "performance_scoring",
                "push", "full_legacy_tests", "runtime_transfer_or_regeneration"):
        assert contract["permissions"][key] is False
    assert contract["limits"]["M1_PF_actions"] == 60
    assert contract["limits"]["candidate_coordinates"] == 9


@pytest.mark.parametrize("maximum", [4, 8])
def test_coordinate_ceiling_before_action(maximum):
    counts = {"u": 0, "h": 0}
    def u(vector, time, **kwargs):
        counts["u"] += 1
        return vector
    def h(vector):
        counts["h"] += 1
        return vector
    actions = CoordinateActions(SimpleNamespace(pf=u, h_matvec=h), .5, maximum)
    for _ in range(maximum):
        actions.pf(np.ones(2))
        actions.h(np.ones(2))
    with pytest.raises(PreparationError, match="coordinate PF"):
        actions.pf(np.ones(2))
    with pytest.raises(PreparationError, match="coordinate H"):
        actions.h(np.ones(2))
    assert counts == {"u": maximum, "h": maximum}


def test_nonfinite_is_not_accepted_narrow_width():
    missing = []
    payload = finite_json({"width": float("inf"), "abstain": True, "prefix": [float("nan"), 1.]}, missing=missing)
    assert payload == {"width": None, "abstain": True, "prefix": [None, 1.]}
    assert len(missing) == 2
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize("target", ["artifacts/truth.json", "docs/unlisted.json", "runtime/exact.npz"])
def test_unallowlisted_repository_data_blocked(tmp_path, target):
    allowed = tmp_path / "input.npz"
    boundary = ReadBoundary(tmp_path, [allowed], tmp_path / "output")
    boundary.hook("open", (str(allowed), "rb", 0))
    with pytest.raises(PreparationError, match="outside allowlist"):
        boundary.hook("open", (str(tmp_path / target), "r", 0))
    assert boundary.payload([])["truth_array_reads"] == 0
    assert len(boundary.denials) == 1


def test_runtime_write_denied_output_write_allowed(tmp_path):
    boundary = ReadBoundary(tmp_path, [tmp_path / "input.npz"], tmp_path / "out")
    boundary.hook("open", (str(tmp_path / "out" / "new.json"), "w", os.O_WRONLY | os.O_CREAT))
    with pytest.raises(PreparationError):
        boundary.hook("open", (str(tmp_path / "input.npz"), "wb", os.O_WRONLY))


def test_manifest_mismatch_before_deserialization(tmp_path):
    path = tmp_path / "data"
    path.write_bytes(b"before")
    entries = [{"path": "data", "bytes": 6, "sha256": sha_file(path)}]
    verify_entries(tmp_path, entries)
    path.write_bytes(b"after!")
    with pytest.raises(PreparationError, match="byte/hash"):
        verify_entries(tmp_path, entries)
    with pytest.raises(PreparationError, match="unsafe"):
        verify_entries(tmp_path, [{"path": "../escape", "bytes": 0, "sha256": "0" * 64}])


def synthetic_repository(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Synthetic Test")
    git(tmp_path, "config", "user.email", "synthetic@example.invalid")
    git(tmp_path, "remote", "add", "origin", "https://github.com/HIROMU1015/synthetic-test.git")
    (tmp_path / "source").write_text("synthetic\n")
    git(tmp_path, "add", "source")
    git(tmp_path, "commit", "-qm", "synthetic source")
    return tmp_path


def test_real_git_barrier_and_no_m1_lookahead(tmp_path):
    root = synthetic_repository(tmp_path)
    commits, events = {}, []
    points = {name: [{"candidate_id": f"{name}_{i}", "time": time, "delta_C_hartree": delta}
                    for i, time, delta in zip(range(3), (.5, .65, .8),
                        (1e-6, 2e-6, -3e-6 if name == "unstable" else 3e-6), strict=True)]
              for name in ("stable", "unstable")}
    def cheap(name):
        return points[name], 108
    def freeze(name, payload, digest):
        directory = root / name
        make_bundle(directory, payload, {"kind": name, "payload_canonical_sha256": digest}, {}, {}, {})
        commits[name] = commit_bundle(root, directory, f"synthetic {name}")
        events.append(name)
    def spectral(name):
        verify_bundle(root, root / "ACQUISITION_FROZEN", commits["ACQUISITION_FROZEN"])
        if name == "stable":
            verify_bundle(root, root / "H1_FROZEN", commits["H1_FROZEN"])
        events.append(name)
        return [{"candidate_id": row["candidate_id"], "time": row["time"], "e_use": 1e-6,
                 "abstain": False} for row in points[name]]
    result = run_shared_schedule(("stable", "unstable"), cheap, spectral, freeze)
    assert events == ["ACQUISITION_FROZEN", "unstable", "H1_FROZEN", "stable"]
    assert result["H1"]["stable"]["source"] == "B2_q_zero"
    assert set(git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commits["ACQUISITION_FROZEN"]).decode().splitlines()) == {
        f"ACQUISITION_FROZEN/{name}" for name in BUNDLE_FILES}
    (root / "ACQUISITION_FROZEN" / "prediction.json").write_text("{}")
    with pytest.raises(PreparationError):
        verify_bundle(root, root / "ACQUISITION_FROZEN", commits["ACQUISITION_FROZEN"])


def test_non_hiromu_commit_rejected(tmp_path):
    root = synthetic_repository(tmp_path)
    git(root, "remote", "set-url", "origin", "https://github.com/quration/forbidden.git")
    directory = root / "freeze"
    make_bundle(directory, {}, {"kind": "test"}, {}, {}, {})
    previous = git(root, "rev-parse", "HEAD")
    with pytest.raises(PreparationError, match="HIROMU1015"):
        commit_bundle(root, directory, "must not commit")
    assert git(root, "rev-parse", "HEAD") == previous
    assert not git(root, "diff", "--cached", "--name-only").strip()


def test_extra_file_not_staged(tmp_path):
    root = synthetic_repository(tmp_path)
    directory = root / "freeze"
    make_bundle(directory, {}, {"kind": "test"}, {}, {}, {})
    (directory / "vector.npy").write_bytes(b"excluded")
    with pytest.raises(PreparationError, match="exactly seven"):
        commit_bundle(root, directory, "must not commit vector")
    assert not git(root, "diff", "--cached", "--name-only").strip()


def test_prior_staged_work_blocks_freeze(tmp_path):
    root = synthetic_repository(tmp_path)
    (root / "source").write_text("user modification")
    git(root, "add", "source")
    directory = root / "freeze"
    make_bundle(directory, {}, {"kind": "test"}, {}, {}, {})
    with pytest.raises(PreparationError, match="tracked/staged"):
        commit_bundle(root, directory, "must preserve user stage")
    assert git(root, "diff", "--cached", "--name-only").decode().strip() == "source"


def test_freeze_payload_immutable():
    points = [{"candidate_id": str(i), "time": t, "delta_C_hartree": 1e-6}
              for i, t in enumerate((.5, .65, .8))]
    def mutating(name, payload, digest):
        payload.clear()
    with pytest.raises(PreparationError, match="mutated"):
        run_shared_schedule(("H2",), lambda s: (points, 108), lambda s: [], mutating)


def test_binary64_plan_uses_hex(tmp_path):
    # No saved prediction/truth is read; purely synthetic reference scales.
    import csv
    path = tmp_path / "plan.csv"
    rows = []
    for system, tref, k, m in (("H2", 1.8, 108, 4), ("H4", 1.2, 2556, 8), ("H6", 1.1, 14344, 8)):
        for ratio in (.5, .65, .8):
            time = ratio * tref
            rows.append({"system": system, "candidate_id": f"{system}_{ratio}", "ratio": ratio,
                "ratio_hex": ratio.hex(), "time": time, "time_hex": time.hex(),
                "t_ref": tref, "t_ref_hex": tref.hex(), "K": k, "primary_m": m})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert [row["time_hex"] for row in load_plan(path)] == [row["time_hex"] for row in rows]
    rows[0]["time_hex"] = (.91).hex()
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(PreparationError, match="binary64"):
        load_plan(path)


def test_runner_no_truth_solver_or_unfreeze_path():
    text = (ROOT / "review_response/run_hchain_prediction_phase.py").read_text()
    for forbidden in ("direct_branch_point(", "scipy.linalg.eigh(", "np.linalg.eigh(",
                      "np.linalg.eig(", "nvidia-smi", "import cupy"):
        assert forbidden not in text
    assert "run_shared_schedule(" in text
    assert "runtime_after != runtime_identity" in text
