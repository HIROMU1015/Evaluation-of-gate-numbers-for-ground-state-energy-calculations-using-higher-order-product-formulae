"""Complete a numerical reproduction-check correction without changing science.

The original runner is preserved byte-for-byte. The singleton-versus-block
expm_multiply roundoff is checked in observable units, and the operational CISD
model remains the original frozen model. Only a missing H6 Yoshida truth grid is
computed; existing grids and predictions are never recomputed or overwritten.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
import time

import numpy as np

from review_response import run_lab_progress_hchain_transfer_20261007 as original


OLD_CHECK = '''    if np.max(np.abs(np.asarray(models["cisd"]["coefficients"]) - prediction["model"]["coefficients"])) > 1e-12:
        raise ValueError("CISD frozen model reproduction failed")'''
NEW_CHECK = '''    saved_training = [row["proxy_imag_hartree"] for row in prediction["training_points"]]
    if np.max(np.abs(np.asarray(training_values["cisd"]) - saved_training)) > 1e-12:
        raise ValueError("CISD frozen training observable reproduction failed")
    models["cisd"] = prediction["model"]'''


def corrected_truth(task):
    original.verify_protocol()
    marker = json.loads((original.OUT / "IMPLEMENTATION_CORRECTION_FROZEN.json").read_text())
    if marker["correction_runner_sha256"] != original.sha(__file__):
        raise ValueError("correction source changed")
    source = inspect.getsource(original.truth_formula)
    if source.count(OLD_CHECK) != 1:
        raise ValueError("unexpected original reproduction check")
    corrected = source.replace(OLD_CHECK, NEW_CHECK)
    scope = dict(vars(original))
    exec(compile(corrected, __file__, "exec"), scope)
    return scope["truth_formula"](task)


def run():
    started = time.perf_counter()
    protocol = original.verify_protocol()
    path = original.OUT / "IMPLEMENTATION_CORRECTION_FROZEN.json"
    if path.exists():
        raise FileExistsError("no automatic correction rerun")
    diagnostic = json.loads((original.OUT / "implementation_reproduction_diagnostic.json").read_text())
    if diagnostic["max_training_proxy_difference"] >= 1e-12:
        raise ValueError("observable difference is not roundoff")
    existing = sorted(original.OUT.glob("*/truth_*.json"))
    original.write_json(path, {
        "utc": original.utc(), "protocol_sha256": original.sha(original.OUT / "protocol.json"),
        "original_runner_sha256": original.sha(original.__file__), "correction_runner_sha256": original.sha(__file__),
        "prediction_freeze_sha256": original.sha(original.OUT / "PREDICTIONS_FROZEN.json"),
        "reason": "small fit coordinates amplify singleton/block proxy roundoff in dimensional fit coefficients",
        "change": "check the five training proxies in Ha at 1e-12; use original frozen CISD model unchanged",
        "new_scientific_conditions": 0, "new_models_or_thresholds_in_operational_selection": 0,
        "missing_truth_scope": [{"system": "H6", "formula": "yoshida4", "candidate_count": 401}],
        "existing_truth_sha256": {str(p.relative_to(original.OUT)): original.sha(p) for p in existing},
        "implementation_diagnostic_sha256": original.sha(original.OUT / "implementation_reproduction_diagnostic.json"),
        "old_original_runner_unchanged": True,
    })
    if (original.OUT / "H6/truth_yoshida4.json").exists():
        raise FileExistsError("missing grid already exists")
    corrected_truth(("H6", "yoshida4"))
    original.write_json(original.OUT / "correction_execution.json", {"elapsed_seconds": time.perf_counter() - started,
                                                                    "correction_frozen_sha256": original.sha(path),
                                                                    "new_direct_candidate_count": 401,
                                                                    "original_prediction_or_rule_changed": False})


if __name__ == "__main__":
    run()
