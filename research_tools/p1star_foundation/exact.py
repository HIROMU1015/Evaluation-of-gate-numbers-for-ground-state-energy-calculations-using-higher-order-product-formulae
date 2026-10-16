"""Sparse Q(i) coefficient arithmetic without tolerance or hidden expansion.

Only managed map entries are counted by the ledger. Python temporaries and
native library internals are not covered: this is NOT the full contract guard.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Generic, TypeVar


class TermLimitExceeded(RuntimeError):
    pass


def rational(value):
    if type(value) is int or isinstance(value, Fraction):
        return Fraction(value)
    raise TypeError("exact coefficients require int or Fraction; no float/complex")


@dataclass(frozen=True)
class QComplex:
    real: Fraction = Fraction(0)
    imag: Fraction = Fraction(0)

    def __post_init__(self):
        object.__setattr__(self, "real", rational(self.real))
        object.__setattr__(self, "imag", rational(self.imag))

    @staticmethod
    def coerce(value):
        return value if isinstance(value, QComplex) else QComplex(rational(value))

    def __add__(self, other):
        other = self.coerce(other)
        return QComplex(self.real + other.real, self.imag + other.imag)

    __radd__ = __add__

    def __neg__(self):
        return QComplex(-self.real, -self.imag)

    def __sub__(self, other):
        return self + -self.coerce(other)

    def __mul__(self, other):
        other = self.coerce(other)
        return QComplex(self.real * other.real - self.imag * other.imag,
                        self.real * other.imag + self.imag * other.real)

    __rmul__ = __mul__

    def __bool__(self):
        return bool(self.real or self.imag)

    def conjugate(self):
        return QComplex(self.real, -self.imag)

    def record(self):
        return {"real": [self.real.numerator, self.real.denominator],
                "imag": [self.imag.numerator, self.imag.denominator]}


I = QComplex(0, 1)
ONE = QComplex(1)
ZERO = QComplex()


class TermLedger:
    """Aggregate live entries across explicitly owned maps; fail before insert."""

    def __init__(self, limit=200_000):
        if type(limit) is not int or limit < 0:
            raise ValueError("nonnegative integer term limit required")
        self.limit = limit
        self.live = 0
        self.peak = 0
        self.stopped = False

    def reserve(self):
        if self.stopped or self.live >= self.limit:
            self.stopped = True
            raise TermLimitExceeded("INCONCLUSIVE: managed term budget exhausted")
        self.live += 1
        self.peak = max(self.peak, self.live)

    def release(self):
        if self.live <= 0:
            raise RuntimeError("term accounting underflow")
        self.live -= 1


K = TypeVar("K")


class TermMap(Generic[K]):
    """One reservation per retained key/coefficient pair; explicit ownership."""

    def __init__(self, ledger):
        self.ledger = ledger
        self._data = {}
        self.closed = False

    def add(self, key, coefficient):
        if self.closed or self.ledger.stopped:
            raise RuntimeError("closed/stopped term store")
        coefficient = QComplex.coerce(coefficient)
        if not coefficient:
            return
        value = self._data.get(key, ZERO) + coefficient
        if not value:
            del self._data[key]
            self.ledger.release()
        elif key in self._data:
            self._data[key] = value
        else:
            self.ledger.reserve()
            try:
                self._data[key] = value
            except BaseException:
                self.ledger.release()
                raise

    def items(self):
        if self.closed:
            raise RuntimeError("closed term store")
        return self._data.items()

    def coefficient(self, key):
        if self.closed:
            raise RuntimeError("closed term store")
        return self._data.get(key, ZERO)

    def __len__(self):
        return len(self._data)

    def close(self):
        if not self.closed:
            for _ in self._data:
                self.ledger.release()
            self._data.clear()
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class Polynomial:
    """Flat exponent -> Gaussian rational map; no SymPy expansion in this path."""

    def __init__(self, nvars, ledger, terms=()):
        if type(nvars) is not int or nvars < 0:
            raise ValueError("invalid variable count")
        self.nvars = nvars
        self.terms = TermMap(ledger)
        try:
            for powers, coefficient in terms:
                if (len(powers) != nvars or
                        any(type(p) is not int or p < 0 for p in powers)):
                    raise ValueError("nonnegative exponent tuple of fixed width required")
                self.terms.add(tuple(powers), coefficient)
        except BaseException:
            self.close()
            raise

    def multiply(self, other):
        if self.nvars != other.nvars or self.terms.ledger is not other.terms.ledger:
            raise ValueError("polynomials require the same width and ledger")
        result = Polynomial(self.nvars, self.terms.ledger)
        try:
            for p, a in self.terms.items():
                for q, c in other.terms.items():
                    result.terms.add(tuple(x + y for x, y in zip(p, q)), a * c)
        except BaseException:
            result.close()
            raise
        return result

    def close(self):
        self.terms.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
