"""Post-hoc scalar/byte audit only; never execute a molecular worker or scorer."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = ROOT / "artifacts/hchain_h6_truth_continuation_20261006"
DOC = "docs/second_study_v2/hchain_truth_continuation_20261006"
BASE = "1aad415bfaed5503508872c1fa5a8a8c12da4193"
SNAPSHOT = "8d774a5a242d802ff6ae8f72ce3cd7152442c326"
STAGES = {
    "readiness": "8c40bba6ab3fec5249c79e6c58473e7132984f07",
    "truth": "6acee8a5b61ae691460d3d8ec7ac2c6f137f7e9a",
    "analysis": SNAPSHOT,
}
UPSTREAM = {
    "inputs": "afbf22d063199ccc573c6664d7198acea1990a3f",
    "reference_time": "cd5488902e46bc1320d6fc983f2d6e76d5aa4010",
    "prediction": "61ae95edce8c4a25167521c0e6e95a83c3cbc4bb",
    "ground": "1e5d66a4914bc50a8afa55baa578cca55a227979",
}
BUNDLE_FILES = ("prediction.json", "prediction.sha256", "FREEZE.json", "source_audit.json",
                "access_audit.json", "resource_audit.json", "manifest.json")
EPS, BETA, K = 0.00015936001019904, 1.2, 14344


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def read(path):
    return json.loads(Path(path).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def bundle_gate(directory, origin):
    for name in BUNDLE_FILES:
        data = (directory / name).read_bytes()
        path = str((directory / name).relative_to(ROOT))
        assert data == git("show", f"{origin}:{path}"), path
    manifest = read(directory / "manifest.json")
    assert manifest["manifest_self_excluded"]
    for entry in manifest["files"]:
        data = (directory / entry["path"]).read_bytes()
        assert len(data) == entry["bytes"] and sha(data) == entry["sha256"]
    assert sha((directory / "prediction.json").read_bytes()) == (directory / "prediction.sha256").read_text().split()[0]


def csv_table(name, rows):
    with (OUT / "tables_figures" / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    assert git("merge-base", "--is-ancestor", SNAPSHOT, "HEAD") == b""
    assert not git("diff", "--name-only") and not git("diff", "--cached", "--name-only")
    for stage, commit in STAGES.items():
        bundle_gate(OUT / stage, commit)
    recovery = ROOT / "artifacts/hchain_h6_geometry_recovery_20261006"
    for stage, commit in UPSTREAM.items():
        bundle_gate(recovery / stage, commit)
    seal = read(ROOT / DOC / "source_freeze.json")
    previous = read(ROOT / "docs/second_study_v2/hchain_geometry_recovery_20261006/source_freeze.json")
    for entry in seal["files"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert sha(data) == entry["sha256"]
        assert data == git("show", f"{seal['content_commit']}:{entry['path']}")
        assert data == git("show", f"{entry['origin_result_commit']}:{entry['path']}")
    for entry in previous["files"]:
        assert (ROOT / entry["path"]).read_bytes() == git("show", f"{BASE}:{entry['path']}")
    changed_old = [name for name in git("diff", "--name-only", BASE, "HEAD").decode().splitlines()
                   if git("ls-tree", "--name-only", BASE, "--", name).strip()]
    assert not changed_old
    readiness = read(OUT / "readiness/prediction.json")
    for row in readiness["runtime_checks"]:
        path = Path(row["path"])
        assert not path.is_symlink() and path.stat().st_size == row["bytes"]
        assert sha(path.read_bytes()) == row["sha256"]
    assert len(readiness["runtime_checks"]) == 8
    truth = read(OUT / "truth/prediction.json")
    result = read(OUT / "analysis/prediction.json")
    assert result["status"] == "hchain_h6_geometry_sweep_truth_continuation_complete_review_required"
    assert result["failure"] is None and result["technical_retry"] == result["scientific_retry"] == 0
    assert len(truth["systems"]) == 5 and len(truth["workers"]) == 4
    assert truth["new_truth_coordinates"] == 12 and truth["anchor_truth_reused"] == 3
    counts = Counter()
    import_events = []
    new_points = []
    for worker in truth["workers"]:
        assert worker["status"] == "complete" and worker["new_front_end_actions"] == 0
        assert worker["expected_ground_vector_read"] and not worker["access"]["denials"]
        assert worker["resource"]["BLAS_threads"] == worker["resource"]["CPU_processes"] == 1
        assert worker["resource"]["own_process_memory"]["VmSwap"] == 0
        points = worker["points"]
        assert [p["ratio"] for p in points] == [.5, .65, .8]
        assert all(p["time"].hex() == p["time_hex"] for p in points)
        assert all(p["quality"]["physical_branch_valid"] for p in points)
        assert "exact-ground overlap" in points[0]["selection_rule"]
        assert all("previous" in p["selection_rule"] for p in points[1:])
        new_points.extend(points)
        counts.update(worker["resource"]["counts"])
        assert len(worker["sealed_source_imports"]) == 1
        event = worker["sealed_source_imports"][0]
        assert event["source_only"] and event["pyc_reads"] == event["pyc_writes"] == 0
        import_events.append({"geometry": worker["unit"], **event})
    for key in ("full_pf_unitary_builds", "direct_Schur_solves", "direct_truth_coordinates", "target_phase_gaps"):
        assert counts[key] == 12
    assert all(value == 0 for value in result["forbidden_front_end_actions"].values())
    assert dict(counts) == result["truth_only_actions"]
    assert counts["GPU_queries"] == counts["GPU_allocations"] == counts["GPU_kernels"] == 0
    pre = read(ROOT / DOC / "focused_tests.json")
    for tests in (pre, result["post_tests"]):
        assert tests["passed"] == 100 and tests["failed"] == tests["error"] == tests["skipped"] == tests["exit_code"] == 0
        assert not tests["truth_bearing_legacy_tests_run"] and tests["molecular_actions"] == 0
    rows = result["analysis"]["rows"]
    assert len(rows) == 75
    coordinates = [r for r in rows if r["gamma"] == 1.01]
    assert len(coordinates) == 15
    for row in rows:
        c, e, gamma, time, budget = (row[k] for k in ("c", "e", "gamma", "time", "frozen_budget"))
        assert row["truth_valid"] and row["physical_branch_correct"]
        margin = (1 - 1 / gamma) * (EPS - c)
        assert math.isclose(row["safety_slack"], margin - (e - c), rel_tol=0, abs_tol=1e-18)
        assert row["safe"] == (e + BETA * K / (time * budget) <= EPS) == (row["safety_slack"] >= 0)
        if gamma == 1:
            assert row["margin_ratio"] is None and row["gamma1_uses_additive_slack"]
        assert row["M1_abstained"] and row["M1_failure_reasons"] == ["no_positive_qpe_allowance"]
        assert row["empirical_width_covers"] and row["decomposition_status"] == "closed_same_H_origin_physical_branch"
    geometry_rows = []
    for summary in result["analysis"]["geometry_summaries"]:
        unit = summary["geometry"]
        decisions = summary["decisions"]
        assert len(decisions) == 5 and all(d["safe"] for d in decisions)
        chosen = next(r for r in coordinates if r["geometry"] == unit and r["candidate_id"] == decisions[1]["decision"]["candidate_id"])
        assert chosen["candidate_id"].endswith("r0.8")
        geometry_rows.append({"geometry": unit, "R_angstrom": float(unit.split("R")[-1]),
            "anchor_reused": unit == "H6_R1.00", "B0_safe": decisions[0]["safe"],
            "all_B1_gamma_safe": all(d["safe"] for d in decisions[1:]),
            "selected_time": chosen["time"], "selected_time_hex": chosen["time_hex"],
            "B1_gamma1_01_over_B0": decisions[1]["budget_ratio_B0"],
            "B1_gamma1_01_reduction_fraction": 1 - decisions[1]["budget_ratio_B0"],
            **{k: chosen[k] for k in ("gamma_req", "safety_slack", "E_C_hartree", "E_M_hartree", "width_M_hartree",
                "same_time_decision_width_window_hartree", "same_time_cost_free_truth_headroom")}})
    csv_table("geometry_summary.csv", geometry_rows)
    csv_table("coordinate_diagnostics.csv", coordinates)
    monitor = read(OUT / "analysis/resource_audit.json")["monitors"][0]
    summary = {
        "geometry_count": 5, "coordinate_count": 15, "new_truth": 12, "anchor_reused": 3,
        "B0_safe_geometries": 5, "B1_all_four_gamma_safe_geometries": 5,
        "gamma1_posthoc_safe_coordinates": sum(r["safe"] for r in rows if r["gamma"] == 1),
        "gamma1_01_safe_coordinates": sum(r["safe"] for r in coordinates),
        "M1_abstention_coordinates": 15, "M1_point_better_than_cheap_coordinates": sum(r["E_M_hartree"] < r["E_C_hartree"] for r in coordinates),
        "M1_empirical_width_coverage_coordinates": 15, "physical_branch_correct_coordinates": 15,
        "positive_same_time_width_windows": sum(r["same_time_decision_width_window_hartree"] > 0 for r in coordinates),
        "PF_H_reference_decomposition_closed_coordinates": 15,
        "maximum_decomposition_closure_residual_hartree": max(abs(r["decomposition_closure_residual"]) for r in coordinates),
        "new_truth_maximum_unitarity_residual_Frobenius": max(p["unitarity_residual_frobenius"] for p in new_points),
        "new_truth_maximum_eigenpair_residual_2_norm": max(p["eigenpair_residual_2_norm"] for p in new_points),
        "new_truth_minimum_target_phase_gap_radians": min(p["minimum_selected_phase_gap_radians"] for p in new_points),
        "new_truth_minimum_ground_overlap_probability": min(p["ground_state_overlap_probability"] for p in new_points),
        "sampled_aggregate_peak_RSS_bytes": monitor["aggregate_peak_RSS_bytes"],
        "maximum_individual_worker_peak_RSS_KiB": max(w["resource"]["peak_RSS_KiB"] for w in truth["workers"]),
        "truth_stage_wall_seconds": monitor["stage_wall_seconds"], "named_run_wall_seconds": result["run_wall_seconds"],
        "geometry_summary": geometry_rows,
    }
    save("summary.json", summary)
    save("review_audit.json", {"schema": "truth_continuation_readonly_audit_v1", "checks_passed": True,
        "verified_snapshot_commit": SNAPSHOT, "stage_origin_result_commits": STAGES,
        "upstream_origin_result_commits": UPSTREAM, "source_rows_verified": len(seal["files"]),
        "old_recovery_source_rows_unchanged": len(previous["files"]), "base_tracked_files_changed": changed_old,
        "stage_bundle_blobs_verified": 21, "upstream_bundle_blobs_verified": 28, "runtime_byte_gates_verified": 8,
        "sealed_source_imports": import_events, "truth_only_actions": dict(counts),
        "forbidden_front_end_actions": result["forbidden_front_end_actions"], "focused_pre_post_tests": [pre, result["post_tests"]],
        "frozen_ground_vectors_read_for_scoring": 4,
        "legacy_truth_array_reads_counter": {"value": counts["truth_array_reads"], "instrumented": False,
            "interpretation": "Not evidence of zero ground-vector access. Four frozen ground vectors were intentionally read; no new ground solve."},
        "PySCF_threads_counter_interpretation": "sum of four worker metadata values, not a thread action count",
        "audit_new_science_actions": 0, "formal_predictions_budgets_widths_gates_changed": False,
        "OS_hermeticity_claim": False, "independent_samples_claim": False, "net_calibration_cost_claim": False})
    registry = []
    for stage, commit in [*STAGES.items(), *UPSTREAM.items()]:
        directory = OUT / stage if stage in STAGES else recovery / stage
        for name in BUNDLE_FILES:
            path = directory / name
            registry.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                "sha256": sha(path.read_bytes()), "origin_result_commit": commit, "verified_snapshot_commit": SNAPSHOT})
    for entry in truth["source_registry"]:
        path = ROOT / entry["path"]
        assert path.read_bytes() == git("show", f"{entry['origin_result_commit']}:{entry['path']}")
        registry.append({**entry, "verified_snapshot_commit": SNAPSHOT,
            "prior_verified_snapshot_commit": entry["verified_snapshot_commit"]})
    save("source_registry.json", {"files": registry, "sealed_science_dependencies": DOC + "/source_freeze.json",
        "private_runtime_metadata_only": readiness["runtime_checks"],
        "Track_R_accepted_commit": "0c40a3d7987e0961262bfd38bbb214a9e2946824"})
    figures(coordinates)
    print(json.dumps({"audit": "passed", "summary": summary}, indent=2))


def figures(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    directory = OUT / "tables_figures"
    for name, fields, labels, scale in (
        ("geometry_safety", ("gamma_req", "safety_slack"), ("Required gamma (unclipped)", "Safety slack at gamma=1.01 (Ha)"), "linear"),
        ("M1_point_width", ("E_C_hartree", "E_M_hartree", "width_M_hartree"), ("Cheap point error (Ha)", "M1 point error (Ha)", "M1 empirical width (Ha)"), "log"),
        ("PF_H_reference_decomposition", ("PF_side_error_hartree", "H_reference_error_hartree", "E_M_hartree"), ("Signed PF-side error (Ha)", "Signed H-reference error (Ha)", "M1 point error (Ha)"), "linear"),
    ):
        fig, axes = plt.subplots(1, len(fields), figsize=(4.1 * len(fields), 3.5))
        for ratio, color in zip(("r0.5", "r0.65", "r0.8"), ("C0", "C1", "C2"), strict=True):
            subset = [r for r in rows if r["candidate_id"].endswith(ratio)]
            distances = [float(r["geometry"].split("R")[-1]) for r in subset]
            for axis, field, label in zip(axes, fields, labels, strict=True):
                axis.plot(distances, [r[field] for r in subset], "o-", color=color, label=ratio.removeprefix("r") + " t_ref")
                anchor = next(r for r in subset if r["geometry"] == "H6_R1.00")
                axis.plot([1.], [anchor[field]], "s", ms=8, mfc="none", mec="black", zorder=3)
                axis.set(xlabel="H6 spacing R (Angstrom)", ylabel=label, yscale=scale)
                axis.legend(fontsize=7)
        if name == "geometry_safety":
            axes[0].axhline(1., color="black", linestyle=":", lw=.8)
            axes[0].axhline(1.01, color="black", linestyle="--", lw=.8)
            axes[1].axhline(0., color="black", linestyle=":", lw=.8)
        fig.tight_layout()
        fig.savefig(directory / (name + ".svg"))
        fig.savefig(directory / (name + ".png"), dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
