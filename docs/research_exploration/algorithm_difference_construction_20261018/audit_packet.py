#!/usr/bin/env python3
"""Administrative text/Git/hash audit. Never evaluates scientific equations.

The --evidence directory contains acquisition and checkout-metadata snapshots.
Default output is stdout. --output is for the precommit unfrozen audit only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = "addf2cecdc78a271b0139f0459266aa4fef5812d"
BRANCH = "qc-algorithm-difference-construction-20261018"
PREFIX = "docs/research_exploration/algorithm_difference_construction_20261018/"
SLUG = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]


def git(args, root=ROOT):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(data):
    return {"bytes": len(data), "sha256": digest(data),
            "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = []

    def check(name, condition, details):
        checks.append({"check": name, "passed": bool(condition), "details": details})

    urls = [git(["remote", "get-url", *flags, "origin"]).decode().strip() for flags in [[], ["--push"]]]
    check("actual permitted fetch/push URLs", all(u == "git@github.com:" + SLUG + ".git" for u in urls), urls)
    ancestry = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"],
                              capture_output=True).returncode == 0
    check("dedicated branch and base ancestry", git(["branch", "--show-current"]).decode().strip() == BRANCH
          and ancestry, {"branch": BRANCH, "base": BASE})
    delta = git(["diff", "--name-status", BASE]).decode().splitlines()
    untracked = git(["ls-files", "--others", "--exclude-standard"]).decode().splitlines()
    check("only new packet; old source/results/contracts untouched",
          not git(["ls-tree", "-r", "--name-only", BASE, "--", PREFIX])
          and all(s.startswith("A\t" + PREFIX) for s in delta)
          and all(s.startswith(PREFIX) for s in untracked), {"tracked_delta": delta, "untracked": untracked})
    required = {"research_problem_and_gap.md", "claim_and_baseline_comparison.md", "discriminating_examples.md",
                "generation_rule_construction.md", "mathematical_and_resource_assessment.md",
                "research_decision_handoff.md", "technical_verdict.json", "source_registry.json",
                "literature_provenance.json", "audit_packet.py"}
    paths = {str(p.relative_to(PACKET)) for p in PACKET.rglob("*") if p.is_file()}
    check("required files and documentary allowlist", required <= paths
          and all((PACKET / p).suffix in {".md", ".json", ".txt", ".py"} for p in paths)
          and not any(p.is_symlink() for p in PACKET.rglob("*")),
          {"required_files": sorted(required), "no_runtime_binary_state_or_scientific_runner": True})
    registry = json.loads((PACKET / "source_registry.json").read_text())
    source_results = []
    for r in registry["sources"]:
        source_root = ROOT if r["repository"] == SLUG else Path("/home/abe/Project/Partially Randomized Trotter")
        data = git(["show", r["verified_snapshot_commit"] + ":" + r["path"]], source_root)
        got = identity(data)
        origin = git(["log", "-1", "--format=%H", r["verified_snapshot_commit"], "--", r["path"]], source_root).decode().strip()
        ok = all(got[k] == r[k] for k in got) and origin == r["origin_result_commit"]
        ok = ok and r["fixed_raw_verified"] and r["raw_bytes"] == len(data) and r["raw_sha256"] == digest(data)
        if source_root == ROOT:
            ok = ok and git(["show", "HEAD:" + r["path"]]) == data
            ok = ok and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
                                       r["verified_snapshot_commit"], BASE], capture_output=True).returncode == 0
        source_results.append({"id": r["id"], "origin_snapshot_blob_bytes_sha256_recorded_raw_match": ok})
    check("12 fixed sources, separate origins and reuse ancestry", len(source_results) == 12
          and all(r["origin_snapshot_blob_bytes_sha256_recorded_raw_match"] for r in source_results), source_results)
    input_results = []
    for r in registry["local_input_observations"]:
        data = (args.evidence / r["private_evidence_name"]).read_bytes()
        ok = data == Path(r["supplied_source"]).read_bytes() and len(data) == r["bytes"] and digest(data) == r["sha256"]
        input_results.append({"label": r["label"], "bytes_preserved_privately": ok, "public_content_included": r["public_content_included"]})
    check("two private original identities; no public input copies", len(input_results) == 2 and all(r["bytes_preserved_privately"] and not r["public_content_included"] for r in input_results) and not (PACKET / "inputs").exists(), input_results)
    literature = json.loads((PACKET / "literature_provenance.json").read_text())
    lit_results = []
    for r in literature["papers"]:
        data = (args.evidence / (r["id"] + ".html")).read_bytes()
        lit_results.append({"id": r["id"], "cached_HTML_bytes_sha256_match": len(data) == r["bytes"]
                            and digest(data) == r["sha256"], "reading_scope": r["reading_scope"]})
    check("bounded primary HTML acquisition identities", len(lit_results) == 3
          and all(r["cached_HTML_bytes_sha256_match"] for r in lit_results)
          and all(not r["fulltext_republished"] for r in literature["papers"]), lit_results)
    verdict = json.loads((PACKET / "technical_verdict.json").read_text())
    zero_fields = ["formal_research_state_changes", "new_scientific_numerics", "saved_scientific_values_reanalysis",
                   "scientific_symbolic_checker", "circuit_build_compile_benchmark", "new_science_contract_grant_authorization"]
    check("scope and technical-versus-formal classification", verdict["primary_classification"] == "REDUCES_TO_KNOWN_PROCEDURES"
          and all(verdict[k] == 0 for k in zero_fields) and not verdict["formally_adopted"]
          and not verdict["important_GPT_science_review_performed"] and verdict["next_minimal_numerical_experiment"] is None,
          {"classification": verdict["primary_classification"], "preserved_states": verdict["preserved_states"],
           "evidence_note": "These scope declarations are descriptive, not mathematical certification."})
    errors = []
    link_count = 0
    primary_urls = {r["url"] for r in literature["papers"]}
    for p in sorted(PACKET.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        width = None
        for number, line in enumerate(text.splitlines(), 1):
            if line != line.rstrip() or "\r" in line:
                errors.append(f"{p.name}:{number}:whitespace")
            if line.startswith("|"):
                current = len(re.split(r"(?<!\\)\|", line)) - 2
                if width is not None and current != width:
                    errors.append(f"{p.name}:{number}:table-columns")
                width = current
            else:
                width = None
        if text.count("\\[") != text.count("\\]"):
            errors.append(p.name + ":display-math-delimiters")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            link_count += 1
            if "://" in target:
                if target not in primary_urls:
                    errors.append(p.name + ":unregistered-primary-link:" + target)
            else:
                path = target.split("#", 1)[0]
                if not (PACKET / path).is_file() and path not in {"static_audit.json", "provenance.json"}:
                    errors.append(p.name + ":missing-local-link:" + target)
    check("authored Markdown links, tables and delimiters", not errors,
          {"files": len(list(PACKET.glob('*.md'))), "links": link_count, "errors": errors,
           "private_original_contents_excluded_from_publication": True})
    before_path = args.evidence / "preservation_before.json"
    before = json.loads(before_path.read_text())
    after = json.loads(args.after.read_text())
    a = {r["path"]: r for r in before["worktrees"]}
    b = {r["path"]: r for r in after["worktrees"]}
    changes = [path for path in a if path not in b or a[path] != b[path]]
    check("all 304 pre-existing checkout metadata preserved", len(a) == 304 and not changes,
          {"original_checkouts": len(a), "unchanged": len(a) - len(changes), "changed": changes,
           "added_checkouts": sorted(set(b) - set(a)), "before_snapshot_sha256": digest(before_path.read_bytes()),
           "after_snapshot_sha256": digest(args.after.read_bytes()),
           "scope": "HEAD/branch/status digest for all; staged/unstaged text diff hashes for both dirty roots. No untracked-content, ignored-runtime, complete shared-process or all-chat audit."})
    info = json.loads((args.evidence / "resources_and_instructions.json").read_text())
    matched = all(digest(Path(r["path"]).read_bytes()) == r["sha256"] for r in info["instructions"])
    check("current instructions and shared-resource settings preserved", matched,
          {"instruction_identities": info["instructions"], "resources": {k: info[k] for k in ["available_cpus", "memory", "workload"]},
           "current_common_version": "2026-10-17; older version not co-normative"})
    out = {"date_jst": "2026-10-18", "audit_scope": "Documentary identities and metadata only; no scientific equation evaluation",
           "base_commit": BASE, "check_count": len(checks), "checks": checks,
           "all_passed": all(c["passed"] for c in checks),
           "mathematics_novelty_and_hardware_cost_certified": False,
           "network_note": "No network in this script. Fixed raw checks are acquisition records; payload receives separate fresh bare fetch and HTTPS verification.",
           "manifest_order": "provenance hashes this precommit output after audit; excludes itself and future child receipt. All payload blobs including manifest get independent publication verification."}
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
