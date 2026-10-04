"""Technical-resume regression tests; synthetic arrays, no molecular truth acquisition."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest

from review_response.hchain_input_reference_preparation import Ledger, PreparationError, sha_array
from review_response.hchain_prediction_phase import NEW_SOURCES, ReadBoundary, preparation_gate
from review_response.hchain_truth_scoring import source_gate
from review_response.run_hchain_truth_scoring_resume import (
    DOC, OUT, allowed_reads, recover_ground, restore_ledger, stopped_gate,
)

ROOT = Path(__file__).resolve().parents[1]
METHOD = "docs/second_study_v2/hchain_input_reference_preparation_20261004/truth_scoring_method.json"


def test_allowlist_contains_all_frozen_prediction_sources():
    runtime = preparation_gate(ROOT)
    allowed = set(allowed_reads(ROOT,runtime))
    assert {ROOT/name for name in NEW_SOURCES} <= allowed


def test_actual_composed_source_and_runtime_gates_under_active_boundary():
    runtime = preparation_gate(ROOT)
    boundary = ReadBoundary(ROOT,allowed_reads(ROOT,runtime),ROOT/OUT)
    sys.addaudithook(boundary.hook)
    try:
        _, source = source_gate(ROOT)
        assert source["prediction_files_verified"] == 38
        assert preparation_gate(ROOT) == runtime
        failure, preservation = stopped_gate(ROOT)
        assert failure["resources"]["counts"]["full_H_ground_solves"] == 3
        assert preservation["file_count"] == 3
        assert not boundary.denials
    finally:
        boundary.enabled = False


def test_resume_still_denies_unlisted_repository_data():
    boundary = ReadBoundary(ROOT,[],ROOT/OUT)
    with pytest.raises(PreparationError,match="outside allowlist"):
        boundary.hook("open",(str(ROOT/"unlisted.json"),"r",0))


def test_restore_counters_not_reset_ground_work():
    failure = {"resources":{"counts":{"full_H_ground_solves":3,"group_component_eigh_batches":149},
        "timings_seconds":{"same_H_ground_acquisition":.03},"maximum_gate_cache_bytes":0,
        "maximum_pf_norm_residual":0.,"maximum_h_exp_norm_residual":0.}}
    ledger = restore_ledger(failure)
    assert ledger.counts["full_H_ground_solves"] == 3
    assert ledger.counts["group_component_eigh_batches"] == 149
    assert ledger.timings["same_H_ground_acquisition"] == .03


def synthetic_ground(tmp_path, vector=None):
    h = np.diag([-1.,1.]).astype(complex)
    path = tmp_path/"ground.npz"
    np.savez_compressed(path,ground_vector=np.asarray([1.,0.],dtype=complex) if vector is None else vector,energy=np.asarray(-1.))
    spec = {"sector_dimension":2,"H_sha256_numpy_v1":sha_array(h),"sector_indices_sha256_numpy_v1":"synthetic"}
    return path,h,spec,json.loads((ROOT/METHOD).read_text())


def test_saved_ground_revalidated_without_solver_or_invented_gap(tmp_path, monkeypatch):
    path,h,spec,method = synthetic_ground(tmp_path)
    import scipy.linalg
    def no_solver(*args,**kwargs):
        raise AssertionError("ground eigensolve must not repeat")
    monkeypatch.setattr(scipy.linalg,"eigh",no_solver)
    ledger = Ledger()
    record = recover_ground(path,h,spec,method,ledger)
    assert record["energy_hartree"] == -1.
    assert record["first_excitation_gap_hartree"] is None
    assert record["solver_seconds"] is None
    assert record["reused"] and not record["computed_on_resume"]
    assert ledger.counts["full_H_ground_solves"] == 0
    assert ledger.counts["ground_revalidation_H_matvecs"] == 1


def test_corrupt_ground_stops_without_repair(tmp_path):
    path,h,spec,method = synthetic_ground(tmp_path,np.asarray([0.,1.],dtype=complex))
    with pytest.raises(PreparationError,match="norm/residual"):
        recover_ground(path,h,spec,method,Ledger())


def test_ground_identity_mismatch_rejected(tmp_path):
    path,h,spec,method = synthetic_ground(tmp_path)
    spec["H_sha256_numpy_v1"] = "wrong"
    with pytest.raises(PreparationError,match="identity"):
        recover_ground(path,h,spec,method,Ledger())


def test_resume_authorization_no_new_ground_or_prediction_change():
    auth = json.loads((ROOT/DOC/"authorization.json").read_text())
    assert auth["same_output_root"] == OUT
    assert auth["limits"]["new_full_H_ground_solves"] == 0
    assert auth["limits"]["new_direct_truth_coordinates"] == 9
    for key in ("original_stop_overwrite","original_sources_or_prediction_change","ground_eigensolve_repeat",
                "budget_policy_width_threshold_change","GPU","push","next_stage"):
        assert auth["permissions"][key] is False


def test_resume_imports_unchanged_scoring_and_never_calls_ground_solver():
    text = (ROOT/"review_response/run_hchain_truth_scoring_resume.py").read_text()
    assert "score_all," in text
    assert "ground_point(" not in text and "eigh(" not in text
    assert text.index('stages["truth_commit"] = commit_stage') < text.index("scored = score_all(")
    assert text.index('stages["ground_commit"] = commit_stage') < text.index("unitary = full_unitary(")
