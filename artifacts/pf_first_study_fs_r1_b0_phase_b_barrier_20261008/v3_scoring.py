"""Nominal scoring uses verified initial saved budgets, without refitting."""
import math
import sys
from b0_common import ROOT,R01,R0,ARMS,PROTOCOL,PREDICTION,CODE_A,require_proof,verify_execution

def validate_ladders(rows,proof):
    data=require_proof(proof);p=data['protocol']
    sys.path.insert(0,str(ROOT/R01))
    from scoring_bridge import validate_ladders as inherited
    inherited(rows,p) # Exact pinned v2 branch mathematics/namespace/coordinates.
    order=[(s['condition'],i) for s in p['systems'] for i in range(6)]
    if [(r['condition'],r['index']) for r in rows]!=order:raise ValueError('fixed N2-then-CO ascending ladder order')
    synthetic=rows[0].get('synthetic_truth_fixture')
    if type(synthetic)!=bool or any(r.get('synthetic_truth_fixture') is not synthetic for r in rows):
        raise ValueError('truth execution scope mismatch')
    expected_code='0'*64 if synthetic else verify_execution()
    for r in rows:
        if (r.get('execution_provenance')!='FS-R1-v3-new-source-direct' or
            r.get('phase_a_prediction_sha256')!=PREDICTION or
            r.get('phase_a_proof_sha256')!=proof.digest):raise ValueError('v3 truth execution binding mismatch')
        if r.get('Phase_B_execution_code_sha256')!=expected_code:raise ValueError('truth Phase B execution code mismatch')
        if r.get('unwrap_integer')!=0:raise ValueError('fixed principal-angle unwrap rule')
        if r.get('direct_error')!=abs(r['signed_direct_shift']):raise ValueError('direct magnitude mismatch')
    return True

def safety_from_saved_budget(direct,budget,spec,constants):
    if type(direct) not in (int,float) or not math.isfinite(direct):raise ValueError('finite signed direct truth required')
    B=budget['nominal_budget']
    if budget['finite_budget_reported'] is not True or B is None:
        return dict(budget=None,slack=None,status='indeterminate',safe=False,valid=False)
    if type(B) not in (int,float) or not math.isfinite(B) or B<=0:raise ValueError('invalid saved budget')
    slack=constants['epsilon_E']-abs(direct)-constants['beta']*spec['K']/(spec['t0']*B)
    # Exact preregistered nominal threshold; no new truth allowance/certificate.
    status='safe' if slack>=0 else 'unsafe'
    endpoint_slacks=[constants['epsilon_E']-abs(direct)-constants['beta']*spec['K']/(spec['t0']*budget[k]) for k in ('B_min','B_max')]
    return dict(budget=B,slack=slack,status=status,safe=status=='safe',valid=True,
        frozen_budget_interval=[budget['B_min'],budget['B_max']],
        prediction_uncertainty=budget['uncertainty_bound'],
        numerical_robustness=dict(slack_at_B_min=endpoint_slacks[0],slack_at_B_max=endpoint_slacks[1],
            nominal_outcome_unchanged=True,truth_certificate=False))

def condition_outcomes(frozen,direct,spec,constants):
    if set(frozen['estimates'])!=set(ARMS) or set(frozen['budgets'])!=set(ARMS):raise ValueError('all four frozen arms required')
    results={a:safety_from_saved_budget(direct,frozen['budgets'][a],spec,constants) for a in ARMS}
    b0=results['M00p']['budget'];b01=results['M01p']['budget'];b11=results['M11p']['budget']
    baseline=results['M00p']['valid'];factor=1-constants['eta']
    return dict(arms=results,B0_prime=b0,primary='M11p',challenger='M01p',
        primary_gain=bool(baseline and results['M11p']['safe'] and b11<=factor*b0),
        local_gain=bool(baseline and results['M01p']['safe'] and b01<=factor*b0),
        state_increment=bool(results['M01p']['safe'] and results['M11p']['safe'] and b11<=factor*b01),
        safety_repair=bool(results['M01p']['valid'] and results['M01p']['status']=='unsafe' and results['M11p']['safe']))

def score_frozen(proof,rows):
    data=require_proof(proof)
    if rows is None:raise PermissionError('truth-free Phase A cannot be scored')
    validate_ladders(rows,proof)
    p=data['protocol'];output=[]
    for spec in p['systems']:
        frozen=next(r for r in data['payload']['initial_operational'] if r['condition']==spec['condition'])
        final=next(r for r in rows if r['condition']==spec['condition'] and r['time_role']=='primary_scoring')
        result=condition_outcomes(frozen,final['signed_direct_shift'],spec,p['constants'])
        result.update(condition=spec['condition'],signed_direct_truth=final['signed_direct_shift'],
            direct_PF_error=abs(final['signed_direct_shift']),truth_time=spec['t0'],truth_branch_id=final['selected_branch_id'],
            frozen_signed_predictions=frozen['estimates'],budget_authority='verified_initial_saved_scalar')
        output.append(result)
    sys.path.insert(0,str(ROOT/R0))
    from scorer import study_interpretation
    return dict(conditions=output,study=study_interpretation(output),truth_values_scored=2,
        intermediate_truth_used_for_resources=False,nominal_budget_rule=True,posthoc_best_arm=None,
        prediction_sha256=PREDICTION,phase_a_proof_sha256=proof.digest,
        synthetic_truth_fixture=rows[0]['synthetic_truth_fixture'])
