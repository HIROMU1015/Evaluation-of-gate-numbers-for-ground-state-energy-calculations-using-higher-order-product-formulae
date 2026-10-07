"""Norm/propagation boundary and lease/recovery fault tests; no production data."""
import copy
import ast
import itertools
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a0_common as c
import numerical_contract as n
import phase_a_wrapper as w
import recovery_wrapper as r
from run_lease import RunLease, read_start


def diag():
    return dict(retained_rank=8, rank_stop_index=None, rank_stop_reason='requested_rank_reached', projected_dimension=9,
                phase_pivot_index=0, tie_resolution_branch='lowest_projected_eigenspace:e0', rank_status='nonzero_rank',
                basis_orthogonality_residual=0., psi_basis_orthogonality_residual=0., projected_Hermiticity_residual=0.,
                projected_H_F_norm=1., Ritz_normalization=1., Ritz_energy=0., Ritz_residual_norm=1., rank_thresholds=[1.]*8)


def binding():
    return dict(authorization_id='synthetic-a0-fixture', authorization_sha256='a'*64,
                protocol_sha256=c.sha((c.HERE/'fs_r1_protocol_v3.json').read_bytes()),
                execution_code_sha256=c.sha(c.canonical(c.read('execution_code_identity.json'))),
                source_hashes={s['condition']:{k:s[k] for k in ('source_identity_sha256','new_H_sha256','operational_archive_sha256')}
                               for s in c.protocol()['systems']})


def fixture_pass(spec, category):
    # Analytic zero scalars. No H, PF, fit kernel or source array is invoked.
    p = c.protocol()
    estimates = dict.fromkeys(p['arms'], 0.)
    return dict(condition=spec['condition'], source_identity_sha256=spec['source_identity_sha256'], pass_category=category,
        proxy_rows=[dict(state=state, time=t, signed_proxy=0., input_norm=1., PF_norm=1., reference_norm=1., echo_real=1., echo_imag=0.)
                    for state in ('CISD','Ritz8') for t in [*spec['training_absolute'],spec['t0']]],
        fits={state:dict(coefficient_values=[0.,0.]) for state in ('CISD','Ritz8')}, estimates=estimates,
        budgets={a:n.budget_interval(v,n.arm_tau(spec['condition'],a),spec,p['constants']) for a,v in estimates.items()},
        Ritz=diag(), ledger=dict(scope='synthetic callback fixture; production actions=0'))


def setup_run(tmp_path, acquire=None, validator=None):
    p = c.protocol()
    calls = []
    def default_acquire(spec, category):
        calls.append((spec['condition'],category))
        return fixture_pass(spec,category)
    kwargs = dict(specs=p['systems'], binding=binding(), registry=tmp_path/'leases', run_id='toy-run',
                  acquire=acquire or default_acquire, validate=lambda row,spec:w.validate_pass(row,spec,p),
                  compare=n.compare_condition, public_path=tmp_path/'public.json',
                  public_validator=validator or (lambda obj:w.validate_complete(obj,p)))
    return kwargs, calls


def test_input_norm_exact_error_gate_pass():
    assert n.absolute_gate(1e-12,1e-12,'input norm error')==1e-12


def test_input_norm_over_gate_fail():
    with pytest.raises(n.NumericalFailure):n.absolute_gate(np.nextafter(1e-12,np.inf),1e-12,'input norm error')
    with pytest.raises(n.NumericalFailure):n.norm_gate(1+2e-12,'input')


@pytest.mark.parametrize('kind', ['PF','reference'])
def test_output_norm_gates(kind):
    n.norm_gate(1.,kind)
    n.absolute_gate(1e-10,n.NORM_GATES[kind],kind)
    with pytest.raises(n.NumericalFailure):n.norm_gate(1+2e-10,kind)


@pytest.mark.parametrize('value', [np.nan,np.inf,-np.inf])
def test_nonfinite_norm_fail(value):
    with pytest.raises(n.NumericalFailure):n.norm_gate(value,'input')


@pytest.mark.parametrize('difference', [n.TAU_G/2,n.TAU_G])
def test_raw_less_or_equal_pass(difference):
    assert n.raw_replay(0.,difference)==difference


def test_raw_over_fail():
    with pytest.raises(n.NumericalFailure):n.raw_replay(0.,np.nextafter(n.TAU_G,np.inf))


def test_near_zero_absolute_only():
    n.raw_replay(0.,n.TAU_G)
    with pytest.raises(n.NumericalFailure):n.raw_replay(1e8,1e8+1e-6)


@pytest.mark.parametrize('condition', ['N2_active_eq_sto3g','CO_active_eq_sto3g'])
def test_coefficient_propagation_worst_case_vertices(condition):
    spec = c.spec_for(condition)
    out = n.propagation(spec)
    P = np.array(out['P'])
    expected = n.TAU_G*np.sum(abs(P),axis=1)
    np.testing.assert_array_equal(expected,out['coefficient_uncertainty_bounds'])
    vertices = np.array(list(itertools.product((-n.TAU_G,n.TAU_G),repeat=3)))
    actual = np.max(abs(vertices@P.T),axis=0)
    np.testing.assert_allclose(actual,expected,rtol=3e-15,atol=0) # toy floating arithmetic only


@pytest.mark.parametrize('condition', ['N2_active_eq_sto3g','CO_active_eq_sto3g'])
def test_t0_linear_map_and_worst_case(condition):
    out = n.propagation(c.spec_for(condition))
    A,P,q = map(np.array,(out['A'],out['P'],out['q']))
    np.testing.assert_allclose(P,np.linalg.pinv(A),rtol=2e-13,atol=0) # independent fixed-design map
    np.testing.assert_array_equal(q@P,out['w'])
    vertices = np.array(list(itertools.product((-n.TAU_G,n.TAU_G),repeat=3)))
    worst = np.max(abs(vertices@np.array(out['w'])))
    np.testing.assert_allclose(worst,out['tau_fit_at_t0'],rtol=3e-15,atol=0)


def test_no_independent_fit_or_budget_tol():
    contract = c.read('fs_r1_numerical_contract_v1.json')
    for key in ('independent_fit_tolerance','independent_budget_absolute_tolerance','independent_budget_relative_tolerance'):
        assert contract[key] is None


@pytest.mark.parametrize('condition', ['N2_active_eq_sto3g','CO_active_eq_sto3g'])
def test_fixed_design_deterministic(condition):
    spec = c.spec_for(condition)
    assert n.propagation(spec)==n.propagation_for(condition)==n.propagation(spec)


def test_budget_finite_interval():
    spec = c.protocol()['systems'][0];cfg=c.protocol()['constants']
    b = n.budget_interval(2e-5,1e-11,spec,cfg)
    assert b['B_min']<b['nominal_budget']<b['B_max'] and b['finite_budget_reported']


@pytest.mark.parametrize('p', [c.protocol()['constants']['epsilon_E'], c.protocol()['constants']['epsilon_E']+1e-8])
def test_budget_equal_or_over_indeterminate(p):
    b = n.budget_interval(p,0.,c.protocol()['systems'][0],c.protocol()['constants'])
    assert b['status']=='NUMERICALLY_INDETERMINATE_BUDGET'
    assert all(b[k] is None for k in ('nominal_budget','B_min','B_max'))


def test_budget_no_clipping_nominally_feasible_edge():
    cfg=c.protocol()['constants'];spec=c.protocol()['systems'][0]
    b=n.budget_interval(cfg['epsilon_E']-1e-12,2e-12,spec,cfg)
    assert b['nominal_feasibility']=='feasible' and b['denominator_min']<0
    assert b['nominal_budget'] is None


def test_ratio_interval_propagation():
    spec=c.protocol()['systems'][0];cfg=c.protocol()['constants']
    x=n.budget_interval(1e-5,1e-11,spec,cfg);base=n.budget_interval(2e-5,2e-11,spec,cfg)
    ratio=n.ratio_interval(x,base)
    assert ratio['lower']==x['B_min']/base['B_max']
    assert ratio['upper']==x['B_max']/base['B_min']
    assert ratio['label']=='prediction_only_not_truth_scored'


@pytest.mark.parametrize('field,new', [('retained_rank',7),('rank_stop_reason','different'),('phase_pivot_index',1),
    ('rank_stop_index',7),('tie_resolution_branch','lowest_projected_eigenspace:e1'),('rank_status','zero_rank')])
def test_ritz_categorical_mismatch_fail(field,new):
    a=diag();b=diag();b[field]=new
    if field=='retained_rank':b['projected_dimension']=8
    with pytest.raises(n.NumericalFailure):n.compare_ritz(a,b)


def test_both_orthogonality_pass_no_energy_difference_tol():
    a=diag();b=diag();a['basis_orthogonality_residual']=n.SCALE;b['Ritz_energy']=17.;b['Ritz_residual_norm']=23.
    result=n.compare_ritz(a,b)
    assert result['continuous_differences']['Ritz_energy']==17.
    assert result['continuous_difference_tolerance'] is None


def test_one_orthogonality_failure_fails_replay():
    a=diag();b=diag();b['basis_orthogonality_residual']=np.nextafter(n.SCALE,np.inf)
    with pytest.raises(n.NumericalFailure):n.compare_ritz(a,b)


def test_all_initial_before_cold_and_aggregate_recovery(tmp_path):
    calls=[]
    def acquire(spec,category):
        if category=='cold_validation':
            private=next((tmp_path/'leases').iterdir())
            assert (private/'initial_operational_complete.recovery.json').exists()
            assert len(calls)>=2
        calls.append((spec['condition'],category))
        return fixture_pass(spec,category)
    kwargs,_=setup_run(tmp_path,acquire=acquire)
    out=w.orchestrate(**kwargs)
    assert calls==[(c.protocol()['systems'][i]['condition'],cat) for cat in ('initial_operational','cold_validation') for i in (0,1)]
    assert out['receipt']['public_matches_recovery']


def test_scientific_indeterminate_does_not_skip_CO(tmp_path):
    calls=[]
    def acquire(spec,category):
        calls.append(spec['condition'])
        row=fixture_pass(spec,category)
        # Supply a valid derived large-fit baseline, with no runtime fitting.
        if spec['condition'].startswith('N2'):
            coef=1.
            row['fits']['CISD']['coefficient_values']=[coef,0.]
            row['estimates']['M00p']=coef*spec['t0']**4
            row['budgets']['M00p']=n.budget_interval(row['estimates']['M00p'],n.arm_tau(spec['condition'],'M00p'),spec,c.protocol()['constants'])
        return row
    kwargs,_=setup_run(tmp_path,acquire=acquire)
    out=w.orchestrate(**kwargs)
    assert calls==[s['condition'] for _ in range(2) for s in c.protocol()['systems']]
    assert out['payload']['initial_operational'][0]['budgets']['M00p']['nominal_budget'] is None


def test_authorization_reuse_new_run_id_rejected(tmp_path):
    b=binding();RunLease(tmp_path/'leases','first',b)
    changed=copy.deepcopy(b);changed['authorization_sha256']='b'*64
    with pytest.raises(FileExistsError):RunLease(tmp_path/'leases','second',changed)


def test_duplicate_RUN_STARTED_rejected(tmp_path):
    first=RunLease(tmp_path/'leases','first',binding())
    before=(first.directory/'RUN_STARTED').read_bytes()
    with pytest.raises(FileExistsError):RunLease(tmp_path/'leases','first',binding())
    assert (first.directory/'RUN_STARTED').read_bytes()==before


def test_recovery_before_public_validation(tmp_path):
    def validator(payload):
        private=next((tmp_path/'leases').iterdir())
        path=private/'phase_a_complete.recovery.json'
        snapshot,_=r.load_return(path)
        assert snapshot['payload']==payload
        assert not (tmp_path/'public.json').exists()
    kwargs,_=setup_run(tmp_path,validator=validator)
    w.orchestrate(**kwargs)


def test_public_failure_no_science_rerun_and_recover_only(tmp_path):
    kwargs,calls=setup_run(tmp_path,validator=lambda x:(_ for _ in ()).throw(ValueError('injected public schema failure')))
    with pytest.raises(ValueError,match='injected'):w.orchestrate(**kwargs)
    assert len(calls)==4
    with pytest.raises(FileExistsError):w.orchestrate(**kwargs)
    assert len(calls)==4
    path=next((tmp_path/'leases').iterdir())/'phase_a_complete.recovery.json'
    receipt=w.recover_public(path,tmp_path/'public.json')
    assert receipt['production_rerun'] is False and len(calls)==4
    snapshot,_=r.load_return(path)
    assert (tmp_path/'public.json').read_bytes()==c.canonical(snapshot['payload'])


def test_completed_lease_cannot_rerun(tmp_path):
    kwargs,calls=setup_run(tmp_path)
    w.orchestrate(**kwargs)
    with pytest.raises(FileExistsError):w.orchestrate(**kwargs)
    assert len(calls)==4


def test_recovery_hash_mismatch_rejected(tmp_path):
    lease=RunLease(tmp_path/'leases','run',binding())
    path,_=r.save_return(lease,'toy',dict(value=1.))
    path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='hash mismatch'):r.load_return(path)


@pytest.mark.parametrize('part', ['real','imag'])
def test_echo_nonfinite(part):
    values={'real':1.,'imag':0.};values[part]=np.nan
    with pytest.raises(n.NumericalFailure):n.echo_gate(values['real'],values['imag'],1.,1.)


def test_Cauchy_bound_frozen_derivation():
    numerical=c.read('fs_r1_numerical_contract_v1.json')
    assert numerical['echo_round_scale']>numerical['complex_dot_gamma_8N']
    assert n.echo_gate(1.,0.,1.,1.)['tau_round']==n.SCALE
    with pytest.raises(n.NumericalFailure):n.echo_gate(1+2*n.SCALE,0.,1.,1.)


def test_budget_status_change_fails_even_prediction_within_tau():
    spec=c.protocol()['systems'][0];cfg=c.protocol()['constants'];tau=1e-11
    a=n.budget_interval(cfg['epsilon_E']-1.5*tau,tau,spec,cfg)
    b=n.budget_interval(cfg['epsilon_E']-.8*tau,tau,spec,cfg)
    with pytest.raises(n.NumericalFailure,match='status'):n.budget_replay(a,b)


def test_stable_indeterminate_is_undefined_not_zero_budget():
    b=n.budget_interval(1.,n.TAU_G,c.protocol()['systems'][0],c.protocol()['constants'])
    result=n.budget_replay(b,b)
    assert result['finite_budget_replay_covered'] is False and result['nominal_difference'] is None


def test_budget_denominator_sign_change_fails():
    a=n.budget_interval(1.,n.TAU_G,c.protocol()['systems'][0],c.protocol()['constants'])
    b=copy.deepcopy(a);b['denominator']=-b['denominator']
    with pytest.raises(n.NumericalFailure,match='sign'):n.budget_replay(a,b)


def test_signed_interval_crossing_zero():
    p=n.prediction_interval(1e-12,n.TAU_G)
    assert p['lower_signed_bound']<0<p['upper_signed_bound'] and p['c_min']==0


def test_missing_duplicate_raw_coordinate_fails():
    spec=c.protocol()['systems'][0];a=fixture_pass(spec,'initial_operational');b=fixture_pass(spec,'cold_validation')
    b['proxy_rows'][-1]=b['proxy_rows'][0].copy()
    with pytest.raises(n.NumericalFailure):n.compare_condition(a,b,spec)


def test_technical_initial_abort_prevents_all_remaining_science(tmp_path):
    calls=[]
    def acquire(spec,category):
        calls.append((spec['condition'],category))
        raise RuntimeError('injected technical failure')
    kwargs,_=setup_run(tmp_path,acquire=acquire)
    with pytest.raises(RuntimeError):w.orchestrate(**kwargs)
    assert len(calls)==1
    with pytest.raises(FileExistsError):w.orchestrate(**kwargs)
    assert len(calls)==1


def test_no_authorization_fails_before_lease_or_backend(tmp_path,monkeypatch):
    monkeypatch.setattr(w,'RunLease',lambda *a,**k:pytest.fail('lease before authorization'))
    with pytest.raises(PermissionError):w.execute_phase_a(None,'no-run',tmp_path/'public.json')
    assert not (tmp_path/'public.json').exists()


def test_execution_bundle_omission_rejected(monkeypatch):
    original=c.read
    def changed(name):
        result=original(name)
        if name=='execution_code_identity.json':result['sha256'].pop(next(iter(result['sha256'])))
        return result
    monkeypatch.setattr(c,'read',changed)
    with pytest.raises(ValueError,match='incomplete'):c.verify_frozen()


def test_recovery_rejects_private_array(tmp_path):
    lease=RunLease(tmp_path/'leases','run',binding())
    with pytest.raises((TypeError,ValueError)):r.save_return(lease,'toy',dict(private=np.ones(2)))
    assert not (lease.directory/'toy.recovery.json').exists()


def test_recovery_lease_binding_tamper_rejected(tmp_path):
    lease=RunLease(tmp_path/'leases','run',binding())
    path,_=r.save_return(lease,'toy',dict(value=1.))
    snapshot=json.loads(path.read_text());snapshot['binding']['protocol_sha256']='f'*64
    raw=c.canonical(snapshot);path.chmod(0o600);path.write_bytes(raw)
    digest=path.with_suffix(path.suffix+'.sha256');digest.chmod(0o600);digest.write_text(c.sha(raw)+'\n')
    with pytest.raises(ValueError,match='binding'):r.load_return(path)


def test_ritz_annotation_preserves_all_frozen_arithmetic():
    import production_adapter as adapter
    raw=(c.ROOT/'artifacts/pf_first_study_response_pilot_phase05_20261006/phase05_math.py').read_bytes()
    tree=adapter.annotated_ritz_ast(raw)
    expected_names={'project','fix_phase','Basis','build_response_basis','solve_ritz_state'}
    old=ast.Module(body=[node for node in ast.parse(raw).body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in expected_names],type_ignores=[])
    annotated_returns=0
    for node in ast.walk(tree):
        if isinstance(node,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='_coefficients' for k in node.keys):
            assert [k.value for k in node.keys[-2:]]==['_coefficients','_tie_index']
            del node.keys[-2:];del node.values[-2:];annotated_returns+=1
    assert annotated_returns==2
    assert ast.dump(tree)==ast.dump(old)


def test_A0_adapter_rejects_production_dimension_without_authorization():
    import production_adapter as adapter
    with pytest.raises(PermissionError):adapter.ContextV3().guard(1568)
    with pytest.raises(PermissionError):adapter.ContextV3(phase='synthetic').guard(1568)


def test_budget_coverage_requires_prediction_replay():
    spec=c.protocol()['systems'][0];cfg=c.protocol()['constants']
    a=n.budget_interval(1e-5,n.TAU_G,spec,cfg)
    b=n.budget_interval(1e-5+2*n.TAU_G,n.TAU_G,spec,cfg)
    with pytest.raises(n.NumericalFailure,match='prediction replay'):n.budget_replay(a,b)


@pytest.mark.parametrize('field', ['execution_code_sha256','source_hashes'])
def test_public_result_current_identity_binding(tmp_path,field):
    kwargs,_=setup_run(tmp_path)
    result=w.orchestrate(**kwargs)['payload']
    result[field]='f'*64 if field=='execution_code_sha256' else {}
    with pytest.raises(ValueError,match='identity changed'):w.validate_complete(result,c.protocol())
