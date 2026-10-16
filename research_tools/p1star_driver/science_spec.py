"""Dormant fixed-contract validator. NEVER loaded/run in technical tests.

This is a literal input binding, not evaluated factor operators or a science
input artifact. Actual JSON must be independently frozen in later approval.
"""


def load_science_spec(raw):
    # The caller has already checked human approval, hashes and one-shot marker.
    expected={
        'schema':'P1STAR-A-v1',
        'matrices':[
            [[1,0,0,0],[0,-1,0,0],[0,0,2,0],[0,0,0,-2]],
            [[0,1,0,0],[1,0,1,0],[0,1,0,1],[0,0,1,0]]],
        'particles':2,'order':4,
        'primitives':{'A':[0,'X'],'B':[0,'P'],'C':[1,'X'],'D':[1,'P']},
        'word':['A','B','C','D','A','C','B','D','A','D','B','C'],
        'boxes':[[-1,1]]*12,
    }
    # Equality alone accepts 1.0/True: also enforce the exact JSON integer types.
    import json
    def typed(value):
        if isinstance(value,list):return [typed(v) for v in value]
        if isinstance(value,dict):return {k:typed(v) for k,v in value.items()}
        return [type(value).__name__,value]
    if json.dumps(typed(raw),sort_keys=True)!=json.dumps(typed(expected),sort_keys=True):
        raise ValueError('fixed P1STAR-A-v1 input mismatch; no replacement/sector rescue permitted')
    return {key:value for key,value in raw.items() if key!='schema'}
