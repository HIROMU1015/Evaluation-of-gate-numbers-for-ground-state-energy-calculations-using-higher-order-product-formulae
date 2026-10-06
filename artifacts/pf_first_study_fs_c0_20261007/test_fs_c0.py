"""Synthetic arithmetic, failure paths, metadata serialization, truth barrier."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import pytest
from jsonschema import Draft202012Validator, ValidationError

import scoring_skeleton as s
import serialization_boundary as ser
from synthetic_math import fit_functional, response_representations

HERE=Path(__file__).parent
PROTOCOL=json.loads((HERE/'fs_c1_protocol.json').read_text())
META=json.loads((HERE/'metadata_fixture.json').read_text())
SCHEMA=json.loads((HERE/'prediction_schema.json').read_text())

def fixture():
    p=copy.deepcopy(PROTOCOL)
    # This fixture tests scalar plumbing with real metadata, never the unresolved
    # production time/uncertainty contract. It cannot authorize production.
    for spec in p['systems']:
        spec['training_times']=spec['historical_training_times']
    payload=dict(schema_version='fs_c1_prediction_v1',payload_kind='synthetic_fixture',
      protocol_sha256=hashlib.sha256(ser.canonical(p)).hexdigest(),
      conditions=[dict(**m,baseline_reproduced=True,
        arms={arm:dict(estimate=-2e-5 if arm=='M00' else -1e-5,
          valid=True,classification_uncertainty_hartree=1e-14,quality_status='synthetic') for arm in s.ARMS})
        for m in copy.deepcopy(META['conditions'])],
      action_counts={k:0 for k in ['explicit_refinement_H_matvec','PF_forward','PF_adjoint','exact_H_echo_actions','small_Ritz','primary_fits']})
    truth=[dict(condition=spec['condition'],formula=spec['formula'],time=spec['t0'],time_sign=1,
        identity=spec['identity'],branch_id=spec['truth_branch_id'],quality='resolved',signed_direct=-1e-5)
        for spec in p['systems']]
    return p,payload,truth

@pytest.mark.parametrize('gamma',[1.,1.01,1.1])
@pytest.mark.parametrize('signed',[-1,1])
def test_slack_identity(gamma,signed):
    spec={'t0':.6,'K':19176,'B0':3e8}
    d=s.decision(signed*3e-5,signed*2e-5,spec,dict(epsilon_E=.00015936001019904,beta=1.2,gamma=gamma))
    assert d['slack']==pytest.approx(d['slack_identity'],abs=1e-19)

def test_zero_baseline_underestimation_does_not_block_safe_saving():
    p,x,t=fixture()
    # Conservatively overestimating M00 does not forbid improvement by M11.
    result=s.score_payload(x,t,p)
    assert result['primary_gain_count']==2
    assert all(r['arms']['M00']['u']<0 and r['flags']['local_gain'] for r in result['conditions'])

def test_unsafe_cannot_be_offset_by_other_system():
    p,x,t=fixture();t[1]['signed_direct']=-5e-5
    result=s.score_payload(x,t,p)
    assert result['conditions'][0]['flags']['primary_gain']
    assert not result['conditions'][1]['flags']['primary_gain']
    assert result['primary_gain_count']==1

def test_safety_repair_is_separate_from_budget_reduction():
    p,x,t=fixture()
    for r in x['conditions']:
        r['arms']['M01']['estimate']=0.
        r['arms']['M11']['estimate']=-5e-5
    for row in t:row['signed_direct']=-5e-5
    result=s.score_payload(x,t,p)
    assert all(r['flags']['safety_repair'] and not r['flags']['state_increment'] for r in result['conditions'])

@pytest.mark.parametrize('kind',['invalid','missing_uncertainty','infeasible','missing_baseline','unresolved'])
def test_invalid_cannot_claim_gain(kind):
    p,x,t=fixture()
    for r in x['conditions']:
        if kind=='invalid':r['arms']['M11']['valid']=False
        if kind=='missing_uncertainty':r['arms']['M11']['classification_uncertainty_hartree']=None
        if kind=='infeasible':r['arms']['M11']['estimate']=p['constants']['epsilon_E']
        if kind=='missing_baseline':r['baseline_reproduced']=False
        if kind=='unresolved':r['arms']['M11']['quality_status']='unresolved'
    assert s.score_payload(x,t,p)['primary_gain_count']==0

def test_exact_zero_slack_kept_with_indeterminate_label():
    p,x,t=fixture();p['constants']['gamma']=1.
    result=s.score_payload(x,t,p)
    for r in result['conditions']:
        assert abs(r['arms']['M11']['slack'])<1e-14
        assert r['arms']['M11']['numerically_indeterminate']
        assert not r['flags']['primary_gain']

@pytest.mark.parametrize('c',[.1,.2])
def test_infeasible_denominator_returns_null(c):
    assert s.budget(c,1.,2,.1,1.2,1.01) is None

@pytest.mark.parametrize('args',[(0,0,2,.1,1.2,1.01),(-1,1,2,.1,1.2,1.01),
    (0,1,0,.1,1.2,1.01),(0,1,True,.1,1.2,1.01),
    (0,1,2,0,1.2,1.01),(0,1,2,.1,1.2,.9),(float('nan'),1,2,.1,1.2,1.01)])
def test_bad_budget_input_stops(args):
    with pytest.raises(s.ContractError):s.budget(*args)

def test_domain_screen_no_truth_and_equality_is_not_excluded():
    d=s.domain_screen(2,1.,.1,1.2,30.,.2)
    assert d['cost_lower_bound']==pytest.approx(24.)
    assert d['maximum_saving']==pytest.approx(.2)
    d2=s.domain_screen(2,1.,.1,1.2,24.,.02)
    assert d2['exclude_target']
    # Literal < is the criterion; use an exactly representable boundary.
    assert not s.domain_screen(1,1.,1.,1.,2.,.5)['exclude_target']

def test_fixed_ols_linear_functional_and_perturbation():
    times=np.array([.05,.1,.15,.2,.25])
    ell,X,scale=fit_functional(times,.6)
    y=X@np.array([-.03,.002])+np.array([1.,-2.,3.,-1.,.5])*1e-8
    dy=np.array([1.,2.,-1.,3.,-2.])*1e-9
    fitted=lambda v:np.array([.6**4,.6**6])@(np.linalg.lstsq(X/scale,v,rcond=None)[0]/scale)
    assert ell@y==pytest.approx(fitted(y),abs=1e-16)
    assert ell@dy==pytest.approx(fitted(y+dy)-fitted(y),abs=1e-16)

def test_budget_gradient_from_fixed_ols():
    ell,_,_=fit_functional([.05,.1,.15,.2,.25],.6)
    y=np.array([1,2,3,4,5])*1e-7;f=ell@y;eps=.01;d=np.array([1,-2,3,-1,2])*1e-12
    analytic=np.sign(f)*(ell@d)/(eps-abs(f))
    actual=np.log((eps-abs(f))/(eps-abs(f+ell@d)))
    assert actual==pytest.approx(analytic,rel=1e-5,abs=1e-14)

def test_four_arm_interaction_signed_identity():
    d=s.signed_interaction(dict(M00=1.,M10=2.,M01=3.,M11=7.))
    assert d==dict(state_in_fit=1.,local_in_CISD=2.,state_in_local=4.,interaction=3.)

@pytest.mark.parametrize('seed',[1,7,19,21])
def test_fixed_response_vector_identity_for_complex_observable(seed):
    rng=np.random.default_rng(seed);n=5
    psi=rng.normal(size=n)+1j*rng.normal(size=n);psi/=np.linalg.norm(psi)
    full=np.column_stack([psi,np.eye(n,dtype=complex)])
    Q,_=np.linalg.qr(full);Z=Q[:,1:3]
    C=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n));H=C+C.conj().T
    W=[]
    for _ in range(2):
        C=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n));A=C+C.conj().T
        original,fixed,trace,rho,w=response_representations(H,psi,Z,A)
        assert original==pytest.approx(fixed,abs=1e-12)
        assert fixed==pytest.approx(trace,abs=1e-12)
        assert np.trace(rho).real==pytest.approx(1.)
        W.append(w)
    assert np.allclose(W[0],W[1],rtol=0,atol=0)

def test_commuting_response_counterexample_and_nonpositive_rho():
    psi=np.sqrt([.9,.1]).astype(complex);Z=np.array([[-np.sqrt(.1)],[np.sqrt(.9)]],dtype=complex)
    H=np.diag([0.,1.]);g,f,tr,rho,w=response_representations(H,psi,Z,H)
    assert g==pytest.approx(-.125)
    assert .1-g==pytest.approx(.225)
    assert np.linalg.eigvalsh(rho)[0]<0
    assert np.allclose(H@H,H@H)

@pytest.mark.parametrize('kind',['missing','duplicate','sign','time','identity','branch','quality','extra','nonfinite'])
def test_bad_truth_joins(kind):
    p,x,t=fixture()
    if kind=='missing':t.pop()
    if kind=='duplicate':t.append(copy.deepcopy(t[0]))
    if kind=='sign':t[0]['time_sign']=-1
    if kind=='time':t[0]['time']=np.nextafter(t[0]['time'],np.inf)
    if kind=='identity':t[0]['identity']={}
    if kind=='branch':t[0]['branch_id']=-1
    if kind=='quality':t[0]['quality']='unresolved'
    if kind=='extra':t.append({**t[0],'condition':'other'})
    if kind=='nonfinite':t[0]['signed_direct']=float('nan')
    with pytest.raises(s.ContractError):s.score_payload(x,t,p)

def test_metadata_schema_and_exact_private_public_roundtrip(tmp_path):
    p,x,t=fixture();x['conditions']=tuple(x['conditions'])
    x['conditions'][0]['t0']=np.float64(x['conditions'][0]['t0'])
    private=tmp_path/'private.json';public=tmp_path/'public.json'
    result=ser.checkpoint_then_publish(x,private,public,Draft202012Validator(SCHEMA).validate)
    assert private.read_bytes()==public.read_bytes()
    assert ser.recover(private)==json.loads(public.read_bytes())
    assert result['recovery_saved_before_schema'] and not result['formal_prediction_freeze']
    with pytest.raises(FileExistsError):ser.checkpoint_then_publish(x,private,public,lambda x:None)

def test_schema_failure_retains_recovery_before_public_write(tmp_path):
    p,x,t=fixture();x['conditions'][0]['arms']['M11']['estimate']='bad'
    private=tmp_path/'recovery.json';public=tmp_path/'public.json'
    with pytest.raises(ValidationError):ser.checkpoint_then_publish(x,private,public,Draft202012Validator(SCHEMA).validate)
    assert private.exists() and not public.exists()
    assert ser.recover(private)['conditions'][0]['arms']['M11']['estimate']=='bad'

def test_public_write_failure_never_triggers_science_retry(tmp_path,monkeypatch):
    p,x,t=fixture();private=tmp_path/'recovery.json';public=tmp_path/'public.json'
    original=ser.exclusive_write
    def broken(path,data):
        if Path(path)==public:raise OSError('simulated publication failure')
        original(path,data)
    monkeypatch.setattr(ser,'exclusive_write',broken)
    with pytest.raises(OSError):ser.checkpoint_then_publish(x,private,public,Draft202012Validator(SCHEMA).validate)
    assert ser.recover(private)==x

@pytest.mark.parametrize('value',[np.ones(3),np.eye(2),complex(1,2),float('inf'),{1:2},{'states':[]},{'direct_truth':1.}])
def test_arrays_complex_truth_nonfinite_cannot_cross_public_boundary(value):
    with pytest.raises((ValueError,TypeError)):ser.canonical(value)

def test_scalar_is_not_rounded():
    x=np.nextafter(.6,np.inf)
    assert json.loads(ser.canonical({'x':np.float64(x)}))['x'].hex()==float(x).hex()

def mock_freeze(tmp_path,monkeypatch):
    p,x,t=fixture();files={'protocol.json':ser.canonical(p),'prediction.json':ser.canonical(x),
      'schema.json':ser.canonical(SCHEMA),'scorer.py':Path(s.__file__).read_bytes(),
      'sources.json':ser.canonical({'system_identities':{x['condition']:x['identity'] for x in p['systems']}})}
    roles=dict(protocol='protocol.json',prediction='prediction.json',schema='schema.json',scorer='scorer.py',sources='sources.json')
    manifest={'files':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()},'roles':roles}
    files['manifest.json']=ser.canonical(manifest)
    for name,data in files.items():(tmp_path/name).write_bytes(data)
    def git_blob(root,commit,path):
        if commit!='a'*40:raise s.ContractError('bad commit')
        return files[path]
    monkeypatch.setattr(s,'_git_bytes',git_blob)
    return files,t,hashlib.sha256(files['manifest.json']).hexdigest()

@pytest.mark.parametrize('target',['manifest.json','prediction.json','protocol.json','schema.json','scorer.py','sources.json'])
def test_modified_frozen_blob_rejected_before_truth(tmp_path,monkeypatch,target):
    files,t,digest=mock_freeze(tmp_path,monkeypatch)
    (tmp_path/target).write_bytes(files[target]+b' ')
    calls=[]
    with pytest.raises(s.ContractError):s.score_frozen(tmp_path,'a'*40,'manifest.json',digest,lambda:calls.append('truth'),synthetic_only=True)
    assert calls==[]

def test_unchanged_frozen_blob_callback_runs_once(tmp_path,monkeypatch):
    files,t,digest=mock_freeze(tmp_path,monkeypatch);calls=[]
    def loader():calls.append('truth');return t
    r=s.score_frozen(tmp_path,'a'*40,'manifest.json',digest,loader,synthetic_only=True)
    assert calls==['truth'] and r['denominator']==2

def test_production_authorization_denies_truth_callback(tmp_path,monkeypatch):
    files,t,digest=mock_freeze(tmp_path,monkeypatch);calls=[]
    with pytest.raises(s.ContractError):s.score_frozen(tmp_path,'a'*40,'manifest.json',digest,lambda:calls.append('truth'))
    assert calls==[]

@pytest.mark.parametrize('path',['../private.json','/absolute','x/../../x'])
def test_invalid_git_paths_are_rejected(path,tmp_path):
    with pytest.raises(s.ContractError):s._git_bytes(tmp_path,'a'*40,path)

def test_immutable_authority_go_no_go_and_zero_production_counts():
    closure=json.loads((HERE/'source_and_backend_closure.json').read_text())
    go=json.loads((HERE/'GO_NO_GO_FOR_FS_C1.json').read_text())
    counts=json.loads((HERE/'action_counts.json').read_text())
    assert closure['truth_join_ready'] and not closure['source_closure']
    assert not go['science_authorized'] and not go['execution_ready']
    assert all(counts[k]==0 for k in counts if k.startswith('production_'))
    assert PROTOCOL['primary']=='M11' and PROTOCOL['constants']['eta_saving']==.02

@pytest.mark.parametrize('suffix',['.pkl','.pickle','.npz','.npy'])
def test_audit_refuses_array_archives_before_read(suffix):
    from build_fs_c0 import Audit
    with pytest.raises(RuntimeError,match='no production array'):
        Audit(HERE).read('nonexistent'+suffix)

def test_public_schema_forbids_hidden_matrix_fields(tmp_path):
    p,x,t=fixture();x['conditions'][0]['unknown_matrix_payload']=[[1,2],[3,4]]
    with pytest.raises(ValidationError):Draft202012Validator(SCHEMA).validate(x)

def test_missing_arm_stops():
    p,x,t=fixture();x['conditions'][0]['arms'].pop('M10')
    with pytest.raises(s.ContractError):s.score_payload(x,t,p)

def test_baseline_zero_budget_reference_is_invalid():
    p,x,t=fixture();p['systems'][0]['B0']=0.
    with pytest.raises(s.ContractError):s.score_payload(x,t,p)

def test_commit_verifier_demands_full_sha(tmp_path):
    with pytest.raises(s.ContractError):s._git_bytes(tmp_path,'abc123','file.json')

def test_each_pass_ledger_checkpoint_is_create_only_and_not_public_freeze(tmp_path):
    p,x,t=fixture()
    for index in range(2):
        path=tmp_path/f'pass{index}.json'
        checkpoint=dict(checkpoint_kind='pass_complete',pass_index=index,
            scalar_rows=x['conditions'],action_counts=x['action_counts'])
        data,digest=ser.save_private_checkpoint(checkpoint,path)
        assert ser.recover(path)==checkpoint
        assert hashlib.sha256(data).hexdigest()==digest
        with pytest.raises(FileExistsError):ser.save_private_checkpoint(checkpoint,path)
