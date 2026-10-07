"""Scalar recovery first; public validation/write second. No science callback."""
import importlib.util
import json
from pathlib import Path
from a0_common import ROOT, canonical, sha
from run_lease import durable, read_start


def boundary():
    path = ROOT/'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py'
    spec = importlib.util.spec_from_file_location('fs_r1_a0_scalar_boundary', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save_return(lease, category, payload):
    # Scalar canonicalization is the private boundary, not public schema validation.
    native = boundary().json_native(payload)
    snapshot = dict(snapshot_kind='FS-R1-A0-private-scalar-recovery-v2', run_id=lease.run_id,
                    binding=lease.binding, RUN_STARTED_sha256=lease.start_sha256,
                    category=category, prediction_freeze=False, phase_B_input_permitted=False, payload=native)
    path = lease.directory/(category+'.recovery.json')
    raw = canonical(snapshot)
    durable(path, raw)
    durable(path.with_suffix(path.suffix+'.sha256'), (sha(raw)+'\n').encode())
    # This journal binds the snapshot digest; scientific callback is already gone.
    lease.note('recovery_saved', recovery_category=category, recovery_sha256=sha(raw),
               scientific_return_completed=True, recovery_saved=True)
    return path, sha(raw)


def load_return(path):
    path = Path(path)
    raw = path.read_bytes()
    digest = sha(raw)
    if digest != path.with_suffix(path.suffix+'.sha256').read_text().strip():
        raise ValueError('recovery hash mismatch')
    snapshot = json.loads(raw)
    if canonical(snapshot) != raw:
        raise ValueError('noncanonical recovery')
    start, start_hash = read_start(path.parent)
    if snapshot['binding'] != start['binding'] or snapshot['run_id'] != start['run_id'] or snapshot['RUN_STARTED_sha256'] != start_hash:
        raise ValueError('recovery lease/source/protocol binding mismatch')
    if snapshot.get('prediction_freeze') is not False or snapshot.get('phase_B_input_permitted') is not False:
        raise ValueError('recovery cannot authorize truth')
    events = [json.loads(p.read_text()) for p in sorted(path.parent.glob('event_*.json'))]
    if not any(e.get('recovery_category') == snapshot['category'] and e.get('recovery_sha256') == digest for e in events):
        raise ValueError('recovery not bound to lease journal')
    boundary().json_native(snapshot['payload'])
    payload = snapshot['payload']
    if isinstance(payload, dict):
        for key in ('protocol_sha256', 'execution_code_sha256', 'source_hashes'):
            if key in payload and payload[key] != start['binding'][key]:
                raise ValueError('payload/recovery identity mismatch')
    return snapshot, raw


def publish_from_recovery(path, public_path, validator):
    snapshot, raw = load_return(path)
    validator(snapshot['payload'])
    # Publish the exact payload bytes from the snapshot, with no refit/recompute.
    payload_raw = canonical(snapshot['payload'])
    public_path = Path(public_path)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    if public_path.exists():
        if public_path.read_bytes() != payload_raw:
            raise ValueError('existing public bytes differ from recovery')
    else:
        durable(public_path, payload_raw)
    if public_path.read_bytes() != payload_raw:
        raise ValueError('public/recovery bytes mismatch')
    return dict(public_sha256=sha(payload_raw), recovery_sha256=sha(raw), recovery_saved_before_public=True,
                public_matches_recovery=True, production_rerun=False)


def mark_publication_complete(lease, receipt):
    if (receipt.get('status') != 'PASS' or receipt.get('remote_fetched_independently') is not True
            or len(receipt.get('remote_verified_commit', '')) != 40):
        raise ValueError('independent committed publication proof required')
    return lease.note('publication_complete', state='completed', remote_verified_commit=receipt['remote_verified_commit'],
                      prediction_manifest_sha256=receipt['manifest_sha256'])
