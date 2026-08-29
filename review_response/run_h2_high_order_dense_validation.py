"""Run a dense H2 direct-diagonalization check for the new high-order PFs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import validate_perturbation_orders_h2 as validation


YP8_LABEL = "8th(Morales-YP8m8)"
QIC10_LABEL = "10th(Morales-QIC-m17)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yp8-start", type=float, default=0.35)
    parser.add_argument("--yp8-stop", type=float, default=1.20)
    parser.add_argument("--yp8-points", type=int, default=49)
    parser.add_argument("--qic10-start", type=float, default=0.55)
    parser.add_argument("--qic10-stop", type=float, default=1.25)
    parser.add_argument("--qic10-points", type=int, default=57)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation.LABEL_TIMES = {
        YP8_LABEL: np.geomspace(args.yp8_start, args.yp8_stop, args.yp8_points),
        QIC10_LABEL: np.geomspace(
            args.qic10_start, args.qic10_stop, args.qic10_points
        ),
    }
    payload = validation.run_validation()
    payload["time_grid_kind"] = "independent_geometric_grid_per_pf"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
