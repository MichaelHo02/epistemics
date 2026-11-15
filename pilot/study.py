"""Fresh fictional record benchmark; exact published function bodies via AST."""
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import warnings

from common import API, CFG, ROOT, destination, save

def cases():
    rng = random.Random(CFG['seed'])
    rows = []
    for i in range(CFG['families']):
        codes = rng.sample(range(1000, 10000), 6)
        names = [f'Velor-{i}-{j}' for j in range(5)]
        docs = [f'The dispatch register records station {name} with routing code {code}. '
                f'This code identifies the station during parcel sorting in sector {i}.'
                for name, code in zip(names, codes)]
        false = docs[0].replace(str(codes[0]), str(codes[5]))
        rows.append({'id': f'record-{i}', 'documents': docs, 'support': docs[0],
                     'false': false, 'answer': str(codes[0]), 'wrong': str(codes[5]),
                     'question': f'What is the routing code of station {names[0]}? Return only the four-digit code, or UNKNOWN if it cannot be established.'})
    return rows

def contents(case, condition):
    original = list(case['documents'])
    extra = {'clean': [], 'true_copies': [case['support']] * 2,
             'distractor_copies': [original[1]] * 2, 'false_copies': [case['false']] * 2}[condition]
    result = extra + original if int(case['id'].split('-')[1]) % 2 else original + extra
    assert all(doc in result for doc in original)
    return result

def load_functions():
    import numpy as np
    from rouge_score import rouge_scorer
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    names = {'calculate_similarity', 'calculate_pairwise_rouge', 'calculate_average_score',
             'group_n_gram_filtering', 'k_mean_filtering', 'conflict_query_gpt'}
    source = (ROOT / 'upstream.py').read_text()
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    ns = dict(np=np, rouge_scorer=rouge_scorer, KMeans=KMeans,
              StandardScaler=StandardScaler, cosine_similarity=cosine_similarity,
              progress_bar=lambda items, **kwargs: items)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'published-functions', 'exec'), ns)
    return ns

def main():
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer
    out = destination()
    data = cases()
    save(out / 'cases.json', data)
    source = (ROOT / 'upstream.py').read_bytes()
    save(out / 'provenance.json', {'source': 'https://github.com/HuichiZhou/TrustRAG/blob/main/defend_module.py',
         'sha256': hashlib.sha256(source).hexdigest(), 'adaptations': 'CPU embedding and API adapter; published filter and three consolidation prompt bodies unchanged; fixed retrieval fictional records'})
    funcs = load_functions()
    torch.set_num_threads(2)
    model_id = 'princeton-nlp/sup-simcse-bert-base-uncased'
    revision = '2d82fab19ac3a73a20dd20333d27eb8a52d6e97f'
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    model = AutoModel.from_pretrained(model_id, revision=revision).eval().cpu()
    embeddings = {}
    for text in dict.fromkeys(t for c in data for t in c['documents'] + [c['false']]):
        with torch.no_grad():
            embeddings[text] = model(**tokenizer(text, return_tensors='pt'),
                output_hidden_states=True).hidden_states[-1][0, 0].numpy()
    api = API(out)
    rows = []
    def filtered(docs, policy):
        if policy == 'no_filter':
            return docs
        incoming = list(dict.fromkeys(docs)) if policy == 'dedup_before_filter' else docs
        with warnings.catch_warnings(record=True):
            _, kept = funcs['k_mean_filtering'](np.stack([embeddings[t] for t in incoming]), list(incoming), [], True)
        kept = list(kept)
        if policy == 'retain_one_after_filter':
            for text, count in Counter(docs).items():
                if count > 1 and text not in kept:
                    kept.append(text)
        return kept
    def evaluate(case, docs):
        answers, memory, consolidated = funcs['conflict_query_gpt']([docs], [case['question']], api)
        codes = set(re.findall(r'(?<!\d)\d{4}(?!\d)', answers[0]))
        return {'answer_text': answers[0], 'correct': codes == {case['answer']},
                'false_answer': codes == {case['wrong']}, 'memory': memory[0],
                'consolidated': consolidated[0]}
    with (out / 'measurements.jsonl').open('w') as handle:
        for case in data:
            for condition in CFG['conditions']:
                docs = contents(case, condition)
                for policy in CFG['policies']:
                    kept = filtered(docs, policy)
                    row = {'family': case['id'], 'condition': condition, 'policy': policy,
                           'input': docs, 'kept': kept, 'support_retained': case['support'] in kept,
                           **evaluate(case, kept)}
                    if condition == 'true_copies' and policy == 'published_filter' and case['support'] not in kept:
                        row['restored_support'] = evaluate(case, kept + [case['support']])
                        row['restored_irrelevant'] = evaluate(case, kept + [case['documents'][1]])
                    rows.append(row)
                    handle.write(json.dumps(row) + '\n'); handle.flush()
            print(json.dumps({'event': 'family_complete', 'family': case['id']}), flush=True)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['condition'], row['policy'])].append(row)
    summary = [{'condition': c, 'policy': p, 'n': len(rs),
                'correct': sum(r['correct'] for r in rs),
                'support_retained': sum(r['support_retained'] for r in rs),
                'false_answers': sum(r['false_answer'] for r in rs)} for (c, p), rs in groups.items()]
    result = {'stage': 'complete', 'summary': summary, 'requests': api.calls,
              'usage': api.tokens, 'limits': 'Development synthetic records; conflicting false copies have no authenticated source priority. Not confirmatory or a native retrieval reproduction.'}
    save(out / 'summary.json', result)
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
