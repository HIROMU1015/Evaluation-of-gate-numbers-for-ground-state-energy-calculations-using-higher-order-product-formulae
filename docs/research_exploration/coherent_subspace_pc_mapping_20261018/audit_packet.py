#!/usr/bin/env python3
"""Document/Git/hash audit only; no scientific calculation or symbolic checks.

Run from this worktree with /usr/bin/python3. With --evidence, compare the six
pre-existing checkout snapshots captured for this task. Without it, that
environment-specific observation is explicitly skipped. --output writes only
the named administrative JSON; default is stdout. Do not rewrite frozen files.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


BASE = "7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd"
PREFIX = "docs/research_exploration/coherent_subspace_pc_mapping_20261018/"
OLD = "docs/research_exploration/coherent_adaptive_subspace_initial_paper_20261018/"
BRANCH = "qc-coherent-subspace-pc-mapping-20261018"
REPO = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]


def git(args, root=ROOT):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(data):
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    return {"bytes": len(data), "sha256": digest(data), "git_blob": blob}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = []

    def check(name, condition, details):
        checks.append({"check": name, "passed": bool(condition), "details": details})

    fetch = git(["remote", "get-url", "origin"]).decode().strip()
    push = git(["remote", "get-url", "--push", "origin"]).decode().strip()
    allowed = {"git@github.com:" + REPO + ".git", "https://github.com/" + REPO + ".git"}
    check("actual fetch/push target", fetch in allowed and push in allowed,
          {"fetch": fetch, "push": push})
    check("isolated branch and base ancestry",
          git(["branch", "--show-current"]).decode().strip() == BRANCH
          and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"],
                             capture_output=True).returncode == 0,
          {"base": BASE, "branch": BRANCH})
    changed = set(git(["diff", "--name-only", BASE]).decode().splitlines())
    changed.update(git(["ls-files", "--others", "--exclude-standard"]).decode().splitlines())
    check("all changes confined to new packet", all(p.startswith(PREFIX) for p in changed),
          {"paths": sorted(changed)})
    required = {"scope_and_protocol.md", "pc_known_method_mapping.md",
                "pc_information_and_cost_comparison.md", "pc_independence_assessment.md",
                "research_decision_handoff.md", "source_registry.json",
                "literature_provenance.json", "audit_packet.py"}
    files = {p.name for p in PACKET.iterdir() if p.is_file()}
    check("required source files", required <= files, {"required": sorted(required)})
    check("documentary publication allowlist",
          all(p.is_file() and not p.is_symlink() and p.suffix in {".md", ".json", ".py"}
              for p in PACKET.iterdir()),
          {"files": sorted(files), "no_runtime_vectors_or_binary_results": True})

    registry = json.loads((PACKET / "source_registry.json").read_text())
    source_results = []
    for r in registry["sources"]:
        source_root = ROOT if r["repository"] == REPO else Path("/home/abe/Project/Partially Randomized Trotter")
        data = git(["show", r["verified_snapshot_commit"] + ":" + r["path"]], source_root)
        origin = git(["log", "-1", "--format=%H", r["verified_snapshot_commit"], "--", r["path"]],
                     source_root).decode().strip()
        got = identity(data)
        ancestry_ok = True
        if source_root == ROOT:
            ancestry_ok = subprocess.run(
                ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", r["verified_snapshot_commit"], BASE],
                capture_output=True).returncode == 0
        raw_ok = (r["fixed_raw_verified"] and r["raw_bytes"] == got["bytes"]
                  and r["raw_sha256"] == got["sha256"])
        ok = all(got[k] == r[k] for k in got) and origin == r["origin_result_commit"] and ancestry_ok and raw_ok
        source_results.append({"id": r["id"], "git_identity_and_origin_match": ok,
                               "recorded_fixed_raw_match": raw_ok})
    check("19 fixed SOURCE identities and origins",
          len(source_results) == 19 and all(r["git_identity_and_origin_match"] for r in source_results),
          source_results)

    old_results = []
    for name, field, count in [("provenance.json", "manifest", 12),
                               ("publication_receipt.json", "payload_files", 13)]:
        old = json.loads(git(["show", BASE + ":" + OLD + name]))
        rows = old[field]
        ok = len(rows) == count
        for r in rows:
            data = git(["show", BASE + ":" + r["path"]])
            got = identity(data)
            ok = ok and all(got[k] == r[k] for k in got)
        old_results.append({"document": name, "entries": len(rows), "all_identity_matches": ok})
    check("prior manifest and parent receipt", all(r["all_identity_matches"] for r in old_results), old_results)

    links = []
    bad_links = []
    deferred_outputs = {"static_audit.json", "provenance.json"}
    bad_tables = []
    for p in sorted(PACKET.glob("*.md")):
        text = p.read_text()
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            ok = (PACKET / path).is_file() or path in deferred_outputs
            links.append({"from": p.name, "to": path, "resolves_or_declared_output": ok})
            if not ok:
                bad_links.append(path)
        expected = None
        for number, line in enumerate(text.splitlines(), 1):
            if line.startswith("|"):
                width = len(re.split(r"(?<!\\)\|", line)) - 2
                if expected is None:
                    expected = width
                elif width != expected:
                    bad_tables.append({"file": p.name, "line": number, "columns": width})
            else:
                expected = None
    check("local Markdown links", not bad_links, links)
    check("Markdown table structure", not bad_tables, {"bad_rows": bad_tables})
    literature = json.loads((PACKET / "literature_provenance.json").read_text())
    reused = literature["reused_primary_sources"]
    extra = {r["id"]: r for r in literature["targeted_primary_sources"]}
    check("bounded literature metadata", len(reused) == 5 and extra["C02"]["status"] == "retrieved"
          and all(r.get("fulltext_republished") is False for r in [*reused, *extra.values()]),
          {"reused_full_html": 5, "new_full_html": 1, "publisher_summary_only": ["C01"],
           "original_fulltext_unavailable": ["C03", "C04"], "math_not_programmatically_checked": True})

    preservation = []
    if args.evidence:
        before = json.loads((args.evidence / "preservation_before.json").read_text())
        for location, old in before.items():
            now = {"head": git(["rev-parse", "HEAD"], location).decode().strip(),
                   "branch": git(["branch", "--show-current"], location).decode().strip(),
                   "staged": digest(git(["diff", "--cached"], location)),
                   "unstaged": digest(git(["diff"], location))}
            status = git(["status", "--short", "--untracked-files=all"], location).decode()
            prior_status = set(old["status"].splitlines())
            current_status = set(status.splitlines())
            same = all(now[k] == old[k] for k in now)
            preservation.append({"checkout": location, "before": {k: old[k] for k in now},
                                 "after": now, "head_branch_tracked_digests_unchanged": same,
                                 "status_unchanged": status == old["status"],
                                 "status_added_entries": sorted(current_status - prior_status),
                                 "status_removed_entries": sorted(prior_status - current_status)})
        check("six existing checkout tracked-state preservation",
              len(preservation) == 6 and all(r["head_branch_tracked_digests_unchanged"] for r in preservation),
              preservation)
    else:
        preservation = [{"not_checked": "Original --evidence snapshot not supplied; not silently certified."}]

    out = {"date_jst": "2026-10-18", "scope": "Documentary static audit only; no mathematics validation",
           "base_commit": BASE, "checks": checks, "check_count": len(checks),
           "all_passed": all(r["passed"] for r in checks),
           "manifest_order": "provenance.json hashes audit output after audit; self excluded. All payload including manifest is independently verified at publication.",
           "network_scope": "This audit performs no network reads. SOURCE raw checks are acquisition attestations; new payload publication gets separate independent fetch/HTTPS checks.",
           "scope_observation": {"new_scientific_calculations": 0, "saved_numeric_reanalysis": 0,
                                 "scientific_symbolic_checker_runs": 0, "circuit_build_compile_benchmarks": 0,
                                 "new_scientific_contracts_or_grants": 0, "formal_research_state_changes": 0},
           "limits": "Static checks cannot certify paper mathematics, novelty, hardware costs, or all concurrent users/jobs. They do not read numerical raw results or modify prior records."}
    rendered = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
        print(json.dumps({"checks": len(checks), "all_passed": out["all_passed"], "output": str(args.output)}))
    else:
        print(rendered, end="")
    if not out["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
