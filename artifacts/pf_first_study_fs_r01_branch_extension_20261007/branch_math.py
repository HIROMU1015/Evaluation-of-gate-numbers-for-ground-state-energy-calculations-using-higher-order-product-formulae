"""Deterministic Schur branch selection; no source loader or production dispatch."""
import numpy as np
from scipy.linalg import schur

GAP=1e-8
OVERLAP=.9
RESIDUAL=1e-10

class BranchFailure(RuntimeError):
    def __init__(self,reason):
        super().__init__('BRANCH_CONTINUATION_FAILED: '+reason);self.reason=reason

def fail(reason):raise BranchFailure(reason)

def normalized(vector,n):
    v=np.asarray(vector,dtype=np.complex128)
    if v.shape!=(n,) or not np.isfinite(v).all():fail('nonfinite/wrong-shape vector')
    if abs(float(np.vdot(v,v).real)-1)>1e-12:fail('selected-vector normalization')
    return v

def phase_fix(vector):
    pivot=int(np.argmax(abs(vector)))
    return vector*np.exp(-1j*np.angle(vector[pivot]))

def namespace(source,index):
    if not isinstance(source,str) or len(source)!=64 or any(c not in '0123456789abcdef' for c in source):
        fail('source identity format')
    return f'FS-R1:{source}:positive:k{index}'

def validate_branch_id(value,source,index):
    if value!=namespace(source,index):fail('historical/wrong-source branch ID')

def ordered_eigenpairs(values,vectors):
    values=np.asarray(values,dtype=np.complex128);vectors=np.asarray(vectors,dtype=np.complex128)
    n=len(values)
    if values.shape!=(n,) or vectors.shape!=(n,n) or not np.isfinite(values).all() or not np.isfinite(vectors).all():fail('nonfinite eigenpairs')
    if np.any(abs(values)==0):fail('zero eigenvalue')
    if np.linalg.norm(vectors.conj().T @ vectors-np.eye(n),ord='fro')>RESIDUAL:fail('duplicate/nonorthogonal eigenbranch assignment')
    order=sorted(range(n),key=lambda j:(float(np.angle(values[j])),float(values[j].real),float(values[j].imag),j))
    return values[order],vectors[:,order]

def clusters(values):
    """Circular phase components under strict < GAP, with chain ambiguity rejected."""
    n=len(values);parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    phases=np.angle(values);order=np.argsort(phases,kind='stable')
    for a,b in zip(order,np.roll(order,-1)):
        if a!=b and abs(float(np.angle(values[a]/values[b])))<GAP:
            x,y=find(int(a)),find(int(b));parent[max(x,y)]=min(x,y)
    out={}
    for i in range(n):out.setdefault(find(i),[]).append(i)
    result=sorted(out.values(),key=lambda group:group[0])
    for group in result:
        for j in group:
            if any(abs(float(np.angle(values[j]/values[k])))>=GAP for k in group):fail('ambiguous chained phase cluster')
    return result

def choose(values,vectors,ground,previous=None,context=None):
    """Singleton: argmax vector overlap. Cluster: argmax projector overlap.

    Ties use the lowest deterministic phase ordinal. Inside a cluster use the
    normalized projection of the reference; its eigenpair residual must still
    pass. No perturbed-eigenvector substitution or extra truth is attempted.
    """
    if context is None:
        if len(values)>16:raise PermissionError('standalone matcher is synthetic only')
    else:
        if context.phase not in ('synthetic','FS-R1-Phase-B'):raise PermissionError('truth branch selection is Phase B only')
        context.guard(len(values))
    values,vectors=ordered_eigenpairs(values,vectors);n=len(values)
    ground=normalized(ground,n);reference=ground if previous is None else normalized(previous,n)
    partitions=clusters(values)
    probabilities=abs(vectors.conj().T @ reference)**2
    ground_prob=abs(vectors.conj().T @ ground)**2
    # Projector aggregation prevents arbitrary degenerate basis rotations from
    # changing the physical eigenspace identity. Singletons reduce to argmax.
    masses=[float(sum(probabilities[group])) for group in partitions]
    comparator=int(np.argmax(ground_prob))
    chosen=(next(i for i,group in enumerate(partitions) if comparator in group)
            if previous is None else int(np.argmax(masses)))
    group=partitions[chosen]
    projection=vectors[:,group] @ (vectors[:,group].conj().T @ reference)
    norm=float(np.linalg.norm(projection))
    if norm<=np.finfo(float).tiny:fail('ambiguous zero projector continuation')
    vector=phase_fix(projection/norm)
    selected_overlap=float(abs(np.vdot(reference,vector))**2)
    if previous is not None and selected_overlap<OVERLAP:fail('previous overlap below 0.9')
    # Eigenphase representative is the circular centroid. A truly degenerate
    # cluster is basis invariant; a near cluster is accepted only if the strict
    # eigenpair gate also passes on the projected vector.
    phase=float(np.angle(sum(values[group]/abs(values[group]))))
    value=complex(values[group[0]]) if len(group)==1 else complex(np.exp(1j*phase))
    minimum_gap=min((abs(float(np.angle(values[group[0]]/v))) for j,v in enumerate(values) if j!=group[0]),default=None)
    return vector,dict(selected_eigenvalue=value,selected_eigenphase=phase,
        selected_ordinal=group[0],ground_comparator_ordinal=comparator,
        disagreement_flag=comparator not in group,ground_overlap=float(abs(np.vdot(ground,vector))**2),
        previous_vector_overlap=None if previous is None else selected_overlap,
        degenerate_projector_overlap=masses[chosen],phase_cluster_size=len(group),minimum_phase_gap=minimum_gap,
        selection_rule=('maximum_exact_ground_overlap' if previous is None else 'maximum_previous_selected_vector_overlap')+
                       (';degenerate_projector_continuity' if len(group)>1 else ''),
        phase_cluster_member_ordinals=group)

def solve_point(unitary,ground,energy,t,source,index,context,previous=None):
    if context.phase not in ('synthetic','FS-R1-Phase-B'):raise PermissionError('direct truth Schur is Phase B only')
    context.guard(unitary.shape[0])
    U=np.asarray(unitary,dtype=np.complex128);n=len(U)
    if U.shape!=(n,n) or not np.isfinite(U).all() or not np.isfinite(energy) or not np.isfinite(t) or t<=0:fail('NaN/Inf or invalid operator/time')
    if index>0 and previous is None:fail('missing prior checkpoint')
    if index==0 and previous is not None:fail('initial anchor cannot use previous branch')
    prior=None
    if previous is not None:
        if previous.get('source_identity_sha256')!=source or previous.get('index')!=index-1:fail('prior source/index mismatch')
        validate_branch_id(previous.get('branch_id'),source,index-1)
        if previous.get('time',t)>=t:fail('non-monotone time sequence')
        prior=previous['vector']
    unitarity=float(np.linalg.norm(U.conj().T @ U-np.eye(n),ord='fro'));context.add('unitarity_residual')
    if unitarity>RESIDUAL:fail('unitarity residual > 1e-10')
    triangular,vectors=schur(U,output='complex',check_finite=True);context.add('Schur_decomposition')
    vector,row=choose(np.diag(triangular),vectors,ground,prior,context=context);context.add('branch_matching')
    residual=float(np.linalg.norm(U @ vector-row['selected_eigenvalue']*vector));context.add('eigenpair_residual')
    if residual>RESIDUAL:fail('eigenpair residual > 1e-10; unresolved phase cluster')
    value=row.pop('selected_eigenvalue')
    # S0 convention: principal angle of exp(-i E t) lambda, unwrap integer 0.
    shift=float(np.angle(np.exp(-1j*energy*t)*value)/t)
    row.update(source_identity_sha256=source,time=float(t),index=index,
        selected_eigenvalue=[float(value.real),float(value.imag)],signed_direct_shift=shift,direct_error=abs(shift),
        selected_branch_id=namespace(source,index),previous_branch_id=None if index==0 else namespace(source,index-1),
        ground_overlap_comparator_id=namespace(source,index)+f':eigenpair:{row["ground_comparator_ordinal"]}',
        unwrap_integer=0,eigenpair_residual=residual,unitarity_residual=unitarity,
        branch_status='resolved',provenance='FS-R1-v2-new-source-direct')
    return row,vector
