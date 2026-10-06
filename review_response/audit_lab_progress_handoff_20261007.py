"""Read-only source, freeze, document and public-package audit; no science runs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/lab_progress_additional_validation_20261007"
DIRECTORIES = [ROOT / "artifacts" / name for name in (
    "lab_progress_h4_state_checks_20261007", "lab_progress_hf_cap_checks_20261007",
    "lab_progress_hchain_transfer_20261007", "lab_progress_additional_validation_20261007")]
DOCS = [ROOT / path for path in (
    "docs/research_outcomes/20261006/lab_progress_slide_outline.md",
    "docs/research_outcomes/20261006/verification_gaps_and_next_checks.md",
    "docs/research_outcomes/20261007/additional_validation_scope.md",
    "docs/research_outcomes/20261007/additional_validation_results.md")]
CODE = [ROOT / "review_response" / name for name in (
    "run_lab_progress_h4_state_checks_20261007.py",
    "audit_lab_progress_h4_spectral_proxy_20261007.py",
    "audit_lab_progress_h4_branch_correspondence_20261007.py",
    "run_lab_progress_hf_cap_checks_20261007.py",
    "run_lab_progress_hchain_transfer_20261007.py",
    "complete_lab_progress_hchain_transfer_20261007.py",
    "summarize_lab_progress_checks_20261007.py",
    "audit_lab_progress_handoff_20261007.py")]
CODE.append(ROOT / "review_tests/test_lab_progress_hchain_transfer_20261007.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def package_files() -> list[Path]:
    paths = set(DOCS + CODE)
    for directory in DIRECTORIES:
        paths.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return sorted(paths)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = "869806ff9995b76ef2786ca7b57b9acc02c2731f"
    source_registry = []
    for directory in DIRECTORIES[:3]:
        for source in read(directory / "protocol.json")["source_registry"]:
            assert len(source["origin_result_commit"]) == 40
            assert len(source["verified_snapshot_commit"]) == 40
            path = ROOT / source["path"]
            assert digest(path) == source["sha256"]
            blob = git("show", f"{source['verified_snapshot_commit']}:{source['path']}")
            assert hashlib.sha256(blob).hexdigest() == source["sha256"]
            assert git("merge-base", "--is-ancestor", source["origin_result_commit"], snapshot) == b""
            source_registry.append({**source, "used_by": str(directory.relative_to(ROOT))})

    manifest_counts = {}
    for directory in DIRECTORIES[:3]:
        manifest = read(directory / "manifest.json")
        if isinstance(manifest.get("files"), list):
            records = {str((directory / r["path"]).relative_to(ROOT)): r["sha256"] for r in manifest["files"]}
            assert manifest["manifest_self_excluded"]
        else:
            records = manifest.get("hashes", manifest.get("files"))
            assert str((directory / "manifest.json").relative_to(ROOT)) in manifest["self_excluded"]
        for name, expected in records.items():
            assert digest(ROOT / name) == expected, name
        manifest_counts[str(directory.relative_to(ROOT))] = len(records)

    links = []
    for doc in DOCS + [d / "report.md" for d in DIRECTORIES[:3]]:
        body = doc.read_text()
        assert body.count("$$") % 2 == 0, doc
        for target in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", body):
            if re.match(r"(?:https?://|#)", target):
                continue
            relative = target.split("#", 1)[0]
            destination = (doc.parent / relative).resolve()
            # Two audit outputs are created after this read-only validation.
            assert destination.is_file() or destination in (OUT / "handoff_checks.json", OUT / "manifest.json"), target
            links.append({"document": str(doc.relative_to(ROOT)), "target": target})
    outline = DOCS[0].read_text()
    slides = re.findall(r"^### Slide (\d+)：(.+)$", outline, re.M)
    index = re.findall(r"^\| (\d+) \| (.+) \|$", outline, re.M)
    assert slides == index and [int(n) for n, _ in slides] == list(range(1, 25))
    assert len(re.findall(r"^### A\d+：", outline, re.M)) == 3
    registry_ids = set(re.findall(r"^\| (E\d+) \|", outline, re.M))
    assert registry_ids == {f"E{n:02}" for n in range(1, 21)}
    widths = []
    for line in outline.splitlines():
        if line.startswith("|"):
            # TeX absolute values contain literal pipes inside math spans.
            width = len(re.sub(r"\$[^$]*\$", "MATH", line).split("|"))
            widths.append(width)
            assert width == widths[0], line
        else:
            widths = []

    self_excluded = [str((OUT / n).relative_to(ROOT)) for n in ("handoff_checks.json", "manifest.json")]
    paths = [p for p in package_files() if str(p.relative_to(ROOT)) not in self_excluded]
    allowed = {".json", ".csv", ".md", ".py", ".png", ".pdf", ""}
    for p in paths:
        assert p.suffix in allowed and ".runtime" not in p.parts and "__pycache__" not in p.parts, p
        assert p.stat().st_size < 50_000_000, p
    existing_linked_blobs = {}
    for link in links:
        path = (ROOT / link["document"]).parent / link["target"].split("#", 1)[0]
        path = path.resolve()
        if path in paths or path in (OUT / "handoff_checks.json", OUT / "manifest.json"):
            continue
        name = str(path.relative_to(ROOT))
        blob = git("show", f"{snapshot}:{name}")
        assert hashlib.sha256(blob).hexdigest() == digest(path), name
        existing_linked_blobs[name] = {"sha256": digest(path), "verified_snapshot_commit": snapshot,
                                      "origin_result_commit_source": "existing E01-E16 registry or participant source registry"}
    checks = {"schema": "lab_progress_additional_handoff_audit_v1",
              "source_registry": source_registry, "verified_input_snapshot": snapshot,
              "source_origin_commits_in_public_branch_history": True,
              "participant_manifest_counts": manifest_counts, "local_links": links,
              "existing_linked_blobs": existing_linked_blobs,
              "slide_count": len(slides), "appendix_count": 3, "evidence_id_count": len(registry_ids),
              "numeric_audit": "cross_checks.json", "scientific_computations_in_this_script": 0,
              "matrix_vector_pickle_runtime_publication_count": 0,
              "generated_python_bytecode_excluded": True,
              "audit_hash_self_excluded": self_excluded,
              "public_files": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p),
                                "bytes": p.stat().st_size} for p in paths],
              "handoff_commit": "supplied in final handoff; verify remote commit and all blobs after publication"}
    (OUT / "handoff_checks.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    all_paths = [p for p in package_files() if p != OUT / "manifest.json"]
    manifest = {"self_excluded": [str((OUT / "manifest.json").relative_to(ROOT))],
                "files": {str(p.relative_to(ROOT)): digest(p) for p in all_paths},
                "source_registry": "handoff_checks.json: origin_result_commit and verified_snapshot_commit are separate",
                "publication_policy": "scalar, code, protocol, report, figures only"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"public_files": len(all_paths) + 1, "source_entries": len(source_registry),
                      "links": len(links), "slides": len(slides), "participant_manifests": manifest_counts}))


if __name__ == "__main__":
    main()
