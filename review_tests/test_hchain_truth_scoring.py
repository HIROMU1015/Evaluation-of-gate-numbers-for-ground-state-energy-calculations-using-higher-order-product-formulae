"""Synthetic scorer/access tests. No saved or newly acquired molecular truth reads."""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path

import numpy as np
import pytest

from review_response.hchain_input_reference_preparation import Ledger, PreparationError, sha_array
from review_response.hchain_prediction_phase import PREP
from review_response.hchain_selective_calibration_schedule import BETA, EPSILON, cheap_policy
from review_response.hchain_truth_scoring import (
    DOC, METHOD, bundle, commit_stage, git, score_action, score_all,
    score_coordinate, truth_quality, verify_stage,
)
from review_response.run_hchain_truth_scoring import ground_point, helper, serial_truth


ROOT = Path(__file__).resolve().parents[1]


def method():
    return json.loads((ROOT/METHOD).read_text())


def truth_point(identifier="x",time=1.,delta=1e-6,valid=True):
    return {"system":"H2","candidate_id":identifier,"time":time,"time_hex":time.hex(),
            "signed_direct_shift_hartree":delta,"minimum_selected_phase_gap_radians":.2,
            "ground_state_overlap_probability":1.,"previous_branch_overlap_probability":1.,
            "unitarity_residual_frobenius":1e-14,"eigenpair_residual_2_norm":1e-14,
            "quality":{"physical_branch_valid":valid,"status":"resolved" if valid else "truth_branch_indeterminate"}}


def m1_point(identifier="x",time=1.,delta=1e-6,width=1e-7,abstain=False):
    return {"candidate_id":identifier,"time":time,"time_hex":time.hex(),"delta_M_hartree":delta,
            "width_M_hartree":width,"abstain":abstain,"core_prediction":{
                "available_dimension":2,"requested_primary_dimension":4,"primary_dimension_used":2,
                "failure_reasons":["primary_dimension_unavailable"] if abstain else [],
                "prefixes":[{"dimension":2,"selected_unwrapped_energy_hartree":-1.+delta}]}}


def test_new_authorization_preserves_prediction_and_bounds():
    auth = json.loads((ROOT/DOC/"authorization.json").read_text())
    assert auth["prediction_commit"] == "858265dacd304c844029ce2576b4559221f0c7c1"
    assert auth["limits"]["same_H_ground_solves"] == 3
    assert auth["limits"]["full_PF_builds"] == auth["limits"]["direct_Schur_solves"] == 9
    for key in ("prediction_modification","budget_policy_width_or_threshold_adjustment",
                "historical_H6_Z2_ground_reuse","extra_coordinates_or_anchors","scientific_rescue_or_rerun","GPU","push","next_stage"):
        assert auth["permissions"][key] is False


@pytest.mark.parametrize("field",["unitarity_residual_frobenius","eigenpair_residual_2_norm"])
def test_numerical_gate_fails_not_repaired(field):
    point = truth_point()
    point[field] = 1e-9
    with pytest.raises(PreparationError,match="gate failed"):
        truth_quality(point,method())


@pytest.mark.parametrize("field",["signed_direct_shift_hartree","minimum_selected_phase_gap_radians"])
def test_nonfinite_truth_rejected(field):
    point = truth_point()
    point[field] = math.nan
    with pytest.raises(PreparationError,match="nonfinite"):
        truth_quality(point,method())


@pytest.mark.parametrize("field,value",[("minimum_selected_phase_gap_radians",1e-8),
                                      ("ground_state_overlap_probability",.89),
                                      ("previous_branch_overlap_probability",.89)])
def test_phase_overlap_warning_indeterminate(field,value):
    point = truth_point()
    point[field] = value
    quality = truth_quality(point,method())
    assert quality["status"] == "truth_branch_indeterminate"
    assert quality["physical_branch_valid"] is False


def test_ground_degenerate_indeterminate_before_pf_selection():
    h = np.eye(2,dtype=complex)
    spec = {"H_sha256_numpy_v1":sha_array(h),"sector_indices_sha256_numpy_v1":"synthetic","sector_dimension":2}
    with pytest.raises(PreparationError,match="degenerate"):
        ground_point(h,spec,method(),Ledger())


def test_ground_eigenpair_same_matrix():
    h = np.asarray([[-1.,.1],[.1,1.]],dtype=complex)
    spec = {"H_sha256_numpy_v1":sha_array(h),"sector_indices_sha256_numpy_v1":"synthetic","sector_dimension":2}
    ledger = Ledger()
    record,state = ground_point(h,spec,method(),ledger)
    assert record["H_sha256_numpy_v1"] == sha_array(h)
    assert np.linalg.norm(h@state-record["energy_hartree"]*state) < 1e-12
    assert ledger.counts["full_H_ground_solves"] == 1
    assert record["historical_Z2_ground_used"] is False


def test_helper_initial_ground_then_previous_without_substitution():
    direct = helper(ROOT)
    unitary = np.diag(np.exp(1j*np.array([-.2,.4])))
    initial,_ = direct(unitary,np.array([1.,0.]),-.2,1.,108,EPSILON,None,1e-8)
    assert abs(initial["signed_direct_shift_hartree"]) < 1e-14
    continued,_ = direct(unitary,np.array([1.,0.]),-.2,1.,108,EPSILON,np.array([0.,1.]),1e-8)
    assert continued["branch_selection_disagrees_with_comparator"]
    assert continued["ground_state_overlap_probability"] == 0.
    assert truth_quality(continued,method())["physical_branch_valid"] is False
    assert isinstance(serial_truth(continued)["selected_eigenvalue"],list)


def test_abstention_does_not_suppress_point_diagnostics():
    truth = truth_point()
    cheap = {"candidate_id":"x","time":1.,"delta_C_hartree":3e-6}
    result = score_coordinate(cheap,m1_point(abstain=True),truth,-1.)
    assert result["M1_policy_abstained"]
    assert result["E_M_hartree"] == 0.
    assert result["empirical_width_covers"] and result["branch_correct_shift_gap"]
    assert result["unwrap_integers_compared"] is False


def test_strict_branch_but_nonstrict_width_coverage():
    truth = truth_point(delta=0.)
    cheap = {"candidate_id":"x","time":1.,"delta_C_hartree":0.}
    scored = score_coordinate(cheap,m1_point(delta=.1,width=.1),truth,-1.)
    assert scored["branch_correct_shift_gap"] is False
    assert scored["empirical_width_covers"] is True
    assert scored["g_target_projected_unit_circle_chord"] == 2*math.sin(.1)
    assert scored["g_rho_others"] is None


def test_budget_uses_absolute_error_without_edit_or_ceil():
    cheap = {"K":108,"B0":{"time":.5,"budget":2e6}}
    action = {"candidate_id":"x","time":1.,"budget":1e6+.123,"fallback":False}
    original = deepcopy(action)
    negative = score_action("H2","B2",action,cheap,{"x":truth_point(delta=-1e-5)})
    positive = score_action("H2","B2",action,cheap,{"x":truth_point(delta=1e-5)})
    assert action == original
    assert negative["total_error_hartree"] == positive["total_error_hartree"] == 1e-5+BETA*108/action["budget"]
    assert negative["frozen_budget"] == 1e6+.123


def test_unsafe_anchor_remains_unsafe_fallback():
    cheap = {"K":108,"B0":{"time":1.,"budget":100.}}
    action = {"candidate_id":"x","time":1.,"budget":100.,"fallback":True}
    scored = score_action("H2","always_M1",action,cheap,{"x":truth_point()})
    assert scored["unsafe"] is True
    assert scored["safe_target_met"] is False


def test_indeterminate_truth_does_not_receive_safe_label():
    cheap = {"K":108,"B0":{"time":.5,"budget":2e6}}
    action = {"candidate_id":"x","time":1.,"budget":1e6,"fallback":False}
    scored = score_action("H2","H1",action,cheap,{"x":truth_point(valid=False)})
    assert scored["raw_arithmetic_safe"]
    assert scored["safe"] is None and scored["safe_target_met"] is None


@pytest.mark.parametrize("budget",[None,0.,-1.,math.inf])
def test_invalid_budget_not_replaced(budget):
    action = {"candidate_id":"x","time":1.,"budget":budget,"fallback":False}
    with pytest.raises(PreparationError,match="invalid frozen budget"):
        score_action("H2","B2",action,{"K":108,"B0":{"time":.5,"budget":1e6}},{"x":truth_point()})


def test_time_no_nearest_matching():
    truth = truth_point()
    action = {"candidate_id":"x","time":np.nextafter(1.,2.),"budget":1e6,"fallback":False}
    with pytest.raises(PreparationError,match="time mismatch"):
        score_action("H2","B2",action,{"K":108,"B0":{"time":.5,"budget":1e6}},{"x":truth})


def synthetic_data():
    prediction = {"cheap_B0_B1_B2_q":{},"M1":{},"H1":{},"always_M1_decisions":{}}
    points,grounds = [],{"systems":{}}
    for system in ("H2","H4","H6"):
        cheap = [{"candidate_id":f"{system}_{index}","time":t,"delta_C_hartree":1e-6}
                 for index,t in enumerate((.5,.65,.8))]
        policy = cheap_policy(cheap,108)
        prediction["cheap_B0_B1_B2_q"][system] = policy
        prediction["H1"][system] = {"action":deepcopy(policy["B2"])}
        prediction["always_M1_decisions"][system] = {"selected":deepcopy(policy["B0"])}
        prediction["M1"][system] = [m1_point(row["candidate_id"],row["time"]) for row in cheap]
        for row in cheap:
            point = truth_point(row["candidate_id"],row["time"])
            point["system"] = system
            points.append(point)
        grounds["systems"][system] = {"energy_hartree":-1.}
    return prediction,{"points":points},grounds


def test_whole_scorer_immutable_three_systems_not_nine_samples():
    prediction,truth,ground = synthetic_data()
    original = deepcopy(prediction)
    result = score_all(prediction,truth,ground)
    assert prediction == original
    assert len(result["coordinate_scores"]) == 9
    assert len(result["decision_scores"]) == 24
    assert result["evidence_axes"]["B2"]["safe"] == 3
    assert all(row["q_one_conditional_path_performance"] == "not_measured" for row in result["system_summaries"].values())
    assert result["next_stage_authorized"] is False


def test_truth_requires_nine_unique_exact_ids():
    prediction,truth,ground = synthetic_data()
    truth["points"][-1] = deepcopy(truth["points"][0])
    with pytest.raises(PreparationError,match="nine unique"):
        score_all(prediction,truth,ground)


def test_real_truth_freeze_byte_gate(tmp_path):
    git(tmp_path,"init","-q")
    git(tmp_path,"config","user.name","Synthetic Test")
    git(tmp_path,"config","user.email","synthetic@example.invalid")
    git(tmp_path,"remote","add","origin","https://github.com/HIROMU1015/synthetic-test.git")
    (tmp_path/"source").write_text("synthetic\n")
    git(tmp_path,"add","source")
    git(tmp_path,"commit","-qm","synthetic source")
    directory = tmp_path/"truth"
    files = bundle(directory,"truth.json","TRUTH_FROZEN.json",{"synthetic":True},{"kind":"TRUTH_FROZEN"},{},{},{})
    commit = commit_stage(tmp_path,directory,files,"synthetic freeze")
    verify_stage(tmp_path,directory,commit,"TRUTH_FROZEN.json")
    (directory/"truth.json").write_text("{}")
    with pytest.raises(PreparationError):
        verify_stage(tmp_path,directory,commit,"TRUTH_FROZEN.json")


def test_wrapper_has_no_predictor_or_historical_runner_execution():
    text = (ROOT/"review_response/run_hchain_truth_scoring.py").read_text()
    assert "checked_functions(" in text
    for forbidden in ("analyze_coordinate(","run_shared_schedule(",".cheap(","import cupy","nvidia-smi"):
        assert forbidden not in text
    assert text.index('stages["truth_commit"] = commit_stage') < text.index('scored = score_all(')
    assert text.index('stages["ground_commit"] = commit_stage') < text.index('unitary = full_unitary(')
