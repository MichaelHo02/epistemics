"""Randomized decision families and independent exact references."""
import random

def feasible(o,p):
    return o['completion']<=p['deadline'] and o['capacity']>=p['minimum_capacity']

def optima(c,p):
    good=[o for o in c['options'] if feasible(o,p)]
    return sorted(o['id'] for o in good if o[p['objective']]==min(v[p['objective']] for v in good)) or ['NONE']

def binding(c,p):
    best=min(o[p['objective']] for o in c['options'] if feasible(o,p))
    cheap=[o for o in c['options'] if o[p['objective']]<best]
    return (any(o['completion']>p['deadline'] and o['capacity']>=p['minimum_capacity'] for o in cheap),
            any(o['completion']<=p['deadline'] and o['capacity']<p['minimum_capacity'] for o in cheap))

def generate(seed,count):
    rng=random.Random(seed); cases=[]
    for i in range(count):
        for attempt in range(50000):
            options=[dict(id=chr(65+j),price=rng.randrange(10,100),completion=rng.randrange(10,100),capacity=rng.randrange(10,100)) for j in range(8)]
            rng.shuffle(options)
            ps=[dict(id='P'+str(j),deadline=rng.randrange(35,86),minimum_capacity=rng.randrange(25,76),objective='price' if i%2==0 else 'completion') for j in range(2)]
            c=dict(id=f'fresh-{i:02}',options=options,profiles=ps)
            if any(optima(c,p)==['NONE'] for p in ps):continue
            if set(optima(c,ps[0])) & set(optima(c,ps[1])):continue
            if i%2==0 and not all(all(binding(c,p)) for p in ps):continue
            if i%2 and not all(binding(c,p)[1] for p in ps):continue
            cases.append(c);break
        else:raise AssertionError('Generation limit reached')
    return cases

def render(options):
    return '\n'.join(f"{o['id']} | price={o['price']} | completion={o['completion']} | capacity={o['capacity']}" for o in options)

def source(c):return render(c['options'])

def user(p):
    return f"Minimize {p['objective']} subject to completion <= {p['deadline']} and capacity >= {p['minimum_capacity']}. Both constraints are mandatory and inclusive. All values are exact."

def score(c,p,choice):
    option=next((o for o in c['options'] if o['id']==choice),None)
    good=bool(option and feasible(option,p));gold=optima(c,p)
    best=next((o[p['objective']] for o in c['options'] if o['id'] in gold),None)
    return dict(correct=choice in gold,feasible=good,abstained=choice=='UNKNOWN',invalid=choice not in [o['id'] for o in c['options']]+['NONE','UNKNOWN'],feasible_regret=option[p['objective']]-best if good else None)

def validate(seed=270416,count=16):
    cs=generate(seed,count);assert cs==generate(seed,count)
    ids=set()
    for c in cs:
        for p in c['profiles']:
            # Independent pairwise dominance reference, no calls to feasible or optima.
            good=[o for o in c['options'] if not(o['completion']>p['deadline'] or o['capacity']<p['minimum_capacity'])]
            ref=sorted(o['id'] for o in good if not any(v[p['objective']]<o[p['objective']] for v in good)) or ['NONE']
            assert ref==optima(c,p);ids.update(ref)
            assert all(score(c,p,g)['feasible_regret']==0 for g in ref)
    assert len(ids)>=5
    c={'options':[dict(id='A',price=10,completion=65,capacity=20),dict(id='B',price=10,completion=65,capacity=20),dict(id='C',price=5,completion=66,capacity=20)]}
    p=dict(objective='price',deadline=65,minimum_capacity=20)
    assert optima(c,p)==['A','B'] and score(c,p,'C')['feasible_regret'] is None
    assert score(c,p,'nonsense')['invalid']
    print('PASS independent reference, deterministic fresh tasks, varied optimum IDs, binding constraints, ties, boundary and invalid answer checks')
    return cs

if __name__=='__main__':validate()
