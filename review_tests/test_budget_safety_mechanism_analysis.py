"""Synthetic arithmetic only: no saved molecular truth or acquisition backend."""

import ast
import math
from pathlib import Path
import unittest

import budget_safety_mechanism_analysis as m


class SafetyTests(unittest.TestCase):
    def test_exact_prediction_gamma_one(self):
        r = m.cheap_capacity(.1, .1, 1, 1)
        self.assertEqual(r["safety_slack_hartree"], 0)
        self.assertIsNone(r["underestimation_to_margin_ratio"])

    def test_gamma_one_underestimation(self):
        r = m.cheap_capacity(.2, .1, 1, 1)
        self.assertLess(r["safety_slack_hartree"], 0)
        self.assertEqual(r["ratio_status"], "undefined_zero_margin_use_slack")

    def test_gamma_one_overestimation(self):
        r = m.cheap_capacity(.1, .2, 1, 1)
        self.assertGreater(r["safety_slack_hartree"], 0)
        self.assertEqual(r["gamma_req_restricted_ge_1"], 1)

    def test_requirement(self):
        r = m.cheap_capacity(.2, .1, 1.1, 1)
        self.assertAlmostEqual(r["gamma_req"], .9 / .8)
        self.assertLess(r["safety_slack_hartree"], 0)

    def test_enough_margin(self):
        self.assertGreater(m.cheap_capacity(.2, .1, 1.2, 1)["safety_slack_hartree"], 0)

    def test_invalid_c(self):
        self.assertEqual(m.cheap_capacity(.1, 1, 1.1, 1)["status"], "invalid_cheap_denominator")

    def test_invalid_e(self):
        self.assertEqual(m.cheap_capacity(1, .1, 1.1, 1)["status"], "no_finite_safe_uncorrected_budget")

    def test_nonfinite(self):
        for value in (math.inf, math.nan, None):
            self.assertTrue(m.cheap_capacity(value, .1, 1.1, 1)["status"].startswith("indeterminate"))

    def test_negative(self):
        self.assertTrue(m.cheap_capacity(-.1, .1, 1.1, 1)["status"].startswith("indeterminate"))

    def test_gamma_below_one(self):
        self.assertTrue(m.cheap_capacity(.1, .1, .9, 1)["status"].startswith("indeterminate"))

    def test_capacity_equals_direct_slack(self):
        for e, c in ((.1, .2), (.2, .1), (.1, .1)):
            for gamma in (1, 1.01, 1.1):
                r = m.cheap_capacity(e, c, gamma, 1)
                self.assertAlmostEqual(r["safety_slack_hartree"], 1 - e - (1 - c) / gamma)

    def test_signed_error_is_not_magnitude_underestimation(self):
        direct, cheap = .1, -.1
        self.assertEqual(abs(direct) - abs(cheap), 0)
        self.assertEqual(abs(direct - cheap), .2)

    def test_same_positive_gamma_fixed_set_argmin(self):
        costs = [2, 1, 3]
        self.assertEqual(min(range(3), key=lambda i: costs[i]),
                         min(range(3), key=lambda i: 1.1 * costs[i]))


class WindowTests(unittest.TestCase):
    def test_eta_zero(self):
        self.assertAlmostEqual(m.width_window(.1, 1, 1, 2, 0, 1), .3)

    def test_eta_ten_percent_tighter(self):
        self.assertLess(m.width_window(.1, 1, 1, 2, .1, 1), m.width_window(.1, 1, 1, 2, 0, 1))

    def test_negative_window(self):
        self.assertLess(m.width_window(.9, 1, 1, 2, 0, 1), 0)

    def test_invalid_window(self):
        for eta in (-.1, 1, math.nan):
            self.assertIsNone(m.width_window(.1, 1, 1, 2, eta, 1))
        self.assertIsNone(m.width_window(.1, 0, 1, 2, 0, 1))


class DecompositionTests(unittest.TestCase):
    def test_identity_required(self):
        self.assertTrue(m.decompose(.1, .1, -1, -1.1, -1.2, -1.1, False)["decomposition_status"].startswith("indeterminate"))

    def test_missing_independent_ground(self):
        self.assertTrue(m.decompose(.1, .1, -1, -1.1, None, -1.1, True)["decomposition_status"].startswith("indeterminate"))

    def test_error_closure(self):
        r = m.decompose(.12, .1, -1.78, -1.9, -2, -1.9, True)
        self.assertAlmostEqual(r["PF_energy_error_signed_hartree"], .12)
        self.assertAlmostEqual(r["H_reference_error_signed_hartree"], .1)
        self.assertAlmostEqual(r["shift_error_signed_hartree"], .02)

    def test_cancellation_not_accuracy_certificate(self):
        r = m.decompose(.1, .1, -1.7, -1.8, -2, -1.9, True)
        self.assertAlmostEqual(r["PF_energy_error_signed_hartree"], .2)
        self.assertAlmostEqual(r["H_reference_error_signed_hartree"], .2)
        self.assertEqual(r["causal_state_or_rank_attribution"], "not_established")

    def test_inconsistent_origin_rejected(self):
        with self.assertRaises(ValueError):
            m.decompose(.12, .1, -1.78, -1.9, -2, -2.9, True)

    def test_rank_reduced_primary_prefix(self):
        core = {"primary_dimension_used": 2, "prefixes": [{"dimension": 1}, {"dimension": 2}, {"dimension": 4}]}
        self.assertEqual(m.prefix(core)["dimension"], 2)

    def test_duplicate_coordinate_rejected(self):
        with self.assertRaises(ValueError):
            m.index([{"id": 1}, {"id": 1}], lambda x: x["id"])

    def test_leading_model(self):
        ratio = .5 * (1 - .5 ** 4 / 5) / (.8 * (1 - .8 ** 4 / 5))
        self.assertAlmostEqual(ratio, .6722589534681074)

    def test_stdlib_import_allowlist(self):
        tree = ast.parse(Path(m.__file__).read_text())
        allowed = {"argparse", "csv", "hashlib", "io", "json", "math", "pathlib", "subprocess", "time"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(n.name in allowed for n in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)


if __name__ == "__main__":
    unittest.main()
