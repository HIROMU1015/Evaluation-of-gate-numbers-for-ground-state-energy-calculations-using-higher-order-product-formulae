from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import reduce
from pprint import pformat
from typing import Any

from .config import PFLabel, require_pf_label
from .pf_decomposition import iter_pf_steps
from .product_formula import _get_w_list


# Per-clique RZ layer depths generated from the original
# qiskit_tEvolutionOperator.estimate_rz_layers_from_grouping(...), using the
# physical-Z-support greedy layering path (bit_wise=False).
# Keys are H-chain lengths, e.g. 2 means H2.
# fmt: off
RZ_LAYER_DIR: dict[int, tuple[int, ...]] = {
    2: (4, 1),
    3: (8, 4, 4, 1, 1, 1, 1),
    4: (9, 5, 5, 4, 4, 4, 4, 4, 2, 3, 2, 2, 3),
    5: (
        12, 7, 7, 9, 7, 7, 9, 4, 4, 4, 4, 4, 2, 2, 4, 4, 4, 2, 2, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 3, 3, 2, 2, 3, 3, 2, 2, 2, 3,
        3, 2, 5,
    ),
    6: (
        15, 9, 9, 9, 9, 9, 9, 8, 6, 6, 6, 8, 6, 4, 4, 4, 6, 6, 4, 4,
        4, 6, 6, 4, 4, 4, 6, 8, 6, 6, 6, 8, 2, 2, 5, 2, 3, 5, 2, 2,
        3, 4, 5, 3, 5, 2, 2, 3, 2, 2, 2, 6, 2, 3, 3, 2, 6,
    ),
    7: (
        17, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 8, 8, 8, 6, 6, 8, 8, 4, 4,
        6, 4, 4, 8, 8, 4, 4, 6, 4, 4, 8, 6, 6, 8, 8, 8, 6, 4, 4, 8,
        4, 4, 6, 6, 4, 4, 8, 4, 4, 6, 8, 8, 8, 6, 6, 8, 5, 2, 2, 2,
        2, 6, 6, 2, 2, 3, 2, 3, 3, 2, 2, 3, 2, 5, 2, 2, 2, 2, 6, 4,
        2, 3, 2, 5, 3, 2, 3, 2, 3, 6, 2, 2, 6, 4, 2, 2, 2, 2, 4, 5,
        3, 3, 5, 4, 8,
    ),
    8: (
        21, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 4, 4,
        8, 4, 4, 8, 8, 4, 4, 8, 4, 4, 8, 8, 8, 8, 8, 8, 8, 4, 4, 8,
        4, 4, 8, 8, 4, 4, 8, 4, 4, 8, 8, 8, 8, 8, 8, 8, 5, 2, 4, 2,
        5, 6, 8, 2, 2, 7, 2, 6, 3, 2, 6, 3, 2, 6, 3, 3, 2, 2, 8, 6,
        6, 3, 2, 7, 3, 2, 5, 2, 6, 8, 2, 2, 6, 6, 2, 5, 2, 6, 4, 6,
        3, 3, 6, 4, 10,
    ),
    9: (
        23, 11, 11, 15, 15, 17, 13, 13, 11, 11, 15, 15, 17, 13, 13, 8,
        8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 8, 8, 6,
        6, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8, 8, 8, 8, 8, 6, 6, 8, 8, 8,
        8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 4, 4, 8, 8,
        8, 8, 8, 8, 8, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 2, 2, 2, 2,
        4, 6, 6, 3, 2, 3, 3, 2, 6, 2, 2, 4, 3, 5, 3, 2, 3, 6, 2, 3,
        2, 5, 2, 2, 2, 3, 5, 4, 2, 2, 3, 3, 7, 2, 2, 2, 2, 2, 6,
        2, 2, 2, 2, 6, 2, 2, 7, 2, 2, 2, 5, 4, 2, 2, 3, 3, 6, 2,
        3, 2, 6, 2, 2, 2, 3, 3, 3, 7, 3, 2, 3, 2, 6, 2, 2, 5, 2,
        2, 2, 4, 6, 6, 3, 2, 3, 2, 7, 3, 2, 6, 2, 3, 2, 4, 7, 8,
        5, 2, 3, 2, 4, 7, 8, 7, 3, 2, 4, 5, 3, 3, 5, 4, 7, 4, 10,
        4, 8,
    ),
    10: (
        26, 13, 13, 17, 17, 17, 13, 13, 13, 13, 17, 17, 17, 13, 13, 16,
        14, 14, 10, 10, 10, 14, 14, 16, 14, 8, 8, 8, 8, 8, 8, 8, 14,
        14, 8, 8, 8, 8, 8, 8, 8, 14, 10, 8, 8, 8, 8, 8, 8, 8, 10,
        10, 8, 8, 8, 8, 8, 8, 8, 10, 10, 8, 8, 8, 8, 8, 8, 8, 10,
        14, 8, 8, 8, 8, 8, 8, 8, 14, 14, 8, 8, 8, 8, 8, 8, 8, 14,
        16, 14, 14, 10, 10, 10, 14, 14, 16, 2, 3, 2, 4, 7, 10, 7, 3,
        2, 5, 3, 5, 6, 2, 5, 4, 5, 8, 3, 2, 6, 6, 2, 3, 4, 8, 2,
        2, 5, 3, 5, 4, 2, 5, 5, 3, 8, 2, 3, 2, 3, 3, 10, 4, 5, 4,
        5, 6, 2, 2, 9, 4, 5, 4, 5, 7, 2, 2, 3, 3, 7, 2, 3, 2, 6,
        4, 2, 5, 5, 3, 3, 6, 6, 2, 3, 4, 8, 2, 2, 5, 6, 2, 4, 4,
        6, 7, 3, 2, 3, 5, 7, 3, 2, 6, 2, 3, 2, 4, 7, 8, 5, 4, 6,
        4, 4, 10, 12, 7, 7, 6, 4, 8, 5, 6, 5, 5, 7, 4, 10, 8, 10,
    ),
    11: (
        27, 13, 13, 17, 17, 17, 17, 17, 13, 13, 13, 13, 17, 17, 17, 17,
        17, 13, 13, 16, 16, 16, 12, 12, 10, 10, 14, 14, 16, 16, 8, 8,
        8, 8, 10, 8, 8, 8, 8, 16, 16, 8, 8, 8, 8, 10, 8, 8, 8, 8,
        16, 12, 8, 8, 8, 8, 14, 8, 8, 8, 8, 12, 12, 8, 8, 8, 8, 14,
        8, 8, 8, 8, 12, 10, 10, 14, 14, 16, 16, 16, 12, 12, 10, 8,
        8, 8, 8, 16, 8, 8, 8, 8, 10, 10, 8, 8, 8, 8, 16, 8, 8, 8,
        8, 10, 14, 8, 8, 8, 8, 12, 8, 8, 8, 8, 14, 14, 8, 8, 8, 8,
        12, 8, 8, 8, 8, 14, 16, 16, 16, 12, 12, 10, 10, 14, 14, 16,
        5, 6, 4, 4, 10, 10, 7, 6, 6, 5, 6, 5, 7, 5, 5, 7, 8, 11,
        5, 4, 7, 6, 6, 7, 6, 8, 4, 5, 5, 7, 8, 4, 4, 7, 5, 5, 8,
        5, 6, 4, 5, 6, 10, 4, 6, 4, 6, 6, 5, 5, 9, 5, 6, 5, 7,
        8, 4, 4, 6, 7, 10, 5, 6, 4, 7, 7, 4, 5, 5, 5, 5, 6, 8,
        5, 6, 4, 8, 5, 4, 7, 8, 4, 4, 4, 6, 7, 7, 6, 6, 6, 8, 5,
        4, 6, 5, 7, 5, 6, 7, 8, 5, 4, 6, 4, 4, 10, 12, 7, 7, 6,
        8, 10, 5, 7, 5, 6, 7, 5, 10, 8, 13,
    ),
    12: (
        30, 13, 13, 17, 17, 17, 17, 17, 13, 13, 13, 13, 17, 17, 17, 17,
        17, 13, 13, 16, 16, 16, 12, 12, 12, 12, 16, 16, 16, 16, 8, 8,
        8, 8, 12, 8, 8, 8, 8, 16, 16, 8, 8, 8, 8, 12, 8, 8, 8, 8,
        16, 12, 8, 8, 8, 8, 16, 8, 8, 8, 8, 12, 12, 8, 8, 8, 8, 16,
        8, 8, 8, 8, 12, 12, 12, 16, 16, 16, 16, 16, 12, 12, 12, 8,
        8, 8, 8, 16, 8, 8, 8, 8, 12, 12, 8, 8, 8, 8, 16, 8, 8, 8,
        8, 12, 16, 8, 8, 8, 8, 12, 8, 8, 8, 8, 16, 16, 8, 8, 8, 8,
        12, 8, 8, 8, 8, 16, 16, 16, 16, 12, 12, 12, 12, 16, 16, 16,
        5, 6, 4, 4, 10, 10, 7, 6, 7, 6, 7, 6, 7, 6, 5, 7, 12, 12,
        6, 4, 7, 6, 7, 7, 6, 11, 4, 5, 5, 7, 9, 5, 4, 7, 7, 8,
        12, 6, 8, 5, 5, 7, 10, 6, 8, 4, 7, 6, 5, 7, 13, 5, 7,
        5, 8, 10, 4, 4, 9, 8, 10, 6, 7, 5, 8, 7, 6, 7, 5, 7, 7,
        9, 12, 8, 7, 6, 9, 6, 5, 7, 12, 6, 6, 6, 6, 7, 7, 7, 8,
        6, 13, 7, 6, 8, 8, 7, 7, 6, 7, 12, 7, 6, 7, 6, 6, 13, 12,
        7, 7, 6, 8, 11, 5, 7, 6, 6, 7, 5, 11, 8, 13,
    ),
    13: (
        33, 15, 15, 17, 17, 17, 17, 17, 17, 17, 17, 17, 15, 15, 17, 17,
        17, 17, 17, 17, 17, 17, 17, 16, 16, 16, 16, 16, 12, 12, 12, 12,
        16, 16, 16, 16, 16, 16, 14, 14, 10, 10, 12, 12, 12, 16, 16, 16,
        16, 16, 16, 14, 14, 10, 10, 12, 12, 12, 16, 16, 16, 16, 14, 14,
        8, 8, 14, 14, 16, 8, 8, 8, 8, 16, 16, 14, 14, 8, 8, 14, 14,
        16, 8, 8, 8, 8, 16, 12, 10, 10, 14, 14, 16, 16, 16, 16, 16,
        12, 12, 12, 12, 10, 10, 14, 14, 16, 16, 16, 16, 16, 12, 12,
        12, 12, 12, 16, 16, 16, 16, 16, 16, 16, 12, 12, 12, 12, 12, 8,
        8, 16, 16, 16, 8, 8, 8, 8, 12, 12, 12, 12, 8, 8, 16, 16, 16,
        8, 8, 8, 8, 12, 16, 16, 16, 8, 8, 12, 12, 12, 8, 8, 8, 8, 16,
        16, 16, 16, 8, 8, 12, 12, 12, 8, 8, 8, 8, 16, 16, 16, 16, 16,
        16, 12, 12, 12, 12, 16, 16, 16, 6, 5, 8, 11, 7, 4, 7, 5, 11,
        12, 7, 6, 6, 8, 5, 6, 8, 9, 5, 6, 9, 8, 8, 6, 8, 7, 8, 7,
        7, 8, 6, 13, 6, 7, 4, 5, 10, 4, 10, 5, 4, 7, 9, 9, 7, 7,
        6, 7, 7, 7, 7, 6, 6, 10, 8, 6, 6, 6, 4, 7, 7, 4, 7, 7, 11,
        10, 8, 8, 7, 7, 6, 5, 10, 5, 6, 11, 10, 5, 7, 7, 5, 10, 9,
        7, 7, 7, 10, 12, 9, 8, 7, 7, 6, 5, 6, 4, 7, 6, 11, 9, 6,
        6, 6, 4, 7, 8, 6, 7, 10, 11, 5, 8, 6, 7, 13, 4, 11, 5, 4,
        7, 11, 6, 7, 4, 5, 9, 5, 8, 8, 7, 8, 7, 9, 7, 5, 6, 7, 5,
        7, 7, 9, 6, 5, 8, 6, 6, 6, 8, 10, 7, 4, 7, 5, 10, 12, 7,
        8, 11, 9, 9, 5, 8, 7, 6, 10, 9, 11, 8, 14,
    ),
    14: (
        35, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17,
        17, 17, 17, 17, 17, 17, 17, 16, 16, 16, 16, 16, 14, 14, 14, 16,
        16, 16, 16, 16, 16, 16, 16, 14, 14, 12, 12, 12, 14, 14, 16, 16,
        16, 16, 16, 16, 14, 14, 12, 12, 12, 14, 14, 16, 16, 16, 16, 14,
        14, 8, 8, 16, 16, 16, 8, 8, 14, 14, 16, 16, 14, 14, 8, 8, 16,
        16, 16, 8, 8, 14, 14, 16, 14, 12, 12, 16, 16, 16, 16, 16, 16,
        16, 12, 12, 14, 14, 12, 12, 16, 16, 16, 16, 16, 16, 16, 12, 12,
        14, 14, 12, 12, 16, 16, 16, 16, 16, 16, 16, 12, 12, 14, 16, 14,
        14, 8, 8, 16, 16, 16, 8, 8, 14, 14, 16, 16, 14, 14, 8, 8, 16,
        16, 16, 8, 8, 14, 14, 16, 16, 16, 16, 14, 14, 12, 12, 12, 14,
        14, 16, 16, 16, 16, 16, 16, 14, 14, 12, 12, 12, 14, 14, 16, 16,
        16, 16, 16, 16, 16, 16, 14, 14, 14, 16, 16, 16, 16, 16, 6, 5,
        9, 11, 7, 5, 10, 8, 10, 12, 10, 6, 8, 11, 5, 6, 11, 10, 5,
        6, 9, 8, 11, 6, 11, 7, 11, 7, 7, 10, 6, 13, 6, 9, 4, 8, 13,
        4, 10, 5, 4, 8, 11, 9, 10, 10, 6, 11, 7, 10, 10, 8, 8, 10,
        8, 6, 9, 9, 4, 13, 10, 5, 10, 8, 11, 10, 8, 9, 7, 7, 6, 8,
        10, 9, 6, 14, 12, 5, 12, 7, 6, 10, 9, 7, 11, 7, 11, 12, 9,
        9, 8, 7, 6, 8, 7, 6, 7, 11, 11, 9, 6, 9, 10, 4, 13, 8, 9,
        10, 12, 11, 8, 12, 7, 11, 13, 6, 11, 6, 5, 10, 11, 6, 11, 5,
        10, 13, 7, 13, 8, 8, 11, 7, 9, 13, 6, 8, 12, 7, 7, 13, 13,
        6, 6, 8, 7, 7, 6, 10, 10, 7, 6, 11, 9, 14, 12, 13, 8, 11, 9,
        10, 6, 8, 7, 6, 10, 9, 11, 8, 13,
    ),
    15: (
        38, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17,
        17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 16, 16, 16, 16, 16,
        16, 16, 14, 14, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 12, 12,
        14, 12, 12, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 12, 12, 14,
        12, 12, 16, 16, 16, 16, 16, 16, 16, 16, 8, 8, 14, 14, 16, 16,
        16, 8, 8, 16, 16, 16, 16, 16, 16, 8, 8, 14, 14, 16, 16, 16, 8,
        8, 16, 16, 16, 16, 12, 12, 14, 14, 16, 16, 16, 16, 16, 16, 16,
        12, 12, 16, 16, 12, 12, 14, 14, 16, 16, 16, 16, 16, 16, 16, 12,
        12, 16, 14, 14, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 14,
        12, 12, 16, 16, 16, 16, 16, 16, 16, 16, 16, 12, 12, 14, 14, 12,
        12, 16, 16, 16, 16, 16, 16, 16, 16, 16, 12, 12, 14, 16, 16, 16,
        8, 8, 16, 16, 16, 16, 16, 8, 8, 14, 14, 16, 16, 16, 16, 8, 8,
        16, 16, 16, 16, 16, 8, 8, 14, 14, 16, 16, 16, 16, 16, 16, 12,
        12, 16, 12, 12, 14, 14, 16, 16, 16, 16, 16, 16, 16, 16, 12, 12,
        16, 12, 12, 14, 14, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 14,
        14, 16, 16, 16, 16, 16, 7, 11, 5, 7, 5, 4, 6, 10, 7, 6, 7, 5,
        9, 7, 11, 7, 7, 7, 9, 11, 7, 6, 5, 5, 8, 6, 6, 7, 6, 10, 6,
        10, 7, 6, 12, 7, 9, 6, 9, 8, 6, 5, 4, 9, 6, 4, 6, 5, 10, 8,
        4, 6, 7, 7, 6, 9, 7, 9, 6, 9, 6, 6, 6, 4, 6, 6, 6, 7, 6, 6,
        4, 10, 10, 4, 8, 8, 7, 5, 9, 7, 12, 4, 10, 5, 8, 6, 7, 7,
        7, 9, 5, 6, 7, 8, 4, 9, 7, 9, 7, 10, 5, 7, 6, 9, 5, 7, 7,
        5, 13, 6, 7, 5, 7, 6, 7, 6, 10, 4, 7, 7, 7, 10, 5, 7, 6, 7,
        7, 7, 8, 6, 10, 4, 7, 7, 6, 11, 5, 6, 5, 7, 8, 8, 10, 5, 6,
        6, 8, 4, 10, 11, 4, 8, 6, 8, 7, 7, 8, 8, 9, 5, 6, 6, 7, 6,
        6, 4, 13, 10, 4, 10, 8, 9, 5, 8, 8, 7, 8, 7, 9, 6, 8, 6, 7,
        6, 4, 13, 7, 4, 7, 6, 6, 8, 6, 4, 7, 6, 7, 8, 10, 8, 9, 6,
        8, 8, 7, 5, 4, 9, 7, 8, 10, 8, 6, 5, 6, 7, 6, 7, 7, 6, 9,
        6, 9, 7, 7, 8, 6, 7, 4, 10, 6, 10, 7, 7, 12, 5, 7, 5, 4, 5,
        12, 6, 11, 10, 11, 14, 5, 10, 6, 8, 9, 7, 7, 8, 12, 5, 10,
        11, 12, 6, 10, 6, 8, 9, 8, 7, 8, 11, 5, 12, 7, 10, 8, 11,
        9, 9, 5, 8, 7, 6, 9, 9, 12, 8, 14, 8, 16, 8, 13,
    ),
}
# fmt: on

DEFAULT_PF_RZ_LABELS: tuple[PFLabel, ...] = (
    "2nd",
    "4th",
    "8th(Morales)",
    "10th(Morales)",
    "8th(Yoshida)",
    "4th(new_3)",
    "4th(new_2)",
)


def _normalize_h_chain(h_chain: int | str) -> int:
    if isinstance(h_chain, str):
        if not h_chain.startswith("H"):
            raise KeyError(h_chain)
        h_chain = int(h_chain[1:])
    if h_chain not in RZ_LAYER_DIR:
        raise KeyError(h_chain)
    return h_chain


def _first_coeff(term: Any) -> complex:
    for coeff in term.terms.values():
        return coeff
    return 0.0


def classify_monomial(term: Any) -> list[tuple[str, tuple[int, ...], complex]]:
    """
    Classify one grouped FermionOperator term into the A/n monomials used for
    the RZ-layer estimate.
    """
    if not term.terms:
        return []

    keys_all = list(term.terms.keys())
    keys = [key for key in keys_all if len(key) > 0]
    if not keys:
        return []

    if len(keys) == 1:
        ops = keys[0]
        if len(ops) == 2:
            i1, a1 = ops[0]
            i2, a2 = ops[1]
            if i1 == i2 and a1 != a2:
                return [("n1", (i1,), _first_coeff(term))]

        if len(ops) == 4:
            idx = [i for i, _ in ops]
            if idx[0] == idx[1] and idx[2] == idx[3]:
                return [("n2", (idx[0], idx[2]), _first_coeff(term))]

    if len(keys) == 2:
        if all(len(key) == 2 for key in keys):
            idx_sets = {tuple(sorted(i for i, _ in key)) for key in keys}
            if len(idx_sets) == 1:
                p, q = list(idx_sets)[0]
                return [("A", (p, q), _first_coeff(term))]

        if all(len(key) == 4 for key in keys):
            counts: Counter[int] = Counter()
            for key in keys:
                for i, _ in key:
                    counts[i] += 1
            modes = list(counts)
            if len(modes) == 3:
                r = max(modes, key=lambda m: counts[m])
                p, q = [m for m in modes if m != r]
                return [("A*n", (p, q, r), _first_coeff(term))]

    if all(len(key) == 4 for key in keys):
        set_to_key = {}
        for key in keys:
            idx_set = frozenset(i for i, _ in key)
            if len(idx_set) not in (3, 4):
                continue
            set_to_key.setdefault(idx_set, key)

        if set_to_key:
            out = []
            for idx_set, rep_key in set_to_key.items():
                if len(idx_set) == 4:
                    p, q, r, s = sorted(idx_set)
                    out.append(("A*A", (p, q, r, s), term.terms[rep_key]))
                elif len(idx_set) == 3:
                    counts = Counter(i for i, _ in rep_key)
                    r_idx = max(counts, key=counts.get)
                    others = sorted(x for x in idx_set if x != r_idx)
                    if len(others) == 2 and counts[r_idx] >= 2:
                        p, q = others
                        out.append(("A*n", (p, q, r_idx), term.terms[rep_key]))
            return out

    return [("unknown", (), _first_coeff(term))]


def _add_zstring(
    z_terms: defaultdict[frozenset[int], complex],
    support: frozenset[int],
    coeff: complex,
) -> None:
    if support:
        z_terms[support] += coeff


def expand_diagonal_monomial(
    kind: str,
    idx: tuple[int, ...],
    coeff: complex,
    z_terms: defaultdict[frozenset[int], complex],
) -> None:
    """Expand an A/n monomial to Z-string supports."""
    if kind == "n1":
        (i,) = idx
        c = coeff / 2.0
        _add_zstring(z_terms, frozenset({i}), -c)
    elif kind == "n2":
        i, j = idx
        c = coeff / 4.0
        _add_zstring(z_terms, frozenset({i}), -c)
        _add_zstring(z_terms, frozenset({j}), -c)
        _add_zstring(z_terms, frozenset({i, j}), c)
    elif kind == "A":
        p, q = idx
        c = coeff / 2.0
        _add_zstring(z_terms, frozenset({p}), -c)
        _add_zstring(z_terms, frozenset({q}), c)
    elif kind == "A*n":
        p, q, r = idx
        c = coeff / 4.0
        _add_zstring(z_terms, frozenset({p}), -c)
        _add_zstring(z_terms, frozenset({q}), c)
        _add_zstring(z_terms, frozenset({p, r}), c)
        _add_zstring(z_terms, frozenset({q, r}), -c)
    elif kind == "A*A":
        p, q, r, s = idx
        expand_diagonal_monomial("n2", (p, r), coeff, z_terms)
        expand_diagonal_monomial("n2", (p, s), -coeff, z_terms)
        expand_diagonal_monomial("n2", (q, r), -coeff, z_terms)
        expand_diagonal_monomial("n2", (q, s), coeff, z_terms)


def extract_z_terms_for_group(
    group_terms: Sequence[Any],
    coeff_tol: float = 0.0,
) -> dict[frozenset[int], complex]:
    """Convert one A/n FermionOperator group into Z-string supports."""
    z_terms: defaultdict[frozenset[int], complex] = defaultdict(complex)

    for term in group_terms:
        for kind, idx, coeff in classify_monomial(term):
            if kind != "unknown":
                expand_diagonal_monomial(kind, idx, coeff, z_terms)

    # Parent code kept exactly-zero supports when coeff_tol == 0.0. Those
    # supports still affect greedy coloring, so preserve that behavior.
    if coeff_tol > 0.0:
        return {
            support: coeff
            for support, coeff in z_terms.items()
            if abs(coeff) > coeff_tol
        }
    return dict(z_terms)


def greedy_layering(supports: Iterable[frozenset[int]]) -> list[list[frozenset[int]]]:
    """Greedy graph coloring for Z strings that conflict on shared qubits."""
    layers: list[list[frozenset[int]]] = []

    for support in supports:
        for layer in layers:
            if all(support.isdisjoint(other) for other in layer):
                layer.append(support)
                break
        else:
            layers.append([support])

    return layers


def extract_z_like_terms_from_qubit_group(
    qubit_group: Any,
    coeff_tol: float = 0.0,
) -> dict[frozenset[int], complex]:
    """
    Extract Pauli supports from one QubitOperator group.

    For H2/H3 this follows the parent code path: X/Y supports are counted as
    Z-like supports after basis-change Clifford gates.
    """
    z_terms: dict[frozenset[int], complex] = {}

    for qubit_term, coeff in qubit_group.terms.items():
        if not qubit_term:
            continue
        support = frozenset(q for q, _ in qubit_term)
        z_terms[support] = z_terms.get(support, 0.0) + coeff

    return {
        support: coeff
        for support, coeff in z_terms.items()
        if abs(coeff) > coeff_tol
    }


def _hchain_integrals(
    h_chain: int | str,
    *,
    distance: float | None = None,
    basis: str | None = None,
):
    """Run PySCF and return constants/integrals needed by the grouper."""
    import numpy as np
    import pyscf
    from pyscf import gto, scf

    from .chemistry_hamiltonian import geo
    from .config import DEFAULT_BASIS

    h = _normalize_h_chain(h_chain)
    if basis is None:
        basis = DEFAULT_BASIS

    geometry, multiplicity, charge = geo(h, distance)
    mol = gto.Mole()
    mol.atom = geometry
    mol.basis = basis
    mol.spin = multiplicity - 1
    mol.charge = charge
    mol.symmetry = False
    mol.build()

    mf = scf.RHF(mol)
    mf.verbose = 0
    mf.kernel()

    mo = mf.mo_coeff
    h_core = mf.get_hcore()
    one_body_integrals = reduce(np.dot, (mo.T, h_core, mo))
    eri = pyscf.ao2mo.kernel(mf.mol, mo)
    eri = pyscf.ao2mo.restore(1, eri, mo.shape[0])
    two_body_integrals = np.asarray(eri.transpose(0, 2, 3, 1), order="C")
    return mf.energy_nuc(), one_body_integrals, two_body_integrals


def _layers_from_z_terms(
    z_terms: Mapping[frozenset[int], complex],
    coeff_tol: float = 0.0,
) -> list[list[frozenset[int]]]:
    layers_all = greedy_layering(z_terms.keys())
    return [
        layer
        for layer in layers_all
        if any(abs(z_terms[support]) > coeff_tol for support in layer)
    ]


def estimate_rz_layers_from_grouping(
    h_chain: int | str,
    *,
    coeff_tol: float = 0.0,
    distance: float | None = None,
    basis: str | None = None,
    validation: bool = False,
) -> tuple[
    list[int],
    list[list[list[frozenset[int]]]],
    list[dict[frozenset[int], complex]],
]:
    """
    Generate per-group RZ layers from scratch for one H-chain.

    This is the current-repo version of the parent
    qiskit_tEvolutionOperator.estimate_rz_layers_from_grouping(...), limited to
    the physical-Z-support greedy-layering path used for RZ_layer_dir.
    """
    h = _normalize_h_chain(h_chain)
    constant, one_body_integrals, two_body_integrals = _hchain_integrals(
        h,
        distance=distance,
        basis=basis,
    )
    n_orb = one_body_integrals.shape[0]

    n_layers_list: list[int] = []
    layers_list: list[list[list[frozenset[int]]]] = []
    z_terms_list: list[dict[frozenset[int], complex]] = []

    if n_orb <= 3:
        from openfermion.transforms import get_fermion_operator, jordan_wigner

        from .Almost_optimal_grouping import make_spinorb_ham_upthendown_order
        from .chemistry_hamiltonian import min_hamiltonian_grouper

        interaction = make_spinorb_ham_upthendown_order(
            constant,
            one_body_integrals,
            two_body_integrals,
            validation=validation,
        )
        ham_qubit = jordan_wigner(get_fermion_operator(interaction))
        grouped_ops, _ = min_hamiltonian_grouper(ham_qubit, ham_name=f"H{h}")

        for q_group in grouped_ops:
            z_terms_g = extract_z_like_terms_from_qubit_group(
                q_group,
                coeff_tol=coeff_tol,
            )
            layers_g = _layers_from_z_terms(z_terms_g, coeff_tol=coeff_tol)
            n_layers_list.append(len(layers_g))
            layers_list.append(layers_g)
            z_terms_list.append(z_terms_g)

        return n_layers_list, layers_list, z_terms_list

    from openfermion.transforms import jordan_wigner

    from .Almost_optimal_grouping import Almost_optimal_grouper

    grouper = Almost_optimal_grouper(
        const=constant,
        one_body_integrals=one_body_integrals,
        two_body_integrals=two_body_integrals,
        fermion_qubit_mapping=jordan_wigner,
        validation=validation,
    )

    for group_terms in grouper.group_term_list:
        z_terms_g = extract_z_terms_for_group(group_terms, coeff_tol=coeff_tol)
        layers_g = _layers_from_z_terms(z_terms_g, coeff_tol=coeff_tol)
        n_layers_list.append(len(layers_g))
        layers_list.append(layers_g)
        z_terms_list.append(z_terms_g)

    return n_layers_list, layers_list, z_terms_list


def generate_rz_layer_dir(
    h_chains: Iterable[int | str] | None = None,
    *,
    coeff_tol: float = 0.0,
    distance: float | None = None,
    basis: str | None = None,
    validation: bool = False,
) -> dict[int, tuple[int, ...]]:
    """Generate RZ_layer_dir itself by running PySCF, grouping, and coloring."""
    if h_chains is None:
        h_chains = sorted(RZ_LAYER_DIR)

    generated: dict[int, tuple[int, ...]] = {}
    for h_chain in h_chains:
        h = _normalize_h_chain(h_chain)
        n_layers, _, _ = estimate_rz_layers_from_grouping(
            h,
            coeff_tol=coeff_tol,
            distance=distance,
            basis=basis,
            validation=validation,
        )
        generated[h] = tuple(n_layers)
    return generated


def assert_generated_rz_layer_dir_matches_static(
    generated: Mapping[int, Sequence[int]],
) -> None:
    """Raise if generated per-group RZ layers differ from bundled values."""
    for h_chain, layers in generated.items():
        expected = RZ_LAYER_DIR.get(h_chain)
        if tuple(layers) != expected:
            raise AssertionError(
                f"H{h_chain}: generated {tuple(layers)}, expected {expected}."
            )


def group_rz_layers(h_chain: int | str) -> tuple[int, ...]:
    """Return per-group RZ layer depths for an H-chain."""
    return RZ_LAYER_DIR[_normalize_h_chain(h_chain)]


def calculate_pf_rz_layer_from_group_layers(
    group_layers: Sequence[int],
    pf_label: PFLabel,
) -> int:
    """Sum per-group RZ depths over one product-formula unitary."""
    label = require_pf_label(pf_label)
    weights = _get_w_list(label)
    return sum(group_layers[group_idx] for group_idx, _ in iter_pf_steps(len(group_layers), weights))


def calculate_pf_rz_layer(h_chain: int | str, pf_label: PFLabel) -> int:
    """Return the RZ layer depth of one PF step for one H-chain."""
    return calculate_pf_rz_layer_from_group_layers(group_rz_layers(h_chain), pf_label)


def build_pf_rz_layer_table(
    h_chains: Iterable[int | str] | None = None,
    pf_labels: Sequence[PFLabel] = DEFAULT_PF_RZ_LABELS,
) -> dict[str, dict[str, int]]:
    """Build the table with the same shape as config.PF_RZ_LAYER."""
    if h_chains is None:
        h_chains = sorted(RZ_LAYER_DIR)
    labels = tuple(require_pf_label(label) for label in pf_labels)
    table: dict[str, dict[str, int]] = {}
    for h_chain in h_chains:
        h = _normalize_h_chain(h_chain)
        table[f"H{h}"] = {
            label: calculate_pf_rz_layer(h, label)
            for label in labels
        }
    return table


def build_pf_rz_layer_table_from_group_layers(
    group_layer_dir: Mapping[int, Sequence[int]],
    pf_labels: Sequence[PFLabel] = DEFAULT_PF_RZ_LABELS,
) -> dict[str, dict[str, int]]:
    """Build a PF RZ table from a generated RZ_layer_dir-like mapping."""
    labels = tuple(require_pf_label(label) for label in pf_labels)
    return {
        f"H{h_chain}": {
            label: calculate_pf_rz_layer_from_group_layers(group_layers, label)
            for label in labels
        }
        for h_chain, group_layers in sorted(group_layer_dir.items())
    }


def assert_matches_config(
    table: Mapping[str, Mapping[str, int]] | None = None,
) -> None:
    """Raise if generated RZ layer entries differ from config.PF_RZ_LAYER."""
    from .config import PF_RZ_LAYER

    generated = build_pf_rz_layer_table() if table is None else table
    for h_chain, row in generated.items():
        if h_chain not in PF_RZ_LAYER:
            raise AssertionError(f"{h_chain} is not present in config.PF_RZ_LAYER.")
        for pf_label, value in row.items():
            expected = PF_RZ_LAYER[h_chain].get(pf_label)
            if value != expected:
                raise AssertionError(
                    f"{h_chain} {pf_label}: generated {value}, expected {expected}."
                )


def format_pf_rz_layer_table(
    table: Mapping[str, Mapping[str, int]] | None = None,
) -> str:
    """Format a PF RZ layer table as a Python literal."""
    if table is None:
        table = build_pf_rz_layer_table()
    return pformat(dict(table), sort_dicts=False, width=120)


def format_rz_layer_dir(
    rz_layer_dir: Mapping[int, Sequence[int]],
) -> str:
    """Format an RZ_layer_dir mapping as a Python literal."""
    return pformat(
        {h_chain: tuple(layers) for h_chain, layers in sorted(rz_layer_dir.items())},
        sort_dicts=False,
        width=120,
    )


def _parse_h_chains(values: Sequence[str] | None) -> list[int | str] | None:
    if not values:
        return None
    return [value if value.startswith("H") else int(value) for value in values]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate PF RZ layer depths from per-group RZ layers."
    )
    parser.add_argument(
        "--h-chain",
        nargs="*",
        help="H-chain labels or integers to output, e.g. H2 H15 or 2 15.",
    )
    parser.add_argument(
        "--pf-label",
        nargs="*",
        default=list(DEFAULT_PF_RZ_LABELS),
        help="Product-formula labels to output.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Also assert that the generated table matches config.PF_RZ_LAYER.",
    )
    parser.add_argument(
        "--generate-rz-layer-dir",
        action="store_true",
        help="Generate RZ_layer_dir itself from PySCF, grouping, and greedy coloring.",
    )
    parser.add_argument(
        "--coeff-tol",
        type=float,
        default=0.0,
        help="Coefficient tolerance used when dropping near-zero Z strings.",
    )
    parser.add_argument(
        "--validation",
        action="store_true",
        help="Enable Almost_optimal_grouper validation while generating RZ_layer_dir.",
    )
    args = parser.parse_args(argv)

    if args.generate_rz_layer_dir:
        rz_layer_dir = generate_rz_layer_dir(
            h_chains=_parse_h_chains(args.h_chain),
            coeff_tol=args.coeff_tol,
            validation=args.validation,
        )
        print(format_rz_layer_dir(rz_layer_dir))
        if args.check:
            assert_generated_rz_layer_dir_matches_static(rz_layer_dir)
        return 0

    table = build_pf_rz_layer_table(
        h_chains=_parse_h_chains(args.h_chain),
        pf_labels=args.pf_label,
    )
    print(format_pf_rz_layer_table(table))
    if args.check:
        assert_matches_config(table if args.h_chain or args.pf_label else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
