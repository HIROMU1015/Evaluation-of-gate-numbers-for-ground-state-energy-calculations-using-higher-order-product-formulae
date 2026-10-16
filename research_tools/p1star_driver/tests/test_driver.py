from copy import deepcopy
from fractions import Fraction as F
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import z3
from p1star_foundation.algebra import Scope
from p1star_foundation.exact import I, ONE, QComplex, TermLimitExceeded
from p1star_foundation.solver import Decision, Status
from p1star_driver.operators import Arena, dgamma, quadrature, formal_log
from p1star_driver.eligibility import eligibility, sector_entries
from p1star_driver.conditions import Conditions, exact_values, recheck
from p1star_driver.fixtures import toy_matrices, toy_settings, rectangle_fixture
from p1star_driver.pipeline import run_pipeline
from p1star_driver.screen import known_screen
from p1star_driver.authorization import (ApprovalRequired, canonical, sha256, check_approval,
                                         consume_once)
from p1star_driver.science import authorized_input
from p1star_driver.practical import supervise, validate_settings


class AlgebraDriverTests(unittest.TestCase):
    def test_noncommuting_electronic_product(self):
        with Arena() as a:
            n=a.new().add_word(((0,1),(0,0)))
            h=a.new().add_word(((0,1),(1,0))).add_word(((1,1),(0,0)))
            expected=a.new().add_word(((0,1),(1,0))).add_word(((1,1),(0,0)),coefficient=-1)
            self.assertTrue(n.commutator(h).equals(expected))

    def test_car_idempotence_and_nilpotence(self):
        with Arena() as a:
            n=a.new().add_word(((0,1),(0,0)))
            self.assertTrue(n.multiplied(n).equals(n))
            c=a.new().add_word(((0,1),))
            self.assertEqual(len(c.multiplied(c).terms),0)

    def test_exact_CCR_Weyl_tensor_separation(self):
        with Arena() as a:
            n=a.new().add_word(((0,1),(0,0)))
            x=quadrature(n,'X');p=quadrature(n,'P')
            self.assertTrue(x.commutator(p).equals(n.scaled(I)))
            xp=x.multiplied(p)
            self.assertEqual({k.bus for k,_ in xp.terms.items()},{(1,1),(0,0)})
            self.assertTrue(all(k.electronic_body==1 for k,_ in xp.terms.items()))
            self.assertTrue(any(e['scope']=='CCR' for e in a.trace.events))

    def test_exact_input_float_rejected(self):
        with Arena() as a:
            with self.assertRaises(TypeError):a.new().add_word(coefficient=.5)

    def test_formal_log_same_generator(self):
        with Arena() as a:
            g=a.new().add_word(((0,1),(0,0)))
            result=formal_log({'G':g},['G','G'],4,[F(1,3),F(1,2)])
            self.assertTrue(result.equals(g.shifted(1,-I*F(5,6))))
            self.assertTrue(all(k.eta_degree==1 for k,_ in result.terms.items()))

    def test_BCH_through_four_with_chronological_sign(self):
        # Standard BCH log(exp(Y)exp(X)); two tiny electronic generators.
        with Arena() as a:
            g=a.new().add_word(((0,1),(0,0)))
            h=a.new().add_word(((0,1),(1,0))).add_word(((1,1),(0,0))).add_word(((0,1),(0,0)))
            x=g.shifted(1,-I);y=h.shifted(1,-I)
            yx=y.commutator(x,4)
            expected=x.plus(y).plus(yx,F(1,2))
            expected=expected.plus(y.commutator(yx,4),F(1,12))
            expected=expected.plus(x.commutator(x.commutator(y,4),4),F(1,12))
            expected=expected.plus(x.commutator(y.commutator(yx,4),4),F(-1,24))
            result=formal_log({'G':g,'H':h},['G','H'],4,[1,1])
            self.assertTrue(any(k.eta_degree==4 and c for k,c in expected.terms.items()))
            self.assertTrue(result.equals(expected))

    def test_bus_rectangle_known_identity(self):
        with Arena() as a:
            x=a.new().add_word(bus=('X',));p=a.new().add_word(bus=('P',))
            result=formal_log({'J':x,'Q':p},['J','Q','J','Q'],4,[1,-1,-1,1])
            self.assertTrue(result.equals(a.identity().shifted(2,-I)))

    def test_degree_body_and_scope_trace(self):
        with Arena(1) as a:
            f=dgamma([[1,0],[0,1]],a)
            two=f.multiplied(f).shifted(3,I,parameter=0)
            self.assertEqual({k.eta_degree for k,_ in two.terms.items()},{3})
            self.assertEqual({k.electronic_body for k,_ in two.terms.items()},{1,2})
            self.assertIn(Scope.FACTOR,two.relation_scopes)
            self.assertTrue(any(e['scope']=='FIXED_FACTOR_SPECIFIC' for e in a.trace.events))

    def test_invalid_order_and_generator(self):
        with Arena() as a:
            g=a.identity()
            with self.assertRaises(ValueError):formal_log({'G':g},['G'],5,[1])
            with self.assertRaises(ValueError):formal_log({'G':g.shifted(1)},['G'],4,[1])


class EligibilityAndConditionsTests(unittest.TestCase):
    def test_artificial_factor_gate_passes(self):
        with Arena() as a:
            report,_=eligibility(toy_matrices(),a,2)
            self.assertTrue(report['passed'])
            self.assertGreater(report['augmented_rank'],report['one_body_span_rank'])

    def test_commuting_and_degenerate_gate_fails(self):
        with Arena() as a:
            m=toy_matrices()[0]
            report,_=eligibility([m,m],a,2)
            self.assertFalse(report['passed'])
            self.assertFalse(report['checks']['noncommuting_full_fock'])
        spec=rectangle_fixture();spec['matrices'][1]=spec['matrices'][0]
        result=run_pipeline(spec,toy_settings())
        self.assertEqual(result['status'],'INCONCLUSIVE')
        self.assertEqual([s['stage'] for s in result['stages']],['EXACT_INPUT_ELIGIBILITY'])

    def test_sector_identity_kept_in_full_Fock(self):
        with Arena(1) as a:
            triple=a.new().add_word(((0,1),(0,0),(1,1),(1,0),(2,1),(2,0)),degree=2)
            pure=a.new().add_word(((0,1),(0,0),(1,1),(1,0),(2,1),(2,0)))
            self.assertFalse(sector_entries(pure,4,2)[1])
            with Conditions(triple,a.new(),4) as conditions:
                self.assertEqual(len(conditions.rows),1)
                self.assertEqual(conditions.rows[0].category,'higher_body')
                self.assertEqual(conditions.solve([(-1,1)],1000).status,Status.UNSAT)

    def test_sector_tag_is_rejected(self):
        with Arena(1) as a:
            value=a.identity().tagged(Scope.SECTOR).shifted(1)
            with self.assertRaises(ValueError):Conditions(value,a.new(),4)

    def test_all_residual_categories_and_complex_split(self):
        with Arena(1) as a:
            residual=a.new().add_word(degree=1,coefficient=QComplex(1,2))
            residual.add_word(((0,1),(0,0)),degree=2)
            residual.add_word(((0,1),(0,0),(1,1),(1,0)),degree=2)
            residual.add_word(bus=('X',),degree=3)
            with Conditions(residual,a.new(),4) as conditions:
                self.assertEqual({r.category for r in conditions.rows},{'scalar','one_body','two_body','bus_nonidentity'})
                self.assertEqual({r.component for r in conditions.rows},{'real','imag'})
                self.assertFalse(conditions.record()['sector_identities_used'])

    def test_bus_nonidentity_impossibility_is_not_dropped(self):
        with Arena(1) as a:
            x=a.new().add_word(bus=('X',),degree=1)
            with Conditions(x,a.new(),4) as c:
                self.assertEqual(c.solve([(-1,1)],1000).status,Status.UNSAT)
                self.assertEqual(c.rows[0].category,'bus_nonidentity')

    def test_algebraic_SAT_rehydration_recheck_and_tamper(self):
        with Arena(1) as a:
            polynomial=a.new().add_word(degree=2,powers=(2,)).add_word(degree=2,coefficient=-2)
            with Conditions(polynomial,a.new(),4) as c:
                decision=c.solve([(1,2)],1000)
                self.assertEqual(decision.status,Status.SAT)
                self.assertTrue(recheck(c,decision,[(1,2)]))
                variables,_=c.ast();values=exact_values(variables,decision.witness)
                self.assertTrue(z3.is_algebraic_value(values[0]))
                decision.witness['x1']={'kind':'rational','numerator':1,'denominator':1}
                self.assertFalse(recheck(c,decision,[(1,2)]))

    def test_exact_UNSAT_and_native_UNKNOWN(self):
        with Arena(1) as a:
            p=a.new().add_word(powers=(2,)).add_word(coefficient=1)
            with Conditions(p,a.new(),4) as c:
                self.assertEqual(c.solve([(-1,1)],1000).status,Status.UNSAT)
            p=a.new().add_word(powers=(2,)).add_word(coefficient=-2)
            with Conditions(p,a.new(),4) as c:
                self.assertEqual(c.solve([(1,2)],1000,1).status,Status.UNKNOWN)

    def test_sparse_condition_digest_deterministic(self):
        with Arena(1) as a:
            p=a.new().add_word(powers=(1,),coefficient=I)
            with Conditions(p,a.new(),4) as c1,Conditions(p,a.new(),4) as c2:
                self.assertEqual(c1.digest(),c2.digest())


class PipelineScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.sat=run_pipeline(rectangle_fixture(),toy_settings())

    def test_artificial_end_to_end_SAT(self):
        self.assertEqual(self.sat['status'],'KNOWN_CONSTRUCTION_ONLY',self.sat.get('reason'))
        self.assertTrue(self.sat['driver_exact_recheck'])
        self.assertTrue(self.sat['solver']['exact_substitution_verified'])
        self.assertEqual(self.sat['managed_terms_after_cleanup'],0)
        self.assertEqual(self.sat['attempts'],1)
        self.assertEqual(self.sat['known_screen']['matches'][0]['kind'],'SINGLE_FACTOR_QUADRATURE_LOOP')

    def test_artificial_end_to_end_UNSAT_fixed_box(self):
        spec=rectangle_fixture();spec['boxes']=[(0,0)]*4
        result=run_pipeline(spec,toy_settings())
        self.assertEqual(result['status'],'NO_SOLUTION_IN_FIXED_ANSATZ')
        self.assertFalse(result['solver']['independent_certificate_verified'])
        self.assertFalse(result['sector_failure_implies_general_sector_no_go'])

    def test_solver_unknown_no_retry(self):
        decision=Decision(Status.UNKNOWN,'injected artificial timeout')
        with patch('p1star_driver.conditions.Conditions.solve',return_value=decision) as solver:
            result=run_pipeline(rectangle_fixture(),toy_settings())
        self.assertEqual(result['status'],'INCONCLUSIVE');self.assertEqual(solver.call_count,1)

    def test_failure_and_term_limit_inconclusive(self):
        settings=toy_settings();settings['terms']=1
        result=run_pipeline(rectangle_fixture(),settings)
        self.assertEqual(result['status'],'INCONCLUSIVE')
        self.assertEqual(result['managed_terms_after_cleanup'],0)
        self.assertIn('TermLimit',result['reason'])
        with patch('p1star_driver.pipeline.formal_log',side_effect=TimeoutError('injected toy deadline')):
            result=run_pipeline(rectangle_fixture(),toy_settings())
        self.assertEqual(result['status'],'INCONCLUSIVE')

    def test_trace_limit_inconclusive_and_cleanup(self):
        settings=toy_settings();settings['trace_events']=1
        result=run_pipeline(rectangle_fixture(),settings)
        self.assertEqual(result['status'],'INCONCLUSIVE')
        self.assertEqual(result['managed_terms_after_cleanup'],0)
        self.assertIn('event limit',result['reason'])

    def test_screen_identity_commutator_concat_and_no_match(self):
        v=lambda x:z3.RealVal(x)
        p={'J':(0,'X'),'Q':(0,'P'),'R':(1,'P')}
        identity=known_screen(p,['J','J'],[v(1),v(-1)])
        self.assertEqual(identity['matches'][0]['kind'],'TRIVIAL_IDENTITY')
        comm=known_screen(p,['J','R','J','R'],list(map(v,[1,1,-1,-1])))
        self.assertEqual(comm['matches'][0]['kind'],'KNOWN_GROUP_COMMUTATOR')
        concat=known_screen(p,['J','Q','J','Q','J','R','J','R'],list(map(v,[1,1,-1,-1,2,1,-2,-1])))
        self.assertEqual(concat['matches'][0]['kind'],'CONCATENATED_KNOWN_LOOPS')
        unknown=known_screen(p,['J','Q','R'],list(map(v,[1,1,1])),
                             {'stage':'CAR_PARAMETER_SELECTION_CLAIM','constraint_ids':['toy-eq-1'],'explanation':'synthetic claim only'})
        self.assertFalse(unknown['matches']);self.assertFalse(unknown['no_match_means_novel'])
        self.assertFalse(unknown['car_selection']['independently_validated'])

    def test_no_screen_match_does_not_promote_novelty(self):
        with patch('p1star_driver.pipeline.known_screen',return_value={'matches':[],'general_novelty_decided':False}):
            result=run_pipeline(rectangle_fixture(),toy_settings())
        self.assertEqual(result['status'],'INCONCLUSIVE');self.assertTrue(result['formal_consistent'])


class AuthorizationAndResourceTests(unittest.TestCase):
    def bindings(self):
        return {'action':'SYNTHETIC-ONLY','input_sha256':sha256(b'{}'),'settings':toy_settings(),
                'code_sha256':'toy-code','environment_sha256':'toy-env','contract_sha256':'toy-contract','addendum_sha256':'toy-addendum'}

    def synthetic_receipt(self,bindings):
        receipt={'explicit_user_approval':True,'approval_reference':'ARTIFICIAL TEST ONLY; no real authorization',
                 'run_id':'toy-run','attempt':1,'allow_retry':False}
        receipt.update({k:v for k,v in bindings.items() if k not in ('settings','addendum_sha256')})
        receipt['settings_sha256']=sha256(canonical(bindings['settings']))
        receipt['resource_addendum_sha256']=bindings['addendum_sha256']
        return receipt

    def test_missing_science_approval_rejects_before_input(self):
        bindings=self.bindings();bindings['action']='P1STAR-A-v1-PHASE-B-ONE-SHOT'
        reader=Mock(side_effect=AssertionError('input reader must never run'))
        with tempfile.TemporaryDirectory() as d:
            for receipt in (None,{'explicit_user_approval':False}):
                with self.assertRaises(ApprovalRequired):authorized_input(receipt,bindings,'DO_NOT_OPEN',d,reader)
        reader.assert_not_called()

    def test_synthetic_gate_hashes_once_and_no_retry(self):
        bindings=self.bindings();receipt=self.synthetic_receipt(bindings)
        with tempfile.TemporaryDirectory() as d:
            reader=Mock(return_value={})
            self.assertEqual(authorized_input(receipt,bindings,'SYNTHETIC',d,reader),{})
            with self.assertRaises(FileExistsError):authorized_input(receipt,bindings,'SYNTHETIC',d,reader)
            self.assertEqual(reader.call_count,1)
            bad=deepcopy(bindings);bad['input_sha256']='changed'
            with self.assertRaises(ApprovalRequired):check_approval(receipt,**bad)

    def test_import_does_not_load_fixed_science_input(self):
        self.assertNotIn('p1star_driver.science_spec',sys.modules)
        source=Path(__file__).resolve().parents[1]/'science_spec.py'
        tree=ast.parse(source.read_text())
        self.assertTrue(all(isinstance(n,(ast.Expr,ast.FunctionDef)) for n in tree.body))

    def test_settings_are_explicit_and_managed_caps_retained(self):
        with self.assertRaises(ValueError):validate_settings({})
        for key,value in [('terms',200001),('output_bytes',20*1024**2+1)]:
            settings=toy_settings();settings[key]=value
            with self.assertRaises(ValueError):validate_settings(settings)

    def test_one_affined_artificial_worker(self):
        with tempfile.TemporaryDirectory() as d:
            result=supervise(['probe','affinity'],d,toy_settings())
        self.assertIsNone(result['stop_reason']);self.assertEqual(result['worker']['affinity'],[result['worker_cpu']])
        self.assertFalse(result['dedicated_RAM_hard_limit_verified'])

    def test_supervised_artificial_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            result=supervise(['probe','pipeline'],d,toy_settings())
        self.assertIsNone(result['stop_reason'])
        self.assertEqual(result['status'],'KNOWN_CONSTRUCTION_ONLY')
        self.assertTrue(result['worker']['driver_exact_recheck'])
        self.assertEqual(result['math_workers'],1)

    def test_AS_is_virtual_address_space_failure(self):
        settings=toy_settings();settings['address_space_bytes']=128*1024**2
        with tempfile.TemporaryDirectory() as d:
            result=supervise(['probe','as'],d,settings)
        self.assertEqual(result['status'],'INCONCLUSIVE')
        self.assertIn('MemoryError',result['worker']['reason'])
        self.assertFalse(result['dedicated_RAM_hard_limit_verified'])

    def test_wall_abnormal_output_and_RSS_stops(self):
        cases=[('sleep','WALL_LIMIT',{'wall_seconds':1}),('abnormal','ABNORMAL_EXIT',{}),
               ('output','OUTPUT_LIMIT',{'output_bytes':1024}),
               ('rss','RSS_MONITOR_THRESHOLD',{'rss_bytes':24*1024**2})]
        for fixture,reason,changes in cases:
            with self.subTest(fixture=fixture),tempfile.TemporaryDirectory() as d:
                settings=toy_settings();settings.update(changes)
                result=supervise(['probe',fixture],d,settings)
                self.assertEqual(result['status'],'INCONCLUSIVE');self.assertEqual(result['stop_reason'],reason)
                self.assertLessEqual(result['captured_bytes'],settings['output_bytes'])


if __name__=='__main__':unittest.main()
