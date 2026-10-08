"""B0 requirements 1–50: saved real scalars and <=16 dimensional toy truth only."""
import ast
import copy
import json
from pathlib import Path
import pickle
import sys
from unittest.mock import Mock
import numpy as np
import pytest
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import b0_common as c
import v3_barrier as barrier
import v3_scoring as scoring
import truth_adapter as adapter
import phase_b_controller as controller
import truth_recovery as recovery
sys.path.insert(0,str(c.ROOT/c.R01))
import branch_math as bm

@pytest.fixture(scope='session')
def real_proof():return barrier.verify_phase_a()

class FakeEvidence:
    """In-memory committed/local/remote transport; never a truth source."""
    def __init__(self):
        ext=c.read(HERE/'phase_a_external_remote_verification.json')
        self.files={p:(c.ROOT/p).read_bytes() for p in ext['verified_file_sha256']}
        self.remote=copy.deepcopy(self.files);self.committed=copy.deepcopy(self.files)
        self.valid_lineage=True
    def blob(self,commit,path):return self.committed[path]
    def independent_blob(self,commit,path):return self.remote[path]
    def local(self,path):return self.files[path]
    def lineage(self,origin,handoff):
        if not self.valid_lineage:raise ValueError('handoff lineage mismatch')
        return ['A\t'+c.A+'/remote_verification.json']

@pytest.fixture
def freeze(tmp_path):
    ev=FakeEvidence();rp=tmp_path/'remote.json'
    rp.write_bytes((HERE/'phase_a_external_remote_verification.json').read_bytes())
    return ev,rp

def verify(fixture,**kwargs):
    ev,rp=fixture
    return barrier.verify_phase_a(receipt_path=rp,evidence=ev,**kwargs)

def test_01_real_committed_v3_freeze_accepts_without_oracle(real_proof):
    assert real_proof.data['prediction_sha256']==c.PREDICTION
    assert real_proof.data['oracle_decode']==0 and len(real_proof.data['private_recovery_checks'])==7

def test_01_correct_fixture_transport(freeze):assert verify(freeze).data['production_results_sha256']==c.RESULT

@pytest.mark.parametrize('field,value',[
    ('science_origin','a'*40),('handoff','b'*40),('prediction_sha','c'*64),('results_sha','d'*64)])
def test_02_04_05_commit_and_hash_identity(freeze,field,value):
    with pytest.raises(ValueError):verify(freeze,**{field:value})

def test_03_handoff_lineage_mismatch(freeze):
    freeze[0].valid_lineage=False
    with pytest.raises(ValueError,match='lineage'):verify(freeze)

@pytest.mark.parametrize('name',[
    'production_results.json','prediction_manifest.json','cold_replay.json','private_recovery_receipt.json',
    'numerical_gate_audit.json','source_identity.json','predicted_budgets.json'])
def test_05_to_10_corrupt_member_bytes_fail_closed(freeze,name):
    path=c.A+'/'+name;freeze[0].files[path]+=b'corrupt'
    with pytest.raises(ValueError,match='blob mismatch'):verify(freeze)

@pytest.mark.parametrize('path',[
    c.A0+'/fs_r1_numerical_contract_v1.json',c.A0+'/execution_code_identity.json',
    c.A0+'/phase_a_wrapper.py',c.R0+'/new_source_identity.json',c.R0+'/new_source_registry.json'])
def test_07_08_09_member_identity(freeze,path):
    freeze[0].remote[path]+=b'corrupt'
    with pytest.raises(ValueError,match='blob mismatch'):verify(freeze)

def test_06_byte_length_record_rejected(freeze):
    ev,_=freeze;path=c.A+'/prediction_manifest.json';m=json.loads(ev.files[path])
    m['files'][0]['bytes']+=1
    for files in (ev.files,ev.remote,ev.committed):files[path]=c.canonical(m)
    with pytest.raises(ValueError,match='SHA mismatch'):verify(freeze)

@pytest.mark.parametrize('field,value',[
    ('status','FAIL'),('remote_fetched_independently',False),('remote_verified_commit','f'*40),
    ('manifest_sha256','0'*64),('origin_result_commit','0'*40)])
def test_11_invalid_remote_receipt(freeze,field,value):
    _,rp=freeze;receipt=json.loads(rp.read_text());receipt[field]=value;rp.write_bytes(c.canonical(receipt))
    with pytest.raises(ValueError,match='receipt invalid'):verify(freeze)

def test_11_remote_receipt_absent(freeze):
    freeze[1].unlink()
    with pytest.raises(ValueError,match='absent'):verify(freeze)

def test_11_remote_target_sha_missing(freeze):
    _,rp=freeze;receipt=json.loads(rp.read_text());del receipt['verified_file_sha256'][c.A+'/production_results.json']
    rp.write_bytes(c.canonical(receipt))
    with pytest.raises(ValueError,match='target blob'):verify(freeze)

@pytest.mark.parametrize('kind',['source','protocol','code'])
def test_09_11_remote_authorities(freeze,kind):
    _,rp=freeze;receipt=json.loads(rp.read_text())
    key={'source':'source_hashes','protocol':'protocol_sha256','code':'execution_code_sha256'}[kind]
    receipt[key]={} if kind=='source' else '0'*64;rp.write_bytes(c.canonical(receipt))
    with pytest.raises(ValueError):verify(freeze)

@pytest.mark.parametrize('kind',['cold','gate','ritz_gate','proxy_gate','truth','budget'])
def test_12_13_14_semantic_failure(real_proof,kind):
    data=real_proof.data;payload=data['payload']
    components={Path(r['path']).name:c.read(c.ROOT/r['path']) for r in
        c.read(c.ROOT/c.A/'prediction_manifest.json')['files'] if r['path'].endswith('.json')}
    if kind=='cold':components['cold_replay.json']['status']='FAIL'
    elif kind=='gate':components['numerical_gate_audit.json']['status']='FAIL'
    elif kind=='ritz_gate':components['numerical_gate_audit.json']['Ritz_gates'][0]['status']='FAIL'
    elif kind=='proxy_gate':components['numerical_gate_audit.json']['proxy_gates'][0]['Cauchy_pass']=False
    elif kind=='truth':payload['initial_operational'][0]['direct_truth']=1.
    else:payload['initial_operational'][0]['budgets']['M00p']['nominal_budget']=None
    with pytest.raises((ValueError,TypeError)):
        barrier.validate_saved_components(payload,components,data['protocol'])

@pytest.mark.parametrize('key',['ground_overlap','signed_direct_shift','exact_ground','branch_id','vector','unitary'])
def test_14_truth_information_rejected(key):
    with pytest.raises(ValueError,match='truth-containing'):barrier.scalar_prediction({'nested':{key:0}})

def test_10_missing_private_recovery_is_no_go(freeze,monkeypatch):
    receipt=c.read(c.ROOT/c.A/'private_recovery_receipt.json');missing=Path(receipt['snapshots'][0]['private_path'])
    original=Path.is_file
    monkeypatch.setattr(Path,'is_file',lambda p:False if p==missing else original(p))
    with pytest.raises(ValueError,match='snapshot absent'):verify(freeze)

def test_10_private_recovery_sha_mismatch(freeze,monkeypatch):
    receipt=c.read(c.ROOT/c.A/'private_recovery_receipt.json');target=Path(receipt['snapshots'][0]['private_path'])
    original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda p:original(p)+b'corrupt' if p==target else original(p))
    with pytest.raises(ValueError,match='recovery hash'):verify(freeze)

def test_10_public_return_recovery_evidence(freeze):
    path=c.A+'/private_recovery_receipt.json';freeze[0].remote[path]=b'{}\n'
    with pytest.raises(ValueError):verify(freeze)

def synthetic_binding(proof):
    return dict(authorization_id='B0-synthetic-test-only',authorization_sha256='0'*64,
        protocol_sha256=c.PROTOCOL,execution_code_sha256='0'*64,source_hashes=proof.data['source_hashes'],
        prediction_sha256=c.PREDICTION,phase='synthetic')

def toy_loader(spec,proof,context):
    context.guard(2)
    sys.path.insert(0,str(c.ROOT/c.R0));import backend
    ns=backend.native();Batch,Spectrum=ns['ComponentBatch'],ns['ComponentSpectrum']
    spectrum=Spectrum(2,(Batch(np.array([[0,1]],dtype=np.int64),np.array([[-1.,1.]]),
        np.eye(2,dtype=complex)[None]),),2,1,2,4)
    context.add('truth_only_source_load')
    return dict(hamiltonian=csr_matrix(np.diag([-1.,1.])),component_spectra=[spectrum],
        current_m3_sequence=proof.data['protocol']['current_m3_sequence'],
        exact_ground=np.array([1,0],dtype=complex),exact_energy=-1.,
        source_identity_sha256=spec['source_identity_sha256'],synthetic_fixture=True)

def toy_execute(tmp_path,proof,**kwargs):
    context=controller.TruthContext(proof,phase='synthetic')
    result=controller.execute_verified(proof,context,tmp_path/'leases','toy-run',synthetic_binding(proof),
        tmp_path/'public.json',loader=toy_loader,**kwargs)
    return result,context

@pytest.fixture
def toy_run(tmp_path,real_proof):return toy_execute(tmp_path,real_proof)

def test_15_to_17_initial_saved_budget_authority(toy_run,real_proof,monkeypatch):
    result,context=toy_run;before=real_proof.raw
    sys.path.insert(0,str(c.ROOT/c.A0));import numerical_contract
    monkeypatch.setattr(numerical_contract,'budget_interval',Mock(side_effect=AssertionError('budget recalculation in scoring')))
    output=scoring.score_frozen(real_proof,result['payload']['rows'])
    for frozen,scored in zip(real_proof.data['payload']['initial_operational'],output['conditions']):
        for arm in c.ARMS:
            assert scored['arms'][arm]['budget']==frozen['budgets'][arm]['nominal_budget']
            assert scored['arms'][arm]['frozen_budget_interval']==[frozen['budgets'][arm]['B_min'],frozen['budgets'][arm]['B_max']]
    assert before==real_proof.raw and not output['intermediate_truth_used_for_resources']

def test_16_cold_cannot_overwrite_initial(real_proof):
    data=real_proof.data;data['payload']['cold_validation'][0]['budgets']['M00p']['nominal_budget']=1.
    assert real_proof.data['payload']['initial_operational'][0]['budgets']['M00p']['nominal_budget']==299615772.6844654
    assert real_proof.data['payload']['cold_validation'][0]['budgets']['M00p']['nominal_budget']!=1.

def test_18_missing_arm_rejected(real_proof):
    frozen=real_proof.data['payload']['initial_operational'][0];del frozen['budgets']['M11p']
    with pytest.raises(ValueError,match='four'):scoring.condition_outcomes(frozen,0.,real_proof.data['protocol']['systems'][0],real_proof.data['protocol']['constants'])

def test_19_truth_free_cannot_score(real_proof):
    with pytest.raises(PermissionError):scoring.score_frozen(real_proof,None)

def test_20_valid_synthetic_truth_slack(toy_run,real_proof):
    out=scoring.score_frozen(real_proof,toy_run[0]['payload']['rows']);p=real_proof.data['protocol']
    for row,spec in zip(out['conditions'],p['systems']):
        for arm,r in row['arms'].items():
            assert r['slack']==p['constants']['epsilon_E']-abs(row['signed_direct_truth'])-p['constants']['beta']*spec['K']/(spec['t0']*r['budget'])

@pytest.mark.parametrize('direct,status',[(.5,'safe'),(np.nextafter(.5,0.),'safe'),(np.nextafter(.5,1.),'unsafe')])
def test_21_safety_threshold_without_allowance(direct,status):
    b=dict(nominal_budget=2.,B_min=2.,B_max=2.,finite_budget_reported=True,uncertainty_bound=0.)
    out=scoring.safety_from_saved_budget(float(direct),b,dict(t0=1.,K=1),dict(epsilon_E=1.,beta=1.))
    assert out['status']==status

def budget_fixture(values):
    return dict(estimates=dict.fromkeys(c.ARMS,0.),budgets={a:dict(nominal_budget=B,B_min=B,B_max=B,
        finite_budget_reported=True,uncertainty_bound=1e-11) for a,B in zip(c.ARMS,values)})

@pytest.mark.parametrize('budgets,direct,flags',[
    ([10,9,9,8],0.,(True,True,True,False)),
    ([10,9,9.8,9.8],0.,(True,True,False,False)),
    ([3,3,2,4],.6,(False,False,False,True)),
    ([10,9,9,8],1.,(False,False,False,False))])
def test_22_to_25_preregistered_outcomes(budgets,direct,flags):
    out=scoring.condition_outcomes(budget_fixture(budgets),direct,dict(t0=1.,K=1),dict(epsilon_E=1.,beta=1.,eta=.02))
    assert tuple(out[k] for k in ['primary_gain','local_gain','state_increment','safety_repair'])==flags

def test_26_unsafe_not_offset_by_average(real_proof,toy_run):
    rows=copy.deepcopy(toy_run[0]['payload']['rows'])
    rows[5]['signed_direct_shift']=1.;rows[5]['direct_error']=1.
    out=scoring.score_frozen(real_proof,rows)
    assert out['study']['primary_gain_count']==1
    assert out['study']['interpretation']=='condition-dependent'
    assert 'resource extension STOP' in out['study']['stop_rules']
    assert not out['conditions'][0]['primary_gain'] and out['conditions'][1]['primary_gain']

def test_27_intermediate_truth_not_scored(real_proof,toy_run):
    rows=copy.deepcopy(toy_run[0]['payload']['rows']);before=scoring.score_frozen(real_proof,rows)
    for r in rows:
        if r['time_role']=='branch_certification':r['signed_direct_shift']=999.;r['direct_error']=999.
    assert scoring.score_frozen(real_proof,rows)==before

def test_28_failed_truth_has_no_scientific_result(real_proof,toy_run):
    rows=copy.deepcopy(toy_run[0]['payload']['rows']);rows[5]['branch_status']='unresolved'
    with pytest.raises(bm.BranchFailure):scoring.score_frozen(real_proof,rows)

def test_29_30_31_32_complete_toy_execution(toy_run):
    out,context=toy_run;rows=out['payload']['rows']
    assert len(rows)==12 and sum(r['time_role']=='primary_scoring' for r in rows)==2
    assert context.counts['truth_coordinate_attempt']==context.counts['truth_coordinate_completed']==12
    assert context.counts['Schur_decomposition']==context.counts['PF_unitary_construction']==12
    assert context.counts['truth_only_source_load']==2
    for r in rows:
        assert r['synthetic_truth_fixture']
        assert r['selection_rule'].startswith('maximum_exact_ground_overlap' if r['index']==0 else 'maximum_previous_selected_vector_overlap')

def test_33_cluster_projector_continuation(real_proof):
    context=controller.TruthContext(real_proof,phase='synthetic');phi=np.array([1,1],dtype=complex)/np.sqrt(2)
    vector,row=bm.choose(np.array([1,1],dtype=complex),np.eye(2,dtype=complex),np.array([1,0],dtype=complex),phi,context)
    assert row['phase_cluster_size']==2 and 'degenerate_projector_continuity' in row['selection_rule']
    assert abs(np.vdot(vector,phi))**2>.999999

@pytest.mark.parametrize('kind',['overlap','residual','unitarity'])
def test_34_35_36_failure_stops_remaining_without_retry(tmp_path,real_proof,kind):
    calls=[];context=controller.TruthContext(real_proof,phase='synthetic')
    def builder(source,t,proof,ctx):
        calls.append(t)
        if kind=='unitarity':return np.diag([1,1.01]).astype(complex)
        if kind=='residual':return np.diag(np.exp(1j*np.array([0,5e-9])))
        if len(calls)==1:return np.eye(2,dtype=complex)
        R=np.array([[1,-1],[1,1]])/np.sqrt(2)
        return R@np.diag(np.exp(1j*np.array([0,.1])))@R.T
    args=(real_proof,context,tmp_path/'leases','toy-run',synthetic_binding(real_proof),tmp_path/'public.json')
    with pytest.raises(bm.BranchFailure):controller.execute_verified(*args,loader=toy_loader,builder=builder)
    assert len(calls)==(2 if kind=='overlap' else 1)
    n=len(calls)
    with pytest.raises(FileExistsError):controller.execute_verified(*args,loader=toy_loader,builder=builder)
    assert len(calls)==n and not (tmp_path/'public.json').exists()

def test_37_ambiguous_cluster_stop(real_proof):
    ctx=controller.TruthContext(real_proof,phase='synthetic')
    with pytest.raises(bm.BranchFailure,match='ambiguous'):
        bm.choose(np.exp(1j*np.array([0,.75e-8,1.5e-8])),np.eye(3,dtype=complex),np.array([1,0,0],dtype=complex),context=ctx)

@pytest.mark.parametrize('kind',['namespace','historical','extra','nearest','adaptive','role','order','proof','code','scope'])
def test_38_to_42_ladder_substitution_rejected(real_proof,toy_run,kind):
    rows=copy.deepcopy(toy_run[0]['payload']['rows'])
    if kind=='namespace':rows[0]['selected_branch_id']=bm.namespace('0'*64,0)
    elif kind=='historical':rows[0]['selected_branch_id']='historical:6'
    elif kind=='extra':rows.append(copy.deepcopy(rows[0]))
    elif kind=='nearest':rows[-1]['time']=float(np.nextafter(rows[-1]['time'],1.))
    elif kind=='adaptive':rows[1]['time']=(rows[0]['time']+rows[1]['time'])/2
    elif kind=='role':rows[0]['time_role']='primary_scoring'
    elif kind=='order':rows[0],rows[6]=rows[6],rows[0]
    elif kind=='proof':rows[0]['phase_a_proof_sha256']='0'*64
    elif kind=='code':rows[0]['Phase_B_execution_code_sha256']='1'*64
    else:rows[0]['synthetic_truth_fixture']=False
    with pytest.raises((ValueError,bm.BranchFailure)):scoring.validate_ladders(rows,real_proof)

def test_43_no_authorization_no_barrier_or_oracle(monkeypatch,tmp_path):
    spy=Mock(side_effect=AssertionError('freeze/source reached'));monkeypatch.setattr(controller,'verify_phase_a',spy)
    with pytest.raises(PermissionError):controller.execute_phase_b(None,'bad',tmp_path/'bad.json')
    spy.assert_not_called()

def test_44_fake_verified_flag_rejected(real_proof):
    with pytest.raises(PermissionError):controller.TruthContext({'verified':True},phase='synthetic').guard(2)
    with pytest.raises(PermissionError):c.require_proof(c.VerifiedFreeze(real_proof.raw,real_proof.digest,object()))

def valid_auth_fixture(monkeypatch):
    contract=c.read(HERE/'phase_b_bridge_contract.json');code=c.verify_execution()
    auth=dict(explicit_science_authorization=True,phase='FS-R1-Phase-B',request_stage='FS-R1-Phase-B-production',
        approval_reference='SYNTHETIC_AUTHORIZATION_FIXTURE_NOT_USER_APPROVAL',authorization_id='synthetic-binding-test-only',
        protocol_sha256=c.PROTOCOL,prediction_sha256=c.PREDICTION,science_origin_commit=c.SCIENCE,
        handoff_commit=c.HANDOFF,handoff_proof_sha256=contract['handoff_proof_sha256'],
        phase_b_execution_code_sha256=code,branch_ladder_sha256=c.LADDER,source_hashes=contract['source_hashes'],truth_coordinate_budget=12)
    original=controller.read
    monkeypatch.setattr(controller,'read',lambda path:dict(status='GO_FOR_FS_R1_PHASE_B_PRODUCTION',tests_pass=True)
        if Path(path).name=='GO_NO_GO_FOR_PHASE_B_PRODUCTION.json' else original(path))
    return auth

def test_45_complete_authorization_binding_only(monkeypatch):
    a=valid_auth_fixture(monkeypatch)
    assert controller.validate_authorization(a)['truth_coordinate_budget']==12

@pytest.mark.parametrize('field',['authorization_id','protocol_sha256','prediction_sha256','science_origin_commit',
    'handoff_commit','handoff_proof_sha256','phase_b_execution_code_sha256','branch_ladder_sha256','source_hashes',
    'truth_coordinate_budget','approval_reference','request_stage'])
def test_45_every_binding_is_required(monkeypatch,field):
    a=valid_auth_fixture(monkeypatch);a.pop(field)
    with pytest.raises(PermissionError):controller.validate_authorization(a)

def test_46_consumed_phase_A_authorization_rejected(monkeypatch):
    a=valid_auth_fixture(monkeypatch);a['authorization_id']=c.read(HERE/'phase_b_bridge_contract.json')['consumed_phase_a_authorization_id']
    with pytest.raises(PermissionError,match='Phase A'):controller.validate_authorization(a)

def test_47_duplicate_authorization_even_changed_run_id(tmp_path,real_proof):
    toy_execute(tmp_path,real_proof)
    ctx=controller.TruthContext(real_proof,phase='synthetic');spy=Mock()
    with pytest.raises(FileExistsError):controller.execute_verified(real_proof,ctx,tmp_path/'leases','different-run-id',
        synthetic_binding(real_proof),tmp_path/'new.json',loader=spy)
    spy.assert_not_called()

def test_48_recovery_integrity_mismatch(toy_run):
    path=Path(toy_run[0]['private_recovery'])
    path.chmod(0o600);path.write_bytes(path.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='SHA mismatch'):recovery.load_snapshot(path)

def test_48_checkpoint_binding_mismatch(toy_run,real_proof):
    result,ctx=toy_run;row=result['payload']['rows'][0];metadata=row['selected_vector_checkpoint']
    bp=Path(metadata['private_path']+'.binding.json');bp.chmod(0o600)
    value=json.loads(bp.read_text());value['phase_a_proof_sha256']='0'*64;bp.write_bytes(c.canonical(value))
    with pytest.raises(ValueError,match='binding mismatch'):
        adapter.previous(metadata,row['source_identity_sha256'],0,row['time'],real_proof,ctx,Mock())

def test_49_public_failure_scalar_only_recovery(tmp_path,real_proof):
    ctx=controller.TruthContext(real_proof,phase='synthetic');validator=Mock(side_effect=ValueError('serialization failure'))
    with pytest.raises(ValueError,match='serialization failure'):
        controller.execute_verified(real_proof,ctx,tmp_path/'leases','toy',synthetic_binding(real_proof),
            tmp_path/'public.json',loader=toy_loader,public_validator=validator)
    before=ctx.counts.copy();directory=next((tmp_path/'leases').iterdir());saved=directory/'truth_complete.recovery.json'
    assert saved.is_file() and not (tmp_path/'public.json').exists()
    receipt=recovery.publish_saved(saved,tmp_path/'public.json',lambda value:scoring.validate_ladders(value['rows'],real_proof))
    assert receipt['science_rerun'] is False and ctx.counts==before
    with pytest.raises(FileExistsError):controller.execute_verified(real_proof,ctx,tmp_path/'leases','changed-id',
        synthetic_binding(real_proof),tmp_path/'public2.json',loader=toy_loader)
    assert ctx.counts==before

def test_50_B0_cannot_dispatch_or_decode(real_proof,monkeypatch):
    decoder=Mock(side_effect=AssertionError('oracle decode'));monkeypatch.setattr(pickle,'loads',decoder)
    ctx=controller.TruthContext(real_proof)
    with pytest.raises(PermissionError):adapter.load_source(real_proof.data['protocol']['systems'][0],real_proof,ctx)
    ctx=controller.TruthContext(real_proof,phase='synthetic')
    with pytest.raises(PermissionError):adapter.load_source(real_proof.data['protocol']['systems'][0],real_proof,ctx)
    decoder.assert_not_called()

def test_real_preflight_stops_before_truth_only_import(monkeypatch):
    spy=Mock(side_effect=AssertionError('truth source boundary'));monkeypatch.setattr(adapter,'load_source',spy)
    result=controller.preflight_phase_b()
    assert result['oracle_decode']==0 and result['production_lease_created'] is False and result['Phase_B_authorized'] is False
    spy.assert_not_called()

def test_truth_kernel_arithmetic_AST_identity():
    raw=(c.ROOT/c.R01/'truth_executor.py').read_bytes();tree=adapter.kernel_ast(raw)
    expected=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in adapter.KERNEL_NAMES]
    assert ast.dump(tree,include_attributes=False)==ast.dump(ast.Module(body=expected,type_ignores=[]),include_attributes=False)

def test_ladder_binary64_unchanged(real_proof):
    ladder=real_proof.data['branch_ladder']
    assert c.sha((c.ROOT/c.R01/'branch_ladder.json').read_bytes())==c.LADDER
    for system in ladder['systems']:
        assert [float(t).hex() for t in system['times']]==system['times_hex']
        assert system['times'][-1]==next(s['t0'] for s in real_proof.data['protocol']['systems'] if s['condition']==system['condition'])

def test_cost_classes_and_unknown_internal_work(toy_run):
    cost=toy_run[0]['payload']['truth_validation_cost']
    assert cost['cost_class']=='truth_validation_cost' and cost['QPE_addition'] is False
    assert cost['internal_work']['Schur_internal'] is None and cost['GPU_memory_bytes'] is None

def test_scalar_recovery_rejects_oracle_and_arrays():
    for value in [{'exact_ground':[1,0]},{'exact_energy':1.},{'vector':[1,0]},{'x':np.eye(2)}]:
        with pytest.raises((ValueError,TypeError)):recovery.scalar_boundary(value)
