"""Norm/replay/interval rules; no source access or production observations."""
import math
import numpy as np
from a0_common import read

EPS = 2.220446049250313e-16
N = 1568
SCALE = 64 * EPS * N
TAU_G = 1e-11
NORM_GATES = {'input': 1e-12, 'PF': 1e-10, 'reference': 1e-10}
CATEGORIES = ('retained_rank', 'rank_stop_index', 'rank_stop_reason', 'projected_dimension',
              'phase_pivot_index', 'tie_resolution_branch', 'rank_status')


class NumericalFailure(ValueError):
    pass


def finite(value, label='scalar'):
    v = float(value)
    if not math.isfinite(v):
        raise NumericalFailure('nonfinite ' + label)
    return v


def absolute_gate(error, limit, label):
    error, limit = finite(error, label), finite(limit, 'gate')
    if error < 0 or limit < 0 or error > limit:
        raise NumericalFailure(label + ' exceeds fixed absolute gate')
    return error


def norm_gate(norm, kind):
    norm = finite(norm, kind + ' norm')
    if norm < 0:
        raise NumericalFailure('negative norm')
    return absolute_gate(abs(norm - 1), NORM_GATES[kind], kind + ' norm error')


def echo_gate(real, imag, reference_norm, pf_norm):
    norm_gate(reference_norm, 'reference')
    norm_gate(pf_norm, 'PF')
    real, imag = finite(real, 'echo real'), finite(imag, 'echo imag')
    magnitude = finite(math.hypot(real, imag), 'echo magnitude')
    product = finite(reference_norm * pf_norm, 'Cauchy product')
    tau_round = SCALE * max(product, 1.0)
    if magnitude > product + tau_round:
        raise NumericalFailure('echo Cauchy bound')
    return dict(echo_magnitude=magnitude, Cauchy_product=product, tau_round=tau_round)


def raw_replay(initial, cold):
    return absolute_gate(abs(finite(cold) - finite(initial)), TAU_G, 'raw proxy replay')


def propagation(spec):
    """Fixed linear map equivalent to H01's t/t_ref scaled OLS, no proxy input."""
    times = np.asarray(spec['training_absolute'], dtype=np.float64)
    t_ref = spec['fit_scale_t_ref']
    scaled = np.column_stack(((times / t_ref)**4, (times / t_ref)**6))
    linear, _, rank, singular = np.linalg.lstsq(scaled, np.eye(3), rcond=None)
    if rank != 2:
        raise NumericalFailure('fixed fit design must have rank 2')
    P = linear / np.asarray([t_ref**4, t_ref**6])[:, None]
    A = np.column_stack((times**4, times**6))
    q = np.asarray([spec['t0']**4, spec['t0']**6])
    w = q @ P
    factors = np.sum(np.abs(P), axis=1)
    return dict(condition=spec['condition'], training_absolute=times.tolist(), t0=spec['t0'], fit_scale_t_ref=t_ref,
                A=A.tolist(), P=P.tolist(), q=q.tolist(), w=w.tolist(), scaled_design=scaled.tolist(),
                scaled_design_singular_values=singular.tolist(), rank=int(rank),
                coefficient_uncertainty_factors=factors.tolist(),
                coefficient_uncertainty_bounds=(TAU_G * factors).tolist(),
                prediction_uncertainty_factor=float(np.sum(np.abs(w))),
                tau_fit_at_t0=float(TAU_G * np.sum(np.abs(w))),
                method='diag(t_ref^-4,t_ref^-6) lstsq(scaled_design,I3,rcond=None); same fixed linear map as H01',
                inputs='fixed coordinates only; no production proxy/fit/arm observation')


def propagation_for(condition):
    return next(r for r in read('fit_uncertainty_propagation.json')['systems'] if r['condition'] == condition)


def arm_tau(condition, arm):
    if arm not in ('M00p', 'M10p', 'M01p', 'M11p'):
        raise NumericalFailure('unknown arm')
    return propagation_for(condition)['tau_fit_at_t0'] if arm in ('M00p', 'M10p') else TAU_G


def prediction_interval(p, tau):
    p, tau = finite(p, 'prediction'), finite(tau, 'uncertainty')
    if tau < 0:
        raise NumericalFailure('negative uncertainty')
    out = dict(signed_prediction=p, uncertainty_bound=tau,
               lower_signed_bound=p-tau, upper_signed_bound=p+tau,
               absolute_magnitude=abs(p), c_min=max(0., abs(p)-tau), c_max=abs(p)+tau)
    for key, value in out.items():
        finite(value, key)
    return out


def budget_interval(p, tau, spec, constants):
    out = prediction_interval(p, tau)
    epsilon = constants['epsilon_E']
    d_min, d_max = epsilon-out['c_max'], epsilon-out['c_min']
    d = epsilon-out['absolute_magnitude']
    for value in (d_min, d_max, d):
        finite(value, 'denominator')
    out.update(denominator=d, denominator_min=d_min, denominator_max=d_max,
               nominal_feasibility='feasible' if d > 0 else 'infeasible')
    if out['c_max'] >= epsilon:
        out.update(status='NUMERICALLY_INDETERMINATE_BUDGET', nominal_budget=None,
                   B_min=None, B_max=None, finite_budget_reported=False)
    else:
        numerator = constants['gamma'] * constants['beta'] * spec['K'] / spec['t0']
        B, B_min, B_max = numerator/d, numerator/d_max, numerator/d_min
        for value in (B, B_min, B_max):
            if finite(value, 'budget') <= 0:
                raise NumericalFailure('nonpositive budget')
        out.update(status='FEASIBLE_BUDGET_INTERVAL', nominal_budget=B,
                   B_min=B_min, B_max=B_max, finite_budget_reported=True)
    return out


def budget_replay(initial, cold):
    if initial['status'] != cold['status']:
        raise NumericalFailure('budget replay status changed')
    tau = finite(initial['uncertainty_bound'], 'prediction uncertainty')
    if finite(cold['uncertainty_bound'], 'prediction uncertainty') != tau:
        raise NumericalFailure('budget replay uncertainty changed')
    absolute_gate(abs(finite(cold['signed_prediction'])-finite(initial['signed_prediction'])), tau, 'budget prediction replay')
    sign = lambda x: 0 if x == 0 else (1 if x > 0 else -1)
    for key in ('denominator', 'denominator_min', 'denominator_max'):
        if sign(finite(initial[key], key)) != sign(finite(cold[key], key)):
            raise NumericalFailure('budget denominator sign changed')
    if initial['status'] == 'NUMERICALLY_INDETERMINATE_BUDGET':
        if any(x[k] is not None for x in (initial, cold) for k in ('nominal_budget', 'B_min', 'B_max')):
            raise NumericalFailure('finite budget for indeterminate interval')
        return dict(status='STABLE_INDETERMINATE_NO_FINITE_BUDGET', finite_budget_replay_covered=False,
                    nominal_difference=None)
    for x in (initial, cold):
        for key in ('nominal_budget', 'B_min', 'B_max'):
            if finite(x[key], key) <= 0:
                raise NumericalFailure('invalid budget interval')
        if not x['B_min'] <= x['nominal_budget'] <= x['B_max']:
            raise NumericalFailure('invalid interval ordering')
    return dict(status='ANALYTICALLY_COVERED_AFTER_PREDICTION_GATE', finite_budget_replay_covered=True,
                nominal_difference=abs(cold['nominal_budget']-initial['nominal_budget']))


def ratio_interval(numerator, baseline):
    if not (numerator['finite_budget_reported'] and baseline['finite_budget_reported']):
        return dict(label='prediction_only_not_truth_scored', status='NOT_DEFINED_INDETERMINATE_BUDGET',
                    nominal=None, lower=None, upper=None)
    out = dict(label='prediction_only_not_truth_scored', status='FINITE_INTERVAL',
               nominal=numerator['nominal_budget']/baseline['nominal_budget'],
               lower=numerator['B_min']/baseline['B_max'], upper=numerator['B_max']/baseline['B_min'])
    for k in ('nominal', 'lower', 'upper'):
        finite(out[k], 'ratio')
    return out


def ritz_gate(diag):
    for key in CATEGORIES:
        if key not in diag:
            raise NumericalFailure('missing Ritz category ' + key)
    rank = diag['retained_rank']
    if type(rank) is not int or not 0 <= rank <= 8 or diag['projected_dimension'] != rank+1:
        raise NumericalFailure('Ritz rank/dimension')
    if diag['rank_status'] != ('zero_rank' if rank == 0 else 'nonzero_rank'):
        raise NumericalFailure('Ritz rank status')
    for key in ('basis_orthogonality_residual', 'psi_basis_orthogonality_residual'):
        absolute_gate(diag[key], SCALE, key)
    herm_limit = SCALE * max(finite(diag['projected_H_F_norm']), np.finfo(float).tiny)
    absolute_gate(diag['projected_Hermiticity_residual'], herm_limit, 'projected Hermiticity')
    norm_gate(diag['Ritz_normalization'], 'input')
    for key in ('Ritz_energy', 'Ritz_residual_norm'):
        finite(diag[key], key)
    if diag['Ritz_residual_norm'] < 0:
        raise NumericalFailure('negative Ritz residual')
    for v in diag['rank_thresholds']:
        finite(v, 'rank threshold')
    return True


def compare_ritz(initial, cold):
    ritz_gate(initial)
    ritz_gate(cold)
    for key in CATEGORIES:
        if initial[key] != cold[key]:
            raise NumericalFailure('Ritz categorical mismatch: ' + key)
    differences = {key:abs(cold[key]-initial[key]) for key in
                   ('Ritz_energy', 'Ritz_residual_norm', 'Ritz_normalization', 'basis_orthogonality_residual',
                    'psi_basis_orthogonality_residual', 'projected_Hermiticity_residual', 'projected_H_F_norm')}
    return dict(categorical_match=True, independent_gates_pass=True, continuous_differences=differences,
                continuous_difference_tolerance=None, downstream_proxy_replay_required=True)


def compare_condition(initial, cold, spec):
    if initial['condition'] != spec['condition'] or cold['condition'] != spec['condition']:
        raise NumericalFailure('condition replay key')
    expected_keys = {(state, float(t).hex()) for state in ('CISD', 'Ritz8') for t in [*spec['training_absolute'], spec['t0']]}
    def index(rows):
        out = {(r['state'], float(r['time']).hex()):r for r in rows}
        if len(rows) != 8 or len(out) != 8 or set(out) != expected_keys:
            raise NumericalFailure('missing/duplicate/substituted proxy coordinate')
        for row in rows:
            norm_gate(row['input_norm'], 'input')
            echo_gate(row['echo_real'], row['echo_imag'], row['reference_norm'], row['PF_norm'])
            finite(row['signed_proxy'], 'proxy')
        return out
    first, second = index(initial['proxy_rows']), index(cold['proxy_rows'])
    raw = [dict(state=k[0], time=first[k]['time'], absolute_difference=raw_replay(first[k]['signed_proxy'], second[k]['signed_proxy']))
           for k in sorted(expected_keys)]
    ritz = compare_ritz(initial['Ritz'], cold['Ritz'])
    registry = propagation_for(spec['condition'])
    coefficients = {}
    for state in ('CISD', 'Ritz8'):
        a, b = initial['fits'][state]['coefficient_values'], cold['fits'][state]['coefficient_values']
        if len(a) != 2 or len(b) != 2:
            raise NumericalFailure('two fit coefficients required')
        coefficients[state] = [absolute_gate(abs(finite(y)-finite(x)), tau, 'fit coefficient replay')
                               for x, y, tau in zip(a, b, registry['coefficient_uncertainty_bounds'])]
    prediction_diffs, budgets = {}, {}
    for arm in ('M00p', 'M10p', 'M01p', 'M11p'):
        tau = arm_tau(spec['condition'], arm)
        prediction_diffs[arm] = absolute_gate(abs(finite(cold['estimates'][arm])-finite(initial['estimates'][arm])), tau, arm+' replay')
        budgets[arm] = budget_replay(initial['budgets'][arm], cold['budgets'][arm])
    return dict(condition=spec['condition'], raw_proxy_comparisons=raw, coefficient_differences=coefficients,
                prediction_differences=prediction_diffs, Ritz=ritz, budget_replay=budgets,
                all_gates_pass=True, truth_scored=False)
