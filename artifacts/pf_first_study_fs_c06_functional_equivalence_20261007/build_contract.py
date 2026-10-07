"""Freeze source-validation inputs before decoding candidates or taking actions."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '75fe0d65a2940f160ea42f6414fc2246d67bd0cf'
H01 = '568f00249abb5b89ae3e6bb39cb4af87ed8581bd'
H02 = '16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe'
CONSTRUCTION = 'e0692a83b06cd2660804f70618b142bc39b6209b'
sources = []


def source(path, snapshot, origin=None):
    raw = subprocess.check_output(['git', 'show', f'{snapshot}:{path}'], cwd=ROOT)
    if origin is None:
        origin = subprocess.check_output(['git', 'log', '--diff-filter=A', '--format=%H',
                                         snapshot, '--', path], cwd=ROOT, text=True).splitlines()[-1]
    sources.append(dict(path=path, origin_result_commit=origin,
                        verified_snapshot_commit=snapshot, sha256=hashlib.sha256(raw).hexdigest()))
    return json.loads(raw)


def write(name, value):
    path = HERE / name
    if path.exists():
        raise RuntimeError('Contract already exists; no result-driven overwrite: ' + name)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    prefix = 'artifacts/pf_first_study_fs_c05_execution_closure_20261007/'
    baseline = source(prefix + 'baseline_contract.json', BASE, BASE)
    fixture = source(prefix + 'saved_scalar_fixture.json', BASE, BASE)
    v2 = source(prefix + 'fs_c1_protocol_v2.json', BASE, BASE)
    for name in ['README.md', 'GO_NO_GO_FOR_FS_C1.json', 'source_recovery_audit.json',
                 'backend_reproduction_preflight.json']:
        path = prefix + name
        if name.endswith('.json'):
            source(path, BASE, BASE)
        else:
            raw = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
            sources.append(dict(path=path, origin_result_commit=BASE,
                                verified_snapshot_commit=BASE, sha256=hashlib.sha256(raw).hexdigest()))
    h02proto = source('review_response/h02_finite_time_controlled_state_protocol.json', H02,
                      'a228b5f357c73b8e4978fc19253b2885c40df6b6')
    server = source('artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/audit.json',
                    H02, H02)
    rows = []
    for base, saved in zip(baseline['systems'], fixture['systems'], strict=True):
        condition = base['condition']
        p = 'artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/'
        metadata = source(p + f'cache/{condition}.metadata.json', H01, H01)
        echo = source(p + f'echo/{condition}__current_m3.json', H01, H01)
        # Only echo/proxy fingerprints, never direct_reference_model or sanity truth.
        echo_fingerprint = {'times': [r['time'] for r in echo['states']['cisd']],
                            'proxy': [r['echo_imag_hartree'] for r in echo['states']['cisd']]}
        rows.append(dict(condition=condition, baseline=base, M00=saved,
                         historical_metadata=metadata['system'],
                         historical_environment=metadata['environment'],
                         H01_CISD_echo_fingerprint=echo_fingerprint,
                         server_H02_reconstruction_attestation=next(r for r in server['reconstruction']
                                                                  if r['condition'] == condition),
                         server_H02_echo_attestation=next(r for r in server['exact_echo_reproduction']
                                                         if r['condition'] == condition and
                                                         r['formula'] == 'current_m3')))
    tolerance = h02proto['evaluation']
    contract = dict(
        contract_id='FS-C0.6-functional-equivalence-v1', fixed_before_decode=True,
        source_acceptance_contract='functional_equivalence', historical_source_status='missing',
        metadata_absolute_tolerance_hartree=tolerance['reconstruction_metadata_absolute_tolerance_hartree'],
        state_absolute_tolerance=tolerance['reconstruction_state_diagnostic_absolute_tolerance'],
        proxy_absolute_tolerance_hartree=tolerance['exact_echo_reproduction_absolute_tolerance_hartree'],
        norm_absolute_tolerance=1e-10,
        selected_prediction_absolute_tolerance_hartree=1e-9,
        fit_coefficient_bound='propagate the frozen 1e-9 proxy bound through the historical scaled OLS linear map; add binary64 roundoff 2e-14 relative',
        additional_gate_rationale='Norm 1e-10 is the historical H02 scalar-invariance tolerance. Selected prediction bound reuses the historical 1e-9 Ha metadata/echo bound, rather than allowing a large extrapolation error hidden by coefficient uncertainty. Budget bound is propagated from this prediction bound, without tuning.',
        cold_replay_proxy_tolerance_hartree=1e-9,
        source_gates=['H_exact_SHA', 'metadata_sector', 'ordered_groups', 'CISD_fingerprints',
                      'M00_proxy', 'M00_fit', 'echo_contract', 'cold_replay'],
        group_gate='Keep all group/batch/index orders. Compare historical ordered group and term-count attestations; numerical content requires independently hash-linked group content or pinned reconstruction against it. Sum-H alone is insufficient.',
        current_m3_sequence=baseline['current_m3_sequence'],
        existing_candidates={
            'N2_active_eq_sto3g': dict(path='/tmp/h02-finite-hQfmVi/artifacts/h02_finite_time_controlled_state_20260922_568f002/server_only_cache/N2_active_eq_sto3g.pkl',
                                     whole_file_sha='401308552bf924ba4cc8c4367676f9e092f2b44919b4753d9bc06411fe0f66de'),
            'CO_active_eq_sto3g': dict(path='/tmp/h02-finite-hQfmVi/artifacts/h02_finite_time_controlled_state_20260922_568f002/server_only_cache/CO_active_eq_sto3g.pkl',
                                     whole_file_sha='b7fb3fda2a15483fe8ef1754b1f9140683a94ab75f4a4990989fad5bcc40cbe6')},
        validation_schedule=dict(M00_CISD_points=3, cold_independent_passes=2,
                                 arbitrary_complex_vector='deterministic exp(i*j)/sqrt(d), same first training time, initial/cold; no Ritz',
                                 optional_exact_ground_echo_points=0,
                                 component_content_checks='identity audit only; no new PF eigenvalue truth'),
        maximum_reconstruction_per_condition=1, reconstruction_only_after_candidate_failure=True,
        stop='Publish FS-C0.6 then stop; no FS-C1 actions even with GO',
        reconstruction=dict(code_revision=CONSTRUCTION, python='3.12.3',
                            interpreter='/home/abe/myproject/pf_external_cache/venv_f_hf_retry1_py312/bin/python',
                            packages={k: importlib.metadata.version(k) for k in
                                      ['numpy', 'scipy', 'pyscf', 'openfermion', 'qiskit', 'qiskit-aer']},
                            threads={'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                                     'MKL_NUM_THREADS': '1'}, component_processes=1,
                            random_seed=None, solver='unaltered historical prepare_condition',
                            geometry_and_sector='historical_metadata per condition; no modifications',
                            no_second_tuning_attempt=True))
    write('historical_fingerprint_registry.json', dict(sources=sources, systems=rows,
                                                      truth_files_loaded=False))
    write('source_manifest.json', dict(sources=sources, private_binary_publication=False,
                                      origin_and_verified_snapshot_separate=True))
    write('validation_contract.json', contract)
    v3 = json.loads(json.dumps(v2))
    v3.update(protocol_id='FS-C1-20261007-v3', stage='FS-C0.6 source reconstruction validation',
              historical_source_status='missing', source_acceptance_contract='functional_equivalence',
              M00_historical_reference='immutable', operational_source_kind='pending until audit',
              historical_training='3-point', M11_primary=True, M01_challenger=True,
              science_authorized=False, execution_ready=False, stop=contract['stop'])
    v3.pop('truth_barrier', None)
    v3['truth_barrier'] = dict(FS_C1_direct_truth_access=False, Phase_B_scorer_callable=False,
                              all_source_export_fields_allowlisted=True)
    for system in v3['systems']:
        system.pop('truth_branch_id', None)
    v3['gates']['baseline_reproduction_bound_hartree'] = 1e-9
    v3['gates']['echo_numeric_uncertainty_contract'] = 'validation_contract.json; no operational safety certificate inferred'
    write('fs_c1_protocol_v3.json', v3)
    print('Contracts and authority registry frozen; no candidate decoded.')


if __name__ == '__main__':
    main()
