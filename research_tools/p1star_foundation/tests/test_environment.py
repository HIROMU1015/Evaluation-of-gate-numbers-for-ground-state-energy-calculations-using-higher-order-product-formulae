import json
from pathlib import Path
import tempfile
import unittest

from p1star_foundation.environment import loaded_z3_library,require_bound_backend


class EnvironmentTests(unittest.TestCase):
    def test_loaded_backend_matches_frozen_library(self):
        require_bound_backend()
        identity=loaded_z3_library()
        self.assertEqual(identity['bytes'],21715032)
        self.assertEqual(identity['sha256'],'fa2f59a2be4292e8eefc4928f9cdc8eaad6f2ae8e44476fd67c1f03ab86e767f')

    def test_changed_library_lock_rejected_before_solver_use(self):
        original=Path(__file__).resolve().parents[1]/'environment_lock.json'
        lock=json.loads(original.read_text())
        lock['runtime']['z3_mapped_library']['sha256']='0'*64
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad_lock.json';path.write_text(json.dumps(lock))
            with self.assertRaises(RuntimeError):require_bound_backend(path)

    def test_changed_version_lock_rejected(self):
        original=Path(__file__).resolve().parents[1]/'environment_lock.json'
        lock=json.loads(original.read_text());lock['runtime']['z3_full_version']='unapproved'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad_lock.json';path.write_text(json.dumps(lock))
            with self.assertRaises(RuntimeError):require_bound_backend(path)
