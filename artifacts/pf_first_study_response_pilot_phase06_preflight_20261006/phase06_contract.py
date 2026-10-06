"""Pinned design contract and explicit execution-domain accounting."""
from dataclasses import dataclass,field
from pathlib import Path
import hashlib,json

BASE='48f3d889d096f2fe3af55c200a757747df384941'
PH05='artifacts/pf_first_study_response_pilot_phase05_20261006'
PROTOCOL_SHA='38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3'
IDENTITY_SHA='e771dbd97654425ff636edfa092a6ee19cddfebc289912670a50fd6a5be361bc'

class GateError(ValueError):pass

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

@dataclass(frozen=True,slots=True)
class Contract:
    protocol:dict
    identity:dict
    protocol_sha256:str
    identity_sha256:str

    def verify(self):
        encoded=lambda value:(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        if sha(encoded(self.protocol))!=PROTOCOL_SHA or sha(encoded(self.identity))!=IDENTITY_SHA:
            raise GateError('failed_source_identity: in-memory frozen contract changed')

def load_contract(root):
    root=Path(root)
    p=(root/PH05/'response_pilot_protocol.json').read_bytes()
    s=(root/PH05/'source_identity_phase_a.json').read_bytes()
    if sha(p)!=PROTOCOL_SHA or sha(s)!=IDENTITY_SHA:
        raise GateError('failed_source_identity: normative contract bytes changed')
    return Contract(json.loads(p),json.loads(s),PROTOCOL_SHA,IDENTITY_SHA)

@dataclass(frozen=True,slots=True)
class Authorization:
    phase:str
    protocol_sha256:str
    record_sha256:str

def load_authorization(path,phase):
    if path is None:
        raise GateError('science_not_authorized: separate approved execution record required')
    raw=Path(path).read_bytes();record=json.loads(raw)
    if record.get('science_authorized') is not True or record.get('phase')!=phase or record.get('protocol_sha256')!=PROTOCOL_SHA:
        raise GateError('science_not_authorized: phase/scope mismatch')
    return Authorization(phase,PROTOCOL_SHA,sha(raw))

COUNTERS=('H_matvec_count','projection_count','orthogonalization_count',
    'small_dense_response_solve_count','response_svd_factorization_count',
    'small_dense_ritz_eigh_count','PF_forward_action_count','PF_adjoint_action_count',
    'PF_action_on_original_state_count','PF_action_on_ritz_state_count',
    'exact_H_echo_action_count','new_direct_truth_count','saved_direct_truth_read_count',
    'new_vector_preparation_count','new_state_preparation_count','response_vector_generated_count',
    'stored_response_vector_count','PF_dense_build_count','group_expm_count','full_H_expm_count',
    'PF_dense_matrix_multiplication_count','H_spectral_norm_svd_count','fit_count',
    'new_ground_solve_count','full_H_eigh_count','new_Schur_count')

@dataclass
class ExecutionContext:
    domain:str='synthetic'
    authorization:Authorization|None=None
    counts:dict=field(default_factory=lambda:dict.fromkeys(COUNTERS,0))
    time_coordinates:set=field(default_factory=set)
    trace:list=field(default_factory=list)

    def guard(self):
        if self.domain not in ('synthetic','production'):
            raise GateError('invalid execution domain')
        if self.domain=='production' and (self.authorization is None or self.authorization.phase!='phase-a' or self.authorization.protocol_sha256!=PROTOCOL_SHA):
            raise GateError('science_not_authorized: stopped before production arithmetic')

    def require_input_domain(self,domain):
        if domain!=self.domain:
            raise GateError('input domain mismatch; cannot relabel production as synthetic')
        self.guard()

    def add(self,name,count=1):
        self.guard()
        if name not in self.counts or count<0:raise GateError('unknown/negative action counter')
        self.counts[name]+=count

    @property
    def science(self):return self.counts.copy() if self.domain=='production' else dict.fromkeys(COUNTERS,0)

    @property
    def synthetic(self):return self.counts.copy() if self.domain=='synthetic' else dict.fromkeys(COUNTERS,0)

def expected_counts(k,stop,group_count=13):
    u=len({min(m,k) for m in (1,2,4,8)}-{0})
    return {'H_matvec_count':2*(1+k),'projection_count':2*(1+3*k+2*int(stop)+22),
        'orthogonalization_count':2*(k*(k-1)+2*k*int(stop)),
        'PF_forward_action_count':44*(1+u),'PF_adjoint_action_count':44,
        'response_svd_factorization_count':2*u,'small_dense_response_solve_count':44*u,
        'small_dense_ritz_eigh_count':2*u,'PF_action_on_original_state_count':88,
        'PF_action_on_ritz_state_count':44*u,'exact_H_echo_action_count':44*(2+u),
        'new_vector_preparation_count':2*k,'new_state_preparation_count':2*u,
        'response_vector_generated_count':44*u,'stored_response_vector_count':0,
        'PF_dense_build_count':44,'group_expm_count':44*4*(2*group_count-1),
        'PF_dense_matrix_multiplication_count':44*(4*(2*group_count-1)+7),
        'full_H_expm_count':44,'H_spectral_norm_svd_count':2,'fit_count':27,
        'new_direct_truth_count':0,'saved_direct_truth_read_count':0,
        'new_ground_solve_count':0,'full_H_eigh_count':0,'new_Schur_count':0}
