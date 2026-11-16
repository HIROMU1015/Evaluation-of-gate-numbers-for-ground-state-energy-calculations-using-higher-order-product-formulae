"""Audit phase wrapping using the actual PF sectors and frozen saved curves.

No existing artifacts are changed. Full eigensystems and recovered PF vectors
are scratch caches; only one compact JSON and a Markdown report are published.
"""
from __future__ import annotations
import argparse, contextlib, hashlib, io, json, math, os, pickle, sys, time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, schur

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'review_response')]
from poster_finite_time import reference_module
from trotterlib.product_formula import _get_s2_sequence
from trotterlib.config import BETA,DECOMPO_NUM
from trotterlib.cost_validation import analytic_minimum_cost
from run_poster_h8 import load_point,point_key

BASE=ROOT/'artifacts/poster_finite_time_20261116'
OUT=ROOT/'artifacts/poster_finite_time_20261116_h8'
SCRATCH=OUT/'runtime/phase_wrap_analysis'
EPS=1.59360010199040e-4
FLOOR=5e-13
LABELS={'w8':'8th(Morales)','w1016':'10th(Morales)','wmy4':'4th(new_2)','y8':'8th(Morales-Y8m10b)'}
REF=BASE/'references/4672f3f'
SOURCES={}


def read(path):
    path=Path(path);SOURCES[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())

def dump_pickle(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb') as f:pickle.dump(data,f,protocol=5)

def isolated_chemistry(h):
    import trotterlib.chemistry_hamiltonian as chemistry
    original=getattr(chemistry.MolecularData,'_phase_wrap_original',chemistry.MolecularData)
    folder=SCRATCH/'molecules'/f'H{h}';folder.mkdir(parents=True,exist_ok=True)
    def molecule(*args,**kwargs):
        kwargs['data_directory']=str(folder)
        return original(*args,**kwargs)
    molecule._phase_wrap_original=original
    chemistry.MolecularData=molecule

def prepare_small(h,published_h2=False):
    key=f'H{h}'+('_published' if published_h2 else '')
    dest=SCRATCH/f'{key}.pkl'
    if dest.exists():
        with dest.open('rb') as f:return pickle.load(f)
    started=time.perf_counter();isolated_chemistry(h)
    from validate_hchain_perturbative_estimator import _as_group_operator
    offset={}
    if published_h2:
        import validate_hchain_perturbative_estimator as sector
        original=sector._prepare_system
    else:
        sector=reference_module(REF/'review_response/hchain_direct_sector_v1_1.py','phase_wrap_sector')
        original=sector._prepare_system
    def full_system(number):
        system=original(number)
        offset['identity']=float(sum(_as_group_operator(g).terms.get((),0) for g in system['groups']).real)
        return system
    sector._prepare_system=full_system
    with contextlib.redirect_stdout(io.StringIO()):
        if published_h2:
            old=sector._prepare_sector_system(h)
            system=dict(h_chain=h,energy=old['ground_energy_without_constant_hartree'],state=old['ground_state'],group_spectra=old['group_spectra'],sector=old['sector'])
        else:system=sector.prepare_sparse_sector_system_v1_1(h)
    hamiltonian=sum(((v*w)@v.conj().T for w,v in system['group_spectra']))
    eigenvalues,eigenvectors=eigh(hamiltonian,check_finite=False,driver='evd')
    residual=float(np.linalg.norm(hamiltonian@eigenvectors-eigenvectors*eigenvalues))
    assert abs(eigenvalues[0]-system['energy'])<1e-10
    answer=dict(key=key,h_chain=h,system=system,hamiltonian=hamiltonian,energies=eigenvalues,vectors=eigenvectors,
        identity_offset=offset['identity'],sector=system['sector'],full_spectrum_residual=residual,
        ground_overlap=float(abs(np.vdot(system['state'],eigenvectors[:,0]))**2),preparation_seconds=time.perf_counter()-started)
    dump_pickle(dest,answer)
    print('SPECTRUM',key,'dim',len(eigenvalues),'E0/Emax',eigenvalues[[0,-1]],'seconds',answer['preparation_seconds'],flush=True)
    return answer

def prepare_h8():
    dest=SCRATCH/'H8.pkl'
    if dest.exists():
        with dest.open('rb') as f:return pickle.load(f)
    started=time.perf_counter()
    with (OUT/'runtime/H8_compact.pkl').open('rb') as f:system=pickle.load(f)
    hamiltonian=sum(system['group_matrices'][1:],system['group_matrices'][0].copy()).toarray()
    assert np.max(abs(hamiltonian.imag))==0
    hamiltonian=hamiltonian.real
    eigenvalues,eigenvectors=eigh(hamiltonian,check_finite=False,driver='evd')
    residual=float(np.linalg.norm(hamiltonian@eigenvectors-eigenvectors*eigenvalues))
    meta=system['metadata'];offset=meta['fci']['davidson_attempts'][-1]['energy_hartree']-meta['original_energy_without_constant_hartree']
    assert abs(eigenvalues[0]-system['energy'])<1e-10
    answer=dict(key='H8',h_chain=8,system=system,hamiltonian=hamiltonian,energies=eigenvalues,vectors=eigenvectors,
        identity_offset=offset,sector=dict(population=meta['population_sector'],additional_z2=meta['additional_symmetry'],dimension=len(eigenvalues)),
        full_spectrum_residual=residual,ground_overlap=float(abs(np.vdot(system['state'],eigenvectors[:,0]))**2),preparation_seconds=time.perf_counter()-started)
    dump_pickle(dest,answer)
    print('SPECTRUM H8','dim',len(eigenvalues),'E0/Emax',eigenvalues[[0,-1]],'seconds',answer['preparation_seconds'],flush=True)
    return answer

def prep_job(pair):return prepare_small(*pair)['key']

def native_curves(h):
    folder=OUT if h==8 else BASE
    rows=[]
    for alias in ('w8','w1016','wmy4'):
        path=folder/'raw'/f'H{h}_{alias}.json';d=read(path);r=d['results'][f'H{h}'][LABELS[alias]]
        rows.append(dict(h=h,alias=alias,label=LABELS[alias],sector=f'H{h}',source=str(path.relative_to(ROOT)),
            alpha=r['initial_fit']['alpha'],p=r['formal_order'],alpha_source=r['initial_fit']['source'],
            t_ana=r['analytic_power_law_optimum']['time'],n_rot=r['pauli_rotations_per_step'],validity=r['power_law_validity'],
            points=[dict(t=q['time'],shift=q['signed_direct_error_hartree'],overlap=q['selected_ground_state_overlap_probability'],
                branch_agreement=q['branch_shift_disagreement_hartree']<=1e-10,raw=q) for q in r['direct_diagonalization']['points']]))
    return rows

def published_curve(h):
    label=LABELS['y8']
    rejection=read(BASE.parent/'server_cost_validity/integrated_boundary_recheck_20260902/pf_cost_rejection_tests.json')
    rec=next(r for r in rejection['current_target_records'] if r['h_chain']==h and r['label']==label)
    if h==6:
        path=REF/'artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/raw/H6_y8.json'
        r=read(path)['results']['H6']['results'][label];alpha=r['fixed_order_alpha'];tana=r['analytic_optimal_time'];pts=[]
        for q in r['points']:
            a=q['continuously_tracked_branch'];b=q['maximum_ground_overlap_branch']
            pts.append(dict(t=q['time'],shift=a['unwrapped_energy_shift_hartree'],overlap=a['ground_overlap_probability'],
                branch_agreement=a['schur_index']==b['schur_index'] and abs(a['unwrapped_energy_shift_hartree']-b['energy_shift_hartree'])<=1e-10,raw=q))
        valid=dict(t_valid=None,status='recomputed_from_20260927_grid',reference_t_valid=rec['t_valid'])
        reliable=[q for q in pts if min(abs(q['shift']),alpha*q['t']**8)>FLOOR]
        first=reliable[0]
        if abs(abs(first['shift'])/(alpha*first['t']**8)-1)<=.1:
            last=first
            for q in pts[pts.index(first)+1:]:
                if abs(abs(q['shift'])/(alpha*q['t']**8)-1)>.1:
                    valid.update(t_valid=last['t'],boundary_bracket=[last['t'],q['t']]);break
                last=q
    else:
        path=BASE.parent/f'server_cost_validity/H{h}_wide_direct_validation.json';d=read(path);r=d['results'][label]
        alpha=EPS/(9*rec['t_ana']**8);tana=rec['t_ana'];energy=d['system']['ground_energy_without_constant_hartree']
        pts=[dict(t=t,shift=q['selected_effective_energy_hartree']-energy,overlap=q['selected_ground_state_overlap_probability'],branch_agreement=None,raw=q) for t,q in zip(r['times'],r['points'])]
        valid=dict(t_valid=rec['t_valid'],status='published_legacy_boundary',reference_source='pf_cost_rejection_tests.json')
        # Keep the published boundary and explicitly expose a recomputation with
        # the coefficient paired with t_ana; historical H2 mixes two fits.
        last=None
        for q in pts:
            if min(abs(q['shift']),alpha*q['t']**8)<=FLOOR:continue
            if abs(abs(q['shift'])/(alpha*q['t']**8)-1)>.1:
                valid.update(recomputed_t_valid=last['t'] if last else None,recomputed_failure=q['t']);break
            last=q
    return dict(h=h,alias='y8',label=label,sector='H2_published' if h==2 else f'H{h}',source=str(path.relative_to(ROOT)),
        alpha=alpha,p=8,alpha_source=(str(path.relative_to(ROOT))+'#fixed_order_alpha' if h==6 else 'pf_cost_rejection_tests.json#epsilon_E/(9*t_ana^8)'),
        t_ana=tana,n_rot=DECOMPO_NUM[f'H{h}'][label],validity=valid,points=pts)

def all_curves():
    rows=[]
    for h in (2,4,5,6,8):
        rows+=native_curves(h)
        if h!=8:rows.append(published_curve(h))
    return rows

def events(row):
    pts=row['points'];low=next((i for i,q in enumerate(pts) if q['overlap']<.99),None)
    valid=row['validity'];fail=valid.get('boundary_bracket',[None,None])[1]
    if fail is None:fail=valid.get('first_reliable_time')
    if fail is None:fail=valid.get('recomputed_failure')
    failure=next((q for q in pts if fail is not None and abs(q['t']-fail)<1e-12),None)
    return dict(first_low=pts[low] if low is not None else None,
        low_bracket=[pts[low-1]['t'] if low else None,pts[low]['t']] if low is not None else None,
        failure=failure,last_sample=pts[-1]['t'])

def preview():
    for key in ('H2','H2_published','H4','H5','H6','H8'):
        with (SCRATCH/f'{key}.pkl').open('rb') as f:d=pickle.load(f)
        e=d['energies'];width=e[-1]-e[0]
        print('WIDTH',key,'dimension',len(e),'E0=',e[0],'Emax=',e[-1],'W=',width,'tau=',2*np.pi/width,flush=True)
    for row in all_curves():
        ev=events(row)
        with (SCRATCH/f"{row['sector']}.pkl").open('rb') as f:d=pickle.load(f)
        tau=2*np.pi/(d['energies'][-1]-d['energies'][0])
        print('ROW',row['h'],row['alias'],'low',ev['first_low']['t'] if ev['first_low'] else None,'valid',row['validity'].get('t_valid'),'firstfail',ev['failure']['t'] if ev['failure'] else None,'tana/tau',row['t_ana']/tau,flush=True)

def event_targets(row,system):
    ev=events(row);tau=2*np.pi/(system['energies'][-1]-system['energies'][0]);targets={}
    if ev['first_low'] is not None:targets['first_overlap_below_0p99']=ev['first_low']
    if ev['failure'] is not None and ev['failure']['t']>=tau:targets['first_10pct_failure']=ev['failure']
    return targets

def recovered_pf(row,point,system,builder=None):
    t=point['t'];dest=SCRATCH/f"pf_H{row['h']}_{row['alias']}_{float(t).hex()}.pkl"
    if dest.exists():
        with dest.open('rb') as f:return pickle.load(f)
    start=time.perf_counter()
    if row['h']==8:
        folder=OUT/'runtime/points'/point_key(row['alias'],t,point['raw']['eigensolver_method'])
        data=load_point(folder);values=data['values'];vectors=data['vectors'];selected=point['raw']['selected_schur_index']
        metrics=dict(source='saved_full_PF_eigensystem',new_pf_diagonalization=False,selected_residual=float(data['residuals'][selected]),
            full_spectrum_residual=float(np.linalg.norm(data['residuals'])),saved_folder=str(folder.relative_to(ROOT)))
    else:
        u=builder.build(_get_s2_sequence(row['label']),t)
        built=time.perf_counter();tri,vectors=schur(u,output='complex',check_finite=False);values=np.diag(tri).copy()
        wanted=np.exp(1j*(system['system']['energy']+point['shift'])*t)
        distances=abs(np.angle(values/wanted));selected=int(np.argmin(distances))
        repro=float(distances[selected]/t)
        residual=float(np.linalg.norm(u@vectors[:,selected]-values[selected]*vectors[:,selected]))
        metrics=dict(source='recomputed_existing_time_to_recover_unsaved_vectors',new_pf_diagonalization=True,
            selected_residual=residual,full_spectrum_residual=float(np.linalg.norm(tri-np.diag(values))),
            energy_shift_reproduction_difference_hartree=repro,build_seconds=built-start,total_seconds=time.perf_counter()-start)
    state=system['system']['state'];ground=abs(vectors.conj().T@state)**2
    competitors=[i for i in np.argsort(ground)[::-1] if i!=selected]
    other=int(competitors[0]);vector=np.asarray(vectors[:,selected]);other_vector=np.asarray(vectors[:,other])
    coefficients=system['vectors'].conj().T@vector;weights=abs(coefficients)**2
    energies=system['energies'];cuts=np.r_[0,np.flatnonzero(np.diff(energies)>1e-9)+1,len(energies)]
    groups=[]
    for lo,hi in zip(cuts,cuts[1:]):
        groups.append(dict(indices=[int(lo),int(hi-1)],energy=float(np.mean(energies[lo:hi])),weight=float(sum(weights[lo:hi]))))
    excited=sorted(groups[1:],key=lambda g:g['weight'],reverse=True)
    leak=float(sum(weights[1:]));dominant=excited[0];gap=dominant['energy']-energies[0];ratio=t*gap/(2*np.pi)
    other_weights=abs(system['vectors'].conj().T@other_vector)**2
    a,b=dominant['indices'];other_dominant_weight=float(sum(other_weights[a:b+1]))
    identified=leak>1e-8 and dominant['weight']/leak>=.8
    n=max(1,round(ratio))
    answer=dict(time=t,selected_ground_overlap=float(ground[selected]),saved_ground_overlap=point['overlap'],
        selected_schur_index=int(selected),partner_pf_index=other,partner_pf_ground_overlap=float(ground[other]),
        pair_ground_weight=float(ground[selected]+ground[other]),pair_phase_gap_radians=float(abs(np.angle(values[other]/values[selected]))),
        total_excited_weight=leak,dominant_excited_fraction=float(dominant['weight']/leak) if leak>0 else None,
        dominant_partner_identified=bool(identified),partner_energy_without_identity_hartree=dominant['energy'],
        partner_energy_hartree=dominant['energy']+system['identity_offset'],partner_exact_indices=dominant['indices'],
        partner_eigenstate_weight=dominant['weight'],partner_pf_weight_in_same_exact_eigenspace=other_dominant_weight,
        predicted_first_crossing_time=float(2*np.pi/gap),time_over_predicted_first_crossing=float(ratio),
        nearest_wrap_integer=int(n),relative_time_difference_to_nearest_wrap=float(ratio/n-1),
        within_5pct_of_first_wrap=bool(identified and abs(ratio-1)<=.05),
        maximum_energy_eigenspace_weight=groups[-1]['weight'],top_excited_eigenspaces=excited[:3],metrics=metrics)
    dump_pickle(dest,answer)
    print('PARTNER',row['h'],row['alias'],t,'k',dominant['indices'],'fraction',answer['dominant_excited_fraction'],'t/tstar',ratio,'identified',identified,'seconds',time.perf_counter()-start,flush=True)
    return answer

def partner_job(h):
    rows=[row for row in all_curves() if row['h']==h]
    builders={};systems={};result=[]
    gpu=reference_module(REF/'src/trotterlib/sector_pf_gpu.py',f'trotterlib.phase_wrap_gpu_{h}') if h!=8 else None
    try:
        for row in rows:
            sector=row['sector']
            if sector not in systems:
                with (SCRATCH/f'{sector}.pkl').open('rb') as f:systems[sector]=pickle.load(f)
            system=systems[sector]
            targets=event_targets(row,system)
            if targets and h!=8 and sector not in builders:builders[sector]=gpu.GpuSectorPFBuilder(system['system']['group_spectra'],logical_device={2:0,4:1,5:2,6:3}[h])
            for kind,q in targets.items():result.append((row['h'],row['alias'],kind,recovered_pf(row,q,system,builders.get(sector))))
    finally:
        for b in builders.values():b.close()
    return result

def partner_stage():
    with ProcessPoolExecutor(max_workers=4,mp_context=get_context('spawn')) as pool:
        futures=[pool.submit(partner_job,h) for h in (2,4,5,6)]
        partner_job(8)
        for f in futures:f.result()

def restricted_h8(rows):
    result={}
    for alias in ('w8','w1016'):
        row=next(r for r in rows if r['h']==8 and r['alias']==alias);pts=row['points']
        accepted=[q for q in pts if q['overlap']>=.99 and q['branch_agreement'] and abs(q['shift'])<EPS]
        cost=lambda q:BETA*row['n_rot']/(q['t']*(EPS-abs(q['shift'])))
        best=min(accepted,key=cost);i=pts.index(best);last=max(q['t'] for q in accepted)
        result[alias]=dict(time=best['t'],cost=cost(best),overlap=best['overlap'],signed_error_hartree=best['shift'],
            n_rot=row['n_rot'],accepted_count=len(accepted),saved_count=len(pts),last_accepted_time=last,
            minimum_at_upper_accepted_endpoint=best['t']==last,next_saved_time=pts[i+1]['t'] if i+1<len(pts) else None,
            next_saved_overlap=pts[i+1]['overlap'] if i+1<len(pts) else None)
    result['tenth_over_eighth']=result['w1016']['cost']/result['w8']['cost']
    bound=BETA*result['w1016']['n_rot']/(result['w1016']['last_accepted_time']*EPS)
    result['tenth_cost_lower_bound_for_t_at_most_last_accepted']=bound
    result['lower_bound_over_eighth']=bound/result['w8']['cost']
    result['scope']='minimum over saved feasible points with overlap>=0.99 and branch disagreement<=1e-10 Ha; no continuous/global optimum claim'
    result['endpoint_caution']='Endpoint cost is not a lower bound on an uncomputed continuous optimum; a separate lower bound beta*N/(t_cap*epsilon) is given for the stated cap.'
    result['new_pf_diagonalizations']=0
    return result

def fmt(x,digits=6):return '—' if x is None else f'{x:.{digits}f}'

def report_stage():
    rows=all_curves();systems={};spectra={};partners=[];table_rows=[]
    for key in ('H2','H2_published','H4','H5','H6','H8'):
        with (SCRATCH/f'{key}.pkl').open('rb') as f:d=pickle.load(f)
        systems[key]=d;e=d['energies'];width=float(e[-1]-e[0]);offset=d['identity_offset']
        info=d['sector'];small={k:v for k,v in info.items() if k in ('kind','dimension','population_counts','state_vector_ordering_convention','population','additional_z2')}
        spectra[key]=dict(dimension=len(e),E0=float(e[0]+offset),Emax=float(e[-1]+offset),identity_offset=offset,
            E0_without_identity=float(e[0]),Emax_without_identity=float(e[-1]),W=width,t_fold=2*np.pi/width,
            full_eigensystem_residual=d['full_spectrum_residual'],ground_overlap_with_saved_state=d['ground_overlap'],
            preparation_seconds=d['preparation_seconds'],sector=small)
    for row in rows:
        key=row['sector'];system=systems[key];tau=spectra[key]['t_fold'];ev=events(row);valid=row['validity'];low=ev['first_low'];failure=ev['failure']
        r=dict(system=f"H{row['h']}",formula=row['alias'],sector=key,alpha=row['alpha'],p=row['p'],alpha_source=row['alpha_source'],
            n_rot=row['n_rot'],source=row['source'],t_ana=row['t_ana'],t_ana_over_t_fold=row['t_ana']/tau,
            t_overlap=low['t'] if low else None,overlap_at_first_drop=low['overlap'] if low else None,
            t_overlap_over_t_fold=low['t']/tau if low else None,overlap_bracket=ev['low_bracket'],last_sample=ev['last_sample'],
            t_valid=valid.get('t_valid'),t_valid_over_t_fold=valid['t_valid']/tau if valid.get('t_valid') else None,
            t_first_10pct_failure=failure['t'] if failure else None,
            t_first_10pct_failure_over_t_fold=failure['t']/tau if failure else None,validity=valid,saved_points=len(row['points']))
        if failure:r['ratio_at_first_failure']=abs(failure['shift'])/(row['alpha']*failure['t']**row['p'])
        for kind,q in event_targets(row,system).items():
            path=SCRATCH/f"pf_H{row['h']}_{row['alias']}_{float(q['t']).hex()}.pkl"
            with path.open('rb') as f:partner=pickle.load(f)
            existing=next((i for i,a in enumerate(partners) if a['system']==r['system'] and a['formula']==r['formula'] and a['time']==q['t']),None)
            if existing is None:
                partner=dict(system=r['system'],formula=r['formula'],event_kinds=[kind],**partner)
                if row['h']==8:
                    raw=load_point(ROOT/partner['metrics']['saved_folder'])
                    partner['metrics']['partner_eigenpair_residual']=float(raw['residuals'][partner['partner_pf_index']])
                    assert max(partner['metrics']['selected_residual'],partner['metrics']['partner_eigenpair_residual'])<1e-10
                partners.append(partner);existing=len(partners)-1
            elif kind not in partners[existing]['event_kinds']:partners[existing]['event_kinds'].append(kind)
            r[kind+'_partner_index']=existing
        if failure and failure['t']<tau:r['first_failure_relation']='before_any_exact_ground_phase_wrap'
        elif failure:r['first_failure_relation']='at_or_after_first_possible_exact_wrap; see projection'
        if low is None:r['overlap_status']='no drop on saved grid; narrow unsampled dips not excluded'
        table_rows.append(r)
    spectra['H8']['source']='saved H8_compact.pkl group_matrices sum'
    spectra['H2_published']['note']='Legacy published PF used dimension 6; v2 dimension 4. Their extrema and W coincide.'
    protocol=read(OUT/'protocol.json')
    frozen_hash=hashlib.sha256((OUT/'runtime/H8_compact.pkl').read_bytes()).hexdigest()
    assert frozen_hash==protocol['physics_cache_sha256']
    conditional=restricted_h8(rows);new=[p['metrics'] for p in partners if p['metrics']['new_pf_diagonalization']]
    calculations=dict(new_full_Hamiltonian_eigensystems=6,spectral_preparation_task_seconds_sum=sum(d['preparation_seconds'] for d in systems.values()),
        spectral_preparation_largest_task_seconds=max(d['preparation_seconds'] for d in systems.values()),spectral_preparation_parallel_workers=4,
        new_PF_diagonalizations=len(new),new_H8_PF_diagonalizations=0,PF_solve_task_seconds_sum=sum(p['total_seconds'] for p in new),
        maximum_PF_solve_seconds=max(p['total_seconds'] for p in new),reused_H8_full_PF_eigensystems=sum(not p['metrics']['new_pf_diagonalization'] for p in partners),
        PF_execution='4 processes, GPUs 0..3, complex128, full CPU Schur, 1 BLAS thread each',
        times_are='sum/max of measured task durations, not summed parallel wall time; PF points reuse existing times',all_new_PF_times_previously_sampled=True)
    for source in [ROOT/'src/trotterlib/config.py',REF/'review_response/hchain_direct_sector_v1_1.py',REF/'src/trotterlib/sector_pf_gpu.py',ROOT/'review_response/run_poster_h8.py',ROOT/'review_response/poster_h8_accelerated.py']:
        SOURCES[str(source.relative_to(ROOT))]=hashlib.sha256(source.read_bytes()).hexdigest()
    for row in rows:
        source=ROOT/row['alpha_source']
        if source.is_file():SOURCES[str(source.relative_to(ROOT))]=hashlib.sha256(source.read_bytes()).hexdigest()
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in SOURCES.items())
    assert all(d['ground_overlap']>1-1e-8 and d['full_spectrum_residual']<1e-10 for d in systems.values())
    assert all(abs(p['selected_ground_overlap']-p['saved_ground_overlap'])<1e-6 for p in partners)
    assert all(p['metrics']['selected_residual']<1e-10 and p['metrics'].get('energy_shift_reproduction_difference_hartree',0)<1e-10 for p in partners)
    payload=dict(schema_version=1,baseline_commit='5e006b53d9439f3502209bcad26e21fb298745bd',epsilon_E=EPS,beta=BETA,
        definitions=dict(energies='Hartree; E0/Emax include identity and nuclear energy; without-identity values match stored direct-PF convention.',
            t_fold='2*pi/W: first possible exact ground/excited eigenphase alias in the actual numerical sector',
            t_overlap='first SAVED point with tracked PF eigenvector exact-ground overlap probability <0.99',
            t_valid='stored last passing point in first contiguous 10% interval; first failure is separate',noise_floor=FLOOR,
            phase_wrap='(E_k-E0)*t=2*pi*n, integer n>=1; original first-wrap hypothesis sets n=1',
            partner_identification='project selected PF vector onto complete exact-H eigenspaces (degeneracy tolerance 1e-9 Ha); identify only if >80% of excited weight and total excited weight>1e-8',
            no_nearest_energy_fitting=True,branch_agreement_tolerance_hartree=1e-10),
        spectra=spectra,rows=table_rows,partners=partners,restricted_H8_tenth=conditional,computations=calculations,
        findings=dict(width_only_first_wrap_universal_explanation_supported=False,
            reason='Observed overlap losses generally differ from 2*pi/W. Actual dominant partners explain many losses at n=1 and some at n=2; many 10% departures occur before 2*pi/W.',
            limitations=['Only saved times; narrow earlier avoided crossings may have been missed.',
                'Spectral matching plus actual PF mixing supports resonance association, not certified causality or earliest continuous-time jump.',
                'H4 v2 at 10% failure has multiple excited components; no unique partner claimed.',
                'H2 published legacy t_valid uses another alpha than its t_ana; old and recomputed boundaries retained.',
                'H6 published dense boundary source absent; 2026-09-27 grid used with old boundary retained.']),
        validation=dict(pass_=True,inputs_unchanged=True,frozen_H8_physics_cache_sha256=frozen_hash,phase_reproduction_tolerance_hartree=1e-10,used_eigenpair_residual_tolerance=1e-10,
            source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),inputs_sha256=SOURCES)
    # Alpha paths already occur in every row; index their hashes by row identity.
    payload['alpha_files_sha256']={r['system']+'/'+r['formula']:SOURCES[r['alpha_source']] for r in table_rows if r['alpha_source'] in SOURCES}
    alpha_paths={r['alpha_source'] for r in table_rows}
    payload['inputs_sha256']={path:sha for path,sha in SOURCES.items() if path not in alpha_paths}
    # Avoid repeating derivable diagnostics; retain the multi-state exception.
    for partner in partners:
        for field in ('selected_schur_index','partner_pf_index','saved_ground_overlap','within_5pct_of_first_wrap','partner_energy_without_identity_hartree','partner_eigenstate_weight'):
            partner.pop(field,None)
        if partner['dominant_partner_identified']:partner.pop('top_excited_eigenspaces',None)
        partner['metrics'].pop('saved_folder',None)
        partner['metrics']['source']='recomputed_saved_time' if partner['metrics']['new_pf_diagonalization'] else 'saved_PF_cache'
    encoded=json.dumps(payload,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n'
    print('JSON_SECTION_BYTES',{k:len(json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()) for k,v in payload.items()},flush=True)
    assert len(encoded.encode())<=50000,len(encoded.encode())
    (OUT/'phase_wrapping_analysis.json').write_text(encoded);render_report(payload,len(encoded.encode()))
    print('REPORT JSON bytes',len(encoded.encode()),'computations',calculations,'restricted ratio',conditional['tenth_over_eighth'],flush=True)

def render_report(data,byte_count):
    spectra=data['spectra'];rows=data['rows'];partners=data['partners'];c=data['restricted_H8_tenth'];calc=data['computations']
    energy=['| 系 | セクター次元 | E0 (Ha) | Emax (Ha) | W (Ha) | 2π/W |','|---|---:|---:|---:|---:|---:|']
    for key in ('H2','H4','H5','H6','H8'):
        s=spectra[key];energy.append(f"| {key} | {s['dimension']} | {s['E0']:.9f} | {s['Emax']:.9f} | {s['W']:.9f} | {s['t_fold']:.9f} |")
    table=['| 系 | PF | t0.99 | t0.99 W/2π | t_valid | t_valid W/2π | 初回10%失敗 W/2π | t_ana W/2π |','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:table.append(f"| {r['system']} | {r['formula']} | {fmt(r['t_overlap'])} | {fmt(r['t_overlap_over_t_fold'],4)} | {fmt(r['t_valid'])} | {fmt(r['t_valid_over_t_fold'],4)} | {fmt(r['t_first_10pct_failure_over_t_fold'],4)} | {fmt(r['t_ana_over_t_fold'],4)} |")
    candidate=['| 系 | PF・事象 | 観測t | 相手k（0始まり） | E_k (Ha) | 2π/(E_k−E0) | 観測t/t* | 励起重み中の相手割合 |','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in partners:
        event='重なり' if 'first_overlap_below_0p99' in r['event_kinds'] else '10%逸脱'
        k=str(r['partner_exact_indices'][0])+('（候補・非一意）' if not r['dominant_partner_identified'] else '')
        candidate.append(f"| {r['system']} | {r['formula']}・{event} | {r['time']:.9f} | {k} | {r['partner_energy_hartree']:.9f} | {r['predicted_first_crossing_time']:.9f} | {r['time_over_predicted_first_crossing']:.9f} | {r['dominant_excited_fraction']:.6f} |")
    text=f'''# H8追加監査：位相折り返しとPF誤差

観測された重なり低下を一律に「セクター幅による最初の折り返し2π/W」と置く仮説は支持されない。一方、実際に混ざる相手をPF固有ベクトルから調べると、個別のエネルギー差による1周目または2周目の位相一致に対応する例が多い。10%適合域を失う原因を、すべてこの共鳴で説明することもできない。
基準commitは5e006b5。既存成果物は変更せず本報告を追加。作図用結果JSONはphase_wrapping_analysis.jsonの1個（{byte_count:,} bytes、50 KB以下）。

## 実計算セクターの厳密スペクトル

{chr(10).join(energy)}

E0/Emaxは恒等項と核反発を含む全エネルギー。元のPF計算は恒等項を除いたH−cIなので、そのE0/EmaxとcもJSONに保存。Wと比較時刻はcに依存しない。H2出版版の旧セクターは次元6、v2は次元4だが上下端とWは一致。H8は固定人口4900からPF全群に共通な既存Z2の2468次元へ制限した実セクターで、別セクターのEmaxを混ぜていない。
保存済み完全Hスペクトルがなかったため、小さい系は元の順序対応sector-preparationで再構築、H8は保存済みgroup_matricesの和を全対角化した。全固有対残差の最大は{max(s['full_eigensystem_residual'] for s in spectra.values()):.3e}。保存基底状態との重なりは全系1−1e−8以上。

## 重なり低下、10%境界と折り返し

w8=8次v2、w1016=10次v2、wmy4=新4次、y8=出版版8次。t0.99は重なり確率が初めて0.99未満になった保存点。Wで規格化した値は1未満なら最初の折り返しより手前、1より大きければ先。欠測の狭い共鳴を除外した連続時間の最初の点ではない。—は格子上未観測、または短時間の適合域未確定。

{chr(10).join(table)}

t_validは最後の合格点で、最初の失敗点と異なる。JSONには両方と境界区間を保存。10次H4/H5/H6/H8は最初の解像された短時間点が10%を外れ、t_valid未確定。後から再適合する窓に飛ばさない。
H2出版版は旧t_valid=1.631502286を主表に保持したが、旧t_anaと同じαへそろえると最後の合格1.881426370、最初の失敗2.169635442。旧境界はwide解析の別αに由来し、主表のt_validと今回の初回失敗は同一αの対ではない。どちらも2π/Wより前。
H6出版版は9月27日格子でt_valid=1.715194464、初回失敗1.905771627。旧密境界1.810484385はJSONに参照値として残す。元ファイル未収録のため再検証していない。
新4次は全系で10%逸脱が2π/Wより前（H8:0.702161対0.827385）。H2の8次/10次、H4/H5/H6/H8の10次の初回逸脱も折り返し前。このため「全ての10%逸脱＝厳密Hの2π折り返し」は合わない。固定αのfit窓・高次項、短時間端の係数丸め/数値感度は別の可能性だが、本監査では原因を一意に決めない。

## 実際に混ざる相手の同定

PF固有ベクトルを厳密Hの全固有空間へ射影し、励起重みの80%以上が1つに集まる場合だけ主相手と呼ぶ。時刻に合わせた最近傍エネルギー選びではない。射影重み、相手PF枝との位相間隔、2枝に含まれる基底重み、残差もJSONに保存。kは固有値昇順の0始まり。

{chr(10).join(candidate)}

H8・8次の最初の重なり低下はk=1234との1周目（t*=1.800167474、観測1.800174210、差+0.000374%）。10%逸脱は別のk=1224との1周目（t*=1.804832339、観測1.804841431）に対応する。これらを同じ交差とみなさない。
H8・10次の最初の観測低下はk=2281の2周目（t*=1.209534408、観測2.419047261≈2t*）。H2出版版、H4の8次v2、H5/H6出版版にも2周目に近い例がある。これは「全状態中の最初の交差」や「同じ相手との1周目が必ず最初の観測低下」という仮説と異なる。
H5の8次v2、H6の8次/10次、H8新4次、H4出版版などは、別の相手との1周目に近い。Emaxの状態が常に主要な相手になるわけではない。位相一致だけでなく、PFの結合強度、回避交差の幅、格子間隔にも依存する。
H4・8次の10%逸脱は主候補の割合が約61%で、相手は一意に同定できない。最初の重なり低下点では別のk=35（Emax）が支配的で約2周目に近い。
保存点だけでは、より早い狭い交差を見落としていないことや、相手PF枝をt→0まで連続追跡すると確実にこのkへ接続することを証明しない。射影と位相一致は共鳴への対応を支持するが、因果の厳密な証明ではない。

## H8・10次の条件付き最小値

重なり≥0.99かつシフトの枝照合差≤1e−10 Ha、コスト定義可能な保存点に限定。296点中{c['w1016']['accepted_count']}点が合格し、最小は許容保存点の上端：

- t={c['w1016']['time']:.15f}、重なり={c['w1016']['overlap']:.12f}。
- 総回転数={c['w1016']['cost']:.9f}、同条件の8次最小={c['w8']['cost']:.9f}。
- 10次/8次={c['tenth_over_eighth']:.12f}。8次最小は条件内側。
- 次の保存点t={c['w1016']['next_saved_time']:.15f}は重なり={c['w1016']['next_saved_overlap']:.9f}で除外。

「上端での値」であり、保存した許容点集合にはこれより低い値はない。ただし未計算の連続時刻の最小値の下限とは言えず、追加点で下がる可能性がある。
厳密な下限が必要ならt≤t_cap={c['w1016']['last_accepted_time']:.15f}に範囲を固定し、e≥0よりF≥βN/(t_cap ε_E)={c['tenth_cost_lower_bound_for_t_at_most_last_accepted']:.9f}を使える。この下限の8次比は{c['lower_bound_over_eighth']:.12f}>1。ただしcap以降に再び条件を満たす未計算点がないとは主張しない。
条件付き最小値のための新規対角化は0点。前報1.3158は不一致の最小点を含む参考値で、今回の条件付き1.4747と区別して前報を保存する。

## 追加計算、再現と限界

- 厳密H全対角化：6セクター、準備込みタスク時間合計{calc['spectral_preparation_task_seconds_sum']:.3f}秒、最大{calc['spectral_preparation_largest_task_seconds']:.3f}秒。小さい系4並列とH8を同時実行。
- 固有ベクトル未保存の既存時刻PF再対角化：{calc['new_PF_diagonalizations']}点、4 GPU並列。タスク時間合計{calc['PF_solve_task_seconds_sum']:.3f}秒、1点最大{calc['maximum_PF_solve_seconds']:.3f}秒。全シフトを1e−10 Ha以内で再現。
- H8のPF追加対角化は0点、保存済み完全固有系4点を再利用。厳密Hのスペクトルは別途新規計算。
- complex128、OMP/OPENBLAS/MKL各1、TROTTER_QISKIT_DEVICE=GPU、CUDA_VISIBLE_DEVICES=0,1,2,3。時間合計は並列タスクの和で、実経過時間ではない。

実行は共有Python環境で`PYTHONPATH=/tmp/poster-finite-time-deps:src:review_response OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=0,1,2,3 /home/AbeHiromu/venvs/trotter-common/bin/python review_response/analyze_poster_phase_wrapping.py prepare`、続いて`partners`と`report`。大きい固有ベクトル等はruntime/phase_wrap_analysisに保管しGitに含めない。H8の再現には既存runtime/H8_compact.pklとruntime/pointsが必要で、それらがない環境では元のH8 runnerによる再計算が必要。入力と実装ハッシュは結果JSONに保存。
未完事項：欠測区間を含む最初の共鳴の厳密な位置、H4・8次の10%逸脱の単一相手、旧H6境界生データの再検証、連続時間での制約付き大域最小。推測で補完していない。
'''
    (OUT/'phase_wrapping_report.md').write_text(text)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','preview','partners','report']);args=parser.parse_args();SCRATCH.mkdir(parents=True,exist_ok=True)
    if args.stage=='prepare':
        with ProcessPoolExecutor(max_workers=4,mp_context=get_context('spawn')) as pool:
            pending=pool.map(prep_job,[(2,False),(2,True),(4,False),(5,False),(6,False)])
            prepare_h8()
            list(pending)
    if args.stage=='partners':partner_stage()
    if args.stage=='report':report_stage()
    preview()
if __name__=='__main__':main()
