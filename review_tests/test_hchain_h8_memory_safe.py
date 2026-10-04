"""Synthetic/source/access checks; no molecular truth or candidate acquisition."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from review_response.hchain_h8_memory_safe import (
    BASE, DOC, H8Ledger, StreamingVectorAdapter, array_digest_stream,
    dense_digest_stream, plan_rows, read, runtime_gate, truth_feasibility, validate_plan,
)
from review_response.hchain_input_reference_preparation import PreparationError, VectorAdapter, sha_array, sha_file
from review_response.hchain_prediction_phase import ReadBoundary
from review_response.hchain_selective_calibration_schedule import run_shared_schedule

ROOT=Path(__file__).resolve().parents[1]


def test_vector_methods_are_identical_bodies():
    for name in ("pf","h_exp","h_matvec","cheap","_vector"):
        assert getattr(StreamingVectorAdapter,name) is getattr(VectorAdapter,name)


def test_streamed_pf_and_cheap_equivalence_synthetic():
    x=np.array([[0,1],[1,0]],complex)
    z=np.diag([1.,-1.]).astype(complex)
    sequence=(.2,.3,.5)
    state=np.array([1.,0.],complex)
    old=VectorAdapter(x+z,[x,z],sequence,H8Ledger(),allowed_kinds=("candidate",))
    new=StreamingVectorAdapter(csr_matrix(x+z),(csr_matrix(g) for g in (x,z)),2,sequence,H8Ledger(),allowed_kinds=("candidate",))
    assert np.array_equal(old.pf(state,.3,kind="candidate"),new.pf(state,.3,kind="candidate"))
    assert old.cheap(state,.3,kind="candidate")==new.cheap(state,.3,kind="candidate")
    assert new.storage_profile()["simultaneous_full_sector_dense_group_matrices"]==0


def test_group_stream_rejects_count_mismatch():
    with pytest.raises(PreparationError):
        StreamingVectorAdapter(csr_matrix(np.eye(2)),iter([csr_matrix(np.eye(2))]),2,[1.],H8Ledger())


def test_numpy_v1_hash_has_no_full_copy_and_matches_dense():
    value=np.array([[1.+2j,0.],[0.,-3.]],complex)
    assert array_digest_stream(value)==sha_array(value)
    assert dense_digest_stream(csr_matrix(value))==sha_array(value)
    with pytest.raises(PreparationError): array_digest_stream(value.T)


def test_no_group_ensemble_or_dense_group_creation_in_h8_source():
    source=(ROOT/"review_response/run_hchain_h8_memory_safe.py").read_text()
    assert "groups = [qubit_operator_sector_matrix" not in source
    assert "group.toarray()" not in source
    assert "dense_h = h.toarray()" in source
    assert "del dense_h" in source
    assert "previous=view.copy()" in source and "del view,u" in source


def test_protocol_and_inherited_source_identities():
    auth=read(ROOT/DOC/"protocol.json")
    old=read(ROOT/"docs/second_study_v2/hchain_odd_extension_20261004/protocol.json")
    for key in ("PF","reference_grid","epsilon_E","beta","eta","gamma_frontier","rank_core_rules","reference_fit_rules"):
        assert auth[key]==old[key]
    assert auth["base_commit"]==BASE and auth["permissions"]["push"] is False
    spec=auth["systems"][0]
    assert (spec["charge"],spec["multiplicity"],spec["sector_dimension"],spec["CISD_dimension"])==(0,1,4900,361)
    assert spec["primary_m"]==8
    for row in read(ROOT/DOC/"source_registry.json")["sources"]:
        assert sha_file(ROOT/row["path"])==row["sha256"]
        assert row["origin_result_commit"] and row["verified_snapshot_commit"]==BASE


def test_h8_candidate_plan_exact_hex_and_no_rescue():
    refs={"H8":{"qualified":True,"t_ref":1.23456789012345}}
    identity={"H8":{"sector_dimension":4900,"K":123}}
    rows=plan_rows(refs,identity)
    assert len(rows)==3 and [r["primary_m"] for r in rows]==[8,8,8]
    assert validate_plan(rows,refs,identity)==rows
    changed=deepcopy(rows);changed[0]["time"]=np.nextafter(changed[0]["time"],np.inf)
    with pytest.raises(PreparationError):validate_plan(changed,refs,identity)
    assert plan_rows({"H8":{"qualified":False,"t_ref":None}},identity)==[]


def test_resource_ceiling_before_extra_action():
    ledger=H8Ledger()
    for _ in range(3):ledger.charge("candidate_cheap_pf_actions",9)
    with pytest.raises(PreparationError):ledger.charge("candidate_cheap_pf_actions",9)
    assert ledger.payload()["native_workspace_allocation_count"]=="unknown_not_instrumented"


def test_truth_planning_gate_does_not_compute_truth():
    times={"truth_Schur_branch_gap":1.,"truth_full_PF_construction":1.,"H7_same_H_ground":1.}
    result=truth_feasibility(4900,2*1024**3,times,2)
    assert result["predicted_memory_bytes"]>4*1024**3 and not result["feasible"]
    assert result["budgeted_simultaneous_dense_objects"]==9
    assert result["native_workspace_requirement_certified"] is False


def test_truth_and_source_access_boundary(tmp_path):
    output=tmp_path/"artifacts/new"
    source=tmp_path/"source.py"
    boundary=ReadBoundary(tmp_path,[source],output)
    boundary.hook("open",(str(source),"r",0))
    boundary.hook("open",(str(output/"new.npz"),"wb",0))
    for name in ("artifacts/old/direct.json","artifacts/old/ground.npz"):
        with pytest.raises(PreparationError):boundary.hook("open",(str(tmp_path/name),"r",0))


def test_freeze_order_and_h1_comparator_separation():
    events=[]
    def cheap(name):
        return [{"candidate_id":f"p{i}","time":t,"delta_C_hartree":1e-6}
                for i,t in enumerate((.5,.65,.8))],100
    def spectral(name):
        events.append("comparator")
        return [{"candidate_id":f"p{i}","time":t,"abstain":False,"e_use":1e-5}
                for i,t in enumerate((.5,.65,.8))]
    result=run_shared_schedule(["H8"],cheap,spectral,lambda name,payload,digest:events.append(name))
    assert events==["ACQUISITION_FROZEN","H1_FROZEN","comparator"]
    assert result["cheap"]["H8"]["q"]==0
    assert result["H1"]["H8"]["action"]==result["cheap"]["H8"]["B2"]


def test_runtime_extra_member_and_hash_rejected(tmp_path):
    private=tmp_path/".runtime";private.mkdir()
    path=private/"input.json";path.write_text("{}")
    inputs={"runtime_files":[{"path":path.name,"bytes":path.stat().st_size,"sha256":sha_file(path)}]}
    runtime_gate(tmp_path,inputs)
    (private/"extra.json").write_text("{}")
    with pytest.raises(PreparationError):runtime_gate(tmp_path,inputs)
