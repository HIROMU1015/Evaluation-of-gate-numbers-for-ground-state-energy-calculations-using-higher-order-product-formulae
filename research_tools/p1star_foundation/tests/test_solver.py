from fractions import Fraction as F
import unittest
from unittest.mock import patch
import z3

from p1star_foundation.exact import Polynomial,QComplex,TermLedger
from p1star_foundation.solver import (Status,polynomial_expression,proof_capability_probe,
                                     real_literal,solve_exact)


class ExactSolverTests(unittest.TestCase):
    def test_rational_SAT_on_closed_boundary(self):
        u=z3.Real('toy_boundary')
        result=solve_exact([u],[u==real_literal(F(1,3))],[(F(1,3),F(1,3))])
        self.assertEqual(result.status,Status.SAT)
        self.assertEqual(result.witness[str(u)]['numerator'],1)
        self.assertEqual(result.witness[str(u)]['denominator'],3)
        self.assertTrue(result.exact_substitution_verified)

    def test_algebraic_witness_is_not_decimal(self):
        u=z3.Real('toy_root')
        result=solve_exact([u],[u*u==real_literal(2)],[(1,2)])
        self.assertEqual(result.status,Status.SAT)
        self.assertEqual(result.witness[str(u)]['kind'],'real_algebraic')
        self.assertIn('root-obj',result.witness[str(u)]['sexpr'])
        self.assertTrue(result.exact_substitution_verified)
        self.assertFalse(result.independent_certificate_verified)

    def test_exact_real_algebraic_input(self):
        u=z3.Real('toy_algebraic_coefficient')
        root=z3.simplify(z3.Sqrt(real_literal(2)))
        self.assertTrue(z3.is_algebraic_value(root))
        result=solve_exact([u],[root*u==real_literal(1)],[(0,1)])
        self.assertEqual(result.status,Status.SAT)
        self.assertEqual(result.witness[str(u)]['kind'],'real_algebraic')

    def test_known_real_UNSAT_not_missing_rational_root(self):
        u=z3.Real('toy_impossible')
        result=solve_exact([u],[u*u+1==0],[(-1,1)])
        self.assertEqual(result.status,Status.UNSAT)
        self.assertFalse(result.independent_certificate_verified)
        self.assertIn('trusted',result.reason)

    def test_box_changes_known_feasibility(self):
        u=z3.Real('toy_outside_box')
        result=solve_exact([u],[u*u==2],[(-1,1)])
        self.assertEqual(result.status,Status.UNSAT)

    def test_twelve_artificial_real_variables(self):
        # A tiny independent chain with known roots +/-sqrt(1/2).
        # No pulse word, factors, Hamiltonian or P1* coefficients are involved.
        us=z3.Reals(' '.join(f'toy_chain_u{j}' for j in range(12)))
        conditions=[us[0]*us[0]==real_literal(F(1,2))]
        conditions.extend(us[j]==us[0] for j in range(1,12))
        result=solve_exact(us,conditions,[(0,1)]*12)
        self.assertEqual(result.status,Status.SAT)
        self.assertEqual(len(result.witness),12)
        self.assertTrue(all(v['kind']=='real_algebraic' for v in result.witness.values()))

    def test_sparse_polynomial_bridge_and_complex_rejection(self):
        u=z3.Real('toy_sparse')
        ledger=TermLedger(20)
        with Polynomial(1,ledger,[((2,),1),((0,),-2)]) as p:
            result=solve_exact([u],[polynomial_expression(p,[u])==0],[(1,2)])
            self.assertEqual(result.status,Status.SAT)
        with Polynomial(1,ledger,[((0,),QComplex(0,1))]) as p:
            with self.assertRaises(ValueError):polynomial_expression(p,[u])

    def test_actual_native_resource_limit_is_UNKNOWN(self):
        u=z3.Real('toy_resource_limit')
        result=solve_exact([u],[u*u==2],[(1,2)],rlimit=1)
        self.assertEqual(result.status,Status.UNKNOWN)
        self.assertTrue(result.reason)
        self.assertFalse(result.witness)

    def test_UNKNOWN_handling_deterministic_injection(self):
        class Unknown:
            def set(self,**_):pass
            def add(self,*_):pass
            def to_smt2(self):return '; injected control-flow test'
            def check(self):return z3.unknown
            def reason_unknown(self):return 'injected unknown, not an actual solver result'
        u=z3.Real('toy_injected')
        with patch('p1star_foundation.solver.z3.SolverFor',return_value=Unknown()):
            result=solve_exact([u],[u==0],[(-1,1)])
        self.assertEqual(result.status,Status.UNKNOWN)
        self.assertIn('injected',result.reason)

    def test_nonpolynomial_and_foreign_symbols_rejected(self):
        u,v=z3.Reals('toy_validate_u toy_validate_v')
        for bad in [u/v==0,z3.ForAll([v],u==v),u**real_literal(F(1,2))==0,u==v]:
            with self.assertRaises(ValueError):solve_exact([u],[bad],[(-1,1)])
        with self.assertRaises(TypeError):real_literal(0.1)
        with self.assertRaises(ValueError):solve_exact([u],[u==0],[(1,-1)])

    def test_proof_export_not_independent_validation(self):
        probe=proof_capability_probe()
        self.assertIn(probe['toy_status'],('unsat','unknown'))
        self.assertFalse(probe['independent_certificate_verified'])
