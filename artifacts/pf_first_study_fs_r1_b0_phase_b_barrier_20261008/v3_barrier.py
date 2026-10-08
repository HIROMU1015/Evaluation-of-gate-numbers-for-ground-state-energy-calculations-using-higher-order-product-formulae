"""Read-only actual Git/independent-remote/private-scalar v3 Phase A barrier."""
import json
from pathlib import Path
import subprocess
import sys
from b0_common import (ROOT,HERE,A,A0,R0,R01,SCIENCE,HANDOFF,PREDICTION,RESULT,PROTOCOL,NUMERICAL,
    CODE_A,LADDER,REMOTE,ARMS,sha,canonical,path_ok,_issue_verified_freeze)

class GitEvidence:
    def __init__(self,root,remote_receipt):
        self.root=Path(root)
        self.bare=Path(remote_receipt['independent_bare'])
        if not self.bare.is_dir() or (self.bare/'objects/info/alternates').exists():raise ValueError('independent remote object store required')
        url=subprocess.check_output(['git','--git-dir',str(self.bare),'remote','get-url','origin'],text=True).strip()
        if url!=REMOTE:raise ValueError('remote repository identity mismatch')
    def blob(self,commit,path):
        return subprocess.check_output(['git','show',commit+':'+path_ok(path)],cwd=self.root,stderr=subprocess.DEVNULL)
    def independent_blob(self,commit,path):
        return subprocess.check_output(['git','--git-dir',str(self.bare),'show',commit+':'+path_ok(path)],stderr=subprocess.DEVNULL)
    def local(self,path):return (self.root/path_ok(path)).read_bytes()
    def lineage(self,origin,handoff):
        parent=subprocess.check_output(['git','rev-parse',handoff+'^'],cwd=self.root,text=True).strip()
        if parent!=origin:raise ValueError('handoff lineage mismatch')
        rows=subprocess.check_output(['git','diff','--name-status',origin,handoff],cwd=self.root,text=True).splitlines()
        if not rows or any(not r.startswith('A\t'+A+'/') for r in rows):raise ValueError('science changes in handoff')
        return rows

def scalar_prediction(value):
    import math
    forbidden={'exact_ground','exact_energy','ground_state','exact_state','direct_truth','signed_direct_shift',
        'branch_id','selected_branch_id','branch_rows','previous_vector_overlap','ground_overlap','unitary',
        'vector','vectors','matrix','matrices','true_gap','ground_state_overlap_probability','selected_eigenvalue'}
    if isinstance(value,dict):
        if set(value)&forbidden:raise ValueError('truth-containing Phase A prediction')
        for v in value.values():scalar_prediction(v)
    elif isinstance(value,list):
        for v in value:scalar_prediction(v)
    elif type(value) not in (bool,str,int,float,type(None)):raise ValueError('non-scalar prediction')
    elif type(value)==float and not math.isfinite(value):raise ValueError('nonfinite prediction')

def validate_saved_components(payload,components,p):
    scalar_prediction(payload)
    sys.path.insert(0,str(ROOT/A0))
    from phase_a_wrapper import validate_complete
    validate_complete(payload,p) # Frozen scalar validation only; no acquisition/fit.
    cold=components['cold_replay.json'];gates=components['numerical_gate_audit.json']
    if cold.get('status')!='PASS' or cold.get('replay')!=payload['replay']:raise ValueError('cold replay evidence mismatch')
    if gates.get('status')!='PASS' or gates.get('replay_pass') is not True or gates.get('thresholds_modified') is not False:
        raise ValueError('numerical gate evidence mismatch')
    if len(gates['proxy_gates'])!=32 or not all(all(r[k] is True for k in
        ('finite','input_norm_pass','PF_norm_pass','reference_norm_pass','Cauchy_pass')) for r in gates['proxy_gates']):
        raise ValueError('numerical proxy gate FAIL')
    if len(gates['Ritz_gates'])!=4 or any(r['status']!='PASS' for r in gates['Ritz_gates']):raise ValueError('Ritz gate FAIL')
    if gates['fixed_contract']!=p['numerical_contract']:raise ValueError('numerical contract evidence mismatch')
    saved=components['predicted_budgets.json']
    for key,category in [('initial','initial_operational'),('cold','cold_validation')]:
        expected=[dict(condition=r['condition'],budgets=r['budgets'],ratios=r['prediction_only_ratios']) for r in payload[category]]
        if saved[key]!=expected:raise ValueError('frozen budget view mismatch')
    for category in ('initial_operational','cold_validation'):
        for r in payload[category]:
            if set(r['budgets'])!=set(ARMS) or any(b['finite_budget_reported'] is not True or b['status']!='FEASIBLE_BUDGET_INTERVAL' for b in r['budgets'].values()):
                raise ValueError('all eight finite budget intervals required')
    truth=components['truth_access_audit.json']
    expected={'direct_truth_reads','branch_solves','truth_schur','exact_ground_operational_reads','historical_truth_reads','new_direct_truth_coordinates'}
    if set(truth['counts'])!=expected or any(type(v)!=int or v!=0 for v in truth['counts'].values()):raise ValueError('truth access not zero')
    if truth['original_pickle_reads']!=0 or truth['Phase_B_executed'] is not False:raise ValueError('Phase A oracle access')
    return True

def verify_phase_a(root=ROOT,receipt_path=None,evidence=None,*,science_origin=SCIENCE,handoff=HANDOFF,
                   prediction_sha=PREDICTION,results_sha=RESULT):
    if science_origin!=SCIENCE:raise ValueError('Phase A science-origin commit mismatch')
    if handoff!=HANDOFF:raise ValueError('Phase A handoff commit mismatch')
    if prediction_sha!=PREDICTION or results_sha!=RESULT:raise ValueError('fixed prediction/result SHA mismatch')
    receipt_path=Path(receipt_path or HERE/'phase_a_external_remote_verification.json')
    if not receipt_path.is_file():raise ValueError('remote receipt absent')
    external_raw=receipt_path.read_bytes();external=json.loads(external_raw)
    if (external.get('status')!='PASS' or external.get('remote_fetched_independently') is not True or
        external.get('remote_verified_commit')!=HANDOFF or external.get('origin_result_commit')!=SCIENCE or
        external.get('prediction_sha256')!=PREDICTION or external.get('manifest_sha256')!=PREDICTION):
        raise ValueError('independent handoff remote receipt invalid')
    ev=evidence or GitEvidence(root,external)
    changes=ev.lineage(SCIENCE,HANDOFF)
    checked={}
    def checked_blob(path,commit=HANDOFF,expected_sha=None,length=None):
        path_ok(path);raw=ev.blob(commit,path)
        if raw!=ev.local(path) or raw!=ev.independent_blob(commit,path):raise ValueError('committed/local/remote blob mismatch: '+path)
        digest=sha(raw)
        if expected_sha is not None and digest!=expected_sha:raise ValueError('SHA mismatch: '+path)
        if length is not None and len(raw)!=length:raise ValueError('byte length mismatch: '+path)
        if external.get('verified_file_sha256',{}).get(path)!=digest:raise ValueError('remote target blob evidence mismatch: '+path)
        checked[path]=digest
        return raw
    manifest_raw=checked_blob(A+'/prediction_manifest.json',expected_sha=PREDICTION)
    manifest=json.loads(manifest_raw)
    if canonical(manifest)!=manifest_raw:raise ValueError('noncanonical prediction manifest')
    if ev.blob(SCIENCE,A+'/prediction_manifest.json')!=manifest_raw:raise ValueError('science-origin freeze mismatch')
    side=checked_blob(A+'/prediction.sha256')
    if side!=(PREDICTION+'\n').encode() or ev.blob(SCIENCE,A+'/prediction.sha256')!=side:raise ValueError('prediction SHA sidecar mismatch')
    if manifest.get('self_excluded') is not True or manifest.get('format')!='FS-R1-Phase-A-v3-prediction-freeze-v1':
        raise ValueError('v3 prediction manifest schema mismatch')
    records=manifest.get('files')
    if not isinstance(records,list) or not records or any(set(r)!={'path','sha256','bytes'} for r in records):raise ValueError('v3 file record array required')
    paths=[r['path'] for r in records]
    if len(set(paths))!=len(paths) or A+'/prediction_manifest.json' in paths or A+'/prediction.sha256' in paths:
        raise ValueError('manifest duplicate/self reference')
    components={}
    for record in records:
        if not record['path'].startswith(A+'/'):raise ValueError('unexpected prediction file path')
        raw=checked_blob(record['path'],expected_sha=record['sha256'],length=record['bytes'])
        if ev.blob(SCIENCE,record['path'])!=raw:raise ValueError('science-origin member changed')
        if record['path'].endswith('.json'):components[Path(record['path']).name]=json.loads(raw)
    if sha(checked_blob(A+'/production_results.json'))!=RESULT or manifest['prediction_payload_sha256']!=RESULT:
        raise ValueError('production result SHA mismatch')
    expected_ids={'protocol_sha256':PROTOCOL,'numerical_contract_sha256':NUMERICAL,'execution_code_sha256':CODE_A}
    if any(manifest.get(k)!=v for k,v in expected_ids.items()):raise ValueError('manifest v3 authority mismatch')
    protocol_raw=checked_blob(A0+'/fs_r1_protocol_v3.json',expected_sha=PROTOCOL);p=json.loads(protocol_raw)
    checked_blob(A0+'/fs_r1_numerical_contract_v1.json',expected_sha=NUMERICAL)
    bundle=json.loads(checked_blob(A0+'/execution_code_identity.json'))
    if sha(canonical(bundle))!=CODE_A:raise ValueError('execution code bundle mismatch')
    sys.path.insert(0,str(ROOT/A0))
    from a0_common import execution_paths
    if set(bundle['sha256'])!=set(execution_paths()):raise ValueError('execution code members incomplete')
    for path,digest in bundle['sha256'].items():checked_blob(path,expected_sha=digest)
    sources={s['condition']:{k:s[k] for k in ('source_identity_sha256','new_H_sha256','operational_archive_sha256')} for s in p['systems']}
    if manifest['source_hashes']!=sources or external.get('source_hashes')!=sources:raise ValueError('source identity mismatch')
    identities=json.loads(checked_blob(R0+'/new_source_identity.json'))['identities']
    registry=json.loads(checked_blob(R0+'/new_source_registry.json'))['sources']
    for spec in p['systems']:
        identity=next(i for i in identities if i['condition']==spec['condition'])
        record=next(i for i in registry if i['condition']==spec['condition'])
        if sha(canonical(identity))!=spec['source_identity_sha256'] or identity['hamiltonian_sha256']!=spec['new_H_sha256']:
            raise ValueError('source identity canonical/H mismatch')
        if record['source_identity_sha256']!=spec['source_identity_sha256'] or record['operational_archive_sha256']!=spec['operational_archive_sha256']:
            raise ValueError('operational archive identity mismatch')
    # Sanitized archive/member byte checks only; never np.load, CSR decode or
    # original pickle open. Reuse the unchanged historical metadata audit.
    import ast,importlib.util
    audit_path='artifacts/pf_first_study_fs_r1_phase_a_20261007/build_audit.py'
    checked_blob(audit_path)
    module_spec=importlib.util.spec_from_file_location('b0_archive_byte_audit',ROOT/audit_path)
    audit=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(audit)
    audit.ROOT=Path(root);audit.BASE=HANDOFF
    tree=ast.parse(checked_blob(R0+'/source_io.py'))
    keys=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='META_KEYS' for t in n.targets))
    archive_checks=[audit.check_archive(next(r for r in registry if r['condition']==spec['condition']),
        next(i for i in identities if i['condition']==spec['condition']),keys) for spec in p['systems']]
    ladder_raw=checked_blob(R01+'/branch_ladder.json',expected_sha=LADDER)
    if p['truth_contract']['ladder_sha256']!=LADDER:raise ValueError('v3 branch ladder mismatch')
    payload=components['production_results.json']
    validate_saved_components(payload,components,p)
    # Published origin receipt has a different schema/commit role from the new
    # independent handoff receipt. Validate its actual maps, not just PASS.
    old_raw=checked_blob(A+'/remote_verification.json');old=json.loads(old_raw)
    if (old.get('status')!='PASS' or old.get('remote_fetched_independently') is not True or
        old.get('remote_verified_commit')!=SCIENCE or old.get('origin_result_commit')!=SCIENCE or
        old.get('manifest_sha256')!=PREDICTION or old.get('prediction_payload_sha256')!=RESULT):
        raise ValueError('published science remote receipt mismatch')
    for path,digest in old['verified_file_sha256'].items():
        raw=checked_blob(path,SCIENCE,expected_sha=digest)
        if ev.blob(HANDOFF,path)!=raw:raise ValueError('handoff changed science blob')
    for record in old['authority_records']:
        checked_blob(record['path'],SCIENCE,expected_sha=record['sha256'])
    for k,v in expected_ids.items():
        if old.get(k)!=v or external.get(k)!=v:raise ValueError('remote authority identity mismatch')
    auth=components['authorization_receipt.json'];recovery=components['private_recovery_receipt.json']
    binding=auth['binding']
    if sha(canonical(auth['authorization']))!=binding['authorization_sha256'] or recovery['binding']!=binding:
        raise ValueError('recovery authorization binding mismatch')
    if any(binding.get(k)!=v for k,v in {'protocol_sha256':PROTOCOL,'execution_code_sha256':CODE_A,'source_hashes':sources}.items()):
        raise ValueError('recovery source/protocol/code mismatch')
    if recovery['RUN_STARTED_sha256']!=auth['RUN_STARTED_sha256'] or recovery['run_id']!=auth['run_id']:
        raise ValueError('recovery run lease mismatch')
    ret=recovery['public_return_receipt']
    if (recovery['private_recovery_before_public'] is not True or recovery['initial_aggregate_before_cold'] is not True or
        ret['recovery_saved_before_public'] is not True or ret['public_matches_recovery'] is not True or
        ret['public_sha256']!=RESULT or ret['recovery_sha256']!=manifest['recovery_snapshot_sha256'] or ret['production_rerun'] is not False):
        raise ValueError('recovery saved-before-public/result mismatch')
    from recovery_wrapper import load_return
    private_checks=[]
    snapshots=recovery['snapshots']
    expected=['initial_operational_N2_active_eq_sto3g','initial_operational_CO_active_eq_sto3g','initial_operational_complete',
        'cold_validation_N2_active_eq_sto3g','cold_validation_CO_active_eq_sto3g','cold_validation_complete','phase_a_complete']
    if [r['category'] for r in snapshots]!=expected:raise ValueError('recovery coverage/order mismatch')
    for record in snapshots:
        path=Path(record['private_path'])
        if not path.is_file():raise ValueError('private recovery snapshot absent; NO-GO')
        snapshot,raw=load_return(path)
        if (sha(raw)!=record['sha256'] or len(raw)!=record['bytes'] or snapshot['binding']!=binding or
            snapshot['category']!=record['category'] or snapshot['RUN_STARTED_sha256']!=auth['RUN_STARTED_sha256'] or snapshot['run_id']!=auth['run_id']):
            raise ValueError('private recovery integrity mismatch')
        category=record['category']
        expected_payload=payload if category=='phase_a_complete' else (
            payload[category.removesuffix('_complete')] if category.endswith('_complete') else
            next(r for r in payload['initial_operational' if category.startswith('initial_operational') else 'cold_validation'] if category.endswith(r['condition'])))
        if snapshot['payload']!=expected_payload:raise ValueError('private/public scalar recovery mismatch')
        private_checks.append(dict(category=category,sha256=sha(raw),read_only=True))
    if manifest['truth_access']!=components['truth_access_audit.json']['counts'] or not manifest['phase_a_complete'] or not manifest['cold_replay_pass'] or not manifest['all_numerical_gates_pass'] or not manifest['all_arms_have_finite_budget_intervals']:
        raise ValueError('Phase A completeness/truth evidence mismatch')
    data=dict(science_origin_commit=SCIENCE,handoff_commit=HANDOFF,prediction_sha256=PREDICTION,
        production_results_sha256=RESULT,protocol_sha256=PROTOCOL,numerical_contract_sha256=NUMERICAL,
        phase_a_execution_code_sha256=CODE_A,source_hashes=sources,protocol=p,payload=payload,
        branch_ladder=json.loads(ladder_raw),branch_ladder_sha256=LADDER,
        remote_receipt_sha256=sha(external_raw),published_origin_receipt_sha256=sha(old_raw),
        private_recovery_checks=private_checks,archive_byte_checks=archive_checks,phase_a_authorization_id=binding['authorization_id'],
        checked_blob_sha256=checked,handoff_additions=changes,oracle_decode=0,Phase_B_authorized=False)
    return _issue_verified_freeze(data)
