"""Frozen v2 metadata/pinned v1 utilities; importing this module runs no science."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
R0=ROOT/'artifacts/pf_first_study_fs_r0_rebaseline_20261007'
sys.path.insert(0,str(R0))
import source_io
import backend as v1_backend
import scorer as v1_scorer

def read(name):return json.loads((HERE/name).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return source_io.canonical(value)
def protocol():return read('fs_r1_protocol_v2.json')
def spec_for(condition):
    matches=[s for s in protocol()['systems'] if s['condition']==condition]
    if len(matches)!=1:raise ValueError('fixed condition required')
    return matches[0]
def ladder_for(condition):
    raw=(HERE/'branch_ladder.json').read_bytes()
    if sha(raw)!=protocol()['truth_contract']['ladder_sha256']:raise ValueError('frozen branch ladder hash mismatch')
    return next(s for s in json.loads(raw)['systems'] if s['condition']==condition)

def execution_code_paths():
    import freeze
    core=['r01_common.py','branch_math.py','truth_executor.py','r01_barrier.py','scoring_bridge.py','phase_a_v2.py']
    config=[R0/'fs_r1_protocol.json',R0/'new_source_registry.json',HERE/'branch_ladder.json',HERE/'coordinate_resolution.json']
    return sorted(set(freeze.execution_code_paths()+[str((HERE/n).relative_to(ROOT)) for n in core]+[str(p.relative_to(ROOT)) for p in config]))
