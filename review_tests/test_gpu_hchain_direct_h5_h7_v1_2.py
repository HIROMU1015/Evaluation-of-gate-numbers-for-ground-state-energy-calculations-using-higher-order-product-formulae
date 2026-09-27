from __future__ import annotations

import json
from pathlib import Path

import run_gpu_hchain_direct_h5_h7 as base
import run_gpu_hchain_direct_h5_h7_v1_1 as v1_1
import run_gpu_hchain_direct_h5_h7_v1_2 as v1_2


def test_parity_amendment_hash_scope_and_threshold_are_fixed() -> None:
    path = base.PROJECT_ROOT / v1_2.PARITY_AMENDMENT
    assert base.sha256(path) == v1_2.PARITY_AMENDMENT_SHA256
    payload = base.load_json(path)
    assert payload["parent_identity_amendment_sha256"] == v1_1.IDENTITY_AMENDMENT_SHA256
    assert payload["trigger"]["gpu_direct_points_completed"] == 31
    assert payload["trigger"]["H5_y8_started"] is False
    assert payload["diagnosis"]["maximum_shift_difference_against_fresh_cpu_at_identical_physical_times_hartree"] < 1e-9
    assert payload["unchanged"][0] == "maximum absolute direct-shift difference threshold 1e-9 Ha"


def test_v1_2_cache_key_adds_parity_amendment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(base.SYSTEMS[5], "group_count", 43)
    phase_a = tmp_path / "phase_a"
    phase_a.mkdir()
    (phase_a / "predictions.json").write_text('{"value": 1}\n', encoding="utf-8")
    (phase_a / "source_manifest.json").write_text('{"source": 1}\n', encoding="utf-8")
    key, material = v1_2.cache_key(phase_a, 5, "m5")
    assert len(key) == 64
    assert material["gpu_identity_amendment_v1_1_sha256"] == v1_1.IDENTITY_AMENDMENT_SHA256
    assert material["gpu_parity_amendment_v1_2_sha256"] == v1_2.PARITY_AMENDMENT_SHA256
    assert material["sector_identity"]["group_count"] == 43


def test_parent_schedule_failure_does_not_replace_same_time_gate(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "output"
    (output / "raw").mkdir(parents=True)
    (output / "raw" / "H5_m5.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        v1_2,
        "same_time_cpu_comparison",
        lambda payload, key: {
            "pass": True,
            "maximum_absolute_direct_shift_difference_hartree": 1e-15,
        },
    )
    monkeypatch.setattr(
        base,
        "compare_raw_to_parent",
        lambda payload, key: {"pass": False, "maximum_absolute_direct_shift_difference_hartree": 1e-7},
    )
    monkeypatch.setattr(
        base,
        "selected_summary",
        lambda payload, system, key: {
            "relative_t_grid_star": 1.35,
            "status": "scorable",
            "numerical": {"maximum_branch_shift_disagreement_hartree": 0.0},
        },
    )
    unitary = {"pass": True, "frobenius_difference": 1e-15}
    parity = v1_2.update_h5_parity(output, "m5", unitary)
    assert parity["m5"]["pass"] is True
    assert parity["m5"]["parent_raw_schedule_diagnostic"]["pass"] is False
    assert parity["m5"]["parent_raw_schedule_diagnostic"]["gate_role"].startswith("diagnostic_only")


def test_parity_amendment_keeps_parent_grid_precision_and_branches() -> None:
    payload = base.load_json(base.PROJECT_ROOT / v1_2.PARITY_AMENDMENT)
    unchanged = "\n".join(payload["unchanged"])
    for required in ("31-point", "complex128", "branch", "1e-9", "1e-10", "cache"):
        assert required in unchanged
