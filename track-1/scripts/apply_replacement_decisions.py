"""Build a new, unapproved candidate version from an audited reserve prefix.

Retains the old dataset intact. Every skipped reserve must have a logged reason.
This changes candidate selection, never published questions, options or keys.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from epistemics_dataset.pipeline import write_jsonl
from epistemics_dataset.seeds import digest


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def build(dataset, reviews_path, bundle, decisions_path, output):
    original = read(dataset / 'main-cases.jsonl')
    reviews = read(reviews_path)
    audit = json.loads((bundle / 'manifest.json').read_text())
    if digest(original) != audit['original_candidate_hash'] or digest(reviews) != audit['review_input_hash']:
        raise ValueError('Review bundle does not match these original inputs')
    by_id = {r['sample_id']: r for r in reviews}
    if len(by_id) != len(reviews) or set(by_id) != {c['sample_id'] for c in original}:
        raise ValueError('Original review IDs are missing or duplicated')
    reserve_rows = read(bundle / 'reserve-cases.jsonl')
    reserves = {r['case']['sample_id']: r for r in reserve_rows}
    decisions = json.loads(decisions_path.read_text())['decisions']
    decision_ids = [r['sample_id'] for r in decisions]
    if len(set(decision_ids)) != len(decision_ids):
        raise ValueError('Duplicate reserve decisions')
    decisions_by_id = dict(zip(decision_ids, decisions))
    if not set(decision_ids).issubset(reserves):
        raise ValueError('Decision refers to a question outside the saved reserves')
    needs = Counter(c['subject'] for c in original if by_id[c['sample_id']]['evidence_status'] == 'hold')
    kept = defaultdict(list)
    for sid, d in decisions_by_id.items():
        row = reserves[sid]
        if d['rank_within_subject'] != row['rank_within_subject']:
            raise ValueError('Reserve rank mismatch: ' + sid)
        if d['decision'] == 'retain_candidate':
            if not all(d.get(k) for k in ('passage_en', 'source_url', 'review_note')):
                raise ValueError('Retained candidate lacks draft evidence: ' + sid)
            if d.get('approved_for_experiment') is not False:
                raise ValueError('Reserve decisions cannot approve evaluation')
            kept[row['case']['subject']].append(row)
        elif d['decision'] == 'exclude_candidate':
            if not d.get('reason'):
                raise ValueError('Missing reserve exclusion reason: ' + sid)
        else:
            raise ValueError('Unresolved reserve decision: ' + sid)
    if Counter({s: len(rows) for s, rows in kept.items()}) != needs:
        raise ValueError('Retained reserve counts do not cover original holds by subject')
    for sub, rows in kept.items():
        rows.sort(key=lambda r: r['rank_within_subject'])
        last_rank = rows[-1]['rank_within_subject']
        expected_prefix = {r['case']['sample_id'] for r in reserve_rows
                           if r['case']['subject'] == sub and r['rank_within_subject'] <= last_rank}
        reviewed_prefix = {sid for sid in decision_ids if reserves[sid]['case']['subject'] == sub}
        if reviewed_prefix != expected_prefix:
            raise ValueError('A reserve was skipped or reviewed out of prefix order: ' + sub)
    used = Counter()
    selected, evidence, changes = [], [], []
    for c in original:
        review = by_id[c['sample_id']]
        if review['evidence_status'] != 'hold':
            selected.append(c)
            evidence.append(dict(review, approved_for_experiment=False))
            continue
        sub = c['subject']
        new = kept[sub][used[sub]]['case']
        used[sub] += 1
        d = decisions_by_id[new['sample_id']]
        selected.append(new)
        evidence.append({'sample_id': new['sample_id'], 'subject': sub,
                         'question': new['languages']['en']['question'], 'answer_code': new['answer'],
                         'answer_text': new['languages']['en']['option_' + new['answer'].lower()],
                         'source_url': d['source_url'], 'passage_en': d['passage_en'],
                         'passage_zh': None, 'passage_vi': None, 'passage_kind': d['passage_kind'],
                         'review_note': d['review_note'], 'evidence_status': 'draft_supported',
                         'support_review': 'pending', 'question_review': 'pending',
                         'language_review': 'pending', 'reuse_review': 'pending',
                         'approved_for_experiment': False})
        changes.append({'excluded_sample_id': c['sample_id'], 'replacement_sample_id': new['sample_id'],
                        'subject': sub, 'reason': review['review_note'],
                        'exclusion_category': 'unresolved_pre_outcome_quality_hold',
                        'old_question_hash': digest(c), 'new_question_hash': digest(new),
                        'model_outcomes_seen': False})
    if len({c['sample_id'] for c in selected}) != len(original):
        raise ValueError('Replacement produced repeated question IDs')
    if Counter(c['subject'] for c in selected) != Counter(c['subject'] for c in original):
        raise ValueError('Replacement changed subject allocation')
    # All validation precedes writes, and an existing version is never overwritten.
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output is not empty; use a new version directory')
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / 'main-cases.jsonl', selected)
    write_jsonl(output / 'evidence-candidates.jsonl', evidence)
    write_jsonl(output / 'replacement-ledger.jsonl', changes)
    write_jsonl(output / 'reserve-decisions.jsonl', decisions)
    write_jsonl(output / 'question-rows.jsonl', [
        {'sample_id': c['sample_id'], 'language': lang, 'original': row}
        for c in selected for lang, row in c['languages'].items()])
    (output / 'question-review.md').write_text('# Candidate version 2: original multilingual questions\n\n'
        'Unapproved candidate selection. Evidence, answer, reuse and language reviews remain pending.\n\n'
        + '\n\n'.join('## ' + c['sample_id'] + '\n\n' + '\n\n'.join(
            '**' + lang + '**\n\n' + row['question'] + '\n\n' + '\n'.join(
                '- ' + code + '. ' + row['option_' + code.lower()] for code in 'ABCD')
            for lang, row in c['languages'].items()) + '\n\nPublished key: ' + c['answer'] for c in selected) + '\n')
    result = {'status': 'candidate_selection_updated_not_approved', 'questions': len(selected),
              'question_language_rows': len(selected) * 3, 'candidate_hash': digest(selected),
              'original_candidate_hash': digest(original), 'source_review_hash': digest(reviews),
              'reserve_decisions_hash': digest(decisions), 'replacements_applied': len(changes),
              'reserves_reviewed': len(decisions),
              'reserves_excluded': sum(d['decision'] == 'exclude_candidate' for d in decisions),
              'approved_questions': 0, 'api_calls': 0,
              'note': 'Held originals are excluded conservatively before model outcomes; not all have proven key errors. '
                      'Replacement English, source, reuse and multilingual reviews are still pending. Original source records are unchanged.'}
    (output / 'selection-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('dataset', 'reviews', 'bundle', 'decisions', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.dataset, a.reviews, a.bundle, a.decisions, a.output), indent=2))
