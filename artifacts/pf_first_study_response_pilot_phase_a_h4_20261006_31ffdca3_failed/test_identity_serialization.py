"""Metadata-only regression reproducer; no H4 numeric operations or truth."""
from pathlib import Path
import json,hashlib
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[2]
P06=ROOT/'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'

def identity_and_schema():
    schema=json.loads((P06/'phase_a_schema.json').read_bytes())['properties']['source']['properties']['input_array_identities']
    audit=json.loads((P06/'production_source_identity.json').read_bytes())['observed_identity_audit']
    pairs=audit['ordered_group_identity']
    # Exactly the frozen loader's list(zip(groups, hashes)) representation.
    audit['ordered_group_identity']=list(zip([p[0] for p in pairs],[p[1] for p in pairs]))
    return audit,schema

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def test_frozen_production_identity_python_representation_fails_schema():
    audit,schema=identity_and_schema()
    assert len(audit['ordered_group_identity'])==13
    assert all(isinstance(pair,tuple) for pair in audit['ordered_group_identity'])
    assert not Draft202012Validator(schema).is_valid(audit)

def test_json_identity_representation_passes_without_hash_or_science_change():
    audit,schema=identity_and_schema()
    serialized=json.loads(canonical(audit))
    assert Draft202012Validator(schema).is_valid(serialized)
    assert hashlib.sha256(canonical(audit)).hexdigest()==hashlib.sha256(canonical(serialized)).hexdigest()
