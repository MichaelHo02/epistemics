import json
import re
from collections import defaultdict
from common import API, CFG, destination, save
from materials import generate, optima, score, source, user, validate

def parse(text):
    try:
        value = json.loads(text)
        return value.get('choice', 'INVALID') if isinstance(value, dict) else 'INVALID'
    except (ValueError, TypeError):
        return 'INVALID'

def main():
    validate()
    out = destination()
    data = generate(CFG['seed'], CFG['families'])
    save(out / 'cases.json', data)
    api = API(out)
    rows = []
    def read(case, profile, text):
        prompt = ('Select using only the supplied evidence and user requirements. '
            'If needed information is absent or ambiguous, return UNKNOWN. '
            'Return only JSON with one field choice: option ID or UNKNOWN.\n'
            + user(profile) + '\nEvidence:\n' + text)
        answer = api.query(prompt)
        choice = parse(answer)
        return {'choice': choice, 'response': answer, **score(case, profile, choice)}
    with (out / 'measurements.jsonl').open('w') as handle:
        for case in data:
            src = source(case)
            for profile in case['profiles']:
                full = read(case, profile, src)
                row = {'family': case['id'], 'profile': profile['id'], 'method': 'full_source',
                       'budget': None, 'text': src, **full}
                rows.append(row); handle.write(json.dumps(row) + '\n'); handle.flush()
                for budget in CFG['budgets']:
                    for method in CFG['methods']:
                        if method == 'oracle':
                            gold = optima(case, profile)
                            text = '\n'.join(line for line in src.splitlines() if any('[' + g + ']' in line for g in gold))
                        elif method == 'lexical':
                            words = set(re.findall(r'\w+', user(profile).lower()))
                            lines = sorted(enumerate(src.splitlines()),
                                key=lambda pair: (-len(words & set(re.findall(r'\w+', pair[1].lower()))), pair[0]))
                            selected = []
                            for _, line in lines:
                                if len(api.encoding.encode('\n'.join(selected + [line]))) <= budget:
                                    selected.append(line)
                            text = '\n'.join(selected)
                        else:
                            instructions = {'generic': 'Summarize the catalog faithfully, preserving important facts.',
                                'user_aware': 'Summarize the catalog to support the supplied user decision.',
                                'structured': 'Create a compact evidence-linked briefing of constraints and option attributes. Preserve feasibility information and trade-offs; do not invent missing values.'}[method]
                            context = '' if method == 'generic' else '\nUser requirements: ' + user(profile)
                            text = api.query(instructions + context +
                                f'\nYour briefing must fit {budget} o200k_base tokens. Give only the briefing.\nCatalog:\n' + src)
                        original_tokens = len(api.encoding.encode(text))
                        # Uniform hard delivery cap: no retries or cherry-picking overlength responses.
                        text = api.encoding.decode(api.encoding.encode(text)[:budget])
                        row = {'family': case['id'], 'profile': profile['id'], 'method': method,
                               'budget': budget, 'original_tokens': original_tokens,
                               'delivered_tokens': len(api.encoding.encode(text)),
                               'truncated': original_tokens > budget, 'text': text,
                               **read(case, profile, text)}
                        rows.append(row); handle.write(json.dumps(row) + '\n'); handle.flush()
            print(json.dumps({'event': 'family_complete', 'family': case['id']}), flush=True)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['method'], row['budget'])].append(row)
    summary = [{'method': m, 'budget': b, 'n': len(rs),
                'correct': sum(r['correct'] for r in rs), 'feasible': sum(r['feasible'] for r in rs),
                'abstained': sum(r['abstained'] for r in rs), 'invalid': sum(r['invalid'] for r in rs),
                'truncated': sum(r.get('truncated', False) for r in rs)} for (m, b), rs in groups.items()]
    result = {'stage': 'complete', 'summary': summary, 'requests': api.calls, 'usage': api.tokens,
              'limits': 'Synthetic development tasks, one model; hard maximum budgets rather than equal realized length. Oracle privileged upper bound. No human benefit or stable domain generalization claim.'}
    save(out / 'summary.json', result)
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
