"""JSON-native scalar metadata and create-only private recovery boundary.

No science kernels or truth readers are imported here. Normalization is pure:
it preserves values, insertion order, and canonical identity bytes.
"""
from pathlib import Path
import json,math,os
import numpy as np
from phase06_contract import GateError,canonical,sha,PROTOCOL_SHA

def to_json_native(value):
    if isinstance(value,Path):return str(value)
    if isinstance(value,np.generic):return to_json_native(value.item())
    if isinstance(value,np.ndarray):
        # Metadata vectors only; complex arrays and matrices are not scalar metadata.
        if value.ndim>1 or value.dtype.kind not in 'biufUS':
            raise GateError('nonmetadata array rejected at scalar boundary')
        return to_json_native(value.tolist())
    if value is None or isinstance(value,(str,bool,int)):return value
    if isinstance(value,float):
        if not math.isfinite(value):raise GateError('nonfinite JSON scalar')
        return value
    if isinstance(value,(tuple,list)):return [to_json_native(v) for v in value]
    if isinstance(value,dict):
        if not all(isinstance(k,str) for k in value):raise GateError('JSON object keys must be strings')
        return {k:to_json_native(v) for k,v in value.items()}
    raise GateError('unsupported scalar metadata type: '+type(value).__name__)

def normalize_payload(payload):
    # Do not invent identities or round/reshape science values.
    before=canonical(payload)
    native=to_json_native(payload)
    if canonical(native)!=before:raise GateError('normalization changed canonical scalar payload')
    if sha(canonical(native['source']['input_array_identities']))!=native['source']['source_sha256']:
        raise GateError('source identity changed at serialization boundary')
    return native

FORBIDDEN_KEYS={'exact_state','exact_proxy','direct_shift','direct_truth','total_error',
    'underestimation','outcome','controlled_state','ground_energy','H4_exact_state',
    'H4_ground_energy','L_m_complex_pairs','a_m_complex_pairs'}
PAYLOAD_KEYS={'schema_version','input_domain','source','basis','rows','fits','predictions',
    'residual_convergence','cost','replay','runtime'}

def _reject_forbidden(value):
    if isinstance(value,dict):
        if set(value)&FORBIDDEN_KEYS:raise GateError('truth/private matrix field in recovery scalar snapshot')
        for v in value.values():_reject_forbidden(v)
    elif isinstance(value,list):
        for v in value:_reject_forbidden(v)

def validate_snapshot(snapshot):
    if set(snapshot)!={'snapshot_kind','phase_b_input_permitted','prediction_freeze',
        'execution_attempt','provenance','payload'}:raise GateError('recovery structure mismatch')
    if snapshot['snapshot_kind']!='private_phase_a_scalar_recovery_v1' or snapshot['execution_attempt']!=2:
        raise GateError('recovery type/attempt mismatch')
    if snapshot['phase_b_input_permitted'] is not False or snapshot['prediction_freeze'] is not False:
        raise GateError('recovery cannot substitute for public prediction freeze')
    payload=snapshot['payload'];provenance=snapshot['provenance']
    if set(payload)!=PAYLOAD_KEYS:raise GateError('recovery payload structure mismatch')
    if set(provenance)!={'protocol_sha256','code_sha256','source_sha256','authorization_sha256','execution_base_commit'}:
        raise GateError('recovery provenance structure mismatch')
    for key in ('protocol_sha256','code_sha256','source_sha256'):
        if provenance[key]!=payload['source'][key]:raise GateError('recovery identity mismatch')
    if provenance['protocol_sha256']!=PROTOCOL_SHA:raise GateError('recovery normative protocol changed')
    if sha(canonical(payload['source']['code_files']))!=provenance['code_sha256']:
        raise GateError('recovery code hash mismatch')
    if sha(canonical(payload['source']['input_array_identities']))!=provenance['source_sha256']:
        raise GateError('recovery source hash mismatch')
    if len(payload['rows'])!=22 or len(payload['fits'])!=9 or any(len(v)!=12 for v in payload['predictions'].values()):
        raise GateError('recovery fixed scalar row counts mismatch')
    _reject_forbidden(snapshot)
    canonical(snapshot)

def exclusive_bytes(path,raw):
    path=Path(path)
    with path.open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    path.chmod(0o444)

def write_recovery(directory,payload,authorization_sha256,execution_base_commit,repository_root):
    directory=Path(directory)
    if directory.resolve().is_relative_to(Path(repository_root).resolve()):
        raise GateError('recovery must remain outside repository')
    if directory.exists():raise GateError('immutable recovery directory already exists')
    native=normalize_payload(payload)
    snapshot={'snapshot_kind':'private_phase_a_scalar_recovery_v1','phase_b_input_permitted':False,
        'prediction_freeze':False,'execution_attempt':2,
        'provenance':{**{key:native['source'][key] for key in ('protocol_sha256','code_sha256','source_sha256')},
            'authorization_sha256':authorization_sha256,'execution_base_commit':execution_base_commit},
        'payload':native}
    validate_snapshot(snapshot)
    directory.mkdir(parents=True,exist_ok=False,mode=0o700)
    raw=canonical(snapshot);digest=sha(raw)
    exclusive_bytes(directory/'recovery_snapshot.json',raw)
    exclusive_bytes(directory/'recovery_snapshot.sha256',(digest+'\n').encode())
    # On-disk revalidation happens before returning to any public artifact writer.
    checked=read_recovery(directory)
    if canonical(checked)!=raw:raise GateError('recovery roundtrip changed bytes')
    return {'recovery_snapshot_valid':True,'sha256':digest,'bytes':len(raw),
        'create_only':True,'read_only_files':True,'fsync_completed':True,
        'saved_before_public_validation':True,'contains_truth':False,
        'phase_b_input_permitted':False,'prediction_freeze_substitute':False}

def read_recovery(directory):
    directory=Path(directory);raw=(directory/'recovery_snapshot.json').read_bytes()
    if sha(raw)!=(directory/'recovery_snapshot.sha256').read_text().strip():
        raise GateError('recovery snapshot SHA256 mismatch')
    parsed=json.loads(raw);validate_snapshot(parsed)
    if canonical(parsed)!=raw:raise GateError('recovery noncanonical bytes')
    return parsed

def persist_then_write(payload,private,recovery_dir,public_dir,private_diagnostics_dir,
                       schema,authorization_sha256,execution_base_commit,repository_root,writer=None):
    # The first operation after science returns persists the complete scalar payload.
    audit=write_recovery(recovery_dir,payload,authorization_sha256,execution_base_commit,repository_root)
    native=read_recovery(recovery_dir)['payload']
    if writer is None:
        from phase06_freeze import write_phase_a_artifact
        writer=write_phase_a_artifact
    writer(public_dir,native,schema,private,private_diagnostics_dir)
    return native,audit
