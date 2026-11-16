import json
from collections import defaultdict
from common import API,CFG,destination,save
from materials import LABELS,prompt,validate

def parse(text):
    try:v=json.loads(text)
    except ValueError:return 'INVALID'
    return v['verdict'] if isinstance(v,dict) and v.get('verdict') in LABELS else 'INVALID'

def main():
    data=validate();out=destination();save(out/'cases.json',data);api=API(out);rows=[]
    with (out/'measurements.jsonl').open('w') as f:
        for c in data:
            for method in CFG['methods']:
                instruction=prompt(c)
                if method=='interval_reminder':
                    instruction+='\nReason by computing the lowest possible change (current lower minus previous upper) and highest possible change (current upper minus previous lower); compare the resulting interval with the claim band. Use exact arithmetic.'
                response=api.query(instruction);label=parse(response)
                # Cheap deterministic calculator receives exactly the same supplied values
                # and precision rules, with no external or private gold evidence.
                delta=round(float(c['after'])-float(c['before']),1)
                naive='ENTAILED' if delta==float(c['claim']) else 'INCOMPATIBLE'
                r=dict(source_row_id=c['id'],month=c['month'],variant=c['variant'],mode=c['mode'],method=method,
                    reference=c['label'],prediction=label,correct=label==c['label'],response=response,
                    false_refutation=label=='INCOMPATIBLE' and c['label']!='INCOMPATIBLE',
                    overclaim_support=label=='ENTAILED' and c['label']=='UNRESOLVED',
                    naive_baseline=naive,naive_correct=naive==c['label'])
                rows.append(r);f.write(json.dumps(r)+'\n');f.flush()
    groups=defaultdict(list)
    for r in rows:groups[(r['method'],r['mode'])].append(r)
    summary=[dict(method=m,mode=p,n=len(rs),correct=sum(r['correct'] for r in rs),
        false_refutations=sum(r['false_refutation'] for r in rs),overclaims=sum(r['overclaim_support'] for r in rs),
        invalid=sum(r['prediction']=='INVALID' for r in rs),naive_correct=sum(r['naive_correct'] for r in rs)) for (m,p),rs in groups.items()]
    result=dict(stage='complete',summary=summary,requests=api.calls,usage=api.tokens,
        deterministic_reference_accuracy=1.0,limits='The interval rule is a deployable exact baseline, not a new method. Three source releases, nine rows; paired synthetic changes/precision modes. Closed tolerance bands are stipulated, not exact ABS rounding tie conventions. Source truth and evidence compatibility differ. Stop novelty framing if only textbook interval arithmetic is measured.')
    save(out/'summary.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
