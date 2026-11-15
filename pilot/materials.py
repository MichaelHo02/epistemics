"""Independently generated finite decision tasks and exact decision reference."""
import random

def generate(seed, count):
    rng = random.Random(seed)
    families = []
    for i in range(count):
        domain = ['travel service', 'compute booking', 'equipment rental'][i % 3]
        # The cheapest option misses the tight deadline; a mid-price option satisfies it.
        options = [dict(id=f'O{j}', price=30 + j * 17 + rng.randint(0, 5),
                        completion=90 - j * 10, capacity=2 + j % 3) for j in range(6)]
        rng.shuffle(options)
        profiles = [dict(id='tight', deadline=65, minimum_capacity=2),
                    dict(id='flexible', deadline=95, minimum_capacity=2)]
        families.append(dict(id=f'family-{i:02}', domain=domain, options=options, profiles=profiles))
    return families

def optima(case, profile):
    feasible = [o for o in case['options'] if o['completion'] <= profile['deadline']
                and o['capacity'] >= profile['minimum_capacity']]
    if not feasible:
        return ['UNKNOWN']
    price = min(o['price'] for o in feasible)
    return [o['id'] for o in feasible if o['price'] == price]

def source(case):
    return '\n'.join(f"[{o['id']}] {case['domain']} option {o['id']}: price {o['price']} credits; "
        f"completion minute {o['completion']}; capacity {o['capacity']}. "
        f"Catalog note: this option belongs to service group {case['id']}." for o in case['options'])

def user(profile):
    return (f"Choose the lowest-price option completing by minute {profile['deadline']} inclusive, "
            f"with capacity at least {profile['minimum_capacity']}. These constraints are mandatory. "
            'All values are exact; there are no additional preferences.')

def score(case, profile, choice):
    option = next((o for o in case['options'] if o['id'] == choice), None)
    feasible = bool(option and option['completion'] <= profile['deadline']
                    and option['capacity'] >= profile['minimum_capacity'])
    best_ids = optima(case, profile)
    best = next((o['price'] for o in case['options'] if o['id'] in best_ids), None)
    return dict(correct=choice in best_ids, feasible=feasible,
                feasible_regret=(option['price'] - best) if feasible and best is not None else None,
                abstained=choice == 'UNKNOWN', invalid=choice not in [o['id'] for o in case['options']] + ['UNKNOWN'])

def validate():
    for case in generate(82641, 12):
        assert len({o['id'] for o in case['options']}) == 6
        answers = []
        for p in case['profiles']:
            gold = optima(case, p)
            assert gold != ['UNKNOWN']
            assert all(score(case, p, g)['feasible_regret'] == 0 for g in gold)
            for o in case['options']:
                expected = o['completion'] <= p['deadline'] and o['capacity'] >= p['minimum_capacity']
                assert score(case, p, o['id'])['feasible'] == expected
            answers.append(gold)
        assert answers[0] != answers[1]
    # Boundary and ties must be accepted; infeasible choices have no numerical regret.
    c = {'options': [dict(id='A', price=10, completion=65, capacity=2),
                     dict(id='B', price=10, completion=65, capacity=2),
                     dict(id='C', price=1, completion=66, capacity=2)]}
    p = dict(deadline=65, minimum_capacity=2)
    assert optima(c, p) == ['A', 'B']
    assert score(c, p, 'C')['feasible_regret'] is None
    assert score(c, p, 'nonsense')['invalid']

if __name__ == '__main__':
    validate()
    print('PASS: feasible reference, independent feasibility checks, ties, inclusive boundary, invalid choices, profile reversals')
