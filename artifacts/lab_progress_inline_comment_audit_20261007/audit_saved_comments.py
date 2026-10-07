#!/usr/bin/env python3
"""Audit saved scalars and the requested manuscript edits; no scientific runs."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DOC = ROOT / 'docs/research_outcomes/20261006/lab_progress_slide_outline.md'
SNAPSHOT = '19362c23ccdc16b6ad0ff547cc363e138a3930d2'
SOURCES = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(path, origin):
    data = subprocess.check_output(['git', 'show', f'{SNAPSHOT}:{path}'], cwd=ROOT)
    old = subprocess.check_output(['git', 'show', f'{origin}:{path}'], cwd=ROOT)
    subprocess.run(['git', 'merge-base', '--is-ancestor', origin, SNAPSHOT],
                   cwd=ROOT, check=True)
    local = ROOT / path
    if local.exists():
        assert local.read_bytes() == data, f'Existing source differs from snapshot: {path}'
    SOURCES.append({
        'path': path, 'origin_result_commit': origin,
        'verified_snapshot_commit': SNAPSHOT, 'sha256': sha(data),
        'origin_blob_sha256': sha(old), 'origin_blob_equals_verified': old == data,
    })
    return data.decode()


def saved_json(path, origin):
    return json.loads(source(path, origin))


def saved_csv(path, origin):
    return list(csv.DictReader(io.StringIO(source(path, origin))))


def main():
    proto = saved_json('PF_first_study_protocol_20260925.json',
                       'd3faddebe490dbe8224bd4274578f2edd313dfb0')
    base = 'artifacts/pf_first_study_phase_b_20260925_5a2f0a2/'
    origin = 'd13f49dc8923b0553f8c8596de3c44c8a7a6f14f'
    observed = saved_csv(base + 'observables.csv', origin)
    states = saved_csv(base + 'state_diagnostics.csv', origin)
    overlap = {r['state_id']: float(r['exact_overlap_probability']) for r in states}
    assert math.isclose(overlap['rhf'], 0.9364638563852806, abs_tol=1e-14)
    assert math.isclose(overlap['cisd'], 0.9994668439213916, abs_tol=1e-14)
    at_point = {(r['state_id'], float(r['time_hartree_inverse'])):
                float(r['proxy_imag_hartree']) for r in observed
                if r['formula_id'] == 'm5_best' and
                math.isclose(abs(float(r['time_hartree_inverse'])), 0.4, abs_tol=1e-14)}
    exact_even = (at_point['exact', 0.4] + at_point['exact', -0.4]) / 2
    parity = {}
    for state in ['cisd', 'controlled_q0.010_phi1.570796326795']:
        positive, negative = at_point[state, 0.4], at_point[state, -0.4]
        parity[state] = {'time': 0.4, 'g_positive': positive, 'g_negative': negative,
                         'g_odd': (positive - negative) / 2,
                         'even_state_difference': (positive + negative) / 2 - exact_even}
    assert parity['cisd']['g_odd'] == 0
    assert math.isclose(parity['cisd']['even_state_difference'], -9.814288833975554e-9,
                        rel_tol=1e-10)
    artificial = parity['controlled_q0.010_phi1.570796326795']
    assert math.isclose(artificial['g_odd'], -2.1606577811639216e-9, rel_tol=1e-10)
    assert math.isclose(artificial['even_state_difference'], 8.040560178340833e-9,
                        rel_tol=1e-10)

    expansion = saved_json('artifacts/validation_expansion_20261007/audit.json', SNAPSHOT)
    counts = {name: expansion['A1'][name] for name in ['H4', 'H6']}
    for name, eligible, state, mixed, excluded in [
            ('H4', 50, 43, 7, 6), ('H6', 46, 31, 15, 10)]:
        record = counts[name]
        assert record['all_case_count'] == 56
        assert record['fit_eligible_count'] == eligible
        assert record['fit_eligible_counts'] == {'E_state_hartree': state, 'mixed': mixed}
        assert record['primary_fit_not_identifiable_count'] == excluded
    branch = proto['phase_and_branch_policy']
    assert branch['branch_warning_ground_overlap_below'] == 0.9
    assert branch['branch_warning_previous_overlap_below'] == 0.9
    supplemental = saved_json(
        'artifacts/lab_progress_hchain_transfer_20261007/supplementary_dominant_phase.json',
        '8436a2f3644e0403ff5ebf19bee6caae364ae66e')
    split_errors = []
    for row in supplemental['records']:
        pf = abs(row['dominant_phase_shift'])
        qpe = proto['constants']['qpe_beta'] * row['K'] / (row['time'] * row['budget'])
        total = pf + qpe
        assert math.isclose(total, row['frozen_budget_total_error'], abs_tol=1e-15)
        epsilon = proto['constants']['target_error_hartree']
        assert row['formal_continuation_result_unchanged']
        assert not row['supplementary_precision_met']
        split_errors.append({'system': row['system'], 'time': row['time'],
                             'pf_error': pf, 'qpe_error': qpe, 'total_error': total,
                             'pf_alone_exceeds_target': pf > epsilon,
                             'total_exceeds_target': total > epsilon,
                             'formal_classification': 'unchanged; unconfirmed'})
    assert {r['system']: r['pf_alone_exceeds_target'] for r in split_errors} == {
        'H2': True, 'H5': True, 'H6': False}

    comparison = saved_json(
        'artifacts/m3_one_two_term_model_comparison_server2_20260910_92df2db_cpu/summary.json',
        '73cdbf200d348cc610d4c20f45a3208ce7ad2e7e')
    selection = {}
    for row in comparison['records']:
        if row['condition'] not in ['H6', 'H7'] or row['formula'] != 'current_m3':
            continue
        selection[row['condition']] = {model: row['models'][model]['metrics']
                                      for model in ['original_one_term', 'two_term']}
        assert selection[row['condition']]['two_term']['direct_cost_loss_against_saved_local_grid'] == 0
    assert round(selection['H6']['original_one_term']['direct_cost_loss_against_saved_local_grid'] * 100, 3) == 0.168
    assert round(selection['H7']['original_one_term']['direct_cost_loss_against_saved_local_grid'] * 100, 3) == 0.172
    source('artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md',
           '828b8a4f75f6d78fc1bd2ecdd1a3bfbfd6388fa0')
    allocation = saved_json('artifacts/pf_first_study_phase_a_20260925_6265243/predictions.json',
                            '5a2f0a2e0315493c892c79f1a6b8c9285cc52ac3')
    m5 = next(row for row in allocation['experiment_B']['formula_predictions']
              if row['formula_id'] == 'm5_best')
    reference_time = m5['proxy_t_ana_hartree_inverse']
    fit_times = [reference_time * fraction for fraction in [0.1, 0.2, 0.3, 0.4, 0.5]]
    assert round(fit_times[0], 3) == 0.215
    assert round(fit_times[-1], 3) == 1.077

    comments = json.loads((OUT / 'comments.json').read_text())
    text = DOC.read_text()
    assert len(comments['comments']) == 22
    assert all(c['status'] == 'resolved' and '[' + c['comment'] + ']' not in text
               for c in comments['comments'])
    assert not re.search(r'\[(?!E\d+)[^\]\n]*[ぁ-んァ-ヶ一-龠][^\]\n]*\](?!\()', text)
    headings = re.findall(r'^### Slide (\d+)：(.*)$', text, re.M)
    assert [int(n) for n, _ in headings] == list(range(1, 30))
    index_titles = dict(re.findall(r'^\| (\d+) \| (.*) \|$', text, re.M))
    assert all(index_titles[n] == title for n, title in headings)
    assert len(re.findall(r'^### A[123]：', text, re.M)) == 3
    assert text.count('\n$$\n') % 2 == 0
    declared = set(re.findall(r'^\| (E\d+) \|', text, re.M))
    used = {ref for item in re.findall(r'\[(E\d+[^\]]*)\]', text)
            for ref in re.findall(r'E\d+', item)}
    assert used <= declared
    missing = []
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        destination = (DOC.parent / target.split('#', 1)[0]).resolve()
        if destination in [OUT / 'checks.json', OUT / 'manifest.json']:
            continue  # Both files are generated below and then checked to exist.
        if not destination.exists():
            missing.append(target)
    assert not missing, missing
    slide21 = text.split('### Slide 21：', 1)[1].split('### Slide 22：', 1)[0]
    supplement = slide21.split('**補足：**', 1)[1]
    assert '未知分子への独立検証ではない' not in supplement
    assert '信号判定不成立' in text and '計算自体は全ケースで行った' in text
    assert all(s['origin_blob_equals_verified'] for s in SOURCES)
    checks = {
        'scope': 'saved scalar reaggregation and manuscript audit only',
        'new_scientific_calculations': False, 'refitting_performed': False,
        'source_registry': SOURCES, 'state_overlap_squared': overlap,
        'signed_time_proxy_diagnostic': parity, 'primary_fit_eligibility': counts,
        'frozen_branch_policy': branch, 'supplemental_pf_qpe_error_split': split_errors,
        'one_vs_two_term_selection_metrics': selection,
        'm5_resource_model_fit_times_hartree_inverse': fit_times,
        'document_checks': {'resolved_comments': 22, 'main_slide_count': 29,
                            'appendix_count': 3, 'title_index_matches': True,
                            'no_remaining_inline_comments': True,
                            'local_links_exist': True, 'evidence_refs_declared': True,
                            'math_delimiters_paired': True,
                            'user_slide21_supplement_deletion_preserved': True},
        'all_checks_passed': True,
    }
    (OUT / 'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
    paths = [DOC, OUT / 'comments.json', OUT / 'audit_saved_comments.py', OUT / 'checks.json']
    manifest = {'self_excluded': 'manifest.json',
                'reason': 'Avoid circular hashing; the containing commit identifies the manifest.',
                'verified_source_snapshot_commit': SNAPSHOT,
                'new_scientific_calculations': False,
                'files': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    assert (OUT / 'checks.json').exists() and (OUT / 'manifest.json').exists()
    print(json.dumps(checks['document_checks'], ensure_ascii=False))


if __name__ == '__main__':
    main()
