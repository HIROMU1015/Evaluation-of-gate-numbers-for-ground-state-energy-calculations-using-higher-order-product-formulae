from dataclasses import dataclass
from functools import reduce
from typing import Any, List, Tuple

import numpy as np

import pyscf
from pyscf import fci, gto, scf
from pyscf.fci import cistring

from openfermion import InteractionOperator
from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import jordan_wigner, get_fermion_operator
from openfermion.chem.molecular_data import spinorb_from_spatial

from .Almost_optimal_grouping import Almost_optimal_grouper

from .chemistry_hamiltonian import geo

DEFAULT_BASIS = "sto-3g"  # PySCF 基底関数
FCI_RESIDUAL_TOLERANCE = 1e-10
FCI_DAVIDSON_RETRY_LINDEP = 1e-20
MAX_FULL_PSPACE_DIMENSION = 1024


@dataclass(frozen=True)
class GroupedFCIResult:
    """Grouped Hamiltonian and a checked PySCF FCI ground state."""

    grouped_jw_list: List[List[QubitOperator]]
    n_qubits: int
    energy: float
    state_vector: np.ndarray
    diagnostics: dict[str, Any]


def _fci_residual_norm(
    solver: Any,
    one_body_integrals: np.ndarray,
    eri_mo: np.ndarray,
    ci_matrix: np.ndarray,
    electronic_energy: float,
) -> float:
    """Return ||H_FCI c - E_elec c|| without a sparse eigensolve."""
    h2e = solver.absorb_h1e(
        one_body_integrals,
        eri_mo,
        solver.norb,
        solver.nelec,
        0.5,
    )
    h_ci = solver.contract_2e(h2e, ci_matrix, solver.norb, solver.nelec)
    return float(np.linalg.norm(h_ci - electronic_energy * ci_matrix))


def _solve_checked_fci(
    mol: Any,
    mf: Any,
    one_body_integrals: np.ndarray,
    eri_mo: np.ndarray,
) -> tuple[Any, float, np.ndarray, dict[str, Any]]:
    """Solve FCI with a bounded exact-PySCF path and verify its residual.

    PySCF's default pspace threshold (400 determinants) sends H7's 735
    determinant sector through Davidson convergence.  On this server that
    solver reports convergence even though the state residual is about 2.5e-6.
    For small sectors we instead ask PySCF to diagonalize the complete FCI
    pspace with LAPACK.  The explicit dimension and memory guard prevents this
    small-system remedy from silently becoming a large dense calculation.
    """
    if not bool(mf.converged):
        raise RuntimeError("PySCF RHF did not converge")

    n_orbitals = int(mf.mo_coeff.shape[1])
    n_alpha, n_beta = mol.nelec
    ci_dimension = int(
        cistring.num_strings(n_orbitals, n_alpha)
        * cistring.num_strings(n_orbitals, n_beta)
    )
    full_pspace = ci_dimension <= MAX_FULL_PSPACE_DIMENSION

    solver = fci.FCI(mol, mf.mo_coeff)
    solver.conv_tol = 1e-12
    solver.conv_tol_residual = FCI_RESIDUAL_TOLERANCE
    solver.max_cycle = 400
    solver.max_space = 40
    if full_pspace:
        solver.pspace_size = ci_dimension
        solver.davidson_only = False
        method = "pyscf_full_pspace_lapack_eigh"
    else:
        solver.pspace_size = min(int(solver.pspace_size), ci_dimension)
        solver.davidson_only = True
        method = "pyscf_davidson"

    energy, ci_matrix = solver.kernel()
    electronic_energy = float(energy - mf.energy_nuc())
    residual = _fci_residual_norm(
        solver,
        one_body_integrals,
        eri_mo,
        ci_matrix,
        electronic_energy,
    )
    attempts = [
        {
            "attempt": 1,
            "initial_guess": "pyscf_default",
            "lindep": float(solver.lindep),
            "fci_converged": bool(solver.converged),
            "fci_residual_norm": residual,
            "energy_hartree": float(energy),
        }
    ]

    # PySCF's Davidson solver can reach an energy-stationary vector and then
    # stop on a linearly dependent correction before the requested residual
    # tolerance is met.  Keep PySCF as the eigensolver and restart from that CI
    # vector with a tighter linear-dependence threshold.  H9--H11 need this
    # continuation on the GPU server; small full-pspace solves do not.
    if not full_pspace and (
        not bool(solver.converged) or residual > FCI_RESIDUAL_TOLERANCE
    ):
        previous_energy = float(energy)
        solver.lindep = min(
            float(solver.lindep),
            FCI_DAVIDSON_RETRY_LINDEP,
        )
        energy, ci_matrix = solver.kernel(ci0=np.asarray(ci_matrix))
        electronic_energy = float(energy - mf.energy_nuc())
        residual = _fci_residual_norm(
            solver,
            one_body_integrals,
            eri_mo,
            ci_matrix,
            electronic_energy,
        )
        attempts.append(
            {
                "attempt": 2,
                "initial_guess": "previous_ci_vector",
                "lindep": float(solver.lindep),
                "fci_converged": bool(solver.converged),
                "fci_residual_norm": residual,
                "energy_hartree": float(energy),
                "energy_change_hartree": float(energy) - previous_energy,
            }
        )
    diagnostics = {
        "source": "PySCF FCI",
        "method": method,
        "scf_converged": bool(mf.converged),
        "fci_converged": bool(solver.converged),
        "fci_residual_norm": residual,
        "fci_residual_tolerance": FCI_RESIDUAL_TOLERANCE,
        "n_orbitals": int(solver.norb),
        "n_alpha": int(n_alpha),
        "n_beta": int(n_beta),
        "ci_dimension": ci_dimension,
        "full_pspace_dimension_limit": MAX_FULL_PSPACE_DIMENSION,
        "full_pspace_dense_matrix_bytes": (
            int(ci_dimension * ci_dimension * np.dtype(float).itemsize)
            if full_pspace
            else None
        ),
        "davidson_retry_performed": len(attempts) > 1,
        "davidson_retry_lindep": FCI_DAVIDSON_RETRY_LINDEP,
        "davidson_attempts": attempts,
        "used_scipy_eigsh": False,
    }
    if not bool(solver.converged):
        raise RuntimeError(
            "PySCF FCI did not converge: "
            f"method={method}, dimension={ci_dimension}, residual={residual}"
        )
    if residual > FCI_RESIDUAL_TOLERANCE:
        raise RuntimeError(
            "PySCF FCI residual exceeds tolerance: "
            f"{residual} > {FCI_RESIDUAL_TOLERANCE} "
            f"(method={method}, dimension={ci_dimension})"
        )
    return solver, float(energy), np.asarray(ci_matrix), diagnostics


def make_checked_fci_result_from_pyscf_solver_grouper(
    molecule_type: int,
) -> GroupedFCIResult:
    """Build grouped JW terms and a residual-checked PySCF FCI state."""
    # PySCF FCI から |ψ₀⟩ を構築し、グルーピング済み JW 演算子群とともに返す。
    # 分子情報を構築して SCF を実行
    geometry, multiplicity, molcharge = geo(molecule_type)
    mol = gto.Mole()
    mol.atom = geometry
    mol.basis = DEFAULT_BASIS
    mol.spin = multiplicity - 1
    mol.charge = molcharge
    mol.symmetry = False
    mol.build()
    mf = scf.RHF(mol)
    mf.kernel()
    # 積分（1体・2体）を構築
    constant = mf.energy_nuc()
    mo_coeff = mf.mo_coeff
    h_core = mf.get_hcore()
    one_body_integrals = reduce(np.dot, (mo_coeff.T, h_core, mo_coeff))

    eri_mo = pyscf.ao2mo.kernel(mf.mol, mo_coeff)
    eri_mo = pyscf.ao2mo.restore(1, eri_mo, mo_coeff.shape[0])
    two_body_integrals = np.asarray(eri_mo.transpose(0, 2, 3, 1), order="C")

    # 近似グルーピングで JW 演算子を作成
    almost_optimal_grouper = Almost_optimal_grouper(
        constant,
        one_body_integrals,
        two_body_integrals,
        fermion_qubit_mapping=jordan_wigner,
        validation=True,
    )
    grouping_term_list = almost_optimal_grouper.group_term_list
    # 定数項をグループ先頭へ（OpenFermion FermionOperator の空文字は恒等項）
    grouping_term_list[0].insert(
        0,
        FermionOperator("", almost_optimal_grouper._const_fermion),
    )
    grouped_jw_list: List[List[QubitOperator]] = [
        jordan_wigner(sum(group_term)) for group_term in grouping_term_list
    ]

    # FCI を解いて基底状態を構築
    fci_solver, energy, ci_matrix, diagnostics = _solve_checked_fci(
        mol,
        mf,
        one_body_integrals,
        eri_mo,
    )
    n_qubits = fci_solver.norb * 2
    n_orbitals = fci_solver.norb
    nelec_alpha, nelec_beta = fci_solver.nelec
    fci_vector = np.zeros(2**n_qubits, dtype=np.complex128)

    ci_strings_alpha = cistring.make_strings(range(n_orbitals), nelec_alpha)
    ci_strings_beta = cistring.make_strings(range(n_orbitals), nelec_beta)

    # 注意: 右が q0 となる Qiskit のビット順に合わせるにはビット反転が必要だが、
    # 既存コードは **反転しない** 前提で構築しているため、その挙動を維持する。
    # CI 係数をビット列へ展開
    for i, a_str in enumerate(ci_strings_alpha):
        alpha_index = list(format(a_str, f"0{n_qubits // 2}b"))[::-1]
        for j, b_str in enumerate(ci_strings_beta):
            beta_index = list(format(b_str, f"0{n_qubits // 2}b"))[::-1]
            bitstring = "".join(alpha_index) + "".join(beta_index)
            sign = 1
            N = len(alpha_index)
            for k in range(N):
                if alpha_index[k] == "1":
                    for l in range(N):
                        if beta_index[l] == "1":
                            sign *= -1
            index = int(bitstring, 2)
            fci_vector[index] = sign * ci_matrix[i][j]

    state_vec = fci_vector.reshape(-1, 1)
    return GroupedFCIResult(
        grouped_jw_list=grouped_jw_list,
        n_qubits=n_qubits,
        energy=energy,
        state_vector=state_vec,
        diagnostics=diagnostics,
    )


def make_fci_vector_from_pyscf_solver_grouper(
    molecule_type: int,
) -> Tuple[List[List[QubitOperator]], int, float, np.ndarray]:
    """Compatibility wrapper returning the historical four-value tuple."""
    result = make_checked_fci_result_from_pyscf_solver_grouper(molecule_type)
    return (
        result.grouped_jw_list,
        result.n_qubits,
        result.energy,
        result.state_vector,
    )


def make_fci_vector_from_pyscf_solver(
    molecule_type: int,
) -> Tuple[QubitOperator, int, float, np.ndarray, np.ndarray]:
    """PySCFからFCIベクトルとJWハミルトニアンを生成（元コードと同一の並びと位相）。"""
    # --- Geometry / SCF ---
    # 分子情報を構築して SCF を実行
    geometry, multiplicity, molcharge = geo(molecule_type)
    mol = gto.Mole()
    mol.atom = geometry
    mol.basis = "sto-3g"
    mol.spin = multiplicity - 1
    mol.charge = molcharge
    mol.symmetry = False
    mol.build()
    mf = scf.RHF(mol)
    mf.kernel()

    # --- Molecular integrals ---
    # 積分（1体・2体）を構築
    constant = mf.energy_nuc()
    mo_coeff = mf.mo_coeff
    h_core = mf.get_hcore()
    one_body = reduce(np.dot, (mo_coeff.T, h_core, mo_coeff))
    eri_mo = pyscf.ao2mo.kernel(mf.mol, mo_coeff)
    eri_mo = pyscf.ao2mo.restore(1, eri_mo, mo_coeff.shape[0])
    two_body = np.asarray(eri_mo.transpose(0, 2, 3, 1), order="C")

    # spin-orbital Hamiltonian → Fermion → JW
    # フェルミオン演算子を JW に変換
    h1s, h2s = spinorb_from_spatial(one_body, two_body * 0.5)
    ham_fermion = get_fermion_operator(InteractionOperator(constant, h1s, h2s))
    jw_hamiltonian = jordan_wigner(ham_fermion)

    # --- FCI solve ---
    # FCI を解いて基底状態を構築
    fci_solver, energy, ci_matrix, _ = _solve_checked_fci(
        mol,
        mf,
        one_body,
        eri_mo,
    )
    num_orbitals = fci_solver.norb
    n_qubits = num_orbitals * 2
    nelec_alpha, nelec_beta = fci_solver.nelec

    # --- CI state on qubits: interleave [beta_k, alpha_k] for k=0.. ---
    state_vector = np.zeros(2 ** n_qubits, dtype=np.complex128)
    ci_strings_alpha = cistring.make_strings(range(num_orbitals), nelec_alpha)
    ci_strings_beta = cistring.make_strings(range(num_orbitals), nelec_beta)

    # CI 係数をビット列へ展開
    for i, a_str in enumerate(ci_strings_alpha):
        a_bits = format(a_str, f"0{n_qubits // 2}b")[::-1]  # LSBが軌道0
        for j, b_str in enumerate(ci_strings_beta):
            b_bits = format(b_str, f"0{n_qubits // 2}b")[::-1]

            # 交互に [β_k, α_k]
            interleaved = []
            for bit_a, bit_b in zip(a_bits, b_bits):
                interleaved.append(bit_b)
                interleaved.append(bit_a)
            bitstring = "".join(interleaved)

            # Jordan–Wigner 位相補正（元コードと同じ規則）
            sign = 1
            N = len(a_bits)
            for k in range(N):
                if a_bits[k] == "1":
                    # 反転後の添字で k より大きい位置が元の「左側」
                    for l in range(k + 1, N):
                        if b_bits[l] == "1":
                            sign *= -1

            index = int(bitstring, 2)
            state_vector[index] = sign * ci_matrix[i][j]

    state_vec = state_vector.reshape(-1, 1)
    return jw_hamiltonian, n_qubits, energy, state_vec, ci_matrix
