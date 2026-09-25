"""CLI/schema/training-boundary wrapper for first-study Phase A."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence

from review_response import _pf_first_study_phase_a_base as _base
from review_response._pf_first_study_phase_a_base import (  # noqa: F401
    DEFAULT_OUTPUT,
    _experiment_c_inputs,
    _proxy_rows_for_signed_times,
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


_original_mechanism_models = _base._mechanism_models


def _mechanism_models_with_frozen_training_boundary(
    rows: Sequence[dict[str, Any]],
    state_ids: Sequence[str],
    maximum_condition: float,
) -> list[dict[str, Any]]:
    if rows and rows[0]["experiment_id"] == "B":
        training = {0.10, 0.15, 0.20, 0.25, 0.30}
        rows = [
            row for row in rows if float(row["absolute_time"]) in training
        ]
    return _original_mechanism_models(rows, state_ids, maximum_condition)


_base.write_csv = _write_csv_union
_base._mechanism_models = _mechanism_models_with_frozen_training_boundary


def main() -> int:
    return _base.main()


if __name__ == "__main__":
    raise SystemExit(main())
