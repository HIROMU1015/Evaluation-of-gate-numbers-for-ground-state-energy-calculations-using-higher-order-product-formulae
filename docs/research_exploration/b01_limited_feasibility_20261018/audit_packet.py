#!/usr/bin/env python3
"""Reusable document/Git/hash audit, no scientific calculation or equation checks.

B-01 adaptation of inherited static-only management audit; not a science checker.
--evidence holds private Git-metadata snapshots; no input originals published.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SLUG = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    packet = args.packet.resolve()
    root = packet.parents[2]
    prefix = str(packet.relative_to(root)) + "/"
    config = json.loads((packet / "audit_config.json").read_text())
    base = config["base_commit"]

    def git(cmd, cwd=root):
        return subprocess.check_output(["git", "-C", str(cwd), *cmd], stderr=subprocess.PIPE)

    checks = []

    def check(name, ok, details):
        checks.append({"check": name, "passed": bool(ok), "details": details})

    urls = [git(["remote", "get-url", *f, "origin"]).decode().strip() for f in [[], ["--push"]]]
    check("permitted actual remote URLs", all(u == "git@github.com:" + SLUG + ".git" for u in urls), urls)
    ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, "HEAD"], capture_output=True).returncode == 0
    check("dedicated branch and base", ancestor and git(["branch", "--show-current"]).decode().strip() == config["branch"], {"base": base, "branch": config["branch"]})
    delta = git(["diff", "--name-status", base]).decode().splitlines()
    extra = git(["ls-files", "--others", "--exclude-standard"]).decode().splitlines()
    check("only new packet; frozen base unchanged", all(x.startswith("A\t" + prefix) for x in delta)
          and all(x.startswith(prefix) for x in extra) and not git(["ls-tree", "-r", "--name-only", base, "--", prefix]),
          {"tracked_delta": delta, "new_untracked": extra})
    files = [p for p in packet.rglob("*") if p.is_file()]
    check("required documentary publication files", all((packet / f).is_file() for f in config["required_files"])
          and all(p.suffix in {".md", ".json", ".py"} and not p.is_symlink() for p in files)
          and not (packet / "inputs").exists(), {"required": config["required_files"], "private_original_content_included": False})
    registry = json.loads((packet / "source_registry.json").read_text())
    results = []
    for r in registry["sources"]:
        source_root = root if r["repository"] == SLUG else Path("/home/abe/Project/Partially Randomized Trotter")
        b = git(["show", r["verified_snapshot_commit"] + ":" + r["path"]], source_root)
        blob = git(["rev-parse", r["verified_snapshot_commit"] + ":" + r["path"]], source_root).decode().strip()
        origin = git(["log", "-1", "--format=%H", r["verified_snapshot_commit"], "--", r["path"]], source_root).decode().strip()
        ok = len(b) == r["bytes"] and sha(b) == r["sha256"] and blob == r["git_blob"] and origin == r["origin_result_commit"]
        ok = ok and r["fixed_raw_verified"] and r["raw_bytes"] == len(b) and r["raw_sha256"] == sha(b)
        if source_root == root:
            ok = ok and git(["show", "HEAD:" + r["path"]]) == b
        results.append({"id": r["id"], "identity_origin_recorded_raw_match": ok})
    check("fixed SOURCE identities and preserved Evaluation blobs", len(results) == config["source_count"] and all(r["identity_origin_recorded_raw_match"] for r in results), results)
    errors = []
    for p in packet.glob("*.md"):
        text = p.read_text()
        columns = None
        for number, line in enumerate(text.splitlines(), 1):
            if line != line.rstrip() or "\r" in line:
                errors.append(f"{p.name}:{number}:whitespace")
            if line.startswith("|"):
                width = len(re.split(r"(?<!\\)\|", line)) - 2
                if columns is not None and columns != width:
                    errors.append(f"{p.name}:{number}:table")
                columns = width
            else:
                columns = None
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" not in target and not (packet / target.split("#")[0]).is_file() and target not in {"provenance.json", "static_audit.json"}:
                errors.append(p.name + ":missing link:" + target)
        if text.count("\\[") != text.count("\\]"):
            errors.append(p.name + ":display delimiter")
    check("authored Markdown structure and local links", not errors, errors)
    before_path = args.evidence / "preservation_before.json"
    a = {r["path"]: r for r in json.loads(before_path.read_text())["worktrees"]}
    b = {r["path"]: r for r in json.loads(args.after.read_text())["worktrees"]}
    changes = [p for p in a if p not in b or a[p] != b[p]]
    check("existing checkout metadata preserved", len(a) == config["original_checkout_count"] and not changes,
          {"original": len(a), "unchanged": len(a) - len(changes), "changes": changes, "added": sorted(set(b) - set(a)),
           "before_snapshot_sha256": sha(before_path.read_bytes()), "after_snapshot_sha256": sha(args.after.read_bytes()),
           "limits": "HEAD/branch/status digests plus both dirty-root staged/unstaged diff hashes. No untracked-content, ignored-runtime or all-job audit."})
    info = json.loads((args.evidence / "instructions_and_resources.json").read_text())
    check("private task and current instruction identities", all(sha(Path(r["path"]).read_bytes()) == r["sha256"] for r in info["instructions_and_private_task_identity"]), info)
    decision = json.loads((packet / "feasibility_assessment.json").read_text())
    ok = decision["technical_classification"] in {"A", "B", "C", "D", "E"}
    ok = ok and decision["formal_state_changes"] == 0 and decision["other_series_state_changes"] == 0
    ok = ok and not any(decision[k] for k in ["new_algorithm_constructed", "new_filter_or_circuit_constructed",
        "new_theorem_independently_adopted", "science_executed", "important_scientific_review_performed",
        "new_contract_grant_authorization", "private_originals_published"])
    check("phase-specific authorized decision/survey scope", ok, {"phase": config["phase"], "config": config,
          "mathematical_novelty_certified": False})
    out = {"date_jst": "2026-10-18", "phase": config["phase"], "audit_scope": "documentary_static_management_only",
           "checks": checks, "check_count": len(checks), "all_passed": all(c["passed"] for c in checks),
           "no_scientific_equations_evaluated": True,
           "network_note": "Recorded raw acquisitions checked by identity; publication uses a separate fresh independent fetch/HTTPS verification.",
           "manifest_order": "provenance hashes this precommit output after audit; self and future child receipt excluded, both verified separately at publication."}
    rendered = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
        print(json.dumps({"phase": config["phase"], "checks": len(checks), "all_passed": out["all_passed"]}))
    else:
        print(rendered, end="")
    if not out["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
