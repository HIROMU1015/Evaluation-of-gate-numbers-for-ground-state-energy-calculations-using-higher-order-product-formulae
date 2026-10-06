"""Frozen Phase A verification and saved-scalar scoring views.

No Phase A/kernel/backend computation is called. The normative Phase0.6 scorer
and saved-truth selector are reused unchanged; added functions audit identities,
predicate trace, and the 22-coordinate proxy mechanism table.
"""
from pathlib import Path
import csv,io,json,math
from contextlib import contextmanager
from phase06_contract import GateError,canonical,sha,PROTOCOL_SHA,BASE,PH05
from phase06_freeze import verify_phase_a_freeze,GitTransport
from phase06_phase_b import select_saved_truth,score_payload
from phase06_kernels import TRAIN,EVAL

A_COMMIT='53a88c28b7587ab61efb93d6ba30974c9d3d6404'
A_BRANCH='pf-first-study-response-pilot-h4-phase-a-retry2-20261006'
A_DIR='artifacts/pf_first_study_response_pilot_phase_a_h4_retry2_20261006_d6dc5674'
PRED_SHA='9ce3d4e7ec89575f1d661515cddb636fab0288c5c4149df1c85dc529adace18f'
PHASE_A_SHA='4c10e6e766319c88bf8375c6c1422a43dbb75df8becefb8a5dee4aa4e5b25eb4'
BRANCH_CSV='artifacts/pf_first_study_phase_b_20260925_5a2f0a2/branch_audit.csv'
EXACT_CSV='artifacts/pf_first_study_phase_b_20260925_5a2f0a2/observables.csv'

def frozen_receipt(root):
    payload=json.loads((Path(root)/A_DIR/'phase_a.json').read_bytes())
    return {'commit':A_COMMIT,'branch':A_BRANCH,'prediction_path':A_DIR+'/phase_a.json',
        'prediction_sha256':PHASE_A_SHA,'protocol_sha256':PROTOCOL_SHA,
        'source_sha256':payload['source']['source_sha256'],'code_sha256':payload['source']['code_sha256'],
        'publication_verified':True}

def verify_all_phase_a(root,schema,transport=None,receipt=None):
    from phase06_contract import load_contract
    transport=transport or GitTransport(root);receipt=receipt or frozen_receipt(root)
    if receipt.get('commit')!=A_COMMIT or receipt.get('branch')!=A_BRANCH or receipt.get('prediction_sha256')!=PHASE_A_SHA:
        raise GateError('FAILED_PHASE_A_FREEZE_VERIFICATION: exact frozen receipt required')
    payload,raw=verify_phase_a_freeze(root,receipt,load_contract(root),schema,transport)
    prediction=(Path(root)/A_DIR/'predictions.json').read_bytes()
    if sha(prediction)!=PRED_SHA or prediction!=transport.blob(A_COMMIT,A_DIR+'/predictions.json'):
        raise GateError('FAILED_PHASE_A_FREEZE_VERIFICATION: altered predictions.json')
    if prediction!=canonical(payload['predictions']):raise GateError('prediction projection mismatch')
    if (Path(root)/A_DIR/'prediction.sha256').read_text().strip()!=PRED_SHA:
        raise GateError('prediction hash file mismatch')
    manifest_path=A_DIR+'/publication_manifest.json'
    manifest_raw=(Path(root)/manifest_path).read_bytes()
    if manifest_raw!=transport.blob(A_COMMIT,manifest_path):raise GateError('publication manifest blob mismatch')
    checks=[]
    for record in json.loads(manifest_raw)['files']:
        if not record['path'].startswith(A_DIR+'/'):raise GateError('Phase A publication file outside fixed directory')
        content=(Path(root)/record['path']).read_bytes()
        if len(content)!=record['bytes'] or sha(content)!=record['sha256'] or content!=transport.blob(A_COMMIT,record['path']):
            raise GateError('Phase A publication blob/hash mismatch: '+record['path'])
        checks.append({'path':record['path'],'sha256':record['sha256']})
    marker=json.loads((Path(root)/A_DIR/'PHASE_A_FROZEN').read_bytes())
    if marker['numerical_status']!='PHASE_A_NUMERICALLY_READY' or marker['prediction_sha256']!=PRED_SHA or marker['strict_phase_a_sha256']!=PHASE_A_SHA:
        raise GateError('Phase A freeze marker mismatch')
    return payload,{'status':'passed','phase_a_commit':A_COMMIT,'phase_a_branch':A_BRANCH,
        'predictions_sha256':PRED_SHA,'strict_phase_a_sha256':PHASE_A_SHA,
        'protocol_sha256':PROTOCOL_SHA,'source_sha256':payload['source']['source_sha256'],
        'code_sha256':payload['source']['code_sha256'],'remote_tip_verified':True,
        'source_identity_only_reload_verified':True,'publication_blobs_verified':checks,
        'truth_opened_during_verification':False}

def guarded_intake(root,schema,reader,transport=None,receipt=None):
    payload,audit=verify_all_phase_a(root,schema,transport,receipt)
    direct,exact,truth_audit=reader()
    return payload,audit,direct,exact,truth_audit

def read_saved_truth_once(root,transport=None):
    transport=transport or GitTransport(root)
    registry=json.loads(transport.blob(BASE,PH05+'/source_manifest.json'))
    source={r['path']:r for r in registry['sources']}
    join=json.loads(transport.blob(BASE,PH05+'/saved_truth_join_contract.json'))
    if join['source']!=BRANCH_CSV:raise GateError('frozen truth join source mismatch')
    records=[];bytes_by_path={}
    for path in (BRANCH_CSV,EXACT_CSV):
        raw=(Path(root)/path).read_bytes();record=source[path]
        blob=transport.git('rev-parse',A_COMMIT+':'+path).decode().strip()
        if sha(raw)!=record['sha256'] or raw!=transport.blob(BASE,path) or blob!=record['git_blob_sha']:
            raise GateError('truth source SHA/blob identity mismatch')
        bytes_by_path[path]=raw
        records.append({**record,'verified_snapshot_commit':A_COMMIT,
            'truth_authority_snapshot_commit':BASE,'source_file_read_for_scoring_count':1})
    direct,exact=select_saved_truth(bytes_by_path[BRANCH_CSV],bytes_by_path[EXACT_CSV],join)
    allowed_quality={'resolved','marginal','unresolved'}
    if any(r['quality'] not in allowed_quality for r in exact.values()):raise GateError('saved exact proxy quality label mismatch')
    # Second text scan is provenance only: no selected/nonselected scalar value conversion.
    row_identities=[];raw_counts={}
    for path in (BRANCH_CSV,EXACT_CSV):
        count=0
        for row in csv.DictReader(io.StringIO(bytes_by_path[path].decode())):
            count+=1
            if (row['experiment_id'],row['case_id'],row['formula_id'])!=('B','H4','current_m3'):continue
            if path==BRANCH_CSV and row['grid_role']!='mechanism_fixed':continue
            if path==EXACT_CSV and row['state_id']!='exact':continue
            t=float(row['time_hartree_inverse'])
            if t not in (direct if path==BRANCH_CSV else exact):continue
            row_identities.append({'source_path':path,'experiment_id':'B','system':'H4','PF':'current_m3',
                'time':t,'sign':int(row['sign']),'absolute_time':float(row['absolute_time']),
                'branch_reliable':row.get('branch_reliable'),'selected_eigenbranch_id':row.get('selected_eigenbranch_id'),
                'proxy_quality':row.get('quality_class'),'scalar_kind':'saved_direct' if path==BRANCH_CSV else 'saved_exact_proxy'})
        raw_counts[path]=count
    if len(row_identities)!=34:raise GateError('selected truth provenance rows mismatch')
    return direct,exact,{'sources':records,'row_identities':row_identities,
        'raw_csv_rows_scanned':raw_counts,'selected_direct_distinct_coordinates':12,
        'selected_exact_proxy_distinct_coordinates':22,'scalar_decode_passes':1,
        'additional_text_scan':'Identity/provenance only; no truth-value conversion or scoring repeat.',
        'nonselected_truth_scalars_numerically_decoded':0,'new_truth_generated':0}

def pareto_trace(response_tuple,ritz_tuple):
    dominated=all(k<=r for k,r in zip(ritz_tuple,response_tuple)) and any(k<r for k,r in zip(ritz_tuple,response_tuple))
    unique=not dominated and any(r<k for r,k in zip(response_tuple,ritz_tuple))
    return {'response_tuple':list(response_tuple),'ritz_tuple':list(ritz_tuple),
        'response_Pareto_dominated_by_Ritz':dominated,'response_unique_tradeoff':unique,
        'axes':['S_abs','S_under','standalone_H_actions','standalone_PF_forward_plus_adjoint']}

def outcome_trace(payload,result):
    arms=result['arms'];b,r,k=(arms[a] for a in ('A0','A1','A2'))
    costs=payload['cost']['standalone_primary_one_pass']
    trade=pareto_trace((r['S_abs'],r['S_under'],costs['A1']['H_actions'],costs['A1']['PF_actions']),
        (k['S_abs'],k['S_under'],costs['A2']['H_actions'],costs['A2']['PF_actions']))
    valid=all(payload['fits'][a]['raw_positive_even_two_term']['status']=='fit_ok' for a in ('A0','A1','A2'))
    rb=r['S_abs']<b['S_abs'] and r['S_under']<b['S_under'];kb=k['S_abs']<b['S_abs'] and k['S_under']<b['S_under']
    point=r['point_S_abs']<b['point_S_abs'];converged=payload['residual_convergence']['converged']
    unique=trade['response_unique_tradeoff']
    predicates={'numerically_valid_primary_fits':valid,'response_S_abs_below_baseline':r['S_abs']<b['S_abs'],
        'response_S_under_below_baseline':r['S_under']<b['S_under'],
        'Ritz_S_abs_below_baseline':k['S_abs']<b['S_abs'],'Ritz_S_under_below_baseline':k['S_under']<b['S_under'],
        'response_improves_both':rb,'Ritz_improves_both':kb,'response_point_eval_aggregate_improves':point,
        'residual_converged':converged,'response_unique_tradeoff':unique}
    candidates={'numerical_invalid_D':not valid,'A':valid and rb and converged and unique,
        'B':valid and rb and kb and not unique,'C':valid and point and not rb,
        'D':valid and not rb and not kb}
    precedence=['numerical_invalid_D','A','B','C','D']
    chosen=next((key for key in precedence if candidates[key]),'mixed')
    expected={'numerical_invalid_D':'no_benefit_numerically_unstable','A':'response_specific_support',
        'B':'generic_state_improvement','C':'point_only','D':'no_benefit','mixed':'inconclusive_mixed_predicates'}[chosen]
    if result['outcome']!=expected:raise GateError('normative scorer / predicate trace conflict')
    return {'predicates':predicates,'candidate_predicates':candidates,'precedence':precedence+['mixed'],
        'chosen':chosen,'outcome':expected,'tradeoff':trade,
        'threshold_policy':'Frozen strict scalar decrease only; no additional tolerance/material threshold.'}

def proxy_rows_and_bridge(payload,exact,result):
    rows=[]
    for row in payload['rows']:
        t=row['time'];baseline_abs=abs(row['proxies']['A0']-exact[t]['proxy'])
        for arm,g in {**row['proxies'],'A3':exact[t]['proxy']}.items():
            error=g-exact[t]['proxy'];absolute=abs(error)
            rows.append({'arm':arm,'time':t,'role':row['role'],'proxy':g,'exact_proxy':exact[t]['proxy'],
                'signed_point_error':error,'absolute_point_error':absolute,
                'vs_A0':'improved' if absolute<baseline_abs else 'worsened' if absolute>baseline_abs else 'equal'})
    bridge={}
    for arm in result['arms']:
        selected=[r for r in rows if r['arm']==arm];evaluation=[r for r in selected if r['role']=='evaluation']
        point22=sum(r['absolute_point_error'] for r in selected)
        point12=sum(r['absolute_point_error'] for r in evaluation)
        # This arithmetic order matches the frozen scorer's evaluation row order.
        if point12!=result['arms'][arm]['point_S_abs']:raise GateError('point evaluation denominator mismatch')
        bridge[arm]={'point_S_abs_22':point22,'point_S_abs_eval12':point12,
            'total_S_abs_eval12':result['arms'][arm]['S_abs'],
            'point_improved_eval_rows':sum(r['vs_A0']=='improved' for r in evaluation),
            'point_worsened_eval_rows':sum(r['vs_A0']=='worsened' for r in evaluation),
            'point_equal_eval_rows':sum(r['vs_A0']=='equal' for r in evaluation)}
    return rows,bridge

def zero_new_science_actions():
    return dict.fromkeys(('H_matvec','PF_forward','PF_adjoint','response_solve','Ritz_solve',
        'new_fit_A0_A1_A2','new_fit_m_diagnostic_arms','new_direct_truth','new_exact_proxy',
        'ground_solve','Schur','eigensolve','branch_continuation','new_H_state_PF_geometry_molecule'),0)

@contextmanager
def no_new_science(exact):
    """Observe only A3's three fixed least-squares fits; block science entry points."""
    import numpy as np
    import scipy.linalg
    import phase06_kernels as kernels
    import phase06_phase_b as frozen_b
    import phase06_phase_a as frozen_a
    from phase06_backend import EchoBackend
    ledger={'new_science_actions':zero_new_science_actions(),'A3_reference_fits':0,
        'A3_fit_rule_invocations':0,'blocked_science_attempts':0}
    changes=[]
    def replace(module,name,value):
        changes.append((module,name,getattr(module,name)));setattr(module,name,value)
    def forbidden(*args,**kwargs):
        ledger['blocked_science_attempts']+=1
        raise GateError('new science action prohibited in Phase B')
    original_fit=frozen_b.fit_two_term_model;original_lstsq=np.linalg.lstsq
    def reference_fit(times,pos,neg,quality):
        if tuple(times)!=TRAIN or list(pos)!=[exact[t]['proxy'] for t in TRAIN] or list(neg)!=[exact[-t]['proxy'] for t in TRAIN]:
            raise GateError('only fixed A3 reference fit is authorized')
        if ledger['A3_fit_rule_invocations']!=0:raise GateError('A3 reference cannot be refitted after scoring')
        ledger['A3_fit_rule_invocations']+=1
        return original_fit(times,pos,neg,quality)
    def counted_lstsq(a,b,*args,**kwargs):
        if ledger['A3_fit_rule_invocations']!=1 or a.shape!=(5,2) or b.shape!=(5,):
            raise GateError('unauthorized least-squares fit')
        ledger['A3_reference_fits']+=1
        if ledger['A3_reference_fits']>3:raise GateError('A3 reference fit budget exceeded')
        return original_lstsq(a,b,*args,**kwargs)
    for name in ('build_response_basis','factor_response','solve_response_least_squares','solve_ritz_state'):
        replace(kernels,name,forbidden)
    replace(frozen_a,'execute_phase_a',forbidden)
    for name in ('__init__','build','forward','adjoint'):replace(EchoBackend,name,forbidden)
    for name in ('eig','eigh','eigvals','eigvalsh'):replace(np.linalg,name,forbidden)
    for name in ('expm','schur','eig','eigh'):replace(scipy.linalg,name,forbidden)
    replace(frozen_b,'fit_two_term_model',reference_fit);replace(np.linalg,'lstsq',counted_lstsq)
    try:yield ledger
    finally:
        for module,name,value in reversed(changes):setattr(module,name,value)
