"""V2 barrier, ladder budgets, actual toy PF/Schur/checkpoint/recovery pipeline."""
import copy
import io
import json
from pathlib import Path
import sys
from unittest.mock import Mock
import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import r01_common as a
import r01_barrier as barrier
import truth_executor as executor
import scoring_bridge as bridge
import branch_math as math
from phase_a_v2 import ContextV2

def prediction():
    p=a.protocol()
    rows=[]
    for sp in p['systems']:
        estimates=dict(M00p=.0001,M10p=.00009,M01p=.00008,M11p=.00005)
        rows.append(dict(condition=sp['condition'],source_identity_sha256=sp['source_identity_sha256'],time=sp['t0'],
            estimates=estimates,budgets={arm:a.v1_scorer.budget(abs(v),sp['t0'],sp['K'],p['constants']) for arm,v in estimates.items()}))
    return dict(stage='FS-R1-Phase-A',truth_opened=False,protocol_sha256=a.sha((HERE/'fs_r1_protocol_v2.json').read_bytes()),systems=rows)

def proof():
    return dict(verified=True,protocol=a.protocol(),protocol_sha256=a.sha((HERE/'fs_r1_protocol_v2.json').read_bytes()),
        prediction_sha256=a.sha(a.canonical(prediction())),phase_a_commit='a'*40)

def toy_loader(spec,p,context):
    ns=a.v1_backend.native();B,S=ns['ComponentBatch'],ns['ComponentSpectrum']
    spectrum=S(2,(B(np.array([[0,1]],dtype=np.int64),np.array([[-1.,1.]]),np.eye(2,dtype=complex)[None]),),2,1,2,4)
    context.add('truth_only_source_load')
    return dict(hamiltonian=csr_matrix(np.diag([-1.,1.])),component_spectra=[spectrum],
        current_m3_sequence=p['protocol']['current_m3_sequence'],exact_ground=np.array([1,0],dtype=complex),exact_energy=-1.,
        source_identity_sha256=spec['source_identity_sha256'],synthetic_fixture=True)

@pytest.fixture
def toy_run(tmp_path):
    context=ContextV2('synthetic');p=proof()
    output=executor.execute_truth(p,context,tmp_path/'run',loader=toy_loader)
    return output,context,tmp_path/'run'

@pytest.fixture
def phase_a(tmp_path,monkeypatch):
    raw_prediction=a.canonical(prediction())
    files={'prediction.json':raw_prediction,'protocol.json':(HERE/'fs_r1_protocol_v2.json').read_bytes(),
        'source.json':(a.R0/'new_source_identity.json').read_bytes(),
        'recovery.json':a.canonical(dict(prediction_sha256=a.sha(raw_prediction),recovery_saved_before_public_validation=True))}
    code={p:(a.ROOT/p).read_bytes() for p in a.execution_code_paths()};files.update(code)
    files['code.json']=a.canonical(dict(format='FS-R1-code-v2',sha256={p:a.sha(v) for p,v in code.items()}))
    roles=dict(prediction='prediction.json',protocol='protocol.json',source_identity='source.json',code='code.json',recovery_reference='recovery.json')
    manifest=dict(stage='FS-R1-Phase-A',truth_opened=False,files={role:dict(path=path,sha256=a.sha(files[path])) for role,path in roles.items()})
    files['manifest.json']=a.canonical(manifest)
    for path,raw in files.items():
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    digest=a.sha(files['manifest.json']);commit='a'*40
    receipt=dict(status='PASS',remote_verified_commit=commit,manifest_sha256=digest,remote_fetched_independently=True,
        verified_file_sha256={path:a.sha(raw) for path,raw in files.items()})
    receipt_path=tmp_path/'receipt.json';receipt_path.write_bytes(a.canonical(receipt))
    monkeypatch.setattr(barrier,'git_blob',lambda root,co,path:files[path])
    return dict(args=(tmp_path,commit,'manifest.json',digest,receipt_path),files=files,root=tmp_path,receipt=receipt)

def test_14_exact_six_each():
    assert all(len(sp['times'])==6 for sp in a.read('branch_ladder.json')['systems'])

def test_15_twelve_total():
    budget=a.read('truth_budget.json');assert budget['truth_total_coordinates']==12 and budget['historical_truth_reuse']==0

def test_16_only_two_primary():
    systems=a.read('branch_ladder.json')['systems']
    assert sum(sp['roles'].count('primary_scoring') for sp in systems)==2
    assert sum(sp['roles'].count('branch_certification') for sp in systems)==10

@pytest.mark.parametrize('kind',['midpoint','extra','historical','nearest','duplicate'])
def test_17_to_20_reject_coordinate_changes(toy_run,kind):
    rows=copy.deepcopy(toy_run[0]['rows'])
    if kind=='midpoint':rows[1]['time']=(rows[0]['time']+rows[1]['time'])/2
    elif kind=='extra':rows.append(rows[0])
    elif kind=='historical':rows[0]['provenance']='historical saved truth'
    elif kind=='nearest':rows[-1]['time']=np.nextafter(rows[-1]['time'],1.)
    else:rows[1]=copy.deepcopy(rows[0])
    with pytest.raises(math.BranchFailure):bridge.validate_ladders(rows,a.protocol())

def test_missing_coordinate_fail(toy_run):
    with pytest.raises(math.BranchFailure,match='12 truth'):bridge.validate_ladders(toy_run[0]['rows'][:-1],a.protocol())

def test_phase_A_before_freeze_rejected(phase_a):
    args=list(phase_a['args']);args[1]='';reader=Mock()
    with pytest.raises(ValueError,match='full Phase A'):barrier.verify_phase_a(*args,reader)
    reader.assert_not_called()

@pytest.mark.parametrize('path',['prediction.json','source.json','protocol.json','code.json','recovery.json'])
def test_27_to_30_changed_role_rejected(phase_a,path):
    (phase_a['root']/path).write_text('mutated');reader=Mock()
    with pytest.raises(ValueError,match='mismatch'):barrier.verify_phase_a(*phase_a['args'],reader)
    reader.assert_not_called()

def test_changed_execution_code_rejected(phase_a):
    path=a.execution_code_paths()[-1];(phase_a['root']/path).write_text('mutated implementation')
    with pytest.raises(ValueError,match='execution code'):barrier.verify_phase_a(*phase_a['args'])

@pytest.mark.parametrize('field',['remote_verified_commit','manifest_sha256','remote_fetched_independently'])
def test_31_remote_receipt_mismatch(phase_a,field):
    proof=phase_a['receipt'];proof[field]=False if field=='remote_fetched_independently' else 'b'*40
    phase_a['args'][-1].write_bytes(a.canonical(proof))
    with pytest.raises(ValueError,match='receipt mismatch'):barrier.verify_phase_a(*phase_a['args'])

def test_valid_full_barrier_then_callback(phase_a):
    callback=Mock(return_value='opened')
    assert barrier.verify_phase_a(*phase_a['args'],callback)=='opened';callback.assert_called_once()

def test_32_intermediates_cannot_enter_B0(toy_run):
    pred=prediction();rows=toy_run[0]['rows'];result=bridge.score_frozen(pred,rows,a.protocol())
    changed=copy.deepcopy(rows)
    for row in changed:
        if row['time_role']=='branch_certification':row['signed_direct_shift']=999.
    assert bridge.score_frozen(pred,changed,a.protocol())==result
    for source,out in zip(pred['systems'],result['conditions']):assert out['B0_prime']==source['budgets']['M00p']

def test_33_intermediate_cannot_change_t0(toy_run):
    pred=prediction();pred['systems'][0]['time']=toy_run[0]['rows'][0]['time']
    with pytest.raises(ValueError,match='source/time changed'):bridge.score_frozen(pred,toy_run[0]['rows'],a.protocol())

def test_34_intermediate_cannot_select_arm(toy_run):
    result=bridge.score_frozen(prediction(),toy_run[0]['rows'],a.protocol())
    assert result['posthoc_best_arm'] is None and all(r['primary']=='M11p' for r in result['conditions'])

def test_35_only_final_t0_scorer_call(toy_run,monkeypatch):
    original=a.v1_scorer.condition_outcomes;calls=[]
    def spy(estimates,direct,spec,cfg):
        calls.append((spec['condition'],direct,spec['t0']));return original(estimates,direct,spec,cfg)
    monkeypatch.setattr(a.v1_scorer,'condition_outcomes',spy)
    result=bridge.score_frozen(prediction(),toy_run[0]['rows'],a.protocol())
    assert result['truth_values_scored']==2 and len(calls)==2
    for condition,value,t in calls:
        row=next(r for r in toy_run[0]['rows'] if r['condition']==condition and r['time_role']=='primary_scoring')
        assert value==row['signed_direct_shift'] and t==row['time']

def test_36_ground_overlap_not_estimator(toy_run):
    before=bridge.score_frozen(prediction(),toy_run[0]['rows'],a.protocol());rows=copy.deepcopy(toy_run[0]['rows'])
    for row in rows:row['ground_overlap']=0.
    assert bridge.score_frozen(prediction(),rows,a.protocol())==before
    pred=prediction();pred['systems'][0]['ground_overlap']=.9
    with pytest.raises(ValueError,match='truth information'):bridge.validate_prediction(pred,a.protocol())

def test_complete_toy_native_pf_schur_checkpoints(toy_run):
    output,context,directory=toy_run
    assert output['synthetic'] and output['truth_attempts']==12 and len(output['rows'])==12
    for key in ['PF_unitary_construction','Schur_decomposition','branch_matching','selected_vector_checkpoint','eigenpair_residual','unitarity_residual']:
        assert context.counts[key]==12
    assert context.counts['truth_only_source_load']==2
    assert (directory/'truth_scalar_recovery.json').exists()
    assert len(list(directory.glob('vector_*.npy')))==12
    assert all(abs(row['signed_direct_shift'])<1e-13 for row in output['rows'])

def test_branch_failure_stops_all_remaining_no_retry(tmp_path):
    builder=Mock(return_value=np.diag([1.,1.01]));context=ContextV2('synthetic');directory=tmp_path/'run'
    with pytest.raises(math.BranchFailure,match='unitarity'):executor.execute_truth(proof(),context,directory,loader=toy_loader,builder=builder)
    assert builder.call_count==1 and json.loads((directory/'FAILED.json').read_text())['further_truth_forbidden']
    with pytest.raises(FileExistsError):executor.execute_truth(proof(),context,directory,loader=toy_loader,builder=builder)
    assert builder.call_count==1

def test_private_checkpoint_hash_and_missing(toy_run):
    output,context,directory=toy_run;row=output['rows'][0];metadata=row['selected_vector_checkpoint']
    prior=executor.load_checkpoint(metadata,row['source_identity_sha256'],0,row['time'],context)
    assert prior['vector'].shape==(2,)
    altered=copy.deepcopy(metadata);altered['sha256']='0'*64
    with pytest.raises(math.BranchFailure,match='SHA'):executor.load_checkpoint(altered,row['source_identity_sha256'],0,row['time'],context)
    altered=copy.deepcopy(metadata);altered['private_path']=str(directory/'missing.npy')
    with pytest.raises(math.BranchFailure,match='missing'):executor.load_checkpoint(altered,row['source_identity_sha256'],0,row['time'],context)

def test_truth_recovery_before_public_and_no_science_retry(toy_run,tmp_path):
    output,context,directory=toy_run;before=context.counts.copy();public=tmp_path/'public.json'
    validator=Mock(side_effect=ValueError('public schema failure'))
    with pytest.raises(ValueError):executor.publish_recovered(directory/'truth_scalar_recovery.json',public,validator)
    assert not public.exists() and context.counts==before
    receipt=executor.publish_recovered(directory/'truth_scalar_recovery.json',public,lambda obj:None)
    assert not receipt['science_rerun'] and context.counts==before

def test_truth_source_not_opened_before_production_authorization(monkeypatch):
    decoder=Mock(side_effect=AssertionError('oracle decode'));monkeypatch.setattr(executor.pickle,'loads',decoder)
    spec=a.protocol()['systems'][0]
    with pytest.raises(PermissionError):executor.load_truth_source(spec,proof(),ContextV2())
    with pytest.raises(PermissionError):executor.load_truth_source(spec,proof(),ContextV2('synthetic'))
    decoder.assert_not_called()

def test_phaseA_context_v2_no_authorization_no_science():
    for phase in ('FS-R0.1','FS-R1-Phase-A','FS-R1-Phase-B'):
        with pytest.raises(PermissionError):ContextV2(phase).guard(1568)

def test_wrong_source_sha_before_decode(monkeypatch):
    decoder=Mock();monkeypatch.setattr(executor.pickle,'loads',decoder)
    spec=copy.deepcopy(a.protocol()['systems'][0]);spec['source_identity_sha256']='b'*64
    context=ContextV2('synthetic');monkeypatch.setattr(context,'guard',lambda *args:None)
    with pytest.raises(math.BranchFailure,match='source identity'):executor.load_truth_source(spec,proof(),context)
    decoder.assert_not_called()

def test_truth_source_decoder_wrong_whole_SHA_rejected_before_decode(tmp_path,monkeypatch):
    spec=a.protocol()['systems'][0];bad=tmp_path/'bad.pkl';bad.write_bytes(b'wrong raw source')
    registry={'sources':[dict(condition=spec['condition'],source_identity_sha256=spec['source_identity_sha256'],private_original_path=str(bad),private_original_whole_sha256='0'*64)]}
    fakeR0=tmp_path/'R0';fakeR0.mkdir();(fakeR0/'new_source_registry.json').write_bytes(a.canonical(registry))
    (fakeR0/'new_source_identity.json').write_bytes((a.R0/'new_source_identity.json').read_bytes())
    monkeypatch.setattr(executor,'R0',fakeR0);decoder=Mock();monkeypatch.setattr(executor.pickle,'loads',decoder)
    context=ContextV2('synthetic');monkeypatch.setattr(context,'guard',lambda *args:None)
    with pytest.raises(math.BranchFailure,match='whole SHA'):executor.load_truth_source(spec,proof(),context)
    decoder.assert_not_called()

def test_phaseA_math_preserved():
    old=json.loads((a.R0/'fs_r1_protocol.json').read_text());new=a.protocol()
    excluded={'protocol_id','stage','revision_reason','supersedes_protocol_id','supersedes_commit','truth_contract','phase_B',
        'approved_status_amendment','final_preflight_status','execution_ready'}
    assert {k:v for k,v in old.items() if k not in excluded}=={k:v for k,v in new.items() if k not in excluded}

def test_action_budget_truth_separate_from_calibration():
    old=json.loads((a.R0/'predicted_action_budget.json').read_text());new=a.read('predicted_action_budget_v2.json')
    for k in ('PF_forward_vector_actions','logical_exact_H_echo','explicit_Ritz_H_matvec_nominal','small_Ritz_solve_nominal','scalar_fits'):assert new[k]==old[k]
    truth=new['phase_B_truth_validation']
    assert truth['PF_unitary_construction']==truth['Schur_decomposition']==12
    assert a.read('cost_contract_truth.json')['QPE_addition'] is False

def test_private_checkpoint_scalar_public_fields_only(toy_run):
    row=toy_run[0]['rows'][0]
    assert set(row['selected_vector_checkpoint'])=={'private_path','sha256','source_identity_sha256','time','index','branch_id','dimension','dtype'}
    assert 'vector' not in row and 'exact_ground' not in row and 'unitary' not in row

def test_ladder_binary64_freeze_and_coordinate_audit():
    ladder=a.read('branch_ladder.json')
    for system in ladder['systems']:
        assert [float(t).hex() for t in system['times']]==system['times_hex']
        assert all(a<b for a,b in zip(system['times'],system['times'][1:]))
        assert system['binary64_authority_agreement']
        if a.read('coordinate_resolution.json')['choice']=='explicit_display':assert system['binary64_display_agreement']
