#!/usr/bin/env python3
"""Identity-amended v1.1 wrapper for the frozen H5/H7 GPU runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import run_gpu_hchain_direct_h5_h7 as base


IDENTITY_AMENDMENT = Path(
    "review_response/hchain_direct_gpu_h5_h7_identity_amendment_v1_1.json"
)
IDENTITY_AMENDMENT_MD = Path(
    "review_response/hchain_direct_gpu_h5_h7_identity_amendment_v1_1.md"
)
IDENTITY_AMENDMENT_SHA256 = (
    "589f1e26f8e912550e39f35c96121d4a33961855ff98f877a256c2659b5bd392"
)
PARENT_H5_M5_RAW_SHA256 = (
    "da52273613ce59df6347d99001a7daafece1281cc65fbe298de94d7bb998a3d7"
)
PARENT_H5_Y8_RAW_SHA256 = (
    "9c5cecece27197ebfa858693fe6376015b54bc89d55c2d4f6db12844958a44b6"
)

_ORIGINAL_VERIFY_PARENT_IDENTITY = base.verify_parent_identity
_ORIGINAL_VALIDATE_PHASE_A = base.validate_phase_a
_ORIGINAL_INITIALIZE_OUTPUT = base.initialize_output
_ORIGINAL_CACHE_KEY = base.cache_key
_ORIGINAL_FOCUSED_TEST_ARGS = base.focused_test_args
_BASE_SOURCE_PATHS = tuple(base.SOURCE_PATHS)


def verify_parent_identity() -> dict[str, str]:
    identity = _ORIGINAL_VERIFY_PARENT_IDENTITY()
    checks = {
        base.PROJECT_ROOT / IDENTITY_AMENDMENT: IDENTITY_AMENDMENT_SHA256,
        base.PROJECT_ROOT / base.PARENT_RAW_ROOT / "H5_m5.json": PARENT_H5_M5_RAW_SHA256,
        base.PROJECT_ROOT / base.PARENT_RAW_ROOT / "H5_y8.json": PARENT_H5_Y8_RAW_SHA256,
    }
    for path, expected in checks.items():
        actual = base.sha256(path)
        if actual != expected:
            raise RuntimeError(f"identity amendment evidence mismatch: {path}: {actual}")
    identity["gpu_identity_amendment_v1_1_sha256"] = IDENTITY_AMENDMENT_SHA256
    return identity


def focused_test_args() -> list[str]:
    return [
        base.sys.executable,
        "-m",
        "pytest",
        "-q",
        "review_tests/test_gpu_hchain_direct_h5_h7_v1_1.py",
        "review_tests/test_hchain_direct_optimal_time_scaling.py",
        "review_tests/test_hchain_direct_optimal_time_scaling_partial_v1_2.py",
        "review_tests/test_hchain_direct_sector_v1_1.py",
        "review_tests/test_sector_pf.py",
    ]


def install_base_overrides() -> None:
    base.SYSTEMS[5]["group_count"] = 43
    base.SOURCE_PATHS = tuple(
        dict.fromkeys(
            _BASE_SOURCE_PATHS
            + (
                IDENTITY_AMENDMENT,
                IDENTITY_AMENDMENT_MD,
                Path("review_response/run_gpu_hchain_direct_h5_h7_v1_1.py"),
                Path("review_tests/test_gpu_hchain_direct_h5_h7_v1_1.py"),
            )
        )
    )
    base.verify_parent_identity = verify_parent_identity
    base.focused_test_args = focused_test_args
    base.validate_phase_a = validate_phase_a
    base.initialize_output = initialize_output
    base.cache_key = cache_key


def _copy_amendment(output: Path) -> None:
    for source, name in (
        (IDENTITY_AMENDMENT, "gpu_identity_amendment_v1_1.json"),
        (IDENTITY_AMENDMENT_MD, "gpu_identity_amendment_v1_1.md"),
    ):
        source_path = base.PROJECT_ROOT / source
        destination = output / name
        if destination.exists():
            if base.sha256(destination) != base.sha256(source_path):
                raise RuntimeError(f"identity amendment copy mismatch: {destination}")
        else:
            shutil.copyfile(source_path, destination)


def _refresh_manifest(output: Path, schema: str, status: str) -> None:
    public = sorted(
        path
        for path in output.rglob("*")
        if path.is_file()
        and ".runtime" not in path.parts
        and path.name != "manifest.json"
    )
    base.parent._manifest(
        output,
        public,
        {
            "schema_version": schema,
            "status": status,
            "identity_amendment_v1_1_sha256": IDENTITY_AMENDMENT_SHA256,
            "created_at_utc": base.utc_now(),
        },
    )


def freeze_phase_a(output: Path, physical_gpu: int) -> None:
    install_base_overrides()
    base.freeze_phase_a(output, physical_gpu)
    _copy_amendment(output)
    audit_path = output / "audit.json"
    audit = base.load_json(audit_path)
    audit["identity_amendment_v1_1_sha256"] = IDENTITY_AMENDMENT_SHA256
    audit["corrected_expected_H5_group_count"] = 43
    base.write_json(audit_path, audit)
    marker_path = output / "PHASE_A_FROZEN"
    marker = base.load_json(marker_path)
    marker["identity_amendment_v1_1_sha256"] = IDENTITY_AMENDMENT_SHA256
    base.write_json(marker_path, marker)
    _refresh_manifest(
        output,
        "hchain_direct_gpu_h5_h7_phase_a_manifest_v1_1",
        "phase_a_frozen_no_truth_generated_identity_amended",
    )


def validate_phase_a(phase_a: Path) -> dict[str, Any]:
    marker = _ORIGINAL_VALIDATE_PHASE_A(phase_a)
    if marker.get("identity_amendment_v1_1_sha256") != IDENTITY_AMENDMENT_SHA256:
        raise RuntimeError("Phase A identity amendment hash mismatch")
    amendment_copy = phase_a / "gpu_identity_amendment_v1_1.json"
    if not amendment_copy.exists() or base.sha256(amendment_copy) != IDENTITY_AMENDMENT_SHA256:
        raise RuntimeError("Phase A identity amendment copy mismatch")
    if base.load_json(amendment_copy)["allowed_change"] != {
        "path": "expected_sector_identity.H5.group_count",
        "from": 45,
        "to": 43,
    }:
        raise RuntimeError("identity amendment scope widened")
    verify_parent_identity()
    return marker


def initialize_output(output: Path, phase_a: Path, h_chain: int) -> None:
    _ORIGINAL_INITIALIZE_OUTPUT(output, phase_a, h_chain)
    _copy_amendment(output)


def cache_key(
    phase_a: Path, h_chain: int, formula_key: str
) -> tuple[str, dict[str, Any]]:
    _, material = _ORIGINAL_CACHE_KEY(phase_a, h_chain, formula_key)
    material["gpu_identity_amendment_v1_1_sha256"] = IDENTITY_AMENDMENT_SHA256
    material["sector_identity"] = dict(base.SYSTEMS[h_chain])
    material["sector_identity"].pop("id", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), material


def _register_amendment_in_raw(output: Path, h_chain: int, formula_key: str) -> None:
    path = output / "raw" / f"H{h_chain}_{formula_key}.json"
    payload = base.load_json(path)
    payload.setdefault("registered_amendments", {})[
        "gpu_identity_v1_1_sha256"
    ] = IDENTITY_AMENDMENT_SHA256
    base.write_json(path, payload)


def run_cell(
    phase_a: Path,
    output: Path,
    h_chain: int,
    formula_key: str,
    physical_gpu: int,
    h5_output: Path | None,
) -> dict[str, Any]:
    install_base_overrides()
    result = base.run_cell(
        phase_a,
        output,
        h_chain,
        formula_key,
        physical_gpu,
        h5_output,
    )
    _register_amendment_in_raw(output, h_chain, formula_key)
    return result


def analyze_outputs(
    phase_a: Path,
    h5_output: Path,
    h7_output: Path | None,
    full_test_log: Path | None,
) -> dict[str, Any]:
    install_base_overrides()
    result = base.analyze_outputs(phase_a, h5_output, h7_output, full_test_log)
    outputs = [h5_output] + ([h7_output] if h7_output is not None else [])
    for output in outputs:
        assert output is not None
        audit_path = output / "audit.json"
        audit = base.load_json(audit_path)
        audit["gpu_identity_amendment_v1_1_sha256"] = IDENTITY_AMENDMENT_SHA256
        audit["expected_H5_group_count"] = 43
        base.write_json(audit_path, audit)
        report_path = output / "report.md"
        report = report_path.read_text(encoding="utf-8")
        report += (
            "\nIdentity amendment v1.1 corrected only the expected H5 group "
            "count from 45 to the parent- and fresh-source-consistent value 43.\n"
        )
        report_path.write_text(report, encoding="utf-8")
        _refresh_manifest(
            output,
            "hchain_direct_gpu_h5_h7_manifest_v1_1",
            str(result["status"]),
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-phase-a")
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--gpu", type=int, default=1)
    cell = subparsers.add_parser("run-cell")
    cell.add_argument("--phase-a", type=Path, required=True)
    cell.add_argument("--output", type=Path, required=True)
    cell.add_argument("--system", type=int, choices=[5, 7], required=True)
    cell.add_argument("--formula", choices=["m5", "y8"], required=True)
    cell.add_argument("--gpu", type=int, default=1)
    cell.add_argument("--h5-output", type=Path)
    tests = subparsers.add_parser("run-tests")
    tests.add_argument("--kind", choices=["focused", "all"], required=True)
    tests.add_argument("--log", type=Path, required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--phase-a", type=Path, required=True)
    analyze.add_argument("--h5-output", type=Path, required=True)
    analyze.add_argument("--h7-output", type=Path)
    analyze.add_argument("--full-test-log", type=Path)
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else base.PROJECT_ROOT / path


def main() -> None:
    args = parse_args()
    if args.command == "freeze-phase-a":
        freeze_phase_a(resolved(args.output), args.gpu)
        result: Any = {
            "status": "phase_a_frozen_identity_amended",
            "output": str(resolved(args.output)),
        }
    elif args.command == "run-cell":
        result = run_cell(
            resolved(args.phase_a),
            resolved(args.output),
            args.system,
            args.formula,
            args.gpu,
            resolved(args.h5_output) if args.h5_output else None,
        )
    elif args.command == "run-tests":
        install_base_overrides()
        result = base.execute_tests(args.kind, resolved(args.log))
    elif args.command == "analyze":
        result = analyze_outputs(
            resolved(args.phase_a),
            resolved(args.h5_output),
            resolved(args.h7_output) if args.h7_output else None,
            resolved(args.full_test_log) if args.full_test_log else None,
        )
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
