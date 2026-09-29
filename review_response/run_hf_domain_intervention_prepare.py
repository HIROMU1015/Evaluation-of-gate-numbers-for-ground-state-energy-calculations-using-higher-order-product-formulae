"""Verify and sanitize the inherited HF cache for the v2 domain pilot.

This preflight adapter performs no PF/H action and no eigensolve.  It verifies
fixed cache identities, copies only allowlisted Hamiltonian/CISD/PF-component
fields into a new runtime boundary, and records all excluded top-level fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import pickle
from typing import Any

import numpy as np

import run_h01_approximate_state_calibration as h01
from hf_domain_intervention_pilot import HFPilotError, load_json, sha256_file, write_json


CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")
SCHEMA = "hf_domain_intervention_sanitized_system_v1"
ALLOWED = {
    "schema", "condition", "source_pickle_sha256", "protocol_sha256",
    "hamiltonian_sha256", "hamiltonian", "component_spectra", "term_counts",
    "cisd_state",
}


def sanitize(cache_root: Path, output_root: Path, authorization_path: Path) -> dict[str, Any]:
    authorization = load_json(authorization_path)
    expected = authorization["resolved_execution_blockers"]["cache_preflight"]
    if output_root.exists():
        raise HFPilotError("sanitized output must be new")
    runtime = output_root / ".runtime" / "sanitized"
    runtime.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        pickle_path = cache_root / "cache" / f"{condition}.pkl"
        metadata_path = cache_root / "cache" / f"{condition}.metadata.json"
        if not pickle_path.is_file() or not metadata_path.is_file():
            raise HFPilotError(f"missing inherited cache: {condition}")
        actual_pickle = sha256_file(pickle_path)
        if actual_pickle != expected["pickle_sha256"][condition]:
            raise HFPilotError(f"source pickle identity mismatch: {condition}")
        system = h01._load_system(pickle_path)
        if system.get("hamiltonian_sha256") != expected["hamiltonian_sha256"][condition]:
            raise HFPilotError(f"Hamiltonian identity mismatch: {condition}")
        state = np.asarray(system.get("states", {}).get("cisd"), dtype=np.complex128).reshape(-1)
        if state.size == 0 or abs(float(np.linalg.norm(state)) - 1.0) > 1e-10:
            raise HFPilotError(f"invalid CISD state: {condition}")
        sanitized = {
            "schema": SCHEMA,
            "condition": condition,
            "source_pickle_sha256": actual_pickle,
            "protocol_sha256": system["protocol_sha256"],
            "hamiltonian_sha256": system["hamiltonian_sha256"],
            "hamiltonian": system["hamiltonian"],
            "component_spectra": system["component_spectra"],
            "term_counts": system["term_counts"],
            "cisd_state": state.copy(),
        }
        if set(sanitized) != ALLOWED:
            raise HFPilotError("sanitized allowlist drift")
        destination = runtime / f"{condition}.pkl"
        with destination.open("wb") as stream:
            pickle.dump(sanitized, stream, protocol=pickle.HIGHEST_PROTOCOL)
        excluded = sorted(set(system) - {"protocol_sha256", "hamiltonian_sha256", "hamiltonian", "component_spectra", "term_counts", "states"})
        entries.append({
            "condition": condition,
            "source_pickle_path": str(pickle_path.resolve()),
            "source_pickle_sha256": actual_pickle,
            "source_metadata_path": str(metadata_path.resolve()),
            "source_metadata_sha256": sha256_file(metadata_path),
            "sanitized_relative_path": str(destination.relative_to(output_root)),
            "sanitized_sha256": sha256_file(destination),
            "allowed_fields": sorted(sanitized),
            "source_top_level_fields_excluded": excluded,
            "states_subfields_excluded": sorted(set(system.get("states", {})) - {"cisd"}),
            "truth_path_exposed_to_predictor": False,
            "dimension": int(state.size),
        })
        del system
    manifest = {
        "schema": "hf_domain_intervention_sanitized_manifest_v1",
        "authorization_sha256": sha256_file(authorization_path),
        "source_cache_root": str(cache_root.resolve()),
        "condition_count": len(entries),
        "entries": entries,
        "PF_action_count": 0,
        "H_matvec_count": 0,
        "eigendecomposition_count": 0,
        "direct_truth_count": 0,
        "GPU_operation_count": 0,
    }
    write_json(output_root / "sanitized_input_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    manifest = sanitize(
        args.cache_root.resolve(), args.output_root.resolve(),
        args.authorization.resolve(),
    )
    print(json.dumps({
        "status": "hf_cache_sanitized_truth_not_exposed",
        "condition_count": manifest["condition_count"],
        "output_root": str(args.output_root.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
