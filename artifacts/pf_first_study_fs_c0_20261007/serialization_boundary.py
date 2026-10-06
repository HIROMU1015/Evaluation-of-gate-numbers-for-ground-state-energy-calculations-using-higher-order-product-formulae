"""Durable private scalar checkpoint first, strict public validation second."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path

FORBIDDEN_KEYS = {"matrix", "matrices", "vector", "vectors", "unitary", "states",
                  "exact_state", "ground_state", "signed_direct", "direct_truth",
                  "exact_overlap", "true_gap", "pickle", "runtime_secret"}

def json_native(value):
    if value is None or type(value) in (bool, str, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("nonfinite scalar")
        return value
    if isinstance(value, Path):
        return str(value)
    # Only numpy scalar values, never ndarray values, can cross this boundary.
    if type(value).__module__.startswith("numpy") and not hasattr(value, "shape"):
        return json_native(value.item())
    if type(value).__module__.startswith("numpy") and getattr(value, "shape", None) == () and type(value).__name__ != "ndarray":
        return json_native(value.item())
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise TypeError("non-string dictionary key")
        if set(value) & FORBIDDEN_KEYS:
            raise ValueError("private/truth key in prediction checkpoint")
        return {k: json_native(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(v) for v in value]
    raise TypeError("unsupported object or array")

def canonical(value):
    return (json.dumps(json_native(value), sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False)+"\n").encode()

def exclusive_write(path, data):
    path = Path(path)
    with path.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    path.chmod(0o400)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def save_private_checkpoint(payload, private_path):
    """Use after each pass with its scalar rows and completed action ledger."""
    private_path = Path(private_path)
    if private_path.exists():
        raise FileExistsError('create-only private checkpoint exists')
    data = canonical(payload)
    digest = hashlib.sha256(data).hexdigest()
    exclusive_write(private_path, data)
    exclusive_write(private_path.with_suffix(private_path.suffix+'.sha256'), (digest+'\n').encode())
    return data, digest

def checkpoint_then_publish(payload, private_path, public_path, validator):
    """On a schema failure the recovery bytes remain; no science is rerun."""
    private_path, public_path = Path(private_path), Path(public_path)
    if private_path.exists() or public_path.exists():
        raise FileExistsError("create-only checkpoint/public path exists")
    data, digest = save_private_checkpoint(payload, private_path)
    native = json.loads(data)
    validator(native)
    exclusive_write(public_path, data)
    reread = public_path.read_bytes()
    if reread != data or canonical(json.loads(reread)) != data:
        raise RuntimeError("public payload exact roundtrip failed")
    return dict(sha256=digest, private_bytes=len(data), public_bytes=len(reread),
                canonical_roundtrip=True, recovery_saved_before_schema=True,
                formal_prediction_freeze=False)

def recover(path):
    path = Path(path)
    data = path.read_bytes()
    expected = path.with_suffix(path.suffix+".sha256").read_text().strip()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("recovery SHA mismatch")
    obj = json.loads(data)
    if canonical(obj) != data:
        raise ValueError("recovery noncanonical")
    return obj
