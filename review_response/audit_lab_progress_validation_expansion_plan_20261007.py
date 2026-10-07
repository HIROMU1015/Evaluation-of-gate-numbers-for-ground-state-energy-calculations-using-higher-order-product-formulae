#!/usr/bin/env python3
"""Audit a proposal catalog using public saved scalars only; never run science."""
import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = "1d01e77247364b49dbce2e9ce2fe7c32af0fb937"
RESULT = "8436a2f3644e0403ff5ebf19bee6caae364ae66e"
REPO = "HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
OUT = ROOT / "artifacts/lab_progress_validation_expansion_plan_20261007"
DOC = "docs/research_outcomes/20261007/validation_expansion_candidates.md"
SCRIPT = "review_response/audit_lab_progress_validation_expansion_plan_20261007.py"
PUBLIC_SOURCES = [
    "AGENTS.md",
    "docs/research_outcomes/20261006/lab_progress_slide_outline.md",
    "docs/research_outcomes/20261007/additional_validation_results.md",
    "docs/research_outcomes/20261007/additional_validation_scope.md",
    "PF_first_study_protocol_20260925.json",
    "artifacts/pf_first_study_phase_a_20260925_6265243/phase_a_proxy_models.csv",
    "artifacts/pf_first_study_phase_a_20260925_6265243/phase_a_proxy_observables.csv",
    "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/dominance_summary.csv",
    "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/state_diagnostics.csv",
    "artifacts/lab_progress_h4_state_checks_20261007/report.md",
    "artifacts/lab_progress_h4_state_checks_20261007/training_proxies.csv",
    "artifacts/lab_progress_h4_state_checks_20261007/long_time_bridge.csv",
    "artifacts/lab_progress_h4_state_checks_20261007/direct_grid.csv",
    "artifacts/lab_progress_h4_state_checks_20261007/spectral_checks.json",
    "artifacts/lab_progress_hchain_transfer_20261007/report.md",
    "artifacts/lab_progress_hchain_transfer_20261007/protocol.json",
    "artifacts/lab_progress_hchain_transfer_20261007/canonical_long_time_error_decomposition.csv",
    "artifacts/lab_progress_hchain_transfer_20261007/H5/direct_grid_m5_best.csv",
    "artifacts/lab_progress_hchain_transfer_20261007/H6/direct_grid_m5_best.csv",
    *[f"artifacts/lab_progress_hchain_transfer_20261007/H6/truth_{pf}.json"
      for pf in ("current_m3", "two_term_center", "m5_best", "yoshida4")],
    "artifacts/lab_progress_hf_cap_checks_20261007/report.md",
    "artifacts/lab_progress_hf_cap_checks_20261007/joint_selection_scoring.csv",
    "artifacts/lab_progress_additional_validation_20261007/followup_sources.json",
    "artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/report.md",
    "artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md",
    "docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md",
    "docs/second_study_v2/result_synthesis_20261005/approved_gpt_review.md",
]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text())


def read_csv(path):
    with (ROOT / path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def source_entry(path, origin=None):
    data = (ROOT / path).read_bytes()
    assert data == git("show", f"{BASE}:{path}"), f"source changed: {path}"
    if origin is None:
        origin = git("log", BASE, "--diff-filter=A", "-1", "--format=%H", "--", path).decode().strip()
    assert re.fullmatch(r"[0-9a-f]{40}", origin), path
    # Public file origin and verified snapshot remain separate, even if equal.
    entry = dict(path=path, origin_result_commit=origin,
                 origin_role="public_file_origin", verified_snapshot_commit=BASE,
                 git_blob_sha=git("rev-parse", f"{BASE}:{path}").decode().strip(),
                 sha256=digest(data), bytes=len(data),
                 snapshot_github_url=f"https://github.com/{REPO}/blob/{BASE}/{path}")
    if any(path.startswith(f"artifacts/{prefix}") for prefix in (
            "lab_progress_h4_state_checks_", "lab_progress_hchain_transfer_", "lab_progress_hf_cap_checks_")):
        entry["science_result_origin_commit"] = RESULT
    return entry


def build_registry():
    sources = [source_entry(p) for p in PUBLIC_SOURCES]
    external = read_json("artifacts/lab_progress_additional_validation_20261007/followup_sources.json")["sources"]
    for item in external:
        data = git("show", f"{item['verified_snapshot_commit']}:{item['path']}")
        assert digest(data) == item["sha256"]
        assert len(data) == item["bytes"]
        assert git("rev-parse", f"{item['verified_snapshot_commit']}:{item['path']}").decode().strip() == item["git_blob_sha"]
        sources.append({**item, "reference_kind": "existing_external_branch_snapshot"})
    return dict(schema="validation_expansion_source_registry_v1", repository=REPO,
                origin_and_snapshot_roles_separate=True, sources=sources,
                private_arrays_read_or_published=False,
                new_scientific_computations=0, model_refits=0)


def build_checks():
    proto = read_json("PF_first_study_protocol_20260925.json")
    track = proto["experiment_B_h4"]["fixed_time_mechanism_track"]
    dominance = read_csv("artifacts/pf_first_study_phase_b_20260925_5a2f0a2/dominance_summary.csv")
    h4 = [r for r in dominance if r["experiment_id"] == "B"]
    h4_counts = dict(Counter(r["dominant_component"] for r in h4))
    all_counts = dict(Counter(r["dominant_component"] for r in dominance))
    assert len(h4) == 56 and h4_counts["E_state_hartree"] == 49
    assert len(dominance) == 128 and all_counts["E_state_hartree"] == 79
    models = read_csv("artifacts/pf_first_study_phase_a_20260925_6265243/phase_a_proxy_models.csv")
    bm = [r for r in models if r["experiment_id"] == "B"]
    assert len(bm) == 168 and len({r["model_id"] for r in bm}) == 3
    diag = read_csv("artifacts/pf_first_study_phase_b_20260925_5a2f0a2/state_diagnostics.csv")
    overlaps = {r["state_id"]: float(r["exact_overlap_probability"])
                for r in diag if r["state_id"] in ("rhf", "cisd")}
    assert abs(overlaps["rhf"] - 0.9364638563852806) < 1e-14
    assert abs(overlaps["cisd"] - 0.9994668439213916) < 1e-14
    bridge = read_csv("artifacts/lab_progress_h4_state_checks_20261007/long_time_bridge.csv")
    for row in bridge:
        total = sum(float(row[k]) for k in ("fit_component", "state_component", "proxy_component"))
        assert abs(total - float(row["total_prediction_difference"])) < 1e-12
    chain_proto = read_json("artifacts/lab_progress_hchain_transfer_20261007/protocol.json")
    h6_input = next(r for r in chain_proto["systems"] if r["system"] == "H6")
    assert h6_input["input_identity"]["sector_dimension"] == 400
    chain = {}
    for system in ("H5", "H6"):
        rows = read_csv(f"artifacts/lab_progress_hchain_transfer_20261007/{system}/direct_grid_m5_best.csv")
        good = [r for r in rows if r["branch_reliable"] == "True" and
                r["direct_cost"] and math.isfinite(float(r["direct_cost"])) and float(r["direct_cost"]) > 0]
        first_bad = next(r for r in rows if r["branch_reliable"] == "False")
        assert float(first_bad["ground_overlap"]) < 0.9 and float(first_bad["previous_overlap"]) < 0.9
        chain[system] = dict(candidate_count=len(rows),
                            first_unreliable_saved_point=first_bad,
                            pointwise_reliable_minimum=min(good, key=lambda r: float(r["direct_cost"])))
    assert abs(float(chain["H6"]["pointwise_reliable_minimum"]["time"]) - 2.2834071119880326) < 1e-14
    resources = {pf: read_json(f"artifacts/lab_progress_hchain_transfer_20261007/H6/truth_{pf}.json")["resource"]
                 for pf in ("current_m3", "two_term_center", "m5_best", "yoshida4")}
    hf = read_csv("artifacts/lab_progress_hf_cap_checks_20261007/joint_selection_scoring.csv")
    assert len(hf) == 6 and sum(r["precision_pass"] == "True" for r in hf) == 2
    hf_margins = [dict(condition=r["condition"], cap=float(r["cap"]),
                       saved_precision_pass=r["precision_pass"] == "True",
                       post_hoc_required_cost_over_predicted_cost=float(r["actual_required_cost"]) / float(r["predicted_cost"]))
                  for r in hf]
    c0_path = "artifacts/pf_first_study_fs_c0_20261007/GO_NO_GO_FOR_FS_C1.json"
    c0 = json.loads(git("show", f"9accc300ba7b8049ae9a1ef870ca4e7c0032e6ae:{c0_path}"))
    assert c0["status"] == "NO_GO_FOR_FS_C1" and not c0["science_authorized"]
    proposals = read_json(str((OUT / "proposed_scopes.json").relative_to(ROOT)))
    assert not proposals["candidate_science_authorized"] and proposals["model_refits"] == 0
    candidates = {x["candidate_id"]: x for x in proposals["candidates"]}
    assert set(candidates) == {f"A{i}" for i in range(1, 9)}
    assert all(x["status"] == "draft_not_authorized_for_execution" and not x["science_executed"] for x in candidates.values())
    a1 = candidates["A1"]["proposed_scope"]
    assert a1["training_time_magnitudes"] == track["training_time_magnitudes_hartree_inverse"]
    assert a1["evaluation_time_magnitudes"] == track["evaluation_time_magnitudes_hartree_inverse"]
    assert a1["models"] == track["model_fits"]
    assert a1["case_count"] == 4 * (2 + 3 * 4) == 56
    assert a1["evaluation_row_count"] == 56 * 6 * 2 == 672
    assert a1["distinct_pf_time_coordinates"] == 4 * (5 + 6) * 2 == 88
    assert a1["proposed_max_full_pf_builds_with_two_cold_runs"] == 176
    a6 = candidates["A6"]["proposed_scope"]
    old_grid = read_csv("artifacts/lab_progress_h4_state_checks_20261007/direct_grid.csv")
    old_times = [float(r["time_hartree_inverse"]) for r in old_grid if r["formula_id"] == "m5_best"]
    matched = sum(any(abs(t - s) < 1e-12 for s in old_times) for t in a6["proposed_nine_point_grid"])
    assert matched == 3 and 9 - matched == a6["distinct_new_coordinates"] == 6
    return dict(schema="saved_scalar_expansion_checks_v1", verified_snapshot_commit=BASE,
                new_scientific_computations=0, model_refits=0, formal_results_modified=False,
                H4_short_time=dict(case_count=56, dominance_counts=h4_counts,
                                   all_case_count=128, all_dominance_counts=all_counts,
                                   saved_model_count=168, physical_state_overlap_squared=overlaps),
                H4_long_time_bridge=bridge, H6_input_identity_from_public_protocol=h6_input["input_identity"],
                H5_H6_saved_branch_checks=chain, H6_historical_runtime_per_formula=resources,
                HF_post_hoc_same_point_margin=hf_margins,
                FS_C0_status_at_referenced_snapshot=c0,
                proposal_scope_arithmetic_passed=True,
                limitations=["Historical runtimes do not predict new experiment wall time.",
                             "No private arrays are loaded or produced by this audit.",
                             "Pointwise branch validity does not establish correspondence at unconfirmed selected points.",
                             "HF post-hoc margins are not a validated new policy."])


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def run(write):
    registry, checks = build_registry(), build_checks()
    for name, value in (("source_registry.json", registry), ("saved_evidence_checks.json", checks)):
        path = OUT / name
        if write:
            path.write_bytes(json_bytes(value))
        else:
            assert path.read_bytes() == json_bytes(value), f"stale audit: {name}"
    links = re.findall(r"\]\(([^)]+)\)", (ROOT / DOC).read_text())
    for link in links:
        if link.startswith("https://"):
            continue
        target = (ROOT / DOC).parent / unquote(link.split("#")[0])
        # The self-excluded manifest is produced below.
        assert target.exists() or target.resolve() == OUT / "manifest.json", str(target)
    files = [DOC, SCRIPT, *[str((OUT / name).relative_to(ROOT)) for name in (
        "proposed_scopes.json", "source_registry.json", "saved_evidence_checks.json")]]
    manifest = dict(schema="validation_expansion_manifest_v1", verified_source_snapshot=BASE,
                    self_excluded="manifest.json is excluded from its own file hash list",
                    files=[dict(path=p, sha256=digest((ROOT / p).read_bytes()),
                                bytes=(ROOT / p).stat().st_size) for p in files],
                    documentation_link_count=len(links), source_reference_count=len(registry["sources"]),
                    new_scientific_computations=0, model_refits=0)
    if write:
        (OUT / "manifest.json").write_bytes(json_bytes(manifest))
    else:
        assert (OUT / "manifest.json").read_bytes() == json_bytes(manifest), "stale manifest"
    print(json.dumps(dict(status="PASS", source_references=len(registry["sources"]),
                          candidates=8, new_scientific_computations=0, model_refits=0,
                          manifest_hashed_files=len(files), local_links_verified=True)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write new audit artifacts; default verifies")
    run(parser.parse_args().write)
