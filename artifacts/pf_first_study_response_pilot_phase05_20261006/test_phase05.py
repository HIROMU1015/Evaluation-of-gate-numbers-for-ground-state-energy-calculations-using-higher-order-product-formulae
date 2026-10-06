"""All numerical arrays below are deterministic synthetic fixtures, dimension <=10."""
import ast
import hashlib
from pathlib import Path
import numpy as np
import pytest
from scipy.linalg import expm
from phase05_math import *
from phase05_phase_a import PhaseAInput,build_predictions,freeze_prediction_identity
from phase05_phase_b import verify_frozen_predictions,score_saved_truth,classify_outcome
from phase05_runner import verify_source_hash,main

def fixture(n=5):
    rng=np.random.default_rng(20261006+n)
    x=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n))
    H=(x+x.conj().T)/2
    psi=rng.normal(size=n)+1j*rng.normal(size=n)
    psi/=np.linalg.norm(psi)
    return H,psi

def test_exact_target_invariance_all_synthetic_eigenstates():
    H,psi=fixture()
    _,vectors=np.linalg.eigh(H)
    A,_=fixture()
    z=np.arange(5)+1j*np.arange(5)[::-1]
    z=z-psi*np.vdot(psi,z)
    X=np.outer(z,psi.conj())-np.outer(psi,z.conj())
    corrected=A-(H@X-X@H)
    for e in vectors.T:
        assert abs(np.vdot(e,corrected@e)-np.vdot(e,A@e))<2e-13
    ledger=ActionLedger(); basis=build_response_basis(H,psi,ledger)
    assert np.vdot(psi,(H@X-X@H)@psi).real==pytest.approx(2*np.vdot(z,basis.r).real)

def test_exact_input_state_generates_zero_correction():
    H=np.diag([0.,1.,2.]); psi=np.array([1.,0.,0.])
    ledger=ActionLedger(); basis=build_response_basis(H,psi,ledger)
    assert basis.Z.shape[1]==0
    a=np.array([0.,2.,1.],complex)
    z,d=solve_response_least_squares(factor_response(basis,8,ledger),a,ledger)
    assert compute_response_proxy(.3,z,basis.r)==.3

def test_identity_observable_generates_zero_correction():
    H,psi=fixture(); ledger=ActionLedger(); basis=build_response_basis(H,psi,ledger)
    a=project(psi,3*psi,ledger)
    z,d=solve_response_least_squares(factor_response(basis,8,ledger),a,ledger)
    assert compute_response_proxy(3.,z,basis.r)==pytest.approx(3.,abs=2e-13)
    z,d=solve_response_least_squares(factor_response(basis,8,ledger),np.zeros(5),ledger)
    assert d["relative_residual"]==0.

def test_commuting_counterexample_preserved_not_a_zero_rule():
    H=np.diag([0.,1.]); psi=np.sqrt([.9,.1]); ledger=ActionLedger()
    basis=build_response_basis(H,psi,ledger)
    a=project(psi,H@psi,ledger)
    z,d=solve_response_least_squares(factor_response(basis,8,ledger),a,ledger)
    assert 2*np.vdot(z,basis.r).real==pytest.approx(.225)
    assert compute_response_proxy(.1,z,basis.r)==pytest.approx(-.125)

def test_full_response_removes_first_order_sensitivity_2x2():
    H=np.diag([0.,2.]); A=np.array([[.3,.7],[.7,-.2]])
    def estimator(theta):
        psi=np.array([np.cos(theta),np.sin(theta)]); ledger=ActionLedger()
        basis=build_response_basis(H,psi,ledger)
        a=project(psi,A@psi,ledger)
        z,d=solve_response_least_squares(factor_response(basis,8,ledger),a,ledger)
        return compute_response_proxy(np.vdot(psi,A@psi).real,z,basis.r)
    h=1e-4
    assert abs((estimator(h)-estimator(-h))/(2*h))<1e-7
    assert (np.vdot([np.cos(h),np.sin(h)],A@np.array([np.cos(h),np.sin(h)])).real-.3)/h >1.3

def test_full_residual_ls_differs_from_projected_equation():
    L=np.array([[2.,1.],[1.,3.]]); Z=np.array([[1.],[0.]])
    b=Basis(np.array([1.,0.]),0,np.zeros(2),Z,np.zeros(2),L@Z,L@Z,False,())
    ledger=ActionLedger(); f=factor_response(b,1,ledger)
    z,d=solve_response_least_squares(f,np.array([0.,1.]),ledger)
    assert z[0]==pytest.approx(.2)
    assert d["d_norm"]==pytest.approx(np.sqrt(.8))
    assert np.linalg.solve(Z.T@L@Z,Z.T@np.array([0.,1.]))[0]==0

def test_truncated_svd_residual_and_minimum_norm():
    H,psi=fixture(); ledger=ActionLedger(); basis=build_response_basis(H,psi,ledger)
    f=factor_response(basis,2,ledger); a=np.arange(5)+1j
    z,d=solve_response_least_squares(f,a,ledger)
    c=np.linalg.lstsq(f.B,a,rcond=KAPPA*EPS*max(f.B.shape))[0]
    assert np.allclose(z,f.Z@c)
    assert d["d_norm"]==pytest.approx(np.linalg.norm(a-f.B@c))
    assert d["relative_residual"]==pytest.approx(np.linalg.norm(a-f.B@c)/np.linalg.norm(a))

def test_singular_values_below_frozen_cutoff_are_dropped():
    Z=np.eye(3)[:,:2]; B=Z@np.diag([1.,1e-18])
    b=Basis(np.array([0.,0.,1.]),0,np.zeros(3),Z,np.zeros(3),B,B,False,())
    ledger=ActionLedger(); f=factor_response(b,2,ledger)
    z,d=solve_response_least_squares(f,np.array([1.,1.,0.]),ledger)
    assert d["effective_rank"]==1
    assert np.allclose(z,[1.,0.,0.]) and d["d_norm"]==pytest.approx(1.)

def test_rank_deficient_krylov_stops_without_replacement():
    H=np.diag([0.,1.,2.]); psi=np.sqrt([.9,.1,0.]); ledger=ActionLedger()
    b=build_response_basis(H,psi,ledger)
    assert b.Z.shape==(3,1) and b.stopped
    assert ledger.synthetic["H_matvec_count"]==2

def test_basis_shared_and_counts_with_full_rank_eight():
    H,psi=fixture(10); ledger=ActionLedger(); b=build_response_basis(H,psi,ledger)
    assert b.Z.shape[1]==8
    assert ledger.synthetic["H_matvec_count"]==9
    assert ledger.synthetic["projection_count"]==25
    assert ledger.synthetic["orthogonalization_count"]==56
    for m in M_VALUES:
        state,data=solve_ritz_state(b,m,ledger)
        assert np.linalg.norm(state)==pytest.approx(1.)
    assert ledger.synthetic["H_matvec_count"]==9

def test_actual_krylov_span_matches_requested_unprojected_powers():
    H,psi=fixture(7); ledger=ActionLedger(); b=build_response_basis(H,psi,ledger,max_m=4)
    Q=np.eye(7)-np.outer(psi,psi.conj())
    raw=np.column_stack([Q@np.linalg.matrix_power(H,j)@b.r for j in range(4)])
    rawQ=np.linalg.qr(raw)[0]
    assert np.linalg.norm(rawQ@rawQ.conj().T-b.Z@b.Z.conj().T)<1e-12

def test_echo_observable_matches_saved_definition_and_signed_order():
    H,psi=fixture(3); G=H+np.diag([1.,2.,3.])
    t=.2; U=expm(1j*G*t); W=expm(-1j*H*t)@U
    ledger=ActionLedger(); base,a=compute_a_from_echo(W,psi,t,ledger)
    A=(W-W.conj().T)/(2j*t)
    assert base==pytest.approx(np.vdot(psi,A@psi).real)
    assert np.allclose(a,(np.eye(3)-np.outer(psi,psi.conj()))@A@psi)
    assert np.allclose(W.conj().T,U.conj().T@expm(1j*H*t))
    assert np.linalg.norm(expm(1j*H*t)@U.conj().T-W.conj().T)>1e-4
    assert ledger.synthetic["PF_forward_action_count"]==1
    assert ledger.synthetic["PF_adjoint_action_count"]==1

def test_same_fit_rule_matches_inherited_function_without_importing_loaders():
    root=Path(__file__).resolve().parents[2]
    text=(root/"review_response/pf_first_study_phase_common.py").read_text()
    tree=ast.parse(text)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="scaled_power_fit")
    scope={"np":np,"Sequence":list,"Any":object}
    exec(compile(ast.Module(body=[node],type_ignores=[]),"inherited_fit_only","exec"),scope)
    t=np.array(TRAIN); y=3*t**4-.7*t**6
    inherited=scope["scaled_power_fit"](t,y,(4,6))
    for arm in ("baseline","response","ritz"):
        model=fit_two_term_model(TRAIN,y,y,["resolved"]*5)["raw_positive_even_two_term"]
        assert model["coefficients"]==pytest.approx(inherited["coefficients"])
        assert model["condition_number"]==pytest.approx(inherited["scaled_design_condition_number"])
        assert model["status"]=="fit_ok"
    assert fit_two_term_model(TRAIN,y,y,["unresolved"]*5)["raw_positive_even_two_term"]["status"]=="not_identifiable"

def synthetic_predictions():
    H,psi=fixture(4); G,_=fixture(4)
    echoes={s*t:expm(1j*G*(s*t)**5) for t in TRAIN+EVAL for s in (1,-1)}
    ledger=ActionLedger(); data=build_predictions(PhaseAInput(H,psi,echoes),ledger)
    raw,digest=freeze_prediction_identity(data)
    frozen=verify_frozen_predictions(raw,digest,"a"*40,raw)
    return frozen,ledger

def test_phase_a_rejects_evaluation_truth_and_production_arrays():
    H,psi=fixture()
    with pytest.raises(TypeError):
        PhaseAInput(H,psi,{},evaluation_truth=object())
    with pytest.raises(ValueError,match="synthetic"):
        build_response_basis(np.eye(36),np.eye(36)[0],ActionLedger())
    with pytest.raises(RuntimeError,match="disabled"):
        main(["--phase-a"])
    with pytest.raises(RuntimeError,match="disabled"):
        main(["--phase-b"])

def test_source_hash_mismatch_stops_before_decode(tmp_path):
    path=tmp_path/"synthetic_bytes"; path.write_bytes(b"synthetic only")
    with pytest.raises(ValueError,match="source SHA"):
        verify_source_hash(path,"0"*64)
    assert verify_source_hash(path,hashlib.sha256(path.read_bytes()).hexdigest())

def test_phase_a_hash_mismatch_stops_before_truth():
    with pytest.raises(ValueError,match="mismatch"):
        verify_frozen_predictions(b"changed","0"*64,"a"*40,b"original")
    with pytest.raises(ValueError,match="mismatch"):
        verify_frozen_predictions(b"changed",hashlib.sha256(b"changed").hexdigest(),"a"*40,b"original")

def test_sign_crossing_is_nonadditive_and_all_twelve_rows_retained():
    frozen,ledger=synthetic_predictions()
    import json
    payload=json.loads(frozen.raw)
    for predictions in payload["predictions"].values():
        for p in predictions:
            p["prediction"]=.25
    raw,digest=freeze_prediction_identity(payload)
    frozen=verify_frozen_predictions(raw,digest,"a"*40,raw)
    coords=[s*t for t in EVAL for s in (1,-1)]
    truth=[{"time":t,"direct_shift":-1.,"exact_proxy":0.,"branch_reliable":True} for t in coords]
    result=score_saved_truth(frozen,truth)
    assert all(len(a["rows"])==12 for a in result["arms"].values())
    assert all(a["sign_crossing_count"]==12 for a in result["arms"].values())
    assert all(r["underestimation"]==pytest.approx(abs(r["direct_shift"])-abs(r["prediction"])) for r in result["arms"]["A1"]["rows"])
    assert not any("component" in k for r in result["arms"]["A1"]["rows"] for k in r)
    assert result["saved_direct_truth_read_count"]==12 and result["new_direct_truth_count"]==0

def test_science_counters_stay_zero_through_complete_synthetic_pipeline():
    frozen,ledger=synthetic_predictions()
    assert all(v==0 for v in ledger.science.values())
    assert ledger.synthetic["PF_forward_action_count"]>0

def test_saved_oracle_arm_added_only_in_phase_b_without_actions():
    frozen,ledger=synthetic_predictions()
    before=ledger.synthetic.copy()
    oracle=[{"time":s*t,"proxy":.7*(s*t)**4,"quality":"resolved"} for t in TRAIN+EVAL for s in (1,-1)]
    truth=[{"time":s*t,"direct_shift":.7*(s*t)**4,"exact_proxy":.7*(s*t)**4,
        "branch_reliable":True} for t in EVAL for s in (1,-1)]
    import json
    assert "A3" not in json.loads(frozen.raw)["predictions"]
    result=score_saved_truth(frozen,truth,oracle)
    assert result["arms"]["A3"]["S_abs"]<1e-15
    assert result["saved_exact_proxy_read_count"]==22
    assert ledger.synthetic==before

def test_zero_residual_reuses_baseline_without_ritz_pf_actions():
    H=np.diag([0.,1.]);psi=np.array([1.,0.])
    echoes={s*t:np.diag(np.exp(1j*np.array([.2,.3])*(s*t)**5)) for t in TRAIN+EVAL for s in (1,-1)}
    ledger=ActionLedger(); data=build_predictions(PhaseAInput(H,psi,echoes),ledger)
    assert data["effective_basis_dimension"]==0
    assert ledger.synthetic["H_matvec_count"]==1
    assert ledger.synthetic["PF_forward_action_count"]==22
    assert ledger.synthetic["PF_adjoint_action_count"]==22
    assert ledger.synthetic["PF_action_on_ritz_state_count"]==0

def test_joint_eight_dimension_plan_matches_instrumented_synthetic_counts():
    H,psi=fixture(10)
    G=H+np.diag(np.arange(10))
    echoes={s*t:expm(1j*G*(s*t)**5) for t in TRAIN+EVAL for s in (1,-1)}
    ledger=ActionLedger(); data=build_predictions(PhaseAInput(H,psi,echoes),ledger)
    assert data["effective_basis_dimension"]==8
    assert ledger.synthetic["H_matvec_count"]==9
    assert ledger.synthetic["PF_forward_action_count"]==110
    assert ledger.synthetic["PF_adjoint_action_count"]==22
    assert ledger.synthetic["PF_action_on_original_state_count"]==44
    assert ledger.synthetic["PF_action_on_ritz_state_count"]==88
    assert ledger.synthetic["small_dense_response_solve_count"]==88
    assert ledger.synthetic["response_svd_factorization_count"]==4
    assert ledger.synthetic["small_dense_ritz_eigh_count"]==4
    assert ledger.synthetic["projection_count"]==47
    assert ledger.synthetic["orthogonalization_count"]==56

def test_outcomes_preserve_tradeoffs_and_no_percentage_tuning():
    base={"S_abs":10.,"S_under":5.}
    response={"S_abs":8.,"S_under":4.,"H_actions":9,"PF_actions":44}
    ritz={"S_abs":9.,"S_under":4.,"H_actions":9,"PF_actions":22}
    assert classify_outcome(base,response,ritz,residual_converged=True,response_point_improved=True)=="response_specific_support"
    response["S_abs"]=9.5
    assert classify_outcome(base,response,ritz,residual_converged=True,response_point_improved=True)=="generic_state_improvement"
    response["S_abs"]=11.
    assert classify_outcome(base,response,ritz,residual_converged=True,response_point_improved=True)=="point_only"
    assert classify_outcome(base,response,ritz,residual_converged=True,response_point_improved=True,stable=False)=="no_benefit_numerically_unstable"
