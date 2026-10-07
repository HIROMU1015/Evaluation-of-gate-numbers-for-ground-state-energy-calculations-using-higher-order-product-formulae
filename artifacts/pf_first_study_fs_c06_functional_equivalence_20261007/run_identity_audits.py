"""Audit rejected candidates and one-shot reconstruction, with fresh-load replay."""
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import time
from source_adapter import identity_audit, digest

HERE = Path(__file__).resolve().parent
PRIVATE = Path('/tmp/fs-c06-validation-private-20261007')


def main():
    started = time.perf_counter()
    contract = json.loads((HERE/'validation_contract.json').read_text())
    registry = json.loads((HERE/'historical_fingerprint_registry.json').read_text())
    result = {'candidate': [], 'reconstruction': [], 'cold_replay': []}
    for fingerprint in registry['systems']:
        condition = fingerprint['condition']
        for reconstructed in [False, True]:
            path = PRIVATE/(condition+'_reconstructed_validation.pkl') if reconstructed else Path(contract['existing_candidates'][condition]['path'])
            first = identity_audit(path, fingerprint, contract, reconstructed=reconstructed,
                                   private_dir=PRIVATE, pass_name='initial')
            cold = identity_audit(path, fingerprint, contract, reconstructed=reconstructed,
                                  private_dir=PRIVATE, pass_name='cold')
            same = first['actual_identities'] == cold['actual_identities'] and first['gates']==cold['gates']
            result['reconstruction' if reconstructed else 'candidate'].append(first)
            result['cold_replay'].append(dict(condition=condition, source_kind=first['source_kind'],
                                             independent_load=True, identity_replay_pass=same,
                                             observed_H_sha256=cold['actual_identities']['hamiltonian_sha256'],
                                             target_match=cold['gates']['H_exact_SHA'],
                                             PF='NOT_RUN_SOURCE_REJECTED', echo='NOT_RUN_SOURCE_REJECTED',
                                             fit='NOT_RUN_SOURCE_REJECTED', proxy_difference=None,
                                             fit_difference=None))
    result['reconstruction_calls'] = [json.loads((PRIVATE/(f['condition']+'_reconstruction_return.json')).read_text())
                                      for f in registry['systems']]
    # Drop raw construction metadata from the public result; the historical registry and
    # scalar difference audit carry fingerprints, while arrays remain in private pickles.
    for row in result['reconstruction_calls']:
        row.pop('metadata',None)
    result['resources'] = dict(wall_seconds=time.perf_counter()-started,
                               peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                               software={k:importlib.metadata.version(k) for k in
                                         ['numpy','scipy','pyscf','openfermion','qiskit','qiskit-aer']},
                               python=sys.version.split()[0],
                               threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']})
    result['counts'] = dict(FS_C1_science_action_count=0, new_direct_truth=0,
                            source_reconstruction_validation_action_count=2,
                            source_identity_audit_pass_count=8,
                            source_validation_action_count=10,
                            count_definition='two prepare_condition calls plus eight independent identity/fingerprint audit passes; PF/echo actions separately zero',
                            preliminary_schema_source_loads=2, preliminary_identity_source_loads=2,
                            audited_source_loads=8, total_source_loads=12,
                            validation_ground_solve_calls=sum(r['ground_solve_calls'] for r in result['reconstruction_calls']),
                            explicit_Ritz_H_matvec=0, small_Ritz_solve=0,
                            backend_validation_PF_forward=0, logical_exact_H_echo=0,
                            group_application=0, group_gate_materialization=0,
                            M00_validation_backend_fit_calls=0)
    assert result['counts']['validation_ground_solve_calls']==2
    assert all(not r['gates']['H_exact_SHA'] for r in result['candidate']+result['reconstruction'])
    # Secure the complete scalar return before exposing public audit documents.
    recovery = PRIVATE/'complete_identity_audit_recovery.json'
    recovery.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    recovery.chmod(0o600)
    print(json.dumps(dict(candidate_H_exact_pass=False, reconstructed_H_exact_pass=False,
                         source_validation_action_count=10, FS_C1_science_action_count=0)))


if __name__=='__main__':
    main()
