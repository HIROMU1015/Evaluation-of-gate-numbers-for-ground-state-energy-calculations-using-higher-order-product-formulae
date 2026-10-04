"""Synthetic/source-only extension tests; never open molecular truth artifacts."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from review_response.hchain_odd_extension import (
    DOC, SYSTEMS, SystemLedger, dimensions, plan_rows, primary_rank, validate_plan,
)
from review_response.hchain_input_reference_preparation import PreparationError, checked_functions, sha_file
from review_response.hchain_prediction_phase import CoordinateActions, ReadBoundary, finite_json
from review_response.hchain_selective_calibration_schedule import cheap_policy, h1_final, run_shared_schedule
from review_response.pf_spectral_recoverability_d2 import analyze_coordinate
from review_response.run_hchain_odd_extension import validate_runtime

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("n,a,b,sector,cisd,primary", [(3,2,0,3,3,2),(5,3,1,50,38,8),(7,4,2,735,171,8),(8,4,4,4900,361,8)])
def test_dimensions_and_predeclared_rank(n,a,b,sector,cisd,primary):
    assert dimensions(n,a,b) == (sector,cisd)
    assert primary_rank(sector) == primary


@pytest.mark.parametrize("key,maximum", [("reference_pf_actions",34),("reference_h_exponential_actions",34),
    ("candidate_cheap_pf_actions",3),("candidate_h_exponential_actions",3),("m1_pf_vector_actions",6),
    ("m1_h_matvecs",6),("Arnoldi_chains",3),("full_H_ground_solves",1),("full_pf_unitary_builds",3),
    ("direct_Schur_solves",3),("target_phase_gaps",3)])
def test_per_system_ceilings_before_action(key,maximum):
    ledger = SystemLedger(2)
    for _ in range(maximum):
        ledger.charge(key,999)
    with pytest.raises(PreparationError):
        ledger.charge(key,999)
    assert ledger.counts[key] == maximum


def test_plan_excludes_failed_h3_without_rescue():
    ref = {s:{"qualified":s!="H3","t_ref":1.23456789012345 if s!="H3" else None} for s in SYSTEMS}
    identity = {s:{"sector_dimension":d,"K":100} for s,d in zip(SYSTEMS,(3,50,735))}
    rows = plan_rows(ref,identity)
    assert len(rows) == 6 and {r["system"] for r in rows} == {"H5","H7"}
    assert validate_plan(rows,ref,identity) == rows
    changed = deepcopy(rows)
    changed[0]["time"] = np.nextafter(changed[0]["time"],np.inf)
    with pytest.raises(PreparationError):
        validate_plan(changed,ref,identity)


def test_grid_fit_and_pf_sources_fixed():
    auth = json.loads((ROOT/DOC/"protocol.json").read_text())
    assert auth["remote_gate"]["tip"] == auth["base_commit"]
    assert auth["permissions"]["push"] is False and auth["permissions"]["H8_science"] is False
    assert [r["hex"] for r in auth["reference_grid"]] == [float(t).hex() for t in np.geomspace(.02,1.8,34)]
    old = json.loads((ROOT/"docs/second_study_v2/hchain_independent_validation_20261004/system_and_pf_contract.json").read_text())
    assert auth["PF"]["canonical_sequence_hex"] == old["PF"]["canonical_sequence_hex"]
    registry = json.loads((ROOT/DOC/"source_registry.json").read_text())
    assert len(registry["sources"]) >= 20
    for row in registry["sources"]:
        assert sha_file(ROOT/row["path"]) == row["sha256"]
        assert row["origin_result_commit"] and row["verified_snapshot_commit"] == auth["base_commit"]


def test_below_floor_has_no_reference_and_no_threshold_change():
    contract = json.loads((ROOT/"docs/second_study_v2/hchain_independent_validation_20261004/cheap_reference_scale_contract.json").read_text())
    source = contract["fit_function"]
    fit = checked_functions(ROOT/source["path"],source["sha256"],["leading_fit"])["leading_fit"]
    before = deepcopy(contract)
    result = fit(np.geomspace(.02,1.8,34),np.full(34,1e-15),contract["fit_rules"],4)
    assert not result["qualified"] and result["selected_window"] is None
    assert before == contract


def synthetic_points(signs=(1,1,1)):
    return [{"candidate_id":f"p{i}","time":t,"delta_C_hartree":s*1e-6}
            for i,(t,s) in enumerate(zip((.5,.65,.8),signs))]


def test_q_zero_h1_does_not_see_comparator():
    cheap = cheap_policy(synthetic_points(),100)
    assert cheap["q"] == 0
    assert h1_final(cheap)["action"] == cheap["B2"]
    with pytest.raises(PreparationError):
        h1_final(cheap,[])


def test_real_schedule_conditional_then_h1_then_comparator():
    events = []
    def cheap(name):
        events.append(("cheap",name))
        return synthetic_points((1,1,-1) if name=="q1" else (1,1,1)),100
    def m1(name):
        events.append(("m1",name))
        return [{"candidate_id":p["candidate_id"],"time":p["time"],"abstain":False,"e_use":2e-6}
                for p in synthetic_points()]
    def freeze(name,payload,digest):
        events.append((name,digest))
    result = run_shared_schedule(["q0","q1"],cheap,m1,freeze)
    names = [r[0] for r in events]
    assert events.index(("m1","q1")) > names.index("ACQUISITION_FROZEN")
    assert events.index(("m1","q1")) < names.index("H1_FROZEN")
    assert events.index(("m1","q0")) > names.index("H1_FROZEN")
    assert result["H1"]["q0"]["action"] == result["cheap"]["q0"]["B2"]


def test_read_boundary_blocks_historical_truth_and_writes(tmp_path):
    output = tmp_path/"artifacts/new"
    allowed = tmp_path/"source.py"
    boundary = ReadBoundary(tmp_path,[allowed],output)
    boundary.hook("open",(str(allowed),"r",0))
    boundary.hook("open",(str(output/"input.npz"),"wb",0))
    for name in ("artifacts/old/direct.json","artifacts/old/ground.npz","source.py"):
        with pytest.raises(PreparationError):
            boundary.hook("open",(str(tmp_path/name),"w" if name=="source.py" else "r",0))


def test_nonfinite_width_never_becomes_small():
    missing=[]
    assert finite_json({"width":float("inf")},missing=missing)["width"] is None
    assert missing


def test_runtime_member_set_and_hash_gates(tmp_path):
    private = tmp_path/".runtime"
    private.mkdir()
    path = private/"H3_input.npz"
    np.savez(path,cisd=np.array([1.,0.]))
    inputs = {"runtime_files":[{"path":path.name,"bytes":path.stat().st_size,"sha256":sha_file(path)}]}
    validate_runtime(tmp_path,inputs)
    (private/"unexpected.json").write_text("{}")
    with pytest.raises(PreparationError):
        validate_runtime(tmp_path,inputs)


def test_rank_deficiency_remains_abstention():
    rules=json.loads((ROOT/"docs/second_study_v2/hchain_independent_validation_20261004/rank_aware_M1_amendment.json").read_text())["numerical_rules"]
    h=np.diag([.1,.2,.4]).astype(complex)
    u=np.diag(np.exp(1j*np.diag(h).real))
    p,_=analyze_coordinate(start=np.array([1.,0.,0.]),apply_u=lambda v:u@v,apply_h=lambda v:h@v,
        time_value=1.,prefix_dimensions=[1,2],primary_dimension=2,previous_vector=None,
        numerical_rules=rules,epsilon_hartree=.00015936001019904,beta=1.2,rotations_per_step=100)
    assert p["available_dimension"] == 1 and p["abstained"]
    assert "primary_dimension_unavailable" in p["failure_reasons"]
