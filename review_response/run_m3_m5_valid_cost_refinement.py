"""Prepare compact systems and GPU-schedule predictable-cost refinements."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


GPU_IDS = (0, 1, 2, 3, 5, 6, 7)
SYSTEMS = (2, 4, 5, 6, 7, 8, 9)
FORMULAS = ("m5", "m3")
OLD_WORKTREE = Path("/tmp/trotter-m3-predictability-h7")


def _run_preparations(output: Path, python: str, env: dict[str, str]) -> None:
    processes: list[tuple[int, subprocess.Popen[bytes], object]] = []
    for h_chain in (2, 4, 5, 6, 7):
        log = (output / f"H{h_chain}_preparation.log").open("xb")
        if h_chain == 2:
            command = [
                python,
                "-u",
                "review_response/refine_m3_m5_valid_cost.py",
                "prepare-h2",
                "--processes",
                "1",
                "--output",
                str(output / "H2.pkl"),
                "--metadata",
                str(output / "H2_system.json"),
            ]
        else:
            command = [
                python,
                "-u",
                "review_response/run_gpu_m3_predictability_h7.py",
                "prepare",
                "--h-chain",
                str(h_chain),
                "--processes",
                "1",
                "--output",
                str(output / f"H{h_chain}.pkl"),
                "--metadata",
                str(output / f"H{h_chain}_system.json"),
            ]
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        processes.append((h_chain, process, log))
        print(f"H{h_chain}: preparation started pid={process.pid}", flush=True)
    failed = []
    for h_chain, process, log in processes:
        code = process.wait()
        log.close()
        print(f"H{h_chain}: preparation exit={code}", flush=True)
        if code:
            failed.append(h_chain)
    if failed:
        raise RuntimeError(f"preparation failures: {failed}")


def _system_path(output: Path, h_chain: int) -> Path:
    if h_chain <= 7:
        return output / f"H{h_chain}.pkl"
    return OLD_WORKTREE / "artifacts/m3_h8_h9_20260908_a5f9512" / f"H{h_chain}.pkl"


def _baseline(h_chain: int, formula: str) -> Path | None:
    if h_chain <= 7:
        return None
    if formula == "m5":
        return Path(
            "artifacts/m5_h8_h9_same_protocol_20260908_5d72b7d_retry1"
        ) / f"H{h_chain}_m5.json"
    return Path("artifacts/m3_h8_h9_20260908_a5f9512") / (
        f"H{h_chain}_m3_local_c1_r2_s007.json"
    )


def launch(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    env = dict(os.environ)
    env.update(
        PYTHONPATH=args.pythonpath,
        MPLBACKEND="Agg",
        OMP_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
    )
    _run_preparations(output, args.python, env)

    tasks = [(h_chain, formula) for h_chain in reversed(SYSTEMS) for formula in FORMULAS]
    active: dict[int, tuple[int, str, subprocess.Popen[bytes], object]] = {}
    results: list[Path] = []
    failed: list[str] = []
    while tasks or active:
        while tasks and len(active) < len(GPU_IDS):
            gpu = next(gpu_id for gpu_id in GPU_IDS if gpu_id not in active)
            h_chain, formula = tasks.pop(0)
            target = output / f"H{h_chain}_{formula}.json"
            log = (output / f"H{h_chain}_{formula}.log").open("xb")
            command = [
                args.python,
                "-u",
                "review_response/refine_m3_m5_valid_cost.py",
                "worker",
                "--h",
                str(h_chain),
                "--formula",
                formula,
                "--gpu",
                str(gpu),
                "--system",
                str(_system_path(output, h_chain)),
                "--output",
                str(target),
            ]
            baseline = _baseline(h_chain, formula)
            if baseline is not None:
                command += ["--baseline", str(baseline)]
            worker_env = dict(env, CUDA_VISIBLE_DEVICES=str(gpu))
            process = subprocess.Popen(
                command, env=worker_env, stdout=log, stderr=subprocess.STDOUT
            )
            active[gpu] = (h_chain, formula, process, log)
            results.append(target)
            print(
                f"H{h_chain} {formula}: GPU {gpu}, pid={process.pid}", flush=True
            )
        time.sleep(2)
        for gpu, (h_chain, formula, process, log) in list(active.items()):
            code = process.poll()
            if code is None:
                continue
            log.close()
            del active[gpu]
            print(f"H{h_chain} {formula}: exit={code}", flush=True)
            if code:
                failed.append(f"H{h_chain}_{formula}")

    aggregate = [
        args.python,
        "review_response/refine_m3_m5_valid_cost.py",
        "aggregate",
        "--inputs",
        *map(str, results),
        "--output",
        str(output / "summary.json"),
        "--report",
        str(output / "report.md"),
        "--complete",
        str(output / "COMPLETE"),
    ]
    code = subprocess.call(aggregate, env=env)
    print(f"aggregate exit={code}; worker failures={failed}", flush=True)
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--python", default="/home/AbeHiromu/venvs/trotter-common/bin/python"
    )
    parser.add_argument(
        "--pythonpath",
        default=(
            "/home/AbeHiromu/projects/"
            "Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
            "using-higher-order-product-formulae/venv/lib/python3.12/site-packages:"
            "src:review_response"
        ),
    )
    return parser


if __name__ == "__main__":
    sys.exit(launch(build_parser().parse_args()))
