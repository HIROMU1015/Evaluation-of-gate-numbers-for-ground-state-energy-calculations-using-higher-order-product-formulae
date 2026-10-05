"""Private sequential supervisor. No numerical imports or scientific recipe changes.

The immutable P2 CLI owns every scientific action and checkpoint. This supervisor
only launches authorized phases once and watches its own process group, deadlines,
and the combined private-control/output disk footprint. It never retries a worker.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import time

CONTROL = Path(__file__).resolve().parent
ROOT = CONTROL.parents[1]
PYTHON = "/home/AbeHiromu/venvs/trotter-common/bin/python"


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def footprint(roots):
    total = 0
    for root in roots:
        for directory, _, files in os.walk(root):
            for name in files:
                try:
                    s = (Path(directory) / name).lstat()
                    total += max(s.st_size, s.st_blocks * 512)
                except FileNotFoundError:
                    pass
    return total


def refresh_reviewed_history():
    """Re-audit changed refs; reuse manual review only for identical known blobs/paths."""
    certificate_path = CONTROL / "server_history_certificate.json"
    certificate = read(certificate_path)
    inventory = read(CONTROL / certificate["inventory_path"])
    refs = subprocess.check_output(["git", "-C", str(ROOT), "for-each-ref",
                                    "--format=%(refname) %(objectname)"]).decode().splitlines()
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    if head != certificate["audited_tip_commit"]:
        raise RuntimeError("pre-input source HEAD changed; fresh manual review required")
    if refs == inventory["refs"]:
        return
    source = ROOT / "review_response/audit_prospective_ch2_history.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != "b5d18a865c95a1e16883f3bd91a95cb794b7afee51d3754cbfa335994d9c09f5":
        raise RuntimeError("history audit implementation differs from P2")
    spec = importlib.util.spec_from_file_location("private_history_audit", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    latest = module.inventory(ROOT)
    if latest["unreadable_text_blobs"]:
        raise RuntimeError("new audit has unreadable text; manual review required")
    known = {r["sha256"]: r for r in certificate["content_review_ledger"]}
    for match in latest["matches"]:
        old = known.get(match["sha256"])
        if old is None or not set(match["paths"]).issubset(old["paths"]) or match["blob_oid"] != old["blob_oid"]:
            write(CONTROL / "unreviewed_history_inventory.json", latest)
            raise RuntimeError("new/unreviewed history match; stop for manual review without further science")
    frozen_name = "server_history_inventory_" + hashlib.sha256(
        json.dumps(latest, sort_keys=True).encode()).hexdigest() + ".json"
    write(CONTROL / frozen_name, latest)
    certificate = {**certificate,
                   "created_UTC": datetime.now(timezone.utc).isoformat(),
                   "inventory_path": frozen_name,
                   "inventory_sha256": hashlib.sha256((CONTROL / frozen_name).read_bytes()).hexdigest(),
                   "reviewed_blob_sha256": [r["sha256"] for r in latest["matches"]],
                   "content_review_ledger": [known[r["sha256"]] for r in latest["matches"]],
                   "manual_review_reuse": "only identical previously reviewed blob SHA256/OID and known paths; unknown content stops"}
    write(certificate_path, certificate)
    digest = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
    write(CONTROL / ("server_history_certificate_" + digest + ".json"), certificate)
    print(json.dumps({"history_refs_refreshed": True,
                      "manually_reviewed_matches": len(latest["matches"]),
                      "new_unreviewed_matches": 0, "certificate_sha256": digest}), flush=True)


def run_worker(phase, condition, input_commit, allocation):
    output = Path(allocation["approved_output_root"])
    expiry = datetime.fromisoformat(allocation["expires_UTC"])
    if datetime.now(timezone.utc) >= expiry:
        raise RuntimeError("allocation expired before dispatch")
    disk_cap = int(allocation["writable_disk_quota_bytes"])
    disk_stop = disk_cap - 128 * 2**20
    roots = (CONTROL, output)
    if footprint(roots) >= disk_stop:
        raise RuntimeError("cumulative disk quota reserve exhausted before dispatch")
    if phase in ("input", "seal-inputs"):
        refresh_reviewed_history()
    command = [PYTHON, "-u", str(ROOT / "review_response/run_prospective_input_reference.py"),
               phase, "--project-root", str(ROOT), "--output-root", str(output),
               "--allocation", str(CONTROL / "allocation.json"),
               "--history-certificate", str(CONTROL / "server_history_certificate.json")]
    if condition:
        command += ["--condition-id", condition]
    if input_commit:
        command += ["--input-commit", input_commit]
    name = phase + ("_" + condition if condition else "")
    env = os.environ.copy()
    env.update(PYTHONPATH="src:review_response:.", PYTHONNOUSERSITE="1",
               PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", TMPDIR=str(CONTROL / "tmp"))
    started = time.monotonic()
    start_utc = datetime.now(timezone.utc).isoformat()
    peak_rss, peak_disk, terminated_for, usage = 0, 0, None, None
    proc = None
    with (CONTROL / (name + ".stdout.log")).open("x") as stdout, \
         (CONTROL / (name + ".stderr.log")).open("x") as stderr:
        try:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout,
                                    stderr=stderr, start_new_session=True)
            # Only this newly spawned worker's CPU affinity is restricted.
            os.sched_setaffinity(proc.pid, {min(os.sched_getaffinity(0))})
            last_heartbeat, last_disk = started, 0.
            while True:
                pid, status, current_usage = os.wait4(proc.pid, os.WNOHANG)
                if pid:
                    proc.returncode = os.waitstatus_to_exitcode(status)
                    usage = current_usage
                    peak_rss = max(peak_rss, int(usage.ru_maxrss * 1024))
                    break
                now = time.monotonic()
                try:
                    fields = Path(f"/proc/{proc.pid}/status").read_text().splitlines()
                    rss = next(int(line.split()[1]) * 1024 for line in fields if line.startswith("VmRSS:"))
                    peak_rss = max(peak_rss, rss)
                except (FileNotFoundError, StopIteration):
                    rss = 0
                if now - last_disk >= .1:
                    disk_bytes = footprint(roots)
                    peak_disk = max(peak_disk, disk_bytes)
                    last_disk = now
                    free = os.statvfs(CONTROL)
                    free_bytes = free.f_bavail * free.f_frsize
                    if disk_bytes >= disk_stop:
                        terminated_for = "cumulative_disk_quota_reserve_reached"
                    elif free_bytes < 256 * 2**20:
                        terminated_for = "filesystem_free_space_reserve_reached"
                if rss > allocation["worker_rss_limit_bytes"]:
                    terminated_for = "own_worker_RSS_limit_exceeded"
                if now - started >= allocation["worker_wall_seconds"]:
                    terminated_for = "own_worker_command_wall_limit_exceeded"
                if datetime.now(timezone.utc) >= expiry:
                    terminated_for = "global_allocation_expired"
                if terminated_for:
                    if os.getpgid(proc.pid) != proc.pid:
                        raise RuntimeError("unexpected own process group; refusing group signal")
                    os.killpg(proc.pid, signal.SIGKILL)
                    _, status, usage = os.wait4(proc.pid, 0)
                    proc.returncode = os.waitstatus_to_exitcode(status)
                    peak_rss = max(peak_rss, int(usage.ru_maxrss * 1024))
                    break
                if now - last_heartbeat >= 30:
                    print(json.dumps({"phase": phase, "condition_id": condition,
                                      "wall_seconds": now - started,
                                      "own_worker_peak_RSS_bytes": peak_rss,
                                      "cumulative_peak_disk_bytes": peak_disk}), flush=True)
                    last_heartbeat = now
                time.sleep(.1)
        finally:
            if proc is not None and proc.returncode is None:
                if os.getpgid(proc.pid) == proc.pid:
                    os.killpg(proc.pid, signal.SIGKILL)
                _, status, usage = os.wait4(proc.pid, 0)
                proc.returncode = os.waitstatus_to_exitcode(status)
            result = {"phase": phase, "condition_id": condition, "start_UTC": start_utc,
                      "end_UTC": datetime.now(timezone.utc).isoformat(),
                      "command_wall_seconds": time.monotonic() - started,
                      "own_worker_peak_RSS_bytes": peak_rss,
                      "cumulative_peak_disk_bytes": max(peak_disk, footprint(roots)),
                      "exit_code": proc.returncode if proc else None,
                      "terminated_for": terminated_for, "scientific_retries": 0,
                      "monitor_interval_seconds": .1, "disk_monitor_interval_seconds": .1,
                      "limits": "periodic own-process watchdog; not native cgroup hard limits"}
            write(CONTROL / (name + ".command_resource.json"), result)
    print(json.dumps(result), flush=True)
    if result["exit_code"] != 0 or terminated_for:
        raise RuntimeError("worker stopped; no retry, marker deletion, or output reset permitted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("input", "seal-inputs", "references", "seal-references"))
    parser.add_argument("--input-commit")
    args = parser.parse_args()
    allocation = read(CONTROL / "allocation.json")
    if allocation["workers"] != 1:
        raise RuntimeError("this supervisor reserves exactly one sequential worker")
    if args.phase in ("references", "seal-references") and not args.input_commit:
        raise RuntimeError("frozen input commit required")
    with (CONTROL / (args.phase + "_supervisor_started.json")).open("x") as stream:
        json.dump({"start_UTC": datetime.now(timezone.utc).isoformat(),
                   "allocation_sha256": hashlib.sha256((CONTROL / "allocation.json").read_bytes()).hexdigest(),
                   "workers": 1, "retries": 0}, stream, indent=2)
    (CONTROL / "tmp").mkdir(exist_ok=True)
    conditions = read(ROOT / "docs/second_study_v2/prospective_core_protocol_20261005/conditions.json")
    items = [c["condition_id"] for c in conditions] if args.phase in ("input", "references") else [None]
    for condition in items:
        run_worker(args.phase, condition, args.input_commit, allocation)


if __name__ == "__main__":
    main()
