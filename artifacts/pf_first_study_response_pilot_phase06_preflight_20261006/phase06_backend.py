"""Fixed signed S2-cache Padé backend. Each build has a fresh block cache."""
import numpy as np
import scipy
from scipy.linalg import expm
from phase06_contract import GateError

class EchoBackend:
    def __init__(self,data,contract,context):
        contract.verify()
        context.require_input_domain(data.domain)
        if np.__version__!='1.26.4' or scipy.__version__!='1.14.1':
            raise GateError('backend software version mismatch; frozen numpy/scipy required')
        self.data=data;self.context=context
        self.sequence=tuple(contract.protocol['formula_definition']['s2_sequence'])
        self.matrices={};self.cache_events=[];self.unitarity={}

    def build(self,t):
        self.context.require_input_domain(self.data.domain)
        if not t:raise GateError('zero time excluded')
        if t in self.matrices:raise GateError('duplicate signed build; counter scope fixed')
        n=len(self.data.psi);groups=self.data.groups
        blocks={};U=np.eye(n,dtype=np.complex128)
        for weight in self.sequence:
            if weight not in blocks:
                block=np.eye(n,dtype=np.complex128)
                steps=[(i,weight/2) for i in range(len(groups)-1)]+[(len(groups)-1,weight)]+[(i,weight/2) for i in reversed(range(len(groups)-1))]
                for index,w in steps:
                    self.context.add('group_expm_count')
                    step=expm(1j*groups[index]*(float(t)*float(w)))
                    self.context.add('PF_dense_matrix_multiplication_count')
                    block=step@block
                blocks[weight]=block
            self.context.add('PF_dense_matrix_multiplication_count')
            U=blocks[weight]@U
        self.context.add('PF_dense_build_count');self.context.add('full_H_expm_count')
        minus=expm(-1j*self.data.H*t)
        residual=float(np.linalg.norm(U.conj().T@U-np.eye(n)))
        if not np.isfinite(residual) or residual>1e-10:raise GateError('PF unitarity gate')
        self.matrices[t]=(U,minus);self.unitarity[t]=residual
        self.context.time_coordinates.add(('current_m3',float(t)))
        self.cache_events.append({'time':float(t),'unique_block_weights':len(blocks),'cache_scope':'this signed build only'})
        return U,minus

    def audit_signed_pair(self,t):
        U=self.matrices[t][0];negative=self.matrices[-t][0]
        residual=float(np.linalg.norm(negative-U.conj().T)/max(np.linalg.norm(U),np.finfo(float).tiny))
        if not np.isfinite(residual) or residual>1e-10:raise GateError('U(-t) versus U(t) adjoint gate')
        return residual

    def forward(self,t,state,original=True):
        self.context.guard();U,minus=self.matrices[t]
        self.context.add('PF_forward_action_count');self.context.add('exact_H_echo_action_count')
        self.context.add('PF_action_on_original_state_count' if original else 'PF_action_on_ritz_state_count')
        return minus@(U@state)

    def adjoint(self,t,state):
        self.context.guard();U,minus=self.matrices[t]
        self.context.add('PF_adjoint_action_count');self.context.add('exact_H_echo_action_count')
        self.context.add('PF_action_on_original_state_count')
        return U.conj().T@(minus.conj().T@state)
