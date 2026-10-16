from fractions import Fraction
import unittest

from p1star_driver.operators import Arena,formal_log,quadrature,dgamma
from p1star_driver.fixtures import rectangle_fixture,toy_settings
from p1star_driver.pipeline import run_pipeline
from p1star_driver.practical import validate_settings


def records(expression):return dict(expression.terms.items())


class CachedAlgebraTests(unittest.TestCase):
    def test_bounded_recovery_cap_is_explicit(self):
        settings=toy_settings();settings['terms']=200001
        with self.assertRaises(ValueError):validate_settings(settings)
        settings['technical_recovery_terms_cap']=2000000
        validate_settings(settings)
        settings['terms']=2000001
        with self.assertRaises(ValueError):validate_settings(settings)
    def test_cached_vs_foundation_tensor_products(self):
        snapshots=[]
        for cached in (False,True):
            with Arena(cached=cached) as arena:
                f=dgamma([[1,1],[1,0]],arena)
                g=dgamma([[0,0],[0,1]],arena)
                x=quadrature(f,'X');p=quadrature(g,'P')
                snapshots.append(records(x.multiplied(p).multiplied(p).multiplied(x)))
        self.assertEqual(*snapshots)

    def test_cached_fourth_order_log_matches_reference(self):
        snapshots=[];counts=[]
        for cached in (False,True):
            with Arena(3,cached=cached) as arena:
                f=dgamma([[1,1],[1,0]],arena)
                g=dgamma([[0,0],[0,1]],arena)
                generators={'J':quadrature(f,'X'),'Q':quadrature(g,'P')}
                value=formal_log(generators,['J','Q','J'],4)
                snapshots.append(records(value));counts.append(len(arena.trace.events))
        self.assertEqual(*snapshots)
        self.assertLess(counts[1],counts[0])

    def test_cached_toy_pipeline_and_cleanup(self):
        settings=toy_settings();settings.update(algebra_backend='cached_tensor_products_v1',trace_output='digest_and_derivations')
        result=run_pipeline(rectangle_fixture(),settings)
        self.assertEqual(result['status'],'KNOWN_CONSTRUCTION_ONLY',result.get('reason'))
        self.assertTrue(result['driver_exact_recheck'])
        self.assertEqual(result['managed_terms_after_cleanup'],0)
        self.assertGreater(result['trace']['cache']['hits']['electron'],0)

    def test_cached_ledger_failure_cleanup(self):
        settings=toy_settings();settings.update(algebra_backend='cached_tensor_products_v1',terms=1)
        result=run_pipeline(rectangle_fixture(),settings)
        self.assertEqual(result['status'],'INCONCLUSIVE')
        self.assertEqual(result['managed_terms_after_cleanup'],0)
