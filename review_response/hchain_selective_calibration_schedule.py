"""No-fit B1/B2/H1 rules and conditional-first acquisition scheduler.

No truth, vector acquisition or filesystem reads. The preparation tests use
callbacks/stubs only; molecular candidate execution needs separate permission.
"""
from __future__ import annotations

from copy import deepcopy
import math
import time

from review_response.hchain_input_reference_preparation import PreparationError, canonical_hash


EPSILON = 0.00015936001019904
BETA = 1.2
GAMMAS = (1.01, 1.02, 1.05, 1.10)


def budget(t, error, k):
    if not math.isfinite(t) or t <= 0 or not math.isfinite(error) or error < 0 or error >= EPSILON:
        return None
    value = float(BETA * int(k) / (float(t) * (EPSILON - float(error))))
    return value if math.isfinite(value) and value > 0 else None


def select(rows, fallback):
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        return deepcopy(fallback)
    chosen = min(eligible, key=lambda row: (row["budget"], row["time"], row["candidate_id"]))
    return {"candidate_id": chosen["candidate_id"], "time": chosen["time"],
            "budget": chosen["budget"], "fallback": False}


def cheap_policy(points, k):
    if len(points) != 3 or len({p["candidate_id"] for p in points}) != 3:
        raise PreparationError("three unique fixed candidates required")
    points = sorted(points, key=lambda row: row["time"])
    t0 = float(points[0]["time"])
    base = budget(t0, abs(float(points[0]["delta_C_hartree"])), k)
    if base is None:
        raise PreparationError("invalid benchmark baseline; no replacement anchor")
    b0 = 1.01 * base
    fallback = {"candidate_id": points[0]["candidate_id"], "time": t0, "budget": b0, "fallback": True}
    frontier = []
    for gamma in GAMMAS:
        rows = []
        for point in points:
            t = float(point["time"])
            delta = float(point["delta_C_hartree"])
            cost = budget(t, abs(delta), k)
            b = None if cost is None else gamma * cost
            allowance = EPSILON - BETA * int(k) / (t * (0.90 * b0))
            eligible = t > t0 and allowance > 0 and b is not None and b <= 0.90 * b0
            rows.append({"candidate_id": point["candidate_id"], "time": t, "budget": b,
                         "allowance": allowance, "eligible": bool(eligible)})
        frontier.append({"gamma": gamma, "rows": rows, "selected": select(rows, fallback)})
    selected_ids = {arm["selected"]["candidate_id"] for arm in frontier if not arm["selected"]["fallback"]}
    eligible_sets = {tuple(row["candidate_id"] for row in arm["rows"] if row["eligible"]) for arm in frontier}
    fallback_set = {arm["selected"]["fallback"] for arm in frontier}
    floor = max(1e-12, 1e-6 * EPSILON)
    exterior = [float(row["delta_C_hartree"]) for row in points[1:]]
    signs = {0 if not math.isfinite(value) or abs(value) <= floor else (1 if value > 0 else -1)
             for value in exterior}
    diagnostics = {"gamma_candidate_disagreement": len(selected_ids) > 1,
                   "gamma_eligibility_disagreement": len(eligible_sets) > 1 or len(fallback_set) > 1,
                   "proxy_sign_instability": 0 in signs or {-1, 1} <= signs}
    unstable = any(diagnostics.values())
    gamma_index = 3 if unstable else 0
    b2 = deepcopy(frontier[gamma_index]["selected"])
    return {"B0": fallback, "B1_frontier": frontier, "B2": b2,
            "B2_gamma": GAMMAS[gamma_index], "instability": diagnostics,
            "q": int(unstable or b2["fallback"]), "points": deepcopy(points), "K": int(k)}


def spectral_policy(spectral, cheap):
    if {row["candidate_id"] for row in spectral} != {row["candidate_id"] for row in cheap["points"]}:
        raise PreparationError("exact candidate match required; no nearest/interpolation")
    rows = []
    for prediction in spectral:
        identifier = prediction["candidate_id"]
        point = next(row for row in cheap["points"] if row["candidate_id"] == identifier)
        if float(prediction["time"]).hex() != float(point["time"]).hex():
            raise PreparationError("M1 candidate time hex mismatch")
        e_use = prediction.get("e_use")
        usable = (not prediction.get("abstain", True) and e_use is not None
                  and math.isfinite(e_use) and 0 <= e_use < EPSILON)
        t = float(point["time"])
        allowance = EPSILON - BETA * cheap["K"] / (t * (0.90 * cheap["B0"]["budget"]))
        rows.append({"candidate_id": identifier, "time": t,
                     "budget": budget(t, e_use, cheap["K"]) if usable else None,
                     "eligible": bool(t > cheap["B0"]["time"] and allowance > 0
                                      and usable and e_use <= allowance),
                     "usable": usable, "e_use": e_use})
    return select(rows, cheap["B0"]), rows


def h1_final(cheap, spectral=None):
    b2 = deepcopy(cheap["B2"])
    if cheap["q"] == 0:
        if spectral is not None:
            raise PreparationError("q=0 H1 must not see M1 output")
        return {"action": b2, "source": "B2_q_zero", "consistency": "not_opened"}
    if spectral is None:
        raise PreparationError("q=1 requires conditional acquisition or explicit abstention rows")
    m1, rows = spectral_policy(spectral, cheap)
    at_cheap = next(row for row in rows if row["candidate_id"] == b2["candidate_id"])
    if not at_cheap["usable"]:
        return {"action": b2 if not b2["fallback"] else deepcopy(cheap["B0"]),
                "source": "M1_unusable", "consistency": "indeterminate"}
    consistent = at_cheap["e_use"] + BETA * cheap["K"] / (b2["time"] * b2["budget"]) <= EPSILON
    if consistent:
        options = [action for action in (b2, m1) if not action["fallback"]]
        chosen = min(options, key=lambda action: action["budget"]) if options else cheap["B0"]
        if (not b2["fallback"] and not m1["fallback"]
                and math.isclose(b2["budget"], m1["budget"], rel_tol=1e-12, abs_tol=0)):
            chosen = b2
        return {"action": deepcopy(chosen), "source": "B2_validated", "consistency": True}
    return {"action": m1 if not m1["fallback"] else deepcopy(cheap["B0"]),
            "source": "B2_invalidated", "consistency": False}


def run_shared_schedule(systems, cheap_acquire, spectral_acquire, freeze, *, clock=time.perf_counter):
    """Freeze q, acquire q=1 only, freeze H1, THEN fill q=0 comparator.

Callbacks must enforce their own input/source/coordinate/action gates. This
orchestrator shares every q=1 M1 chain with the always-M1 comparator. Completion
wall is a warm shared-path measurement, not an independent cold always-M1 run.
"""
    started = clock()
    costs = {}
    cheap = {}
    for system in systems:
        before = clock()
        points, k = cheap_acquire(system)
        acquisition_seconds = clock() - before
        before = clock()
        cheap[system] = cheap_policy(points, k)
        costs[system] = {"cheap_acquisition_seconds": acquisition_seconds,
                         "cheap_decision_seconds": clock() - before,
                         "conditional_spectral_seconds": 0.0}
    acquisition_payload = deepcopy(cheap)
    acquisition_hash = canonical_hash(acquisition_payload)
    freeze("ACQUISITION_FROZEN", acquisition_payload, acquisition_hash)
    if canonical_hash(acquisition_payload) != acquisition_hash:
        raise PreparationError("acquisition freeze callback mutated frozen payload")
    conditional = {}
    for system in systems:
        if cheap[system]["q"]:
            before = clock()
            conditional[system] = spectral_acquire(system)
            costs[system]["conditional_spectral_seconds"] = clock() - before
    before = clock()
    h1 = {system: h1_final(cheap[system], conditional.get(system)) for system in systems}
    adoption_seconds = clock() - before
    h1_payload = deepcopy(h1)
    h1_hash = canonical_hash(h1_payload)
    freeze("H1_FROZEN", h1_payload, h1_hash)
    if canonical_hash(h1_payload) != h1_hash:
        raise PreparationError("H1 freeze callback mutated frozen payload")
    h1_combined_wall = clock() - started
    # Original cheap/q and H1 decisions are immutable even if a freeze callback mutates its copy.
    if canonical_hash(cheap) != acquisition_hash or canonical_hash(h1) != h1_hash:
        raise PreparationError("decision changed across freeze boundary")
    all_spectral = deepcopy(conditional)
    before = clock()
    for system in systems:
        if not cheap[system]["q"]:
            all_spectral[system] = spectral_acquire(system)
    completion_wall = clock() - before
    return {"cheap": cheap, "H1": h1, "always_M1_predictions": all_spectral,
            "acquisition_hash": acquisition_hash, "H1_hash": h1_hash,
            "resource": {"per_system": costs, "H1_combined_wall_seconds": h1_combined_wall,
                         "H1_adoption_seconds": adoption_seconds,
                         "comparator_completion_wall_seconds_excluded_from_H1": completion_wall,
                         "shared_preprocessing": "account_separately_in_caller",
                         "standalone_cold_always_M1_wall": "not_measured",
                         "shared_path_cost_is_rigorous_cost_envelope": False}}
