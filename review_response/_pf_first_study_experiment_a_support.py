"""Run the preregistered first-study Experiment A validation.

Only the fixed two-level controls and the committed H2 arrays are evaluated.
The output is an implementation audit, not a molecular generality result.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time
from typing import Any, Sequence

import mpmath as mp
import numpy as np
from scipy.linalg import expm, schur

from review_response.bch_matrix_series import (
    effective_hamiltonian_series,
    ordered_exponential_product_series,
)
from trotterlib.pf_decomposition import iter_s2_sequence_steps


DEFAULT_PROTOCOL = Path("PF_first_study_protocol_20260925.json")
DEFAULT_OUTPUT = Path("artifacts/pf_first_study_experiment_a_20260925_d3fadde")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(value: np.ndarray) -> str:
    """Implement the frozen sha256-numpy-v1 array identity."""

    array = np.ascontiguousarray(np.asarray(value))
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode("utf-8"))
    digest.update(b"\n")
    digest.update(
        json.dumps(list(array.shape), separators=(",", ":")).encode("utf-8")
    )
    digest.update(b"\n")
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def git_output(project_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def load_protocol(path: Path) -> tuple[dict[str, Any], str]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    digest = sha256_file(path)
    words = path.with_suffix(path.suffix + ".sha256").read_text(
        encoding="utf-8"
    ).split()
    if len(words) < 2 or words[0] != digest or Path(words[-1]).name != path.name:
        raise ValueError("frozen protocol SHA-256 mismatch")
    if protocol.get("protocol_id") != "pf_first_study_mechanism_decision_v1_0":
        raise ValueError("unexpected protocol_id")
    if protocol.get("status") != "preregistered_before_formal_execution":
        raise ValueError("protocol is not preregistered")
    return protocol, digest


def formula_registry(protocol: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for formula_id in protocol["scope"]["included_formula_ids"]:
        entry = protocol["formulae"][formula_id]
        rows.append(
            {
                "formula_id": formula_id,
                "formal_order": int(entry["formal_order"]),
                "sequence": tuple(float(value) for value in entry["s2_sequence"]),
                "provenance": entry["provenance"],
            }
        )
    return tuple(rows)


def pf_unitary(
    groups: Sequence[np.ndarray], sequence: Sequence[float], time_value: float
) -> np.ndarray:
    dimension = int(np.asarray(groups[0]).shape[0])
    spectra = [np.linalg.eigh(np.asarray(group, dtype=np.complex128)) for group in groups]
    unitary = np.eye(dimension, dtype=np.complex128)
    for group_index, weight in iter_s2_sequence_steps(len(groups), sequence):
        values, vectors = spectra[group_index]
        factor = (
            vectors
            * np.exp(1j * float(time_value) * float(weight) * values)[None, :]
        ) @ vectors.conj().T
        unitary = factor @ unitary
    return unitary


def _mp_matrix(value: np.ndarray) -> mp.matrix:
    array = np.asarray(value, dtype=np.complex128)
    result = mp.matrix(array.shape[0], array.shape[1])
    for row in range(array.shape[0]):
        for column in range(array.shape[1]):
            item = complex(array[row, column])
            result[row, column] = mp.mpc(str(item.real), str(item.imag))
    return result


def pf_unitary_high_precision(
    groups: Sequence[np.ndarray],
    sequence: Sequence[float],
    time_value: float,
    decimal_digits: int,
) -> np.ndarray:
    with mp.workdps(decimal_digits):
        converted = [_mp_matrix(group) for group in groups]
        unitary = mp.eye(converted[0].rows)
        time_mp = mp.mpf(str(float(time_value)))
        for group_index, weight in iter_s2_sequence_steps(len(groups), sequence):
            generator = (
                mp.j
                * time_mp
                * mp.mpf(str(float(weight)))
                * converted[group_index]
            )
            unitary = mp.expm(generator) * unitary
        return np.asarray(
            [
                [complex(unitary[row, column]) for column in range(unitary.cols)]
                for row in range(unitary.rows)
            ],
            dtype=np.complex128,
        )


def propagator_minus(hamiltonian: np.ndarray, time_value: float) -> np.ndarray:
    energies, vectors = np.linalg.eigh(np.asarray(hamiltonian, dtype=np.complex128))
    return (
        vectors * np.exp(-1j * float(time_value) * energies)[None, :]
    ) @ vectors.conj().T


def anchored_eigenbasis(
    hamiltonian: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    energies, vectors = np.linalg.eigh(np.asarray(hamiltonian, dtype=np.complex128))
    result = np.array(vectors, copy=True)
    for column in range(result.shape[1]):
        pivot = int(np.argmax(np.abs(result[:, column])))
        result[:, column] *= np.exp(-1j * np.angle(result[pivot, column]))
        if result[pivot, column].real < 0.0:
            result[:, column] *= -1.0
    return energies, result


def two_level_systems() -> dict[str, dict[str, Any]]:
    pauli_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    pauli_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    hamiltonian = pauli_x + pauli_z
    energies, vectors = anchored_eigenbasis(hamiltonian)
    ground, excited = vectors[:, 0], vectors[:, 1]
    states = {
        "exact_ground": ground,
        "real_q001": np.sqrt(0.99) * ground + np.sqrt(0.01) * excited,
        "complex_q001": np.sqrt(0.99) * ground + 1j * np.sqrt(0.01) * excited,
    }
    common = {
        "hamiltonian": hamiltonian,
        "energy": float(energies[0]),
        "ground_state": ground,
        "states": states,
    }
    return {
        "two_level_commuting": {
            **common,
            "groups": [0.4 * hamiltonian, 0.6 * hamiltonian],
            "commuting": True,
        },
        "two_level_noncommuting": {
            **common,
            "groups": [pauli_x, pauli_z],
            "commuting": False,
        },
    }


def load_h2_system(
    project_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = protocol["source_identity"]["f01_bundle"]
    path = project_root / bundle["path"]
    if sha256_file(path) != bundle["sha256"]:
        raise ValueError("H2 source bundle SHA-256 mismatch")
    identity = protocol["source_identity"]["h2_arrays_for_experiment_a"]
    arrays = np.load(path)
    keys = [
        identity["hamiltonian_key"],
        "H2_ground_state",
        "H2_ground_energy",
        *identity["ordered_group_keys"],
    ]
    observed = {key: sha256_array(arrays[key]) for key in keys}
    expected = {
        identity["hamiltonian_key"]: identity["hamiltonian_sha256"],
        "H2_ground_state": identity["ground_state_sha256"],
        "H2_ground_energy": identity["ground_energy_array_sha256"],
        **dict(
            zip(
                identity["ordered_group_keys"],
                identity["ordered_group_sha256"],
                strict=True,
            )
        ),
    }
    if observed != expected:
        raise ValueError("H2 source array identity mismatch")
    hamiltonian = np.asarray(
        arrays[identity["hamiltonian_key"]], dtype=np.complex128
    )
    state = np.asarray(arrays["H2_ground_state"], dtype=np.complex128)
    groups = [
        np.asarray(arrays[key], dtype=np.complex128)
        for key in identity["ordered_group_keys"]
    ]
    energy = float(np.asarray(arrays["H2_ground_energy"]).reshape(()))
    return (
        {
            "hamiltonian": hamiltonian,
            "groups": groups,
            "energy": energy,
            "ground_state": state,
            "states": {"exact_ground": state},
            "commuting": False,
        },
        {
            "path": str(bundle["path"]),
            "file_sha256": bundle["sha256"],
            "array_sha256": observed,
        },
    )
