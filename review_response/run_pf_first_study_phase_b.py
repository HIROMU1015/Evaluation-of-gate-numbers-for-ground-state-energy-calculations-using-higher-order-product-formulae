"""CLI/schema wrapper for the preregistered Phase B truth scorer."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence

from review_response import _pf_first_study_phase_b_base as _base
from review_response._pf_first_study_phase_b_base import (  # noqa: F401
    DEFAULT_OUTPUT,
    _verify_phase_a,
    run,
)


def _write_csv_union(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


_base.write_csv = _write_csv_union


def main() -> int:
    return _base.main()


if __name__ == "__main__":
    raise SystemExit(main())
