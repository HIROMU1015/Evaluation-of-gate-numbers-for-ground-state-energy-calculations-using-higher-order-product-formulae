"""Scalar-only tests: do not import or execute any science acquisition/scorer."""

import math
import re
import unittest
from pathlib import Path

from study2_evidence_map import assemble, csv_true, finite_budget, read_sources, unique_coordinates


class EvidenceMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.registry = read_sources(Path(__file__).resolve().parents[1])
        cls.evidence = assemble(cls.data)

    def test_pinned_origin_and_snapshot_are_separate_and_identical(self):
        self.assertEqual(len(self.registry), 11)
        self.assertTrue(any(r["origin_result_commit"] != r["verified_snapshot_commit"] for r in self.registry))
        for row in self.registry:
            self.assertEqual(len(row["origin_result_commit"]), 40)
            self.assertEqual(row["origin_blob"], row["snapshot_blob"])
            self.assertEqual(len(row["sha256"]), 64)

    def test_native_families_and_diagnostic_units(self):
        rows = self.evidence["native_main_analysis"]
        self.assertEqual([(r["family"], r["conditions"], r["coordinates"]) for r in rows],
                         [("HF", 2, 6), ("HCl", 2, 6), ("H-chain", 6, 18)])
        self.assertEqual(rows[0]["gamma1_01_coordinate_safe_diagnostic"], 5)
        self.assertEqual([r["safe"] for r in rows[0]["gamma1_01_selected_decisions"]], [False, True])
        self.assertEqual(rows[1]["gamma1_02_coordinate_safe_diagnostic"], 6)

    def test_h3_excluded_not_unsafe(self):
        series = self.evidence["hchain_series"]
        self.assertEqual((series["attempted_systems"], series["reference_eligible_systems"]), (7, 6))
        self.assertEqual(series["excluded"][0]["system"], "H3")
        self.assertIsNone(series["excluded"][0]["unsafe"])
        self.assertEqual(series["q1_measured_conditions"], 0)

    def test_geometry_counts_and_anchor_reuse(self):
        g = self.evidence["h6_geometry"]
        self.assertEqual((g["geometries"], g["coordinates"], g["source_new_truth_coordinates"],
                          g["source_reused_anchor_coordinates"]), (5, 15, 12, 3))
        self.assertEqual((g["gamma1_01_safe_coordinates"], g["M1_formal_abstentions"],
                          g["M1_empirical_width_covers"], g["decomposition_closed"]), (15, 15, 15, 15))

    def test_gamma1_is_slack_only_and_not_operational(self):
        g = self.evidence["h6_geometry"]
        self.assertEqual(g["gamma1_posthoc_safe_coordinates"], 12)
        self.assertEqual(len(g["gamma1_posthoc_unsafe_coordinates"]), 3)
        self.assertTrue(all("R1.60" in x for x in g["gamma1_posthoc_unsafe_coordinates"]))
        for row in self.data["g_analysis"]["analysis"]["rows"]:
            if row["gamma"] == 1:
                self.assertIsNone(row["margin_ratio"])
                self.assertTrue(row["gamma1_uses_additive_slack"])

    def test_geometry_point_accuracy_regimes(self):
        rows = self.evidence["h6_geometry"]["selected_geometry_scalars"]
        self.assertTrue(all(r["E_M_hartree"] < r["E_C_hartree"] for r in rows if r["R_angstrom"] <= 1.2))
        self.assertTrue(all(r["E_M_hartree"] > r["E_C_hartree"] for r in rows if r["R_angstrom"] >= 1.4))
        self.assertLess(self.evidence["h6_geometry"]["gamma_req_truth_diagnostic"]["max"], 1.01)

    def test_rank_accuracy_does_not_imply_budget_value(self):
        rows = self.evidence["rank_diagnostics"]["ranks"]
        self.assertEqual([r["point_better_than_cheap"] for r in rows], [0, 3, 9, 9])
        self.assertEqual([r["finite_hypothetical_budgets"] for r in rows], [0, 0, 2, 6])
        self.assertEqual([r["budget_unavailable"] for r in rows], [9, 9, 7, 3])
        self.assertEqual([r["hypothetical_budget_below_same_time_cheap"] for r in rows], [0, 0, 0, 0])

    def test_nonfinite_or_missing_budget_is_unavailable(self):
        for value in (None, math.nan, math.inf, -1, 0, False, "1"):
            self.assertFalse(finite_budget(value))
        self.assertTrue(finite_budget(10.0))

    def test_prospective_attempted_denominator_and_terminal_records(self):
        p = self.evidence["prospective"]
        self.assertEqual((p["denominators"]["attempted_conditions"], p["denominators"]["scored_conditions"],
                          p["denominators"]["scored_coordinates"], p["denominators"]["family_units"]), (16, 13, 39, 4))
        self.assertEqual(p["families"], ["BeH2", "CH2", "LiF", "LiH"])
        self.assertEqual(len(p["terminal_records"]), 3)
        self.assertTrue(all(r["unsafe"] is None for r in p["terminal_records"]))
        self.assertEqual(p["selected_frozen_decisions"]["B1_gamma_1.01"]["safe"], 6)
        self.assertEqual(p["M1_accepted_performance_count"], 0)

    def test_unconfirmed_decomposition_stays_indeterminate(self):
        self.assertEqual([r["decomposition_indeterminate"] for r in self.evidence["native_main_analysis"]], [6, 6, 0])
        self.assertEqual(self.evidence["prospective"]["decomposition_indeterminate"], 39)
        self.assertEqual(self.evidence["prospective"]["branch_gap_compatible_diagnostics_not_absolute_branch_confirmation"], 37)

    def test_no_pooled_n_or_new_science(self):
        e = self.evidence
        self.assertIsNone(e["pooled_independent_sample_count"])
        self.assertIsNone(e["pooled_success_rate"])
        self.assertEqual(e["new_scientific_actions"], 0)
        self.assertFalse(e["Hchain_new_science_authorized"])
        self.assertFalse(e["source_rescoring"])
        self.assertNotEqual(e["contracts"]["Hchain_and_G"]["times"], e["contracts"]["prospective"]["times"])

    def test_coordinate_overlap_verified_not_pooled(self):
        native = {(r["condition"], r["time_hex"]) for r in self.data["m1"] if r["family"] == "H-chain"}
        rank = {(r["system"], r["time_hex"]) for r in self.data["r_analysis"]["analysis"]["rows"]}
        anchor = {("H6", r["time_hex"]) for r in self.data["g_analysis"]["analysis"]["rows"] if r["geometry"] == "H6_R1.00"}
        self.assertEqual(len(rank), 9)
        self.assertEqual(len(anchor), 3)
        self.assertTrue(rank <= native and anchor <= native)

    def test_committed_package_matches_scalar_assembly(self):
        import json
        path = Path(__file__).resolve().parents[1] / "artifacts/study2_evidence_integration_20261006/evidence_scalars.json"
        self.assertEqual(json.loads(path.read_text()), self.evidence)

    def test_review_document_local_links_exist(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "docs/second_study_v2/evidence_integration_20261006").glob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith("https://"):
                    self.assertTrue((path.parent / target).is_file(), f"Missing link: {path.name}: {target}")

    def test_unknown_boolean_and_duplicate_coordinates_fail_closed(self):
        with self.assertRaises(ValueError):
            csv_true("")
        with self.assertRaises(ValueError):
            unique_coordinates([{"time_hex": "0x1p0"}] * 2, ("time_hex",))


if __name__ == "__main__":
    unittest.main()
