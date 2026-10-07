"""Pure scalar new-source budgets/safety/outcomes. No historical truth/budget inputs."""
import math

ARMS=('M00p','M10p','M01p','M11p')

def finite(x):
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x): raise ValueError('finite scalar required')
    return float(x)

def budget(c,t,K,cfg):
    c,t=finite(c),finite(t)
    epsilon,beta,gamma,eta=(finite(cfg[k]) for k in ('epsilon_E','beta','gamma','eta'))
    if epsilon<=0 or beta<=0 or gamma<=0 or not 0<=eta<1: raise ValueError('budget constants domain')
    if c<0 or t<=0 or type(K)!=int or K<=0: raise ValueError('budget domain')
    if c>=cfg['epsilon_E']: return None
    return cfg['gamma']*cfg['beta']*K/(t*(cfg['epsilon_E']-c))

def safety(estimate,direct,t,K,cfg,valid=True,numeric_allowance=0.):
    numeric_allowance=finite(numeric_allowance)
    if numeric_allowance<0 or type(valid)!=bool: raise ValueError('validity/allowance domain')
    B=budget(abs(finite(estimate)),t,K,cfg)
    if B is None: return dict(budget=None,slack=None,safe=False,status='infeasible',valid=False)
    slack=cfg['epsilon_E']-abs(finite(direct))-cfg['beta']*K/(t*B)
    status='safe' if slack>=numeric_allowance else ('unsafe' if slack < -numeric_allowance else 'indeterminate')
    return dict(budget=B,slack=slack,safe=valid and status=='safe',status=status,valid=bool(valid))

def condition_outcomes(estimates,direct,spec,cfg,valid=None,numeric_allowance=0.):
    if set(estimates)!=set(ARMS): raise ValueError('all four preregistered arms required')
    valid=dict.fromkeys(ARMS,True) if valid is None else valid
    if set(valid)!=set(ARMS): raise ValueError('all four validity flags required')
    results={arm:safety(value,direct,spec['t0'],spec['K'],cfg,valid[arm],numeric_allowance) for arm,value in estimates.items()}
    b0=results['M00p']['budget']; b01=results['M01p']['budget']; b11=results['M11p']['budget']
    reference_valid=results['M00p']['valid'] and b0 is not None
    factor=1-cfg['eta']
    primary=reference_valid and results['M11p']['safe'] and b11<=factor*b0
    local=reference_valid and results['M01p']['safe'] and b01<=factor*b0
    increment=results['M01p']['safe'] and results['M11p']['safe'] and b11<=factor*b01
    repair=results['M01p']['valid'] and results['M01p']['status']=='unsafe' and results['M11p']['safe']
    return dict(arms=results,B0_prime=b0,primary_gain=bool(primary),local_gain=bool(local),
                state_increment=bool(increment),safety_repair=bool(repair),primary='M11p',challenger='M01p')

def study_interpretation(rows):
    if len(rows)!=2: raise ValueError('both fixed conditions required')
    count=sum(r['primary_gain'] for r in rows)
    stop=[]
    if any(r['arms']['M11p']['status']=='unsafe' for r in rows): stop.append('resource extension STOP')
    if any(not r['arms']['M11p']['valid'] or r['arms']['M11p']['status']=='indeterminate' for r in rows):
        stop.append('numerical/technical identification incomplete; no scientific support')
    if all(r['arms']['M11p']['safe'] for r in rows) and count<2: stop.append('stop micro-accuracy optimization')
    local_sufficient=all(r['local_gain'] and not r['state_increment'] for r in rows)
    state_count=sum(r['state_increment'] for r in rows)
    return dict(primary_gain_count=count,interpretation=['no resource-stage support','condition-dependent','small development support'][count],
                local_preferred_simpler=local_sufficient,state_extension_consideration=state_count==2,
                condition_dependence=state_count==1,stop_rules=stop,independent_validation=False,posthoc_best_arm=None)
