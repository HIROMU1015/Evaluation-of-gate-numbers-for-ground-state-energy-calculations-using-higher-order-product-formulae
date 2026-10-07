"""Publish only scalar recovery; never loads a source pickle or runs science."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = Path('/tmp/fs-c06-validation-private-20261007')
BASE = '75fe0d65a2940f160ea42f6414fc2246d67bd0cf'
FREEZE = 'a5fb9835657c3e5ac1658d1323b5746bf318fc8c'
STATUS = 'NO_GO_RECONSTRUCTION_MISMATCH'
NOT_RUN = 'NOT_RUN_H_EXACT_SHA_REJECTION'


def write(name, data):
    (HERE/name).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def main():
    recovery_path = PRIVATE/'complete_identity_audit_recovery.json'
    raw = recovery_path.read_bytes()
    result = json.loads(raw)
    registry = json.loads((HERE/'historical_fingerprint_registry.json').read_text())
    contract = json.loads((HERE/'validation_contract.json').read_text())
    assert len(result['candidate']) == len(result['reconstruction']) == 2
    assert all(not r['gates']['H_exact_SHA'] for k in ['candidate','reconstruction'] for r in result[k])
    assert all(r['status']=='RETURNED' and not r['technical_failure'] for r in result['reconstruction_calls'])
    assert result['counts']['FS_C1_science_action_count']==result['counts']['new_direct_truth']==0
    checkpoint = dict(private_scalar_recovery_saved_before_publication=True,
                      private_recovery_sha256=hashlib.sha256(raw).hexdigest(),
                      validation_contract_freeze_commit=FREEZE)
    write('candidate_source_audit.json', dict(**checkpoint, status='BOTH_REJECT_H_EXACT_SHA',
          systems=result['candidate'], whole_pickle_mismatch_alone_is_not_rejection=True))
    write('reconstruction_audit.json', dict(**checkpoint, status=STATUS,
          attempts=result['reconstruction_calls'], systems=result['reconstruction'],
          pinned_configuration=contract['reconstruction'], attempts_per_condition=1,
          tuning_retries=0, technical_failures=0))
    summaries=[]
    for candidate, rebuilt in zip(result['candidate'],result['reconstruction']):
        assert candidate['condition']==rebuilt['condition']
        summaries.append(dict(condition=candidate['condition'], expected_H_sha256=candidate['expected_H_sha256'],
          candidate_H_sha256=candidate['actual_identities']['hamiltonian_sha256'],
          reconstructed_H_sha256=rebuilt['actual_identities']['hamiltonian_sha256'],
          candidate_gates=candidate['gates'], reconstructed_gates=rebuilt['gates'], accepted_source=None))
    write('functional_equivalence_result.json', dict(**checkpoint,status=STATUS, systems=summaries,
          reason='Both existing candidates and each one-shot reconstruction fail mandatory exact Hamiltonian SHA.',
          historical_source_status='missing', no_source_is_functionally_equivalent=True,
          tolerance_changed_after_results=False, further_validation=NOT_RUN))
    write('operational_source_identity.json', dict(status='NO_ACCEPTED_SOURCE_NO_EXPORT',
          historical_source_status='missing', source_acceptance_contract='functional_equivalence',
          systems=[dict(condition=s['condition'],source_kind=None,provenance=None,H_sha256=None,
                        CISD_sha256=None,group_sha_list=None,ordered_group_identity_sha256=None,
                        sector_metadata_sha256=None,dtype=None,shape=None,serialization_rule=None,
                        historical_pickle_sha256=s['baseline']['identity']['source_pickle_sha256']) for s in registry['systems']],
          validation_source_digests='candidate_source_audit.json and reconstruction_audit.json; not operational identities'))
    write('sanitization_audit.json',dict(status='NOT_EXPORTED_SOURCE_REJECTED',operational_export_count=0,
          acceptance_required_before_export=True,allowlist_guard='source_adapter.py:sanitized/assert_sanitized',
          synthetic_tests_only=True,production_sanitization_pass=None,
          exact_ground_vector_exported=False,exact_ground_overlap_exported=False,
          exact_gap_exported=False,direct_PF_truth_exported=False,branch_truth_exported=False,
          old_result_labels_exported=False))
    write('M00_reproduction.json',dict(status=NOT_RUN, saved_reference_immutable=True,
          scope='Targets only. Null reproduction differences are unmeasured, not zero.',
          systems=[dict(condition=s['condition'],historical=s['M00'], recalculated_proxy_values=None,
                        maximum_proxy_difference_hartree=None,recalculated_coefficients=None,
                        coefficient_difference=None,recalculated_signed_prediction=None,
                        prediction_difference_hartree=None,recalculated_budget=None,budget_difference=None)
                   for s in registry['systems']]))
    with (HERE/'M00_reproduction.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,lineterminator='\n',fieldnames=['condition','time','historical_proxy_hartree','recalculated_proxy_hartree','difference_hartree','status'])
        writer.writeheader()
        for s in registry['systems']:
            for t,p in zip(s['M00']['times'],s['M00']['saved_proxy_values']):
                writer.writerow(dict(condition=s['condition'],time=t,historical_proxy_hartree=p,
                                     recalculated_proxy_hartree='',difference_hartree='',status=NOT_RUN))
    write('backend_reproduction.json',dict(status=NOT_RUN,
          production_arbitrary_vector=None,production_PF_order=None,production_echo_sign=None,
          production_norm_difference=None,production_cold_reproduction=None,
          synthetic_backend_test_scope='Native historical functions on analytically specified 2x2 fixtures only; not N2/CO backend reproduction.',
          successful_source_backend_path_implemented=False,
          H_rejection_stops_before_PF_echo_fit=True, source_backend_ready=False))
    write('echo_numerical_contract.json',dict(status='FROZEN_BOUND_NOT_PRODUCTION_VALIDATED',
          contract='validation_contract.json',freeze_commit=FREEZE,
          proxy_absolute_tolerance_hartree=contract['proxy_absolute_tolerance_hartree'],
          state_absolute_tolerance=contract['state_absolute_tolerance'],
          metadata_absolute_tolerance_hartree=contract['metadata_absolute_tolerance_hartree'],
          norm_absolute_tolerance=contract['norm_absolute_tolerance'],
          selected_prediction_absolute_tolerance_hartree=contract['selected_prediction_absolute_tolerance_hartree'],
          fit_coefficient_bound=contract['fit_coefficient_bound'], additional_gate_rationale=contract['additional_gate_rationale'],
          echo='vdot(CISD, expm_multiply(-1j*t*H, PF(CISD)))',PF_sign='+i',dtype='complex128',
          tolerance_adjusted_after_result=False,production_validation_pass=None))
    counts=dict(result['counts'])
    counts['recorded_reconstruction_and_audit_actions']=counts['source_validation_action_count']
    counts['source_validation_action_count'] += counts['preliminary_schema_source_loads']+counts['preliminary_identity_source_loads']
    counts['count_definition']='two prepare_condition calls, eight initial/cold identity audit passes, and four preliminary source-load/inspection operations; 14 total, nested ground/H/PF/echo work reported separately'
    ledger=dict(counts=counts,reconstruction_resources=result['reconstruction_calls'],
          identity_audit_resources=result['resources'],
          preliminary_source_loads=dict(schema=2,identity=2,wall_seconds=None,peak_RSS_bytes=None,
            note='Two preliminary schema decodes and two preliminary identity decodes precede eight logged initial/cold passes. Not omitted from total source loads.'),
          explicit_source_CISD_fingerprint_H_matvec_in_logged_audits=8,
          construction_internal_H_work=None,preliminary_identity_H_work=None,
          expm_multiply_internal=dict(matvec=None,matmat=None,rmatvec=None,rmatmat=None,norm_estimation=None),
          internal_work_status='unknown; not reported as zero',
          synthetic_test_actions='Excluded from physical source-validation ledger; test fixtures only.',
          actual_measured_wall_seconds=sum(r['wall_seconds'] for r in result['reconstruction_calls'])+result['resources']['wall_seconds'],
          measured_wall_scope='Two reconstruction calls plus combined identity audit; preliminary loads, tests, orchestration and publication excluded.',
          max_observed_process_peak_RSS_bytes=max(r['peak_RSS_bytes'] for r in result['reconstruction_calls']),
          RSS_scope='Linux ru_maxrss per process, not summed simultaneous RAM',
          software=result['resources']['software'],python=result['resources']['python'],threads=result['resources']['threads'])
    write('cost_ledger.json',ledger)
    write('cold_replay_audit.json',dict(status='SOURCE_LOAD_IDENTITY_REPLAY_PASS_BACKEND_NOT_RUN',
          systems=result['cold_replay'],scope='Fresh pickle load each time; no source object/intermediate cache reused. Same-process identity replay only; no production PF/echo/fit replay.'))
    write('truth_access_audit.json',dict(FS_C1_science_action_count=0,new_direct_truth=0,
          validation_ground_solve_calls=2,exact_ground_use='private validation fingerprints only',
          operational_export_count=0,FS_C1_truth_files_loaded=False,Phase_B_scoring_calls=0,
          historical_truth_files_used_for_equivalence=False,
          historical_echo_read_scope='CISD proxy/fit fields only; direct_reference_model/sanity not extracted into equivalence inputs.',
          historical_metadata_ground_scalar_use='Authorized source fingerprint comparison only, not operational estimation.',
          group_order_changed=False,PySCF_settings_changed=False,solver_changed=False,
          private_binary_publication=False,barrier_guard='source_adapter.py:forbid_c1_truth'))
    decision=dict(status=STATUS,FS_C1_science_authorized=False,execution_ready=False,
          existing_candidate_result='REJECT_H_EXACT_SHA',pinned_reconstruction_result='REJECT_H_EXACT_SHA',
          metadata_sector_pass=True,CISD_fingerprints_pass=True,ordered_group_attestations_match=False,
          numerical_group_content_status=NOT_RUN,M00_proxy_status=NOT_RUN,M00_fit_status=NOT_RUN,
          backend_status=NOT_RUN,cold_source_identity_replay_pass=True,cold_backend_pass=None,
          operational_export_count=0,source_validation_action_count=counts['source_validation_action_count'],FS_C1_science_action_count=0,
          new_direct_truth=0,stop='FS-C0.6 complete then stop; no extra reconstruction, no FS-C1.',
          future_research_decision='GPT/user must decide source recovery or any revised identity contract. No revision executed here.')
    write('GO_NO_GO_FOR_FS_C1.json',decision)
    protocol=json.loads((HERE/'fs_c1_protocol_v3.json').read_text())
    protocol['authorization_amendment']='Approved FS-C0.6 attachment; source reconstruction validation only. FS-C1 science not authorized.'
    protocol['supersedes_protocol']='artifacts/pf_first_study_fs_c05_execution_closure_20261007/fs_c1_protocol_v2.json'
    protocol['supersedes_commit']=BASE
    protocol['revision_reason']='Functional-equivalence source contract; retain immutable historical 3-point M00 from v2.'
    protocol['operational_source_kind']='unavailable after audit'
    protocol['operational_source_kind_initial']='pending until audit'
    protocol['audit_status']=STATUS
    protocol['status_update_after_audit_only']=True
    protocol['validation_contract_freeze_commit']=FREEZE
    protocol['unresolved_issues']=[dict(condition=s['condition'],id='SOURCE_H_EXACT_SHA_MISMATCH',
             detail='Existing H02 candidate and single pinned reconstruction rejected; no accepted operational source. M00/backend reproduction not run.') for s in registry['systems']]
    write('fs_c1_protocol_v3.json',protocol)
    manifest=json.loads((HERE/'source_manifest.json').read_text())
    manifest['initial_registry_freeze_commit']=FREEZE
    manifest['private_recovery_receipt']=checkpoint
    manifest['validation_sources']=[dict(condition=r['condition'],source_kind=r['source_kind'],
        whole_binary_sha256=r['source_binary_sha256'],actual_H_sha256=r['actual_identities']['hamiltonian_sha256'],
        operationally_accepted=False,binary_published=False) for k in ['candidate','reconstruction'] for r in result[k]]
    manifest['execution_code_pins']=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
          origin_result_commit=None,verified_snapshot_commit=None,
          commit_resolution='new FS-C0.6 code; final handoff commit supplied separately')
          for p in [HERE/'reconstruct_once.py',HERE/'source_adapter.py',HERE/'run_identity_audits.py']]
    revision=contract['reconstruction']['code_revision']
    path='review_response/run_h01_approximate_state_calibration.py'
    native_raw=subprocess.check_output(['git','show',revision+':'+path],cwd=HERE.parents[1])
    manifest['execution_dependencies']=[dict(path=path,origin_result_commit=revision,verified_snapshot_commit=revision,sha256=hashlib.sha256(native_raw).hexdigest(),role='pinned historical prepare_condition; entire clean checkout at this commit')]
    manifest['historical_native_function_pins']=json.loads((HERE.parents[1]/'artifacts/pf_first_study_fs_c05_execution_closure_20261007/native_source_pins.json').read_text())
    write('source_manifest.json',manifest)
    rows='\n'.join(f"| {r['condition'].split('_')[0]} | {kind} | `{r['actual_identities']['hamiltonian_sha256']}` | {r['maximum_CISD_fingerprint_difference']:.9g} |" for kind,key in [('既存H02','candidate'),('1回再構成','reconstruction')] for r in result[key])
    (HERE/'README.md').write_text(f'''# FS-C0.6：functional-equivalence source reconstruction audit

最終判定は **{STATUS}**。既存H02候補と、各条件1回の固定再構成の両方で、必須のhistorical Hamiltonian SHA完全一致を満たさなかった。whole-pickle SHAだけを理由に棄却した結果ではない。FS-C1は開始していない。

起点はFS-C0.5 `{BASE}`、契約をdecode前に固定したcommitは `{FREEZE}`。コード・環境・許容差を結果後に変えていない。再構成はN₂・COとも正常にreturnし、technical failureは0。historical H01 pickleは現在もmissingであり、historical source recoveredとは呼ばない。

| 条件 | source | 計算したHamiltonian SHA | CISD fingerprint最大絶対差 |
|---|---|---|---:|
{rows}

historical H SHAはN₂ `{registry['systems'][0]['historical_metadata']['hamiltonian_sha256']}`、CO `{registry['systems'][1]['historical_metadata']['hamiltonian_sha256']}`。算出規則はhistorical CSR shape/indptr/indices/dataのbytesをそのままSHA256に入力する。丸め・sort・reorderによる救済は行っていない。

geometry/sector/basis順序は一致し、removed constant差はN₂約1.42e−14 Ha、CO約2.27e−13 Ha。CISD差は1e−6以内。ただし、この数値的一致でH完全一致の必須条件を置き換えない。group countとterm count列は一致し、ordered group SHA列は4sourceとも不一致。numerical group contentの独立検証はH棄却後には実施していない。

[M00 reproduction](M00_reproduction.json)は保存された3 training proxy・係数・prediction・B0をtargetsとして維持し、新しいproxy/fit差は **null／NOT_RUN**。PF/echo、production arbitrary-vector、production cold PF/echo/fitも未実施であり、差0やPASSとは報告しない。sourceをfresh loadした4組のidentity replayは一致した。これはhistorical sourceとの一致やbackend再現のPASSではない。

[費用記録](cost_ledger.json)はsource validation 14 actions（prepare_condition 2回＋identity/fingerprint audit 8回＋予備source load/inspection 4回）、ground solve 2回、FS-C1 science 0、新direct PF truth 0。preliminary decode 4回も含めsource loadは12回。PF/echo 0、Ritz matvec/solve 0。expm内部作業はunknown/null。再構成のwallはN₂8.570秒、CO11.183秒、process peak RSSは約592 MB／609 MB。環境はPython3.12.3、NumPy1.26.4、SciPy1.14.1、PySCF2.7.0、OpenFermion1.6.1、Qiskit1.3.0／Aer0.15.1、BLAS/OMP/MKL各1thread。

operational sourceは採用できず、sanitized exportは0。private matrix/vector/pickle/exact stateは公開しない。exact groundはprivate validation fingerprintに限って使った。新v3の3-point M00、M10同一座標、M11 primary、M01 challengerを維持し、v1/v2と旧研究artifactは変更していない。

過去H02 server auditのH一致・差0は、当時のserver cacheについてのattestationである。今回見つかったローカル候補の同一性を保証しない。H SHAが違う原因（solver丸め、mapping、他の差など）は本監査では特定せず、物理的差の大きさも確定しない。

読む順序：このREADME → [判定](GO_NO_GO_FOR_FS_C1.json) → [source契約](source_contract.md) → [候補監査](candidate_source_audit.json) → [再構成監査](reconstruction_audit.json) → [fingerprint registry](historical_fingerprint_registry.json) → [cold](cold_replay_audit.json)／[費用](cost_ledger.json) → [verification](verification.json)。テストは既存114＋新規22＝136件すべてPASS（[tests.log](tests.log)）。再構成用Python3.12環境にはjsonschemaがないため、テストは既存114件と同じPython3.11環境で実行した。再構成環境は変更していない。新規テストのPF/echoはsynthetic 2×2、係数再現はsaved-scalarのみで、N₂/CO source/backend reproductionの代替ではない。

GPT/userに判断を依頼する点は、当時監査済みserver sourceを回収する方針、または別途source acceptance契約を再検討するか。ここでは契約を緩めず、追加再構成もFS-C1も開始せず停止する。slideは変更していない。
''')
    (HERE/'source_contract.md').write_text('''# Source contract

historical source（missingのH01 pickle）、validation source（decode/reconstructして検証した4候補）、operational source（全gate PASS後にoracleを除いたexport）を区別する。今回は最後のsourceは存在しない。

規範はdecode前に固定した[validation_contract.json](validation_contract.json)。whole-pickle SHA mismatch aloneは不採用理由にしないが、historical H SHA完全一致は必須。historical SHAは履歴として保持し、別SHAのsourceをhistorical original recoveredとは呼ばない。

順序は、H/metadata/sector/geometry/current_m3 → ordered group identity → CISD fingerprints → M00 3-point proxy/fit → echo/backend → independent cold replay → sanitized export。Hが不一致なら後続PF/echo/fitはNOT_RUN。既存候補の失敗後に限りhistorical pipelineで各条件1回再構成を認め、設定変更による2回目を禁止する。

metadata許容差1e−9 Ha、state fingerprint1e−6、proxy/echo1e−9 Haはhistorical H02由来。追加norm1e−10はhistorical scalar-invariance由来。selected prediction1e−9 Ha、係数・budgetへの伝播規則もdecode前に固定した。許容差を結果後に変えない。

group count、term count列、ordered SHA列、application/component order、numerical contentを区別する。group数が一致してもordered identityが通ったとはしない。既存候補のnumerical contentは単なるmetadata attestationでは保証しない。今回の順序付きgroup hash attestationは不一致、numerical contentチェックはH棄却で未実施。

H digestはhistorical sparse hashのshape int64、CSR indptr/indices/dataのstored contiguous bytes。sort、dtype cast、丸め、再orderingによる一致化をしない。CISD standalone historical hashは残っていないためbitwise一致を必須にせず、norm/energy/error/variance/residual/PySCF diagnostics/sector outside normを比較する。ground overlapはvalidation sandboxだけで確認する。

exportは全gate PASSのときだけallowlistから作る。許可fieldはH、ordered component spectra、CISD、restricted basis、sector/mapping metadata、removed constant、current_m3 order。exact ground/vector/overlap/gap、direct PF truth、branch truth、旧成否labelは除く。今回exportはなく、operational identityのSHA/dtype/shapeはnull。候補のdigestをoperational identityとして流用しない。

M00保存proxy/係数/B0は変更しない。original H01 echoの他の時刻をM00 trainingへ流用しない。v3のtrainingはC0.5で閉じた3点、M10は同一絶対時刻、M11 primary、M01 challenger。source受理後のproduction backend成功pathは今回未確立。unit testsのsynthetic backendでその未確立を埋めない。
''')
    (HERE/'research_amendment.md').write_text(f'''# FS-C0.6 research amendment

ユーザーの2026-10-07添付仕様に基づき、whole-pickle唯一条件からfunctional-equivalence階層へ変更した。H exact SHAは必須のまま、CISDはhistorical diagnostic fingerprintsを用いる。existing candidate decodeと、失敗後のhistorical pinned reconstruction各条件1回だけが今回の承認範囲。FS-C1 scienceの承認はない。

起点 `{BASE}`。decode前freeze `{FREEZE}`。validation_contractとfingerprint targetsは以後不変。新v3はv2から派生し、初期operational_source_kind=pending until auditを記録したうえで、監査後statusだけunavailable/{STATUS}へ更新した。v2から継承していた旧five-point conflictと旧bytewise-source-only記述は、新v3の未解決事項から除き、今回のH SHA不一致へ置換した。M00/B0、座標、arms、PF係数、gamma、margin/safety規則は変更しない。v1/v2は保存したまま。

両条件の既存candidate・1回再構成ともH SHA不一致。technical errorではなくidentity契約不成立。source equivalenceの成立やhistorical source recoveredは主張しない。原因の物理的解釈やH許容差への変更は研究判断であり、本監査の実行範囲に含めない。

source validation actionsとFS-C1 interventionsを分離した費用会計と、return後private scalar recoveryをpublic writeより先に保存する境界を保持した。科学的sourceはprivate sandboxだけに残し、新しいdirect PF eigentruthは計算せず、operational exportもない。判定はNO-GOとして引き渡し、FS-C0.6で停止する。
''')
    print(json.dumps(dict(status=STATUS,public_scalar_artifacts_written=True,FS_C1_science_action_count=0)))


if __name__=='__main__':
    main()
