"""Exact finite-CAR input gates and sector span checks; generic inputs only."""
from itertools import combinations

from p1star_foundation.exact import ONE, ZERO, QComplex
from .operators import dgamma


def divide(a,b):
    a,b=QComplex.coerce(a),QComplex.coerce(b)
    norm=b.real*b.real+b.imag*b.imag
    if not norm:raise ZeroDivisionError('exact zero pivot')
    return a*QComplex(b.real/norm,-b.imag/norm)


def rank(rows):
    """Exact Gaussian elimination over Q(i); no numerical rank threshold."""
    if not rows:return 0
    a=[[QComplex.coerce(v) for v in row] for row in rows]
    width=len(a[0])
    if any(len(row)!=width for row in a):raise ValueError('rectangular rows required')
    r=0
    for c in range(width):
        pivot=next((k for k in range(r,len(a)) if a[k][c]),None)
        if pivot is None:continue
        a[r],a[pivot]=a[pivot],a[r]
        v=a[r][c];a[r]=[divide(x,v) for x in a[r]]
        for k in range(r+1,len(a)):
            if a[k][c]:
                scale=a[k][c];a[k]=[x-scale*y for x,y in zip(a[k],a[r])]
        r+=1
        if r==len(a):break
    return r


def sector_entries(expression,modes,particles):
    """Ephemeral exact operator entries. No state vectors/simulation/truncation."""
    states=[sum(1<<j for j in occupied) for occupied in combinations(range(modes),particles)]
    positions={s:i for i,s in enumerate(states)}
    result={}
    for key,coefficient in expression.terms.items():
        if key.bus!=(0,0) or key.eta_degree or any(key.parameters):
            raise ValueError('sector gate requires pure-electronic constant expression')
        if any(p>=modes for p,_ in key.fermions):raise ValueError('mode outside input space')
        for column,state in enumerate(states):
            current=state;sign=1
            for p,creation in reversed(key.fermions):
                occupied=bool(current & (1<<p))
                if occupied==bool(creation):break
                if (current & ((1<<p)-1)).bit_count()%2:sign=-sign
                current ^= 1<<p
            else:
                if current in positions:
                    index=(positions[current],column)
                    value=result.get(index,ZERO)+coefficient*sign
                    if value:result[index]=value
                    else:result.pop(index,None)
    return len(states),result


def eligibility(matrices,arena,particles,target=None):
    if len(matrices)!=2:raise ValueError('exactly two factors required')
    modes=len(matrices[0])
    if modes<1 or not 0<=particles<=modes:raise ValueError('invalid sector')
    for matrix in matrices:
        if len(matrix)!=modes or any(len(row)!=modes for row in matrix):raise ValueError('factor shape mismatch')
        if any(QComplex.coerce(matrix[p][q])!=QComplex.coerce(matrix[q][p]).conjugate()
               for p in range(modes) for q in range(modes)):raise ValueError('Hermitian factors required')
    factors=[dgamma(matrix,arena,'input_factor_'+str(j)) for j,matrix in enumerate(matrices)]
    squares=[f.multiplied(f) for f in factors]
    k=squares[0].plus(squares[1]) if target is None else target
    comm=factors[0].commutator(factors[1])
    dimension,comm_sector=sector_entries(comm,modes,particles)
    _,k_sector=sector_entries(k,modes,particles)
    coordinates=[(r,c) for r in range(dimension) for c in range(dimension)]
    columns=[[ONE if r==c else ZERO for r,c in coordinates]]
    for p in range(modes):
        for q in range(modes):
            e=arena.new('sector_span_basis').add_word(((p,1),(q,0)))
            _,entries=sector_entries(e,modes,particles)
            columns.append([entries.get(index,ZERO) for index in coordinates]);e.close()
    base_rank=rank(list(zip(*columns)))
    target_column=[k_sector.get(index,ZERO) for index in coordinates]
    augmented_rank=rank(list(zip(*(columns+[target_column]))))
    checks={
        'noncommuting_full_fock':bool(len(comm.terms)),
        'noncommuting_sector':bool(comm_sector),
        'two_body_nontrivial_full_fock':any(key.electronic_body is not None and key.electronic_body>=2 for key,_ in k.terms.items()),
        'two_body_nontrivial_sector':augmented_rank>base_rank,
        'factors_nonzero_full_and_sector':all(len(f.terms) and sector_entries(f,modes,particles)[1] for f in factors),
        'squares_nonzero_full_and_sector':all(len(s.terms) and sector_entries(s,modes,particles)[1] for s in squares),
        'target_nonzero_full_and_sector':bool(len(k.terms) and k_sector),
    }
    report={'passed':all(bool(x) for x in checks.values()),'checks':{name:bool(value) for name,value in checks.items()},
            'modes':modes,'identification_N':particles,'sector_dimension':dimension,
            'one_body_span_rank':base_rank,'augmented_rank':augmented_rank,
            'primary_domain':'full Fock','sector_role':'input identification only; not an identity rescue',
            'relations_used':{'full_fock':'CAR plus particular input coefficients','sector':'occupation-basis restriction and exact Q(i) linear span'}}
    comm.close()
    for s in squares:s.close()
    if target is None:k.close()
    return report,factors
