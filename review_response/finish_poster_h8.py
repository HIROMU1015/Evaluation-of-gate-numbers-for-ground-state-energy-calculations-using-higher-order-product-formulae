"""Finish the authorized H8 calculation after the conversation yields.

Wait for the current jobs, resume missing work, validate, make figures/tables,
and publish only this extension on the previously approved working branch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/poster_finite_time_20261116_h8'
PYTHON='/home/AbeHiromu/venvs/trotter-common/bin/python'
ALIASES=('w8','w1016','wmy4')
SCRIPTS=['poster_h8_accelerated.py','run_poster_h8.py','report_poster_h8.py','validate_poster_h8_fold.py','validate_poster_h8_final.py','finish_poster_h8.py']
EXPECTED_HEAD='17b30aa9eefda919f3085e2557c31918fbb3076d'
EXPECTED_PUBLICATION_HEAD=EXPECTED_HEAD


def utc():return datetime.now(timezone.utc).isoformat()
def write(path,payload):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)
def command(args,log=None,check=True):
    if log:
        with (OUT/log).open('w') as stream:r=subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,env=os.environ)
    else:r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,env=os.environ)
    if check and r.returncode:raise RuntimeError(f'Command failed ({r.returncode}): {args}; log={log}; {getattr(r,"stderr","")}')
    return r

def alive(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except (FileNotFoundError,ProcessLookupError):return False

def progress(stage,**extra):
    rows={}
    for alias in ALIASES:
        p=OUT/'checkpoints'/f'{alias}.json'
        try:d=json.loads(p.read_text());rows[alias]=dict(point_count=len(d['points']),last_step=d['history'][-1:] )
        except (FileNotFoundError,json.JSONDecodeError):pass
    write(OUT/'background_status.json',dict(stage=stage,updated_at_utc=utc(),progress=rows,**extra))

def valid_raw(alias):
    try:
        d=json.loads((OUT/'raw'/f'H8_{alias}.json').read_text());r=next(iter(d['results']['H8'].values()))
        m=r['direct_diagonalization']['curve']['minimum'];g=r['direct_diagonalization']['diagnostic_gates'];c=r['refinement_convergence'];bracket=c['bracket']
        return bool(m['is_interior_of_sampled_time_range'] and g['matrix_numerics_pass'] and c['relative_cost_change']<1e-5 and c['relative_time_change']<1e-4 and 1e-12<(bracket[1]-bracket[0])/m['time']<1e-4)
    except (FileNotFoundError,json.JSONDecodeError,KeyError,StopIteration):return False

def publish(files):
    branch=command(['git','branch','--show-current']).stdout.strip();head=command(['git','rev-parse','HEAD']).stdout.strip()
    staged=command(['git','diff','--cached','--name-only']).stdout.strip()
    if branch!='poster-finite-time-20261116' or head!=EXPECTED_PUBLICATION_HEAD or staged:
        return dict(status='saved_not_published',reason='Branch/HEAD/staging changed while calculation ran; user work left untouched.',branch=branch,head=head)
    command(['git','add','--',*files])
    command(['git','-c','core.whitespace=-blank-at-eof','diff','--cached','--check'])
    command(['git','commit','-m','Add accelerated parallel H8 finite-time poster validation'],log='publication_commit.log')
    commit=command(['git','rev-parse','HEAD']).stdout.strip()
    push=command(['git','push','-u','origin','poster-finite-time-20261116'],log='publication_push.log',check=False)
    if push.returncode:return dict(status='committed_push_failed',commit=commit,reason='See publication_push.log; no authentication secrets are printed.')
    remote=command(['git','ls-remote','--heads','origin','refs/heads/poster-finite-time-20261116']).stdout.split()[0]
    if remote!=commit:raise RuntimeError('Remote head does not equal result commit')
    return dict(status='pushed',commit=commit,branch=branch,url='https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/tree/poster-finite-time-20261116/artifacts/poster_finite_time_20261116_h8')

def main():
    global EXPECTED_PUBLICATION_HEAD
    parser=argparse.ArgumentParser();parser.add_argument('--pids',type=int,nargs='*',default=[]);parser.add_argument('--publish',action='store_true');parser.add_argument('--expected-publication-head',default=EXPECTED_HEAD);args=parser.parse_args()
    EXPECTED_PUBLICATION_HEAD=args.expected_publication_head
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='/tmp/poster-finite-time-deps:'+str(ROOT/'src')+':'+str(ROOT/'review_response'),
        TROTTER_PROJECT_ROOT=str(ROOT),TROTTER_QISKIT_DEVICE='GPU',TROTTER_QISKIT_AER_PRECISION='double',CUDA_VISIBLE_DEVICES='0,1,2,3,4,5,6,7',
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR='/tmp/poster-h8-matplotlib')
    try:
        while any(alive(p) for p in args.pids):
            progress('calculating',active_pids=[p for p in args.pids if alive(p)]);time.sleep(30)
        for attempt in range(2):
            missing=[a for a in ALIASES if not valid_raw(a)]
            if not missing:break
            progress('resuming',attempt=attempt+1,aliases=missing)
            command([PYTHON,'-u','review_response/run_poster_h8.py','sweep','--aliases',*missing,'--devices','0','1','2','3','4','5','6','7',
                     '--parallel-formulas','--aggregate-name',f'resume_{attempt+1}_analysis.json'],log=f'resume_{attempt+1}.log')
        if not all(valid_raw(a) for a in ALIASES):raise RuntimeError('At least one formula did not pass convergence/numerical checks; raw checkpoints retained')
        progress('validating_optima')
        command([PYTHON,'-u','review_response/validate_poster_h8_final.py'],log='final_schur_validation.log')
        progress('generating_reports')
        # Reconstruct the aggregate after all writers have stopped.
        aggregates=[OUT/'wide_time_cost_analysis.json',OUT/'remaining_formulas_analysis.json',OUT/'resume_1_analysis.json',OUT/'resume_2_analysis.json']
        data=next(json.loads(p.read_text()) for p in aggregates if p.exists())
        data['results']={'H8':{}}
        for alias in ALIASES:data['results']['H8'].update(json.loads((OUT/'raw'/f'H8_{alias}.json').read_text())['results']['H8'])
        write(OUT/'wide_time_cost_analysis.json',data)
        command([PYTHON,'review_response/report_poster_h8.py'],log='report_generation.log')
        for name in ['acceleration_validation.json','cost_identity.json','fast_solver_validation.json','fold_equivalence.json','final_schur_validation.json','validation.json']:
            if not json.loads((OUT/name).read_text()).get('pass_'):raise RuntimeError(f'Validation failed: {name}')
        prior=ROOT/'artifacts/poster_finite_time_20261116'
        for row in json.loads((prior/'references/baseline_input_manifest.json').read_text()):
            if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError(f'Baseline input changed: {row["path"]}')
        for r in data['results']['H8'].values():
            path=ROOT/r['initial_fit']['source']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=r['initial_fit']['sha256']:raise RuntimeError('Original alpha file changed')
        write(OUT/'COMPLETED.json',dict(completed_at_utc=utc(),systems=['H8'],aliases=list(ALIASES),validation_pass=True,
              previous_inputs_unchanged=True,report='report.md',summary='summary.md',runtime_excluded_from_publication=True))
        excluded={'manifest.json','background_status.json','PUBLICATION.json','finish.log','publication_commit.log','publication_push.log'}
        files=sorted(p for p in OUT.rglob('*') if p.is_file() and 'runtime' not in p.relative_to(OUT).parts and p.name not in excluded)
        scripts=[ROOT/'review_response'/n for n in SCRIPTS]
        for p in scripts:compile(p.read_text(),str(p),'exec')
        manifest=dict(baseline_commit='20d64c2',poster_parent_commit=EXPECTED_HEAD,complete_scope='H8 with earlier H2/H4/H6 and reference H5 unchanged',
            files=[dict(path=str(p.relative_to(OUT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],
            scripts=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in scripts])
        write(OUT/'manifest.json',manifest)
        published=publish([str(p.relative_to(ROOT)) for p in files+scripts+[OUT/'manifest.json']]) if args.publish else dict(status='saved_locally')
        write(OUT/'PUBLICATION.json',published)
        progress('complete',publication=published,report=(OUT/'report.md').read_text())
    except BaseException as error:
        write(OUT/'FAILED.json',dict(failed_at_utc=utc(),error=str(error),checkpoints_retained=True))
        progress('failed',error=str(error));raise

if __name__=='__main__':main()
