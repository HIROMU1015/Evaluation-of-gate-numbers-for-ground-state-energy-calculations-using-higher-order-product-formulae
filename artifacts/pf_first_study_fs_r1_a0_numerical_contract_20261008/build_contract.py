"""A0: fixed-coordinate linear propagation and metadata freeze only."""
import copy
import json
from pathlib import Path
from a0_common import HERE, ROOT, R01, canonical, sha, execution_paths
from numerical_contract import EPS, N, SCALE, TAU_G, CATEGORIES, propagation


def write(name, value):
    raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n'
    with (HERE/name).open('x') as f:
        f.write(raw)


def main():
    v2 = json.loads((R01/'fs_r1_protocol_v2.json').read_text())
    propagated = dict(kind='fixed_design_uncertainty_propagation', raw_proxy_tau_Ha=TAU_G,
                      production_observations=0, systems=[propagation(s) for s in v2['systems']])
    write('fit_uncertainty_propagation.json', propagated)
    numerical = dict(contract_id='FS-R1-production-numerical-v1', frozen_on='2026-10-08',
        machine_epsilon=EPS, sector_dimension=N, precision_multiplier=64, inherited_scale=SCALE,
        input_state_norm_abs=1e-12, pf_output_norm_abs=1e-10, exact_h_reference_norm_abs=1e-10,
        norm_definition='abs(l2_norm-1), inclusive <=; no hidden renormalization or rtol/ULP allowance',
        echo_round_rule='64 epsilon_mach N max(reference_norm PF_norm,1)',
        echo_round_derivation='64 eps N uses inherited guard factor; exceeds gamma_(8N)=8N eps/(1-8N eps) for complex-dot arithmetic at N=1568; max(product,1) fixes a unit norm scale floor',
        echo_round_scale=SCALE, complex_dot_gamma_8N=(8*N*EPS)/(1-8*N*EPS),
        raw_proxy_replay_abs_hartree=TAU_G, raw_proxy_replay_relative=None,
        raw_proxy_pairs=16, replay_bound_role='reproducibility only; not truth/model bias, fit residual or resource eta',
        fit_uncertainty='analytic_linear_propagation', coefficient_rule='tau_g sum_i abs(P_ji)',
        prediction_rule='tau_g sum_i abs((q P)_i)', independent_fit_tolerance=None,
        coefficient_replay_gate='required diagnostic; every derived coefficient bound and prediction gate must pass',
        local_prediction_tau_Ha=TAU_G, budget_uncertainty='prediction_interval_propagation',
        magnitude_interval='[max(0,abs(p)-tau_p),abs(p)+tau_p]',
        near_infeasible='c_max >= epsilon_E', near_infeasible_status='NUMERICALLY_INDETERMINATE_BUDGET',
        near_infeasible_finite_budget=False, clipping=False,
        budget_interval='B_min=gamma beta K/[t0(epsilon-c_min)]; B_max=gamma beta K/[t0(epsilon-c_max)]',
        independent_budget_absolute_tolerance=None, independent_budget_relative_tolerance=None,
        budget_replay='prediction replay passes; finite intervals analytically covered; status or any denominator sign change/nonfinite fails',
        both_indeterminate='preserve null budgets and stable indeterminate status; finite-budget replay coverage remains false; no scientific budget interpretation',
        ratio_interval='[B_arm_min/B0_max,B_arm_max/B0_min]; prediction_only_not_truth_scored',
        ritz_categorical_replay='exact_match', ritz_categories=list(CATEGORIES),
        ritz_continuous_gates='inherited_64_eps_N_rules', ritz_continuous_difference_tolerance=None,
        ritz_energy_residual_replay='record differences; independent gates + categories + downstream proxies determine acceptance',
        phase_A_order='all_initial_conditions_then_all_cold_replays',
        execution_order=['N2 initial','CO initial','initial aggregate scalar recovery','N2 cold','CO cold'],
        nonfinite_policy='immediate numerical failure; null indeterminate budgets are intentional undefined values, never Inf',
        science_authorized=False, Phase_B_authorized=False)
    write('fs_r1_numerical_contract_v1.json', numerical)
    v3 = copy.deepcopy(v2)
    v3.update(protocol_id='FS-R1-20261007-v3', stage='FS-R1-A0 numerical-contract freeze',
              frozen_on='2026-10-08', supersedes_protocol_id=v2['protocol_id'],
              supersedes_commit='4e5c3ba2e3497915cd1668d9ac5cd77640ab2938',
              revision_reason='close physical-production replay/norm acceptance contract before any Phase A observation',
              FS_R1_science_authorized=False, final_preflight_status='pending tests',
              execution_ready=False, approved_status_amendment='numerical_contract_amendment.md')
    for field, name in (('numerical_contract','fs_r1_numerical_contract_v1.json'), ('fit_uncertainty_propagation','fit_uncertainty_propagation.json')):
        v3[field] = dict(path=str((HERE/name).relative_to(ROOT)), sha256=sha((HERE/name).read_bytes()))
    v3['execution_wrapper'] = dict(order=numerical['execution_order'],
        entrypoint=str((HERE/'phase_a_wrapper.py').relative_to(ROOT))+':execute_phase_a',
        private_lease_registry='/tmp/fs-r1-phase-a-production-private-20261008/leases',
        lease_key='SHA256(authorization_id), independent of run_id; all existing states forbid reuse',
        authorization='separate explicit Phase A authorization with actual v3 protocol and complete execution-code hash',
        recovery='per-condition immediate scalar recovery, then all-initial aggregate recovery before cold; final recovery before public validation',
        retry='serialization-only from private snapshot; no production retry from the same authorization',
        Phase_A_authorized_in_A0=False, Phase_B_authorized=False)
    v3['arm_budget_definition'] = 'new v3 uncertainty interval; c_max>=epsilon => NUMERICALLY_INDETERMINATE_BUDGET/null; nominal only when c_max<epsilon; no clipping'
    v3['phase_B'] = v2['phase_B']+'; v3 prediction/code/numerical binding requires separately reviewed Phase B barrier extension'
    write('fs_r1_protocol_v3.json', v3)
    bundle = dict(format='FS-R1-A0-execution-code-v1', sha256={p:sha((ROOT/p).read_bytes()) for p in execution_paths()})
    write('execution_code_identity.json', bundle)
    actions = json.loads((R01/'predicted_action_budget_v2.json').read_text())
    actions.update(protocol_id=v3['protocol_id'], stage='FS-R1-A0', actual_FS_R1_actions=0, planned_only=True,
                   wrapper_extra_H_matvec=0, cached_H_ritz_residual=True, source_loads_phase_A=4,
                   production_authorized_in_A0=False)
    write('predicted_action_budget_v3.json', actions)
    docs = {
        'numerical_contract_amendment.md': '''# Approved numerical amendment

User attachment §5–31 fixes vector-norm/replay/propagation rules before observations.
v3 is additive; v1/v2 and historical artifacts remain unchanged. No production execution is authorized by A0.
The new budget interval/indeterminate rule supersedes v2's nominal-only feasibility rule for Phase A numerical reporting.
Sources, coordinates, current_m3, group order, Ritz8 arithmetic, H01 fit, epsilon/beta/gamma/eta, arm roles and truth ladder are unchanged.
The phase-B resource target is unchanged; indeterminate budgets cannot support a gain claim.
v3 binds the new numerical contract and exact fixed-design propagation bytes. A later Phase B approval must also update its v2-only blob barrier for v3; A0 does not enable Phase B.
''',
        'norm_contract.md': '''# Vector norm and echo contract

Input |l2 norm−1|≤1e-12; PF output and exact-H reference |l2 norm−1|≤1e-10. Inclusive comparisons use the computed binary64 norm error, with no hidden renormalization, rtol or extra ULP slack.
The future adapter adds the requested norm gate instead of retaining v1's stricter squared-norm predicate. The Phase05 MGS/Ritz arithmetic is unchanged; no invalid state is normalized away.
Reference exp(+iHt)psi is the bra representation of the exp(−iHt) echo. Both evolutions have the same mathematical norm; sign convention is unchanged.
Echo real/imag/magnitude must be finite. Cauchy bound uses tau_round=64 eps N max(norm_reference norm_PF,1), frozen before any observation.
At N=1568 this inherited guard scale exceeds gamma_(8N)=8N eps/(1−8N eps), the standard conservative complex-dot accumulation scale. It audits arithmetic sanity, not propagation error or truth.
''',
        'replay_contract.md': '''# Complete cold replay

Compare 16 raw proxy pairs: 3 CISD training +3 Ritz training +CISD t0 +Ritz t0 per condition.
Primary rule is |cold−initial|≤1e-11 Ha, including equality; rtol is absent, including near zero.
Fit coefficients and predictions use only frozen P/qP L1 bounds. Every derived coefficient diagnostic and prediction gate must pass; conflicting diagnostics fail closed.
Ritz categories match exactly. Each pass independently passes inherited gates. Energy/residual/other continuous differences are saved without an independent difference threshold; downstream proxies must pass.
Initial result stays primary. No averaging, extra replay, coordinate/rank/source/backend rescue or tolerance adjustment.
This tolerance concerns reproducibility and does not certify bias, direct truth or resource success.
''',
        'budget_uncertainty_contract.md': '''# Prediction and budget intervals

Signed interval [p−tau,p+tau], magnitude [max(0,|p|−tau),|p|+tau], denominator [epsilon−c_max,epsilon−c_min].
When c_max≥epsilon, status NUMERICALLY_INDETERMINATE_BUDGET and nominal budget/B_min/B_max are null. No clipping or nominal feasibility rescue.
Otherwise B_min=gamma beta K/[t0(epsilon−c_min)], B_max=gamma beta K/[t0(epsilon−c_max)], nominal uses |p|. Every finite value must remain finite/positive.
Budget replay has no separate atol/rtol. After prediction replay passes, both finite intervals are analytically covered. Status changes, nonfinite intervals, or any nominal/min/max denominator sign change fail.
If both passes remain indeterminate with unchanged denominator signs, preserve undefined budgets, mark finite-budget coverage false, and make no budget/resource interpretation. Intentional null is not NaN/Inf.
Ratio interval [B_arm_min/B0_max,B_arm_max/B0_min] exists only for positive finite intervals and is labelled prediction_only_not_truth_scored.
''',
        'ritz_replay_contract.md': '''# Ritz8 replay

Keep complex128, exactly two MGS passes, prefix rejection, no replacement/rescue, rank≤8 and projected dimension≤9.
Keep rank thresholds 64 eps N max(||Hpsi||,|E|,tiny) and 64 eps N max(||Hz_previous||,||B_previous||,|E|,tiny).
Independent gates: ||Z†Z−I||_F and ||psi†Z||_2≤64 eps N; projected anti-Hermitian norm≤64 eps N max(||Hm||_F,tiny).
Categories match exactly: retained rank, rejection index/reason, projected dimension, phase pivot, lowest-eigenspace tie projection branch, zero/nonzero status.
Rejected direction index is zero-based (=accepted rank). No rejection gives null index/requested_rank_reached. Zero-rank reuses original CISD as in frozen Phase05; tie label zero_rank_reuse_CISD.
Nonzero state uses largest-magnitude pivot positive, first index ties; projected tie uses e0,e1,... as inherited.
AST annotations expose the already chosen small coefficients/tie index privately without replacing arithmetic. Cached Hpsi/HZ compute the Ritz residual with no new H action. No coefficients, basis or vector are published.
Continuous differences are diagnostics without a new hand-set energy/residual tolerance. Categories + independent gates + downstream proxies determine replay acceptance.
''',
        'phase_a_orchestration.md': '''# Fixed future Phase A execution order

N2 initial → CO initial → initial aggregate scalar recovery → N2 cold → CO cold.
Per-condition scalar recovery is immediate after each return and precedes numerical/public schema processing; aggregate initial recovery is durable before any cold callback.
Acquire only scalars; independent callback invocations reload source and reconstruct basis/state/native caches/PF/echo/fit/budget. The returned object retains no scientific intermediate.
No code path selects CO using an N2 scientific value. Numerical/technical exceptions can abort; infeasible/indeterminate scientific magnitudes do not skip CO.
All cold calculations follow successful initial conditions. Actual consumed actions are saved per pass/system; no extra H for Ritz diagnostics.
A0 uses scalar mock callbacks/fault injection, not actual N2/CO arrays or kernels. Production entry rejects missing authorization before importing a backend, creating a lease or decoding source.
''',
        'run_lease_contract.md': '''# Authorization-keyed exclusive lease

Private registry is frozen in v3. Atomic mkdir keyed by SHA256(authorization_id) and create-only/fsync RUN_STARTED hold run ID, authorization/protocol/source/code hashes, UTC time, pid and host.
Changing run ID cannot reuse authorization. Every existing lease directory blocks another run, including failed/partial/serialization-failed/completed states. A0 consumes no production authorization/lease.
RUN_STARTED is immutable; create-only durable stage events distinguish calculation started, scientific return, recovery saved, science completed, public serialization failed/completed and publication complete.
Incomplete directory creation/fsync remains conservatively consumed. No lease deletion, retry or rollback is part of the API.
Publication completion requires independent remote proof. Public/schema failure after science completion leaves science state completed; only serialization recovery is allowed.
These are workflow guards, not authentication against arbitrary Python or manual private-file deletion.
''',
        'recovery_contract_v2.md': '''# Scalar recovery v2

Return → inherited C0 scalar canonicalization → create-only private snapshot+SHA256/fsync → lease digest event → public/numerical schema validation.
Per-condition/aggregate/final snapshots bind RUN_STARTED SHA/run ID/authorization/protocol/full code/source identities and retain raw proxies, coefficients, uncertainty intervals, budgets, Ritz diagnostics/ranks, actions and wall/RSS.
Arrays, states, matrices, unitary and oracle keys are rejected; only scalar lists/dicts cross the private boundary. Private snapshots stay outside the repository.
Public failure cannot invoke acquisition again. Serialization-only recovery verifies canonical bytes/hash, immutable lease bindings, journal digest and current code/protocol before validating/writing the exact payload bytes.
If science/normalization or recovery itself fails, the authorization remains consumed. No rescue or science restart. Publication retries use saved bytes and cannot create a new science lease.
'''
    }
    for name, value in docs.items():
        write(name, value)
    print(json.dumps(dict(protocol_id=v3['protocol_id'], propagation=[{'condition':s['condition'], 'tau_fit':s['tau_fit_at_t0']} for s in propagated['systems']],
                          production_actions=0, truth_access=0)), flush=True)


if __name__ == '__main__':
    main()
