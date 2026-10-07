"""Guarded native vector PF/echo and CSR Ritz8 adapter; FS-R0 never dispatches science."""
import ast
from dataclasses import dataclass, field
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply
from source_io import load_operational, sparse_hash, array_identity

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def native():
    pins=json.loads((HERE/'implementation_pins.json').read_text())
    p=ROOT/pins['c05_adapter']['path']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=pins['c05_adapter']['sha256']:
        raise ValueError('native loader identity changed')
    spec=importlib.util.spec_from_file_location('fs_r0_native_loader',p)
    m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
    return m.native_namespace(ROOT)

def fixed_spec(spec):
    protocol=json.loads((HERE/'fs_r1_protocol.json').read_text())
    matches=[s for s in protocol['systems'] if s['condition']==spec['condition']]
    if len(matches)!=1 or spec!=matches[0]: raise ValueError('fixed source/coordinate contract changed')
    return protocol

def load_registered_source(spec,context):
    context.guard(spec['dimension']); fixed_spec(spec)
    records=json.loads((HERE/'new_source_registry.json').read_text())['sources']
    record=next(r for r in records if r['condition']==spec['condition'])
    if record['source_identity_sha256']!=spec['source_identity_sha256']: raise ValueError('source identity changed')
    start=time.perf_counter()
    source=load_operational(record['operational_archive_path'],spec['operational_archive_sha256'],native())
    source['source_identity_sha256']=spec['source_identity_sha256']
    context.wall_seconds+=time.perf_counter()-start; context.add('source_load')
    return source

@dataclass
class Context:
    phase: str='FS-R0'
    authorization: dict|None=None
    counts: dict=field(default_factory=dict)
    wall_seconds: float=0.0

    def guard(self,dimension=None):
        if self.phase=='synthetic':
            if dimension is not None and dimension>16: raise PermissionError('production dimension in synthetic context')
            return
        if self.phase not in ('FS-R1-Phase-A','FS-R1-Phase-B'):
            raise PermissionError('FS-R0: no PF/echo/Ritz/fit/budget science')
        a=self.authorization or {}
        if a.get('explicit_science_authorization') is not True or a.get('phase')!=self.phase:
            raise PermissionError('separate user/GPT science authorization required')
        if a.get('protocol_sha256') != hashlib.sha256((HERE/'fs_r1_protocol.json').read_bytes()).hexdigest():
            raise PermissionError('authorization bound to another protocol')
        if self.phase=='FS-R1-Phase-B' and a.get('verified_phase_a') is not True:
            raise PermissionError('Phase A freeze verification required')

    def add(self,name,count=1):
        self.guard()
        self.counts[name]=self.counts.get(name,0)+count

    def snapshot(self):
        return dict(phase=self.phase,logical_actions=self.counts.copy(),
            classical=dict(wall_seconds=self.wall_seconds,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),
            expm_internal=dict(matvec=None,matmat=None,rmatvec=None,norm_estimation=None),
            internal_work_status='unknown',predicted_QPE_unit='PF rotations',
            threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            software=dict(numpy=np.__version__,python=__import__('sys').version.split()[0],scipy=__import__('scipy').__version__))

def compatible(H,psi):
    # Used only after science guard; accepts CSR at N=1568 without densification.
    H=csr_matrix(H,dtype=np.complex128)
    psi=np.asarray(psi,dtype=np.complex128)
    if H.shape[0]!=H.shape[1] or psi.shape!=(H.shape[0],) or H.shape[0]>1568:
        raise ValueError('incompatible fixed sector')
    if not np.isfinite(H.data).all() or not np.isfinite(psi).all(): raise ValueError('nonfinite operator/state')
    if abs(np.vdot(psi,psi).real-1)>1e-12: raise ValueError('state norm gate')
    anti=H-H.conj().T
    if np.linalg.norm(anti.data)>1e-12*max(np.linalg.norm(H.data),np.finfo(float).tiny):
        raise ValueError('Hamiltonian Hermiticity gate')
    return H,psi

def ritz8(H,psi,context):
    context.guard(H.shape[0])
    pins=json.loads((HERE/'implementation_pins.json').read_text())['ritz_math']
    raw=(ROOT/pins['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pins['sha256']: raise ValueError('Ritz math identity changed')
    wanted={'project','fix_phase','Basis','build_response_basis','solve_ritz_state'}
    nodes=[n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
    ns=dict(np=np,dataclass=dataclass,EPS=np.finfo(float).eps,KAPPA=64.,M_VALUES=(8,),require_synthetic=compatible)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),pins['path'],'exec',dont_inherit=True),ns)
    start=time.perf_counter()
    basis=ns['build_response_basis'](H,psi,context,max_m=8)
    state,diagnostics=ns['solve_ritz_state'](basis,8,context)
    context.wall_seconds+=time.perf_counter()-start
    diagnostics.update(retained_rank=basis.Z.shape[1],rank_stop=basis.stopped,
                       thresholds=list(basis.attempted_thresholds))
    return state,diagnostics

class NativeAdapter:
    def __init__(self,source,context):
        self.source=source; self.context=context; self.ns=native()

    def forward(self,psi,t):
        self.context.guard(self.source['hamiltonian'].shape[0])
        H,psi=compatible(self.source['hamiltonian'],psi)
        if not np.isfinite(t) or t<=0: raise ValueError('fixed positive time required')
        protocol=json.loads((HERE/'fs_r1_protocol.json').read_text())
        sequence=self.source['current_m3_sequence']
        if sequence!=protocol['current_m3_sequence']: raise ValueError('PF coefficients changed')
        result,timing=self.ns['_apply_pf_cpu'](self.source,sequence,t,psi)
        steps=list(self.ns['iter_s2_sequence_steps'](len(self.source['component_spectra']),sequence))
        self.context.add('PF_forward_vector_action')
        self.context.add('group_application',len(steps))
        self.context.add('group_materialization',len(set(steps)))
        self.context.wall_seconds+=timing['total']
        return result

    def proxy(self,psi,t):
        self.context.guard(self.source['hamiltonian'].shape[0])
        _,psi=compatible(self.source['hamiltonian'],psi)
        evolved=self.forward(psi,t)
        start=time.perf_counter()
        reference=expm_multiply(1j*t*self.source['hamiltonian'],psi)
        echo=np.vdot(reference,evolved)
        self.context.add('logical_exact_H_echo')
        self.context.wall_seconds+=time.perf_counter()-start
        return dict(signed_proxy=float(echo.imag/t),PF_norm=float(np.linalg.norm(evolved)),
                    reference_norm=float(np.linalg.norm(reference)),echo_real=float(echo.real),echo_imag=float(echo.imag))

    def fit(self,times,values,t_ref,t0):
        self.context.guard(self.source['hamiltonian'].shape[0])
        if len(times)!=3 or len(values)!=3: raise ValueError('three fixed training points only')
        if self.context.phase!='synthetic':
            p=json.loads((HERE/'fs_r1_protocol.json').read_text())
            s=next(s for s in p['systems'] if s['source_identity_sha256']==self.source['source_identity_sha256'])
            if list(times)!=s['training_absolute'] or t_ref!=s['fit_scale_t_ref'] or t0!=s['t0']:
                raise ValueError('fixed fit coordinates changed')
        points=[dict(time=t,echo_imag_hartree=v) for t,v in zip(times,values)]
        result=self.ns['_fit_proxy'](points,'echo_imag_hartree',3,t_ref,'FS-R1-3point')
        a4,a6=result['coefficient_values']
        result['signed_prediction_at_t0']=a4*t0**4+a6*t0**6
        self.context.add('scalar_fit')
        return result

def prediction_pass(source,spec,context):
    """Future authorized one-pass acquisition; no truth data or historical B0."""
    context.guard(source['hamiltonian'].shape[0])
    started=time.perf_counter(); prior_wall=context.wall_seconds
    if context.phase!='synthetic':
        fixed_spec(spec)
        if source.get('source_identity_sha256')!=spec['source_identity_sha256'] or sparse_hash(source['hamiltonian'])!=spec['new_H_sha256']:
            raise ValueError('prediction source identity changed')
        identities=json.loads((HERE/'new_source_identity.json').read_text())['identities']
        identity=next(i for i in identities if i['condition']==spec['condition'])
        if array_identity(source['cisd'])['sha256']!=identity['CISD']['sha256']:
            raise ValueError('prediction CISD identity changed')
    backend=NativeAdapter(source,context)
    psi=source['cisd']; refined,ritz_diag=ritz8(source['hamiltonian'],psi,context)
    times=spec['training_absolute']; t0=spec['t0']
    rows={}
    for label,state in [('CISD',psi),('Ritz8',refined)]:
        rows[label]=[backend.proxy(state,t) for t in [*times,t0]]
    fits={label:backend.fit(times,[r['signed_proxy'] for r in value[:3]],spec['fit_scale_t_ref'],t0) for label,value in rows.items()}
    estimates={'M00p':fits['CISD']['signed_prediction_at_t0'], 'M10p':fits['Ritz8']['signed_prediction_at_t0'],
               'M01p':rows['CISD'][3]['signed_proxy'],'M11p':rows['Ritz8'][3]['signed_proxy']}
    from scorer import budget
    cfg=json.loads((HERE/'fs_r1_protocol.json').read_text())['constants']
    budgets={arm:budget(abs(value),t0,spec['K'],cfg) for arm,value in estimates.items()}
    context.wall_seconds=prior_wall+time.perf_counter()-started
    return dict(condition=spec['condition'],estimates=estimates,budgets=budgets,proxy_rows=rows,fits=fits,
                Ritz=ritz_diag,ledger=context.snapshot(),source_identity_sha256=spec['source_identity_sha256'])

def cold_replay(spec,context_factory,loader=load_registered_source,acquire=prediction_pass):
    """Future authorized initial/cold passes, with no scientific object sharing."""
    output={}
    for category in ('initial_operational','cold_validation'):
        context=context_factory(); context.guard(spec.get('dimension'))
        source=loader(spec,context)
        output[category]=acquire(source,spec,context)
        del source,context
    return output
