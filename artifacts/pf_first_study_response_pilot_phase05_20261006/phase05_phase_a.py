"""Synthetic Phase A. Typed input contains no truth and no file loader."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np
from phase05_math import (ActionLedger, M_VALUES, TRAIN, EVAL, build_response_basis,
    factor_response, solve_response_least_squares, compute_a_from_echo,
    compute_response_proxy, solve_ritz_state, compute_proxy_for_state,
    fit_two_term_model, evaluate_fit, require_synthetic)

@dataclass(frozen=True, slots=True)
class PhaseAInput:
    H: np.ndarray
    psi: np.ndarray
    signed_echoes: dict
    input_kind: str = "synthetic"

def build_predictions(inputs: PhaseAInput, ledger: ActionLedger):
    if type(inputs) is not PhaseAInput or inputs.input_kind != "synthetic":
        raise TypeError("Phase 0.5 only accepts typed synthetic PhaseAInput")
    require_synthetic(inputs.H,inputs.psi)
    coordinates=tuple(sign*t for t in TRAIN+EVAL for sign in (1,-1))
    if set(inputs.signed_echoes)!=set(coordinates):
        raise ValueError("exact fixed signed grid required")
    basis=build_response_basis(inputs.H,inputs.psi,ledger)
    factors,states={},{}
    for m in M_VALUES:
        k=min(m,basis.Z.shape[1])
        if k not in factors:
            factors[k]=factor_response(basis,m,ledger)
            states[k]=solve_ritz_state(basis,m,ledger)[0]
    rows=[]
    for t in coordinates:
        W=inputs.signed_echoes[t]
        if W.shape!=inputs.H.shape or np.linalg.norm(W.conj().T@W-np.eye(len(inputs.psi)))>1e-10:
            raise ValueError("echo unitary gate")
        base,a=compute_a_from_echo(W,inputs.psi,t,ledger)
        row={"time":t,"g_base":base,"response":{},"ritz":{},"residuals":{}}
        response_cache,ritz_cache={},{}
        for m in M_VALUES:
            k=min(m,basis.Z.shape[1])
            if k not in response_cache:
                z,diagnostic=solve_response_least_squares(factors[k],a,ledger)
                response_cache[k]=(compute_response_proxy(base,z,basis.r),diagnostic)
                ritz_cache[k]=base if k==0 else compute_proxy_for_state(W,states[k],t,ledger,original=False)[0]
            row["response"][str(m)],row["residuals"][str(m)]=response_cache[k]
            row["ritz"][str(m)]=ritz_cache[k]
        rows.append(row)
    # Synthetic unit fixtures supply resolved data. Future production adapter
    # must compute each arm's frozen rho from cold repeatability + roundoff gates.
    arms={"A0":("g_base",None),"A1":("response","8"),"A2":("ritz","8")}
    arms.update({f"response_m{m}":("response",str(m)) for m in (1,2,4)})
    arms.update({f"ritz_m{m}":("ritz",str(m)) for m in (1,2,4)})
    lookup={r["time"]:r for r in rows}
    fits,predictions={},{}
    for arm,(field,m) in arms.items():
        value=lambda t:lookup[t][field] if m is None else lookup[t][field][m]
        fits[arm]=fit_two_term_model(TRAIN,[value(t) for t in TRAIN],[value(-t) for t in TRAIN],["resolved"]*5)
        model=fits[arm]["raw_positive_even_two_term"]
        predictions[arm]=[{"time":sign*t,"prediction":evaluate_fit(model,sign*t),"proxy":value(sign*t)} for t in EVAL for sign in (1,-1)]
    return {"input_kind":"synthetic","rows":rows,"fits":fits,"predictions":predictions,
        "effective_basis_dimension":basis.Z.shape[1],"ledger":ledger.synthetic.copy()}

def frozen_bytes(payload):
    return json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def freeze_prediction_identity(payload):
    raw=frozen_bytes(payload)
    return raw,hashlib.sha256(raw).hexdigest()
