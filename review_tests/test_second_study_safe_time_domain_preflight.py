from __future__ import annotations

import json
from pathlib import Path

import pytest

from review_response import run_second_study_safe_time_domain_preflight as preflight


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GPU_PROMPT = Path(
    "review_response/gpu_second_study_safe_time_domain_preflight_prompt.md"
)


def test_local_preflight_revalidates_frozen_sources_without_new_computation() -> None:
    report = preflight.build_preflight_report(PROJECT_ROOT)
    assert report["status"] == (
        "local_preflight_pass_gpu_server_preflight_pending"
    )
    assert report["protocol_commit"] == preflight.PROTOCOL_COMMIT
    assert report["failed_checks"] == []
    assert report["check_count"] >= 40
    assert report["read_only"] is True
    assert report["new_computation"] == {
        "direct_truth_coordinates": 0,
        "phase_a_proxy_points": 0,
        "new_hamiltonians": 0,
        "new_states": 0,
        "new_fits": 0,
    }
    assert report["phase_a_authorized"] is False
    assert report["phase_b_authorized"] is False
    assert len(report["gpu_server_pending"]) == 3


def test_local_preflight_output_is_json_and_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "preflight.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_second_study_safe_time_domain_preflight.py",
            "--project-root",
            str(PROJECT_ROOT),
            "--output",
            str(output),
        ],
    )
    assert preflight.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["failed_checks"] == []
    with pytest.raises(preflight.PreflightError, match="refusing to overwrite"):
        preflight.main()


def test_gpu_search_is_not_silently_treated_as_complete() -> None:
    report = preflight.build_preflight_report(PROJECT_ROOT)
    assert "pending" in report["status"]
    assert report["gpu_server_pending"]
    assert all(
        row["passed"] for row in report["checks"].values()
    )


def test_gpu_prompt_is_preflight_only_and_pins_reviewed_inputs() -> None:
    prompt = GPU_PROMPT.read_text(encoding="utf-8")
    assert preflight.PROTOCOL_COMMIT in prompt
    assert "3a0dd5684abd7039935c02c14b44e3cb24bb149a" in prompt
    assert preflight.EXPECTED_PROTOCOL_SHA256 in prompt
    assert "preflight_pass_phase_a_not_authorized" in prompt
    assert "no_go_independence_contaminated" in prompt
    assert "Phase A、Phase B、新規分子生成" in prompt
    assert "PREFLIGHT_ONLY_COMPLETE" in prompt
