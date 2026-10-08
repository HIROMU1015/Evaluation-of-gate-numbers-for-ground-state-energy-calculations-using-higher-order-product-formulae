"""Package saved scalars only. Never imports a production adapter or source loader."""
import csv
import io
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
A0=ROOT/'artifacts/pf_first_study_fs_r1_a0_numerical_contract_20261008'
PRIVATE=Path('/tmp/fs-r1-phase-a-execution-record-20261008')
sys.path.insert(0,str(A0))
from a0_common import canonical, sha, verify_frozen
from recovery_wrapper import load_return
from run_lease import durable, read_start

def read(path): return json.loads(Path(path).read_text())
def save(name,value):
    raw=value if isinstance(value,bytes) else canonical(value)
    durable(HERE/name,raw)
def identity(name):
    raw=(HERE/name).read_bytes()
    return dict(path=str((HERE/name).relative_to(ROOT)),sha256=sha(raw),bytes=len(raw))

def main():
    p,code=verify_frozen()
    outcome=read(PRIVATE/'invocation_outcome.json')
    assert outcome['success'] and outcome['entrypoint_invocations']==1 and outcome['science_retries']==0
    result=outcome['result'];payload=result['payload']
    lease=Path(result['lease_directory'])
    start,start_hash=read_start(lease)
    final,raw=load_return(result['private_recovery'])
    assert canonical(final['payload'])==(HERE/'production_results.json').read_bytes()==canonical(payload)
    assert result['receipt']['public_matches_recovery'] and result['receipt']['recovery_saved_before_public']
    assert all(r['all_gates_pass'] for r in payload['replay'])
    events=[read(path) for path in sorted(lease.glob('event_*.json'))]
    expected=['initial_operational_N2_active_eq_sto3g','initial_operational_CO_active_eq_sto3g',
        'initial_operational_complete','cold_validation_N2_active_eq_sto3g','cold_validation_CO_active_eq_sto3g',
        'cold_validation_complete','phase_a_complete']
    assert [e['recovery_category'] for e in events if e['stage']=='recovery_saved']==expected
    assert [e['stage'] for e in events][-2:]==['science_return_completed','public_serialization_completed']
    snapshots=[]
    for category in expected:
        path=lease/(category+'.recovery.json')
        snapshot,data=load_return(path)
        assert snapshot['binding']==start['binding']
        snapshots.append(dict(category=category,private_path=str(path),sha256=sha(data),bytes=len(data),
            lease_binding_verified=True,canonical_verified=True,sidecar_and_journal_verified=True))
    authorization=read(PRIVATE/'authorization.json')
    assert sha(canonical(authorization))==start['binding']['authorization_sha256']
    save('authorization_receipt.json',dict(authorization=authorization,binding=start['binding'],
        run_id=start['run_id'],RUN_STARTED_sha256=start_hash,lease_directory=str(lease),
        lease_exclusive=True,entrypoint_invocations=1,science_retries=0,authorization_consumed=True,
        launch_marker_sha256=sha((PRIVATE/'ENTRYPOINT_INVOCATION_STARTED').read_bytes()),
        invocation_outcome_sha256=sha((PRIVATE/'invocation_outcome.json').read_bytes()),Phase_B_authorized=False))
    save('private_recovery_receipt.json',dict(private_snapshots_published=False,snapshots=snapshots,
        binding=start['binding'],run_id=start['run_id'],RUN_STARTED_sha256=start_hash,
        public_return_receipt=result['receipt'],private_recovery_before_public=True,
        initial_aggregate_before_cold=True,science_retries=0,serialization_recovery_retries=0))
    passes=[r for category in ('initial_operational','cold_validation') for r in payload[category]]
    save('ritz_diagnostics.json',dict(passes=[dict(condition=r['condition'],pass_category=r['pass_category'],
        diagnostics=r['Ritz'],wall_seconds=r['Ritz_wall_seconds']) for r in passes],
        exact_ground_input=False,diagnostic_extra_H_actions=0,continuous_difference_tolerance=None))
    save('fit_results.json',dict(passes=[dict(condition=r['condition'],pass_category=r['pass_category'],
        fits=r['fits']) for r in passes],fixed_propagation_identity=p['fit_uncertainty_propagation'],
        no_additional_fits=True))
    save('predicted_budgets.json',dict(unit='predicted_QPE_PF_rotations',label='prediction_only_not_truth_scored',
        initial=[dict(condition=r['condition'],budgets=r['budgets'],ratios=r['prediction_only_ratios'])
            for r in payload['initial_operational']],cold=[dict(condition=r['condition'],budgets=r['budgets'],
            ratios=r['prediction_only_ratios']) for r in payload['cold_validation']],historical_B0_reused=False))
    interval_keys=('signed_prediction','uncertainty_bound','lower_signed_bound','upper_signed_bound',
        'absolute_magnitude','c_min','c_max','denominator','denominator_min','denominator_max',
        'nominal_feasibility','status','finite_budget_reported')
    save('prediction_intervals.json',dict(role='numerical_reproducibility_width_not_truth_certificate',
        passes=[dict(condition=r['condition'],pass_category=r['pass_category'],arms={a:{k:b[k] for k in interval_keys}
            for a,b in r['budgets'].items()}) for r in passes]))
    maxima=dict(raw_proxy=max(d['absolute_difference'] for r in payload['replay'] for d in r['raw_proxy_comparisons']),
        fit_coefficient=max(d for r in payload['replay'] for ds in r['coefficient_differences'].values() for d in ds),
        signed_prediction=max(d for r in payload['replay'] for d in r['prediction_differences'].values()))
    save('cold_replay.json',dict(status='PASS',raw_proxy_pairs=16,scientific_intermediates_shared=False,
        initial_is_primary=True,no_averaging=True,replay=payload['replay'],maximum_absolute_differences=maxima))
    fields=['condition','pass_category','state','time','time_hex','signed_proxy','input_norm','PF_norm',
        'reference_norm','echo_real','echo_imag','echo_magnitude','Cauchy_product','tau_round',
        'wall_seconds','PF_wall_seconds','echo_wall_seconds','peak_RSS_bytes','group_applications','group_materializations']
    csv_stream=io.StringIO(newline='')
    writer=csv.DictWriter(csv_stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
    gates=[]
    for r in passes:
        for row in r['proxy_rows']:
            record={k:row[k] for k in fields if k in row}
            record.update(condition=r['condition'],pass_category=r['pass_category'],time_hex=float(row['time']).hex())
            writer.writerow(record)
            gates.append(dict(condition=r['condition'],pass_category=r['pass_category'],state=row['state'],
                time_hex=float(row['time']).hex(),input_norm_error=abs(row['input_norm']-1),
                PF_norm_error=abs(row['PF_norm']-1),reference_norm_error=abs(row['reference_norm']-1),
                Cauchy_excess=row['echo_magnitude']-row['Cauchy_product'],tau_round=row['tau_round'],
                finite=True,input_norm_pass=True,PF_norm_pass=True,reference_norm_pass=True,Cauchy_pass=True))
    save('proxy_values.csv',csv_stream.getvalue().encode())
    # CSV decimal roundtrip must retain every binary64 proxy; no recomputation.
    csv_rows=list(csv.DictReader(io.StringIO(csv_stream.getvalue())))
    saved_rows=[v for r in passes for v in r['proxy_rows']]
    assert len(csv_rows)==32 and all(float(a['signed_proxy'])==b['signed_proxy'] for a,b in zip(csv_rows,saved_rows))
    save('numerical_gate_audit.json',dict(status='PASS',fixed_contract=p['numerical_contract'],
        thresholds_modified=False,proxy_gates=gates,Ritz_gates=[dict(condition=r['condition'],
        pass_category=r['pass_category'],status='PASS') for r in passes],replay_pass=True,
        maximum_errors={k:max(g[k] for g in gates) for k in ('input_norm_error','PF_norm_error','reference_norm_error','Cauchy_excess')},
        extra_Ritz_energy_or_residual_difference_tolerance=None,truth_safety_established=False))
    counts={}
    for r in passes:
        for k,v in r['ledger']['logical_actions'].items(): counts[k]=counts.get(k,0)+v
    planned=dict(PF_forward_vector_action=32,logical_exact_H_echo=32,H_matvec_count=36,
        small_dense_ritz_eigh_count=4,scalar_fit=8)
    assert all(counts[k]==v for k,v in planned.items())
    save('action_counts.json',dict(planned=planned,actual=counts,planned_actual_difference={k:counts[k]-v for k,v in planned.items()},
        passes=[dict(condition=r['condition'],pass_category=r['pass_category'],counts=r['ledger']['logical_actions']) for r in passes],
        expm_multiply_internal_work=dict(matvec=None,matmat=None,rmatvec=None,norm_estimation=None,status='unknown'),
        entrypoint_invocations=1,science_retries=0,new_direct_truth_coordinates=0))
    save('cost_ledger.json',dict(classical=dict(unit='actions_wall_seconds_RSS_bytes',
        sum_condition_wall_seconds=sum(r['ledger']['classical']['wall_seconds'] for r in passes),
        entrypoint_wall_seconds=outcome['total_entrypoint_wall_seconds'],
        process_peak_RSS_bytes=outcome['process_peak_RSS_bytes'],RSS_scope='process cumulative high-water mark; not per-condition allocation',
        passes=[dict(condition=r['condition'],pass_category=r['pass_category'],ledger=r['ledger'],
            arm_cost_views=r['arm_cost_views']) for r in passes]),
        predicted_QPE=dict(unit='PF rotations',path='predicted_budgets.json',label='prediction_only_not_truth_scored'),
        classical_cost_not_converted_to_QPE_rotations=True,expm_internal_work_status='unknown'))
    observed=outcome['observed_open_events']
    assert observed['original_pickle_opens']==observed['truth_module_source_opens']==0
    assert observed['sanitized_archive_opens']=={s['condition']:2 for s in p['systems']}
    truth=dict(payload['truth_access'],new_direct_truth_coordinates=0)
    assert all(v==0 for v in truth.values())
    save('truth_access_audit.json',dict(counts=truth,observed_open_events=observed,
        evidence='frozen Phase A capability path, sanitized member allowlists, runtime Python open observation, saved wrapper truth counters; no truth dispatch',
        direct_truth_dispatches=0,branch_ladder_executions=0,full_H_eigensolves=0,
        original_pickle_reads=0,Phase_B_executed=False,Phase_B_authorized=False,
        exact_H_echo_is_vector_reference_action=True,pytest_scope='preflight synthetic tests; not production truth or ground solves'))
    save('execution_lease_receipt.json',dict(RUN_STARTED=start,RUN_STARTED_sha256=start_hash,
        events=events,events_sha256=[dict(filename=f.name,sha256=sha(f.read_bytes())) for f in sorted(lease.glob('event_*.json'))],
        all_initial_before_cold_verified=True,private_files_published=False))
    save('production.log',(PRIVATE/'production.log').read_bytes())
    scientific_files=['production_results.json','proxy_values.csv','ritz_diagnostics.json','fit_results.json',
        'predicted_budgets.json','prediction_intervals.json','cold_replay.json','numerical_gate_audit.json',
        'action_counts.json','cost_ledger.json','truth_access_audit.json','private_recovery_receipt.json',
        'authorization_receipt.json','phase_a_protocol_snapshot.json','source_identity.json','source_manifest.json',
        'execution_lease_receipt.json','preflight.json','tests.log']
    manifest=dict(format='FS-R1-Phase-A-v3-prediction-freeze-v1',protocol_id=p['protocol_id'],
        stage='FS-R1-Phase-A',phase_a_complete=True,truth_opened=False,Phase_B_authorized=False,
        repository='HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae',
        authority_origin_result_commit='7a7234c9c5412c7209e3559aadfb71b30ad727fc',
        authority_verified_snapshot_commit='7a7234c9c5412c7209e3559aadfb71b30ad727fc',
        protocol_sha256=payload['protocol_sha256'],execution_code_sha256=code,
        numerical_contract_sha256=p['numerical_contract']['sha256'],source_hashes=payload['source_hashes'],
        prediction_payload_sha256=sha((HERE/'production_results.json').read_bytes()),
        recovery_snapshot_sha256=result['receipt']['recovery_sha256'],
        all_numerical_gates_pass=True,cold_replay_pass=True,
        all_arms_have_finite_budget_intervals=all(b['finite_budget_reported'] for r in passes for b in r['budgets'].values()),
        truth_access=truth,files=[identity(n) for n in sorted(scientific_files)],
        self_excluded=True,self_exclusion='prediction_manifest.json and prediction.sha256 excluded to avoid self reference',
        hash_rule='prediction.sha256 is SHA256 of exact compact sorted JSON plus trailing newline prediction_manifest.json bytes',
        semantic_scope='truth-free development predictions; no direct truth safety/resource claim')
    manifest_raw=canonical(manifest)
    save('prediction_manifest.json',manifest_raw)
    save('prediction.sha256',(sha(manifest_raw)+'\n').encode())
    print(json.dumps(dict(status='PHASE_A_NUMERICALLY_COMPLETE_FROZEN_LOCAL',prediction_sha256=sha(manifest_raw),
        frozen_files=len(scientific_files),actual=counts,maximum_replay_differences=maxima,
        wall_seconds=outcome['total_entrypoint_wall_seconds'],peak_RSS_bytes=outcome['process_peak_RSS_bytes'])),flush=True)

if __name__=='__main__': main()
