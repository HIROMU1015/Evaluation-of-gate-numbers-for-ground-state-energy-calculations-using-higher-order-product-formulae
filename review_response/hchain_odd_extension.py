"""Odd-chain extension plumbing; inherited scientific rules remain unchanged."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path

import numpy as np

from review_response.hchain_input_reference_preparation import (
    Ledger, PreparationError, canonical_hash, sha_file, write_json,
)
from review_response.hchain_prediction_phase import (
    check_remote, git, require_clean, verify_blob, verify_entries,
)
from review_response.hchain_truth_scoring import score_action, score_coordinate

BASE = "5a9226a94fad0b578df1a53edd1a29e3571ad8c3"
DOC = "docs/second_study_v2/hchain_odd_extension_20261004"
OUT = "artifacts/hchain_h3_h5_h7_extension_20261004"
OLD = "docs/second_study_v2/hchain_independent_validation_20261004"
PREP_DOC = "docs/second_study_v2/hchain_input_reference_preparation_20261004"
SYSTEMS = ("H3", "H5", "H7")
STATUS = "hchain_h3_h5_h7_extension_complete_review_required"


def dimensions(n, alpha, beta):
    if not 0 <= alpha <= n or not 0 <= beta <= n:
        raise PreparationError("invalid population")
    single_a, single_b = alpha * (n-alpha), beta * (n-beta)
    choose = lambda x: math.comb(x, 2) if x >= 2 else 0
    cisd = (1 + single_a + single_b + choose(alpha)*choose(n-alpha)
            + choose(beta)*choose(n-beta) + single_a*single_b)
    return math.comb(n, alpha)*math.comb(n, beta), cisd


def primary_rank(dimension):
    return max(m for m in (1, 2, 4, 8) if m <= dimension)


class SystemLedger(Ledger):
    """Tight extension limits override the inherited adapter's broader caps."""
    def __init__(self, primary):
        super().__init__()
        self.limits = {
            "Hamiltonian_generations": 1, "CISD_generations": 1,
            "input_verification_h_matvecs": 1,
            "reference_pf_actions": 34, "reference_h_exponential_actions": 34,
            "candidate_cheap_pf_actions": 3, "candidate_h_exponential_actions": 3,
            "m1_pf_vector_actions": 3*primary, "m1_h_matvecs": 3*primary,
            "Arnoldi_chains": 3, "full_H_ground_solves": 1,
            "full_pf_unitary_builds": 3, "direct_Schur_solves": 3,
            "direct_truth_coordinates": 3, "target_phase_gaps": 3,
        }

    def charge(self, key, maximum):
        super().charge(key, min(maximum, self.limits.get(key, maximum)))


def file_entry(root, path):
    return {"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
            "sha256": sha_file(path)}


def seal(root):
    check_remote(root)
    require_clean(root)
    content = git(root, "rev-parse", "HEAD").decode().strip()
    git(root, "merge-base", "--is-ancestor", BASE, content)
    paths = [f"{DOC}/protocol.json", f"{DOC}/protocol.md", f"{DOC}/source_registry.json",
             "review_response/hchain_odd_extension.py",
             "review_response/run_hchain_odd_extension.py",
             "review_tests/test_hchain_odd_extension.py"]
    rows = []
    for name in paths:
        verify_blob(root, name, content)
        rows.append({**file_entry(root, root/name), "origin_result_commit": content,
                     "verified_snapshot_commit": content})
    write_json(root/DOC/"implementation_manifest.json", {
        "content_commit": content, "manifest_self_excluded": True, "files": rows,
        "base_verified_snapshot": BASE})


def source_gate(root):
    require_clean(root)
    check_remote(root)
    manifest_path = root/DOC/"implementation_manifest.json"
    verify_blob(root, str(manifest_path.relative_to(root)), "HEAD")
    sealed = json.loads(manifest_path.read_text())
    verify_entries(root, sealed["files"])
    for row in sealed["files"]:
        verify_blob(root, row["path"], sealed["content_commit"])
    registry = json.loads((root/DOC/"source_registry.json").read_text())
    verify_entries(root, registry["sources"])
    for row in registry["sources"]:
        verify_blob(root, row["path"], BASE)
    changed = git(root, "diff", "--name-only", BASE, "HEAD").decode().splitlines()
    permitted = (DOC+"/", OUT+"/", "docs/second_study_v2/hchain_h8_extension_preflight_20261004/")
    exact = {"review_response/hchain_odd_extension.py", "review_response/run_hchain_odd_extension.py",
             "review_tests/test_hchain_odd_extension.py"}
    if any(name not in exact and not name.startswith(permitted) for name in changed):
        raise PreparationError("inherited/even-series source or artifact modified")
    return {"execution_HEAD": git(root, "rev-parse", "HEAD").decode().strip(),
            "content_commit": sealed["content_commit"], "verified_base_snapshot": BASE,
            "implementation_manifest_sha256": sha_file(manifest_path),
            "new_files": sealed["files"], "inherited_sources": registry["sources"],
            "inherited_artifacts_modified": False}


def commit_files(root, paths, message):
    """Explicit lightweight allowlist, checked before and after commit."""
    require_clean(root)
    check_remote(root)
    paths = [str(Path(path).relative_to(root)) for path in paths]
    if len(paths) != len(set(paths)) or not paths:
        raise PreparationError("empty/duplicate commit path set")
    if any(".runtime" in Path(name).parts or Path(name).suffix not in (".json", ".csv", ".md", ".sha256", ".log") for name in paths):
        raise PreparationError("non-lightweight commit member")
    git(root, "add", "--", *paths)
    if set(git(root, "diff", "--cached", "--name-only").decode().splitlines()) != set(paths):
        raise PreparationError("unexpected staged member; stop without commit")
    git(root, "commit", "-m", message)
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    if set(git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()) != set(paths):
        raise PreparationError("unexpected committed member")
    for name in paths:
        verify_blob(root, name, commit)
    return commit


def plan_rows(references, identity):
    rows = []
    for system in SYSTEMS:
        reference = references[system]
        if not reference["qualified"]:
            continue
        t_ref = reference["t_ref"]
        if not math.isfinite(t_ref) or t_ref <= 0:
            raise PreparationError("invalid reference; no replacement")
        for ratio in (.5, .65, .8):
            t = float(ratio)*float(t_ref)
            rows.append({"system": system, "candidate_id": f"{system}_r{ratio}",
                "ratio": ratio, "ratio_hex": ratio.hex(), "t_ref": t_ref,
                "t_ref_hex": t_ref.hex(), "time": t, "time_hex": t.hex(),
                "K": identity[system]["K"], "primary_m": primary_rank(identity[system]["sector_dimension"])})
    return rows


def validate_plan(rows, references, identity):
    if rows != plan_rows(references, identity):
        raise PreparationError("candidate exact binary64/identity mismatch")
    return rows


def immutable_score(prediction, truth, ground):
    before = canonical_hash(prediction)
    frozen = deepcopy(prediction)
    by_id = {row["candidate_id"]: row for row in truth["points"]}
    expected = {row["candidate_id"] for row in frozen["plan"]}
    if set(by_id) != expected or len(truth["points"]) != len(expected):
        raise PreparationError("truth exact coordinate set mismatch")
    coordinates, decisions, summaries = [], [], {}
    for system in frozen["eligible_systems"]:
        cheap = frozen["cheap_B0_B1_B2_q"][system]
        m1 = {row["candidate_id"]: row for row in frozen["M1"][system]}
        coords = [score_coordinate(p, m1[p["candidate_id"]], by_id[p["candidate_id"]],
                  ground["systems"][system]["energy_hartree"]) for p in cheap["points"]]
        coordinates.extend(coords)
        arms = [("B0", cheap["B0"], None),
            *[(f"B1_gamma_{arm['gamma']}", arm["selected"], arm["gamma"]) for arm in cheap["B1_frontier"]],
            ("B2", cheap["B2"], cheap["B2_gamma"]),
            ("H1", frozen["H1"][system]["action"], cheap["B2_gamma"]),
            ("always_M1", frozen["always_M1_decisions"][system]["selected"], None)]
        scored = [score_action(system, name, action, cheap, by_id, gamma=gamma) for name, action, gamma in arms]
        decisions.extend(scored)
        summaries[system] = {
            "q": cheap["q"], "B2_H1_action_identical": cheap["B2"] == frozen["H1"][system]["action"],
            "minimum_safe_gamma_in_fixed_frontier": next((r["gamma"] for r in scored if r["arm"].startswith("B1_") and r["safe"] is True), None),
            "q_one_conditional_path_performance": "not_measured" if cheap["q"] == 0 else "see_frozen_conditional_path",
            "M1_branch_pass": sum(r["branch_correct_shift_gap"] is True for r in coords),
            "M1_width_cover": sum(r["empirical_width_covers"] is True for r in coords),
            "M1_abstentions": sum(r["M1_policy_abstained"] for r in coords), "decisions": scored}
    if canonical_hash(prediction) != before:
        raise PreparationError("scorer changed prediction")
    return {"status": STATUS, "coordinate_scores": coordinates, "decision_scores": decisions,
            "system_summaries": summaries, "prediction_modified": False,
            "empirical_width_is_certificate": False, "next_stage_authorized": False}
