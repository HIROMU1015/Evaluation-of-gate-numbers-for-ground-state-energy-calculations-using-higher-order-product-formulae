"""Metadata/code-only FS-R0.1 generator; never unpickles or runs science."""
import copy
import json
from pathlib import Path
import subprocess
from r01_common import ROOT,HERE,R0,sha,canonical,execution_code_paths

BASE='3469b29f53a2c559bb8f6785bcba68a2896d41a5'
REQUEST=Path('/home/abe/.codex/attachments/b253cd95-62df-4b37-98b2-9bd793cf0ae8/貼り付けたテキスト.txt')
DISPLAY=[
    [0.06263494343795273,0.12526988687590546,0.18790483031385818,0.31317471718976365,0.5923370942191331,0.5983202971910435],
    [0.06546804264781796,0.1309360852956359,0.19640412794345388,0.3273402132390898,0.6066206637106297,0.6127481451622522]]
def write(name,obj):
    p=HERE/name
    raw=obj.encode() if isinstance(obj,str) else (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    if p.exists() and p.read_bytes()!=raw:raise FileExistsError('create-only preflight report differs: '+name)
    if not p.exists():p.write_bytes(raw)

def main():
    request=REQUEST.read_bytes();(HERE/'authorization_request.md').write_bytes(request)
    resolution=json.loads((HERE/'coordinate_resolution.json').read_text())
    assert resolution['authority_is_explicit_user_coordinate'] is True and resolution['choice'] in ('explicit_display','binary64_formula')
    original=json.loads((R0/'fs_r1_protocol.json').read_text());p=copy.deepcopy(original)
    systems=[]
    for spec,shown in zip(p['systems'],DISPLAY):
        derived=[*spec['training_absolute'],.5*spec['fit_scale_t_ref'],.99*spec['t0'],spec['t0']]
        differences=[dict(index=i,formula_value=left,display_value=right,formula_hex=float(left).hex(),display_hex=float(right).hex(),absolute_difference=right-left)
                     for i,(left,right) in enumerate(zip(derived,shown)) if float(left).hex()!=float(right).hex()]
        times=list(shown) if resolution['choice']=='explicit_display' else derived
        assert times[:3]==spec['training_absolute'] and times[-1]==spec['t0']
        assert all(a<b for a,b in zip(times,times[1:]))
        systems.append(dict(condition=spec['condition'],source_identity_sha256=spec['source_identity_sha256'],
            new_H_sha256=spec['new_H_sha256'],t_ref=spec['fit_scale_t_ref'],t0=spec['t0'],times=times,
            times_hex=[float(t).hex() for t in times],roles=['branch_certification']*5+['primary_scoring'],
            formulas=['0.1*t_ref (frozen 3point authority)','0.2*t_ref (frozen 3point authority)','0.3*t_ref (frozen 3point authority)',
                      '0.5*t_ref','0.99*t0','t0'],
            binary64_display_agreement=times==shown,binary64_formula_agreement=times==derived,
            binary64_authority_agreement=True,formula_display_differences=differences,
            coordinate_authority=resolution['choice'],coordinate_authority_record='coordinate_resolution.json',
            first_three_provenance='FS-R0 frozen external 3point coordinates; preserve binary64 authority',
            remaining_provenance='historical sentinel/S0 exact-time connection design; no result-driven time selection'))
    write('branch_ladder.json',dict(protocol_id='FS-R1-20261007-v2',systems=systems,total=12,scoring=2,certification=10,
        execution_order='N2 ascending six, then CO ascending six; fail aborts entire run',adaptive_insertion=False))
    contract=dict(truth_total_coordinates=12,truth_primary_scoring_coordinates=2,truth_branch_certification_coordinates=10,
        branch_times=['0.1*t_ref','0.2*t_ref','0.3*t_ref','0.5*t_ref','0.99*t0','t0'],
        first_selector='maximum_exact_ground_overlap',continuation_selector='maximum_previous_selected_vector_overlap',
        phase_cluster_selector='maximum previous-reference projector overlap; singleton equals maximum vector overlap',
        first_cluster_rule='seed eigenpair uses max ground overlap; if degenerate use its cluster projector',
        phase_cluster_gap=1e-8,phase_cluster_comparison='strict <; exactly threshold is singleton separation',
        cluster_ambiguity='reject chained connected cluster whose pairwise circular diameter >= gap',
        cluster_vector='normalized reference projection into selected eigenspace, deterministic largest-component phase',
        cluster_eigenphase='circular centroid of member eigenphases; projected vector must pass eigenpair residual',
        eigenpair_residual_gate=1e-10,unitarity_gate=1e-10,previous_overlap_gate=.9,
        tie_rule='first deterministic ascending circular eigenphase/real/imag/original ordinal; exact degenerate basis resolved by projector',
        comparator='diagnostic only; never used for continuation, t0 selection or estimator',
        branch_namespace='FS-R1:<source_identity_sha>:positive:k<ladder index>',
        unwrap_integer=0,direct_shift='angle(exp(-i E t) lambda)/t, S0 principal-angle energy-origin convention',
        branch_continuation_closed=True,physical_branch_certified_on_production=False,
        historical_truth_reuse=False,historical_branch_ID_reuse=False,adaptive_truth_extension='forbidden',
        failure_status='BRANCH_CONTINUATION_FAILED',failure_policy='abort remaining coordinates; no retry/grid/rule rescue; technical, no resource outcome',
        ground_isolation='truth-only original exact state/energy after verified Phase A barrier; no new ground solve',
        ladder_path=str((HERE/'branch_ladder.json').relative_to(ROOT)),ladder_sha256=sha((HERE/'branch_ladder.json').read_bytes()),
        numerical_backend='CPU complex128 native left-product on identity block; scipy.linalg.schur output complex',
        selected_vector_checkpoint='private npy plus identity/hash metadata, create-only/fsync',
        primary_scoring='only final t0 signed direct shift after both complete six-point ladders PASS')
    p.update(protocol_id='FS-R1-20261007-v2',stage='FS-R0.1 branch-extension preflight',
        revision_reason='new-source physical branch continuation requires preregistered lower-time certification ladder',
        supersedes_protocol_id=original['protocol_id'],supersedes_commit=BASE,
        truth_contract=contract,phase_B='after actual Phase A freeze/remote/code/source/recovery proof, two ascending six-coordinate truth-only ladders; score final t0 only',
        approved_status_amendment='branch_extension_amendment.md',final_preflight_status='GO_FOR_FS_R1_PHASE_A',
        execution_ready=True,FS_R1_science_authorized=False)
    write('fs_r1_protocol_v2.json',p)
    write('truth_budget.json',dict(truth_total_coordinates=12,truth_branch_certification_coordinates=10,truth_primary_scoring_coordinates=2,
        historical_truth_reuse=0,actual_production_truth=0,actual_FS_R1_science=0,adaptive_insertion=False,planned_only=True))
    plan=json.loads((R0/'predicted_action_budget.json').read_text())
    plan.update(truth_coordinates=12,branch_certification_coordinates=10,primary_scoring_coordinates=2)
    phaseB=dict(planned_only=True,truth_only_source_load=2,PF_unitary_construction=12,PF_identity_block_action=12,
        block_columns=1568,Schur_decomposition=12,branch_matching=12,selected_vector_checkpoint=12,
        eigenpair_residual=12,unitarity_residual=12,
        truth_group_matrix_application=6*sum(s['group_applications_per_vector'] for s in p['systems']),
        truth_group_materialization=6*sum(s['gate_materializations_per_vector'] for s in p['systems']),
        exact_ground_solve=0,cold_truth_replay=0,actual_actions=0,
        failure='actual consumed/completed counts only; no remaining points after failure')
    plan['phase_B_truth_validation']=phaseB;write('predicted_action_budget_v2.json',plan)
    write('cost_contract_truth.json',dict(category='truth_validation_cost',separate_from_Phase_A_calibration=True,QPE_addition=False,
        units=dict(actions='logical counts',wall='seconds',RSS='bytes',GPU_memory='bytes or null (CPU path)'),
        mandatory=list(phaseB),planned=phaseB,measured_production_values=None,
        threads_software='ContextV2 inherited snapshot',internal_eigensolver_operation_count=None))
    write('branch_checkpoint_schema.json',dict(private_payload='complex128 selected vector only; npy allow_pickle=False',
        public_manifest_fields=['private_path','sha256','source_identity_sha256','time','index','branch_id','dimension','dtype'],
        publication_of_vector=False,prior_required_for_indices_1_to_5=True,missing_or_changed='BRANCH_CONTINUATION_FAILED',
        create_only=True,fsync=True,automatic_science_retry=False))
    write('truth_output_schema.json',dict(required_coordinate_fields=['condition','source_identity_sha256','time','time_role',
        'selected_eigenvalue','selected_eigenphase','signed_direct_shift','direct_error','selected_branch_id','previous_branch_id',
        'ground_overlap','previous_vector_overlap','degenerate_projector_overlap','phase_cluster_size','minimum_phase_gap',
        'eigenpair_residual','unitarity_residual','selection_rule','ground_overlap_comparator_id','disagreement_flag','unwrap_integer',
        'wall_seconds','peak_RSS_bytes','GPU_memory_bytes','selected_vector_checkpoint','prediction_sha256'],
        eigenvalue_encoding='[real, imaginary]',minimum_phase_gap_single_dimension=None,anchor_previous_vector_overlap=None,
        vector_payload_forbidden=True,no_intermediate_resource_cost_or_best_time=True))
    write('phase_a_freeze_schema_v2.json',dict(stage='FS-R1-Phase-A',truth_opened=False,
        required_roles=['prediction','protocol','source_identity','code','recovery_reference'],
        code_bundle_format='FS-R1-code-v2',required_code_paths=execution_code_paths(),
        recovery_reference=dict(prediction_sha256='same exact committed prediction bytes',recovery_saved_before_public_validation=True),
        protocol_sha256=sha((HERE/'fs_r1_protocol_v2.json').read_bytes()),
        requires_full_commit_manifest_prediction_source_code_hashes_and_independent_remote_receipt=True,
        current_science_authorized=False))
    write('branch_extension_amendment.md','# Approved FS-R0.1 amendment\n\nDirect PF truth路線を維持し、new source上のlower-time anchorからpositive branchを追跡する。t0単独のmaximum-ground selectorへ変更しない。\n\ntruth budgetを2→12へ正式改訂：certification10＋t0 scoring2。FS-R0.1はprotocol/code freezeとsynthetic preflightのみで、今回の実truth/scienceの承認ではない。旧v1や旧artifactは上書きしない。branch ladderは既存design由来。adaptive insertionとfailure後の救済は禁じ、GPT/userへ戻す。\n')
    write('branch_contract.md','# Branch contract\n\n初点はmaximum exact-ground-overlap eigenpairでseed。以後singletonはmaximum previous-selected-vector overlap、phase gap<1e-8のclusterはprojector overlapを使う。厳密thresholdは非cluster。seedの退化cluster内もreferenceの投影を使う。\n\nSchur eigenpairをphase/real/imag/original ordinal順に並べ、tieは最初。退化内はP referenceを正規化してlargest-magnitude pivotのphaseを固定。cluster phaseはcircular centroid、選択vectorの固有残差が1e-10を超えるnear-degenerate clusterはunresolvedとして停止。連鎖clusterのcircular diameter>=gap、zero projector、非直交/duplicate eigenbranchesも停止。\n\ncontinuation時の選択vector overlap>=0.9、unitarity Frobenius/eigenpair 2-norm<=1e-10。ground comparatorはdiagnosticのみ。新source namespaceとladder indexをcheckpointにbindする。旧ID6/9は不可。direct shiftとunwrap0はS0 principal-angle conventionを維持する。\n\nこれらは実装上の事前固定規則で、production PASSを意味しない。branch failureはtechnical gate failure、resource successには数えない。\n')
    rows=['|condition|six ascending times|','|---|---|']+[f"|{s['condition']}|{s['times']}|" for s in systems]
    write('fs_r1_protocol_v2.md','# FS-R1-20261007-v2\n\n'+p['revision_reason']+'\n\n'+'\n'.join(rows)+'\n\n最初5点/conditionはbranch certification、最後t0だけresource scoring。Phase Aのsources/training/t0/Ritz8/4arms/constants/budgets/outcomes/cold replayはv1を維持し、truth契約とbarrierだけを改訂。M11p primary、M01p challenger。new source identityはR0のまま。\n\nGO後も別承認までscienceを実行しない。physical branch PASSとresource outcomeはFS-R1 Phase B後に初めて判定できる。\n')
    write('truth_executor_contract.md','# Production truth executor preflight\n\ntruth_executor.execute_truthは1568-sector metadataにbindしたCPU native PF identity-block construction→complex Schur→ordered branch matching→residual/ unitarity→private scalar/checkpointの経路。condition内は昇順に前checkpointを検証して追跡し、計12以外を受け付けない。N2完了後COへ進む。failureはrun全体の残りtruthを中止する。\n\nRUN_STARTEDのexclusive leaseがretryを防ぐ。scalar returnをfsync/private保存後にvector checkpoint、最後にcomplete ladder検証。public serialization recoveryはprivate scalarsを読み直すだけ。vector/ground/unitaryをGitへ出さない。R0.1ではproduction guardが全経路を拒否し、tiny toy fixturesのみ実行する。\n')
    write('truth_only_source_contract.md','# Truth-only source isolation\n\nloaderはactual committed Phase A/remote/code/source/prediction/recovery barrier後、別science authorizationを確認してからprivate original C0.6 bytesをwhole SHA照合・decodeする。stored exact groundとH-without-constant energyのみbranch seed/comparatorに使い、新ground solveをしない。\n\nPFは同じR0 operational archiveからconstructし、H SHA/sector/basis/metadata/group/removed constantをnew identityへ照合。oracle vectorはPhase A sourceにもpublic outputにも渡さない。R0.1では元pickleをdecodeせず、既知binaryのavailability/hash確認に留める。\n')
    write('phase_barrier_v2.md','# V2 Phase A/B barrier\n\n40-character commit、actual committed/local manifest/prediction/protocol/source identity/all execution code/recovery reference、independent remote receiptのhashを照合する。predictionは4arm budgetsをnew estimatesから再計算するscalar検査で検証し、truth diagnosticsを拒否する。recovery referenceは同じprediction bytesへbindする。\n\nv2 Contextは同じprotocol hashへの別承認を要求。Phase A mathはv1のsource/coordinate/Ritz/PF/echo/fit/budget関数を変えず、Contextの承認protocolだけv2へbindする。truth-only codeはPhase B/barrier proof後のみ。今回の承認はpreflightだけ。\n')
    write('source_manifest.json',dict(base_verified_snapshot_commit=BASE,request_sha256=sha(request),request_origin_commit=None,
        request_first_publication='R0.1 handoff commit',origin_and_snapshot_roles_separate=True,
        sources=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size,
            origin_result_commit=subprocess.check_output(['git','log','-1','--format=%H',BASE,'--',str(p.relative_to(ROOT))],cwd=ROOT,text=True).strip(),
            verified_snapshot_commit=BASE,git_blob_sha=subprocess.check_output(['git','rev-parse',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT,text=True).strip())
            for p in [R0/n for n in ('README.md','fs_r1_protocol.json','new_source_registry.json','new_source_identity.json',
                'publication_manifest.json','GO_NO_GO_FOR_FS_R1.json','source_io.py','backend.py','freeze.py','scorer.py')]+
            [ROOT/'review_response/_pf_first_study_s0_exact_time_scoring_base.py',ROOT/'review_response/run_pf_first_study_s0_exact_time_scoring_v1_1.py',ROOT/'AGENTS.md']]))
    write('authorization_scope.json',dict(stage='FS-R0.1',request_sha256=sha(request),base_commit=BASE,
        allowed='protocol/implementation/freeze/synthetic tests/handoff',production_truth_authorized=False,FS_R1_science_authorized=False,
        new_source_reconstruction_authorized=False,truth_budget_amended_for_future_R1=12,stop_after_handoff=True))
    print(json.dumps(dict(ladder_binary64_exact=True,conditions=2,coordinates=12,production_actions=0)))

if __name__=='__main__':main()
