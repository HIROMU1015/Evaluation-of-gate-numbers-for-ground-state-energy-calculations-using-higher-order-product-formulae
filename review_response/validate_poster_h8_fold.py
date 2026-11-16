"""Compare full unitaries from folded and explicit symmetric compositions."""
import time
import numpy as np
from poster_h8_accelerated import OUT,prepare,CompactGpuBuilder
from reproduce_poster_baseline import ALIASES,analytic,write_json
from trotterlib.product_formula import _get_s2_sequence


def main():
    system=prepare(8)
    folded=CompactGpuBuilder(system,fold=True)
    explicit=CompactGpuBuilder(system,fold=False)
    results=[]
    try:
        for alias in ALIASES:
            model=analytic(8,alias);seq=_get_s2_sequence(model['label']);t=model['time']
            start=time.perf_counter();u=folded.build(seq,t);v=explicit.build(seq,t)
            difference=float(np.linalg.norm(u-v)/np.linalg.norm(v))
            result=dict(alias=alias,time=t,relative_unitary_frobenius_difference=difference,
                        selected_basis_dimension=len(u),seconds=time.perf_counter()-start,pass_=difference<1e-10)
            results.append(result);print(result,flush=True)
    finally:folded.close();explicit.close()
    payload=dict(pass_=all(x['pass_'] for x in results),results=results,
                 meaning='Complete 2468 by 2468 H8 unitary matrices agree; neither branch overlaps nor error-model fits are substituted for the matrix comparison.')
    write_json(OUT/'fold_equivalence.json',payload)
    assert payload['pass_']

if __name__=='__main__':main()
