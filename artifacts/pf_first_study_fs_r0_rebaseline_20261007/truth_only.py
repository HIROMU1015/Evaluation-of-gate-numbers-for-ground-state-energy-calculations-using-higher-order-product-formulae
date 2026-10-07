"""New-source truth interface: barrier first; no historical fallback.

Physical branch continuation needs a separately closed new-source anchor
contract. This module deliberately cannot fabricate a maximum-overlap substitute.
"""
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from scipy.linalg import schur
from freeze import verify_phase_a

def validate_truth_rows(rows,protocol):
    expected={s['condition']:s for s in protocol['systems']}
    if len(rows)!=2 or {r['condition'] for r in rows}!=set(expected):
        raise ValueError('exactly two unique new truth coordinates required')
    for row in rows:
        spec=expected[row['condition']]
        if row.get('provenance')!='FS-R1-new-source-direct': raise ValueError('historical truth path/provenance rejected')
        if row.get('source_identity_sha256')!=spec['source_identity_sha256']: raise ValueError('truth source changed')
        if float(row['time']).hex()!=float(spec['t0']).hex(): raise ValueError('nearest-time substitution rejected')
        label=row.get('branch_id')
        if not isinstance(label,str) or not label.startswith('FS-R1:'+spec['source_identity_sha256']+':'):
            raise ValueError('historical branch ID cannot identify new truth')
        if row.get('branch_status')!='resolved': raise ValueError('physical branch unresolved')
        for key in ('unitarity_residual','eigenpair_residual'):
            if not np.isfinite(row.get(key,np.nan)) or row[key]>1e-10 or row[key]<0:
                raise ValueError('truth numerical gate')
        if not np.isfinite(row.get('signed_direct',np.nan)): raise ValueError('nonfinite truth')
    return True

def continue_schur_at_target(unitary,ground,energy,t,anchor,branch_id):
    """Reusable guarded Schur step, no source/old-value lookup.

    Only toy tests call it in FS-R0. For a future physical call, a valid
    same-new-source anchor is mandatory. No extra coordinates are generated here.
    """
    if anchor is None: raise RuntimeError('NEW_SOURCE_CONTINUATION_ANCHOR_UNAVAILABLE')
    if anchor['time']>=t: raise ValueError('lower-time continuation anchor required')
    triangular,vectors=schur(unitary,output='complex',check_finite=True)
    eigenvalues=np.diag(triangular)
    probabilities=abs(vectors.conj().T @ anchor['vector'])**2
    index=int(np.argmax(probabilities)); vector=vectors[:,index]; value=eigenvalues[index]
    if probabilities[index]<0.9: raise RuntimeError('branch continuity quality gate')
    gaps=abs(np.angle(eigenvalues/value))
    if any(gaps[j]<1e-8 for j in range(len(gaps)) if j!=index):
        raise RuntimeError('degenerate branch needs projector continuation contract')
    unitarity=float(np.linalg.norm(unitary.conj().T @ unitary-np.eye(len(unitary))))
    residual=float(np.linalg.norm(unitary @ vector-value*vector))
    if unitarity>1e-10 or residual>1e-10: raise RuntimeError('Schur numeric gate')
    return dict(signed_direct=float(np.angle(np.exp(-1j*energy*t)*value)/t),
                branch_id=branch_id,branch_status='resolved',unitarity_residual=unitarity,
                eigenpair_residual=residual,previous_overlap=float(probabilities[index]))

def dispatch_new_truth(root,commit,manifest_path,manifest_sha,remote_receipt,context,algorithm):
    def after_barrier(proof):
        context.guard()
        contract=proof['protocol']['truth_contract']
        if contract.get('branch_continuation_closed') is not True:
            raise RuntimeError('NEW_SOURCE_BRANCH_CONTINUATION_CONTRACT_UNCLOSED')
        return algorithm(proof)
    return verify_phase_a(root,commit,manifest_path,manifest_sha,remote_receipt,after_barrier)
