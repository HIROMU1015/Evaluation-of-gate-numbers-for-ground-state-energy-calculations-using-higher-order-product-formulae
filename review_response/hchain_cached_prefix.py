"""Truth-free cached-prefix views; no acquisition or branch policy selection."""

import numpy as np

from pf_spectral_recoverability_d2 import ArnoldiChain

PREFIXES = (1, 2, 4, 8, 16, 32)


def cached_prefix(chain, dimension):
    """Return metrics restricted to this prefix, or None after breakdown.

    This helper deliberately does not choose continuation vectors, run prefix
    eigensolvers or promote a lower rank to an accepted missing primary rank.
    """
    if dimension not in PREFIXES:
        raise ValueError("only predeclared prefixes 1,2,4,8,16,32 are allowed")
    if not (chain.basis.shape == chain.u_basis.shape == chain.h_basis.shape):
        raise ValueError("cached action shapes mismatch")
    if dimension > chain.dimension:
        return None
    q, uq, hq = (values[:, :dimension] for values in (chain.basis, chain.u_basis, chain.h_basis))
    return ArnoldiChain(
        basis=q, u_basis=uq, h_basis=hq,
        relative_remainders=chain.relative_remainders[:dimension - 1],
        breakdown=chain.breakdown and dimension == chain.dimension,
        orthogonality_residual_frobenius=float(np.linalg.norm(q.conj().T @ q - np.eye(dimension), "fro")),
        maximum_pf_norm_residual=float(np.max(np.abs(np.linalg.norm(uq, axis=0) - 1.0))),
    )
