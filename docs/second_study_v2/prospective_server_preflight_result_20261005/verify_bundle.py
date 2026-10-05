"""Validate review metadata only. No numerical imports, tests or science runners."""
import argparse
import csv
import datetime
import hashlib
import json
import math
import pathlib
import re
import subprocess

BUNDLE = pathlib.Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
ORIGINAL_ROOT = ROOT.parent.parent
BASE = 'c04d95a9fa8b9653b58bea59169ce6e7352a9da0'
STATUS = 'prospective_budget_safety_preflight_complete_review_required'


def git(*args, root=ROOT):
    return subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args],
                          check=True, capture_output=True).stdout


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate():
    expected = {'report.md', 'hardware_and_allocation.json', 'candidate_inventory.csv',
                'parallel_resource_plan.md', 'protocol_draft.md', 'source_registry.json',
                'access_and_operation_audit.json', 'bundle_manifest.json', 'handoff.md',
                'usage_history_scope.json', 'resource_planning_arithmetic.json',
                'validation.json', 'verify_bundle.py'}
    files = {p.name for p in BUNDLE.iterdir() if p.is_file()}
    assert files <= expected, files - expected
    assert expected - {'bundle_manifest.json', 'validation.json'} <= files
    for p in BUNDLE.iterdir():
        assert p.is_file() and not p.is_symlink()
        assert p.stat().st_size < 250_000, p
    documents = {}
    for p in BUNDLE.glob('*.json'):
        documents[p.name] = json.loads(p.read_text())
    links = 0
    for p in BUNDLE.glob('*.md'):
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', p.read_text()):
            if target.startswith(('https://', 'http://')):
                continue
            target = target.split('#', 1)[0]
            if target:
                assert (p.parent / target).resolve().is_file(), (p, target)
                links += 1
    with (BUNDLE / 'candidate_inventory.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 31
        assert len({r['condition_id'] for r in rows}) == len(rows)
        assert all(None not in r and all(v is not None for v in r.values()) for r in rows)
        assert sum(r['record_role'] == 'prospective_geometry_proposal' for r in rows) == 20
        assert sum(r['record_role'] == 'separate_open_shell_stratum_proposal' for r in rows) == 4
        assert sum(r['condition_novelty'] == 'previously_used' for r in rows) == 5
        assert all(r['prospective_test_set_adopted'] == 'false' for r in rows)
        assert all(r['condition_novelty'] in {'unverified', 'previously_used'} for r in rows)
        for row in rows:
            n, na, nb = (int(row[k]) for k in ['active_spatial_orbitals_estimate', 'n_alpha', 'n_beta'])
            d = math.comb(n, na) * math.comb(n, nb)
            assert int(row['sector_dimension_estimate']) == d
            assert int(row['active_electrons']) == na + nb
            assert int(row['total_electrons']) - 2 * int(row['frozen_core_spatial_orbitals_proposal']) == na + nb
            assert int(row['one_complex128_matrix_bytes']) == 16 * d * d
            assert int(row['nine_dense_matrices_bytes']) == 9 * 16 * d * d
    reg = documents['source_registry.json']
    hashed_sources, path_only_sources = 0, 0
    for s in reg['sources']:
        path = s['path']
        origin, snapshot = s['origin_result_commit'], s['verified_snapshot_commit']
        assert re.fullmatch('[0-9a-f]{40}', origin)
        assert re.fullmatch('[0-9a-f]{40}', snapshot)
        origin_oid = git('rev-parse', origin + ':' + path).decode().strip()
        snapshot_oid = git('rev-parse', snapshot + ':' + path).decode().strip()
        assert origin_oid == snapshot_oid == s['git_blob_oid_at_handoff']
        if 'sha256' in s:
            data = git('show', snapshot + ':' + path)
            assert sha256(data) == s['sha256']
            assert (ROOT / path).read_bytes() == data
            hashed_sources += 1
        else:
            assert s['content_opened_or_hashed'] is False
            path_only_sources += 1
    prior = json.loads((ROOT / 'docs/second_study_v2/prospective_server_preflight_20261005/bundle_manifest.json').read_text())
    for s in prior['files']:
        data = git('show', BASE + ':' + s['path'])
        assert sha256(data) == s['sha256'] and len(data) == s['bytes']
    audit = documents['access_and_operation_audit.json']
    assert audit['status'] == STATUS
    assert all(v == 0 for v in audit['counters'].values())
    assert documents['hardware_and_allocation.json']['cpu']['allocation_status'] == 'allocation_unverified'
    assert documents['hardware_and_allocation.json']['cpu']['allocated_CPU_budget'] is None
    assert documents['usage_history_scope.json']['prospective_conditions_adopted'] == 0
    baseline = audit['root_dirty_baseline']
    for path, value in baseline['tracked_dirty_file_sha256'].items():
        assert sha256((ORIGINAL_ROOT / path).read_bytes()) == value
    assert sha256((ORIGINAL_ROOT / '.git/index').read_bytes()) == baseline['main_index_sha256']
    assert git('rev-parse', 'HEAD', root=ORIGINAL_ROOT).decode().strip() == baseline['root_HEAD']
    before = pathlib.Path('/tmp/pf-study2-preflight-root-status-before.txt').read_text().splitlines()
    after = git('status', '--porcelain=v1', '-uall', root=ORIGINAL_ROOT).decode().splitlines()
    own_prefix = '.worktrees/gpu-pf-study2-prospective-preflight-20261005/'
    keep = lambda lines: sorted(line for line in lines if not line[3:].startswith(own_prefix))
    assert keep(before) == keep(after), 'unrelated root porcelain state changed'
    changed = git('diff', '--name-only', BASE).decode().splitlines()
    assert all(p.startswith(str(BUNDLE.relative_to(ROOT)) + '/') for p in changed)
    status = git('status', '--porcelain=v1', '-uall').decode().splitlines()
    assert all(line[3:].startswith(str(BUNDLE.relative_to(ROOT)) + '/') for line in status)
    git('merge-base', '--is-ancestor', 'e895870f16878ee4181b0e0dfe3159826a791563', BASE)
    return {'schema': 'study2_prospective_preflight_review_validation_v1',
            'status': STATUS, 'validation_scope': 'metadata, links, hashes, Git blobs and dirty preservation only',
            'local_relative_links_checked': links, 'candidate_CSV_rows': len(rows),
            'source_origin_snapshot_blob_pairs_checked': hashed_sources + path_only_sources,
            'source_sha256_and_worktree_bytes_checked': hashed_sources,
            'usage_path_only_blobs_checked_without_content_read': path_only_sources,
            'instruction_manifest_files_checked': len(prior['files']),
            'new_scientific_operations': 0, 'numeric_tests_run': 0, 'legacy_tests_run': 0,
            'root_dirty_files_and_main_index_preserved': True,
            'root_unrelated_porcelain_state_preserved': True, 'base_source_and_frozen_results_unchanged': True,
            'no_numeric_library_imports_or_runner_execution': True,
            'publication_status': audit.get('publication_status', 'pending_at_bundle_freeze'),
            'publication_verification': 'not complete; remote SHA/fetch/required blobs require successful authenticated publication'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    result = validate()
    if args.seal:
        result['validated_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (BUNDLE / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
        files = []
        for p in sorted(BUNDLE.iterdir()):
            if p.name == 'bundle_manifest.json':
                continue
            data = p.read_bytes()
            files.append({'path': str(p.relative_to(ROOT)), 'sha256': sha256(data), 'bytes': len(data)})
        manifest = {'schema': 'study2_prospective_preflight_result_manifest_v1',
                    'status': STATUS, 'manifest_self_excluded': True, 'handoff_commit': BASE,
                    'created_date_jst': '2026-10-05', 'files': files,
                    'operations': {'new_scientific_acquisition': 0, 'GPU_queries_allocations_kernels': 0,
                                   'shared_environment_changes': 0, 'numeric_tests': 0},
                    'publication_status': result['publication_status'],
                    'publication_commit': 'commit containing this manifest reported in final handoff; no self-reference'}
        (BUNDLE / 'bundle_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    manifest = json.loads((BUNDLE / 'bundle_manifest.json').read_text())
    assert manifest['manifest_self_excluded'] is True
    listed = {pathlib.Path(s['path']).name for s in manifest['files']}
    assert listed == {p.name for p in BUNDLE.iterdir()} - {'bundle_manifest.json'}
    for entry in manifest['files']:
        data = (ROOT / entry['path']).read_bytes()
        assert sha256(data) == entry['sha256'] and len(data) == entry['bytes']
    print(json.dumps({**result, 'manifest_files_verified': len(manifest['files']),
                      'bundle_manifest_sha256': sha256((BUNDLE / 'bundle_manifest.json').read_bytes())}))


if __name__ == '__main__':
    main()
