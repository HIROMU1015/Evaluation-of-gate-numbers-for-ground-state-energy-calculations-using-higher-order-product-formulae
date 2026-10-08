"""Create-only, lease-bound scalar recovery and serialization-only publication."""
import json
from pathlib import Path
import sys
from b0_common import ROOT,A0,sha,canonical

sys.path.insert(0,str(ROOT/A0))
from run_lease import durable,read_start

def scalar_boundary(value):
    import importlib.util
    path=ROOT/'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py'
    spec=importlib.util.spec_from_file_location('b0_scalar_boundary',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def reject(x):
        if isinstance(x,dict):
            if set(x)&{'exact_ground','exact_energy','state_vector','ground','energy','oracle_source'}:
                raise ValueError('private oracle/vector in truth scalar recovery')
            for v in x.values():reject(v)
        elif isinstance(x,(list,tuple)):
            for v in x:reject(v)
    reject(value)
    return module.json_native(value)

def save_snapshot(lease,category,payload):
    snapshot=dict(format='FS-R1-v3-Phase-B-scalar-recovery-v1',category=category,
        run_id=lease.run_id,RUN_STARTED_sha256=lease.start_sha256,binding=lease.binding,
        payload=scalar_boundary(payload),science_retry_permitted=False)
    raw=canonical(snapshot);path=lease.directory/(category+'.recovery.json')
    durable(path,raw);durable(Path(str(path)+'.sha256'),(sha(raw)+'\n').encode())
    lease.note('recovery_saved',recovery_category=category,recovery_sha256=sha(raw),scientific_return_completed=True)
    return path

def load_snapshot(path):
    path=Path(path);raw=path.read_bytes()
    if sha(raw)!=Path(str(path)+'.sha256').read_text().strip():raise ValueError('truth recovery SHA mismatch')
    snapshot=json.loads(raw);start,start_hash=read_start(path.parent)
    if (canonical(snapshot)!=raw or snapshot['RUN_STARTED_sha256']!=start_hash or
        snapshot['binding']!=start['binding'] or snapshot['run_id']!=start['run_id'] or snapshot['science_retry_permitted'] is not False):
        raise ValueError('truth recovery binding mismatch')
    events=[json.loads(p.read_text()) for p in sorted(path.parent.glob('event_*.json'))]
    if not any(e.get('recovery_category')==snapshot['category'] and e.get('recovery_sha256')==sha(raw) for e in events):
        raise ValueError('truth recovery journal mismatch')
    scalar_boundary(snapshot['payload'])
    return snapshot

def publish_saved(path,public_path,validator):
    snapshot=load_snapshot(path);payload=snapshot['payload']
    validator(payload)
    raw=canonical(payload);public_path=Path(public_path)
    public_path.parent.mkdir(parents=True,exist_ok=True)
    if public_path.exists():
        if public_path.read_bytes()!=raw:raise ValueError('existing public truth bytes mismatch')
    else:durable(public_path,raw)
    return dict(public_sha256=sha(raw),private_recovery_sha256=sha(Path(path).read_bytes()),science_rerun=False)
