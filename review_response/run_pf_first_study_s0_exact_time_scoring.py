"""Public entry point for first-study S0 exact-time scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from review_response import _pf_first_study_s0_exact_time_scoring_base as _base
from review_response._pf_first_study_s0_exact_time_scoring_base import *  # noqa: F401,F403


_original_verify_frozen_inputs = _base._verify_frozen_inputs


def _verify_with_canonical_constant_keys(
    practical_root: Path, first_study_protocol: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol, predictions = _original_verify_frozen_inputs(
        practical_root, first_study_protocol
    )
    # The frozen JSON stores these shared values under ``constants``.  The
    # implementation body consumes a local resource view so no protocol file,
    # prediction, threshold, or selection is changed.
    protocol["resource_metrics"]["target_error_hartree"] = protocol["constants"][
        "target_error_hartree"
    ]
    protocol["resource_metrics"]["qpe_beta"] = protocol["constants"]["qpe_beta"]
    protocol["resource_metrics"]["budget_multipliers"] = protocol["constants"][
        "budget_multipliers"
    ]
    return protocol, predictions


_base._verify_frozen_inputs = _verify_with_canonical_constant_keys

run = _base.run
main = _base.main


if __name__ == "__main__":
    main()
