from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


EXPECTED_GAMMAS = (1.01, 1.02, 1.05, 1.10)
PREDICTION_FILES = (
    "prediction.json",
    "prediction.sha256",
    "PREDICTION_FROZEN.json",
    "source_audit.json",
    "access_audit.json",
    "resource_audit.json",
    "manifest.json",
)


class S1AError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def exact_gamma_frontier(selection: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(selection)
    required = {
        "gamma",
        "eligible_candidates",
        "selected_candidate",
        "fallback",
        "frozen_continuous_budget",
    }
    failures: list[str] = []
    if len(rows) != len(EXPECTED_GAMMAS):
        failures.append("gamma_arm_count_not_four")
    gammas: list[float] = []
    for index, row in enumerate(rows):
        missing = sorted(required - set(row))
        if missing:
            failures.append(f"arm_{index}_missing_fields:{','.join(missing)}")
            continue
        try:
            gammas.append(float(row["gamma"]))
        except (TypeError, ValueError):
            failures.append(f"arm_{index}_gamma_not_numeric")
    if sorted(gammas) != sorted(EXPECTED_GAMMAS):
        failures.append("gamma_values_not_exact_frontier")
    return {
        "available": not failures,
        "arm_count": len(rows),
        "gamma_values": sorted(gammas),
        "failures": failures,
    }


def manifest_payload(root: Path, names: Iterable[str], schema: str, status: str) -> dict[str, Any]:
    files = []
    for name in sorted(names):
        data = (root / name).read_bytes()
        files.append({"path": name, "bytes": len(data), "sha256": sha256_bytes(data)})
    return {
        "schema": schema,
        "status": status,
        "entry_count": len(files),
        "files": files,
        "manifest_self_excluded": True,
    }


def git_output(project_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=project_root, text=True, stderr=subprocess.STDOUT
    ).strip()


def verify_prediction_commit(
    project_root: Path,
    prediction_root: Path,
    prediction_commit: str,
    artifact_relative: Path,
) -> dict[str, Any]:
    resolved = git_output(project_root, "rev-parse", f"{prediction_commit}^{{commit}}")
    if git_output(project_root, "rev-parse", "HEAD") != resolved:
        raise S1AError("scorer HEAD must equal prediction freeze commit")
    verified = []
    for name in PREDICTION_FILES:
        current = (prediction_root / name).read_bytes()
        committed = subprocess.check_output(
            ["git", "show", f"{resolved}:{(artifact_relative / name).as_posix()}"],
            cwd=project_root,
            stderr=subprocess.STDOUT,
        )
        if current != committed:
            raise S1AError(f"prediction differs from freeze commit: {name}")
        verified.append(name)
    return {
        "prediction_commit": resolved,
        "verified_prediction_commit_files": verified,
        "verified_prediction_commit_file_count": len(verified),
    }


def classify_contract_failure(prediction: dict[str, Any]) -> dict[str, Any]:
    if prediction.get("contract_replayable") is not False:
        raise S1AError("contract-failure scorer requires contract_replayable=false")
    return {
        "classification_code": "D",
        "classification": "contract_or_cost_not_replayable",
        "classification_priority": ["D", "B", "A", "C", "E"],
        "reason": "required saved four-gamma cheap frontier is missing for at least one condition",
        "truth_required_for_classification": False,
    }
