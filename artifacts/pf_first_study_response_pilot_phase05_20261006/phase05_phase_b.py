"""Phase B scoring only: consumes byte-verified immutable predictions."""
from dataclasses import dataclass
import hashlib
import json
import re
import subprocess
import numpy as np
from phase05_math import TRAIN,EVAL,fit_two_term_model,evaluate_fit

@dataclass(frozen=True, slots=True)
class FrozenPredictions:
    raw: bytes
    sha256: str
    commit: str

def verify_frozen_predictions(raw,expected_sha256,commit,committed_blob):
    if not re.fullmatch(r"[0-9a-f]{40}",commit):
        raise ValueError("full commit SHA required")
    if hashlib.sha256(raw).hexdigest()!=expected_sha256 or raw!=committed_blob:
        raise ValueError("Phase A hash / committed blob mismatch; stop before truth")
    return FrozenPredictions(bytes(raw),expected_sha256,commit)

def read_committed_prediction_blob(repository,commit,relative_path):
    if not re.fullmatch(r"[0-9a-f]{40}",commit) or relative_path.startswith("/") or ".." in relative_path.split("/"):
        raise ValueError("invalid committed blob address")
    return subprocess.check_output(["git","-C",str(repository),"show",f"{commit}:{relative_path}"])

def score_saved_truth(frozen,truth_rows,oracle_signed_rows=None):
    if type(frozen) is not FrozenPredictions or hashlib.sha256(frozen.raw).hexdigest()!=frozen.sha256:
        raise ValueError("verified frozen predictions required")
    payload=json.loads(frozen.raw)
    expected={sign*t for t in (.125,.175,.225,.275,.35,.40) for sign in (1,-1)}
    if len(truth_rows)!=12 or {r["time"] for r in truth_rows}!=expected:
        raise ValueError("exactly 12 distinct saved evaluation coordinates required")
    if any(not r["branch_reliable"] for r in truth_rows):
        raise ValueError("saved branch unreliable; stop scoring without repair")
    truth={r["time"]:r for r in truth_rows}
    oracle_fits=None
    if oracle_signed_rows is not None:
        oracle_coordinates={s*t for t in TRAIN+EVAL for s in (1,-1)}
        if len(oracle_signed_rows)!=22 or {r["time"] for r in oracle_signed_rows}!=oracle_coordinates:
            raise ValueError("exactly 22 saved oracle proxy rows required")
        oracle={r["time"]:r for r in oracle_signed_rows}
        if any(oracle[t]["proxy"]!=truth[t]["exact_proxy"] for t in expected):
            raise ValueError("inconsistent saved exact-proxy reference")
        oracle_fits=fit_two_term_model(TRAIN,[oracle[t]["proxy"] for t in TRAIN],
            [oracle[-t]["proxy"] for t in TRAIN],[oracle[t]["quality"] for t in TRAIN])
        model=oracle_fits["raw_positive_even_two_term"]
        payload["predictions"]["A3"]=[{"time":s*t,"prediction":evaluate_fit(model,s*t),
            "proxy":oracle[s*t]["proxy"]} for t in EVAL for s in (1,-1)]
    result={}
    for arm,predictions in payload["predictions"].items():
        if len(predictions)!=12 or {r["time"] for r in predictions}!=expected:
            raise ValueError("incomplete Phase A predictions")
        rows=[]
        for p in predictions:
            t=p["time"]; direct=truth[t]["direct_shift"]; exact=truth[t]["exact_proxy"]
            if not all(np.isfinite(x) for x in (p["prediction"],p["proxy"],direct,exact)):
                raise ValueError("nonfinite scoring scalar")
            error=p["prediction"]-direct
            u=abs(direct)-abs(p["prediction"])
            rows.append({"time":t,"prediction":p["prediction"],"direct_shift":direct,
                "state_like_error":p["proxy"]-exact,"total_error":error,"absolute_error":abs(error),
                "underestimation":u,"positive_underestimation":max(0,u),
                "sign_crossing":bool(np.sign(p["prediction"])!=np.sign(direct))})
        result[arm]={"rows":rows,"S_abs":sum(r["absolute_error"] for r in rows),
            "S_under":sum(r["positive_underestimation"] for r in rows),
            "E_max":max(r["absolute_error"] for r in rows),
            "sign_crossing_count":sum(r["sign_crossing"] for r in rows)}
    baseline={r["time"]:r for r in result["A0"]["rows"]}
    for value in result.values():
        value["improved_count"]=sum(r["absolute_error"]<baseline[r["time"]]["absolute_error"] for r in value["rows"])
        value["worsened_count"]=sum(r["absolute_error"]>baseline[r["time"]]["absolute_error"] for r in value["rows"])
    return {"phase_a_commit":frozen.commit,"phase_a_sha256":frozen.sha256,
        "saved_direct_truth_read_count":12,"new_direct_truth_count":0,"arms":result,
        "saved_exact_proxy_read_count":22 if oracle_signed_rows is not None else 12,
        "oracle_fits":oracle_fits}

def classify_outcome(base,response,ritz,*,residual_converged,response_point_improved,
                     stable=True):
    """Frozen logical predicates; costs are standalone H and total PF actions.

    No invented percentage gate. Mixed cases remain explicitly inconclusive.
    """
    rb=response["S_abs"]<base["S_abs"] and response["S_under"]<base["S_under"]
    kb=ritz["S_abs"]<base["S_abs"] and ritz["S_under"]<base["S_under"]
    rt=(response["S_abs"],response["S_under"],response["H_actions"],response["PF_actions"])
    kt=(ritz["S_abs"],ritz["S_under"],ritz["H_actions"],ritz["PF_actions"])
    ritz_dominates=all(k<=r for k,r in zip(kt,rt)) and any(k<r for k,r in zip(kt,rt))
    unique=not ritz_dominates and any(r<k for r,k in zip(rt,kt))
    if not stable:
        return "no_benefit_numerically_unstable"
    if rb and residual_converged and unique:
        return "response_specific_support"
    if rb and kb and not unique:
        return "generic_state_improvement"
    if response_point_improved and not rb:
        return "point_only"
    if not rb and not kb:
        return "no_benefit"
    return "inconclusive_mixed_predicates"
