"""Controlled extractive briefing audit; common format and equal token lengths."""
import json
import re
from collections import defaultdict
from common import API,CFG,destination,save
from materials import optima,render,score,source,user,validate

def parse_choice(text):
    try:
        v=json.loads(text)
        return v['choice'] if isinstance(v,dict) and isinstance(v.get('choice'),str) else 'INVALID'
    except ValueError:return 'INVALID'

def parse_ids(text,allowed,count):
    try:v=json.loads(text)
    except ValueError:return None
    ids=v.get('ids') if isinstance(v,dict) else None
    if not isinstance(ids,list) or not all(isinstance(i,str) for i in ids):return None
    return ids if len(ids)==count and len(set(ids))==count and set(ids)<=set(allowed) else None

def main():
    data=validate(CFG['seed'],CFG['families']);out=destination();save(out/'cases.json',data);api=API(out)
    lengths={len(api.encoding.encode(render([o]))) for c in data for o in c['options']}
    if len(lengths)!=1:raise AssertionError('Row token lengths differ; stop before live calls')
    rows=[]
    def read(c,p,text):
        response=api.query('Choose using only supplied evidence and requirements. If evidence is insufficient return UNKNOWN. If evidence establishes no feasible option return NONE. Return only JSON with choice (option ID, UNKNOWN or NONE).\n'+user(p)+'\nEvidence:\n'+text)
        choice=parse_choice(response)
        return dict(response=response,choice=choice,**score(c,p,choice))
    with (out/'measurements.jsonl').open('w') as f:
        def record(r):rows.append(r);f.write(json.dumps(r)+'\n');f.flush()
        for c in data:
            for pi,p in enumerate(c['profiles']):
                record(dict(family=c['id'],profile=p['id'],method='full_source',slots=8,**read(c,p,source(c))))
                for k in CFG['slots']:
                    expected=None
                    for method in CFG['methods']:
                        selection=None
                        if method=='lexical':
                            words=set(re.findall(r'\w+',user(p).lower()))
                            ranked=sorted(enumerate(c['options']),key=lambda pair:(-len(words & set(re.findall(r'\w+',render([pair[1]]).lower()))),pair[0]))
                            ids=[o['id'] for _,o in ranked[:k]]
                        else:
                            context={'blind':'User requirements unavailable.','user_aware':user(p),'swapped_profile':user(c['profiles'][1-pi])}[method]
                            prompt=f'Select exactly {k} distinct catalog option IDs to retain in a short briefing. Prefer evidence useful for a decision. Do not answer the decision. Return only JSON with ids, an array of selected IDs.\nRequirements: '+context+'\nCatalog:\n'+source(c)
                            selection=api.query(prompt);ids=parse_ids(selection,[o['id'] for o in c['options']],k)
                        if ids is None:
                            record(dict(family=c['id'],profile=p['id'],method=method,slots=k,selection_invalid=True,selection_response=selection,correct=False));continue
                        # Same source order and renderer for every method; no prose truncation.
                        text=render([o for o in c['options'] if o['id'] in ids]);tokens=len(api.encoding.encode(text))
                        if expected is None:expected=tokens
                        assert tokens==expected
                        record(dict(family=c['id'],profile=p['id'],method=method,slots=k,ids=ids,selection_invalid=False,selection_response=selection,text=text,tokens=tokens,optimum_retained=bool(set(optima(c,p))&set(ids)),**read(c,p,text)))
            print(json.dumps(dict(event='family_complete',family=c['id'])),flush=True)
    groups=defaultdict(list)
    for r in rows:groups[(r['method'],r['slots'])].append(r)
    summary=[dict(method=m,slots=k,n=len(rs),correct=sum(r['correct'] for r in rs),selection_invalid=sum(r.get('selection_invalid',False) for r in rs),optimum_retained=sum(r.get('optimum_retained',False) for r in rs)) for (m,k),rs in groups.items()]
    result=dict(stage='complete',summary=summary,requests=api.calls,usage=api.tokens,primary='User-aware minus blind family-averaged optimum retention at two slots; development diagnostic.',limits='One model, synthetic same-schema tasks conditioned on differing user optima. Extractive option-row selection, not free-form briefing or human benefit. Prompt cache reuse makes repeated cells dependent.')
    save(out/'summary.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
