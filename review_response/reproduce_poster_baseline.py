"""Reproduce poster analytics and stored wide points without editing inputs."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import pickle
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'review_response')]
import numpy as np
from trotterlib.config import BETA, DECOMPO_NUM, P_DIR, normalize_pf_label
from trotterlib.cost_validation import analytic_optimal_time, analytic_minimum_cost

OUT = ROOT / 'artifacts/poster_finite_time_20261116'
EPS = 1.59360010199040e-4
ALIASES = ('w8', 'w1016', 'wmy4')

def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')

def isolated_molecule_files():
    import trotterlib.chemistry_hamiltonian as chemistry
    original = chemistry.MolecularData
    runtime = OUT / 'runtime/molecules'
    runtime.mkdir(parents=True, exist_ok=True)
    def molecule(*args, **kwargs):
        kwargs['data_directory'] = str(runtime)
        return original(*args, **kwargs)
    chemistry.MolecularData = molecule

def analytic(h, alias):
    label = normalize_pf_label(alias)
    family = 'singlet' if h % 2 == 0 else 'triplet_1+'
    ham = f'H{h}_sto-3g_{family}_distance_100_charge_{h % 2}'
    source = ROOT / f'artifacts/trotter_expo_coeff_gr_original/{ham}_grouping_Operator_{alias}_ave'
    with source.open('rb') as stream:
        alpha = float(pickle.load(stream))
    order = P_DIR[label]
    n_exp = DECOMPO_NUM[f'H{h}'][label]
    t = analytic_optimal_time(alpha, order, EPS)
    cost = analytic_minimum_cost(BETA, n_exp, alpha, order, EPS)
    return dict(label=label, alias=alias, formal_order=order, alpha=alpha,
                alpha_source=str(source.relative_to(ROOT)), alpha_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                pauli_rotations_per_step=n_exp, time=t, value=cost, cost=cost, uses=cost/n_exp)

def main():
    started = time.perf_counter()
    rows = [analytic(8, alias) for alias in ALIASES]
    expected = [(1., 1., 1.), (1.940, .798, 1.549), (.295, 2.936, .866)]
    for row, want in zip(rows, expected):
        got = [row['pauli_rotations_per_step']/rows[0]['pauli_rotations_per_step'], row['uses']/rows[0]['uses'], row['value']/rows[0]['value']]
        row['ratios_per_step_uses_total'] = got
        row['expected_rounded'] = list(want)
        row['pass'] = all(abs(x-y) <= .0005 for x,y in zip(got,want))
    result = dict(baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(),
                  h8_analytic=rows, environment=dict(python=sys.version, platform=platform.platform(),
                  variables={k:v for k,v in os.environ.items() if k.startswith(('TROTTER_','CUDA_')) or k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
                  versions={p:importlib.metadata.version(p) for p in ('numpy','scipy','pyscf','openfermion','qiskit','qiskit-aer')}))
    write_json(OUT/'reproducibility.json',result)
    if not all(row['pass'] for row in rows):
        raise RuntimeError('H8 analytic reproduction failed; do not continue')
    isolated_molecule_files()
    import validate_hchain_perturbative_estimator as baseline
    reference_path = ROOT / 'artifacts/server_cost_validity/H4_wide_direct_validation.json'
    reference = json.loads(reference_path.read_text())['results']['8th(Morales-Y8m10b)']
    times = np.asarray(reference['times'][:14])
    print('prepare original H4 system',flush=True)
    system = baseline._prepare_sector_system(4)
    print('H4 sector', system['sector'],flush=True)
    points = baseline._direct_points(system, '8th(Morales-Y8m10b)', times)
    comparisons=[]
    for i,point in enumerate(points):
        error = point['direct_error_hartree']
        target = reference['direct_errors_hartree'][i]
        comparisons.append(dict(time=float(times[i]),recomputed=error,reference=target,absolute_difference=abs(error-target),
                                relative_difference=abs(error-target)/max(target,1e-30),pass_=abs(error-target)<=1e-11,diagnostics=point))
    result['wide_reproduction'] = dict(script='review_response/validate_hchain_perturbative_estimator.py',
           source_sha256=hashlib.sha256((ROOT/'review_response/validate_hchain_perturbative_estimator.py').read_bytes()).hexdigest(),
           source_reference=str(reference_path.relative_to(ROOT)),system={k:v for k,v in system.items() if k not in ('ground_state','group_spectra')},
           absolute_tolerance_hartree=1e-11,points=comparisons,pass_=all(p['pass_'] for p in comparisons),
           maximum_absolute_difference=max(p['absolute_difference'] for p in comparisons))
    result['pass'] = all(row['pass'] for row in rows) and result['wide_reproduction']['pass_']
    result['elapsed_seconds'] = time.perf_counter()-started
    write_json(OUT/'reproducibility.json',result)
    print('REPRODUCTION',result['pass'],result['wide_reproduction']['maximum_absolute_difference'],flush=True)
    if not result['pass']:
        raise RuntimeError('Wide reproduction failed; do not continue')

if __name__ == '__main__':
    main()
