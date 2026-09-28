from __future__ import annotations

import json
import math
from pathlib import Path

from run_pf_r1_reorientation_d0 import arg_minus_imag, build_rows, gamma_required

ROOT = Path(__file__).resolve().parents[1]

def test_gamma_required_matches_frozen_r1_arithmetic() -> None:
    epsilon = 0.00015936001019904
    got = gamma_required(epsilon, -2.423348313074747e-06, 4.994256553637891e-06)
    assert got == 1.016654654156445
    assert max(1.0, got) == got

def test_arg_minus_imag_is_small_angle_only_not_proxy_fix() -> None:
    time = 0.20163872995835974
    real = 0.9999997603131261
    imag = -4.886410608362368e-07
    got = arg_minus_imag(real, imag, time)
    assert abs(got - (-5.808449475385022e-13)) <= 1e-24

def test_protocol_freezes_six_coordinates_and_no_authorization() -> None:
    protocol = json.loads((ROOT / "review_response/pf_spectral_information_pilot_protocol_draft.json").read_text())
    assert protocol["status"] == "d0_protocol_frozen_d1_not_authorized"
    assert len(protocol["scope"]["coordinates"]) == 6
    assert protocol["definitions"]["top_k"]["values"] == [1, 2, 4, 8, "all"]
    assert protocol["compression_gate"]["low_dimensional_k_maximum"] == 4
    assert protocol["authorization"]["d1_spectral_pilot_authorized"] is False
    assert protocol["authorization"]["d2_authorized"] is False

def test_real_r1_read_only_derivation_counts_and_reference_values() -> None:
    coordinates, strategies, summary = build_rows(ROOT)
    assert len(coordinates) == 10
    assert len(strategies) == 16
    assert summary["maximum_local_cisd_gamma_required"] == 1.0981387382626462
    assert summary["maximum_absolute_arg_minus_imag_hartree"] == 1.6216300641170266e-11
    assert summary["posthoc_gamma_1_10_safe_strategy_rows"] == 16
    assert all(row["posthoc_gamma_1_10_is_adopted_method"] is False for row in strategies)
