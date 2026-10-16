"""Approval/hash boundary. Receipts record human authority; they do not grant it."""
import hashlib
import json
import os
from pathlib import Path


SCIENCE_ACTION='P1STAR-A-v1-PHASE-B-ONE-SHOT'


class ApprovalRequired(RuntimeError):pass


def sha256(data):return hashlib.sha256(data).hexdigest()


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def code_digest():
    root=Path(__file__).resolve().parents[1]
    records=[]
    for package in ('p1star_foundation','p1star_driver'):
        for path in sorted((root/package).rglob('*')):
            if path.is_file() and path.suffix in {'.py','.json'} and 'tests' not in path.parts:
                records.append([str(path.relative_to(root)),sha256(path.read_bytes())])
    return sha256(canonical(records))


def check_approval(receipt,*,action,input_sha256,settings,code_sha256,environment_sha256,contract_sha256,addendum_sha256):
    """Check before opening scientific input. No receipt is produced by tests."""
    if not receipt or receipt.get('explicit_user_approval') is not True:
        raise ApprovalRequired('separate explicit user approval missing')
    required={'action':action,'input_sha256':input_sha256,'settings_sha256':sha256(canonical(settings)),
              'code_sha256':code_sha256,'environment_sha256':environment_sha256,
              'contract_sha256':contract_sha256,'resource_addendum_sha256':addendum_sha256}
    if any(receipt.get(key)!=value for key,value in required.items()):
        raise ApprovalRequired('approval action or frozen hash mismatch')
    if not receipt.get('approval_reference') or not receipt.get('run_id'):
        raise ApprovalRequired('human approval reference and unique run id required')
    if receipt.get('attempt')!=1 or receipt.get('allow_retry') is not False:
        raise ApprovalRequired('single attempt, no automatic retry required')
    return required


def consume_once(directory,receipt):
    """Persistent attempt marker: failure still consumes approval, no retry."""
    directory=Path(directory)
    key=sha256(canonical({'run_id':receipt['run_id'],'input':receipt['input_sha256']}))
    path=directory/(key+'.attempted')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(canonical({'run_id':receipt['run_id'],'attempt':1}))
    return path


def read_frozen_input(path,expected_sha256,*,maximum_bytes=1024*1024):
    with Path(path).open('rb') as stream:data=stream.read(maximum_bytes+1)
    if len(data)>maximum_bytes or sha256(data)!=expected_sha256:
        raise ApprovalRequired('input size/hash mismatch')
    return json.loads(data)
