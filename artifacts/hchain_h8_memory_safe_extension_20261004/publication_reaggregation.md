# Publication scalar reaggregation source

This is publication-only Python source. It reads committed/frozen scalar artifacts, writes lightweight aliases, sums counters, and forms the H2–H8 summary. It does not run a predictor, eigensolver, direct truth, fitting, or policy adjustment. Scientific scoring is already performed by the frozen implementation.

```python
"""Publish reached-stage scalar evidence; never execute molecular science."""
from collections import Counter
import json
from pathlib import Path
import sys

from review_response.hchain_h8_memory_safe import BASE,DOC,OUT,STATUS,read,source_gate,runtime_gate
from review_response.hchain_odd_extension import commit_files,file_entry,git
from review_response.hchain_prediction_phase import verify_blob,verify_entries
from review_response.run_hchain_odd_extension import frozen
from review_response.hchain_input_reference_preparation import sha_file,write_json
from review_response.run_hchain_truth_scoring import utc,write_csv

root=Path.cwd().resolve()
out=root/OUT
source=source_gate(root)
tests=read(Path(sys.argv[1]))
inputs,ic=frozen(root,out,"inputs")
stages={"input_commit":ic}
payloads={"inputs":inputs}
for name in ("reference","acquisition","h1","prediction","ground","truth","scored"):
    if (out/name/"FREEZE.json").exists():
        payloads[name],stages[name+"_commit"]=frozen(root,out,name)
runtime_gate(out,inputs,allow_ground="ground" in payloads)
equiv=root/DOC/"implementation_equivalence.json"
write_json(out/"implementation_equivalence.json",read(equiv))
write_json(out/"input_identity.json",{
    "origin_result_commit":ic,"verified_snapshot_commit":source["execution_HEAD"],
    "system_identity":inputs["system_identity"],"input_identity":inputs["input_identity"],
    "runtime_files":inputs["runtime_files"],"runtime_not_in_Git":True})
if "reference" in payloads:
    ref=payloads["reference"]
    write_json(out/"reference_results.json",ref)
    write_csv(out/"candidate_plan.csv",ref["plan"])
for name,alias in (("acquisition","ACQUISITION_FROZEN.json"),("h1","H1_FROZEN.json"),
                   ("prediction","PREDICTION_FROZEN.json"),("ground","ground_manifest.json"),
                   ("truth","truth_manifest.json")):
    if name in payloads:
        write_json(out/alias,{"kind":read(out/name/"FREEZE.json")["kind"],
            "origin_result_commit":stages[name+"_commit"],"verified_snapshot_commit":source["execution_HEAD"],
            "manifest_path":f"{name}/manifest.json","manifest_sha256":sha_file(out/name/"manifest.json"),
            "payload_sha256":sha_file(out/name/"payload.json"),"freeze_blob_verified":True})
if "prediction" in payloads:
    (out/"prediction.sha256").write_text(sha_file(out/"prediction/payload.json")+"  prediction/payload.json\n")

audits={}
for phase in ("inputs","reference","prediction","truth"):
    path=out/f"{phase}_execution_audit.json"
    if path.exists():audits[phase]=read(path)
preflight=read(out/"resource_preflight.json") if (out/"resource_preflight.json").exists() else None
phase_resources={}
for phase,audit in audits.items():
    resources=audit["resources"]
    phase_resources[phase]=resources["systems"]["H8"] if "systems" in resources else resources
if preflight:phase_resources["preflight"]=preflight["resources"]
totals=Counter()
for resource in phase_resources.values():totals.update(resource["counts"])
resources={"phase_specific":phase_resources,"summed_counts_including_preflight":dict(totals),
    "peak_RSS_KiB":max((r["peak_RSS_KiB"] for r in phase_resources.values()),default=0),
    "peak_aggregation":"maximum, not sum; separate CLI processes run sequentially",
    "preflight_actions_excluded_from_34_reference_and_3_candidate_campaigns":True,
    "classical_counts_not_quantum_K":True,"H_exponential_internal_matvecs":"unknown_not_exposed",
    "GPU_queries_allocations_kernels":0,"CPU_processes":1,"BLAS_threads":1,
    "implementation_regression_resource_scope":"separate old/new H7 one-coordinate comparison",
    "regression_resources":read(equiv)["resources"],
    "combined_H1_path_resource":payloads.get("prediction",{}).get("schedule_resource")}
write_json(out/"resource_audit.json",resources)
phase_access={}
for phase,audit in audits.items():
    recorded=dict(audit["access"])
    if "truth_array_reads" in audit:
        recorded["original_template_truth_array_reads"]=recorded["truth_array_reads"]
        recorded["truth_array_reads"]=audit["truth_array_reads"]
        recorded["count_source"]="explicit top-level truth execution counter; original template preserved"
    phase_access[phase]=recorded
access={"phases":phase_access,
    "preflight":None if preflight is None else preflight["access"],
    "implementation_regression_reads":read(equiv)["access"],
    "prediction_truth_opened":payloads.get("prediction",{}).get("truth_opened"),
    "GPU_operations":0,"CuPy_imported":False,"OS_hermeticity_claim":False,
    "publication_reads_saved_scalar_only":True}
write_json(out/"access_audit.json",access)

historical=[]
integrated=[]
old_input=read(root/"artifacts/hchain_input_reference_preparation_20261004_06922cb/input_identity.json")
old_pred=read(root/"artifacts/hchain_truth_free_prediction_20261004/final/prediction.json")
old_score=read(root/"artifacts/hchain_truth_scoring_20261004/result/scoring.json")
odd_input=read(root/"artifacts/hchain_h3_h5_h7_extension_20261004/inputs/payload.json")
odd_pred=read(root/"artifacts/hchain_h3_h5_h7_extension_20261004/prediction/payload.json")
odd_ref=read(root/"artifacts/hchain_h3_h5_h7_extension_20261004/reference/payload.json")
odd_score=read(root/"artifacts/hchain_h3_h5_h7_extension_20261004/scoring.json")
for name in ("artifacts/hchain_input_reference_preparation_20261004_06922cb/input_identity.json",
             "artifacts/hchain_truth_free_prediction_20261004/final/prediction.json",
             "artifacts/hchain_truth_scoring_20261004/result/scoring.json",
             "artifacts/hchain_h3_h5_h7_extension_20261004/inputs/payload.json",
             "artifacts/hchain_h3_h5_h7_extension_20261004/prediction/payload.json",
             "artifacts/hchain_h3_h5_h7_extension_20261004/reference/payload.json",
             "artifacts/hchain_h3_h5_h7_extension_20261004/scoring.json"):
    verify_blob(root,name,BASE)
    origin=git(root,"log","-1","--format=%H",BASE,"--",name).decode().strip()
    historical.append({**file_entry(root,root/name),"origin_result_commit":origin,"verified_snapshot_commit":BASE})
for system in ("H2","H3","H4","H5","H6","H7","H8"):
    if system in ("H2","H4","H6"):
        pred,score=old_pred,old_score
        identity=pred["input_identity"][system]
        origin=historical[2]["origin_result_commit"]
    elif system in ("H3","H5","H7"):
        pred,score=odd_pred,odd_score
        identity=odd_input["input_identity"][system]
        origin=historical[-1]["origin_result_commit"]
    else:
        pred,score=payloads.get("prediction"),payloads.get("scored")
        identity=inputs["input_identity"]["H8"]
        origin=stages.get("scored_commit")
    row={"system":system,"sector_dimension":identity["sector_dimension"],"CISD_dimension":identity["CISD_subspace_dimension"],
         "K":identity["K"],"origin_result_commit":origin,"verified_snapshot_commit":BASE if system!="H8" else source["execution_HEAD"]}
    if system=="H3":
        row.update({"status":odd_ref["references"]["H3"]["status"],"q":None,"performance_scored":False})
    elif pred is None or score is None:
        row.update({"status":"stage_not_reached","q":None if pred is None else pred["cheap_B0_B1_B2_q"][system]["q"],"performance_scored":False})
    else:
        cheap=pred["cheap_B0_B1_B2_q"][system]
        coords=[r for r in score["coordinate_scores"] if r["system"]==system]
        decisions=[r for r in score["decision_scores"] if r["system"]==system]
        row.update({"status":"scored","q":cheap["q"],"performance_scored":True,
            "M1_branch_pass":sum(r["branch_correct_shift_gap"] is True for r in coords),
            "M1_width_cover":sum(r["empirical_width_covers"] is True for r in coords),
            "M1_abstentions":sum(r["M1_policy_abstained"] for r in coords),
            "q_one_conditional_path_measured":cheap["q"]==1})
        for arm in ("B0","B2","H1","always_M1"):
            action=next(r for r in decisions if r["arm"]==arm)
            for field in ("safe","B_over_B0","safe_target_met","candidate_id","frozen_budget"):
                row[f"{arm}_{field}"]=action[field]
    integrated.append(row)
write_csv(out/"h2_h8_integrated_summary.csv",integrated)
write_json(out/"publication_source_registry.json",{"sources":historical,"historical_science_modified":False,
    "origin_and_verified_snapshot_separate":True,"new_stages":stages})
test_rows=[]
for index,test in enumerate(tests):
    name=f"tests/{index:02d}_{test['phase']}.log"
    path=out/name;path.parent.mkdir(exist_ok=True)
    path.write_text(test["output"])
    test_rows.append({k:v for k,v in test.items() if k!="output"}|{"log":name,"log_sha256":sha_file(path)})
failure_paths=[p for p in out.glob("*FAILURE.json")]+[p for p in out.glob("*RESOURCE_STOP.json")]
if (out/"COMPLETE.json").exists():status=STATUS
elif failure_paths:status=read(failure_paths[-1]).get("status","H8_execution_failed_stop")
elif (out/"execution_decision.json").exists():status=read(out/"execution_decision.json")["status"]
else:status="H8_memory_safe_resource_blocked"
write_json(out/"execution_audit.json",{"status":status,"utc":utc(),"branch":git(root,"branch","--show-current").decode().strip(),
    "base_commit":BASE,"implementation_content_commit":source["content_commit"],"stage_commits":stages,
    "publication_snapshot_before_content_commit":source["execution_HEAD"],"source":source,"tests":test_rows,
    "unrecorded_initial_development_tests":"two runs of 118 passed; UTC not separately captured, not used for stage gates",
    "scientific_rules_modified":False,"push_authorized":False,"next_stage_authorized":False,
    "prediction_frozen_byte_identity": "7/7" if "prediction" in payloads else "stage_not_reached"})
print(json.dumps({"status":status,"stages":stages,"resources":dict(totals),"peak_RSS_KiB":resources["peak_RSS_KiB"],
                  "H8_summary":integrated[-1],"historical_summary":integrated[:-1]},indent=2))
```
