"""Gated, distributed exact H8/H9 validation with the e4bcd03 fit protocol."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import time
import traceback

import numpy as np
import run_gpu_m3_predictability_h7 as base
from trotterlib.fit_window import rolling_loglog_fits

GRID = np.geomspace(0.06, 0.80, 15)


def qualify(times, errors):
    windows = rolling_loglog_fits(np.asarray(times), np.asarray(errors),
                                 formal_order=4, noise_floor=5e-13, window_size=5)
    eligible = [w for w in windows if w['order_deviation'] <= .2 and w['r2'] >= .999]
    selected = min(eligible, key=lambda w: w['start_index'], default=None)
    return {'qualified': selected is not None, 'selected_window': selected,
            'evaluated_windows': windows, 'times': list(times), 'errors_hartree': list(errors),
            'noise_floor': 5e-13, 'order_tolerance': .2, 'minimum_r2': .999,
            'uncomputed_time_count': 15-len(times)}


def metrics(points, model_cost, qualified):
    minimum = min((p['direct_cost'] for p in points if p['direct_cost'] is not None), default=None)
    schedule = next(p['direct_cost'] for p in points if p['relative_time'] == 1.)
    result = base._summarize_points(points, model_cost) if minimum is not None else {}
    result.update(eta_schedule=None if schedule is None else abs(model_cost-schedule)/schedule,
                  eta_grid=None if minimum is None else abs(model_cost-minimum)/minimum,
                  eta_choice=None if minimum is None or schedule is None else (schedule-minimum)/minimum)
    checks = result.setdefault('frozen_predictability_checks', {})
    checks['short_time_fit_qualified'] = qualified
    checks['minimum_cost_prediction_within_10_percent'] = result['eta_grid'] is not None and result['eta_grid'] <= .1
    result['passed'] = all(checks.values())
    return result


def worker(args):
    path = args.output
    if path.exists():
        raise RuntimeError(f'Refusing to overwrite {path}')
    data = {'status': 'running', 'git': base._git_state(), 'h_chain': args.h,
            'candidate': args.candidate, 'points': [], 'started_at': base._now()}
    base._atomic_json(path, data)
    try:
        with args.system.open('rb') as f:
            system = pickle.load(f)
        candidate = base._candidate_records()[args.candidate]
        data['weights'] = candidate['weights']
        sequence = base._sequence(candidate['weights'])
        errors = []
        start = time.perf_counter()
        for t in GRID:
            evolved = base._apply_pf_components(system['component_spectra'], sequence, t, system['state'])
            z = np.exp(-1j*system['energy']*t)*np.vdot(system['state'], evolved)
            errors.append(abs(float(z.imag/t)))
            if len(errors) >= 5:
                fit = qualify(GRID[:len(errors)], errors)
                data['fit'] = fit
                base._atomic_json(path, data)
                if fit['qualified']:
                    break
        data['fit_seconds'] = time.perf_counter()-start
        if not fit['qualified']:
            data.update(status='fit_failed', passed=False)
            base._atomic_json(path, data)
            return 2
        alpha = fit['selected_window']['fixed_order_alpha']
        tana = base._analytic_time(alpha)
        data.update(alpha=alpha, t_ana=tana)
        import cupy as cp
        cp.get_default_memory_pool().set_limit(size=6*2**30)
        gpu = base._gpu_info(args.gpu)
        data['environment'] = base._environment(gpu)
        data['memory_pool_limit_bytes'] = 6*2**30
        times = [1.] if args.pilot else base.RELATIVE_TIMES
        previous = shift = None
        with base.GpuMemoryMonitor(args.gpu) as monitor:
            for r in times:
                free, _ = cp.cuda.runtime.memGetInfo()
                needed = 3*2**30 if args.h == 8 else 7*2**30
                if free < needed:
                    raise RuntimeError(f'Insufficient free memory: {free} < {needed}; stopping this worker')
                t = r*tana
                print(f'H{args.h} {args.candidate} r={r}: constructing', flush=True)
                unitary, build = base._build_pf_unitary_gpu(system['component_spectra'], sequence, t)
                point, previous, shift = base._analyze_unitary(
                    unitary, system['state'], system['energy'], t, base._rotations(args.h),
                    alpha*t**4, previous, shift)
                point.update(relative_time=r)
                point['timing_seconds'].update(build)
                data['points'].append(point)
                data['gpu_memory'] = monitor.summary(gpu['memory_used_mib'])
                base._atomic_json(path, data)
                print(f'H{args.h} {args.candidate} r={r}: residual={point["eigenpair_residual_2_norm"]:.3e}', flush=True)
                del unitary
        data['gpu_memory'] = monitor.summary(gpu['memory_used_mib'])
        if args.pilot:
            p = data['points'][0]
            data['pilot_passed'] = p['eigenpair_residual_2_norm'] <= 1e-10 and p['ground_overlap_probability'] >= .99
        else:
            model = base._cost(tana, alpha*tana**4, base._rotations(args.h))
            data['summary'] = metrics(data['points'], model, fit['qualified'])
        data.update(status='complete', completed_at=base._now(), total_seconds=time.perf_counter()-start)
        base._atomic_json(path, data)
        return 0
    except Exception:
        data.update(status='failed', traceback=traceback.format_exc())
        base._atomic_json(path, data)
        traceback.print_exc()
        return 1


def recap(out):
    source = base._candidate_records()
    records = []
    for name, candidate in source.items():
        old = candidate['holdout_systems']['H6']
        fit = qualify(old['short_time_fit']['times'], old['short_time_fit']['errors_hartree'])
        points = old['direct_points']
        minimum = min(p['direct_cost'] for p in points if p['direct_cost'] is not None)
        schedule = next(p['direct_cost'] for p in points if p['relative_time']==1.)
        model = old['analytic_model_cost']
        checks = dict(old['analysis_predictability_pass']['checks'])
        checks.update(short_time_fit_qualified=fit['qualified'], minimum_cost_prediction_within_10_percent=abs(model-minimum)/minimum<=.1)
        records.append(dict(h_chain=6, candidate=name, fit=fit, eta_schedule=abs(model-schedule)/schedule,
                            eta_grid=abs(model-minimum)/minimum, eta_choice=(schedule-minimum)/minimum,
                            checks=checks, passed=all(checks.values())))
        oldpath = Path('artifacts/gpu_m3_predictability_h7_20260905_aadbc63')/f'H7_{name}.json'
        old = json.loads(oldpath.read_text())
        points = old['short_time_fit']['points']
        fit = qualify([p['time'] for p in points], [p['perturbative_error_hartree'] for p in points])
        records.append(dict(h_chain=7, candidate=name, fit=fit, summary=metrics(old['points'], old['analytic_model_cost'], fit['qualified'])))
    base._atomic_json(out/'H6_H7_reaggregated.json', {'records':records, 'protocol_commit':'e4bcd03'})


def launch(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    recap(out)
    names = list(base._candidate_records())
    def run(h, gpu, name, pilot=False):
        target = out/f'H{h}_{name}{"_pilot" if pilot else ""}.json'
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
        cmd = [sys.executable, __file__, 'worker', '--h', str(h), '--gpu', str(gpu),
               '--candidate', name, '--system', str(out/f'H{h}.pkl'), '--output', str(target)]
        if pilot:
            cmd.append('--pilot')
        with target.with_suffix('.log').open('x') as log:
            code = subprocess.call(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
        return code, target
    def chain(h, gpus):
        code = base.prepare_system(argparse.Namespace(h_chain=h, processes=4, output=out/f'H{h}.pkl', metadata=out/f'H{h}_system.json'))
        if code:
            return False
        code, target = run(h, gpus[0], names[0], True)
        if code or not json.loads(target.read_text()).get('pilot_passed'):
            return False
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            results = list(pool.map(lambda x: run(h, *x), zip(gpus, names)))
        return all(code==0 for code, _ in results)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(chain, 8, [0,1,2]), pool.submit(chain, 9, [3,5,6])]
        results = [f.result() for f in futures]
    raw = [json.loads(p.read_text()) for p in out.glob('H[89]_m3*.json') if '_pilot' not in p.name]
    base._atomic_json(out/'summary.json', {'status':'complete' if all(results) else 'incomplete', 'results':raw})
    report = ['# H8/H9 fixed m3 validation', '', '| System | Candidate | fit | eta schedule | eta grid | eta choice | pass |', '|---|---|---|---|---|---|---|']
    for r in raw:
        s=r.get('summary', {})
        report.append(f'| H{r["h_chain"]} | {r["candidate"]} | {r.get("fit",{}).get("qualified")} | {s.get("eta_schedule")} | {s.get("eta_grid")} | {s.get("eta_choice")} | {s.get("passed")} |')
    (out/'report.md').write_text('\n'.join(report)+'\n')
    if all(results):
        (out/'COMPLETE').write_text(base._now()+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode', choices=['launch','worker'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--system',type=Path)
    p.add_argument('--h',type=int,choices=[8,9])
    p.add_argument('--gpu',type=int,choices=[0,1,2,3,5,6,7])
    p.add_argument('--candidate')
    p.add_argument('--pilot',action='store_true')
    a=p.parse_args()
    if a.mode=='launch':
        launch(a)
    else:
        sys.exit(worker(a))
