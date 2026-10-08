"""Future v3 authorization -> real freeze barrier -> exclusive lease -> truth.

B0 preflight never calls execute_phase_b with a production authorization.
Synthetic orchestration can use only <=16-dimensional injected source fixtures.
"""
from dataclasses import dataclass,field
import json
import os
from pathlib import Path
import resource
import sys
import time
from b0_common import (ROOT,HERE,A0,SCIENCE,HANDOFF,PREDICTION,PROTOCOL,LADDER,CODE_A,sha,canonical,
    require_proof,verify_execution,read)
from v3_barrier import verify_phase_a
from v3_scoring import validate_ladders,score_frozen
from truth_recovery import save_snapshot,publish_saved

sys.path.insert(0,str(ROOT/A0))
from run_lease import RunLease,durable

def validate_authorization(authorization):
    a=authorization or {}
    if (a.get('explicit_science_authorization') is not True or a.get('phase')!='FS-R1-Phase-B' or
        a.get('request_stage')!='FS-R1-Phase-B-production' or not isinstance(a.get('authorization_id'),str) or not a['authorization_id'].strip()):
        raise PermissionError('B0 grants no production truth; separate Phase B approval required')
    if not isinstance(a.get('approval_reference'),str) or not a['approval_reference'].strip():raise PermissionError('separate Phase B approval reference required')
    contract=read(HERE/'phase_b_bridge_contract.json');code=verify_execution()
    expected=dict(protocol_sha256=PROTOCOL,prediction_sha256=PREDICTION,science_origin_commit=SCIENCE,
        handoff_commit=HANDOFF,handoff_proof_sha256=contract['handoff_proof_sha256'],
        phase_b_execution_code_sha256=code,branch_ladder_sha256=LADDER,
        source_hashes=contract['source_hashes'],truth_coordinate_budget=12)
    if any(a.get(k)!=v for k,v in expected.items()) or type(a.get('truth_coordinate_budget'))!=int:
        raise PermissionError('Phase B authorization must bind every frozen authority/budget')
    if a['authorization_id']==contract['consumed_phase_a_authorization_id']:raise PermissionError('consumed Phase A authorization cannot be reused')
    go=read(HERE/'GO_NO_GO_FOR_PHASE_B_PRODUCTION.json')
    if go.get('status')!='GO_FOR_FS_R1_PHASE_B_PRODUCTION' or go.get('tests_pass') is not True:
        raise PermissionError('B0 implementation/preflight GO required')
    return dict(authorization_id=a['authorization_id'],authorization_sha256=sha(canonical(a)),
        protocol_sha256=PROTOCOL,execution_code_sha256=code,source_hashes=expected['source_hashes'],
        prediction_sha256=PREDICTION,science_origin_commit=SCIENCE,handoff_commit=HANDOFF,
        handoff_proof_sha256=expected['handoff_proof_sha256'],branch_ladder_sha256=LADDER,
        truth_coordinate_budget=12,phase='FS-R1-Phase-B')

@dataclass
class TruthContext:
    proof: object
    phase: str='FS-R1-B0'
    authorization: dict|None=None
    counts: dict=field(default_factory=dict)
    wall_seconds: float=0.0

    def guard(self,dimension=None):
        require_proof(self.proof)
        if self.phase=='synthetic':
            if dimension is not None and (type(dimension)!=int or not 1<=dimension<=16):
                raise PermissionError('synthetic truth limited to <=16 dimensions')
            return
        if self.phase!='FS-R1-Phase-B':raise PermissionError('B0 production truth dispatch forbidden')
        binding=validate_authorization(self.authorization)
        data=require_proof(self.proof)
        if data['remote_receipt_sha256']!=binding['handoff_proof_sha256'] or data['source_hashes']!=binding['source_hashes']:
            raise PermissionError('authorized v3 proof binding mismatch')
        if dimension is not None and dimension!=1568:raise PermissionError('fixed production sector dimension')

    def add(self,name,count=1):
        self.guard();self.counts[name]=self.counts.get(name,0)+count

    def snapshot(self):
        import numpy,scipy
        return dict(cost_class='truth_validation_cost',logical_actions=self.counts.copy(),
            wall_seconds=self.wall_seconds,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            GPU_memory_bytes=None,internal_work=dict(PF_kernel=None,Schur_internal=None,status='unknown'),
            attempted_coordinates=self.counts.get('truth_coordinate_attempt',0),
            completed_coordinates=self.counts.get('truth_coordinate_completed',0),
            threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            software=dict(python=sys.version.split()[0],numpy=numpy.__version__,scipy=scipy.__version__),
            synthetic=self.phase=='synthetic',QPE_addition=False)

def execute_verified(proof,context,registry,run_id,binding,public_path,*,loader=None,builder=None,public_validator=None):
    context.guard();data=require_proof(proof);p=data['protocol']
    if context.proof.digest!=proof.digest:raise PermissionError('context proof mismatch')
    if context.phase!='synthetic' and (loader is not None or builder is not None):raise PermissionError('production callbacks cannot replace frozen kernels')
    frozen_registry=Path(read(HERE/'phase_b_bridge_contract.json')['private_truth_lease_registry'])
    if context.phase=='synthetic':
        if binding.get('phase')!='synthetic' or Path(registry).resolve()==frozen_registry.resolve():
            raise PermissionError('synthetic lease cannot consume production authorization/registry')
    elif (Path(registry).resolve()!=frozen_registry.resolve() or binding!=validate_authorization(context.authorization)):
        raise PermissionError('fixed authorization-keyed truth lease required')
    # Synthetic seams are unavailable at the production entrypoint.
    from truth_adapter import load_source,unitary,checkpoint,previous
    import numpy as np
    sys.path.insert(0,str(ROOT/'artifacts/pf_first_study_fs_r01_branch_extension_20261007'))
    from branch_math import solve_point
    acquire=loader or load_source;construct=builder or unitary
    lease=RunLease(registry,run_id,binding)
    rows=[];final_path=None;started=time.perf_counter()
    try:
        for spec,ladder in zip(p['systems'],data['branch_ladder']['systems']):
            if spec['condition']!=ladder['condition'] or len(ladder['times'])!=6:raise ValueError('fixed ladder condition mismatch')
            source=acquire(spec,proof,context);n=source['hamiltonian'].shape[0];context.guard(n)
            if source['source_identity_sha256']!=spec['source_identity_sha256']:raise ValueError('truth source namespace mismatch')
            prior_meta=None
            for index,t in enumerate(ladder['times']):
                prior=None if index==0 else previous(prior_meta,spec['source_identity_sha256'],index-1,
                    ladder['times'][index-1],proof,context,lease)
                attempt=len(rows)+1
                if attempt>12:raise ValueError('extra truth coordinate')
                context.add('truth_coordinate_attempt')
                durable(lease.directory/f'attempt_{attempt:02d}.json',canonical(dict(condition=spec['condition'],
                    time=t,time_hex=float(t).hex(),index=index,binding=binding,RUN_STARTED_sha256=lease.start_sha256)))
                tick=time.perf_counter();U=construct(source,t,proof,context)
                context.guard(U.shape[0])
                row,vector=solve_point(U,source['exact_ground'],source['exact_energy'],t,spec['source_identity_sha256'],index,context,prior)
                row.update(condition=spec['condition'],time_role='primary_scoring' if index==5 else 'branch_certification',
                    execution_provenance='FS-R1-v3-new-source-direct',phase_a_prediction_sha256=PREDICTION,
                    phase_a_proof_sha256=proof.digest,Phase_B_execution_code_sha256=binding['execution_code_sha256'],
                    synthetic_truth_fixture=context.phase=='synthetic',wall_seconds=time.perf_counter()-tick,
                    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_memory_bytes=None)
                # Immediate durable scalar return before checkpoint or public schema.
                save_snapshot(lease,f'coordinate_{attempt:02d}',row)
                prior_meta=checkpoint(lease.directory/f'vector_{attempt:02d}.npy',vector,row,proof,context,lease)
                row['selected_vector_checkpoint']=prior_meta;rows.append(row)
                context.add('truth_coordinate_completed')
                del U,vector,prior
            del source
        validate_ladders(rows,proof)
        context.wall_seconds=time.perf_counter()-started
        output=dict(status='BRANCH_CERTIFICATION_PASS',rows=rows,truth_attempts=12,primary_scoring_endpoints=2,
            truth_validation_cost=context.snapshot(),prediction_sha256=PREDICTION,
            phase_a_proof_sha256=proof.digest,phase_B_execution_code_sha256=binding['execution_code_sha256'],
            synthetic=context.phase=='synthetic',resource_outcome=score_frozen(proof,rows))
        final_path=save_snapshot(lease,'truth_complete',output)
        lease.note('science_return_completed',state='completed')
        def validator(payload):
            validate_ladders(payload['rows'],proof)
            if payload['resource_outcome']!=score_frozen(proof,payload['rows']):raise ValueError('saved scoring mismatch')
            if public_validator is not None:public_validator(payload)
        try:receipt=publish_saved(final_path,public_path,validator)
        except Exception as error:
            lease.note('public_serialization_failed',state='completed',error_type=type(error).__name__,error=str(error));raise
        lease.note('public_serialization_completed',state='completed')
        return dict(payload=output,receipt=receipt,lease_directory=str(lease.directory),private_recovery=str(final_path))
    except Exception as error:
        if final_path is None:
            context.wall_seconds=time.perf_counter()-started
            lease.note('truth_calculation_failed',state='failed',error_type=type(error).__name__,error=str(error),
                attempted_coordinates=context.counts.get('truth_coordinate_attempt',0),completed_coordinates=len(rows),
                further_truth_forbidden=True,technical_failure=True,truth_validation_cost=context.snapshot())
        raise

def execute_phase_b(authorization,run_id,public_path):
    binding=validate_authorization(authorization) # Before freeze access or lease.
    proof=verify_phase_a()
    context=TruthContext(proof,phase='FS-R1-Phase-B',authorization=authorization)
    context.guard()
    registry=Path(read(HERE/'phase_b_bridge_contract.json')['private_truth_lease_registry'])
    if registry.resolve().is_relative_to(ROOT):raise ValueError('private truth lease/checkpoints must stay outside repository')
    return execute_verified(proof,context,registry,run_id,binding,public_path)

def preflight_phase_b():
    # Actual committed scalars/hash/recovery only. No authorization, lease, or
    # truth-only helper import/callback/source decode follows this boundary.
    proof=verify_phase_a()
    return dict(status='VERIFIED_STOPPED_BEFORE_TRUTH_ONLY_BOUNDARY',proof_sha256=proof.digest,
        source_hashes=proof.data['source_hashes'],truth_source_opens=0,oracle_decode=0,
        production_lease_created=False,Phase_B_authorized=False)
