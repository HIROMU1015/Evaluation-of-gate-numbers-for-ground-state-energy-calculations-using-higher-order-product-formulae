"""Reproduce identity-only H4 checks and synthetic action counts; no truth reader."""
from pathlib import Path
import ast,json,sys
import numpy as np
import scipy
from phase06_contract import load_contract,ExecutionContext,expected_counts,sha,canonical
from phase06_inputs import load_phase_a_inputs,synthetic_inputs
from phase06_phase_a import execute_phase_a
from phase06_freeze import code_identity,validate_artifact

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def synthetic_fixture():
    rng=np.random.default_rng(20261029);groups=[]
    for _ in range(13):
        x=rng.normal(size=(10,10))+1j*rng.normal(size=(10,10))
        groups.append((x+x.conj().T)/26)
    psi=rng.normal(size=10)+1j*rng.normal(size=10)
    psi/=np.linalg.norm(psi)
    return synthetic_inputs(sum(groups),groups,psi)

def collect():
    contract=load_contract(ROOT)
    production=load_phase_a_inputs(ROOT,contract) # Exactly fifteen allowlisted identities.
    identity=production.identity_audit
    H=np.diag([0.,1.,2.]).astype(complex) # Synthetic, unrelated to production.H.
    cases=[('nominal_rank8',synthetic_fixture(),8,False),
        ('prefix_stop_rank1',synthetic_inputs(H,[H/13]*13,np.sqrt([.9,.1,0.])),1,True),
        ('zero_rank',synthetic_inputs(H,[H/13]*13,np.array([1.,0.,0.])),0,True)]
    counts=[];schema=json.loads((HERE/'phase_a_schema.json').read_bytes())
    for name,data,rank,stopped in cases:
        context=ExecutionContext('synthetic')
        payload,_=execute_phase_a(data,contract,context,code_identity(HERE))
        validate_artifact(payload,schema)
        assert payload['basis']['actual_rank']==rank
        assert context.counts==expected_counts(rank,stopped)
        counts.append({'fixture':name,'domain':'synthetic','dimension':len(data.psi),
            'group_count':13,'actual_rank':rank,'prefix_stopped':stopped,
            'expected':expected_counts(rank,stopped),'implemented':context.counts,
            'first_pass_actions':payload['cost']['first_pass_actions'],
            'cold_replay_increment':payload['cost']['cold_replay_increment'],
            'cache_isolation_passed':payload['replay']['cache_isolation_passed'],
            'all_counts_match':True,'production_science_actions':context.science})
    inherited=json.loads((ROOT/'artifacts/pf_first_study_response_pilot_phase05_20261006/expected_action_counts.json').read_bytes())
    nominal=counts[0]['implemented']
    compared={key:nominal[key]==value for key,value in inherited['joint_all_m_with_cold_replay'].items() if key in nominal}
    assert all(compared.values())
    imports={}
    for path in [HERE/'phase06_inputs.py',HERE/'phase06_phase_a.py',HERE/'phase06_backend.py',HERE/'phase06_kernels.py']:
        tree=ast.parse(path.read_text())
        modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert 'phase06_phase_b' not in modules
        imports[path.name]=modules
    loader_tree=ast.parse((HERE/'phase06_inputs.py').read_text())
    assert not any(isinstance(n,ast.MatMult) for n in ast.walk(loader_tree))
    expm_tree=ast.parse(__import__('inspect').getsource(scipy.linalg.expm))
    forbidden_calls=[n.func.attr for n in ast.walk(expm_tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('eig','eigh','schur')]
    assert forbidden_calls==[]
    return {'production_identity':identity,'action_counts':counts,
        'nominal_comparison_with_frozen_phase05':compared,
        'phase_a_module_imports':imports,'allowlist_loader_has_no_matrix_products':True,
        'scipy_expm_source_sha256':sha(__import__('inspect').getsource(scipy.linalg.expm).encode()),
        'scipy_expm_eig_eigh_schur_calls':forbidden_calls,
        'versions':{'numpy':np.__version__,'scipy':scipy.__version__},
        'science_action_count':0,'production_truth_access_count':0}

if __name__=='__main__':
    result=collect()
    print(json.dumps({'source_identity_passed':result['production_identity']['status']=='passed',
        'synthetic_counter_cases':[r['fixture'] for r in result['action_counts']],
        'all_action_counts_match':all(r['all_counts_match'] for r in result['action_counts']),
        'science_action_count':0,'production_truth_access_count':0},indent=2))
