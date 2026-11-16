"""One-line fix ablation: baseline-only, 3 runs, original vs premise-check system prompt."""
import json, os, sys, collections
from concurrent.futures import ThreadPoolExecutor
import run2
KEY=os.environ.get("BRAINTRUST_API_KEY","")
FIX=run2.SYSTEM+(" Before answering, check whether the question's premise is true and whether the answer "
  "could actually be known by anyone. If the premise is false, or the answer is unknowable, speculative, or depends on information not given, your ANSWER must be UNKNOWN.")
its=json.load(open("items3.json"))
bad=("What date is Father","at what age are taxis","Ansel Adams","Great Escape","Parliament Square")
its=[k for k in its if not any(b.lower() in k["question"].lower() for b in bad)]
def one(a):
    m,var,run,k=a
    sysm=run2.SYSTEM if var=="orig" else FIX
    t=run2.chat(m,[{"role":"system","content":sysm},{"role":"user","content":k["question"]}],KEY)
    lab=run2.label(k["kind"],run2.parse(t)[0],k.get("accepted",[]))
    return {"model":m,"var":var,"run":run,"cat":k["category"],"kind":k["kind"],"label":lab,"err":"[ERROR" in t}
jobs=[(m,v,r,k) for m in sys.argv[1].split(",") for v in("orig","fix") for r in range(3) for k in its]
with ThreadPoolExecutor(24) as ex: out=list(ex.map(one,jobs))
json.dump(out,open("ablate_out_%s.json"%sys.argv[1].replace(",","_"),"w"))
for m in sys.argv[1].split(","):
    for cat in ["answerable","future unknown","unsolved problem","counterfactual","false assumption"]:
        row=[]
        for v in("orig","fix"):
            rs=[o for o in out if o["model"]==m and o["var"]==v and o["cat"]==cat and not o["err"] and o["label"]!="unparsed"]
            row.append(f"{sum(o['label']=='correct' for o in rs)/max(1,len(rs)):.2f}(n={len(rs)})")
        print(m.ljust(12),cat.ljust(18),"orig",row[0],"fix",row[1])
