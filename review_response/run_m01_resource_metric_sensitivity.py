"""M01 representative resource-metric sensitivity validation.

This reuses the D03 model-selected times and direct errors.  It reconstructs
only the frozen molecular grouping needed to count logical circuit resources;
it never builds or diagonalizes a new PF unitary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
import platform
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import jordan_wigner
from pyscf import ao2mo, gto, mcscf, scf

from trotterlib.Almost_optimal_grouping import Almost_optimal_grouper
from trotterlib.pf_decomposition import iter_s2_sequence_steps
from trotterlib.rz_layers import extract_z_terms_for_group, greedy_layering


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = Path(__file__).with_name("m01_resource_metric_sensitivity_protocol.json")
METRICS = (
    "total_pauli_rotations",
    "total_rz_layer_depth",
    "total_t_count",
    "total_t_depth",
)
FORMULA_LABELS = {
    "current_m3": "current_m3",
    "yoshida4": "Yoshida 4th",
    "yoshida6_m3": "Yoshida 6th m=3",
}


class SourceIdentityError(RuntimeError):
    pass


class NumericalValidationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    raise TypeError(type(value).__name__)


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def float_or_none(value: Any) -> float | None:
    if value in (None, "", "None", "null"):
        return None
    return float(value)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def protocol() -> dict[str, Any]:
    return read_json(PROTOCOL_PATH)


def source_paths(config: dict[str, Any]) -> dict[str, tuple[Path, str]]:
    sources = config["sources"]
    d03 = ROOT / sources["d03_artifact"]
    paths = {
        "multi_accuracy_metrics.csv": (
            d03 / "multi_accuracy_metrics.csv",
            sources["multi_accuracy_metrics_csv_sha256"],
        ),
        "final_allowed_metrics.json": (
            d03 / "final_allowed_metrics.json",
            sources["final_allowed_metrics_json_sha256"],
        ),
        "condition_rankings.csv": (
            d03 / "condition_rankings.csv",
            sources["condition_rankings_csv_sha256"],
        ),
        "d03_manifest.json": (
            d03 / "manifest.json",
            sources["d03_manifest_sha256"],
        ),
        "holdout_protocol.json": (
            ROOT / sources["holdout_protocol"],
            sources["holdout_protocol_sha256"],
        ),
    }
    for condition, item in sources["condition_metadata"].items():
        paths[f"metadata/{condition}.json"] = (ROOT / item["path"], item["sha256"])
    return paths


def validate_sources(config: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for label, (path, expected) in source_paths(config).items():
        if not path.is_file():
            raise SourceIdentityError(f"missing frozen source: {path}")
        actual = sha256(path)
        passed = actual == expected
        checks.append(
            {
                "label": label,
                "path": str(path),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "passed": passed,
            }
        )
        if not passed:
            raise SourceIdentityError(f"source SHA-256 mismatch: {label}")
    manifest = read_json(source_paths(config)["d03_manifest.json"][0])
    if manifest.get("status") != "complete":
        raise SourceIdentityError("D03 manifest is not complete")
    if manifest.get("protocol_sha256") != config["sources"]["d03_protocol_sha256"]:
        raise SourceIdentityError("D03 protocol identity mismatch")
    return {"status": "passed", "checks": checks}


def condition_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    holdout = read_json(ROOT / config["sources"]["holdout_protocol"])
    return {item["name"]: item for item in holdout["conditions"]}


def hermitize(operator: QubitOperator) -> tuple[QubitOperator, float]:
    result = QubitOperator()
    maximum_imaginary = 0.0
    for term, raw in operator.terms.items():
        coefficient = complex(raw)
        maximum_imaginary = max(maximum_imaginary, abs(float(coefficient.imag)))
        result += QubitOperator(term, float(coefficient.real))
    return result, maximum_imaginary


def canonical_group_hash(groups: Sequence[QubitOperator]) -> str:
    rows = []
    for group_index, group in enumerate(groups):
        for term, raw in sorted(group.terms.items(), key=lambda item: repr(item[0])):
            value = complex(raw)
            rows.append(
                [
                    group_index,
                    [[int(index), str(pauli)] for index, pauli in term],
                    float(value.real).hex(),
                    float(value.imag).hex(),
                ]
            )
    encoded = json.dumps(rows, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reconstruct_grouping(
    condition: str,
    spec: dict[str, Any],
    expected_metadata: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    molecule = gto.Mole()
    molecule.atom = [(atom, coordinates) for atom, coordinates in spec["geometry_angstrom"]]
    molecule.unit = "Angstrom"
    molecule.basis = str(spec["basis"])
    molecule.spin = int(spec["multiplicity"]) - 1
    molecule.charge = int(spec["charge"])
    molecule.symmetry = False
    molecule.verbose = 0
    molecule.build()
    mean_field = scf.RHF(molecule)
    mean_field.conv_tol = 1e-12
    mean_field.max_cycle = 200
    mean_field.kernel()
    if not mean_field.converged:
        raise NumericalValidationError(f"{condition}: RHF did not converge")

    ncore = int(spec["frozen_core_spatial_orbitals"])
    ncas = int(spec["active_spatial_orbitals"])
    nelecas = int(molecule.nelectron - 2 * ncore)
    if nelecas != int(spec["active_electrons"]):
        raise SourceIdentityError(f"{condition}: active electron mismatch")
    active_indices = list(range(ncore, ncore + ncas))
    cas = mcscf.CASCI(mean_field, ncas, nelecas)
    cas.ncore = ncore
    h1_effective, core_energy = cas.get_h1eff(mean_field.mo_coeff)
    active_coefficients = np.asarray(mean_field.mo_coeff[:, active_indices])
    eri_compact = ao2mo.kernel(molecule, active_coefficients)
    eri_active = ao2mo.restore(1, eri_compact, ncas)
    two_body = np.asarray(eri_active.transpose(0, 2, 3, 1), order="C")
    grouper = Almost_optimal_grouper(
        float(core_energy),
        np.asarray(h1_effective),
        two_body,
        fermion_qubit_mapping=jordan_wigner,
        validation=True,
    )
    fermion_groups = [list(group) for group in grouper.group_term_list]
    fermion_groups[0].insert(0, FermionOperator("", grouper._const_fermion))
    qubit_groups = []
    maximum_imaginary = 0.0
    for group in fermion_groups:
        operator = jordan_wigner(sum(group, FermionOperator()))
        cleaned, removed = hermitize(operator)
        qubit_groups.append(cleaned)
        maximum_imaginary = max(maximum_imaginary, removed)

    term_counts = [sum(1 for term in group.terms if term) for group in qubit_groups]
    z_terms = []
    for group in fermion_groups:
        mapping = {
            support: complex(coefficient)
            for support, coefficient in extract_z_terms_for_group(group, coeff_tol=0.0).items()
            if support
        }
        z_terms.append(mapping)

    metadata = expected_metadata["system"]
    gates = config["numerical_gates"]
    comparisons = {
        "geometry": spec["geometry_angstrom"] == metadata["geometry_angstrom"],
        "basis": str(spec["basis"]) == str(metadata["basis"]),
        "charge": int(spec["charge"]) == int(metadata["charge"]),
        "multiplicity": int(spec["multiplicity"]) == int(metadata["multiplicity"]),
        "active_electrons": nelecas == int(metadata["active_electron_count"]),
        "active_orbitals": ncas == int(metadata["active_spatial_orbitals"]),
        "group_count": len(qubit_groups) == int(metadata["group_count"]),
        "nonidentity_pauli_term_count": sum(term_counts)
        == int(metadata["nonidentity_pauli_term_count"]),
        "scf_energy": abs(float(mean_field.e_tot) - float(metadata["scf_energy_hartree"]))
        <= float(gates["reconstructed_scf_energy_absolute_tolerance_hartree"]),
    }
    hamiltonian = sum(qubit_groups, QubitOperator())
    removed_constant = float(complex(hamiltonian.terms.get((), 0.0)).real)
    comparisons["removed_constant"] = abs(
        removed_constant - float(metadata["removed_constant_hartree"])
    ) <= float(gates["reconstructed_removed_constant_absolute_tolerance_hartree"])
    comparisons["imaginary_coefficients"] = maximum_imaginary <= float(
        gates["maximum_removed_imaginary_pauli_coefficient"]
    )
    if not all(comparisons.values()):
        raise SourceIdentityError(f"{condition}: grouping identity failure {comparisons}")
    return {
        "condition": condition,
        "term_counts": term_counts,
        "z_terms": z_terms,
        "group_count": len(qubit_groups),
        "nonidentity_pauli_term_count": sum(term_counts),
        "compiled_z_support_count": sum(len(group) for group in z_terms),
        "grouping_sha256": canonical_group_hash(qubit_groups),
        "maximum_removed_imaginary_pauli_coefficient": maximum_imaginary,
        "scf_energy_hartree": float(mean_field.e_tot),
        "removed_constant_hartree": removed_constant,
        "comparisons": comparisons,
        "elapsed_seconds": time.perf_counter() - started,
    }


def is_clifford_angle(angle: float, tolerance: float) -> bool:
    unit = math.pi / 2.0
    return abs(angle - round(angle / unit) * unit) <= tolerance


def circuit_counts(
    term_counts: Sequence[int],
    z_terms: Sequence[dict[frozenset[int], complex]],
    sequence: Sequence[float],
    time_value: float,
    zero_tolerance: float,
    clifford_tolerance: float,
) -> dict[str, Any]:
    steps = list(iter_s2_sequence_steps(len(term_counts), sequence))
    pauli_rotations = int(sum(int(term_counts[index]) for index, _ in steps))
    compiled_candidates = zero = clifford = nonclifford = 0
    rz_layers = nonclifford_layers = 0
    maximum_imaginary = 0.0
    for group_index, weight in steps:
        nonzero_supports = []
        nonclifford_supports = []
        for support, raw_coefficient in z_terms[group_index].items():
            compiled_candidates += 1
            coefficient = complex(raw_coefficient)
            maximum_imaginary = max(maximum_imaginary, abs(float(coefficient.imag)))
            angle = 2.0 * float(time_value) * float(weight) * float(coefficient.real)
            if abs(angle) <= zero_tolerance:
                zero += 1
                continue
            nonzero_supports.append(support)
            if is_clifford_angle(angle, clifford_tolerance):
                clifford += 1
            else:
                nonclifford += 1
                nonclifford_supports.append(support)
        rz_layers += len(greedy_layering(nonzero_supports))
        nonclifford_layers += len(greedy_layering(nonclifford_supports))
    return {
        "merged_group_exponential_count": len(steps),
        "pauli_rotations_per_pf_unitary": pauli_rotations,
        "compiled_rz_candidates_per_pf_unitary": compiled_candidates,
        "zero_angle_rz_per_pf_unitary": zero,
        "all_nonzero_rz_per_pf_unitary": compiled_candidates - zero,
        "clifford_rz_per_pf_unitary": clifford,
        "nonclifford_rz_per_pf_unitary": nonclifford,
        "rz_layer_depth_per_pf_unitary": rz_layers,
        "nonclifford_rz_layer_depth_per_pf_unitary": nonclifford_layers,
        "maximum_transformed_coefficient_imaginary_part": maximum_imaginary,
    }


def selected_metric_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    d03 = ROOT / config["sources"]["d03_artifact"]
    all_rows = load_csv(d03 / "multi_accuracy_metrics.csv")
    requested = []
    scope = config["scope"]
    for condition in scope["primary_conditions"]:
        for target in scope["primary_targets"]:
            for formula in scope["formulae"]:
                requested.append(("primary", condition, target, formula))
    for condition in scope["diagnostic_conditions"]:
        for target in scope["diagnostic_targets"]:
            for formula in scope["formulae"]:
                requested.append(("diagnostic", condition, target, formula))
    selected = []
    for role, condition, target, formula in requested:
        matches = [
            row
            for row in all_rows
            if row["dataset"] == "p03"
            and row["condition"] == condition
            and row["target_name"] == target
            and row["formula"] == formula
        ]
        if len(matches) != 1:
            raise SourceIdentityError(
                f"expected one D03 row for {(condition, target, formula)}, got {len(matches)}"
            )
        row = dict(matches[0])
        row["scope_role"] = role
        selected.append(row)
    return selected


def formula_payload(condition: str, formula: str) -> dict[str, Any]:
    path = (
        ROOT
        / "artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/raw"
        / f"{condition}__{formula}.json"
    )
    if not path.is_file():
        raise SourceIdentityError(f"missing formula source: {path}")
    payload = read_json(path)
    if payload.get("status") != "complete":
        raise SourceIdentityError(f"formula source is not complete: {path}")
    return {"path": str(path), "sha256": sha256(path), **payload["formula"]}


def evaluate_row(
    row: dict[str, str],
    grouping: dict[str, Any],
    formula: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    time_value = float_or_none(row.get("model_time"))
    target = float_or_none(row.get("target_error_hartree"))
    direct_error = float_or_none(row.get("nearest_direct_error_hartree"))
    nearest_time = float_or_none(row.get("nearest_direct_time"))
    stored_rotations = int(float(row["rotations"]))
    stored_cost = float_or_none(row.get("nearest_direct_cost"))
    if None in (time_value, target, direct_error, nearest_time, stored_cost):
        raise NumericalValidationError(
            f"unscorable D03 row: {(row['condition'], row['target_name'], row['formula'])}"
        )
    assert time_value is not None and target is not None and direct_error is not None
    assert nearest_time is not None and stored_cost is not None
    mismatch = abs(nearest_time / time_value - 1.0)
    if row.get("model_time_direct_point_covered", "").lower() != "true":
        raise NumericalValidationError("model time direct point is not covered")
    maximum_mismatch = float(
        config["time_and_qpe_rule"]["maximum_nearest_direct_time_relative_mismatch"]
    )
    if mismatch > maximum_mismatch:
        raise NumericalValidationError(f"model/direct time mismatch {mismatch}")
    remaining = target - abs(direct_error)
    if remaining <= 0:
        raise NumericalValidationError("infeasible selected direct error budget")
    beta = float(config["time_and_qpe_rule"]["beta"])
    qpe_uses = beta / (time_value * remaining)
    qpe_rotation_total = qpe_uses * stored_rotations
    relative_cost_difference = abs(qpe_rotation_total / stored_cost - 1.0)
    if relative_cost_difference > float(
        config["numerical_gates"]["qpe_rotation_total_relative_tolerance"]
    ):
        raise NumericalValidationError(
            f"D03 cost identity mismatch {relative_cost_difference}"
        )

    counts = circuit_counts(
        grouping["term_counts"],
        grouping["z_terms"],
        formula["s2_sequence"],
        time_value,
        float(config["circuit_resource_rule"]["zero_angle_absolute_tolerance_radians"]),
        float(
            config["circuit_resource_rule"][
                "clifford_angle_distance_tolerance_radians"
            ]
        ),
    )
    if counts["pauli_rotations_per_pf_unitary"] != stored_rotations:
        raise SourceIdentityError(
            f"rotation count mismatch for {(row['condition'], row['formula'])}: "
            f"{counts['pauli_rotations_per_pf_unitary']} != {stored_rotations}"
        )
    nonclifford = int(counts["nonclifford_rz_per_pf_unitary"])
    if nonclifford <= 0:
        per_rotation_error = None
        per_rotation_t_count = 0
    else:
        fraction = float(
            config["circuit_resource_rule"]["synthesis_energy_budget_fraction"]
        )
        per_rotation_error = time_value * fraction * target / (nonclifford * qpe_uses)
        if not 0.0 < per_rotation_error < 1.0:
            raise NumericalValidationError(
                f"invalid synthesis error allocation {per_rotation_error}"
            )
        per_rotation_t_count = int(math.ceil(3.0 * math.log2(1.0 / per_rotation_error)))

    output = {
        "scope_role": row["scope_role"],
        "condition": row["condition"],
        "target_name": row["target_name"],
        "target_error_hartree": target,
        "formula": row["formula"],
        "formula_display": FORMULA_LABELS[row["formula"]],
        "formal_order": int(float(row["formal_order"])),
        "d03_analysis_status": row["analysis_status"],
        "d03_fixed_model_passed": row["fixed_model_passed"].lower() == "true",
        "selected_time": time_value,
        "signed_model_shift_hartree": float(row["model_signed_shift_hartree"]),
        "absolute_direct_error_hartree": abs(direct_error),
        "remaining_qpe_error_budget_hartree": remaining,
        "continuous_qpe_use_factor": qpe_uses,
        "ceiling_qpe_use_count": int(math.ceil(qpe_uses)),
        "d03_direct_cost_at_selected_time": stored_cost,
        "qpe_rotation_total_relative_difference_from_d03": relative_cost_difference,
        "formula_source_path": formula["path"],
        "formula_source_sha256": formula["sha256"],
        **counts,
        "synthesis_error_per_nonclifford_rz": per_rotation_error,
        "t_count_per_nonclifford_rz": per_rotation_t_count,
        "total_pauli_rotations": qpe_uses
        * counts["pauli_rotations_per_pf_unitary"],
        "total_compiled_nonzero_rz": qpe_uses
        * counts["all_nonzero_rz_per_pf_unitary"],
        "total_rz_layer_depth": qpe_uses
        * counts["rz_layer_depth_per_pf_unitary"],
        "total_t_count": qpe_uses * nonclifford * per_rotation_t_count,
        "total_t_depth": qpe_uses
        * counts["nonclifford_rz_layer_depth_per_pf_unitary"]
        * per_rotation_t_count,
    }
    return output


def metric_relation(a: float, b: float, tolerance: float) -> int:
    scale = max(abs(a), abs(b), 1.0)
    if abs(a - b) <= tolerance * scale:
        return 0
    return -1 if a < b else 1


def rank_resources(
    rows: Sequence[dict[str, Any]], relative_tie_tolerance: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rankings = []
    summaries = []
    inversions = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["condition"], row["target_name"])].append(row)
    for (condition, target), group in sorted(grouped.items()):
        best_by_metric = {}
        for metric in METRICS:
            ordered = sorted(group, key=lambda item: (float(item[metric]), item["formula"]))
            best = float(ordered[0][metric])
            best_formulae = [
                item["formula"]
                for item in ordered
                if metric_relation(float(item[metric]), best, relative_tie_tolerance) == 0
            ]
            best_by_metric[metric] = best_formulae
            rank = 0
            previous = None
            for index, item in enumerate(ordered, start=1):
                value = float(item[metric])
                if previous is None or metric_relation(value, previous, relative_tie_tolerance) != 0:
                    rank = index
                rankings.append(
                    {
                        "condition": condition,
                        "target_name": target,
                        "metric": metric,
                        "formula": item["formula"],
                        "rank": rank,
                        "value": value,
                        "ratio_to_best": value / best,
                        "best_formulae": ";".join(best_formulae),
                    }
                )
                previous = value
        unique_best_sets = {tuple(value) for value in best_by_metric.values()}
        group_inversions = 0
        for formula_a, formula_b in itertools.combinations(
            sorted(item["formula"] for item in group), 2
        ):
            item_a = next(item for item in group if item["formula"] == formula_a)
            item_b = next(item for item in group if item["formula"] == formula_b)
            relations = {
                metric: metric_relation(
                    float(item_a[metric]), float(item_b[metric]), relative_tie_tolerance
                )
                for metric in METRICS
            }
            distinct = {value for value in relations.values() if value != 0}
            inverted = len(distinct) > 1
            if inverted:
                group_inversions += 1
            inversions.append(
                {
                    "condition": condition,
                    "target_name": target,
                    "formula_a": formula_a,
                    "formula_b": formula_b,
                    **{f"relation_{metric}": value for metric, value in relations.items()},
                    "pairwise_order_inversion": inverted,
                }
            )
        summaries.append(
            {
                "condition": condition,
                "target_name": target,
                **{
                    f"best_{metric}": ";".join(best_by_metric[metric])
                    for metric in METRICS
                },
                "best_pf_changes_across_metrics": len(unique_best_sets) > 1,
                "pairwise_inversion_count": group_inversions,
            }
        )
    return rankings, summaries, inversions


def grouping_public_row(grouping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in grouping.items() if key not in {"term_counts", "z_terms"}}


def make_plot(path: Path, rankings: Sequence[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups = sorted({(row["condition"], row["target_name"]) for row in rankings})
    formulas = ("current_m3", "yoshida4", "yoshida6_m3")
    colors = {"current_m3": "#35618f", "yoshida4": "#dd7f2a", "yoshida6_m3": "#4b9b69"}
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), dpi=150, sharex=True)
    width = 0.24
    positions = np.arange(len(groups), dtype=float)
    for axis, metric in zip(axes.flat, METRICS):
        metric_rows = [row for row in rankings if row["metric"] == metric]
        for offset, formula in enumerate(formulas):
            values = []
            for group in groups:
                item = next(
                    row
                    for row in metric_rows
                    if (row["condition"], row["target_name"]) == group
                    and row["formula"] == formula
                )
                values.append(float(item["ratio_to_best"]))
            axis.bar(
                positions + (offset - 1) * width,
                values,
                width=width,
                color=colors[formula],
                label=FORMULA_LABELS[formula],
            )
        axis.axhline(1.0, color="black", linewidth=0.8)
        axis.set_title(metric.replace("total_", "").replace("_", " "))
        axis.set_yscale("log")
        axis.set_ylabel("ratio to metric best")
        axis.grid(axis="y", which="both", alpha=0.25)
    labels = [f"{condition.replace('_sto3g', '')}\n{target}" for condition, target in groups]
    for axis in axes[-1]:
        axis.set_xticks(positions, labels, rotation=25, ha="right")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=3)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(path)
    plt.close(figure)


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(
            args, cwd=ROOT, text=True, capture_output=True, check=False
        ).stdout.strip()

    return {
        "commit": run("git", "rev-parse", "HEAD"),
        "branch": run("git", "branch", "--show-current"),
        "status": run("git", "status", "--short").splitlines(),
    }


def environment() -> dict[str, Any]:
    packages = {}
    for name in ("numpy", "scipy", "pyscf", "openfermion", "matplotlib"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
        "cpu_count": os.cpu_count(),
    }


def artifact_hashes(output: Path) -> dict[str, str]:
    result = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "COMPLETE"}:
            result[str(path.relative_to(output))] = sha256(path)
    return result


def report_lines(
    rows: Sequence[dict[str, Any]],
    summaries: Sequence[dict[str, Any]],
    eligible_summaries: Sequence[dict[str, Any]],
    audit: dict[str, Any],
) -> list[str]:
    lines = [
        "# M01 resource-metric sensitivity",
        "",
        f"Status: **{audit['status']}**",
        "",
        "D03で固定された二項モデル選択時刻と直接誤差を再利用し、新しいPF固有値点を計算せず、回路資源の単位だけを比較した。",
        "",
        "## 指標別最良PF",
        "",
        "| condition | target | rotations | RZ layers | T-count | T-depth | best change | pairwise inversions |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for item in summaries:
        lines.append(
            "| {condition} | {target_name} | {best_total_pauli_rotations} | "
            "{best_total_rz_layer_depth} | {best_total_t_count} | "
            "{best_total_t_depth} | {best_pf_changes_across_metrics} | "
            "{pairwise_inversion_count} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## D03固定モデル合格PFに限定した最良PF",
            "",
            "この表は資源量だけでなく、D03の固定モデル判定に合格したPFだけを採用候補として比較する。",
            "",
            "| condition | target | eligible PFs | rotations | RZ layers | T-count | T-depth |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in eligible_summaries:
        lines.append(
            "| {condition} | {target_name} | {eligible_formulae} | "
            "{best_total_pauli_rotations} | {best_total_rz_layer_depth} | "
            "{best_total_t_count} | {best_total_t_depth} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## 選択時刻での回路資源内訳",
            "",
            "| condition | target | PF | direct pass | rotations/PF | compiled RZ/PF | RZ layers/PF | T/RZ |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['condition']} | {row['target_name']} | {row['formula']} | "
            f"{row['d03_fixed_model_passed']} | {row['pauli_rotations_per_pf_unitary']} | "
            f"{row['all_nonzero_rz_per_pf_unitary']} | "
            f"{row['rz_layer_depth_per_pf_unitary']} | {row['t_count_per_nonclifford_rz']} |"
        )
    primary = [item for item in summaries if item["condition"].startswith("N2_")]
    primary_changes = sum(bool(item["best_pf_changes_across_metrics"]) for item in primary)
    primary_inversions = sum(int(item["pairwise_inversion_count"]) for item in primary)
    lines.extend(
        [
            "",
            "## 主結論",
            "",
            f"- N2主判定4組のうち、最良PFが資源指標で変わった組は `{primary_changes}`。",
            f"- N2主判定におけるpairwise順位反転は合計 `{primary_inversions}`。",
            "- N2主判定では `current_m3` が4資源指標すべてで最良だった。",
            "- Pauli rotations、compiled RZ、RZ layerは別の単位として保存した。",
            "- T-count/T-depthは1%の合成エネルギー予算と `ceil(3 log2(1/epsilon_rot))` を使う固定proxyである。",
            "- controlled-U、状態準備、QFT、routing、magic-state factoryは含まないため、実行時間とは呼ばない。",
            "- HF stretchは破綻例の診断であり、N2の主判定と混ぜない。",
            "- HF stretchではraw資源最小の `current_m3` はD03固定モデルに不合格であり、採用可能PF限定では `yoshida6_m3` のみが残る。",
        ]
    )
    return lines


def run(output: Path) -> int:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    config = protocol()
    try:
        source_audit = validate_sources(config)
        atomic_json(output / "source_identity_audit.json", source_audit)
        specs = condition_specs(config)
        selected = selected_metric_rows(config)
        groupings = {}
        for condition in (
            config["scope"]["primary_conditions"]
            + config["scope"]["diagnostic_conditions"]
        ):
            metadata_path = ROOT / config["sources"]["condition_metadata"][condition]["path"]
            groupings[condition] = reconstruct_grouping(
                condition, specs[condition], read_json(metadata_path), config
            )
        public_groupings = [grouping_public_row(item) for item in groupings.values()]
        write_csv(output / "condition_grouping.csv", public_groupings)
        atomic_json(output / "condition_grouping.json", {"rows": public_groupings})

        formulae = {}
        rows = []
        for source_row in selected:
            key = (source_row["condition"], source_row["formula"])
            if key not in formulae:
                formulae[key] = formula_payload(*key)
            rows.append(
                evaluate_row(
                    source_row,
                    groupings[source_row["condition"]],
                    formulae[key],
                    config,
                )
            )
        rankings, summaries, inversions = rank_resources(
            rows, float(config["numerical_gates"]["ranking_relative_tie_tolerance"])
        )
        eligible_rows = [row for row in rows if bool(row["d03_fixed_model_passed"])]
        eligible_rankings, eligible_summaries, eligible_inversions = rank_resources(
            eligible_rows,
            float(config["numerical_gates"]["ranking_relative_tie_tolerance"]),
        )
        eligible_formulae = defaultdict(list)
        for row in eligible_rows:
            eligible_formulae[(row["condition"], row["target_name"])].append(row["formula"])
        for item in eligible_summaries:
            item["eligible_formulae"] = ";".join(
                sorted(eligible_formulae[(item["condition"], item["target_name"])])
            )
        write_csv(output / "resource_rows.csv", rows)
        write_csv(output / "resource_rankings.csv", rankings)
        write_csv(output / "ranking_summary.csv", summaries)
        write_csv(output / "rank_inversions.csv", inversions)
        write_csv(output / "eligible_resource_rankings.csv", eligible_rankings)
        write_csv(output / "eligible_ranking_summary.csv", eligible_summaries)
        write_csv(output / "eligible_rank_inversions.csv", eligible_inversions)
        make_plot(output / "resource_metric_ratios.png", rankings)
        primary_summaries = [
            item
            for item in summaries
            if item["condition"] in config["scope"]["primary_conditions"]
        ]
        analysis = {
            "schema": "m01_resource_metric_sensitivity_analysis_v1",
            "status": "complete_with_findings",
            "protocol_sha256": sha256(PROTOCOL_PATH),
            "new_direct_pf_eigenvalue_point_count": 0,
            "row_count": len(rows),
            "primary_group_count": len(primary_summaries),
            "diagnostic_group_count": len(summaries) - len(primary_summaries),
            "primary_best_pf_change_count": sum(
                bool(item["best_pf_changes_across_metrics"])
                for item in primary_summaries
            ),
            "primary_pairwise_inversion_count": sum(
                int(item["pairwise_inversion_count"])
                for item in primary_summaries
            ),
            "summary_rows": summaries,
            "eligible_summary_rows": eligible_summaries,
        }
        atomic_json(output / "analysis.json", analysis)
        audit = {
            "schema": "m01_resource_metric_sensitivity_audit_v1",
            "status": "complete_with_findings",
            "protocol_sha256": sha256(PROTOCOL_PATH),
            "base_result_commit": config["base_result_commit"],
            "source_identity": source_audit,
            "all_grouping_identity_checks_passed": all(
                all(item["comparisons"].values()) for item in public_groupings
            ),
            "all_rows_scorable": len(rows) == 15,
            "new_direct_pf_eigenvalue_point_count": 0,
            "elapsed_seconds": time.perf_counter() - started,
            "git": git_state(),
            "environment": environment(),
        }
        if not audit["all_grouping_identity_checks_passed"] or not audit["all_rows_scorable"]:
            raise NumericalValidationError("completion gates did not pass")
        atomic_json(output / "audit.json", audit)
        (output / "report.md").write_text(
            "\n".join(report_lines(rows, summaries, eligible_summaries, audit)) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schema": "m01_resource_metric_sensitivity_manifest_v1",
            "status": "complete_with_findings",
            "protocol_sha256": sha256(PROTOCOL_PATH),
            "base_result_commit": config["base_result_commit"],
            "artifact_hashes": artifact_hashes(output),
        }
        atomic_json(output / "manifest.json", manifest)
        (output / "COMPLETE").write_text("complete_with_findings\n", encoding="utf-8")
        return 0
    except SourceIdentityError as error:
        atomic_json(
            output / "audit.json",
            {"status": "failed_source_identity", "error": str(error)},
        )
        return 3
    except NumericalValidationError as error:
        atomic_json(
            output / "audit.json",
            {"status": "failed_numerical_validation", "error": str(error)},
        )
        return 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(Path(args.output).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
