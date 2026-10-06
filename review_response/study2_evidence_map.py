"""Read committed scalar evidence only; do not acquire, rescore, or adopt policies."""

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY = (
    "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-"
    "using-higher-order-product-formulae"
)
MAIN = "bfe715fc1c04325535a3c4d63ea4584e691dc322"
G = "1e03a659f3111623fa2b7afc3d8a87eeda1f4730"
R = "0c40a3d7987e0961262bfd38bbb214a9e2946824"
P = "a852c41331f2c8e0f7415c34e78c0110e4afd284"
BRANCHES = {
    MAIN: "pf-second-study-v2-budget-safety-mechanism-20261005",
    G: "pf-study2-hchain-h6-truth-continuation-20261006",
    R: "pf-study2-hchain-m1-rank-convergence-20261006",
    P: "gpu-pf-study2-prospective-truth-scoring-20261006",
}
_MAIN_DIR = "artifacts/budget_safety_mechanism_20261005/"
SOURCES = (
    ("capacity", MAIN, _MAIN_DIR + "budget_safety_capacity.csv"),
    ("m1", MAIN, _MAIN_DIR + "m1_point_width_abstention.csv"),
    ("selected", MAIN, _MAIN_DIR + "selected_frozen_budget_safety.csv"),
    ("model", MAIN, _MAIN_DIR + "hchain_model_vs_observation.csv"),
    ("decomposition", MAIN, _MAIN_DIR + "m1_reference_error_decomposition.csv"),
    ("series", P, "artifacts/hchain_h8_memory_safe_extension_20261004/h2_h8_integrated_summary.csv"),
    ("g_summary", G, "artifacts/hchain_h6_truth_continuation_20261006/summary.json"),
    ("g_analysis", G, "artifacts/hchain_h6_truth_continuation_20261006/analysis/prediction.json"),
    ("r_analysis", R, "artifacts/hchain_m1_rank_convergence_20261006/analysis/prediction.json"),
    ("prospective", P, "artifacts/prospective_truth_scoring_20261006/final/scoring.json"),
    ("prospective_protocol", P, "docs/second_study_v2/prospective_core_protocol_20261005/protocol.json"),
)
STATUS = "second_study_v2_evidence_map_integration_complete_review_required"
DOC_DIR = "docs/second_study_v2/evidence_integration_20261006/"
ARTIFACT_DIR = "artifacts/study2_evidence_integration_20261006/"
PUBLICATION_FILES = (
    "review_response/study2_evidence_map.py", "review_tests/test_study2_evidence_map.py",
    "docs/current_research_status.md", DOC_DIR + "README.md", DOC_DIR + "approved_closure.md",
    DOC_DIR + "evidence_map.md", ARTIFACT_DIR + "evidence_scalars.json",
    ARTIFACT_DIR + "source_registry.json", ARTIFACT_DIR + "source_publication_audit.json",
    ARTIFACT_DIR + "COMPLETE.json", ARTIFACT_DIR + "verification.json",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def read_sources(root):
    """Only the enumerated committed JSON/CSV blobs may be read."""
    data, registry = {}, []
    for key, snapshot, path in SOURCES:
        raw = git(root, "show", f"{snapshot}:{path}")
        origin = git(root, "log", "-1", "--format=%H", snapshot, "--", path).decode().strip()
        require(len(origin) == 40, f"Missing origin: {path}")
        git(root, "merge-base", "--is-ancestor", origin, snapshot)
        require(raw == git(root, "show", f"{origin}:{path}"), f"Origin bytes differ: {path}")
        data[key] = (list(csv.DictReader(io.StringIO(raw.decode())))
                     if path.endswith(".csv") else json.loads(raw))
        registry.append({
            "key": key, "path": path,
            "origin_result_commit": origin,
            "origin_definition": "last_path_revision_at_verified_snapshot",
            "verified_snapshot_commit": snapshot,
            "published_snapshot_branch": BRANCHES[snapshot],
            "snapshot_blob": git(root, "rev-parse", f"{snapshot}:{path}").decode().strip(),
            "origin_blob": git(root, "rev-parse", f"{origin}:{path}").decode().strip(),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "origin_snapshot_byte_identical": True,
            "url": f"https://github.com/{REPOSITORY}/blob/{snapshot}/{path}",
        })
    return data, registry


def csv_true(value):
    require(value in ("True", "False"), f"Unknown CSV boolean: {value!r}")
    return value == "True"


def finite_budget(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def value_range(values):
    values = list(values)
    require(bool(values) and all(math.isfinite(x) for x in values), "Nonfinite or empty scalar range")
    return {"min": min(values), "max": max(values)}


def unique_coordinates(rows, fields):
    keys = [tuple(row[field] for field in fields) for row in rows]
    require(len(keys) == len(set(keys)), "Duplicate coordinate in a native block")


def assemble(data):
    """Count saved outcomes; never recompute a budget, truth, width, or selector."""
    native = []
    for family, expected in (("HF", 6), ("HCl", 6), ("H-chain", 18)):
        c = [r for r in data["capacity"] if r["family"] == family and float(r["gamma"]) == 1.01]
        m = [r for r in data["m1"] if r["family"] == family]
        d = [r for r in data["decomposition"] if r["family"] == family]
        require(len(c) == len(m) == len(d) == expected, f"Native {family} coverage changed")
        unique_coordinates(c, ("condition", "candidate_id", "time_hex"))
        require({(r["condition"], r["time_hex"]) for r in c} ==
                {(r["condition"], r["time_hex"]) for r in m}, "Native point tuple mismatch")
        native.append({
            "family": family, "conditions": len({r["condition"] for r in c}),
            "coordinates": len(c), "contract": sorted({r["contract"] for r in c}),
            "gamma1_01_coordinate_safe_diagnostic": sum(csv_true(r["safe_arithmetic"]) for r in c),
            "gamma_req_truth_diagnostic": value_range(float(r["gamma_req"]) for r in c),
            "M1_point_better_than_cheap": sum(csv_true(r["point_improves_over_cheap"]) for r in m),
            "M1_empirical_width_covers": sum(csv_true(r["empirical_width_covers"]) for r in m),
            "M1_formal_abstentions": sum(csv_true(r["abstained"]) for r in m),
            "decomposition_closed": sum(r["decomposition_status"].startswith("closed") for r in d),
            "decomposition_indeterminate": sum(r["decomposition_status"].startswith("indeterminate") for r in d),
        })
    hf_selected = [r for r in data["selected"] if r["condition"].startswith("HF_") and r["arm"] == "B1_gamma_1.01"]
    require(len(hf_selected) == 2, "HF selected decision coverage")
    hcl_102 = [r for r in data["capacity"] if r["family"] == "HCl" and float(r["gamma"]) == 1.02]
    native[0]["gamma1_01_selected_decisions"] = [
        {"condition": r["condition"], "candidate": r["candidate_id"], "safe": csv_true(r["saved_safe"])}
        for r in hf_selected
    ]
    native[1]["gamma1_02_coordinate_safe_diagnostic"] = sum(csv_true(r["safe_arithmetic"]) for r in hcl_102)

    series = data["series"]
    require(len(series) == 7, "H2-H8 attempted denominator")
    usable = [r for r in series if csv_true(r["performance_scored"])]
    excluded = [r for r in series if not csv_true(r["performance_scored"])]
    require(len(usable) == 6 and [r["system"] for r in excluded] == ["H3"], "H3 eligibility changed")
    require(all(r["q"] == "0" and csv_true(r["B2_safe"]) and csv_true(r["H1_safe"]) for r in usable), "Native saved decisions changed")
    model = data["model"]
    require(len(model) == 6, "Model comparison coverage")
    series_block = {
        "attempted_systems": 7, "reference_eligible_systems": 6,
        "excluded": [{"system": r["system"], "status": r["status"], "unsafe": None} for r in excluded],
        "selected_B2_H1_safe_conditions": 6, "q1_measured_conditions": 0,
        "selected_saving_fraction": value_range(float(r["saved_B2_saving"]) for r in model),
        "leading_model_saving_fraction": sorted({float(r["leading_model_saving"]) for r in model}),
        "independent_causal_decomposition_of_saving": False,
        "population_sector_warning": "H7 charge+1, multiplicity3, populations4/2; size series is not a pure neutral-singlet scaling study",
    }

    gs, grows = data["g_summary"], data["g_analysis"]["analysis"]["rows"]
    g01 = [r for r in grows if r["gamma"] == 1.01]
    g1 = [r for r in grows if r["gamma"] == 1.0]
    require(len(grows) == 75 and len(g01) == len(g1) == 15, "Geometry gamma/coordinate coverage")
    unique_coordinates(g01, ("geometry", "candidate_id", "time_hex"))
    for summary_key, row_key in (
        ("gamma1_01_safe_coordinates", "safe"), ("M1_abstention_coordinates", "M1_abstained"),
        ("M1_empirical_width_coverage_coordinates", "empirical_width_covers"),
        ("physical_branch_correct_coordinates", "physical_branch_correct"),
    ):
        require(gs[summary_key] == sum(r[row_key] is True for r in g01), f"G summary mismatch: {summary_key}")
    require(gs["new_truth"] + gs["anchor_reused"] == 15, "G new/reused denominator")
    geometry = {
        "geometries": gs["geometry_count"], "coordinates": 15,
        "source_new_truth_coordinates": gs["new_truth"], "source_reused_anchor_coordinates": gs["anchor_reused"],
        "gamma1_01_safe_coordinates": gs["gamma1_01_safe_coordinates"],
        "gamma1_posthoc_safe_coordinates": sum(r["safe"] for r in g1),
        "gamma1_posthoc_unsafe_coordinates": [r["candidate_id"] for r in g1 if not r["safe"]],
        "gamma_req_truth_diagnostic": value_range(r["gamma_req"] for r in g01),
        "M1_formal_abstentions": gs["M1_abstention_coordinates"],
        "M1_empirical_width_covers": gs["M1_empirical_width_coverage_coordinates"],
        "M1_point_better_than_cheap": sum(r["E_M_hartree"] < r["E_C_hartree"] for r in g01),
        "decomposition_closed": sum(r["decomposition_status"] == "closed_same_H_origin_physical_branch" for r in g01),
        "selected_geometry_scalars": gs["geometry_summary"],
        "selected_cost_free_oracle_headroom_fraction": value_range(r["same_time_cost_free_truth_headroom"] for r in gs["geometry_summary"]),
        "selected_B0_saving_fraction": value_range(r["B1_gamma1_01_reduction_fraction"] for r in gs["geometry_summary"]),
    }

    rank_rows = data["r_analysis"]["analysis"]["rows"]
    require(len(rank_rows) == 36, "Rank diagnostic coverage")
    native_hchain = {(r["condition"], r["time_hex"]) for r in data["m1"] if r["family"] == "H-chain"}
    rank_coordinates = {(r["system"], r["time_hex"]) for r in rank_rows}
    anchor_coordinates = {("H6", r["time_hex"]) for r in g01 if r["geometry"] == "H6_R1.00"}
    require(len(rank_coordinates) == 9 and rank_coordinates <= native_hchain, "Rank/native tuple overlap not verified")
    require(len(anchor_coordinates) == 3 and anchor_coordinates <= native_hchain, "G/native H6 anchor overlap not verified")
    ranks = []
    for rank in (4, 8, 16, 32):
        rows = [r for r in rank_rows if r["rank"] == rank]
        require(len(rows) == 9, "Rank coordinate coverage")
        unique_coordinates(rows, ("system", "candidate_id", "time_hex"))
        finite = [r for r in rows if finite_budget(r["hypothetical_M1_budget"])]
        require(all(r["M1_budget_beats_same_time_cheap"] ==
                    (r["hypothetical_M1_budget"] < r["same_time_cheap_gamma1_01_budget"]) for r in finite), "Rank finite budget comparison mismatch")
        require(all(r["M1_budget_beats_same_time_cheap"] is None for r in rows if not finite_budget(r["hypothetical_M1_budget"])), "Unavailable budget misclassified")
        ranks.append({
            "rank": rank, "coordinates": len(rows),
            "point_better_than_cheap": sum(r["E_M_hartree"] < r["E_C_hartree"] for r in rows),
            "positive_qpe_allowance": sum(r["positive_QPE_allowance"] for r in rows),
            "finite_hypothetical_budgets": len(finite), "budget_unavailable": len(rows) - len(finite),
            "hypothetical_budget_below_same_time_cheap": sum(r["M1_budget_beats_same_time_cheap"] is True for r in rows),
            "empirical_width_covers": sum(r["empirical_width_covers"] for r in rows),
            "decomposition_closed": sum(r["decomposition_status"] == "closed_same_H_origin_physical_branch" for r in rows),
        })
    rank_block = {"systems": ["H6", "H7", "H8"], "reused_coordinates": 9, "rank_rows": 36,
                  "new_truth": 0, "rank8_reproduction_pass": 9, "ranks": ranks,
                  "rank_rescue_or_formal_adoption": False}
    require(all(r["rank8_control_passed"] for r in rank_rows), "Rank8 control changed")

    p = data["prospective"]
    protocol = data["prospective_protocol"]
    require(protocol["direction"] == "C" and protocol["PF"]["id"] == "current_m3" and
            protocol["reference"]["ratios"] == [0.8, 1, 1.2] and
            protocol["resource"]["T0_ratio"] == 0.8 and protocol["resource"]["B0_gamma"] == 1.1,
            "Prospective native contract changed")
    require(p["denominators"]["attempted_conditions"] == 16 and
            p["denominators"]["scored_conditions"] == 13 and
            p["denominators"]["scored_coordinates"] == 39 and
            p["denominators"]["family_units"] == 4, "Prospective denominator changed")
    require(len(p["conditions"]) == 16 and len(p["coordinate_scores"]) == 39, "Prospective rows missing")
    axes = {}
    for arm, saved in p["B0_B1_evidence_axes"].items():
        rows = [r for r in p["decision_scores"] if r["arm"] == arm]
        require(len(rows) == 13 and len({r["condition_id"] for r in rows}) == 13, "Prospective selected unit mismatch")
        require(sum(r["safe"] for r in rows) == saved["safe"] and
                sum(r["unsafe"] for r in rows) == saved["unsafe"] and
                sum(r["safe_target_met"] for r in rows) == saved["safe_target_met"], "Prospective saved axis mismatch")
        require(all(r["budget_or_policy_modified"] is False for r in rows), "Frozen policy modified")
        axes[arm] = saved
    terminal = [{"condition_id": c["condition"]["condition_id"], "status": c["status"],
                 "unsafe": None, "new_science_actions": c["new_science_actions"]}
                for c in p["conditions"] if not c["scored"]]
    require({r["condition_id"] for r in terminal} == {"LiH_R1.40", "LiH_R2.60", "LiF_R2.60"}, "Prospective ineligible record changed")
    require(all(r["new_science_actions"] == 0 for r in terminal), "Ineligible condition rescue")
    require(all(r["M1_frozen_abstained"] is True and r["M1_accepted_performance"] is False for r in p["coordinate_scores"]), "Prospective adoption changed")
    require(all(r["PF_H_reference_decomposition"]["status"] == "indeterminate" for r in p["coordinate_scores"]), "Unconfirmed prospective decomposition")
    prospective = {
        "denominators": p["denominators"], "families": sorted({c["condition"]["family"] for c in p["conditions"]}),
        "selected_frozen_decisions": axes, "terminal_records": terminal,
        "M1_formal_candidate_abstentions": p["M1_candidate_abstentions_preserved"],
        "M1_formal_condition_abstentions": p["M1_condition_abstentions_preserved"],
        "M1_accepted_performance_count": p["M1_accepted_performance_count"],
        "M1_empirical_width_diagnostic_covers": p["empirical_width_diagnostic_covered"],
        "branch_gap_compatible_diagnostics_not_absolute_branch_confirmation": p["branch_gap_diagnostic_compatible"],
        "decomposition_indeterminate": 39,
        "CH2_stratum": p["CH2_stratum"], "CH2_ground_claim": p["CH2_ground_claim"],
    }
    require(p["M1_candidate_abstentions_preserved"] == 39 and p["M1_condition_abstentions_preserved"] == 13, "Prospective abstention count")
    # These are native contracts, not a normalized or rescored common experiment.
    return {
        "status": STATUS, "direction": "C_unchanged_user_approved",
        "evidence_class": "post_hoc_documentation_of_committed_scalar_results",
        "new_scientific_actions": 0, "source_rescoring": False, "source_policy_changed": False,
        "Hchain_new_science_authorized": False, "Track_R_G_completion_user_accepted": True,
        "pooled_independent_sample_count": None, "pooled_success_rate": None,
        "native_main_analysis": native, "hchain_series": series_block,
        "h6_geometry": geometry, "rank_diagnostics": rank_block, "prospective": prospective,
        "overlap": [
            "Track G H6 R1.00 anchor: 3 truth coordinates reused from native H6",
            "Track R: 9 truth coordinates reused from native H6/H7/H8; 36 rows are rank diagnostics",
            "Candidates within a condition and conditions within a family are not independent samples",
        ],
        "contracts": {
            "HF": {"times": "T0, 1.3*T0, 1.6*T0", "B0": "inherited first-study benchmark"},
            "HCl": {"times": "0.5,0.65,0.8*t_ana", "B0": "no shared B0 in this native comparison"},
            "Hchain_and_G": {"times": "0.5,0.65,0.8*t_ref", "B0": "0.5*t_ref; gamma1.01"},
            "prospective": {"times": "0.8,1.0,1.2*t_ref", "B0": "0.8*t_ref; gamma1.10; benchmark not safe fallback"},
        },
        "limits": [
            "gamma1 is post-hoc; use additive safety slack, not a zero-margin ratio",
            "empirical width coverage is not a certificate",
            "cost-free oracle headroom excludes acquisition cost; no net-cost claim",
            "H6 small-margin sufficiency is not general-molecule generalization or a pure contract-matched causal test",
            "PF/H-reference decomposition requires verified same H, sector, energy origin and physical absolute branch",
            "Scientific results stay frozen; any new science needs separate GPT/user authorization",
        ],
    }


def verify_source_publication(root):
    fetch_url = git(root, "remote", "get-url", "origin").decode().strip()
    push_urls = git(root, "remote", "get-url", "--push", "--all", "origin").decode().splitlines()
    allowed_urls = {f"git@github.com:{REPOSITORY}.git", f"https://github.com/{REPOSITORY}.git"}
    require(fetch_url in allowed_urls and push_urls and all(u in allowed_urls for u in push_urls),
            "Origin is not the explicitly allowed HIROMU1015 repository")
    observed = git(root, "ls-remote", "--heads", "origin",
                   *("refs/heads/" + branch for branch in BRANCHES.values())).decode().splitlines()
    tips = {line.split()[1]: line.split()[0] for line in observed}
    records = []
    for snapshot, branch in BRANCHES.items():
        ref = "refs/heads/" + branch
        require(tips.get(ref) == snapshot, f"Source remote tip differs: {branch}")
        records.append({"branch": branch, "remote_tip_commit": tips[ref],
                        "verified_snapshot_commit": snapshot, "remote_tip_matches_snapshot": True})
    return {"audit_stage": "source_visibility_before_new_handoff_push",
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "fetch_url": fetch_url, "push_urls": push_urls, "sources": records,
            "new_handoff_branch_publication": "pending_separate_nonforce_push_and_remote_byte_gate"}


def write_package(root, output):
    require(not output.exists(), "Use a new output directory; do not overwrite an evidence package")
    data, registry = read_sources(root)
    evidence = assemble(data)
    publication = verify_source_publication(root)
    output.mkdir(parents=True)
    for name, obj in (("evidence_scalars.json", evidence), ("source_registry.json", registry),
                      ("source_publication_audit.json", publication)):
        (output / name).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (output / "COMPLETE.json").write_text(json.dumps({
        "status": STATUS, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "source_blobs": len(registry), "source_byte_gates_passed": len(registry),
        "new_scientific_actions": 0, "next_science_authorized": False,
        "method": "stdlib JSON/CSV decoding and counting committed scalar outcomes; no scientific-module imports",
        "claims_pending_GPT_paper_integration_review": True,
    }, indent=2, sort_keys=True) + "\n")
    return evidence


def seal_publication_manifest(root):
    """Seal only explicitly enumerated review files; never rewrite a tracked manifest."""
    relative = ARTIFACT_DIR + "publication_manifest.json"
    tracked = git(root, "ls-files", "--", relative).decode().strip()
    require(not tracked, "Publication manifest is already tracked; do not rewrite its freeze")
    changed = git(root, "diff", "--name-only", P).decode().splitlines()
    require(set(changed) <= {"docs/current_research_status.md"}, "Unexpected inherited tracked-file change")
    manifest = {
        "status": STATUS, "self_excluded": relative,
        "base_snapshot_commit": P, "handoff_commit": "the_commit_containing_this_manifest_no_self_reference",
        "only_modified_inherited_file": "docs/current_research_status.md",
        "files": [{"path": path, "bytes": len((root / path).read_bytes()),
                   "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()} for path in PUBLICATION_FILES],
        "private_runtime_or_scientific_arrays_included": False,
    }
    (root / relative).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"manifest_files": len(PUBLICATION_FILES), "self_excluded": relative}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seal-publication-manifest", action="store_true")
    args = parser.parse_args()
    if args.seal_publication_manifest:
        require(args.output is None, "Do not mix output generation and publication sealing")
        seal_publication_manifest(args.project_root.resolve())
        return
    require(args.output is not None, "An explicit new output directory is required")
    evidence = write_package(args.project_root.resolve(), args.output.resolve())
    print(json.dumps({"status": evidence["status"], "new_scientific_actions": 0}))


if __name__ == "__main__":
    main()
