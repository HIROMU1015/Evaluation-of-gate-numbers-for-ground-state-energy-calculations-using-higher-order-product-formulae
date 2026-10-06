"""Synthetic same-H, numerical-boundary, immutable-score and freeze tests."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

import prospective_truth_scoring as s
import prospective_input_reference as prep
import prospective_candidate_prediction as p
import run_prospective_truth_scoring as runner

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = prep.read(ROOT/prep.DOC/"protocol.json")
RULE = PROTOCOL["truth_future"]


def coordinate(cid="synthetic", ratio=1.):
    t=float(.5*ratio)
    return {"condition_id":cid,"coordinate_id":cid+"_r"+str(ratio),"ratio":ratio,"ratio_hex":float(ratio).hex(),
            "time":t,"time_hex":t.hex(),"t_ref":.5,"t_ref_hex":(.5).hex(),"K":108}


def point(cid="synthetic",ratio=1.,direct=1e-6,valid=True):
    return {**coordinate(cid,ratio),"attempted":True,"signed_direct_shift_hartree":direct,
            "minimum_selected_phase_gap_radians":.2,"ground_state_overlap_probability":1.,
            "previous_branch_overlap_probability":1.,"unitarity_residual_frobenius":1e-14,
            "eigenpair_residual_2_norm":1e-14,"phase_cluster_size":1,
            "quality":{"physical_branch_valid":valid,"status":"resolved" if valid else "indeterminate"}}


def m1(cid="synthetic",ratio=1.,delta=1e-6,width=1e-7):
    return {**coordinate(cid,ratio),"delta_M_hartree":delta,"width_M_hartree":width,"eligible":False,
            "nonfinite_fields":[],"failure_reasons":["h_ritz_residual"] if coordinate(cid,ratio)["coordinate_id"] in s.EXCLUDED_M1 else ["no_positive_qpe_allowance"],
            "core_prediction":{"primary_dimension_used":8,"prefixes":[{"dimension":8,
                "h_reference_energy_hartree":-1.,"selected_unwrapped_energy_hartree":-1.+delta}]}}


def cheap(cid="synthetic",ratio=1.,delta=3e-6):
    return {**coordinate(cid,ratio),"delta_C_hartree":delta}


def ground_identity(h):
    return {"H_dense_numpy_v1":prep.array_hash(h),"sector_dimension":len(h),"sector_indices_numpy_v1":"synthetic",
            "condition":{"condition_id":"synthetic","populations":[1,1]},"removed_scalar_hartree":0.,"constant_policy":"scalar_removed"}


def test_ground_same_H_once_and_eigenpair_residual():
    h=np.asarray([[-1.,.1],[.1,1.]],dtype=np.complex128)
    ledger=s.TruthLedger()
    record,vector=s.ground_point(h,ground_identity(h),RULE,ledger)
    assert record["status"] == "same_H_ground_valid"
    assert np.linalg.norm(h@vector-record["energy_hartree"]*vector)<1e-12
    assert ledger.counts["exact_ground_solves"] == 1
    with pytest.raises(prep.PreparationError,match="cap"):
        s.ground_point(h,ground_identity(h),RULE,ledger)


@pytest.mark.parametrize("gap",[0.,1e-11,1e-10])
def test_ground_ambiguity_indeterminate_no_vector_rescue(gap):
    h=np.diag(np.asarray([0.,gap],dtype=np.complex128))
    record,vector=s.ground_point(h,ground_identity(h),RULE,s.TruthLedger())
    assert vector is None and "ground_ambiguity" in record["failure_reasons"]


def test_ground_hash_mismatch_before_scientific_action():
    h=np.diag(np.asarray([-1.,1.],dtype=np.complex128));identity=ground_identity(h)
    identity["H_dense_numpy_v1"]="wrong"
    ledger=s.TruthLedger()
    with pytest.raises(prep.PreparationError,match="identity"):
        s.ground_point(h,identity,RULE,ledger)
    assert ledger.counts["exact_ground_solves"] == 0


def test_full_PF_uses_left_applied_frozen_component_order():
    a=csr_matrix(np.array([[.1,.2],[.2,-.1]],dtype=complex))
    b=csr_matrix(np.diag([.3,-.2]).astype(complex))
    ledger=s.TruthLedger()
    adapter=prep.ReferenceAdapter(a+b,[a,b],[1.],ledger)
    actual=s.full_unitary(adapter,.4,ledger)
    expected=np.eye(2,dtype=complex)
    for index,weight in adapter.steps:
        expected=prep.component_exponential(adapter.spectra[index],.4*weight)@expected
    assert np.allclose(actual,expected,atol=1e-14)
    assert np.linalg.norm(actual.conj().T@actual-np.eye(2))<1e-12
    assert ledger.counts["full_PF_materializations"] == 1
    assert all(ledger.counts[k] == 0 for k in s.ZERO)


def test_direct_ground_initial_and_previous_continuation_no_substitution():
    direct=s.direct_helper(ROOT)
    unitary=np.diag(np.exp(1j*np.array([-.2,.4])))
    exact=np.array([1.,0.])
    first,_=direct(unitary,exact,-.2,1.,108,1e-4,None,1e-8)
    later,_=direct(unitary,exact,-.2,1.,108,1e-4,np.array([0.,1.]),1e-8)
    assert abs(first["signed_direct_shift_hartree"])<1e-14
    assert later["branch_selection_disagrees_with_comparator"]
    assert not s.truth_quality(later,RULE)["physical_branch_valid"]
    assert first["direct_cost"] is None  # scoring is deferred until truth commit


@pytest.mark.parametrize("field,value",[("unitarity_residual_frobenius",1e-9),
    ("eigenpair_residual_2_norm",1e-9),("minimum_selected_phase_gap_radians",1e-8),
    ("ground_state_overlap_probability",.899999),("previous_branch_overlap_probability",.899999),("phase_cluster_size",2)])
def test_truth_boundary_indeterminate_without_rescue(field,value):
    row=point();row[field]=value
    quality=s.truth_quality(row,RULE)
    assert quality["status"] == "truth_branch_indeterminate" and not quality["physical_branch_valid"]


@pytest.mark.parametrize("field",["signed_direct_shift_hartree","minimum_selected_phase_gap_radians",
    "unitarity_residual_frobenius","eigenpair_residual_2_norm"])
@pytest.mark.parametrize("bad",[None,math.inf,math.nan])
def test_nonfinite_truth_never_valid(field,bad):
    row=point();row[field]=bad
    assert not s.truth_quality(row,RULE)["physical_branch_valid"]


def test_numerical_equal_residual_and_overlap_thresholds_pass():
    row=point();row.update(unitarity_residual_frobenius=1e-10,eigenpair_residual_2_norm=1e-10,
                          ground_state_overlap_probability=.9,previous_branch_overlap_probability=.9)
    assert s.truth_quality(row,RULE)["physical_branch_valid"]


@pytest.mark.parametrize("name,limit",[("exact_ground_solves",1),("full_PF_materializations",3),("direct_Schur_solves",3)])
def test_attempted_actions_persist_before_next_dispatch(tmp_path,name,limit):
    path=tmp_path/"checkpoint.json";ledger=s.TruthLedger(checkpoint=path)
    for _ in range(limit): ledger.charge(name)
    assert prep.read(path)["counts"][name] == limit
    with pytest.raises(prep.PreparationError,match="cap"): ledger.charge(name)
    assert prep.read(path)["counts"][name] == limit


@pytest.mark.parametrize("name",s.ZERO)
def test_truth_ledger_forbids_candidate_reference_M1_gap_retry(name):
    with pytest.raises(prep.PreparationError): s.TruthLedger().charge(name)


def test_unavailable_continuation_has_explicit_missing_record():
    row=s.missing_point(coordinate(),"continuation_undefined")
    assert not row["attempted"] and row["signed_direct_shift_hartree"] is None
    assert not row["quality"]["physical_branch_valid"]


def test_abstained_M1_has_raw_diagnostics_and_no_accepted_performance():
    result=s.score_coordinate(cheap(),m1(),point(),{"status":"same_H_ground_valid","energy_hartree":-1.},PROTOCOL)
    assert result["M1_frozen_abstained"] and not result["M1_accepted_performance"]
    assert result["M1_point_error_hartree"] == 0.
    assert result["empirical_width_covers"] and result["branch_gap_compatibility_diagnostic"]
    assert result["PF_H_reference_decomposition"]["status"] == "indeterminate"
    assert not result["absolute_lift_is_confirmed_physical_branch"]


@pytest.mark.parametrize("cid,ratio",[("CH2_R1.40",1.2),("CH2_R1.70",1.)])
def test_pre_truth_h_ritz_failure_never_accepted(cid,ratio):
    result=s.score_coordinate(cheap(cid,ratio),m1(cid,ratio),point(cid,ratio),{"status":"same_H_ground_valid","energy_hartree":-1.},PROTOCOL)
    assert result["M1_pre_truth_h_ritz_failure"]
    assert "h_ritz_residual" in result["M1_failure_reasons_preserved"]
    assert result["M1_point_error_hartree"] == 0. and not result["M1_accepted_performance"]


def test_strict_branch_nonstrict_width_and_nonfinite_width_provenance():
    tr=point(direct=0.)
    result=s.score_coordinate(cheap(),m1(delta=.2,width=.2),tr,{},PROTOCOL)
    assert result["branch_gap_compatibility_diagnostic"] is False
    assert result["empirical_width_covers"] is True
    raw=m1();raw["width_M_hartree"]=None;raw["nonfinite_fields"]=[{"original":"inf"}]
    result=s.score_coordinate(cheap(),raw,tr,{},PROTOCOL)
    assert result["empirical_width_covers"] is None and result["width_nonfinite_provenance"]


def test_selected_budget_margin_slack_without_modification():
    rows=[cheap(ratio=r) for r in (.8,1.,1.2)]
    frozen={"cheap":rows,**p.cheap_decisions(rows,PROTOCOL)}
    action=frozen["B1"][0]["decision"]["selected"]
    original=deepcopy(action);tr=point(ratio=1.2,direct=2e-5)
    result=s.score_decision("synthetic","B1",action,1.01,frozen,tr,PROTOCOL)
    assert action == original
    assert result["frozen_budget"] == action["budget"]
    assert result["M_gamma_hartree"] == (1-1/1.01)*(PROTOCOL["resource"]["epsilon_E"]-3e-6)
    assert result["safety_slack_hartree"] == result["M_gamma_hartree"]-(2e-5-3e-6)
    assert result["unsafe"] is True and result["fallback"] is False


@pytest.mark.parametrize("budget",[0.,-1.,math.inf,None])
def test_invalid_frozen_budget_not_repaired(budget):
    frozen={"cheap":[cheap()],"B0":{"time":.4,"budget":1e6}}
    action={"time":.5,"time_hex":(.5).hex(),"budget":budget}
    with pytest.raises(prep.PreparationError,match="invalid frozen budget"):
        s.score_decision("synthetic","B0",action,1.1,frozen,point(),PROTOCOL)


def test_indeterminate_truth_no_safe_or_coverage_label():
    frozen={"cheap":[cheap()],"B0":{"time":.4,"budget":1e9}}
    action={"time":.5,"time_hex":(.5).hex(),"budget":1e9}
    result=s.score_decision("synthetic","B0",action,1.1,frozen,point(valid=False),PROTOCOL)
    assert result["safe"] is None
    coordinate_result=s.score_coordinate(cheap(),m1(),point(valid=False),{},PROTOCOL)
    assert coordinate_result["empirical_width_covers"] is None


@pytest.mark.parametrize("direct,delta_c",[(2e-4,1e-6),(1e-6,2e-4)])
def test_gamma_req_only_positive_both_allowances(direct,delta_c):
    result=s.score_coordinate(cheap(delta=delta_c),m1(),point(direct=direct),{},PROTOCOL)
    assert result["gamma_req_truth_diagnostic"] is None


def test_time_ulp_variant_rejected():
    row=cheap();row["time"]=float(np.nextafter(row["time"],1.))
    with pytest.raises(prep.PreparationError,match="binary64"):
        s.score_coordinate(row,m1(),point(),{},PROTOCOL)


def synthetic_study():
    prediction={"conditions":[]};truth={"conditions":[]}
    specs=prep.read(ROOT/prep.DOC/"conditions.json")
    for spec in specs:
        cid=spec["condition_id"]
        if cid in p.TERMINAL:
            prediction["conditions"].append({"condition":spec,"status":p.TERMINAL[cid],"predictions":None})
            truth["conditions"].append({"condition_id":cid,"points":[],"ground":None,"resource":{"counts":{}}})
        else:
            rows=[cheap(cid,r) for r in (.8,1.,1.2)]
            frozen={"cheap":rows,"M1":[m1(cid,r) for r in (.8,1.,1.2)],"M1_decision":{"selected":None},**p.cheap_decisions(rows,PROTOCOL)}
            identity={"condition":spec,"H_dense_numpy_v1":"synthetic-H","sector_indices_numpy_v1":"synthetic-sector",
                      "sector_dimension":2,"removed_scalar_hartree":0.,"constant_policy":"scalar_removed",
                      "PF_sequence_hex":[float(1.).hex()],"ordered_pauli_groups_sha256":"synthetic-groups"}
            prediction["conditions"].append({"condition":spec,"predictions":frozen,"input_identity":identity,"input_identity_sha256":"synthetic-input"})
            ground={"status":"same_H_ground_valid","energy_hartree":-1.,"condition":spec,
                    **{key:identity[key] for key in ['H_dense_numpy_v1','sector_indices_numpy_v1','sector_dimension','removed_scalar_hartree','constant_policy']},
                    "solver":"scipy.linalg.eigh(driver='evd', check_finite=True)","normalization_residual":0.,
                    "eigenpair_residual_hartree":1e-14,"first_excitation_gap_hartree":.1,"ground_vector_numpy_v1":"synthetic-ground"}
            points=[{**point(cid,r),**{key:identity[key] for key in ['H_dense_numpy_v1','sector_indices_numpy_v1','removed_scalar_hartree','PF_sequence_hex','ordered_pauli_groups_sha256']},
                     "input_identity_sha256":"synthetic-input","ground_vector_numpy_v1":"synthetic-ground"} for r in (.8,1.,1.2)]
            truth["conditions"].append({"condition_id":cid,"condition":spec,"status":"truth_complete_valid","points":points,
                 "ground":ground,
                 "resource":{"counts":{"exact_ground_solves":1,"full_PF_materializations":3,"direct_Schur_solves":3}}})
    return prediction,truth


def test_full_immutable_scoring_keeps_16_13_39_4_and_abstentions():
    prediction,truth=synthetic_study();original=(deepcopy(prediction),deepcopy(truth))
    scored=s.score_all(prediction,truth,PROTOCOL)
    assert (prediction,truth) == original
    assert scored["denominators"]["attempted_conditions"] == 16
    assert scored["denominators"]["family_units"] == 4
    assert scored["denominators"]["scored_coordinates"] == 39
    assert len(scored["decision_scores"]) == 65
    assert scored["M1_accepted_performance_count"] == 0
    assert all(r["M1_frozen_abstained"] for r in scored["coordinate_scores"])


def test_incomplete_truth_never_complete_oracle_or_denominator_selection():
    prediction,truth=synthetic_study()
    condition=next(c for c in truth["conditions"] if c["points"])
    condition["points"][1]=s.missing_point(coordinate(condition["condition_id"],1.),"continuation_undefined")
    scored=s.score_all(prediction,truth,PROTOCOL)
    assert scored["denominators"]["attempted_conditions"] == 16
    assert scored["denominators"]["scored_coordinates"] == 38
    result=next(r for r in scored["conditions"] if r["condition"]["condition_id"] == condition["condition_id"])
    assert result["native_oracle"]["complete_native_3_candidate_oracle"] is False
    assert result["native_oracle"]["complete_oracle"] is None


def test_ineligible_science_fails_closed():
    prediction,truth=synthetic_study()
    tr=next(r for r in truth["conditions"] if not r["points"])
    tr["ground"]={"energy_hartree":-1.}
    with pytest.raises(prep.PreparationError,match="ineligible"):
        s.score_all(prediction,truth,PROTOCOL)


@pytest.mark.parametrize("field",["H_dense_numpy_v1","sector_indices_numpy_v1","removed_scalar_hartree",
                                 "PF_sequence_hex","ordered_pauli_groups_sha256","input_identity_sha256","ground_vector_numpy_v1","K"])
def test_direct_source_or_contract_tamper_fails_immutable_scoring(field):
    prediction,truth=synthetic_study()
    tr=next(r for r in truth['conditions'] if r['points'])
    tr['points'][0][field]='tampered'
    with pytest.raises(prep.PreparationError,match='identity|hash|source'):
        s.score_all(prediction,truth,PROTOCOL)


@pytest.mark.parametrize("field",['H_dense_numpy_v1','sector_indices_numpy_v1','removed_scalar_hartree','constant_policy','sector_dimension'])
def test_same_H_ground_provenance_tamper_fails(field):
    prediction,truth=synthetic_study()
    tr=next(r for r in truth['conditions'] if r['points']);tr['ground'][field]='tampered'
    with pytest.raises(prep.PreparationError,match='identity'):
        s.score_all(prediction,truth,PROTOCOL)


def test_truth_valid_label_cannot_bypass_direct_gates():
    prediction,truth=synthetic_study()
    tr=next(r for r in truth['conditions'] if r['points'])
    tr['points'][0]['ground_state_overlap_probability']=.89
    with pytest.raises(prep.PreparationError,match='validity'):
        s.score_all(prediction,truth,PROTOCOL)


def test_missing_truth_record_fails_closed():
    prediction,truth=synthetic_study()
    tr=next(r for r in truth["conditions"] if r["points"]);tr["points"].pop()
    with pytest.raises(prep.PreparationError,match="39 terminal"):
        s.score_all(prediction,truth,PROTOCOL)


def allocation(tmp_path):
    evidence=tmp_path/"evidence.json";prep.write(evidence,{"synthetic":True})
    now=datetime.now(timezone.utc)
    return {"verified":True,"authority":"user_explicit_quota","allocation_phase":"prospective_truth_scoring",
        "fresh_allocation":True,"prediction_allocation_inherited":False,"deadline_renewed":False,
        "usable_cpu_quota":16,"usable_ram_bytes":128*2**30,"workers":4,"worker_rss_limit_bytes":12*2**30,
        "worker_wall_seconds":7200,"direct_coordinate_wall_seconds":1800,"job_wall_seconds":43200,
        "coordinator_reserved_ram_bytes":32*2**30,"writable_disk_quota_bytes":2*2**30,"reserved_disk_bytes":128*2**20,
        "approved_output_root":str(tmp_path/"out"),"cumulative_disk_roots":[str(tmp_path/"out")],
        "evidence":[{"path":"evidence.json","sha256":prep.sha_file(evidence)}],
        "starts_UTC":(now-timedelta(seconds=1)).isoformat(),"expires_UTC":(now+timedelta(hours=11)).isoformat()}


@pytest.mark.parametrize("field,value",[("workers",5),("usable_cpu_quota",17),("usable_ram_bytes",129*2**30),
    ("worker_rss_limit_bytes",13*2**30),("direct_coordinate_wall_seconds",1801),("worker_wall_seconds",7201),
    ("job_wall_seconds",43201),("writable_disk_quota_bytes",3*2**30),("reserved_disk_bytes",0),
    ("prediction_allocation_inherited",True),("deadline_renewed",True),("fresh_allocation",False)])
def test_fresh_allocation_hard_caps_and_no_inheritance(tmp_path,field,value):
    data=allocation(tmp_path);data[field]=value
    with pytest.raises(prep.PreparationError):
        s.allocation_gate(data,tmp_path/"out",tmp_path,[tmp_path/"out"])


def test_fresh_allocation_exact_roots_and_expiry(tmp_path):
    data=allocation(tmp_path)
    assert s.allocation_gate(data,tmp_path/"out",tmp_path,[tmp_path/"out"])["workers"] == 4
    with pytest.raises(prep.PreparationError,match="roots"):
        s.allocation_gate(data,tmp_path/"out",tmp_path,[tmp_path/"other"])
    data["expires_UTC"]=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    with pytest.raises(prep.PreparationError,match="expired"):
        s.allocation_gate(data,tmp_path/"out",tmp_path,[tmp_path/"out"])


def test_disk_reserve_stops_before_quota(tmp_path):
    data=allocation(tmp_path);(tmp_path/"out").mkdir()
    (tmp_path/"out"/"large").write_bytes(b"a"*4096)
    data["writable_disk_quota_bytes"]=128*2**20
    with pytest.raises(prep.PreparationError,match="reserve"):
        s.resource_guard(data)


def test_private_temp_links_count_metadata_without_following_targets(tmp_path):
    output=tmp_path/'out';output.mkdir()
    outside=tmp_path/'outside';outside.mkdir()
    (outside/'data').write_bytes(b'a'*8192)
    (output/'file_link').symlink_to(outside/'data')
    (output/'directory_link').symlink_to(outside,target_is_directory=True)
    expected=sum(max(f.lstat().st_size,f.lstat().st_blocks*512) for f in output.iterdir())
    assert s.disk_bytes([output]) == expected
    (outside/'data').write_bytes(b'a'*(64*1024))
    assert s.disk_bytes([output]) == expected


def test_one_shot_execution_and_worker_markers(tmp_path):
    runner.one_shot(tmp_path/"STARTED.json","synthetic")
    with pytest.raises(FileExistsError): runner.one_shot(tmp_path/"STARTED.json","synthetic")


def test_truth_bundle_real_git_blob_freeze_and_tamper(tmp_path):
    p.git(tmp_path,"init","-q","-b","synthetic-study")
    p.git(tmp_path,"config","user.name","Synthetic Test")
    p.git(tmp_path,"config","user.email","synthetic@example.invalid")
    p.git(tmp_path,"remote","add","origin","https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae.git")
    (tmp_path/"source").write_text("synthetic\n");p.git(tmp_path,"add","source");p.git(tmp_path,"commit","-qm","synthetic source")
    directory=tmp_path/"truth"
    names=s.write_bundle(directory,"truth.json","TRUTH_FROZEN.json",{"synthetic":True},{},{},{},
                         {"pre_truth_gate.json":{"status":"PASS"},"pre_tests.json":{},"pre_tests.log":"synthetic\n"})
    commit=s.commit_bundle(tmp_path,directory,names,"synthetic truth freeze")
    s.verify_bundle(tmp_path,directory,commit)
    assert prep.read(directory/"manifest.json")["manifest_self_excluded"]
    (directory/"truth.json").write_text("{}\n")
    with pytest.raises(prep.PreparationError): s.verify_bundle(tmp_path,directory,commit)
