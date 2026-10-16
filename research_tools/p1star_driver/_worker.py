"""Internal single process worker. Artificial probes have a separate allowlist."""
import json
import os
from pathlib import Path
import sys
import time

from .authorization import sha256
from .practical import worker_limits


def main():
    cpu,address_space=int(sys.argv[1]),int(sys.argv[2])
    worker_limits(cpu,address_space)
    kind=sys.argv[3]
    if kind=='probe':
        fixture=sys.argv[4]
        if fixture=='sleep':time.sleep(10)
        elif fixture=='abnormal':os._exit(19)
        elif fixture=='rss':
            blob=bytearray(32*1024**2)
            time.sleep(2)
            del blob
        elif fixture=='as':
            blob=bytearray(256*1024**2)
            del blob
        elif fixture=='output':
            sys.stdout.write('x'*16384);sys.stdout.flush()
        elif fixture=='affinity':
            print(json.dumps({'status':'ARTIFICIAL_PASS','affinity':sorted(os.sched_getaffinity(0))}))
        elif fixture=='pipeline':
            from .fixtures import rectangle_fixture, toy_settings
            from .pipeline import run_pipeline
            print(json.dumps(run_pipeline(rectangle_fixture(),toy_settings()),separators=(',',':')))
        else:raise ValueError('unknown artificial worker fixture')
    elif kind=='science':
        plan_bytes=Path(sys.argv[4]).read_bytes()
        if sha256(plan_bytes)!=sys.argv[5]:raise ValueError('plan changed after preflight')
        plan=json.loads(plan_bytes)
        if plan['settings']['address_space_bytes']!=address_space:raise ValueError('worker AS setting mismatch')
        from .science import execute_approved_worker
        print(json.dumps(execute_approved_worker(plan),separators=(',',':')))
    else:raise ValueError('explicit science or artificial probe required')


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'INCONCLUSIVE','reason':type(error).__name__+': '+str(error)}))
