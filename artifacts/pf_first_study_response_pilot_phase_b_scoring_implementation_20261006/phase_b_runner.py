"""One authorized Phase B intake/scoring; no new production science."""
from pathlib import Path
import argparse,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P06=ROOT/'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
sys.path.insert(0,str(P06));sys.path.insert(0,str(HERE))
from phase06_contract import canonical,sha,load_authorization,PROTOCOL_SHA,GateError
from phase_b_scoring import *

def exclusive(path,obj):
    raw=canonical(obj)
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--expected-base',required=True)
    args=parser.parse_args(argv)
    def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a])
    if git('rev-parse','HEAD').decode().strip()!=args.expected_base or git('status','--porcelain').strip():
        raise GateError('Phase B requires clean exact implementation base')
    if git('branch','--show-current').decode().strip()!='pf-first-study-response-pilot-h4-phase-b-20261006':
        raise GateError('Phase B branch identity mismatch')
    if args.output.exists() or args.runtime.exists():raise GateError('create-only output/runtime required')
    if args.runtime.resolve().is_relative_to(ROOT):raise GateError('private runtime outside repository required')
    record=json.loads(args.authorization.read_bytes())
    required={'phase':'phase-b','science_authorized':True,'phase_a_commit':A_COMMIT,
        'prediction_sha256':PRED_SHA,'strict_phase_a_sha256':PHASE_A_SHA,'protocol_sha256':PROTOCOL_SHA,
        'new_science_calculation_count_authorized':0,'saved_direct_truth_coordinates':12,
        'saved_exact_proxy_coordinates':22,'A3_reference_fits':3,'phase_a_modification_prohibited':True,
        'N2_CO_HF_extension_prohibited':True}
    if any(record.get(k)!=v for k,v in required.items()):raise GateError('Phase B authorization scope mismatch')
    auth=load_authorization(args.authorization,'phase-b')
    test_record=json.loads((HERE/'implementation_preflight.json').read_bytes())
    if not test_record['all_tests_passed']:raise GateError('tests have not passed before truth')
    for p in HERE.glob('phase_b_*.py'):
        path=str(p.relative_to(ROOT));raw=p.read_bytes()
        if sha(raw)!=test_record['code_files'][path] or raw!=git('show',args.expected_base+':'+path):
            raise GateError('uncommitted scoring code before truth')

    truth_open_permitted=[False];freeze_done=[False];reads=[];forbidden=[]
    def access_audit(event,items):
        if event!='open' or not isinstance(items[0],(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(items[0])).resolve();mode=items[1]
        reading=mode is None or 'r' in mode or '+' in mode
        if reading and path.is_relative_to(ROOT):
            rel=str(path.relative_to(ROOT))
            if path.suffix=='.csv' and not rel.startswith(A_DIR+'/'):
                if rel not in (BRANCH_CSV,EXACT_CSV) or not truth_open_permitted[0]:
                    forbidden.append(rel);raise PermissionError('unapproved CSV read before/after Phase A verification')
            if path.suffix in ('.npz','.npy','.pkl','.pickle') and freeze_done[0]:
                forbidden.append(rel);raise PermissionError('no production array access after identity freeze gate')
            reads.append(rel)
    sys.addaudithook(access_audit)
    args.runtime.mkdir(parents=True,exist_ok=False,mode=0o700)
    exclusive(args.runtime/'scoring_started.json',{'phase':'phase-b','base_commit':args.expected_base,
        'phase_a_commit':A_COMMIT,'authorization_sha256':auth.record_sha256,'saved_scalar_intake_count':1,
        'new_science_actions_authorized':0})
    schema=json.loads((P06/'phase_a_schema.json').read_bytes())
    before_pred=(ROOT/A_DIR/'predictions.json').read_bytes()
    before_phase=(ROOT/A_DIR/'phase_a.json').read_bytes()
    try:
        payload,freeze_audit=verify_all_phase_a(ROOT,schema)
    except BaseException as error:
        exclusive(args.runtime/'freeze_failure.json',{'status':'FAILED_PHASE_A_FREEZE_VERIFICATION',
            'error_type':type(error).__name__,'error':str(error),'saved_truth_access_count':0})
        raise
    freeze_done[0]=True
    args.output.mkdir(parents=True,exist_ok=False)
    exclusive(args.output/'phase_a_freeze_verification.json',freeze_audit)
    exclusive(args.output/'authorization_phase_b.json',record)
    # Only now permit the two fixed saved-truth files to the one scalar intake.
    truth_open_permitted[0]=True
    try:
        direct,exact,truth_audit=read_saved_truth_once(ROOT)
    finally:truth_open_permitted[0]=False
    original_payload=canonical(payload)
    with no_new_science(exact) as action_ledger:
        result=score_payload(payload,direct,exact,frozen_receipt(ROOT))
    if action_ledger['A3_reference_fits']!=3 or action_ledger['blocked_science_attempts']:
        raise GateError('Phase B action accounting mismatch')
    if canonical(payload)!=original_payload or (ROOT/A_DIR/'predictions.json').read_bytes()!=before_pred or (ROOT/A_DIR/'phase_a.json').read_bytes()!=before_phase:
        raise GateError('Phase A predictions/coefficients altered during scoring')
    trace=outcome_trace(payload,result)
    proxy_rows,bridge=proxy_rows_and_bridge(payload,exact,result)
    if forbidden:raise GateError('prohibited file access was attempted')
    bundle={'phase_a_payload':payload,'direct':{str(k):v for k,v in direct.items()},
        'exact':{str(k):v for k,v in exact.items()},'result':result,'outcome_trace':trace,
        'proxy_rows':proxy_rows,'mechanism_to_total_bridge':bridge,'truth_source_audit':truth_audit,
        'action_ledger':action_ledger,'file_read_audit':reads,'phase_a_prediction_unchanged':True,
        'scoring_code_identity':test_record['code_files'],'phase_a_freeze_verification':freeze_audit}
    exclusive(args.runtime/'saved_scoring_bundle.json',bundle)
    exclusive(args.runtime/'saved_scoring_bundle.sha256',{'sha256':sha((args.runtime/'saved_scoring_bundle.json').read_bytes())})
    print(json.dumps({'scoring_complete':True,'outcome':result['outcome'],
        'response_unique_tradeoff':trace['tradeoff']['response_unique_tradeoff'],
        'primary':{a:{key:result['arms'][a][key] for key in ('S_abs','S_under','E_max','point_S_abs','sign_crossing_count')} for a in ('A0','A1','A2')},
        'saved_direct_truth_coordinates':12,'saved_exact_proxy_coordinates':22,
        'A3_reference_fits':action_ledger['A3_reference_fits'],'new_science_action_count':0,
        'Phase_A_unchanged':True},indent=2))

if __name__=='__main__':main()
