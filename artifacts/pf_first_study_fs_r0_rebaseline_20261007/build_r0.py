"""FS-R0 identity-only source freeze and additive design builder; no science calls."""
import hashlib
import json
from pathlib import Path
import pickle
import subprocess
import sys
import os

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from source_io import export_operational,load_operational,canonical,sha,durable_create,array_identity,sparse_hash

BASE='14972353238cb001ccb1f754288daaae1ec3f65e'
C06='artifacts/pf_first_study_fs_c06_functional_equivalence_20261007'
C05='artifacts/pf_first_study_fs_c05_execution_closure_20261007'
C0='artifacts/pf_first_study_fs_c0_20261007'
PRIVATE=Path('/tmp/fs-r0-operational-private-20261007')
URL='https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'

def read(p):return json.loads((ROOT/p).read_text())
def write(name,obj):
    p=HERE/name
    text=obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if p.exists():
        if p.read_text()==text:return
        raise FileExistsError('create-only FS-R0 report differs: '+name)
    p.write_text(text)

def main():
    request=Path('/home/abe/.codex/attachments/96945275-79ae-4f83-9eb5-bd69724ed07b/貼り付けたテキスト.txt').read_bytes()
    (HERE/'authorization_request.md').write_bytes(request)
    write('authorization_scope.json',dict(request_sha256=sha(request),base_commit=BASE,session_date_JST='2026-10-07',
        stage='FS-R0',FS_R1_science_authorized=False,new_direct_truth_authorized=False,
        history_route_closed=True,approved_amendment='branch_continuation_amendment.md',
        stop='publish preflight; no R1 execution'))
    baseline=read(C05+'/baseline_contract.json')
    ledger=read(C06+'/cost_ledger.json')
    env=read(C06+'/validation_contract.json')['reconstruction']
    implementation={}
    for name,p in [('c05_adapter',C05+'/closure_adapter.py'),('ritz_math','artifacts/pf_first_study_response_pilot_phase05_20261006/phase05_math.py')]:
        implementation[name]=dict(path=p,sha256=sha((ROOT/p).read_bytes()))
    write('implementation_pins.json',implementation)
    identities=[]; registry=[]; audits=[]; specs=[]
    from backend import native
    ns=native()
    for spec,record in zip(baseline['systems'],ledger['reconstruction_resources']):
        condition=spec['condition']
        source=Path('/tmp/fs-c06-validation-private-20261007')/(condition+'_reconstructed_validation.pkl')
        if not source.is_file():
            write('GO_NO_GO_FOR_FS_R1.json',dict(status='NO_GO_REGENERATED_SOURCE_BYTES_UNAVAILABLE',condition=condition))
            return
        raw=source.read_bytes()
        if sha(raw)!=record['private_binary_sha256']: raise ValueError('C0.6 one-shot exact bytes changed')
        d=pickle.loads(raw)
        destination=PRIVATE/condition
        identity=export_operational(d,baseline['current_m3_sequence'],destination,record['H_sha'])
        identity.update(condition=condition,source_generation_code_revision=env['code_revision'],
            source_generation_contract_commit='a5fb9835657c3e5ac1658d1323b5746bf318fc8c',
            source_result_origin_commit=BASE,verified_snapshot_commit=BASE,
            generation_environment=env,private_original_whole_SHA=sha(raw))
        identities.append(identity)
        digest=sha(canonical(identity))
        loaded=load_operational(destination/'source.npz',identity['source_archive_sha256'],ns)
        assert sparse_hash(loaded['hamiltonian'])==record['H_sha']
        assert array_identity(loaded['cisd'])['sha256']==array_identity(d['system']['states']['cisd'])['sha256']
        assert loaded['metadata']['group_sha256']==d['metadata']['group_sha256']
        oldK=spec['K']; counts=loaded['metadata']['term_counts']
        steps=list(ns['iter_s2_sequence_steps'](len(counts),baseline['current_m3_sequence']))
        K=sum(counts[i] for i,_ in steps)
        if K!=oldK: raise ValueError('new PF rotation count differs from frozen design K')
        if counts!=read(C0+'/source_and_backend_closure.json')['systems'][len(specs)]['term_counts']:
            raise ValueError('new term count sequence differs from design')
        registry.append(dict(condition=condition,source_kind='new regenerated follow-up source',
            private_original_path=str(source),private_original_whole_sha256=sha(raw),
            operational_archive_path=str(destination/'source.npz'),operational_archive_sha256=identity['source_archive_sha256'],
            source_identity_sha256=digest,hamiltonian_sha256=record['H_sha'],source_generation_code_revision=env['code_revision'],
            origin_result_commit=BASE,verified_snapshot_commit=BASE,binaries_public=False))
        specs.append(dict(condition=condition,dimension=1568,K=K,group_count=len(counts),
            source_identity_sha256=digest,operational_archive_sha256=identity['source_archive_sha256'],
            new_H_sha256=record['H_sha'],training_absolute=spec['historical_training_absolute'],
            M10_training_absolute=spec['historical_training_absolute'],t0=spec['t0'],t0_hex=spec['t0_hex'],
            fit_scale_t_ref=spec['t_ref'],coordinate_provenance='prior development fixed external design; not new-source optimum',
            group_applications_per_vector=len(steps),gate_materializations_per_vector=len(set(steps))))
        audits.append(dict(condition=condition,exact_C06_bytes=True,sanitized_archive_valid=True,
            H_hash_preserved=True,CISD_bytes_preserved=True,basis_bytes_preserved=True,group_order_preserved=True,
            new_K=K,design_K=oldK,rotation_contract_pass=True,
            forbidden_fields_absent=['exact_ground','overlap','gap','direct_truth','historical_truth','branch_label','safe_unsafe','C06_acceptance'],
            metadata_only_reloads=1,production_observable_calculations=0))
    write('new_source_identity.json',dict(historical_source_identity_used_as_gate=False,identities=identities))
    write('new_source_registry.json',dict(sources=registry,old_truth_and_budget_reuse=False,
        private_binary_publication=False,science_performed=False))
    write('sanitized_export_manifest.json',dict(format='FS-R0-operational-v1',sources=registry,
        arrays_manifests='new_source_identity.json',canonical_identity_rule='SHA256 of canonical per-condition identity JSON incl trailing newline',
        public_payload='hashes/dtype/shapes/provenance only; npz/private source bytes excluded'))
    write('sanitization_audit.json',dict(status='PASS',operational_export_count=2,systems=audits,
        exact_ground_used=False,source_generation_count=0,science_actions=0))
    protocol=dict(protocol_id='FS-R1-20261007-v1',series='FS-R1',stage='FS-R0 preflight',
        research_question='At identical regenerated H/PF/external coordinates, can state improvement and/or selected-time local evaluation reduce QPE budgets safely?',
        development_status='known N2/CO development conditions; no independent/prospective/transfer guarantee',
        source_kind='new regenerated follow-up source',historical_recovery_route='ended',
        historical_H_match_gate=False,historical_truth_reuse=False,historical_B0_reuse=False,
        systems=specs,current_m3_sequence=baseline['current_m3_sequence'],
        arms={'M00p':'new CISD 3-point fit at t0; generates NEW B0_prime',
              'M10p':'new Ritz8 same 3 absolute points and fit',
              'M01p':'new CISD local g(t0), no fit','M11p':'same new Ritz8 local g(t0), no fit; primary'},
        primary='M11p',challenger='M01p',historical_training_relative=[0.1,0.2,0.3],
        sentinel_in_fit=False,relative_0_4_role='none',fit=baseline['fit'],
        constants=dict(epsilon_E=0.00015936001019904,beta=1.2,gamma=1.01,eta=0.02),
        B0_prime_definition='gamma beta K/[t0(epsilon_E-|new M00p(t0)|)]',
        arm_budget_definition='same formula with each arm magnitude; c>=epsilon => infeasible/null; no clipping',
        safety_definition='epsilon_E-|new direct(t0)|-beta K/(t0 B_j)>=0; keep raw slack, invalid/indeterminate cannot support gain',
        ritz=dict(primary_m=8,MGS_passes=2,prefix_rank_stop=True,replacement_direction=False,
                  phase_rule='largest magnitude component positive; first tie index',projected_max_dimension=9,
                  numeric_rules_source='artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json',
                  full_ground_input=False,rank_sweep=False),
        cold_replay='one complete independent source/basis/state/PF/echo/proxy/fit/budget replay; no scientific intermediates shared',
        phase_A='new sanitized source only; freeze all estimates/budgets/code/protocol/source hashes in committed prediction; truth unopened',
        phase_B='verify actual Phase A commit/blobs and independent remote receipt first; then only two new source truth points',
        truth_contract=dict(targets=[{'condition':s['condition'],'time':s['t0'],'source_identity_sha256':s['source_identity_sha256']} for s in specs],
            new_direct_truth_coordinates=2,branch_ids='FS-R1:<new source identity SHA>:<new branch id>; historical6/9 forbidden',
            branch_continuation_closed=False,blocker='NEW_SOURCE_CONTINUATION_ANCHOR_UNAVAILABLE',
            prior_algorithm='S0 v1.1 needs nearest lower same-source reliable continuous branch anchor',
            historical_anchor_reuse=False,extra_truth_coordinates_authorized=False,
            unitarity_gate=1e-10,eigenpair_residual_gate=1e-10,nearest_time_substitution=False),
        outcome_rules={'primary_gain':'valid safe M11p B11<=0.98 B0_prime','local_gain':'valid safe M01p B01<=0.98 B0_prime',
            'state_increment':'safe M01p/M11p B11<=0.98 B01','safety_repair':'valid unsafe M01p and safe M11p, separate from saving'},
        study_interpretation={'2/2':'small development support','1/2':'condition-dependent','0/2':'no resource-stage support','unsafe_offset_by_average':False},
        stop_rules=['M11p unsafe either condition: resource extension STOP','both safe but target not met: stop micro-accuracy optimization',
            'M01p sufficient and no state_increment: simpler local intervention preferred','state_increment2/2: consider refinement extension',
            'state_increment1/2: keep condition dependence; no molecules until success','technical failure separate from science',
            'R0 stops after handoff regardless GO; separate R1 authorization required'],
        cost_units={'classical':'source/H/Ritz/PF/echo/groups/fit actions, wall seconds/RSS bytes','QPE':'predicted PF rotations'},
        FS_R1_science_authorized=False,execution_ready=False,
        approved_status_amendment='branch_continuation_amendment.md',
        final_preflight_status='NO_GO_BRANCH_CONTINUATION_UNCLOSED')
    write('fs_r1_protocol.json',protocol)
    write('scoring_contract.json',dict(arms=['M00p','M10p','M01p','M11p'],primary='M11p',challenger='M01p',
        constants=protocol['constants'],B0_prime_definition=protocol['B0_prime_definition'],
        safety=protocol['safety_definition'],outcomes=protocol['outcome_rules'],
        all_conditions=True,no_posthoc_arm_selection=True,old_B0_allowed=False,
        branch_numerical_gates=protocol['truth_contract'],schema_status='scalar functions complete; physical truth continuation pending'))
    plan=dict(planned_only=True,conditions=2,passes=2,state_coordinates_per_condition_pass=8,
        proxy_evaluations=32,PF_forward_vector_actions=32,logical_exact_H_echo=32,PF_adjoint=0,
        explicit_Ritz_H_matvec_nominal=36,explicit_Ritz_H_matvec_rank_stop='sum(1+k), k<=8 over 4 refinement passes',
        small_Ritz_solve_nominal=4,small_Ritz_solve_rank_zero='0 when rank=0; original CISD reused',
        scalar_fits=8,initial_operational_fits=4,cold_validation_fits=4,
        truth_coordinates=2,new_direct_truth_executed=0,actual_FS_R1_actions=0,block_action_schedule='single vector; block calls0',
        planned_phase_A_group_application=sum(16*s['group_applications_per_vector'] for s in specs),
        planned_phase_A_group_materialization=sum(16*s['gate_materializations_per_vector'] for s in specs))
    write('predicted_action_budget.json',plan)
    write('cost_contract.json',dict(mandatory=['source_load','explicit H matvec','small Ritz solve','PF forward vector',
        'logical exact-H echo','group application','group materialization','scalar fit','wall_seconds','peak_RSS_bytes','threads/software'],
        units=protocol['cost_units'],mixed_unit_single_scalar=None,
        expm_internal=dict(matvec=None,matmat=None,rmatvec=None,norm_estimation=None),internal_count_status='unknown, not zero',
        views=['joint acquisition','initial operational','cold validation','incremental over available baseline','inherited source generation'],
        incremental={'M01p':{'PF_forward':1,'echo':1},'M11p':{'explicit_H':'1+k','small_Ritz':'1 if k>0 else 0','PF_forward':1,'echo':1}},
        measured_FS_R1_costs=None,nominal=plan,source_regeneration_count_in_R0=0))
    write('research_pivot.md','# Approved research pivot\n\n2026-10-07 JSTユーザー/GPT指示に従い、historical H01復元路線を終了。探索・SHAへ合わせる再構成・parameter tuningは続けない。C0.6の一度だけ生成したexact binaryをnew regenerated follow-up sourceとして凍結した。historical source recovered/functionally equivalentとは呼ばない。両条件を固定し、旧formal/Phase0/H4/C0/C0.5/C0.6は保存する。\n\n新しいseriesはFS-R0 preflight → 別承認後FS-R1 prediction/new truth。historical B0/direct truth/branchIDはnew scienceに転用しない。新B0_primeを新M00pから生成する。new sourceの差をmethod improvementとして解釈しない。\n')
    write('historical_vs_new_source_scope.md','# Historical vs new source\n\n旧結果はmotivation/design history/prior headroomのみ。原H01 pickleはmissing、旧H SHAと新SHAは異なる。FS-R0では旧H一致をgateにせず、prediction/truth両phaseが同じnew source identityを使うことをgateにする。保存時刻はprior developmentから固定されたexternal design coordinatesで、新sourceの最適時刻ではない。旧B0・direct値とnewB0_prime・truth_prime・saving_primeを同一分母に混ぜない。N2/COは既知development条件。独立/prospective validationやtransfer guaranteeを主張しない。\n')
    lines=['|condition|M00p=M10p training absolute|fixed t0|K|','|---|---|---|---|']
    for s in specs:lines.append(f"|{s['condition']}|{s['training_absolute']}|{s['t0']}|{s['K']}|")
    write('four_arm_contract.md','# New-source four arms\n\n'+ '\n'.join(lines)+'\n\nM00p/M10pは元H01のt/t_ref・y/max_abs scaling、[4,6] no-intercept unweighted OLS。t_refも固定numerical scaling constantで、Ritzによる再推定をしない。M01p/M11pはlocal g(t0)のみでfitしない。M11p primary/M01p cheaper challenger。B0_primeは新M00pから計算し、historical保存B0を参照しない。c>=epsilonはinfeasible。\n')
    write('fs_r1_protocol.md','# FS-R1-20261007-v1\n\nFS-R0で固定したnew sources・external design coordinateによるdevelopment比較。Phase Aで32 logical PF/echo評価（initial16+cold16）、rank8ならexplicit H36/small Ritz4、new fits8。Phase Aをcommit/hash/remote freeze後、Phase Bでnewtruth2pointsのみ。R0ではこれらを実行していない。\n\n'+ '\n'.join(lines)+'\n\n新truthの物理branch continuationは未成立。同じnew sourceのlower-time anchorがなく、旧S0のhistorical anchorを再利用できない。t0だけの最大ground overlapへselection ruleを独自変更しない。追加truth座標も未承認。契約が閉じるまではNO_GO_PROTOCOL_OR_BACKEND。全4arm基準・study interpretation・停止条件はJSONがnormative。\n')
    write('truth_generation_contract.md','# New truth contract — continuation unresolved\n\n同じnew regenerated H/sector/ordered groups/current_m3/removed-constant originと同じt0でnew direct deltaを作る。必要targetはN2 t0、CO t0の計2。new branchはsource SHAでnamespaced identityを割り当て、旧ID6/9を流用しない。eigenpair residual/||U†U-I||Fとも1e-10、phase cluster1e-8、previous-overlap warning0.9をS0から継承し、missing/duplicate/nearest-time/old provenanceを拒否する。旧truth値を返すfallbackは存在しない。\n\nS0 v1.1のphysical continuous branchは同一sourceのlower reliable anchorを必要とする。新sourceにはまだanchorがなく、2target上限の下でlower-time branch計算を追加できない。t0の最大ground overlapだけへ置換することは未承認。branch continuation contractは未確立としてfail closed。truth_only.pyはSchur stepとbarrierだけを準備し、production sourceのbranch solve/eigensolve/PFは一切呼ばない。GPT/userの決定が必要。\n')
    write('truth_barrier.md','# Phase A/B barrier\n\nPhase Bは40文字Phase A commit・prediction/protocol/source identity/code各SHA・manifest SHA・independent remote verification receiptを要求。git showのactual committed bytesとlocal bytesを比較し、receiptにも同じcommit/manifest/files hashesを照合してからtruth callbackへ進む。receiptはindependent bare remote fetch/hash後にのみ生成する。field1個でも不一致ならtruthは開かない。R0 Contextはproduction actionを拒否し、synthetic modeは16次元以下。将来も別のscience authorizationをprotocol hashにbindする。\n\n原C0.6 binary中のexact groundはtruth-only moduleの後段だけで許可する。operational archiveには存在しない。branch contract未確立のため、この版ではtruth dispatchをさらに停止する。\n')
    write('cold_replay_contract.md','# Complete cold replay\n\n将来のPhase Aは各passでarchiveの検証/loadからRitz basis/state、PF gate caches、exact-H echo、proxy、fit、budgetまで独立に再構築。immutable source bytesのみ再利用可能。cached state/HZ/expm/gate/proxy/fitは共有しない。initial/cold各16 evaluations、fits各4を別カテゴリで記録。rank0ならRitz=CISD、small solve0、実際のH1+retained rankを数える。各pass scalar return後の回復snapshotは別create-only file。R0ではsynthetic冷再構築だけを試験する。\n')
    write('recovery_contract.md','# Durable scalar recovery\n\n各pass return → private scalar recovery/fsync/hash/create-only → public schema validation/write/roundtrip → Git prediction freeze。検証済みC0 serialization_boundaryを変更せず利用。array/vector/complex/nonfinite/truthをPhase A公開から拒否し、tuple/numpy scalarだけを正規化する。public failure後はprivate bytesからserializationのみ回復し、scienceを自動rerunしない。回復自体のfailureはincidentとして停止。R0はsynthetic試験だけ。\n')
    write('truth_access_audit.json',dict(FS_R1_science_action_count=0,new_direct_truth=0,new_branch_solves=0,
        production_H_matvec=0,Ritz_build=0,PF_echo_science=0,science_fits=0,budget_outcomes=0,
        identity_only_original_decodes=2,operational_metadata_only_loads=2,
        initial_availability_inspection_decodes=2,source_regeneration=0,historical_searches=0,
        exact_ground_used_by_operational=False,new_truth_files_opened=False,
        allowed_read_scope='C0.6 exact binary identity/export and authority code/metadata only',
        raw_historical_truth_loaded=False,private_binaries_published=False))
    write('GO_NO_GO_FOR_FS_R1.json',dict(status='NO_GO_BRANCH_CONTINUATION_UNCLOSED',
        original_status_category='NO_GO_PROTOCOL_OR_BACKEND',status_amendment='explicit user/GPT followup 2026-10-07',
        reason='NEW_SOURCE_BRANCH_CONTINUATION_CONTRACT_UNCLOSED',source_bytes_available=True,
        both_source_identities_frozen=True,sanitized_exports_valid=True,four_arm_protocol_complete=True,
        native_vector_adapter_implemented=True,truth_generation_contract_complete=False,
        Phase_A_B_barrier_implemented=True,recovery_implemented=True,cost_accounting_implemented=True,
        FS_R1_science_action_count=0,new_direct_truth=0,FS_R1_science_authorized=False,
        stop='finish R0 handoff; no R1/no new source/no extra truth coordinates'))
    # Read/hash provenance. No raw truth tables included as new science inputs.
    wanted=[C06+'/'+n for n in ('README.md','GO_NO_GO_FOR_FS_C1.json','reconstruction_audit.json','cost_ledger.json',
        'validation_contract.json','source_manifest.json','reconstruct_once.py')]
    wanted += [C05+'/'+n for n in ('baseline_contract.json','native_source_pins.json','closure_adapter.py')]
    wanted += [C0+'/serialization_boundary.py','artifacts/pf_first_study_response_pilot_phase05_20261006/phase05_math.py',
        'artifacts/pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json',
        'src/trotterlib/component_sector_pf.py','src/trotterlib/pf_decomposition.py',
        'review_response/run_h01_approximate_state_calibration.py','review_response/run_pf_first_study_s0_exact_time_scoring_v1_1.py',
        'review_response/_pf_first_study_s0_exact_time_scoring_base.py','AGENTS.md']
    records=[]
    for p in wanted:
        data=(ROOT/p).read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
        origin=BASE if p.startswith(C06+'/') else subprocess.check_output(['git','log','-1','--format=%H',BASE,'--',p],cwd=ROOT,text=True).strip()
        records.append(dict(path=p,sha256=sha(data),bytes=len(data),origin_result_commit=origin,
            verified_snapshot_commit=BASE,git_blob_sha=subprocess.check_output(['git','rev-parse',BASE+':'+p],cwd=ROOT,text=True).strip(),
            snapshot_url=URL+'/blob/'+BASE+'/'+p))
    write('source_manifest.json',dict(repository=URL.removeprefix('https://github.com/'),sources=records,
        private_validation_source_origin=BASE,origin_and_snapshot_roles_separate=True,
        request_sha256=sha(request),request_origin_commit=None,request_first_publication='R0 final handoff commit'))
    print(json.dumps(dict(source_exports=2,canonical_identities=2,science=0,truth=0,status='NO_GO_BRANCH_CONTINUATION_UNCLOSED')))

if __name__=='__main__':main()
