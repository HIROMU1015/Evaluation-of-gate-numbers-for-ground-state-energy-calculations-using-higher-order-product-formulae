from fractions import Fraction as F
import itertools
import unittest

from p1star_foundation.algebra import (Basis, Provenance, Scope, TensorExpression,
    Trace, normal_car, normal_xp, word_to_weyl, weyl_to_xp)
from p1star_foundation.exact import (I, ONE, ZERO, Polynomial, QComplex,
    TermLedger, TermLimitExceeded, TermMap)


class ExactCoefficientTests(unittest.TestCase):
    def test_gaussian_rational_and_tiny_nonzero(self):
        a = QComplex(F(1, 3), F(2, 7))
        self.assertEqual(a * a.conjugate(), QComplex(F(1, 9) + F(4, 49)))
        self.assertEqual(I * I, QComplex(-1))
        self.assertTrue(QComplex(F(1, 10**100)))

    def test_approximate_coefficients_rejected(self):
        for bad in (0.1, complex(0, 1), True, '1/3'):
            with self.assertRaises(TypeError):
                QComplex(bad)

    def test_sympy_QQ_I_round_trip(self):
        import sympy as s
        for a in (QComplex(F(2, 3), F(-5, 7)), QComplex(F(1, 10**60))):
            value = s.Rational(a.real.numerator,a.real.denominator) + s.I*s.Rational(a.imag.numerator,a.imag.denominator)
            exact = s.QQ_I.to_sympy(s.QQ_I.from_sympy(value))
            self.assertEqual(s.expand(exact-value), 0)
            self.assertFalse(exact.atoms(s.Float))

    def test_global_managed_map_limit_and_release(self):
        ledger = TermLedger(2)
        with TermMap(ledger) as a, TermMap(ledger) as b:
            a.add('a',ONE); b.add('b',ONE)
            self.assertEqual(ledger.live,2)
            with self.assertRaises(TermLimitExceeded):
                b.add('c',ONE)
            self.assertEqual(ledger.live,2)
            self.assertEqual(len(b),1)
            self.assertTrue(ledger.stopped)
        self.assertEqual(ledger.live,0)

    def test_cancellation_releases_and_polynomial_product(self):
        ledger=TermLedger(20)
        with Polynomial(1,ledger,[((1,),1),((0,),1)]) as p:
            with Polynomial(1,ledger,[((1,),1),((0,),-1)]) as q:
                with p.multiply(q) as product:
                    self.assertEqual(dict(product.terms.items()),{(2,):ONE,(0,):QComplex(-1)})
        self.assertEqual(ledger.live,0)

    def test_failed_polynomial_constructor_releases(self):
        ledger=TermLedger(5)
        with self.assertRaises(ValueError):
            Polynomial(1,ledger,[((0,),1),((-1,),1)])
        self.assertEqual(ledger.live,0)


class CARTests(unittest.TestCase):
    def test_defining_anticommutators_two_generic_modes(self):
        # Exhaustive small software fixtures, not a P1* Fock-space computation.
        ledger=TermLedger(100)
        for p,q in itertools.product((0,1), repeat=2):
            for a,b in itertools.product((0,1), repeat=2):
                with normal_car(((p,a),(q,b)),ledger) as left:
                    with normal_car(((q,b),(p,a)),ledger) as right:
                        with TermMap(ledger) as total:
                            for k,c in itertools.chain(left.items(),right.items()): total.add(k,c)
                            expected={():ONE} if p==q and a!=b else {}
                            self.assertEqual(dict(total.items()),expected)
        self.assertEqual(ledger.live,0)

    def test_creation_ascending_annihilation_descending(self):
        ledger=TermLedger(20)
        with normal_car(((3,1),(1,1),(1,0),(3,0)),ledger) as result:
            self.assertEqual(dict(result.items()),{((1,1),(3,1),(3,0),(1,0)):ONE})

    def test_occupation_idempotence_and_contraction_trace(self):
        ledger=TermLedger(30); trace=Trace()
        with normal_car(((0,1),(0,0),(0,1),(0,0)),ledger,trace) as result:
            self.assertEqual(dict(result.items()),{((0,1),(0,0)):ONE})
        self.assertIn('delta_contraction',{e['rule'] for e in trace.events})
        self.assertIn('nilpotency',{e['rule'] for e in trace.events})

    def test_generic_words_normalization_is_idempotent(self):
        ledger=TermLedger(100)
        alphabet=((0,0),(0,1),(1,0),(1,1))
        for word in itertools.product(alphabet,repeat=3):
            with normal_car(word,ledger) as ordered:
                for normal, c in ordered.items():
                    with normal_car(normal,ledger) as again:
                        self.assertEqual(dict(again.items()),{normal:ONE})
        self.assertEqual(ledger.live,0)


class CCRAndTensorTests(unittest.TestCase):
    def test_commutator_and_Weyl_sign(self):
        ledger=TermLedger(30)
        for word,constant in [(('X','P'),I*F(1,2)),(('P','X'),-I*F(1,2))]:
            with word_to_weyl(word,ledger) as result:
                self.assertEqual(dict(result.items()),{(1,1):ONE,(0,0):constant})
        with normal_xp(('P','X'),ledger) as xp:
            self.assertEqual(dict(xp.items()),{(1,1):ONE,(0,0):-I})
        self.assertEqual(ledger.live,0)

    def test_six_word_symmetrization_degree_four(self):
        ledger=TermLedger(200)
        # Definition of W(2,2): average the six distinct words, not dynamics.
        words=set(itertools.permutations(('X','X','P','P')))
        with TermMap(ledger) as average:
            for word in words:
                with word_to_weyl(word,ledger) as result:
                    for key,c in result.items():average.add(key,c*F(1,6))
            self.assertEqual(dict(average.items()),{(2,2):ONE})
        self.assertEqual(ledger.live,0)

    def test_basis_round_trip_small_generic_bus_words(self):
        ledger=TermLedger(1000)
        for length in range(4):
            for word in itertools.product(('X','P'),repeat=length):
                with normal_xp(word,ledger) as expected:
                    with word_to_weyl(word,ledger) as weyl:
                        with TermMap(ledger) as restored:
                            for (p,q),a in weyl.items():
                                with weyl_to_xp(p,q,ledger) as expanded:
                                    for key,b in expanded.items():restored.add(key,a*b)
                            self.assertEqual(dict(restored.items()),dict(expected.items()))
        self.assertEqual(ledger.live,0)

    def test_tensor_grades_and_origin_separation(self):
        ledger=TermLedger(100); provenance=Provenance(('toy_origin',))
        with TensorExpression(ledger,provenance) as expression:
            expression.add_word(((7,1),(7,0)),('P','X'),eta_degree=3,parameters=(2,0))
            for key,c in expression.terms.items():
                self.assertEqual(key.eta_degree,3)
                self.assertEqual(key.electronic_body,1)
                self.assertEqual(key.parameters,(2,0))
                self.assertIsInstance(c,QComplex)
            self.assertEqual(expression.provenance.origins,('toy_origin',))
            self.assertIn(Scope.CAR,expression.provenance.scopes)
            self.assertIn(Scope.CCR,expression.provenance.scopes)
        body=Basis(0,((2,1),(5,1),(8,1),(8,0),(5,0),(2,0)),(0,0))
        self.assertEqual(body.electronic_body,3)
        self.assertIsNone(Basis(0,((1,1),),(0,0)).electronic_body)

    def test_relation_tags_never_turn_sector_into_full_fock(self):
        car=Provenance(('toy',)).tagged(Scope.CAR)
        factor=car.tagged(Scope.FACTOR)
        sector=factor.tagged(Scope.SECTOR)
        factor.require_full_fock()
        self.assertNotEqual(car.scopes,factor.scopes)
        with self.assertRaises(ValueError): sector.require_full_fock()

    def test_trace_limit_and_bad_alphabet_fail(self):
        ledger=TermLedger(20)
        with self.assertRaises(RuntimeError):normal_car(((0,0),(0,1)),ledger,Trace(0))
        with self.assertRaises(ValueError):normal_xp(('unknown',),ledger)
        self.assertEqual(ledger.live,0)

    def test_tensor_failure_closes_partial_result(self):
        ledger=TermLedger(3)
        expression=TensorExpression(ledger,Provenance(('toy_fail',)))
        with self.assertRaises((TermLimitExceeded,RuntimeError)):
            expression.add_word(((0,0),(0,1)),('X','P'))
        self.assertTrue(expression.terms.closed)
        self.assertEqual(ledger.live,0)

    def test_trace_links_each_input_even_after_cancellation(self):
        ledger=TermLedger(50)
        with TensorExpression(ledger,Provenance(('toy_trace',))) as expression:
            expression.add_word((),('P','X'))
            expression.add_word((),('P','X'),coefficient=-ONE)
            self.assertEqual(len(expression.terms),0)
            events=expression.trace.events
            self.assertEqual({e['input_id'] for e in events},{1,2})
            self.assertEqual(sum(e['rule']=='input_word' for e in events),2)
            self.assertTrue(all(e['scope'] in {s.value for s in Scope} for e in events))
