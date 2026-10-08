"""Metadata/byte preflight only; does not create a science lease or decode arrays."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
A0 = ROOT/'artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008'
R0 = ROOT/'artifacts/pf_first_study_fs_r0_rebaseline_20261007'
BASE = '7a7234c9c5412c7209e3559aadfb71b30ad727fc'
PRIVATE = Path('/tmp/fs-r1-phase-a-execution-record-20261008')
REQUEST = Path('/home/abe/.codex/attachments/1baae85d-ab9a-41b1-b3fd-883793b000a6/貼り付けたテキスト.txt')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
def save(path, value):
    raw = value if isinstance(value,bytes) else canonical(value)
    with Path(path).open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    Path(path).chmod(0o400)
    fd=os.open(Path(path).parent,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def main():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('branch','--show-current').decode().strip()=='pf-first-study-fs-r1-phase-a-production-20261008'
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    # All inherited authority plus the complete A0 publication, independently
    # compared with actual committed blobs before loading any scientific data.
    paths={r['path'] for r in json.loads((A0/'source_manifest.json').read_text())['sources']}
    paths.update(r['path'] for r in json.loads((A0/'publication_manifest.json').read_text())['files'])
    paths.add(str((A0/'publication_manifest.json').relative_to(ROOT)))
    paths.add('artifacts/pf_first_study_fs_r1_phase_a_20261007/build_audit.py')
    records=[]
    for path in sorted(paths):
        raw=(ROOT/path).read_bytes()
        assert raw==git('show',BASE+':'+path), path
        records.append(dict(path=path,sha256=sha(raw),bytes=len(raw),
            git_blob_sha=git('rev-parse',BASE+':'+path).decode().strip(),
            origin_result_commit=git('log','-1','--format=%H',BASE,'--',path).decode().strip(),
            verified_snapshot_commit=BASE))
    sys.path.insert(0,str(A0))
    from a0_common import verify_frozen, require_authorization
    p,code=verify_frozen()
    protocol_hash=sha((A0/'fs_r1_protocol_v3.json').read_bytes())
    numerical_hash=sha((A0/'fs_r1_numerical_contract_v1.json').read_bytes())
    assert protocol_hash=='b1d37961484b212a6f2fab8b38092e56e640bac85c2369ab4cb29ba4ec383884'
    assert numerical_hash=='16067176e0d1b211c5c43bd85287741cc93719977a57b675d5e2547b84dae573'
    assert code=='abb832afdd8de951e005d3104d2f7e1644329d86612607b61820e1f15ec1d9e4'
    bundle=json.loads((A0/'execution_code_identity.json').read_text())['sha256']
    for path,digest in bundle.items():
        assert sha(git('show',BASE+':'+path))==digest
    prior=ROOT/'artifacts/pf_first_study_fs_r1_phase_a_20261007/build_audit.py'
    ms=importlib.util.spec_from_file_location('byte_preflight',prior)
    audit=importlib.util.module_from_spec(ms);ms.loader.exec_module(audit)
    audit.ROOT=ROOT; audit.BASE=BASE
    tree=ast.parse((R0/'source_io.py').read_text())
    meta_keys=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='META_KEYS' for t in n.targets))
    registry=json.loads((R0/'new_source_registry.json').read_text())['sources']
    identities=json.loads((R0/'new_source_identity.json').read_text())['identities']
    checks=[]
    for spec in p['systems']:
        record=next(r for r in registry if r['condition']==spec['condition'])
        identity=next(i for i in identities if i['condition']==spec['condition'])
        assert record['source_identity_sha256']==spec['source_identity_sha256']
        assert record['operational_archive_sha256']==spec['operational_archive_sha256']
        assert identity['hamiltonian_sha256']==spec['new_H_sha256']
        checks.append(audit.check_archive(record,identity,meta_keys))
    log=Path('/tmp/fs-r1-phase-a-production-tests-20261008.log').read_bytes()
    assert b'317 passed' in log and b'failed' not in log
    import numpy, scipy
    assert numpy.__version__=='1.26.4' and scipy.__version__=='1.14.1'
    threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}
    assert set(threads.values())=={'1'}
    free=shutil.disk_usage('/tmp').free
    memory={a.rstrip(':'):int(b)*1024 for a,b,*_ in (l.split() for l in Path('/proc/meminfo').read_text().splitlines()) if a in ('MemTotal:','MemAvailable:')}
    assert free>1024**3 and memory['MemAvailable']>1024**3
    PRIVATE.mkdir(mode=0o700,exist_ok=False)
    save(PRIVATE/'write_probe',b'private create-only fsync probe\n')
    auth=dict(explicit_science_authorization=True,phase='FS-R1-Phase-A',
        authorization_id='FS-R1-Phase-A-20261008-'+str(uuid.uuid4()),
        protocol_sha256=protocol_hash,execution_code_sha256=code,
        user_request_sha256=sha(REQUEST.read_bytes()),base_commit=BASE,
        source_hashes={s['condition']:{k:s[k] for k in ('source_identity_sha256','new_H_sha256','operational_archive_sha256')} for s in p['systems']},
        authorized_production_runs=1,Phase_B_authorized=False,new_direct_truth_coordinates=0)
    _,binding=require_authorization(auth)
    lease=Path(p['execution_wrapper']['private_lease_registry'])/sha(auth['authorization_id'].encode())
    assert not lease.exists() and not lease.resolve().is_relative_to(ROOT)
    save(PRIVATE/'authorization.json',auth)
    save(PRIVATE/'run_id.txt',b'FS-R1-Phase-A-production-20261008-once\n')
    save(HERE/'authorization_request.md',REQUEST.read_bytes())
    save(HERE/'tests.log',log)
    save(HERE/'source_manifest.json',dict(repository='HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae',
        base_verified_snapshot_commit=BASE,origin_and_snapshot_roles_separate=True,
        private_binary_publication=False,sources=records))
    save(HERE/'source_identity.json',dict(stage='pre_execution_identity_only',checks=checks,
        numeric_array_decodes=0,original_pickle_reads=0,private_binaries_published=False))
    save(HERE/'phase_a_protocol_snapshot.json',dict(protocol_id=p['protocol_id'],
        authority_path=str((A0/'fs_r1_protocol_v3.json').relative_to(ROOT)),
        protocol_sha256=protocol_hash,numerical_contract_sha256=numerical_hash,
        execution_code_bundle_sha256=code,origin_result_commit=BASE,verified_snapshot_commit=BASE,
        Phase_A_authorized_by_current_request=True,Phase_B_authorized=False,protocol=p))
    save(HERE/'preflight.json',dict(status='PASS',base_commit=BASE,git_blobs_verified=len(records),
        execution_bundle_members_verified=len(bundle),protocol_sha256=protocol_hash,
        numerical_contract_sha256=numerical_hash,execution_code_bundle_sha256=code,
        source_allowlists_and_oracle_absence_pass=True,source_checks=checks,
        authorization_binding=binding,science_lease_created=False,science_actions=0,
        tests_total=317,tests_pass=True,private_fsync_probe_pass=True,
        environment=dict(python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,
            threads=threads,available_disk_bytes=free,**memory,cgroup_limits='not exposed at conventional paths'),
        source_original_pickle_reads=0,new_direct_truth_coordinates=0,Phase_B_authorized=False))
    print(json.dumps(dict(status='PASS',tests=317,authority_blobs=len(records),authorization_id=auth['authorization_id'],lease_created=False)),flush=True)

if __name__=='__main__': main()
