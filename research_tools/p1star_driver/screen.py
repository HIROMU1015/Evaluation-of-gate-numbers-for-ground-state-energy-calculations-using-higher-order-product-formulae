"""Bounded syntactic known-construction screen. No general novelty oracle."""
import z3


def known_screen(primitives,word,values,selection_evidence=None):
    if len(word)!=len(values):raise ValueError('complete exact segment witness required')
    def zero(value):return z3.is_true(z3.simplify(value==0))
    def opposite(a,b):return zero(a+b)
    active=[];cancellations=[]
    for j,(name,value) in enumerate(zip(word,values)):
        if zero(value):
            cancellations.append({'zero_segment':j});continue
        if active and active[-1][0]==name:
            name0,value0,indices=active.pop()
            total=z3.simplify(value0+value)
            cancellations.append({'merged_identical_generator':indices+[j]})
            if not zero(total):active.append((name0,total,indices+[j]))
        else:active.append((name,value,[j]))
    matches=[]
    if not active:matches.append({'kind':'TRIVIAL_IDENTITY','mapping':'adjacent exact same-generator exponential merging'})
    def rectangle(block):
        if len(block)!=4:return None
        (a,x,_),(b,y,_),(c,z,_),(d,w,_)=block
        if a==c and b==d and a!=b and opposite(x,z) and opposite(y,w):
            pa,pb=primitives[a],primitives[b]
            same=pa[0]==pb[0] and {pa[1],pb[1]}=={'X','P'}
            return {'kind':'SINGLE_FACTOR_QUADRATURE_LOOP' if same else 'KNOWN_GROUP_COMMUTATOR',
                    'chronological_primitives':[a,b,c,d],
                    'amplitudes':[v.sexpr() for _,v,_ in block],
                    'mapping':'U4 U3 U2 U1 = exp(-Y) exp(-X) exp(Y) exp(X)',
                    'scope':'exact word correspondence; no truncated-order inference'}
        return None
    whole=rectangle(active)
    if whole:matches.append(whole)
    elif active and len(active)%4==0:
        blocks=[rectangle(active[j:j+4]) for j in range(0,len(active),4)]
        if all(blocks):matches.append({'kind':'CONCATENATED_KNOWN_LOOPS','blocks':blocks,
                                     'scope':'literal concatenation, no reordering or independence asserted'})
    evidence=selection_evidence or {}
    selection={'stage':evidence.get('stage','POSTHOC_NORMAL_ORDERING_ONLY'),
               'constraint_ids':evidence.get('constraint_ids',[]),
               'explanation':evidence.get('explanation','CAR used to normalize; parameter-selection mechanism not supplied'),
               'independently_validated':False}
    if selection['stage'] not in {'POSTHOC_NORMAL_ORDERING_ONLY','CAR_PARAMETER_SELECTION_CLAIM'}:
        raise ValueError('unknown CAR selection provenance')
    return {'matches':matches,'cancellations':cancellations,'car_selection':selection,
            'general_novelty_decided':False,'no_match_means_novel':False,
            'scope':'adjacent merging plus literal four-pulse rectangles/concatenations only; no cyclic/reordered equivalence search'}
