"""FS-C0.6 source guards. No Phase B, scorer, or FS-C1 runner imports."""
import hashlib
import json
import math
from pathlib import Path
import pickle
import resource
import time
import numpy as np

HERE = Path(__file__).resolve().parent
REQUIRED_GATES = ('H_exact_SHA', 'metadata_sector', 'ordered_groups', 'CISD_fingerprints',
                  'M00_proxy', 'M00_fit', 'echo_contract', 'cold_replay')
EXPORT_KEYS = {'hamiltonian', 'component_spectra', 'cisd', 'restricted_basis',
               'metadata', 'removed_constant', 'current_m3_sequence'}
METADATA_KEYS = {'condition', 'geometry_angstrom', 'basis', 'charge', 'multiplicity',
                 'total_electron_count', 'total_spatial_orbitals', 'active_electron_count',
                 'active_spatial_orbitals', 'frozen_core_spatial_orbitals', 'n_alpha', 'n_beta',
                 'population_sector_dimension', 'restricted_dimension', 'z2_mask', 'z2_target',
                 'group_count', 'term_counts', 'group_sha256'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sparse_hash(matrix):
    h = hashlib.sha256(np.asarray(matrix.shape, dtype=np.int64).tobytes())
    for array in (matrix.indptr, matrix.indices, matrix.data):
        h.update(np.ascontiguousarray(array).tobytes())
    return h.hexdigest()


def array_hash(array):
    a = np.asarray(array)
    return digest(canonical(dict(dtype=a.dtype.str, shape=list(a.shape))) + a.tobytes(order='C'))


def accept(gates):
    # Pickle byte mismatch is intentionally not a scientific rejection gate.
    return all(gates.get(key) is True for key in REQUIRED_GATES)


def forbid_c1_truth(*_a, **_kw):
    raise PermissionError('FS-C0.6 cannot open Phase B/scorer or FS-C1 truth')


def one_attempt(path, config):
    with Path(path).open('x') as stream:
        json.dump(config, stream, sort_keys=True)


def check_pinned(actual, expected):
    if canonical(actual) != canonical(expected):
        raise ValueError('pinned reconstruction configuration changed')
    return True


def sanitized(system, metadata, sequence, gates):
    if not accept(gates):
        raise PermissionError('source has not passed every functional-equivalence gate')
    # Construct by allowlist, never copy a source dict and remove a few fields.
    return dict(hamiltonian=system['hamiltonian'], component_spectra=system['component_spectra'],
                cisd=system['states']['cisd'], restricted_basis=system['restricted_basis'],
                metadata={k: metadata[k] for k in METADATA_KEYS},
                removed_constant=metadata['removed_constant_hartree'],
                current_m3_sequence=tuple(sequence))


def assert_sanitized(export):
    if set(export) != EXPORT_KEYS or set(export['metadata']) != METADATA_KEYS:
        raise ValueError('oracle/truth or unknown export fields present')
    return True


def identity_audit(path, fingerprint, contract, *, reconstructed=False, private_dir=None, pass_name='initial'):
    started = time.perf_counter()
    raw = Path(path).read_bytes()
    decoded = pickle.loads(raw)
    if reconstructed:
        system, metadata = decoded['system'], decoded['metadata']
    else:
        system = decoded
        metadata = json.loads(Path(path).with_suffix('.metadata.json').read_text())
    historical = fingerprint['historical_metadata']
    actual_hash = sparse_hash(system['hamiltonian'])
    metadata_checks = {key: metadata.get(key) == historical.get(key) for key in METADATA_KEYS}
    # Removed constant is covered by the historical numeric metadata contract.
    constant_difference = abs(metadata['removed_constant_hartree'] - historical['removed_constant_hartree'])
    basis = np.asarray(system['restricted_basis'])
    n = historical['active_spatial_orbitals']
    expected_basis = np.asarray([v for v in range(1 << (2*n))
                                if (v >> n).bit_count() == historical['n_alpha']
                                and (v & ((1 << n)-1)).bit_count() == historical['n_beta']
                                and (v & historical['z2_mask']).bit_count() % 2 == historical['z2_target']], dtype=basis.dtype)
    metadata_checks['basis_order_exact'] = np.array_equal(basis, expected_basis)
    metadata_checks['dimension_matches_data'] = system['hamiltonian'].shape == (historical['restricted_dimension'],)*2
    state = system['states']['cisd']
    action = system['hamiltonian'] @ state
    energy = float(np.vdot(state, action).real)
    residual = action - energy * state
    diagnostics = dict(normalization=float(np.linalg.norm(state)), energy_expectation_hartree=energy,
                       energy_error_hartree=energy-float(system['energy']),
                       energy_variance_hartree2=float(np.vdot(residual,residual).real),
                       hamiltonian_residual_2_norm=float(np.linalg.norm(residual)),
                       overlap_probability_with_exact_ground_for_evaluation_only=float(abs(np.vdot(system['state'],state))**2))
    saved_state = historical['states']['cisd']
    differences = {key: abs(value - saved_state[key]) for key,value in diagnostics.items()}
    state_attested = ['pyscf_cisd_total_energy_hartree','pyscf_cisd_correlation_energy_hartree',
                      'pyscf_vs_matrix_energy_difference_hartree','matrix_plus_constant_energy_hartree',
                      'population_sector_outside_norm','additional_z2_sector_outside_norm']
    attested_differences = {key: abs(metadata['states']['cisd'][key]-saved_state[key]) for key in state_attested}
    identities = dict(hamiltonian_sha256=actual_hash, cisd_sha256=array_hash(state),
                      restricted_basis_sha256=array_hash(basis),
                      ordered_group_identity_sha256=digest(canonical(metadata['group_sha256'])),
                      group_sha_list=metadata['group_sha256'],
                      component_order_sha256=[digest(b''.join(array_hash(a).encode() for batch in spectrum.batches
                                              for a in (batch.indices, batch.eigenvalues) +
                                              (() if batch.eigenvectors is None else (batch.eigenvectors,))))
                                              for spectrum in system['component_spectra']],
                      H_dtype=system['hamiltonian'].dtype.str, H_shape=list(system['hamiltonian'].shape),
                      CISD_dtype=np.asarray(state).dtype.str, CISD_shape=list(np.asarray(state).shape))
    gates = dict(H_exact_SHA=actual_hash==historical['hamiltonian_sha256'],
                 metadata_sector=all(value for key,value in metadata_checks.items() if key not in
                                     ['group_sha256','term_counts','group_count']) and
                                     constant_difference<=contract['metadata_absolute_tolerance_hartree'],
                 ordered_groups=False,
                 CISD_fingerprints=max([*differences.values(),*attested_differences.values()])<=contract['state_absolute_tolerance'],
                 M00_proxy=None, M00_fit=None, echo_contract=None, cold_replay=None)
    group_attestations = all(metadata_checks[key] for key in ['group_sha256','term_counts','group_count'])
    # Stop at the mandatory H exact hash. Do not materialize PF gates on rejected sources.
    result = dict(condition=fingerprint['condition'], pass_name=pass_name,
                  source_kind='reconstructed candidate' if reconstructed else 'existing H02 candidate',
                  source_binary_sha256=digest(raw), historical_whole_pickle_status='missing',
                  historical_whole_pickle_sha256=fingerprint['baseline']['identity']['source_pickle_sha256'],
                  historical_whole_pickle_match=digest(raw)==fingerprint['baseline']['identity']['source_pickle_sha256'],
                  actual_identities=identities, expected_H_sha256=historical['hamiltonian_sha256'],
                  gates=gates, metadata_identity_checks=metadata_checks,
                  removed_constant_difference_hartree=constant_difference,
                  recalculated_CISD_fingerprint_differences=differences,
                  additional_metadata_attestation_differences=attested_differences,
                  CISD_pyscf_and_preprojection_diagnostics='metadata attestations; no new CISD solve during candidate audit',
                  ordered_group_attestations_match=group_attestations,
                  numerical_group_content='NOT_RUN_H_HASH_REJECTION',
                  maximum_CISD_fingerprint_difference=max([*differences.values(),*attested_differences.values()]),
                  accepted=False, status='REJECT_H_EXACT_SHA' if not gates['H_exact_SHA'] else 'SOURCE_GATE_UNCLOSED',
                  PF_forward=0, logical_exact_H_echo=0, FS_C1_science_action_count=0,
                  ground_fingerprint_used_only_in_validation_sandbox=True,
                  wall_seconds=time.perf_counter()-started,
                  peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    if private_dir:
        target = Path(private_dir)/(fingerprint['condition']+'_'+result['source_kind'].replace(' ','_')+'_'+pass_name+'_audit_recovery.json')
        target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        target.chmod(0o600)
    return result
