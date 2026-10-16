"""One in-process exact QF_NRA check; accepts no scientific input files.

Native Z3 term storage is opaque. This module cannot discharge the global
200,000-term contract and must not be mistaken for a Phase B launch path.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import z3

from .exact import rational
from .environment import require_bound_backend


class Status(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    UNKNOWN = "UNKNOWN"


@dataclass
class Decision:
    status: Status
    reason: str
    witness: dict = field(default_factory=dict)
    exact_substitution_verified: bool = False
    independent_certificate_verified: bool = False
    input_smt2: str = ""
    input_sha256: str = ""
    backend: str = "Z3 QF_NRA/NLSat"
    backend_version: str = ""

    def record(self):
        return dict(self.__dict__, status=self.status.value)


def real_literal(value, ctx=None):
    value = rational(value)
    return z3.RealVal(f"{value.numerator}/{value.denominator}", ctx=ctx)


def polynomial_expression(polynomial, variables):
    if len(variables) != polynomial.nvars or not variables:
        raise ValueError("polynomial/variable width mismatch")
    ctx = variables[0].ctx
    result = real_literal(0, ctx)
    for powers, coefficient in polynomial.terms.items():
        if coefficient.imag:
            raise ValueError("split complex coefficient conditions exactly before real solving")
        term = real_literal(coefficient.real, ctx)
        for variable, power in zip(variables, powers):
            if power:
                term = term * variable**power
        result = result + term
    return result


def _validate(variables, constraints):
    if not variables or len({v.get_id() for v in variables}) != len(variables):
        raise ValueError("distinct declared real variables required")
    ids = {v.get_id() for v in variables}
    ctx = variables[0].ctx
    for v in variables:
        if v.ctx != ctx or not z3.is_const(v) or not z3.is_real(v) or v.decl().kind() != z3.Z3_OP_UNINTERPRETED:
            raise ValueError("only declared real variables are allowed")
    allowed = {z3.Z3_OP_ADD, z3.Z3_OP_SUB, z3.Z3_OP_MUL, z3.Z3_OP_UMINUS,
               z3.Z3_OP_EQ, z3.Z3_OP_LE, z3.Z3_OP_GE, z3.Z3_OP_LT,
               z3.Z3_OP_GT, z3.Z3_OP_AND, z3.Z3_OP_OR, z3.Z3_OP_NOT,
               z3.Z3_OP_TRUE, z3.Z3_OP_FALSE}
    def visit(expr):
        if expr.ctx != ctx or not z3.is_app(expr):
            raise ValueError("quantifiers and foreign contexts are unsupported")
        if z3.is_rational_value(expr) or z3.is_algebraic_value(expr):
            return
        kind = expr.decl().kind()
        if kind == z3.Z3_OP_UNINTERPRETED:
            if not z3.is_const(expr) or expr.get_id() not in ids:
                raise ValueError("undeclared symbol/function")
            return
        if kind == z3.Z3_OP_POWER:
            power = expr.arg(1)
            if not z3.is_rational_value(power) or power.denominator_as_long() != 1 or power.numerator_as_long() < 0:
                raise ValueError("only nonnegative integer powers are polynomial")
        elif kind not in allowed:
            raise ValueError("unsupported non-polynomial QF_NRA operation")
        for child in expr.children():
            visit(child)
    for c in constraints:
        if not z3.is_bool(c):
            raise ValueError("Boolean polynomial constraints required")
        visit(c)


def solve_exact(variables, constraints, boxes, *, timeout_ms=5000, rlimit=None):
    """Return a single trusted-solver decision; never retry or enumerate models.

    Callers must construct exact ASTs (e.g. via real_literal/Fraction). An AST
    cannot reveal whether a caller previously converted a Python float into it.
    """
    variables, constraints, boxes = tuple(variables), tuple(constraints), tuple(boxes)
    require_bound_backend()
    _validate(variables, constraints)
    if len(boxes) != len(variables):
        raise ValueError("one closed box interval per real variable required")
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("positive timeout required")
    ctx = variables[0].ctx
    all_constraints = list(constraints)
    for variable, (lower, upper) in zip(variables, boxes):
        lower, upper = rational(lower), rational(upper)
        if lower > upper:
            raise ValueError("reversed box interval")
        all_constraints.extend([variable >= real_literal(lower, ctx), variable <= real_literal(upper, ctx)])
    z3.set_param("parallel.enable", False)
    solver = z3.SolverFor("QF_NRA", ctx=ctx)
    solver.set(timeout=timeout_ms)
    if rlimit is not None:
        if type(rlimit) is not int or rlimit <= 0:
            raise ValueError("positive resource count required")
        solver.set(rlimit=rlimit)
    solver.add(*all_constraints)
    text = solver.to_smt2()
    base = {"input_smt2":text,"input_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "backend_version":z3.get_full_version()}
    try:
        status = solver.check()
        if status == z3.unsat:
            return Decision(Status.UNSAT, "trusted exact real solver conclusion; no independently checked certificate", **base)
        if status != z3.sat:
            return Decision(Status.UNKNOWN, solver.reason_unknown(), **base)
        model = solver.model()
        values = [model.eval(v, model_completion=True) for v in variables]
        witness = {}
        for v, value in zip(variables, values):
            if z3.is_rational_value(value):
                witness[str(v)] = {"kind":"rational", "numerator":value.numerator_as_long(),
                                   "denominator":value.denominator_as_long(),"sexpr":value.sexpr()}
            elif z3.is_algebraic_value(value):
                witness[str(v)] = {"kind":"real_algebraic","sexpr":value.sexpr()}
            else:
                return Decision(Status.UNKNOWN,"model contains non-exact/non-ground real value", **base)
        substitutions = tuple(zip(variables, values))
        checked = all(z3.is_true(z3.simplify(z3.substitute(c, *substitutions))) for c in all_constraints)
        if not checked:
            return Decision(Status.UNKNOWN,"exact substitution did not close all original conditions", **base)
        return Decision(Status.SAT,"exact substitution checked by the same backend",witness,
                        exact_substitution_verified=True, **base)
    except z3.Z3Exception as error:
        return Decision(Status.UNKNOWN,"backend exception: "+str(error), **base)


def proof_capability_probe():
    """Known toy contradiction only; exported text is not an independent proof."""
    ctx = z3.Context(proof=True)
    u = z3.Real("toy_proof_u", ctx=ctx)
    solver = z3.SolverFor("QF_NRA", ctx=ctx)
    solver.set(timeout=2000)
    solver.add(u*u + 1 == 0)
    status = solver.check()
    result = {"toy_status":str(status),"independent_certificate_verified":False}
    try:
        proof = solver.proof().sexpr()
        result.update(proof_text_available=True, proof_sha256=hashlib.sha256(proof.encode()).hexdigest(),
                      proof_has_trusted_theory_lemma="th-lemma" in proof)
    except z3.Z3Exception as error:
        result.update(proof_text_available=False, reason=str(error))
    return result
