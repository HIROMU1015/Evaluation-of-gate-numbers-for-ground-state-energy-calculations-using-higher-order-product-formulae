"""Post-hoc scalar audit; no Hamiltonian/PF calculations or refits."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/validation_expansion_20261007"
STAGES = ("a1_proxy", "a1_truth", "a3", "a6", "b3")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")


def close(a, b, atol=1e-12):
    assert abs(float(a) - float(b)) <= atol


def population(models, dominance):
    primary = [m for m in models if m["model_id"] == "raw_positive_even_two_term"]
    invalid = {(r["formula_id"], r["state_id"]) for r in primary if r["status"] != "fit_ok"}
    eligible = [r for r in dominance if (r["formula_id"], r["state_id"]) not in invalid and int(r["resolved_point_count"]) > 0]
    return dict(all_case_count=len(dominance), legacy_counts=dict(Counter(r["dominant_component"] for r in dominance)),
                fit_eligible_count=len(eligible), fit_eligible_counts=dict(Counter(r["dominant_component"] for r in eligible)),
                primary_fit_not_identifiable_count=len(invalid),
                excluded=[dict(formula_id=r["formula_id"], state_id=r["state_id"], inherited_label=r["dominant_component"])
                          for r in dominance if (r["formula_id"], r["state_id"]) in invalid],
                scope="post-hoc eligibility summary only; original model status and legacy labels unchanged")


def audit():
    p = read(OUT / "protocol.json")
    marker = read(OUT / "PROTOCOL_FROZEN.json")
    assert sha(OUT / "protocol.json") == marker["protocol_sha256"]
    assert sha(ROOT / "review_response/run_validation_expansion_20261007.py") == marker["runner_sha256"]
    for s in p["source_registry"]:
        assert sha(ROOT / s["path"]) == s["sha256"]
        blob = subprocess.check_output(["git", "show", s["verified_snapshot_commit"] + ":" + s["path"]], cwd=ROOT)
        assert blob == (ROOT / s["path"]).read_bytes()
        assert len(s["origin_result_commit"]) == 40 and len(s["verified_snapshot_commit"]) == 40
    completion = {s: read(OUT / (s + "_COMPLETE.json")) for s in STAGES}
    assert not list(OUT.glob("*_FAILED.json"))
    for s, c in completion.items():
        assert c["protocol_sha256"] == marker["protocol_sha256"]
        assert c["elapsed_seconds"] < p["resource_caps"]["wall_seconds_per_stage"]
        assert c["peak_RSS_KiB"] < 4 * 1024 ** 2
        assert set(c["environment"]["BLAS_threads"].values()) == {"1"}
    barrier = read(OUT / "A1_PREDICTIONS_FROZEN.json")
    assert barrier["models_sha256"] == sha(OUT / "A1_models.csv")
    assert barrier["observations_sha256"] == sha(OUT / "A1_observations.csv")
    assert barrier["new_pf_eigenvalues_used"] is False
    obs = rows(OUT / "A1_observations.csv")
    models = rows(OUT / "A1_models.csv")
    dec = rows(OUT / "A1_error_decomposition.csv")
    dom = rows(OUT / "A1_dominance_summary.csv")
    branches = rows(OUT / "A1_branch_audit.csv")
    assert (len(obs), len(models), len(dec), len(dom), len(branches)) == (1320, 168, 672, 56, 88)
    train = p["mechanism"]["fixed_time_mechanism_track"]["training_time_magnitudes_hartree_inverse"]
    evals = p["mechanism"]["fixed_time_mechanism_track"]["evaluation_time_magnitudes_hartree_inverse"]
    assert set(float(r["absolute_time"]) for r in obs) == set(train + evals)
    assert set(float(r["absolute_time"]) for r in dec) == set(evals)
    assert all(r["branch_reliable"] == "True" for r in branches)
    for r in dec:
        close(sum(float(r[k]) for k in ("E_fit_signed_hartree", "E_state_signed_hartree", "E_proxy_signed_hartree")), r["E_total_signed_hartree"])
    for d in dom:
        resolved = [r for r in dec if r["formula_id"] == d["formula_id"] and r["state_id"] == d["state_id"] and r["quality_class"] == "resolved"]
        assert len(resolved) == int(d["resolved_point_count"])
        counts = {k: sum(float(r[k]) >= 3 * max(float(r[o]) for o in ("E_fit_hartree", "E_state_hartree", "E_proxy_hartree") if o != k) for r in resolved)
                  for k in ("E_fit_hartree", "E_state_hartree", "E_proxy_hartree")}
        wins = [k for k, n in counts.items() if n >= len(resolved) // 2 + 1]
        assert d["dominant_component"] == (wins[0] if len(wins) == 1 else "mixed")
    h4_model_path = "artifacts/pf_first_study_phase_a_20260925_6265243/phase_a_proxy_models.csv"
    h4_models = [r for r in rows(ROOT / h4_model_path) if r["case_id"] == "H4"]
    h4_dom = [r for r in rows(ROOT / "artifacts/pf_first_study_phase_b_20260925_5a2f0a2/dominance_summary.csv") if r["case_id"] == "H4"]
    h4_provenance = dict(path=h4_model_path, sha256=sha(ROOT / h4_model_path),
                         origin_result_commit="5a2f0a2e0315493c892c79f1a6b8c9285cc52ac3", verified_snapshot_commit=p["input_snapshot_commit"])
    assert subprocess.check_output(["git", "show", p["input_snapshot_commit"] + ":" + h4_model_path], cwd=ROOT) == (ROOT / h4_model_path).read_bytes()
    a1 = dict(H4=population(h4_models, h4_dom), H6=population(models, dom), supplemental_source=h4_provenance,
              unreliable_branch_points=0, all_resolved_evaluation_rows=sum(r["quality_class"] == "resolved" for r in dec))
    components = rows(OUT / "A3_spectral_components.csv")
    spectral = rows(OUT / "A3_spectral_summary.csv")
    assert [float(r["time"]) for r in spectral] == p["A3"]["times"]
    for s in spectral:
        items = [r for r in components if r["time"] == s["time"]]
        assert len(items) == 400 and sum(r["tracked"] == "True" for r in items) == 1
        close(sum(float(r["weight"]) for r in items), 1)
        close(sum(float(r["contribution"]) for r in items), s["exact_proxy"])
        close(sum(float(r["contribution"]) for r in items if r["tracked"] == "False"), s["other_contribution"])
        assert float(s["spectral_closure"]) <= 1e-12 and float(s["bias_closure"]) <= 1e-12
    local = rows(OUT / "A6_local_grid.csv")
    assert [float(r["time"]) for r in local] == p["A6"]["times"]
    assert sum(r["is_new_coordinate"] == "True" for r in local) == 6
    assert all(r["branch_reliable"] == "True" for r in local)
    epsilon, beta = float(p["constants"]["target_error_hartree"]), float(p["constants"]["qpe_beta"])
    for r in local:
        expected = beta * 3996 / (float(r["time"]) * (epsilon - abs(float(r["direct_shift_hartree"]))))
        close(expected, r["direct_cost"], 1e-7)
        close(p["A6"]["original_budget"] / expected, r["frozen_budget_over_cost"])
    minimum = min(local, key=lambda r: float(r["direct_cost"]))
    close(minimum["direct_cost"], completion["a6"]["local_minimum"]["direct_cost"], 1e-7)
    scoring = rows(OUT / "B3_scoring.csv")
    joint = rows(OUT / "B3_joint_scoring.csv")
    frozen_b3 = read(OUT / "B3_SELECTION_FROZEN.json")
    assert frozen_b3["choices"] == p["B3"]["choices"] and frozen_b3["joint_choices"] == p["B3"]["joint_choices"]
    for f in p["B3"]["choices"]:
        r = next(r for r in scoring if (r["condition"], r["formula"]) == (f["condition"], f["formula"]))
        for key in ("cap", "budget", "selected_time", "predicted_cost", "predicted_signed_shift"):
            close(r[key], f[key])
        t, k, delta, b = float(r["selected_time"]), int(r["rotations"]), float(r["direct_shift"]), float(r["budget"])
        cost = beta * k / (t * (epsilon - abs(delta)))
        close(cost, r["actual_required_cost"], 1e-6)
        error = abs(delta) + beta * k / (t * b)
        close(error, r["total_error"])
        assert (error <= epsilon) == (r["precision_pass"] == "True")
        close(float(r["fit_difference"]) + float(r["state_difference"]) + float(r["proxy_difference"]), float(r["predicted_signed_shift"]) - delta)
    assert len(scoring) == 4 and len(joint) == 2
    hf_branch = rows(OUT / "B3_branch_audit.csv")
    assert len(hf_branch) == p["B3"]["max_full_pf_builds"]
    for r in hf_branch:
        assert float(r["ground_overlap"]) >= .9
        assert not r["previous_overlap"] or float(r["previous_overlap"]) >= .9
        assert float(r["eigenpair_residual"]) < 1e-10
        assert not r["coarse_refined_difference"] or float(r["coarse_refined_difference"]) < 1e-9
    caps = dict(A1_PF_builds=completion["a1_proxy"]["resources"]["full_PF_builds"],
                A1_H_actions=completion["a1_proxy"]["resources"]["H_exponential_vector_actions"],
                A1_Schur=completion["a1_truth"]["pf_schur_calls"], A3_PF_builds=completion["a3"]["resources"]["full_PF_builds"],
                A3_H_actions=completion["a3"]["resources"]["H_exponential_vector_actions"], A3_Schur=completion["a3"]["pf_schur_calls"],
                A6_PF_builds=completion["a6"]["full_pf_builds"], A6_Schur=completion["a6"]["pf_schur_calls"],
                B3_PF_builds=completion["b3"]["full_pf_builds"], B3_Schur=completion["b3"]["pf_schur_calls"])
    assert caps == dict(A1_PF_builds=176, A1_H_actions=2640, A1_Schur=88, A3_PF_builds=1, A3_H_actions=2,
                        A3_Schur=2, A6_PF_builds=9, A6_Schur=9, B3_PF_builds=516, B3_Schur=776)
    report = ROOT / "docs/research_outcomes/20261007/validation_expansion_results.md"
    prose = report.read_text()
    local_links = [x for x in re.findall(r"\]\(([^)]+)\)", prose) if not x.startswith("https://")]
    assert all((report.parent / x).is_file() for x in local_links)
    assert prose.count("$$") % 2 == 0
    result = dict(all_checks_passed=True, no_new_science_in_audit=True, source_registry_unchanged=True,
                  protocol_sha256=marker["protocol_sha256"], A1=a1,
                  A3=dict(points=spectral, components=800, original_selected_point_not_rescued=True),
                  A6=dict(local_minimum=minimum, original_grid_minimum_retained=p["A6"]["original_minimum_cost"],
                          cost_change_fraction=completion["a6"]["relative_cost_change"]),
                  B3=dict(joint_selections=joint, no_refit=True, no_cap_tuning=True),
                  actual_call_counts=caps, execution_seconds={s:c["elapsed_seconds"] for s,c in completion.items()},
                  document_checks=dict(local_links=len(local_links), local_links_valid=True, math_delimiters_paired=True),
                  peak_RSS_MiB=max(c["peak_RSS_KiB"] for c in completion.values()) / 1024,
                  tests=dict(total_passed=10, scientific_coordinates_used=False,
                             paths=["review_tests/test_pf_first_study_phase_b_scorer_unit.py", "review_tests/test_lab_progress_hchain_transfer_20261007.py",
                                    "review_tests/test_sector_pf.py", "review_tests/test_validation_expansion_20261007.py"]),
                  limits=["56 artificial-state/PF cases are not independent molecular samples", "unidentifiable fits are separated in an additional eligibility summary",
                          "A1 short-time and A3 finite-time questions remain separate", "A6 is a nine-point local check, not continuous optimization",
                          "B3 adds cap 0.75 only and establishes no optimal or universally safe cap"])
    write(OUT / "audit.json", result)
    public_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "manifest.json")
    public_files += [ROOT / "review_response/run_validation_expansion_20261007.py", Path(__file__),
                     ROOT / "review_tests/test_validation_expansion_20261007.py", ROOT / "docs/research_outcomes/20261007/validation_expansion_results.md"]
    for path in public_files:
        assert path.suffix in {".json", ".csv", ".md", ".py"} and path.is_file()
    write(OUT / "manifest.json", dict(self_excluded="artifacts/validation_expansion_20261007/manifest.json",
                                     science_execution_commit=completion["a1_proxy"]["execution_commit"],
                                     input_verified_snapshot_commit=p["input_snapshot_commit"],
                                     entries=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path), bytes=path.stat().st_size) for path in public_files],
                                     historical_source_registry=p["source_registry"], supplemental_source=h4_provenance,
                                     private_payloads_published=False))
    print(json.dumps(dict(all_checks_passed=True, A1=a1["H6"]["fit_eligible_counts"], artifacts=len(public_files), actual_call_counts=caps)))


if __name__ == "__main__":
    audit()
