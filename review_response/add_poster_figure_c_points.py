"""Add only the two absent H2/H4 published-PF points at the fixed t_ana."""
from pathlib import Path
import json, os, time
import numpy as np
from reproduce_poster_baseline import isolated_molecule_files, write_json
import validate_hchain_perturbative_estimator as baseline
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.pf_decomposition import iter_s2_sequence_steps

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/poster_finite_time_20261116'
LABEL='8th(Morales-Y8m10b)'

def main():
    isolated_molecule_files()
    rejection=json.loads((ROOT/'artifacts/server_cost_validity/integrated_boundary_recheck_20260902/pf_cost_rejection_tests.json').read_text())
    destination=OUT/'figure_C_additional_points.json'
    if destination.exists():
        print('Reusing the two saved supplementary points');return
    rows=[];started=time.perf_counter()
    for h in (2,4):
        begin=time.perf_counter()
        record=next(r for r in rejection['current_target_records'] if r['h_chain']==h and r['label']==LABEL)
        t=record['t_ana'];saved=json.loads((ROOT/f'artifacts/server_cost_validity/H{h}_wide_direct_validation.json').read_text())
        legacy=saved['results'][LABEL];i=max(i for i,x in enumerate(legacy['times']) if x<t)
        system=baseline._prepare_sector_system(h)
        q,vector,energy=baseline._direct_point(system,LABEL,t,previous_eigenvector=None,previous_effective_energy=legacy['points'][i]['selected_effective_energy_hartree'])
        unitary=np.eye(len(vector),dtype=complex)
        for group,weight in iter_s2_sequence_steps(system['num_groups'],_get_s2_sequence(LABEL)):
            values,vectors=system['group_spectra'][group]
            unitary=((vectors*np.exp(1j*t*weight*values))@vectors.conj().T)@unitary
        residual=float(np.linalg.norm(unitary@vector-np.exp(1j*energy*t)*vector))
        q.update(time=t,signed_direct_error_hartree=energy-system['ground_energy_without_constant_hartree'],
            eigenpair_residual_norm=residual,source='new',selection='maximum exact-ground overlap; energy winding referenced to the preceding legacy tracked point',
            branch_agreement=True,branch_agreement_basis='unique dominant exact-ground component (overlap > 0.5); selected eigenphase agrees with nearest tracked energy winding')
        assert q['selected_ground_state_overlap_probability']>.5 and residual<1e-10
        rows.append(dict(system=f'H{h}',point=q,elapsed_seconds=time.perf_counter()-begin,sector=system['sector']))
    write_json(destination,dict(results=rows,total_seconds=time.perf_counter()-started,new_diagonalization_points=2,
        environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','TROTTER_QISKIT_DEVICE')},
        method='unchanged validate_hchain_perturbative_estimator._direct_point; full sector eigensystem on CPU; one additional point per system'))
    print(json.dumps([(r['system'],r['elapsed_seconds'],r['point']['signed_direct_error_hartree']) for r in rows]))
if __name__=='__main__':main()
