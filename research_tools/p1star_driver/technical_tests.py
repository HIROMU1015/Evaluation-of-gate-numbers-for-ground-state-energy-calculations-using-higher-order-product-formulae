"""Run only foundation identities and artificial driver tests; emit scalar audit.

No science CLI or fixed input loader is invoked. Do not use for science work.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest

from p1star_foundation.environment import collect_runtime, require_bound_backend


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[]

    def startTest(self,test):
        super().startTest(test);self.started=time.monotonic()

    def addSuccess(self,test):
        super().addSuccess(test)
        self.records.append({'test':test.id(),'status':'PASS','seconds':time.monotonic()-self.started})


def main():
    output=Path(sys.argv[1])
    root=Path(__file__).resolve().parents[1]
    require_bound_backend()
    suite=unittest.TestSuite()
    counts={}
    # Independent discovery roots prevent duplicate test module names.
    for package in ('p1star_foundation','p1star_driver'):
        loader=unittest.TestLoader()
        child=loader.discover(str(root/package/'tests'))
        counts[package]=child.countTestCases();suite.addTest(child)
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(suite)
    source=[]
    for package in counts:
        for path in sorted((root/package).rglob('*.py')):
            data=path.read_bytes()
            source.append({'path':str(path.relative_to(root.parent)),'bytes':len(data),
                           'sha256':hashlib.sha256(data).hexdigest()})
    record={'kind':'artificial technical verification; no P1* science',
            'completed_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
            'passed':result.wasSuccessful(),'tests_run':result.testsRun,'suite_counts':counts,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'elapsed_seconds':time.monotonic()-started,'test_records':result.records,
            'source_snapshot':source,'runtime':collect_runtime(),
            'science_entrypoint_executed':False,'fixed_science_input_loaded':False,
            'fixed_factors_evaluated':False,'fixed_12_segment_expanded':False,
            'actual_science_conditions_generated_or_solved':False,
            'interpretation':'PASS establishes artificial technical checks only, not scientific feasibility or authorization'}
    output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
