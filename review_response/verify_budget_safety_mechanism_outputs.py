"""Independent Decimal arithmetic/output provenance audit; no acquisition imports."""
import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import subprocess

DOCS = "docs/second_study_v2/budget_safety_mechanism_20261005"
OUT = "artifacts/budget_safety_mechanism_20261005"
D = Decimal.from_float


def verify(root):
    result = json.loads((root / OUT / "analysis.json").read_text())
    tables = result["tables"]
    eps = D(.00015936001019904)
    beta = D(1.2)
    checks = 0
    def check(condition, label):
        nonlocal checks
        if not condition:
            raise ValueError(label)
        checks += 1
    def near(x, y, label, tolerance=Decimal("1e-15")):
        check(abs(D(x) - y) <= tolerance, label)
    with localcontext() as ctx:
        ctx.prec = 60
        for r in tables["budget_safety_capacity"]:
            e, c, gamma, t, b = (D(r[k]) for k in ("e_hartree", "c_hartree", "gamma", "time", "frozen_or_diagnostic_budget"))
            u = e - c
            margin = (1 - 1 / gamma) * (eps - c)
            slack = margin - u
            near(r["underestimation_hartree"], u, "underestimation")
            near(r["margin_hartree"], margin, "margin")
            near(r["safety_slack_hartree"], slack, "slack")
            near(r["gamma_req"], (eps - c) / (eps - e), "gamma_req", Decimal("1e-12"))
            check(r["safe_arithmetic"] == (e + beta * r["K"] / (t * b) <= eps), "raw budget safety")
            if r["gamma"] == 1:
                check(r["underestimation_to_margin_ratio"] is None, "gamma1 ratio must be undefined")
                check(r["ratio_status"] == "undefined_zero_margin_use_slack", "gamma1 label")
        for r in tables["selected_frozen_budget_safety"]:
            slack = eps - D(r["e_hartree"]) - beta * r["K"] / (D(r["time"]) * D(r["frozen_budget"]))
            near(r["safety_slack_hartree"], slack, "frozen decision slack")
            check(r["saved_raw_safe"] == (slack >= 0), "frozen decision flag")
            check(not r["budget_changed"], "budget immutable")
        for r in tables["width_decision_windows"]:
            m = next(x for x in tables["m1_point_width_abstention"] if x["candidate_id"] == r["candidate_id"]
                     and x["condition"] == r["condition"])
            win = eps - abs(D(m["delta_M_signed_hartree"])) - beta * r["K"] / (
                D(r["time"]) * (1 - D(r["eta"])) * D(r["comparator_budget"]))
            near(r["w_win_hartree"], win, "width window")
            check(not r["window_is_operational_success_claim"], "window diagnostic scope")
        for r in tables["m1_reference_error_decomposition"]:
            if "PF_energy_error_signed_hartree" in r:
                residual = D(r["shift_error_signed_hartree"]) - (
                    D(r["PF_energy_error_signed_hartree"]) - D(r["H_reference_error_signed_hartree"]))
                near(r["closure_rounding_residual_hartree"], residual, "component closure")
                check(abs(residual) <= D(r["closure_rounding_allowance_hartree"]), "component rounding allowance")
            else:
                check(r["decomposition_status"].startswith("indeterminate"), "missing energy origin must not be filled")
        model_ratio = Decimal(".5") * (1 - Decimal(".5") ** 4 / 5) / (Decimal(".8") * (1 - Decimal(".8") ** 4 / 5))
        for r in tables["hchain_model_vs_observation"]:
            near(r["leading_model_budget_ratio"], model_ratio, "leading model")
            check(r["saved_B2_safe"] and not r["difference_is_independent_causal_component"], "model/empirical separation")
    expected = {"budget_safety_capacity": 150, "selected_frozen_budget_safety": 64,
                "m1_point_width_abstention": 30, "width_decision_windows": 300,
                "m1_reference_error_decomposition": 30, "oracle_headroom_by_contract": 10,
                "same_time_oracle_headroom": 30, "hchain_model_vs_observation": 6}
    for name, count in expected.items():
        check(len(tables[name]) == count, "table count " + name)
    for name, rows in tables.items():
        with (root / OUT / (name + ".csv")).open() as stream:
            csv_rows = list(csv.DictReader(stream))
        check(len(csv_rows) == len(rows), "CSV rows " + name)
        for saved, encoded in zip(rows, csv_rows):
            for key, value in saved.items():
                formatted = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else "" if value is None else str(value)
                check(encoded[key] == formatted, "CSV scalar agrees with JSON " + name + "/" + key)
    c0 = list(csv.DictReader((root / "artifacts/pf_post_d2a_width_design_readonly_20260929/budget_headroom_and_widths.csv").open()))
    for source in c0:
        row = next(r for r in tables["same_time_oracle_headroom"] if r["condition"] == source["condition"] and r["time_hex"] == source["time_hex"])
        near(row["S_max_same_time"], D(float(source["S_max_same_time"])), "C0 same-time headroom reproduced")
        window = next(r for r in tables["width_decision_windows"] if r["condition"] == source["condition"]
                      and r["time_hex"] == source["time_hex"] and r["eta"] == 0
                      and r["comparator_scope"] == "same_time_main_baseline_gamma1.02_not_condition_B0")
        near(window["w_win_hartree"], D(float(source["w_win_eta_0_hartree"])), "C0 width window reproduced")
    registry = json.loads((root / DOCS / "source_registry.json").read_text())
    for r in registry["sources"]:
        b = (root / r["path"]).read_bytes()
        check(hashlib.sha256(b).hexdigest() == r["sha256"] and len(b) == r["bytes"], "source identity")
        for key in ("origin_result_commit", "verified_snapshot_commit"):
            check(subprocess.check_output(["git", "-C", str(root), "show", r[key] + ":" + r["path"]]) == b,
                  "source origin/snapshot blob")
    manifest = json.loads((root / OUT / "manifest.json").read_text())
    check(manifest["manifest_self_excluded"] and not any(r["path"].endswith("/manifest.json") for r in manifest["files"]),
          "explicit self-exclusion")
    for r in manifest["files"]:
        b = (root / r["path"]).read_bytes()
        check(hashlib.sha256(b).hexdigest() == r["sha256"] and len(b) == r["bytes"], "runner manifest")
    check(result["summary"]["new_scientific_acquisition_count"] == 0, "no acquisition")
    return {"status": "independent_output_audit_pass", "checks": checks,
            "arithmetic": "Decimal60_separate_implementation", "source_identity_checks": len(registry["sources"]),
            "tables": {k: len(v) for k, v in tables.items()}, "C0_rows_reconciled": len(c0),
            "all_saved_decisions_reconciled": 64, "gamma1_undefined_ratio_rows": 30,
            "new_scientific_acquisition_count": 0, "legacy_molecular_tests_executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), indent=2))
