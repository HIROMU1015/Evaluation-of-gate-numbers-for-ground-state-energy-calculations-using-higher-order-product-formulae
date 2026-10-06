"""FS-C1 scalar scorer. No production runner, state loader, or fitting path.

score_frozen verifies committed prediction/protocol/code/schema/manifest bytes
before the supplied truth callback. This package has science_authorized=False.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ARMS = ("M00", "M10", "M01", "M11")

class ContractError(ValueError):
    pass

def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"nonfinite/non-numeric {name}")
    return float(value)

def budget(c, t, K, epsilon, beta, gamma):
    c, t, epsilon, beta, gamma = [finite(x, n) for x, n in
        zip((c, t, epsilon, beta, gamma), ("c", "t", "epsilon", "beta", "gamma"))]
    if isinstance(K, bool) or not isinstance(K, int) or K <= 0:
        raise ContractError("K must be a positive integer")
    if t <= 0 or epsilon <= 0 or beta <= 0 or gamma < 1 or c < 0:
        raise ContractError("budget domain violation")
    if c >= epsilon:
        return None
    result = gamma * beta * K / (t * (epsilon - c))
    if not math.isfinite(result) or result <= 0:
        raise ContractError("budget overflow/underflow")
    return result

def decision(signed_estimate, signed_direct, spec, constants):
    estimate, direct = finite(signed_estimate, "estimate"), finite(signed_direct, "direct")
    c, e = abs(estimate), abs(direct)
    if finite(spec['B0'], 'B0') <= 0:
        raise ContractError('nonpositive B0 reference')
    eps, beta, gamma = (constants[k] for k in ("epsilon_E", "beta", "gamma"))
    B = budget(c, spec["t0"], spec["K"], eps, beta, gamma)
    M = (1 - 1/gamma) * (eps - c)
    if B is None:
        return dict(estimate=estimate, c=c, e=e, u=e-c, margin=M,
                    B=None, slack=None, slack_identity=None, raw_safe=False,
                    B_over_B0=None, saving=None, feasible=False)
    slack = eps - e - beta * spec["K"] / (spec["t0"] * B)
    return dict(estimate=estimate, c=c, e=e, u=e-c, margin=M, B=B,
                slack=slack, slack_identity=M-(e-c), raw_safe=slack >= 0,
                B_over_B0=B/spec["B0"], saving=1-B/spec["B0"], feasible=True)

def domain_screen(K, T, epsilon, beta, B0, eta):
    budget(0., T, K, epsilon, beta, 1.)
    B0, eta = finite(B0, "B0"), finite(eta, "eta")
    if B0 <= 0 or not 0 <= eta < 1:
        raise ContractError("screen domain violation")
    lower = beta*K/(T*epsilon)
    headroom = 1-lower/B0
    return dict(cost_lower_bound=lower, maximum_saving=headroom,
                exclude_target=headroom < eta)

def signed_interaction(estimates):
    values = {a: finite(estimates[a], a) for a in ARMS}
    return dict(state_in_fit=values["M10"]-values["M00"],
                local_in_CISD=values["M01"]-values["M00"],
                state_in_local=values["M11"]-values["M01"],
                interaction=(values["M11"]-values["M10"])-(values["M01"]-values["M00"]))

def select_truth(rows, specs):
    """Exact binary64 joins; duplicates, extra targets and identity errors stop."""
    result = {}
    for row in rows:
        condition = row.get("condition")
        if condition not in specs or condition in result:
            raise ContractError("unexpected/duplicate truth condition")
        spec = specs[condition]
        if (row.get("formula") != spec["formula"] or
            finite(row.get("time"), "truth time").hex() != float(spec["t0"]).hex() or
            row.get("time_sign") != 1 or row.get("identity") != spec["identity"] or
            row.get("branch_id") != spec["truth_branch_id"] or row.get("quality") != "resolved"):
            raise ContractError("truth sign/time/identity/branch/quality mismatch")
        result[condition] = finite(row.get("signed_direct"), "direct truth")
    if set(result) != set(specs):
        raise ContractError("missing truth")
    return result

def score_payload(payload, truth_rows, protocol):
    specs = {s["condition"]: s for s in protocol["systems"]}
    conditions = payload["conditions"]
    if len(conditions) != len(specs) or {x["condition"] for x in conditions} != set(specs):
        raise ContractError("prediction condition coverage mismatch")
    truth = select_truth(truth_rows, specs)
    results = []
    constants = protocol["constants"]
    eta = constants["eta_saving"]
    for row in conditions:
        spec = specs[row["condition"]]
        if row["identity"] != spec["identity"] or row["t0"] != spec["t0"] or row["training_times"] != spec["training_times"]:
            raise ContractError("prediction identity/time mismatch")
        if set(row["arms"]) != set(ARMS):
            raise ContractError("four arms required")
        metrics = {}
        for arm in ARMS:
            a = row["arms"][arm]
            if a["estimate"] is None:
                if a["valid"]:
                    raise ContractError("valid arm has null estimate")
                metrics[arm] = {"valid": False, "validated_safe": False, "B": None,
                                "numerically_indeterminate": True}
                continue
            d = decision(a["estimate"], truth[row["condition"]], spec, constants)
            uncertainty = a["classification_uncertainty_hartree"]
            if uncertainty is not None and finite(uncertainty, "uncertainty") < 0:
                raise ContractError("negative uncertainty")
            indeterminate = uncertainty is None or (d["slack"] is not None and abs(d["slack"]) <= uncertainty)
            quality_ok = a['quality_status'] in ('resolved', 'marginal') or (payload['payload_kind']=='synthetic_fixture' and a['quality_status']=='synthetic')
            valid = a["valid"] and quality_ok and row["baseline_reproduced"] and d["feasible"]
            d.update(valid=bool(valid), numerically_indeterminate=indeterminate,
                     validated_safe=bool(valid and d["raw_safe"] and not indeterminate))
            metrics[arm] = d
        m01, m11 = metrics["M01"], metrics["M11"]
        def gain(m, reference):
            return bool(m["validated_safe"] and m["B"] <= (1-eta)*reference)
        flags = dict(primary_gain=gain(m11, spec["B0"]),
                     local_gain=gain(m01, spec["B0"]),
                     state_increment=bool(m01["validated_safe"] and m11["validated_safe"] and m11["B"] <= (1-eta)*m01["B"]),
                     safety_repair=bool(m01.get("valid") and not m01.get("numerically_indeterminate") and not m01.get("raw_safe", False) and m11["validated_safe"]))
        estimates = {a: row["arms"][a]["estimate"] for a in ARMS}
        results.append(dict(condition=row["condition"], arms=metrics, flags=flags,
                            signed_differences=None if any(v is None for v in estimates.values()) else signed_interaction(estimates)))
    return dict(conditions=results, primary_gain_count=sum(r["flags"]["primary_gain"] for r in results),
                denominator=len(specs), independent_holdout=False,
                operational_general_safety_certificate=False)

def _git_bytes(root, commit, path):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ContractError("full40 freeze commit required")
    p = Path(path)
    if p.is_absolute() or ".." in p.parts:
        raise ContractError("invalid freeze path")
    return subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root,
                           check=True, capture_output=True).stdout

def _local_bytes(root, path):
    p = root/path
    if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
        raise ContractError('freeze path escapes checkout')
    return p.read_bytes()

def score_frozen(root, commit, manifest_path, manifest_sha256, truth_loader, *, synthetic_only=False):
    """The callback cannot run until the complete committed freeze is checked."""
    root = Path(root)
    manifest_bytes = _git_bytes(root, commit, manifest_path)
    if _local_bytes(root,manifest_path) != manifest_bytes or hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
        raise ContractError("freeze manifest mismatch")
    manifest = json.loads(manifest_bytes)
    if set(manifest) != {"files", "roles"} or set(manifest["roles"]) != {"prediction", "protocol", "schema", "scorer", "sources"}:
        raise ContractError("incomplete freeze roles")
    blobs = {}
    for path, digest in manifest["files"].items():
        data = _git_bytes(root, commit, path)
        if _local_bytes(root,path) != data or hashlib.sha256(data).hexdigest() != digest:
            raise ContractError("frozen blob mismatch")
        blobs[path] = data
    roles = manifest["roles"]
    if not set(roles.values()).issubset(blobs):
        raise ContractError("freeze omits required role")
    if Path(__file__).read_bytes() != blobs[roles["scorer"]]:
        raise ContractError("executing scorer differs from frozen code")
    protocol = json.loads(blobs[roles["protocol"]])
    payload = json.loads(blobs[roles["prediction"]])
    sources = json.loads(blobs[roles["sources"]])
    if sources.get("system_identities") != {x["condition"]: x["identity"] for x in protocol["systems"]}:
        raise ContractError("frozen source identities mismatch")
    if payload["protocol_sha256"] != hashlib.sha256(blobs[roles["protocol"]]).hexdigest():
        raise ContractError("prediction/protocol hash mismatch")
    if synthetic_only:
        if payload["payload_kind"] != "synthetic_fixture":
            raise ContractError("synthetic entry cannot score production")
    else:
        if payload['payload_kind'] != 'fs_c1_predictions':
            raise ContractError('production entry cannot score synthetic fixture')
        if not protocol["science_authorized"] or not protocol["execution_ready"]:
            raise ContractError("FS-C1 execution not authorized/ready")
    from jsonschema import Draft202012Validator
    Draft202012Validator(json.loads(blobs[roles["schema"]])).validate(payload)
    specs = {s["condition"]: s for s in protocol["systems"]}
    if len(payload["conditions"]) != len(specs) or {r["condition"] for r in payload["conditions"]} != set(specs):
        raise ContractError("freeze coverage mismatch")
    for r in payload["conditions"]:
        s = specs[r["condition"]]
        if r["identity"] != s["identity"] or r["t0"] != s["t0"] or r["training_times"] != s["training_times"]:
            raise ContractError("freeze metadata mismatch before truth")
    return score_payload(payload, truth_loader(), protocol)
