"""22 requested guards, native toy checks and saved-scalar checks.

No source decode, reconstruction or N2/CO PF/echo calls occur in these tests.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import numpy as np
import pytest
from scipy.linalg import expm

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import source_adapter as s


def load(name):
    return json.loads((HERE/name).read_text())


def all_gates():
    return {key:True for key in s.REQUIRED_GATES}


def closure():
    spec=importlib.util.spec_from_file_location('c06_native_toy',ROOT/'artifacts/pf_first_study_fs_c05_execution_closure_20261007/closure_adapter.py')
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


def toy_export():
    # Deliberately contaminate input dictionaries with oracle fields.
    system=dict(hamiltonian='toy_H',component_spectra='toy_groups',restricted_basis='toy_basis',
                states={'cisd':'toy_CISD','exact_ground':'forbidden'},
                state='forbidden_ground_vector',energy='forbidden_oracle',
                direct_PF_truth='forbidden_direct',exact_gap='forbidden_gap')
    metadata={k:('allowed-'+k) for k in s.METADATA_KEYS}
    metadata.update(removed_constant_hartree=0.,exact_ground_overlap='forbidden',
                    branch_truth='forbidden',old_success_label=True)
    return s.sanitized(system,metadata,load('validation_contract.json')['current_m3_sequence'],all_gates())


def test_01_whole_pickle_mismatch_is_not_sufficient_to_reject():
    gates=all_gates(); gates['whole_pickle_match']=False
    assert s.accept(gates)
    assert not s.accept(load('candidate_source_audit.json')['systems'][0]['gates'])


def test_02_H_hash_mismatch_rejects_despite_other_gates():
    gates=all_gates(); gates['H_exact_SHA']=False
    assert not s.accept(gates)
    for row in load('reconstruction_audit.json')['systems']:
        assert row['actual_identities']['hamiltonian_sha256']!=row['expected_H_sha256']
        with pytest.raises(PermissionError): s.sanitized({}, {}, [], row['gates'])


def test_03_ordered_group_reorder_rejects():
    groups=load('historical_fingerprint_registry.json')['systems'][0]['historical_metadata']['group_sha256']
    changed=groups[::-1]
    assert sorted(groups)==sorted(changed)
    gates=all_gates()
    gates['ordered_groups']=s.digest(s.canonical(groups))==s.digest(s.canonical(changed))
    assert not s.accept(gates)


def test_04_sector_mismatch_rejects():
    gates=all_gates(); gates['metadata_sector']=False
    assert not s.accept(gates)
    # Rejected sector cannot export even if all arrays were present.
    with pytest.raises(PermissionError): s.sanitized({}, {}, [], gates)


def test_05_CISD_diagnostic_mismatch_rejects():
    tolerance=load('validation_contract.json')['state_absolute_tolerance']
    gates=all_gates(); gates['CISD_fingerprints']=1.001*tolerance<=tolerance
    assert not s.accept(gates)
    gates['CISD_fingerprints']=None
    assert not s.accept(gates)


def test_06_M00_proxy_mismatch_rejects():
    tolerance=load('validation_contract.json')['proxy_absolute_tolerance_hartree']
    gates=all_gates(); gates['M00_proxy']=2*tolerance<=tolerance
    assert not s.accept(gates)
    gates['M00_proxy']=None
    assert not s.accept(gates)


def test_07_M00_fit_mismatch_rejects():
    gates=all_gates(); gates['M00_fit']=False
    assert not s.accept(gates)
    assert all(row['coefficient_difference'] is None for row in load('M00_reproduction.json')['systems'])


def test_08_pinned_configuration_immutable():
    expected=load('validation_contract.json')['reconstruction']
    assert s.check_pinned(copy.deepcopy(expected),expected)
    actual=copy.deepcopy(expected); actual['solver']='different SCF solver'
    with pytest.raises(ValueError,match='configuration'): s.check_pinned(actual,expected)


def test_09_second_tuning_reconstruction_prohibited(tmp_path):
    marker=tmp_path/'attempt.json'; config=load('validation_contract.json')['reconstruction']
    s.one_attempt(marker,config)
    original=marker.read_bytes()
    with pytest.raises(FileExistsError): s.one_attempt(marker,{**config,'solver':'tuned'})
    assert marker.read_bytes()==original
    assert load('reconstruction_audit.json')['attempts_per_condition']==1


def test_10_validation_ground_cannot_enter_export():
    export=toy_export()
    assert 'state' not in export and 'energy' not in export and 'states' not in export
    assert export['cisd']=='toy_CISD'
    assert s.assert_sanitized(export)


def test_11_truth_fields_stripped_by_allowlist():
    export=toy_export()
    assert set(export)==s.EXPORT_KEYS
    assert set(export['metadata'])==s.METADATA_KEYS
    assert 'forbidden' not in repr(export)
    poisoned=copy.deepcopy(export); poisoned['metadata']['branch_truth']='unsafe'
    with pytest.raises(ValueError): s.assert_sanitized(poisoned)


def test_12_arbitrary_complex_vector_native_PF():
    a=closure(); backend,_=a.fixture()
    vector=np.exp(1j*np.arange(2))/np.sqrt(2)
    expected=vector.copy(); Z=np.diag([1.,-1.]); X=np.array([[0.,1.],[1.,0.]])
    for weight in backend.sequence:
        for H,w in [(Z,weight/2),(X,weight),(Z,weight/2)]:
            expected=expm(1j*0.137*w*H)@expected
    got=backend.forward(vector,0.137)
    assert got.dtype==np.complex128
    np.testing.assert_allclose(got,expected,rtol=0,atol=2e-14)
    assert abs(np.linalg.norm(got)-1)<1e-12


def test_13_echo_sign_native_toy():
    a=closure(); backend,vector=a.fixture(); t=0.2
    evolved=backend.forward(vector,t)
    expected=np.vdot(vector,expm(-1j*t*backend.H.toarray())@evolved).imag/t
    got=backend.proxy(vector,t)['proxy']
    assert got==pytest.approx(expected,abs=4e-15)
    wrong=np.vdot(vector,expm(1j*t*backend.H.toarray())@evolved).imag/t
    assert abs(wrong-got)>1e-2


def test_14_cold_replay_toy_and_source_identity_scope():
    a=closure(); first,v=a.fixture(); second,v2=a.fixture()
    assert first is not second and first.H is not second.H
    assert first.proxy(v,0.2)==second.proxy(v2,0.2)
    audit=load('cold_replay_audit.json')
    assert all(r['identity_replay_pass'] and not r['target_match'] for r in audit['systems'])
    assert all(r['PF'].startswith('NOT_RUN') and r['proxy_difference'] is None for r in audit['systems'])


def test_15_saved_three_point_CISD_proxy_consistency():
    # Saved scalar consistency only. Actual N2/CO proxy replay is blocked by H rejection.
    registry=load('historical_fingerprint_registry.json')
    for system in registry['systems']:
        row=system['M00']; assert len(row['times'])==3
        proxies=np.array(row['saved_echo_imaginary'])/np.array(row['times'])
        np.testing.assert_allclose(proxies,row['saved_proxy_values'],rtol=0,atol=1e-21)
        assert row['times']==system['baseline']['historical_training_absolute']
    assert load('M00_reproduction.json')['status']=='NOT_RUN_H_EXACT_SHA_REJECTION'


def test_16_saved_historical_coefficients_prediction_budget():
    a=closure(); protocol=load('fs_c1_protocol_v3.json'); assert a.baseline_gate(protocol)
    for system in load('historical_fingerprint_registry.json')['systems']:
        row=system['M00']
        fitted=a.historical_scalar_fit(row['times'],row['saved_proxy_values'],row['t_ref'],row['t0'])
        np.testing.assert_allclose(fitted['coefficient_values'],row['saved_coefficients'],rtol=0,atol=1e-15)
        assert fitted['signed_prediction_at_t0']==pytest.approx(row['saved_signed_prediction'],abs=1e-16)
        c=protocol['constants']; b=c['gamma']*c['beta']*system['baseline']['K']/(row['t0']*(c['epsilon_E']-abs(fitted['signed_prediction_at_t0'])))
        assert b==pytest.approx(row['saved_B0'],rel=1e-13)
    assert protocol['M11_primary'] and protocol['M01_challenger'] and not protocol['science_authorized']


def test_17_source_validation_and_C1_costs_separate():
    counts=load('cost_ledger.json')['counts']
    assert counts['source_validation_action_count']==counts['source_reconstruction_validation_action_count']+counts['source_identity_audit_pass_count']+counts['preliminary_schema_source_loads']+counts['preliminary_identity_source_loads']==14
    assert counts['total_source_loads']==counts['audited_source_loads']+counts['preliminary_schema_source_loads']+counts['preliminary_identity_source_loads']==12
    assert counts['FS_C1_science_action_count']==counts['new_direct_truth']==0
    assert counts['validation_ground_solve_calls']==2
    assert counts['backend_validation_PF_forward']==counts['logical_exact_H_echo']==0


def test_18_unknown_expm_work_remains_null():
    ledger=load('cost_ledger.json')
    assert all(value is None for value in ledger['expm_multiply_internal'].values())
    assert ledger['construction_internal_H_work'] is None
    assert ledger['preliminary_source_loads']['wall_seconds'] is None


def test_19_wall_RSS_environment_recorded():
    ledger=load('cost_ledger.json')
    for row in ledger['reconstruction_resources']:
        assert row['wall_seconds']>0 and row['peak_RSS_bytes']>0 and not row['technical_failure']
    contract=load('validation_contract.json')['reconstruction']
    assert ledger['threads']==contract['threads'] and ledger['software']==contract['packages']
    assert ledger['python']==contract['python']


def test_20_direct_truth_absent_and_injection_rejected():
    export=toy_export(); assert 'direct_PF_truth' not in export
    export['direct_PF_truth']=0
    with pytest.raises(ValueError): s.assert_sanitized(export)
    audit=load('truth_access_audit.json')
    assert not audit['FS_C1_truth_files_loaded'] and not audit['historical_truth_files_used_for_equivalence']


def test_21_exact_ground_absent_and_no_real_export():
    export=toy_export(); assert 'exact_ground' not in export
    export['exact_ground']='forbidden'
    with pytest.raises(ValueError): s.assert_sanitized(export)
    audit=load('sanitization_audit.json')
    assert not audit['exact_ground_vector_exported'] and audit['operational_export_count']==0


def test_22_Phase_B_scorer_not_callable():
    runner=Mock(side_effect=AssertionError('no scorer/truth call allowed'))
    with pytest.raises(PermissionError,match='Phase B/scorer'): s.forbid_c1_truth(runner)
    runner.assert_not_called()
    assert load('GO_NO_GO_FOR_FS_C1.json')['status']=='NO_GO_RECONSTRUCTION_MISMATCH'
    assert not load('fs_c1_protocol_v3.json')['execution_ready']
