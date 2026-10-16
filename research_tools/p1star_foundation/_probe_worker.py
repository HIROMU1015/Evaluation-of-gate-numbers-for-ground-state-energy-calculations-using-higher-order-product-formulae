"""Allowlisted artificial OS guard fixtures. No scientific library imports."""
import json
import os
import resource
import signal
import sys
import time


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in {'affinity','memory','wall','output'}:
        raise SystemExit('artificial fixture only')
    fixture, cpu, address_space = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    os.sched_setaffinity(0,{cpu})
    resource.setrlimit(resource.RLIMIT_AS,(address_space,address_space))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    # Child-only hard NPROC cap; never changes limits of the parent or user peers.
    resource.setrlimit(resource.RLIMIT_NPROC,(1,1))
    if fixture == 'affinity':
        fork_blocked = False
        try:
            pid = os.fork()
        except OSError:
            fork_blocked = True
        else:
            if pid == 0:
                os._exit(0)
            os.waitpid(pid,0)
        print(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),
                          'threads':len(os.listdir('/proc/self/task')),
                          'RLIMIT_AS':list(resource.getrlimit(resource.RLIMIT_AS)),
                          'fork_blocked_for_worker':fork_blocked}))
    elif fixture == 'memory':
        try:
            oversized = bytearray(address_space * 2)
        except MemoryError:
            print('EXPECTED_MEMORY_ERROR_FROM_RLIMIT_AS')
        else:
            raise RuntimeError('virtual-address allocation cap failed')
    elif fixture == 'wall':
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        time.sleep(10)
    elif fixture == 'output':
        while True:
            os.write(1,b'x' * 4096)


if __name__ == '__main__':
    main()
