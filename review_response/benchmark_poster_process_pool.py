"""Numerical equivalence and warm throughput of process-owned GPU points."""
import time
import numpy as np
from poster_finite_time import ROOT, Sweep, reference_module
from poster_process_pool import ProcessPointPool
from reproduce_poster_baseline import isolated_molecule_files, analytic, write_json


def main():
    out=ROOT/'artifacts/poster_finite_time_20261116'
    refs=out/'references/4672f3f'
    isolated_molecule_files()
    sector=reference_module(refs/'review_response/hchain_direct_sector_v1_1.py','poster_process_sector')
    gpu=reference_module(refs/'src/trotterlib/sector_pf_gpu.py','trotterlib.poster_process_parent_gpu')
    system=sector.prepare_sparse_sector_system_v1_1(6)
    parent=gpu.GpuSectorPFBuilder(system['group_spectra'],logical_device=0)
    pool=ProcessPointPool(system,refs/'src/trotterlib/sector_pf_gpu.py',[0,1,2])
    results=[]
    try:
        began=time.perf_counter()
        list(pool.evaluate('w8',np.array([.4,.5,.6])*analytic(6,'w8')['time']))
        startup=time.perf_counter()-began
        for alias in ('w8','w1016','wmy4'):
            times=np.geomspace(.35,.85,9)*analytic(6,alias)['time']
            began=time.perf_counter();serial=Sweep(system,alias,parent).calculate(times);serial_seconds=time.perf_counter()-began
            began=time.perf_counter();parallel=Sweep(system,alias,pool).calculate(times);parallel_seconds=time.perf_counter()-began
            diff=max(abs(a['signed_direct_error_hartree']-b['signed_direct_error_hartree']) for a,b in zip(serial,parallel))
            overlap=max(abs(a['selected_ground_state_overlap_probability']-b['selected_ground_state_overlap_probability']) for a,b in zip(serial,parallel))
            results.append(dict(alias=alias,point_count=len(times),serial_seconds=serial_seconds,process_parallel_seconds=parallel_seconds,
                speedup=serial_seconds/parallel_seconds,maximum_signed_shift_difference_hartree=diff,maximum_ground_overlap_difference=overlap,
                pass_=diff<1e-11 and overlap<1e-8))
    finally:
        pool.close();parent.cp.cuda.Device(0).use();parent.close()
    payload=dict(system='H6',dimension=400,physical_devices=[5,6,7],logical_devices=[0,1,2],blas_threads_per_process=1,
                 worker_startup_plus_three_points_seconds=startup,results=results,pass_=all(r['pass_'] for r in results),
                 source='spawn workers, complete spectra resident per GPU; time-order branch tracking in parent after collection')
    write_json(out/'process_parallel_validation.json',payload)
    print(payload,flush=True)
    assert payload['pass_']

if __name__=='__main__':main()
