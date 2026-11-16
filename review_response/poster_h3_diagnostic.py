"""Resolve the H3 triplet sector, bypassing the unrestricted eigsh shortcut."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import numpy as np
from poster_finite_time import ROOT, Sweep, reference_module, environment
from reproduce_poster_baseline import ALIASES, EPS, analytic, isolated_molecule_files, write_json
from run_morales_y8m10b_hchain import _prepare_system
from openfermion.linalg import get_sparse_operator
from scipy.linalg import eigh
from trotterlib.cost_extrapolation import calculation_cost
from validate_hchain_perturbative_estimator import _as_group_operator

out=ROOT/'artifacts/poster_finite_time_20261116'
repro=json.loads((out/'reproducibility.json').read_text())
assert repro['pass']
isolated_molecule_files()
sector=reference_module(out/'references/4672f3f/review_response/hchain_direct_sector_v1_1.py','poster_h3_sector')
gpu=reference_module(out/'references/4672f3f/src/trotterlib/sector_pf_gpu.py','trotterlib.poster_h3_gpu')
with contextlib.redirect_stdout(io.StringIO()):
    original = _prepare_system(3)
indices = np.asarray([i for i in range(64) if format(i,'06b')[::2].count('1') == 2 and format(i,'06b')[1::2].count('1') == 0])
hamiltonian = np.zeros((len(indices),len(indices)),complex)
for group in original['groups']:
    op = _as_group_operator(group)
    matrix = get_sparse_operator(op,6).tocsr()
    hamiltonian += matrix[indices][:,indices].toarray() - op.terms.get((),0)*np.eye(len(indices))
values, vectors = eigh(hamiltonian)
state = np.zeros(64,complex)
state[indices] = vectors[:,0]
def physical_system(h):
    return dict(original, state=state, energy_without_constant=float(values[0]))
sector._prepare_system=physical_system
system=sector.prepare_sparse_sector_system_v1_1(3)
print('physical H3 sector',system['sector'],flush=True)
assert sorted(system['sector']['population_counts'])==[0,2]
state=system['state']
residuals=[]
for values,vectors in system['group_spectra']:
    action=vectors@(values*(vectors.conj().T@state))
    residuals.append(float(np.linalg.norm(action-np.vdot(state,action)*state)))
builder=gpu.GpuSectorPFBuilder(system['group_spectra'])
payload=dict(system={k:v for k,v in system.items() if k not in ('group_spectra','state')},
             environment=environment(),reason='The legacy H3 shortcut diagonalizes all Fock/spin sectors and does not enforce the requested triplet populations. Here an exact lowest state in the fixed (2,0) triplet sector and the unchanged legacy grouping are used.',
             group_ground_state_eigenvector_residuals=residuals,maximum_group_ground_state_eigenvector_residual=max(residuals),results={})
try:
    for alias in ALIASES:
        model=analytic(3,alias)
        n_exp,_=calculation_cost(original['groups'],model['label'],system['ham_name'])
        sweep=Sweep(system,alias,builder)
        times=np.unique(np.r_[np.geomspace(.03,2,56),1,4,8,16])*model['time']
        points=sweep.calculate(times)
        t,cost=sweep.curve(points)
        i=int(np.nanargmin(cost))
        payload['results'][model['label']]=dict(alias=alias,formal_order=model['formal_order'],initial_fit=model,
            pauli_rotations_per_step=model['pauli_rotations_per_step'],actual_grouped_pauli_rotations_per_step=n_exp,
            analytic_power_law_optimum=model,times=t.tolist(),
            direct_diagonalization=dict(points=points,curve=dict(errors_hartree=[p['direct_error_hartree'] for p in points],costs=cost.tolist(),minimum=dict(index=i,time=float(t[i]),value=float(cost[i]),is_interior_of_sampled_time_range=False))),
            status='no_interior_minimum_through_16_tana' if i==len(points)-1 else 'requires_further_analysis',
            maximum_direct_error_hartree=max(p['direct_error_hartree'] for p in points))
        print(alias,'actual/table cost',n_exp,model['pauli_rotations_per_step'],'max error',max(p['direct_error_hartree'] for p in points),'minindex',i,flush=True)
finally:
    builder.close()
write_json(out/'H3_diagnostic.json',payload)
