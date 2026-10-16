"""One worker, cooperative lock, wall/RSS/output monitoring and optional AS cap.

No cgroup claims. RSS polling can overshoot. RLIMIT_AS is virtual address space.
"""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from p1star_foundation.guards import Deadline, SingleJob


def validate_settings(settings):
    # No real-science defaults: all settings must be frozen in later approval.
    for key in ('wall_seconds','rss_bytes','address_space_bytes','output_bytes',
                'terms','trace_events','solver_timeout_ms'):
        if type(settings.get(key)) is not int or settings[key]<=0:raise ValueError('explicit positive setting required: '+key)
    recovery_cap=settings.get('technical_recovery_terms_cap',200000)
    if type(recovery_cap) is not int or not 200000<=recovery_cap<=2000000:
        raise ValueError('bounded technical recovery cap must be 200000..2000000')
    if settings['terms']>recovery_cap:raise ValueError('managed TermLedger cap exceeds explicitly frozen cap')
    if settings['output_bytes']<512:raise ValueError('at least 512 output bytes needed for stop record')
    if settings['output_bytes']>20*1024**2:raise ValueError('managed output cap cannot exceed 20 MiB')
    if settings.get('solver_rlimit') is not None and (type(settings['solver_rlimit']) is not int or settings['solver_rlimit']<=0):
        raise ValueError('invalid solver rlimit')


def worker_limits(cpu,address_space_bytes):
    import resource
    os.sched_setaffinity(0,{cpu})
    resource.setrlimit(resource.RLIMIT_AS,(address_space_bytes,address_space_bytes))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def rss(pid):
    try:
        text=Path('/proc')/str(pid)/'status'
        return int(next(line.split()[1] for line in text.read_text().splitlines() if line.startswith('VmRSS:')))*1024
    except (FileNotFoundError,ProcessLookupError,StopIteration):return 0


def supervise(arguments,directory,settings):
    """Internal argv, not shell. Call only with driver worker or toy probe args."""
    validate_settings(settings)
    deadline=Deadline(settings['wall_seconds']);peak=0;capture=bytearray();reason=None
    cpu=min(os.sched_getaffinity(0))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
             MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',SYMPY_GROUND_TYPES='python',
             PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    command=[sys.executable,'-m','p1star_driver._worker',str(cpu),str(settings['address_space_bytes']),*arguments]
    started=time.monotonic()
    with SingleJob(Path(directory)/'p1star-science-job.lock'):
        process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                 start_new_session=True,env=env)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while selector.get_map():
                    if not deadline.remaining():reason='WALL_LIMIT';break
                    resident=rss(process.pid);peak=max(peak,resident)
                    if resident>settings['rss_bytes']:reason='RSS_MONITOR_THRESHOLD';break
                    for key,_ in selector.select(min(.02,deadline.remaining())):
                        chunk=os.read(key.fileobj.fileno(),8192)
                        if not chunk:selector.unregister(key.fileobj);continue
                        if len(capture)+len(chunk)>settings['output_bytes']:
                            reason='OUTPUT_LIMIT';break
                        capture.extend(chunk)
                    if reason:break
                if reason is None:
                    try:process.wait(timeout=max(.001,deadline.remaining()))
                    except subprocess.TimeoutExpired:reason='WALL_LIMIT'
        finally:
            # This worker never spawns children. Kill its owned process group on failure.
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            process.wait(timeout=5);process.stdout.close()
    if reason is None and process.returncode:reason='ABNORMAL_EXIT'
    payload=None
    if reason is None:
        try:payload=json.loads(capture)
        except (ValueError,UnicodeError):reason='INVALID_WORKER_OUTPUT'
    return {'status':'INCONCLUSIVE' if reason else payload.get('status','INCONCLUSIVE'),
            'stop_reason':reason,'worker':payload,'returncode':process.returncode,
            'captured_bytes':len(capture),'captured_sha256':__import__('hashlib').sha256(capture).hexdigest(),
            'sampled_worker_RSS_peak':peak,'elapsed_seconds':time.monotonic()-started,
            'operating_settings':settings,'worker_cpu':cpu,'math_workers':1,
            'dedicated_RAM_hard_limit_verified':False,'native_terms_counted':False,
            'monitor_scope':'one in-process worker; sampled RSS may overshoot; supervisor memory excluded; RLIMIT_AS virtual address space'}
