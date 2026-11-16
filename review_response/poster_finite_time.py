"""Poster finite-time cost comparison, based on 20d64c2 and 4672f3f.

Run with the shared scientific interpreter and an isolated CuPy installation.
Existing data and configuration are read-only. All products go to --output.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
import importlib.util
import io
import json
import os
import pickle
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'review_response')]
import numpy as np
from scipy.linalg import schur
from trotterlib.config import BETA, DECOMPO_NUM
from trotterlib.cost_validation import discrete_minimum, measured_cost_curve
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.sector_pf import build_sector_pf_unitary
from reproduce_poster_baseline import ALIASES, EPS, analytic, isolated_molecule_files, write_json

NOISE_FLOOR = 5e-13


def reference_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment():
    import importlib.metadata
    return dict(variables={k:v for k,v in os.environ.items() if k.startswith(('TROTTER_','CUDA_')) or k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
                versions={p:importlib.metadata.version(p) for p in ('numpy','scipy','pyscf','openfermion','qiskit','qiskit-aer')},
                dtype='complex128', solver='CPU scipy.linalg.schur',
                construction='4672f3f GpuSectorPFBuilder, complete conserved sector, repeated S2 cache')


class Sweep:
    def __init__(self, system, alias, builder):
        self.system = system
        self.alias = alias
        self.model = analytic(system['h_chain'], alias)
        self.label = self.model['label']
        self.sequence = _get_s2_sequence(self.label)
        self.builder = builder
        self.cache = {}
        self.history = []

    def calculate(self, times):
        pending = [t for t in sorted(set(map(float, times))) if t not in self.cache]
        if hasattr(self.builder, 'evaluate'):
            self.cache.update(self.builder.evaluate(self.alias, pending))
            return self.track()
        builders = self.builder if isinstance(self.builder, list) else [self.builder]
        if len(builders) > 1:
            # A worker owns one device and its resident spectra. Results are
            # collected before continuity is evaluated in increasing time.
            def chunk(worker):
                builder, assigned = worker
                builder.cp.cuda.Device(builder.logical_device).use()
                return [self._calculate_point(t, builder) for t in assigned]
            with ThreadPoolExecutor(max_workers=len(builders)) as pool:
                for batch in pool.map(chunk, [(b, pending[i::len(builders)]) for i,b in enumerate(builders)]):
                    self.cache.update(batch)
        else:
            for t in pending:
                key, value = self._calculate_point(t, builders[0])
                self.cache[key] = value
        return self.track()

    def _calculate_point(self, t, builder):
        began = time.perf_counter()
        builder.cp.cuda.Device(builder.logical_device).use()
        unitary = builder.build(self.sequence,t)
        built = time.perf_counter()
        tri, vectors = schur(unitary, output='complex', check_finite=False)
        values = np.diag(tri).copy()
        state = self.system['state']
        rotated = np.exp(-1j*self.system['energy']*t)*np.vdot(state,unitary@state)
        residuals = np.linalg.norm(unitary@vectors-vectors*values,axis=0)
        data = dict(values=values, vectors=vectors,
            unitarity=float(np.linalg.norm(unitary.conj().T@unitary-np.eye(len(state)))),
            schur_offdiagonal=float(np.linalg.norm(tri-np.diag(values))), residuals=residuals,
            overlap_phase_error=float(abs(np.angle(rotated)/t)),
            survival=float(abs(rotated)**2),
            build_seconds=built-began, elapsed=time.perf_counter()-began)
        return t, data

    def track(self):
        state = self.system['state']
        energy = self.system['energy']
        previous = None
        previous_shift = None
        points = []
        for t, data in sorted(self.cache.items()):
            vectors = data['vectors']
            ground = abs(vectors.conj().T@state)**2
            maximum = int(np.argmax(ground))
            overlaps = None if previous is None else abs(vectors.conj().T@previous)**2
            selected = maximum if previous is None else int(np.argmax(overlaps))
            shifts = np.angle(np.exp(-1j*energy*t)*data['values'])/t
            shift = float(shifts[selected])
            winding = 0 if previous_shift is None else round((previous_shift-shift)*t/(2*np.pi))
            shift += winding*2*np.pi/t
            error = abs(shift)
            model = self.model['alpha']*t**self.model['formal_order']
            points.append(dict(time=t, relative_time=t/self.model['time'],
                direct_error_hartree=error,signed_direct_error_hartree=shift,
                model_error_hartree=model,direct_to_model_ratio=error/model,
                selected_ground_state_overlap_probability=float(ground[selected]),
                tracking_overlap_probability=None if overlaps is None else float(overlaps[selected]),
                eigenpair_residual_norm=float(data['residuals'][selected]),
                maximum_ground_overlap_probability=float(ground[maximum]),
                maximum_ground_overlap_shift_hartree=float(shifts[maximum]),
                branch_shift_disagreement_hartree=abs(shift-float(shifts[maximum])),
                selected_schur_index=selected, maximum_ground_schur_index=maximum,
                phase_unwrap_winding=winding,
                effective_energy_step_change_hartree=None if previous_shift is None else shift-previous_shift,
                unitarity_residual_frobenius_norm=data['unitarity'],
                schur_off_diagonal_residual_frobenius_norm=data['schur_offdiagonal'],
                matrix_overlap_phase_error_hartree=data['overlap_phase_error'],
                ground_state_survival_probability=data['survival'],
                unitary_build_seconds=data['build_seconds'],elapsed_seconds=data['elapsed']))
            previous = vectors[:,selected]
            previous_shift = shift
        return points

    def curve(self, points):
        times = np.array([p['time'] for p in points])
        errors = np.array([p['direct_error_hartree'] for p in points])
        costs = measured_cost_curve(times,errors,beta=BETA,n_exp=self.model['pauli_rotations_per_step'],epsilon_e=EPS)
        return times, costs

    def minimum(self, points):
        times,costs=self.curve(points)
        selected=discrete_minimum(times,costs)
        if selected is None:
            raise RuntimeError(f'No feasible direct point for {self.label}')
        selected['is_interior_of_sampled_time_range']=0<selected['index']<len(times)-1
        return selected

    def run(self):
        tana=self.model['time']
        # Extra short-time points establish the start of contiguous validity.
        grid=np.unique(np.r_[np.geomspace(.03,.3,15),np.geomspace(.3,2.,41),1.])*tana
        points=self.calculate(grid)
        for extension in range(5):
            minimum=self.minimum(points)
            if minimum['is_interior_of_sampled_time_range']:
                break
            lo,hi=points[0]['time'],points[-1]['time']
            grid=np.geomspace(lo/2,lo,16) if minimum['index']==0 else np.geomspace(hi,hi*2,25)
            self.history.append(dict(kind='range_extension',start=float(grid[0]),stop=float(grid[-1])))
            points=self.calculate(grid)
        else:
            raise RuntimeError('Minimum remains on a search-range boundary')
        # Refinement keeps the same exact spectra; tracking is redone on the
        # complete increasing grid after every insertion, including old points.
        for round_ in range(8):
            old=self.minimum(points)
            i=old['index'];lo=points[i-1]['time'];hi=points[i+1]['time']
            points=self.calculate(np.linspace(lo,hi,25))
            new=self.minimum(points)
            self.history.append(dict(kind='minimum_refinement',round=round_,bracket=[lo,hi],minimum=new,
                relative_cost_change=abs(new['value']/old['value']-1),relative_time_change=abs(new['time']/old['time']-1)))
            if round_>=1 and abs(new['value']/old['value']-1)<1e-4 and abs(new['time']/old['time']-1)<1e-3 and (hi-lo)/new['time']<1e-3:
                break
        # Low adjacent overlap is a reason to add actual diagonalization points.
        # Never replace continuity with a maximum-ground-overlap choice.
        for round_ in range(7):
            additions=[(a['time']+b['time'])/2 for a,b in zip(points,points[1:])
                       if b['tracking_overlap_probability']<.9 and b['time']/a['time']-1>1e-4]
            if not additions:
                break
            self.history.append(dict(kind='continuity_refinement',round=round_,added_points=len(additions)))
            points=self.calculate(additions)
        # Refine the first reliable pass/fail boundary; later re-entry is ignored.
        for round_ in range(8):
            valid=self.validity(points)
            bracket=valid.get('boundary_bracket')
            if not bracket or bracket[1]/bracket[0]-1<1e-3:
                break
            points=self.calculate([sum(bracket)/2])
        return self.result(points)

    @staticmethod
    def validity(points):
        # Numerical-floor points before the first resolved observation are not
        # evidence for or against the leading power. Once started, no re-entry.
        reliable=[i for i,p in enumerate(points) if p['model_error_hartree']>NOISE_FLOOR and p['direct_error_hartree']>NOISE_FLOOR]
        if not reliable:
            return dict(t_valid=None,status='no_resolved_short_time_point',noise_floor_hartree=NOISE_FLOOR)
        start=reliable[0]
        if abs(points[start]['direct_to_model_ratio']-1)>.1:
            return dict(t_valid=None,status='first_resolved_short_time_point_fails',first_reliable_time=points[start]['time'],first_reliable_ratio=points[start]['direct_to_model_ratio'],noise_floor_hartree=NOISE_FLOOR)
        last=start
        for i in range(start+1,len(points)):
            p=points[i]
            if p['direct_error_hartree']<=NOISE_FLOOR or abs(p['direct_to_model_ratio']-1)>.1:
                return dict(t_valid=points[last]['time'],status='first_contiguous_interval_bracketed',
                            t_start=points[start]['time'],boundary_bracket=[points[last]['time'],p['time']],noise_floor_hartree=NOISE_FLOOR)
            last=i
        return dict(t_valid=points[last]['time'],status='right_censored_lower_bound',t_start=points[start]['time'],noise_floor_hartree=NOISE_FLOOR)

    def result(self,points):
        times,costs=self.curve(points)
        minimum=self.minimum(points)
        i=minimum['index']
        # Keep the location of the sampled minimum and a connected 1% basin.
        left=right=i
        while left>0 and np.isfinite(costs[left-1]) and costs[left-1]<=1.01*costs[i]:left-=1
        while right<len(points)-1 and np.isfinite(costs[right+1]) and costs[right+1]<=1.01*costs[i]:right+=1
        crossings=[[a['time'],b['time']] for a,b in zip(points,points[1:]) if a['signed_direct_error_hartree']*b['signed_direct_error_hartree']<0]
        basin_cross=any(a<=points[right]['time'] and b>=points[left]['time'] for a,b in crossings)
        atana=min(points,key=lambda p:abs(p['time']-self.model['time']))
        if abs(atana['time']/self.model['time']-1)>1e-12:raise RuntimeError('Exact t_ana point missing')
        p=self.model['formal_order'];r=atana['direct_to_model_ratio']
        valid=self.validity(points)
        model_costs=measured_cost_curve(times,self.model['alpha']*times**p,beta=BETA,n_exp=self.model['pauli_rotations_per_step'],epsilon_e=EPS)
        def finite(values):return [float(x) if np.isfinite(x) else None for x in values]
        gates=dict(maximum_unitarity_residual=max(x['unitarity_residual_frobenius_norm'] for x in points),
                   maximum_eigenpair_residual=max(x['eigenpair_residual_norm'] for x in points),
                   maximum_schur_offdiagonal_residual=max(x['schur_off_diagonal_residual_frobenius_norm'] for x in points),
                   maximum_branch_shift_disagreement_hartree=max(x['branch_shift_disagreement_hartree'] for x in points),
                   minimum_adjacent_tracking_overlap=min(x['tracking_overlap_probability'] for x in points[1:]),
                   minimum_ground_overlap_at_optimum=points[i]['selected_ground_state_overlap_probability'],
                   maximum_branch_disagreement_in_near_optimal_basin=max(x['branch_shift_disagreement_hartree'] for x in points[left:right+1]))
        gates['matrix_numerics_pass']=max(gates['maximum_unitarity_residual'],gates['maximum_eigenpair_residual'],gates['maximum_schur_offdiagonal_residual'])<=1e-10
        gates['all_time_branch_agreement_pass']=gates['maximum_branch_shift_disagreement_hartree']<=1e-10
        gates['optimum_branch_quality_pass']=gates['minimum_ground_overlap_at_optimum']>=.9 and gates['maximum_branch_disagreement_in_near_optimal_basin']<=1e-10
        return dict(label=self.label,alias=self.alias,formal_order=p,pauli_rotations_per_step=self.model['pauli_rotations_per_step'],
            times=times.tolist(),source='new complete-sector diagonalization',initial_fit=dict(alpha=self.model['alpha'],source=self.model['alpha_source'],sha256=self.model['alpha_sha256']),
            analytic_power_law_optimum=self.model,power_law_errors_hartree=[x['model_error_hartree'] for x in points],
            power_law_curve=dict(costs=finite(model_costs),minimum=discrete_minimum(times,model_costs)),
            direct_diagonalization=dict(times=times.tolist(),curve=dict(errors_hartree=[x['direct_error_hartree'] for x in points],costs=finite(costs),minimum=minimum,num_valid_cost_points=int(np.isfinite(costs).sum())),
                points=points,minimum_selected_ground_state_overlap_probability=min(x['selected_ground_state_overlap_probability'] for x in points),diagnostic_gates=gates),
            direct_optimum_vs_analytic=dict(time_ratio=minimum['time']/self.model['time'],cost_ratio=minimum['value']/self.model['value']),
            at_analytic_time=dict(**atana,same_time_direct_to_model_cost_ratio=p/(p+1-r) if r<p+1 else None,denominator_feasible=r<p+1),
            power_law_validity=dict(**valid,t_ana_over_t_valid=self.model['time']/valid['t_valid'] if valid['t_valid'] else None),
            optimum_diagnostics=dict(neighbor_bracket=[points[i-1]['time'],points[i+1]['time']],near_optimal_1percent_interval=[points[left]['time'],points[right]['time']],signed_error_sign_change_in_near_optimal_interval=basin_cross,sign_change_brackets=crossings),
            search_history=self.history,elapsed_seconds=sum(x['elapsed_seconds'] for x in points),point_count=len(points))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--aliases', nargs='+', choices=ALIASES, default=list(ALIASES))
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--systems',type=int,nargs='+',default=[2,4,6,5])
    parser.add_argument('--parallel-backend', choices=['thread','process'], default='process')
    parser.add_argument('--logical-gpus', type=int, nargs='+', default=[int(os.environ.get('TROTTER_DIRECT_LOGICAL_GPU','0'))])
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/poster_finite_time_20261116')
    args=parser.parse_args()
    if any(h not in (2,4,5,6) for h in args.systems):
        raise RuntimeError('Current scope allows H2/H4/H6 and reference H5 only; H8 awaits approval')
    out=args.output.resolve()
    repro=json.loads((out/'reproducibility.json').read_text())
    if not repro['pass']:raise RuntimeError('Required reproduction gate is not passed')
    isolated_molecule_files()
    refs=out/'references/4672f3f'
    sector=reference_module(refs/'review_response/hchain_direct_sector_v1_1.py','poster_new_sector')
    gpu=reference_module(refs/'src/trotterlib/sector_pf_gpu.py','trotterlib.poster_sector_pf_gpu')
    result_path=out/'wide_time_cost_analysis.json'
    payload=json.loads(result_path.read_text()) if result_path.exists() else dict(schema_version=1,
        purpose='Poster formulas, direct finite-time reoptimization',baseline_commit='20d64c2fea1ed2d2188777df4f3d962ee94df486',method_reference_commit='4672f3f5c57e34a553518b10655396a195521294',
        cost_model=dict(formula='beta*N_exp/(t*(epsilon_E-e_PF(t)))',beta=BETA,epsilon_E_hartree=EPS,invalid_when='e_PF(t) >= epsilon_E'),
        environment=environment(),claim_scope='Minimum of the sampled finite domain, with local refinement; no continuous/global optimality claim',results={},systems={})
    for h in args.systems:
        if f'H{h}' in payload['results'] and all(analytic(h,a)['label'] in payload['results'][f'H{h}'] for a in args.aliases) and not args.refresh:
            print('already complete',h,flush=True);continue
        began=time.perf_counter()
        print('PREPARE',h,flush=True)
        system=sector.prepare_sparse_sector_system_v1_1(h)
        expected=sorted(((h-h%2+2*(h%2))//2,(h-h%2-2*(h%2))//2))
        if sorted(system['sector']['population_counts'])!=expected:
            write_json(out/f'H{h}_sector_mismatch.json',dict(actual=system['sector'],expected_populations=expected))
            raise RuntimeError(f'H{h} input state has wrong populations {system["sector"]["population_counts"]}; expected {expected}')
        payload['systems'][f'H{h}']={k:v for k,v in system.items() if k not in ('state','group_spectra')}
        payload['results'].setdefault(f'H{h}',{})
        builders=[gpu.GpuSectorPFBuilder(system['group_spectra'],logical_device=device) for device in args.logical_gpus]
        builder=builders[0]
        point_pool=None
        try:
            payload['systems'][f'H{h}']['backend']=builder.identity()
            # Exact CPU/GPU equality at the same physical t, for every formula.
            parity={}
            for alias in args.aliases:
                model=analytic(h,alias);t=model['time']
                builder.cp.cuda.Device(builder.logical_device).use()
                u=builder.build(_get_s2_sequence(model['label']),t)
                cpu=build_sector_pf_unitary(system['group_spectra'],_get_s2_sequence(model['label']),t,method='s2-cache')
                delta=float(np.linalg.norm(cpu-u)/np.linalg.norm(cpu))
                parity[alias]=dict(time=t,relative_unitary_frobenius_difference=delta,pass_=delta<1e-10)
                if delta>1e-10:raise RuntimeError('CPU/GPU unitary parity failed')
            payload['systems'][f'H{h}']['cpu_gpu_parity']=parity
            if len(args.logical_gpus)>1 and args.parallel_backend=='process':
                from poster_process_pool import ProcessPointPool
                point_pool=ProcessPointPool(system,refs/'src/trotterlib/sector_pf_gpu.py',args.logical_gpus)
            for alias in args.aliases:
                label=analytic(h,alias)['label']
                if label in payload['results'][f'H{h}'] and not args.refresh:continue
                print('SWEEP',h,alias,flush=True)
                sweep=Sweep(system,alias,point_pool if point_pool is not None else builders)
                r=sweep.run()
                r['execution_environment']=environment()
                r['execution_environment']['logical_gpu_workers']=args.logical_gpus
                r['execution_environment']['parallel_backend']=args.parallel_backend if len(args.logical_gpus)>1 else 'single_gpu'
                payload['results'][f'H{h}'][label]=r
                write_json(out/'raw'/f'H{h}_{alias}.json',dict(system=payload['systems'][f'H{h}'],calculation=r['execution_environment'],results={f'H{h}':{label:r}}))
                write_json(result_path,payload)
                print('DONE',h,alias,'points',r['point_count'],'time ratio',r['direct_optimum_vs_analytic']['time_ratio'],'gates',r['direct_diagonalization']['diagnostic_gates'],flush=True)
        finally:
            if point_pool is not None:point_pool.close()
            for resident in builders:
                resident.cp.cuda.Device(resident.logical_device).use()
                resident.close()
        payload['systems'][f'H{h}']['total_wall_seconds']=time.perf_counter()-began
        write_json(result_path,payload)
    print('COMPLETE requested systems',flush=True)

if __name__=='__main__':main()
