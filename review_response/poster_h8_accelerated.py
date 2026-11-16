"""Exact compact-group PF calculation for the poster H8 extension.

Pauli coefficients and PF weights are unchanged. Population and automatically
verified diagonal-Z symmetry sectors are exact. Group components are complete,
with zero structural cutoff. The final PF matrix remains a dense unitary.
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'review_response')]
import numpy as np
from scipy.linalg import eigh, schur
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from trotterlib.component_sector_pf import (
    _as_group_operator, fixed_population_basis, find_balanced_z2_symmetry,
    diagonalize_components,
)
from trotterlib.config import BETA, DECOMPO_NUM
from trotterlib.product_formula import _get_s2_sequence
from reproduce_poster_baseline import ALIASES, EPS, analytic, write_json

OUT=Path(os.environ.get('TROTTER_POSTER_H8_OUTPUT',str(ROOT/'artifacts/poster_finite_time_20261116_h8'))).resolve()


def _prepare_group(arguments):
    group, nq, pop_basis, selected = arguments
    op=_as_group_operator(group)
    cols=np.arange(len(pop_basis),dtype=np.int64)
    rows=[];columns=[];values=[]
    for term, coefficient in op.terms.items():
        if not term or coefficient==0:continue
        target=pop_basis.copy()
        phase=np.full(len(pop_basis),coefficient,dtype=np.complex128)
        for qubit,pauli in term:
            mask=1<<(nq-1-qubit)
            occupied=(pop_basis&mask)!=0
            if pauli=='X':target^=mask
            elif pauli=='Y':target^=mask;phase*=np.where(occupied,-1j,1j)
            else:phase*=np.where(occupied,-1.,1.)
        rows.append(target);columns.append(cols);values.append(phase)
    rectangle=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(columns))),shape=(1<<nq,len(pop_basis))).tocsr()
    rectangle.eliminate_zeros()
    outside=np.setdiff1d(np.arange(1<<nq),pop_basis)
    population_leak=float(np.linalg.norm(rectangle[outside].data))
    population=rectangle[pop_basis].tocsr()
    excluded=np.setdiff1d(np.arange(len(pop_basis)),selected)
    symmetry_leak=float(np.linalg.norm(population[excluded][:,selected].data))
    matrix=population[selected][:,selected].tocsr()
    matrix.eliminate_zeros()
    spectrum=diagonalize_components(matrix,structural_cutoff=0.)
    transpose_residual=float(np.linalg.norm((matrix-matrix.T).data))
    hermitian_residual=float(np.linalg.norm((matrix-matrix.getH()).data))
    diagnostics=dict(population_leakage=population_leak,symmetry_leakage=symmetry_leak,
        hermitian_residual=hermitian_residual,transpose_residual=transpose_residual,
        maximum_imaginary_entry=float(np.max(np.abs(matrix.data.imag),initial=0.)),
        maximum_component_size=spectrum.maximum_component_size,component_count=spectrum.component_count,
        retained_complex_elements=spectrum.retained_complex_elements,nnz=int(matrix.nnz))
    return matrix,spectrum,diagnostics


def prepare(h,output=OUT,processes=8):
    output=Path(output)
    cache=output/'runtime'/f'H{h}_compact.pkl'
    if cache.exists():
        with cache.open('rb') as f:return pickle.load(f)
    from trotterlib.qiskit_time_evolution_pyscf import make_checked_fci_result_from_pyscf_solver_grouper
    started=time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        fci=make_checked_fci_result_from_pyscf_solver_grouper(h)
    groups=fci.grouped_jw_list
    full_state=fci.state_vector.reshape(-1)
    basis, population=fixed_population_basis(fci.n_qubits,full_state)
    pop_state=full_state[basis]
    try:
        mask,target,selected,symmetry=find_balanced_z2_symmetry(groups,fci.n_qubits,basis,pop_state)
    except RuntimeError as error:
        selected=np.arange(len(basis));symmetry=dict(kind='population_only',reason=str(error))
    state=pop_state[selected].copy();state/=np.linalg.norm(state)
    print(f'PREPARE H{h}: {len(groups)} groups, population {len(basis)}, exact symmetry {len(selected)}',flush=True)
    arguments=[(g,fci.n_qubits,basis,selected) for g in groups]
    if processes>1:
        with ProcessPoolExecutor(max_workers=processes,mp_context=get_context('spawn')) as pool:
            prepared=list(pool.map(_prepare_group,arguments))
    else:prepared=[_prepare_group(x) for x in arguments]
    matrices=[x[0] for x in prepared]
    spectra=[x[1] for x in prepared]
    group_diagnostics=[x[2] for x in prepared]
    for key in ('population_leakage','symmetry_leakage','hermitian_residual'):
        if max(x[key] for x in group_diagnostics)>1e-11:raise RuntimeError(f'Group gate failed: {key}')
    hamiltonian=sum(matrices[1:],matrices[0].copy()).tocsr()
    constant=float(sum(_as_group_operator(g).terms.get((),0) for g in groups).real)
    original_energy=float(fci.energy-constant)
    initial_residual=float(np.linalg.norm(hamiltonian@state-original_energy*state))
    energy,vector=eigsh(hamiltonian,k=1,which='SA',v0=state,tol=1e-13,maxiter=2000)
    overlap=float(abs(np.vdot(state,vector[:,0]))**2)
    state=vector[:,0];energy=float(energy[0])
    residual=float(np.linalg.norm(hamiltonian@state-energy*state))
    if residual>1e-10 or overlap<1-1e-8:raise RuntimeError('Hamiltonian ground-state refinement failed')
    metadata=dict(h_chain=h,num_qubits=fci.n_qubits,num_groups=len(groups),population_sector=population,
        additional_symmetry=symmetry,dimension=len(selected),ground_energy_without_constant_hartree=energy,
        original_energy_without_constant_hartree=original_energy,ground_state_refinement_overlap=overlap,
        initial_ground_residual=initial_residual,ground_residual=residual,fci=fci.diagnostics,
        group_diagnostics=group_diagnostics,preparation_seconds=time.perf_counter()-started,
        coefficient_cutoff=0.,structural_cutoff=0.,
        compact_spectra_estimated_bytes=sum(x.retained_complex_elements for x in spectra)*16,
        dense_spectra_estimated_bytes=len(groups)*len(selected)**2*16)
    system=dict(h_chain=h,state=state,energy=energy,component_spectra=spectra,metadata=metadata,
                population_basis=basis,selected_population_positions=selected,group_matrices=matrices)
    cache.parent.mkdir(parents=True,exist_ok=True)
    with cache.open('wb') as f:pickle.dump(system,f,protocol=5)
    write_json(output/f'H{h}_preparation.json',metadata)
    print(f'PREPARED H{h}: residual {residual:.3e}; compact spectra {metadata["compact_spectra_estimated_bytes"]} bytes; {metadata["preparation_seconds"]:.2f}s',flush=True)
    return system


class CompactGpuBuilder:
    def __init__(self,system,device=0,fold=True):
        import cupy as cp
        from cupyx.scipy.sparse import csr_matrix
        self.cp=cp;self.csr_matrix=csr_matrix;self.logical_device=device
        cp.cuda.Device(device).use()
        self.dimension=len(system['state'])
        self.fold=fold and all(x['transpose_residual']==0. for x in system['metadata']['group_diagnostics'])
        self.groups=[]
        # CSR row/column structure is fixed for each complete component. Only
        # values of the small dense exponential blocks change with time.
        for spectrum in system['component_spectra']:
            batches=[];rows=[];cols=[]
            for batch in spectrum.batches:
                idx=batch.indices;k=batch.component_size
                rows.append(np.repeat(idx,k,axis=1).reshape(-1))
                cols.append(np.tile(idx,(1,k)).reshape(-1))
                batches.append((cp.asarray(batch.eigenvalues),None if batch.eigenvectors is None else cp.asarray(batch.eigenvectors)))
            row=np.concatenate(rows);col=np.concatenate(cols)
            order=np.lexsort((col,row));sortedrow=row[order]
            indptr=np.r_[0,np.cumsum(np.bincount(sortedrow,minlength=self.dimension))].astype(np.int32)
            self.groups.append((batches,cp.asarray(order),cp.asarray(col[order].astype(np.int32)),cp.asarray(indptr)))
        cp.cuda.Stream.null.synchronize()
        self.metrics=[]
        self.last_unitary=None

    def _gate(self,index,scaled):
        cp=self.cp;batches,order,indices,indptr=self.groups[index]
        values=[]
        for eigenvalues,vectors in batches:
            phases=cp.exp(1j*scaled*eigenvalues)
            gate=phases[:,:,None] if vectors is None else (vectors*phases[:,None,:])@vectors.conj().transpose(0,2,1)
            values.append(gate.reshape(-1))
        data=cp.concatenate(values)[order]
        return self.csr_matrix((data,indices,indptr),shape=(self.dimension,self.dimension))

    def _half(self,weight,t):
        cp=self.cp;current=cp.eye(self.dimension,dtype=cp.complex128)
        for i in range(len(self.groups)):
            current=self._gate(i,t*weight/2)@current
        return current

    def _s2(self,weight,t):
        if self.fold:
            half=self._half(weight,t)
            return half.T@half
        cp=self.cp;current=cp.eye(self.dimension,dtype=cp.complex128)
        for i in range(len(self.groups)-1):current=self._gate(i,t*weight/2)@current
        current=self._gate(len(self.groups)-1,t*weight)@current
        for i in reversed(range(len(self.groups)-1)):current=self._gate(i,t*weight/2)@current
        return current

    def build(self,sequence,t):
        cp=self.cp;cp.cuda.Device(self.logical_device).use();start=time.perf_counter()
        if self.fold and np.array_equal(sequence,np.asarray(sequence)[::-1]):
            mid=len(sequence)//2;current=cp.eye(self.dimension,dtype=cp.complex128);cache={}
            for w in sequence[:mid]:
                w=float(w)
                if w not in cache:cache[w]=self._s2(w,t)
                current=cache[w]@current
            current=self._half(float(sequence[mid]),t)@current
            result=current.T@current
        else:
            current=cp.eye(self.dimension,dtype=cp.complex128);cache={}
            for w in sequence:
                w=float(w)
                if w not in cache:cache[w]=self._s2(w,t)
                current=cache[w]@current
            result=current
        unitarity=float(cp.linalg.norm(result.conj().T@result-cp.eye(self.dimension)).get())
        symmetry=float(cp.linalg.norm(result-result.T).get())
        host=cp.asnumpy(result);cp.cuda.Stream.null.synchronize()
        self.last_unitary=result
        self.metrics.append(dict(seconds=time.perf_counter()-start,folded=self.fold,device=self.logical_device,unitarity=unitarity,symmetry=symmetry))
        return host

    def close(self):
        self.cp.cuda.Device(self.logical_device).use();self.groups.clear();self.last_unitary=None;self.cp.get_default_memory_pool().free_all_blocks()


def joint_real_eigensystem(unitary,cluster_gap=1e-6):
    """Simultaneously diagonalize real and imaginary symmetric unitary parts.

    Near-degenerate proxy eigenvalues are resolved by diagonalizing the second
    commuting matrix inside each cluster. The caller checks actual U residuals
    and falls back to complex Schur when those checks do not pass.
    """
    real=(unitary.real+unitary.real.T)/2
    imag=(unitary.imag+unitary.imag.T)/2
    proxy=real+.3713906763541037*imag
    vals,vectors=eigh(proxy,check_finite=False,driver='evd')
    boundaries=np.r_[0,np.flatnonzero(np.diff(vals)>cluster_gap)+1,len(vals)]
    for lo,hi in zip(boundaries,boundaries[1:]):
        if hi-lo>1:
            v=vectors[:,lo:hi]
            _,rotation=eigh(v.T@imag@v,check_finite=False)
            vectors[:,lo:hi]=v@rotation
    uv=unitary@vectors
    eigenvalues=np.sum(vectors*uv,axis=0)
    residuals=np.linalg.norm(uv-vectors*eigenvalues,axis=0)
    return eigenvalues,vectors,residuals


def eigensystem(unitary,method='auto'):
    start=time.perf_counter();used=method
    if method=='auto':
        values,vectors,residuals=joint_real_eigensystem(unitary)
        if np.max(residuals)>2e-11:
            used='schur_fallback'
        else:used='joint_real'
    if method=='schur' or used=='schur_fallback':
        triangular,vectors=schur(unitary,output='complex',check_finite=False)
        values=np.diag(triangular).copy()
        residuals=np.linalg.norm(unitary@vectors-vectors*values,axis=0)
        used='schur' if method=='schur' else used
    return values,vectors,residuals,dict(method=used,seconds=time.perf_counter()-start,maximum_residual=float(np.max(residuals)))


def validate():
    from poster_finite_time import reference_module
    from trotterlib.sector_pf import build_sector_pf_unitary
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ROOT/'artifacts/poster_finite_time_20261116/wide_time_cost_analysis.json').read_text())
    results=[]
    for h in (4,6):
        system=prepare(h)
        builder=CompactGpuBuilder(system)
        full=None
        if h==4:
            sector=reference_module(ROOT/'artifacts/poster_finite_time_20261116/references/4672f3f/review_response/hchain_direct_sector_v1_1.py','poster_h8_validation_sector')
            from reproduce_poster_baseline import isolated_molecule_files
            # H4 is only used for validating the already published dense path.
            isolated_molecule_files();full=sector.prepare_sparse_sector_system_v1_1(4)
        try:
            for alias in ALIASES:
                model=analytic(h,alias);t=model['time'];label=model['label']
                u=builder.build(_get_s2_sequence(label),t)
                values,vectors,residuals,metric=eigensystem(u)
                index=int(np.argmax(abs(vectors.conj().T@system['state'])**2))
                shift=float(np.angle(np.exp(-1j*system['energy']*t)*values[index])/t)
                expected=baseline['results'][f'H{h}'][label]['at_analytic_time']['signed_direct_error_hartree']
                result=dict(h_chain=h,alias=alias,time=t,signed_shift=shift,reference_shift=expected,absolute_difference=abs(shift-expected),eigensolver=metric,
                            unitarity_residual=float(np.linalg.norm(u.conj().T@u-np.eye(len(u)))))
                if full is not None:
                    dense=build_sector_pf_unitary(full['group_spectra'],_get_s2_sequence(label),t)
                    pos=system['selected_population_positions']
                    result['relative_unitary_difference']=float(np.linalg.norm(dense[np.ix_(pos,pos)]-u)/np.linalg.norm(u))
                result['pass']=abs(shift-expected)<=1e-11 and max(residuals)<=1e-10 and result.get('relative_unitary_difference',0)<=1e-10
                results.append(result);print(result,flush=True)
        finally:builder.close()
    payload=dict(pass_=all(x['pass'] for x in results),results=results)
    write_json(OUT/'acceleration_validation.json',payload)
    if not payload['pass_']:raise RuntimeError('Compact/folded validation failed')


def benchmark(h=8):
    system=prepare(h)
    builder=CompactGpuBuilder(system)
    results=[]
    try:
        for alias in ALIASES:
            model=analytic(h,alias);t=model['time'];start=time.perf_counter()
            u=builder.build(_get_s2_sequence(model['label']),t)
            built=time.perf_counter()
            values,vectors,residuals,solver=eigensystem(u)
            idx=int(np.argmax(abs(vectors.conj().T@system['state'])**2))
            shift=float(np.angle(np.exp(-1j*system['energy']*t)*values[idx])/t)
            result=dict(alias=alias,label=model['label'],time=t,dimension=len(u),build_seconds=built-start,total_seconds=time.perf_counter()-start,eigensolver=solver,
                        selected_signed_shift_hartree=shift,selected_ground_overlap=float(abs(np.vdot(system['state'],vectors[:,idx]))**2),selected_residual=float(residuals[idx]),
                        unitarity_residual=float(np.linalg.norm(u.conj().T@u-np.eye(len(u)))),
                        symmetry_residual=float(np.linalg.norm(u-u.T)))
            results.append(result);print('BENCHMARK',result,flush=True)
            write_json(OUT/f'H{h}_benchmark.json',dict(results=results,metadata=system['metadata']))
    finally:builder.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['validate','prepare','benchmark']);p.add_argument('--system',type=int,default=8);args=p.parse_args()
    if args.action=='validate':validate()
    elif args.action=='prepare':prepare(args.system)
    else:
        if not json.loads((OUT/'acceleration_validation.json').read_text())['pass_']:raise RuntimeError('First validate H4/H6')
        benchmark(args.system)

if __name__=='__main__':main()
