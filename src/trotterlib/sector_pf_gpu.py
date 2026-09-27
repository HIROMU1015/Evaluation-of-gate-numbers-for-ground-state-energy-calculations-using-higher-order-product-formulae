"""Exact dense conserved-sector PF construction on one CUDA device.

The implementation mirrors :mod:`trotterlib.sector_pf`: each grouped
Hamiltonian is represented by its complete eigensystem, repeated S2 blocks
are cached algebraically, and no truncation or reduced-rank approximation is
used.  Only the unitary construction is performed on the GPU; callers may
transfer the resulting complex128 matrix to the host for a CPU Schur factor.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import numpy as np

from .pf_decomposition import iter_s2_sequence_steps


class GpuSectorPFBuilder:
    """Keep complete group spectra resident and build exact dense PF matrices."""

    def __init__(
        self,
        spectra: Sequence[tuple[np.ndarray, np.ndarray]],
        *,
        logical_device: int = 0,
    ) -> None:
        if not spectra:
            raise ValueError("spectra must contain at least one Hamiltonian group")
        import cupy as cp

        self.cp = cp
        self.logical_device = int(logical_device)
        cp.cuda.Device(self.logical_device).use()
        self.dimension = int(np.asarray(spectra[0][0]).shape[0])
        self.group_count = len(spectra)
        self.spectra: list[tuple[Any, Any]] = []
        for values, vectors in spectra:
            host_values = np.asarray(values)
            host_vectors = np.asarray(vectors)
            if host_values.dtype != np.float64:
                host_values = host_values.astype(np.float64, copy=False)
            if host_vectors.dtype != np.complex128:
                host_vectors = host_vectors.astype(np.complex128, copy=False)
            if host_values.shape != (self.dimension,):
                raise ValueError("group eigenvalue shape mismatch")
            if host_vectors.shape != (self.dimension, self.dimension):
                raise ValueError("group eigenvector shape mismatch")
            self.spectra.append((cp.asarray(host_values), cp.asarray(host_vectors)))
        cp.cuda.Stream.null.synchronize()
        self.metrics: list[dict[str, Any]] = []

    def _left_apply(
        self, matrix: Any, spectrum: tuple[Any, Any], scaled_time: float
    ) -> Any:
        cp = self.cp
        values, vectors = spectrum
        projected = vectors.conj().T @ matrix
        projected *= cp.exp(1j * float(scaled_time) * values)[:, None]
        return vectors @ projected

    def _s2_block(self, block_weight: float, evolution_time: float) -> Any:
        cp = self.cp
        block = cp.eye(self.dimension, dtype=cp.complex128)
        for group_index, weight in iter_s2_sequence_steps(
            self.group_count, [float(block_weight)]
        ):
            block = self._left_apply(
                block,
                self.spectra[group_index],
                float(evolution_time) * float(weight),
            )
        return block

    def build(
        self, s2_sequence: Sequence[float], evolution_time: float
    ) -> np.ndarray:
        """Return the exact complex128 PF unitary on the host."""
        cp = self.cp
        started = time.perf_counter()
        pool = cp.get_default_memory_pool()
        pool.free_all_blocks()
        free_before, total_memory = cp.cuda.runtime.memGetInfo()
        blocks: dict[float, Any] = {}
        block_started = time.perf_counter()
        for raw_weight in s2_sequence:
            weight = float(raw_weight)
            if weight not in blocks:
                blocks[weight] = self._s2_block(weight, evolution_time)
        cp.cuda.Stream.null.synchronize()
        block_seconds = time.perf_counter() - block_started

        compose_started = time.perf_counter()
        unitary = cp.eye(self.dimension, dtype=cp.complex128)
        for raw_weight in s2_sequence:
            unitary = blocks[float(raw_weight)] @ unitary
        cp.cuda.Stream.null.synchronize()
        compose_seconds = time.perf_counter() - compose_started

        transfer_started = time.perf_counter()
        host = cp.asnumpy(unitary)
        cp.cuda.Stream.null.synchronize()
        transfer_seconds = time.perf_counter() - transfer_started
        free_after, _ = cp.cuda.runtime.memGetInfo()
        pool_reserved = int(pool.total_bytes())
        metric = {
            "backend": "gpu_exact_dense_sector_unitary_cpu_schur",
            "dtype": "complex128",
            "logical_device": self.logical_device,
            "dimension": self.dimension,
            "group_count": self.group_count,
            "s2_stage_count": len(s2_sequence),
            "unique_s2_stage_count": len(set(map(float, s2_sequence))),
            "block_build_seconds": float(block_seconds),
            "stage_compose_seconds": float(compose_seconds),
            "host_transfer_seconds": float(transfer_seconds),
            "build_seconds": float(time.perf_counter() - started),
            "device_total_bytes": int(total_memory),
            "device_free_before_bytes": int(free_before),
            "device_free_after_bytes": int(free_after),
            "cupy_pool_reserved_bytes": pool_reserved,
        }
        self.metrics.append(metric)
        del unitary, blocks
        pool.free_all_blocks()
        if host.dtype != np.complex128:
            raise RuntimeError(f"GPU unitary dtype changed to {host.dtype}")
        return host

    def clear_metrics(self) -> None:
        self.metrics.clear()

    def identity(self) -> dict[str, Any]:
        cp = self.cp
        properties = cp.cuda.runtime.getDeviceProperties(self.logical_device)
        name = properties.get("name", "unknown")
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="replace")
        return {
            "backend": "gpu_exact_dense_sector_unitary_cpu_schur",
            "dtype": "complex128",
            "cupy_version": cp.__version__,
            "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
            "logical_device": self.logical_device,
            "device_name": str(name),
            "dimension": self.dimension,
            "group_count": self.group_count,
        }

    def close(self) -> None:
        cp = self.cp
        self.spectra.clear()
        cp.get_default_memory_pool().free_all_blocks()
        cp.cuda.Stream.null.synchronize()

