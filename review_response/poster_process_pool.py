"""GPU point workers use spawn so that each process owns a CUDA context."""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context, current_process
from pathlib import Path

_worker_system = None
_worker_builder = None


def _initialize(system, gpu_source, devices):
    from poster_finite_time import reference_module
    global _worker_system, _worker_builder
    # Spawn creates fresh interpreters, before any CUDA context in the worker.
    device = devices[(current_process()._identity[0] - 1) % len(devices)]
    gpu = reference_module(Path(gpu_source), 'trotterlib.poster_process_gpu')
    _worker_system = system
    _worker_builder = gpu.GpuSectorPFBuilder(system['group_spectra'], logical_device=device)


def _point(job):
    from poster_finite_time import Sweep
    alias, t = job
    sweep = Sweep(_worker_system, alias, _worker_builder)
    return sweep._calculate_point(t, _worker_builder)


class ProcessPointPool:
    def __init__(self, system, gpu_source, devices):
        self.executor = ProcessPoolExecutor(
            max_workers=len(devices), mp_context=get_context('spawn'),
            initializer=_initialize, initargs=(system, str(gpu_source), tuple(devices)),
        )

    def evaluate(self, alias, times):
        return self.executor.map(_point, [(alias, t) for t in times], chunksize=1)

    def close(self):
        self.executor.shutdown(wait=True)
