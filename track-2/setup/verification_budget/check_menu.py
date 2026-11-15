"""Offline design validation, not an LLM experiment. Standard library only.
Uses DIVA's documented conditional-independent discrete model and DP recurrence.
"""
import argparse
import copy
import gzip
import hashlib
import itertools
import json
from functools import lru_cache
from pathlib import Path

TOL = 1e-7

class Solver:
    def __init__(self, model):
        self.m = model
        self.start = tuple(sorted(tuple(x) for x in model.get('observed', [])))
        self.budget = model['budget']
        self.value = lru_cache(None)(self._value)

    def weights(self, obs):
        w = list(self.m['prior'])
        for i, o in obs:
            w = [p * self.m['items'][i]['lik'][s][o] for s, p in enumerate(w)]
        return w

    def stop(self, obs):
        w = self.weights(obs)
        return max(sum(p*u for p,u in zip(w, act))/sum(w) for act in self.m['utility'])

    def available(self, obs):
        if len(obs)-len(self.start) >= self.budget:
            return []
        done = {i for i, _ in obs}
        return [i for i in range(len(self.m['items'])) if i not in done]

    def q(self, obs, i):
        w = self.weights(obs)
        item = self.m['items'][i]
        value = -item['cost']
        for o in range(len(item['outcomes'])):
            prob = sum(p*item['lik'][s][o] for s,p in enumerate(w))/sum(w)
            if prob:
                value += prob*self.value(tuple(sorted(obs+((i,o),))))
        return value

    def _value(self, obs):
        return max([self.stop(obs)] + [self.q(obs,i) for i in self.available(obs)])

    def moves(self, obs):
        v = self.value(obs)
        moves = ['STOP'] if abs(self.stop(obs)-v)<TOL else []
        return moves + [self.m['items'][i]['label'] for i in self.available(obs) if abs(self.q(obs,i)-v)<TOL]

    def histories(self):
        remaining = [i for i in range(len(self.m['items'])) if i not in {j for j,_ in self.start}]
        for depth in range(self.budget+1):
            for inds in itertools.combinations(remaining,depth):
                for outs in itertools.product(*(range(len(self.m['items'][i]['outcomes'])) for i in inds)):
                    obs=tuple(sorted(self.start+tuple(zip(inds,outs))))
                    if sum(self.weights(obs))>0:
                        yield obs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    rows=[json.loads(x) for x in gzip.open(args.input,'rt')]
    results=[]
    for row in rows:
        original=Solver(row['model'])
        assert abs(original.value(original.start)-row['exact']['dp_value'])<TOL, row['id']
        base=copy.deepcopy(row['model']); base['budget']=3
        extra=copy.deepcopy(base)
        for j in range(4):
            extra['items'].append({'label':f'IRRELEVANT_{j}', 'lik':[[.5,.5] for _ in base['prior']], 'cost':.1,'outcomes':['heads','tails']})
        a,b=Solver(base),Solver(extra)
        # Every possible positive-probability history of ORIGINAL checks within
        # budget, not just the root or the optimal path. Extra checks may still
        # be considered by b in its continuation DP.
        histories=0; max_error=0.
        for obs in a.histories():
            histories+=1
            err=abs(a.value(obs)-b.value(obs)); max_error=max(max_error,err)
            assert err<TOL and a.moves(obs)==b.moves(obs), (row['id'],obs)
        # Positive control: a cheap perfectly informative additional check.
        useful=copy.deepcopy(base)
        k=len(base['prior'])
        useful['items'].append({'label':'PERFECT_CHECK','lik':[[float(s==o) for o in range(k)] for s in range(k)],'cost':.01,'outcomes':[str(s) for s in range(k)]})
        c=Solver(useful)
        results.append({'id':row['id'],'histories_checked':histories,'max_value_error':max_error,'root_moves':a.moves(a.start),'positive_control_gain':c.value(c.start)-a.value(a.start)})
    out={'kind':'offline_design_validation_not_llm_experiment','source_revision':'d3fb499629d8d2420cf943e3d09338d75df373b3','dataset_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'n':len(results),'budget':3,'added_options':4,'added_option_cost':.1,'stored_values_reproduced':len(results),'histories_checked':sum(x['histories_checked'] for x in results),'max_value_error':max(x['max_value_error'] for x in results),'root_stop_optimal':sum('STOP' in x['root_moves'] for x in results),'positive_control_improves':sum(x['positive_control_gain']>TOL for x in results),'results':results,'limitations':['Synthetic finance pilot data; not held-out evaluation.','Conditional independence and stated probabilities are assumed.','All original-check histories validated; not all histories containing added checks.','No LLM behavior, empirical effect, or novelty established.','Independent standard-library DP follows upstream recurrence; not execution of upstream NumPy engine.']}
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='results'}))

if __name__=='__main__':
    main()
