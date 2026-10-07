"""Complete future Phase B executor. FS-R0.1 cannot dispatch production truth.

Only an actual committed Phase A barrier proof plus separate science approval
opens the private original source. No historical lookup or adaptive coordinates.
"""
import io
import json
import pickle
from pathlib import Path
import resource
import sys
import time
import numpy as np
from r01_common import ROOT,R0,read,protocol,sha,canonical,ladder_for,source_io,v1_backend
from branch_math import fail,normalized,solve_point,validate_branch_id,BranchFailure

def gate(proof,context,dimension=None):
    if context.phase not in ('synthetic','FS-R1-Phase-B'):raise PermissionError('truth-only Phase B required')
    context.guard(dimension)
    if proof.get('verified') is not True or proof.get('protocol_sha256')!=sha((Path(__file__).parent/'fs_r1_protocol_v2.json').read_bytes()):
        raise PermissionError('verified frozen v2 Phase A proof required')

def load_truth_source(spec,proof,context):
    """Oracle access only after barrier. No regeneration or exact-state solve."""
    gate(proof,context,spec['dimension'])
    if spec not in proof['protocol']['systems']:fail('source identity mismatch')
    records=json.loads((R0/'new_source_registry.json').read_text())['sources']
    record=next(r for r in records if r['condition']==spec['condition'])
    if record['source_identity_sha256']!=spec['source_identity_sha256']:fail('source identity mismatch')
    identity=next(i for i in json.loads((R0/'new_source_identity.json').read_text())['identities'] if i['condition']==spec['condition'])
    if sha(canonical(identity))!=spec['source_identity_sha256']:fail('frozen source identity SHA mismatch')
    if record['private_original_whole_sha256']!=identity['private_original_whole_SHA']:fail('frozen truth-only whole SHA mismatch')
    if record['operational_archive_sha256']!=spec['operational_archive_sha256']:fail('frozen operational archive SHA mismatch')
    start=time.perf_counter()
    raw=Path(record['private_original_path']).read_bytes()
    if sha(raw)!=record['private_original_whole_sha256']:fail('truth-only source whole SHA mismatch')
    sys.path.insert(0,str(ROOT/'src'))
    decoded=pickle.loads(raw);system=decoded['system'];metadata=decoded['metadata']
    if source_io.sparse_hash(system['hamiltonian'])!=spec['new_H_sha256']:fail('truth H SHA mismatch')
    source=source_io.load_operational(record['operational_archive_path'],spec['operational_archive_sha256'],v1_backend.native())
    if source_io.sparse_hash(source['hamiltonian'])!=spec['new_H_sha256'] or source['current_m3_sequence']!=proof['protocol']['current_m3_sequence']:
        fail('truth/operational H or PF mismatch')
    if source_io.array_identity(system['restricted_basis'])['sha256']!=identity['restricted_basis']['sha256']:
        fail('truth sector/basis mismatch')
    if sha(canonical({k:metadata[k] for k in source_io.META_KEYS}))!=identity['sector_metadata_sha256']:fail('truth sector/origin/group mismatch')
    ground=normalized(system['state'],spec['dimension']).copy()
    energy=float(system['energy'])
    if not np.isfinite(energy):fail('nonfinite exact-ground energy')
    # Keep full original bytes bound to C0.6, but do not solve a new H ground
    # state. E is the original H-without-removed-constant energy convention.
    source.update(exact_ground=ground,exact_energy=energy,source_identity_sha256=spec['source_identity_sha256'])
    context.add('truth_only_source_load');context.wall_seconds+=time.perf_counter()-start
    return source

def native_unitary(source,t,proof,context):
    n=source['hamiltonian'].shape[0];gate(proof,context,n)
    if source['current_m3_sequence']!=proof['protocol']['current_m3_sequence']:fail('fixed current_m3 changed')
    ns=v1_backend.native()
    # Native left-product action on all identity columns = full U_P(t), +i sign.
    # Matrix/block work is truth-validation cost, not Phase A vector PF cost.
    U,timing=ns['_apply_pf_cpu'](source,source['current_m3_sequence'],t,np.eye(n,dtype=np.complex128))
    steps=list(ns['iter_s2_sequence_steps'](len(source['component_spectra']),source['current_m3_sequence']))
    context.add('PF_unitary_construction');context.add('PF_identity_block_action')
    context.add('truth_group_matrix_application',len(steps));context.add('truth_group_materialization',len(set(steps)))
    context.wall_seconds+=timing['total']
    return np.asarray(U,dtype=np.complex128)

def save_checkpoint(path,vector,row,context):
    context.guard(len(vector));vector=normalized(vector,len(vector))
    path=Path(path);buf=io.BytesIO();np.save(buf,vector,allow_pickle=False);raw=buf.getvalue()
    source_io.durable_create(path,raw)
    metadata=dict(private_path=str(path),sha256=sha(raw),source_identity_sha256=row['source_identity_sha256'],
        time=row['time'],index=row['index'],branch_id=row['selected_branch_id'],dimension=len(vector),dtype=vector.dtype.str)
    source_io.durable_create(path.with_suffix('.json'),canonical(metadata))
    context.add('selected_vector_checkpoint')
    return metadata

def load_checkpoint(metadata,source,index,time_value,context):
    context.guard(metadata['dimension'])
    if metadata['source_identity_sha256']!=source or metadata['index']!=index or float(metadata['time']).hex()!=float(time_value).hex():fail('prior checkpoint identity/time mismatch')
    validate_branch_id(metadata['branch_id'],source,index)
    path=Path(metadata['private_path'])
    if not path.is_file():fail('missing prior checkpoint')
    raw=path.read_bytes()
    if sha(raw)!=metadata['sha256']:fail('prior vector SHA mismatch')
    if json.loads(path.with_suffix('.json').read_text())!=metadata:fail('prior checkpoint metadata mismatch')
    vector=normalized(np.load(io.BytesIO(raw),allow_pickle=False),metadata['dimension'])
    return dict(vector=vector,source_identity_sha256=source,index=index,time=float(time_value),branch_id=metadata['branch_id'])

def save_scalar_recovery(path,payload):
    raw=canonical(payload);path=Path(path)
    source_io.durable_create(path,raw)
    source_io.durable_create(path.with_suffix(path.suffix+'.sha256'),(sha(raw)+'\n').encode())

def execute_truth(proof,context,private_run_directory,loader=load_truth_source,builder=native_unitary):
    gate(proof,context)
    p=proof['protocol']
    if p!=protocol():fail('frozen v2 protocol mismatch')
    directory=Path(private_run_directory);directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    # Exclusive lease makes an automatic rerun/rescue after science or public
    # serialization failure impossible. Recovery reads scalars/checkpoints only.
    source_io.durable_create(directory/'RUN_STARTED.json',canonical(dict(protocol_sha256=proof['protocol_sha256'],
        prediction_sha256=proof['prediction_sha256'],phase_a_commit=proof['phase_a_commit'],truth_limit=12)))
    rows=[];attempts=0
    try:
        for spec in p['systems']:
            ladder=ladder_for(spec['condition']);source=loader(spec,proof,context);previous_meta=None
            for index,t in enumerate(ladder['times']):
                previous=None
                if index:
                    if previous_meta is None:fail('missing prior checkpoint')
                    previous=load_checkpoint(previous_meta,spec['source_identity_sha256'],index-1,ladder['times'][index-1],context)
                attempts+=1
                if attempts>12:fail('extra coordinate')
                source_io.durable_create(directory/f'attempt_{attempts:02d}.json',canonical(dict(condition=spec['condition'],time=t,index=index)))
                start=time.perf_counter();U=builder(source,t,proof,context)
                row,vector=solve_point(U,source['exact_ground'],source['exact_energy'],t,spec['source_identity_sha256'],index,context,previous)
                row.update(condition=spec['condition'],time_role='primary_scoring' if index==5 else 'branch_certification',
                    wall_seconds=time.perf_counter()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    GPU_memory_bytes=None,prediction_sha256=proof['prediction_sha256'])
                # Durable scalar recovery before checkpoint/public validation.
                save_scalar_recovery(directory/f'scalar_{attempts:02d}.json',row)
                previous_meta=save_checkpoint(directory/f'vector_{attempts:02d}.npy',vector,row,context)
                row['selected_vector_checkpoint']=previous_meta;rows.append(row)
                del U,vector,previous
            del source
        from scoring_bridge import validate_ladders
        validate_ladders(rows,p)
        output=dict(status='BRANCH_CERTIFICATION_PASS',synthetic=context.phase=='synthetic',rows=rows,
            primary_scored_values=2,truth_attempts=attempts,truth_validation_cost=context.snapshot(),
            prediction_sha256=proof['prediction_sha256'],no_resource_outcome_computed=True)
        save_scalar_recovery(directory/'truth_scalar_recovery.json',output)
        return output
    except Exception as error:
        source_io.durable_create(directory/'FAILED.json',canonical(dict(status='BRANCH_CONTINUATION_FAILED',reason=str(error),
            truth_attempts=attempts,completed_points=len(rows),further_truth_forbidden=True,technical_failure=True)))
        raise

def publish_recovered(private_recovery_path,public_path,validator):
    """Serialization-only recovery. Never calls PF, Schur, source load or fit."""
    raw=Path(private_recovery_path).read_bytes();payload=json.loads(raw)
    if sha(raw)!=Path(str(private_recovery_path)+'.sha256').read_text().strip():raise ValueError('truth recovery SHA mismatch')
    if canonical(payload)!=raw:raise ValueError('noncanonical truth scalar recovery')
    validator(payload)
    source_io.durable_create(public_path,raw)
    return dict(sha256=sha(raw),science_rerun=False)
