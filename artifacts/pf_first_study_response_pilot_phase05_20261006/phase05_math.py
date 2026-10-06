"""Phase 0.5 synthetic-only reference kernels; no archive or truth loaders."""
from dataclasses import dataclass, field
import numpy as np

EPS = np.finfo(np.float64).eps
KAPPA = 64.0
M_VALUES = (1, 2, 4, 8)
TRAIN = (0.10, 0.15, 0.20, 0.25, 0.30)
EVAL = (0.125, 0.175, 0.225, 0.275, 0.35, 0.40)
COUNTERS = (
    "H_matvec_count", "projection_count", "orthogonalization_count",
    "small_dense_response_solve_count", "response_svd_factorization_count",
    "small_dense_ritz_eigh_count", "PF_forward_action_count",
    "PF_adjoint_action_count", "PF_action_on_original_state_count",
    "PF_action_on_ritz_state_count", "exact_H_echo_action_count",
    "new_direct_truth_count", "saved_direct_truth_read_count",
    "new_vector_preparation_count", "new_state_preparation_count",
)

@dataclass
class ActionLedger:
    synthetic: dict = field(default_factory=lambda: dict.fromkeys(COUNTERS, 0))
    science: dict = field(default_factory=lambda: dict.fromkeys(COUNTERS, 0))

    def add(self, name, count=1):
        # This module has deliberately no science execution path.
        if name not in self.synthetic:
            raise KeyError(name)
        self.synthetic[name] += count

def require_synthetic(H, psi):
    H = np.asarray(H, dtype=np.complex128)
    psi = np.asarray(psi, dtype=np.complex128)
    if H.ndim != 2 or H.shape[0] != H.shape[1] or not 1 <= len(psi) <= 16:
        raise ValueError("Phase 0.5 kernels accept synthetic dimension <=16 only")
    if psi.shape != (H.shape[0],) or not np.all(np.isfinite(H)) or not np.all(np.isfinite(psi)):
        raise ValueError("invalid synthetic inputs")
    if abs(np.vdot(psi, psi).real - 1) > 1e-12:
        raise ValueError("state norm gate")
    if np.linalg.norm(H-H.conj().T) > 1e-12 * max(np.linalg.norm(H), np.finfo(float).tiny):
        raise ValueError("Hermiticity gate")
    return H, psi

def project(psi, v, ledger):
    ledger.add("projection_count")
    return v - psi * np.vdot(psi, v)

def fix_phase(v):
    pivot = int(np.argmax(np.abs(v)))
    return v * np.exp(-1j*np.angle(v[pivot])) if abs(v[pivot]) else v

@dataclass
class Basis:
    psi: np.ndarray
    energy: float
    r: np.ndarray
    Z: np.ndarray
    Hpsi: np.ndarray
    HZ: np.ndarray
    B: np.ndarray
    stopped: bool
    attempted_thresholds: tuple

def build_response_basis(H, psi, ledger, max_m=8):
    H, psi = require_synthetic(H, psi)
    if max_m not in M_VALUES:
        raise ValueError("fixed m only")
    n = len(psi)
    Hpsi = H @ psi
    ledger.add("H_matvec_count")
    energy = float(np.vdot(psi, Hpsi).real)
    r = project(psi, Hpsi-energy*psi, ledger)
    candidate = r.copy()
    scale = max(np.linalg.norm(Hpsi), abs(energy), np.finfo(float).tiny)
    zs, hzs, bs, thresholds = [], [], [], []
    stopped = False
    for _ in range(max_m):
        for _pass in range(2):
            candidate = project(psi, candidate, ledger)
            for z in zs:
                candidate -= z*np.vdot(z, candidate)
                ledger.add("orthogonalization_count")
        threshold = KAPPA*EPS*n*scale
        thresholds.append(float(threshold))
        norm = float(np.linalg.norm(candidate))
        if norm <= threshold:
            stopped = True
            break
        z = fix_phase(candidate/norm)
        Hz = H @ z
        ledger.add("H_matvec_count")
        ledger.add("new_vector_preparation_count")
        b = project(psi, Hz-energy*z, ledger)
        zs.append(z); hzs.append(Hz); bs.append(b)
        candidate = b.copy()
        scale = max(np.linalg.norm(Hz), np.linalg.norm(b), abs(energy), np.finfo(float).tiny)
    Z = np.column_stack(zs) if zs else np.empty((n, 0), complex)
    HZ = np.column_stack(hzs) if zs else np.empty((n, 0), complex)
    B = np.column_stack(bs) if zs else np.empty((n, 0), complex)
    if np.linalg.norm(Z.conj().T@Z-np.eye(len(zs))) > KAPPA*EPS*n or np.linalg.norm(psi.conj()@Z) > KAPPA*EPS*n:
        raise ValueError("orthogonality gate; no third reorthogonalization pass")
    return Basis(psi, energy, r, Z, Hpsi, HZ, B, stopped, tuple(thresholds))

@dataclass
class ResponseFactor:
    Z: np.ndarray
    B: np.ndarray
    U: np.ndarray
    s: np.ndarray
    Vh: np.ndarray
    retained: np.ndarray
    threshold: float

def factor_response(basis, m, ledger):
    if m not in M_VALUES:
        raise ValueError("fixed m only")
    k = min(m, basis.Z.shape[1])
    Z, B = basis.Z[:, :k], basis.B[:, :k]
    if not np.all(np.isfinite(B)):
        raise ValueError("nonfinite response matrix")
    if k:
        U,s,Vh = np.linalg.svd(B, full_matrices=False)
        ledger.add("response_svd_factorization_count")
        threshold = KAPPA*EPS*max(B.shape)*s[0]
    else:
        U,s,Vh = np.empty((len(basis.psi),0),complex),np.empty(0),np.empty((0,0),complex)
        threshold = 0.0
    return ResponseFactor(Z, B, U, s, Vh, s > threshold, float(threshold))

def solve_response_least_squares(factor, a, ledger):
    a=np.asarray(a,dtype=np.complex128)
    if a.shape!=(factor.B.shape[0],) or not np.all(np.isfinite(a)):
        raise ValueError("nonfinite or mismatched response RHS")
    keep = factor.retained
    c = np.zeros(factor.Z.shape[1], complex)
    if len(c):
        ledger.add("small_dense_response_solve_count")
        if np.any(keep):
            c = factor.Vh[keep].conj().T @ ((factor.U[:,keep].conj().T @ a)/factor.s[keep])
    z = factor.Z @ c
    d = a-factor.B @ c
    a_norm, z_norm, d_norm = float(np.linalg.norm(a)),float(np.linalg.norm(z)),float(np.linalg.norm(d))
    eps_num = KAPPA*EPS*max(len(a),1)*max(a_norm,1.0)  # Fixed 1 Ha scale floor.
    retained_s = factor.s[keep]
    if not np.all(np.isfinite(z)) or not np.all(np.isfinite(d)):
        raise ValueError("nonfinite response solution")
    complex_pair=lambda x:[float(np.real(x)),float(np.imag(x))]
    return z, {"d_norm":d_norm,"relative_residual":d_norm/max(a_norm,eps_num),
        "z_norm":z_norm,"effective_rank":int(np.sum(keep)),
        "condition_number":float(retained_s[0]/retained_s[-1]) if len(retained_s) else None,
        "singular_values":factor.s.tolist(),"svd_threshold":factor.threshold,
        "basis_dimension":factor.Z.shape[1],"epsilon_num":float(eps_num),
        "condition_number_full":float(factor.s[0]/factor.s[-1]) if len(factor.s) and factor.s[-1]>0 else None,
        "full_condition_status":"finite" if len(factor.s) and factor.s[-1]>0 else "singular_or_empty",
        "L_m_complex_pairs":[[complex_pair(x) for x in row] for row in factor.Z.conj().T@factor.B],
        "a_m_complex_pairs":[complex_pair(x) for x in factor.Z.conj().T@a],
        "coefficient_norm":float(np.linalg.norm(c)),
        "numerical_residual_allowance":KAPPA*EPS*len(a)*(a_norm+np.linalg.norm(factor.B)*np.linalg.norm(c))}

def compute_response_proxy(g_base, z, r):
    return float(g_base-2*np.vdot(z,r).real)

def solve_ritz_state(basis, m, ledger):
    if m not in M_VALUES:
        raise ValueError("fixed m only")
    k=min(m,basis.Z.shape[1])
    V=np.column_stack((basis.psi,basis.Z[:,:k]))
    HV=np.column_stack((basis.Hpsi,basis.HZ[:,:k]))
    projected=V.conj().T@HV
    anti=np.linalg.norm(projected-projected.conj().T)
    if anti > KAPPA*EPS*len(basis.psi)*max(np.linalg.norm(projected),np.finfo(float).tiny):
        raise ValueError("projected Hermiticity gate")
    if not k:
        return basis.psi.copy(), {"lowest_energy":basis.energy,"projected_dimension":1,"degeneracy":1}
    values, vectors=np.linalg.eigh((projected+projected.conj().T)/2)
    ledger.add("small_dense_ritz_eigh_count")
    tol=KAPPA*EPS*len(projected)*max(np.linalg.norm(projected,2),np.finfo(float).tiny)
    low=vectors[:,values-values[0] <= tol]
    # Deterministic lowest-eigenspace tie: project e0, then e1,... if needed.
    for j in range(len(projected)):
        coeff=low@low[j,:].conj()
        if np.linalg.norm(coeff)>KAPPA*EPS*len(projected):
            coeff=coeff/np.linalg.norm(coeff)
            break
    state=fix_phase(V@coeff)
    ledger.add("new_state_preparation_count")
    return state,{"lowest_energy":float(values[0]),"projected_dimension":k+1,"degeneracy":low.shape[1]}

def compute_proxy_for_state(W, state, t, ledger, original=True):
    if not t:
        raise ValueError("t=0 excluded")
    if len(state)>16:
        raise ValueError("synthetic only")
    ledger.add("PF_forward_action_count")
    ledger.add("exact_H_echo_action_count")
    ledger.add("PF_action_on_original_state_count" if original else "PF_action_on_ritz_state_count")
    w=W@state
    return float(np.vdot(state,w).imag/t), w

def compute_a_from_echo(W, psi, t, ledger):
    base,w=compute_proxy_for_state(W,psi,t,ledger)
    ledger.add("PF_adjoint_action_count")
    ledger.add("PF_action_on_original_state_count")
    ledger.add("exact_H_echo_action_count")
    adj=W.conj().T@psi
    a=project(psi,(w-adj)/(2j*t),ledger)
    return base,a

def fit_two_term_model(times, positive, negative, positive_quality):
    if tuple(times)!=TRAIN or len(positive_quality)!=5:
        raise ValueError("fixed training grid required")
    quality=all(q in ("marginal","resolved") for q in positive_quality) and sum(q=="resolved" for q in positive_quality)>=3
    output={}
    pos,neg=np.asarray(positive,float),np.asarray(negative,float)
    if pos.shape!=(5,) or neg.shape!=(5,) or not np.all(np.isfinite(pos)) or not np.all(np.isfinite(neg)):
        raise ValueError("five finite signed training pairs required")
    for name,y,powers in (("raw_positive_even_two_term",pos,(4,6)),("evenized_two_term",(pos+neg)/2,(4,6)),("odd_diagnostic",(pos-neg)/2,(5,7))):
        design=np.column_stack([np.asarray(times)**p for p in powers])
        norms=np.linalg.norm(design,axis=0)
        scaled=design/norms
        coeff=np.linalg.lstsq(scaled,y,rcond=None)[0]/norms
        cond=float(np.linalg.cond(scaled))
        output[name]={"powers":list(powers),"coefficients":coeff.tolist(),"condition_number":cond,
            "training_residual":float(np.max(np.abs(design@coeff-y))),
            "status":"fit_ok" if quality and cond<=1e8 else "not_identifiable",
            "selection_active":name=="raw_positive_even_two_term"}
        if powers==(4,6):
            output[name].update(a4=float(coeff[0]),a6=float(coeff[1]))
    return output

def evaluate_fit(model,t):
    return float(sum(c*t**p for c,p in zip(model["coefficients"],model["powers"],strict=True)))
