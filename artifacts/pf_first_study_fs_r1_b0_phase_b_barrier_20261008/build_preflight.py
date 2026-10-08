"""Build additive B0 contracts/audit from saved scalars; no science dispatch."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from b0_common import (A,A0,R01,R0,SCIENCE,HANDOFF,PREDICTION,RESULT,PROTOCOL,NUMERICAL,CODE_A,LADDER,
    REMOTE,sha,canonical,read,verify_execution)
from phase_b_controller import preflight_phase_b
from v3_barrier import verify_phase_a

REQUEST=Path('/home/abe/.codex/attachments/51cac800-b8b4-4d26-aeef-3374e3b73ab8/貼り付けたテキスト.txt')
def write(name,value):
    raw=value.encode() if isinstance(value,str) else canonical(value)
    with (HERE/name).open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    (HERE/name).chmod(0o400)
    fd=os.open(HERE,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def main():
    assert git('rev-parse','HEAD')==HANDOFF
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    code=verify_execution()
    log=Path('/tmp/fs-r1-b0-all-tests-20261008.log').read_text()
    assert '419 passed' in log and 'failed' not in log
    counts=dict(Phase_A_reexecution=0,production_Ritz=0,production_PF=0,production_echo=0,
        new_direct_truth=0,production_branch_execution=0,production_Schur=0,exact_ground_oracle_decode=0)
    observer=dict(original_pickle_open=0,pickle_find_class=0,production_lease_created=False)
    original_paths={str(r['private_original_path']) for r in read(ROOT/R0/'new_source_registry.json')['sources']}
    def observe(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
            if os.fsdecode(args[0]) in original_paths:observer['original_pickle_open']+=1
        if event=='pickle.find_class':observer['pickle_find_class']+=1
    sys.addaudithook(observe)
    stopped=preflight_phase_b()
    proof=verify_phase_a();data=proof.data
    assert stopped['proof_sha256']==proof.digest
    assert data['remote_receipt_sha256']==read(HERE/'phase_b_bridge_contract.json')['handoff_proof_sha256']
    assert data['oracle_decode']==0 and not any(observer.values())
    lease_path=Path(read(HERE/'phase_b_bridge_contract.json')['private_truth_lease_registry'])
    assert not lease_path.exists()
    request=REQUEST.read_bytes()
    write('authorization_request.md',request.decode())
    write('tests.log',log)
    external=read(HERE/'phase_a_external_remote_verification.json')
    authority_paths=set(external['verified_file_sha256'])
    test_paths=[
        'artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py',
        'artifacts/pf_first_study_fs_c05_execution_closure_20261007/test_fs_c05.py',
        'artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/test_fs_c06.py',
        R0+'/test_fs_r0.py',R01+'/test_branch_math.py',R01+'/test_fs_r01.py',A0+'/test_a0.py']
    authority_paths.update(test_paths);authority_paths.add('AGENTS.md')
    authorities=[]
    for path in sorted(authority_paths):
        raw=(ROOT/path).read_bytes()
        assert raw==subprocess.check_output(['git','show',HANDOFF+':'+path],cwd=ROOT)
        authorities.append(dict(path=path,sha256=sha(raw),bytes=len(raw),
            git_blob_sha=git('rev-parse',HANDOFF+':'+path),
            origin_result_commit=git('log','-1','--format=%H',HANDOFF,'--',path),
            verified_snapshot_commit=HANDOFF))
    write('source_manifest.json',dict(repository=external['repository'],base_verified_snapshot_commit=HANDOFF,
        source_origin_and_verified_snapshot_roles_separate=True,sources=authorities,
        request_sha256=sha(request),request_origin='current user attachment; implementation/preflight only',
        private_binary_publication=False))
    freeze_view={k:data[k] for k in ('science_origin_commit','handoff_commit','prediction_sha256',
        'production_results_sha256','protocol_sha256','numerical_contract_sha256','phase_a_execution_code_sha256',
        'source_hashes','branch_ladder_sha256','remote_receipt_sha256','published_origin_receipt_sha256',
        'private_recovery_checks','archive_byte_checks','checked_blob_sha256','handoff_additions')}
    write('phase_a_freeze_verification.json',dict(status='PASS',verified_proof_sha256=proof.digest,
        **freeze_view,remote_independent_blobs_verified=external['actual_remote_blobs_verified'],
        public_manifest_file_records_verified=19,private_snapshots_read_only_verified=7,
        numerical_gates_pass=True,cold_replay_pass=True,all_eight_initial_budget_intervals_finite=True,
        Phase_A_reexecution=0,oracle_decode=0,stopped_before_truth_only_boundary=stopped))
    p=data['protocol'];ladder=data['branch_ladder']
    write('branch_ladder_binding.json',dict(authority_path=R01+'/branch_ladder.json',authority_sha256=LADDER,
        rules_protocol_path=R01+'/fs_r1_protocol_v2.json',prediction_protocol_id=p['protocol_id'],
        unchanged=True,total_coordinates=12,certification_coordinates=10,scoring_coordinates=2,
        adaptive_extension=False,binary64_authority='existing ladder JSON/times_hex; preserve displayed-coordinate decision',
        systems=ladder['systems'],source_hashes=data['source_hashes']))
    write('phase_b_execution_plan.json',dict(entrypoint='phase_b_controller.py:execute_phase_b',
        current_stage='FS-R1-B0',Phase_B_authorized=False,truth_budget=12,
        order=['authorization validation','committed v3 freeze/local/independent remote/source/recovery verification',
            'authorization-keyed exclusive truth lease','N2 truth-only source; ascending six points',
            'CO truth-only source; ascending six points','complete both ladders; score final two t0 only',
            'private final scalar recovery','public validation/serialization','future separate publication'],
        systems=[dict(condition=s['condition'],dimension=s['dimension'],source_identity_sha256=s['source_identity_sha256'],
            times=l['times'],times_hex=l['times_hex'],roles=l['roles']) for s,l in zip(p['systems'],ladder['systems'])],
        no_adaptive_rescue=True,branch_failure='abort all remaining truth; technical outcome; no resource judgment',
        production_callback_replacement=False,prediction_recalculation=False))
    cost_plan=dict(truth_only_source_load=2,PF_identity_block_action=12,PF_unitary_construction=12,
        Schur_decomposition=12,branch_matching=12,unitarity_residual=12,eigenpair_residual=12,
        selected_vector_checkpoint=12,truth_coordinate_attempt=12,truth_coordinate_completed=12)
    write('truth_validation_cost_contract.json',dict(cost_class='truth_validation_cost',planned=cost_plan,
        truth_coordinates=12,certification=10,scoring=2,actual_production_B0=dict.fromkeys(cost_plan,0),
        measured_fields=['attempted/completed coordinates','wall_seconds','peak_RSS_bytes','GPU_memory_bytes',
            'truth-only source loads','identity-block/unitary PF','Schur','matching','residuals','checkpoints'],
        internal_work=dict(PF_kernel=None,Schur_internal=None,status='unknown, not zero'),
        actual_peak_RSS_or_GPU_truth=None,classical_calibration_cost_separate=True,predicted_QPE_rotations_separate=True,
        QPE_addition=False,planned_values_not_measured=True))
    import numpy,scipy
    mem={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key,value,*_=line.split()
        if key in ('MemTotal:','MemAvailable:'):mem[key.rstrip(':')]=int(value)*1024
    registry=read(ROOT/R0/'new_source_registry.json')['sources']
    availability=[dict(condition=r['condition'],truth_only_private_original_available=Path(r['private_original_path']).is_file(),
        original_byte_size=Path(r['private_original_path']).stat().st_size,
        expected_whole_sha256=r['private_original_whole_sha256'],original_file_opened=False,
        whole_hash_rechecked_in_B0=False,decode_in_B0=False) for r in registry]
    assert all(r['truth_only_private_original_available'] for r in availability)
    kernel_path=ROOT/R01/'truth_executor.py'
    from truth_adapter import kernel_ast,KERNEL_NAMES
    original_nodes=[n for n in ast.parse(kernel_path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in KERNEL_NAMES]
    assert ast.dump(kernel_ast(kernel_path.read_bytes()),include_attributes=False)==ast.dump(ast.Module(body=original_nodes,type_ignores=[]),include_attributes=False)
    write('truth_executor_readiness.json',dict(status='STATIC_AND_SYNTHETIC_READY',
        mathematical_kernel_authority=R01+'/branch_math.py',mathematical_kernel_sha256=sha((ROOT/R01/'branch_math.py').read_bytes()),
        extracted_truth_helpers=sorted(KERNEL_NAMES),extracted_helper_arithmetic_AST_identical=True,
        extracted_helper_source_sha256=sha(kernel_path.read_bytes()),production_dimension=1568,
        one_complex128_dense_array_bytes=1568*1568*16,memory_estimate_scope='one array only; not full Schur peak/performance',
        environment=dict(python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,
            threads={k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            available_disk_bytes=shutil.disk_usage('/tmp').free,**mem),
        source_availability_stat_only=availability,max_new_synthetic_truth_dimension=3,
        full_synthetic_ladder_and_native_identity_block_and_Schur_test_pass=True,
        physical_1568_unitary_or_Schur_executed=False,production_numerical_success_or_performance_measured=False,
        production_ground_solves=0,Phase_B_authorized=False))
    write('production_action_audit.json',dict(stage='FS-R1-B0',scope='this implementation/preflight task only',
        counts=counts,observed_read_only_preflight=observer,truth_lease_registry_available_but_uncreated=str(lease_path),
        production_lease_created=False,Phase_B_authorized=False,
        tests_scope='synthetic <=16 only; new B0 truth fixtures use dimension 2/3; no actual molecule oracle',
        sanitized_archives_checked_by_bytes_without_array_decode=True,
        private_snapshot_reads_are_saved_Phase_A_scalars_only=True,old_artifacts_changed=False))
    write('phase_a_v3_freeze_binding_contract.md',"""# v3 Phase A freeze binding

Science origin is 89c091e885c07b7c02883b1479a143c23f51df3c; handoff is e00ebc2024f72272cec64ebfd20c771d03665e95. The immediate parent and add-only handoff diff are checked. All frozen members stay equal at origin/handoff/local/independent remote.

prediction.sha256 is SHA256 of exact canonical prediction_manifest.json, d1f95e5ee38e72cc5cb04cfb805c0ae441060104828c18268574acda5d2215a9. Result payload SHA is separately 899046840755e57531fac06ff4946fe947544040b3006963b28aeab0e241a4d1. The existing record-array manifest and self-exclusion are preserved.

Verify every path/length/SHA/actual committed/local/remote byte, v3 protocol, numerical contract, parsed canonical Phase A execution bundle and all members; source identities/registry/archive whole/member/allowlists; frozen scalar validator; cold/numerical gates; eight finite intervals; truth-zero audit; private scalar recovery and authorization/lease. No arrays are decoded. Missing recovery is NO-GO.

The published remote receipt proves the science-origin commit. The new read-only adapter proves the handoff from a new independent bare with no alternates. Both receipts' target commits, manifest/payload hashes, authority identities, actual target maps and independent Git objects are checked. PASS alone is insufficient.

VerifiedFreeze contains immutable canonical evidence and an internal issuance seal from this full validation. A dictionary carrying verified=True cannot open a truth callback. These are workflow provenance guards, not authentication against arbitrary Python/file manipulation.
""")
    write('phase_b_authorization_contract.md',"""# Separate Phase B science authorization

B0 issues no production authorization. A future explicit approval must provide: explicit_science_authorization=true; phase=FS-R1-Phase-B; request_stage=FS-R1-Phase-B-production; nonempty approval_reference; a new fixed authorization_id; protocol_sha256; prediction_sha256; science_origin_commit; handoff_commit; handoff_proof_sha256; phase_b_execution_code_sha256; branch_ladder_sha256; source_hashes; truth_coordinate_budget=12.

Use full-precision authority from phase_b_bridge_contract.json and parsed canonical execution_code_identity.json. The consumed Phase A authorization ID is rejected. B0 GO is preflight eligibility, not approval.

Validate authorization before freeze verification or a truth lease. Then validate actual v3 freeze/independent remote/recovery/source/code. Only then atomically create the fixed authorization-keyed lease in /tmp/fs-r1-phase-b-production-private-20261008/leases. Changing run ID cannot reuse approval. Failed/partial/completed/public-failed states all prohibit another science run. No production callback/registry substitution is accepted.
""")
    write('v3_scoring_bridge_contract.md',"""# Frozen initial nominal-budget scoring

Use verified initial_operational saved estimates and nominal/B_min/B_max/uncertainty values. Cold is reproducibility evidence only. Verification may compare the saved budget with the existing v3 analytic expression exactly; scoring never recomputes/replaces it.

Require a sealed Phase A proof and both complete validated six-coordinate ladders. Reject partial/failed/extra/nearest-time/historical/source-namespace/code/scope substitutions. All 12 rows are validated, but only the two final t0 direct shifts enter resource scoring. Synthetic truth outputs remain labelled synthetic and cannot be mixed with production rows.

e=abs(d). S=epsilon_E-e-beta*K/(t0*saved_nominal_budget). Safe iff S>=0, unsafe iff S<0. No new allowance/certificate or truth-driven narrowing. Intentional undefined budgets are indeterminate and cannot support a gain; the actual frozen package must have eight finite initial intervals.

Primary_gain: safe M11p and B11<=0.98 B0. Local_gain: safe M01p and B01<=0.98 B0. State_increment: both safe and B11<=0.98 B01. Safety_repair: unsafe M01p and safe M11p. Keep M11p primary/M01p challenger, existing 0/2,1/2,2/2 interpretation and STOP rules; unsafe cannot be averaged away.

Saved interval endpoint slack diagnostics describe numerical sensitivity only. The registered nominal-budget primary rule is unchanged. No post-hoc best arm, new scientific success threshold or truth certificate is introduced.
""")
    write('truth_only_barrier_contract.md',"""# Truth-only boundary

Order: separate authorization -> actual committed v3 Phase A freeze -> independent remote receipt -> prediction/protocol/code/source/recovery -> authorization-keyed truth lease -> private original oracle source -> exactly 12 branch coordinates.

B0 calls preflight_phase_b, which returns VERIFIED_STOPPED_BEFORE_TRUTH_ONLY_BOUNDARY without creating a production lease or invoking a truth-only source/kernel callback. Synthetic truth is limited to <=16 dimensions; actual 1568 metadata cannot open an oracle through synthetic context.

The pinned v2 load_truth_source/native_unitary/checkpoint helpers are extracted as unchanged function ASTs. Their gate is supplied by the new controller and requires genuine sealed v3 evidence and the separately authorized context. No fabricated v2 proof/hash/verified flag is passed. The immutable v3 proof exposes the fixed protocol to those kernels.

The original source is opened/whole-hash-checked/decoded only after the lease. Stored exact ground and removed-constant energy convention seed/diagnose the branch; no new ground solve occurs. The same sanitized archive/H/sector/basis/groups/PF are checked. Oracle energy/vector never enters prediction/scoring preprocessing or public payload.
""")
    write('recovery_contract.md',"""# Phase B lease/checkpoint/scalar recovery

Exclusive authorization-keyed RUN_STARTED and append-only fsync events use the unchanged A0 lease implementation. Production registry/binding is fixed; no change of run ID/registry can rescue a consumed approval.

Before each coordinate: prior checkpoint integrity and exact source/index/time/branch binding; create-only attempt record. Native PF identity-block -> inherited complex Schur/branch/residual gates -> immediate scalar recovery (before checkpoint/public schema). Private selected vector keeps the inherited npy+metadata checkpoint and adds a create-only SHA sidecar binding authorization/protocol/prediction/Phase-B-code/source/RUN_STARTED/proof.

Every scalar recovery is canonical/create-only/fsync/SHA and bound to RUN_STARTED, authorization/code/source/protocol/freeze and journal. Full ladders are validated before final endpoint scoring. Final scalar recovery precedes public serialization. Arrays/ground/energy/oracle payloads are rejected.

Any source/numeric/branch/checkpoint/recovery failure aborts all remaining truth and records actual attempted/completed coordinates and cost. No resource interpretation from an incomplete ladder. Public failure after final science leaves the consumed lease completed. publish_saved verifies saved bytes/hash/binding/journal and serializes only; it has no science callback. Private vectors/matrices/source/snapshot binaries stay outside Git.
""")
    go=dict(status='GO_FOR_FS_R1_PHASE_B_PRODUCTION',stage='FS-R1-B0',preflight_only=True,
        Phase_B_authorized=False,tests_pass=True,tests_existing=317,tests_new=102,tests_total=419,
        v3_freeze_binding=True,scoring_bridge=True,truth_only_barrier=True,
        branch_executor_static_synthetic_ready=True,lease_and_recovery_complete=True,
        phase_a_prediction_sha256=PREDICTION,phase_b_execution_code_sha256=code,
        truth_coordinates_planned=12,truth_coordinates_executed=0,zero_action_audit=counts,
        actual_production_numerics_performance_or_resource_outcome_established=False,
        remaining_preflight_blockers=[],next='GPT review and separate explicit Phase B production authorization; STOP')
    write('GO_NO_GO_FOR_PHASE_B_PRODUCTION.json',go)
    write('verification.json',dict(status='PASS',final_status=go['status'],base_commit=HANDOFF,
        phase_a_science_origin_commit=SCIENCE,phase_a_handoff_commit=HANDOFF,
        prediction_sha256=PREDICTION,production_results_sha256=RESULT,protocol_sha256=PROTOCOL,
        numerical_contract_sha256=NUMERICAL,phase_a_execution_code_sha256=CODE_A,
        phase_b_execution_code_sha256=code,phase_b_execution_code_members=36,
        source_hashes=data['source_hashes'],branch_ladder_sha256=LADDER,
        real_freeze_proof_sha256=proof.digest,private_recovery_snapshots_read_only_verified=7,
        independent_Phase_A_remote_blobs_verified=external['actual_remote_blobs_verified'],
        tests=dict(existing=317,new=102,total=419,result='PASS'),
        all_user_test_requirements_1_to_50_covered=True,kernel_arithmetic_AST_identity=True,
        authority_files=len(authorities),Phase_B_authorized=False,production_actions=counts,
        old_artifacts_changed=False,private_binaries_published=False,
        publication_status_at_creation='not yet pushed; final independent B0 receipt/handoff recorded after publication',
        not_established=['1568 production branch/Schur gates','physical branch certification','performance','actual resource/safety outcomes']))
    write('README.md',f"""# FS-R1-B0 v3 Phase B barrier closure / preflight

**GO_FOR_FS_R1_PHASE_B_PRODUCTION**（preflight）。Phase B science authorizationはfalse。別承認まで停止する。

固定v3 Phase Aを一切変更せず、actual Git/independent remote/private recoveryからのbarrier、保存budgetを使うscoring、既存branch mathへのv3 controller、authorization-keyed leaseとscalar/checkpoint recoveryを実装した。

読む順序：

1. [GO判定](GO_NO_GO_FOR_PHASE_B_PRODUCTION.json) → [real freeze検証](phase_a_freeze_verification.json)
2. [v3 binding](phase_a_v3_freeze_binding_contract.md) / [remote adapter evidence](phase_a_external_remote_verification.json)
3. [bridge identity](phase_b_bridge_contract.json) / [authorization](phase_b_authorization_contract.md) / [truth-only barrier](truth_only_barrier_contract.md)
4. [scoring](v3_scoring_bridge_contract.md) / [ladder](branch_ladder_binding.json) / [execution plan](phase_b_execution_plan.json)
5. [executor readiness](truth_executor_readiness.json) / [recovery](recovery_contract.md) / [cost](truth_validation_cost_contract.json)
6. [419 tests](tests.log) / [zero-action audit](production_action_audit.json) / [verification](verification.json)
7. [code bundle](execution_code_identity.json) / [source manifest](source_manifest.json) / [publication manifest](publication_manifest.json)

Science-origin={SCIENCE}、handoff={HANDOFF}。両者の親・add-only差分と凍結blob不変を確認した。
Prediction SHA={PREDICTION} はcanonical prediction manifestのSHA。Result payload SHA={RESULT} は別役割。
Phase Aの全値・budget区間・uncertainty・source/code/protocolは不変。Remote receiptも改変していない。

新しい独立bareでPhase Aの121 blobを取得・照合し、既存science-origin receiptと追加handoff receiptの役割を分離した。barrierはPASSだけでなくactual committed/local/remote bytesと対象hash mapsを確認する。
Private scalar recovery 7件もread-onlyで全SHA/sidecar/journal/lease/authorization/source/protocol/code/public resultを検証した。Missing snapshotならNO-GO。Sanitized archiveは全member/allowlist/whole SHAを確認したが、numpy arrayはdecodeしていない。

v2 branch mathとnative PF/Schur/checkpoint算術は旧ファイルを変更せず再利用する。v3 proofを旧v2 proofへ偽装しない。
Inherited row provenanceはmathのv2を保持し、新execution_provenanceとproof/code bindingがv3実行を表す。4つの抽出kernel ASTは原本と完全一致。
固定ladderは12点（certification10、scoring2）。Binary64は旧JSON/times_hexをauthorityとし、表示値や0.99t0の乗算で再生成しない。
Ground overlapは初点seed/comparatorのみ、以後はprevious-vector/projector continuity。overlap>=0.9、unitarity/eigenpair residual<=1e-10、phase cluster strict <1e-8、tie/phase/unwrap0を保持する。
Extra/adaptive/nearest-time/historical rescueなし。失敗は残りtruthを全停止するtechnical outcome。

Scoringは検証済みinitialの保存nominal budgetそのものを使う。Coldで上書きせず、prediction/fit/budget再計算も行わない。
両ladder全点が成立した場合のみ最終t0の2 truthをscoreする。未成立truthには科学判定を返さない。
Primary/local/state increment/safety repair、0/2・1/2・2/2、unsafe STOPを維持。Intervalは数値感度診断で、primary nominal ruleとtruth certificateへ変えない。

**既存317＋新規102＝419 PASS**。Real freeze受理、改変/欠落/lineage/code/source/recovery/remote拒否、保存budgetの使用、safety境界/outcome、12点toy continuation、failure STOP、authorization/duplicate lease、checkpoint、serialization-only recoveryを検証した。
新規truth fixturesは2/3次元。Real scalar/hash auditは実行したが、1568 unitary/Schur・oracle decodeは0。Static resource/backend/原source availabilityは確認しただけで、production性能・数値成立・物理branch・実resource safetyは未測定。

Phase B全production actions=0、Phase A再実行=0、production lease未作成、Phase_B_authorized=false。旧artifact/branchと現在のIDE編集は保全する。
Private vectors/matrices/ground/source/recovery bytesはGitへ公開しない。Synthetic authorization metadataはtestsのfixtureであり、operational承認ではない。

Future entrypointはphase_b_controller.execute_phase_b(authorization, run_id, public_path)。別承認が全authority/12点budgetへbindし、actual freezeとprivate recoveryが再検証できる場合のみleaseを作りtruth sourceを開く。
B0 hash/bundleは{code}（parsed compact sorted JSON＋newline）。公開後の40文字B0 commit/remote tip/blob/manifest検証は別receiptとfinal handoffで示し、自己参照commit/hash循環を作らない。

GPTに判断してほしい項目：v3 barrier/scoring/executor/lease/recovery契約のレビューと、12点Phase B productionを別承認するか。B0 GOだけでtruth実行を始めてはいけない。
""")
    pub_files=[]
    for path in sorted(HERE.iterdir()):
        if path.name=='publication_manifest.json':continue
        assert path.is_file()
        raw=path.read_bytes()
        pub_files.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(raw),bytes=len(raw)))
    write('publication_manifest.json',dict(package_kind='FS-R1-B0-v3-Phase-B-barrier-preflight',
        repository=external['repository'],branch='pf-first-study-fs-r1-b0-phase-b-barrier-20261008',
        base_verified_snapshot_commit=HANDOFF,phase_a_prediction_sha256=PREDICTION,phase_b_execution_code_sha256=code,
        production_science_authorized=False,private_binaries_published=False,files=pub_files,
        self_excluded=True,self_exclusion='publication_manifest.json excludes itself; post-push receipt separate',
        old_science_artifacts_unchanged=True))
    print(json.dumps(dict(status=go['status'],tests=419,public_files=len(pub_files)+1,
        authority_files=len(authorities),Phase_B_authorized=False,production_actions=counts,
        phase_b_execution_code_sha256=code)),flush=True)

if __name__=='__main__':main()
