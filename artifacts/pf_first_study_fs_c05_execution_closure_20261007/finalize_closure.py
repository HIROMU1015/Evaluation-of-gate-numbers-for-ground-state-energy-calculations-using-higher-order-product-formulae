"""Record passed tests/scalar-only preflight and seal the additive package."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import closure_adapter as a
import build_closure as build

def put(name,value):
    build.write(name,value)

def main():
    log=Path('/tmp/fs-c05-task-20261007/pytest_final.log').read_text()
    assert '114 passed' in log and 'failed' not in log
    put('tests.log','Command: PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 '
        '/home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python -m pytest -q -p no:cacheprovider '
        'artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py '
        'artifacts/pf_first_study_fs_c05_execution_closure_20261007/test_fs_c05.py\n'
        'Scope: existing 74 + new 40; synthetic fixtures and saved scalar arithmetic only.\n'+log)
    saved=json.loads((HERE/'saved_scalar_fixture.json').read_text())
    baseline=json.loads((HERE/'baseline_contract.json').read_text())
    results=[]
    for record,spec in zip(saved['systems'],baseline['systems']):
        actual=a.historical_scalar_fit(record['times'],record['saved_proxy_values'],record['t_ref'],record['t0'])
        difference=np.asarray(actual['coefficient_values'])-np.asarray(record['saved_coefficients'])
        constants=json.loads((HERE/'fs_c1_protocol_v2.json').read_text())['constants']
        recovered_B0=constants['gamma']*constants['beta']*spec['K']/(spec['t0']*(constants['epsilon_E']-abs(record['saved_signed_prediction'])))
        results.append(dict(condition=record['condition'],
            status='SAVED_SCALAR_ARITHMETIC_PASS', native_production_backend_status='NOT_RUN',
            saved_coefficients=record['saved_coefficients'],scalar_refit_coefficients=actual['coefficient_values'],
            coefficient_absolute_differences=abs(difference).tolist(),
            saved_selected_prediction=record['saved_signed_prediction'],
            scalar_refit_selected_prediction=actual['signed_prediction_at_t0'],
            selected_prediction_absolute_difference=abs(actual['signed_prediction_at_t0']-record['saved_signed_prediction']),
            saved_B0=record['saved_B0'], saved_prediction_budget_arithmetic=recovered_B0,
            B0_arithmetic_absolute_difference=abs(recovered_B0-record['saved_B0']),
            arithmetic_assertion='binary64/library arithmetic fixture rtol=2e-14; not M00 backend tolerance',
            training_points=[dict(time=t,saved_proxy=v,new_backend_proxy=None,absolute_difference=None,
                relative_difference=None,allowed_backend_tolerance=None,status='NOT_RUN_SCIENCE_ZERO')
                for t,v in zip(record['times'],record['saved_proxy_values'])],
            preserved_primary=True))
    # Tiny native fixture measurement, never production. New cold object/ledger.
    b0,state0=a.fixture(); b1,state1=a.fixture()
    y0=[b0.proxy(state0,t)['proxy'] for t in [0.1,0.2,0.3]]
    y1=[b1.proxy(state1,t)['proxy'] for t in [0.1,0.2,0.3]]
    assert y0==y1
    put('backend_reproduction_preflight.json',dict(
        production_backend_reproduction='NOT_RUN',backend_ready=False,
        cause='source missing; §31 prohibits new production PF/echo in C0.5',
        original_native_function_bodies_used=True,source_pins='native_source_pins.json',
        saved_scalar_reproduction=results,
        synthetic=dict(status='PASS',arbitrary_state=True,echo_sign=True,PF_norm=True,
            cold_fixture=True,recovery=True,complete_toy_Ritz_cold_replay='test_16: independent 2x2 residual refinement + fit',
            recorded_proxy_cold_difference=0.0,production_inference=False,
            initial_ledger=b0.ledger.snapshot(),cold_ledger=b1.ledger.snapshot()),
        M00_reproduction_tolerance='M00_REPRODUCTION_TOLERANCE_UNCLOSED',
        production_science_actions=0))
    # Diff and source hashes verify old artifacts without decoding truth tables.
    changed=subprocess.check_output(['git','diff','--name-only',build.BASE],cwd=a.ROOT,text=True).splitlines()
    assert changed==[]
    registry=json.loads((HERE/'source_manifest.json').read_text())
    for s in registry['sources']:
        raw=(a.ROOT/s['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==s['sha256']
        assert raw==subprocess.check_output(['git','show',build.BASE+':'+s['path']],cwd=a.ROOT)
    put('verification.json',dict(status='PASS_FOR_C05_AUTHORIZED_SCOPE',
        FS_C1_status='NO_GO_SOURCE_MISSING',base_commit=build.BASE,
        tests={'existing':74,'new':40,'total':114,'passed':114,'failed':0},
        saved_scalar_arithmetic='PASS',production_backend_reproduction='NOT_RUN',
        old_tracked_files_unchanged=True,authority_blobs_hashed=len(registry['sources']),
        production_science_actions=0,production_array_decodes=0,source_regeneration=0,
        raw_FS_C1_truth_opens=0,unapproved_research_changes=0,
        source_recovery='SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT',
        internal_expm_work='unknown/null; accepted cost contract; not zero',
        publication_state_at_creation='pre-commit/pre-push; independent remote receipt follows outside sealed package',
        inspection_limits='No syscall-level global interception. Scope checked by source-pinned tests, explicit read/import paths and command audit.'))
    put('handoff.md','# GPT handoff\n\nRepository: '+build.URL+'\nBranch: pf-first-study-fs-c05-execution-closure-20261007\nBase: '+build.BASE+'\n\n読む順序はREADMEに記載。3-point amendmentと114テストを完了。原本SHA一致は0/2、canonical identityとproduction backend数値契約は未成立。production scienceは0、FS-C1を実行していない。旧成果物は同一blobのまま。\n\nGPT/userに判断してほしい項目: original identity sourceを回収する追加経路、または別source identity/functional equivalenceへの変更を今後承認するか。今回の成果物は後者の設計やscienceを承認しない。FS-C0.5で停止する。\n\n本ファイル作成時点ではpush前。現在の公開状態・40文字commit固定リンク・独立remote取得/hash結果は最終報告と外部receiptに記録する。自己参照commitを捏造しない。pickle、private arrays、.runtime、認証情報の新規公開は0。\n')
    manifest_path=HERE/'publication_manifest.json'
    files=[]
    for p in sorted(HERE.iterdir()):
        if p.is_file() and p != manifest_path:
            raw=p.read_bytes()
            files.append(dict(path=str(p.relative_to(a.ROOT)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    put('publication_manifest.json',dict(repository=build.URL.removeprefix('https://github.com/'),
        base_commit=build.BASE,branch='pf-first-study-fs-c05-execution-closure-20261007',
        files=files,self_exclusion=str(manifest_path.relative_to(a.ROOT)),
        self_exclusion_reason='manifest cannot hash its own final bytes; verified as commit blob independently',
        excluded=['private pickle','production matrix/vector/unitary/exact-state','private recovery','.runtime','secrets'],
        origin_snapshot_policy='source_manifest preserves distinct origin_result_commit and verified_snapshot_commit',
        remote_verification='fetch into independent bare repo; match tip, all new/public authority SHA/blobs; external receipt',
        production_science_actions=0))
    print(json.dumps(dict(new_publication_files=len(files)+1,source_blobs=len(registry['sources']),tests=114,production_science=0)))

if __name__=='__main__':
    main()
