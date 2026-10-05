#!/usr/bin/env python3
"""Render Study 2 synthesis from committed scalar tables, never science/runtime inputs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path

BASE = "bfe715fc1c04325535a3c4d63ea4584e691dc322"
ROOT = Path(__file__).resolve().parents[1]
DOC = Path("docs/second_study_v2/result_synthesis_20261005")
DATA = Path("artifacts/budget_safety_mechanism_20261005")
OUT = Path("paper/study2/figures")
CONDITIONS = ["HF_full_eq_sto3g", "HF_full_stretch150_sto3g",
              "H2", "H4", "H5", "H6", "H7", "H8",
              "HCl_full_eq_sto3g", "HCl_full_stretch150_sto3g"]
LABELS = ["HF eq", "HF stretch", "H2", "H4", "H5", "H6", "H7", "H8",
          "HCl eq", "HCl stretch"]
BLUE, ORANGE, RED, GREY, PURPLE = "#0072B2", "#D55E00", "#B2182B", "#666666", "#8064A2"


class SynthesisError(ValueError):
    pass


def flag(value):
    if value not in ("True", "False"):
        raise SynthesisError(f"missing/invalid boolean: {value!r}")
    return value == "True"


def number(value, optional=False):
    if value == "" and optional:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise SynthesisError(f"missing/invalid number: {value!r}") from None
    if not math.isfinite(v):
        raise SynthesisError("nonfinite scalar")
    return v


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(root, commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root)


def verify_sources(root=ROOT):
    registry = json.loads((root / DOC / "source_registry.json").read_text())
    if registry["base_snapshot_commit"] != BASE:
        raise SynthesisError("wrong base snapshot")
    for entry in registry["sources"]:
        path = entry["path"]
        raw = (root / path).read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise SynthesisError(f"source bytes changed: {path}")
        for commit in (entry["origin_result_commit"], entry["verified_snapshot_commit"]):
            if raw != git_bytes(root, commit, path):
                raise SynthesisError(f"origin/snapshot mismatch: {path}")
    review = registry["review_source"]
    if sha(root / review["path"]) != review["sha256"]:
        raise SynthesisError("approved review changed")
    # Preserve transitive origin metadata from the original 41-entry registry.
    upstream = json.loads((root / "docs/second_study_v2/budget_safety_mechanism_20261005/source_registry.json").read_text())
    for entry in upstream["sources"]:
        raw = (root / entry["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise SynthesisError("upstream scalar source hash mismatch")
        for commit in (entry["origin_result_commit"], entry["verified_snapshot_commit"]):
            if raw != git_bytes(root, commit, entry["path"]):
                raise SynthesisError("upstream origin/snapshot mismatch")
    return {"direct_sources": len(registry["sources"]), "upstream_sources": len(upstream["sources"]),
            "review_sha256": review["sha256"], "all_source_bytes_unchanged": True}


def index(rows, fields):
    result = {}
    for line, row in enumerate(rows, 2):
        key = tuple(row[f] for f in fields)
        if key in result:
            raise SynthesisError(f"duplicate key {key}")
        result[key] = (line, row)
    return result


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)


def source_row(table, line, row):
    return {"path": str(DATA / table), "csv_line": line, "row": dict(row)}


def ordered(rows):
    rank = {c: i for i, c in enumerate(CONDITIONS)}
    return sorted(rows, key=lambda r: (rank[r["condition"]], number(r["time"])))


def build_display(root=ROOT):
    names = ["budget_safety_capacity.csv", "selected_frozen_budget_safety.csv",
             "same_time_oracle_headroom.csv", "oracle_headroom_by_contract.csv",
             "m1_point_width_abstention.csv", "width_decision_windows.csv",
             "m1_reference_error_decomposition.csv", "hchain_model_vs_observation.csv"]
    tables = {n: read_csv(root / DATA / n) for n in names}
    counts = {n: len(rows) for n, rows in tables.items()}
    expected = [150, 64, 30, 10, 30, 300, 30, 6]
    if list(counts.values()) != expected:
        raise SynthesisError(f"changed table coverage: {counts}")
    cap = index(tables[names[0]], ("condition", "candidate_id", "gamma"))
    selected = index(tables[names[1]], ("condition", "arm"))
    m1 = index(tables[names[4]], ("condition", "candidate_id"))
    decomp = index(tables[names[6]], ("condition", "candidate_id"))
    window = index(tables[names[5]], ("condition", "candidate_id", "comparator_scope", "eta"))
    oracle = index(tables[names[3]], ("condition",))
    same = index(tables[names[2]], ("condition", "candidate_id"))
    panels = {"figure_1_selected": [], "figure_2_coordinates": [],
              "figure_2_decisions": [], "figure_3_components": []}
    for condition in CONDITIONS[:8]:
        line, r = selected[(condition, "B2")]
        _, h1 = selected[(condition, "H1")]
        _, fixed = selected[(condition, "B1_gamma_1.01")]
        if any(r[f] != other[f] for other in (h1, fixed)
               for f in ("candidate_id", "frozen_budget", "saved_safe", "q")):
            raise SynthesisError("B2/H1/fixed-cheap identity changed")
        if r["q"] != "0":
            raise SynthesisError("unexpected conditional acquisition")
        cl, c = cap[(condition, r["candidate_id"], "1.01")]
        u, margin, slack = (number(r[k]) for k in
                            ("underestimation_hartree", "budget_margin_capacity_hartree",
                             "safety_slack_hartree"))
        if not close(margin-u, slack) or flag(r["saved_safe"]) != (slack >= 0):
            raise SynthesisError("stored slack or safety disagrees")
        if not close(number(c["margin_hartree"]), margin):
            raise SynthesisError("capacity join differs")
        panels["figure_1_selected"].append({
            "condition": condition, "candidate_id": r["candidate_id"],
            "u_microhartree": u*1e6, "margin_microhartree": margin*1e6,
            "slack_microhartree": slack*1e6, "safe": flag(r["saved_safe"]),
            "c_microhartree": number(r["c_hartree"])*1e6,
            "e_microhartree": number(r["e_hartree"])*1e6,
            "cheap_sign": math.copysign(1, number(c["delta_C_signed_hartree"])),
            "truth_sign": math.copysign(1, number(c["delta_direct_signed_hartree"])),
            "sources": [source_row(names[1], line, r), source_row(names[0], cl, c)]})
        ml, mr = selected[(condition, "always_M1")]
        panels["figure_2_decisions"].append({
            "condition": condition, "cheap_B_over_B0": number(r["B_over_B0"]),
            "cheap_safe": flag(r["saved_safe"]), "M1_B_over_B0": number(mr["B_over_B0"]),
            "M1_fallback": flag(mr["fallback"]), "M1_safe": flag(mr["saved_safe"]),
            "sources": [source_row(names[1], line, r), source_row(names[1], ml, mr)]})
    for r in ordered(tables[names[2]]):
        key = (r["condition"], r["candidate_id"])
        sl, sr = same[key]
        ml, mr = m1[key]
        ol, orow = oracle[(key[0],)]
        valid = flag(sr["same_time_reference_safe"])
        headroom = number(sr["S_max_same_time"], optional=True)
        if valid != (headroom is not None):
            raise SynthesisError("unsafe comparator must have undefined headroom")
        if valid and not close(headroom, 1-number(sr["same_time_perfect_truth_budget"]) /
                               number(sr["same_time_cheap_budget"])):
            raise SynthesisError("headroom formula differs")
        scope = "same_time_fixed_cheap_gamma_" + sr["same_time_reference_gamma"]
        wl0, wr0 = window[key + (scope, "0")]
        wl1, wr1 = window[key + (scope, "0.1")]
        if flag(wr0["arithmetic_window_valid"]) != valid:
            raise SynthesisError("width-window comparator validity differs")
        windows = [number(wr["w_win_hartree"])*1e6 if valid else None
                   for wr in (wr0, wr1)]
        panels["figure_2_coordinates"].append({
            "condition": key[0], "candidate_id": key[1], "family": sr["family"],
            "gamma": sr["same_time_reference_gamma"],
            "headroom_percent": headroom*100 if valid else None,
            "comparator_safe": valid, "E_M_hartree": number(mr["E_M_hartree"]),
            "width_hartree": number(mr["width_hartree"]),
            "width_microhartree": number(mr["width_hartree"])*1e6,
            "window_eta0_microhartree": windows[0],
            "window_eta10_microhartree": windows[1],
            "abstained": flag(mr["abstained"]),
            "point_improves": flag(mr["point_improves_over_cheap"]),
            "empirical_width_covers": flag(mr["empirical_width_covers"]),
            "native_oracle_candidate_id": orow["oracle_candidate_id"],
            "sources": [source_row(names[2], sl, sr), source_row(names[4], ml, mr),
                        source_row(names[3], ol, orow), source_row(names[5], wl0, wr0),
                        source_row(names[5], wl1, wr1)]})
    for r in ordered(tables[names[6]]):
        if r["family"] != "H-chain":
            if r["PF_energy_error_signed_hartree"] or r["H_reference_error_signed_hartree"]:
                raise SynthesisError("unexpected HF/HCl decomposition")
            continue
        if r["decomposition_status"] != "same_H_origin_physical_lift_verified_saved_diagnostic":
            raise SynthesisError("unverified energy identity")
        line, row = decomp[(r["condition"], r["candidate_id"])]
        a, ref, shift = (number(r[k]) for k in ("PF_energy_error_signed_hartree",
                         "H_reference_error_signed_hartree", "shift_error_signed_hartree"))
        residual = number(r["closure_rounding_residual_hartree"])
        allowance = number(r["closure_rounding_allowance_hartree"])
        if not close(shift-(a-ref), residual) or abs(residual) > allowance:
            raise SynthesisError("component closure fails")
        panels["figure_3_components"].append({
            "condition": r["condition"], "candidate_id": r["candidate_id"],
            "A_hartree": a, "R_hartree": ref, "shift_hartree": shift,
            "rounding_allowance_hartree": allowance,
            "sources": [source_row(names[6], line, row)]})
    for row in tables[names[0]]:
        if row["gamma"] == "1" and row["underestimation_to_margin_ratio"] != "":
            raise SynthesisError("gamma=1 ratio must remain undefined")
    return {"schema": "study2_figure_display_v1", "base_snapshot": BASE,
            "display_only_not_new_scientific_results": True, "table_rows": counts,
            "transformations": ["Hartree * 1e6 = microhartree", "fraction * 100 = percent",
                                "stored source fields copied without new policy scoring"],
            **panels}


def validate_display(display, root=ROOT):
    """Independent Decimal check of display conversions and original CSV row pointers."""
    pointers = 0
    for name in ("figure_1_selected", "figure_2_coordinates",
                 "figure_2_decisions", "figure_3_components"):
        for mark in display[name]:
            for src in mark["sources"]:
                rows = read_csv(root / src["path"])
                if rows[src["csv_line"]-2] != src["row"]:
                    raise SynthesisError("plot row pointer drift")
                pointers += 1
    with localcontext() as ctx:
        ctx.prec = 50
        def check_display(v, raw, factor):
            if v is None:
                return
            exact = Decimal(raw)*Decimal(factor)
            if abs(Decimal(str(v))-exact) > max(Decimal("1e-14"), abs(exact)*Decimal("2e-15")):
                raise SynthesisError("display conversion differs")
        for mark in display["figure_1_selected"]:
            row = mark["sources"][0]["row"]
            for target, field in (("u_microhartree", "underestimation_hartree"),
                                  ("margin_microhartree", "budget_margin_capacity_hartree"),
                                  ("slack_microhartree", "safety_slack_hartree"),
                                  ("c_microhartree", "c_hartree"), ("e_microhartree", "e_hartree")):
                check_display(mark[target], row[field], "1000000")
        for mark in display["figure_2_coordinates"]:
            check_display(mark["headroom_percent"], mark["sources"][0]["row"]["S_max_same_time"], "100")
            check_display(mark["width_microhartree"], mark["sources"][1]["row"]["width_hartree"], "1000000")
            for i, target in ((3, "window_eta0_microhartree"), (4, "window_eta10_microhartree")):
                check_display(mark[target], mark["sources"][i]["row"]["w_win_hartree"], "1000000")
    return {"source_row_pointers_checked": pointers, "display_conversion_check": "Decimal50_pass",
            "unsafe_headroom_not_zero": True, "gamma1_ratio_not_plotted": True}


def render(display, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "study2-frozen-scalar-synthesis-20261005",
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    files = []
    def save(fig, name):
        for extension in ("png", "svg", "pdf"):
            path = out / f"{name}.{extension}"
            if extension == "png":
                fig.savefig(path, dpi=180, facecolor="white")
            else:
                metadata = {"Date": None} if extension == "svg" else {
                    "CreationDate": None, "ModDate": None, "Creator": "Study2 scalar figure renderer"}
                fig.savefig(path, metadata=metadata, facecolor="white")
            files.append(path)
        plt.close(fig)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 5), layout="constrained",
                                gridspec_kw={"width_ratios": [1.6, 1]})
    rows = display["figure_1_selected"]
    for y, row in enumerate(rows):
        u, m = row["u_microhartree"], row["margin_microhartree"]
        ax.plot([u, m], [y, y], color="#BBBBBB", lw=2)
        ax.scatter(u, y, color=BLUE if row["safe"] else RED, marker="o", s=45, zorder=3)
        ax.scatter(m, y, color=GREY, marker="s", s=38, zorder=3)
    ax.axvline(0, color=GREY, lw=.7)
    ax.set_yticks(range(8), LABELS[:8]); ax.invert_yaxis()
    ax.set_xlabel(r"Underestimation $u=e-c$ and margin $M$ [$\mu$Ha]")
    ax.set_title(r"(a) Frozen B2 = H1 = fixed cheap $\gamma=1.01$")
    ax.text(.98, .46, r"safe iff $u\leq M$", transform=ax.transAxes, ha="right")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, label="u (safe)"),
                       Line2D([], [], marker="o", ls="", color=RED, label="u (unsafe)"),
                       Line2D([], [], marker="s", ls="", color=GREY, label="margin")],
              loc="lower right", frameon=False)
    ax.grid(axis="x", alpha=.2)
    for j, row in enumerate(rows[:2]):
        bx.bar(j-.18, row["c_microhartree"], width=.32, color=BLUE)
        bx.bar(j+.18, row["e_microhartree"], width=.32, color=ORANGE)
        signs = f"cheap {'+' if row['cheap_sign'] > 0 else '-'} / truth {'+' if row['truth_sign'] > 0 else '-'}"
        bx.text(j, max(row["c_microhartree"], row["e_microhartree"])+1.1, signs,
                ha="center", fontsize=8)
    bx.set_xticks([0, 1], ["HF eq", "HF stretch"]); bx.set_ylim(0, 29)
    bx.set_ylabel(r"PF error magnitude [$\mu$Ha]")
    bx.set_title("(b) The budget uses magnitudes, not signed error")
    bx.legend(handles=[Line2D([], [], color=BLUE, lw=7, label="cheap c"),
                       Line2D([], [], color=ORANGE, lw=7, label="truth e")], frameon=False)
    fig.suptitle("Frozen budget reliability at selected coordinates", fontsize=13)
    save(fig, "figure_1_budget_safety")
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 9), layout="constrained")
    aa, bb, cc, dd = axes.flat
    coords = display["figure_2_coordinates"]
    def decorate(ax):
        ax.set_xticks([i*3+1 for i in range(10)], LABELS, rotation=45, ha="right")
        for boundary in (5.5, 23.5):
            ax.axvline(boundary, color=GREY, lw=.6, alpha=.5)
        ax.set_xlim(-.7, 29.7); ax.grid(axis="y", alpha=.2)
    for x, row in enumerate(coords):
        if row["comparator_safe"]:
            aa.scatter(x, row["headroom_percent"], color=BLUE, s=24)
        else:
            aa.axvspan(x-.35, x+.35, color=RED, alpha=.10)
            aa.text(x, 6, "unsafe\nundefined", color=RED, ha="center", fontsize=7)
        bb.scatter(x, row["E_M_hartree"], color=BLUE, marker="o", s=23)
        bb.scatter(x, row["width_hartree"], color=ORANGE, marker="^", s=26)
        if row["abstained"]:
            bb.scatter(x, row["width_hartree"], facecolors="none", edgecolors=RED, s=90)
        cc.scatter(x, row["width_microhartree"], color=ORANGE, marker="^", s=26)
        if row["comparator_safe"]:
            cc.scatter(x, row["window_eta0_microhartree"], color=BLUE, s=23)
            cc.scatter(x, row["window_eta10_microhartree"], color=PURPLE, marker="v", s=23)
    aa.axhline(10, color=GREY, ls="--", lw=1)
    aa.text(29, 10.25, "10% target", ha="right", fontsize=8)
    aa.set_ylim(-.3, 11.4); aa.set_ylabel("Residual same-time oracle headroom [%]")
    aa.set_title("(a) Named safe cheap vs cost-free perfect truth")
    bb.set_yscale("log"); bb.set_ylabel("Point error and empirical width [Ha]")
    bb.set_title("(b) Fixed M1 point error, width and abstention")
    bb.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, label="point error"),
                       Line2D([], [], marker="^", ls="", color=ORANGE, label="width"),
                       Line2D([], [], marker="o", ls="", mfc="none", mec=RED, label="abstained")],
              fontsize=8, frameon=False, loc="upper left")
    cc.set_yscale("symlog", linthresh=.1); cc.axhline(0, color=GREY, lw=.7)
    cc.set_ylabel(r"Width and fixed-point win window [$\mu$Ha]")
    cc.set_title("(c) Width-only changes with the M1 point held fixed")
    cc.legend(handles=[Line2D([], [], marker="^", ls="", color=ORANGE, label="current width"),
                       Line2D([], [], marker="o", ls="", color=BLUE, label="win window 0%"),
                       Line2D([], [], marker="v", ls="", color=PURPLE, label="win window 10%")],
              fontsize=8, frameon=False)
    for ax in (aa, bb, cc):
        decorate(ax)
    for x, row in enumerate(display["figure_2_decisions"]):
        dd.scatter(x-.10, row["cheap_B_over_B0"], color=BLUE if row["cheap_safe"] else RED,
                   marker="o", s=40)
        dd.scatter(x+.10, row["M1_B_over_B0"], color=ORANGE, marker="s", s=38)
        if row["M1_fallback"]:
            dd.annotate("fallback", (x+.1, row["M1_B_over_B0"]), xytext=(0, 8),
                        textcoords="offset points", ha="center", rotation=45, fontsize=7)
    dd.axhline(1, color=GREY, ls="--", lw=.7)
    dd.set_ylim(.55, 1.15); dd.set_xticks(range(8), LABELS[:8], rotation=45, ha="right")
    dd.set_ylabel("Selected frozen budget / inherited B0")
    dd.set_title("(d) Actual frozen actions at possibly different times")
    dd.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, label="fixed cheap / B2 / H1"),
                       Line2D([], [], marker="o", ls="", color=RED, label="cheap unsafe"),
                       Line2D([], [], marker="s", ls="", color=ORANGE, label="always-M1")],
              fontsize=8, frameon=False, loc="lower right")
    fig.suptitle("Oracle headroom and the actual fixed M1 package", fontsize=13)
    save(fig, "figure_2_headroom_and_m1")
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.7), layout="constrained")
    for ax, condition in zip(axes.flat, CONDITIONS[2:8]):
        rows = [r for r in display["figure_3_components"] if r["condition"] == condition]
        for x, row in enumerate(rows):
            for offset, key, color, marker in ((-.12, "A_hartree", BLUE, "o"),
                                               (0, "R_hartree", ORANGE, "s"),
                                               (.12, "shift_hartree", PURPLE, "D")):
                ax.scatter(x+offset, row[key], color=color, marker=marker, s=40)
        ax.axhline(0, color=GREY, lw=.7)
        if condition == "H2":
            ax.set_ylim(-7e-16, 7e-16)
            ax.text(.03, .03, "floating-point rounding region\nnot a physical mechanism",
                    transform=ax.transAxes, fontsize=8)
        else:
            # Display scaling only, never a numerical or scientific gate.
            smallest = min(abs(row[k]) for row in rows
                           for k in ("A_hartree", "R_hartree", "shift_hartree") if row[k] != 0)
            ax.set_yscale("symlog", linthresh=max(smallest/10, 1e-15))
            ax.margins(y=.18)
            # Suppress crowded near-zero decade labels, not data marks.
            low = math.ceil(math.log10(smallest))
            high = math.floor(math.log10(max(abs(v) for v in ax.get_ylim())))
            decades = [10.0**k for k in range(low, high+1)]
            ax.set_yticks([-v for v in reversed(decades)] + [0.0] + decades)
        ax.set_xticks([0, 1, 2], ["0.5", "0.65", "0.8"])
        ax.set_xlabel(r"Native candidate ratio $r=t/t_{\rm ref}$")
        ax.set_ylabel("Signed energy error [Ha]"); ax.set_title(condition)
        ax.grid(axis="y", alpha=.2)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=BLUE, label="PF error A"),
                        Line2D([], [], marker="s", ls="", color=ORANGE, label="H-reference error R"),
                        Line2D([], [], marker="D", ls="", color=PURPLE, label="saved shift error A - R")],
               loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle("PF recovery and reference errors are distinct", fontsize=13)
    save(fig, "figure_3_pf_reference_components")
    return files, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    sources = verify_sources()
    display = build_display()
    validation = validate_display(display)
    if args.verify_only:
        existing = json.loads((ROOT / OUT / "figure_data.json").read_text())
        if existing != display:
            raise SynthesisError("saved display data differs")
        manifest = json.loads((ROOT / OUT / "figure_manifest.json").read_text())
        for item in manifest["files"]:
            if sha(ROOT / item["path"]) != item["sha256"]:
                raise SynthesisError("figure artifact hash changed")
        print(json.dumps({"verification": "PASS", **sources, **validation}))
        return
    out = ROOT / OUT
    if out.exists():
        raise SynthesisError("refusing to overwrite existing figures; verification only")
    out.mkdir(parents=True)
    paths, version = render(display, out)
    after = verify_sources()
    if after != sources:
        raise SynthesisError("source audit changed during rendering")
    def write(name, obj):
        path = out / name
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
        paths.append(path)
    write("figure_data.json", display)
    write("render_audit.json", {
        "schema": "study2_render_audit_v1", "status": "render_complete",
        "python": sys.version, "matplotlib": version, "backend": "Agg",
        "source_verification": sources, "display_validation": validation,
        "new_scientific_acquisition": {"PF_actions": 0, "H_actions": 0, "Arnoldi": 0,
                                     "ground": 0, "direct_truth": 0, "gap": 0, "GPU": 0},
        "science_modules_imported": [], "main_analysis_rerun": False,
        "runtime_opened": False, "overwrite_allowed": False,
        "display_arithmetic_performed": True})
    manifest = {"schema": "study2_figure_manifest_v1", "base_snapshot": BASE,
                "manifest_self_excluded": True, "files": [
                    {"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha(p)}
                    for p in paths]}
    (out / "figure_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"rendered_main_figures": 3, "formats": ["png", "svg", "pdf"],
                      **sources, **validation}))


if __name__ == "__main__":
    main()
