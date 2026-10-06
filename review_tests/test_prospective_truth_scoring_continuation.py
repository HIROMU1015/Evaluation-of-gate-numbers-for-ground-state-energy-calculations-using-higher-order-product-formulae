"""Scalar-only saved acquisition, real commit barrier, and immutable scorer tests."""
from copy import deepcopy
from pathlib import Path

import pytest

import continue_prospective_truth_scoring as c
import prospective_candidate_prediction as p
import prospective_input_reference as prep
import prospective_truth_scoring as s
from review_tests.test_prospective_truth_scoring import PROTOCOL, synthetic_study


@pytest.fixture
def saved(tmp_path):
    prediction, truth = synthetic_study()
    private = tmp_path/"private"
    specs = [r["condition"] for r in prediction["conditions"]]
    ready = []
    for row in truth["conditions"]:
        if not row["points"]:
            continue
        cid = row["condition_id"]
        ready.append(cid)
        directory = private/"workers"/cid
        directory.mkdir(parents=True)
        row["resource"].update({"BLAS_threads": 1, "peak_rss_bytes": 4096, "condition_wall_seconds": 10.})
        for point in row["points"]:
            point["coordinate_wall_seconds"] = 1.
        prep.write(directory/"result.json", row)
        prep.write(directory/"action_checkpoint.json", {"counts": row["resource"]["counts"]})
        prep.write(directory/"current_phase.json", {"stage": "condition_complete"})
    prep.write(private/"technical_retry_token.json", {"ready_conditions": ready})
    snapshot = {"acquisition_execution_commit": c.ACQUISITION_COMMIT,
                "scientific_acquisition_completed_conditions": 13, "completed_resolved_coordinates": 39,
                "prior_technical_acquisition_retries": 1,
                "files": [{"path": str(f.relative_to(private)), "sha256": prep.sha_file(f), "bytes": f.stat().st_size}
                          for f in sorted((private/"workers").glob("*/*.json"))]}
    data = {"worker_rss_limit_bytes": 12*2**30, "worker_wall_seconds": 7200, "direct_coordinate_wall_seconds": 1800}
    return tmp_path, private, prediction, specs, data, snapshot


def test_saved_complete_aggregation_keeps_bytes_and_16_13_39_4(saved):
    root, private, prediction, specs, data, snapshot = saved
    before = deepcopy(prediction)
    with c.scalar_only():
        c.verify_saved(private, snapshot)
        records, counts = c.aggregate_saved(root, private, prediction, PROTOCOL, specs, data)
        c.verify_saved(private, snapshot)
    assert counts["exact_ground_solves"] == 13
    assert counts["full_PF_materializations"] == counts["direct_Schur_solves"] == 39
    assert all(counts[key] == 0 for key in s.ZERO)
    assert len(records) == 16 and sum(len(r["points"]) for r in records) == 39
    assert prediction == before
    assert {r["condition_id"] for r in records if r["ground"] is None} == set(p.TERMINAL)


@pytest.mark.parametrize("modification", ["missing_result", "unfinished", "terminal_worker", "wrong_condition",
    "extra_ground", "checkpoint_mismatch", "forbidden_M1", "RSS_cap", "coordinate_cap", "condition_cap",
    "BLAS_threads", "wrong_H", "changed_time", "negative_count"])
def test_partial_or_changed_acquisition_never_restarts(saved, modification):
    root, private, prediction, specs, data, _ = saved
    directory = next((private/"workers").iterdir())
    row = prep.read(directory/"result.json")
    if modification == "missing_result":
        (directory/"result.json").unlink()
    elif modification == "unfinished":
        prep.write(directory/"current_phase.json", {"stage": "complex_Schur"})
    elif modification == "terminal_worker":
        (private/"workers"/next(iter(p.TERMINAL))).mkdir()
    elif modification == "checkpoint_mismatch":
        prep.write(directory/"action_checkpoint.json", {"counts": {"exact_ground_solves": 1}})
    else:
        if modification == "wrong_condition": row["condition_id"] = "wrong"
        if modification == "extra_ground": row["resource"]["counts"]["exact_ground_solves"] = 2
        if modification == "forbidden_M1": row["resource"]["counts"]["new_M1_actions"] = 1
        if modification == "RSS_cap": row["resource"]["peak_rss_bytes"] = 13*2**30
        if modification == "coordinate_cap": row["points"][0]["coordinate_wall_seconds"] = 1801.
        if modification == "condition_cap": row["resource"]["condition_wall_seconds"] = 7201.
        if modification == "BLAS_threads": row["resource"]["BLAS_threads"] = 2
        if modification == "wrong_H": row["ground"]["H_dense_numpy_v1"] = "changed"
        if modification == "changed_time": row["points"][0]["time"] += .001
        if modification == "negative_count": row["resource"]["counts"]["other"] = -1
        prep.write(directory/"result.json", row)
    with c.scalar_only(), pytest.raises((prep.PreparationError, FileNotFoundError)):
        c.aggregate_saved(root, private, prediction, PROTOCOL, specs, data)


def test_saved_snapshot_rejects_one_byte_change(saved):
    _, private, _, _, _, snapshot = saved
    path = private/snapshot["files"][0]["path"]
    path.write_bytes(path.read_bytes()+b" ")
    with pytest.raises(prep.PreparationError, match="evidence changed"):
        c.verify_saved(private, snapshot)


@pytest.mark.parametrize("name", ["ground_point", "full_unitary", "direct_helper", "eigh", "schur"])
def test_scalar_guard_blocks_scientific_calls_and_restores(name):
    original = getattr(s, name)
    with c.scalar_only(), pytest.raises(prep.PreparationError, match="forbids scientific"):
        getattr(s, name)()
    assert getattr(s, name) is original


@pytest.mark.parametrize("relative", [".runtime/value.json", "state.npz", "unitary.npy", "cache.pickle"])
def test_scalar_guard_blocks_arrays_and_runtime_opens(tmp_path, relative):
    path = tmp_path/relative
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"synthetic")
    with c.scalar_only(), pytest.raises(prep.PreparationError, match="forbids array/runtime"):
        path.read_bytes()
    assert path.read_bytes() == b"synthetic"


def test_invalid_truth_commit_blocks_scorer_before_call(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(s, "score_all", lambda *a: called.append(True))
    with pytest.raises((FileNotFoundError, prep.PreparationError)):
        c.frozen_score(tmp_path, tmp_path/"truth", "invalid", {}, {})
    assert called == []


def test_saved_aggregate_real_git_freeze_and_unchanged_scoring(saved):
    root, private, prediction, specs, data, snapshot = saved
    p.git(root, "init", "-q", "-b", "synthetic-continuation")
    p.git(root, "config", "user.name", "Synthetic Test")
    p.git(root, "config", "user.email", "synthetic@example.invalid")
    p.git(root, "remote", "add", "origin", "https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae.git")
    (root/"synthetic-source").write_text("synthetic\n")
    p.git(root, "add", "--", "synthetic-source")
    p.git(root, "commit", "-qm", "synthetic source")
    with c.scalar_only():
        records, counts = c.aggregate_saved(root, private, prediction, PROTOCOL, specs, data)
        truth = {"conditions": records}
        directory = root/"truth"
        names = s.write_bundle(directory, "truth.json", "TRUTH_FROZEN.json", truth, {}, {"new_actions": counts}, {},
                    {"pre_truth_gate.json": {"status": "PASS"}, "pre_tests.json": {}, "pre_tests.log": "synthetic\n"})
        commit = s.commit_bundle(root, directory, names, "synthetic saved truth freeze")
        original = deepcopy(prediction), prep.sha_file(directory/"truth.json")
        result = c.frozen_score(root, directory, commit, prediction, PROTOCOL)
        assert result == s.score_all(prediction, truth, PROTOCOL)
        assert result["denominators"]["scored_coordinates"] == 39
        assert result["M1_candidate_abstentions_preserved"] == 39
        assert result["M1_accepted_performance_count"] == 0
        assert (prediction, prep.sha_file(directory/"truth.json")) == original
        c.verify_saved(private, snapshot)
        (directory/"truth.json").write_text("{}\n")
        with pytest.raises(prep.PreparationError):
            c.frozen_score(root, directory, commit, prediction, PROTOCOL)
