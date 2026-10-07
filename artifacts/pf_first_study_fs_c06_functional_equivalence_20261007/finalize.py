"""Verify scalar/code publication and preservation, without source decode/actions."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL=HERE.relative_to(ROOT).as_posix()
BASE='75fe0d65a2940f160ea42f6414fc2246d67bd0cf'
FREEZE='a5fb9835657c3e5ac1658d1323b5746bf318fc8c'
REQUIRED=['README.md','research_amendment.md','fs_c1_protocol_v3.json','source_contract.md',
 'historical_fingerprint_registry.json','candidate_source_audit.json','reconstruction_audit.json',
 'functional_equivalence_result.json','operational_source_identity.json','sanitization_audit.json',
 'M00_reproduction.json','backend_reproduction.json','echo_numerical_contract.json','cost_ledger.json',
 'cold_replay_audit.json','truth_access_audit.json','tests.log','verification.json',
 'source_manifest.json','publication_manifest.json','GO_NO_GO_FOR_FS_C1.json']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    log=Path('/tmp/fs-c06-tests-final.log').read_text()
    assert '136 passed' in log and 'failed' not in log and 'ERROR' not in log
    initial=Path('/tmp/fs-c06-tests-initial.log').read_text()
    (HERE/'tests.log').write_text('Final command: PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/fs-c06-mpl-cache PYTHONPATH=src:artifacts/pf_first_study_fs_c0_20261007:artifacts/pf_first_study_fs_c05_execution_closure_20261007 /home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python -m pytest -q -p no:cacheprovider artifacts/pf_first_study_fs_c0_20261007/test_fs_c0.py artifacts/pf_first_study_fs_c05_execution_closure_20261007/test_fs_c05.py artifacts/pf_first_study_fs_c06_functional_equivalence_20261007/test_fs_c06.py\n'
      'Test environment: Python3.11.1, NumPy1.26.4, SciPy1.14.1, pytest8.3.3, jsonschema4.26.0. This is the previous 114-test environment; reconstruction retains pinned Python3.12.3 environment.\n'
      'Scope: existing114 plus new22; synthetic native PF/echo and saved-scalar arithmetic only. No real source decoding or physical PF/echo.\n\n'+log+
      '\nEarlier collection attempt in pinned reconstruction venv: jsonschema missing; collection stopped, no tests/actions ran. No dependency or reconstruction environment changes were made. Retried tests in existing test environment.\n'+initial)
    for p in HERE.glob('*.json'):
        json.loads(p.read_text())
    for p in HERE.glob('*.py'):
        ast.parse(p.read_text(),filename=p.name)
    frozen={}
    for name in ['validation_contract.json','historical_fingerprint_registry.json','build_contract.py']:
        before=git('show',f'{FREEZE}:{REL}/{name}')
        frozen[name]=sha(before)==sha((HERE/name).read_bytes())
    assert all(frozen.values())
    source_manifest=json.loads((HERE/'source_manifest.json').read_text())
    original_manifest=json.loads(git('show',f'{FREEZE}:{REL}/source_manifest.json'))
    assert source_manifest['sources']==original_manifest['sources']
    source_checks=[]
    for record in source_manifest['sources']+source_manifest['execution_dependencies']:
        raw=git('show',f"{record['verified_snapshot_commit']}:{record['path']}")
        assert sha(raw)==record['sha256']
        source_checks.append(dict(path=record['path'],origin_result_commit=record['origin_result_commit'],
           verified_snapshot_commit=record['verified_snapshot_commit'],sha256_matches=True))
    for record in source_manifest['execution_code_pins']:
        assert sha((HERE/record['path']).read_bytes())==record['sha256']
    frozen_protocol=json.loads(git('show',f'{FREEZE}:{REL}/fs_c1_protocol_v3.json'))
    final_protocol=json.loads((HERE/'fs_c1_protocol_v3.json').read_text())
    kept=['systems','constants','arms','fit','ritz','current_m3_sequence','historical_training_relative',
          'historical_baseline_model','M00_historical_reference','historical_training','M11_primary',
          'M01_challenger','sentinel_in_fit','relative_0_4_role','gates']
    assert all(frozen_protocol[k]==final_protocol[k] for k in kept)
    changes=git('diff','--name-only',BASE).decode().splitlines()
    assert all(p.startswith(REL+'/') for p in changes)
    previous=[]
    # Every tracked file existing at the starting commit must remain byte-identical.
    for rawpath in git('ls-tree','-r','--name-only',BASE).decode().splitlines():
        path=ROOT/rawpath
        if not path.is_file():
            raise AssertionError('Starting artifact removed: '+rawpath)
    # git diff verifies tracked content globally; hashes below provide explicit v1/v2 evidence.
    for relpath in ['artifacts/pf_first_study_fs_c0_20261007/fs_c1_protocol.json',
                    'artifacts/pf_first_study_fs_c05_execution_closure_20261007/fs_c1_protocol_v2.json',
                    'artifacts/pf_first_study_fs_c05_execution_closure_20261007/baseline_contract.json']:
        ok=sha(git('show',f'{BASE}:{relpath}'))==sha((ROOT/relpath).read_bytes())
        assert ok
        previous.append(dict(path=relpath,byte_identical=True))
    links=[]
    for p in HERE.glob('*.md'):
        for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if dest.startswith(('http:','https:')): continue
            target=(p.parent/dest.split('#')[0]).resolve()
            if target.name in ['verification.json','publication_manifest.json']: continue
            assert target.exists(), (p.name,dest)
            links.append(dict(document=p.name,target=dest,exists=True))
    allowed={'.md','.json','.csv','.log','.py'}
    files=sorted(p for p in HERE.iterdir() if p.is_file())
    assert all(p.suffix in allowed for p in files)
    assert not any(p.is_dir() for p in HERE.iterdir())
    forbidden_calls={'open_c1_truth','score_payload','eigh','eig','eigvals','eigvalsh'}
    operational_guard_audit=[]
    for name in ['source_adapter.py','run_identity_audits.py','publish_audits.py','finalize.py']:
        tree=ast.parse((HERE/name).read_text())
        calls=[node.func.id if isinstance(node.func,ast.Name) else node.func.attr
               for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Name,ast.Attribute))]
        assert not forbidden_calls.intersection(calls),name
        operational_guard_audit.append(dict(path=name,forbidden_truth_calls_present=False))
    counts=json.loads((HERE/'cost_ledger.json').read_text())['counts']
    assert counts['FS_C1_science_action_count']==counts['new_direct_truth']==0
    assert counts['source_reconstruction_validation_action_count']==2
    decision=json.loads((HERE/'GO_NO_GO_FOR_FS_C1.json').read_text())
    assert decision['status']=='NO_GO_RECONSTRUCTION_MISMATCH'
    decision['tests']=dict(existing=114,new=22,passed=136,failed=0,
                           physical_source_backend_reproduction=False)
    decision['cost_ledger_recorded']=True
    dump('GO_NO_GO_FOR_FS_C1.json',decision)
    verification=dict(status='PASS_AUDIT_PUBLICATION_CHECKS_SCIENTIFIC_SOURCE_NO_GO',
      audit_result=decision['status'],base_commit=BASE,contract_freeze_commit=FREEZE,
      tests=decision['tests'],test_environment=dict(python='3.11.1',numpy='1.26.4',scipy='1.14.1',pytest='8.3.3',jsonschema='4.26.0'),
      pinned_reconstruction_environment_unchanged=True,
      frozen_contract_blobs_unchanged=frozen,initial_source_registry_unchanged=True,
      v3_scientific_fields_unchanged_from_initial_freeze=kept,
      existing_v1_v2_and_baseline_blobs=previous,all_existing_tracked_content_unchanged_outside_new_package=True,
      old_science_artifacts_modified=False,historical_source_blob_checks=source_checks,
      code_AST_truth_checks=operational_guard_audit,local_links=links,
      source_validation_action_count=counts['source_validation_action_count'],FS_C1_science_action_count=0,
      new_direct_truth=0,private_binaries_published=False,operational_export_count=0,
      physical_backend_status='NOT_RUN_H_EXACT_SHA_REJECTION',
      publication_scope='Scalar/code/docs/log/hash only. No pickle/matrix/vector/unitary/exact state binaries.',
      remote_verification='Performed after final commit/push and reported in final handoff; not inferred by this precommit check.')
    dump('verification.json',verification)
    missing=[name for name in REQUIRED if name!='publication_manifest.json' and not (HERE/name).is_file()]
    assert not missing,missing
    manifest=dict(schema='FS-C0.6-publication-v1',self_exclusion='publication_manifest.json excluded from its own hash list',
       base_commit=BASE,validation_contract_freeze_commit=FREEZE,private_source_binary_publication=False,
       entries=[dict(path=p.name,size_bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
                for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='publication_manifest.json'])
    dump('publication_manifest.json',manifest)
    assert all((HERE/name).is_file() for name in REQUIRED)
    print(json.dumps(dict(verification='PASS',final_status=decision['status'],tests=136,public_file_count=len(manifest['entries'])+1,
                         source_pins=len(source_checks),FS_C1_science_action_count=0)))


if __name__=='__main__':
    main()
