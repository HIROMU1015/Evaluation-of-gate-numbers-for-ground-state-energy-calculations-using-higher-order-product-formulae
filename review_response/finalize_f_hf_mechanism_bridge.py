"""Attach test results and refreshed hashes to an HF bridge manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--related-tests-exit-code", type=int, required=True)
    parser.add_argument("--all-review-tests-exit-code", type=int, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    result = {
        "related_tests_exit_code": args.related_tests_exit_code,
        "related_tests_passed": args.related_tests_exit_code == 0,
        "all_review_tests_exit_code": args.all_review_tests_exit_code,
        "all_review_tests_passed": args.all_review_tests_exit_code == 0,
    }
    (output / "test_results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tests"] = result
    manifest["artifact_hashes"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE"}
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
