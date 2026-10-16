import io
import json
from pathlib import Path
import tempfile
import unittest

from p1star_foundation.guards import (CONTRACT_LIMITS,Deadline,NotReady,OutputBudget,
    OutputLimitExceeded,SingleJob,readiness,require_phase_b_ready,run_technical_probe)


class GuardTests(unittest.TestCase):
    def test_unchanged_contract_limits(self):
        self.assertEqual(CONTRACT_LIMITS.__dict__,{'jobs':1,'cpu_processes':1,
            'ram_bytes':17179869184,'wall_seconds':1800,'terms':200000,'output_bytes':20971520})

    def test_aggregate_output_exact_boundary_and_no_partial_write(self):
        budget=OutputBudget(4);a=io.BytesIO();b=io.BytesIO()
        budget.write(a,b'ab');budget.write(b,b'cd')
        with self.assertRaises(OutputLimitExceeded):budget.write(b,b'e')
        self.assertEqual(a.getvalue()+b.getvalue(),b'abcd')
        self.assertEqual(budget.used,4)
        self.assertTrue(budget.stopped)

    def test_one_monotonic_deadline_not_per_stage(self):
        clock=[10]
        deadline=Deadline(30,clock=lambda:clock[0])
        clock[0]=29;self.assertEqual(deadline.remaining(),11)
        clock[0]=40
        with self.assertRaises(TimeoutError):deadline.check()

    def test_lock_excludes_overlapping_worker_and_releases(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'job.lock'
            with SingleJob(path):
                with self.assertRaises(NotReady):
                    with SingleJob(path):pass
            with SingleJob(path):pass

    def test_worker_single_cpu_process_and_virtual_address_limit(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_technical_probe('affinity',d)
        self.assertEqual(result['reason'],'EXITED')
        self.assertEqual(result['returncode'],0)
        row=json.loads(result['output'])
        self.assertEqual(len(row['affinity']),1)
        self.assertEqual(row['threads'],1)
        self.assertTrue(row['fork_blocked_for_worker'])
        self.assertEqual(row['RLIMIT_AS'],[128*1024**2]*2)
        self.assertFalse(result['RAM_hard_limit_verified'])

    def test_memory_probe_is_small_address_space_test(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_technical_probe('memory',d)
        self.assertEqual(result['returncode'],0)
        self.assertIn('EXPECTED_MEMORY_ERROR',result['output'])

    def test_external_wall_kill_even_when_TERM_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_technical_probe('wall',d,seconds=0.25)
        self.assertEqual(result['reason'],'WALL_LIMIT')
        self.assertLess(result['returncode'],0)

    def test_aggregate_capture_bound(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_technical_probe('output',d,output_bytes=1024)
        self.assertEqual(result['reason'],'OUTPUT_LIMIT')
        self.assertLessEqual(result['captured_bytes'],1024)

    def test_no_arbitrary_or_scientific_command_path(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):run_technical_probe('science',d)
        with self.assertRaises(NotReady):require_phase_b_ready()
        report=readiness()
        self.assertEqual(report['status'],'NOT_READY')
        self.assertFalse(report['science_authorized'])
        self.assertFalse(report['contract_changed'])
