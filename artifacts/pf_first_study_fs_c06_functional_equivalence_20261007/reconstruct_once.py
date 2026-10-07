"""One-shot historical prepare_condition in a private validation sandbox."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import pickle
import resource
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PRIVATE = Path('/tmp/fs-c06-validation-private-20261007')
PINNED = Path('/tmp/fs-c06-pinned-h01-e0692a8')


def write_private(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('condition', choices=['N2_active_eq_sto3g', 'CO_active_eq_sto3g'])
    args = parser.parse_args()
    contract = json.loads((HERE / 'validation_contract.json').read_text())
    config = contract['reconstruction']
    assert sys.version.split()[0] == config['python']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PINNED,
                                   text=True).strip() == config['code_revision']
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=PINNED,
                                   text=True).strip() == ''
    for package, version in config['packages'].items():
        assert importlib.metadata.version(package) == version
    for variable, value in config['threads'].items():
        assert os.environ[variable] == value
    identity = json.loads((PRIVATE / (args.condition + '_candidate_identity_recovery.json')).read_text())
    assert not identity['H_exact_match'], 'No reconstruction after candidate PASS'
    marker = PRIVATE / (args.condition + '_reconstruction_attempt.json')
    # O_EXCL makes restarting/tuning the same condition impossible.
    with marker.open('x') as stream:
        json.dump(dict(condition=args.condition, attempt=1, config=config,
                       contract_sha256=hashlib.sha256((HERE / 'validation_contract.json').read_bytes()).hexdigest()), stream)
    marker.chmod(0o600)
    sys.path[:0] = [str(PINNED / 'review_response'), str(PINNED / 'src')]
    import run_h01_approximate_state_calibration as native
    assert Path(native.__file__).resolve().is_relative_to(PINNED)
    ground_calls = 0
    captured_groups = None
    original_eigh, original_hash = native.eigh, native._group_hashes

    def ground_eigh(*a, **kw):
        nonlocal ground_calls
        ground_calls += 1
        return original_eigh(*a, **kw)

    def capture_groups(groups):
        nonlocal captured_groups
        captured_groups = groups  # Keep original order, no mutation.
        return original_hash(groups)

    native.eigh, native._group_hashes = ground_eigh, capture_groups
    started = time.perf_counter()
    try:
        system, metadata = native.prepare_condition(args.condition,
            PRIVATE / (args.condition + '_reconstruction_work'), config['component_processes'])
        # Returned scalars are secured before any public validation or serialization.
        recovery = dict(condition=args.condition, status='RETURNED', metadata=metadata,
                        ground_solve_calls=ground_calls, source_reconstruction_validation_action_count=1,
                        wall_seconds=time.perf_counter() - started,
                        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                        FS_C1_science_action_count=0, new_direct_truth=0)
        write_private(PRIVATE / (args.condition + '_reconstruction_scalar_recovery.json'), recovery)
        binary = PRIVATE / (args.condition + '_reconstructed_validation.pkl')
        with binary.open('xb') as stream:
            pickle.dump(dict(system=system, metadata=metadata, ordered_groups=captured_groups),
                        stream, protocol=pickle.HIGHEST_PROTOCOL)
        binary.chmod(0o600)
        receipt = dict(recovery, private_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                       H_sha=native._sparse_hash(system['hamiltonian']),
                       technical_failure=False, source_kind='reconstructed candidate')
        write_private(PRIVATE / (args.condition + '_reconstruction_return.json'), receipt)
        print(json.dumps({k: receipt[k] for k in ['condition', 'status', 'H_sha',
                                                'wall_seconds', 'peak_RSS_bytes', 'ground_solve_calls']}))
    except Exception as error:
        write_private(PRIVATE / (args.condition + '_reconstruction_return.json'),
                      dict(condition=args.condition, status='TECHNICAL_FAILURE',
                           technical_failure=True, error_type=type(error).__name__, error=str(error),
                           ground_solve_calls=ground_calls,
                           source_reconstruction_validation_action_count=1,
                           wall_seconds=time.perf_counter() - started,
                           peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                           FS_C1_science_action_count=0, new_direct_truth=0))
        raise


if __name__ == '__main__':
    main()
