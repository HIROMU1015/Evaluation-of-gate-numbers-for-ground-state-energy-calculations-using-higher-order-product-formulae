"""Document/Git identity checks only. No scientific computation or network calls.

Run from any checkout containing the packet:
  python3 <packet>/audit_packet.py --pr-repository <PR checkout>
The optional --write stores static_audit.json. --preservation-before is a local
management snapshot, not a scientific result or a file required in Git.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


BASE = "b58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66"
PACKET = Path(__file__).resolve().parent
REQUIRED = [
    "research_problem_and_access.md",
    "prior_art_and_baselines.md",
    "adaptive_subspace_construction.md",
    "mathematical_and_cost_analysis.md",
    "research_decision_handoff.md",
    "future_validation_conditions.md",
    "inputs/user_instruction.txt",
    "inputs/gpt_rereview_20261018.md",
    "source_registry.json",
    "literature_registry.json",
    "audit_packet.py",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def observe(repo):
    return {
        "head": git(repo, "rev-parse", "HEAD").decode().strip(),
        "branch": git(repo, "branch", "--show-current").decode().strip(),
        "status": git(repo, "status", "--porcelain=v1", "--untracked-files=all").decode(),
        "staged_diff_sha256": digest(git(repo, "diff", "--cached", "--binary")),
        "unstaged_diff_sha256": digest(git(repo, "diff", "--binary")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-repository", type=Path, required=True)
    parser.add_argument("--preservation-before", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    repo = Path(git(PACKET, "rev-parse", "--show-toplevel").decode().strip())
    prefix = PACKET.relative_to(repo).as_posix() + "/"
    checks = []

    def check(name, ok, details=None):
        checks.append({"check": name, "passed": bool(ok), "details": details})

    check("required_documentary_files", all((PACKET / f).is_file() for f in REQUIRED))
    changed = git(repo, "diff", "--name-only", BASE).decode().splitlines()
    check("no_base_tracked_file_changed", all(p.startswith(prefix) for p in changed), changed)
    for mode, options in [("fetch", []), ("push", ["--push"])]:
        urls = git(repo, "remote", "get-url", *options, "--all", "origin").decode().splitlines()
        ok = bool(urls) and all(
            re.fullmatch(r"(?:git@github\.com:|https://github\.com/)HIROMU1015/[^/]+(?:\.git)?", u)
            for u in urls
        )
        check("allowed_origin_" + mode, ok, urls)

    sources = json.loads((PACKET / "source_registry.json").read_text())
    entries = sources["git_sources"]
    check("thirteen_fixed_sources", len(entries) == 13)
    verified = []
    for item in entries:
        local_repo = repo if "Evaluation-of-" in item["repository"] else args.pr_repository
        ref = item["verified_snapshot_commit"] + ":" + item["path"]
        data = git(local_repo, "show", ref)
        blob = git(local_repo, "rev-parse", ref).decode().strip()
        origin = git(
            local_repo, "log", "-1", "--format=%H", item["verified_snapshot_commit"],
            "--", item["path"]
        ).decode().strip()
        raw = item["raw_verification"]
        ok = (
            len(data) == item["bytes"] and digest(data) == item["sha256"]
            and blob == item["git_blob"] and origin == item["origin_result_commit"]
            and raw["matches_git"] and raw["raw_bytes"] == item["bytes"]
            and raw["raw_sha256"] == item["sha256"]
        )
        if local_repo == repo:
            ancestry = subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor",
                 item["verified_snapshot_commit"], BASE], check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ).returncode == 0
            ok = ok and ancestry
        verified.append({"id": item["id"], "passed": ok})
    check("git_blob_bytes_sha256_origin_and_recorded_raw", all(r["passed"] for r in verified), verified)

    for item in sources["local_inputs"]:
        data = (PACKET / item["path"]).read_bytes()
        check("input_identity_" + item["path"], len(data) == item["bytes"] and digest(data) == item["sha256"])

    literature = json.loads((PACKET / "literature_registry.json").read_text())["papers"]
    check("bounded_primary_literature_coverage", len(literature) == 21 and sum(
        bool(p["full_html_downloaded"]) for p in literature
    ) == 13)

    missing_links = []
    pipe_errors = []
    for name in REQUIRED:
        if not name.endswith(".md") or name.startswith("inputs/"):
            continue
        file = PACKET / name
        content = file.read_text()
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if "://" in target or target.startswith("#"):
                continue
            rel = target.split("#", 1)[0]
            # Publication receipt is a later child commit, never a cyclic input.
            if not (file.parent / rel).is_file():
                missing_links.append({"file": name, "target": target})
        expected = None
        for line_no, line in enumerate(content.splitlines(), 1):
            if line.startswith("|"):
                count = len(re.findall(r"(?<!\\)\|", line))
                if expected is None:
                    expected = count
                elif count != expected:
                    pipe_errors.append({"file": name, "line": line_no, "pipes": count, "expected": expected})
            else:
                expected = None
    check("authored_document_local_links", not missing_links, missing_links)
    check("authored_markdown_table_columns", not pipe_errors, pipe_errors)

    bad_files = []
    for f in PACKET.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix not in {".md", ".txt", ".json", ".py"} or ".runtime" in f.parts:
            bad_files.append(f.relative_to(PACKET).as_posix())
    check("documentary_publication_allowlist", not bad_files, bad_files)

    preservation = []
    if args.preservation_before:
        before = json.loads(args.preservation_before.read_text())
        for path, old in before.items():
            current = observe(Path(path))
            preserved_fields = ["head", "branch", "staged_diff_sha256", "unstaged_diff_sha256"]
            preservation.append({
                "worktree_role": Path(path).name,
                "unchanged": old == current,
                "head_branch_tracked_diffs_preserved": all(old[k] == current[k] for k in preserved_fields),
                "status_lines_added": sorted(set(current["status"].splitlines()) - set(old["status"].splitlines())),
                "status_lines_removed": sorted(set(old["status"].splitlines()) - set(current["status"].splitlines())),
                "before_identity_sha256": digest(json.dumps(old, sort_keys=True).encode()),
                "after_identity_sha256": digest(json.dumps(current, sort_keys=True).encode()),
            })
        check("seven_existing_worktrees_head_branch_tracked_diffs_preserved", len(preservation) == 7 and all(
            r["head_branch_tracked_diffs_preserved"] for r in preservation
        ), preservation)

    result = {
        "date_jst": "2026-10-18",
        "scope": "documentary identity, scope, links, Git base preservation; no scientific calculation",
        "base_commit": BASE,
        "source_raw_note": "raw GETs were separately performed once; this audit verifies their stored identity fields without network",
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "scientific_numerical_runs": 0,
        "saved_scientific_values_reanalyzed": 0,
        "scientific_symbolic_checkers": 0,
        "circuits_built_compiled_benchmarked": 0,
        "new_scientific_grants": 0,
        "formal_research_state_changes": 0,
        "independent_mathematical_certification": False,
        "limitations": [
            "No mathematical formulas, physical claims, or sample-complexity theorems are programmatically tested.",
            "Preservation covers seven observed checkouts' HEAD/branch/status and tracked diff digests; not ignored runtime, all untracked file bytes, all worktrees, or all jobs.",
            "Status additions/removals are separately reported; passing tracked-preservation checks does not mean all untracked status lines stayed unchanged.",
            "Frozen input Markdown may contain historical local paths; authored-document link checks exclude those unchanged originals.",
            "Final publication verification is recorded in a subsequent publication receipt and final chat, outside this precommit audit.",
        ],
    }
    if args.write:
        (PACKET / "static_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"all_passed": result["all_passed"], "checks": len(checks),
                      "failures": [x for x in checks if not x["passed"]]}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)


if __name__ == "__main__":
    main()
