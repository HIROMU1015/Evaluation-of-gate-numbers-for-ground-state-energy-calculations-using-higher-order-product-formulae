"""One-shot H8 memory gates; then inherited reference/prediction and serial truth.

New storage and object lifetimes only. No push or changed scientific rule.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import gc
import json
import os
from pathlib import Path
import sys
import threading
import time

import numpy as np
from scipy.sparse import csr_matrix, load_npz, save_npz
from scipy.sparse.linalg import norm as sparse_norm

import review_response.run_hchain_odd_extension as inherited
from review_response.hchain_input_reference_preparation import (
    AllowlistedArchive, PreparationError, VectorAdapter, bounded_stage, canonical_hash,
    checked_functions, sha_array, sha_file, write_json,
)
from review_response.hchain_prediction_phase import CoordinateActions, ReadBoundary, finite_json
from review_response.hchain_selective_calibration_schedule import BETA, EPSILON
from review_response.pf_spectral_recoverability_d2 import analyze_coordinate
from review_response.run_hchain_prediction_phase import fixed_environment
from review_response.run_hchain_truth_scoring import (
    full_unitary, ground_point, helper, serial_truth, utc, write_csv,
)
from review_response.hchain_truth_scoring import METHOD, truth_quality
from review_response.hchain_odd_extension import immutable_score
from review_response.hchain_h8_memory_safe import (
    BASE, BRANCH, DOC, OUT, STATUS, H8Ledger, StreamingVectorAdapter,
    array_digest_stream, commit_files, current_memory, dense_digest_stream,
    file_entry, git, load_system, plan_rows, read, runtime_gate, seal, source_gate,
    truth_feasibility, validate_plan, verify_blob, verify_entries,
)


def context(root):
    source = source_gate(root)
    auth = read(root/DOC/"protocol.json")
    if str(root) != auth["worktree"] or git(root, "branch", "--show-current").decode().strip() != BRANCH:
        raise PreparationError("frozen dedicated H8 worktree/branch required")
    fixed_environment(auth)
    return source, auth


def configure(root):
    """Explicit reuse of unmodified phase bodies, with H8 storage callbacks.

    Not a new reference/Arnoldi/policy implementation. Base source hashes are
    checked before configuring the requested system and source/output namespace.
    """
    context(root)
    inherited.DOC, inherited.OUT, inherited.SYSTEMS = DOC, OUT, ("H8",)
    inherited.source_gate = source_gate
    inherited.SystemLedger = H8Ledger
    inherited.generate = generate
    inherited.load_system = load_system
    inherited.plan_rows, inherited.validate_plan = plan_rows, validate_plan
    return inherited


def equivalence(root):
    source, auth = context(root)
    destination = root/DOC/"implementation_equivalence.json"
    if destination.exists():
        raise PreparationError("equivalence one-shot; no retuning/retry")
    regression = auth["regression"]
    parent = root.parent/regression["runtime_worktree"]
    archived = parent/regression["runtime_path"]
    if sha_file(archived) != regression["runtime_sha256"]:
        raise PreparationError("original H7 runtime changed; no replacement")
    expected = read(root/regression["prediction_payload"])
    inputs = read(root/regression["input_payload"])
    spec = inputs["input_identity"]["H7"]
    row = next(r for r in expected["plan"] if r["system"] == "H7" and r["ratio"] == .5)
    time_value = float.fromhex(row["time_hex"])
    sequence = [float.fromhex(t) for t in auth["PF"]["canonical_sequence_hex"]]
    keys = ["hamiltonian", "cisd", "sector_indices"]+[f"group_{i:03d}" for i in range(spec["group_count"])]
    access = []
    archive = AllowlistedArchive(archived, regression["runtime_sha256"], keys, access)
    checks, records = {}, {}
    rules = read(root/inherited.OLD/"rank_aware_M1_amendment.json")["numerical_rules"]
    # Freeze tolerances BEFORE results: strict inherited abs 1e-14 / rel 1e-12.
    def compare(key, old, new):
        checks[key] = {"old": float(old), "new": float(new), "absolute_difference": abs(float(old)-float(new)),
                       "pass": bool(np.isclose(old, new, atol=1e-14, rtol=1e-12))}
    try:
        h, state = archive.read("hamiltonian"), archive.read("cisd")
        for implementation in ("old", "streamed"):
            ledger = H8Ledger()
            with bounded_stage(ledger, f"H7_{implementation}_equivalence", 1800):
                if implementation == "old":
                    groups = [archive.read(k) for k in keys[3:]]
                    adapter = VectorAdapter(h, groups, sequence, ledger, allowed_kinds=("candidate", "m1"))
                    del groups
                else:
                    adapter = StreamingVectorAdapter(h, (archive.read(k) for k in keys[3:]),
                        spec["group_count"], sequence, ledger, allowed_kinds=("candidate", "m1"))
                pf = adapter.pf(state, time_value, kind="candidate")
                cheap = adapter.cheap(state, time_value, kind="candidate")
                actions = CoordinateActions(adapter, time_value, 8)
                prediction, _ = analyze_coordinate(start=state, apply_u=actions.pf, apply_h=actions.h,
                    time_value=time_value, prefix_dimensions=[1,2,4,8], primary_dimension=8,
                    previous_vector=None, numerical_rules=rules, epsilon_hartree=EPSILON,
                    beta=BETA, rotations_per_step=spec["K"])
                records[implementation] = {"PF": pf.copy(), "cheap": cheap, "M1": finite_json(prediction),
                                           "resources": ledger.payload()}
            del adapter
            gc.collect()
        old, new = records["old"], records["streamed"]
        checks["PF_vector"] = {"maximum_absolute_difference": float(np.max(np.abs(old["PF"]-new["PF"]))),
            "pass": bool(np.allclose(old["PF"], new["PF"], atol=1e-14, rtol=1e-12))}
        compare("cheap", old["cheap"]["delta_C_hartree"], new["cheap"]["delta_C_hartree"])
        for key in ("signed_shift_estimate_hartree", "empirical_width_hartree", "e_use_hartree"):
            compare(key, old["M1"][key], new["M1"][key])
        checks["M1_all_fields_exact"] = {"pass": canonical_hash(old["M1"]) == canonical_hash(new["M1"])}
        saved = expected["M1"]["H7"][0]["core_prediction"]
        for key in ("signed_shift_estimate_hartree", "empirical_width_hartree"):
            compare("saved_"+key, saved[key], new["M1"][key])
        for key in ("maximum_pf_norm_residual", "maximum_h_exp_norm_residual"):
            compare(key, old["resources"][key], new["resources"][key])
        passed = all(c["pass"] for c in checks.values())
        status = "implementation_equivalence_pass" if passed else "H8_memory_safe_implementation_not_equivalent"
        result = {"status": status, "coordinate": row, "checks": checks,
            "tolerances": {"absolute": 1e-14, "relative": 1e-12, "M1_all_fields": "byte-exact canonical JSON"},
            "source": source, "regression_runtime": {"path": str(archived), "sha256": sha_file(archived)},
            "access": access, "truth_accesses": 0, "GPU_operations": 0,
            "resources": {n: r["resources"] for n,r in records.items()},
            "unchanged_vector_methods": all(getattr(StreamingVectorAdapter, n) is getattr(VectorAdapter, n)
                                           for n in ("pf", "h_exp", "h_matvec", "cheap")), "utc": utc()}
        write_json(destination, result)
        commit_files(root, [destination], "Audit H7 old/streamed H8 storage equivalence")
        print(json.dumps({"status": status, "checks": checks}), flush=True)
    finally:
        archive.close()


def generate(root, out, spec, helpers, ledger, sequence, chemistry_sha):
    """Same even-chain integral/group/CISD bodies; CSR groups saved serially."""
    if read(root/DOC/"implementation_equivalence.json")["status"] != "implementation_equivalence_pass":
        raise PreparationError("equivalence gate failed; no H8 generation")
    from pyscf import ao2mo, gto, mcscf, scf
    from openfermion import FermionOperator, QubitOperator, jordan_wigner
    from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
    from trotterlib.component_sector_pf import qubit_operator_sector_matrix
    from trotterlib.pf_decomposition import iter_s2_sequence_steps
    private, n = out/".runtime", 8
    started = time.perf_counter()
    ledger.charge("Hamiltonian_generations", 1)
    mol = gto.Mole()
    mol.atom = [("H", (0., 0., float(i-(n-1)/2))) for i in range(n)]
    mol.unit, mol.basis, mol.spin, mol.charge, mol.symmetry = "Angstrom", "sto-3g", 0, 0, False
    mol.verbose, mol.output = 3, str(private/"H8_scf.log")
    mol.build()
    hf = scf.RHF(mol)
    hf.conv_tol, hf.max_cycle = 1e-12, 200
    hf.kernel()
    if not hf.converged or mol.nelectron != 8 or hf.mo_coeff.shape != (8,8):
        raise PreparationError("canonical RHF convergence gate failed")
    cas = mcscf.CASCI(hf, n, (4,4))
    cas.ncore = 0
    h1, scalar = cas.get_h1eff(hf.mo_coeff)  # No CASCI/FCI kernel or exact state.
    eri = ao2mo.restore(1, ao2mo.kernel(mol, hf.mo_coeff), n)
    two = np.asarray(eri.transpose(0,2,3,1), order="C")
    with (private/"H8_grouping.log").open("w") as log, redirect_stdout(log):
        grouper = Almost_optimal_grouper(float(scalar), np.asarray(h1), two,
            fermion_qubit_mapping=jordan_wigner, validation=True)
    grouped = grouper.group_term_list
    grouped[0].insert(0, FermionOperator("", grouper._const_fermion))
    ops = [jordan_wigner(sum(g, FermionOperator())) for g in grouped]
    real_ops, discarded = [], 0.
    for op in ops:
        real = QubitOperator()
        for term, coefficient in op.terms.items():
            discarded = max(discarded, abs(complex(coefficient).imag))
            if abs(complex(coefficient).imag) > 1e-9:
                raise PreparationError("imaginary Pauli coefficient gate failed")
            real += QubitOperator(term, float(complex(coefficient).real))
        real_ops.append(real)
    counts = [sum(bool(term) for term in op.terms) for op in real_ops]
    k = sum(counts[i] for i,_ in iter_s2_sequence_steps(len(counts), sequence))
    indices = helpers["sector_basis_indices"](16, spec["sector_kind"], [4,4])
    if len(indices) != 4900:
        raise PreparationError("H8 population dimension mismatch")
    h = csr_matrix((4900,4900), dtype=np.complex128)
    hashes, max_group_bytes, max_group_residual = [], 0, 0.
    for index, op in enumerate(real_ops):
        group = qubit_operator_sector_matrix(op,16,indices,remove_constant=True)
        max_group_bytes = max(max_group_bytes, group.data.nbytes+group.indices.nbytes+group.indptr.nbytes)
        max_group_residual = max(max_group_residual, float(sparse_norm(group-group.getH())))
        if max_group_residual > 1e-12:
            raise PreparationError("group Hermiticity gate failed")
        hashes.append(dense_digest_stream(group))
        h = h+group
        save_npz(private/f"H8_group_{index:03d}.npz", group)
        ledger.snapshot("group_generation", largest_object_bytes=max_group_bytes)
        del group
    ledger.timings["Hamiltonian_group_preparation"] += time.perf_counter()-started
    if not np.all(np.isfinite(h.data)) or sparse_norm(h-h.getH()) > 1e-12:
        raise PreparationError("Hamiltonian finite/Hermitian gate failed")
    reference = helpers["hartree_fock_full_basis_index"](16,spec["sector_kind"],[4,4])
    ledger.charge("CISD_generations",1)
    before = time.perf_counter()
    dense_h = h.toarray()  # The ONE permitted full H, not a group ensemble.
    ledger.snapshot("CISD_full_H", largest_object_bytes=dense_h.nbytes,
                    live_dense_matrices=1, explicit_large_allocations=1)
    state, generation = helpers["determinant_cisd_state"](dense_h,indices,reference)
    generation["subspace_positions"] = generation["subspace_positions"].tolist()
    del dense_h
    gc.collect()
    ledger.counts["CISD_subspace_eigh_calls"] += 1
    state *= np.exp(-1j*np.angle(state[int(np.argmax(np.abs(state)))]))
    ledger.timings["CISD_construction"] += time.perf_counter()-before
    positions = [i for i,index in enumerate(indices) if (int(index)^reference).bit_count()//2 <= 2]
    norm = float(np.linalg.norm(state))
    if len(positions) != 361 or abs(norm-1) > 1e-12 or not np.all(np.isfinite(state)):
        raise PreparationError("CISD support/dimension/norm gate failed")
    if any(abs(state[i]) > 1e-12 for i in range(len(state)) if i not in positions):
        raise PreparationError("CISD support gate failed")
    ledger.charge("input_verification_h_matvecs",1)
    action = h@state
    expectation = float(np.vdot(state,action).real/(norm*norm))
    terms = [[{"term":[[int(q),str(p)] for q,p in term],"coefficient":float(coef.real)}
              for term,coef in op.terms.items()] for op in real_ops]
    identity = {"H_sha256_numpy_v1": dense_digest_stream(h), "CISD_sha256_numpy_v1":sha_array(state),
        "group_sha256_numpy_v1":hashes,"sector_indices_sha256_numpy_v1":sha_array(indices),
        "sector_dimension":4900,"CISD_subspace_dimension":361,"CISD_positions":positions,
        "CISD_positions_sha256_numpy_v1":sha_array(np.asarray(positions,dtype=np.int64)),
        "RHF_reference_integer":int(reference),"state_norm":norm,"H_expectation_hartree":expectation,
        "H_expectation_residual_hartree":float(np.linalg.norm(action-expectation*state)),
        "H_hermiticity_residual":float(sparse_norm(h-h.getH())),"maximum_group_Hermiticity_residual":max_group_residual,
        "group_sum_residual":0.,"group_sum_check_method":"H is ordered CSR sum; checked by construction, no second ensemble",
        "K":k,"group_count":len(real_ops),"nonidentity_Pauli_counts":counts,
        "ordered_term_coefficient_sha256":canonical_hash(terms),
        "ordered_group_structure_sha256":canonical_hash([[r["term"] for r in g] for g in terms]),
        "MO_sha256_numpy_v1":sha_array(hf.mo_coeff),"SCF_method":type(hf).__name__,"SCF_converged":True,
        "maximum_discarded_imaginary_Pauli_coefficient":discarded,"CISD_is_ground_certificate":False,
        "CISD_equals_full_population_sector":False,"exact_state_input_used":False,
        "phase_alignment_to_exact_performed":False,"new_state_phase":"largest_component_real_positive",
        "historical_byte_identity_claim":False,"legacy_K_47932_assumed":False,
        "maximum_generated_group_CSR_bytes":max_group_bytes,"CISD_generation":generation,
        "generation_source_sha256":sha_file(root/"review_response/run_hchain_h8_memory_safe.py")}
    save_npz(private/"H8_H.npz",h)
    np.savez_compressed(private/"H8_state.npz",cisd=state,sector_indices=indices)
    np.savez_compressed(private/"H8_integrals.npz",mo=hf.mo_coeff,h1=h1,two_body=two,scalar=np.asarray(scalar))
    write_json(private/"H8_group_operators.json",{"groups":terms,"K":k,"counts":counts})
    ledger.snapshot("input_complete",largest_object_bytes=max_group_bytes)
    return identity


def preflight(root):
    source, auth = context(root)
    engine = configure(root)
    out = root/OUT
    if (out/"resource_preflight.json").exists() or (out/"preflight_STARTED.json").exists():
        raise PreparationError("one-shot resource preflight; no retry")
    inputs, input_commit = engine.frozen(root,out,"inputs")
    write_json(out/"preflight_STARTED.json",{"utc":utc(),"input_commit":input_commit})
    members, ledger = [], H8Ledger()
    allowed = [root/r["path"] for r in source["inherited_sources"]+source["new_files"]]
    allowed += [root/DOC/"implementation_manifest.json",root/DOC/"implementation_equivalence.json"]
    allowed += list((root/"src").rglob("*.py"))+list((root/"review_response").glob("*.py"))
    boundary = ReadBoundary(root,allowed,out)
    sys.addaudithook(boundary.hook)
    try:
        seq = [float.fromhex(t) for t in auth["PF"]["canonical_sequence_hex"]]
        with bounded_stage(ledger,"H8_preflight_component_preprocessing",1800):
            system = load_system(out,inputs,"H8",ledger,members,seq,("reference","m1"))
        adapter, state = system["adapter"],system["state"]
        observations = []
        for name, call in (
            ("one_cold_PF_vector_action",lambda:adapter.pf(state,.02)),
            ("one_H_exponential_action",lambda:adapter.h_exp(state,.02)),
            ("one_warm_M1_PF_vector_action",lambda:adapter.pf(state,.02,kind="m1")),
            ("one_H_matvec",lambda:adapter.h_matvec(state))):
            before=time.perf_counter()
            value=call()
            observations.append({"stage":name,"wall_seconds":time.perf_counter()-before,
                **ledger.snapshot(name,largest_object_bytes=value.nbytes),"result_norm":float(np.linalg.norm(value))})
            del value
        timings={r["stage"]:r["wall_seconds"] for r in observations}
        cold=timings["one_cold_PF_vector_action"]
        warm=timings["one_warm_M1_PF_vector_action"]
        hexp=timings["one_H_exponential_action"]
        matvec=timings["one_H_matvec"]
        preprocessing=ledger.timings["H8_preflight_component_preprocessing"]
        ref_estimate=2*(preprocessing+34*(cold+hexp))
        pred_estimate=2*(preprocessing+3*(cold+hexp)+24*(warm+matvec))
        prior=read(root/auth["regression"]["truth_resource_audit"])["resources"]["systems"]["H7"]["timings_seconds"]
        h7_input=read(root/auth["regression"]["input_payload"])["input_identity"]["H7"]
        # Shared matrix-action sequence length, not quantum K, controls this scaling.
        from trotterlib.pf_decomposition import iter_s2_sequence_steps
        old_steps=len(tuple(iter_s2_sequence_steps(h7_input["group_count"],seq)))
        feasibility=truth_feasibility(4900,current_memory()["VmRSS_bytes"],prior,len(adapter.steps)/old_steps)
        memory_ok=ledger.payload()["peak_RSS_KiB"]*1024 < 4*1024**3
        time_ok=max(ref_estimate,pred_estimate)<1800
        status=("H8_memory_safe_execution_ready" if memory_ok and time_ok and feasibility["feasible"] else
            "H8_memory_safe_prediction_ready_truth_blocked" if memory_ok and time_ok else "H8_memory_safe_resource_blocked")
        result={"status":status,"input_commit":input_commit,"gate_A_equivalence":True,"gate_B_frozen_identity":True,
            "gate_C_memory":memory_ok,"gate_D_reference_prediction_runtime":time_ok,"gate_E_truth":feasibility,
            "observations":observations,"storage":adapter.storage_profile(),"resources":ledger.payload(),
            "reference_estimated_seconds":ref_estimate,"prediction_estimated_seconds":pred_estimate,
            "runtime_estimate_class":"twofold planning allowance on measured primitives, not a rigorous bound",
            "truth_not_benchmarked_before_prediction":True,"access":boundary.payload(members),"utc":utc()}
        write_json(out/"resource_preflight.json",result)
        write_json(out/"execution_decision.json",{"status":status,"gates_sha256":sha_file(out/"resource_preflight.json"),
            "science_execution_allowed":status=="H8_memory_safe_execution_ready","push_authorized":False,
            "threshold_changes_authorized":False,"next_stage_authorized":False})
        commit_files(root,[out/"resource_preflight.json",out/"execution_decision.json",out/"preflight_STARTED.json"],
                     "Freeze measured H8 memory/time preflight and execution gates")
        print(json.dumps({"status":status,"truth_feasibility":feasibility,"reference_estimated_seconds":ref_estimate,
                          "prediction_estimated_seconds":pred_estimate}),flush=True)
    except BaseException as error:
        write_json(out/"preflight_FAILURE.json",{"utc":utc(),"message":str(error),"resources":ledger.payload(),
                   "access":boundary.payload(members),"no_retry_or_rescue_authorized":True})
        raise
    finally:
        boundary.enabled=False


def execution_gate(root):
    path=root/OUT/"execution_decision.json"
    verify_blob(root,str(path.relative_to(root)),"HEAD")
    if read(path)["status"] != "H8_memory_safe_execution_ready":
        raise PreparationError("resource gate blocks reference, prediction and truth")


def truth(root):
    """Unchanged dense ground/Schur algorithm, ONE coordinate and copied continuation vector."""
    source,auth=context(root)
    execution_gate(root)
    engine=configure(root)
    out=root/OUT
    if (out/"truth_STARTED.json").exists():
        raise PreparationError("one truth acquisition only")
    prediction,pred_commit=engine.frozen(root,out,"prediction")
    inputs,input_commit=engine.frozen(root,out,"inputs")
    reference,ref_commit=engine.frozen(root,out,"reference")
    plan=validate_plan(prediction["plan"],reference["references"],inputs["input_identity"])
    write_json(out/"truth_STARTED.json",{"utc":utc(),"prediction_commit":pred_commit})
    ledger,members=H8Ledger(),[]
    allowed=[root/r["path"] for r in source["inherited_sources"]+source["new_files"]]
    allowed += [root/DOC/"implementation_manifest.json"]+list((root/"src").rglob("*.py"))
    allowed += list((root/"review_response").glob("*.py"))
    boundary=ReadBoundary(root,allowed,out)
    sys.addaudithook(boundary.hook)
    stages={"prediction_commit":pred_commit,"input_commit":input_commit,"reference_commit":ref_commit}
    def freeze(name,payload,marker):
        access=boundary.payload(members)
        access["truth_array_reads"]=ledger.counts["truth_array_reads"]
        return engine.freeze(root,out,name,payload,marker,source_gate(root),access,ledger.payload())
    try:
        method=read(root/METHOD)
        seq=[float.fromhex(v) for v in auth["PF"]["canonical_sequence_hex"]]
        with bounded_stage(ledger,"H8_same_H_ground",1800):
            loaded=load_system(out,inputs,"H8",ledger,members,seq,())
            h=loaded["adapter"].h.toarray()
            ledger.snapshot("same_H_ground_input",largest_object_bytes=h.nbytes,live_dense_matrices=1,explicit_large_allocations=1)
            record,view=ground_point(h,inputs["input_identity"]["H8"],method,ledger)
            exact=view.copy()  # Never retain all 4900 eigenvectors through a column view.
            del view,h
            gc.collect()
            path=out/".runtime/H8_ground.npz"
            np.savez_compressed(path,ground_vector=exact,energy=np.asarray(record["energy_hartree"]))
            record["runtime_file"]=file_entry(out/".runtime",path)
            ledger.snapshot("same_H_ground_released")
        ground={"systems":{"H8":record},**stages}
        stages["ground_commit"]=freeze("ground",ground,"GROUND_FROZEN")
        engine.frozen(root,out,"ground")
        verify_entries(out/".runtime",[record["runtime_file"]])
        with np.load(path,allow_pickle=False) as archive:
            exact=archive["ground_vector"].copy()
            energy=float(archive["energy"])
        ledger.counts["truth_array_reads"]+=1
        if sha_array(exact)!=record["ground_vector_sha256_numpy_v1"] or energy!=record["energy_hartree"]:
            raise PreparationError("same-H ground freeze mismatch")
        direct=helper(root)
        previous,points=None,[]
        for index,row in enumerate(plan):
            engine.frozen(root,out,"prediction")
            with bounded_stage(ledger,f"H8_truth_{row['candidate_id']}",1800):
                before=time.perf_counter()
                u=full_unitary(loaded["adapter"],row["time"],ledger)
                ledger.timings["truth_full_PF_construction"]+=time.perf_counter()-before
                ledger.snapshot("one_full_PF",largest_object_bytes=u.nbytes,live_dense_matrices=1,explicit_large_allocations=1)
                ledger.charge("direct_Schur_solves",3)
                before=time.perf_counter()
                point,view=direct(u,exact,energy,row["time"],row["K"],EPSILON,previous,1e-8)
                previous=view.copy()  # Selected vector only, not the full Schur matrix view.
                del view,u
                gc.collect()
                ledger.timings["truth_Schur_branch_gap"]+=time.perf_counter()-before
                ledger.charge("direct_truth_coordinates",3)
                ledger.charge("target_phase_gaps",3)
                point=serial_truth(point)
                point.update({"system":"H8","candidate_id":row["candidate_id"],"time_hex":row["time_hex"],
                    "H_sha256_numpy_v1":inputs["input_identity"]["H8"]["H_sha256_numpy_v1"],
                    "ground_vector_sha256_numpy_v1":record["ground_vector_sha256_numpy_v1"],
                    "phase_unwrap_basis":"principal_ground_relative","computed":True,"reused":False,
                    "initial_or_continuation":"initial_exact_ground" if index==0 else "previous_selected_vector"})
                point["quality"]=truth_quality(point,method)
                ledger.snapshot("coordinate_dense_objects_released")
                points.append(point)
                write_json(out/"truth_checkpoints"/f"{row['candidate_id']}.json",point)
                print(json.dumps({"event":"DIRECT_POINT","candidate":row["candidate_id"],"quality":point["quality"]["status"]}),flush=True)
        stages["truth_commit"]=freeze("truth",{"points":points,"coordinate_count":3,"nearest_or_interpolation":0,**stages},"TRUTH_FROZEN")
        prediction,_=engine.frozen(root,out,"prediction")
        ground,_=engine.frozen(root,out,"ground")
        truths,_=engine.frozen(root,out,"truth")
        scored=immutable_score(prediction,truths,ground)
        scored["status"],scored["stage_commits"]=STATUS,stages
        write_json(out/"scoring.json",scored)
        write_csv(out/"coordinate_scoring.csv",scored["coordinate_scores"])
        write_csv(out/"decision_scoring.csv",scored["decision_scores"])
        stages["scoring_commit"]=freeze("scored",scored,"IMMUTABLE_SCORING_COMPLETE")
        write_json(out/"COMPLETE.json",{"status":STATUS,"utc":utc(),**stages,
            "next_stage_authorized":False,"push_authorized":False,"old_formal_results_unchanged":True})
        write_json(out/"truth_execution_audit.json",{"phase":"truth","resources":ledger.payload(),
            "access":boundary.payload(members),"truth_array_reads":ledger.counts["truth_array_reads"],"utc":utc()})
    except BaseException as error:
        write_json(out/"truth_FAILURE.json",{"status":"H8_truth_resource_blocked_after_prediction_freeze"
            if isinstance(error,(MemoryError,PreparationError)) else "H8_truth_execution_failure",
            "message":str(error),"resources":ledger.payload(),"prediction_modified":False,"no_retry":True})
        raise
    finally:
        boundary.enabled=False


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",required=True,choices=("seal","equivalence","inputs","preflight","reference","prediction","truth"))
    args=parser.parse_args()
    root=Path.cwd().resolve()
    stop=threading.Event()
    def own_memory_watchdog():
        # Only /proc/self: never inspect or signal another user's process.
        while not stop.wait(.05):
            memory=current_memory()
            if memory.get("VmRSS_bytes",0)>4*1024**3 or memory.get("VmSwap_bytes",0)>0:
                directory=root/OUT
                if directory.exists():
                    write_json(directory/f"{args.phase}_RESOURCE_STOP.json",{
                        "status":"H8_truth_resource_blocked_after_prediction_freeze" if args.phase=="truth"
                                 else "H8_memory_safe_resource_blocked",
                        "phase":args.phase,"memory":memory,"utc":utc(),"own_process_exit_only":True,
                        "prediction_modified":False,"no_retry_or_rescue_authorized":True})
                os._exit(93)
    watcher=threading.Thread(target=own_memory_watchdog,daemon=True)
    if args.phase!="seal":watcher.start()
    try:
        if args.phase=="seal": seal(root)
        elif args.phase=="equivalence": equivalence(root)
        elif args.phase=="preflight": preflight(root)
        elif args.phase=="truth": truth(root)
        else:
            if args.phase!="inputs": execution_gate(root)
            configure(root).execute(root,args.phase)
    finally:
        stop.set()
        if watcher.is_alive():watcher.join(timeout=1.)


if __name__=="__main__":
    main()
