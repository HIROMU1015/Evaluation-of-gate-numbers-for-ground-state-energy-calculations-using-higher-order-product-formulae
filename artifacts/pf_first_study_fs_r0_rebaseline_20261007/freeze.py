"""Commit/blob/hash/remote barrier before any new-source truth callback."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from source_io import durable_create, canonical

REQUIRED=('prediction','protocol','source_identity','code')

def execution_code_paths():
    from backend import HERE,ROOT
    core=[str((HERE/n).relative_to(ROOT)) for n in ('backend.py','source_io.py','scorer.py','freeze.py','truth_only.py')]
    pins=json.loads((HERE/'implementation_pins.json').read_text())
    native_pins=ROOT/'artifacts/pf_first_study_fs_c05_execution_closure_20261007/native_source_pins.json'
    return sorted(set(core+[str(native_pins.relative_to(ROOT)),str((HERE/'implementation_pins.json').relative_to(ROOT)),
        'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py']+
        [v['path'] for v in pins.values()]+[v['path'] for v in json.loads(native_pins.read_text())['sources']]))

def git_blob(root,commit,path):
    return subprocess.check_output(['git','show',commit+':'+path],cwd=root,stderr=subprocess.DEVNULL)

def verify_phase_a(root,commit,manifest_path,manifest_sha,remote_receipt,reader=None):
    if not re.fullmatch('[0-9a-f]{40}',commit): raise ValueError('full Phase A commit required')
    raw=git_blob(root,commit,manifest_path)
    if hashlib.sha256(raw).hexdigest()!=manifest_sha or (Path(root)/manifest_path).read_bytes()!=raw:
        raise ValueError('Phase A manifest changed')
    manifest=json.loads(raw)
    if manifest.get('stage')!='FS-R1-Phase-A' or manifest.get('truth_opened') is not False:
        raise ValueError('Phase A freeze incomplete')
    if set(REQUIRED)-set(manifest['files']): raise ValueError('missing Phase A required identities')
    proof=json.loads(Path(remote_receipt).read_text()) if remote_receipt else None
    if not proof or proof.get('status')!='PASS' or proof.get('remote_verified_commit')!=commit or proof.get('manifest_sha256')!=manifest_sha:
        raise ValueError('missing/bad remote verification')
    if proof.get('remote_fetched_independently') is not True: raise ValueError('remote independent fetch required')
    blobs={}
    for role,record in manifest['files'].items():
        path=record['path']; data=git_blob(root,commit,path)
        actual=hashlib.sha256(data).hexdigest()
        if actual!=record['sha256'] or data!=(Path(root)/path).read_bytes(): raise ValueError('changed '+role)
        if proof.get('verified_file_sha256',{}).get(path)!=actual: raise ValueError('remote file identity missing')
        blobs[role]=data
    protocol=json.loads(blobs['protocol'])
    if protocol.get('series')!='FS-R1' or protocol.get('historical_truth_reuse') is not False:
        raise ValueError('historical protocol cannot open new truth')
    bundle=json.loads(blobs['code'])
    if bundle.get('format')!='FS-R1-code-v1' or set(bundle.get('sha256',{}))!=set(execution_code_paths()):
        raise ValueError('all execution code identities required')
    for path,expected in bundle['sha256'].items():
        data=git_blob(root,commit,path); actual=hashlib.sha256(data).hexdigest()
        if actual!=expected or data!=(Path(root)/path).read_bytes(): raise ValueError('changed execution code')
        if proof.get('verified_file_sha256',{}).get(path)!=actual: raise ValueError('remote code identity missing')
    result=dict(phase_a_commit=commit,manifest_sha256=manifest_sha,verified=True,protocol=protocol)
    return reader(result) if reader else result

def recovery_then_public(payload,private_path,public_path,validator):
    # Inherit the scalar normalization/private-truth exclusions from sealed C0.
    from backend import ROOT
    import importlib.util
    p=ROOT/'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py'
    spec=importlib.util.spec_from_file_location('fs_r0_scalar_boundary',p)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.checkpoint_then_publish(payload,private_path,public_path,validator)

def verify_remote_publication(remote,branch,commit,manifest_path,manifest_sha,records,bare_directory,receipt_path):
    """Future Phase A remote receipt generator; read-only remote, independent repo.

    Does not run truth or science. A receipt is created only after all committed
    required files have been downloaded from the remote and hashed.
    """
    if not re.fullmatch('[0-9a-f]{40}',commit): raise ValueError('full commit required')
    tip=subprocess.check_output(['git','ls-remote',remote,'refs/heads/'+branch],text=True).split()[0]
    if tip!=commit: raise ValueError('remote tip mismatch')
    bare=Path(bare_directory)
    if bare.exists(): raise FileExistsError('independent verifier directory must be fresh')
    subprocess.run(['git','init','--bare',str(bare)],check=True,capture_output=True)
    def git(*args):return subprocess.check_output(['git','--git-dir',str(bare),*args])
    git('remote','add','origin',remote)
    git('config','remote.origin.promisor','true'); git('config','remote.origin.partialclonefilter','blob:none')
    git('fetch','--quiet','--depth=1','--filter=blob:none','origin',branch)
    if git('rev-parse','FETCH_HEAD').decode().strip()!=commit: raise ValueError('remote fetch mismatch')
    raw=git('show',commit+':'+manifest_path)
    if hashlib.sha256(raw).hexdigest()!=manifest_sha: raise ValueError('remote manifest hash mismatch')
    verified={}
    for record in records:
        data=git('show',commit+':'+record['path']); value=hashlib.sha256(data).hexdigest()
        if value!=record['sha256']: raise ValueError('remote file hash mismatch')
        verified[record['path']]=value
    proof=dict(status='PASS',remote_verified_commit=commit,manifest_sha256=manifest_sha,
               remote_fetched_independently=True,verified_file_sha256=verified)
    durable_create(receipt_path,canonical(proof))
    return proof
