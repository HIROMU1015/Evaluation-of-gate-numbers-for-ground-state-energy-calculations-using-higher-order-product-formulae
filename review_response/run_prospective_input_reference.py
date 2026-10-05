"""P3 commands: input, seal-inputs, references, seal-references.

Never changes Git automatically. The operator commits the global input seal before
any reference acquisition. Candidate/M1/truth/scorer commands intentionally absent.
Independent input/reference workers may be allocation-reserved by a supervisor;
each condition's atomic STARTED marker prevents concurrent/repeated science.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time

from prospective_input_reference import (
    DOC, P1_COMMIT, ZERO_KEYS, PreparationError, ReferenceAdapter, ReferenceLedger,
    allocation_gate, bounded_process, create_input, environment_readiness,
    fit_function, load_input, read, reference_summary, remaining_worker_wall, sha_file, sha_json, utc,
    validate_grid, write,
)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def verify_entries(root, manifest):
    for row in manifest["files"]:
        if sha_file(root / row["path"]) != row["sha256"]:
            raise PreparationError("frozen source/protocol file mismatch: " + row["path"])


def source_gate(root):
    seal = read(root / DOC / "implementation_manifest.json")
    verify_entries(root, seal)
    if git(root, "diff", "--name-only", "HEAD").strip() or git(root, "diff", "--cached", "--name-only").strip():
        raise PreparationError("tracked source must be clean before preparation")
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", P1_COMMIT, "HEAD"], check=True)
    for path in ("protocol.json", "conditions.json", "reference_grid.json", "source_registry.json"):
        expected = git(root, "show", f"{P1_COMMIT}:{DOC / path}")
        if (root / DOC / path).read_bytes() != expected:
            raise PreparationError("P1 scientific specification differs from its freeze")
    return seal


def history_gate(root, certificate_path, *, require_current_tip):
    certificate = read(certificate_path)
    inventory_path = certificate_path.parent / certificate["inventory_path"]
    if sha_file(inventory_path) != certificate["inventory_sha256"]:
        raise PreparationError("server history inventory checksum mismatch")
    inventory = read(inventory_path)
    if certificate.get("classification") != "repository_tracked_family_unseen" or certificate.get("positive_prior_science_evidence") != 0:
        raise PreparationError("CH2 history failed: stop P1 without substitution")
    if inventory["unreadable_text_blobs"] or certificate.get("manual_content_review_complete") is not True:
        raise PreparationError("all history content matches must be manually reviewed")
    if {m["sha256"] for m in inventory["matches"]} != set(certificate["reviewed_blob_sha256"]):
        raise PreparationError("server history content review does not cover every matching blob")
    audited = certificate["audited_tip_commit"]
    if require_current_tip and git(root, "rev-parse", "HEAD").decode().strip() != audited:
        raise PreparationError("history must be audited at current pre-science source tip")
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", audited, "HEAD"], check=True)
    if require_current_tip:
        refs = git(root, "for-each-ref", "--format=%(refname) %(objectname)").decode().splitlines()
        if refs != inventory["refs"] or git(root, "rev-parse", "--is-shallow-repository").decode().strip() != "false":
            raise PreparationError("history refs changed or repository is shallow; re-audit before science")
    return certificate


def marker(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise PreparationError("condition/phase already attempted; no repeated science or output reset") from exc


def frozen_inputs(root, output, commit):
    if not commit or git(root, "rev-parse", "HEAD").decode().strip() != commit:
        raise PreparationError("reference HEAD must equal the global input freeze commit")
    seal = read(output / "INPUT_FROZEN.json")
    for name in ["INPUT_FROZEN.json", *seal["input_files"]]:
        relative = (output / name).relative_to(root).as_posix()
        if git(root, "show", f"{commit}:{relative}") != (output / name).read_bytes():
            raise PreparationError("global input freeze differs from commit blob")
    for row in seal["manifest"]:
        if sha_file(output / row["path"]) != row["sha256"]:
            raise PreparationError("global input hash manifest mismatch")
    return seal


def context(args, reference=False):
    root = Path(args.project_root).resolve()
    output = Path(args.output_root).resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise PreparationError("lightweight output must be inside this independent Git worktree") from exc
    source_gate(root)
    allocation = allocation_gate(read(args.allocation), output, evidence_root=Path(args.allocation).parent)
    readiness = environment_readiness()
    history = history_gate(root, Path(args.history_certificate), require_current_tip=not reference)
    protocol = read(root / DOC / "protocol.json")
    conditions = read(root / DOC / "conditions.json")
    if len(conditions) != 16 or len({c["condition_id"] for c in conditions}) != 16:
        raise PreparationError("immutable 16-condition core inventory required")
    return root, output, allocation, readiness, history, protocol, conditions


def input_worker(args):
    root, output, allocation, readiness, history, protocol, conditions = context(args)
    spec = next((c for c in conditions if c["condition_id"] == args.condition_id), None)
    if spec is None:
        raise PreparationError("condition not in approved core; no substitution")
    if (output / "INPUT_FROZEN.json").exists():
        raise PreparationError("input generation prohibited after global freeze")
    path = output / "conditions" / spec["condition_id"]
    marker(path / "INPUT_STARTED.json", {"condition": spec["condition_id"], "start_UTC": utc(),
        "source_HEAD": git(root, "rev-parse", "HEAD").decode().strip(), "scientific_retries": 0})
    ledger = ReferenceLedger(allocation["worker_rss_limit_bytes"])
    try:
        with bounded_process(ledger, remaining_worker_wall(allocation)):
            identity = create_input(spec, output / ".runtime" / spec["condition_id"], ledger)
    except PreparationError as error:
        identity = {"status": "input_reference_ineligible", "condition": spec,
                    "failure_reason": str(error), "runtime_files": []}
    identity.update({"created_UTC": utc(), "resource": ledger.payload(), "environment": readiness,
                     "allocation_sha256": sha_file(args.allocation),
                     "server_history_certificate_sha256": sha_file(args.history_certificate),
                     "origin_code_commit": git(root, "rev-parse", "HEAD").decode().strip(),
                     "verified_protocol_commit": P1_COMMIT})
    write(path / "input_identity.json", identity)
    return {"condition_id": spec["condition_id"], "status": identity["status"]}


def seal_inputs(args):
    root, output, allocation, readiness, history, protocol, conditions = context(args)
    if (output / "INPUT_FROZEN.json").exists():
        raise PreparationError("global input seal already exists; do not rewrite")
    rows, files = [], []
    for spec in conditions:
        relative = f"conditions/{spec['condition_id']}/input_identity.json"
        identity = read(output / relative)
        if identity["condition"] != spec or identity["status"] not in ("input_eligible", "input_reference_ineligible"):
            raise PreparationError("missing/unrecognized terminal input condition; do not shrink denominator")
        if identity["status"] == "input_eligible":
            # Byte checks only; no input regeneration or numerical action.
            for entry in identity["runtime_files"]:
                if sha_file(output / ".runtime" / spec["condition_id"] / entry["path"]) != entry["sha256"]:
                    raise PreparationError("input runtime changed before freeze")
        rows.append({"condition_id": spec["condition_id"], "status": identity["status"]})
        files.append({"path": relative, "sha256": sha_file(output / relative)})
    payload = {"status": "prospective_global_input_frozen_reference_not_opened", "created_UTC": utc(),
        "condition_count": 16, "conditions": rows, "input_files": [row["path"] for row in files],
        "manifest": files, "protocol_commit": P1_COMMIT, "candidate_M1_truth_actions": 0,
        "allocation_sha256": sha_file(args.allocation), "history_certificate_sha256": sha_file(args.history_certificate)}
    write(output / "INPUT_FROZEN.json", payload)
    return {"status": payload["status"], "next": "commit exactly 16 input_identity files + INPUT_FROZEN; then references"}


def reference_worker(args):
    root, output, allocation, readiness, history, protocol, conditions = context(args, reference=True)
    frozen_inputs(root, output, args.input_commit)
    spec = next((c for c in conditions if c["condition_id"] == args.condition_id), None)
    if spec is None:
        raise PreparationError("unapproved reference condition")
    if (output / "COMPLETE.json").exists():
        raise PreparationError("preparation complete; no further science")
    path = output / "conditions" / spec["condition_id"]
    identity = read(path / "input_identity.json")
    marker(path / "REFERENCE_STARTED.json", {"start_UTC": utc(), "input_commit": args.input_commit,
                                             "condition_id": spec["condition_id"]})
    ledger = ReferenceLedger(allocation["worker_rss_limit_bytes"], checkpoint=path / "action_checkpoint.json")
    points = []
    if identity["status"] != "input_eligible":
        summary = {"status": "input_reference_ineligible", "candidate_plan": [], "reference_attempted": False}
    else:
        try:
            with bounded_process(ledger, remaining_worker_wall(allocation)):
                h, state, groups = load_input(identity, output / ".runtime" / spec["condition_id"])
                adapter = ReferenceAdapter(h, groups, [float.fromhex(x) for x in protocol["PF"]["canonical_sequence_hex"]], ledger)
                times = validate_grid(read(root / DOC / "reference_grid.json"))
                for t in times:  # deliberately acquire all 34 before looking for a fit
                    points.append(adapter.point(state, t))
                    write(path / "reference_checkpoint.json", {"points": points, "resource": ledger.payload()})
                summary = reference_summary(points, times, protocol, fit_function(root, read(root / DOC / "source_registry.json")))
        except PreparationError as error:
            summary = {"status": "reference_preparation_stopped", "failure_reason": str(error),
                       "candidate_plan": [], "completed_points": len(points)}
    summary.update({"condition_id": spec["condition_id"], "points": points, "resource": ledger.payload(),
                    "input_commit": args.input_commit, "input_identity_sha256": sha_file(path / "input_identity.json"),
                    "created_UTC": utc(), "verified_protocol_commit": P1_COMMIT,
                    "fit_is_truth_free_model_scale_not_oracle": True})
    write(path / "reference_result.json", summary)
    return {"condition_id": spec["condition_id"], "status": summary["status"]}


def seal_references(args):
    root, output, allocation, readiness, history, protocol, conditions = context(args, reference=True)
    frozen_inputs(root, output, args.input_commit)
    if (output / "COMPLETE.json").exists():
        raise PreparationError("one completion seal only")
    totals, rows, candidates, manifest = Counter(), [], [], []
    for spec in conditions:
        path = output / "conditions" / spec["condition_id"]
        result = read(path / "reference_result.json")
        identity = read(path / "input_identity.json")
        if result["input_commit"] != args.input_commit or result["input_identity_sha256"] != sha_file(path / "input_identity.json"):
            raise PreparationError("result is not from frozen input")
        for phase in (identity, result):
            if any(phase["resource"]["counts"].get(key, 0) != 0 for key in ZERO_KEYS):
                raise PreparationError("forbidden candidate/M1/truth/scoring activity")
            totals.update(phase["resource"]["counts"])
        if any(result["resource"]["counts"].get(k, 0) > 34 for k in ("reference_pf_actions", "reference_h_exponential_actions")):
            raise PreparationError("condition action cap exceeded")
        rows.append({"condition_id": spec["condition_id"], "family": spec["family"], "stratum": spec["stratum"],
                     "status": result["status"], "t_ref": result.get("t_ref"), "t_ref_hex": result.get("t_ref_hex"),
                     "K": identity.get("K"), "sector_dimension": identity.get("sector_dimension"),
                     "CISD_dimension": identity.get("CISD", {}).get("dimension"), "resource": result["resource"]})
        if result["status"] == "reference_candidate_plan_ready":
            for row in result["candidate_plan"]:
                candidates.append({"condition_id": spec["condition_id"], **row, "K": identity["K"]})
        relative = f"conditions/{spec['condition_id']}/reference_result.json"
        manifest.append({"path": relative, "sha256": sha_file(output / relative)})
    if any(totals[k] > 544 for k in ("reference_pf_actions", "reference_h_exponential_actions")):
        raise PreparationError("global cumulative action cap exceeded")
    write(output / "candidate_plan.json", {"candidate_count": len(candidates), "candidates": candidates,
                                          "science_at_candidates": 0, "all_conditions": rows})
    status = "prospective_input_reference_preparation_complete_review_required"
    write(output / "report.json", {"status": status, "condition_count": 16, "family_units": 4,
        "conditions": rows, "total_counts": dict(totals), "input_commit": args.input_commit,
        "phase_status_counts": dict(Counter(row["status"] for row in rows)), "environment": readiness,
        "limits": "preparation only; no candidate performance, holdout success, safety or certification claim"})
    manifest.extend({"path": name, "sha256": sha_file(output / name)} for name in ("candidate_plan.json", "report.json"))
    write(output / "manifest.json", {"files": manifest, "manifest_self_excluded": True,
                                      "COMPLETE_json_excluded_to_avoid_reference_cycle": True})
    write(output / "COMPLETE.json", {"status": status, "created_UTC": utc(), "input_commit": args.input_commit,
                                    "manifest_sha256": sha_file(output / "manifest.json"), "next_science_authorized": False})
    return {"status": status, "candidate_count": len(candidates), "stop": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("input", "seal-inputs", "references", "seal-references"))
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--allocation", required=True)
    parser.add_argument("--history-certificate", required=True)
    parser.add_argument("--condition-id")
    parser.add_argument("--input-commit")
    args = parser.parse_args()
    dispatch = {"input": input_worker, "seal-inputs": seal_inputs,
                "references": reference_worker, "seal-references": seal_references}
    try:
        print(json.dumps(dispatch[args.phase](args), indent=2))
    except (PreparationError, subprocess.CalledProcessError, OSError, KeyError, ValueError) as error:
        parser.exit(2, f"Preparation stopped: {error}\n")


if __name__ == "__main__":
    main()
