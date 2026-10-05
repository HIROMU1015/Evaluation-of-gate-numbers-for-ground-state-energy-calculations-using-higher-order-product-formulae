"""Synthetic and read-only scalar tests. No molecular or legacy acquisition imports."""
import ast
import copy
import importlib.util
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

PATH = Path(__file__).resolve().parents[1] / "review_response/render_pf_study2_result_synthesis.py"
spec = importlib.util.spec_from_file_location("study2_synthesis", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ScalarHelpers(unittest.TestCase):
    def test_true(self): self.assertTrue(m.flag("True"))
    def test_false(self): self.assertFalse(m.flag("False"))
    def test_missing_not_false(self):
        with self.assertRaises(m.SynthesisError): m.flag("")
    def test_invalid_boolean(self):
        with self.assertRaises(m.SynthesisError): m.flag("unknown")
    def test_missing_not_zero(self):
        with self.assertRaises(m.SynthesisError): m.number("")
    def test_optional_missing(self): self.assertIsNone(m.number("", optional=True))
    def test_negative_kept(self): self.assertEqual(m.number("-2"), -2)
    def test_nonfinite_rejected(self):
        for v in ("NaN", "inf", "-inf"):
            with self.assertRaises(m.SynthesisError): m.number(v)
    def test_duplicate_key_rejected(self):
        with self.assertRaises(m.SynthesisError): m.index([{"id": "a"}, {"id": "a"}], ("id",))
    def test_csv_line_number(self):
        self.assertEqual(m.index([{"id": "a"}], ("id",))[("a",)][0], 2)
    def test_no_science_imports(self):
        tree = ast.parse(PATH.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom): imports.append(node.module or "")
        self.assertFalse(any(s.startswith(("trotterlib", "cupy", "scipy", "qiskit"))
                             for s in imports))


class SavedScalars(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.display = m.build_display()
    def test_source_origin_and_snapshot_bytes(self):
        self.assertEqual(m.verify_sources()["upstream_sources"], 41)
    def test_selected_condition_count(self):
        self.assertEqual(len(self.display["figure_1_selected"]), 8)
    def test_hf_eq_failure_not_rescued(self):
        r = self.display["figure_1_selected"][0]
        self.assertFalse(r["safe"]); self.assertLess(r["slack_microhartree"], 0)
    def test_hf_stretch_safe_sign_flip(self):
        r = self.display["figure_1_selected"][1]
        self.assertTrue(r["safe"]); self.assertNotEqual(r["cheap_sign"], r["truth_sign"])
    def test_all_hchain_selected_safe(self):
        self.assertTrue(all(r["safe"] for r in self.display["figure_1_selected"][2:]))
    def test_unsafe_headroom_undefined(self):
        rows = [r for r in self.display["figure_2_coordinates"] if not r["comparator_safe"]]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["candidate_id"], "eq_1p6T0")
        self.assertIsNone(rows[0]["headroom_percent"])
        self.assertIsNone(rows[0]["window_eta0_microhartree"])
    def test_headroom_below_ten_is_named_safe_scope_only(self):
        self.assertEqual(sum(r["comparator_safe"] for r in self.display["figure_2_coordinates"]), 29)
        self.assertTrue(all(r["headroom_percent"] < 10 for r in self.display["figure_2_coordinates"]
                            if r["comparator_safe"]))
    def test_current_m1_abstentions_preserved(self):
        self.assertEqual(sum(r["abstained"] for r in self.display["figure_2_coordinates"]), 13)
    def test_m1_point_improvement_not_universal(self):
        self.assertEqual(sum(r["point_improves"] for r in self.display["figure_2_coordinates"]), 23)
    def test_empirical_width_not_certificate(self):
        self.assertEqual(sum(r["empirical_width_covers"] for r in self.display["figure_2_coordinates"]), 30)
    def test_hchain_m1_fallback_all(self):
        self.assertTrue(all(r["M1_fallback"] for r in self.display["figure_2_decisions"][2:]))
    def test_decomposition_only_verified_hchain(self):
        rows = self.display["figure_3_components"]
        self.assertEqual(len(rows), 18)
        self.assertEqual({r["condition"] for r in rows}, {"H2", "H4", "H5", "H6", "H7", "H8"})
    def test_fixed_grid_oracle_boundary_not_continuous_optimum(self):
        rows = [r for r in self.display["figure_2_coordinates"] if r["family"] == "H-chain"]
        self.assertTrue(all(r["native_oracle_candidate_id"].endswith("r0.8") for r in rows))
    def test_negative_ten_percent_windows_not_zeroed(self):
        self.assertTrue(all(r["window_eta10_microhartree"] < 0
                            for r in self.display["figure_2_coordinates"] if r["comparator_safe"]))
    def test_decimal_display_and_row_pointers(self):
        self.assertEqual(m.validate_display(self.display)["source_row_pointers_checked"], 200)
    def test_corrupted_display_rejected(self):
        display = copy.deepcopy(self.display)
        display["figure_1_selected"][0]["u_microhartree"] += 1
        with self.assertRaises(m.SynthesisError): m.validate_display(display)


class PublishedMaterials(unittest.TestCase):
    def test_final_display_is_saved_scalar_display(self):
        stored = json.loads((m.ROOT / m.OUT / "figure_data.json").read_text())
        self.assertEqual(stored, m.build_display())

    def test_figure_manifest_hashes_and_self_exclusion(self):
        manifest_path = m.ROOT / m.OUT / "figure_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertTrue(manifest["manifest_self_excluded"])
        self.assertEqual(len(manifest["files"]), 11)
        for entry in manifest["files"]:
            path = m.ROOT / entry["path"]
            self.assertNotEqual(path, manifest_path)
            self.assertEqual(path.stat().st_size, entry["bytes"])
            self.assertEqual(m.sha(path), entry["sha256"])

    def test_literature_access_scope_not_overstated(self):
        registry = json.loads((m.ROOT / m.DOC / "related_work_registry.json").read_text())
        self.assertEqual(len(registry["entries"]), 10)
        self.assertTrue(registry["gpt_review_access_claims_separate_from_codex_access"])
        self.assertEqual(sum(e["technical_access"] == "relevant_full_text_checked"
                             for e in registry["entries"]), 2)
        self.assertTrue(all(not e["external_method_implemented"] for e in registry["entries"]))
        self.assertIn("not_retrieved", registry["entries"][0]["publication"]["technical_full_text_access"])

    def test_local_markdown_targets_exist(self):
        paths = list((m.ROOT / m.DOC).glob("*.md"))
        paths += [m.ROOT / "paper/study2/README.md", m.ROOT / "paper/study2/figure_captions.md"]
        checked = 0
        for path in paths:
            for target in re.findall(r"!?\[[^\]]*\]\(([^)\n]+)\)", path.read_text()):
                target = target.strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                resolved = (path.parent / unquote(parsed.path)).resolve()
                self.assertTrue(resolved.is_relative_to(m.ROOT), (path, target))
                self.assertTrue(resolved.exists(), (path, target))
                checked += 1
        self.assertGreater(checked, 70)


if __name__ == "__main__": unittest.main()
