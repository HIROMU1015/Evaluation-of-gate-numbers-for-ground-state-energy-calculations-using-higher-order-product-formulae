#!/usr/bin/env python3
"""Audit D2-A branch scoring without running any scientific computation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence


RESULT_COMMIT = "e1fd81dc0f3c58396b99fee40ac55987b9dc4f07"
PREDICTION_COMMIT = "49c7bc017647b2922bd0e86cc95b3f45cff612f5"
PROTOCOL_RELATIVE = (
    "review_response/"
    "pf_spectral_recoverability_d2_a_scoring_audit_protocol.json"
)
PROTOCOL_SHA256 = "4542976fcbabc15af789cbbb84761ddc1338132b071dc459ef74d1db2edb6564"
PREDICTION_ROOT = Path(
    "artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c"
)
RESULT_ROOT = Path(
    "artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c"
)
D1_ROOT = Path("artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2")
FIXED_HASHES = {
    PREDICTION_ROOT / "prediction.json":
        "cc496d70c0d7c48239b6f6dd9f69fa351a1b65f9109bb4b1588da1f17dd16226",
    PREDICTION_ROOT / "manifest.json":
        "7f424e75ace03cae645b39cebe9875ecf2c3722828728d326bd715e13f45ec3b",
    RESULT_ROOT / "coordinate_scoring.csv":
        "4381eb3d99e58ca85e941eb8d3189502b360e3ac70eed1aedacfd5b2c90c63c5",
    RESULT_ROOT / "coordinate_scoring.json":
        "bf4aeb658b298e5a4e0f6231dd1efb3141918a12695c835778b8d2876be85eb5",
    RESULT_ROOT / "decision.json":
        "00b3a35a2e0fd87a55b0b0f24fd3fc35d0fa89f33c01e433ea2dfa328beea2a7",
    RESULT_ROOT / "manifest.json":
        "474c26d6653ee6b07b6c9d7eb0f6bfc8978cfb9dab0c83c83f0173cd18bffaab",
    D1_ROOT / "coordinate_summary.csv":
        "b4bffaddc65a3c9bf25859a65515f1f7959b68374657689d7796f08f5285cd82",
    Path("review_response/pf_spectral_recoverability_d2.py"):
        "04eafd4051430be55c1494a6fbadf1800b2dc7c54ab1c3071a7a3e0a7616d033",
    Path("review_response/run_pf_spectral_recoverability_d2_a_scorer.py"):
        "473d199021fe241144cc8a81f5b7be3fb07be2afc6e2085fb8d6289a07008ad2",
}
COMPLETE_STATUS_ALL_CORRECT = (
    "scoring_audit_coordinate_system_mismatch_confirmed_"
    "physical_branch_6_of_6_stop"
)
COMPLETE_STATUS_PHYSICAL_FAILURE = (
    "scoring_audit_physical_branch_failure_confirmed_stop"
)


class AuditError(RuntimeError):
    """Raised when a fixed scoring-audit identity or definition fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise AuditError("refusing empty audit CSV")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if str(key) not in fields:
                fields.append(str(key))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_output(root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True,
        text=not binary,
    )
    return completed.stdout


def verify_manifest(root: Path, manifest_relative: Path) -> int:
    artifact_root = root / manifest_relative.parent
    manifest = load_json(root / manifest_relative)
    rows = manifest.get("files", [])
    if not rows:
        raise AuditError(f"empty manifest: {manifest_relative}")
    for row in rows:
        path = artifact_root / str(row["path"])
        if (
            not path.is_file()
            or path.stat().st_size != int(row["bytes"])
            or sha256_file(path) != str(row["sha256"])
        ):
            raise AuditError(f"manifest mismatch: {path}")
    return len(rows)


def verify_blob(root: Path, commit: str, relative: Path) -> None:
    blob = git_output(root, "show", f"{commit}:{relative.as_posix()}", binary=True)
    if blob != (root / relative).read_bytes():
        raise AuditError(f"file differs from {commit}: {relative}")


def verify_fixed_identity(root: Path) -> dict[str, Any]:
    head = str(git_output(root, "rev-parse", "HEAD")).strip()
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", RESULT_COMMIT, head],
        cwd=root, check=False, capture_output=True,
    ).returncode != 0:
        raise AuditError("D2-A result commit is not an ancestor of HEAD")
    protocol_path = root / PROTOCOL_RELATIVE
    if sha256_file(protocol_path) != PROTOCOL_SHA256:
        raise AuditError("scoring audit protocol hash mismatch")
    rows = []
    for relative, expected in FIXED_HASHES.items():
        actual = sha256_file(root / relative)
        if actual != expected:
            raise AuditError(f"fixed input hash mismatch: {relative}")
        rows.append({"path": relative.as_posix(), "sha256": actual})
    for relative in (
        PREDICTION_ROOT / "prediction.json",
        PREDICTION_ROOT / "manifest.json",
    ):
        verify_blob(root, PREDICTION_COMMIT, relative)
    for relative in (
        RESULT_ROOT / "coordinate_scoring.csv",
        RESULT_ROOT / "coordinate_scoring.json",
        RESULT_ROOT / "decision.json",
        RESULT_ROOT / "manifest.json",
    ):
        verify_blob(root, RESULT_COMMIT, relative)
    prediction_manifest_count = verify_manifest(
        root, PREDICTION_ROOT / "manifest.json"
    )
    result_manifest_count = verify_manifest(root, RESULT_ROOT / "manifest.json")
    original_decision = load_json(root / RESULT_ROOT / "decision.json")
    if original_decision.get("status") != "d2_a_complete_close_spectral_route_stop":
        raise AuditError("original D2-A formal status changed")
    return {
        "head": head,
        "result_commit_ancestor": True,
        "verified_fixed_inputs": rows,
        "prediction_manifest_entry_count": prediction_manifest_count,
        "result_manifest_entry_count": result_manifest_count,
        "original_formal_status": original_decision["status"],
        "original_formal_status_unchanged": True,
    }


def verify_definition_sources(root: Path) -> dict[str, Any]:
    core = (root / "review_response/pf_spectral_recoverability_d2.py").read_text(
        encoding="utf-8"
    )
    d1 = (root / "review_response/run_pf_spectral_information_pilot_d1.py").read_text(
        encoding="utf-8"
    )
    scorer = (
        root / "review_response/run_pf_spectral_recoverability_d2_a_scorer.py"
    ).read_text(encoding="utf-8")
    required = {
        "d2_absolute_principal": "np.angle(eigenvalue) / time_value" in core,
        "d2_absolute_reference":
            "(float(reference_energy) - principal) / period" in core,
        "d1_exact_ground_phase_removal":
            "np.exp(-1j * exact_energy * time_value) * target_eigenvalue" in d1,
        "d1_relative_shift_reference":
            "principal_shift, saved_shift, 2.0 * np.pi / time_value" in d1,
        "original_scorer_integer_equality":
            "predicted_unwrap == truth_unwrap" in scorer,
        "original_scorer_half_gap_check":
            "estimate_error < 0.5 * phase_gap_energy" in scorer,
    }
    if not all(required.values()):
        raise AuditError(f"definition source check failed: {required}")
    return {
        "checks": required,
        "d2_integer_coordinate": "absolute PF energy winding near H-Ritz energy",
        "d1_integer_coordinate": "exact-ground-removed relative shift winding",
        "direct_integer_equality_is_valid": False,
        "coordinate_system_mismatch_confirmed": True,
    }


def _key(condition: str, time_hex: str) -> tuple[str, str]:
    return str(condition), str(time_hex)


def audit_coordinate(
    prediction: Mapping[str, Any],
    scoring: Mapping[str, Any],
    d1: Mapping[str, str],
) -> dict[str, Any]:
    condition = str(prediction["condition"])
    time_value = float(prediction["time_hartree_inverse"])
    time_hex = str(prediction["time_hex"])
    if (
        condition != str(scoring["condition"])
        or time_hex != str(scoring["time_hex"])
        or condition != str(d1["condition"])
        or time_hex != str(d1["time_hex"])
    ):
        raise AuditError("coordinate identity mismatch")
    primary_dimension = int(prediction["primary_dimension_used"])
    primary = next(
        row for row in prediction["prefixes"]
        if int(row["dimension"]) == primary_dimension
    )
    predicted_shift = float(prediction["signed_shift_estimate_hartree"])
    direct_shift = float(scoring["direct_signed_shift_hartree"])
    if abs(predicted_shift - float(scoring["predicted_signed_shift_hartree"])) > 1e-18:
        raise AuditError("saved predicted shift changed")
    predicted_integer = int(primary["selected_phase_unwrap_integer"])
    d1_integer = int(d1["phase_unwrap_integer"])
    if (
        predicted_integer != int(scoring["predicted_phase_unwrap_integer"])
        or d1_integer != int(scoring["truth_phase_unwrap_integer"])
    ):
        raise AuditError("saved unwrap label changed")

    real = float(primary["selected_unit_circle_eigenvalue_real"])
    imag = float(primary["selected_unit_circle_eigenvalue_imaginary"])
    h_reference = float(primary["h_reference_energy_hartree"])
    principal = math.atan2(imag, real) / time_value
    period = 2.0 * math.pi / time_value
    recomputed_integer = int(round((h_reference - principal) / period))
    recomputed_energy = principal + recomputed_integer * period
    saved_unwrapped_energy = float(primary["selected_unwrapped_energy_hartree"])
    if abs((saved_unwrapped_energy - h_reference) - predicted_shift) > 1e-12:
        raise AuditError("frozen signed shift is inconsistent with H reference")
    if (
        recomputed_integer != predicted_integer
        or abs(recomputed_energy - saved_unwrapped_energy) > 1e-12
    ):
        raise AuditError("D2 absolute unwrap does not reproduce frozen prediction")

    signed_error = predicted_shift - direct_shift
    absolute_error = abs(signed_error)
    raw_phase_error = signed_error * time_value
    phase_error = abs(math.atan2(math.sin(raw_phase_error), math.cos(raw_phase_error)))
    phase_gap = float(d1["phase_gap_radian"])
    half_gap = 0.5 * phase_gap
    half_gap_energy = half_gap / time_value
    physical_branch_correct = phase_error < half_gap
    energy_check = absolute_error < half_gap_energy
    if physical_branch_correct != energy_check:
        raise AuditError("phase and local-energy branch checks disagree")
    common_predicted = h_reference + predicted_shift
    common_truth = h_reference + direct_shift
    return {
        "condition": condition,
        "time_hartree_inverse": time_value,
        "time_hex": time_hex,
        "primary_dimension": primary_dimension,
        "predicted_signed_shift_hartree": predicted_shift,
        "direct_signed_shift_hartree": direct_shift,
        "signed_shift_error_hartree": signed_error,
        "absolute_shift_error_hartree": absolute_error,
        "phase_error_radian": phase_error,
        "d1_phase_gap_radian": phase_gap,
        "half_phase_gap_radian": half_gap,
        "half_gap_energy_hartree": half_gap_energy,
        "absolute_error_to_half_gap_ratio": absolute_error / half_gap_energy,
        "physical_branch_correct": physical_branch_correct,
        "original_branch_correct": bool(scoring["branch_correct"]),
        "d2_absolute_unwrap_integer": predicted_integer,
        "d1_relative_unwrap_integer": d1_integer,
        "integer_labels_equal": predicted_integer == d1_integer,
        "integer_coordinates_directly_comparable": False,
        "h_reference_energy_hartree": h_reference,
        "predicted_energy_on_h_reference_hartree": common_predicted,
        "truth_target_on_h_reference_hartree": common_truth,
        "common_reference_energy_error_hartree": abs(common_predicted - common_truth),
        "abstained": bool(scoring["abstained"]),
        "frozen_budget_safe": scoring["frozen_budget_safe"],
        "quantum_budget_lower_than_main_baseline": bool(
            scoring["quantum_budget_lower_than_main_baseline"]
        ),
    }


def build_manifest(output: Path, names: Sequence[str]) -> dict[str, Any]:
    return {
        "schema": "pf_spectral_recoverability_d2_a_scoring_audit_manifest_v1",
        "files": [
            {
                "path": name,
                "bytes": (output / name).stat().st_size,
                "sha256": sha256_file(output / name),
            }
            for name in names
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    root = args.project_root.resolve()
    protocol_path = (
        args.protocol if args.protocol.is_absolute() else root / args.protocol
    ).resolve()
    if protocol_path != (root / PROTOCOL_RELATIVE).resolve():
        raise AuditError("unexpected scoring audit protocol path")
    identity = verify_fixed_identity(root)
    definitions = verify_definition_sources(root)
    protocol = load_json(protocol_path)
    if (
        protocol.get("status")
        != "post_hoc_scoring_audit_prepared_original_result_unchanged"
        or protocol["completion"].get("d2_b_authorized") is not False
    ):
        raise AuditError("audit protocol boundary mismatch")

    prediction = load_json(root / PREDICTION_ROOT / "prediction.json")
    original_scoring = load_json(root / RESULT_ROOT / "coordinate_scoring.json")
    d1_rows = load_csv(root / D1_ROOT / "coordinate_summary.csv")
    scoring_by_key = {
        _key(row["condition"], row["time_hex"]): row
        for row in original_scoring["rows"]
    }
    d1_by_key = {
        _key(row["condition"], row["time_hex"]): row for row in d1_rows
    }
    rows = []
    for row in prediction["predictions"]:
        key = _key(row["condition"], row["time_hex"])
        if key not in scoring_by_key or key not in d1_by_key:
            raise AuditError(f"missing fixed coordinate input: {key}")
        rows.append(audit_coordinate(row, scoring_by_key[key], d1_by_key[key]))
    if len(rows) != 6 or len(scoring_by_key) != 6 or len(d1_by_key) != 6:
        raise AuditError("audit requires exactly six matched coordinates")

    physical_count = sum(bool(row["physical_branch_correct"]) for row in rows)
    original_count = sum(bool(row["original_branch_correct"]) for row in rows)
    lower_budget_count = sum(
        bool(row["quantum_budget_lower_than_main_baseline"]) for row in rows
    )
    unsafe_count = sum(row["frozen_budget_safe"] is False for row in rows)
    abstention_count = sum(bool(row["abstained"]) for row in rows)
    status = (
        COMPLETE_STATUS_ALL_CORRECT
        if physical_count == 6
        else COMPLETE_STATUS_PHYSICAL_FAILURE
    )
    summary = {
        "coordinate_count": 6,
        "original_integer_based_branch_correct_count": original_count,
        "representation_invariant_physical_branch_correct_count": physical_count,
        "coordinate_system_mismatch_confirmed": True,
        "maximum_absolute_shift_error_hartree": max(
            float(row["absolute_shift_error_hartree"]) for row in rows
        ),
        "maximum_absolute_error_to_half_gap_ratio": max(
            float(row["absolute_error_to_half_gap_ratio"]) for row in rows
        ),
        "abstention_count": abstention_count,
        "unsafe_frozen_budget_count": unsafe_count,
        "budget_lower_than_main_baseline_count": lower_budget_count,
        "accuracy_recovered_all_development_coordinates": physical_count == 6,
        "certification_cost_advantage_observed": lower_budget_count > 0,
    }
    decision = {
        "schema": "pf_spectral_recoverability_d2_a_scoring_audit_decision_v1",
        "status": status,
        "classification": "post_hoc_procedural_definition_audit",
        "protocol_sha256": PROTOCOL_SHA256,
        "original_d2_a_status": "d2_a_complete_close_spectral_route_stop",
        "original_d2_a_status_unchanged": True,
        "original_d2_a_artifacts_modified": False,
        "prediction_modified": False,
        "new_scientific_computation_count": 0,
        "arnoldi_action_count": 0,
        "hamiltonian_action_count": 0,
        "pf_action_count": 0,
        "new_truth_count": 0,
        "gpu_query_count": 0,
        "gpu_allocation_count": 0,
        "gpu_kernel_count": 0,
        "d2_b_authorized": False,
        "independent_generalization_claim": False,
        "summary": summary,
        "research_interpretation": (
            "accuracy_recovered_but_certification_cost_not_advantageous"
            if physical_count == 6 and lower_budget_count == 0
            else "physical_branch_failure_requires_route_closure_review"
        ),
        "next_step": "stop_for_full_research_direction_review",
        "wall_seconds": time.perf_counter() - started,
    }
    output = (
        args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    ).resolve()
    if output.exists():
        raise AuditError("scoring audit output must be new")
    output.mkdir(parents=True)
    write_csv(output / "coordinate_scoring_audit.csv", rows)
    atomic_json(output / "coordinate_scoring_audit.json", {
        "schema": "pf_spectral_recoverability_d2_a_coordinate_scoring_audit_v1",
        "rows": rows,
    })
    atomic_json(output / "definition_audit.json", definitions)
    atomic_json(output / "source_identity.json", identity)
    atomic_json(output / "decision.json", decision)
    report = (
        "# D2-A scoring audit\n\n"
        f"- Status: `{status}`\n"
        "- Classification: post-hoc procedural definition audit\n"
        f"- Original integer-based branch correct: {original_count}/6\n"
        f"- Representation-invariant physical branch correct: {physical_count}/6\n"
        f"- Maximum absolute shift error: "
        f"{summary['maximum_absolute_shift_error_hartree']:.12e} Ha\n"
        f"- Maximum error / half-gap: "
        f"{summary['maximum_absolute_error_to_half_gap_ratio']:.12e}\n"
        f"- Unsafe frozen budgets: {unsafe_count}\n"
        f"- Budgets below main baseline: {lower_budget_count}/6\n"
        "- Original D2-A decision changed: no\n"
        "- D2-B authorized: false\n"
        "- Next step: full research-direction review\n"
    )
    (output / "report.md").write_text(report, encoding="utf-8")
    atomic_json(output / "SCORING_AUDIT_COMPLETE.json", {
        "status": status,
        "original_d2_a_status_unchanged": True,
        "d2_b_authorized": False,
    })
    names = [
        "coordinate_scoring_audit.csv", "coordinate_scoring_audit.json",
        "definition_audit.json", "source_identity.json", "decision.json",
        "report.md", "SCORING_AUDIT_COMPLETE.json",
    ]
    atomic_json(output / "manifest.json", build_manifest(output, names))
    print(json.dumps({
        "status": status,
        "summary": summary,
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
