"""Explicit future science entrypoint. Not invoked by this technical task.

No scientific input is opened until separate approval and frozen hashes match.
Import has no scientific side effects. Receipts are human attestations, not
cryptographic authorization; a JSON flag alone never substitutes user approval.
"""
import argparse
import json
from pathlib import Path

from .authorization import (SCIENCE_ACTION, ApprovalRequired, canonical, check_approval,
                            code_digest, consume_once, read_frozen_input, sha256)
from .practical import validate_settings, supervise


CONTRACT_PATH='docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md'
CONTRACT_SHA256='96f6b22768e2a92944259a44a550cb734cb6f789ee8ea5a9a66193a1994887d6'
ADDENDUM_PATH='docs/research_exploration/p1star_science_driver_20261017/resource_policy_addendum.md'


def validate_plan(plan):
    """Preflight reads approval/environment/resource records, never science input."""
    from p1star_foundation.environment import collect_runtime, require_bound_backend
    root=Path(__file__).resolve().parents[2]
    settings=plan['settings'];validate_settings(settings)
    receipt=plan.get('approval')
    if not receipt or receipt.get('explicit_user_approval') is not True:
        raise ApprovalRequired('separate explicit user approval missing')
    contract=sha256((root/CONTRACT_PATH).read_bytes())
    if contract!=CONTRACT_SHA256:raise ApprovalRequired('original scientific contract changed')
    environment_bytes=Path(plan['environment_record']).read_bytes()
    check_approval(receipt,action=SCIENCE_ACTION,input_sha256=plan['input_sha256'],settings=settings,
                   code_sha256=code_digest(),environment_sha256=sha256(environment_bytes),
                   contract_sha256=contract,addendum_sha256=sha256((root/ADDENDUM_PATH).read_bytes()))
    if settings['terms']>200000:
        recovery=plan.get('execution_campaign_authority',{})
        if recovery.get('repair_and_resume_authorized') is not True or recovery.get('reference')!=receipt['approval_reference']:
            raise ApprovalRequired('larger managed budget requires explicit technical recovery authority')
        path=root/'docs/research_exploration/p1star_phase_b_execution_20261017/resource_recovery_addendum.md'
        if receipt.get('technical_recovery_addendum_sha256')!=sha256(path.read_bytes()):
            raise ApprovalRequired('technical recovery resource addendum hash mismatch')
    require_bound_backend()
    if json.loads(environment_bytes)!=collect_runtime():raise ApprovalRequired('runtime differs from approved environment record')
    if not Path(plan['attempt_directory']).is_dir():raise ApprovalRequired('persistent attempt/lock directory required')
    return settings


def authorized_input(receipt,bindings,input_path,attempt_directory,reader=read_frozen_input):
    """Shared tested boundary; tests use synthetic action, never real input."""
    check_approval(receipt,**bindings)
    consume_once(attempt_directory,receipt)
    return reader(input_path,bindings['input_sha256'])


def execute_approved_worker(plan):
    settings=validate_plan(plan)
    receipt=plan['approval']
    bindings={'action':SCIENCE_ACTION,'input_sha256':plan['input_sha256'],'settings':settings,
              'code_sha256':receipt['code_sha256'],'environment_sha256':receipt['environment_sha256'],
              'contract_sha256':receipt['contract_sha256'],'addendum_sha256':receipt['resource_addendum_sha256']}
    raw=authorized_input(receipt,bindings,plan['input_path'],plan['attempt_directory'])
    # Lazy import and fixed-input validation occur only beyond the approval gate.
    from .science_spec import load_science_spec
    from .pipeline import run_pipeline
    return run_pipeline(load_science_spec(raw),settings)


def main():
    parser=argparse.ArgumentParser(description='One separately approved P1STAR-A-v1 Phase B job; no retries')
    parser.add_argument('--approved-plan',required=True)
    args=parser.parse_args()
    launch_requested=False
    output_cap=512
    try:
        plan_path=Path(args.approved_plan).resolve()
        plan_bytes=plan_path.read_bytes();plan=json.loads(plan_bytes)
        settings=validate_plan(plan)
        output_cap=settings['output_bytes']
        launch_requested=True
        result=supervise(['science',str(plan_path),sha256(plan_bytes)],plan['attempt_directory'],settings)
    except Exception as error:
        result={'status':'INCONCLUSIVE','reason':type(error).__name__+': '+str(error),
                'launch_requested':launch_requested,'retry_permitted':False}
    # The supervisor's captured output plus this envelope must fit approved cap.
    output=canonical(result)
    if len(output)+1>output_cap:
        output=canonical({'status':'INCONCLUSIVE','reason':'final envelope output limit'})
    print(output.decode())


if __name__=='__main__':main()
