"""Identity preflight by default; separate explicit authorization for science."""
from pathlib import Path
import argparse,json
from phase06_contract import load_contract,load_authorization,ExecutionContext,canonical,GateError
from phase06_inputs import load_phase_a_inputs

def main(argv=None):
    parser=argparse.ArgumentParser()
    actions=parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--preflight',action='store_true')
    actions.add_argument('--phase-a',action='store_true')
    actions.add_argument('--phase-b',action='store_true')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--private-output',type=Path)
    parser.add_argument('--freeze-receipt',type=Path)
    args=parser.parse_args(argv)
    contract=load_contract(args.root)
    if args.preflight:
        inputs=load_phase_a_inputs(args.root,contract)
        print(json.dumps(inputs.identity_audit,ensure_ascii=False,indent=2))
        return inputs.identity_audit
    phase='phase-a' if args.phase_a else 'phase-b'
    authorization=load_authorization(args.authorization,phase) # before loader/truth reader
    schema=json.loads(Path(__file__).with_name('phase_a_schema.json').read_bytes())
    if args.phase_a:
        if args.output is None or args.private_output is None:raise GateError('new public/private output paths required')
        from phase06_phase_a import execute_phase_a
        from phase06_freeze import verify_committed_code,write_phase_a_artifact,publish_phase_a
        identities=verify_committed_code(args.root,Path(__file__).parent)
        inputs=load_phase_a_inputs(args.root,contract)
        payload,private=execute_phase_a(inputs,contract,ExecutionContext('production',authorization),identities)
        write_phase_a_artifact(args.output,payload,schema,private,args.private_output)
        receipt=publish_phase_a(args.root,args.output,authorization)
        # Receipt is external to the self-referencing commit; Phase B consumes it.
        with (args.private_output/'freeze_receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
        print(json.dumps(receipt,indent=2))
        return receipt
    if args.freeze_receipt is None or args.output is None or args.output.exists():
        raise GateError('Phase B requires frozen receipt and new output path')
    from phase06_phase_b import run_phase_b
    result=run_phase_b(args.root,json.loads(args.freeze_receipt.read_bytes()),contract,schema,authorization)
    with args.output.open('xb') as f:f.write(canonical(result))
    print(json.dumps({'phase_b_complete':True,'outcome':result['outcome'],'new_direct_truth_count':0}))
    return result

if __name__=='__main__':main()
