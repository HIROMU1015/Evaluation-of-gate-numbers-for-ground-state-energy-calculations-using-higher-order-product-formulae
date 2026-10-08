"""Pinned metadata, scalar identities, and sealed v3 freeze evidence."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
A='artifacts/pf_first_study_fs_r1_phase_a_production_20261008'
A0='artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008'
R01='artifacts/pf_first_study_fs_r01_branch_extension_20261007'
R0='artifacts/pf_first_study_fs_r0_rebaseline_20261007'
SCIENCE='89c091e885c07b7c02883b1479a143c23f51df3c'
HANDOFF='e00ebc2024f72272cec64ebfd20c771d03665e95'
PREDICTION='d1f95e5ee38e72cc5cb04cfb805c0ae441060104828c18268574acda5d2215a9'
RESULT='899046840755e57531fac06ff4946fe947544040b3006963b28aeab0e241a4d1'
PROTOCOL='b1d37961484b212a6f2fab8b38092e56e640bac85c2369ab4cb29ba4ec383884'
NUMERICAL='16067176e0d1b211c5c43bd85287741cc93719977a57b675d5e2547b84dae573'
CODE_A='abb832afdd8de951e005d3104d2f7e1644329d86612607b61820e1f15ec1d9e4'
LADDER='8bf31841545b21df6c1480d0c8b1e7e15a88f2918c06123909bc4104482effeb'
REMOTE='git@github.com:HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae.git'
ARMS=('M00p','M10p','M01p','M11p')
_SEAL=object()

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def read(path):return json.loads(Path(path).read_text())
def path_ok(path):
    p=PurePosixPath(path)
    if not isinstance(path,str) or p.is_absolute() or '..' in p.parts or str(p)!=path:raise ValueError('unsafe manifest path')
    return path

@dataclass(frozen=True)
class VerifiedFreeze:
    """Immutable serialized evidence; no public verified=True bypass."""
    raw: bytes
    digest: str
    seal: object

    @property
    def data(self):return json.loads(self.raw)

    def __getitem__(self,key):return self.data[key]

def require_proof(proof):
    if not isinstance(proof,VerifiedFreeze) or proof.seal is not _SEAL or sha(proof.raw)!=proof.digest:
        raise PermissionError('actual v3 committed/remote/recovery proof required')
    data=proof.data
    if data['science_origin_commit']!=SCIENCE or data['handoff_commit']!=HANDOFF or data['prediction_sha256']!=PREDICTION:
        raise PermissionError('v3 proof authority mismatch')
    return data

def _issue_verified_freeze(data):
    raw=canonical(data)
    return VerifiedFreeze(raw,sha(raw),_SEAL)

def inherited_execution_paths():
    a=read(ROOT/A0/'execution_code_identity.json')['sha256']
    extra=[R01+'/'+n for n in ('branch_math.py','truth_executor.py','scoring_bridge.py','r01_common.py',
        'fs_r1_protocol_v2.json','branch_ladder.json','coordinate_resolution.json')]
    return sorted(set(a)|set(extra)|{R0+'/scorer.py','artifacts/pf_first_study_fs_r1_phase_a_20261007/build_audit.py'})

def execution_paths():
    own=['b0_common.py','v3_barrier.py','v3_scoring.py','truth_adapter.py','phase_b_controller.py','truth_recovery.py']
    config=['phase_b_bridge_contract.json','phase_a_external_remote_verification.json']
    prefix=str(HERE.relative_to(ROOT))+'/'
    return sorted(inherited_execution_paths()+[prefix+n for n in own+config])

def verify_execution():
    bundle=read(HERE/'execution_code_identity.json')
    if bundle.get('format')!='FS-R1-B0-execution-code-v1' or set(bundle.get('sha256',{}))!=set(execution_paths()):
        raise ValueError('complete Phase B execution bundle required')
    for path,digest in bundle['sha256'].items():
        if sha((ROOT/path_ok(path)).read_bytes())!=digest:raise ValueError('changed Phase B execution member: '+path)
    return sha(canonical(bundle))
