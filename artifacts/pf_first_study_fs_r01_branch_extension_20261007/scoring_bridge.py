"""Scoring consumes only complete validated ladders' final t0 truth."""
import math
from r01_common import canonical,sha,spec_for,ladder_for,v1_scorer
from branch_math import BranchFailure,validate_branch_id,fail

def validate_prediction(prediction,p):
    if set(prediction)!={'stage','truth_opened','protocol_sha256','systems'} or prediction['stage']!='FS-R1-Phase-A' or prediction['truth_opened'] is not False:
        raise ValueError('truth-free frozen prediction schema')
    from r01_common import HERE
    if prediction['protocol_sha256']!=sha((HERE/'fs_r1_protocol_v2.json').read_bytes()):raise ValueError('prediction protocol hash')
    expected={s['condition']:s for s in p['systems']}
    rows=prediction['systems']
    if len(rows)!=2 or {r.get('condition') for r in rows}!=set(expected):raise ValueError('both prediction conditions')
    forbidden={'ground_overlap','ground_state_overlap_probability','branch_id','signed_direct_shift','branch_rows',
        'exact_ground','exact_state','ground_state','direct_truth','previous_vector_overlap','previous_branch_id',
        'selected_branch_id','selected_eigenvalue','ground_overlap_comparator_id','degenerate_projector_overlap','vector','vectors','unitary'}
    def scalar_only(obj):
        if isinstance(obj,dict):
            if forbidden&set(obj):raise ValueError('truth information in Phase A')
            for value in obj.values():scalar_only(value)
        elif isinstance(obj,(list,tuple)):
            for value in obj:scalar_only(value)
        elif type(obj) not in (bool,str,int,float,type(None)):raise ValueError('non-scalar Phase A object')
        elif isinstance(obj,float) and not math.isfinite(obj):raise ValueError('nonfinite prediction')
    scalar_only(rows)
    for row in rows:
        allowed={'condition','source_identity_sha256','time','estimates','budgets','proxy_rows','fits','Ritz','ledger','initial_operational','cold_validation'}
        if set(row)-allowed:raise ValueError('truth information or unknown field in Phase A')
        sp=expected[row['condition']]
        if row['source_identity_sha256']!=sp['source_identity_sha256'] or row['time']!=sp['t0']:raise ValueError('prediction source/time changed')
        if set(row['estimates'])!=set(v1_scorer.ARMS) or set(row['budgets'])!=set(v1_scorer.ARMS):raise ValueError('all four frozen arms required')
        for arm,estimate in row['estimates'].items():
            expected_budget=v1_scorer.budget(abs(estimate),sp['t0'],sp['K'],p['constants'])
            if row['budgets'][arm]!=expected_budget:raise ValueError('new-source frozen budget mismatch')
    return True

def validate_ladders(rows,p):
    if len(rows)!=12:fail('required 12 truth coordinates missing/extra')
    for spec in p['systems']:
        condition=spec['condition'];ladder=ladder_for(condition)
        selected=[r for r in rows if r.get('condition')==condition]
        if len(selected)!=6:fail('required six coordinates per condition')
        for index,(row,time) in enumerate(zip(selected,ladder['times'])):
            if row.get('source_identity_sha256')!=spec['source_identity_sha256']:fail('source identity mismatch')
            if not math.isfinite(row.get('time',float('nan'))) or float(row['time']).hex()!=float(time).hex():fail('historical/nearest-time/missing/non-monotone coordinate')
            if row.get('index')!=index:fail('duplicate branch assignment/index')
            validate_branch_id(row.get('selected_branch_id'),spec['source_identity_sha256'],index)
            if index and row.get('previous_branch_id')!=selected[index-1]['selected_branch_id']:fail('previous branch checkpoint mismatch')
            if not index and row.get('previous_branch_id') is not None:fail('anchor prior branch')
            role='primary_scoring' if index==5 else 'branch_certification'
            if row.get('time_role')!=role or row.get('provenance')!='FS-R1-v2-new-source-direct' or row.get('branch_status')!='resolved':fail('historical truth substitution/role/unresolved branch')
            for key in ('eigenpair_residual','unitarity_residual'):
                value=row.get(key,float('nan'))
                if not math.isfinite(value) or not 0<=value<=1e-10:fail('residual/NaN/Inf gate')
            if index:
                overlap=row.get('previous_vector_overlap',float('nan'))
                if not math.isfinite(overlap) or not .9<=overlap<=1+1e-12:fail('previous overlap gate')
                if not row.get('selection_rule','').startswith('maximum_previous_selected_vector_overlap'):fail('later ground-overlap selector forbidden')
            elif not row.get('selection_rule','').startswith('maximum_exact_ground_overlap'):fail('first anchor selector')
            if not math.isfinite(row.get('signed_direct_shift',float('nan'))):fail('nonfinite direct shift')
    return True

def score_frozen(prediction,rows,p):
    validate_prediction(prediction,p);validate_ladders(rows,p)
    results=[]
    for spec in p['systems']:
        condition=spec['condition'];frozen=next(r for r in prediction['systems'] if r['condition']==condition)
        final=next(r for r in rows if r['condition']==condition and r['time_role']=='primary_scoring')
        if final['time']!=spec['t0']:fail('branch intermediate cannot change t0')
        result=v1_scorer.condition_outcomes(frozen['estimates'],final['signed_direct_shift'],spec,p['constants'])
        result.update(condition=condition,truth_time=spec['t0'],truth_branch_id=final['selected_branch_id'])
        results.append(result)
    return dict(conditions=results,study=v1_scorer.study_interpretation(results),truth_values_scored=2,
        intermediate_truth_used_for_resources=False,posthoc_best_arm=None)
