"""Only tiny synthetic algebra is exercised by FS-C0 tests; no archive loader."""
import numpy as np

def fit_functional(times, target):
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or len(times) < 3 or not np.all(np.isfinite(times)) or np.any(times <= 0):
        raise ValueError("invalid synthetic training times")
    if len(set(times)) != len(times):
        raise ValueError("duplicate synthetic times")
    X = np.column_stack((times**4, times**6))
    scale = np.linalg.norm(X, axis=0)
    scaled = X/scale
    ell = (np.array([target**4, target**6])/scale) @ np.linalg.pinv(scaled)
    return ell, X, scale

def response_representations(H, psi, Z, A):
    # This is the frozen full residual least-squares expression, not L_m.
    E = np.vdot(psi, H@psi).real
    Q = np.eye(len(psi))-np.outer(psi, psi.conj())
    r = (H-E*np.eye(len(psi)))@psi
    B = Q@(H-E*np.eye(len(psi)))@Q@Z
    U, singular, Vh = np.linalg.svd(B, full_matrices=False)
    cutoff = 64*np.finfo(float).eps*max(B.shape)*singular[0]
    keep = singular > cutoff
    inverse = (Vh.conj().T[:,keep]/singular[keep])@U[:,keep].conj().T
    z = Z@inverse@Q@A@psi
    w = Q@inverse.conj().T@Z.conj().T@r
    bare = np.vdot(psi,A@psi).real
    original = bare-2*np.vdot(r,z).real
    fixed = bare-2*np.vdot(w,A@psi).real
    rho = np.outer(psi,psi.conj())-np.outer(psi,w.conj())-np.outer(w,psi.conj())
    return original, fixed, np.trace(rho@A).real, rho, w
