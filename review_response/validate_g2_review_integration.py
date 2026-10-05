"""Read-only validation of the post-G2 review bundle; no acquisition or replay."""
import argparse
import ast
import csv
import hashlib
import io
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

BASE = "56d42b137c315f0ad058f4ec8bb07396e9da47b1"
BUNDLE = "docs/second_study_v2/research_review_integration_after_g2_20261005"
PARENT = "docs/second_study_v2/research_direction_review_after_hchain_20261005"
G2 = "artifacts/hf_g2_fixed_rule_replay_20261005"
SCRIPT = "review_response/validate_g2_review_integration.py"
STATUS = "second_study_v2_g2_review_integration_complete_review_required"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root):
    root = root.resolve()

    def raw(path):
        resolved = (root / path).resolve()
        require(resolved.is_relative_to(root), "path escaped project: " + path)
        require(".runtime" not in resolved.parts, "runtime access forbidden")
        return resolved.read_bytes()

    def obj(path):
        return json.loads(raw(path))

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args])

    def source_check(record):
        data = raw(record["path"])
        require(len(data) == record["bytes"], "bytes: " + record["path"])
        require(hashlib.sha256(data).hexdigest() == record["sha256"],
                "hash: " + record["path"])
        require(data == git("show", BASE + ":" + record["path"]),
                "snapshot: " + record["path"])
        require(data == git("show", record["origin_result_commit"] + ":" + record["path"]),
                "origin: " + record["path"])

    def manifest_check(path, scope):
        value = obj(path)
        require(value["manifest_self_excluded"] is True, "self exclusion")
        require(value["file_count"] == len(value["files"]), "manifest count")
        require(len({r["path"] for r in value["files"]}) == len(value["files"]),
                "duplicate manifest path")
        for record in value["files"]:
            data = raw(str(pathlib.PurePosixPath(scope) / record["path"]))
            require(len(data) == record["bytes"], "manifest bytes")
            require(hashlib.sha256(data).hexdigest() == record["sha256"],
                    "manifest hash")
        return len(value["files"])

    registry = obj(BUNDLE + "/source_registry.json")
    require(registry["verified_snapshot_commit"] == BASE, "registry base")
    require(len(registry["sources"]) == registry["source_count"] == 29,
            "direct source count")
    ids = {s["id"] for s in registry["sources"]}
    require(len(ids) == 29, "source IDs")
    for record in registry["sources"]:
        require(record["verified_snapshot_commit"] == BASE, "source snapshot")
        source_check(record)
    inherited = obj(PARENT + "/source_registry.json")
    require(len(inherited["sources"]) == 37, "inherited source count")
    for record in inherited["sources"]:
        source_check(record)
    ids.update(s["id"] for s in inherited["sources"])

    manifests = {
        "parent_content": manifest_check(PARENT + "/manifest.json", PARENT),
        "parent_publication": manifest_check(PARENT + "/publication_manifest.json", PARENT),
        "G2_result": manifest_check(G2 + "/result/manifest.json", G2 + "/result"),
        "G2_publication": manifest_check(G2 + "/publication/publication_manifest.json", G2),
    }
    freeze_count = {}
    for stage, commit in (
        ("cheap", "50d0293d8f03541913a4d2a9c924336e8df9a1a1"),
        ("h1", "d4c5e78cac5fa9cc7be6de4c15c0022a49009638"),
        ("prediction", "0b4dca38bac1aa2c1b70d60702a72e378c5e4b3b"),
    ):
        scope = G2 + "/" + stage
        manifests["G2_" + stage] = manifest_check(scope + "/manifest.json", scope)
        files = [r["path"] for r in obj(scope + "/manifest.json")["files"]]
        files.append("manifest.json")
        for name in files:
            path = scope + "/" + name
            require(raw(path) == git("show", commit + ":" + path), "freeze changed")
        freeze_count[stage] = len(files)

    original = list(csv.DictReader(io.StringIO(raw(PARENT + "/evidence_matrix.csv").decode())))
    rows = list(csv.DictReader(io.StringIO(raw(BUNDLE + "/evidence_matrix.csv").decode())))
    require(len(original) == 24 and len(rows) == 27, "matrix dimensions")
    require(rows[:24] == original, "inherited row values changed")
    require(len({r["row_id"] for r in rows}) == 27, "duplicate matrix row")
    for row in rows:
        require(None not in row and None not in row.values(), "invalid CSV fields")
        require(set(row["source_ids"].split(";")) <= ids, "unresolved source ID")

    result = obj(G2 + "/result/result.json")
    decision = obj(BUNDLE + "/decision.json")
    require(result["classification"] == decision["G2"]["classification"] ==
            "D_gate_false_negative", "G2 classification")
    require(result["classification_is_not_original_S1A_taxonomy"], "taxonomy scope")
    require(result["q_acquisition_count"] == result["decision_change_count"] == 0,
            "acquisition/decision counts")
    require([c["q"] for c in result["condition_scores"]] == [0, 0], "q")
    require([c["B2"]["safe_and_valid"] for c in result["condition_scores"]] ==
            [False, True], "safety outcomes")
    require(result["aggregates"]["always_M1"]["safe_and_valid_count"] == 2,
            "M1 safe count")
    require(result["aggregates"]["B0"]["safe_and_valid_count"] == 2, "B0 safe count")
    require(all(c["T0_reproduction_pass"] for c in result["condition_scores"]),
            "T0 control")
    require(all(c["B2"] == c["H1"] for c in result["condition_scores"]), "H1 != B2")
    diagnostics = result["coordinate_diagnostics"]
    require(len(diagnostics) == 6 and
            all(x["M1_physical_branch_correct"] and x["M1_empirical_width_covers"]
                for x in diagnostics), "branch/width diagnostics")
    for row, score in zip(rows[24:26], result["condition_scores"]):
        selected = next(x for x in diagnostics if
                        x["candidate_id"] == score["B2"]["candidate_id"])
        condition_rows = [x for x in diagnostics if x["condition"] == score["condition"]]
        require(row["system_condition"] == score["condition"], "condition")
        require(float(row["cheap_frozen_budget"]) ==
                score["B2"]["frozen_continuous_budget"], "B2 matrix")
        require(float(row["M1_frozen_budget"]) ==
                score["always_M1"]["frozen_continuous_budget"], "M1 matrix")
        require(float(row["B0_budget"]) == score["B0"]["frozen_continuous_budget"],
                "B0 matrix")
        require(row["safety"] == score["outcome"], "matrix safety")
        require(float(row["M1_absolute_point_error_Ha"]) == selected["E_M_hartree"],
                "selected point error")
        require(float(row["M1_width_Ha"]) == selected["M1_width_hartree"],
                "selected width")
        require(float(row["B2_H1_budget_over_B0"]) == score["B2"]["B_over_B0"],
                "budget ratio")
        require(int(row["M1_point_improved_coordinate_count"]) ==
                sum(x["E_M_hartree"] < x["E_C_hartree"] for x in condition_rows),
                "point improvement count")
        require(int(row["M1_abstention_count"]) ==
                sum(x["M1_abstained"] for x in condition_rows), "abstention count")
        require(int(row["branch_pass_count"]) ==
                sum(x["M1_physical_branch_correct"] for x in condition_rows),
                "branch count")
        require(int(row["empirical_width_cover_count"]) ==
                sum(x["M1_empirical_width_covers"] for x in condition_rows),
                "width coverage count")
    require(result["resource_value"]["combined_cost_status"] ==
            "combined_cost_not_evaluable", "cost overclaim")
    require(decision["status"] == STATUS and decision["evidence_class"] ==
            "governance_scope", "review status")
    require(decision["Direction_C_provisionally_approved"], "provisional C")
    for key in ("final_research_direction_approved", "RQ_finalized", "novelty_finalized",
                "scientific_execution_authorized", "gate_redesign_authorized",
                "current_research_status_update_authorized", "push_authorized",
                "push_performed"):
        require(decision[key] is False, "authority or finality: " + key)
    for key in ("new_scientific_computation_count", "real_replay_or_scorer_reruns",
                "threshold_or_gamma_changes", "new_PF_H_actions", "new_Arnoldi",
                "new_truth_gap", "GPU_operations"):
        require(decision[key] == 0, "scope counts: " + key)
    require(decision["automatic_next_steps"] == [], "automatic followup")

    links = 0
    for page in (root / BUNDLE).glob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", page.read_text()):
            require(not target.startswith(("http:", "https:")), "new web claim")
            destination = (page.parent / target.split("#")[0]).resolve()
            require(destination.is_relative_to(root) and destination.exists(),
                    "broken local link: " + target)
            links += 1
    require(raw("docs/current_research_status.md") ==
            git("show", BASE + ":docs/current_research_status.md"), "current status changed")
    changed = git("diff", "--name-status", BASE).decode().splitlines()
    require(all(line.startswith("A\t") and
                (line.split("\t", 1)[1].startswith(BUNDLE + "/") or
                 line.split("\t", 1)[1] == SCRIPT) for line in changed),
            "existing tracked file changed or out-of-scope addition")
    imports = {n.names[0].name.split(".")[0] for n in
               ast.walk(ast.parse(raw(SCRIPT))) if isinstance(n, ast.Import)}
    require(not imports & {"numpy", "scipy", "cupy", "torch", "jax"},
            "scientific imports")
    return {
        "schema": "post_G2_review_integration_validation_v1",
        "status": STATUS,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "verified_snapshot_commit": BASE,
        "all_checks_passed": True,
        "validation_kind": "read_only_hash_Git_CSV_scalar_mapping_and_links_not_scoring",
        "direct_origin_snapshot_sources_verified": 29,
        "inherited_origin_snapshot_sources_verified": 37,
        "inherited_matrix_rows_verified": 24,
        "integrated_matrix_rows": 27,
        "G2_added_rows": 3,
        "G2_condition_budget_triplets_verified": 2,
        "G2_freeze_files_byte_identity": freeze_count,
        "upstream_manifest_payload_counts": manifests,
        "local_markdown_links_verified": links,
        "existing_tracked_files_unchanged": True,
        "current_research_status_unchanged": True,
        "new_scientific_computation_count": 0,
        "real_replay_or_scorer_reruns": 0,
        "full_legacy_tests_executed": False,
        "external_literature_rechecked": False,
        "q_one_combined_cost_measured": False,
        "remote_refs_checked": False,
        "push_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args()
    print(json.dumps(validate(args.project_root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
