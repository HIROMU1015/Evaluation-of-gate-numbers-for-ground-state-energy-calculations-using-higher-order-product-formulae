"""Future v3 Phase A adapter. Imported/executed only after separate authorization.

Frozen native PF/fit and Phase05 Ritz arithmetic are reused. New code adds scalar
diagnostics/gates and intervals; cached Hpsi/HZ supply residuals without extra H.
"""
import ast
from dataclasses import dataclass
import sys
import time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply
from a0_common import ROOT, R0, require_authorization, protocol, sha
from numerical_contract import norm_gate, echo_gate, finite, ritz_gate, arm_tau, budget_interval, ratio_interval

sys.path.insert(0, str(R0))
import backend as v1
from source_io import array_identity, sparse_hash


@dataclass
class ContextV3(v1.Context):
    phase: str = 'FS-R1-A0'

    def guard(self, dimension=None):
        if self.phase == 'synthetic':
            if dimension is not None and dimension > 16:
                raise PermissionError('production dimension in synthetic context')
            return
        if self.phase != 'FS-R1-Phase-A':
            raise PermissionError('A0 and Phase B authorize no production dispatch')
        require_authorization(self.authorization)


def compatible(H, psi):
    H, psi = csr_matrix(H, dtype=np.complex128), np.asarray(psi, dtype=np.complex128)
    if H.shape != (len(psi), len(psi)) or psi.ndim != 1 or len(psi) > 1568:
        raise ValueError('fixed sector/state interface')
    if not np.isfinite(H.data).all() or not np.isfinite(psi).all():
        raise ValueError('nonfinite H/state')
    norm_gate(float(np.linalg.norm(psi)), 'input')
    anti = H-H.conj().T
    if np.linalg.norm(anti.data) > 1e-12 * max(np.linalg.norm(H.data), np.finfo(float).tiny):
        raise ValueError('inherited H Hermiticity gate')
    return H, psi


def annotated_ritz_ast(raw):
    """Pure code transformation: append private return metadata only."""
    names = {'project', 'fix_phase', 'Basis', 'build_response_basis', 'solve_ritz_state'}
    nodes = [n for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    # Annotate return dictionaries only; no arithmetic statement is replaced.
    solve = next(n for n in nodes if n.name == 'solve_ritz_state')
    for node in ast.walk(solve):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Tuple):
            diag = node.value.elts[1]
            zero = isinstance(node.value.elts[0], ast.Call)
            diag.keys.extend([ast.Constant('_coefficients'), ast.Constant('_tie_index')])
            diag.values.extend([ast.Constant(None) if zero else ast.Name(id='coeff', ctx=ast.Load()),
                                ast.Constant(None) if zero else ast.Name(id='j', ctx=ast.Load())])
    tree = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    return tree


def ritz_with_diagnostics(H, psi, context):
    context.guard(H.shape[0])
    pin = __import__('json').loads((R0/'implementation_pins.json').read_text())['ritz_math']
    raw = (ROOT/pin['path']).read_bytes()
    if sha(raw) != pin['sha256']:
        raise ValueError('changed Ritz authority')
    tree = annotated_ritz_ast(raw)
    namespace = dict(np=np, dataclass=dataclass, EPS=np.finfo(float).eps, KAPPA=64., M_VALUES=(8,), require_synthetic=compatible)
    exec(compile(tree, pin['path'], 'exec', dont_inherit=True), namespace)
    basis = namespace['build_response_basis'](H, psi, context, max_m=8)
    state, old = namespace['solve_ritz_state'](basis, 8, context)
    rank = basis.Z.shape[1]
    V = np.column_stack((basis.psi, basis.Z))
    HV = np.column_stack((basis.Hpsi, basis.HZ))
    projected = V.conj().T @ HV
    coeff = old.pop('_coefficients')
    tie_index = old.pop('_tie_index')
    pivot = int(np.argmax(np.abs(state)))
    if rank:
        raw_state = V @ coeff
        phase = np.exp(-1j*np.angle(raw_state[pivot]))
        Hstate = HV @ (phase*coeff)
    else:
        Hstate = basis.Hpsi
    diag = dict(requested_m=8, retained_rank=int(rank),
        rank_stop_index=int(rank) if basis.stopped else None,
        rank_stop_reason='prefix_rank_threshold' if basis.stopped else 'requested_rank_reached',
        projected_dimension=int(rank+1), phase_pivot_index=pivot,
        tie_resolution_branch='zero_rank_reuse_CISD' if rank == 0 else 'lowest_projected_eigenspace:e'+str(tie_index),
        rank_status='zero_rank' if rank == 0 else 'nonzero_rank',
        basis_orthogonality_residual=float(np.linalg.norm(basis.Z.conj().T@basis.Z-np.eye(rank))),
        psi_basis_orthogonality_residual=float(np.linalg.norm(basis.psi.conj()@basis.Z)),
        projected_Hermiticity_residual=float(np.linalg.norm(projected-projected.conj().T)),
        projected_H_F_norm=float(np.linalg.norm(projected)), Ritz_energy=old['lowest_energy'],
        Ritz_residual_norm=float(np.linalg.norm(Hstate-old['lowest_energy']*state)),
        Ritz_normalization=float(np.linalg.norm(state)), rank_thresholds=list(basis.attempted_thresholds),
        phase_convention='largest-magnitude component positive; first index wins ties; frozen zero-rank CISD reuse',
        phase_pivot_real=float(state[pivot].real), phase_pivot_imag=float(state[pivot].imag),
        explicit_H_matvec_count=context.counts.get('H_matvec_count', 0),
        small_Ritz_solve_count=context.counts.get('small_dense_ritz_eigh_count', 0),
        residual_uses_cached_Hpsi_HZ=True, full_H_solve=0)
    ritz_gate(diag)
    return state, diag


def proxy(source, state, t, context, state_name, category):
    context.guard(source['hamiltonian'].shape[0])
    _, state = compatible(source['hamiltonian'], state)
    start = time.perf_counter()
    before = context.counts.copy()
    native = v1.native()
    evolved, timing = native['_apply_pf_cpu'](source, source['current_m3_sequence'], t, state)
    steps = list(native['iter_s2_sequence_steps'](len(source['component_spectra']), source['current_m3_sequence']))
    context.add('PF_forward_vector_action')
    context.add('group_application', len(steps))
    context.add('group_materialization', len(set(steps)))
    if not np.isfinite(evolved).all():
        raise ValueError('nonfinite PF output')
    pf_norm = float(np.linalg.norm(evolved))
    norm_gate(pf_norm, 'PF')
    echo_start = time.perf_counter()
    reference = expm_multiply(1j*t*source['hamiltonian'], state)
    context.add('logical_exact_H_echo')
    if not np.isfinite(reference).all():
        raise ValueError('nonfinite exact-H reference')
    reference_norm = float(np.linalg.norm(reference))
    norm_gate(reference_norm, 'reference')
    echo = np.vdot(reference, evolved)
    sanity = echo_gate(float(echo.real), float(echo.imag), reference_norm, pf_norm)
    g = finite(echo.imag/t, 'proxy')
    return dict(pass_category=category, state=state_name, time=t, signed_proxy=g,
        input_norm=float(np.linalg.norm(state)), PF_norm=pf_norm, PF_norm_error=abs(pf_norm-1),
        reference_norm=reference_norm, echo_real=float(echo.real), echo_imag=float(echo.imag), **sanity,
        wall_seconds=time.perf_counter()-start, PF_wall_seconds=timing['total'],
        echo_wall_seconds=time.perf_counter()-echo_start,
        peak_RSS_bytes=context.snapshot()['classical']['peak_RSS_bytes'],
        group_applications=context.counts['group_application']-before.get('group_application', 0),
        group_materializations=context.counts['group_materialization']-before.get('group_materialization', 0))


def _acquire_condition(spec, category, context, p, binding):
    if spec not in p['systems'] or category not in ('initial_operational', 'cold_validation'):
        raise ValueError('fixed condition/pass')
    started = time.perf_counter()
    source = v1.load_registered_source(spec, context)
    if sparse_hash(source['hamiltonian']) != spec['new_H_sha256'] or source['current_m3_sequence'] != p['current_m3_sequence']:
        raise ValueError('source H/PF identity')
    identities = __import__('json').loads((R0/'new_source_identity.json').read_text())['identities']
    identity = next(i for i in identities if i['condition'] == spec['condition'])
    if array_identity(source['cisd'])['sha256'] != identity['CISD']['sha256']:
        raise ValueError('CISD byte identity')
    norm_gate(float(np.linalg.norm(source['cisd'])), 'input')
    ritz_start = time.perf_counter()
    refined, diag = ritz_with_diagnostics(source['hamiltonian'], source['cisd'], context)
    ritz_wall = time.perf_counter()-ritz_start
    rows, fits = [], {}
    native = v1.native()
    for label, state in (('CISD', source['cisd']), ('Ritz8', refined)):
        local_rows = [proxy(source, state, t, context, label, category) for t in [*spec['training_absolute'], spec['t0']]]
        rows.extend(local_rows)
        fit_start = time.perf_counter()
        points = [dict(time=r['time'], echo_imag_hartree=r['signed_proxy']) for r in local_rows[:3]]
        fit = native['_fit_proxy'](points, 'echo_imag_hartree', 3, spec['fit_scale_t_ref'], 'FS-R1-3point')
        context.add('scalar_fit')
        a4, a6 = [finite(v, 'fit coefficient') for v in fit['coefficient_values']]
        fit['signed_prediction_at_t0'] = finite(a4*spec['t0']**4+a6*spec['t0']**6, 'fit prediction')
        fit['wall_seconds'] = time.perf_counter()-fit_start
        fits[label] = fit
    estimates = dict(M00p=fits['CISD']['signed_prediction_at_t0'], M10p=fits['Ritz8']['signed_prediction_at_t0'],
                     M01p=rows[3]['signed_proxy'], M11p=rows[7]['signed_proxy'])
    budgets = {a:budget_interval(v, arm_tau(spec['condition'], a), spec, p['constants']) for a,v in estimates.items()}
    ratios = {a:ratio_interval(budgets[a], budgets['M00p']) for a in ('M01p', 'M10p', 'M11p')}
    context.wall_seconds = time.perf_counter()-started
    # Nothing returned retains source, basis, state, PF or gate arrays/cache.
    return dict(condition=spec['condition'], source_identity_sha256=spec['source_identity_sha256'],
                protocol_sha256=binding['protocol_sha256'], execution_code_sha256=binding['execution_code_sha256'],
                pass_category=category, proxy_rows=rows, fits=fits, estimates=estimates, budgets=budgets,
                prediction_only_ratios=ratios, Ritz=diag, ledger=context.snapshot(), Ritz_wall_seconds=ritz_wall,
                arm_cost_views=dict(M00p={'PF':3, 'echo':3, 'fit':1}, M01p={'PF':1, 'echo':1, 'fit':0},
                    M10p={'PF':3, 'echo':3, 'fit':1}, M11p={'PF':1, 'echo':1, 'fit':0},
                    shared_M10p_M11p_refinement={'H':diag['explicit_H_matvec_count'], 'small_Ritz':diag['small_Ritz_solve_count'],
                                               'wall_seconds':ritz_wall}),
                scientific_intermediates_retained=False)


def acquire_condition(spec, category, authorization):
    p, binding = require_authorization(authorization)
    context = ContextV3(phase='FS-R1-Phase-A', authorization=authorization)
    context.guard(spec['dimension'])
    try:
        return _acquire_condition(spec, category, context, p, binding)
    except Exception as exc:
        exc.partial_action_ledger = context.snapshot()
        raise
