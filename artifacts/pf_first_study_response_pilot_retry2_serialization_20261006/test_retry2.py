"""Serialization/recovery tests; production use is identity-only metadata."""
from pathlib import Path
import copy,json,sys,hashlib,ast
import numpy as np
import pytest
from jsonschema import Draft202012Validator,ValidationError
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P06=ROOT/'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
sys.path.insert(0,str(P06));sys.path.insert(0,str(HERE))
from phase06_contract import load_contract,canonical,sha,PROTOCOL_SHA,ExecutionContext,GateError,expected_counts
from phase06_inputs import load_phase_a_inputs,synthetic_inputs
from phase06_phase_a import execute_phase_a
from phase06_freeze import validate_artifact,verify_phase_a_freeze,code_identity
from retry2_boundary import *

@pytest.fixture(scope='module')
def schema():return json.loads((P06/'phase_a_schema.json').read_bytes())

@pytest.fixture(scope='module')
def contract():return load_contract(ROOT)

@pytest.fixture(scope='module')
def identity(contract):return load_phase_a_inputs(ROOT,contract).identity_audit

@pytest.fixture(scope='module')
def synthetic(contract):
    rng=np.random.default_rng(20261006);groups=[]
    for _ in range(13):
        a=rng.normal(size=(10,10))+1j*rng.normal(size=(10,10));groups.append((a+a.conj().T)/26)
    psi=rng.normal(size=10)+1j*rng.normal(size=10);psi/=np.linalg.norm(psi)
    context=ExecutionContext('synthetic')
    p,d=execute_phase_a(synthetic_inputs(sum(groups),groups,psi),contract,context,code_identity(P06))
    assert context.counts==expected_counts(8,False) and sum(context.science.values())==0
    return p,d

def test_A_original_tuple_identity_reproduces_attempt1(identity,schema):
    validator=Draft202012Validator(schema['properties']['source']['properties']['input_array_identities'])
    assert isinstance(identity['ordered_group_identity'][0],tuple)
    with pytest.raises(ValidationError):validator.validate(identity)

def test_B_JSON_native_production_identity_passes_strict_schema(identity,schema):
    native=to_json_native(identity)
    Draft202012Validator(schema['properties']['source']['properties']['input_array_identities']).validate(native)
    assert all(isinstance(pair,list) for pair in native['ordered_group_identity'])
    assert isinstance(identity['ordered_group_identity'][0],tuple) # pure, no input mutation

def test_C_order_hash_pairing_and_roundtrip_unchanged(identity):
    native=to_json_native(identity);roundtrip=json.loads(json.dumps(native,allow_nan=False))
    assert canonical(identity)==canonical(native)==canonical(roundtrip)
    assert sha(canonical(identity))==sha(canonical(roundtrip))
    assert native['arrays']==identity['arrays'] and native['members_opened']==identity['members_opened']
    assert [list(pair) for pair in identity['ordered_group_identity']]==roundtrip['ordered_group_identity']

def test_D_protocol_schema_and_frozen_kernel_bytes_unchanged(contract):
    assert sha((ROOT/'artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json').read_bytes())==PROTOCOL_SHA
    authority=json.loads((P06/'preflight_protocol.json').read_bytes())
    assert code_identity(P06)==authority['code_files_sha256']
    contract.verify()

def test_E_recovery_cannot_open_truth_or_satisfy_public_freeze(tmp_path,synthetic,contract,schema):
    root=tmp_path/'repository';root.mkdir();recovery=tmp_path/'private'
    write_recovery(recovery,synthetic[0],'a'*64,'b'*40,root)
    snapshot=read_recovery(recovery)
    assert snapshot['phase_b_input_permitted'] is False
    with pytest.raises(GateError,match='full commit freeze missing'):
        verify_phase_a_freeze(root,snapshot,contract,schema)
    tree=ast.parse((HERE/'retry2_boundary.py').read_text())
    assert not any(isinstance(n,ast.ImportFrom) and n.module=='phase06_phase_b' for n in ast.walk(tree))

def test_full_scalar_payload_with_production_metadata_normalizes(synthetic,identity,schema):
    payload=copy.deepcopy(synthetic[0]);payload['input_domain']='production' # schema fixture only
    payload['source']['input_array_identities']=identity
    payload['source']['source_metadata']=load_contract(ROOT).identity['molecular_metadata']
    payload['source']['source_sha256']=sha(canonical(identity))
    with pytest.raises(ValidationError):validate_artifact(payload,schema)
    fixed=normalize_payload(payload);validate_artifact(fixed,schema)
    validate_artifact(json.loads(canonical(fixed)),schema)
    assert fixed['predictions']==payload['predictions'] and fixed['cost']==payload['cost']

def test_utility_preserves_precision_order_numpy_and_path():
    number=np.float64(np.nextafter(1.,2.));v={'z':(np.int64(7),np.bool_(True),number),'a':Path('metadata'),'b':np.asarray([1,3,2],np.int64)}
    native=to_json_native(v)
    assert list(native)==['z','a','b'] and native['z']==[7,True,float(number)]
    assert native['z'][2].hex()==float(number).hex() and native['a']=='metadata' and native['b']==[1,3,2]

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),complex(1,2),np.eye(2),np.array([1+2j]),{1:'bad'}])
def test_nonfinite_complex_matrix_and_nonstring_keys_rejected(bad):
    with pytest.raises(GateError):to_json_native(bad)

def test_recovery_create_only_readonly_sha_and_all_scalar_fields(tmp_path,synthetic):
    root=tmp_path/'repo';root.mkdir();recovery=tmp_path/'private'
    before=canonical(synthetic[0]);audit=write_recovery(recovery,synthetic[0],'a'*64,'b'*40,root)
    snapshot=read_recovery(recovery)
    assert audit['recovery_snapshot_valid'] and audit['saved_before_public_validation']
    assert audit['sha256']==sha((recovery/'recovery_snapshot.json').read_bytes())
    assert canonical(snapshot['payload'])==before and canonical(synthetic[0])==before
    assert (recovery/'recovery_snapshot.json').stat().st_mode&0o222==0
    with pytest.raises(GateError,match='already exists'):write_recovery(recovery,synthetic[0],'a'*64,'b'*40,root)

def test_recovery_must_stay_private_and_has_no_truth(tmp_path,synthetic):
    root=tmp_path/'repo';root.mkdir()
    with pytest.raises(GateError,match='outside repository'):write_recovery(root/'snapshot',synthetic[0],'a'*64,'b'*40,root)
    p=copy.deepcopy(synthetic[0]);p['basis']['exact_state']=[1,0]
    with pytest.raises(GateError,match='truth/private'):write_recovery(tmp_path/'private',p,'a'*64,'b'*40,root)

def test_public_writer_failure_leaves_recovery_and_no_science_rerun(tmp_path,synthetic,schema):
    root=tmp_path/'repo';root.mkdir();recovery=tmp_path/'private'
    called=[]
    def failed_writer(*args):
        assert read_recovery(recovery)['payload']['predictions']==synthetic[0]['predictions']
        called.append('public');raise RuntimeError('injected public artifact failure')
    with pytest.raises(RuntimeError,match='injected public'):
        persist_then_write(*synthetic,recovery,root/'artifacts'/'phase_a',tmp_path/'diagnostics',schema,'a'*64,'b'*40,root,writer=failed_writer)
    assert called==['public'] and read_recovery(recovery)['payload']['cost']['actions']['H_matvec_count']==18

def test_public_writer_success_uses_same_recovered_scalar_bytes(tmp_path,synthetic,schema):
    root=tmp_path/'repo';root.mkdir();recovery=tmp_path/'private';public=root/'artifacts'/'phase_a'
    native,audit=persist_then_write(*synthetic,recovery,public,tmp_path/'diagnostics',schema,'a'*64,'b'*40,root)
    assert (public/'phase_a.json').read_bytes()==canonical(native)
    assert read_recovery(recovery)['payload']==native and audit['recovery_snapshot_valid']
    assert not (public/'recovery_snapshot.json').exists()

def test_actual_public_schema_failure_preserves_private_recovery(tmp_path,synthetic,schema):
    root=tmp_path/'repo';root.mkdir();recovery=tmp_path/'private'
    broken=copy.deepcopy(schema);broken['required']=[*broken['required'],'injected_required_field']
    with pytest.raises(ValidationError):
        persist_then_write(*synthetic,recovery,root/'artifacts'/'phase_a',tmp_path/'diagnostics',broken,'a'*64,'b'*40,root)
    assert read_recovery(recovery)['payload']['predictions']==synthetic[0]['predictions']
    assert not (root/'artifacts'/'phase_a').exists()

def test_retry_driver_calls_recovery_before_public_artifact_writer():
    tree=ast.parse((HERE/'retry2_runner.py').read_text())
    calls=[(node.lineno,node.func.id) for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
    line=lambda name:min(n for n,k in calls if k==name)
    assert line('execute_phase_a')<line('write_recovery')<line('write_phase_a_artifact')

def test_corrupt_recovery_hash_rejected(tmp_path,synthetic):
    root=tmp_path/'repo';root.mkdir();directory=tmp_path/'private'
    write_recovery(directory,synthetic[0],'a'*64,'b'*40,root)
    p=directory/'recovery_snapshot.sha256';p.chmod(0o644);p.write_text('0'*64+'\n')
    with pytest.raises(GateError,match='SHA256'):read_recovery(directory)

def test_recovery_structure_and_semantics_reject_bad_fields(tmp_path,synthetic):
    root=tmp_path/'repo';root.mkdir();directory=tmp_path/'private'
    write_recovery(directory,synthetic[0],'a'*64,'b'*40,root)
    snapshot=read_recovery(directory)
    for key,value in [('prediction_freeze',True),('phase_b_input_permitted',True),('execution_attempt',3)]:
        changed=copy.deepcopy(snapshot);changed[key]=value
        with pytest.raises(GateError):validate_snapshot(changed)
