"""Exact reuse of foundation normal forms; no new algebraic rewrite rules.

Memoize pure electron and oscillator products, independently of eta/parameters.
Cache maps share the live-term ledger. Cache hits are counted, not re-expanded
into duplicate normalization traces. First derivations retain foundation traces.
"""
import hashlib
import json

from p1star_foundation.algebra import normal_car, weyl_to_xp, word_to_weyl
from p1star_foundation.exact import TermMap


class ProductCache:
    def __init__(self,arena):
        self.arena=arena
        self.electron={};self.oscillator={}
        self.hits={'electron':0,'oscillator':0}
        self.misses={'electron':0,'oscillator':0}

    def car(self,left,right):
        key=(left,right)
        if key in self.electron:
            self.hits['electron']+=1;return self.electron[key]
        self.misses['electron']+=1
        self.arena.trace.begin_input(('cached_electron_product',),{'left':left,'right':right})
        result=normal_car(left+right,self.arena.ledger,self.arena.trace)
        self.electron[key]=result
        return result

    def bus(self,left,right):
        key=(left,right)
        if key in self.oscillator:
            self.hits['oscillator']+=1;return self.oscillator[key]
        self.misses['oscillator']+=1
        self.arena.trace.begin_input(('cached_Weyl_product',),{'left':left,'right':right})
        result=TermMap(self.arena.ledger)
        try:
            with weyl_to_xp(*left,self.arena.ledger,self.arena.trace) as x:
                with weyl_to_xp(*right,self.arena.ledger,self.arena.trace) as y:
                    for (p,q),a in x.items():
                        for (r,s),b in y.items():
                            word=('X',)*p+('P',)*q+('X',)*r+('P',)*s
                            with word_to_weyl(word,self.arena.ledger,self.arena.trace) as converted:
                                for basis,c in converted.items():result.add(basis,a*b*c)
        except BaseException:
            result.close();raise
        self.oscillator[key]=result
        return result

    def record(self):
        rows=[]
        for kind,cache in (('electron',self.electron),('oscillator',self.oscillator)):
            for key,terms in sorted(cache.items()):
                rows.append([kind,key,[[basis,c.record()] for basis,c in sorted(terms.items())]])
        return {'normalization_cache_entries':{'electron':len(self.electron),'oscillator':len(self.oscillator)},
                'hits':dict(self.hits),'misses':dict(self.misses),
                'cache_contents_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                'scope':'pure full-Fock CAR and Weyl products from unchanged foundation; no factor/sector-dependent identities cached',
                'cached_terms_counted_by_TermLedger':True}

    def close(self):
        for cache in (self.electron,self.oscillator):
            for terms in cache.values():terms.close()
            cache.clear()
