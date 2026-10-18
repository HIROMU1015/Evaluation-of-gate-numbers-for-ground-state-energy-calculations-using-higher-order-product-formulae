#!/usr/bin/env python3
"""Audit approved closure documents, Git identities and preservation metadata.

This administrative program performs no scientific, numerical, or symbolic
validation. Default output is stdout; use --output only before freezing payload.
Original preservation snapshots stay outside Git and contain Git metadata only.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = "793cd63089dea8ca3e66b8c7faba173a198530eb"
BRANCH = "qc-coherent-subspace-g-closure-20261018"
PREFIX = "docs/research_exploration/coherent_subspace_g_closure_20261018/"
SLUG = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]


def git(args, root=ROOT):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(data):
    return {"bytes": len(data), "sha256": sha(data),
            "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--instructions", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = []

    def check(name, condition, details):
        checks.append({"check": name, "passed": bool(condition), "details": details})

    urls = [git(["remote", "get-url", *flags, "origin"]).decode().strip()
            for flags in [[], ["--push"]]]
    check("actual permitted fetch/push URLs", all(u == "git@github.com:" + SLUG + ".git" for u in urls), urls)
    ancestry = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"],
                              capture_output=True).returncode == 0
    check("dedicated branch and base ancestry", git(["branch", "--show-current"]).decode().strip() == BRANCH
          and ancestry, {"base": BASE, "branch": BRANCH})
    delta = git(["diff", "--name-status", BASE]).decode().splitlines()
    untracked = git(["ls-files", "--others", "--exclude-standard"]).decode().splitlines()
    check("new packet only; all frozen tracked sources untouched",
          not git(["ls-tree", "-r", "--name-only", BASE, "--", PREFIX])
          and all(s.startswith("A\t" + PREFIX) for s in delta)
          and all(s.startswith(PREFIX) for s in untracked),
          {"tracked_delta": delta, "new_untracked": untracked})
    required = {"research_closure_decision.md", "technical_outcomes_and_reduction.md",
                "remaining_questions_and_scope.md", "research_decision_handoff.md",
                "decision.json", "source_registry.json", "audit_packet.py"}
    files = list(PACKET.iterdir())
    check("required documentary files and allowlist", required <= {p.name for p in files}
          and all(p.is_file() and not p.is_symlink() and p.suffix in {".md", ".json", ".py"} for p in files),
          {"required": sorted(required), "no_scientific_binaries_or_runtime": True})
    decision = json.loads((PACKET / "decision.json").read_text())
    check("approved limited closure semantics", decision["formal_status"] == "CLOSED"
          and decision["independent_new_algorithm_candidate"] == "NOT_RETAINED"
          and decision["technical_basis"]["pc_classification"] == "B"
          and decision["pd"] == {"additional_construction_or_numerics": "NOT_PERFORMED",
                                 "usefulness": "UNDETERMINED", "proceed": False}
          and decision["decision_authority"]["actor"] == "user"
          and decision["authorized_formal_state_change_targets"] == ["fixed current G exploration only"],
          {"formal_status": "CLOSED", "candidate": "NOT_RETAINED", "P-c": "B",
           "authority": "current explicit user approval; Codex records it"})
    check("other series and general method scope preserved", decision["other_research_state_changes"] == 0
          and len(decision["excluded_from_closure"]) == 5
          and decision["other_series"]["SOS-PF_A2"] == "NOT_ADOPTED unchanged"
          and decision["D1_existing_constraints_maintained"]
          and decision["D2_original_finite_basis_electronic_H_absolute_E0_maintained"]
          and not decision["scientific_execution_authorized"]
          and not decision["detailed_scientific_review_authorized"]
          and not decision["new_scientific_contract_or_grant_issued"]
          and not decision["followup_research_authorized"],
          {"other_series": decision["other_series"], "excluded": decision["excluded_from_closure"]})
    registry = json.loads((PACKET / "source_registry.json").read_text())
    source_results = []
    for r in registry["sources"]:
        source_root = ROOT if r["repository"] == SLUG else Path("/home/abe/Project/Partially Randomized Trotter")
        data = git(["show", r["verified_snapshot_commit"] + ":" + r["path"]], source_root)
        origin = git(["log", "-1", "--format=%H", r["verified_snapshot_commit"], "--", r["path"]],
                     source_root).decode().strip()
        ok = all(identity(data)[k] == r[k] for k in ["bytes", "sha256", "git_blob"])
        ok = ok and origin == r["origin_result_commit"] and r["fixed_raw_verified"]
        ok = ok and r["raw_bytes"] == len(data) and r["raw_sha256"] == sha(data)
        if source_root == ROOT:
            ok = ok and git(["show", "HEAD:" + r["path"]]) == data
            ok = ok and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
                                        r["verified_snapshot_commit"], BASE], capture_output=True).returncode == 0
        source_results.append({"id": r["id"], "origin_snapshot_blob_bytes_sha256_raw_match": ok})
    check("30 fixed SOURCE identities, ancestry and recorded raw checks", len(source_results) == 30
          and all(r["origin_snapshot_blob_bytes_sha256_raw_match"] for r in source_results), source_results)
    old_manifests = []
    for directory in ["coherent_adaptive_subspace_initial_paper_20261018", "coherent_subspace_pc_mapping_20261018"]:
        prefix = "docs/research_exploration/" + directory + "/"
        for name, field in [("provenance.json", "manifest"), ("publication_receipt.json", "payload_files")]:
            rows = json.loads(git(["show", BASE + ":" + prefix + name]))[field]
            matches = all(all(identity(git(["show", BASE + ":" + r["path"]]))[k] == r[k]
                              for k in ["bytes", "sha256", "git_blob"]) for r in rows)
            old_manifests.append({"path": prefix + name, "entries": len(rows), "all_match": matches})
    check("both frozen manifests and parent publication receipts", all(r["all_match"] for r in old_manifests), old_manifests)

    bad = []
    local_links = []
    registered_urls = {r["github_url"] for r in registry["sources"]}
    fixed_refs = []
    for p in sorted(PACKET.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        defs = dict(re.findall(r"^\[([^\]]+)\]:\s+(\S+)", text, re.M))
        for label in re.findall(r"\[[^\]]+\]\[([^\]]+)\]", text):
            if label not in defs:
                bad.append(p.name + ":missing reference:" + label)
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text) + list(defs.values())
        for target in targets:
            if "://" in target:
                ok = target in registered_urls
                fixed_refs.append({"from": p.name, "registered_fixed_url": ok})
                if not ok:
                    bad.append(target)
            else:
                path = target.split("#", 1)[0]
                ok = (PACKET / path).is_file() or path in {"static_audit.json", "provenance.json"}
                local_links.append({"from": p.name, "to": path, "resolves_or_declared_output": ok})
                if not ok:
                    bad.append(target)
        expected = None
        for line in text.splitlines():
            if line != line.rstrip() or "\r" in line:
                bad.append(p.name + ":whitespace")
            if line.startswith("|"):
                width = len(re.split(r"(?<!\\)\|", line)) - 2
                if expected is not None and expected != width:
                    bad.append(p.name + ":table columns")
                expected = width
            else:
                expected = None
        if not text.endswith("\n"):
            bad.append(p.name + ":missing final newline")
    check("UTF-8 Markdown, links, fixed references and tables", not bad,
          {"errors": bad, "local_links": local_links, "fixed_references": fixed_refs})
    instruction_data = json.loads(args.instructions.read_text())
    current = instruction_data["current_common_instruction"]
    instruction_path = Path(current["repository_root"]) / current["path"]
    check("latest unified common instruction preserved", current["path"] == "research_project_instructions_unified_2026-10-17.md"
          and sha(instruction_path.read_bytes()) == current["sha256"],
          {"path": current["path"], "bytes": current["bytes"], "sha256": current["sha256"],
           "local_untracked_observation_not_public_Git_source": not current["tracked_at_observed_checkout"],
           "older_common_versions_not_co_normative": True})
    before = json.loads(args.before.read_text())
    after = json.loads(args.after.read_text())
    a = {r["path"]: r for r in before["worktrees"]}
    b = {r["path"]: r for r in after["worktrees"]}
    changed = [path for path in a if path not in b or a[path] != b[path]]
    counts = {}
    for row in a.values():
        key = row["repository_root"]
        counts[key] = counts.get(key, 0) + 1
    check("all 303 pre-existing checkouts preserved", len(a) == 303 and not changed,
          {"original_checkouts": len(a), "counts_by_repository": counts,
           "unchanged": len(a) - len(changed), "changed": changed,
           "new_checkouts": sorted(set(b) - set(a)),
           "before_snapshot_bytes_sha256": {"bytes": args.before.stat().st_size, "sha256": sha(args.before.read_bytes())},
           "after_snapshot_bytes_sha256": {"bytes": args.after.stat().st_size, "sha256": sha(args.after.read_bytes())},
           "observations": "HEAD/branch/porcelain status digest for all existing checkouts, plus staged/unstaged diff digest for both dirty roots; no untracked-content, ignored-runtime or complete shared-job audit"})
    out = {"date_jst": "2026-10-18", "audit_type": "documentary_static_management_only",
           "base_commit": BASE, "check_count": len(checks), "checks": checks,
           "all_passed": all(c["passed"] for c in checks),
           "scientific_validation_performed": False,
           "scope_statement": "No new mathematical/priority review, scientific runs, saved-value reanalysis, symbolic checker, solver, circuit work, grant, or other-series state changes. Only the user-approved current-G closure is recorded.",
           "manifest_order": "provenance.json hashes this precommit audit output after audit, excluding itself and future child receipt; publication independently checks all payload bytes including provenance.",
           "network_statement": "This script performs no network retrieval. Fixed SOURCE raw matches are acquisition attestations; payload publication gets fresh independent bare fetch and fixed-raw GET checks."}
    rendered = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
        print(json.dumps({"checks": len(checks), "all_passed": out["all_passed"]}))
    else:
        print(rendered, end="")
    if not out["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
