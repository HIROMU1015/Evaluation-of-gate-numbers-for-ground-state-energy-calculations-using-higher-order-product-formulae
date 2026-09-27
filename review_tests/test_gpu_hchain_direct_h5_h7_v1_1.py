from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_gpu_hchain_direct_h5_h7 as base
import run_gpu_hchain_direct_h5_h7_v1_1 as amended


def test_identity_amendment_hash_and_scope_are_fixed() -> None:
    path = base.PROJECT_ROOT / amended.IDENTITY_AMENDMENT
    assert base.sha256(path) == amended.IDENTITY_AMENDMENT_SHA256
    payload = base.load_json(path)
    assert payload["parent_gpu_extension_sha256"] == base.sha256(
        base.PROJECT_ROOT / base.EXTENSION
    )
    assert payload["allowed_change"] == {
        "path": "expected_sector_identity.H5.group_count",
        "from": 45,
        "to": 43,
    }
    assert payload["trigger"]["direct_points_completed"] == 0
    assert payload["trigger"]["pf_unitaries_built"] == 0


def test_identity_amendment_parent_raw_evidence_is_hash_pinned() -> None:
    root = base.PROJECT_ROOT / base.PARENT_RAW_ROOT
    assert base.sha256(root / "H5_m5.json") == amended.PARENT_H5_M5_RAW_SHA256
    assert base.sha256(root / "H5_y8.json") == amended.PARENT_H5_Y8_RAW_SHA256
    for formula_key in ("m5", "y8"):
        raw = base.load_json(root / f"H5_{formula_key}.json")
        system = raw["results"]["H5"]["system"]
        assert system["num_groups"] == 43
        assert system["sector"]["population_counts"] == [3, 1]
        assert system["sector"]["dimension"] == 50


def test_amended_system_identity_accepts_only_43_groups(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(base.SYSTEMS[5], "group_count", 43)
    valid = {
        "num_groups": 43,
        "sector": {"population_counts": [3, 1], "dimension": 50},
    }
    base.validate_system_identity(valid, 5)
    invalid = json.loads(json.dumps(valid))
    invalid["num_groups"] = 45
    with pytest.raises(RuntimeError, match="sector identity mismatch"):
        base.validate_system_identity(invalid, 5)


def test_amended_cache_key_includes_amendment_and_corrected_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(base.SYSTEMS[5], "group_count", 43)
    phase_a = tmp_path / "phase_a"
    phase_a.mkdir()
    (phase_a / "predictions.json").write_text('{"value": 1}\n', encoding="utf-8")
    (phase_a / "source_manifest.json").write_text('{"source": 1}\n', encoding="utf-8")
    key, material = amended.cache_key(phase_a, 5, "m5")
    assert len(key) == 64
    assert material["gpu_identity_amendment_v1_1_sha256"] == amended.IDENTITY_AMENDMENT_SHA256
    assert material["sector_identity"]["group_count"] == 43
    assert material["dtype"] == "complex128"


def test_h7_identity_and_all_scientific_rules_remain_unchanged() -> None:
    extension = base.load_json(base.PROJECT_ROOT / base.EXTENSION)
    amendment = base.load_json(base.PROJECT_ROOT / amended.IDENTITY_AMENDMENT)
    assert extension["expected_sector_identity"]["H7"] == {
        "family": "odd_cation_triplet",
        "population_counts": [4, 2],
        "dimension": 735,
        "group_count": 105,
    }
    unchanged = "\n".join(amendment["unchanged"])
    for required in ("31-point", "complex128", "branch", "numerical gates", "H7"):
        assert required in unchanged
