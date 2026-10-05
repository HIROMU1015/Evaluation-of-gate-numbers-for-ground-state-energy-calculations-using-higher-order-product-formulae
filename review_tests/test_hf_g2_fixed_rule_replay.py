"""Synthetic/stdlib tests only; no molecular artifact or truth reads."""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from review_response import hf_g2_fixed_rule_replay as core
from review_response import run_hf_g2_fixed_rule_replay as runner


CONSTANTS = {"epsilon_E_hartree": .00015936001019904, "beta": 1.2, "K_current_m3_per_step": 9108}
BASELINE = {"T0_hartree_inverse": 1.0, "B0_continuous": 7e7}


def fixture(deltas=(-1e-6, -2e-6, -3e-6)):
    points, rows, plan = [], [], {}
    for i, (factor, delta) in enumerate(zip((1., 1.3, 1.6), deltas)):
        identifier = "c" + str(i)
        allowance = core.inherited.target_allowance(epsilon_hartree=CONSTANTS["epsilon_E_hartree"],
            beta=1.2, rotations=9108, time_value=factor, baseline_budget=7e7, eta=.10)
        arms = core.inherited.b1_arm_rows(candidate_id=identifier, time_value=factor, factor_of_t0=factor,
            signed_proxy_hartree=delta, allowance_hartree=allowance, gammas=core.GAMMAS,
            beta=1.2, rotations=9108, epsilon_hartree=CONSTANTS["epsilon_E_hartree"])
        for arm in arms:
            arm.update({"condition": "synthetic", "time_hex": factor.hex()})
        rows.extend(arms)
        points.append({"candidate_id": identifier, "time_hartree_inverse": factor,
            "factor_of_T0": factor, "allowance_hartree": allowance, "B1": arms})
        plan[identifier] = {"condition": "synthetic", "time_hex": factor.hex()}
    frontier = [core.inherited.select_condition(rows, arm="B1_local_CISD_proxy", gamma=gamma,
        fallback_candidate_id="c0", fallback_time=1., fallback_budget=7e7) for gamma in core.GAMMAS]
    return {"condition": "synthetic", "candidates": points, "selection": {"B1": frontier}}, plan


class ReplayTests(unittest.TestCase):
    def test_lexical_cheap_projection_skips_undecodable_M1(self):
        text = '{"conditions":[{"condition":"synthetic","candidates":[{"candidate_id":"c0","B1":[],"M1":{"not_decoded":invalid_scalar}}],"selection":{"B1":[],"M1":{"not_decoded":invalid_scalar}}}]}'
        value, decoded = core.lexical_project(text, core.cheap_paths())
        self.assertNotIn("M1", value["conditions"][0]["candidates"][0])
        self.assertFalse(any("M1" in p for p in decoded))

    def test_lexical_conditional_projection_skips_q_zero(self):
        text = '{"conditions":[{"condition":"a","candidates":[{"M1":{"arm":"selected"}}],"selection":{"M1":{}}},{"condition":"b","candidates":[{"M1":{"not_decoded":invalid_scalar}}]}]}'
        value, decoded = core.lexical_project(text, core.spectral_paths([0]))
        self.assertIsNone(value["conditions"][1])
        self.assertTrue(all(p[1] == 0 for p in decoded))

    def test_lexical_strings_delimiters_and_escapes(self):
        text = json.dumps({"skip": {"text": 'x \\" } [ ]'}, "allow": [1, 2]})
        self.assertEqual(core.lexical_project(text, [("allow",)])[0], {"allow": [1, 2]})

    def test_stable_rule_uses_saved_gamma_1p01(self):
        condition, plan = fixture()
        result = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        self.assertEqual((result["q"], result["B2_gamma"]), (0, 1.01))
        self.assertEqual(result["B2"], condition["selection"]["B1"][0])

    def test_sign_instability_escalates_without_truth(self):
        condition, plan = fixture((-1e-6, -2e-6, 3e-6))
        result = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        self.assertEqual((result["q"], result["B2_gamma"]), (1, 1.10))
        self.assertTrue(result["instability"]["proxy_sign_instability"])

    def test_indeterminate_sign_uses_inherited_noise_floor(self):
        condition, plan = fixture((-1e-6, 0., -3e-6))
        result = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        self.assertEqual(result["q"], 1)
        self.assertEqual(result["sign_noise_floor_hartree"], max(1e-12, 1e-6 * CONSTANTS["epsilon_E_hartree"]))

    def test_missing_frontier_fails_without_reconstruction(self):
        condition, plan = fixture()
        condition["selection"]["B1"].pop()
        with self.assertRaises(core.ReplayError):
            core.cheap_policy(condition, BASELINE, CONSTANTS, plan)

    def test_saved_selector_tamper_fails(self):
        condition, plan = fixture()
        condition["selection"]["B1"][0]["frozen_continuous_budget"] *= 1.01
        with self.assertRaises(core.ReplayError):
            core.cheap_policy(condition, BASELINE, CONSTANTS, plan)

    def test_exact_time_hex_required(self):
        condition, plan = fixture()
        plan["c1"]["time_hex"] = (1.3 + 1e-15).hex()
        with self.assertRaises(core.ReplayError):
            core.cheap_policy(condition, BASELINE, CONSTANTS, plan)

    def test_q_zero_H1_rejects_spectral(self):
        condition, plan = fixture()
        cheap = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        self.assertEqual(core.h1_final(cheap, None, CONSTANTS)["action"], cheap["B2"])
        with self.assertRaises(core.ReplayError):
            core.h1_final(cheap, {}, CONSTANTS)

    def test_q_one_unusable_retains_B2(self):
        condition, plan = fixture((-1e-6, -2e-6, 3e-6))
        cheap = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        spectral = {"rows": [{"candidate_id": cheap["B2"]["selected_candidate"], "e_use_hartree": 1e-6, "abstained": True}], "selection": cheap["B0"]}
        result = core.h1_final(cheap, spectral, CONSTANTS)
        self.assertEqual(result["source"], "M1_unusable")
        self.assertEqual(result["action"], cheap["B2"])

    def test_q_one_inconsistency_switches_to_frozen_M1(self):
        condition, plan = fixture((-1e-6, -2e-6, 3e-6))
        cheap = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        m1 = deepcopy(cheap["B2"])
        m1["frozen_continuous_budget"] *= 1.2
        spectral = {"rows": [{"candidate_id": cheap["B2"]["selected_candidate"], "e_use_hartree": 1.5e-4, "abstained": False}], "selection": m1}
        result = core.h1_final(cheap, spectral, CONSTANTS)
        self.assertEqual(result["source"], "B2_invalidated")
        self.assertEqual(result["action"], m1)

    def test_q_one_consistent_numerical_tie_prefers_B2(self):
        condition, plan = fixture((-1e-6, -2e-6, 3e-6))
        cheap = core.cheap_policy(condition, BASELINE, CONSTANTS, plan)
        m1 = deepcopy(cheap["B2"])
        m1["frozen_continuous_budget"] *= (1 - 1e-13)
        m1["arm"] = "M1_fixed_D2A_spectral"
        spectral = {"rows": [{"candidate_id": cheap["B2"]["selected_candidate"], "e_use_hartree": 0., "abstained": False}], "selection": m1}
        self.assertEqual(core.h1_final(cheap, spectral, CONSTANTS)["action"], cheap["B2"])

    def test_frozen_budget_safety_does_not_use_signed_error(self):
        action = {"selected_candidate": "c", "selected_time_hartree_inverse": 1.6,
                  "frozen_continuous_budget": 5e7, "fallback": False}
        small = core.score_action(action, -1e-6, BASELINE, CONSTANTS, True)
        large = core.score_action(action, -1e-4, BASELINE, CONSTANTS, True)
        self.assertTrue(small["budget_safe"])
        self.assertFalse(large["budget_safe"])
        self.assertFalse(large["safe_target_met"])

    def test_outcome_gate_false_negative_and_fixed_explanation(self):
        safe = {"safe_and_valid": True, "frozen_continuous_budget": 10., "fallback": False}
        unsafe = {**safe, "safe_and_valid": False}
        self.assertEqual(core.outcome(unsafe, unsafe, [safe], 0, True), "D_gate_false_negative")
        self.assertEqual(core.outcome(unsafe, safe, [safe], 1, True), "B_fixed_cheap_explains_change")
        self.assertTrue(core.outcome(unsafe, safe, [], 1, True).startswith("C_"))

    def test_freeze_head_gate_and_payload_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / runner.ARTIFACT / "cheap"
            directory.mkdir(parents=True)
            payload = b'{}\n'
            (directory / "decisions.json").write_bytes(payload)
            marker = {"payload_file": "decisions.json", "payload_sha256": hashlib.sha256(payload).hexdigest()}
            runner.dump(directory / "ACQUISITION_FROZEN.json", marker)
            files = [{"path": p.name, "bytes": p.stat().st_size, "sha256": runner.digest(p.read_bytes())} for p in directory.iterdir()]
            runner.dump(directory / "manifest.json", {"files": files})
            blobs = {p.name: p.read_bytes() for p in directory.iterdir()}
            with patch.object(runner, "head", return_value="other"):
                with self.assertRaises(core.ReplayError):
                    runner.verify_frozen(root, "cheap", "freeze", True)
            with patch.object(runner, "head", return_value="freeze"), patch.object(runner, "git", side_effect=lambda r, *a: blobs[a[-1].split('/')[-1]]):
                self.assertEqual(runner.verify_frozen(root, "cheap", "freeze", True)[0], {})
                (directory / "decisions.json").write_text('{"tamper": true}\n')
                with self.assertRaises(core.ReplayError):
                    runner.verify_frozen(root, "cheap", "freeze", True)

    def test_source_hash_rejects_before_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.json").write_text('{}')
            registry = {"sources": [{"role": "s", "allowed_stages": ["cheap"], "path": "source.json", "sha256": "wrong", "bytes": 2}]}
            with self.assertRaises(core.ReplayError):
                runner.source_bytes(root, registry, "s", "cheap", [])
            with self.assertRaises(core.ReplayError):
                runner.source_bytes(root, registry, "s", "score", [])

    def test_modules_have_no_scientific_imports(self):
        allowed = {"__future__", "argparse", "ast", "copy", "csv", "datetime", "hashlib", "io", "json", "math", "pathlib", "resource", "subprocess", "sys", "time", "review_response"}
        for module in (core, runner):
            tree = ast.parse(Path(module.__file__).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(n.name.split('.')[0] in allowed for n in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module.split('.')[0], allowed)


if __name__ == "__main__":
    unittest.main()
