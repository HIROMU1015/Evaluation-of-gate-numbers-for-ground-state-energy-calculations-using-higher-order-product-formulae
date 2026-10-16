"""Full-Fock basis equality -> exact real polynomial equations, without sectors."""
from dataclasses import dataclass
import hashlib
import json

import z3
from p1star_foundation.algebra import Scope
from p1star_foundation.exact import Polynomial, QComplex
from p1star_foundation.solver import polynomial_expression, real_literal, solve_exact, Status


@dataclass
class Equation:
    basis: tuple
    component: str
    category: str
    polynomial: Polynomial


class Conditions:
    def __init__(self,actual,target,order):
        actual._compatible(target)
        if Scope.SECTOR in actual.relation_scopes | target.relation_scopes:
            raise ValueError('sector-specific identities cannot enter full-Fock conditions')
        self.arena=actual.arena
        self.rows=[]
        self.order=order
        self.residual=actual.plus(target,-1)
        grouped={}
        try:
            for key,c in self.residual.terms.items():
                if key.eta_degree>order:continue
                basis=(key.eta_degree,key.fermions,key.bus)
                for part,value in (('real',c.real),('imag',c.imag)):
                    if not value:continue
                    index=(basis,part)
                    if index not in grouped:
                        poly=Polynomial(self.arena.nvars,self.arena.ledger)
                        body=key.electronic_body
                        category=('bus_nonidentity' if key.bus!=(0,0) else
                                  'scalar' if body==0 else 'one_body' if body==1 else
                                  'two_body' if body==2 else 'higher_body' if body is not None else 'number_changing')
                        row=Equation(basis,part,category,poly)
                        grouped[index]=row;self.rows.append(row)
                    grouped[index].polynomial.terms.add(key.parameters,QComplex(value))
            self.rows=[r for r in self.rows if len(r.polynomial.terms)]
        except BaseException:
            self.close();raise

    def record(self):
        rows=[]
        for row in self.rows:
            rows.append({'basis':row.basis,'component':row.component,'category':row.category,
                         'terms':[[powers,c.record()] for powers,c in sorted(row.polynomial.terms.items())]})
        rows.sort(key=lambda r:json.dumps(r,sort_keys=True))
        return {'domain':'full Fock CAR basis x exact Weyl basis','order':self.order,
                'equations':rows,'sector_identities_used':False}

    def digest(self):
        return hashlib.sha256(json.dumps(self.record(),sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def ast(self):
        if not self.arena.nvars:raise ValueError('solver bridge requires real parameters')
        context=z3.Context()
        variables=tuple(z3.Real('x'+str(j+1),ctx=context) for j in range(self.arena.nvars))
        constraints=tuple(polynomial_expression(row.polynomial,variables)==real_literal(0,context) for row in self.rows)
        return variables,constraints

    def solve(self,boxes,timeout_ms,rlimit=None):
        variables,constraints=self.ast()
        return solve_exact(variables,constraints,boxes,timeout_ms=timeout_ms,rlimit=rlimit)

    def close(self):
        for row in self.rows:row.polynomial.close()
        self.residual.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()


def exact_values(variables,witness):
    """Rehydrate rational or SMT-LIB real algebraic root objects, never decimals."""
    values=[]
    context=variables[0].ctx
    for variable in variables:
        row=witness[str(variable)]
        if row['kind']=='rational':
            from fractions import Fraction
            value=real_literal(Fraction(row['numerator'],row['denominator']),context)
        elif row['kind']=='real_algebraic':
            # Internal, backend-produced serialization; do not accept arbitrary user SMT.
            text='(declare-const witness_value Real) (assert (= witness_value '+row['sexpr']+'))'
            equality=z3.parse_smt2_string(text,ctx=context)[0]
            value=equality.arg(1)
            if not z3.is_algebraic_value(value):raise ValueError('non-ground algebraic witness')
        else:raise ValueError('unsupported exact witness')
        values.append(value)
    return tuple(values)


def recheck(conditions,decision,boxes):
    if decision.status!=Status.SAT:return False
    variables,constraints=conditions.ast()
    values=exact_values(variables,decision.witness)
    constraints=list(constraints)
    if len(boxes)!=len(variables):return False
    for v,(lower,upper) in zip(variables,boxes):
        constraints.extend((v>=real_literal(lower,v.ctx),v<=real_literal(upper,v.ctx)))
    return all(z3.is_true(z3.simplify(z3.substitute(c,*zip(variables,values)))) for c in constraints)
