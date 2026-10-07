"""Create an additive pre-execution audit; no production/science entry point.

Reads frozen Git docs/code and sanitized archive bytes/metadata only. It never
decodes numpy arrays or original pickles, builds states, or invokes PF/echo/fit.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import zipfile

BASE = 'dd41c5eaad4a88339f7bbb69267bfdace9fb86e5'
STATUS = 'PHASE_A_NUMERICAL_CONTRACT_UNCLOSED'
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R01 = 'artifacts/pf_first_study_fs_r01_branch_extension_20261007'
R0 = 'artifacts/pf_first_study_fs_r0_rebaseline_20261007'
P05 = 'artifacts/pf_first_study_response_pilot_phase05_20261006'
P06 = 'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
C05 = 'artifacts/pf_first_study_fs_c05_execution_closure_20261007'
BRANCH = 'pf-first-study-fs-r1-phase-a-20261007'
REPO = 'HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def read(path):
    return json.loads((ROOT / path).read_text())


def write(name, obj):
    raw = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
    with (HERE / name).open('x') as f:
        f.write(raw)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def check_archive(record, identity, meta_keys):
    """Byte and allowlist checks only; no numpy.load or scientific arithmetic."""
    path = Path(record['operational_archive_path'])
    raw = path.read_bytes()
    assert sha(raw) == record['operational_archive_sha256'] == identity['source_archive_sha256']
    assert len(raw) == identity['source_archive_bytes']
    assert sha(canonical(identity)) == record['source_identity_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        metadata_raw = z.read('operational.json')
        assert sha(metadata_raw) == identity['operational_metadata_sha256']
        meta = json.loads(metadata_raw)
        assert set(meta) == {'format', 'metadata', 'ordered_groups', 'component_spectra', 'current_m3_sequence', 'arrays'}
        assert meta['format'] == 'FS-R0-operational-v1'
        assert set(meta['metadata']) == set(meta_keys)
        allowed = {'H_data', 'H_indices', 'H_indptr', 'H_shape', 'CISD', 'restricted_basis'}
        for spectrum in meta['component_spectra']:
            assert set(spectrum) == {'dimension', 'batches', 'source_nnz', 'component_count', 'maximum_component_size', 'retained_complex_elements'}
            for batch in spectrum['batches']:
                assert set(batch) == {'indices', 'eigenvalues', 'eigenvectors'}
                allowed.update(n for n in batch.values() if n is not None)
        assert set(meta['arrays']) == allowed
        assert meta['arrays'] == identity['arrays']
        assert set(names) == {'operational.json'} | {n + '.npy' for n in allowed}
        for name, member in meta['arrays'].items():
            b = z.read(name + '.npy')
            assert sha(b) == member['file_sha256'] and len(b) == member['file_bytes']
        group_hashes = [sha(json.dumps(g, separators=(',', ':')).encode()) for g in meta['ordered_groups']]
        assert group_hashes == identity['ordered_group_sha256'] == meta['metadata']['group_sha256']
        assert sha(canonical(meta['metadata'])) == identity['sector_metadata_sha256']
    return dict(condition=record['condition'], status='PASS', source_identity_sha256=record['source_identity_sha256'],
                operational_archive_sha256=sha(raw), archive_bytes=len(raw), npy_member_file_hashes_verified=len(allowed),
                metadata_allowlist_pass=True, arrays_allowlist_pass=True, oracle_fields_absent=True,
                hamiltonian_sha256=identity['hamiltonian_sha256'], H_hash_recomputed=False,
                H_identity_evidence='exact archive/member bytes match frozen operational identity; no CSR decode or matvec',
                original_pickle_opened=False, numpy_array_decodes=0, numeric_source_loads=0,
                source_result_origin_commit=identity['source_result_origin_commit'],
                source_identity_origin_result_commit=git('log', '-1', '--format=%H', BASE, '--', R0 + '/new_source_identity.json').decode().strip(),
                verified_snapshot_commit=BASE)


def main(args):
    started = time.perf_counter()
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
    request_raw = Path(args.request).read_bytes()
    with (HERE / 'authorization_request.md').open('xb') as f:
        f.write(request_raw)
    existing_log = Path(args.tests_log).read_text()
    assert '260 passed' in existing_log and 'failed' not in existing_log
    write('tests.log', existing_log)
    protocol_path = R01 + '/fs_r1_protocol_v2.json'
    protocol_raw = (ROOT / protocol_path).read_bytes()
    protocol = json.loads(protocol_raw)
    p05 = read(P05 + '/response_pilot_protocol.json')
    # This audit is deliberately scoped to the actual unchanged v2 authority.
    # No guessed key names or accepted default tolerance define a future gate.
    assert protocol['protocol_id'] == 'FS-R1-20261007-v2'
    assert isinstance(protocol['cold_replay'], str)
    assert {k for k in protocol if any(s in k.lower() for s in ('cold', 'tolerance', 'numeric', 'noise', 'norm'))} == {'cold_replay'}
    assert protocol['ritz']['numeric_rules_source'] == P05 + '/response_pilot_protocol.json'
    c05_echo = read(C05 + '/echo_numerical_contract.json')
    assert c05_echo['tolerance_hartree'] is None and c05_echo['closed'] is False
    registry = read(R0 + '/new_source_registry.json')['sources']
    identities = read(R0 + '/new_source_identity.json')['identities']
    # Extract only a literal constant from source code; do not import a backend.
    import ast
    tree = ast.parse((ROOT / R0 / 'source_io.py').read_text())
    meta_keys = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'META_KEYS' for t in n.targets))
    source_checks = []
    for spec in protocol['systems']:
        record = next(r for r in registry if r['condition'] == spec['condition'])
        identity = next(i for i in identities if i['condition'] == spec['condition'])
        assert record['source_identity_sha256'] == spec['source_identity_sha256']
        assert record['operational_archive_sha256'] == spec['operational_archive_sha256']
        assert identity['hamiltonian_sha256'] == spec['new_H_sha256']
        check = check_archive(record, identity, meta_keys)
        source_checks.append(check)
        print(json.dumps(dict(source_identity_check=spec['condition'], status='PASS', science_actions=0)), flush=True)
    write('source_identity.json', dict(stage='pre_execution_identity_only', frozen_identity_path=R0 + '/new_source_identity.json',
          frozen_identity_sha256=sha((ROOT / R0 / 'new_source_identity.json').read_bytes()), checks=source_checks,
          production_numeric_gates_evaluated=False, private_binaries_published=False))
    write('phase_a_protocol_snapshot.json', dict(snapshot_kind='immutable Git reference; no normative protocol amendment',
          protocol_id=protocol['protocol_id'], path=protocol_path, sha256=sha(protocol_raw), verified_snapshot_commit=BASE,
          origin_result_commit=git('log', '-1', '--format=%H', BASE, '--', protocol_path).decode().strip(),
          execution_request_sha256=sha(request_raw), constants=protocol['constants'], fixed_systems=protocol['systems'],
          Phase_A_authorized_by_current_request=True, Phase_A_start_conditions_not_satisfied=True, Phase_B_authorized=False))
    missing = ['raw_proxy_replay_acceptance', 'fit_coefficient_replay_acceptance', 'arm_prediction_replay_acceptance',
               'budget_replay_acceptance', 'deterministic_Ritz_diagnostic_replay_acceptance']
    write('numerical_contract_audit.json', dict(status=STATUS, production_started=False, stop_authority='current user request §23',
          protocol_id=protocol['protocol_id'], protocol_sha256=sha(protocol_raw), required_cold_replay_contract_closed=False,
          missing_preregistered_acceptance_rules=missing, scientific_observations_used=0, new_tolerance_selected=False,
          existing_contracts=dict(cold_replay_rebuild=protocol['cold_replay'],
              ritz_numeric_rules=p05['numeric'], H4_scope=p05['scope']['system'],
              H4_noise_rule=p05['numeric']['noise_rule'], C05_echo_tolerance_Ha=c05_echo['tolerance_hartree'],
              C05_status=c05_echo['status'], resource_eta=protocol['constants']['eta']),
          non_substitutions=[
              'H4 eta=max(...,observed cold difference,...) defines a diagnostic, not a frozen upper bound for this replay',
              'H4 full-unitary Frobenius gates are not a preregistered vector-output norm/replay rule for this 1568-sector schedule',
              'Ritz MGS/rank/Hermiticity thresholds concern state construction, not echo/fit/budget replay error',
              'resource eta=0.02 is a Phase B resource criterion, not numerical replay tolerance',
              'tiny-matrix test atol/rtol do not certify physical-production tolerance',
              'exact equality or zero tolerance has not been preregistered and is not selected here'],
          additional_execution_review_items=[
              'explicit production PF/reference vector norm gate definition and propagation across proxies/fits/budgets',
              'Phase A orchestration must finish both initial conditions before either cold replay; inherited helper replays per condition',
              'Phase A exclusive lease and complete Ritz/PF diagnostic recovery wrapper still need a reviewed implementation'],
          prior_GO_scope='R0.1 preflight missed this numerical execution condition; old GO artifact preserved as history',
          technical_failure=False, numerical_observed_failure=False, source_failure=False,
          GPT_review_required='Fix physical-production replay/norm comparison rules before any observation; version/freeze authority and review execution wrapper. No tolerance proposed here.'))
    system_results = []
    for spec in protocol['systems']:
        system_results.append(dict(condition=spec['condition'], execution_status='NOT_RUN', reason=STATUS,
              retained_Ritz_rank=None, estimates={arm:None for arm in protocol['arms']},
              budget_status={arm:'NOT_COMPUTED' for arm in protocol['arms']},
              prediction_only_budget_ratios=None, initial_pass=None, cold_pass=None))
    write('production_results.json', dict(status=STATUS, scientific_return_occurred=False, systems=system_results,
          prediction_sha256=None, safety_scoring_status='PENDING_PHASE_B', resource_outcome=None))
    write('proxy_values.csv', 'pass,condition,state,absolute_time,signed_proxy,input_norm,PF_norm,PF_norm_error,reference_norm,echo_real,echo_imag,wall_seconds,peak_RSS_bytes,group_applications,group_materializations\n')
    write('ritz_diagnostics.json', dict(status='NOT_RUN', requested_m=8, reason=STATUS,
          systems=[dict(condition=s['condition'], retained_rank=None, rank_stop_reason=None,
              basis_orthogonality_residual=None, Ritz_normalization=None, projected_Hermiticity_residual=None,
              Ritz_energy=None, Ritz_residual_norm=None, phase_convention_diagnostic=None,
              explicit_H_matvec_count=0, small_Ritz_solve_count=0) for s in protocol['systems']]))
    write('fit_results.json', dict(status='NOT_RUN', fits=[], reason=STATUS))
    write('predicted_budgets.json', dict(status='NOT_RUN', systems=[dict(condition=s['condition'],
          arms={a:dict(signed_estimate=None, absolute_estimate=None, denominator=None, budget=None, status='NOT_COMPUTED')
                for a in protocol['arms']}) for s in protocol['systems']], ratios_label='prediction_only_not_truth_scored',
          ratios=None, scientific_budget_interpretation=False))
    write('cold_replay.json', dict(status='NOT_RUN_CONTRACT_UNCLOSED', initial_pass_complete=False, cold_pass_started=False,
          raw_proxy_max_difference=None, fit_coefficient_max_difference=None, prediction_max_difference=None,
          budget_max_difference=None, Ritz_diagnostic_max_difference=None, retained_rank_comparison=None,
          tolerance=None, accepted=False, reason=STATUS, primary_result=None, averaging_performed=False))
    actions = dict(source_load=0, explicit_Ritz_H_matvec=0, PF_forward_vector_action=0, logical_exact_H_echo=0,
                   group_application=0, group_materialization=0, small_Ritz_solve=0, scalar_fit=0)
    write('action_counts.json', dict(status='PRODUCTION_NOT_STARTED', production_actual=actions,
          initial_operational=actions, cold_validation=actions,
          planned_nominal_phase_a=dict(source_load=4, PF_forward_vector_action=32, logical_exact_H_echo=32,
              explicit_Ritz_H_matvec=36, small_Ritz_solve=4, scalar_fit=8, group_application=39904, group_materialization=11520),
          audit_only=dict(operational_archive_byte_metadata_checks=2,
              npy_member_file_hash_checks=sum(c['npy_member_file_hashes_verified'] for c in source_checks),
              numpy_array_decodes=0, original_pickle_reads=0), RUN_STARTED_lease_created=False,
          production_authorization_consumed=False, production_start_denied_before_lease_or_science=True,
          expm_internal=dict(matvec=None, matmat=None, rmatvec=None, norm_estimation=None, status='unknown; expm not invoked')))
    write('truth_access_audit.json', dict(scope='this Phase A attempt; excludes historical counts and synthetic tests',
          direct_truth_reads=0, branch_solves=0, truth_schur=0, exact_ground_operational_reads=0,
          historical_truth_reads=0, historical_branch_ID_reads=0, new_direct_truth_count=0,
          truth_only_original_source_opens=0, Phase_B_output_reads=0, Phase_B_execution=0,
          authority_metadata_and_code_read=True, sanitized_archive_only=True, oracle_allowlist_checks='PASS',
          private_binary_publication=False, count_basis='Only metadata/hash audit executed; no production backend, truth loader or original pickle dispatch'))
    write('private_recovery_receipt.json', dict(status='NOT_CREATED_NO_SCIENTIFIC_RETURN', private_snapshot=None,
          recovery_sha256=None, fsync_performed=False, serialization_only_recovery_required=False,
          reason=STATUS, scientific_rerun_count=0))
    # Package hashes intentionally distinguish an audit handoff from prediction freeze.
    write('artifact_inventory.json', dict(package_kind='pre_execution_stop_audit', prediction_freeze_complete=False,
          formal_prediction_sha256=None, intentionally_absent=['prediction_manifest.json', 'prediction.sha256'],
          reason='No scientific predictions exist; publication manifest is audit provenance only',
          cannot_satisfy_Phase_B_prediction_barrier=True))
    import numpy as np
    import scipy
    blas = io.StringIO()
    with contextlib.redirect_stdout(blas):
        np.show_config()
    write('cost_ledger.json', dict(status='NO_PRODUCTION_COST_OBSERVED', production_wall_seconds=None, production_peak_RSS_bytes=None,
          production_per_pass_system_arm_costs=[], predicted_QPE_budgets=None, cost_unit_sum=None,
          audit_only=dict(wall_seconds=time.perf_counter()-started, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                         measured_scope='builder interval through cost-ledger creation; excludes later provenance assembly, prior reading, pytest and remote publication'),
          environment=dict(python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__,
              PySCF=None, PySCF_status='not loaded', threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
              BLAS_configuration=blas.getvalue(), hostname=platform.node(), machine=platform.machine(),
              device='CPU', dependency_upgrades=0)))
    authorities = {'AGENTS.md'}
    authorities.update(R01+'/'+n for n in ('README.md','GO_NO_GO_FOR_FS_R1_PHASE_A.json','fs_r1_protocol_v2.json','branch_ladder.json',
          'branch_contract.md','phase_barrier_v2.md','truth_executor_contract.md','predicted_action_budget_v2.json','verification.json',
          'phase_a_v2.py','r01_common.py','r01_barrier.py','scoring_bridge.py','test_branch_math.py','test_fs_r01.py'))
    authorities.update(R0+'/'+n for n in ('new_source_identity.json','new_source_registry.json','sanitization_audit.json','source_io.py',
          'four_arm_contract.md','scoring_contract.json','cost_contract.json','recovery_contract.md','cold_replay_contract.md',
          'fs_r1_protocol.json','backend.py','implementation_pins.json','test_fs_r0.py','freeze.py'))
    authorities.update(P05+'/'+n for n in ('response_pilot_protocol.json','phase05_math.py'))
    authorities.update(P06+'/'+n for n in ('preflight_protocol.json','cold_replay_design.md'))
    authorities.update(C05+'/'+n for n in ('echo_numerical_contract.json','backend_reproduction_preflight.json',
          'closure_adapter.py','native_source_pins.json','test_fs_c05.py'))
    authorities.update('artifacts/pf_first_study_fs_c0_20261007/'+n for n in ('serialization_boundary.py','test_fs_c0.py'))
    authorities.add('artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/test_fs_c06.py')
    authorities.update(r['path'] for r in read(C05+'/native_source_pins.json')['sources'])
    sources = []
    for path in sorted(authorities):
        raw = (ROOT/path).read_bytes()
        assert raw == git('show', BASE+':'+path)
        sources.append(dict(path=path, bytes=len(raw), sha256=sha(raw),
             origin_result_commit=git('log','-1','--format=%H',BASE,'--',path).decode().strip(),
             verified_snapshot_commit=BASE, git_blob_sha=git('rev-parse',BASE+':'+path).decode().strip()))
    write('source_manifest.json', dict(repository=REPO, base_verified_snapshot_commit=BASE,
          sources=sources, origin_and_snapshot_roles_separate=True,
          current_request_origin='user attachment; first publication in this audit commit', request_sha256=sha(request_raw)))
    write('GO_NO_GO_FOR_PHASE_B.json', dict(status='NO_GO', Phase_A_final_status=STATUS, Phase_A_production_started=False,
          prediction_freeze_complete=False, prediction_sha256=None, Phase_B_authorized=False,
          numerical_contract_closed=False, source_identity_byte_metadata_checks='PASS', tests_pass=True, tests_total=260,
          production_actions=0, new_truth=0, stop='Return to GPT/user after audit publication; no Phase B',
          GPT_decision_required='Preregister numerical replay/norm acceptance rules and freeze revised protocol before production; no numerical tolerance chosen by Codex'))
    write('verification.json', dict(status='AUDIT_PASS_EXECUTION_NO_GO', final_status=STATUS, base_verified_snapshot_commit=BASE,
          existing_tests_rerun=260, tests_result='PASS', new_tests=0,
          no_new_tests_reason='Documentation/byte audit only; existing tests rerun as requested. No production runner implemented under an unclosed contract.',
          tests_scientific_scope='synthetic/guard/recovery tests; no actual N2/CO observables or truth',
          source_checks=source_checks, inherited_authority_files_verified=len(sources), old_artifacts_changed=False,
          production_started=False, production_numeric_gates_evaluated=False, physical_production_certified=False,
          prediction_sha256=None, recovery_snapshot_created=False, source_regeneration=0, scientific_actions=0, new_truth=0,
          publication_state_at_creation='not yet pushed; independent remote receipt recorded separately after commit'))
    write('README.md', '''# FS-R1 Phase A 実行前停止監査

**PHASE_A_NUMERICAL_CONTRACT_UNCLOSED**。添付§23に従い、productionを開始する前に停止した。
Phase A prediction freezeは成立しておらず、Phase BはNO-GO / 未承認。

v2はcold replayの再構築範囲を固定しているが、raw proxy・fit coefficient・arm prediction・budget・
deterministic Ritz診断の差を合格とするproduction用の比較規則/許容差がない。
H4のnoise ruleは観測した差をetaへ取り込む診断で、今回のreplay合格上限にはならない。
RitzのMGS/rank/Hermiticity閾値、synthetic testのatol、resource判定のeta=0.02も代用していない。
前回のGO判定ではこの数値契約の不足を見落としていた。旧GOを上書きせず、今回の追加監査として記録した。

読む順序：

1. [Phase B判定](GO_NO_GO_FOR_PHASE_B.json) → [数値契約監査](numerical_contract_audit.json)
2. [実行依頼の原文](authorization_request.md) §23 → [v2 snapshot参照](phase_a_protocol_snapshot.json)
3. [source byte/metadata確認](source_identity.json) → [実行/未実行値](production_results.json)
4. [260 tests再実行](tests.log) → [検証](verification.json) → [action counts](action_counts.json) / [truth audit](truth_access_audit.json)
5. [cost](cost_ledger.json) → [authority hashes](source_manifest.json) → [publication hashes](publication_manifest.json)

N2/COのsanitized archive SHA、全NPY member file SHA、metadata/array allowlist、ordered group SHAは一致。
NPYの数値decodeやH matvecを行わず、元のtruth-only pickleも開いていない。
H digestは凍結identityとarchive完全一致によりbindした。今回H CSR digestを再計算したとは主張しない。
source missing / reconstruction mismatch / branch failure / 観測済みnumerical failureではない。

|報告項目|N2|CO|
|---|---|---|
|retained Ritz rank|未計算|未計算|
|M00′ / M10′ / M01′ / M11′|すべて未計算|すべて未計算|
|B0′ / B01′ / B10′ / B11′ / prediction-only ratios|すべて未計算|すべて未計算|
|cold replay差 / 数値gate結果|未測定|未測定|

production source load/PF/echo/H/Ritz/fit/group actionsはすべて0。truth access / new direct truthも0。
production wall/RSSは未測定。metadata/hash監査のwall/RSSをcost ledgerへ別scopeで記録した。
既存260 tests PASSはproduction toleranceの証明ではない。
RUN_STARTED lease未作成、science returnなし、private scalar recovery未作成。
prediction SHAはnullで、prediction_manifest.json / prediction.sha256は意図的に作成していない。
publication_manifest.jsonは停止監査のhashであり、Phase B用のprediction hashではない。
private npz/pickle/vector/unitary/recoveryは一切公開していない。

GPTに判断してほしい事項は、観測前に固定するphysical-production replay/norm合格規則。
必要なunits・absolute/relative comparison・near-zero/near-infeasible budget・rank/status一致・fit/budgetへの誤差伝播を明示すること。
Codexは許容差を提案/選定していない。次の契約を承認・version/freezeした後に実行を再開する。
initial全2条件→cold全2条件のorchestration、Phase A lease、完全なdiagnostic/recovery wrapperも実行前review対象。
これらは実装残件であり、今回productionを試行した記録ではない。

起点はdd41c5eaad4a88339f7bbb69267bfdace9fb86e5。branchはpf-first-study-fs-r1-phase-a-20261007。
旧artifactと現在の第2研究workspaceを変更せず、追加auditだけをcommitする。
commit/push後の40桁SHA、remote tip照合、独立fetch/blob確認は外部receiptとhandoffで報告する。
この監査の公開後に停止する。
''')
    assert not git('diff', '--name-only', BASE)
    records = []
    for path in sorted(HERE.iterdir()):
        if path.is_file():
            assert path.suffix in ('.py', '.md', '.json', '.csv', '.log')
            raw = path.read_bytes()
            records.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(raw), bytes=len(raw)))
    write('publication_manifest.json', dict(repository=REPO, branch=BRANCH, package_kind='pre_execution_stop_audit',
          base_verified_snapshot_commit=BASE, self_excluded=True,
          self_exclusion_reason='publication_manifest.json excluded from own hash; committed manifest verified externally',
          prediction_sha256=None, prediction_freeze_complete=False, private_binary_publication=False,
          new_artifact_origin_result_commit='commit containing this manifest; resolved in post-push receipt',
          new_artifact_verified_snapshot_commit='independent remote fetched commit; resolved in post-push receipt',
          origin_and_snapshot_roles_separate=True,
          publication_status_at_creation='not yet pushed; frozen creation-time record', files=records))
    print(json.dumps(dict(status=STATUS, tests=260, new_public_files=len(records)+1,
                          authority_files=len(sources), production_actions=0, new_truth=0, prediction_sha256=None)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--tests-log', required=True)
    main(parser.parse_args())
