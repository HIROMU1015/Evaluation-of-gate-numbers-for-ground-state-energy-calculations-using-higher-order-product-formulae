"""V2 Phase A committed blobs and remote proof before truth-only loader."""
import json
from pathlib import Path
import re
import subprocess
from r01_common import ROOT,HERE,sha,canonical,execution_code_paths,protocol

def git_blob(root,commit,path):
    return subprocess.check_output(['git','show',commit+':'+path],cwd=root,stderr=subprocess.DEVNULL)

def verify_phase_a(root,commit,manifest_path,manifest_sha,receipt_path,reader=None):
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('full Phase A commit required')
    raw=git_blob(root,commit,manifest_path)
    if sha(raw)!=manifest_sha or raw!=(Path(root)/manifest_path).read_bytes():raise ValueError('Phase A manifest hash mismatch')
    manifest=json.loads(raw)
    if manifest.get('stage')!='FS-R1-Phase-A' or manifest.get('truth_opened') is not False:raise ValueError('Phase A freeze incomplete')
    roles={'prediction','protocol','source_identity','code','recovery_reference'}
    if set(manifest.get('files',{}))!=roles:raise ValueError('required Phase A identities/recovery missing')
    if not receipt_path:raise ValueError('missing remote receipt')
    proof=json.loads(Path(receipt_path).read_text())
    if proof.get('status')!='PASS' or proof.get('remote_verified_commit')!=commit or proof.get('manifest_sha256')!=manifest_sha or proof.get('remote_fetched_independently') is not True:
        raise ValueError('remote receipt mismatch')
    blobs={}
    for role,record in manifest['files'].items():
        data=git_blob(root,commit,record['path']);actual=sha(data)
        if actual!=record['sha256'] or data!=(Path(root)/record['path']).read_bytes():raise ValueError(role+' hash mismatch')
        if proof.get('verified_file_sha256',{}).get(record['path'])!=actual:raise ValueError(role+' remote blob mismatch')
        blobs[role]=data
    if blobs['protocol']!=(HERE/'fs_r1_protocol_v2.json').read_bytes():raise ValueError('v2 protocol mismatch')
    p=json.loads(blobs['protocol'])
    if p['protocol_id']!='FS-R1-20261007-v2' or p['historical_truth_reuse'] or not p['truth_contract']['branch_continuation_closed']:
        raise ValueError('v2 truth contract mismatch')
    bundle=json.loads(blobs['code'])
    if bundle.get('format')!='FS-R1-code-v2' or set(bundle.get('sha256',{}))!=set(execution_code_paths()):raise ValueError('v2 code bundle incomplete')
    for path,digest in bundle['sha256'].items():
        data=git_blob(root,commit,path)
        if sha(data)!=digest or data!=(Path(root)/path).read_bytes() or data!=(ROOT/path).read_bytes() or proof.get('verified_file_sha256',{}).get(path)!=digest:raise ValueError('execution code mismatch')
    expected=(ROOT/'artifacts/pf_first_study_fs_r0_rebaseline_20261007/new_source_identity.json').read_bytes()
    if blobs['source_identity']!=expected:raise ValueError('FS-R0 source identity mismatch')
    from scoring_bridge import validate_prediction
    prediction=json.loads(blobs['prediction']);validate_prediction(prediction,p)
    recovery=json.loads(blobs['recovery_reference'])
    if recovery.get('prediction_sha256')!=sha(blobs['prediction']) or recovery.get('recovery_saved_before_public_validation') is not True:
        raise ValueError('recovery-bound prediction mismatch')
    result=dict(verified=True,phase_a_commit=commit,manifest_sha256=manifest_sha,protocol=p,
        protocol_sha256=sha(blobs['protocol']),prediction_sha256=sha(blobs['prediction']),prediction=prediction)
    return reader(result) if reader else result

def dispatch_truth(root,commit,manifest_path,manifest_sha,receipt_path,context,private_run_directory,executor=None):
    def opened(proof):
        if context.phase not in ('synthetic','FS-R1-Phase-B'):raise PermissionError('truth-only Phase B required')
        context.phase_a_proof=proof;context.guard()
        if executor is None:
            from truth_executor import execute_truth
            return execute_truth(proof,context,private_run_directory)
        return executor(proof,context,private_run_directory)
    return verify_phase_a(root,commit,manifest_path,manifest_sha,receipt_path,opened)
