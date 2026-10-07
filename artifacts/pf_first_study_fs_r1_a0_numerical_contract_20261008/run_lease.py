"""Create-only authorization-keyed lease and durable stage journal."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from a0_common import canonical, sha


def durable(path, raw):
    path = Path(path)
    with path.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    path.chmod(0o400)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def metadata():
    return dict(timestamp_UTC=datetime.now(timezone.utc).isoformat(), process_id=os.getpid(), hostname=socket.gethostname())


class RunLease:
    def __init__(self, registry, run_id, binding):
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError('nonempty run ID required')
        registry = Path(registry)
        registry.mkdir(mode=0o700, parents=True, exist_ok=True)
        # run ID is deliberately excluded: changing it cannot reuse authorization.
        self.directory = registry / sha(binding['authorization_id'].encode())
        self.directory.mkdir(mode=0o700, exist_ok=False)
        fd = os.open(registry, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        self.binding, self.run_id, self.sequence = binding, run_id, 0
        self.state = 'started'
        start = dict(kind='RUN_STARTED', state='started', stage='calculation_started', run_id=run_id,
                     binding=binding, **metadata())
        durable(self.directory/'RUN_STARTED', canonical(start))
        self.start_sha256 = sha(canonical(start))

    def note(self, stage, state=None, **details):
        if state is not None:
            if state not in ('started', 'completed', 'failed') or (self.state in ('completed', 'failed') and state == 'started'):
                raise ValueError('lease state transition')
            self.state = state
        self.sequence += 1
        event = dict(kind='RUN_STAGE', state=self.state, stage=stage, run_id=self.run_id,
                     RUN_STARTED_sha256=self.start_sha256, binding=self.binding, **metadata(), **details)
        durable(self.directory/f'event_{self.sequence:03d}.json', canonical(event))
        return event


def read_start(directory):
    raw = (Path(directory)/'RUN_STARTED').read_bytes()
    start = json.loads(raw)
    if canonical(start) != raw or start.get('kind') != 'RUN_STARTED':
        raise ValueError('invalid immutable lease')
    return start, sha(raw)
