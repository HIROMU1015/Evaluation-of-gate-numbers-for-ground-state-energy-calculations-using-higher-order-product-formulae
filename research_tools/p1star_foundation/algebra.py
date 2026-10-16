"""Generic CAR and exact one-oscillator CCR/Weyl adapters.

No factor matrices, Hamiltonian, sector projection, eligibility calculation,
Magnus/formal-log expansion or scientific condition generator is included.
Weyl basis means the average of all distinct X/P words with fixed counts.
"""
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
from itertools import combinations
from math import comb

from .exact import I, ONE, QComplex, TermMap


class Scope(str, Enum):
    INPUT = "INPUT"
    CAR = "CAR"
    CCR = "CCR"
    FACTOR = "FIXED_FACTOR_SPECIFIC"
    SECTOR = "SECTOR_SPECIFIC"


class Trace:
    """Bounded event log. It tracks operations, not a new correctness proof."""

    def __init__(self, event_limit=200_000):
        self.events = []
        self.event_limit = event_limit
        self.input_id = None
        self._inputs = 0

    def add(self, scope, rule, detail):
        if len(self.events) >= self.event_limit:
            raise RuntimeError("INCONCLUSIVE: provenance event limit")
        self.events.append({"scope": Scope(scope).value, "rule": rule,
                            "input_id":self.input_id, "detail":detail})

    def begin_input(self, origins, detail):
        self._inputs += 1
        self.input_id = self._inputs
        self.add(Scope.INPUT, "input_word", {"origins":origins, **detail})


@dataclass(frozen=True)
class Provenance:
    origins: tuple[str, ...]
    scopes: frozenset[Scope] = frozenset({Scope.INPUT})

    def tagged(self, scope):
        return replace(self, scopes=self.scopes | {Scope(scope)})

    def require_full_fock(self):
        if Scope.SECTOR in self.scopes:
            raise ValueError("sector-specific relation cannot certify full Fock identity")


@dataclass(frozen=True)
class Basis:
    eta_degree: int
    fermions: tuple[tuple[int, int], ...]  # (mode, creation=1/annihilation=0)
    bus: tuple[int, int]  # Weyl counts (X,P); distinct tensor factor
    parameters: tuple[int, ...] = ()

    @property
    def electronic_body(self):
        creators = sum(action for _, action in self.fermions)
        annihilators = len(self.fermions) - creators
        if creators != annihilators:
            return None  # number-changing monomial, not mislabelled as k-body
        return creators


def _fermion_word(word):
    word = tuple(tuple(op) for op in word)
    if any(len(op) != 2 or type(op[0]) is not int or op[0] < 0 or
           type(op[1]) is not int or op[1] not in (0, 1) for op in word):
        raise ValueError("fermion labels require nonnegative mode and action 0/1")
    return word


def _normal_car(word, coefficient, result, trace):
    """Use defining CAR locally, retaining contraction and swap events."""
    word = _fermion_word(word)
    for j in range(len(word) - 1):
        (p, a), (q, b) = word[j:j + 2]
        if a == b and p == q:
            trace.add(Scope.CAR, "nilpotency", (word, j))
            return
        if a == 0 and b == 1:
            trace.add(Scope.CAR, "annihilation_creation_swap", (word, j))
            if p == q:
                trace.add(Scope.CAR, "delta_contraction", (word, j))
                _normal_car(word[:j] + word[j + 2:], coefficient, result, trace)
            swapped = word[:j] + (word[j + 1], word[j]) + word[j + 2:]
            _normal_car(swapped, -coefficient, result, trace)
            return
        if a == b and ((a == 1 and p > q) or (a == 0 and p < q)):
            trace.add(Scope.CAR, "same_action_swap", (word, j))
            swapped = word[:j] + (word[j + 1], word[j]) + word[j + 2:]
            _normal_car(swapped, -coefficient, result, trace)
            return
    result.add(word, coefficient)


def normal_car(word, ledger, trace=None):
    trace = trace if trace is not None else Trace()
    result = TermMap(ledger)
    try:
        _normal_car(word, ONE, result, trace)
    except BaseException:
        result.close()
        raise
    return result


def _normal_xp(word, coefficient, result, trace):
    for j in range(len(word) - 1):
        if word[j:j + 2] == ("P", "X"):
            trace.add(Scope.CCR, "PX_to_XP_minus_i", (word, j))
            _normal_xp(word[:j] + word[j + 2:], -I * coefficient, result, trace)
            swapped = word[:j] + ("X", "P") + word[j + 2:]
            _normal_xp(swapped, coefficient, result, trace)
            return
    result.add((word.count("X"), word.count("P")), coefficient)


def normal_xp(word, ledger, trace=None):
    word = tuple(word)
    if any(letter not in ("X", "P") for letter in word):
        raise ValueError("only the exact oscillator X/P alphabet is supported")
    trace = trace if trace is not None else Trace()
    result = TermMap(ledger)
    try:
        _normal_xp(word, ONE, result, trace)
    except BaseException:
        result.close()
        raise
    return result


def weyl_to_xp(p, q, ledger, trace=None):
    """Implement the symmetrization definition, with no factorial-word cache."""
    if any(type(k) is not int or k < 0 for k in (p, q)):
        raise ValueError("nonnegative Weyl counts required")
    trace = trace if trace is not None else Trace()
    result = TermMap(ledger)
    try:
        weight = QComplex(Fraction(1, comb(p + q, p)))
        for positions in combinations(range(p + q), p):
            word = tuple("X" if j in positions else "P" for j in range(p + q))
            with normal_xp(word, ledger, trace) as ordered:
                for key, coefficient in ordered.items():
                    result.add(key, weight * coefficient)
    except BaseException:
        result.close()
        raise
    return result


def word_to_weyl(word, ledger, trace=None):
    """Finite triangular basis conversion using the explicit definition above."""
    trace = trace if trace is not None else Trace()
    result = TermMap(ledger)
    try:
        with normal_xp(word, ledger, trace) as remaining:
            while len(remaining):
                key = max((k for k, _ in remaining.items()), key=lambda k: (sum(k), k))
                coefficient = remaining.coefficient(key)
                result.add(key, coefficient)
                trace.add(Scope.CCR, "XP_to_Weyl_basis", key)
                with weyl_to_xp(*key, ledger, trace) as basis:
                    for lower, weight in basis.items():
                        remaining.add(lower, -coefficient * weight)
    except BaseException:
        result.close()
        raise
    return result


class TensorExpression:
    """Flat polynomial/operator records with explicit relation provenance."""

    def __init__(self, ledger, provenance, trace=None):
        self.terms = TermMap(ledger)
        self.provenance = provenance
        self.trace = trace if trace is not None else Trace()

    def add_word(self, fermions, bus, *, coefficient=ONE, eta_degree=0, parameters=()):
        if type(eta_degree) is not int or eta_degree < 0:
            raise ValueError("nonnegative formal degree required")
        if any(type(p) is not int or p < 0 for p in parameters):
            raise ValueError("nonnegative parameter powers required")
        coefficient = QComplex.coerce(coefficient)
        fermions, bus = tuple(fermions), tuple(bus)
        try:
            self.trace.begin_input(self.provenance.origins,
                {"fermions":fermions,"bus":bus,"eta_degree":eta_degree,
                 "parameters":tuple(parameters),"coefficient":coefficient.record()})
            with normal_car(fermions, self.terms.ledger, self.trace) as electrons:
                with word_to_weyl(bus, self.terms.ledger, self.trace) as oscillator:
                    for e, a in electrons.items():
                        for b, c in oscillator.items():
                            self.terms.add(Basis(eta_degree, e, b, tuple(parameters)), coefficient * a * c)
            self.provenance = self.provenance.tagged(Scope.CAR).tagged(Scope.CCR)
        except BaseException:
            # No partial normal form may escape as a valid expression.
            self.close()
            raise

    def close(self):
        self.terms.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
