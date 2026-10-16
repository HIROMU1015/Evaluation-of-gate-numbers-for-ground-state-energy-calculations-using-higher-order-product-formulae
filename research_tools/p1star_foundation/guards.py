"""Fail-closed readiness and bounded, allowlisted technical probes only."""
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time


@dataclass(frozen=True)
class Limits:
    jobs: int = 1
    cpu_processes: int = 1
    ram_bytes: int = 16 * 1024**3
    wall_seconds: int = 1800
    terms: int = 200_000
    output_bytes: int = 20 * 1024**2


CONTRACT_LIMITS = Limits()


class NotReady(RuntimeError):
    pass


class OutputLimitExceeded(RuntimeError):
    pass


class OutputBudget:
    """Aggregate bytes written through this owner, across multiple files."""

    def __init__(self, limit=CONTRACT_LIMITS.output_bytes):
        if type(limit) is not int or limit < 0:
            raise ValueError("nonnegative byte limit required")
        self.limit = limit
        self.used = 0
        self.stopped = False

    def write(self, stream, data):
        if not isinstance(data, bytes):
            raise TypeError("writer accepts encoded bytes only")
        if self.stopped or self.used + len(data) > self.limit:
            self.stopped = True
            raise OutputLimitExceeded("INCONCLUSIVE: aggregate output limit")
        # Charge before IO; a failed/partial write never creates extra budget.
        self.used += len(data)
        count = stream.write(data)
        if count != len(data):
            self.stopped = True
            raise OSError("incomplete output write")


class SingleJob:
    """Cooperative exclusive lock for launchers using the same path."""

    def __init__(self, path):
        self.path = Path(path)
        self.fd = None

    def __enter__(self):
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            self.fd = None
            raise NotReady("another job owns this launcher lock")
        return self

    def __exit__(self, *_):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class Deadline:
    def __init__(self, seconds, clock=time.monotonic):
        if seconds <= 0:
            raise ValueError("positive whole-job deadline required")
        self.clock = clock
        self.end = clock() + seconds

    def remaining(self):
        return max(0, self.end - self.clock())

    def check(self):
        if self.remaining() <= 0:
            raise TimeoutError("INCONCLUSIVE: whole-job deadline")


def resource_probe():
    """Read-only. Never create/modify a cgroup or contact a privileged service."""
    rows = Path('/proc/self/cgroup').read_text().splitlines()
    rel = next((r.split(':', 2)[2] for r in rows if r.startswith('0::')), None)
    leaf = Path('/sys/fs/cgroup') / rel.lstrip('/') if rel is not None else None
    result = {"cgroup_path":str(leaf) if leaf else None,
              "cpu_affinity":sorted(os.sched_getaffinity(0)),
              "limits":CONTRACT_LIMITS.__dict__, "cgroups_modified":False}
    for name in ('memory.max', 'memory.swap.max', 'pids.max', 'cgroup.controllers'):
        path = leaf/name if leaf else None
        try:
            result[name] = {"value":path.read_text().strip(),"writable":os.access(path,os.W_OK)}
        except (OSError, AttributeError) as error:
            result[name] = {"error":type(error).__name__}
    mounts = [line for line in Path('/proc/self/mountinfo').read_text().splitlines() if ' - cgroup2 ' in line]
    result['cgroup_mount_readonly'] = any('ro' in line.split()[5].split(',') for line in mounts)
    result['dedicated_cgroup_verified'] = False
    result['aggregate_16_GiB_limit_verified'] = False
    result['native_library_internal_terms_counted'] = False
    return result


def readiness():
    resource = resource_probe()
    reasons = []
    if not resource['dedicated_cgroup_verified'] or not resource['aggregate_16_GiB_limit_verified']:
        reasons.append('NO_VERIFIED_DEDICATED_16_GIB_JOB_LIMIT')
    if not resource['native_library_internal_terms_counted']:
        reasons.append('OPAQUE_NATIVE_AND_PYTHON_TEMPORARY_TERM_STORAGE')
    # Deliberately no override or science callback. This package is infrastructure.
    return {"status":"NOT_READY", "reasons":reasons, "resource_probe":resource,
            "science_authorized":False,"science_entrypoint_present":False,
            "contract_changed":False}


def require_phase_b_ready():
    report = readiness()
    raise NotReady('Phase B launch refused: '+','.join(report['reasons']))


def _kill_owned_group(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def run_technical_probe(fixture, directory, *, seconds=2, output_bytes=4096,
                        address_space_bytes=128 * 1024**2):
    """One allowlisted stdlib-only artificial worker, never arbitrary commands.

    RLIMIT_AS is intentionally labelled virtual address space, not RAM/cgroup.
    Supervisor is outside the worker. Tests use short, reduced artificial caps.
    """
    if fixture not in {'affinity','memory','wall','output'}:
        raise ValueError("not an allowlisted artificial fixture")
    directory = Path(directory)
    deadline = Deadline(seconds)
    cpus = sorted(os.sched_getaffinity(0))
    if not cpus:
        raise NotReady('no permitted CPU')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    root = str(Path(__file__).resolve().parents[1])
    env['PYTHONPATH'] = root
    command = [sys.executable,'-m','p1star_foundation._probe_worker',fixture,
               str(cpus[0]),str(address_space_bytes)]
    capture = bytearray()
    reason = 'EXITED'
    with SingleJob(directory/'technical-job.lock'):
        process = subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,start_new_session=True,env=env)
        try:
            with selectors.DefaultSelector() as select:
                select.register(process.stdout,selectors.EVENT_READ)
                while select.get_map():
                    if deadline.remaining() <= 0:
                        reason='WALL_LIMIT'; break
                    events=select.select(timeout=min(deadline.remaining(), 0.05))
                    for key, _ in events:
                        chunk=os.read(key.fileobj.fileno(),4096)
                        if not chunk:
                            select.unregister(key.fileobj); continue
                        if len(capture)+len(chunk)>output_bytes:
                            reason='OUTPUT_LIMIT'; break
                        capture.extend(chunk)
                    if reason=='OUTPUT_LIMIT': break
                if reason=='EXITED':
                    try:
                        process.wait(timeout=deadline.remaining())
                    except subprocess.TimeoutExpired:
                        reason='WALL_LIMIT'
        finally:
            _kill_owned_group(process)
            process.stdout.close()
    return {'fixture':fixture,'reason':reason,'returncode':process.returncode,
            'captured_bytes':len(capture),'output':capture.decode('utf-8',errors='replace'),
            'RAM_hard_limit_verified':False,'virtual_address_space_limit':address_space_bytes}


if __name__ == '__main__':
    # Diagnostic only: there is no --run-science option.
    if len(sys.argv) != 1:
        raise SystemExit('only read-only readiness diagnosis is available')
    print(json.dumps(readiness(),indent=2))
