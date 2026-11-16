"""Exact integer interval oracle with a separately implemented exhaustive check."""
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LABELS=['ENTAILED','INCOMPATIBLE','UNRESOLVED']

def ticks(value):
    from decimal import Decimal
    # 0.05 is one tick; all observed source values have one decimal place.
    n=Decimal(value)*20
    assert n==int(n)
    return int(n)

def verdict(before,after,claim,mode):
    b,a,c=map(ticks,[before,after,claim]);radius=0 if mode=='exact_levels' else 1
    lo,hi=a-b-2*radius,a-b+2*radius
    # The reported change denotes a CLOSED tolerance band of +/-0.05pp.
    # This is an explicit experimental semantics, not a claim about ABS tie-breaking.
    cl,ch=c-1,c+1
    if hi<cl or lo>ch:return 'INCOMPATIBLE'
    if cl<=lo and hi<=ch:return 'ENTAILED'
    return 'UNRESOLVED'

def exhaustive(before,after,claim,mode):
    b,a,c=map(ticks,[before,after,claim]);r=0 if mode=='exact_levels' else 1
    # Endpoints and midpoints suffice for these closed linear intervals. Use half ticks
    # here, independently of analytic subtraction in verdict().
    possible=[y-x for x,y in itertools.product(range(2*(b-r),2*(b+r)+1),range(2*(a-r),2*(a+r)+1))]
    contains=[2*(c-1)<=v<=2*(c+1) for v in possible]
    return 'ENTAILED' if all(contains) else 'INCOMPATIBLE' if not any(contains) else 'UNRESOLVED'

def cases():
    from decimal import Decimal
    rows=json.loads((ROOT/'sources/rows.json').read_text());result=[]
    for ri,row in enumerate(rows):
        for variant,shift in [('published','0.0'),('nearby','0.1'),('far','0.5')]:
            claim=str(Decimal(row['published_change'])+Decimal(shift))
            for mode in ['exact_levels','rounded_levels']:
                result.append(dict(**row,variant=variant,claim=claim,mode=mode,
                    label=verdict(row['before'],row['after'],claim,mode)))
    return result

def prompt(case):
    precision=('The two displayed levels are stipulated exact values.' if case['mode']=='exact_levels' else
        'Each displayed level x denotes any real value in the closed interval [x-0.05, x+0.05].')
    return ('Evaluate only the supplied numerical evidence under the stated experimental contract. '
        'Ignore external knowledge or whether an institution published the claim. '
        'Change is current minus previous, measured in percentage points. '
        +precision+' A claimed change c denotes the closed band [c-0.05,c+0.05]. '
        'ENTAILED means every possible change lies in the claim band; INCOMPATIBLE means no possible change lies in it; '
        'UNRESOLVED means some but not all possible changes lie in it. These are evidence-relative verdicts, not truth labels. '
        'Return only JSON with verdict: ENTAILED, INCOMPATIBLE or UNRESOLVED.\n'
        +f"Series: {case['metric']}, seasonally adjusted. Release reference: {case['month']} 2025.\n"
        +f"Previous level: {case['before']} percent. Current level: {case['after']} percent. Claimed change: {case['claim']} percentage points.")

def validate():
    data=cases();assert len(data)==54
    for c in data:assert c['label']==exhaustive(c['before'],c['after'],c['claim'],c['mode'])
    assert verdict('67.2','67.3','0.2','rounded_levels')=='UNRESOLVED'
    assert verdict('67.2','67.3','0.2','exact_levels')=='INCOMPATIBLE'
    assert verdict('4.0','4.1','0.1','exact_levels')=='ENTAILED'
    assert verdict('4.0','4.1','0.5','rounded_levels')=='INCOMPATIBLE'
    # Precision can alter justified verdict without changing the printed numerals.
    assert any(verdict(c['before'],c['after'],c['claim'],'exact_levels')!=verdict(c['before'],c['after'],c['claim'],'rounded_levels') for c in data)
    print('PASS analytic intervals vs exhaustive reference on all 54 cells, boundary controls and precision reversals')
    return data

if __name__=='__main__':validate()
