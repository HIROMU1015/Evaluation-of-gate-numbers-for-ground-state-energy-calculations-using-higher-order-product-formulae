"""Read-only verification of frozen public scalars and actual committed bytes.

Uses the frozen scalar validator, never production/truth/source callbacks.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
A0=ROOT/'artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(name): return json.loads((HERE/name).read_text())

def verify(commit=None):
    manifest_raw=(HERE/'prediction_manifest.json').read_bytes()
    digest=sha(manifest_raw)
    assert digest==(HERE/'prediction.sha256').read_text().strip()
    m=json.loads(manifest_raw)
    assert (json.dumps(m,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()==manifest_raw
    assert m['self_excluded'] and m['phase_a_complete'] and m['Phase_B_authorized'] is False
    assert all(v==0 for v in m['truth_access'].values())
    records=m['files']+read('source_manifest.json')['sources']
    if (HERE/'publication_manifest.json').exists():records+=read('publication_manifest.json')['files']
    for r in records:
        raw=(ROOT/r['path']).read_bytes()
        assert sha(raw)==r['sha256'] and len(raw)==r['bytes']
        if commit:
            assert raw==subprocess.check_output(['git','show',commit+':'+r['path']],cwd=ROOT)
    sys.path.insert(0,str(A0))
    from a0_common import verify_frozen, canonical
    from phase_a_wrapper import validate_complete
    p,code=verify_frozen()
    assert code==m['execution_code_sha256']
    assert sha((A0/'fs_r1_protocol_v3.json').read_bytes())==m['protocol_sha256']
    assert sha((A0/'fs_r1_numerical_contract_v1.json').read_bytes())==m['numerical_contract_sha256']
    payload=read('production_results.json')
    assert sha((HERE/'production_results.json').read_bytes())==m['prediction_payload_sha256']
    assert validate_complete(payload,p)
    receipt=read('authorization_receipt.json')
    auth=receipt['authorization']
    assert sha(canonical(auth))==receipt['binding']['authorization_sha256']
    assert auth['user_request_sha256']==sha((HERE/'authorization_request.md').read_bytes())
    assert receipt['binding']['source_hashes']==m['source_hashes']
    assert receipt['entrypoint_invocations']==1 and receipt['science_retries']==0
    assert read('private_recovery_receipt.json')['public_return_receipt']['public_sha256']==m['prediction_payload_sha256']
    expected=[dict(row,condition=r['condition']) for category in ('initial_operational','cold_validation')
              for r in payload[category] for row in r['proxy_rows']]
    actual=list(csv.DictReader(io.StringIO((HERE/'proxy_values.csv').read_text())))
    assert len(expected)==len(actual)==32
    for a,b in zip(actual,expected):
        assert a['condition']==b['condition'] and a['state']==b['state']
        assert a['pass_category']==b['pass_category'] and float(a['time']).hex()==float(b['time']).hex()
        for k in ('signed_proxy','input_norm','PF_norm','reference_norm','echo_real','echo_imag'):
            assert float(a[k])==b[k]
    counts={}
    for category in ('initial_operational','cold_validation'):
        for r in payload[category]:
            for k,v in r['ledger']['logical_actions'].items():counts[k]=counts.get(k,0)+v
    assert counts==read('action_counts.json')['actual']
    assert read('cold_replay.json')['replay']==payload['replay']
    assert all(v==0 for v in read('truth_access_audit.json')['counts'].values())
    if (HERE/'GO_NO_GO_FOR_PHASE_B.json').exists():
        go=read('GO_NO_GO_FOR_PHASE_B.json')
        assert go['Phase_B_authorization'] is False and go['prediction_sha256']==digest
        remote=read('remote_verification.json')
        assert remote['status']=='PASS' and remote['remote_fetched_independently']
        assert remote['prediction_sha256']==digest and len(remote['remote_verified_commit'])==40
    return dict(status='PASS',prediction_sha256=digest,scalar_payload_valid=True,
        files_verified=len({r['path'] for r in records}),CSV_binary64_roundtrip_pass=True,
        counts_match_saved_returns=True,production_dispatches=0,source_numeric_loads=0,truth_dispatches=0,
        committed_blob_comparison=commit)

if __name__=='__main__':print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else None)),flush=True)
