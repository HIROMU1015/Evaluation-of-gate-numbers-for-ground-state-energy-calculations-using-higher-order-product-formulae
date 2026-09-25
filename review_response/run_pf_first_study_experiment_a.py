"""CLI for the preregistered first-study Experiment A validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_response._pf_first_study_experiment_a_support import (
    DEFAULT_OUTPUT,
    DEFAULT_PROTOCOL,
)
from review_response.pf_first_study_experiment_a import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    protocol_path = arguments.protocol
    if not protocol_path.is_absolute():
        protocol_path = project_root / protocol_path
    output_dir = arguments.output
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    audit = run(project_root, protocol_path, output_dir)
    print(
        json.dumps(
            {"status": audit["status"], "checks": audit["checks"]}, indent=2
        )
    )
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
