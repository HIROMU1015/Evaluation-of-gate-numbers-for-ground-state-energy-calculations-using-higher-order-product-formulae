"""Resumable parallel H8 sweep using complete compact group spectra."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import get_context,current_process
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,schur
from threadpoolctl import threadpool_limits
from poster_finite_time import Sweep,environment
from poster_h8_accelerated import ROOT,OUT,prepare,CompactGpuBuilder
from reproduce_poster_baseline import ALIASES,EPS,analytic,write_json
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.config import BETA

_SYSTEM=None
_BUILDER=None
_POINT_DIR=None
_THREADS=None


def initialize(system_path,devices,point_dir,blas_threads):
    global _SYSTEM,_BUILDER,_POINT_DIR,_THREADS
    with open(system_path,'rb') as f:_SYSTEM=pickle.load(f)
    device=devices[(current_process()._identity[0]-1)%len(devices)]
    _THREADS=threadpool_limits(limits=blas_threads)
    _BUILDER=CompactGpuBuilder(_SYSTEM,device=device)
    _POINT_DIR=Path(point_dir);_POINT_DIR.mkdir(parents=True,exist_ok=True)


def solve_gpu(u,builder,method):
    cp=builder.cp
    start=time.perf_counter()
    if method=='joint_real':
        a=(u.real+u.real.T)/2;b=(u.imag+u.imag.T)/2
        proxy=a+.3713906763541037*b
        vals,vectors=eigh(proxy,check_finite=False,driver='evd')
        cuts=np.r_[0,np.flatnonzero(np.diff(vals)>1e-6)+1,len(vals)]
        for lo,hi in zip(cuts,cuts[1:]):
            if hi-lo>1:
                v=vectors[:,lo:hi]
                _,q=eigh(v.T@b@v,check_finite=False)
                vectors[:,lo:hi]=v@q
        vg=cp.asarray(vectors)
        uv=builder.last_unitary@vg
        values=cp.asnumpy(cp.sum(vg*uv,axis=0))
    else:
        tri,vectors=schur(u,output='complex',check_finite=False)
        values=np.diag(tri).copy();vg=cp.asarray(vectors);uv=builder.last_unitary@vg
    residuals=cp.asnumpy(cp.linalg.norm(uv-vg*cp.asarray(values),axis=0))
    return values,vectors,residuals,time.perf_counter()-start


def point_key(alias,t,method):
    return f'{alias}_{float(t).hex().replace(".","_")}_{method}'


def point_job(job):
    alias,t,method=job
    key=point_key(alias,t,method)
    folder=_POINT_DIR/key
    marker=folder/'complete.json'
    if marker.exists():return t,str(folder)
    start=time.perf_counter()
    u=_BUILDER.build(_get_s2_sequence(analytic(8,alias)['label']),t)
    build_seconds=time.perf_counter()-start
    values,vectors,residuals,solve_seconds=solve_gpu(u,_BUILDER,method)
    rotated=np.exp(-1j*_SYSTEM['energy']*t)*np.vdot(_SYSTEM['state'],u@_SYSTEM['state'])
    metric=_BUILDER.metrics[-1]
    folder.mkdir(parents=True,exist_ok=True)
    np.save(folder/'values.npy',values);np.save(folder/'vectors.npy',vectors);np.save(folder/'residuals.npy',residuals)
    write_json(marker,dict(time=t,alias=alias,method=method,unitarity=metric['unitarity'],symmetry=metric['symmetry'],
        schur_offdiagonal=None,overlap_phase_error=float(abs(np.angle(rotated)/t)),survival=float(abs(rotated)**2),
        build_seconds=build_seconds,solve_seconds=solve_seconds,elapsed=time.perf_counter()-start,
        physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES','').split(',')[_BUILDER.logical_device],
        logical_gpu=_BUILDER.logical_device,maximum_eigenpair_residual=float(np.max(residuals))))
    _BUILDER.last_unitary=None
    return t,str(folder)


def load_point(folder):
    folder=Path(folder);data=json.loads((folder/'complete.json').read_text())
    for k in ('values','vectors','residuals'):data[k]=np.load(folder/f'{k}.npy',mmap_mode='r' if k=='vectors' else None)
    # Complete Schur off-diagonal residual <= sqrt(sum column residuals^2).
    data['schur_offdiagonal']=float(np.linalg.norm(data['residuals']))
    return data


class PointPool:
    def __init__(self,system_path,devices,point_dir,blas_threads):
        self.executor=ProcessPoolExecutor(max_workers=len(devices),mp_context=get_context('spawn'),
            initializer=initialize,initargs=(str(system_path),tuple(devices),str(point_dir),blas_threads))
        self.point_dir=Path(point_dir)
    def evaluate(self,alias,times,method='joint_real'):
        pending={};results=[]
        for t in times:
            folder=self.point_dir/point_key(alias,t,method)
            if (folder/'complete.json').exists():results.append((float(t),str(folder)))
            else:pending[self.executor.submit(point_job,(alias,float(t),method))]=t
        for t,path in results:yield t,load_point(path)
        for future in as_completed(pending):
            t,path=future.result()
            print(f'POINT {alias} {t:.12g} {method} complete',flush=True)
            yield t,load_point(path)
    def close(self):self.executor.shutdown(wait=True)


class H8Sweep(Sweep):
    def __init__(self,system,alias,pool):
        super().__init__(system,alias,pool)
        self.pool=pool
        self.checkpoint=OUT/'checkpoints'/f'{alias}.json'
        self.folder_map={}
        if self.checkpoint.exists():
            saved=json.loads(self.checkpoint.read_text());self.history=saved['history']
            for entry in saved['points']:
                if not (Path(entry['folder'])/'complete.json').exists():continue
                self.cache[entry['time']]=load_point(entry['folder']);self.folder_map[entry['time']]=entry['folder']
    def track(self):
        points=super().track()
        for point in points:
            data=self.cache[point['time']]
            point['full_eigensystem_residual_frobenius_norm']=data['schur_offdiagonal']
            point['schur_off_diagonal_residual_frobenius_norm']=data['schur_offdiagonal'] if data['method']=='schur' else None
            point['maximum_ground_eigenpair_residual_norm']=float(data['residuals'][point['maximum_ground_schur_index']])
            point['eigensolver_method']=data['method']
            point['maximum_all_eigenpair_residual']=data['maximum_eigenpair_residual']
            point['symmetry_residual_frobenius_norm']=data['symmetry']
            point['logical_gpu']=data['logical_gpu'];point['physical_gpu']=data['physical_gpu']
        return points
    def save_checkpoint(self):
        entries=[]
        for t,data in sorted(self.cache.items()):
            folder=self.pool.point_dir/point_key(self.alias,t,data['method'])
            entries.append(dict(time=t,folder=str(folder)))
        write_json(self.checkpoint,dict(alias=self.alias,history=self.history,points=entries))
    def calculate(self,times):
        import bisect
        known=sorted(self.cache)
        missing=[]
        for t in sorted(set(map(float,times))):
            i=bisect.bisect_left(known,t)
            neighbors=known[max(0,i-1):i+1]
            if any(abs(t-x)<=1e-12*max(t,x) for x in neighbors):continue
            if missing and abs(t-missing[-1])<=1e-12*max(t,missing[-1]):continue
            missing.append(float(t))
        for t,data in self.pool.evaluate(self.alias,missing):self.cache[t]=data
        # A full real eigensystem supplies the candidate orthonormal basis.
        # Where the reference could enter a numerically unresolved proxy pair,
        # replace the entire point with complex Schur, then retrace all times.
        for iteration in range(len(self.cache)+1):
            points=self.track();redo=[]
            for p in points:
                data=self.cache[p['time']]
                if data['method']=='schur':
                    if p['eigenpair_residual_norm']>1e-10:raise RuntimeError('Selected Schur residual gate failed')
                    continue
                max_ground_index=p['maximum_ground_schur_index']
                strong=max(p['eigenpair_residual_norm'],float(data['residuals'][max_ground_index]))>1e-11
                weak_ground=p['maximum_ground_overlap_probability']<.9
                weak_previous=p['tracking_overlap_probability'] is not None and p['tracking_overlap_probability']<.9
                if strong or weak_ground or weak_previous:redo.append(p['time'])
            if not redo:break
            print('SCHUR FALLBACK',self.alias,len(redo),flush=True)
            for t,data in self.pool.evaluate(self.alias,redo,method='schur'):self.cache[t]=data
        else:raise RuntimeError('Fallback did not settle')
        self.save_checkpoint()
        return self.track()
    def run(self):
        super().run()
        for round_ in range(8):
            before=self.track();old=self.minimum(before);i=old['index']
            lo,hi=before[i-1]['time'],before[i+1]['time']
            after=self.calculate(np.linspace(lo,hi,17));new=self.minimum(after)
            change=abs(new['value']/old['value']-1);time_change=abs(new['time']/old['time']-1)
            self.history.append(dict(kind='final_minimum_refinement',round=round_,minimum=new,relative_cost_change=change,relative_time_change=time_change,bracket=[lo,hi]))
            if change<1e-5 and time_change<1e-4 and (hi-lo)/new['time']<1e-4:break
        else:raise RuntimeError('Final minimum not converged')
        self.save_checkpoint()
        result=self.result(self.track())
        result['refinement_convergence']=self.history[-1]
        return result
    def result(self,points):
        temporary=[dict(p,schur_off_diagonal_residual_frobenius_norm=p['schur_off_diagonal_residual_frobenius_norm'] or 0.) for p in points]
        result=super().result(temporary)
        result['direct_diagonalization']['points']=points
        # For the joint real solver, only residual-validated target branches
        # are used. Full non-target residuals are diagnostics, not Schur form.
        g=result['direct_diagonalization']['diagnostic_gates']
        schur_values=[p['schur_off_diagonal_residual_frobenius_norm'] for p in points if p['eigensolver_method']=='schur']
        g['maximum_schur_offdiagonal_residual']=max(schur_values) if schur_values else None
        g['matrix_numerics_pass']=g['maximum_unitarity_residual']<=1e-10 and g['maximum_eigenpair_residual']<=1e-10 and max(schur_values,default=0.)<=1e-10
        result['method']='Exact population/Z2 sector, complete compact group exponentials, palindrome transpose reuse, residual-checked real joint diagonalization with complex-Schur fallback'
        return result


def fast_benchmark(devices):
    system=prepare(8);pool=PointPool(OUT/'runtime/H8_compact.pkl',devices,OUT/'runtime/points',1)
    results=[]
    expected={x['alias']:x for x in json.loads((OUT/'H8_benchmark.json').read_text())['results']}
    try:
        for alias in ALIASES:
            t=analytic(8,alias)['time'];begin=time.perf_counter()
            data=list(pool.evaluate(alias,[t]))[0][1]
            vectors=data['vectors'];values=data['values'];idx=int(np.argmax(abs(vectors.conj().T@system['state'])**2))
            shift=float(np.angle(np.exp(-1j*system['energy']*t)*values[idx])/t)
            result=dict(alias=alias,joint_method_seconds=data['elapsed'],wall_seconds=time.perf_counter()-begin,
                selected_residual=float(data['residuals'][idx]),maximum_residual=data['maximum_eigenpair_residual'],
                selected_overlap=float(abs(np.vdot(system['state'],vectors[:,idx]))**2),shift=shift,
                reference_difference=abs(shift-expected[alias]['selected_signed_shift_hartree']))
            result['pass']=result['reference_difference']<1e-11 and result['selected_residual']<1e-10
            results.append(result);print('FAST BENCHMARK',result,flush=True)
    finally:pool.close()
    write_json(OUT/'fast_solver_validation.json',dict(pass_=all(x['pass'] for x in results),results=results))


def sweep(devices,aliases,threads,parallel_formulas=False,aggregate_name="wide_time_cost_analysis.json"):
    validation=json.loads((OUT/'acceleration_validation.json').read_text())
    if not validation['pass_']:raise RuntimeError('H4/H6 validation gate missing')
    system=prepare(8)
    result_path=OUT/aggregate_name
    payload=json.loads(result_path.read_text()) if result_path.exists() else dict(schema_version=1,baseline_commit='20d64c2',
        cost_model=dict(formula='beta*N_exp/(t*(epsilon_E-e_PF(t)))',beta=BETA,epsilon_E_hartree=EPS,invalid_when='e_PF(t) >= epsilon_E'),
        system=system['metadata'],environment=dict(**environment(),parallel_backend='spawn_processes_compact_groups',logical_devices=devices,blas_threads_per_worker=threads),results={'H8':{}})
    payload['environment'].update(construction='exact compact group CSR GPU products with transpose palindrome folding',solver='residual-checked real joint eigensystem; complex Schur fallback')
    pool=PointPool(OUT/'runtime/H8_compact.pkl',devices,OUT/'runtime/points',threads)
    def compute_one(alias):
        label=analytic(8,alias)['label']
        start=time.perf_counter();print('START SWEEP',alias,flush=True)
        job=H8Sweep(system,alias,pool);r=job.run();r['wall_seconds']=time.perf_counter()-start
        return label,r
    pending=[a for a in aliases if analytic(8,a)['label'] not in payload['results']['H8']]
    try:
        if parallel_formulas and len(pending)>1:
            with ThreadPoolExecutor(max_workers=len(pending)) as outer:
                futures=[outer.submit(compute_one,a) for a in pending]
                completed=(f.result() for f in as_completed(futures))
                for label,r in completed:
                    payload['results']['H8'][label]=r
                    write_json(OUT/'raw'/f"H8_{r['alias']}.json",dict(system=system['metadata'],calculation=payload['environment'],results={'H8':{label:r}}))
                    write_json(result_path,payload)
                    print('FINISHED',r['alias'],'points',len(r['times']),'minimum',r['direct_diagonalization']['curve']['minimum'],'wall',r['wall_seconds'],flush=True)
        else:
            for alias in pending:
                label,r=compute_one(alias)
                payload['results']['H8'][label]=r
                write_json(OUT/'raw'/f"H8_{r['alias']}.json",dict(system=system['metadata'],calculation=payload['environment'],results={'H8':{label:r}}))
                write_json(result_path,payload)
                print('FINISHED',alias,'points',len(r['times']),'minimum',r['direct_diagonalization']['curve']['minimum'],'wall',r['wall_seconds'],flush=True)
    finally:pool.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fast-benchmark','sweep']);p.add_argument('--devices',nargs='+',type=int,default=list(range(8)));p.add_argument('--aliases',nargs='+',choices=ALIASES,default=list(ALIASES));p.add_argument('--aggregate-name',default='wide_time_cost_analysis.json');p.add_argument('--parallel-formulas',action='store_true');p.add_argument('--blas-threads',type=int,default=1);a=p.parse_args()
    if a.action=='fast-benchmark':fast_benchmark(a.devices)
    else:sweep(a.devices,a.aliases,a.blas_threads,a.parallel_formulas,a.aggregate_name)

if __name__=='__main__':main()
