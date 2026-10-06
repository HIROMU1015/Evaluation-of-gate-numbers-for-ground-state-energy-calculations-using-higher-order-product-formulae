"""Phase B regressions: public Phase A scalars plus synthetic truth only."""
from pathlib import Path
import copy,csv,io,json,sys,shutil
from types import SimpleNamespace
import pytest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P06=ROOT/'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
sys.path.insert(0,str(P06));sys.path.insert(0,str(HERE))
import phase_b_scoring as scoring
from phase_b_scoring import *
from phase06_contract import load_contract
from phase06_phase_b import score_payload,select_saved_truth

@pytest.fixture(scope='module')
def phase_a():return json.loads((ROOT/A_DIR/'phase_a.json').read_bytes())

def encode(rows):
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows);return out.getvalue().encode()

def mock_truth_rows():
    join=json.loads((ROOT/PH05/'saved_truth_join_contract.json').read_bytes())
    branch=[{**key,'direct_shift_hartree':'.01'} for key in join['keys']]
    obs=[{'experiment_id':'B','case_id':'H4','formula_id':'current_m3','state_id':'exact',
        'sign':str(s),'absolute_time':str(t),'time_hartree_inverse':str(s*t),
        'proxy_imag_hartree':'.01','quality_class':'resolved'} for t in TRAIN+EVAL for s in (1,-1)]
    return branch,obs,join

class MockGit:
    def __init__(self,blobs):self.blobs=blobs
    def allowed_remote(self):pass
    def remote_tip(self,branch):return A_COMMIT
    def blob(self,commit,path):return self.blobs[path]

@pytest.fixture
def frozen_copy(tmp_path,phase_a,monkeypatch):
    paths=[str(p.relative_to(ROOT)) for p in (ROOT/A_DIR).iterdir() if p.is_file()]
    paths+=list(phase_a['source']['code_files'])+[PH05+'/response_pilot_protocol.json',PH05+'/source_identity_phase_a.json']
    blobs={}
    for path in paths:
        raw=(ROOT/path).read_bytes();dst=tmp_path/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);blobs[path]=raw
    import phase06_inputs
    monkeypatch.setattr(phase06_inputs,'load_phase_a_inputs',lambda root,contract:SimpleNamespace(identity_audit=phase_a['source']['input_array_identities']))
    return tmp_path,MockGit(blobs),json.loads((P06/'phase_a_schema.json').read_bytes())

def test_correct_full_phase_a_SHA_and_both_prediction_blobs_required(frozen_copy):
    root,git,schema=frozen_copy;p,a=verify_all_phase_a(root,schema,git)
    assert a['status']=='passed' and a['predictions_sha256']==PRED_SHA and a['strict_phase_a_sha256']==PHASE_A_SHA

@pytest.mark.parametrize('mutation',['commit','strict_SHA','predictions_file','strict_file','prediction_hash_file','published_blob','freeze_marker'])
def test_altered_identity_stops_before_truth_reader(frozen_copy,mutation):
    root,git,schema=frozen_copy;receipt=frozen_receipt(root);called=[]
    if mutation=='commit':receipt['commit']='0'*40
    if mutation=='strict_SHA':receipt['prediction_sha256']='0'*64
    if mutation=='predictions_file':(root/A_DIR/'predictions.json').write_bytes(b'{}')
    if mutation=='strict_file':(root/A_DIR/'phase_a.json').write_bytes((root/A_DIR/'phase_a.json').read_bytes()+b' ')
    if mutation=='prediction_hash_file':(root/A_DIR/'prediction.sha256').write_text('0'*64+'\n')
    if mutation=='published_blob':git.blobs[A_DIR+'/predictions.json']=b'{}'
    if mutation=='freeze_marker':(root/A_DIR/'PHASE_A_FROZEN').write_bytes(b'{}')
    with pytest.raises(GateError):guarded_intake(root,schema,lambda:called.append(1),git,receipt)
    assert called==[]

@pytest.mark.parametrize('kind',['missing_direct','duplicate_direct','missing_exact','duplicate_exact',
    'wrong_direct_sign','wrong_exact_sign','wrong_direct_time','wrong_exact_time','unreliable','branch_id'])
def test_missing_duplicate_sign_time_branch_fail_closed(kind):
    branch,obs,join=mock_truth_rows()
    if kind=='missing_direct':branch.pop()
    if kind=='duplicate_direct':branch.append(branch[0])
    if kind=='missing_exact':obs.pop()
    if kind=='duplicate_exact':obs.append(obs[0])
    if kind=='wrong_direct_sign':branch[0]['sign']='1'
    if kind=='wrong_exact_sign':obs[0]['sign']='-1'
    if kind=='wrong_direct_time':branch[0]['time_hartree_inverse']='-0.1250001'
    if kind=='wrong_exact_time':obs[0]['time_hartree_inverse']='0.1000001'
    if kind=='unreliable':branch[0]['branch_reliable']='False'
    if kind=='branch_id':branch[0]['selected_eigenbranch_id']='99'
    with pytest.raises(GateError):select_saved_truth(encode(branch),encode(obs),join)

def payload_fixture(original,b=0.,r=9.,k=8.,point_b=3.,point_r=1.,converged=True):
    p=copy.deepcopy(original)
    for arm,rows in p['predictions'].items():
        value={'A0':b,'A1':r,'A2':k}.get(arm,b)
        point={'A0':point_b,'A1':point_r,'A2':0.5}.get(arm,point_b)
        for row in rows:row['prediction']=value;row['proxy']=point
    p['residual_convergence']['converged']=converged
    direct={s*t:10. for t in EVAL for s in (1,-1)}
    exact={s*t:{'proxy':0.,'quality':'resolved'} for t in TRAIN+EVAL for s in (1,-1)}
    return p,direct,exact

def test_S_abs_S_under_Emax_exact_arithmetic(phase_a):
    p,d,e=payload_fixture(phase_a,b=8.,r=9.,k=8.5)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert out['arms']['A0']['S_abs']==24 and out['arms']['A0']['S_under']==24
    assert out['arms']['A1']['S_abs']==12 and out['arms']['A1']['S_under']==12
    assert out['arms']['A1']['E_max']==1 and out['arms']['A1']['improved_count']==12
    assert out['arms']['A1']['continuous_ratios']['S_abs']==.5

def test_underestimation_direction_crossings_and_zero_sign(phase_a):
    p,d,e=payload_fixture(phase_a,b=8.,r=-12.,k=0.)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert out['arms']['A1']['S_abs']==264 and out['arms']['A1']['S_under']==0
    assert all(row['underestimation']==-2 for row in out['arms']['A1']['rows'])
    assert out['arms']['A1']['sign_crossing_count']==12 and out['arms']['A2']['sign_crossing_count']==12

def test_zero_denominator_ratios_are_null(phase_a):
    p,d,e=payload_fixture(phase_a,b=10.,r=9.,k=9.5)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert all(out['arms']['A1']['continuous_ratios'][key] is None for key in ('S_abs','S_under','E_max'))

@pytest.mark.parametrize('r,k,unique,dominated',[
    ((1.,1.,9,44),(2.,2.,9,22),True,False),
    ((2.,2.,9,44),(1.,1.,9,22),False,True),
    ((1.,1.,9,22),(1.,1.,9,22),False,False)])
def test_frozen_Pareto_axes_and_equal_tuple(r,k,unique,dominated):
    trace=pareto_trace(r,k)
    assert trace['response_unique_tradeoff']==unique
    assert trace['response_Pareto_dominated_by_Ritz']==dominated

@pytest.mark.parametrize('kind,kwargs,expected',[
    ('A',{'b':0.,'r':9.,'k':8.},'response_specific_support'),
    ('B',{'b':0.,'r':8.,'k':9.},'generic_state_improvement'),
    ('C',{'b':8.,'r':7.,'k':8.,'point_b':3.,'point_r':0.},'point_only'),
    ('D',{'b':8.,'r':7.,'k':7.,'point_b':1.,'point_r':2.},'no_benefit'),
    ('mixed',{'b':8.,'r':9.,'k':7.,'converged':False},'inconclusive_mixed_predicates')])
def test_outcome_and_trace_all_frozen_predicates(phase_a,kind,kwargs,expected):
    p,d,e=payload_fixture(phase_a,**kwargs)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert out['outcome']==expected and outcome_trace(p,out)['chosen']==kind

def test_numerically_invalid_precedence_is_frozen_D(phase_a):
    p,d,e=payload_fixture(phase_a)
    p['fits']['A1']['raw_positive_even_two_term']['status']='not_identifiable'
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert out['outcome']=='no_benefit_numerically_unstable'
    assert outcome_trace(p,out)['chosen']=='numerical_invalid_D'

def test_A3_reference_cannot_modify_predictions_or_refit_operational_arms(phase_a,monkeypatch):
    import phase06_phase_b
    p,d,e=payload_fixture(phase_a);before=canonical(p);calls=[]
    original=phase06_phase_b.fit_two_term_model
    def observed(times,pos,neg,quality):
        assert list(pos)==[e[t]['proxy'] for t in TRAIN]
        calls.append('A3');return original(times,pos,neg,quality)
    monkeypatch.setattr(phase06_phase_b,'fit_two_term_model',observed)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert calls==['A3'] and len(out['oracle_fits'])==3 and canonical(p)==before
    assert out['arms']['A3']['point_S_abs']==0

def test_new_science_counters_are_zero():
    counts=zero_new_science_actions()
    assert all(v==0 for v in counts.values()) and counts['new_fit_A0_A1_A2']==0

def test_runtime_guard_blocks_new_eigensolve_and_response_solve(phase_a):
    import numpy as np
    import phase06_kernels
    from phase06_backend import EchoBackend
    _,_,exact=payload_fixture(phase_a)
    with no_new_science(exact) as ledger:
        with pytest.raises(GateError,match='prohibited'):np.linalg.eigh(np.eye(2))
        with pytest.raises(GateError,match='prohibited'):phase06_kernels.solve_ritz_state(None,None,None)
        with pytest.raises(GateError,match='prohibited'):EchoBackend.forward(None,None,None)
    assert ledger['blocked_science_attempts']==3 and all(v==0 for v in ledger['new_science_actions'].values())

def test_runtime_guard_counts_exactly_three_A3_fits_and_no_new_science(phase_a):
    p,d,e=payload_fixture(phase_a);before=canonical(p)
    with no_new_science(e) as ledger:
        out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    assert ledger['A3_fit_rule_invocations']==1 and ledger['A3_reference_fits']==3
    assert ledger['blocked_science_attempts']==0 and canonical(p)==before
    assert all(v==0 for v in ledger['new_science_actions'].values())

def test_complete_twenty_two_coordinate_proxy_table_and_bridge(phase_a):
    p,d,e=payload_fixture(phase_a)
    # Populate synthetic point proxies consistently into scalar rows; no kernels.
    for row in p['rows']:
        for arm in row['proxies']:row['proxies'][arm]={'A0':3.,'A1':1.,'A2':.5}.get(arm,3.)
    out=score_payload(p,d,e,{'commit':A_COMMIT,'prediction_sha256':PHASE_A_SHA})
    rows,bridge=proxy_rows_and_bridge(p,e,out)
    assert len(rows)==220 and bridge['A1']['point_S_abs_22']==22
    assert bridge['A1']['point_S_abs_eval12']==12 and bridge['A1']['point_improved_eval_rows']==12
