"""Artificial technical verification only. No user-supplied science inputs."""
import argparse
import datetime
from fractions import Fraction
import io
import json
from pathlib import Path
import unittest

import z3

from .environment import file_identity,require_bound_backend
from .guards import OutputBudget,readiness
from .solver import proof_capability_probe,real_literal,solve_exact


class RecordingResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.passed=[]

    def addSuccess(self,test):
        super().addSuccess(test)
        self.passed.append(test.id())


def synthetic_evidence():
    """Documented known math fixtures, independent of any electron/bus ansatz."""
    root=z3.Real('toy_record_root')
    cases={
        'positive_sqrt_two':solve_exact([root],[root*root==real_literal(2)],[(1,2)]),
        'negative_square_impossible':solve_exact([root],[root*root+1==0],[(-1,1)]),
        'known_SAT_with_tiny_resource_cap':solve_exact([root],[root*root==2],[(1,2)],rlimit=1),
    }
    variables=z3.Reals(' '.join(f'toy_record_chain_{j}' for j in range(12)))
    constraints=[variables[0]*variables[0]==real_literal(Fraction(1,2))]
    constraints.extend(variables[j]==variables[0] for j in range(1,12))
    cases['twelve_variable_artificial_chain']=solve_exact(variables,constraints,[(0,1)]*12)
    return {name:decision.record() for name,decision in cases.items()}


def run_suite(output):
    require_bound_backend()
    package=Path(__file__).resolve().parent
    suite=unittest.defaultTestLoader.discover(str(package/'tests'))
    stream=io.StringIO()
    runner=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordingResult)
    result=runner.run(suite)
    evidence=synthetic_evidence() if result.wasSuccessful() else {}
    report={
        'kind':'ARTIFICIAL_TECHNICAL_TESTS_ONLY',
        'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'PASS' if result.wasSuccessful() else 'FAIL',
        'tests_run':result.testsRun,'passed_tests':result.passed,
        'failures':[(test.id(),text) for test,text in result.failures],
        'errors':[(test.id(),text) for test,text in result.errors],
        'skipped':[(test.id(),reason) for test,reason in result.skipped],
        'source_files':[dict(file_identity(path),repository_path=str(path.relative_to(package.parents[1])))
                        for path in sorted(package.rglob('*.py'))],
        'environment_lock':file_identity(package/'environment_lock.json'),
        'synthetic_solver_examples':evidence,
        'proof_capability':proof_capability_probe() if result.wasSuccessful() else None,
        'technical_readiness':readiness(),
        'P1STAR_scientific_inputs_loaded':False,
        'P1STAR_scientific_calculations':0,
        'new_mathematical_theorem_proofs':0,
        'science_authorized':False,
        'interpretation':'software functionality and known identity tests, not scientific feasibility or performance evidence',
    }
    data=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    # New artifact only. Do not overwrite prior/frozen reports.
    with Path(output).open('xb') as destination:
        OutputBudget().write(destination,data)
    print(stream.getvalue(),end='')
    print(json.dumps({'tests_run':report['tests_run'],'status':report['status'],
                      'technical_readiness':report['technical_readiness']['status'],
                      'output':str(output)},indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,help='new technical-only JSON artifact')
    args=parser.parse_args()
    raise SystemExit(run_suite(args.output))
