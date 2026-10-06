"""Saved-truth reader and scoring; never imported by Phase A modules."""
from pathlib import Path
import csv,io,json
import numpy as np
from phase06_contract import BASE,PH05,PROTOCOL_SHA,GateError,canonical,sha
from phase06_freeze import verify_phase_a_freeze
from phase06_kernels import TRAIN,EVAL,fit_two_term_model,evaluate_fit

def _verified_truth_bytes(root,path,transport,source_record):
    raw=(Path(root)/path).read_bytes()
    if sha(raw)!=source_record['sha256'] or transport.blob(BASE,path)!=raw:
        raise GateError('saved truth source identity mismatch')
    return raw

def select_saved_truth(branch_raw,observables_raw,join_contract):
    """Numerically decode only twelve direct and twenty-two exact-proxy rows."""
    eval_keys={s*t for t in EVAL for s in (1,-1)};all_keys={s*t for t in TRAIN+EVAL for s in (1,-1)}
    identities={float(r['time_hartree_inverse']):r for r in join_contract['keys']}
    direct={};exact={}
    for r in csv.DictReader(io.StringIO(branch_raw.decode())):
        if (r['experiment_id'],r['case_id'],r['formula_id'],r['grid_role'])!=('B','H4','current_m3','mechanism_fixed'):continue
        t=float(r['time_hartree_inverse'])
        if t not in eval_keys:continue
        if t in direct:raise GateError('duplicate saved direct row')
        expected=identities[t]
        if any(r[k]!=expected[k] for k in expected) or r['branch_reliable']!='True':
            raise GateError('unreliable/mismatched saved branch identity')
        direct[t]=float(r['direct_shift_hartree'])
    for r in csv.DictReader(io.StringIO(observables_raw.decode())):
        if (r['experiment_id'],r['case_id'],r['formula_id'],r['state_id'])!=('B','H4','current_m3','exact'):continue
        t=float(r['time_hartree_inverse'])
        if t not in all_keys:continue
        if t in exact:raise GateError('duplicate saved exact-proxy row')
        if int(r['sign'])!=(1 if t>0 else -1) or float(r['absolute_time'])!=abs(t):
            raise GateError('saved exact proxy coordinate identity mismatch')
        exact[t]={'proxy':float(r['proxy_imag_hartree']),'quality':r['quality_class']}
    if set(direct)!=eval_keys or set(exact)!=all_keys:
        raise GateError('missing saved truth coordinate; no interpolation/repair')
    if not all(np.isfinite(v) for v in [*direct.values(),*(r['proxy'] for r in exact.values())]):
        raise GateError('nonfinite saved truth')
    return direct,exact

def score_payload(payload,direct,exact,receipt):
    expected={s*t for t in EVAL for s in (1,-1)}
    if set(direct)!=expected or set(exact)!={s*t for t in TRAIN+EVAL for s in (1,-1)}:
        raise GateError('complete fixed truth keys required for scoring')
    oracle=fit_two_term_model(TRAIN,[exact[t]['proxy'] for t in TRAIN],
        [exact[-t]['proxy'] for t in TRAIN],[exact[t]['quality'] for t in TRAIN])
    predictions={k:[dict(row) for row in rows] for k,rows in payload['predictions'].items()}
    model=oracle['raw_positive_even_two_term']
    predictions['A3']=[{'time':s*t,'prediction':evaluate_fit(model,s*t),'proxy':exact[s*t]['proxy'],'fit_status':model['status']} for t in EVAL for s in (1,-1)]
    arms={}
    for arm,rows in predictions.items():
        scored=[]
        for p in rows:
            t=p['time'];delta=direct[t];error=p['prediction']-delta;u=abs(delta)-abs(p['prediction'])
            scored.append({**p,'direct_shift':delta,'exact_proxy':exact[t]['proxy'],
                'state_like_error':p['proxy']-exact[t]['proxy'],'total_error':error,
                'absolute_error':abs(error),'underestimation':u,'positive_underestimation':max(0,u),
                'sign_crossing':bool(np.sign(p['prediction'])!=np.sign(delta))})
        arms[arm]={'rows':scored,'S_abs':sum(r['absolute_error'] for r in scored),
            'S_under':sum(r['positive_underestimation'] for r in scored),
            'E_max':max(r['absolute_error'] for r in scored),
            'point_S_abs':sum(abs(r['state_like_error']) for r in scored),
            'sign_crossing_count':sum(r['sign_crossing'] for r in scored)}
    baseline={r['time']:r for r in arms['A0']['rows']}
    for arm,metrics in arms.items():
        comparisons=[np.sign(r['absolute_error']-baseline[r['time']]['absolute_error']) for r in metrics['rows']]
        metrics.update(improved_count=comparisons.count(-1),worsened_count=comparisons.count(1),equal_count=comparisons.count(0))
        metrics['continuous_ratios']={key:metrics[key]/arms['A0'][key] if arms['A0'][key] else None for key in ('S_abs','S_under','E_max','point_S_abs')}
    response=arms['A1'];ritz=arms['A2'];base=arms['A0']
    valid=all(payload['fits'][a]['raw_positive_even_two_term']['status']=='fit_ok' for a in ('A0','A1','A2'))
    rb=response['S_abs']<base['S_abs'] and response['S_under']<base['S_under']
    kb=ritz['S_abs']<base['S_abs'] and ritz['S_under']<base['S_under']
    costs=payload['cost']['standalone_primary_one_pass']
    rt=(response['S_abs'],response['S_under'],costs['A1']['H_actions'],costs['A1']['PF_actions'])
    kt=(ritz['S_abs'],ritz['S_under'],costs['A2']['H_actions'],costs['A2']['PF_actions'])
    dominated=all(k<=r for k,r in zip(kt,rt)) and any(k<r for k,r in zip(kt,rt))
    unique=not dominated and any(r<k for r,k in zip(rt,kt))
    if not valid:outcome='no_benefit_numerically_unstable'
    elif rb and payload['residual_convergence']['converged'] and unique:outcome='response_specific_support'
    elif rb and kb and not unique:outcome='generic_state_improvement'
    elif response['point_S_abs']<base['point_S_abs'] and not rb:outcome='point_only'
    elif not rb and not kb:outcome='no_benefit'
    else:outcome='inconclusive_mixed_predicates'
    return {'phase_a_commit':receipt['commit'],'phase_a_prediction_sha256':receipt['prediction_sha256'],
        'arms':arms,'oracle_fits':oracle,'outcome':outcome,'cost':payload['cost'],
        'response_residual_statistics':{'convergence':payload['residual_convergence'],
            'by_m':{str(m):{'min':min(r['response'][str(m)]['relative_residual'] for r in payload['rows']),
                'max':max(r['response'][str(m)]['relative_residual'] for r in payload['rows']),
                'mean':float(np.mean([r['response'][str(m)]['relative_residual'] for r in payload['rows']]))} for m in (1,2,4,8)}},
        'saved_direct_truth_read_count':12,'saved_exact_proxy_read_count':22,'new_direct_truth_count':0}

def run_phase_b(root,receipt,contract,schema,authorization=None,transport=None,synthetic_reader=None):
    if synthetic_reader is None and (authorization is None or authorization.phase!='phase-b' or authorization.protocol_sha256!=PROTOCOL_SHA):
        raise GateError('science_not_authorized: Phase B truth reader disabled')
    payload,raw=verify_phase_a_freeze(root,receipt,contract,schema,transport)
    if synthetic_reader is None and payload['input_domain']!='production':
        raise GateError('production truth reader requires production Phase A freeze')
    if synthetic_reader is not None:
        if payload['input_domain']!='synthetic':raise GateError('cannot use synthetic truth transport for production inputs')
        direct,exact=synthetic_reader()
    else:
        from phase06_freeze import GitTransport
        transport=transport or GitTransport(root)
        registry_path=PH05+'/source_manifest.json'
        registry_raw=transport.blob(BASE,registry_path)
        registry=json.loads(registry_raw)
        source={r['path']:r for r in registry['sources']}
        join=json.loads(transport.blob(BASE,PH05+'/saved_truth_join_contract.json'))
        branch_path=join['source']
        observables_path='artifacts/pf_first_study_phase_b_20260925_5a2f0a2/observables.csv'
        branch_raw=_verified_truth_bytes(root,branch_path,transport,source[branch_path])
        obs_raw=_verified_truth_bytes(root,observables_path,transport,source[observables_path])
        direct,exact=select_saved_truth(branch_raw,obs_raw,join)
    result=score_payload(payload,direct,exact,receipt)
    if canonical(payload)!=raw:raise GateError('Phase B modified frozen Phase A payload')
    return result
