"""Tiny spectral fixtures for FS-R0.1; no production arrays/source loads."""
from pathlib import Path
import sys
from unittest.mock import Mock
import numpy as np
import pytest

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import branch_math as m
from phase_a_v2 import ContextV2

SOURCE='a'*64
def unitary(phases):return np.diag(np.exp(1j*np.asarray(phases)))
def previous(v,index=0,time=.1,source=SOURCE):
    return dict(vector=v,source_identity_sha256=source,index=index,time=time,branch_id=m.namespace(source,index))
def solve(U,g,t=.1,index=0,prior=None):return m.solve_point(U,g,0.,t,SOURCE,index,ContextV2('synthetic'),prior)

def test_01_first_maximum_ground_overlap():
    ground=np.array([np.sqrt(.1),np.sqrt(.9)])
    row,vector=solve(unitary([.1,.2]),ground)
    assert row['selection_rule']=='maximum_exact_ground_overlap' and row['ground_overlap']==pytest.approx(.9)
    np.testing.assert_allclose(abs(vector),[0,1])

def test_02_later_uses_previous_despite_ground_disagreement():
    row,vector=solve(unitary([.1,.2]),np.array([0,1]),.2,1,previous(np.array([1,0])))
    assert row['selection_rule']=='maximum_previous_selected_vector_overlap' and row['disagreement_flag']
    assert row['ground_overlap']==0 and row['previous_vector_overlap']==1
    np.testing.assert_allclose(abs(vector),[1,0])

@pytest.mark.parametrize('old',[6,9,'6','9'])
def test_03_historical_branch_ID_rejected(old):
    with pytest.raises(m.BranchFailure,match='historical'):m.validate_branch_id(old,SOURCE,0)

def test_04_new_namespace():
    assert m.namespace(SOURCE,0).startswith('FS-R1:'+SOURCE+':positive:')
    with pytest.raises(m.BranchFailure):m.validate_branch_id(m.namespace('b'*64,0),SOURCE,0)

def test_05_wrong_prior_source():
    with pytest.raises(m.BranchFailure,match='source'):solve(unitary([.1,.2]),np.array([1,0]),.2,1,previous(np.array([1,0]),source='b'*64))

def test_06_previous_vector_selector():
    row,_=solve(unitary([.1,.2]),np.ones(2)/np.sqrt(2),.2,1,previous(np.array([0,1])))
    assert row['previous_vector_overlap']==1 and row['selected_ordinal']==1

def test_07_overlap_below_gate():
    v=np.array([np.sqrt(.89),np.sqrt(.11)])
    with pytest.raises(m.BranchFailure,match='below 0.9'):solve(unitary([.1,.2]),v,.2,1,previous(v))

def test_08_exact_tie_deterministic_phase_order():
    row,_=solve(unitary([.2,.1]),np.ones(2)/np.sqrt(2))
    assert row['selected_ordinal']==0 and row['selected_eigenphase']==pytest.approx(.1)

def test_09_projector_basis_rotation_invariant():
    values=np.exp(1j*np.array([.1,.1,.4]));ground=np.array([1,0,0],dtype=complex)
    reference=np.array([1,1,0],dtype=complex)/np.sqrt(2)
    Q=np.eye(3,dtype=complex);R=Q.copy();R[:2,:2]=np.array([[1,1],[-1,1]])/np.sqrt(2)
    left,la=m.choose(values,Q,ground,reference);right,ra=m.choose(values,R,ground,reference)
    np.testing.assert_allclose(left,right,atol=5e-15,rtol=0)
    assert la['phase_cluster_size']==ra['phase_cluster_size']==2
    assert ra['previous_vector_overlap']==pytest.approx(1)
    assert 'projector' in ra['selection_rule']

def test_10_strict_cluster_threshold():
    assert len(m.clusters(np.exp(1j*np.array([0.,1e-8]))))==2
    assert len(m.clusters(np.exp(1j*np.array([0.,.99e-8]))))==1

def test_11_chained_cluster_ambiguous():
    with pytest.raises(m.BranchFailure,match='chained'):m.clusters(np.exp(1j*np.array([0.,.6e-8,1.2e-8])))

def test_near_degenerate_projected_vector_residual_fails():
    with pytest.raises(m.BranchFailure,match='unresolved'):solve(unitary([0.,9e-9]),np.ones(2)/np.sqrt(2))

def test_12_missing_prior_checkpoint():
    with pytest.raises(m.BranchFailure,match='missing prior'):solve(unitary([.1,.2]),np.array([1,0]),.2,1)

def test_13_nonmonotone_time():
    with pytest.raises(m.BranchFailure,match='non-monotone'):solve(unitary([.1,.2]),np.array([1,0]),.1,1,previous(np.array([1,0])))

def test_21_eigenpair_residual_failure(monkeypatch):
    original=m.choose
    def wrong(*args,**kwargs):
        vector,row=original(*args,**kwargs);return np.array([0,1],dtype=complex),row
    monkeypatch.setattr(m,'choose',wrong)
    with pytest.raises(m.BranchFailure,match='eigenpair residual'):solve(unitary([.1,.2]),np.array([1,0]))

def test_22_unitarity_gate():
    with pytest.raises(m.BranchFailure,match='unitarity'):solve(np.diag([1.,1.00001]),np.array([1,0]))

@pytest.mark.parametrize('bad',[np.nan,np.inf,-np.inf])
def test_23_nonfinite_operator(bad):
    with pytest.raises(m.BranchFailure,match='NaN/Inf'):solve(np.array([[bad,0],[0,1]],dtype=complex),np.array([1,0]))

def test_24_duplicate_eigenbranch_assignment():
    with pytest.raises(m.BranchFailure,match='duplicate'):m.choose(np.array([1,1j]),np.ones((2,2))/np.sqrt(2),np.array([1,0]))

def test_25_selected_vector_normalization():
    row,vector=solve(unitary([.1,.1]),np.array([1,1j])/np.sqrt(2))
    assert np.vdot(vector,vector).real==pytest.approx(1)
    assert row['eigenpair_residual']<=1e-10
    with pytest.raises(m.BranchFailure,match='normalization'):solve(unitary([.1,.2]),np.array([2,0]))

def test_initial_anchor_does_not_accept_previous():
    with pytest.raises(m.BranchFailure,match='initial anchor'):solve(unitary([.1,.2]),np.array([1,0]),prior=previous(np.array([1,0])))

def test_unwrap_preserves_S0_principal_angle():
    row,_=solve(unitary([-.2,.2]),np.array([1,0]))
    assert row['signed_direct_shift']==pytest.approx(-2.) and row['unwrap_integer']==0

def test_production_dimension_rejected_before_schur(monkeypatch):
    spy=Mock();monkeypatch.setattr(m,'schur',spy)
    U=Mock(shape=(1568,1568))
    for ctx in [ContextV2(),ContextV2('synthetic')]:
        with pytest.raises(PermissionError):m.solve_point(U,None,None,None,SOURCE,0,ctx)
    spy.assert_not_called()

def test_PhaseA_cannot_call_truth_kernel_even_if_authorized(monkeypatch):
    context=ContextV2('FS-R1-Phase-A');context.guard=Mock()
    spy=Mock();monkeypatch.setattr(m,'schur',spy)
    with pytest.raises(PermissionError,match='Phase B only'):m.solve_point(Mock(shape=(1568,1568)),None,None,None,SOURCE,0,context)
    context.guard.assert_not_called();spy.assert_not_called()
