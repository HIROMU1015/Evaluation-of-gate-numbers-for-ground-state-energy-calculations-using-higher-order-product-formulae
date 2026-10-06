"""Cross-check scalar results and draw diagnostic figures without refitting."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/lab_progress_additional_validation_20261007"
H4 = ROOT / "artifacts/lab_progress_h4_state_checks_20261007"
HF = ROOT / "artifacts/lab_progress_hf_cap_checks_20261007"
D = ROOT / "artifacts/lab_progress_hchain_transfer_20261007"
OLD = ROOT / "artifacts/m3_one_two_term_model_comparison_server2_20260910_92df2db_cpu/summary.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def rows(path: Path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def verify_frozen_inputs() -> None:
    frozen = read(H4 / "PREDICTIONS_FROZEN.json")
    assert sha(H4 / "predictions.json") == frozen["prediction_sha256"]
    assert sha(H4 / "protocol.json") == read(H4 / "predictions.json")["protocol_sha256"]
    frozen = read(HF / "SELECTION_FROZEN.json")
    assert sha(HF / "predictions.json") == frozen["predictions_sha256"]
    assert sha(HF / "protocol.json") == frozen["protocol_sha256"]
    frozen = read(D / "PREDICTIONS_FROZEN.json")
    assert sha(D / "protocol.json") == frozen["protocol_sha256"]
    assert len(frozen["prediction_sha256"]) == 16
    for name, digest in frozen["prediction_sha256"].items():
        assert sha(D / name) == digest
    for directory in (H4, HF, D):
        for source in read(directory / "protocol.json")["source_registry"]:
            assert sha(ROOT / source["path"]) == source["sha256"]


def audit_scalars() -> dict:
    verify_frozen_inputs()
    epsilon = read(H4 / "protocol.json")["constants"]["epsilon_E_hartree"]
    beta = read(H4 / "protocol.json")["constants"]["beta"]
    classifications = []
    for row in rows(H4 / "allocations.csv"):
        total = abs(float(row["direct_shift"])) + float(row["qpe_error"])
        assert abs(total - float(row["total_error"])) < 1e-15
        reliable = row["branch_reliable"] == "True"
        status = "unscorable_branch" if not reliable else "pass" if total <= epsilon else "fail"
        classifications.append({"state_id": row["state_id"], "classification": status,
                                "time": float(row["time_hartree_inverse"]),
                                "budget": float(row["budget"])})
        # Unreliable raw tracked eigenphases are never certified ground truth.
        assert (row["target_met"] == "True") == (status == "pass")
    hf_checks = []
    for row in rows(HF / "scoring.csv"):
        qpe = beta * int(row["rotations"]) / (float(row["selected_time"]) * float(row["budget"]))
        total = abs(float(row["signed_direct_shift"])) + qpe
        assert abs(total - float(row["total_error"])) < 1e-15
        components = sum(float(row[k]) for k in ("model_difference", "state_difference", "proxy_difference"))
        assert abs(components - float(row["total_signed_prediction_difference"])) < 1e-15
        assert (row["precision_pass"] == "True") == (total <= epsilon)
        hf_checks.append({"condition": row["condition"], "formula": row["formula"],
                          "cap": float(row["cap"]), "pass": total <= epsilon})
    schedule = []
    for record in read(OLD)["records"]:
        if record["condition"] not in ("H6", "H7") or record["formula"] != "current_m3":
            continue
        for name in ("original_one_term", "two_term"):
            model = record["models"][name]
            predicted = model["definition"]["predicted_optimal_time"]
            minimum = model["saved_local_direct_minimum"]
            direct = model["predicted_time_direct_point"]["direct_cost"]
            time_difference = abs(predicted - minimum["time"]) / minimum["time"]
            cost_loss = direct / minimum["direct_cost"] - 1
            assert abs(time_difference - model["metrics"]["predicted_time_difference_from_saved_local_grid_minimum"]) < 1e-12
            assert abs(cost_loss - model["metrics"]["direct_cost_loss_against_saved_local_grid"]) < 1e-12
            schedule.append({"condition": record["condition"], "model": name,
                             "predicted_time": predicted, "saved_local_minimum_time": minimum["time"],
                             "relative_time_difference": time_difference,
                             "relative_direct_cost_loss": cost_loss,
                             "scope": "saved seven-point local comparison, not continuous optimum"})
    transfer = read(D / "audit.json")
    assert transfer["direct_candidate_count"] == 4812
    for row in rows(D / "canonical_long_time_error_decomposition.csv"):
        difference = float(row["model_shift"]) - float(row["direct_shift"])
        components = sum(float(row[k]) for k in ("fit_term", "state_term", "proxy_term"))
        assert abs(difference - components) < 1e-12
    auxiliary = read(D / "supplementary_dominant_phase.json")
    assert not auxiliary["continuation_results_or_selection_modified"]
    for row in auxiliary["records"]:
        total = abs(row["dominant_phase_shift"]) + beta * row["K"] / (row["time"] * row["budget"])
        assert abs(total - row["frozen_budget_total_error"]) < 1e-15
        assert row["supplementary_phase_valid"] and not row["supplementary_precision_met"]
        formal = next(r for r in transfer["formal_classifications"] if r["system"] == row["system"])
        assert formal["formal_precision_status"] == "unconfirmed_continuation_branch_gate_failed"
        assert formal["budget"] == row["budget"] and formal["selected_time"] == row["time"]
    snapshot = "869806ff9995b76ef2786ca7b57b9acc02c2731f"
    origin = subprocess.check_output(["git", "log", "-1", "--format=%H", snapshot, "--", str(OLD.relative_to(ROOT))], cwd=ROOT, text=True).strip()
    return {"epsilon_E": epsilon, "h4_classifications": classifications,
            "hf_pf_precision_checks": hf_checks, "one_two_term_saved_schedule_checks": schedule,
            "hchain_formal_classifications": [{"system": r["system"], "status": r["formal_precision_status"]}
                                               for r in transfer["formal_classifications"]],
            "hchain_direct_candidate_count": transfer["direct_candidate_count"],
            "hchain_supplementary_phase_records": auxiliary["records"],
            "existing_schedule_source": {"path": str(OLD.relative_to(ROOT)), "sha256": sha(OLD),
                "origin_result_commit": origin, "verified_snapshot_commit": snapshot},
            "new_scientific_computation_in_this_script": False,
            "new_result_commit": "published handoff commit; supplied by final handoff, not a pre-existing input snapshot"}


def draw_figures() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    decomposition = [r for r in rows(H4 / "state_decomposition_grid.csv")
                     if r["formula_id"] == "m5_best" and r["state_id"] == "cisd"]
    t = [float(r["time_hartree_inverse"]) for r in decomposition]
    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    for key, label, style in (("model_signed_shift", "CISD two-term prediction", "--"),
                              ("proxy_hartree", "CISD proxy", "-"),
                              ("exact_proxy_hartree", "Exact-state proxy", "-")):
        ax.plot(t, [float(r[key]) for r in decomposition], style, label=label)
    ax.plot(t, [float(r["direct_shift_hartree"]) if r["branch_reliable"] == "True"
                else float("nan") for r in decomposition], color="black",
            label="Direct PF shift (reliable points only)")
    epsilon = read(H4 / "protocol.json")["constants"]["epsilon_E_hartree"]
    ax.axhline(epsilon, color="gray", lw=.8)
    ax.axhline(-epsilon, color="gray", lw=.8)
    ax.axvline(2.1466061014866242, color="gray", ls=":", label="Selected time")
    ax.axvline(3.5175172132783867, color="purple", ls=":", label="Reliable grid minimum")
    intervals, start = [], None
    for i, row in enumerate(decomposition):
        if row["branch_reliable"] != "True" and start is None:
            start = i
        if start is not None and (row["branch_reliable"] == "True" or i == len(t)-1):
            end = i-1 if row["branch_reliable"] == "True" else i
            intervals.append(((t[start-1]+t[start])/2 if start else t[start],
                              (t[end]+t[end+1])/2 if end+1 < len(t) else t[end]))
            start = None
    for i, (left, right) in enumerate(intervals):
        ax.axvspan(left, right, color="gray", alpha=.12,
                   label="Branch gate fails" if i == 0 else "_nolegend_")
    ax.set(yscale="symlog", xlabel=r"Evolution time $t$ [Ha$^{-1}$]", ylabel="Signed energy quantity [Ha]",
           title="H4 / m5_best: state, extrapolation and proxy differ at long times")
    ax.set_yscale("symlog", linthresh=1e-6)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=.2)
    fig.savefig(OUT / "h4_long_time_error.png", dpi=160)
    plt.close(fig)

    selected = rows(HF / "joint_selection_scoring.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), constrained_layout=True)
    for ax, condition in zip(axes, ("HF_full_eq_sto3g", "HF_full_stretch150_sto3g")):
        subset = [r for r in selected if r["condition"] == condition]
        base = next(float(r["budget"]) for r in subset if float(r["cap"]) == .5)
        for r in subset:
            cap = float(r["cap"])
            passed = r["precision_pass"] == "True"
            ax.scatter(cap, float(r["budget"]) / base, marker="o" if passed else "x",
                       color="#157f4b" if passed else "#bf3434", s=85)
            ax.annotate("pass" if passed else "fail", (cap, float(r["budget"]) / base),
                        xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9)
        ax.set(title="HF equilibrium" if "eq" in condition else "HF stretched",
               xlabel=r"Upper cap / $t_{proxy}$", ylabel="Predicted budget / original budget",
               xticks=[.5, 1, 1.8], ylim=(.45, 1.15))
        ax.grid(alpha=.2)
    fig.suptitle("Fixed CISD model and 1% margin: lower predicted cost can miss precision")
    fig.savefig(OUT / "hf_cap_precision.png", dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = audit_scalars()
    (OUT / "cross_checks.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    draw_figures()
    print(json.dumps({"h4": summary["h4_classifications"],
                      "hf_pf_pass_count": sum(r["pass"] for r in summary["hf_pf_precision_checks"]),
                      "figures": ["h4_long_time_error.png", "hf_cap_precision.png"]}, indent=2))


if __name__ == "__main__":
    main()
