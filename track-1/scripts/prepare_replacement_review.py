"""Prepare a source-verified reserve review bundle without changing the main set.

This is a local data check: no API calls, no label changes, no automatic approvals.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from epistemics_dataset.global_mmlu import align, answer_agrees, complete, select
from epistemics_dataset.pipeline import write_jsonl
from epistemics_dataset.seeds import digest


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def prepare(config_path, snapshot, dataset, review_file, output):
    import pyarrow.parquet as pq

    config = json.loads(config_path.read_text())
    root = Path(__file__).resolve().parents[1]
    development_ids = set(json.loads((root / config['exclude_ids_file']).read_text())['sample_ids'])
    for name, expected in config['sha256'].items():
        if hashlib.sha256((snapshot / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Source checksum mismatch: ' + name)
    indexes = align({lang: pq.read_table(snapshot / lang / 'test-00000-of-00001.parquet').to_pylist()
                     for lang in config['languages']}, allow_answer_disagreements=True)
    original = read_rows(dataset / 'main-cases.jsonl')
    manifest = json.loads((dataset / 'preparation-manifest.json').read_text())
    if digest(original) != manifest['candidate_hash']:
        raise ValueError('Original selection no longer matches its manifest')
    expected = select(indexes, dict(config, exclude_ids=list(development_ids)))
    if original != expected:
        raise ValueError('Original cases differ from deterministic pinned source selection')
    reviews = read_rows(review_file)
    by_id = {r['sample_id']: r for r in reviews}
    original_ids = {c['sample_id'] for c in original}
    if len(by_id) != len(reviews) or set(by_id) != original_ids:
        raise ValueError('Review IDs must cover the original selection exactly once')
    holds = [c for c in original if by_id[c['sample_id']]['evidence_status'] == 'hold']
    needed = Counter(c['subject'] for c in holds)
    reserves = []
    for subject in config['subjects']:
        eligible = [r for r in indexes['en'].values()
                    if r['subject'] == subject and r['cultural_sensitivity_label'] == config['cultural_sensitivity_label']
                    and r['sample_id'] not in development_ids and complete(indexes, r['sample_id'])
                    and answer_agrees(indexes, r['sample_id'])]
        eligible.sort(key=lambda r: hashlib.sha256((config['selection_salt'] + r['sample_id']).encode()).hexdigest())
        for rank, row in enumerate(eligible, 1):
            sid = row['sample_id']
            if sid in original_ids:
                continue
            case = dict(original[0], sample_id=sid, subject=subject, answer=row['answer'],
                        languages={lang: index[sid] for lang, index in indexes.items()},
                        cultural_sensitivity_label=row['cultural_sensitivity_label'],
                        evidence_status='not_collected', language_review_status='pending')
            reserves.append({'rank_within_subject': rank, 'case': case})
    recorded = read_rows(dataset / 'replacement-queue.jsonl')
    generated = [{'sample_id': r['case']['sample_id'], 'subject': r['case']['subject'],
                  'rank_within_subject': r['rank_within_subject']} for r in reserves]
    if recorded != generated:
        raise ValueError('Saved reserve order differs from the pinned deterministic ranking')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new output folder; existing review bundles are preserved')
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / 'reserve-cases.jsonl', reserves)
    hold_ledger = [{'sample_id': c['sample_id'], 'subject': c['subject'],
                    'decision': 'held_pending_adjudication', 'reason': by_id[c['sample_id']]['review_note'],
                    'original_question_hash': digest(c), 'model_outcomes_seen': False} for c in holds]
    write_jsonl(output / 'original-hold-ledger.jsonl', hold_ledger)
    selected = Counter()
    proposed = []
    for row in reserves:
        sub = row['case']['subject']
        if selected[sub] < needed[sub]:
            proposed.append(dict(row, decision='pending_question_source_and_language_review',
                                 approved_for_experiment=False))
            selected[sub] += 1
    if selected != needed:
        raise ValueError('Not enough reserve candidates to cover holds')
    write_jsonl(output / 'first-reserve-candidates.jsonl', proposed)
    report = {'status': 'replacement_review_pending', 'original_candidate_hash': digest(original),
              'review_input_hash': digest(reviews), 'original_questions': len(original),
              'holds_by_subject': dict(needed), 'held_questions': len(holds),
              'reserve_questions': len(reserves), 'first_reserve_candidates': len(proposed),
              'replacements_applied': 0, 'api_calls': 0,
              'policy': 'Review reserves in saved within-subject order. Log every rejection and its reason. '
                        'Original holds are not all proven key errors. No selection or label is changed by this script.'}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'configs/global-mmlu-main.json')
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--reviews', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.config, args.snapshot, args.dataset, args.reviews, args.output), indent=2))
