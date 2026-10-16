"""Generic one-shot formal verification. This module contains no P1* inputs."""
import hashlib
import json
import time
from collections import Counter

from p1star_foundation.exact import I
from p1star_foundation.guards import Deadline
from p1star_foundation.solver import Status
from .operators import Arena, quadrature, formal_log
from .eligibility import eligibility
from .conditions import Conditions, exact_values, recheck
from .screen import known_screen


def run_pipeline(spec,settings):
    """Generic API: callers own approval/guard boundary. Never retries.

    Technical tests pass ONLY artificial factors/short words here. Science must
    use the separate authorized, supervised entrypoint, not this low-level API.
    """
    deadline=Deadline(settings['wall_seconds'])
    stages=[];started=time.monotonic()
    result={'status':'INCONCLUSIVE','formal_consistent':False,'science_adopted':False,
            'attempts':1,'stages':stages,'primary_domain':'full Fock',
            'sector_failure_implies_general_sector_no_go':False}
    arena=Arena(len(spec['word']),settings['terms'],settings['trace_events'],deadline.check)
    def stage(name):
        deadline.check();stages.append({'stage':name,'elapsed_seconds':time.monotonic()-started})
    try:
        stage('EXACT_INPUT_ELIGIBILITY')
        gate,factors=eligibility(spec['matrices'],arena,spec['particles'])
        result['eligibility']=gate
        if not gate['passed']:
            result['reason']='input eligibility failed; no change of factors/sector permitted'
            return result
        primitives={name:quadrature(factors[index],axis) for name,(index,axis) in spec['primitives'].items()}
        squares=[factor.multiplied(factor) for factor in factors]
        target=squares[0].plus(squares[1]).shifted(2,-I)
        # Tests may explicitly supply a different toy target, never science.
        if spec.get('artificial_target_factor') is not None:
            if spec.get('purpose')!='ARTIFICIAL_ONLY':raise ValueError('toy target override outside artificial fixture')
            target.close();target=squares[spec['artificial_target_factor']].shifted(2,-I)
        stage('FORMAL_LOG')
        logarithm=formal_log(primitives,spec['word'],spec['order'])
        stage('FULL_FOCK_COEFFICIENT_CONDITIONS')
        with Conditions(logarithm,target,spec['order']) as conditions:
            result['coefficient_conditions']=conditions.record()
            result['conditions_sha256']=conditions.digest()
            result['condition_categories']=dict(Counter(r.category for r in conditions.rows))
            stage('ONE_EXACT_SOLVER_CALL')
            remaining_ms=max(1,int(deadline.remaining()*1000))
            decision=conditions.solve(spec['boxes'],min(settings['solver_timeout_ms'],remaining_ms),settings.get('solver_rlimit'))
            result['solver']=decision.record()
            deadline.check()
            if decision.status==Status.UNKNOWN:
                result['reason']='exact backend UNKNOWN: '+decision.reason;return result
            if decision.status==Status.UNSAT:
                result.update(status='NO_SOLUTION_IN_FIXED_ANSATZ',reason='trusted solver UNSAT over exactly the recorded equations and closed real box; no independent certificate')
                return result
            stage('EXACT_WITNESS_RECHECK')
            if not recheck(conditions,decision,spec['boxes']):
                result['reason']='driver exact witness substitution failed';return result
            result['formal_consistent']=True
            result['driver_exact_recheck']=True
            stage('BOUNDED_KNOWN_CONSTRUCTION_SCREEN')
            variables,_=conditions.ast()
            values=exact_values(variables,decision.witness)
            screen=known_screen(spec['primitives'],spec['word'],values,spec.get('selection_evidence'))
            result['known_screen']=screen
            if screen['matches']:
                result.update(status='KNOWN_CONSTRUCTION_ONLY',reason='formal consistency with a literal known-construction correspondence')
            else:
                result['reason']='formal consistency only; novelty/CAR-dependent selection requires separate authorized interpretation'
            # Never manufacture NONTRIVIAL_FORMAL_CANDIDATE from a failed screen.
            return result
    except Exception as error:
        result.update(status='INCONCLUSIVE',reason=type(error).__name__+': '+str(error))
        return result
    finally:
        events=arena.trace.events
        result['trace']={'events':events,'count':len(events),
                         'sha256':hashlib.sha256(json.dumps(events,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                         'interpretation':'transformation log, not an independently checked proof'}
        result['managed_term_peak']=arena.ledger.peak
        result['native_terms_counted']=False
        arena.close()
        result['managed_terms_after_cleanup']=arena.ledger.live
        result['elapsed_seconds']=time.monotonic()-started
