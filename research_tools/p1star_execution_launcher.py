"""Bounded IO/OS receipt for an explicitly approved P1star science CLI attempt.

No scientific expressions are generated here. Every invocation is one-shot;
technical recovery uses a separately recorded attempt, never deletes markers.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


def identity(path):
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def process_start(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]
    except FileNotFoundError:return None


def descendants(pid):
    found=[]
    try:children=(Path('/proc')/str(pid)/'task'/str(pid)/'children').read_text().split()
    except FileNotFoundError:return found
    for value in children:
        child=int(value);found.append(child);found.extend(descendants(child))
    return found


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',required=True)
    parser.add_argument('--python',required=True)
    parser.add_argument('--source-root',required=True)
    args=parser.parse_args()
    plan_path=Path(args.plan).resolve();plan=json.loads(plan_path.read_text())
    if plan['approval']['explicit_user_approval'] is not True or not plan['approval']['approval_reference']:
        raise RuntimeError('real explicit execution approval required')
    run=Path(plan['freeze_metadata']['result_directory'])
    result_path=run/'result.json';stderr_path=run/'controller_stderr.log'
    receipt_path=run/'run_receipt.json'
    for path in (result_path,stderr_path,receipt_path):
        if path.exists():raise FileExistsError('never overwrite an earlier attempt: '+str(path))
    env=dict(os.environ,**plan['freeze_metadata']['launch_environment'])
    env['PYTHONPATH']=str(Path(args.source_root).resolve()/'research_tools')
    command=[args.python,'-m','p1star_driver.science','--approved-plan',str(plan_path)]
    started=time.monotonic();start_utc=datetime.now(timezone.utc).isoformat()
    owned={};reason=None;counts={'stdout':0,'stderr':0}
    caps={'stdout':plan['settings']['output_bytes'],'stderr':256*1024}
    ceiling=plan['settings']['wall_seconds']+60
    with result_path.open('xb') as out,stderr_path.open('xb') as err:
        process=subprocess.Popen(command,cwd=args.source_root,env=env,stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        owned[process.pid]=process_start(process.pid)
        try:
            with selectors.DefaultSelector() as select:
                select.register(process.stdout,selectors.EVENT_READ,('stdout',out))
                select.register(process.stderr,selectors.EVENT_READ,('stderr',err))
                while select.get_map():
                    for pid in descendants(process.pid):owned.setdefault(pid,process_start(pid))
                    if time.monotonic()-started>ceiling:reason='OUTER_WALL_LIMIT';break
                    for key,_ in select.select(.05):
                        name,stream=key.data;chunk=os.read(key.fileobj.fileno(),8192)
                        if not chunk:select.unregister(key.fileobj);continue
                        remaining=caps[name]-counts[name]
                        if len(chunk)>remaining:
                            stream.write(chunk[:remaining]);counts[name]+=remaining
                            reason='OUTER_'+name.upper()+'_LIMIT';break
                        stream.write(chunk);counts[name]+=len(chunk)
                    if reason:break
        finally:
            if reason or process.poll() is None:
                for pid,stamp in reversed(list(owned.items())):
                    if stamp is not None and process_start(pid)==stamp:
                        try:os.kill(pid,signal.SIGKILL)
                        except ProcessLookupError:pass
            process.wait(timeout=10);process.stdout.close();process.stderr.close()
    payload=None
    try:payload=json.loads(result_path.read_text())
    except (ValueError,UnicodeError):reason=reason or 'NO_VALID_RESULT_JSON'
    survivors=[pid for pid,stamp in owned.items() if stamp is not None and process_start(pid)==stamp]
    receipt={'start_UTC':start_utc,'end_UTC':datetime.now(timezone.utc).isoformat(),
             'elapsed_seconds':time.monotonic()-started,'run_id':plan['approval']['run_id'],
             'plan':identity(plan_path),'command':command,'source_root':args.source_root,
             'returncode':process.returncode,'outer_stop_reason':reason,
             'status':'INCONCLUSIVE' if reason else (payload or {}).get('status','INCONCLUSIVE'),
             'result':identity(result_path),'stderr':identity(stderr_path),
             'owned_processes':owned,'survivors':survivors,'outer_wall_seconds':ceiling,
             'one_shot_launcher':True,'prior_attempts_overwritten':False}
    data=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
    if len(data)>768*1024:raise RuntimeError('receipt budget exhausted')
    receipt_path.write_bytes(data)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
