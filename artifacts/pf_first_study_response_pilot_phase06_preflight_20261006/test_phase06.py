"""Production identity only; all scientific arithmetic uses small synthetic arrays."""
import ast,copy,io,json,zipfile
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from scipy.linalg import expm
from jsonschema import ValidationError
import phase06_inputs as inputs
from phase06_contract import *
from phase06_inputs import synthetic_inputs,load_phase_a_inputs,AllowlistArchive,array_hash,PhaseAData
from phase06_backend import EchoBackend
from phase06_kernels import *
from phase06_phase_a import execute_phase_a,residual_convergence,_cache_isolation
from phase06_freeze import validate_artifact,write_phase_a_artifact,code_identity,verify_phase_a_freeze,verify_committed_code
from phase06_phase_b import select_saved_truth,run_phase_b,score_payload
from phase06_runner import main

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

@pytest.fixture(scope='session')
def contract():return load_contract(ROOT)

@pytest.fixture(scope='session')
def schema():return json.loads((HERE/'phase_a_schema.json').read_text())

@pytest.fixture(scope='session')
def production_identity(contract):return load_phase_a_inputs(ROOT,contract)

def fixture(n=10,gcount=13):
    rng=np.random.default_rng(20261006+n+gcount);groups=[]
    for _ in range(gcount):
        x=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n));groups.append((x+x.conj().T)/(2*gcount))
    psi=rng.normal(size=n)+1j*rng.normal(size=n);psi/=np.linalg.norm(psi)
    return synthetic_inputs(sum(groups),groups,psi)

@pytest.fixture(scope='session')
def nominal(contract):
    ctx=ExecutionContext();payload,private=execute_phase_a(fixture(),contract,ctx,code_identity(HERE))
    return payload,private,ctx

def npz_bytes(key,array):
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:
        member=io.BytesIO();np.lib.format.write_array(member,array,allow_pickle=False);z.writestr(key+'.npy',member.getvalue())
    return raw.getvalue()

@pytest.mark.parametrize('key',['H4_exact_state','H4_ground_energy','direct_truth','controlled_state','H4_current_m3_D4','H4_current_m3_D6','H4_current_m3_D8'])
def test_allowlist_rejects_forbidden_member_before_any_open(key,monkeypatch):
    a=np.eye(2,dtype=complex);archive=AllowlistArchive(npz_bytes('allowed',a),{'allowed':((2,2),array_hash(a))})
    def forbidden(*args,**kwargs):raise AssertionError('Zip member opened before allowlist rejection')
    monkeypatch.setattr(zipfile.ZipFile,'open',forbidden)
    with pytest.raises(GateError,match='allowlist'):archive.read(key)
    assert archive.opened==[]

def test_phase_a_loader_has_no_direct_truth_path_or_exact_input_field():
    tree=ast.parse((HERE/'phase06_inputs.py').read_text())
    text=ast.unparse(tree)
    assert '.csv' not in text and 'np.load' not in text
    with pytest.raises(TypeError):PhaseAData(None,(),None,{}, {},'production',exact_state=object())

def test_production_source_identity_headers_and_hashes_only(production_identity):
    audit=production_identity.identity_audit
    assert audit['status']=='passed' and len(audit['members_opened'])==15
    assert audit['forbidden_members_opened']==[]
    assert not audit['production_norms_or_products_computed'] and audit['science_action_count']==0
    assert all(row['dtype']=='<c16' for row in audit['arrays'])
    assert not production_identity.H.flags.writeable and not production_identity.psi.flags.writeable

def test_production_unauthorized_guard_before_any_kernel_or_backend(contract,production_identity):
    ctx=ExecutionContext('production')
    with pytest.raises(GateError,match='science_not_authorized'):
        execute_phase_a(production_identity,contract,ctx,code_identity(HERE))
    with pytest.raises(GateError,match='science_not_authorized'):EchoBackend(production_identity,contract,ctx)
    assert all(v==0 for v in ctx.science.values())
    with pytest.raises(GateError,match='domain mismatch'):
        execute_phase_a(production_identity,contract,ExecutionContext('synthetic'),code_identity(HERE))

def test_file_hash_mismatch_stops_before_production_decode(contract,monkeypatch):
    bundle=dict(contract.identity['f01_bundle']);bundle['sha256']='0'*64
    monkeypatch.setattr(zipfile.ZipFile,'open',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('decode must not happen')))
    with pytest.raises(GateError,match='before decode'):inputs.verified_archive_bytes(ROOT,bundle)

def test_blob_mismatch_stops_before_decode(contract,monkeypatch):
    monkeypatch.setattr(inputs,'_git',lambda *args:'0'*40)
    with pytest.raises(GateError,match='blob mismatch'):inputs.verified_archive_bytes(ROOT,contract.identity['f01_bundle'])

@pytest.mark.parametrize('change',['dtype','shape','hash'])
def test_array_identity_mismatch(change):
    original=np.eye(2,dtype=complex);changed=original.copy();expected=array_hash(original)
    if change=='dtype':changed=changed.real.astype('float64')
    if change=='shape':changed=changed.reshape(4)
    if change=='hash':changed[0,0]=2
    archive=AllowlistArchive(npz_bytes('allowed',changed),{'allowed':((2,2),expected)})
    with pytest.raises(GateError,match='array hash/dtype/shape'):archive.read('allowed')

def test_metadata_and_formula_modification_fail_frozen_contract(contract):
    identity=copy.deepcopy(contract.identity);identity['molecular_metadata']['basis']='changed'
    with pytest.raises(GateError,match='contract changed'):load_phase_a_inputs(ROOT,replace(contract,identity=identity))
    protocol=copy.deepcopy(contract.protocol);protocol['response']['m_values']=[1,2,8]
    with pytest.raises(GateError,match='contract changed'):replace(contract,protocol=protocol).verify()

def test_path_resolution_rejects_escape_before_read(contract):
    b=dict(contract.identity['f01_bundle']);b['path']='../../outside.npz'
    with pytest.raises(GateError,match='path outside'):inputs.verified_archive_bytes(ROOT,b)

def reference_s2(groups,sequence,t):
    # Independently evaluate the inherited spectral builder on synthetic groups.
    spectra=[np.linalg.eigh(g) for g in groups]
    block_cache={};U=np.eye(len(groups[0]),dtype=complex)
    for weight in sequence:
        if weight not in block_cache:
            block=np.eye(len(groups[0]),dtype=complex)
            steps=[(i,weight/2) for i in range(len(groups)-1)]+[(len(groups)-1,weight)]+[(i,weight/2) for i in reversed(range(len(groups)-1))]
            for i,w in steps:
                values,vectors=spectra[i]
                block=vectors@(np.exp(1j*(t*w)*values)[:,None]*(vectors.conj().T@block))
            block_cache[weight]=block
        U=block_cache[weight]@U
    return U

def test_pade_forward_and_original_spectral_order(contract):
    data=fixture(4,3);ctx=ExecutionContext();backend=EchoBackend(data,contract,ctx)
    U,T=backend.build(.4)
    reference=reference_s2(data.groups,contract.protocol['formula_definition']['s2_sequence'],.4)
    assert np.allclose(U,reference,atol=1e-12,rtol=1e-12)
    assert np.allclose(backend.forward(.4,data.psi),T@(reference@data.psi))
    assert ctx.counts['PF_forward_action_count']==1 and ctx.counts['exact_H_echo_action_count']==1

def test_adjoint_order_and_no_opposite_time_echo_substitution(contract):
    data=fixture(4,3);ctx=ExecutionContext();backend=EchoBackend(data,contract,ctx)
    U,T=backend.build(.4);Um,Tm=backend.build(-.4)
    expected=U.conj().T@(T.conj().T@data.psi)
    assert np.allclose(backend.adjoint(.4,data.psi),expected)
    assert np.linalg.norm((Tm@Um)-(T@U).conj().T)>1e-10
    assert backend.audit_signed_pair(.4)<1e-10
    assert len(backend.matrices)==2 and ctx.counts['PF_dense_build_count']==2

def test_unitarity_failure_stops_before_proxy(contract,monkeypatch):
    import phase06_backend
    monkeypatch.setattr(phase06_backend,'expm',lambda matrix:2*np.eye(len(matrix),dtype=complex))
    backend=EchoBackend(fixture(2,2),contract,ExecutionContext())
    with pytest.raises(GateError,match='unitarity'):backend.build(.1)

def test_duplicate_signed_build_forbidden_and_cache_per_build(contract):
    backend=EchoBackend(fixture(3,3),contract,ExecutionContext());backend.build(.1)
    with pytest.raises(GateError,match='duplicate signed'):backend.build(.1)
    backend.build(-.1)
    assert backend.cache_events==[{'time':.1,'unique_block_weights':4,'cache_scope':'this signed build only'},{'time':-.1,'unique_block_weights':4,'cache_scope':'this signed build only'}]
    assert backend.context.counts['group_expm_count']==2*4*5

def test_nominal_counts_and_cold_replay_counted_again(contract,nominal):
    p,private,ctx=nominal;expected=json.loads((ROOT/PH05/'expected_action_counts.json').read_text())['joint_all_m_with_cold_replay']
    for name in ctx.counts:
        if name in expected:assert ctx.counts[name]==expected[name],name
    assert ctx.counts==expected_counts(8,False)
    assert p['cost']['cold_replay_increment']['H_matvec_count']==9
    assert p['cost']['cold_replay_increment']['PF_forward_action_count']==110
    assert p['replay']['cache_isolation_passed'] and len(private)==88
    assert sum(ctx.science.values())==0

def test_rank_stop_counts_and_zero_rank_fallback(contract):
    for psi,k in [(np.sqrt([.9,.1,0.]),1),(np.array([1.,0.,0.]),0)]:
        H=np.diag([0.,1.,2.]).astype(complex)
        data=synthetic_inputs(H,[H/13]*13,psi)
        ctx=ExecutionContext();p,_=execute_phase_a(data,contract,ctx,code_identity(HERE))
        assert p['basis']['actual_rank']==k and p['basis']['status']=='prefix_stopped'
        assert ctx.counts==expected_counts(k,True)
        if k==0:
            assert ctx.counts['PF_action_on_ritz_state_count']==0
            assert all(r['proxies']['A0']==r['proxies']['A1']==r['proxies']['A2'] for r in p['rows'])

def test_full_residual_least_squares_not_projected_galerkin():
    Z=np.array([[1.],[0.]]);L=np.array([[2.,1.],[1.,3.]])
    b=Basis(np.array([1.,0.]),0.,np.zeros(2),Z,np.zeros(2),L@Z,L@Z,False,())
    ctx=ExecutionContext();z,d=solve_response_least_squares(factor_response(b,1,ctx),np.array([0.,1.]),ctx)
    assert z[0]==pytest.approx(.2) and d['d_norm']==pytest.approx(np.sqrt(.8))
    assert np.linalg.solve(Z.T@L@Z,Z.T@np.array([0.,1.]))[0]==0

def test_identity_exact_input_and_commuting_counterexample():
    H=np.diag([0.,1.]);psi=np.sqrt([.9,.1]);ctx=ExecutionContext();b=build_response_basis(H,psi,ctx)
    f=factor_response(b,8,ctx);z,d=solve_response_least_squares(f,np.zeros(2),ctx)
    assert compute_response_proxy(1.,z,b.r)==1.
    z,d=solve_response_least_squares(f,project(psi,H@psi,ctx),ctx)
    assert 2*np.vdot(z,b.r).real==pytest.approx(.225)
    b=build_response_basis(H,np.array([1.,0.]),ctx)
    assert b.Z.shape[1]==0 and np.linalg.norm(b.r)==0

def test_svd_truncation_and_zero_rhs_residual():
    Z=np.eye(3)[:,:2];B=Z@np.diag([1.,1e-18])
    b=Basis(np.array([0.,0.,1.]),0,np.zeros(3),Z,np.zeros(3),B,B,False,())
    ctx=ExecutionContext();f=factor_response(b,2,ctx);z,d=solve_response_least_squares(f,np.array([1.,1.,0.]),ctx)
    assert d['effective_rank']==1 and d['d_norm']==pytest.approx(1.)
    z,d=solve_response_least_squares(f,np.zeros(3),ctx);assert d['relative_residual']==0

def test_residual_convergence_calculation_uses_frozen_allowance(nominal):
    p,_,_=nominal;result=residual_convergence(p['rows'])
    assert len(result['comparisons'])==66
    assert all(c['passed']==(c['residual_increase']<=c['roundoff_allowance']) for c in result['comparisons'])
    rows=copy.deepcopy(p['rows']);rows[0]['response']['8']['d_norm']=100.
    assert not residual_convergence(rows)['converged']

def test_ritz_same_prefix_hermiticity_and_deterministic_phase():
    data=fixture();ctx=ExecutionContext();b=build_response_basis(data.H,data.psi,ctx)
    for m in (1,2,4,8):
        state,d=solve_ritz_state(b,m,ctx)
        V=np.column_stack((b.psi,b.Z[:,:m]))
        assert np.linalg.norm(state-V@(V.conj().T@state))<1e-12
        assert d['projected_dimension']==m+1
        pivot=np.argmax(abs(state));assert abs(state[pivot].imag)<1e-12 and state[pivot].real>=0
    b.HZ[:]=1j*b.Z
    with pytest.raises(ValueError,match='Hermiticity'):solve_ritz_state(b,8,ctx)

def test_ritz_lowest_eigenspace_tie_rule_and_zero_rank():
    psi=np.array([1.,0.,0.],complex);Z=np.eye(3,dtype=complex)[:,1:]
    b=Basis(psi,0,np.zeros(3),Z,np.zeros(3),np.zeros((3,2)),np.zeros((3,2)),False,())
    ctx=ExecutionContext();state,d=solve_ritz_state(b,2,ctx)
    assert np.allclose(state,psi) and d['degeneracy']==3 and d['tie_status']=='degenerate_lowest_subspace'
    b=Basis(psi,0,np.zeros(3),Z[:,:0],np.zeros(3),Z[:,:0],Z[:,:0],True,())
    state,d=solve_ritz_state(b,8,ctx);assert np.allclose(state,psi) and d['tie_status']=='zero_rank_original_state'

def test_all_arms_share_fit_rule_and_quality_gate(nominal):
    p,_,_=nominal
    assert len(p['fits'])==9 and p['cost']['actions']['fit_count']==27
    conditions=[f['raw_positive_even_two_term']['condition_number'] for f in p['fits'].values()]
    assert max(conditions)==min(conditions)
    t=np.array(TRAIN);y=t**4-.7*t**6
    model=fit_two_term_model(TRAIN,y,y,['unresolved']*5)['raw_positive_even_two_term']
    assert model['status']=='not_identifiable'
    assert np.allclose(model['coefficients'],[1.,-.7])

def test_phase_a_dependencies_contain_no_phase_b_or_truth_loader():
    for name in ['phase06_phase_a.py','phase06_inputs.py','phase06_backend.py','phase06_kernels.py']:
        tree=ast.parse((HERE/name).read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert 'phase06_phase_b' not in imports
        assert not any(isinstance(n,ast.Attribute) and n.attr in ('schur',) for n in ast.walk(tree))

def test_schema_rejects_truth_and_raw_matrix_fields(nominal,schema):
    payload=copy.deepcopy(nominal[0]);validate_artifact(payload,schema)
    for target in [payload,payload['rows'][0],payload['rows'][0]['noise']['A0'],payload['rows'][0]['response']['8']]:
        target['exact_proxy']=.5
        with pytest.raises(ValidationError):validate_artifact(payload,schema)
        del target['exact_proxy']
    payload['rows'][0]['response']['8']['L_m_complex_pairs']=[[[1,0]]]
    with pytest.raises(ValidationError):validate_artifact(payload,schema)

def test_phase_a_artifact_create_only_and_private_diagnostics_outside_git(tmp_path,nominal,schema):
    output=tmp_path/'repo'/'artifacts'/'pf_first_study_response_pilot_phase_a_test'
    private=tmp_path/'private'
    write_phase_a_artifact(output,nominal[0],schema,nominal[1],private)
    assert sorted(p.name for p in output.iterdir())==['phase_a.json','phase_a_manifest.json']
    assert (private/'projected_diagnostics.json').exists()
    with pytest.raises(GateError,match='already exists'):write_phase_a_artifact(output,nominal[0],schema,nominal[1],private)

class MockGit:
    def __init__(self,blobs,commit='a'*40):self.blobs=blobs;self.commit=commit
    def allowed_remote(self):pass
    def remote_tip(self,branch):return self.commit
    def blob(self,commit,path):return self.blobs[path]

def test_implementation_and_schema_must_match_committed_snapshot_before_science(tmp_path):
    directory=tmp_path/'artifacts'/'package';directory.mkdir(parents=True)
    (directory/'phase06_stub.py').write_bytes(b'# fixture\n')
    (directory/'phase_a_schema.json').write_bytes(b'{}\n')
    files=code_identity(directory)
    assert 'artifacts/package/phase_a_schema.json' in files
    git=MockGit({path:(tmp_path/path).read_bytes() for path in files})
    assert verify_committed_code(tmp_path,directory,git)==files
    (directory/'phase_a_schema.json').write_bytes(b'{"changed":true}\n')
    with pytest.raises(GateError,match='uncommitted implementation/schema'):
        verify_committed_code(tmp_path,directory,git)

def frozen_fixture(tmp_path,nominal):
    payload=copy.deepcopy(nominal[0]);code_path='artifacts/code_stub.py';code_raw=b'# synthetic code identity fixture\n'
    payload['source']['code_files']={code_path:sha(code_raw)};payload['source']['code_sha256']=sha(canonical(payload['source']['code_files']))
    path='artifacts/pf_first_study_response_pilot_phase_a_fixture/phase_a.json'
    raw=canonical(payload);p=tmp_path/path;p.parent.mkdir(parents=True);p.write_bytes(raw)
    c=tmp_path/code_path;c.write_bytes(code_raw)
    manifest={'files':[{'path':'phase_a.json','sha256':sha(raw),'bytes':len(raw)}],**{k:payload['source'][k] for k in ('protocol_sha256','source_sha256','code_sha256')}}
    blobs={path:raw,str(Path(path).with_name('phase_a_manifest.json')):canonical(manifest),code_path:code_raw,
        PH05+'/response_pilot_protocol.json':(ROOT/PH05/'response_pilot_protocol.json').read_bytes()}
    receipt={'commit':'a'*40,'branch':'synthetic-fixture','prediction_path':path,'prediction_sha256':sha(raw),'publication_verified':True,
        **{k:payload['source'][k] for k in ('protocol_sha256','source_sha256','code_sha256')}}
    return receipt,MockGit(blobs),payload

def synthetic_truth():
    direct={s*t:.3*(s*t)**4 for t in EVAL for s in (1,-1)}
    exact={s*t:{'proxy':.3*(s*t)**4,'quality':'resolved'} for t in TRAIN+EVAL for s in (1,-1)}
    return direct,exact

def test_phase_b_no_commit_or_hash_stops_before_reader(tmp_path,nominal,contract,schema):
    receipt,git,_=frozen_fixture(tmp_path,nominal)
    for key in ('commit','prediction_sha256','protocol_sha256','source_sha256','code_sha256'):
        altered=dict(receipt);altered.pop(key)
        called=[]
        with pytest.raises(GateError):run_phase_b(tmp_path,altered,contract,schema,transport=git,synthetic_reader=lambda:called.append(1))
        assert called==[]

@pytest.mark.parametrize('change',['file','committed_blob','remote','code','source','protocol'])
def test_altered_identity_blocks_truth_reader(tmp_path,nominal,contract,schema,change):
    receipt,git,payload=frozen_fixture(tmp_path,nominal);called=[]
    if change=='file':(tmp_path/receipt['prediction_path']).write_bytes(b'altered')
    if change=='committed_blob':git.blobs[receipt['prediction_path']]=b'altered'
    if change=='remote':git.commit='b'*40
    if change=='code':(tmp_path/'artifacts/code_stub.py').write_bytes(b'changed')
    if change=='source':receipt['source_sha256']='0'*64
    if change=='protocol':git.blobs[PH05+'/response_pilot_protocol.json']=b'changed'
    with pytest.raises(GateError):run_phase_b(tmp_path,receipt,contract,schema,transport=git,synthetic_reader=lambda:called.append(1))
    assert called==[]

def test_verified_synthetic_phase_b_scoring_is_immutable(tmp_path,nominal,contract,schema):
    receipt,git,payload=frozen_fixture(tmp_path,nominal)
    raw=(tmp_path/receipt['prediction_path']).read_bytes()
    result=run_phase_b(tmp_path,receipt,contract,schema,transport=git,synthetic_reader=synthetic_truth)
    assert result['saved_direct_truth_read_count']==12 and result['saved_exact_proxy_read_count']==22
    assert result['new_direct_truth_count']==0 and len(result['arms'])==10
    assert result['arms']['A3']['point_S_abs']==0
    assert all(len(a['rows'])==12 for a in result['arms'].values())
    assert (tmp_path/receipt['prediction_path']).read_bytes()==raw

def mock_saved_csv(contract):
    import csv
    join=json.loads((ROOT/PH05/'saved_truth_join_contract.json').read_bytes())
    branch=[]
    for key in join['keys']:branch.append({**key,'direct_shift_hartree':'.01'})
    observables=[{'experiment_id':'B','case_id':'H4','formula_id':'current_m3','state_id':'exact','sign':str(s),
        'absolute_time':str(t),'time_hartree_inverse':str(s*t),'proxy_imag_hartree':'.01','quality_class':'resolved'} for t in TRAIN+EVAL for s in (1,-1)]
    def encode(rows):
        out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows);return out.getvalue().encode()
    return branch,observables,join,encode

@pytest.mark.parametrize('kind',['missing_direct','duplicate_direct','missing_exact','duplicate_exact','unreliable','branch_identity'])
def test_saved_truth_missing_duplicate_or_unreliable_stops(contract,kind):
    branch,observables,join,encode=mock_saved_csv(contract)
    if kind=='missing_direct':branch.pop()
    if kind=='duplicate_direct':branch.append(branch[0])
    if kind=='missing_exact':observables.pop()
    if kind=='duplicate_exact':observables.append(observables[0])
    if kind=='unreliable':branch[0]['branch_reliable']='False'
    if kind=='branch_identity':branch[0]['selected_eigenbranch_id']='7'
    with pytest.raises(GateError):select_saved_truth(encode(branch),encode(observables),join)

def test_saved_truth_selects_only_frozen_keys(contract):
    branch,obs,join,encode=mock_saved_csv(contract)
    branch.append({**branch[0],'case_id':'other','direct_shift_hartree':'not a number'})
    obs.append({**obs[0],'state_id':'controlled','proxy_imag_hartree':'not a number'})
    direct,exact=select_saved_truth(encode(branch),encode(obs),join)
    assert len(direct)==12 and len(exact)==22

def test_no_current_production_science_or_truth_authorization(contract,monkeypatch):
    import phase06_runner
    monkeypatch.setattr(phase06_runner,'load_phase_a_inputs',lambda *args:(_ for _ in ()).throw(AssertionError('unauthorized production loader')))
    for phase in ('--phase-a','--phase-b'):
        with pytest.raises(GateError,match='science_not_authorized'):main([phase,'--root',str(ROOT)])
    with pytest.raises(GateError,match='science_not_authorized'):run_phase_b(ROOT,{},contract,{},authorization=None)

def test_authorization_scope_checked_and_no_auto_authorization(tmp_path):
    p=tmp_path/'authorization.json'
    p.write_text(json.dumps({'science_authorized':False,'phase':'phase-a','protocol_sha256':PROTOCOL_SHA}))
    with pytest.raises(GateError):load_authorization(p,'phase-a')
    p.write_text(json.dumps({'science_authorized':True,'phase':'phase-b','protocol_sha256':PROTOCOL_SHA}))
    with pytest.raises(GateError):load_authorization(p,'phase-a')

def test_counter_mismatch_stops_before_publication(contract):
    context=ExecutionContext();context.counts['PF_forward_action_count']=1
    with pytest.raises(GateError,match='action_count_contract_mismatch'):
        execute_phase_a(fixture(3,3),contract,context,code_identity(HERE))

def test_synthetic_freeze_cannot_open_production_truth_reader(tmp_path,nominal,contract,schema):
    receipt,git,_=frozen_fixture(tmp_path,nominal)
    with pytest.raises(GateError,match='production Phase A freeze'):
        run_phase_b(tmp_path,receipt,contract,schema,Authorization('phase-b',PROTOCOL_SHA,'0'*64),transport=git)
