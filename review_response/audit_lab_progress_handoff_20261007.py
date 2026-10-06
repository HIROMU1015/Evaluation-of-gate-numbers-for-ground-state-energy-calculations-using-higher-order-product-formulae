"""Read-only source, freeze, document and public-package audit; no science runs."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/lab_progress_additional_validation_20261007"
DIRECTORIES = [ROOT / "artifacts" / name for name in (
    "lab_progress_h4_state_checks_20261007", "lab_progress_hf_cap_checks_20261007",
    "lab_progress_hchain_transfer_20261007", "lab_progress_additional_validation_20261007")]
DOCS = [ROOT / path for path in (
    "docs/research_outcomes/20261006/lab_progress_slide_outline.md",
    "docs/research_outcomes/20261006/verification_gaps_and_next_checks.md",
    "docs/research_outcomes/20261007/additional_validation_scope.md",
    "docs/research_outcomes/20261007/additional_validation_results.md")]
CODE = [ROOT / "review_response" / name for name in (
    "run_lab_progress_h4_state_checks_20261007.py",
    "audit_lab_progress_h4_spectral_proxy_20261007.py",
    "audit_lab_progress_h4_branch_correspondence_20261007.py",
    "run_lab_progress_hf_cap_checks_20261007.py",
    "run_lab_progress_hchain_transfer_20261007.py",
    "complete_lab_progress_hchain_transfer_20261007.py",
    "summarize_lab_progress_checks_20261007.py",
    "audit_lab_progress_handoff_20261007.py")]
CODE.append(ROOT / "review_tests/test_lab_progress_hchain_transfer_20261007.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def package_files() -> list[Path]:
    paths = set(DOCS + CODE)
    for directory in DIRECTORIES:
        paths.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return sorted(paths)


def audit_slide_scalar_explanations(outline: str) -> dict:
    """Check newly explained identities and table values using saved scalars."""
    epsilon = read(DIRECTORIES[0] / "protocol.json")["constants"]["epsilon_E_hartree"]
    one_term_records = read(ROOT / "artifacts/m3_one_two_term_model_comparison_server2_20260910_92df2db_cpu/summary.json")["records"]
    one_term = []
    for record in one_term_records:
        if record["condition"] not in ("H6", "H7") or record["formula"] != "current_m3":
            continue
        definition = record["models"]["original_one_term"]["definition"]
        time = definition["predicted_optimal_time"]
        error = abs(definition["a4"]) * time ** 4
        assert abs(error - epsilon / 5) < 1e-15
        assert abs(error - definition["predicted_error_hartree"]) < 1e-15
        one_term.append({"condition": record["condition"], "predicted_error_hartree": error})
    assert len(one_term) == 2

    bridge = list(csv.DictReader((DIRECTORIES[0] / "long_time_bridge.csv").open()))
    block = outline.split("### Slide 17：", 1)[1].split("### Slide 18：", 1)[0]
    table = [line for line in block.splitlines() if re.match(r"^\| (2\.147|3\.518)：", line)]
    assert len(table) == len(bridge) == 2
    totals = []
    keys = ("fit_component", "state_component", "proxy_component", "total_prediction_difference")
    for line, row in zip(table, bridge, strict=True):
        saved = [float(row[key]) for key in keys]
        assert abs(sum(saved[:3]) - saved[3]) < 1e-15
        assert abs(saved[3] - (float(row["model_signed_shift"]) - float(row["direct_shift_hartree"]))) < 1e-15
        cells = [cell.strip() for cell in line.strip("|").split("|")][1:]
        assert cells == [f"{value * 1e6:+.3f}".replace("-", "−") for value in saved]
        totals.append({"time": float(row["time_hartree_inverse"]),
                       "total_prediction_difference_hartree": saved[3],
                       "displayed_total_microhartree": cells[-1]})
    phase_difference = float(bridge[1]["time_hartree_inverse"]) * float(bridge[1]["direct_shift_hartree"])
    assert f"{phase_difference:.3g}" == "2.45e-05"

    hf_protocol = read(DIRECTORIES[1] / "protocol.json")
    beta = hf_protocol["qpe_beta"]
    assert hf_protocol["target_error_hartree"] == epsilon
    cap_checks = []
    for row in csv.DictReader((DIRECTORIES[1] / "joint_selection_scoring.csv").open()):
        direct = float(row["direct_error"])
        predicted = float(row["predicted_error"])
        actual = beta * int(row["rotations"]) / (float(row["selected_time"]) * (epsilon - direct))
        budget = float(row["budget"])
        total = direct + beta * int(row["rotations"]) / (float(row["selected_time"]) * budget)
        assert abs(actual / float(row["actual_required_cost"]) - 1) < 1e-12
        assert abs(total - float(row["total_error"])) < 1e-15
        assert (budget >= actual) == (total <= epsilon) == (row["precision_pass"] == "True")
        if float(row["cap"]) > 0.5:
            assert predicted < direct and budget < actual
        cap_checks.append({"condition": row["condition"], "cap": float(row["cap"]),
                           "predicted_error_hartree": predicted, "direct_error_hartree": direct,
                           "budget_over_required_cost": budget / actual,
                           "target_precision_met": total <= epsilon})
    assert len(cap_checks) == 6
    return {"epsilon_E": epsilon, "one_term_epsilon_over_five_identity": one_term,
            "h4_signed_decomposition_table": totals, "hf_joint_budget_checks": cap_checks,
            "h4_long_time_target_phase_difference_radians": phase_difference,
            "new_scientific_computations": 0, "model_refits": 0,
            "formal_results_modified": False}


def audit_followup_connection_sources(outline: str) -> dict:
    """Verify separately published source blobs and saved reference arithmetic."""
    registry = read(OUT / "followup_sources.json")
    repository = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
    assert registry["repository"] == repository
    assert registry["origin_and_verified_snapshot_roles_separate"]
    assert registry["new_scientific_computations"] == registry["model_refits"] == 0
    assert not registry["formal_results_modified"]
    public_tips = registry["public_branch_tips_verified_by_git_ls_remote"]
    for branch, tip in public_tips.items():
        assert len(tip) == 40
        # Remote availability was checked separately; this audit is local/read-only.
        git("merge-base", "--is-ancestor", tip, f"refs/remotes/origin/{branch}")

    blobs = {}
    sources = registry["sources"]
    assert len(sources) == 9
    for source in sources:
        origin = source["origin_result_commit"]
        snapshot = source["verified_snapshot_commit"]
        assert len(origin) == len(snapshot) == 40
        git("merge-base", "--is-ancestor", origin, snapshot)
        git("merge-base", "--is-ancestor", snapshot, public_tips[source["public_branch"]])
        name = source["path"]
        assert Path(name).suffix in (".md", ".json", ".csv") and ".runtime" not in Path(name).parts
        blob = git("show", f"{snapshot}:{name}")
        assert hashlib.sha256(blob).hexdigest() == source["sha256"]
        assert len(blob) == source["bytes"]
        assert git("rev-parse", f"{snapshot}:{name}").decode().strip() == source["git_blob_sha"]
        assert git("show", f"{origin}:{name}") == blob
        assert source["snapshot_github_url"] == f"https://github.com/{repository}/blob/{snapshot}/{name}"
        assert source["origin_github_url"] == f"https://github.com/{repository}/blob/{origin}/{name}"
        assert name not in blobs
        blobs[name] = blob
    source_urls = {source["snapshot_github_url"] for source in sources}
    referenced_urls = set(re.findall(r"\]\((https://github\.com/[^)]+/blob/9accc300ba7b8049ae9a1ef870ca4e7c0032e6ae/[^)]+)\)", outline))
    assert referenced_urls and referenced_urls <= source_urls

    c0 = "artifacts/pf_first_study_fs_c0_20261007/"
    outcome_path = "artifacts/pf_first_study_response_pilot_h4_phase_b_20261006_8ffa5c64/scientific_outcome.json"
    outcome = json.loads(blobs[outcome_path])
    assert outcome["outcome"] == "point_only" and not outcome["next_stage_started"]
    assert outcome["S_abs"]["A1"] < outcome["S_abs"]["A0"]
    assert outcome["S_abs"]["A2"] < outcome["S_abs"]["A0"]
    assert outcome["S_under"]["A0"] == outcome["S_under"]["A1"] == 0
    assert outcome["S_under"]["A2"] > 0
    readiness = json.loads(blobs[c0 + "GO_NO_GO_FOR_FS_C1.json"])
    assert readiness["status"] == "NO_GO_FOR_FS_C1"
    assert not any(readiness[key] for key in ("design_complete", "execution_ready", "science_authorized", "training_policy_resolved"))
    assert "TRAINING_BASELINE_CONFLICT" in {issue["id"] for issue in readiness["unresolved_issues"]}

    reference_rows = [row for row in csv.DictReader(io.StringIO(blobs[c0 + "H4_posthoc_decision_scale.csv"].decode()))
                      if float(row["time"]) == 0.4]
    assert len(reference_rows) == 3
    savings = {}
    for row in reference_rows:
        epsilon = float(row["epsilon_E"])
        ratio = (epsilon - float(row["c_A0"])) / (epsilon - float(row["c_method"]))
        assert abs(ratio - float(row["reference_budget_ratio"])) < 1e-15
        assert abs(1 - ratio - float(row["reference_saving"])) < 1e-15
        assert float(row["gamma"]) == 1.01
        savings[row["arm"]] = 100 * (1 - ratio)
    assert f"{savings['A2']:.3f}" == "0.013" and f"{savings['A1']:.3f}" == "0.012"
    return {"registry": "followup_sources.json", "source_entries": sources,
            "published_source_branches": public_tips,
            "source_origin_commits_in_their_published_branch_histories": True,
            "sources_copied_or_regenerated": False,
            "H4_formal_outcome": outcome["outcome"],
            "H4_posthoc_same_time_same_margin_saving_percent": savings,
            "intervention_execution_readiness": readiness["status"],
            "intervention_design_complete": readiness["design_complete"],
            "intervention_science_authorized": readiness["science_authorized"],
            "third_study_start_claimed": False,
            "new_scientific_computations": 0, "model_refits": 0}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = "869806ff9995b76ef2786ca7b57b9acc02c2731f"
    source_registry = []
    for directory in DIRECTORIES[:3]:
        for source in read(directory / "protocol.json")["source_registry"]:
            assert len(source["origin_result_commit"]) == 40
            assert len(source["verified_snapshot_commit"]) == 40
            path = ROOT / source["path"]
            assert digest(path) == source["sha256"]
            blob = git("show", f"{source['verified_snapshot_commit']}:{source['path']}")
            assert hashlib.sha256(blob).hexdigest() == source["sha256"]
            assert git("merge-base", "--is-ancestor", source["origin_result_commit"], snapshot) == b""
            source_registry.append({**source, "used_by": str(directory.relative_to(ROOT))})

    manifest_counts = {}
    for directory in DIRECTORIES[:3]:
        manifest = read(directory / "manifest.json")
        if isinstance(manifest.get("files"), list):
            records = {str((directory / r["path"]).relative_to(ROOT)): r["sha256"] for r in manifest["files"]}
            assert manifest["manifest_self_excluded"]
        else:
            records = manifest.get("hashes", manifest.get("files"))
            assert str((directory / "manifest.json").relative_to(ROOT)) in manifest["self_excluded"]
        for name, expected in records.items():
            assert digest(ROOT / name) == expected, name
        manifest_counts[str(directory.relative_to(ROOT))] = len(records)

    links = []
    for doc in DOCS + [d / "report.md" for d in DIRECTORIES[:3]]:
        body = doc.read_text()
        assert body.count("$$") % 2 == 0, doc
        for target in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", body):
            if re.match(r"(?:https?://|#)", target):
                continue
            relative = target.split("#", 1)[0]
            destination = (doc.parent / relative).resolve()
            # Two audit outputs are created after this read-only validation.
            assert destination.is_file() or destination in (OUT / "handoff_checks.json", OUT / "manifest.json"), target
            links.append({"document": str(doc.relative_to(ROOT)), "target": target})
    outline = DOCS[0].read_text()
    scalar_explanations = audit_slide_scalar_explanations(outline)
    followup_sources = audit_followup_connection_sources(outline)
    slides = re.findall(r"^### Slide (\d+)：(.+)$", outline, re.M)
    index = re.findall(r"^\| (\d+) \| (.+) \|$", outline, re.M)
    assert slides == index and [int(n) for n, _ in slides] == list(range(1, 30))
    assert len(re.findall(r"^### A\d+：", outline, re.M)) == 3
    registry_ids = set(re.findall(r"^\| (E\d+) \|", outline, re.M))
    assert registry_ids == {f"E{n:02}" for n in range(1, 24)}
    widths = []
    for line in outline.splitlines():
        if line.startswith("|"):
            # TeX absolute values contain literal pipes inside math spans.
            width = len(re.sub(r"\$[^$]*\$", "MATH", line).split("|"))
            widths.append(width)
            assert width == widths[0], line
        else:
            widths = []

    self_excluded = [str((OUT / n).relative_to(ROOT)) for n in ("handoff_checks.json", "manifest.json")]
    paths = [p for p in package_files() if str(p.relative_to(ROOT)) not in self_excluded]
    allowed = {".json", ".csv", ".md", ".py", ".png", ".pdf", ""}
    for p in paths:
        assert p.suffix in allowed and ".runtime" not in p.parts and "__pycache__" not in p.parts, p
        assert p.stat().st_size < 50_000_000, p
    existing_linked_blobs = {}
    for link in links:
        path = (ROOT / link["document"]).parent / link["target"].split("#", 1)[0]
        path = path.resolve()
        if path in paths or path in (OUT / "handoff_checks.json", OUT / "manifest.json"):
            continue
        name = str(path.relative_to(ROOT))
        blob = git("show", f"{snapshot}:{name}")
        assert hashlib.sha256(blob).hexdigest() == digest(path), name
        existing_linked_blobs[name] = {"sha256": digest(path), "verified_snapshot_commit": snapshot,
                                      "origin_result_commit_source": "existing E01-E16 registry or participant source registry"}
    checks = {"schema": "lab_progress_additional_handoff_audit_v1",
              "source_registry": source_registry, "verified_input_snapshot": snapshot,
              "source_origin_commits_in_public_branch_history": True,
              "participant_manifest_counts": manifest_counts, "local_links": links,
              "existing_linked_blobs": existing_linked_blobs,
              "slide_count": len(slides), "appendix_count": 3, "evidence_id_count": len(registry_ids),
              "numeric_audit": "cross_checks.json", "scientific_computations_in_this_script": 0,
              "slide_scalar_explanations": scalar_explanations,
              "followup_connection": followup_sources,
              "matrix_vector_pickle_runtime_publication_count": 0,
              "generated_python_bytecode_excluded": True,
              "audit_hash_self_excluded": self_excluded,
              "public_files": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p),
                                "bytes": p.stat().st_size} for p in paths],
              "handoff_commit": "supplied in final handoff; verify remote commit and all blobs after publication"}
    (OUT / "handoff_checks.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    all_paths = [p for p in package_files() if p != OUT / "manifest.json"]
    manifest = {"self_excluded": [str((OUT / "manifest.json").relative_to(ROOT))],
                "files": {str(p.relative_to(ROOT)): digest(p) for p in all_paths},
                "source_registry": "handoff_checks.json: origin_result_commit and verified_snapshot_commit are separate",
                "publication_policy": "scalar, code, protocol, report, figures only"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"public_files": len(all_paths) + 1, "source_entries": len(source_registry),
                      "links": len(links), "slides": len(slides), "participant_manifests": manifest_counts}))


if __name__ == "__main__":
    main()
