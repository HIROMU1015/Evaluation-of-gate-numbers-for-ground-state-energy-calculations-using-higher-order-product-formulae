"""Exact graded electron/oscillator algebra, reusing the frozen foundation."""
from dataclasses import replace
from fractions import Fraction
from math import factorial

from p1star_foundation.algebra import Basis, Scope, Trace, normal_car, weyl_to_xp, word_to_weyl
from p1star_foundation.exact import I, ONE, QComplex, TermLedger, TermMap


class Arena:
    def __init__(self, nvars=0, term_limit=200_000, event_limit=200_000, check=lambda: None):
        self.nvars=nvars
        self.ledger=TermLedger(term_limit)
        self.trace=Trace(event_limit)
        self.check=check
        self.expressions=[]

    def new(self, origin='derived'):
        self.check()
        value=Expression(self,origin)
        self.expressions.append(value)
        return value

    def identity(self):
        result=self.new('identity')
        result.terms.add(Basis(0,(),(0,0),(0,)*self.nvars),ONE)
        return result

    def close(self):
        for expression in self.expressions:expression.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()


class Expression:
    def __init__(self,arena,origin):
        self.arena=arena
        self.origin=origin
        self.terms=TermMap(arena.ledger)
        self.relation_scopes={Scope.INPUT}

    def tagged(self,scope):
        self.relation_scopes.add(scope)
        self.arena.trace.add(scope,'expression_relation_tag',{'origin':self.origin})
        return self

    def add_word(self,fermions=(),bus=(),coefficient=ONE,degree=0,powers=None):
        if type(degree) is not int or degree<0:raise ValueError('invalid formal degree')
        powers=(0,)*self.arena.nvars if powers is None else tuple(powers)
        if len(powers)!=self.arena.nvars or any(type(p) is not int or p<0 for p in powers):
            raise ValueError('invalid parameter monomial')
        coefficient=QComplex.coerce(coefficient)
        fermions,bus=tuple(fermions),tuple(bus)
        self.arena.trace.begin_input((self.origin,),{'fermions':fermions,'bus':bus,'degree':degree,'powers':powers})
        with normal_car(fermions,self.arena.ledger,self.arena.trace) as electron:
            with word_to_weyl(bus,self.arena.ledger,self.arena.trace) as oscillator:
                for e,a in electron.items():
                    for b,c in oscillator.items():
                        self.terms.add(Basis(degree,e,b,powers),coefficient*a*c)
        return self

    def _compatible(self,other):
        if self.arena is not other.arena:raise ValueError('one shared arena/ledger required')

    def plus(self,other,scale=ONE):
        self._compatible(other)
        result=self.arena.new('sum')
        result.relation_scopes=self.relation_scopes | other.relation_scopes
        for k,c in self.terms.items():result.terms.add(k,c)
        for k,c in other.terms.items():result.terms.add(k,c*scale)
        return result

    def scaled(self,coefficient):
        result=self.arena.new('scale')
        result.relation_scopes=set(self.relation_scopes)
        for key,value in self.terms.items():result.terms.add(key,value*coefficient)
        return result

    def shifted(self,degree,coefficient=ONE,parameter=None):
        if type(degree) is not int or degree<0:raise ValueError('invalid degree shift')
        result=self.arena.new('graded_shift')
        result.relation_scopes=set(self.relation_scopes)
        for key,value in self.terms.items():
            powers=list(key.parameters)
            if parameter is not None:
                if not 0<=parameter<len(powers):raise ValueError('invalid parameter index')
                powers[parameter]+=1
            result.terms.add(replace(key,eta_degree=key.eta_degree+degree,parameters=tuple(powers)),value*coefficient)
        return result

    def multiplied(self,other,order=None):
        self._compatible(other)
        result=self.arena.new('noncommutative_product')
        result.relation_scopes=self.relation_scopes | other.relation_scopes | {Scope.CAR,Scope.CCR}
        for left,a in self.terms.items():
            for right,b in other.terms.items():
                self.arena.check()
                degree=left.eta_degree+right.eta_degree
                if order is not None and degree>order:continue
                powers=tuple(p+q for p,q in zip(left.parameters,right.parameters))
                self.arena.trace.begin_input((self.origin,other.origin),
                    {'operation':'multiply','electron_words':(left.fermions,right.fermions),'bus_basis':(left.bus,right.bus)})
                with normal_car(left.fermions+right.fermions,self.arena.ledger,self.arena.trace) as e:
                    with weyl_to_xp(*left.bus,self.arena.ledger,self.arena.trace) as x:
                        with weyl_to_xp(*right.bus,self.arena.ledger,self.arena.trace) as y:
                            for (p,q),c in x.items():
                                for (r,s),d in y.items():
                                    word=('X',)*p+('P',)*q+('X',)*r+('P',)*s
                                    with word_to_weyl(word,self.arena.ledger,self.arena.trace) as bus:
                                        for ef,f in e.items():
                                            for bf,g in bus.items():
                                                result.terms.add(Basis(degree,ef,bf,powers),a*b*c*d*f*g)
        return result

    def commutator(self,other,order=None):
        ab=self.multiplied(other,order)
        ba=other.multiplied(self,order)
        result=ab.plus(ba,-ONE)
        ab.close();ba.close()
        return result

    def close(self):self.terms.close()

    def equals(self,other):
        self._compatible(other)
        return dict(self.terms.items())==dict(other.terms.items())


def dgamma(matrix,arena,label='artificial_factor'):
    size=len(matrix)
    if not size or any(len(row)!=size for row in matrix):raise ValueError('square factor required')
    result=arena.new(label)
    for p,row in enumerate(matrix):
        for q,coefficient in enumerate(row):
            coefficient=QComplex.coerce(coefficient)
            if coefficient:result.add_word(((p,1),(q,0)),coefficient=coefficient)
    return result.tagged(Scope.FACTOR)


def quadrature(factor,axis):
    if axis not in ('X','P'):raise ValueError('only X/P quadratures')
    bus=factor.arena.new('oscillator_'+axis).add_word(bus=(axis,))
    result=factor.multiplied(bus)
    bus.close()
    return result


def formal_log(generators,word,order,amplitudes=None):
    """log(U_last ... U_first), using truncated exp and log(1+V) series.

    This is the standard formal-series construction, not a new Magnus theorem.
    No fixed P1* word or factors are referenced here.
    """
    if type(order) is not int or not 1<=order<=4 or not word:raise ValueError('order 1..4 and finite nonempty word required')
    arena=generators[word[0]].arena
    if amplitudes is None and arena.nvars!=len(word):raise ValueError('one amplitude variable per segment')
    if amplitudes is not None and len(amplitudes)!=len(word):raise ValueError('amplitude length mismatch')
    for name in word:
        if name not in generators:raise ValueError('unknown primitive')
        generator=generators[name]
        if generator.arena is not arena or any(k.eta_degree or any(k.parameters) for k,_ in generator.terms.items()):
            raise ValueError('generators must be parameter/eta independent in one arena')
    u=arena.identity()
    for j,name in enumerate(word):
        h=generators[name].shifted(1,-I if amplitudes is None else -I*amplitudes[j],
                                 parameter=j if amplitudes is None else None)
        power=arena.identity();exponential=arena.identity()
        for n in range(1,order+1):
            next_power=power.multiplied(h,order);power.close();power=next_power
            scaled=power.scaled(Fraction(1,factorial(n)))
            total=exponential.plus(scaled);exponential.close();scaled.close();exponential=total
        next_u=exponential.multiplied(u,order)
        u.close();exponential.close();power.close();h.close();u=next_u
    identity=arena.identity();v=u.plus(identity,-ONE);u.close();identity.close()
    if any(key.eta_degree==0 for key,_ in v.terms.items()):raise ValueError('formal log requires U(0)=I')
    result=arena.new('formal_log');power=arena.identity()
    for n in range(1,order+1):
        next_power=power.multiplied(v,order);power.close();power=next_power
        scaled=power.scaled(Fraction((-1)**(n+1),n))
        total=result.plus(scaled);result.close();scaled.close();result=total
    power.close();v.close()
    return result
