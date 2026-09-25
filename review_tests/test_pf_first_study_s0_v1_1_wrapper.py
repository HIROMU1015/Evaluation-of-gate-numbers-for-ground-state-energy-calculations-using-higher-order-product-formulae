from __future__ import annotations

import json
from pathlib import Path

from review_response import run_pf_first_study_s0_exact_time_scoring_v1_1 as s0


def test_v1_1_wrapper_applies_source_gate_and_restores_base(monkeypatch, tmp_path: Path) -> None:
    output = tmp_path / "result"
    anchors = {
        "CO_active_eq_sto3g": {
            "condition": "CO_active_eq_sto3g",
            "formula": "current_m3",
            "time": 0.5886807290771116,
            "signed_direct_shift_hartree": -1.706714866789847e-05,
            "truth_provenance": s0.REQUIRED_TRUTH_PROVENANCE,
            "truth_sources": ["h01_saved_truth"],
        }
    }
    monkeypatch.setattr(s0, "_load_and_verify_amendment", lambda root: {})
    monkeypatch.setattr(
        s0, "_preflight_anchor_selections", lambda *args, **kwargs: anchors
    )
    original_anchor = s0._base.nearest_lower_reliable_anchor
    original_cache_key = s0._base._point_cache_key

    def fake_base_run(*args, **kwargs):
        assert s0._base.nearest_lower_reliable_anchor is s0.nearest_lower_h01_native_anchor
        assert s0._base._point_cache_key is s0._point_cache_key_v1_1
        s0._base._write_csv(
            output / "branch_audit.csv",
            [
                {
                    "condition": "CO_active_eq_sto3g",
                    "formula": "current_m3",
                    "point_role": "saved_lower_anchor_recomputation",
                    "time": 0.5886807290771116,
                }
            ],
        )
        s0._base._write_json(output / "source_manifest.json", {})
        s0._base._write_json(
            output / "audit.json",
            {
                "status": "complete_exact_time_scoring",
                "checks": {"parent_gate": True},
                "accounting": {},
            },
        )
        (output / "report.md").write_text("# report\n", encoding="utf-8")
        s0._base._write_json(
            output / "manifest.json",
            {"status": "complete_exact_time_scoring", "artifact_sha256": {}},
        )
        (output / "COMPLETE").touch()
        return {"status": "complete_exact_time_scoring"}

    monkeypatch.setattr(s0._base, "run", fake_base_run)
    audit = s0.run(
        Path("."), Path("."), Path("."), Path("."), output, "cpu", 0, None
    )
    assert audit["status"] == "complete_exact_time_scoring"
    assert audit["checks"]["all_anchor_sources_h01_native"]
    assert audit["checks"]["s0_anchor_protocol_hash_match"]
    assert (output / "COMPLETE").is_file()
    assert s0._base.nearest_lower_reliable_anchor is original_anchor
    assert s0._base._point_cache_key is original_cache_key
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["s0_anchor_protocol_sha256"] == s0.EXPECTED_ANCHOR_PROTOCOL_SHA256
    assert "s0_anchor_protocol.json" in manifest["artifact_sha256"]
