"""Unchanged pinned truth kernels; their guard accepts genuine v3 evidence.

Extract function ASTs without importing the original v2 dispatch/controller.
No v2 proof is fabricated, and no arithmetic statement is transformed.
"""
import ast
import json
from pathlib import Path
import sys
from b0_common import ROOT,R01,R0,A0,sha,canonical,require_proof

KERNEL_NAMES={'load_truth_source','native_unitary','save_checkpoint','load_checkpoint'}

def kernel_ast(raw):
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in KERNEL_NAMES]
    if {n.name for n in nodes}!=KERNEL_NAMES:raise ValueError('pinned truth kernel interface changed')
    return ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))

def gate(proof,context,dimension=None):
    require_proof(proof)
    context.guard(dimension)
    if context.phase not in ('synthetic','FS-R1-Phase-B'):raise PermissionError('truth-only v3 context required')
    if context.proof.digest!=proof.digest:raise PermissionError('context/freeze proof mismatch')

def helpers(proof,context):
    gate(proof,context)
    import io,pickle,resource,time,numpy as np
    sys.path.insert(0,str(ROOT/R0));sys.path.insert(0,str(ROOT/R01))
    import source_io,backend
    from branch_math import fail,normalized,validate_branch_id
    path=ROOT/R01/'truth_executor.py';raw=path.read_bytes()
    namespace=dict(ROOT=ROOT,R0=ROOT/R0,Path=Path,sha=sha,canonical=canonical,gate=gate,
        np=np,io=io,pickle=pickle,resource=resource,time=time,sys=sys,json=json,
        source_io=source_io,v1_backend=backend,fail=fail,normalized=normalized,validate_branch_id=validate_branch_id)
    exec(compile(kernel_ast(raw),str(path),'exec',dont_inherit=True),namespace)
    return namespace

def load_source(spec,proof,context):
    gate(proof,context,spec['dimension']) # Synthetic/B0 cannot open 1568 oracle.
    return helpers(proof,context)['load_truth_source'](spec,proof,context)

def unitary(source,t,proof,context):
    gate(proof,context,source['hamiltonian'].shape[0])
    return helpers(proof,context)['native_unitary'](source,t,proof,context)

def checkpoint(path,vector,row,proof,context,lease):
    gate(proof,context,len(vector))
    # These two kernels use only context.guard, never a protocol-shaped proof.
    metadata=helpers(proof,context)['save_checkpoint'](path,vector,row,context)
    from run_lease import durable
    binding=dict(checkpoint=metadata,RUN_STARTED_sha256=lease.start_sha256,binding=lease.binding,
        phase_a_proof_sha256=proof.digest)
    raw=canonical(binding);binding_path=Path(str(path)+'.binding.json')
    durable(binding_path,raw);durable(Path(str(binding_path)+'.sha256'),(sha(raw)+'\n').encode())
    return metadata

def previous(metadata,source,index,t,proof,context,lease):
    path=Path(metadata['private_path']);bp=Path(str(path)+'.binding.json');raw=bp.read_bytes()
    binding=json.loads(raw)
    if (sha(raw)!=Path(str(bp)+'.sha256').read_text().strip() or canonical(binding)!=raw or
        binding['checkpoint']!=metadata or binding['RUN_STARTED_sha256']!=lease.start_sha256 or
        binding['binding']!=lease.binding or binding['phase_a_proof_sha256']!=proof.digest):
        raise ValueError('private selected-vector checkpoint binding mismatch')
    return helpers(proof,context)['load_checkpoint'](metadata,source,index,t,context)
