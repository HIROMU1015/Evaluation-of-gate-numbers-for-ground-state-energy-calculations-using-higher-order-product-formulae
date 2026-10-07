"""Frozen metadata and byte identities only; imports no science/truth loader."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R0 = ROOT / 'artifacts/pf_first_study_fs_r0_rebaseline_20261007'
R01 = ROOT / 'artifacts/pf_first_study_fs_r01_branch_extension_20261007'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def read(name):
    return json.loads((HERE / name).read_text())


def protocol():
    return read('fs_r1_protocol_v3.json')


def spec_for(condition):
    return next(s for s in protocol()['systems'] if s['condition'] == condition)


def execution_paths():
    own = ('a0_common.py', 'numerical_contract.py', 'run_lease.py', 'recovery_wrapper.py',
           'phase_a_wrapper.py', 'production_adapter.py')
    inherited = [R0/n for n in ('backend.py', 'source_io.py', 'implementation_pins.json',
                 'fs_r1_protocol.json', 'new_source_identity.json', 'new_source_registry.json')]
    pins = ROOT/'artifacts/pf_first_study_fs_c05_execution_closure_20261007/native_source_pins.json'
    inherited += [pins, ROOT/'artifacts/pf_first_study_fs_c05_execution_closure_20261007/closure_adapter.py',
                  ROOT/'artifacts/pf_first_study_response_pilot_phase05_20261006/phase05_math.py',
                  ROOT/'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py']
    inherited += [ROOT/r['path'] for r in json.loads(pins.read_text())['sources']]
    return sorted(str(p.relative_to(ROOT)) for p in [*(HERE/n for n in own), *inherited])


def verify_frozen():
    p = protocol()
    for field in ('numerical_contract', 'fit_uncertainty_propagation'):
        record = p[field]
        if sha((ROOT / record['path']).read_bytes()) != record['sha256']:
            raise ValueError('changed ' + field)
    bundle = read('execution_code_identity.json')
    if set(bundle['sha256']) != set(execution_paths()):
        raise ValueError('incomplete execution code/config bundle')
    for path, expected in bundle['sha256'].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('changed execution code: ' + path)
    if bundle['format'] != 'FS-R1-A0-execution-code-v1':
        raise ValueError('execution bundle format')
    return p, sha(canonical(bundle))


def require_authorization(authorization):
    p, code_hash = verify_frozen()
    a = authorization or {}
    if (a.get('explicit_science_authorization') is not True or
            a.get('phase') != 'FS-R1-Phase-A' or
            not isinstance(a.get('authorization_id'), str) or not a['authorization_id'].strip()):
        raise PermissionError('separate Phase A production authorization required; A0 authorizes no science')
    if a.get('protocol_sha256') != sha((HERE / 'fs_r1_protocol_v3.json').read_bytes()):
        raise PermissionError('authorization must bind the actual v3 protocol')
    if a.get('execution_code_sha256') != code_hash:
        raise PermissionError('authorization must bind the complete execution code bundle')
    go = read('GO_NO_GO_FOR_PHASE_A_PRODUCTION.json')
    if go.get('status') != 'GO_FOR_FS_R1_PHASE_A_PRODUCTION' or go.get('tests_pass') is not True:
        raise PermissionError('numerical-contract/wrapper preflight must pass before production')
    binding = dict(authorization_id=a['authorization_id'], authorization_sha256=sha(canonical(a)),
                   protocol_sha256=a['protocol_sha256'], execution_code_sha256=code_hash,
                   source_hashes={s['condition']: {k: s[k] for k in
                       ('source_identity_sha256', 'new_H_sha256', 'operational_archive_sha256')} for s in p['systems']})
    return p, binding
