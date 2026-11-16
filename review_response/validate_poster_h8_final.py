"""Check final selected optimum phases with a complete complex Schur basis."""
from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from poster_h8_accelerated import OUT,prepare
from run_poster_h8 import PointPool,point_key,load_point
from reproduce_poster_baseline import ALIASES,EPS,write_json
from trotterlib.config import BETA


def main():
    system=prepare(8)
    pool=PointPool(OUT/'runtime/H8_compact.pkl',[0,1,2,3,4,5,6,7],OUT/'runtime/points',1)
    def check(alias):
        payload=json.loads((OUT/'raw'/f'H8_{alias}.json').read_text())
        r=next(iter(payload['results']['H8'].values()))
        minimum=r['direct_diagonalization']['curve']['minimum'];t=minimum['time'];point=r['direct_diagonalization']['points'][minimum['index']]
        old=load_point(OUT/'runtime/points'/point_key(alias,t,point['eigensolver_method']))
        reference=old['vectors'][:,point['selected_schur_index']]
        data=list(pool.evaluate(alias,[t],method='schur'))[0][1]
        overlaps=abs(data['vectors'].conj().T@reference)**2;selected=int(np.argmax(overlaps))
        shift=float(np.angle(np.exp(-1j*system['energy']*t)*data['values'][selected])/t)
        previous=point['signed_direct_error_hartree'];shift+=round((previous-shift)*t/(2*np.pi))*2*np.pi/t
        difference=abs(shift-previous)
        cost=BETA*r['pauli_rotations_per_step']/(t*(EPS-abs(shift))) if abs(shift)<EPS else None
        cost_difference=abs(cost/minimum['value']-1) if cost is not None else None
        return dict(alias=alias,time=t,original_method=point['eigensolver_method'],already_full_schur=point['eigensolver_method']=='schur',
                    selected_reference_overlap=float(overlaps[selected]),shift_difference_hartree=difference,
                    schur_residual=float(data['residuals'][selected]),relative_cost_difference=cost_difference,
                    pass_=difference<=1e-11 and float(data['residuals'][selected])<=1e-10 and cost is not None and cost_difference<=1e-6)
    try:
        with ThreadPoolExecutor(max_workers=3) as outer:rows=list(outer.map(check,ALIASES))
    finally:pool.close()
    payload=dict(pass_=all(r['pass_'] for r in rows),results=rows,note='Joint-real target phases are cross-checked against full complex Schur. Points already solved by Schur reuse that complete solve and are labeled accordingly.')
    write_json(OUT/'final_schur_validation.json',payload)
    print(json.dumps(payload,indent=2),flush=True)
    assert payload['pass_']

if __name__=='__main__':main()
