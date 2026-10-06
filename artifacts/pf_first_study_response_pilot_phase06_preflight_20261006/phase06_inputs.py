"""Phase A allowlist: exactly H, ordered groups, and CISD; identity-only preflight."""
from dataclasses import dataclass
from pathlib import Path
import io,json,subprocess,zipfile
import numpy as np
from phase06_contract import BASE,GateError,sha

@dataclass(frozen=True,slots=True)
class PhaseAData:
    H:np.ndarray
    groups:tuple
    psi:np.ndarray
    metadata:dict
    identity_audit:dict
    domain:str

def array_hash(a):
    prefix=(a.dtype.str+'\n'+json.dumps(list(a.shape),separators=(',',':'))+'\n').encode()
    return sha(prefix+np.ascontiguousarray(a).tobytes())

def blob_id(raw):return __import__('hashlib').sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def _git(root,*args):return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()

def verified_archive_bytes(root,bundle):
    root=Path(root).resolve(); path=(root/bundle['path']).resolve()
    if not path.is_relative_to(root) or path.suffix!='.npz':
        raise GateError('failed_source_identity: archive path outside allowlist root')
    raw=path.read_bytes()
    expected_blob=_git(root,'rev-parse',BASE+':'+bundle['path'])
    origin_blob=_git(root,'rev-parse',bundle['publication_commit']+':'+bundle['path'])
    if sha(raw)!=bundle['sha256'] or blob_id(raw)!=expected_blob or origin_blob!=expected_blob:
        raise GateError('failed_source_identity: file SHA/blob mismatch before decode')
    return raw,{'path':bundle['path'],'sha256':sha(raw),'git_blob_sha':expected_blob,
        'origin_result_commit':bundle['publication_commit'],'verified_snapshot_commit':BASE,
        'generation_worktree_head':bundle['generation_worktree_head_recorded_by_manifest'],
        'generation_worktree_was_dirty':bundle['generation_worktree_was_dirty']}

class AllowlistArchive:
    """No arbitrary NPZ getter; forbidden member rejected before ZipFile.open."""
    def __init__(self,raw,spec):
        self._raw=raw;self._spec=spec;self.opened=[]

    def read(self,key):
        if key not in self._spec:raise GateError('failed_source_identity: member outside Phase A allowlist')
        shape,expected=self._spec[key]
        with zipfile.ZipFile(io.BytesIO(self._raw)) as archive:
            name=key+'.npy'
            if archive.namelist().count(name)!=1:
                raise GateError('failed_source_identity: missing/duplicate allowlisted member')
            self.opened.append(name)
            with archive.open(name) as stream:
                a=np.lib.format.read_array(stream,allow_pickle=False)
        if a.dtype.str!='<c16' or a.shape!=tuple(shape) or array_hash(a)!=expected:
            raise GateError('failed_source_identity: array hash/dtype/shape mismatch')
        a.flags.writeable=False
        return a

def load_phase_a_inputs(root,contract):
    # Identity decoding only. No norms, H products, eigensolves, PF, state normalization.
    contract.verify()
    s=contract.identity;a=s['h4_arrays'];meta=s['molecular_metadata'];n=meta['h4_sector_dimension']
    groups=a['ordered_group_keys'];hashes=a['ordered_group_sha256']
    whitelist=[a['experiment_hamiltonian_key'],*groups,s['cisd']['key']]
    if whitelist!=s['phase_a_array_allowlist'] or n!=36 or len(groups)!=13 or groups!=[f'H4_group_{i:03d}' for i in range(13)]:
        raise GateError('failed_source_identity: metadata/group ordering mismatch')
    sequence_hash=sha(''.join(hashes).encode())
    indices=np.asarray(meta['h4_sector_full_indices'],dtype=np.int64)
    if sequence_hash!=a['ordered_group_sequence_sha256'] or array_hash(indices)!=a['sector_indices_sha256']:
        raise GateError('failed_source_identity: sequence/sector identity mismatch')
    rawf,fid=verified_archive_bytes(root,s['f01_bundle'])
    raws,sid=verified_archive_bytes(root,s['h01_state_bundle'])
    spec={a['experiment_hamiltonian_key']:((n,n),a['experiment_hamiltonian_sha256'])}
    spec.update({key:((n,n),value) for key,value in zip(groups,hashes,strict=True)})
    f=AllowlistArchive(rawf,spec);states=AllowlistArchive(raws,{s['cisd']['key']:((n,),s['cisd']['sha256'])})
    H=f.read(a['experiment_hamiltonian_key']);g=tuple(f.read(key) for key in groups);psi=states.read(s['cisd']['key'])
    identities=[{'key':key,'dtype':value.dtype.str,'shape':list(value.shape),'sha256':array_hash(value)} for key,value in zip(whitelist,[H,*g,psi],strict=True)]
    audit={'status':'passed','mode':'identity_only_no_science_arithmetic','archives':[fid,sid],
        'arrays':identities,'members_opened':f.opened+states.opened,'forbidden_members_opened':[],
        'metadata_sha256':sha(json.dumps(meta,sort_keys=True,separators=(',',':')).encode()),
        'ordered_group_identity':list(zip(groups,hashes)),
        'ordered_group_sequence_hash_frozen':a['ordered_group_sequence_sha256'],
        'sector_indices_hash_frozen':a['sector_indices_sha256'],
        'science_action_count':0,'production_norms_or_products_computed':False}
    return PhaseAData(H,g,psi,meta,audit,'production')

def synthetic_inputs(H,groups,psi):
    return PhaseAData(np.asarray(H,complex),tuple(np.asarray(g,complex) for g in groups),
        np.asarray(psi,complex),{'fixture':'synthetic'},{'fixture':'synthetic'},'synthetic')
