"""Create-only FS-C0 audit builder; stdlib, fixed saved scalars/metadata only.

Never imports a production science runner or opens pickle/NPZ/array payloads.
Run with the approved base checkout and a new staging directory.
"""
import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASE = '5b370ec22f7ffeac687ef70e1bcb87337f5fb976'
REPO = 'HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'
INTEGRATION = '0a18168ae56852d7c754c28d05d5ce21bbce5b06'
H4 = 'artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64'
P0 = 'artifacts/pf_first_study_phase0_feasibility_20261006'
P05 = 'artifacts/pf_first_study_response_pilot_phase05_20261006'
P06 = 'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
COMP = 'artifacts/pf_first_study_completion_analysis_20260926_940ee7f'
PRACT = 'artifacts/server_practical_calibration_minimal_20260923_79035cc'
H01 = 'artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8'
S0 = 'artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201'
CONDITIONS = ['N2_active_eq_sto3g','CO_active_eq_sto3g']

def canonical(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def write(path, value):
    data = value.encode() if isinstance(value, str) else canonical(value)
    with path.open('xb') as f:
        f.write(data)

def write_csv(path, rows):
    with path.open('x', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)

class Audit:
    def __init__(self, root):
        self.root=root; self.records={}
    def read(self, path, purpose='fixed evidence', snapshot=BASE, origin=None):
        if Path(path).suffix.lower() in ('.pkl','.pickle','.npz','.npy'):
            raise RuntimeError('no production array/archive access')
        data=(self.root/path).read_bytes()
        gitdata=subprocess.run(['git','show',snapshot+':'+path],cwd=self.root,check=True,capture_output=True).stdout
        assert data==gitdata, ('dirty/incorrect source',path)
        blob=subprocess.run(['git','rev-parse',snapshot+':'+path],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
        version=subprocess.run(['git','log','-1','--format=%H',snapshot,'--',path],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
        origins={S0:'cc3626a8135b647fe283fc60c963de70c5f6b2a5',
                 PRACT:'4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a',
                 H01:'568f00249abb5b89ae3e6bb39cb4af87ed8581bd',
                 COMP:'6a1e54d5e830a20b8817791f9f1f65729815fc12',
                 H4:BASE,P0:'1b7b2fc959185ca1be06581682a67d28e02db21c',
                 P05:'48f3d889d096f2fe3af55c200a757747df384941',
                 P06:'6fae17723f888a62a998f90436516785a67651c6'}
        if origin is None:
            origin=next((c for prefix,c in origins.items() if path.startswith(prefix+'/')),version)
        originbytes=subprocess.run(['git','show',origin+':'+path],cwd=self.root,check=True,capture_output=True).stdout
        assert originbytes==data, ('origin/snapshot byte mismatch',path)
        self.records[path]=dict(path=path,origin_result_commit=origin,
            origin_role='result_publication' if path.startswith('artifacts/') else 'document_or_code_version',
            last_content_version_commit=version,verified_snapshot_commit=snapshot,
            git_blob_sha=blob,sha256=sha(data),bytes=len(data),purpose=purpose,
            evaluation_type='previously observed development evidence; no independent holdout',
            origin_matches_snapshot=True,
            origin_github_url=f'https://github.com/{REPO}/blob/{origin}/{path}',
            snapshot_github_url=f'https://github.com/{REPO}/blob/{snapshot}/{path}')
        return data
    def json(self,path,**kwargs): return json.loads(self.read(path,**kwargs))
    def csv(self,path,**kwargs): return list(csv.DictReader(self.read(path,**kwargs).decode().splitlines()))

def prediction_schema():
    scalar={'type':'number'}
    positive={'type':'number','exclusiveMinimum':0}
    identity={'type':'object','additionalProperties':False,
      'required':['hamiltonian_sha256','source_pickle_sha256','ordered_group_identity_sha256','sector_metadata_sha256','removed_constant_hartree'],
      'properties':{k:{'type':'string','pattern':'^[0-9a-f]{64}$'} for k in ['hamiltonian_sha256','source_pickle_sha256','ordered_group_identity_sha256','sector_metadata_sha256']}}
    identity['properties']['removed_constant_hartree']=scalar
    arm={'type':'object','additionalProperties':False,
      'required':['estimate','valid','classification_uncertainty_hartree','quality_status'],
      'properties':{'estimate':{'type':['number','null']},'valid':{'type':'boolean'},
        'classification_uncertainty_hartree':{'type':['number','null'],'minimum':0},
        'quality_status':{'enum':['resolved','marginal','unresolved','invalid','synthetic']}}}
    counts=['explicit_refinement_H_matvec','PF_forward','PF_adjoint','exact_H_echo_actions','small_Ritz','primary_fits']
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'FS-C1 public scalar prediction v1',
      'type':'object','additionalProperties':False,
      'required':['schema_version','payload_kind','protocol_sha256','conditions','action_counts'],
      'properties':{
        'schema_version':{'const':'fs_c1_prediction_v1'},
        'payload_kind':{'enum':['synthetic_fixture','fs_c1_predictions']},
        'protocol_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},
        'action_counts':{'type':'object','additionalProperties':False,'required':counts,
                         'properties':{k:{'type':'integer','minimum':0} for k in counts}},
        'conditions':{'type':'array','minItems':2,'maxItems':2,'items':{
          'type':'object','additionalProperties':False,
          'required':['condition','identity','t0','training_times','baseline_reproduced','arms'],
          'properties':{'condition':{'enum':CONDITIONS},'identity':identity,'t0':positive,
            'training_times':{'type':'array','minItems':3,'maxItems':5,'uniqueItems':True,'items':positive},
            'baseline_reproduced':{'type':'boolean'},
            'arms':{'type':'object','additionalProperties':False,'required':['M00','M10','M01','M11'],
                    'properties':{k:arm for k in ['M00','M10','M01','M11']}}}}}}
      }

def build(root, output, inputs, amendment):
    output.mkdir(parents=True,exist_ok=False)
    a=Audit(root)
    # Required reading order, and hashes of each unchanged authority.
    required=[('PF_first_study_paper_claim_ledger_20260926.md',None),
      (COMP+'/report.md',None),(COMP+'/decision_trace.csv',None),(COMP+'/calibration_precision.csv',None),
      (COMP+'/cost_factor_decomposition.csv',None),(P0+'/README.md',None),(P0+'/report.md',None),
      (P0+'/resource_headroom.csv',None),(H4+'/README.md',None),(H4+'/scientific_outcome.json',None),
      (H4+'/report.md',None),(H4+'/evaluation_scoring.csv',None),(P05+'/algorithm_design.md',None),
      (P05+'/response_pilot_protocol.json',None),('docs/second_study_v2/evidence_integration_20261006/evidence_map.md',INTEGRATION)]
    for path,snapshot in required: a.read(path,snapshot=snapshot or BASE,purpose='requested authority reading order')
    for path in [P0+'/source_registry.json',COMP+'/source_manifest.json',PRACT+'/protocol.json',
      PRACT+'/sanitized_input_manifest.json',PRACT+'/predictions.json',PRACT+'/proxy_points.csv',PRACT+'/audit.json',
      S0+'/source_manifest.json',S0+'/scoring.csv',S0+'/branch_audit.csv',S0+'/audit.json',S0+'/s0_anchor_protocol.json',
      'review_response/practical_calibration_minimal_protocol.json','review_response/h01_approximate_state_calibration_protocol.json',
      'review_response/run_practical_calibration_minimal.py','review_response/run_h01_approximate_state_calibration.py',
      'src/trotterlib/component_sector_pf.py','src/trotterlib/pf_decomposition.py',P06+'/phase06_kernels.py',P05+'/phase05_math.py']:
        a.read(path,purpose='source/fit/backend/truth provenance closure')
    pred=a.json(PRACT+'/predictions.json'); practical_protocol=a.json(PRACT+'/protocol.json')
    saved_proxies=a.csv(PRACT+'/proxy_points.csv'); heads=a.csv(P0+'/resource_headroom.csv')
    traces=a.csv(COMP+'/decision_trace.csv'); s0scores=a.csv(S0+'/scoring.csv'); branch=a.csv(S0+'/branch_audit.csv')
    s0sources=a.json(S0+'/source_manifest.json'); sanitized=a.json(PRACT+'/sanitized_input_manifest.json')
    instructions=(inputs/'Codex_FS_C0_instructions.md').read_bytes()
    design=json.loads((inputs/'FS_C0_design_summary.json').read_bytes())
    assert design['science_authorized'] is False and design['base_evidence_commit']==BASE
    systems=[]; closure=[]; blockers=[]; fixtures=[]
    requested=[.1,.2,.3,.4,.5]
    for condition in CONDITIONS:
        pm=next(x for x in pred['conditions'] if x['condition']==condition)
        pf=next(x for x in pm['pf_predictions'] if x['formula']=='current_m3')
        sm=a.json(f'{H01}/cache/{condition}.metadata.json')['system']
        cache=next(x for x in s0sources['h01_cache_records'] if x['condition']==condition)
        clean=next(x for x in sanitized['entries'] if x['condition']==condition)
        assert sm['hamiltonian_sha256']==cache['hamiltonian_sha256']==clean['hamiltonian_sha256']
        assert cache['pickle_sha256']==clean['source_pickle_sha256']==practical_protocol['source_identity']['pickle_sha256'][condition]
        assert a.records[f'{H01}/cache/{condition}.metadata.json']['sha256']==cache['metadata_sha256']
        assert all(cache['checks'].values())
        t0=pm['selection']['selected_time']; tref=pf['proxy_analytic_time']; K=pf['rotations']
        head=next(x for x in heads if x['condition']==condition)
        trace=next(x for x in traces if x['condition']==condition and x['formula']=='current_m3')
        score=next(x for x in s0scores if x['condition']==condition)
        assert t0==float(head['selected_time'])==float(trace['condition_selected_time'])==float(score['selected_time'])
        assert K==int(head['rotations_K_P'])==int(trace['rotations'])
        B0=float(score['frozen_budget_gamma_1_01']); assert B0==float(head['B0_frozen'])
        truthrows=[x for x in branch if x['condition']==condition and x['formula']=='current_m3' and float(x['time']).hex()==float(t0).hex()]
        assert len(truthrows)==1
        tr=truthrows[0]; assert tr['branch_quality']=='resolved' and tr['point_role']=='inserted_exact_time_triplet' and float(tr['time_factor'])==1
        assert float(tr['eigenpair_residual_2_norm'])<=1e-10 and float(tr['unitarity_residual_frobenius'])<=1e-10
        assert float(tr['signed_direct_shift_hartree'])==float(score['exact_time_direct_signed_shift_hartree'])
        training=[x for x in saved_proxies if x['condition']==condition and x['formula']=='current_m3' and x['point_role']=='model_training']
        assert len(training)==3
        saved_times=[float(x['time']) for x in training]
        requested_matches=[]
        for rel in requested:
            matches=[x for x in saved_proxies if x['condition']==condition and x['formula']=='current_m3' and float(x['time']).hex()==float(rel*tref).hex()]
            requested_matches.append(dict(relative=rel,expected_time_hex=float(rel*tref).hex(),saved_exact_match_count=len(matches),roles=[x['point_role'] for x in matches]))
        sector={k:sm[k] for k in ['geometry_angstrom','basis','charge','multiplicity','total_spatial_orbitals',
          'total_electron_count','active_electron_count','frozen_core_spatial_orbitals','active_spatial_orbitals',
          'n_alpha','n_beta','population_sector_dimension','restricted_dimension','z2_mask','z2_target']}
        sector['orbital_mapping']='original H01 sorted population basis, restricted Z2, reversed PySCF bits up-then-down JW; no regeneration'
        identity=dict(hamiltonian_sha256=sm['hamiltonian_sha256'],source_pickle_sha256=cache['pickle_sha256'],
            ordered_group_identity_sha256=sha(canonical(sm['group_sha256'])),sector_metadata_sha256=sha(canonical(sector)),
            removed_constant_hartree=sm['removed_constant_hartree'])
        spec=dict(condition=condition,formula='current_m3',K=K,t_ref=tref,t0=t0,t0_hex=float(t0).hex(),
          B0=B0,historical_signed_prediction=pm['selection']['predicted_signed_shift_hartree'],
          historical_coefficients=pf['model']['coefficient_values'],historical_training_times=saved_times,
          historical_training_time_hex=[t.hex() for t in saved_times],
          requested_training_relative=requested,training_times=saved_times if amendment=='original_three' else None,
          training_time_status='user_amended_original_three' if amendment=='original_three' else 'blocked_requested_five_not_historical',
          identity=identity,truth_branch_id=int(tr['selected_eigenbranch_id']),
          allowed_time_cap=float(head['allowed_time_cap_T']))
        systems.append(spec)
        candidates=[root/H01/'cache'/f'{condition}.pkl',root/PRACT/'.runtime/sanitized'/f'{condition}.pkl',
          Path('/home/abe/myproject/Evaluation_numGate_highorder')/H01/'cache'/f'{condition}.pkl']
        private_available=any(p.is_file() for p in candidates)
        # Never decode even if such a path becomes available during C0.
        issue=[dict(id='PRIVATE_SOURCE_UNAVAILABLE',condition=condition,
          detail='Historical pickle hashes are attested; original H01/sanitized runtime caches absent in audited local locations. Need identity-only extraction of H, ordered group spectra, CISD and basis; no molecule/state regeneration.'),
          dict(id='ARRAY_IDENTITIES_UNCLOSED',condition=condition,
          detail='No standalone CISD/basis/component-spectrum canonical array hashes in public metadata. Historical whole-cache digest is not a verified present array export.'),
          dict(id='NATIVE_NUMERICAL_COST_CONTRACT_UNCLOSED',condition=condition,
          detail='PF function accepts arbitrary vector, but expm_multiply internal H work, echo uncertainty/norm precision and memory/wall caps for Ritz input are not closed by existing metadata alone. No backend substitution.')]
        if amendment!='original_three': issue.insert(0,dict(id='TRAINING_BASELINE_CONFLICT',condition=condition,
            detail='Requested original five [0.1,0.2,0.3,0.4,0.5] are historical three fit points plus a sentinel at0.5;0.4 absent. New five-point fit cannot be called original M00/B0.'))
        blockers.extend(issue)
        closure.append(dict(condition=condition,identity=identity,sector=sector,ordered_group_sha256=sm['group_sha256'],
          group_count=sm['group_count'],term_counts=sm['term_counts'],
          component_representation=sm['component_representation'],
          dimension=sm['restricted_dimension'],original_cache_sha256=cache['pickle_sha256'],
          sanitized_cache_sha256=clean['sanitized_sha256'],
          original_array_export_verified=False,private_cache_available=private_available,
          cache_presence_checks=[dict(path=str(p),exists=p.is_file(),decoded=False) for p in candidates],
          historical_metadata_and_cache_attestation_consistent=True,
          standalone_CISD_array_sha256=None,restricted_basis_array_sha256=None,component_spectrum_array_sha256=None,
          exact_t0_truth_join=True,truth_branch_id=int(tr['selected_eigenbranch_id']),
          truth_time_hex=float(tr['time']).hex(),truth_quality=tr['branch_quality'],
          truth_source_path=S0+'/branch_audit.csv',truth_origin_result_commit=a.records[S0+'/branch_audit.csv']['origin_result_commit'],
          truth_eigenpair_residual=float(tr['eigenpair_residual_2_norm']),truth_unitarity_residual=float(tr['unitarity_residual_frobenius']),
          saved_training_time_hex=[t.hex() for t in saved_times],requested_coordinate_audit=requested_matches,
          preprocessing_group_eigensystems='existing small connected-component spectra; rebuilding whole H01 prepare_condition is prohibited: contains full ground solve and state construction',
          unresolved_issues=issue))
        fixtures.append(dict(condition=condition,identity=identity,t0=t0,training_times=saved_times))
    pf_source=(root/'review_response/run_h01_approximate_state_calibration.py').read_text()
    parsed=ast.parse(pf_source)
    pf_def=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='_apply_pf_cpu')
    assert [x.arg for x in pf_def.args.args]==['system','sequence','time_value','states']
    write(output/'backend_review.md',f'''# Native backend inspection (no production calls)

`review_response/run_h01_approximate_state_calibration.py:_apply_pf_cpu` lines {pf_def.lineno}–{pf_def.end_lineno} takes `states` explicitly; its sparse group-gate product supports any compatible vector or column block. It uses the original ordered compact group eigensystems and merged `iter_s2_sequence_steps`, complex128, left multiplications, per-call sparse gate cache. No final dense full-PF matrix is required for this action.

`component_exponential` materializes small-component spectral exponentials as CSR. Fresh preprocessing uses component eigensolves (maximum saved block sizes N2 32 / CO 64); their costs and array identities must be audited separately. H01 `prepare_condition` also performs full-ground diagonalization and CISD construction: **do not use it to restore missing runtime inputs**.

H01 `_echo_points` explicitly computes expm_multiply(-i*t*H, U*state). Practical `proxy_point` computes <exp(+i*t*H)state|U*state>; algebraically the same imaginary echo with an arbitrary state substituted, but its current function hardcodes `system['cisd_state']`. An adapter would have to take an explicit state and preserve signed convention. No such production adapter is executed or declared ready by FS-C0.

SciPy CSR `expm_multiply` internal H matvecs/norm estimation are not exposed by these old counters. Saved exact-H action seconds are not a count of H matvecs. A future instrumented compatible wrapper or explicit unknown status and accepted cost contract is necessary. Error/uncertainty for arbitrary Ritz input and memory/wall caps remain unresolved. Historical H01/P03 spectral preprocessing is counted as inherited or cold preparation, never free total work.

Metadata-only inspection verifies 1568-dimensional sources, N2 81 groups / CO 99 groups, H/cache digests, fixed sector and energy origin. This does **not** verify currently missing production arrays. Runtime/backend readiness is false.
''')
    protocol=dict(protocol_id='FS-C1-20261007-v1',stage='FS-C0 design snapshot',
      research_direction='decision-relevant calibration intervention',base_evidence_commit=BASE,
      science_authorized=False,execution_ready=False,development_informed=True,independent_holdout=False,
      constants=dict(epsilon_E=.00015936001019904,beta=1.2,gamma=1.01,eta_saving=.02),
      arms=dict(M00='CISD fixed-time fit',M10='Ritz8 same-time fit',M01='CISD local imag echo',M11='Ritz8 local imag echo'),
      primary='M11',cheaper_challenger='M01',systems=systems,
      fit=dict(powers=[4,6],intercept=False,weighting='unweighted OLS',new_design_scaling='column 2-norm scaling',
        original_baseline_scaling='relative t/t_ref and response/max_abs scale, original numerical solver; no production refit in C0',
        original_three_only=amendment=='original_three',historical_M00_reproduction_gate='identity and exact saved times; source numerical error bound needed; no newly invented tolerance'),
      ritz=dict(m=8,max_projected_dimension=9,MGS_passes=2,rank_and_tie_rules_source=P05+'/response_pilot_protocol.json',
        rank_breakdown='keep first retained prefix, no rescue; H matvec counts at actual retained rank',
        source_numeric_rules_immutable=True,new_rank_measurements=False),
      gates=dict(baseline_reproduction_bound_hartree=None,echo_numeric_uncertainty_contract=None,
        primary_gain='valid M11 and safe M11 and B11 <=0.98 B0',
        local_gain='valid M01 and safe M01 and B01 <=0.98 B0',
        state_increment='safe M01 and safe M11 and B11 <=0.98 B01',
        safety_repair='valid numerically identified unsafe M01 and safe M11; separate from saving',
        safety='epsilon-e-beta*K/(t*B)>=0; raw slack retained; indeterminate boundary is not a certificate'),
      truth_barrier=dict(all_four_arms_before_truth=True,prediction_protocol_code_source_manifest_commit_SHA_checked=True,
        source=S0+'/branch_audit.csv',source_sha256=a.records[S0+'/branch_audit.csv']['sha256'],
        join='exact binary64 positive t0, condition/PF/H/cache/sector/order/origin plus per-condition saved branch ID',
        production_truth_targets=2,new_truth=0,nearest_time=False,new_exact_proxy=False),
      cold_replay='one full independent basis/state/PF/echo replay; no cache shared across passes; four operational fits only after replay acceptance',
      reporting='each condition separately; no unsafe offset by mean, no post-hoc best arm',
      stop='C0 normal commit/push independent blob verification then stop; C1 requires explicit science authorization and all closures',
      unresolved_issues=blockers,authorization_amendment=amendment)
    write(output/'fs_c1_protocol.json',protocol)
    write(output/'prediction_schema.json',prediction_schema())
    write(output/'source_and_backend_closure.json',dict(source_closure=False,backend_ready=False,
      historical_identity_attestation_consistent=True,truth_join_ready=True,
      array_decodes=0,production_actions=0,systems=closure,unresolved_issues=blockers))
    write(output/'metadata_fixture.json',dict(kind='metadata only, no production prediction',conditions=fixtures))
    # Same saved H4 coordinates, primary arms only; no fit, no new operational budget.
    evalrows=a.csv(H4+'/evaluation_scoring.csv')
    bykey={(x['arm'],float(x['time']),int(x['sign'])):x for x in evalrows}
    post=[]; eps=protocol['constants']['epsilon_E']; gamma=1.01
    for t,sign in sorted({(float(x['time']),int(x['sign'])) for x in evalrows}):
        base=bykey['A0',t,sign]; c0=abs(float(base['prediction']))
        for arm in ['A0','A1','A2']:
            x=bykey[arm,t,sign]; c=abs(float(x['prediction'])); e=abs(float(x['direct_truth']))
            ratio=(eps-c0)/(eps-c); margin=(1-1/gamma)*(eps-c); u=e-c
            post.append(dict(arm=arm,time=t,sign=sign,c_A0=c0,c_method=c,e_saved=e,
              gamma=gamma,epsilon_E=eps,reference_budget_ratio=ratio,reference_saving=1-ratio,
              margin_capacity_hartree=margin,u_hartree=u,u_plus_hartree=max(0,u),
              u_over_same_coordinate_margin=u/margin,
              interpretation='posthoc_saved_scalar_same_time_same_gamma_only; not an operational budget/science success'))
    write_csv(output/'H4_posthoc_decision_scale.csv',post)
    headrows=[]
    for x in heads:
        if x['condition'] not in CONDITIONS+['HF_full_eq_sto3g','HF_full_stretch150_sto3g']:continue
        K=int(x['rotations_K_P']);T=float(x['allowed_time_cap_T']);B0=float(x['B0_frozen'])
        bound=1-1.2*K/(T*eps*B0)
        headrows.append(dict(condition=x['condition'],domain_saving_upper_bound=bound,exclude_eta_2pct=bound<.02,
          same_time_margin_removed_oracle_headroom=float(x['same_time_calibration_headroom']),
          same_time_fixed_gamma_perfect_prediction_saving=float(x['same_time_perfect_prediction_fixed_gamma_saving']),
          selected_time=float(x['selected_time']),T=T,K=K,B0=B0,
          distinction='domain truth-free lower bound vs saved-truth same-time oracle; no operational intervention attained'))
    write_csv(output/'headroom_reference.csv',headrows)
    times=4 if amendment=='original_three' else 6
    counts=dict(explicit_refinement_H_matvec=36,PF_forward=2*2*times*2,PF_adjoint=0,
      exact_H_echo_actions=2*2*times*2,small_Ritz=4,primary_fits=4,
      new_direct_truth=0,new_full_H_ground_eigh_Schur=0,response_solve=0)
    write(output/'predicted_action_budget.json',dict(planned_only=True,science_authorized=False,
      intended_original_five_nominal=design['C1']['nominal_logical_counts_two_systems_two_passes'],
      effective_nominal=counts,positive_times_per_system=times,
      training_policy_resolved=amendment=='original_three',joint_systems=2,complete_passes=2,calibration_states=2,
      standalone_incremental_per_system_single_pass=dict(M01=dict(PF_forward=1,exact_H_echo_actions=1),
        M11=dict(explicit_refinement_H_matvec=9,small_Ritz=1,PF_forward=1,exact_H_echo_actions=1)),
      costs_excluded_from_logical_counts=['internal H-exponential matvec/matmat/rmatvec','norm/trace estimation',
        'group preprocessing/eigensystem validation','sparse gate materialization and multiplies','memory,wall,failed attempts'],
      count_on_rank_breakdown='explicit H is 1+k per state-refinement pass, k<=8; retained prefix only'))
    input_records=[]
    for name in ['FS_C0_design.md','Codex_FS_C0_instructions.md','FS_C0_design_summary.json']:
        b=(inputs/name).read_bytes()
        input_records.append(dict(path='docs/first_study/redesign_20261007/'+name,sha256=sha(b),bytes=len(b),
          origin_result_commit=None,verified_snapshot_commit=None,origin_role='user supplied uncommitted GPT design; original bytes preserved',
          original_local_path='/home/abe/myproject/Evaluation_numGate_highorder/.worktrees/pf-first-study-response-pilot-h4-phase-b-20261006/docs/first_study/'+name))
    registry=dict(repository=REPO,base_evidence_commit=BASE,identity_roles_separate=True,
      inputs=input_records,sources=list(a.records.values()),old_results_modified=False,
      populations=dict(formal_cases=128,pooled_H4_fit_ok_resolved_rows=588,
        H4_current_m3_CISD_primary_eval_coordinates=12,new_C1_development_conditions=2,
        policy='do not pool independent N; second-study integration supplies design limits, not first-study added successes'),
      source_runtime_generation=dict(H01_generation_commit='e0692a83b06cd2660804f70618b142bc39b6209b',H01_dirty=True,
        original_selector_execution_commit='79035cc7c414c04cafe8b9f8bdc779a17ec57302',
        S0_execution_commit='3279201bd046d63cad18c1f4964fa026599137a2'))
    write(output/'evidence_registry.json',registry)
    write(output/'source_manifest.json',dict(repository=REPO,sources=registry['sources'],inputs=input_records,
      verified_snapshot_commit=BASE,content_role_policy='origin/result distinct from verified snapshot; private cache digests attested not array exports'))
    write(output/'GO_NO_GO_FOR_FS_C1.json',dict(status='NO_GO_FOR_FS_C1',C0_documentation_audit_complete=True,
      design_complete=False,source_closure=False,backend_ready=False,truth_join_ready=True,
      test_status='pending',science_authorized=False,execution_ready=False,
      training_policy_resolved=amendment=='original_three',unresolved_issues=blockers,
      remaining_design_requirements=['source-backed M00 reproduction/error tolerance','native echo precision and complete backend ledger/resource caps'],
      no_go_is_science_failure=False,stop='FS-C0 only; do not restore missing arrays by regeneration or launch FS-C1'))
    write(output/'action_counts.json',dict(production_H=0,production_PF_forward=0,production_PF_adjoint=0,
      production_exact_H_echo=0,production_Ritz_state=0,production_fits=0,new_direct_truth=0,
      full_ground_Schur_solve=0,production_array_decodes=0,
      saved_H4_primary_evaluation_rows_reinterpreted=len(post),saved_S0_exact_truth_targets_identity_audited=2,
      historical_prediction_coefficients_read=2,synthetic_math_tests='separate from production ledger'))
    return protocol

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--amendment',choices=['pending','original_three','retain_five'],default='pending')
    x=p.parse_args();build(x.root,x.output,x.inputs,x.amendment)
