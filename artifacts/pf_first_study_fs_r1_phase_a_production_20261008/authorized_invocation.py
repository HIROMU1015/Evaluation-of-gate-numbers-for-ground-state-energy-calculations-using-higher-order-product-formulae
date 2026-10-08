"""Single invocation of the frozen entrypoint; no scientific implementation.

The create-only launch marker prevents accidental second invocation even before
the frozen authorization-keyed lease is reached. Never rerun this file.
"""
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
A0=ROOT/'artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008'
PRIVATE=Path('/tmp/fs-r1-phase-a-execution-record-20261008')
sys.path.insert(0,str(A0))
from a0_common import canonical, sha, verify_frozen
from run_lease import durable

def main():
    preflight=json.loads((HERE/'preflight.json').read_text())
    assert preflight['status']=='PASS' and preflight['tests_total']==317
    auth=json.loads((PRIVATE/'authorization.json').read_text())
    assert sha(canonical(auth))==preflight['authorization_binding']['authorization_sha256']
    verify_frozen()
    run_id=(PRIVATE/'run_id.txt').read_text().strip()
    durable(PRIVATE/'ENTRYPOINT_INVOCATION_STARTED',canonical(dict(run_id=run_id,
        authorization_id=auth['authorization_id'],entrypoint='phase_a_wrapper.execute_phase_a')))
    observed=dict(sanitized_archive_opens={},original_pickle_opens=0,truth_module_source_opens=0)
    # Observe Python open events without changing execution or science arithmetic.
    def observer(event,args):
        if event!='open' or not args or not isinstance(args[0],(str,bytes,os.PathLike)): return
        path=os.fsdecode(args[0])
        if '/tmp/fs-r0-operational-private-20261007/' in path and path.endswith('/source.npz'):
            condition=Path(path).parent.name
            observed['sanitized_archive_opens'][condition]=observed['sanitized_archive_opens'].get(condition,0)+1
        if path.endswith(('.pkl','.pickle')): observed['original_pickle_opens']+=1
        if path.endswith(('/truth_only.py','/truth_executor.py','/scoring_bridge.py')):
            observed['truth_module_source_opens']+=1
    sys.addaudithook(observer)
    from phase_a_wrapper import execute_phase_a
    started=time.perf_counter()
    print(json.dumps(dict(stage='calling_frozen_entrypoint_once',run_id=run_id)),flush=True)
    try:
        result=execute_phase_a(auth,run_id,HERE/'production_results.json')
    except Exception as exc:
        outcome=dict(success=False,error_type=type(exc).__name__,error=str(exc),
            traceback=traceback.format_exc(),partial_action_ledger=getattr(exc,'partial_action_ledger',None))
    else:
        outcome=dict(success=True,result=result)
    outcome.update(run_id=run_id,authorization_id=auth['authorization_id'],
        total_entrypoint_wall_seconds=time.perf_counter()-started,
        process_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        observed_open_events=observed,entrypoint_invocations=1,science_retries=0)
    durable(PRIVATE/'invocation_outcome.json',canonical(outcome))
    print(json.dumps({k:v for k,v in outcome.items() if k not in ('result','traceback')}),flush=True)
    if not outcome['success']: raise SystemExit(1)

if __name__=='__main__': main()
