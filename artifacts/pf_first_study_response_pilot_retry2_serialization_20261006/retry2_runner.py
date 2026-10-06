"""Attempt 2 only: frozen science, recovery persistence, normalized public write."""
from pathlib import Path
import argparse,importlib.abc,json,os,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P06='artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
BASE1='3d7a923f2a8d11aff57a05454eca8e142496833e'
BRANCH='pf-first-study-response-pilot-h4-phase-a-retry2-20261006'
REPO='HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--expected-base',required=True)
    args=parser.parse_args(argv)
    def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a])
    assert git('rev-parse','HEAD').decode().strip()==args.expected_base
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert not git('status','--porcelain').strip()
    assert not args.runtime.exists() and not args.output.exists()
    assert not args.runtime.resolve().is_relative_to(ROOT)
    assert args.output.resolve().is_relative_to(ROOT/'artifacts')
    assert args.output.name.startswith('pf_first_study_response_pilot_phase_a_')
    for a in [('remote','get-url','origin'),('remote','get-url','--push','origin')]:
        assert git(*a).decode().strip() in (f'git@github.com:{REPO}.git',f'https://github.com/{REPO}.git')

    reads=[];blocked=[]
    def file_audit(event,items):
        if event!='open' or not isinstance(items[0],(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(items[0])).resolve();mode=items[1]
        reading=mode is None or 'r' in mode or '+' in mode
        if reading and path.is_relative_to(ROOT):
            rel=str(path.relative_to(ROOT))
            if path.suffix=='.csv' and not path.is_relative_to(args.output.resolve()):
                blocked.append(rel);raise PermissionError('production truth CSV read prohibited')
            reads.append(rel)
    sys.addaudithook(file_audit)
    class NoPhaseB(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname in ('phase06_phase_b','phase05_phase_b'):
                raise ImportError('Phase B import prohibited during Phase A retry')
    sys.meta_path.insert(0,NoPhaseB())
    package=ROOT/P06;sys.path.insert(0,str(package));sys.path.insert(0,str(HERE))
    import numpy as np
    from phase06_contract import load_contract,load_authorization,ExecutionContext,sha,canonical,expected_counts
    from phase06_inputs import load_phase_a_inputs
    from phase06_freeze import verify_committed_code,write_phase_a_artifact
    from phase06_phase_a import execute_phase_a
    from retry2_boundary import write_recovery,read_recovery,to_json_native,exclusive_bytes
    from retry2_preflight import collect

    preflight=json.loads((HERE/'serialization_preflight.json').read_bytes())
    assert preflight['status']=='passed' and preflight['science_action_count']==0
    assert preflight['tests']['all_passed'] and preflight['hard_gates']['recovery_synthetic_test_passed']
    # Immutable code+schema bytes, including this orchestration patch, before science.
    code=verify_committed_code(ROOT,package)
    for p in sorted(HERE.glob('retry2_*.py')):
        path=str(p.relative_to(ROOT));raw=p.read_bytes()
        assert git('show',args.expected_base+':'+path)==raw
        assert preflight['retry_code_files_sha256'][path]==sha(raw)
        code[path]=sha(raw)
    assert preflight['phase06_code_sha256']==verify_committed_code(ROOT,package)
    contract=load_contract(ROOT)
    current=collect() # identity-only normalization gate repeated before science
    assert current['source_sha256_after']==preflight['source_sha256_after']
    record=json.loads(args.authorization.read_bytes())
    assert record['repository']==REPO and record['base_commit']==args.expected_base
    assert record['phase']=='phase-a' and record['execution_attempt']==2
    assert record['retry_kind']=='technical_retry' and record['technical_retry_reason']=='serialization_artifact_boundary'
    assert record['previous_attempt_commit']==BASE1 and record['previous_prediction_freeze'] is False
    assert record['previous_truth_access']==0 and record['science_specification_unchanged'] is True
    assert record['allowed_science_reruns']==1 and record['complete_cold_replay']==1
    assert record['phase_b_authorized'] is False and record['truth_access_prohibited'] is True
    assert record['scope']=={'system':'H4','state':'CISD','PF':'current_m3',
        'm_values':[1,2,4,8],'primary_m':8,'signed_coordinates':[s*t for t in (.1,.15,.2,.25,.3,.125,.175,.225,.275,.35,.4) for s in (1,-1)]}
    authorization=load_authorization(args.authorization,'phase-a')
    schema=json.loads((package/'phase_a_schema.json').read_bytes())
    members=[];original_open=zipfile.ZipFile.open
    allowed={key+'.npy' for key in contract.identity['phase_a_array_allowlist']}
    def guarded_open(archive,name,mode='r',*a,**kw):
        key=name.filename if hasattr(name,'filename') else name
        if mode=='r':
            if key not in allowed:raise PermissionError('forbidden NPZ member')
            members.append(key)
        return original_open(archive,name,mode,*a,**kw)
    zipfile.ZipFile.open=guarded_open
    data=load_phase_a_inputs(ROOT,contract)
    assert sha(canonical(data.identity_audit))==preflight['source_sha256_after']
    assert members==preflight['identity']['members_opened']
    context=ExecutionContext('production',authorization);observations=[]
    def observe(frame,event,result):
        if event=='return' and frame.f_code.co_name=='_one_pass' and frame.f_code.co_filename==str(package/'phase06_phase_a.py') and result is not None:
            observations.append({'pass':len(observations)+1,'H_spectral_norm':result.H_norm,
                'E_psi':result.basis.energy,'initial_state_residual_norm':float(np.linalg.norm(result.basis.r)),
                'actual_rank':result.basis.Z.shape[1],'prefix_stopped':result.basis.stopped,
                'source_numeric_gates_passed':True,'counter_snapshot':context.counts.copy()})
    # Runtime directory is an exclusive attempt marker; no Attempt 3/resume science path.
    args.runtime.mkdir(parents=True,exist_ok=False,mode=0o700)
    exclusive_bytes(args.runtime/'execution_started.json',canonical({'execution_attempt':2,
        'allowed_science_reruns':1,'complete_cold_replay':1,'base_commit':args.expected_base,
        'authorization_sha256':sha(args.authorization.read_bytes()),'retry_code_sha256':sha(canonical(code))}))
    sys.setprofile(observe)
    try:
        payload,private=execute_phase_a(data,contract,context,code)
    except BaseException as error:
        sys.setprofile(None)
        exclusive_bytes(args.runtime/'failed_execution.json',canonical({'status':'PHASE_A_FAILED',
            'error_type':type(error).__name__,'error':str(error),'actual_counters':context.counts,
            'predictions_frozen':False,'additional_science_attempts_authorized':0}))
        raise
    finally:sys.setprofile(None)
    # FIRST operation on returned science outputs: durable private scalar snapshot.
    recovery_audit=write_recovery(args.runtime/'recovery',payload,sha(args.authorization.read_bytes()),args.expected_base,ROOT)
    native=read_recovery(args.runtime/'recovery')['payload']
    audit={'execution_attempt':2,'retry_kind':'technical_retry','execution_base_commit':args.expected_base,
        'passes':observations,'repository_paths_read':sorted(set(reads)),
        'production_npz_members_opened':members,'production_truth_csv_reads':[],
        'blocked_csv_access_attempts':blocked,'saved_direct_truth_access_count':0,'saved_exact_proxy_access_count':0,
        'phase_b_imported':'phase06_phase_b' in sys.modules,'phase_b_executed':False,
        'science_execution_count':1,'complete_cold_replay_count':1,'additional_science_execution_count':0,
        'recovery_snapshot_audit':recovery_audit,'serialization_preflight_rechecked':True}
    exclusive_bytes(args.runtime/'execution_audit.json',canonical(to_json_native(audit)))
    assert len(observations)==2 and not audit['phase_b_imported'] and not blocked
    assert context.counts==expected_counts(native['basis']['actual_rank'],native['basis']['status']=='prefix_stopped')
    try:
        write_phase_a_artifact(args.output,native,schema,private,args.runtime/'projected_diagnostics')
    except BaseException as error:
        exclusive_bytes(args.runtime/'failed_public_artifact.json',canonical({'status':'PHASE_A_FAILED',
            'error_type':type(error).__name__,'error':str(error),'recovery_snapshot_valid':True,
            'science_reexecution_permitted':False,'snapshot_sha256':recovery_audit['sha256']}))
        raise
    exclusive_bytes(args.runtime/'public_artifact_written.json',canonical({'phase_a_sha256':sha((args.output/'phase_a.json').read_bytes()),
        'recovery_snapshot_valid':True,'predictions_frozen_to_Git':False,'Phase_B_executed':False}))
    print(json.dumps({'attempt':2,'science_execution_count':1,'complete_cold_replays':1,
        'actual_rank':native['basis']['actual_rank'],'prefix_stop':native['basis']['status']=='prefix_stopped',
        'residual_converged':native['residual_convergence']['converged'],
        'primary_fit_status':{a:native['fits'][a]['raw_positive_even_two_term']['status'] for a in ('A0','A1','A2')},
        'actual_actions':native['cost']['actions'],'recovery_snapshot_valid':True,
        'phase_a_sha256':sha((args.output/'phase_a.json').read_bytes()),
        'saved_truth_access_count':0,'Phase_B_executed':False},indent=2))

if __name__=='__main__':main()
