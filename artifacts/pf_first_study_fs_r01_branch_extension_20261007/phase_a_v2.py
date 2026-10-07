"""Authorization adapter for unchanged v1 Phase A math bound to the v2 protocol."""
from dataclasses import dataclass
from r01_common import HERE,sha,v1_backend

@dataclass
class ContextV2(v1_backend.Context):
    phase: str='FS-R0.1'
    phase_a_proof: dict|None=None

    def guard(self,dimension=None):
        if self.phase=='synthetic':
            if dimension is not None and dimension>16:raise PermissionError('production dimension in synthetic context')
            return
        if self.phase not in ('FS-R1-Phase-A','FS-R1-Phase-B'):
            raise PermissionError('FS-R0.1 permits no production science or truth')
        a=self.authorization or {}
        if a.get('explicit_science_authorization') is not True or a.get('phase')!=self.phase:
            raise PermissionError('separate user/GPT science authorization required')
        if a.get('protocol_sha256')!=sha((HERE/'fs_r1_protocol_v2.json').read_bytes()):
            raise PermissionError('v2 protocol authorization identity mismatch')
        if self.phase=='FS-R1-Phase-B' and not (self.phase_a_proof or {}).get('verified'):
            raise PermissionError('actual Phase A freeze proof required')

def initial_and_cold(spec,context_factory):
    return v1_backend.cold_replay(spec,context_factory)
