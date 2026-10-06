"""One approved H4 Phase A execution using immutable Phase0.6 kernels.

This wrapper adds read/import guards and scalar observations only. It does not
modify the frozen science routines, thresholds, coordinates, or accounting.
"""
from pathlib import Path
import argparse,hashlib,importlib.abc,json,os,subprocess,sys,zipfile

BASE06='6fae17723f888a62a998f90436516785a67651c6'
P06='artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
P05='artifacts/pf_first_study_response_pilot_phase05_20261006'
REPO='HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--private-output',type=Path,required=True)
    parser.add_argument('--attempt-record',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve();package=root/P06
    def git(*a):return subprocess.check_output(['git','-C',str(root),*a])
    assert git('rev-parse','HEAD').decode().strip()==BASE06
    assert not git('status','--porcelain').strip()
    assert not args.output.exists() and not args.private_output.exists()
    for a in [('remote','get-url','origin'),('remote','get-url','--push','origin')]:
        assert git(*a).decode().strip() in (f'git@github.com:{REPO}.git',f'https://github.com/{REPO}.git')

    reads=[];blocked=[]
    def audit(event,items):
        if event!='open' or not isinstance(items[0],(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(items[0])).resolve()
        mode=items[1]
        reading=mode is None or 'r' in mode or '+' in mode
        if not reading:return
        if path.is_relative_to(root):
            relative=str(path.relative_to(root))
            if path.suffix=='.csv' and not path.is_relative_to(args.output.resolve()):
                blocked.append(relative);raise PermissionError('Phase A prohibits production truth CSV access')
            reads.append(relative)
    sys.addaudithook(audit)
    class NoPhaseB(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname in ('phase06_phase_b','phase05_phase_b'):
                raise ImportError('Phase B import prohibited in approved Phase A execution')
    sys.meta_path.insert(0,NoPhaseB())
    sys.path.insert(0,str(package))
    import numpy as np
    from phase06_contract import load_contract,load_authorization,ExecutionContext,sha,canonical,expected_counts
    from phase06_inputs import load_phase_a_inputs
    from phase06_freeze import verify_committed_code,validate_artifact,write_phase_a_artifact
    from phase06_phase_a import execute_phase_a

    contract=load_contract(root)
    record=json.loads(args.authorization.read_bytes())
    assert record['repository']==REPO and record['base_commit']==BASE06
    assert record['phase']=='phase-a' and record['truth_access_prohibited'] is True
    assert record['scope']['system']=='H4' and record['scope']['PF']=='current_m3' and record['scope']['state']=='CISD'
    assert record['scope']['signed_coordinates']==[s*t for t in (.1,.15,.2,.25,.3,.125,.175,.225,.275,.35,.4) for s in (1,-1)]
    assert record['phase_b_authorized'] is False
    authorization=load_authorization(args.authorization,'phase-a')
    manifest=json.loads((package/'publication_manifest.json').read_bytes())
    for item in manifest['files']:
        raw=(root/item['path']).read_bytes()
        assert sha(raw)==item['sha256'] and len(raw)==item['bytes']
        assert git('show',BASE06+':'+item['path'])==raw
    code=verify_committed_code(root,package)
    preflight=json.loads((package/'preflight_protocol.json').read_bytes())
    assert code==preflight['code_files_sha256']
    assert contract.protocol_sha256==record['protocol_sha256']
    schema=json.loads((package/'phase_a_schema.json').read_bytes())

    members=[];original_open=zipfile.ZipFile.open
    allowed={key+'.npy' for key in contract.identity['phase_a_array_allowlist']}
    def guarded_member(archive,name,mode='r',*a,**kw):
        key=name.filename if hasattr(name,'filename') else name
        if mode=='r':
            if key not in allowed:raise PermissionError('Forbidden production NPZ member decode')
            members.append(key)
        return original_open(archive,name,mode,*a,**kw)
    zipfile.ZipFile.open=guarded_member
    data=load_phase_a_inputs(root,contract)
    old=json.loads((package/'production_source_identity.json').read_bytes())
    assert canonical(data.identity_audit)==canonical(old['observed_identity_audit'])
    assert data.metadata==old['molecular_metadata']
    assert contract.protocol['formula_definition']==old['current_m3']
    assert len(members)==15 and set(members)==allowed
    context=ExecutionContext('production',authorization)
    observations=[]
    def observe(frame,event,result):
        if event=='return' and frame.f_code.co_name=='_one_pass' and frame.f_code.co_filename==str(package/'phase06_phase_a.py') and result is not None:
            observations.append({'pass':len(observations)+1,'H_spectral_norm':result.H_norm,
                'E_psi':result.basis.energy,'initial_state_residual_norm':float(np.linalg.norm(result.basis.r)),
                'actual_rank':result.basis.Z.shape[1],'prefix_stopped':result.basis.stopped,
                'source_numeric_gates_passed':True,
                'maximum_PF_unitarity_residual':max(result.backend.unitarity.values()),
                'counter_snapshot':context.counts.copy()})
    # Exclusive attempt marker prevents accidental extra scientific execution.
    with args.attempt_record.open('x') as f:
        json.dump({'phase':'phase-a','base_commit':BASE06,'authorization_sha256':sha(args.authorization.read_bytes()),
            'driver_sha256':sha(Path(__file__).read_bytes()),'execution_attempt':1,'additional_science_rerun_authorized':False},f,indent=2)
    sys.setprofile(observe)
    try:
        payload,private=execute_phase_a(data,contract,context,code)
    except BaseException as error:
        sys.setprofile(None)
        with args.attempt_record.with_name('failed_execution.json').open('x') as f:
            json.dump({'status':'PHASE_A_FAILED','error_type':type(error).__name__,'error':str(error),
                'actual_counters':context.counts,'predictions_frozen':False},f,indent=2)
        raise
    finally:sys.setprofile(None)
    assert len(observations)==2 and 'phase06_phase_b' not in sys.modules
    assert context.counts==expected_counts(payload['basis']['actual_rank'],payload['basis']['status']=='prefix_stopped')
    validate_artifact(payload,schema)
    write_phase_a_artifact(args.output,payload,schema,private,args.private_output)
    scalar_audit={'base_commit':BASE06,'driver_sha256':sha(Path(__file__).read_bytes()),
        'passes':observations,'repository_paths_read':sorted(set(reads)),
        'production_truth_csv_reads':[],'blocked_csv_access_attempts':blocked,
        'production_npz_members_opened':members,'phase_b_imported':False,'phase_b_executed':False,
        'saved_direct_truth_access_count':0,'saved_exact_proxy_access_count':0,
        'execution_attempts':1,'science_reruns_beyond_frozen_cold_replay':0}
    with (args.private_output/'execution_audit.json').open('x') as f:json.dump(scalar_audit,f,indent=2,allow_nan=False)
    print(json.dumps({'Phase_A_executed':True,'actual_rank':payload['basis']['actual_rank'],
        'residual_converged':payload['residual_convergence']['converged'],
        'primary_fit_status':{a:payload['fits'][a]['raw_positive_even_two_term']['status'] for a in ('A0','A1','A2')},
        'actual_actions':context.counts,'phase_a_sha256':sha((args.output/'phase_a.json').read_bytes()),
        'saved_truth_access_count':0,'Phase_B_executed':False},indent=2))

if __name__=='__main__':main()
