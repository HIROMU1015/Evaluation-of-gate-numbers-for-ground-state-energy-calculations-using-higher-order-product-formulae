"""Check serial versus multi-GPU time points at identical physical times."""
import json
import time
import numpy as np
from poster_finite_time import ROOT, Sweep, reference_module
from reproduce_poster_baseline import ALIASES, analytic, isolated_molecule_files, write_json

out=ROOT/'artifacts/poster_finite_time_20261116'
refs=out/'references/4672f3f'
isolated_molecule_files()
sector=reference_module(refs/'review_response/hchain_direct_sector_v1_1.py','poster_parallel_sector')
gpu=reference_module(refs/'src/trotterlib/sector_pf_gpu.py','trotterlib.poster_parallel_gpu')
system=sector.prepare_sparse_sector_system_v1_1(4)
builders=[gpu.GpuSectorPFBuilder(system['group_spectra'],logical_device=d) for d in (0,1,2)]
results=[]
try:
 for alias in ALIASES:
    times=np.geomspace(.3,1.1,12)*analytic(4,alias)['time']
    begin=time.perf_counter();serial=Sweep(system,alias,builders[0]).calculate(times);serial_seconds=time.perf_counter()-begin
    begin=time.perf_counter();parallel=Sweep(system,alias,builders).calculate(times);parallel_seconds=time.perf_counter()-begin
    difference=max(abs(a['signed_direct_error_hartree']-b['signed_direct_error_hartree']) for a,b in zip(serial,parallel))
    overlap_difference=max(abs(a['selected_ground_state_overlap_probability']-b['selected_ground_state_overlap_probability']) for a,b in zip(serial,parallel))
    results.append(dict(alias=alias,points=len(times),serial_seconds=serial_seconds,parallel_seconds=parallel_seconds,
        maximum_signed_shift_difference_hartree=difference,maximum_ground_overlap_difference=overlap_difference,pass_=difference<=1e-11 and overlap_difference<=1e-8))
finally:
 for b in builders:
    b.cp.cuda.Device(b.logical_device).use();b.close()
payload=dict(logical_devices=[0,1,2],physical_devices=[5,6,7],blas_threads_per_worker=1,results=results,pass_=all(r['pass_'] for r in results),note='Small H4 matrices validate numerical equality; timings are not a forecast of H7 throughput on shared busy GPUs.')
write_json(out/'parallel_validation.json',payload)
print(json.dumps(payload,indent=2))
assert payload['pass_']
