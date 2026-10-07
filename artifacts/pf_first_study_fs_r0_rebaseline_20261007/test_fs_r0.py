"""FS-R0 tests: toy arrays only; sealed production metadata/hash audits only."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock
import zipfile
import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import source_io as s
import backend as b
import freeze as f
import scorer as c
import truth_only as tr

def read(name):return json.loads((HERE/name).read_text())
def config():return read('fs_r1_protocol.json')['constants']

def toy():
    ns=b.native(); B,S=ns['ComponentBatch'],ns['ComponentSpectrum']
    idx=np.array([[0,1]],dtype=np.int64)
    z=S(2,(B(idx.copy(),np.array([[1.,-1.]]),np.eye(2,dtype=complex)[None]),),2,1,2,4)
    x=S(2,(B(idx.copy(),np.array([[-1.,1.]]),np.array([[[1,1],[-1,1]]],dtype=complex)/np.sqrt(2)),),2,1,2,4)
    H=csr_matrix(np.array([[1,1],[1,-1]],dtype=complex))
    state=np.array([np.sqrt(.7),1j*np.sqrt(.3)],dtype=complex)
    groups=[SimpleNamespace(terms={((0,'Z'),):1}),SimpleNamespace(terms={((0,'X'),):1})]
    meta={k:None for k in s.META_KEYS}
    meta.update(condition='toy',group_count=2,term_counts=[1,1],removed_constant_hartree=0,
        group_sha256=[s.sha(json.dumps(g,separators=(',',':')).encode()) for g in s.group_records(groups)])
    decoded={'system':{'hamiltonian':H,'states':{'cisd':state},'restricted_basis':np.array([0,1]),
        'component_spectra':[z,x],'state':'private exact ground','energy':-999},
        'metadata':dict(meta,overlap=.99,gap=1.,direct_truth=2.,branch_id=6,historical_safe=True,C06_acceptance=True),
        'ordered_groups':groups}
    return decoded,ns

@pytest.fixture
def exported(tmp_path):
    decoded,ns=toy(); dest=tmp_path/'private'
    identity=s.export_operational(decoded,read('fs_r1_protocol.json')['current_m3_sequence'],dest,s.sparse_hash(decoded['system']['hamiltonian']))
    with zipfile.ZipFile(dest/'source.npz') as z: meta=json.loads(z.read('operational.json'))
    loaded=s.load_operational(dest/'source.npz',identity['source_archive_sha256'],ns)
    return decoded,identity,meta,loaded,dest,ns

def test_01_exact_ground_absent(exported):
    assert set(exported[3])=={'hamiltonian','cisd','restricted_basis','component_spectra','metadata','current_m3_sequence','ordered_groups'}
    assert 'state' not in exported[2] and 'energy' not in exported[2]

@pytest.mark.parametrize('key',['overlap','gap','direct_truth','branch_id','historical_safe','C06_acceptance'])
def test_02_to_06_oracles_absent(exported,key):
    assert key not in exported[2]['metadata'] and key not in exported[2]['arrays']

def test_07_operational_required(exported):
    assert {'H_data','H_indices','H_indptr','H_shape','CISD','restricted_basis'}<=set(exported[2]['arrays'])
    assert len(exported[3]['component_spectra'])==2 and len(exported[3]['ordered_groups'])==2

def test_08_new_H_hash(exported):
    assert s.sparse_hash(exported[3]['hamiltonian'])==s.sparse_hash(exported[0]['system']['hamiltonian'])
    actual=read('new_source_identity.json')['identities']
    expected=['f4a08b755a4e903f4e9611fee394d6101a5d27279a1bd8af567b97920da5402e',
              '27ed246b354c754a506541dac81650aafdfa413b375fadf0b736822c171fb4c5']
    assert [i['hamiltonian_sha256'] for i in actual]==expected

def test_09_group_order(exported):
    assert exported[3]['ordered_groups']==s.group_records(exported[0]['ordered_groups'])
    assert exported[1]['ordered_group_sha256']==exported[0]['metadata']['group_sha256']
    bad=copy.deepcopy(exported[0]);bad['ordered_groups'].reverse()
    with pytest.raises(ValueError,match='ordered group'):s.export_operational(bad,[],exported[4].parent/'bad',s.sparse_hash(bad['system']['hamiltonian']))

def test_10_CISD_bytes(exported):
    old=exported[0]['system']['states']['cisd'];new=exported[3]['cisd']
    assert old.dtype==new.dtype and old.shape==new.shape and old.tobytes()==new.tobytes()
    assert not new.flags.writeable

def test_archive_oracle_extra_member_rejected(exported,tmp_path):
    source=exported[4]/'source.npz';out=tmp_path/'tampered.npz'
    with zipfile.ZipFile(source) as old,zipfile.ZipFile(out,'w') as new:
        for name in old.namelist():new.writestr(name,old.read(name))
        new.writestr('exact_ground.npy',b'forbidden')
    with pytest.raises(ValueError,match='extra/oracle'):s.load_operational(out,s.sha(out.read_bytes()),exported[5])

@pytest.fixture
def phase_a(tmp_path,monkeypatch):
    files={'prediction.json':s.canonical({'estimates':dict.fromkeys(c.ARMS,.0001)}),
           'protocol.json':s.canonical(read('fs_r1_protocol.json')),
           'source.json':s.canonical({'identity':'new source'})}
    code={path:b'toy frozen code '+path.encode() for path in f.execution_code_paths()}
    files.update(code)
    files['code.json']=s.canonical({'format':'FS-R1-code-v1','sha256':{p:s.sha(v) for p,v in code.items()}})
    manifest={'stage':'FS-R1-Phase-A','truth_opened':False,'files':{
        role:{'path':path,'sha256':s.sha(files[path])} for role,path in zip(f.REQUIRED,['prediction.json','protocol.json','source.json','code.json'])}}
    files['manifest.json']=s.canonical(manifest)
    for name,raw in files.items():
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    commit='a'*40; sha=s.sha(files['manifest.json'])
    proof={'status':'PASS','remote_verified_commit':commit,'manifest_sha256':sha,'remote_fetched_independently':True,
           'verified_file_sha256':{p:s.sha(v) for p,v in files.items()}}
    receipt=tmp_path/'receipt.json';receipt.write_bytes(s.canonical(proof))
    monkeypatch.setattr(f,'git_blob',lambda root,co,path:files[path])
    return dict(args=(tmp_path,commit,'manifest.json',sha,receipt),files=files,proof=proof,root=tmp_path)

def test_11_before_phase_A_rejected(phase_a):
    args=list(phase_a['args']);args[1]=''
    reader=Mock()
    with pytest.raises(ValueError,match='full Phase A'):f.verify_phase_a(*args,reader)
    reader.assert_not_called()

@pytest.mark.parametrize('path',['prediction.json','source.json','protocol.json','code.json'])
def test_12_to_15_changed_frozen_role_rejected(phase_a,path):
    (phase_a['root']/path).write_text('changed')
    reader=Mock()
    with pytest.raises(ValueError,match='changed'):f.verify_phase_a(*phase_a['args'],reader)
    reader.assert_not_called()

def test_every_execution_code_hash_required(phase_a):
    path=f.execution_code_paths()[0];(phase_a['root']/path).write_text('changed implementation')
    reader=Mock()
    with pytest.raises(ValueError,match='execution code'):f.verify_phase_a(*phase_a['args'],reader)
    reader.assert_not_called()

def test_16_missing_remote_rejected(phase_a):
    args=list(phase_a['args']);args[-1]=None
    with pytest.raises(ValueError,match='remote'):f.verify_phase_a(*args)

def truth_rows():
    p=read('fs_r1_protocol.json')
    rows=[{'condition':sp['condition'],'time':sp['t0'],'source_identity_sha256':sp['source_identity_sha256'],
        'provenance':'FS-R1-new-source-direct','branch_id':'FS-R1:'+sp['source_identity_sha256']+':toy',
        'branch_status':'resolved','unitarity_residual':0.,'eigenpair_residual':0.,'signed_direct':0.} for sp in p['systems']]
    return rows,p

def test_17_historical_truth_rejected():
    rows,p=truth_rows();rows[0]['provenance']='historical saved CSV'
    with pytest.raises(ValueError,match='historical truth'):tr.validate_truth_rows(rows,p)

@pytest.mark.parametrize('label',[6,9,'6','9'])
def test_18_historical_branch_ID_rejected(label):
    rows,p=truth_rows();rows[0]['branch_id']=label
    with pytest.raises(ValueError,match='historical branch'):tr.validate_truth_rows(rows,p)

def test_19_nearest_time_rejected():
    rows,p=truth_rows();rows[0]['time']=np.nextafter(rows[0]['time'],1.)
    with pytest.raises(ValueError,match='nearest'):tr.validate_truth_rows(rows,p)

@pytest.mark.parametrize('variant',['third','missing','duplicate'])
def test_20_truth_count(variant):
    rows,p=truth_rows()
    rows=rows+[rows[0]] if variant=='third' else (rows[:1] if variant=='missing' else [rows[0],rows[0]])
    with pytest.raises(ValueError,match='two unique'):tr.validate_truth_rows(rows,p)

def test_valid_barrier_still_rejects_unclosed_branch(phase_a):
    algo=Mock()
    with pytest.raises(RuntimeError,match='CONTRACT_UNCLOSED'):
        tr.dispatch_new_truth(*phase_a['args'],b.Context('synthetic'),algo)
    algo.assert_not_called()

def test_missing_anchor_no_schur(monkeypatch):
    spy=Mock();monkeypatch.setattr(tr,'schur',spy)
    with pytest.raises(RuntimeError,match='ANCHOR_UNAVAILABLE'):tr.continue_schur_at_target(None,None,None,1,None,'new')
    spy.assert_not_called()

def toy_pass(exported):
    source=exported[3];ctx=b.Context('synthetic')
    spec={'condition':'toy','training_absolute':[.1,.2,.3],'M10_training_absolute':[.1,.2,.3],
          't0':.4,'fit_scale_t_ref':1.,'K':10,'source_identity_sha256':'toy'}
    return b.prediction_pass(source,spec,ctx),ctx

def test_21_M00_three_point_native_fit(exported):
    adapter=b.NativeAdapter(exported[3],b.Context('synthetic'))
    times=[.1,.2,.3];values=[2*t**4-3*t**6 for t in times]
    fit=adapter.fit(times,values,1.,.4)
    np.testing.assert_allclose(fit['coefficient_values'],[2,-3],atol=1e-13,rtol=0)
    assert fit['signed_prediction_at_t0']==pytest.approx(2*.4**4-3*.4**6)
    with pytest.raises(ValueError,match='three'):adapter.fit(times+[.4],values+[0],1.,.4)

def test_22_identical_absolute_coordinates():
    for spec in read('fs_r1_protocol.json')['systems']:
        assert spec['M10_training_absolute']==spec['training_absolute'] and len(spec['training_absolute'])==3
        modified=copy.deepcopy(spec);modified['training_absolute'][0]=np.nextafter(spec['training_absolute'][0],1)
        with pytest.raises(ValueError,match='fixed'):b.fixed_spec(modified)

def test_23_M01_no_fit(exported):
    out,ctx=toy_pass(exported)
    assert out['estimates']['M01p']==out['proxy_rows']['CISD'][3]['signed_proxy']
    assert set(out['fits'])=={'CISD','Ritz8'} and ctx.counts['scalar_fit']==2

def test_24_M11_no_fit(exported):
    out,ctx=toy_pass(exported)
    assert out['estimates']['M11p']==out['proxy_rows']['Ritz8'][3]['signed_proxy']
    assert ctx.counts['PF_forward_vector_action']==ctx.counts['logical_exact_H_echo']==8

def test_25_new_B0_arithmetic():
    cfg=config();v=.00005;t=.6;K=20
    assert c.budget(v,t,K,cfg)==cfg['gamma']*cfg['beta']*K/(t*(cfg['epsilon_E']-v))

@pytest.mark.parametrize('factor',[1,2])
def test_26_infeasible_no_clip(factor):
    assert c.budget(factor*config()['epsilon_E'],.6,20,config()) is None

def test_27_raw_safety_slack():
    cfg=config();r=c.safety(.00005,.00003,.6,20,cfg)
    assert r['slack']==cfg['epsilon_E']-.00003-cfg['beta']*20/(.6*r['budget'])
    assert r['safe']
    assert not c.safety(.00005,.00003,.6,20,cfg,valid=False)['safe']

def outcomes(a00=.0001,a01=.00008,a11=.00005,direct=.00004):
    return c.condition_outcomes(dict(M00p=a00,M10p=.00009,M01p=a01,M11p=a11),direct,dict(t0=.6,K=20),config())

def test_28_primary_gain():assert outcomes()['primary_gain']
def test_29_local_gain():assert outcomes()['local_gain']
def test_30_state_increment():assert outcomes()['state_increment']
def test_31_safety_repair():
    r=outcomes(a01=.00004,a11=.00008,direct=.00007)
    assert r['safety_repair'] and not r['state_increment']

def test_32_no_posthoc_best():
    r=outcomes(a11=.00012)
    assert r['local_gain'] and not r['primary_gain']
    result=c.study_interpretation([r,r])
    assert result['posthoc_best_arm'] is None and result['primary_gain_count']==0

def test_33_recovery_precedes_public_validation(tmp_path):
    private=tmp_path/'private.json';public=tmp_path/'public.json'
    def validator(obj):
        assert private.exists() and private.with_suffix('.json.sha256').exists() and not public.exists()
        assert obj=={'value':1.}
    receipt=f.recovery_then_public({'value':np.float64(1)},private,public,validator)
    assert receipt['recovery_saved_before_schema'] and private.read_bytes()==public.read_bytes()

def test_34_serialization_failure_no_science_retry(tmp_path):
    science=Mock(return_value={'value':1.});payload=science()
    private=tmp_path/'private.json';public=tmp_path/'public.json'
    validator=Mock(side_effect=ValueError('schema failure'))
    with pytest.raises(ValueError,match='schema failure'):f.recovery_then_public(payload,private,public,validator)
    assert private.exists() and not public.exists();science.assert_called_once()
    with pytest.raises(FileExistsError):f.recovery_then_public(payload,private,public,validator)
    science.assert_called_once()

def test_35_independent_cold_counters():
    spec={'dimension':2};contexts=[];objects=[]
    def make():
        ctx=b.Context('synthetic');contexts.append(ctx);return ctx
    def loader(sp,ctx):
        d,ns=toy();objects.append(d);ctx.add('source_load');return d
    def acquire(d,sp,ctx):
        source=dict(hamiltonian=d['system']['hamiltonian'],cisd=d['system']['states']['cisd'],
            component_spectra=d['system']['component_spectra'],current_m3_sequence=read('fs_r1_protocol.json')['current_m3_sequence'])
        out=b.prediction_pass(source,dict(condition='toy',training_absolute=[.1,.2,.3],t0=.4,fit_scale_t_ref=1.,K=10,source_identity_sha256='toy'),ctx)
        return out
    result=b.cold_replay(spec,make,loader,acquire)
    assert objects[0] is not objects[1] and contexts[0].counts is not contexts[1].counts
    assert not np.shares_memory(objects[0]['system']['states']['cisd'],objects[1]['system']['states']['cisd'])
    assert result['initial_operational']['estimates']==result['cold_validation']['estimates']
    for ctx in contexts:
        assert ctx.counts['source_load']==1 and ctx.counts['PF_forward_vector_action']==8 and ctx.counts['scalar_fit']==2

def test_36_unknown_internal_null():
    assert all(v is None for v in b.Context().snapshot()['expm_internal'].values())

def test_37_wall_RSS_schema():
    snap=b.Context().snapshot()
    assert snap['classical']['wall_seconds']>=0 and snap['classical']['peak_RSS_bytes']>0
    assert set(snap['threads'])=={'OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'}

def test_38_classical_QPE_units_separate():
    contract=read('cost_contract.json')
    assert contract['mixed_unit_single_scalar'] is None
    assert contract['units']['classical']!=contract['units']['QPE']
    assert contract['measured_FS_R1_costs'] is None

def test_native_echo_sign_and_left_product(exported):
    source=exported[3];psi=source['cisd'];adapter=b.NativeAdapter(source,b.Context('synthetic'));t=.2
    expected=psi.copy();Z=np.diag([1.,-1.]);X=np.array([[0.,1.],[1.,0.]])
    for w in source['current_m3_sequence']:
        for H,weight in [(Z,w/2),(X,w),(Z,w/2)]:expected=expm(1j*t*weight*H) @ expected
    np.testing.assert_allclose(adapter.forward(psi,t),expected,rtol=0,atol=2e-14)
    independent=np.vdot(psi,expm(-1j*t*source['hamiltonian'].toarray()) @ expected).imag/t
    assert adapter.proxy(psi,t)['signed_proxy']==pytest.approx(independent,abs=5e-15)

def test_Ritz_rank_stop_lowest_and_deterministic_phase():
    H=csr_matrix(np.diag([0.,1.,2.]));psi=np.ones(3,dtype=complex)/np.sqrt(3);ctx=b.Context('synthetic')
    state,diag=b.ritz8(H,psi,ctx)
    assert diag['rank_stop'] and diag['retained_rank']==2
    np.testing.assert_allclose(state,[1,0,0],atol=2e-14,rtol=0)
    assert ctx.counts['H_matvec_count']==3 and ctx.counts['small_dense_ritz_eigh_count']==1

def test_Ritz_rank_zero_reuses_state():
    psi=np.array([1.,0.],dtype=complex);ctx=b.Context('synthetic')
    state,diag=b.ritz8(csr_matrix(np.diag([0.,1.])),psi,ctx)
    assert diag['retained_rank']==0 and ctx.counts['H_matvec_count']==1
    assert ctx.counts.get('small_dense_ritz_eigh_count',0)==0
    np.testing.assert_array_equal(state,psi)

def test_1568_interface_guards_before_action(monkeypatch):
    H=SimpleNamespace(shape=(1568,1568));state=Mock();spy=Mock(side_effect=AssertionError('production action'))
    monkeypatch.setattr(b,'compatible',spy)
    with pytest.raises(PermissionError):b.ritz8(H,state,b.Context())
    with pytest.raises(PermissionError):b.ritz8(H,state,b.Context('synthetic'))
    spy.assert_not_called()
    tree=__import__('ast').parse((HERE/'backend.py').read_bytes())
    assert not any(isinstance(n,__import__('ast').Attribute) and n.attr=='toarray' for n in __import__('ast').walk(tree))

def test_FS_R0_production_dispatch_all_closed(exported):
    context=b.Context();source=exported[3];adapter=b.NativeAdapter(source,context)
    for callback in [lambda:adapter.forward(source['cisd'],.2),lambda:adapter.proxy(source['cisd'],.2),
        lambda:adapter.fit([.1,.2,.3],[0,0,0],1.,.4),lambda:b.prediction_pass(source,{},context),
        lambda:b.load_registered_source(read('fs_r1_protocol.json')['systems'][0],context)]:
        with pytest.raises(PermissionError):callback()
    assert context.counts=={}

def test_registered_source_metadata_identity_frozen():
    identities=read('new_source_identity.json')['identities'];records=read('new_source_registry.json')['sources']
    for identity,record in zip(identities,records):
        assert s.sha(s.canonical(identity))==record['source_identity_sha256']
        assert identity['source_result_origin_commit']==identity['verified_snapshot_commit']=='14972353238cb001ccb1f754288daaae1ec3f65e'
        assert identity['H_shape']==[1568,1568] and identity['H_dtype']=='<c16'

def test_user_approved_NO_GO_not_source_failure():
    d=read('GO_NO_GO_FOR_FS_R1.json');p=read('fs_r1_protocol.json')
    assert d['status']=='NO_GO_BRANCH_CONTINUATION_UNCLOSED' and d['both_source_identities_frozen']
    assert not p['truth_contract']['branch_continuation_closed'] and p['truth_contract']['new_direct_truth_coordinates']==2
    assert not p['truth_contract']['extra_truth_coordinates_authorized']

def test_action_plan_arithmetic():
    p=read('predicted_action_budget.json')
    assert p['PF_forward_vector_actions']==p['logical_exact_H_echo']==32
    assert p['explicit_Ritz_H_matvec_nominal']==4*(1+8) and p['scalar_fits']==8
    assert p['actual_FS_R1_actions']==p['new_direct_truth_executed']==0

def test_invalid_or_indeterminate_no_gain():
    r=c.condition_outcomes(dict.fromkeys(c.ARMS,.00005),.00004,dict(t0=.6,K=20),config(),dict.fromkeys(c.ARMS,False))
    assert not any(r[k] for k in ('primary_gain','local_gain','state_increment','safety_repair'))
    assert c.safety(.00005,.00005,.6,20,config(),numeric_allowance=.001)['status']=='indeterminate'
    with pytest.raises(ValueError):c.safety(.00005,.00005,.6,20,config(),numeric_allowance=-1)

def test_unsafe_not_offset_by_average():
    good=outcomes();bad=outcomes(direct=.00013)
    r=c.study_interpretation([good,bad])
    assert r['primary_gain_count']==1 and 'resource extension STOP' in r['stop_rules']
    assert not r['independent_validation']
