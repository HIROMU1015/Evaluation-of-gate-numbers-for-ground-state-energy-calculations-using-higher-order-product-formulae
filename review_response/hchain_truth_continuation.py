"""Infrastructure only: sealed source imports and a zero-front-end truth ledger."""
from contextlib import contextmanager
import hashlib
import importlib.abc
import importlib.machinery
import sys
from pathlib import Path

import hchain_supplement_execution as core

BASE = "1aad415bfaed5503508872c1fa5a8a8c12da4193"
PREDICTION_COMMIT = "61ae95edce8c4a25167521c0e6e95a83c3cbc4bb"
GROUND_COMMIT = "1e5d66a4914bc50a8afa55baa578cca55a227979"
INPUT_COMMIT = "afbf22d063199ccc573c6664d7198acea1990a3f"
REFERENCE_COMMIT = "cd5488902e46bc1320d6fc983f2d6e76d5aa4010"
RECOVERY = "artifacts/hchain_h6_geometry_recovery_20261006"
RECOVERY_DOC = "docs/second_study_v2/hchain_geometry_recovery_20261006"
DOC = "docs/second_study_v2/hchain_truth_continuation_20261006"
DISTANCES = (.8, 1.2, 1.4, 1.6)
SUCCESS = "hchain_h6_geometry_sweep_truth_continuation_complete_review_required"
FAILURE = "hchain_h6_geometry_sweep_truth_continuation_failed_review_required"
FORBIDDEN = ("H6_Hamiltonian_generations", "H6_CISD_generations", "input_verification_h_matvecs",
    "reference_pf_actions", "reference_h_exponential_actions", "candidate_cheap_pf_actions",
    "candidate_h_exponential_actions", "m1_pf_vector_actions", "m1_h_matvecs", "Arnoldi_chains",
    "full_H_ground_solves", "ground_verification_H_matvecs")


def import_entries(root):
    entries = core.read(Path(root) / RECOVERY_DOC / "source_freeze.json")["files"]
    # Close an unchanged pure import dependency omitted by the previous seal.
    name = "review_response/hchain_selective_calibration_schedule.py"
    if not any(row["path"] == name for row in entries):
        data = (Path(root) / name).read_bytes()
        if data != core.git(root, "show", f"{BASE}:{name}"):
            raise core.PreparationError("unchanged truth import dependency changed")
        entries = [*entries, {"path": name, "sha256": hashlib.sha256(data).hexdigest()}]
    return entries


class TruthOnlyLedger(core.ScienceLedger):
    def __init__(self, rank=8):
        super().__init__(rank)
        self.limits.update({name: 0 for name in FORBIDDEN})


class SealedSourceLoader(importlib.machinery.SourceFileLoader):
    def __init__(self, name, path, expected_sha256, events):
        super().__init__(name, str(path))
        self.expected_sha256 = expected_sha256
        self.events = events

    def get_code(self, fullname):
        # Deliberately bypass SourceFileLoader.get_code's bytecode-cache path.
        source = self.get_data(self.path)
        digest = hashlib.sha256(source).hexdigest()
        if digest != self.expected_sha256:
            raise core.PreparationError("sealed import source hash changed: " + self.path)
        code = self.source_to_code(source, self.path)
        self.events.append({"module": fullname, "path": self.path, "sha256": digest,
            "source_only": True, "pyc_reads": 0, "pyc_writes": 0})
        return code


class SealedSourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root, entries):
        self.root = Path(root).resolve()
        self.hashes = {str((self.root / row["path"]).resolve()): row["sha256"]
                       for row in entries if row["path"].endswith(".py")}
        self.events = []

    def find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or not spec.origin or not spec.origin.endswith(".py"):
            return None
        origin = Path(spec.origin).resolve()
        if not origin.is_relative_to(self.root):
            return None
        if str(origin) not in self.hashes or Path(spec.origin).is_symlink():
            raise core.PreparationError("repository import is not a sealed .py source: " + str(origin))
        spec.loader = SealedSourceLoader(fullname, origin, self.hashes[str(origin)], self.events)
        return spec


@contextmanager
def source_only_imports(root, entries):
    finder = SealedSourceFinder(root, entries)
    sys.meta_path.insert(0, finder)
    try:
        yield finder
    finally:
        sys.meta_path.remove(finder)


def verified_runtime_records(root):
    """Validate committed metadata and existing bytes; no generation or H action."""
    root = Path(root)
    for stage, commit in (("inputs", INPUT_COMMIT), ("reference_time", REFERENCE_COMMIT),
                          ("prediction", PREDICTION_COMMIT), ("ground", GROUND_COMMIT)):
        core.verify_bundle(root, root / RECOVERY / stage, commit)
    inputs = core.read(root / RECOVERY / "inputs/prediction.json")
    prediction = core.read(root / RECOVERY / "prediction/prediction.json")
    reference = core.read(root / RECOVERY / "reference_time/prediction.json")
    ground = core.read(root / RECOVERY / "ground/prediction.json")
    expected = {f"H6_R{r:.2f}" for r in DISTANCES}
    if {r["unit"] for r in inputs["workers"]} != expected or len(prediction["workers"]) != 5:
        raise core.PreparationError("fixed four new inputs / five global predictions required")
    if ground["prediction_commit"] != PREDICTION_COMMIT:
        raise core.PreparationError("ground not tied to fixed prediction commit")
    grounds = {r["unit"]: r for r in ground["workers"]}
    plans = {r["unit"]: r["candidate_plan"] for r in reference["workers"]}
    predicted = {r["unit"]: r for r in prediction["workers"]}
    results, checks = [], []
    for item in inputs["workers"]:
        unit = item["unit"]
        record = item["input"]
        g = grounds[unit]
        if any(r["status"] != "complete" for r in (item, g, predicted[unit])):
            raise core.PreparationError("frozen front-end failure; no regeneration")
        for path, digest, size in ((record["runtime_file"], record["runtime_sha256"], record["runtime_bytes"]),
                                   (g["ground_runtime"], g["ground_runtime_sha256"], None)):
            p = Path(path)
            if not p.is_file() or p.is_symlink() or core.sha_file(p) != digest or (size is not None and p.stat().st_size != size):
                raise core.PreparationError("frozen external runtime bytes changed; no regeneration: " + path)
            checks.append({"unit": unit, "path": path, "sha256": digest, "bytes": p.stat().st_size,
                "origin_result_commit": INPUT_COMMIT if size is not None else GROUND_COMMIT,
                "verified_snapshot_commit": BASE, "reused_not_copied": True})
        for key in ("H_sha256_numpy_v1", "sector_indices_sha256_numpy_v1", "sector_dimension"):
            if g["ground"][key] != record["identity"][key]:
                raise core.PreparationError("same-H ground identity mismatch")
        plan = plans[unit]
        if len(plan) != 3 or [p["ratio"] for p in plan] != [.5, .65, .8]:
            raise core.PreparationError("three fixed ascending coordinates required")
        for candidate, cheap, m1 in zip(plan, predicted[unit]["cheap"], predicted[unit]["M1"], strict=True):
            if candidate["time"].hex() != candidate["time_hex"] or any(c["candidate_id"] != candidate["candidate_id"] or c["time_hex"] != candidate["time_hex"] for c in (cheap, m1)):
                raise core.PreparationError("prediction coordinate identity changed")
        results.append({"unit": unit, "stage": "G_truth", "input": record, "ground": g, "plan": plan})
    return prediction, sorted(results, key=lambda r:r["unit"]), checks


def truth_worker(task):
    """Invoke the unchanged original truth worker under source-only import routing."""
    if task["stage"] != "G_truth" or task["unit"] not in {f"H6_R{r:.2f}" for r in DISTANCES}:
        raise core.PreparationError("truth-only stage/geometry required")
    root = Path(task["root"])
    original_guard, original_ledger, original_doc = core.make_guard, core.ScienceLedger, core.DOC
    allowed_runtime = [Path(task["input"]["runtime_file"]), Path(task["ground"]["ground_runtime"])]
    guards = []
    def guarded(root, out, *, extra=()):
        guard = original_guard(root, out, extra=(*extra, *allowed_runtime))
        guards.append(guard)
        return guard
    core.make_guard, core.ScienceLedger, core.DOC = guarded, TruthOnlyLedger, DOC
    entries = core.read(root / DOC / "source_freeze.json")["files"]
    try:
        with source_only_imports(root, entries) as finder:
            result = core.worker(task)
            result["sealed_source_imports"] = finder.events
            result["reuse_input_commit"] = INPUT_COMMIT
            result["reuse_prediction_commit"] = PREDICTION_COMMIT
            result["reuse_ground_commit"] = GROUND_COMMIT
            result["new_front_end_actions"] = sum(result["resource"]["counts"].get(k, 0) for k in FORBIDDEN)
            result["expected_ground_vector_read"] = result["status"] == "complete"
            if result["new_front_end_actions"]:
                raise core.PreparationError("forbidden front-end action in continuation")
            return result
    finally:
        for guard in guards:
            guard.enabled = False
        core.make_guard, core.ScienceLedger, core.DOC = original_guard, original_ledger, original_doc
