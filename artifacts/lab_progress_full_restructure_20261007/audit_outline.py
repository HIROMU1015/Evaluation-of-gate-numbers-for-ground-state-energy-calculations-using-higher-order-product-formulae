#!/usr/bin/env python3
"""Check the adopted outline and exact pinned source blobs; no science execution."""

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = Path(__file__).resolve().parent
OUTLINE = ROOT / "docs/research_outcomes/20261006/lab_progress_slide_outline.md"
NOTES = OUTLINE.with_name("rewrite_review_and_source_notes_20261007.md")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def load(name):
    return json.loads((ARTIFACT / name).read_text(encoding="utf-8"))


def table_width_errors(text):
    errors = []
    tables = 0
    expected = None
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("|"):
            expected = None
            continue
        # Escaped pipes are content; every remaining pipe separates GFM cells.
        width = len(re.findall(r"(?<!\\)\|", line)) - 1
        if expected is None:
            tables += 1
            expected = width
        elif width != expected:
            errors.append({"line": line_number, "expected": expected, "actual": width})
    return tables, errors


def main():
    input_record = load("input_record.json")
    registry = load("source_registry.json")
    previous_records = load("previous_source_records.json")
    text = OUTLINE.read_text(encoding="utf-8")
    raw = OUTLINE.read_bytes()
    checks = {}
    checks["adopted_attachment_exact_after_lf_normalization"] = (
        sha256(raw) == input_record["input_attachment_normalized_sha256"]
        and b"\r" not in raw
    )
    old = git("show", input_record["base_outline_commit"] + ":" + input_record["base_outline_path"])
    checks["previous_outline_hash_matches_public_snapshot"] = sha256(old) == input_record["base_outline_sha256"]

    heading_matches = list(re.finditer(r"^## Slide (\d{2})｜([^\n]+)$", text, re.M))
    heading_rows = [(m.group(1), m.group(2)) for m in heading_matches]
    title_rows = re.findall(r"^\| (\d{2}) \| ([^\n]+?) \| ([\d, ]+) \|$", text, re.M)
    checks["main_slides_01_to_46"] = [n for n, _ in heading_rows] == [f"{i:02d}" for i in range(1, 47)]
    checks["title_table_matches_all_slide_headings"] = heading_rows == [(n, title) for n, title, _ in title_rows]
    mapped_old = {int(n.strip()) for _, _, olds in title_rows for n in olds.split(",")}
    checks["all_previous_29_slides_have_mapping"] = mapped_old == set(range(1, 30))
    checks["supplements_a1_to_a8"] = re.findall(r"^## 補足 (A\d+)｜", text, re.M) == [f"A{i}" for i in range(1, 9)]
    checks["evidence_ids_e01_to_e25"] = re.findall(r"^## (E\d{2})｜", text, re.M) == [f"E{i:02d}" for i in range(1, 26)]
    required_fields = [
        "**このページが答える問い（発表者用）：**", "**位置付け：**",
        "### スライド本文", "### 話すときの補足", "**次へのつなぎ：**",
        "**出典・旧版対応（作成者用）：**",
    ]
    supplement_start = text.index("## 補足 A1｜")
    missing_fields = []
    for i, match in enumerate(heading_matches):
        end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else supplement_start
        block = text[match.end():end]
        missing = [field for field in required_fields if block.count(field) != 1]
        if missing:
            missing_fields.append({"slide": match.group(1), "fields": missing})
    checks["projection_and_presenter_fields_present_per_slide"] = not missing_fields

    anchors = re.findall(r'<a id="([^"]+)"></a>', text)
    checks["explicit_anchors_unique"] = len(anchors) == len(set(anchors))
    checks["slide_and_evidence_anchors_complete"] = (
        {f"slide-{i:02d}" for i in range(1, 47)} | {f"src-e{i:02d}" for i in range(1, 26)}
    ).issubset(set(anchors))
    missing_links = []
    relative_links = []
    for document in [OUTLINE, NOTES]:
        body = document.read_text(encoding="utf-8")
        document_anchors = set(re.findall(r'<a id="([^"]+)"></a>', body))
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", body):
            if target.startswith("#"):
                if target[1:] not in document_anchors:
                    missing_links.append({"document": str(document.relative_to(ROOT)), "target": target})
            elif not urlparse(target).scheme:
                path = (document.parent / unquote(target.split("#", 1)[0])).resolve()
                relative_links.append({"document": str(document.relative_to(ROOT)), "target": target})
                # This audit writes checks.json below; defer that one existence check.
                if not path.is_file() and path != ARTIFACT / "checks.json":
                    missing_links.append(relative_links[-1])
    checks["local_links_and_explicit_anchor_targets_exist"] = not missing_links
    delimiters = re.findall(r"^\$\$$", text, re.M)
    checks["display_math_delimiters_paired"] = len(delimiters) % 2 == 0
    tables, table_errors = table_width_errors(text)
    checks["markdown_table_column_counts_consistent"] = not table_errors
    checks["only_intentional_markdown_trailing_whitespace"] = [
        (n, line[-2:]) for n, line in enumerate(text.splitlines(), 1) if line.rstrip() != line
    ] == [(3, "  ")]

    registry_errors = []
    for source in registry["records"]:
        commit_path = source["verified_snapshot_commit"] + ":" + source["source_path"]
        blob = git("show", commit_path)
        oid = git("rev-parse", commit_path).decode().strip()
        if oid != source["git_blob"] or sha256(blob) != source["sha256"]:
            registry_errors.append(commit_path)
    checks["all_pinned_git_source_blob_hashes_match"] = not registry_errors
    checks["source_origin_and_verified_snapshot_fields_separate"] = all(
        "origin_result_record" in item and "verified_snapshot_commit" in item for item in registry["records"]
    )
    checks["previous_25_source_records_preserved"] = len(previous_records["records"]) == 25
    pinned_links = re.findall(r"https://github\.com/[^\s)]+/blob/[0-9a-f]{40}/[^\s)]+", text)
    registered_urls = {source["url"] for source in registry["records"]}
    checks["every_outline_pinned_link_registered"] = set(pinned_links).issubset(registered_urls)
    checks["previous_e25_commit_retained_in_ancestry"] = subprocess.run(
        ["git", "merge-base", "--is-ancestor", input_record["base_outline_commit"], "HEAD"], cwd=ROOT, check=False
    ).returncode == 0

    result = {
        "kind": "documentation_only_adoption_audit",
        "new_scientific_computation": False,
        "refit_or_formal_rescoring": False,
        "web_article_review": False,
        "passed": all(checks.values()),
        "checks": checks,
        "counts": {
            "main_slides": len(heading_rows), "supplements": 8,
            "evidence_ids": 25, "explicit_anchors": len(anchors), "tables": tables,
            "display_math_blocks": len(delimiters) // 2,
            "outline_pinned_git_links": len(pinned_links),
            "registered_git_source_blobs": len(registry["records"]),
        },
        "details": {"missing_fields": missing_fields, "missing_links": missing_links,
                    "table_errors": table_errors, "source_registry_errors": registry_errors},
        "scope": "Attachment fidelity, Markdown structure, exact referenced Git blobs and provenance. Historical scientific audits and other-chat follow-up tasks were not executed.",
    }
    (ARTIFACT / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert (ARTIFACT / "checks.json").is_file()
    paths = [OUTLINE, NOTES, *sorted(ARTIFACT.glob("*"))]
    paths = [p for p in paths if p.is_file() and p.name != "manifest.json"]
    manifest = {
        "kind": "documentation_only_manifest",
        "self_excluded": True,
        "excluded_files": [str((ARTIFACT / "manifest.json").relative_to(ROOT))],
        "self_exclusion_reason": "Including its own hash would make the manifest self-referential.",
        "files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p.read_bytes()), "bytes": p.stat().st_size} for p in paths],
    }
    (ARTIFACT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "counts": result["counts"], "failed_checks": [k for k, v in checks.items() if not v], "details": result["details"]}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
