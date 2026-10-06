"""Science-zero production identity serialization and inherited hash preflight."""
from pathlib import Path
import json,sys,subprocess
from jsonschema import Draft202012Validator
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P06=ROOT/'artifacts/pf_first_study_response_pilot_phase06_preflight_20261006'
sys.path.insert(0,str(P06));sys.path.insert(0,str(HERE))
from phase06_contract import load_contract,canonical,sha,PROTOCOL_SHA
from phase06_inputs import load_phase_a_inputs
from phase06_freeze import code_identity
from retry2_boundary import to_json_native
BASE1='3d7a923f2a8d11aff57a05454eca8e142496833e'

def collect():
    contract=load_contract(ROOT);data=load_phase_a_inputs(ROOT,contract)
    raw=data.identity_audit;native=to_json_native(raw)
    schema=json.loads((P06/'phase_a_schema.json').read_bytes())
    subschema=schema['properties']['source']['properties']['input_array_identities']
    validator=Draft202012Validator(subschema)
    assert not validator.is_valid(raw)
    validator.validate(native)
    encoded=json.dumps(native,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    roundtrip=json.loads(encoded);validator.validate(roundtrip)
    assert canonical(raw)==canonical(native)==canonical(roundtrip)
    old=json.loads((P06/'production_source_identity.json').read_bytes())
    assert canonical(roundtrip)==canonical(old['observed_identity_audit'])
    assert data.metadata==old['molecular_metadata']
    assert contract.protocol['formula_definition']==old['current_m3']
    old_code=json.loads((P06/'preflight_protocol.json').read_bytes())['code_files_sha256']
    assert code_identity(P06)==old_code
    protected={}
    for directory in ('artifacts/pf_first_study_response_pilot_phase05_20261006',str(P06.relative_to(ROOT)),
        'artifacts/pf_first_study_response_pilot_phase_a_h4_20261006_31ffdca3_failed'):
        for p in (ROOT/directory).iterdir():
            if p.is_file():
                path=str(p.relative_to(ROOT));raw_bytes=p.read_bytes()
                committed=subprocess.check_output(['git','-C',str(ROOT),'show',BASE1+':'+path])
                assert raw_bytes==committed;protected[path]=sha(raw_bytes)
    return {'status':'passed','science_action_count':0,'saved_truth_access_count':0,
        'raw_tuple_old_failure_reproduced':True,'normalized_strict_schema_passed':True,
        'roundtrip_strict_schema_passed':True,'canonical_bytes_unchanged':True,
        'source_sha256_before':sha(canonical(raw)),'source_sha256_after':sha(canonical(roundtrip)),
        'protocol_sha256':PROTOCOL_SHA,'phase06_science_code_and_schema_unchanged':True,
        'group_order_pairing_hashes_unchanged':True,'array_identity_count':len(roundtrip['arrays']),
        'identity':roundtrip,'phase06_code_sha256':old_code,'protected_file_hashes':protected,
        'normalization_module_sha256':sha((HERE/'retry2_boundary.py').read_bytes())}

if __name__=='__main__':
    result=collect()
    print(json.dumps({k:result[k] for k in ('status','science_action_count','saved_truth_access_count',
        'array_identity_count','source_sha256_before','source_sha256_after')},indent=2))
