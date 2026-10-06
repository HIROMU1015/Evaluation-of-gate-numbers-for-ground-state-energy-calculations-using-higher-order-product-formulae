"""Read-only local H-chain inventory; this module cannot acquire science data.

Only named input metadata, frozen source blobs and allowlisted input runtime
files are opened. NPZ inspection reads ZIP member names, not array contents.
No chemistry runner, old scorer, prospective result or ground archive is read.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import zipfile

BASE = "971dc7a9b1b138fbbbb95fc684aa52af657e81b1"
DOC = "docs/second_study_v2/hchain_supplement_local_20261006"
PREP = "artifacts/hchain_input_reference_preparation_20261004_06922cb"
ODD = "artifacts/hchain_h3_h5_h7_extension_20261004"
H8 = "artifacts/hchain_h8_memory_safe_extension_20261004"
INPUT_ORIGINS = {
    "H6": "ed8b77ffb2d446283a079a6a6c9083c0a22886de",
    "H7": "49ec2de066ee8c0f63e99c77b94a52cf2aa73ccd",
    "H8": "5bab841352ec68dc0e2f5e56063b57304cab2721",
}
SOURCES = [
    (f"{PREP}/input_identity.json", INPUT_ORIGINS["H6"], "input"),
    (f"{PREP}/runtime_manifest.json", INPUT_ORIGINS["H6"], "input"),
    (f"{PREP}/candidate_plan.csv", "a03bd71415cac6deb3b653c131905f32b744cec5", "coordinate"),
    (f"{ODD}/inputs/payload.json", INPUT_ORIGINS["H7"], "input"),
    (f"{ODD}/candidate_plan.csv", "ff949e6aa942475f20f0623bcffb617e1e750f24", "published_coordinate"),
    (f"{H8}/inputs/payload.json", INPUT_ORIGINS["H8"], "input"),
    (f"{H8}/candidate_plan.csv", "cc3c49dac8630f6a18a3a6d6edc21b0c18bd6fb6", "published_coordinate"),
    ("artifacts/hchain_truth_free_prediction_20261004/final/prediction.json",
     "858265dacd304c844029ce2576b4559221f0c7c1", "saved_prediction_blob_hash_only"),
    (f"{ODD}/prediction/payload.json", "747868eb3527261fff74c515221b0ea4235bbcbf", "saved_prediction_blob_hash_only"),
    (f"{H8}/prediction/payload.json", "b0a67843d3f3f9e17bdd4ed2a078b63ca11a703e", "saved_prediction_blob_hash_only"),
]
METHOD_PATHS = (
    "review_response/pf_spectral_recoverability_d2.py",
    "review_response/hchain_input_reference_preparation.py",
    "review_response/run_hchain_input_reference_preparation.py",
    "review_response/hchain_prediction_phase.py",
    "review_response/run_hchain_prediction_phase.py",
    "review_response/hchain_odd_extension.py",
    "review_response/run_hchain_odd_extension.py",
    "review_response/hchain_h8_memory_safe.py",
    "review_response/run_hchain_h8_memory_safe.py",
    "review_response/hchain_truth_scoring.py",
    "docs/second_study_v2/hchain_input_reference_preparation_20261004/authorization.json",
    "docs/second_study_v2/hchain_input_reference_preparation_20261004/reference_grid.json",
    "docs/second_study_v2/hchain_input_reference_preparation_20261004/truth_scoring_method.json",
    "docs/second_study_v2/hchain_independent_validation_20261004/system_and_pf_contract.json",
    "docs/second_study_v2/hchain_independent_validation_20261004/rank_aware_M1_amendment.json",
    "docs/second_study_v2/hchain_odd_extension_20261004/protocol.json",
    "docs/second_study_v2/hchain_h8_memory_safe_20261004/protocol.json",
)
DEFERRED_TRUTH = [
    {"system": "H6", "path": "artifacts/hchain_truth_scoring_20261004/truth/truth.json",
     "origin_result_commit": "5a9226a94fad0b578df1a53edd1a29e3571ad8c3"},
    {"system": "H7", "path": f"{ODD}/truth/payload.json",
     "origin_result_commit": "db504bf8b9902a31aa14fa97d84cab9da82bdee4"},
    {"system": "H8", "path": f"{H8}/truth/payload.json",
     "origin_result_commit": "944291272c561a59e42e2b03c25d82353ea2506d"},
]


class PreflightError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def safe_file(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise PreflightError("unsafe relative file name")
    root = Path(root)
    path = root / relative
    if root.is_symlink() or any((root / Path(*relative.parts[:i])).is_symlink()
                                for i in range(1, len(relative.parts) + 1)):
        raise PreflightError("linked source/runtime forbidden")
    if not path.is_file():
        raise PreflightError(f"missing file: {path}")
    return path


def source_entry(root, relative, origin, role):
    path = safe_file(root, relative)
    origin_blob = git(root, "show", f"{origin}:{relative}")
    snapshot_blob = git(root, "show", f"{BASE}:{relative}")
    if origin_blob != snapshot_blob or sha_file(path) != digest(snapshot_blob):
        raise PreflightError(f"frozen source identity mismatch: {relative}")
    return {"path": relative, "role": role, "origin_result_commit": origin,
            "verified_snapshot_commit": BASE, "sha256": digest(snapshot_blob),
            "bytes": len(snapshot_blob), "worktree_byte_identity": True}


def exact_coordinates(text, system):
    result = []
    for row in csv.DictReader(io.StringIO(text)):
        if row["system"] != system:
            continue
        for key in ("ratio", "t_ref", "time"):
            value = float(row[key])
            if not math.isfinite(value) or value <= 0 or value.hex() != row[key + "_hex"]:
                raise PreflightError(f"invalid binary64 coordinate: {system} {key}")
        if (float(row["ratio"]) * float(row["t_ref"])).hex() != row["time_hex"]:
            raise PreflightError("coordinate multiplication mismatch")
        if not 0.02 <= float(row["time"]) <= 1.8:
            raise PreflightError("saved candidate outside native domain")
        result.append(row)
    if [float(row["ratio"]) for row in result] != [0.5, 0.65, 0.8]:
        raise PreflightError("must have exactly three ordered frozen ratios")
    if len({row["candidate_id"] for row in result}) != 3:
        raise PreflightError("duplicate candidate ID")
    if len({(row["t_ref_hex"], row["K"], row["primary_m"]) for row in result}) != 1:
        raise PreflightError("inconsistent system coordinate contract")
    return result


def npz_member_inventory(path, expected):
    """Inspect ZIP directory only; never deserialize an array or pickle."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    if len(names) != len(set(names)) or set(names) != {key + ".npy" for key in expected}:
        raise PreflightError("NPZ sanitized member set mismatch")
    return sorted(names)


def verify_runtime(root, entries, member_sets):
    result = []
    if len({row["path"] for row in entries}) != len(entries):
        raise PreflightError("duplicate runtime path")
    for entry in entries:
        path = safe_file(root, entry["path"])
        if path.stat().st_size != entry["bytes"] or sha_file(path) != entry["sha256"]:
            raise PreflightError(f"runtime byte identity mismatch: {entry['path']}")
        row = dict(entry)
        if path.name in member_sets:
            row["npz_members_not_deserialized"] = npz_member_inventory(path, member_sets[path.name])
        row["byte_identity_pass"] = True
        result.append(row)
    return result


def allocation_gate(allocation, rank_rule_status):
    """Fail closed: host availability and old allocations never grant authority."""
    required = ("CPU_maximum", "workers_maximum", "total_RAM_GiB", "wall_hours", "disk_GiB")
    if allocation.get("status") != "approved_independent_local_allocation":
        return False
    if allocation.get("independent_from_prospective") is not True:
        return False
    if allocation.get("BLAS_threads") != 1 or allocation.get("approved_output") is None:
        return False
    if rank_rule_status != "approved_frozen":
        return False
    for key in required:
        value = allocation.get(key)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
            return False
    return allocation["workers_maximum"] <= allocation["CPU_maximum"]


def inventory(root, workspace):
    root, workspace = Path(root), Path(workspace)
    registry = [source_entry(root, *entry) for entry in SOURCES]
    for relative in METHOD_PATHS:
        origin = git(root, "log", "-1", "--format=%H", BASE, "--", relative).decode().strip()
        registry.append(source_entry(root, relative, origin, "inherited_method_or_protocol_blob"))
    def read(relative):
        return json.loads(safe_file(root, relative).read_text())
    h6_identity = read(f"{PREP}/input_identity.json")["H6"]
    h6_runtime = read(f"{PREP}/runtime_manifest.json")["files"]
    h7_payload = read(f"{ODD}/inputs/payload.json")
    h8_payload = read(f"{H8}/inputs/payload.json")
    payloads = {"H6": h6_identity, "H7": h7_payload["input_identity"]["H7"],
                "H8": h8_payload["input_identity"]["H8"]}
    runtimes = {
        "H6": ("pf-second-study-v2-hchain-input-reference-preparation-20261004", PREP,
               [entry for entry in h6_runtime if entry["path"].startswith(("H6_", "h6_"))]),
        "H7": ("pf-second-study-v2-hchain-h3-h5-h7-extension-20261004", ODD,
               [entry for entry in h7_payload["runtime_files"] if entry["path"].startswith("H7_")]),
        "H8": ("pf-second-study-v2-hchain-h8-memory-safe-extension-20261004", H8,
               h8_payload["runtime_files"]),
    }
    coordinates = {}
    for name, relative in (("H6", PREP), ("H7", ODD), ("H8", H8)):
        coordinates[name] = exact_coordinates(safe_file(root, f"{relative}/candidate_plan.csv").read_text(), name)
    old = read("docs/second_study_v2/hchain_odd_extension_20261004/protocol.json")
    h7_spec = next(row for row in old["systems"] if row["system"] == "H7")
    if (h7_spec["charge"], h7_spec["multiplicity"], h7_spec["n_alpha"], h7_spec["n_beta"],
            payloads["H7"]["sector_dimension"]) != (1, 3, 4, 2, 735):
        raise PreflightError("saved H7 contract changed")
    runtime_audit = {}
    identities = {}
    csr_members = {"indices", "indptr", "format", "shape", "data"}
    for name, (worktree, relative, entries) in runtimes.items():
        spec = payloads[name]
        if int(coordinates[name][0]["K"]) != spec["K"]:
            raise PreflightError("candidate/input K mismatch")
        if name in ("H6", "H7"):
            filename = "H6_predictor_input.npz" if name == "H6" else "H7_input.npz"
            members = {filename: {"hamiltonian", "cisd", "sector_indices"} |
                       {f"group_{i:03d}" for i in range(len(spec["group_sha256_numpy_v1"]))}}
        else:
            members = {"H8_state.npz": {"cisd", "sector_indices"}, "H8_H.npz": csr_members}
            members.update({f"H8_group_{i:03d}.npz": csr_members
                            for i in range(len(spec["group_sha256_numpy_v1"]))})
        runtime_root = workspace / ".worktrees" / worktree / relative / ".runtime"
        runtime_audit[name] = {"root": str(runtime_root), "files": verify_runtime(runtime_root, entries, members),
                               "origin_result_commit": INPUT_ORIGINS[name], "verified_snapshot_commit": BASE}
        identities[name] = {key: spec.get(key) for key in (
            "sector_dimension", "CISD_subspace_dimension", "K", "H_sha256_numpy_v1",
            "CISD_sha256_numpy_v1", "sector_indices_sha256_numpy_v1", "group_sha256_numpy_v1")}
        if name == "H8":
            identities[name]["CISD_subspace_dimension"] = spec["CISD_generation"]["subspace_dimension"]
    return {
        "schema": "hchain_local_supplement_static_inventory_v1",
        "status": "local_inputs_byte_verified_science_gated",
        "source_registry": registry,
        "input_identity_metadata": identities,
        "coordinate_rows": coordinates,
        "runtime_byte_audit": runtime_audit,
        "saved_H7_physical_contract": h7_spec,
        "deferred_truth_registry": [dict(row, verification_status="deferred_until_prediction_freeze")
                                    for row in DEFERRED_TRUTH],
        "checks": {"source_blobs": len(registry), "candidate_coordinates": 9,
                   "runtime_files": sum(len(row["files"]) for row in runtime_audit.values()),
                   "runtime_bytes": sum(entry["bytes"] for row in runtime_audit.values() for entry in row["files"])},
        "access": {"runtime_array_deserializations": 0, "ground_archive_opens": 0,
                   "truth_scalar_opens": 0, "prospective_runtime_or_partial_truth_opens": 0,
                   "old_prediction_reads": "whole-file hash only; no scalar interpretation"},
        "new_science_actions": {"chemistry_generations": 0, "reference_PF": 0,
                                "candidate_cheap_PF": 0, "M1_PF": 0, "H_actions": 0,
                                "ground_solves": 0, "direct_truth": 0, "gap_solves": 0},
        "remaining_gates": ["independent local allocation approval", "rank-specific continuation review",
                            "science runner implementation and tests", "array/physical/energy-origin anchor closure"],
        "science_execution_ready": False,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise PreflightError("refuse to overwrite an audit artifact")
    result = inventory(args.project_root, args.workspace_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], **result["checks"], "science_actions": 0}))


if __name__ == "__main__":
    main()
