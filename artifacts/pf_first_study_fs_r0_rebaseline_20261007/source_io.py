"""Identity-only canonical operational export. No observable/state construction."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import zipfile
import numpy as np
from scipy.sparse import csr_matrix

META_KEYS = ('condition','geometry_angstrom','basis','charge','multiplicity',
    'total_spatial_orbitals','total_electron_count','active_electron_count',
    'frozen_core_spatial_orbitals','active_spatial_orbitals','n_alpha','n_beta',
    'population_sector_dimension','restricted_dimension','z2_mask','z2_target',
    'removed_constant_hartree','group_count','term_counts','group_sha256')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def array_identity(array):
    a=np.asarray(array)
    if a.dtype.hasobject:
        raise ValueError('object array forbidden')
    header=dict(dtype=a.dtype.str,shape=list(a.shape))
    # Keep C0.6's array-digest convention; no newline in its header.
    digest=sha(json.dumps(header,sort_keys=True,separators=(',',':')).encode()+a.tobytes(order='C'))
    return dict(header,bytes=a.nbytes,sha256=digest,serialization='original dtype, logical C-order bytes; no phase/cast/reorder')

def sparse_hash(H):
    h=hashlib.sha256(np.asarray(H.shape,dtype=np.int64).tobytes())
    for a in (H.indptr,H.indices,H.data): h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()

def durable_create(path,raw):
    path=Path(path)
    with path.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    path.chmod(0o400)
    fd=os.open(path.parent,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def group_records(groups):
    # Sorting Pauli terms only reproduces native _group_hashes content encoding.
    # The group list and spectrum/batch/index ordering are never sorted.
    return [[[list(map(list,term)),float(complex(c).real),float(complex(c).imag)]
             for term,c in sorted(g.terms.items())] for g in groups]

def export_operational(decoded,sequence,destination,expected_H):
    system=decoded['system']; metadata=decoded['metadata']; H=system['hamiltonian']
    if sparse_hash(H)!=expected_H: raise ValueError('new frozen H identity mismatch')
    groups=group_records(decoded['ordered_groups'])
    hashes=[sha(json.dumps(g,separators=(',',':')).encode()) for g in groups]
    if hashes!=metadata['group_sha256']: raise ValueError('ordered group metadata mismatch')
    if len(groups)!=len(system['component_spectra']) or len(groups)!=metadata['group_count']:
        raise ValueError('group count mismatch')
    arrays={}; manifest={}
    def add(name,array,member):
        a=np.asarray(array); identity=array_identity(a)
        buf=io.BytesIO(); np.save(buf,a,allow_pickle=False)
        raw=buf.getvalue(); arrays[name+'.npy']=raw
        manifest[name]=dict(identity,file_sha256=sha(raw),file_bytes=len(raw),source_member=member)
    for name,a in [('H_data',H.data),('H_indices',H.indices),('H_indptr',H.indptr),
                   ('H_shape',np.asarray(H.shape,dtype=np.int64)),('CISD',system['states']['cisd']),
                   ('restricted_basis',system['restricted_basis'])]:
        member={'H_data':'hamiltonian.data','H_indices':'hamiltonian.indices','H_indptr':'hamiltonian.indptr',
                'H_shape':'hamiltonian.shape','CISD':'states.cisd'}.get(name,name)
        add(name,a,'system.'+member)
    spectra=[]
    for i,s in enumerate(system['component_spectra']):
        batches=[]
        for j,b in enumerate(s.batches):
            names={}
            for field in ('indices','eigenvalues','eigenvectors'):
                value=getattr(b,field)
                if value is None: names[field]=None
                else:
                    name=f'g{i:03d}_b{j:02d}_{field}'
                    add(name,value,f'system.component_spectra[{i}].batches[{j}].{field}')
                    names[field]=name
            batches.append(names)
        spectra.append(dict(dimension=s.dimension,batches=batches,source_nnz=s.source_nnz,
                            component_count=s.component_count,maximum_component_size=s.maximum_component_size,
                            retained_complex_elements=s.retained_complex_elements))
    operational=dict(format='FS-R0-operational-v1',metadata={k:metadata[k] for k in META_KEYS},
        ordered_groups=groups,component_spectra=spectra,current_m3_sequence=list(sequence),arrays=manifest)
    raw_metadata=canonical(operational)
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        for name,raw in [('operational.json',raw_metadata),*arrays.items()]:
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); entry.external_attr=0o400<<16
            z.writestr(entry,raw)
    raw=archive.getvalue(); destination=Path(destination)
    destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    durable_create(destination/'source.npz',raw)
    durable_create(destination/'source.sha256',(sha(raw)+'\n').encode())
    identity=dict(format='FS-R0-new-source-identity-v1',source_kind='FS-C0.6 one-shot pinned reconstruction',
        source_archive_sha256=sha(raw),source_archive_bytes=len(raw),
        hamiltonian_sha256=sparse_hash(H),CISD=manifest['CISD'],restricted_basis=manifest['restricted_basis'],
        ordered_group_sha256=hashes,ordered_group_identity_sha256=sha(canonical(hashes)),
        component_sha256=[sha(canonical([{f:None if name is None else manifest[name]['sha256']
                                         for f,name in b.items()} for b in s['batches']])) for s in spectra],
        sector_metadata_sha256=sha(canonical(operational['metadata'])),
        operational_metadata_sha256=sha(raw_metadata),removed_constant=metadata['removed_constant_hartree'],
        H_dtype=H.dtype.str,H_shape=list(H.shape),arrays=manifest,
        group_order_rule='stored list/group/batch/index/application order preserved',
        serialization='ZIP_STORED, fixed epoch, deterministic member insertion; npy allow_pickle=False',
        ground_oracle_exported=False)
    return identity

def load_operational(path,expected_sha,native):
    raw=Path(path).read_bytes()
    if sha(raw)!=expected_sha: raise ValueError('operational archive SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if len(set(names))!=len(names) or any(not re.fullmatch(r'[A-Za-z0-9_]+\.(npy|json)',n) for n in names):
            raise ValueError('duplicate/invalid source archive member')
        meta=json.loads(z.read('operational.json'))
        expected={'operational.json'}|{n+'.npy' for n in meta['arrays']}
        if set(names)!=expected or set(meta)!= {'format','metadata','ordered_groups','component_spectra','current_m3_sequence','arrays'}:
            raise ValueError('extra/oracle source archive field')
        if set(meta['metadata'])!=set(META_KEYS): raise ValueError('extra/oracle metadata')
        if meta['format']!='FS-R0-operational-v1': raise ValueError('operational format')
        allowed={'H_data','H_indices','H_indptr','H_shape','CISD','restricted_basis'}
        for s in meta['component_spectra']:
            if set(s)!={'dimension','batches','source_nnz','component_count','maximum_component_size','retained_complex_elements'}:
                raise ValueError('extra/oracle component field')
            for batch in s['batches']:
                if set(batch)!= {'indices','eigenvalues','eigenvectors'}: raise ValueError('component metadata fields')
                allowed.update(n for n in batch.values() if n is not None)
        if set(meta['arrays'])!=allowed: raise ValueError('extra/oracle array')
        arrays={}
        for name,record in meta['arrays'].items():
            b=z.read(name+'.npy')
            if sha(b)!=record['file_sha256']: raise ValueError('array file identity mismatch')
            a=np.load(io.BytesIO(b),allow_pickle=False)
            if array_identity(a)['sha256']!=record['sha256']: raise ValueError('array identity mismatch')
            a.flags.writeable=False; arrays[name]=a
    H=csr_matrix((arrays['H_data'],arrays['H_indices'],arrays['H_indptr']),shape=tuple(arrays['H_shape']),copy=False)
    B,S=native['ComponentBatch'],native['ComponentSpectrum']
    spectra=[]
    for s in meta['component_spectra']:
        batches=tuple(B(*(None if b[f] is None else arrays[b[f]] for f in ('indices','eigenvalues','eigenvectors'))) for b in s['batches'])
        spectra.append(S(s['dimension'],batches,s['source_nnz'],s['component_count'],s['maximum_component_size'],s['retained_complex_elements']))
    return dict(hamiltonian=H,cisd=arrays['CISD'],restricted_basis=arrays['restricted_basis'],
                component_spectra=spectra,metadata=meta['metadata'],current_m3_sequence=meta['current_m3_sequence'],
                ordered_groups=meta['ordered_groups'])
