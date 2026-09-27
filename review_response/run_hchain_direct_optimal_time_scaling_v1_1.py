#!/usr/bin/env python3
"""Ordering-aware v1.1 wrapper for the frozen direct scaling protocol."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import hchain_direct_sector_v1_1 as sector_v1_1
import run_hchain_direct_optimal_time_scaling as parent
import sweep_direct_scaling_h6_h7 as direct


EXPECTED_PARENT_PROTOCOL_SHA256 = (
    "12d10562cf481b836242786462184d8a6ffb342153404c9bf84ff4d5ca836ab9"
)
EXPECTED_AMENDMENT_SHA256 = (
    "5ca0ea30f9ad08bc7e4a54fcd8bab8f50195752dcaf3717c219281a458b0122e"
)


def _v1_1_job_matches(
    payload: dict[str, Any],
    *,
    protocol_sha256: str,
    amendment_sha256: str,
    grid: Sequence[float],
    h_chain: int,
    formula_key: str,
) -> bool:
    return bool(
        parent._job_matches(
            payload,
            protocol_sha256=protocol_sha256,
            grid=grid,
            h_chain=h_chain,
            formula_key=formula_key,
        )
        and payload.get("registered_amendment", {}).get("sha256")
        == amendment_sha256
        and payload.get("registered_amendment", {}).get("sector_rule")
        == "ordering_aware_v1_1"
    )


def _run_jobs_v1_1(
    protocol: dict[str, Any],
    protocol_sha256: str,
    amendment_sha256: str,
    output: Path,
    *,
    resume: bool,
) -> list[Path]:
    raw_root = output / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    runtime_root = output / ".runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    grid = parent._grid_from_protocol(protocol)
    paths: list[Path] = []
    for system in protocol["systems"]["included"]:
        h_chain = int(system["h_chain"])
        for formula in protocol["product_formulas"]:
            formula_key = str(formula["key"])
            destination = raw_root / parent._job_name(h_chain, formula_key)
            paths.append(destination)
            if destination.exists():
                existing = parent._load_json(destination)
                if resume and _v1_1_job_matches(
                    existing,
                    protocol_sha256=protocol_sha256,
                    amendment_sha256=amendment_sha256,
                    grid=grid,
                    h_chain=h_chain,
                    formula_key=formula_key,
                ):
                    print(
                        f"reuse complete protocol/amendment-identical job: {destination}",
                        flush=True,
                    )
                    continue
                raise RuntimeError(
                    f"refusing to overwrite non-reusable v1.1 job: {destination}"
                )
            temporary = runtime_root / parent._job_name(h_chain, formula_key)
            if temporary.exists():
                raise RuntimeError(
                    "incomplete runtime file exists; preserve it and choose a new "
                    f"output: {temporary}"
                )
            print(
                f"start registered v1.1 direct job H{h_chain} {formula_key} "
                f"({len(grid)} points)",
                flush=True,
            )
            started = parent._utc_now()
            payload = direct.run(
                [h_chain],
                [formula_key],
                grid,
                direct.DEFAULT_M5_TIMES,
                direct.DEFAULT_Y8_TIMES,
                5e-12,
                float(protocol["target"]["epsilon_E_hartree"]),
                temporary,
                str(protocol["execution"]["unitary_build_method"]),
            )
            payload["registered_protocol"] = {
                "sha256": protocol_sha256,
                "h_chain": h_chain,
                "formula_key": formula_key,
                "started_at_utc": started,
                "completed_at_utc": parent._utc_now(),
                "prior_direct_results_reused": False,
            }
            payload["registered_amendment"] = {
                "sha256": amendment_sha256,
                "sector_rule": "ordering_aware_v1_1",
                "failed_attempt_output_reused": False,
            }
            parent._write_json(destination, payload)
            temporary.unlink()
            print(f"complete registered v1.1 direct job: {destination}", flush=True)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path(
            "review_response/hchain_direct_optimal_time_scaling_protocol.json"
        ),
    )
    parser.add_argument(
        "--amendment",
        type=Path,
        default=Path(
            "review_response/hchain_direct_optimal_time_scaling_amendment_v1_1.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927"
        ),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    protocol_path = (
        args.protocol if args.protocol.is_absolute() else project_root / args.protocol
    ).resolve()
    amendment_path = (
        args.amendment
        if args.amendment.is_absolute()
        else project_root / args.amendment
    ).resolve()
    output = (
        args.output if args.output.is_absolute() else project_root / args.output
    ).resolve()
    protocol_sha256 = parent._sha256(protocol_path)
    amendment_sha256 = parent._sha256(amendment_path)
    if protocol_sha256 != EXPECTED_PARENT_PROTOCOL_SHA256:
        raise RuntimeError("parent protocol SHA-256 mismatch")
    if amendment_sha256 != EXPECTED_AMENDMENT_SHA256:
        raise RuntimeError("v1.1 amendment SHA-256 mismatch")
    protocol = parent._load_json(protocol_path)
    parent._grid_from_protocol(protocol)

    # The direct module resolves this global at execution time.  No direct PF
    # action occurs before this ordering-aware implementation is installed.
    direct._prepare_sparse_sector_system = (
        sector_v1_1.prepare_sparse_sector_system_v1_1
    )

    if output.exists() and not (args.resume or args.analyze_only):
        raise RuntimeError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_copy = output / "protocol.json"
    amendment_copy = output / "amendment_v1_1.json"
    for source, destination, expected in (
        (protocol_path, protocol_copy, protocol_sha256),
        (amendment_path, amendment_copy, amendment_sha256),
    ):
        if destination.exists():
            if parent._sha256(destination) != expected:
                raise RuntimeError(f"fixed identity mismatch: {destination}")
        else:
            shutil.copyfile(source, destination)

    started = time.perf_counter()
    if not args.analyze_only:
        _run_jobs_v1_1(
            protocol,
            protocol_sha256,
            amendment_sha256,
            output,
            resume=args.resume,
        )
    for system in protocol["systems"]["included"]:
        for formula in protocol["product_formulas"]:
            path = output / "raw" / parent._job_name(
                int(system["h_chain"]), str(formula["key"])
            )
            if not _v1_1_job_matches(
                parent._load_json(path),
                protocol_sha256=protocol_sha256,
                amendment_sha256=amendment_sha256,
                grid=parent._grid_from_protocol(protocol),
                h_chain=int(system["h_chain"]),
                formula_key=str(formula["key"]),
            ):
                raise RuntimeError(f"raw v1.1 identity mismatch: {path}")

    analysis = parent.analyze(protocol, protocol_sha256, output, project_root)
    analysis["amendment_v1_1_sha256"] = amendment_sha256
    parent._write_json(output / "analysis.json", analysis)
    audit_path = output / "audit.json"
    audit = parent._load_json(audit_path)
    audit.update(
        {
            "amendment_v1_1_sha256": amendment_sha256,
            "sector_rule": "ordering_aware_v1_1",
            "failed_attempt_output_reused": False,
            "failed_attempt_completed_direct_points": 0,
        }
    )
    parent._write_json(audit_path, audit)
    public_files = [
        protocol_copy,
        amendment_copy,
        output / "analysis.json",
        output / "report.md",
        audit_path,
        *sorted((output / "raw").glob("*.json")),
    ]
    parent._manifest(
        output,
        public_files,
        {
            "schema_version": "hchain_direct_optimal_time_scaling_manifest_v1_1",
            "status": analysis["status"],
            "protocol_sha256": protocol_sha256,
            "amendment_v1_1_sha256": amendment_sha256,
            "created_at_utc": parent._utc_now(),
        },
    )
    print(
        json.dumps(
            {
                "status": analysis["status"],
                "decision": analysis["decision"],
                "protocol_sha256": protocol_sha256,
                "amendment_v1_1_sha256": amendment_sha256,
                "elapsed_seconds": time.perf_counter() - started,
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
