"""FS-C0.5 identity gates and synthetic-only native adapter; no C1 runner."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time
from dataclasses import dataclass, field
from typing import Any, Sequence, Iterable

import numpy as np
import scipy
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import expm_multiply

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def native_namespace(root=ROOT):
    """Compile only pinned pure/action functions; never import a science driver.

    This avoids module bootstrap, molecule preparation, ground solves and all
    truth routines. Original function bodies are used without rewriting.
    """
    pins = json.loads((HERE / 'native_source_pins.json').read_text())
    ns = dict(np=np, csr_matrix=csr_matrix, coo_matrix=coo_matrix,
              dataclass=dataclass, time=time, Any=Any, Sequence=Sequence, Iterable=Iterable,
              __name__='fs_c05_native_fixture')
    for record in pins['sources']:
        raw = (Path(root) / record['path']).read_bytes()
        if digest(raw) != record['sha256']:
            raise ValueError('native source hash mismatch')
        tree = ast.parse(raw)
        selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                    and n.name in record['definitions']]
        if {n.name for n in selected} != set(record['definitions']):
            raise ValueError('missing pinned definition')
        exec(compile(ast.Module(body=selected, type_ignores=[]), record['path'], 'exec', dont_inherit=True), ns)
    return ns

def baseline_gate(protocol):
    if protocol['historical_baseline_model'] != 'echo_imag_3point':
        raise ValueError('historical model replacement')
    if protocol['historical_training_relative'] != [0.1, 0.2, 0.3]:
        raise ValueError('historical three points required')
    if protocol['sentinel_in_fit'] is not False or protocol['relative_0_4_role'] != 'none':
        raise ValueError('sentinel/0.4 entered fit')
    for s in protocol['systems']:
        times = s['historical_training_absolute']
        if len(times) != 3 or s['M10_training_absolute'] != times:
            raise ValueError('M10 coordinates changed')
        if [float(t).hex() for t in times] != s['historical_training_time_hex']:
            raise ValueError('absolute coordinate bytes changed')
    return True

def check_pickle(path, expected_sha, decoder=None, *, regenerated=False):
    """Hash the exact bytes before any decode; decoder is identity-only."""
    if regenerated:
        raise ValueError('regenerated source forbidden')
    path = Path(path)
    if not path.is_file():
        return {'status': 'NO_GO_SOURCE_MISSING', 'decoded': False, 'sha256': None}
    raw = path.read_bytes()
    actual = digest(raw)
    if actual != expected_sha:
        return {'status': 'NO_GO_SOURCE_IDENTITY', 'decoded': False, 'sha256': actual}
    # Real recovery currently unavailable; no unpickler is provided by this package.
    if decoder is None:
        return {'status': 'WHOLE_PICKLE_MATCH_ONLY', 'decoded': False, 'sha256': actual}
    return {'status': 'IDENTITY_ONLY_DECODED', 'decoded': True,
            'sha256': actual, 'identity_members': decoder(raw)}

def validate_member_identities(actual, expected):
    """All digests must already be fixed by the matching source export.

    No sorting, phase alignment, normalization, regeneration or ground data.
    List equality checks both group and component order.
    """
    keys = ('hamiltonian_sha256', 'cisd_sha256', 'restricted_basis_sha256',
            'ordered_group_sha256', 'ordered_component_sha256',
            'sector_metadata_sha256', 'step_order_sha256')
    for key in keys:
        if expected.get(key) is None or actual.get(key) != expected[key]:
            raise ValueError('source identity mismatch: ' + key)
    if actual.get('source_kind') != 'matching_historical_pickle':
        raise ValueError('source is not historical pickle')
    return True

def open_c1_truth(reader):
    raise PermissionError('FS-C0.5 truth barrier: FS-C1 truth access forbidden')

def reproduction_tolerance(components):
    allowed = {'historical_backend_bound', 'cold_variability_bound', 'floating_backend_bound'}
    if set(components) != allowed:
        raise ValueError('tolerance input is not authorized numerical evidence')
    if any(x is None for x in components.values()):
        return {'status': 'M00_REPRODUCTION_TOLERANCE_UNCLOSED', 'tolerance_hartree': None}
    if any(not math.isfinite(x) or x < 0 for x in components.values()):
        raise ValueError('invalid numerical bound')
    return {'status': 'PREREGISTERED_BOUND', 'tolerance_hartree': max(components.values())}

@dataclass
class Ledger:
    logical_exact_H_echo: int = 0
    explicit_Ritz_H_matvec: int = 0
    PF_forward: int = 0
    group_application: int = 0
    group_gate_materialization: int = 0
    small_Ritz_solve: int = 0
    scalar_fit: int = 0
    wall_seconds: float = 0.0
    expm_internal: dict = field(default_factory=lambda: dict(
        matvec=None, matmat=None, rmatvec=None, rmatmat=None, norm_estimation=None))

    def snapshot(self):
        return {'scope': 'synthetic_fixture_only', 'logical_actions': {
            k: getattr(self, k) for k in ('logical_exact_H_echo', 'explicit_Ritz_H_matvec',
            'PF_forward', 'group_application', 'group_gate_materialization',
            'small_Ritz_solve', 'scalar_fit')},
            'classical': {'wall_seconds': self.wall_seconds,
                          'peak_RSS_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024},
            'expm_internal': self.expm_internal.copy(), 'internal_count_status': 'unknown',
            'predicted_QPE': {'unit': 'PF rotations', 'value': None},
            'software_versions': {'numpy': np.__version__, 'scipy': scipy.__version__},
            'threads': {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')}}

def action_plan(retained_rank, systems=2, passes=2):
    if type(retained_rank) is not int or not 0 <= retained_rank <= 8:
        raise ValueError('rank outside fixed prefix')
    n = systems * passes
    return {'planned_only': True, 'explicit_Ritz_H_matvec': n * (1 + retained_rank),
            'small_Ritz_solve': n, 'PF_forward': n * 2 * 4,
            'logical_exact_H_echo': n * 2 * 4,
            'M00_validation_fits': n, 'M10_initial_operational_fits': systems,
            'M10_cold_validation_fits': systems * (passes - 1),
            'total_fit_calls': n * 2, 'PF_adjoint': 0}

class NativeFixtureAdapter:
    """Original CPU native backend, strictly restricted to tiny test fixtures.

    Production closure/execution cannot be authorized through a boolean switch.
    A separately reviewed C1 runner would be required after source recovery.
    """
    def __init__(self, H, spectra, sequence, ledger=None, *, scope='synthetic'):
        if scope != 'synthetic' or H.shape[0] > 8 or H.shape[0] < 1 or H.shape[0] != H.shape[1]:
            raise PermissionError('production actions forbidden in FS-C0.5')
        self.ns = native_namespace()
        frozen = json.loads((HERE / 'baseline_contract.json').read_text())['current_m3_sequence']
        if list(sequence) != frozen:
            raise ValueError('current_m3 coefficients changed')
        if not spectra or any(s.dimension != H.shape[0] for s in spectra):
            raise ValueError('incompatible group sector')
        self.H = H.copy().astype(np.complex128)
        self.spectra = spectra
        self.sequence = tuple(sequence)
        self.ledger = ledger or Ledger()

    def state(self, value):
        state = np.asarray(value, dtype=np.complex128)
        if state.shape != (self.H.shape[0],) or not np.isfinite(state).all():
            raise ValueError('compatible finite vector required')
        if abs(np.linalg.norm(state) - 1) > 1e-12:
            raise ValueError('normalized fixture required; no silent normalization')
        return state

    def forward(self, state, t):
        state = self.state(state)
        if not math.isfinite(t) or t <= 0:
            raise ValueError('positive fixed fixture time required')
        out, timings = self.ns['_apply_pf_cpu'](
            {'component_spectra': self.spectra}, self.sequence, t, state)
        steps = list(self.ns['iter_s2_sequence_steps'](len(self.spectra), self.sequence))
        self.ledger.PF_forward += 1
        self.ledger.group_application += len(steps)
        self.ledger.group_gate_materialization += len(set(steps))
        self.ledger.wall_seconds += timings['total']
        return out

    def proxy(self, state, t):
        state = self.state(state)
        evolved = self.forward(state, t)
        started = time.perf_counter()
        reference = expm_multiply(1j * t * self.H, state)
        echo = np.vdot(reference, evolved)
        self.ledger.logical_exact_H_echo += 1
        self.ledger.wall_seconds += time.perf_counter() - started
        return {'proxy': float(echo.imag / t), 'pf_norm': float(np.linalg.norm(evolved)),
                'echo_real': float(echo.real), 'echo_imaginary': float(echo.imag)}

def historical_scalar_fit(times, values, t_ref, t0, *, ledger=None):
    if len(times) != 3 or len(values) != 3:
        raise ValueError('exactly three saved training scalars required')
    points = [{'time': t, 'echo_imag_hartree': v} for t,v in zip(times,values)]
    result = native_namespace()['_fit_proxy'](points, 'echo_imag_hartree', 3, t_ref, 'echo_imag_3point')
    a4, a6 = result['coefficient_values']
    result['signed_prediction_at_t0'] = a4 * t0**4 + a6 * t0**6
    if ledger is not None:
        ledger.scalar_fit += 1
    return result

def fixture():
    """Analytically specified 2x2 spectra; no eigensolve or source construction."""
    ns = native_namespace()
    B, S = ns['ComponentBatch'], ns['ComponentSpectrum']
    # H = Z + X, +i sign inherited from component_exponential.
    zvec = np.eye(2, dtype=np.complex128)[None, :, :]
    xvec = np.array([[1,1],[-1,1]],dtype=np.complex128)[None,:,:] / np.sqrt(2)
    indices = np.array([[0,1]], dtype=np.int64)
    z = S(2, (B(indices.copy(), np.array([[1.,-1.]]), zvec),), 2, 1, 2, 4)
    x = S(2, (B(indices.copy(), np.array([[-1.,1.]]), xvec),), 2, 1, 2, 4)
    H = csr_matrix(np.array([[1.,1.],[1.,-1.]],dtype=np.complex128))
    seq = json.loads((HERE / 'baseline_contract.json').read_text())['current_m3_sequence']
    state = np.array([np.sqrt(0.7), 1j*np.sqrt(0.3)], dtype=np.complex128)
    return NativeFixtureAdapter(H, [z,x], seq), state
