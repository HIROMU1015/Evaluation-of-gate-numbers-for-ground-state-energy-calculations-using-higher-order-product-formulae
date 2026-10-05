"""Content inventory of reachable tracked text; no numerical imports/actions.

This produces matches, never automatically certifies that CH2 was not executed.
Each unique text blob in every reachable commit is inspected. Binary/archive,
private, untracked and unreachable objects are outside the stated certificate.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import PurePosixPath
import re
import subprocess

TEXT_SUFFIXES = {".md", ".markdown", ".json", ".csv", ".py", ".pyi", ".txt",
                 ".yaml", ".yml", ".toml", ".sh", ".ipynb", ".rst"}
PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:CH_?2|CH₂|methylene)(?![A-Za-z0-9])", re.I)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def inventory(root):
    refs = git(root, "for-each-ref", "--format=%(refname) %(objectname)").decode().splitlines()
    commits = git(root, "rev-list", "--all").decode().splitlines()
    objects = defaultdict(lambda: {"paths": set(), "example_snapshot_commit": None})
    binary_paths = set()
    for commit in commits:
        for item in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
            if not item:
                continue
            header, raw_path = item.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            path = raw_path.decode("utf-8", "surrogateescape")
            if kind != "blob" or mode == "120000":
                continue
            suffix = PurePosixPath(path).suffix.lower()
            if suffix not in TEXT_SUFFIXES and PurePosixPath(path).name not in {"COMPLETE", "manifest", "Dockerfile"}:
                binary_paths.add(path)
                continue
            row = objects[oid]
            row["paths"].add(path)
            if row["example_snapshot_commit"] is None:
                row["example_snapshot_commit"] = commit

    matches, unreadable, scanned_bytes = [], [], 0
    proc = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for oid, row in sorted(objects.items()):
            proc.stdin.write((oid + "\n").encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().strip().split()
            if len(header) != 3 or header[1] != "blob":
                raise RuntimeError("unexpected Git batch response")
            size = int(header[2])
            body = proc.stdout.read(size)
            if len(body) != size or proc.stdout.read(1) != b"\n":
                raise RuntimeError("incomplete Git blob")
            scanned_bytes += size
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                unreadable.append({"blob_oid": oid, "paths": sorted(row["paths"]), "reason": "non_utf8_text_suffix"})
                continue
            if "\0" in text:
                unreadable.append({"blob_oid": oid, "paths": sorted(row["paths"]), "reason": "binary_NUL"})
                continue
            hits = [{"line": index, "excerpt": line[:800]} for index, line in enumerate(text.splitlines(), 1)
                    if PATTERN.search(line)]
            path_hits = [path for path in row["paths"] if PATTERN.search(path)]
            if hits or path_hits:
                matches.append({"blob_oid": oid, "sha256": hashlib.sha256(body).hexdigest(),
                    "bytes": size, "paths": sorted(row["paths"]),
                    "example_snapshot_commit": row["example_snapshot_commit"],
                    "path_matches": path_hits, "match_lines": hits,
                    "classification": "requires_content_review_not_automatic_execution_evidence"})
    finally:
        proc.stdin.close()
        proc.stdout.close()
        if proc.wait() != 0:
            raise RuntimeError("Git batch failed")
    return {"schema": "prospective_ch2_tracked_history_inventory_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "refs": refs, "reachable_commits": len(commits),
        "reachable_commits_sha256": hashlib.sha256("\n".join(commits).encode()).hexdigest(),
        "unique_tracked_text_blobs_scanned": len(objects), "text_blob_bytes_scanned": scanned_bytes,
        "match_expression": PATTERN.pattern, "text_suffixes": sorted(TEXT_SUFFIXES),
        "excluded_binary_archive_path_count": len(binary_paths),
        "excluded_scope": ["untracked", "private", "archive_payload", "binary_document_contents", "unreachable_objects"],
        "unreadable_text_blobs": unreadable, "matches": matches,
        "certificate": "pending_manual_classification",
        "scientific_actions": 0, "numerical_imports": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    print(json.dumps(inventory(args.project_root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
