"""Read-only design audit and synthetic tests; never decodes production arrays.

Run from any cwd. --write-verification writes only this new Phase0.5 directory.
"""
import argparse
import ast
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write-verification",action="store_true")
    args=parser.parse_args()
    protocol=json.loads((HERE/"response_pilot_protocol.json").read_text())
    sources=json.loads((HERE/"source_manifest.json").read_text())
    counts=json.loads((HERE/"expected_action_counts.json").read_text())
    go=json.loads((HERE/"GO_NO_GO_FOR_SCIENCE.json").read_text())
    base=sources["base_snapshot_commit"]
    source_checks=[]
    for row in sources["sources"]:
        data=(ROOT/row["path"]).read_bytes()
        blob=subprocess.check_output(["git","-C",str(ROOT),"show",base+":"+row["path"]])
        assert data==blob and hashlib.sha256(data).hexdigest()==row["sha256"],row["path"]
        source_checks.append({"path":row["path"],"byte_hash_verified":True,"base_blob_unchanged":True})
    # AST checks are about this reference package, not a universal Python sandbox.
    modules=["phase05_math.py","phase05_phase_a.py","phase05_phase_b.py","phase05_runner.py"]
    for name in modules:
        tree=ast.parse((HERE/name).read_text())
        assert not any(isinstance(n,ast.Attribute) and n.attr=="load" for n in ast.walk(tree)),name
    phase_a=(HERE/"phase05_phase_a.py").read_text()
    assert "from phase05_phase_b" not in phase_a
    assert protocol["response"]["primary_m"]==8
    assert protocol["response"]["m_values"]==[1,2,4,8]
    assert len(set(protocol["scope"]["training_abs_times"]) & set(protocol["scope"]["evaluation_abs_times"]))==0
    assert protocol["science_authorized"] is False
    assert all(v==0 for v in counts["current_phase05_science"].values())
    assert go["science_authorized"] is False and go["production_execution_ready"] is False
    assert go["unresolved_design_issues"]==[]
    from phase05_math import M_VALUES,TRAIN,EVAL
    assert list(M_VALUES)==protocol["response"]["m_values"]
    assert list(TRAIN)==protocol["scope"]["training_abs_times"]
    assert list(EVAL)==protocol["scope"]["evaluation_abs_times"]
    one=counts["joint_all_m_one_pass"];cold=counts["joint_all_m_with_cold_replay"]
    assert one["PF_forward_action_count"]==22*(1+4)
    assert one["PF_adjoint_action_count"]==22
    assert cold["PF_forward_action_count"]+cold["PF_adjoint_action_count"]==264
    assert cold["H_matvec_count"]==18
    assert cold["small_dense_ritz_eigh_count"]==8
    assert cold["group_expm_count"]==4400
    keys=json.loads((HERE/"saved_truth_join_contract.json").read_text())["keys"]
    assert len(keys)==12
    assert len({(r["absolute_time"],r["sign"]) for r in keys})==12
    assert all(r["branch_reliable"] in ("True","true","1") for r in keys)
    digest=hashlib.sha256((HERE/"response_pilot_protocol.json").read_bytes()).hexdigest()
    assert (HERE/"response_pilot_protocol.json.sha256").read_text().split()[0]==digest
    completed=subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider",str(HERE/"test_phase05.py")],capture_output=True,text=True,check=True)
    import numpy, scipy, pytest
    names=[node.name for node in ast.parse((HERE/"test_phase05.py").read_text()).body if isinstance(node,ast.FunctionDef) and node.name.startswith("test_")]
    result={"status":"passed","verification_type":"source bytes/Git identity + code/protocol static audit + synthetic-only tests",
        "source_count":len(source_checks),"authority_count":15,"source_checks":source_checks,
        "production_npz_files_decoded":0,"production_matrix_vector_arithmetic":0,
        "internal_array_hashes":"Inherited from source Phase B protocol; not recomputed by H4 decode in Phase0.5.",
        "science_action_counts":counts["current_phase05_science"],"protocol_sha256":digest,
        "truth_join_key_count":12,"truth_values_used_for_tuning":False,
        "formal_phase0_s4_sources_unchanged":True,"science_authorized":False,
        "production_cli_disabled":True,"synthetic_test_count":len(names),
        "synthetic_tests":names,"software":{"python":platform.python_version(),"numpy":numpy.__version__,"scipy":scipy.__version__,"pytest":pytest.__version__},
        "known_limits":["Synthetic tests do not establish H4 benefit.","Production adapter and noise/cold replay integration are specified but disabled/unconnected.","H4 sources and coordinates are known development data.","No operational quantum implementation or net resource improvement has been established."]}
    if args.write_verification:
        (HERE/"tests.log").write_text(completed.stdout+completed.stderr)
        (HERE/"verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"sources":len(source_checks),"synthetic_tests":len(names),"science_actions":0,"protocol_sha256":digest}))

if __name__=="__main__":
    main()
