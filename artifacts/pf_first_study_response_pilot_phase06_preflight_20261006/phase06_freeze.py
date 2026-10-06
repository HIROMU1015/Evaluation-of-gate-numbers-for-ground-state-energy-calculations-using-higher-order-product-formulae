"""Strict scalar schema, create-only artifact, Git/remote publication receipt."""
from pathlib import Path
import json,re,subprocess,os
from jsonschema import Draft202012Validator
from phase06_contract import BASE,PH05,PROTOCOL_SHA,GateError,canonical,sha

REPO='HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae'
PREFIX='artifacts/pf_first_study_response_pilot_phase_a_'

def validate_artifact(payload,schema):
    canonical(payload) # Reject NaN/Infinity before any freeze/reader handoff.
    Draft202012Validator(schema).validate(payload)
    # Exact coordinates/arm keys are checked in addition to structural JSON schema.
    if payload['source']['protocol_sha256']!=PROTOCOL_SHA:raise GateError('artifact protocol mismatch')
    if sha(canonical(payload['source']['code_files']))!=payload['source']['code_sha256']:
        raise GateError('artifact code identity mismatch')
    if sha(canonical(payload['source']['input_array_identities']))!=payload['source']['source_sha256']:
        raise GateError('artifact source identity mismatch')
    train=(.1,.15,.2,.25,.3);evaluate=(.125,.175,.225,.275,.35,.4)
    coordinates={s*t for t in train+evaluate for s in (1,-1)}
    if len(payload['rows'])!=22 or {r['time'] for r in payload['rows']}!=coordinates:
        raise GateError('artifact signed grid mismatch')
    for arm,rows in payload['predictions'].items():
        if len(rows)!=12 or {r['time'] for r in rows}!={s*t for t in evaluate for s in (1,-1)}:
            raise GateError('prediction grid mismatch')
        for row in rows:
            model=payload['fits'][arm]['raw_positive_even_two_term']
            expected=sum(c*row['time']**p for c,p in zip(model['coefficients'],model['powers'],strict=True))
            if row['prediction']!=expected or row['fit_status']!=model['status']:
                raise GateError('prediction does not match frozen fitted coefficients/status')
    for arm,models in payload['fits'].items():
        for name,model in models.items():
            if name!='odd_diagnostic' and (model['a4']!=model['coefficients'][0] or model['a6']!=model['coefficients'][1]):
                raise GateError('a4/a6 coefficient identity mismatch')
    if payload['replay']['cache_isolation_passed'] is not True:
        raise GateError('incomplete cold replay')

def code_identity(directory):
    directory=Path(directory);root=directory.parents[1]
    paths=[*directory.glob('phase06_*.py'),directory/'phase_a_schema.json']
    return {str(path.relative_to(root)):sha(path.read_bytes()) for path in sorted(paths)}

def verify_committed_code(root,directory,transport=None):
    """Stop before science if the executable/schema differ from their Git snapshot."""
    transport=transport or GitTransport(root)
    identities=code_identity(directory)
    for path,digest in identities.items():
        if sha(transport.blob('HEAD',path))!=digest:
            raise GateError('uncommitted implementation/schema; stop before production science')
    return identities

def write_phase_a_artifact(output,payload,schema,private_diagnostics,private_output):
    validate_artifact(payload,schema)
    output=Path(output);private_output=Path(private_output)
    if output.exists() or private_output.exists():raise GateError('immutable artifact: output already exists')
    if private_output.resolve().is_relative_to(output.resolve().parents[1]):
        raise GateError('private projected matrices must be outside repository artifact area')
    output.mkdir(parents=True,exist_ok=False)
    private_output.mkdir(parents=True,exist_ok=False)
    raw=canonical(payload)
    # Exclusive create: future Phase A never overwrites a frozen artifact.
    with (output/'phase_a.json').open('xb') as f:f.write(raw)
    manifest={'self_exclusion':['phase_a_manifest.json'],'files':[{'path':'phase_a.json','sha256':sha(raw),'bytes':len(raw)}],
        'protocol_sha256':payload['source']['protocol_sha256'],'code_sha256':payload['source']['code_sha256'],
        'source_sha256':payload['source']['source_sha256'],'private_projected_diagnostics_published':False}
    with (output/'phase_a_manifest.json').open('xb') as f:f.write(canonical(manifest))
    with (private_output/'projected_diagnostics.json').open('xb') as f:f.write(canonical(private_diagnostics))
    return manifest

class GitTransport:
    def __init__(self,root):self.root=Path(root)
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args])
    def allowed_remote(self):
        for args in [('remote','get-url','origin'),('remote','get-url','--push','origin')]:
            url=self.git(*args).decode().strip()
            if url not in (f'git@github.com:{REPO}.git',f'https://github.com/{REPO}.git'):
                raise GateError('repository remote outside allowed HIROMU1015 target')
    def blob(self,commit,path):return self.git('show',commit+':'+path)
    def remote_tip(self,branch):
        if not re.fullmatch(r'[A-Za-z0-9._/-]+',branch):raise GateError('invalid branch')
        out=self.git('ls-remote','--heads','origin','refs/heads/'+branch).decode().split()
        if len(out)!=2:raise GateError('published Phase A branch missing')
        return out[0]

def publish_phase_a(root,output,authorization):
    if authorization is None or authorization.phase!='phase-a' or authorization.protocol_sha256!=PROTOCOL_SHA:
        raise GateError('science_not_authorized: Phase A publication requires approved execution')
    root=Path(root).resolve();out=Path(output).resolve();relative=str(out.relative_to(root))
    if not relative.startswith(PREFIX):raise GateError('Phase A publication path outside dedicated artifact namespace')
    transport=GitTransport(root);transport.allowed_remote()
    branch=transport.git('branch','--show-current').decode().strip()
    if not branch or branch in ('main','master'):raise GateError('dedicated research branch required')
    if transport.git('diff','--cached','--name-only').strip():raise GateError('unrelated staged files; stop without reset/stash')
    # Stage only the two public scalar files, no .runtime/array/state data.
    paths=[relative+'/phase_a.json',relative+'/phase_a_manifest.json']
    transport.git('add','--',*paths)
    staged=transport.git('diff','--cached','--name-only').decode().splitlines()
    if sorted(staged)!=sorted(paths):raise GateError('publication stage whitelist mismatch')
    transport.git('diff','--cached','--check')
    transport.git('commit','-m','Freeze response pilot Phase A predictions before saved-truth scoring')
    commit=transport.git('rev-parse','HEAD').decode().strip()
    transport.git('push','origin','HEAD:refs/heads/'+branch)
    if transport.remote_tip(branch)!=commit:raise GateError('remote publication SHA mismatch')
    for path in paths:
        if transport.blob(commit,path)!=(root/path).read_bytes():raise GateError('published committed scalar blob mismatch')
    payload=json.loads((out/'phase_a.json').read_bytes())
    return {'commit':commit,'branch':branch,'prediction_path':paths[0],
        'prediction_sha256':sha((out/'phase_a.json').read_bytes()),
        'protocol_sha256':payload['source']['protocol_sha256'],'source_sha256':payload['source']['source_sha256'],
        'code_sha256':payload['source']['code_sha256'],'publication_verified':True}

def verify_phase_a_freeze(root,receipt,contract,schema,transport=None):
    # This function has no truth loader. Its successful return is the reader gate.
    contract.verify()
    if not isinstance(receipt,dict) or not re.fullmatch(r'[0-9a-f]{40}',receipt.get('commit','')):
        raise GateError('Phase A full commit freeze missing')
    path=receipt.get('prediction_path','')
    if not path.startswith(PREFIX) or not path.endswith('/phase_a.json') or '..' in path.split('/'):
        raise GateError('invalid frozen prediction path')
    if receipt.get('publication_verified') is not True or receipt.get('protocol_sha256')!=PROTOCOL_SHA:
        raise GateError('Phase A publication/protocol receipt mismatch')
    transport=transport or GitTransport(root);transport.allowed_remote()
    if transport.remote_tip(receipt.get('branch',''))!=receipt['commit']:
        raise GateError('remote/local Phase A identity mismatch')
    if sha(transport.blob(receipt['commit'],PH05+'/response_pilot_protocol.json'))!=PROTOCOL_SHA:
        raise GateError('committed normative protocol identity mismatch before truth')
    raw=(Path(root)/path).read_bytes()
    if raw!=transport.blob(receipt['commit'],path) or sha(raw)!=receipt.get('prediction_sha256'):
        raise GateError('altered prediction blob/hash; stop before truth')
    manifest=json.loads(transport.blob(receipt['commit'],str(Path(path).with_name('phase_a_manifest.json'))))
    if manifest['files']!=[{'path':'phase_a.json','sha256':sha(raw),'bytes':len(raw)}]:
        raise GateError('frozen prediction manifest mismatch')
    payload=json.loads(raw);validate_artifact(payload,schema)
    for field in ('protocol_sha256','source_sha256','code_sha256'):
        if receipt.get(field)!=payload['source'][field] or manifest.get(field)!=payload['source'][field]:
            raise GateError('Phase A receipt identity mismatch: '+field)
    for path,digest in payload['source']['code_files'].items():
        if path.startswith('/') or '..' in path.split('/') or not (path.endswith('.py') or path.endswith('/phase_a_schema.json')):
            raise GateError('invalid frozen code path')
        if sha(transport.blob(receipt['commit'],path))!=digest or sha((Path(root)/path).read_bytes())!=digest:
            raise GateError('code identity mismatch before truth')
    if payload['input_domain']=='production':
        from phase06_inputs import load_phase_a_inputs
        # Identity-only reload: no norm/matvec/PF calculation.
        audit=load_phase_a_inputs(root,contract).identity_audit
        if sha(canonical(audit))!=receipt['source_sha256']:
            raise GateError('source identity changed after Phase A freeze')
    return payload,raw
