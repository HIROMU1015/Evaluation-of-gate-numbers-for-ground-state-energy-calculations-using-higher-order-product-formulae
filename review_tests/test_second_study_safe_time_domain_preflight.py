from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from review_response import run_second_study_safe_time_domain_preflight as preflight


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GPU_PROMPT = Path(
    "review_response/gpu_second_study_safe_time_domain_preflight_prompt.md"
)
GPU_RETRY_PROMPT = Path(
    "review_response/"
    "gpu_second_study_safe_time_domain_preflight_v1_1_retry_prompt.md"
)
AMENDMENT_PATH = Path(
    "review_response/"
    "second_study_safe_time_domain_preflight_amendment_v1_1.json"
)


def test_local_preflight_revalidates_frozen_sources_without_new_computation() -> None:
    report = preflight.build_preflight_report(PROJECT_ROOT)
    assert report["status"] == (
        "local_preflight_pass_gpu_server_preflight_pending"
    )
    assert report["protocol_commit"] == preflight.PROTOCOL_COMMIT
    assert report["schema"].endswith("_v1_1")
    assert report["preflight_amendment_sha256"] == (
        preflight.EXPECTED_AMENDMENT_SHA256
    )
    assert report["origin_repository_identity"] == (
        preflight.EXPECTED_REPOSITORY_ID
    )
    assert report["failed_checks"] == []
    assert report["check_count"] == 67
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


def test_v1_1_amendment_hash_and_scientific_nonchange_are_frozen() -> None:
    amendment = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    actual = hashlib.sha256(AMENDMENT_PATH.read_bytes()).hexdigest()
    sidecar = Path(str(AMENDMENT_PATH) + ".sha256").read_text().split()[0]
    assert actual == sidecar == preflight.EXPECTED_AMENDMENT_SHA256
    assert amendment["parent_protocol"] == {
        "commit": preflight.PROTOCOL_COMMIT,
        "sha256": preflight.EXPECTED_PROTOCOL_SHA256,
    }
    assert amendment["preserved_failed_preflight"]["result_commit"] == (
        "e1891dfd24ec5f0064b0598e51eb260073fd2b1e"
    )
    assert not any(amendment["scientific_protocol_changes"].values())
    assert amendment["retry_rules"]["phase_a_authorized"] is False
    assert amendment["retry_rules"]["phase_b_authorized"] is False


@pytest.mark.parametrize(
    "remote",
    [
        preflight.EXPECTED_REMOTE,
        (
            "https://github.com/HIROMU1015/"
            "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
            "using-higher-order-product-formulae.git"
        ),
        (
            "ssh://git@github.com/HIROMU1015/"
            "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
            "using-higher-order-product-formulae.git"
        ),
    ],
)
def test_supported_remote_transports_have_one_repository_identity(
    remote: str,
) -> None:
    assert preflight.canonical_repository_identity(remote) == (
        preflight.EXPECTED_REPOSITORY_ID
    )


def test_different_repository_does_not_match_expected_identity() -> None:
    measured = preflight.canonical_repository_identity(
        "https://github.com/HIROMU1015/not-the-frozen-repository.git"
    )
    assert measured != preflight.EXPECTED_REPOSITORY_ID


def test_full_preflight_accepts_gpu_https_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    https_remote = (
        "https://github.com/HIROMU1015/"
        "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
        "using-higher-order-product-formulae.git"
    )
    original_git_text = preflight._git_text

    def gpu_git_text(project_root: Path, *args: str) -> str:
        if args == ("remote", "get-url", "origin"):
            return https_remote
        return original_git_text(project_root, *args)

    monkeypatch.setattr(preflight, "_git_text", gpu_git_text)
    report = preflight.build_preflight_report(PROJECT_ROOT)
    assert report["origin"] == https_remote
    assert report["origin_repository_identity"] == (
        preflight.EXPECTED_REPOSITORY_ID
    )
    assert report["checks"]["git:origin"]["passed"] is True
    assert report["failed_checks"] == []


@pytest.mark.parametrize(
    "remote",
    [
        "https://example.com/HIROMU1015/repository.git",
        "https://token@github.com/HIROMU1015/repository.git",
        "https://github.com/HIROMU1015/repository.git?ref=main",
        "ftp://github.com/HIROMU1015/repository.git",
        "https://github.com/HIROMU1015/repository/extra.git",
        "ssh://abe@github.com/HIROMU1015/repository.git",
    ],
)
def test_unsafe_or_ambiguous_remote_forms_are_rejected(remote: str) -> None:
    with pytest.raises(preflight.PreflightError):
        preflight.canonical_repository_identity(remote)


def test_gpu_v1_1_retry_prompt_preserves_failure_and_stops_before_phase_a() -> None:
    prompt = GPU_RETRY_PROMPT.read_text(encoding="utf-8")
    assert "0f3381863ed0eb0a31b59b8018e816bebe3840f7" in prompt
    assert preflight.EXPECTED_AMENDMENT_SHA256 in prompt
    assert "e1891dfd24ec5f0064b0598e51eb260073fd2b1e" in prompt
    assert "gpu-second-study-safe-time-domain-preflight-v1-1-20260927" in prompt
    assert "/usr/bin/python3" in prompt
    assert "67/67" in prompt
    assert "preflight_pass_phase_a_not_authorized" in prompt
    assert "Phase A、Phase B、新規Hamiltonian" in prompt
