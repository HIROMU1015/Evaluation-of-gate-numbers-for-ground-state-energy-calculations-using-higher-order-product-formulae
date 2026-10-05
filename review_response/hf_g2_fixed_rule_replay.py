"""HF-only S1A Rules 1--3 replay. Standard library, no acquisition or truth I/O.

The lexical projector reads a combined artifact's bytes, but only decodes the
explicitly allowed value paths. Skipped M1 subtrees are not JSON-decoded during
cheap projection. This is a procedural development replay, not prospective
blinding or an OS sandbox.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

from review_response import hf_domain_intervention_pilot as inherited


GAMMAS = (1.01, 1.02, 1.05, 1.10)
CONDITIONS = ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")


class ReplayError(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise ReplayError(message)


def lexical_project(text, paths):
    """Project explicit tuple paths, '*' matching array indices only.

    No raw_decode of an excluded scalar/subtree. The input artifact is separately
    hash-checked; this projector is not a general-purpose JSON validator.
    """
    decoder = json.JSONDecoder()
    allowed = [tuple(path) for path in paths]
    pos = 0
    decoded = []

    def ws():
        nonlocal pos
        while pos < len(text) and text[pos].isspace():
            pos += 1

    def matches(pattern, path):
        return all(a == b or (a == "*" and isinstance(b, int))
                   for a, b in zip(pattern, path))

    def string_end(start):
        index = start + 1
        while index < len(text):
            if text[index] == "\\":
                index += 2
            elif text[index] == '"':
                return index + 1
            else:
                index += 1
        raise ReplayError("unterminated JSON string")

    def skip():
        nonlocal pos
        ws()
        require(pos < len(text), "missing JSON value")
        if text[pos] == '"':
            pos = string_end(pos)
        elif text[pos] in "[{":
            stack = [text[pos]]
            pos += 1
            while stack:
                require(pos < len(text), "unterminated JSON subtree")
                char = text[pos]
                if char == '"':
                    pos = string_end(pos)
                    continue
                if char in "[{":
                    stack.append(char)
                elif char in "]}":
                    require((stack[-1], char) in (("[", "]"), ("{", "}")), "JSON delimiter mismatch")
                    stack.pop()
                pos += 1
        else:
            while pos < len(text) and text[pos] not in ",]} \r\n\t":
                pos += 1

    def value(path):
        nonlocal pos
        ws()
        candidates = [p for p in allowed if len(p) >= len(path) and matches(p, path)]
        if not candidates:
            skip()
            return None
        if any(len(p) == len(path) for p in candidates):
            result, pos = decoder.raw_decode(text, pos)
            decoded.append(list(path))
            return result
        require(pos < len(text), "missing projected JSON container")
        char = text[pos]
        if char == "{":
            pos += 1
            result = {}
            ws()
            while text[pos] != "}":
                key, pos = decoder.raw_decode(text, pos)
                require(isinstance(key, str) and key not in result, "invalid/duplicate projected key")
                ws()
                require(text[pos] == ":", "missing JSON colon")
                pos += 1
                child_path = path + (key,)
                keep = any(len(p) >= len(child_path) and matches(p, child_path) for p in candidates)
                child = value(child_path)
                if keep:
                    result[key] = child
                ws()
                if text[pos] == "}":
                    break
                require(text[pos] == ",", "missing JSON comma")
                pos += 1
                ws()
            pos += 1
            return result
        require(char == "[", "projected container must be object or array")
        pos += 1
        result = []
        ws()
        index = 0
        while text[pos] != "]":
            result.append(value(path + (index,)))
            index += 1
            ws()
            if text[pos] == "]":
                break
            require(text[pos] == ",", "missing JSON array comma")
            pos += 1
            ws()
        pos += 1
        return result

    result = value(())
    ws()
    require(pos == len(text), "trailing JSON data")
    return result, decoded


def cheap_paths():
    paths = [(key,) for key in ("schema", "status", "budget_model", "eta", "p0_protocol_sha256", "authorization_sha256")]
    paths += [("conditions", "*", "condition"), ("conditions", "*", "selection", "B1")]
    paths += [("conditions", "*", "candidates", "*", key) for key in
              ("candidate_id", "time_hartree_inverse", "factor_of_T0", "allowance_hartree", "B1")]
    return paths


def spectral_paths(indices):
    fields = ("arm", "candidate_id", "condition", "time_hartree_inverse", "time_hex", "factor_of_T0",
              "signed_shift_estimate_hartree", "width_hartree", "e_use_hartree", "allowance_hartree",
              "eligible", "abstained", "failure_reasons", "continuous_budget", "continuous_budget_hex")
    paths = []
    for index in indices:
        paths += [("conditions", index, "condition"), ("conditions", index, "selection", "M1")]
        paths += [("conditions", index, "candidates", "*", "M1", key) for key in fields]
    return paths


def fallback(baseline, control_id):
    return inherited.select_condition([], arm="B0", gamma=None,
        fallback_candidate_id=control_id, fallback_time=baseline["T0_hartree_inverse"],
        fallback_budget=baseline["B0_continuous"])


def verify_action(action, points, baseline):
    by_id = {p["candidate_id"]: p for p in points}
    require(action["selected_candidate"] in by_id, "unknown selected candidate")
    point = by_id[action["selected_candidate"]]
    require(float(action["selected_time_hartree_inverse"]).hex() == float(point["time_hartree_inverse"]).hex(), "selected time mismatch")
    budget = action["frozen_continuous_budget"]
    require(math.isfinite(budget) and budget > 0 and float(budget).hex() == action["frozen_continuous_budget_hex"], "budget/hex mismatch")
    if action["fallback"]:
        require(point["factor_of_T0"] == 1 and budget == baseline["B0_continuous"], "fallback contract mismatch")


def cheap_policy(condition, baseline, constants, plan):
    """Use saved four-gamma eligibility/selections; fail rather than fill missing.

    Recomputing inherited scalar arithmetic is only a consistency check. The
    frontier must already exist; it is never created as a replacement input.
    """
    points = sorted(condition["candidates"], key=lambda p: p["time_hartree_inverse"])
    require(len(points) == 3 and len({p["candidate_id"] for p in points}) == 3, "three unique native candidates required")
    require([p["factor_of_T0"] for p in points] == [1.0, 1.3, 1.6], "native HF factors changed")
    frontier = condition["selection"]["B1"]
    require(len(frontier) == 4 and tuple(x["gamma"] for x in frontier) == GAMMAS, "saved four-gamma frontier required")
    rows = []
    for point in points:
        fixed = plan[point["candidate_id"]]
        require(fixed["condition"] == condition["condition"], "candidate condition mismatch")
        require(float(point["time_hartree_inverse"]).hex() == fixed["time_hex"], "candidate binary64 identity mismatch")
        arms = point["B1"]
        require(len(arms) == 4 and tuple(a["gamma"] for a in arms) == GAMMAS, "missing candidate gamma arm")
        require(len({a["signed_shift_estimate_hartree"] for a in arms}) == 1, "proxy differs across gamma arms")
        require(all(a["time_hex"] == fixed["time_hex"] and a["candidate_id"] == point["candidate_id"] for a in arms), "B1 coordinate identity mismatch")
        allowance = inherited.target_allowance(epsilon_hartree=constants["epsilon_E_hartree"], beta=constants["beta"],
            rotations=constants["K_current_m3_per_step"], time_value=point["time_hartree_inverse"],
            baseline_budget=baseline["B0_continuous"], eta=0.10)
        require(point["allowance_hartree"] == allowance, "saved allowance differs from inherited rule")
        check = inherited.b1_arm_rows(candidate_id=point["candidate_id"], time_value=point["time_hartree_inverse"],
            factor_of_t0=point["factor_of_T0"], signed_proxy_hartree=arms[0]["signed_shift_estimate_hartree"],
            allowance_hartree=allowance, gammas=GAMMAS, beta=constants["beta"],
            rotations=constants["K_current_m3_per_step"], epsilon_hartree=constants["epsilon_E_hartree"])
        for saved, expected in zip(arms, check):
            require(all(saved.get(k) == v for k, v in expected.items()), "saved B1 arithmetic/eligibility mismatch")
        rows.extend(arms)
    for arm in frontier:
        expected = inherited.select_condition(rows, arm="B1_local_CISD_proxy", gamma=arm["gamma"],
            fallback_candidate_id=points[0]["candidate_id"], fallback_time=baseline["T0_hartree_inverse"],
            fallback_budget=baseline["B0_continuous"])
        require(arm == expected, "saved selection differs from inherited selector")
        verify_action(arm, points, baseline)
    diagnostics = {
        "gamma_candidate_disagreement": len({a["selected_candidate"] for a in frontier if not a["fallback"]}) > 1,
        "gamma_eligibility_disagreement": len({tuple(sorted(a["eligible_candidates"])) for a in frontier}) > 1 or len({a["fallback"] for a in frontier}) > 1,
    }
    floor = max(1e-12, 1e-6 * constants["epsilon_E_hartree"])
    signs = {0 if not math.isfinite(p["B1"][0]["signed_shift_estimate_hartree"]) or abs(p["B1"][0]["signed_shift_estimate_hartree"]) <= floor
             else (1 if p["B1"][0]["signed_shift_estimate_hartree"] > 0 else -1) for p in points[1:]}
    diagnostics["proxy_sign_instability"] = 0 in signs or {-1, 1} <= signs
    unstable = any(diagnostics.values())
    b2 = deepcopy(frontier[3 if unstable else 0])
    return {"condition": condition["condition"], "points": points, "B0": fallback(baseline, points[0]["candidate_id"]),
            "B1": deepcopy(frontier), "B2": b2, "B2_gamma": b2["gamma"], "instability": diagnostics,
            "sign_noise_floor_hartree": floor, "cheap_instability": unstable, "q": int(unstable or b2["fallback"])}


def validate_spectral(spectral, cheap, baseline):
    require(spectral["condition"] == cheap["condition"], "M1 condition mismatch")
    points = cheap["points"]
    require(len(spectral["candidates"]) == 3, "three saved M1 rows required")
    rows = [c["M1"] for c in spectral["candidates"]]
    require({r["candidate_id"] for r in rows} == {p["candidate_id"] for p in points}, "exact M1 candidate match required")
    for row in rows:
        point = next(p for p in points if p["candidate_id"] == row["candidate_id"])
        require(float(row["time_hartree_inverse"]).hex() == float(point["time_hartree_inverse"]).hex() == row["time_hex"], "M1 binary64 time mismatch")
        require(row["factor_of_T0"] == point["factor_of_T0"] and row["allowance_hartree"] == point["allowance_hartree"], "M1 native contract mismatch")
    selection = spectral["selection"]["M1"]
    expected = inherited.select_condition(rows, arm="M1_fixed_D2A_spectral", gamma=None,
        fallback_candidate_id=points[0]["candidate_id"], fallback_time=baseline["T0_hartree_inverse"], fallback_budget=baseline["B0_continuous"])
    require(selection == expected, "saved M1 selector mismatch")
    verify_action(selection, points, baseline)
    return {"rows": rows, "selection": deepcopy(selection)}


def h1_final(cheap, spectral, constants):
    b2 = deepcopy(cheap["B2"])
    if cheap["q"] == 0:
        require(spectral is None, "q=0 H1 must not receive M1")
        return {"action": b2, "source": "B2_q_zero", "consistency": "not_opened", "spectral": None}
    require(spectral is not None, "q=1 requires saved M1")
    row = next(r for r in spectral["rows"] if r["candidate_id"] == b2["selected_candidate"])
    e_use = row["e_use_hartree"]
    usable = not row["abstained"] and e_use is not None and math.isfinite(e_use) and 0 <= e_use < constants["epsilon_E_hartree"]
    if not usable:
        return {"action": b2 if not b2["fallback"] else deepcopy(cheap["B0"]), "source": "M1_unusable", "consistency": "indeterminate", "spectral": spectral}
    consistency = e_use + constants["beta"] * constants["K_current_m3_per_step"] / (b2["selected_time_hartree_inverse"] * b2["frozen_continuous_budget"]) <= constants["epsilon_E_hartree"]
    m1 = spectral["selection"]
    if not consistency:
        action = m1 if not m1["fallback"] else cheap["B0"]
        source = "B2_invalidated"
    else:
        options = [a for a in (b2, m1) if not a["fallback"]]
        action = min(options, key=lambda a: a["frozen_continuous_budget"]) if options else cheap["B0"]
        if not b2["fallback"] and not m1["fallback"] and math.isclose(b2["frozen_continuous_budget"], m1["frozen_continuous_budget"], rel_tol=1e-12, abs_tol=0):
            action = b2
        source = "B2_validated"
    return {"action": deepcopy(action), "source": source, "consistency": consistency, "spectral": spectral}


def score_action(action, direct, baseline, constants, control_pass):
    t = action["selected_time_hartree_inverse"]
    b = action["frozen_continuous_budget"]
    lhs = abs(direct) + constants["beta"] * constants["K_current_m3_per_step"] / (t * b)
    safe = lhs <= constants["epsilon_E_hartree"]
    target = not action["fallback"] and t > baseline["T0_hartree_inverse"] and b <= .90 * baseline["B0_continuous"]
    return {"candidate_id": action["selected_candidate"], "time_hartree_inverse": t, "frozen_continuous_budget": b,
            "fallback": action["fallback"], "budget_safety_lhs_hartree": lhs, "budget_safe": safe,
            "procedurally_valid": bool(control_pass), "safe_and_valid": bool(safe and control_pass),
            "target_met": bool(target), "safe_target_met": bool(safe and control_pass and target), "B_over_B0": b / baseline["B0_continuous"]}


def strictly_better(x, y):
    return x < y * (1 - 1e-12)


def outcome(b2, h1, fixed, q, control):
    if not control:
        return "incomplete_reference_control_failure"
    if not q:
        return "A_cheap_sufficient" if b2["safe_and_valid"] else "D_gate_false_negative"
    improvement = h1["safe_and_valid"] and (not b2["safe_and_valid"] or strictly_better(h1["frozen_continuous_budget"], b2["frozen_continuous_budget"]) or (b2["fallback"] and not h1["fallback"]))
    explained = any(a["safe_and_valid"] and a["frozen_continuous_budget"] <= h1["frozen_continuous_budget"] * (1 + 1e-12) for a in fixed)
    if improvement and not explained:
        return "C_conditional_spectral_decision_value_cost_unresolved"
    return "B_fixed_cheap_explains_change" if improvement else "B_no_H1_incremental_value"
