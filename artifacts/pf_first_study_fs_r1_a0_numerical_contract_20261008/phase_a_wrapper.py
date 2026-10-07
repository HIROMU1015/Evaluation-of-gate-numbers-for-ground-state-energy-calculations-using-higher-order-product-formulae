"""Fixed all-initial then all-cold orchestration; A0 never invokes production."""
from pathlib import Path
from a0_common import HERE, ROOT, canonical, read, require_authorization, sha
from numerical_contract import compare_condition, ritz_gate, norm_gate, echo_gate, finite, budget_interval, ratio_interval, NumericalFailure
from recovery_wrapper import save_return, publish_from_recovery
from run_lease import RunLease


def validate_pass(row, spec, p):
    if row['condition'] != spec['condition'] or row['source_identity_sha256'] != spec['source_identity_sha256']:
        raise NumericalFailure('source/condition mismatch')
    ritz_gate(row['Ritz'])
    keys = {(r['state'], float(r['time']).hex()) for r in row['proxy_rows']}
    expected = {(s, float(t).hex()) for s in ('CISD', 'Ritz8') for t in [*spec['training_absolute'], spec['t0']]}
    if len(row['proxy_rows']) != 8 or keys != expected:
        raise NumericalFailure('fixed proxy coordinates')
    for r in row['proxy_rows']:
        norm_gate(r['input_norm'], 'input')
        norm_gate(r['PF_norm'], 'PF')
        norm_gate(r['reference_norm'], 'reference')
        echo_gate(r['echo_real'], r['echo_imag'], r['reference_norm'], r['PF_norm'])
        finite(r['signed_proxy'], 'proxy')
        if r['signed_proxy'] != r['echo_imag']/r['time']:
            raise NumericalFailure('proxy/echo identity')
    from numerical_contract import arm_tau
    if set(row['estimates']) != set(p['arms']) or set(row['budgets']) != set(p['arms']):
        raise NumericalFailure('four arms required')
    for arm, prediction in row['estimates'].items():
        expected_budget = budget_interval(prediction, arm_tau(spec['condition'], arm), spec, p['constants'])
        if row['budgets'][arm] != expected_budget:
            raise NumericalFailure('uncertainty/budget derivation mismatch')
    for state, fit_arm, local_arm in (('CISD', 'M00p', 'M01p'), ('Ritz8', 'M10p', 'M11p')):
        coefficients = row['fits'][state]['coefficient_values']
        if len(coefficients) != 2:
            raise NumericalFailure('fit coefficient count')
        a4, a6 = [finite(v, 'fit coefficient') for v in coefficients]
        if row['estimates'][fit_arm] != a4*spec['t0']**4+a6*spec['t0']**6:
            raise NumericalFailure('prediction/fit identity')
        local = next(r for r in row['proxy_rows'] if r['state'] == state and r['time'] == spec['t0'])
        if row['estimates'][local_arm] != local['signed_proxy']:
            raise NumericalFailure('local prediction identity')
    return True


def validate_complete(payload, p):
    if payload['stage'] != 'FS-R1-Phase-A' or payload['truth_opened'] is not False:
        raise ValueError('truth-free Phase A required')
    if payload['protocol_sha256'] != sha((HERE/'fs_r1_protocol_v3.json').read_bytes()):
        raise ValueError('v3 result protocol changed')
    from a0_common import verify_frozen
    _, code_hash = verify_frozen()
    if payload['execution_code_sha256'] != code_hash:
        raise ValueError('result execution code identity changed')
    sources = {s['condition']: {k:s[k] for k in
        ('source_identity_sha256', 'new_H_sha256', 'operational_archive_sha256')} for s in p['systems']}
    if payload['source_hashes'] != sources:
        raise ValueError('result source identity changed')
    for category in ('initial_operational', 'cold_validation'):
        if len(payload[category]) != 2:
            raise ValueError('both conditions required')
        for row, spec in zip(payload[category], p['systems']):
            validate_pass(row, spec, p)
    if len(payload['replay']) != 2 or not all(r['all_gates_pass'] for r in payload['replay']):
        raise ValueError('complete replay required')
    for key, value in payload['truth_access'].items():
        if value != 0:
            raise ValueError('truth access')
    expected_replay = [compare_condition(a, b, s) for a,b,s in
        zip(payload['initial_operational'], payload['cold_validation'], p['systems'])]
    if payload['replay'] != expected_replay:
        raise ValueError('saved replay differs from frozen scalar comparison')
    return True


def orchestrate(specs, binding, registry, run_id, acquire, validate, compare, public_path, public_validator):
    """Injection seam for toy callback/fault tests; no production loader import."""
    lease = RunLease(registry, run_id, binding)
    completed = {'initial_operational': [], 'cold_validation': []}
    returned = False
    final_path = None
    try:
        for category in ('initial_operational', 'cold_validation'):
            for spec in specs:
                # acquire must return only scalars; private recovery is next.
                result = acquire(spec, category)
                returned = True
                save_return(lease, category+'_'+spec['condition'], result)
                validate(result, spec)
                completed[category].append(result)
            # This initial aggregate checkpoint must exist before any cold call.
            save_return(lease, category+'_complete', completed[category])
        replay = [compare(a, b, s) for a, b, s in zip(completed['initial_operational'], completed['cold_validation'], specs)]
        payload = dict(stage='FS-R1-Phase-A', truth_opened=False, protocol_sha256=binding['protocol_sha256'],
                       source_hashes=binding['source_hashes'], execution_code_sha256=binding['execution_code_sha256'],
                       **completed, replay=replay,
                       truth_access=dict(direct_truth_reads=0, branch_solves=0, truth_schur=0,
                           exact_ground_operational_reads=0, historical_truth_reads=0),
                       Phase_B_authorized=False, safety_status='PENDING_PHASE_B')
        final_path, _ = save_return(lease, 'phase_a_complete', payload)
        lease.note('science_return_completed', state='completed', scientific_return_completed=True, recovery_saved=True)
        try:
            receipt = publish_from_recovery(final_path, public_path, public_validator)
        except Exception as exc:
            lease.note('public_serialization_failed', state='completed', scientific_return_completed=True, recovery_saved=True,
                       error_type=type(exc).__name__, error=str(exc))
            raise
        lease.note('public_serialization_completed', state='completed', scientific_return_completed=True, recovery_saved=True)
        return dict(payload=payload, receipt=receipt, lease_directory=str(lease.directory), private_recovery=str(final_path))
    except Exception as exc:
        if final_path is None:
            lease.note('calculation_failed', state='failed', any_scientific_return=returned,
                       completed_conditions={k:len(v) for k,v in completed.items()}, error_type=type(exc).__name__, error=str(exc),
                       partial_action_ledger=getattr(exc, 'partial_action_ledger', None))
        raise


def execute_phase_a(authorization, run_id, public_path):
    # Must fail before creating a lease, importing backend or decoding an archive.
    p, binding = require_authorization(authorization)
    registry = Path(p['execution_wrapper']['private_lease_registry'])
    if registry.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('private lease/recovery outside repository required')
    from production_adapter import acquire_condition
    return orchestrate(p['systems'], binding, registry, run_id,
        lambda spec, category: acquire_condition(spec, category, authorization),
        lambda row, spec: validate_pass(row, spec, p), compare_condition, public_path,
        lambda payload: validate_complete(payload, p))


def recover_public(private_snapshot, public_path):
    """Serialization-only entry point: accepts no science callback or loader."""
    p = read('fs_r1_protocol_v3.json')
    from a0_common import verify_frozen
    verify_frozen()
    return publish_from_recovery(private_snapshot, public_path, lambda payload: validate_complete(payload, p))
