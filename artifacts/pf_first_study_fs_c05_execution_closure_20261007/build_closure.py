"""Build the additive science-zero closure from pinned public metadata/scalars.

No pickle decode, production adapter, raw truth reader or science driver import.
Search observations are explicit external inputs; repeating the builder is not
a new search. Use a fresh destination when reproducing a report.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = '9accc300ba7b8049ae9a1ef870ca4e7c0032e6ae'
C0 = 'artifacts/pf_first_study_fs_c0_20261007'
PRACT = 'artifacts/server_practical_calibration_minimal_20260923_79035cc'
H01 = 'artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8'
P03 = 'artifacts/server_unused_molecule_frozen_holdout_20260921_d288797'
OBS = Path('/tmp/fs-c05-task-20261007')
URL = 'https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads((ROOT / path).read_text())

def write(name, obj):
    path = OUT / name
    if path.exists():
        raise FileExistsError('create-only report: ' + name)
    raw = obj if isinstance(obj, str) else json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n'
    path.write_text(raw)

def main():
    old = read(C0+'/fs_c1_protocol.json')
    practical = read(PRACT+'/protocol.json')
    closure = read(C0+'/source_and_backend_closure.json')
    model = practical['selector']['proxy_model']
    assert model['name'] == 'echo_imag_3point'
    assert model['training_relative_to_proxy_t_ana'] == [0.1,0.2,0.3]
    timestamp = datetime.now(timezone.utc).isoformat()
    request = Path('/home/abe/.codex/attachments/6c08bb9a-2a7e-48da-92cc-ab57afe74e12/貼り付けたテキスト.txt').read_bytes()
    (OUT/'authorization_request.md').write_bytes(request)
    write('authorization_scope.json', dict(request_sha256=sha(request), request_bytes=len(request),
        request_copy='authorization_request.md', session_date_JST='2026-10-07',
        base_commit=BASE, source_missing_followup='source_missing_followup.md',
        production_science_authorized=False, production_science_actions=0,
        final_stage='FS-C0.5; stop after publication; no C1 or regeneration'))
    write('source_missing_followup.md', '# 2026-10-07 JST user clarification\n\nユーザーは、別保存先・実際に接続可能なSSH alias/hostname/IPが分からず、履歴上のサーバーパスだけが残ることを確認した。pickle/runtimeはGitHubから意図的に除外されており、Git履歴からの復元経路も確認されていない。指定SHAに一致する原本が既知のローカル候補から見つからなければ SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT として停止し、source missingとしてNO-GOを確定する指示を受けた。再生成source/functional equivalenceへ変更するかは後続GPT/user判断であり未承認。\n\n同名H02候補のSHA不一致はcandidate-level identity rejectionとして記録する。最終completionはこの追加入力に従い NO_GO_SOURCE_MISSING とする。\n')
    baseline = dict(historical_baseline_model=model['name'],
        historical_training_relative=model['training_relative_to_proxy_t_ana'],
        sentinel_relative=0.5,sentinel_in_fit=False,relative_0_4_role='none',
        M00_primary='immutable historical saved baseline',
        M00_reproduction='execution validation only',
        current_m3_sequence=practical['formulae']['current_m3']['s2_sequence'],
        fit=dict(powers=[4,6],intercept=False,weighting='unweighted OLS',
                 scaling='times/t_ref; values/max(abs(values)); numpy.linalg.lstsq rcond=None; unscale coefficients',
                 numerical_function='review_response/run_h01_approximate_state_calibration.py:_fit_proxy'),
        systems=[])
    for s in old['systems']:
        baseline['systems'].append({k:s[k] for k in ('condition','t0','t0_hex','B0','K','t_ref',
            'historical_coefficients','historical_signed_prediction','historical_training_time_hex','identity')})
        baseline['systems'][-1].update(historical_training_absolute=s['historical_training_times'],
            M10_training_absolute=s['historical_training_times'],
            historical_reference_authority=C0+'/fs_c1_protocol.json')
    write('baseline_contract.json',baseline)
    new = json.loads(json.dumps(old))
    new.update({k:v for k,v in baseline.items() if k not in ('systems','fit','current_m3_sequence')})
    new.update(protocol_id='FS-C1-20261007-v2',stage='FS-C0.5 source/backend execution closure',
        supersedes_protocol=C0+'/fs_c1_protocol.json', supersedes_commit=BASE,
        revision_reason='historical baseline corrected from erroneous five-point assumption to source-backed echo_imag_3point training',
        authorization_amendment='approved 2026-10-07 attachment §1; no science authorization',
        execution_ready=False,science_authorized=False,
        stop='FS-C0.5 normal publication verification then stop; separate authorization for C1',
        cold_replay='independent source load/refinement/PF/echo/proxy/fit; immutable source bytes may recur; no intermediate cache shared')
    new['fit']=baseline['fit']
    new['current_m3_sequence']=baseline['current_m3_sequence']
    for s,b in zip(new['systems'],baseline['systems']):
        s.update(historical_training_absolute=b['historical_training_absolute'],
                 M10_training_absolute=b['M10_training_absolute'], training_times=b['historical_training_absolute'],
                 requested_training_relative=[0.1,0.2,0.3], training_time_status='source-backed 3-point contract closed')
    new['arms']={'M00':'immutable saved CISD 3-point prediction/B0; replay validation only',
                 'M10':'residual Krylov Ritz8, identical 3 absolute times, identical fit, historical t0',
                 'M01':'historical CISD local g(t0), no fit', 'M11':'same Ritz8 local g(t0), no fit; primary'}
    write('fs_c1_protocol_v2.json',new)
    write('research_amendment.md','# Approved amendment\n\nGPT/userはhistorical M00をecho_imag_3pointへ修正した。trainingは元CISD t_refの0.1/0.2/0.3であり、保存された絶対時刻をそのまま使う。0.4を補わず、0.5 sentinelをfitから除外し、H01の別5点modelへ置換しない。M00 primary prediction/B0はimmutable saved value。新backendの再現値はvalidationのみ。M10も同一絶対時刻・元numerical/scaling conventionを使う。\n\nM11 primary、M01 cheaper challenger、残りのrank/epsilon/beta/gamma/eta・sector/PF/t0/claim scopeはC0から継承。Codexによる新しい研究方針変更はない。旧v1・FS-C0・formal/Phase0/H4は編集しない。今回のNO-GOはsource欠損に関する実行前判定で、science failureではない。\n\n§23のbackend replay比較の準備は行うが、§31のscience-zero上限によりN2/COの新PF/echoを呼ばない。saved scalar arithmeticとsyntheticのみを実行する。\n')
    coordlines=['|Condition|M00 = M10 training absolute times|historical t0|B0|','|---|---|---|---|']
    for s in baseline['systems']:
        coordlines.append(f"|{s['condition']}|{s['historical_training_absolute']}|{s['t0']}|{s['B0']}|")
    write('fs_c1_protocol_v2.md','# FS-C1-20261007-v2\n\nScience未承認・execution未ready。旧v1を保存したadditive amendment。\n\n'+ '\n'.join(coordlines)+'\n\nM00は保存baseline、M10は同じ3点のRitz8 fit、M01/M11は同じt0のlocal proxyでfitなし。Ritzから新t_ref/timeを作らない。primary M11/challenger M01、判定式とtruth barrierは旧C0に従う。数値gateは未完了のままnull。\n')
    # Files discovered by recorded rg filename search. Hash-before-decode, no decoder.
    from closure_adapter import check_pickle
    paths = OBS.joinpath('search_paths.txt').read_text().splitlines()
    candidates=[]
    for p in paths:
        condition=Path(p).stem
        if condition not in practical['source_identity']['pickle_sha256']:
            continue
        expected=practical['source_identity']['pickle_sha256'][condition]
        result=check_pickle(p,expected)
        candidates.append(dict(path=p,condition=condition,bytes=Path(p).stat().st_size,
            expected_sha256=expected, observed=result, accepted=False))
        assert not result['decoded'] and result['status']=='NO_GO_SOURCE_IDENTITY'
    worktrees=[line[9:] for line in subprocess.check_output(['git','worktree','list','--porcelain'],cwd=ROOT,text=True).splitlines() if line.startswith('worktree ')]
    checks=[]
    for root in worktrees:
        for prefix in (H01+'/cache',P03+'/cache',PRACT+'/.runtime/sanitized'):
            for s in baseline['systems']:
                p=Path(root)/prefix/(s['condition']+'.pkl')
                checks.append(dict(path=str(p),exists=p.is_file()))
    server='/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'
    write('source_recovery_audit.json',dict(status='SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT',
        final_completion='NO_GO_SOURCE_MISSING', observed_at_UTC=timestamp,
        search_tool='rg --files --hidden --no-ignore, exact N2/CO filenames including ignored .runtime',
        roots=['/home/abe','/tmp','/mnt','/media'],
        coverage=['repository root','all registered current/old worktrees','H01/P03/server artifacts',
                  '.runtime and .runtime/sanitized','local project copies','external pf_external_cache',
                  'mounted /media/abe/T7 user backup'],
        candidates=candidates,expected_path_checks=checks,
        search_stderr=OBS.joinpath('search_errors.txt').read_text().splitlines(),
        search_limitations=['unrelated service/other-user private tmp directories inaccessible',
            'historical server mount absent locally; no usable SSH endpoint provided; remote filesystem not searched'],
        historical_server_root=dict(path=server,exists=Path(server).exists(),connectable_endpoint=None,
                                    authority=PRACT+'/audit.json:provenance/source roots; user followup'),
        pickle_decodes=0, canonical_exports=0, source_regenerations=0,
        candidate_rejection='whole SHA mismatch: not decoded, not replaced even if contents/H match',
        completion_rule='expected originals unrecovered; user followup explicitly requests source missing final status'))
    identities=[]
    for s in baseline['systems']:
        ids=s['identity']
        identities.append(dict(condition=s['condition'],closed=False,status='SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT',
            expected_whole_pickle_sha256=ids['source_pickle_sha256'], recovered_whole_pickle_sha256=None,
            expected_hamiltonian_sha256=ids['hamiltonian_sha256'], verified_hamiltonian_sha256=None,
            cisd_sha256=None,restricted_basis_sha256=None,ordered_group_identity_sha256=None,
            each_group_component_sha256=None,sector_metadata_sha256=None,dtype_shape=None,
            source_path=None,source_recovery_timestamp=None,source_provenance_commit='568f00249abb5b89ae3e6bb39cb4af87ed8581bd',
            historical_metadata_attestation_only=True,
            phase_canonicalization='none; preserve original stored bytes; no phase/overlap/gap alignment'))
    write('canonical_source_identity.json',dict(closed=False,systems=identities,
        canonical_export_rule='not executed because exact whole-pickle identity failed; private arrays never published',
        export_requirements=['dtype.str, shape, C-order stored bytes hash, file bytes/hash, source member/key',
            'historical H hash serialization reproduced exactly alongside any canonical export hash',
            'ordered groups and each ordered component; no sorting to match',
            'CISD/basis/sector/PF order/constant; no scientific operation during decode']))
    # Pin only the existing implementation definitions needed for fixture/scalar work.
    specs=[('src/trotterlib/pf_decomposition.py',['_iter_s2_steps','iter_s2_sequence_steps']),
           ('src/trotterlib/component_sector_pf.py',['ComponentBatch','ComponentSpectrum','component_exponential']),
           ('review_response/run_h01_approximate_state_calibration.py',['_apply_pf_cpu','_fit_proxy'])]
    write('native_source_pins.json',dict(verified_snapshot_commit=BASE,sources=[dict(
        path=p,sha256=sha((ROOT/p).read_bytes()),definitions=d) for p,d in specs]))
    # Select public saved scalar training rows, never direct truth tables.
    records=[]
    with (ROOT/PRACT/'proxy_points.csv').open() as f:
        rows=list(csv.DictReader(f))
    predictions=read(PRACT+'/predictions.json')
    for s in baseline['systems']:
        found=[r for r in rows if r['condition']==s['condition'] and r['formula']=='current_m3' and r['point_role']=='model_training']
        assert [float(r['time']) for r in found] == s['historical_training_absolute']
        pred=next(c for c in predictions['conditions'] if c['condition']==s['condition'])
        pred=next(p for p in pred['pf_predictions'] if p['formula']=='current_m3')
        records.append(dict(condition=s['condition'],times=s['historical_training_absolute'],
            saved_proxy_values=[float(r['echo_imag_hartree']) for r in found],
            saved_echo_imaginary=[float(r['echo_imaginary']) for r in found],
            saved_pf_norm=[float(r['pf_state_norm']) for r in found],
            saved_reference_norm=[float(r['exact_state_norm']) for r in found],
            saved_coefficients=s['historical_coefficients'],saved_signed_prediction=s['historical_signed_prediction'],
            saved_B0=s['B0'],t_ref=s['t_ref'],t0=s['t0'],
            saved_training_fit_diagnostics={k:pred['model'][k] for k in ('training_design_condition_number','training_maximum_absolute_residual_hartree')}))
    write('saved_scalar_fixture.json',dict(authority=PRACT+'/proxy_points.csv; predictions.json; C0 protocol',
        meaning='saved scalar arithmetic only; no new backend evaluation',systems=records))
    write('echo_numerical_contract.json',dict(status='M00_REPRODUCTION_TOLERANCE_UNCLOSED',closed=False,
        definition='Im<psi|exp(-iHt) U(t)|psi>/t = Im<exp(+iHt)psi|U(t)psi>/t',
        energy_origin='exact same removed-constant restricted H as historical PF',dtype='complex128',
        sign_and_orientation='native PF exp(+i t weight spectrum); exact reference exp(+iHt)',
        tolerance_hartree=None,
        components={'historical_backend_bound':None,'cold_variability_bound':None,'floating_backend_bound':None},
        evidence=[{'condition':r['condition'], 'fit_diagnostics':r['saved_training_fit_diagnostics'],
                   'use':'fit residual/condition retained as diagnostics; not backend error certificates'} for r in records],
        historical_threads_benchmark='N2 time0.1 echoes identical across 1/4/8 threads; not independent cold replay or CO bound',
        uncertainty_rule='echo absolute bound propagates as delta_proxy <= delta_echo/abs(t); actual source-backed echo bound unavailable',
        forbidden_tolerance_inputs=['direct truth','exact-ground overlap/gap','model fit residual as backend certificate','sentinel sign threshold as numeric bound'],
        numerical_failure_policy='do not tune bound after production result; no source replay scheduled in C0.5'))
    from closure_adapter import action_plan
    write('cost_contract.json',dict(status='LOGICAL_LEDGER_AND_UNKNOWN_POLICY_CLOSED',production_cost_measurement='NOT_RUN',
        mandatory=['logical exact-H echo','explicit Ritz H matvec','PF forward','ordered group application',
                   'small Ritz solve','wall_seconds','peak_RSS_bytes','software versions','thread settings'],
        expm_internal={'status':'unknown','matvec':None,'matmat':None,'rmatvec':None,'rmatmat':None,'norm_estimation':None},
        unknown_is_not_zero=True,units={'classical':'seconds/RSS bytes','logical':'per-vector actions and group calls',
                                    'predicted_QPE':'PF rotations'},single_weighted_sum=None,
        planned_rank8_joint=action_plan(8),actual_production={k:0 for k in action_plan(8) if k not in ('planned_only',)},
        per_condition_per_vector_PF={'N2_active_eq_sto3g':{'group_applications':1121,'distinct_gate_materializations':324},
                                   'CO_active_eq_sto3g':{'group_applications':1373,'distinct_gate_materializations':396}},
        cold_fit_amendment='§27 rebuilds all fits per pass: M00 validation4 + M10 initial2/cold2 =8. C0 v1 saved4 fit plan unchanged in history.',
        categories=['standalone operational','incremental over saved baseline','joint acquisition','cold validation','inherited preparation','failed attempts'],
        standalone_incremental={'M01':{'PF_forward':1,'logical_exact_H_echo':1},
                                'M11':{'PF_forward':1,'logical_exact_H_echo':1,'explicit_Ritz_H_matvec':'1+k','small_Ritz_solve':1}},
        group_schedule='single vector call; native gate cache local to one forward action; no shared scientific intermediates'))
    write('backend_contract.md','# Native backend contract\n\nclosure_adapter.pyはpinned sourceのASTから元_apply_pf_cpu、component_exponential、merged S2 iterator、_fit_proxyの関数bodyを変更せず取り出す。科学runnerのimport、prepare_condition、ground/sector construction、group eigensolveを行わない。complex128・ordered spectra・固定current_m3・左からのgate @ current・component exp(+i t λ)を保存する。stateは明示入力、interfaceはstate-independent。\n\n実行可能adapterは最大8次元synthetic fixtureだけに制限した。N2/CO production adapter/FS-C1 runnerは完成していない。原本欠損につきproduction replayはNOT_RUN、saved-scalar arithmeticのPASSをbackend再現PASSと呼ばない。normalizationをsilent repairせず、toy normを監査する。将来matching sourceが見つかった場合のcanonical identity要件はmanifestに保存したが、再生成ルートは実装しない。\n')
    write('cold_replay_contract.md','# Complete cold replay contract\n\nFS-C1は未承認。将来のinitial/coldはそれぞれ独立source load、state refinement、PF、exact-H echo、proxy、fitを再構築する。immutable source bytesの再利用だけは許可し、state/Krylov/HZ/group-gate/expm/proxy/fit cacheは共有しない。同じ保存絶対時刻と同じrank/tie rulesを使う。\n\n§27のfit独立再構築に合わせ、2分子×2passesのM00 validation4 + M10 fits4 (initial operational2/cold validation2) =8を予定callとして明示。M00 primaryは保存値のまま。4training/local時刻×2states×2分子×2passesのPF/echo32、explicit refinement H36 (rank8)、small Ritz4。実行値はすべて0。synthetic fixtureのcold passだけを新規object/state/spectra/ledgerで試験する。\n')
    write('recovery_contract.md','# Durable recovery before public validation\n\nC0の検証済みserialization_boundary.pyを変更せず使う。各pass science return直後にscalar rows/action ledgerをcreate-only private checkpointとしてfsync/hash/read-only保存し、その後public schema validation、公開write、hash roundtrip、Git commitfreezeへ進む。privateとpublic/freezeは別概念。tuple/numpy scalarはboundaryで変換し、arrays/complex/nonfinite/truthは拒否する。\n\n公開validation failure後もprivate bytesからserializationだけを回復する。science rerunを自動承認しない。checkpoint作成自体の失敗もincidentとして停止し、追加scienceは個別承認が必要。C0.5ではsynthetic checkpoint fixtureのみ。source pickleやprivate working arrayをGitへ追加しない。\n')
    write('truth_access_audit.json',dict(raw_FS_C1_truth_opens=0,new_direct_truth=0,exact_ground_source_construction=0,
        production_array_decodes=0,prohibited_production_actions={k:0 for k in [
            'H_matvec','Ritz_basis','Ritz_solve','PF_evolution','selected_time_proxy','new_proxy_fit',
            'direct_truth','full_ground','Schur','eigensolve','H_regeneration','CISD_regeneration',
            'molecule_regeneration','group_regeneration','new_PF','new_time_selection']},
        raw_truth_files_not_opened=['S0 scoring.csv','S0 branch_audit.csv','H4 direct/exact truth'],
        allowed_reads=['C0 authority metadata','H01/P03 source provenance','saved practical CISD proxy scalars','source manifests'],
        development_informed=True,independent_blind_evaluation=False,
        instrumented_guard='open_c1_truth rejects before invoking any reader; production adapter blocked by scope/size',
        verification_basis='recorded commands, builder import/read audit and synthetic guard tests; no claim of global syscall interception'))
    write('GO_NO_GO_FOR_FS_C1.json',dict(status='NO_GO_SOURCE_MISSING',
        reason='SOURCE_NOT_RECOVERABLE_UNDER_IDENTITY_CONTRACT',production_science_actions=0,
        baseline_3point_closed=True,source_closure=False,canonical_array_identity_closed=False,
        native_backend_production_reproduction='NOT_RUN',M00_reproduction_tolerance_hartree=None,
        echo_numeric_contract_closed=False,cost_ledger_contract_closed=True,
        internal_expm_work_status='unknown/null accepted by §25',science_authorized=False,
        FS_C1_runner_complete=False,execution_ready=False,
        additional_unclosed=['M00_REPRODUCTION_TOLERANCE_UNCLOSED','production native replay NOT_RUN','echo error bound unavailable'],
        candidate_identity_rejections=len(candidates),final_status_authority='request §10 and user source-missing followup',
        stop='complete closure/publication only; no C1 or source regeneration'))
    write('README.md','# FS-C0.5 execution closure — NO_GO_SOURCE_MISSING\n\n2026-10-07 JST。historical baselineをsource-backed echo_imag_3pointへ修正し、M00/M10の保存絶対3時刻と元numerical conventionを固定した。M00 primary prediction/B0は保存値のまま。\n\n指定whole-pickle SHAに一致するN2/CO原本は探索範囲内で回収できなかった。旧H02 worktreeの同名2候補はSHA不一致でdecode前に棄却。canonical array identity、production backend再現、M00再現許容差、echo数値boundは未完了。保存scalar算術とsynthetic試験のPASSはproduction再現の証拠ではない。source missingはscience failureではない。\n\nproduction science action=0。FS-C1 runnerは未完成・science未開始。Hamiltonian/CISD/group再生成は禁止を維持する。旧formal/Phase0/H4/FS-C0 artifactsは変更していない。\n\n読む順序:\n\n1. [GO_NO_GO_FOR_FS_C1.json](GO_NO_GO_FOR_FS_C1.json)、[source_recovery_audit.json](source_recovery_audit.json)、[canonical_source_identity.json](canonical_source_identity.json)\n2. [research_amendment.md](research_amendment.md)、[fs_c1_protocol_v2.md](fs_c1_protocol_v2.md)、[baseline_contract.json](baseline_contract.json)\n3. [backend_reproduction_preflight.json](backend_reproduction_preflight.json)、[echo_numerical_contract.json](echo_numerical_contract.json)、[backend_contract.md](backend_contract.md)\n4. [cost_contract.json](cost_contract.json)、[cold_replay_contract.md](cold_replay_contract.md)、[recovery_contract.md](recovery_contract.md)\n5. [verification.json](verification.json)、[tests.log](tests.log)、[source_manifest.json](source_manifest.json)、[publication_manifest.json](publication_manifest.json)\n\nGPT/userへ返す判断: 原本探索の追加手段があるか、または将来別source/identity契約への再設計を承認するか。後者の設計・計算は今回実施しない。追加science authorizationは別途必要。\n\n再検証は新temporary pathで PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py artifacts/pf_first_study_fs_c05_execution_closure_20261007/test_fs_c05.py。hash-pinned native definitionsをsyntheticだけに使う。\n\nRepositoryは '+URL+'、branch pf-first-study-fs-c05-execution-closure-20261007。固定handoff commitとremote取得receiptは最終報告で示す。publication_manifestは自己除外。凍結文書の公開前状態を後から書き換えない。\n')
    source_registry()

def source_registry():
    # Source provenance registry contains public bytes only, distinct roles.
    baseline=json.loads((OUT/'baseline_contract.json').read_text())
    specs=[(s['path'],s['definitions']) for s in json.loads((OUT/'native_source_pins.json').read_text())['sources']]
    request=(OUT/'authorization_request.md').read_bytes()
    wanted=[C0+'/'+n for n in ('README.md','GO_NO_GO_FOR_FS_C1.json','source_and_backend_closure.json','research_decision.md',
        'four_arm_design.md','fs_c1_protocol.json','fs_c1_protocol.md','backend_review.md','cost_dictionary.md',
        'predicted_action_budget.json','source_manifest.json','serialization_boundary.py','test_fs_c0.py')]
    wanted += [PRACT+'/'+n for n in ('protocol.json','predictions.json','proxy_points.csv','audit.json','manifest.json','sanitized_input_manifest.json') if (ROOT/PRACT/n).is_file()]
    wanted += [H01+'/manifest.json',P03+'/manifest.json']
    wanted += [H01+'/cache/'+s['condition']+'.metadata.json' for s in baseline['systems']]
    wanted += ['artifacts/pf_first_study_phase0_feasibility_20261006/source_registry.json',
               'artifacts/pf_first_study_completion_analysis_20260926_940ee7f/source_manifest.json',
               'AGENTS.md', 'review_response/run_practical_calibration_minimal.py',
               'review_response/h01_approximate_state_calibration_protocol.json',
               'review_response/unused_molecule_frozen_holdout_protocol.json'] + [p for p,_ in specs]
    oldreg={s['path']:s for s in read(C0+'/source_manifest.json')['sources']}
    sources=[]
    for p in wanted:
        raw=(ROOT/p).read_bytes()
        if p.startswith(C0+'/'): origin=BASE
        elif p.startswith(PRACT+'/'): origin='4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a'
        elif p.startswith(H01+'/'): origin='568f00249abb5b89ae3e6bb39cb4af87ed8581bd'
        elif p.startswith(P03+'/'): origin='33a761d44a24022ad61192c41a196dd4cb3afbca'
        else: origin=oldreg.get(p,{}).get('origin_result_commit') or subprocess.check_output(['git','log','-1','--format=%H',BASE,'--',p],cwd=ROOT,text=True).strip()
        snap=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
        assert raw==snap
        sources.append(dict(path=p,bytes=len(raw),sha256=sha(raw),origin_result_commit=origin,
            verified_snapshot_commit=BASE,snapshot_github_url=URL+'/blob/'+BASE+'/'+p,
            git_blob_sha=subprocess.check_output(['git','rev-parse',BASE+':'+p],cwd=ROOT,text=True).strip(),
            origin_role='original result/document/code version, separate from verified snapshot'))
    write('source_manifest.json',dict(repository=URL.removeprefix('https://github.com/'),sources=sources,
        new_user_input=dict(path='authorization_request.md',sha256=sha(request),origin_result_commit=None,verified_snapshot_commit=None,
                            origin_role='new user attachment; first publication is final handoff commit'),
        role_policy='origin/result and verified snapshot distinct even for equal blobs; no pickle/arrays published'))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-registry-only',action='store_true')
    args=parser.parse_args()
    source_registry() if args.source_registry_only else main()
