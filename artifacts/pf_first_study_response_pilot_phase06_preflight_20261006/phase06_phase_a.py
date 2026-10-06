"""Truth-free production path, complete independent cold replay, fixed fit."""
from dataclasses import dataclass
from pathlib import Path
import time,resource
import numpy as np
from phase06_contract import GateError,canonical,sha,expected_counts,ExecutionContext
from phase06_inputs import PhaseAData,array_hash
from phase06_backend import EchoBackend
from phase06_kernels import (TRAIN,EVAL,M_VALUES,build_response_basis,factor_response,
    solve_response_least_squares,solve_ritz_state,project,compute_response_proxy,
    fit_two_term_model,evaluate_fit)

ARMS={'A0':('base',None),'A1':('response','8'),'A2':('ritz','8'),
    **{f'response_m{m}':('response',str(m)) for m in (1,2,4)},
    **{f'ritz_m{m}':('ritz',str(m)) for m in (1,2,4)}}

@dataclass
class PassResult:
    rows:dict
    basis:object
    backend:object
    factors:dict
    states:dict
    state_diagnostics:dict
    H_norm:float

def _one_pass(data,contract,context):
    context.require_input_domain(data.domain)
    H=data.H
    norm=float(np.linalg.norm(data.psi))
    if abs(norm**2-1)>1e-12:raise GateError('input state normalization gate')
    psi=np.array(data.psi,dtype=np.complex128,copy=True)/norm
    if np.linalg.norm(H-H.conj().T)>1e-12*max(np.linalg.norm(H),np.finfo(float).tiny):
        raise GateError('input Hamiltonian Hermiticity gate')
    if np.linalg.norm(sum(data.groups,np.zeros_like(H))-H)>1e-12:
        raise GateError('input ordered group sum gate')
    working=PhaseAData(H,data.groups,psi,data.metadata,data.identity_audit,data.domain)
    basis=build_response_basis(H,psi,context)
    factors,states,diagnostics={},{},{}
    for m in M_VALUES:
        k=min(m,basis.Z.shape[1])
        if k not in factors:
            factors[k]=factor_response(basis,m,context)
            states[k],diagnostics[k]=solve_ritz_state(basis,m,context)
    context.add('H_spectral_norm_svd_count')
    H_norm=float(np.linalg.norm(H,2))
    backend=EchoBackend(working,contract,context)
    for magnitude in TRAIN+EVAL:
        backend.build(magnitude);backend.build(-magnitude)
        backend.audit_signed_pair(magnitude)
    rows={}
    for t in (s*m for m in TRAIN+EVAL for s in (1,-1)):
        w=backend.forward(t,psi)
        base=float(np.vdot(psi,w).imag/t)
        adj=backend.adjoint(t,psi)
        a=project(psi,(w-adj)/(2j*t),context)
        r_values,r_diagnostics,k_values={},{},{}
        for k in factors:
            z,d=solve_response_least_squares(factors[k],a,context)
            r_values[k]=compute_response_proxy(base,z,basis.r);r_diagnostics[k]=d
            k_values[k]=base if k==0 else float(np.vdot(states[k],backend.forward(t,states[k],original=False)).imag/t)
        rows[t]={'base':base,'response':{str(m):r_values[min(m,basis.Z.shape[1])] for m in M_VALUES},
            'ritz':{str(m):k_values[min(m,basis.Z.shape[1])] for m in M_VALUES},
            'response_diagnostics':{str(m):r_diagnostics[min(m,basis.Z.shape[1])] for m in M_VALUES}}
        if not all(np.isfinite(v) for v in [base,*r_values.values(),*k_values.values()]):
            raise GateError('nonfinite proxy; stop before fit')
    return PassResult(rows,basis,backend,factors,states,diagnostics,H_norm)

def _cache_isolation(first,cold):
    if first.basis is cold.basis or first.backend is cold.backend or first.factors is cold.factors:
        raise GateError('cold replay shares scientific cache')
    for name in ('Z','HZ','B','r','psi'):
        if np.shares_memory(getattr(first.basis,name),getattr(cold.basis,name)):
            raise GateError('cold replay shares generated basis/state array')
    for t in first.backend.matrices:
        for left,right in zip(first.backend.matrices[t],cold.backend.matrices[t],strict=True):
            if np.shares_memory(left,right):raise GateError('cold replay shares PF matrix')
    for k in first.factors:
        for name in ('U','s','Vh'):
            if np.shares_memory(getattr(first.factors[k],name),getattr(cold.factors[k],name)):
                raise GateError('cold replay shares response factor')
        if np.shares_memory(first.states[k],cold.states[k]):raise GateError('cold replay shares Ritz state')
    if first.basis.Z.shape!=cold.basis.Z.shape or first.basis.stopped!=cold.basis.stopped:
        raise GateError('cold replay rank/status mismatch')

def residual_convergence(rows):
    checks=[]
    for row in rows:
        diagnostics=row['response']
        for a,b in zip(M_VALUES[:-1],M_VALUES[1:],strict=True):
            left,right=diagnostics[str(a)],diagnostics[str(b)]
            allowance=left['numerical_residual_allowance']+right['numerical_residual_allowance']
            checks.append({'time':row['time'],'from_m':a,'to_m':b,
                'residual_increase':right['d_norm']-left['d_norm'],'roundoff_allowance':allowance,
                'passed':bool(right['d_norm']<=left['d_norm']+allowance)})
    return {'converged':all(c['passed'] for c in checks),'comparisons':checks}

def execute_phase_a(data,contract,context,code_identity):
    contract.verify()
    context.require_input_domain(data.domain)
    started=time.perf_counter()
    first=_one_pass(data,contract,context)
    first_counts=context.counts.copy()
    cold=_one_pass(data,contract,context)
    _cache_isolation(first,cold)
    rows=[];private=[]
    for t in first.rows:
        f,c=first.rows[t],cold.rows[t]
        proxies={};noise={}
        for arm,(field,m) in ARMS.items():
            value=f[field] if m is None else f[field][m]
            replay=c[field] if m is None else c[field][m]
            difference=abs(value-replay)
            eta=max(first.backend.unitarity[t]/abs(t),difference,
                50*np.finfo(float).eps*max(first.H_norm,1/abs(t)))
            rho=abs(value)/max(eta,1e-300)
            quality='resolved' if rho>=100 else 'marginal' if rho>=10 else 'unresolved'
            proxies[arm]=value
            noise[arm]={'first_pass':value,'cold_replay':replay,'replay_difference':difference,
                'proxy_noise':eta,'signal_to_noise_rho':rho,'quality_class':quality}
        response={}
        for m,d in f['response_diagnostics'].items():
            private.append({'time':t,'m':int(m),'L_m_complex_pairs':d['L_m_complex_pairs'],'a_m_complex_pairs':d['a_m_complex_pairs']})
            response[m]={k:v for k,v in d.items() if k not in ('L_m_complex_pairs','a_m_complex_pairs')}
            response[m]['g_base']=f['base'];response[m]['g_response']=f['response'][m]
        ritz={str(m):{**first.state_diagnostics[min(m,first.basis.Z.shape[1])],'proxy':f['ritz'][str(m)]} for m in M_VALUES}
        rows.append({'time':t,'role':'training' if abs(t) in TRAIN else 'evaluation',
            'proxies':proxies,'noise':noise,'response':response,'ritz':ritz,
            'PF_unitarity_residual':first.backend.unitarity[t],
            'U_signed_adjoint_residual':first.backend.audit_signed_pair(abs(t))})
    lookup={r['time']:r for r in rows};fits={};predictions={}
    for arm in ARMS:
        fits[arm]=fit_two_term_model(TRAIN,[lookup[t]['proxies'][arm] for t in TRAIN],
            [lookup[-t]['proxies'][arm] for t in TRAIN],[lookup[t]['noise'][arm]['quality_class'] for t in TRAIN])
        context.add('fit_count',3)
        model=fits[arm]['raw_positive_even_two_term']
        predictions[arm]=[{'time':s*t,'prediction':evaluate_fit(model,s*t),
            'proxy':lookup[s*t]['proxies'][arm],'fit_status':model['status']} for t in EVAL for s in (1,-1)]
    k=first.basis.Z.shape[1]
    expected=expected_counts(k,first.basis.stopped,len(data.groups))
    if context.counts!=expected:
        raise GateError('action_count_contract_mismatch: '+str({key:(expected[key],context.counts[key]) for key in expected if expected[key]!=context.counts[key]}))
    orth=float(np.linalg.norm(first.basis.Z.conj().T@first.basis.Z-np.eye(k)))
    psi_orth=float(np.linalg.norm(first.basis.psi.conj()@first.basis.Z))
    payload={'schema_version':'phase_a_v1','input_domain':data.domain,
        'source':{'protocol_sha256':contract.protocol_sha256,'code_sha256':sha(canonical(code_identity)),
            'code_files':code_identity,'source_sha256':sha(canonical(data.identity_audit)),
            'input_array_identities':data.identity_audit,'source_metadata':data.metadata},
        'basis':{'requested_m':list(M_VALUES),'actual_rank':k,
            'rank_thresholds':list(first.basis.attempted_thresholds),'orthogonality_residual':orth,
            'psi_orthogonality_residual':psi_orth,'status':'prefix_stopped' if first.basis.stopped else 'max_m_reached'},
        'rows':rows,'fits':fits,'predictions':predictions,'residual_convergence':residual_convergence(rows),
        'cost':{'actions':context.counts.copy(),'first_pass_actions':first_counts,
            'cold_replay_increment':{key:context.counts[key]-first_counts[key]-(27 if key=='fit_count' else 0) for key in context.counts},
            'unique_PF_time_coordinate_count':len(context.time_coordinates),
            'response_basis_dimension':k,'response_effective_ranks':{str(m):int(np.sum(first.factors[min(m,k)].retained)) for m in M_VALUES},
            'original_state_reuse_count':1,'stored_response_vector_count':0,
            'standalone_primary_one_pass':{'A0':{'H_actions':0,'PF_actions':22},'A1':{'H_actions':1+k,'PF_actions':44},'A2':{'H_actions':1+k,'PF_actions':22}},
            'generated_basis_vectors_peak':3*k,'generated_ritz_states_peak':len(first.states)-int(0 in first.states)},
        'replay':{'complete':True,'cache_isolation_passed':True,'shared_source_arrays_only':True,
            'independent_signed_builds_per_pass':22,'block_cache_scope':'single signed build',
            'first_backend_cache_events':first.backend.cache_events,'cold_backend_cache_events':cold.backend.cache_events},
        'runtime':{'wall_seconds':time.perf_counter()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    return payload,private
