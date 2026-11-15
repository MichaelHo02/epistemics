"""Finalize exact reviewed data; no API calls, dotenv access, or model evaluation.

Supplemental rows must already have explicit semantic approvals. This program
checks provenance and hashes; it never grants a scientific or language approval.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from epistemics_dataset.openai_eval import preflight, initial_messages, revision_messages, wrong_option
from epistemics_dataset.seeds import digest

CONTENT = ('sample_id', 'source_url', 'passage_en', 'passage_zh', 'passage_vi')
GATES = ('question_review', 'support_review', 'reuse_review', 'language_review')


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def finalize(candidate, raw_translations, reviewed_files, config_path, output):
    cases = read(candidate / 'main-cases.jsonl')
    source = {r['sample_id']: r for r in read(candidate / 'evidence-reviewed-and-pending.jsonl')}
    raw_rows = read(raw_translations)
    raw = {r['sample_id']: r for r in raw_rows}
    reviewed_rows = [r for path in reviewed_files for r in read(path)]
    reviewed = {r['sample_id']: r for r in reviewed_rows}
    pending = {sid for sid, r in source.items() if not r.get('approved_for_experiment')}
    if len(raw) != len(raw_rows) or len(reviewed) != len(reviewed_rows):
        raise ValueError('Repeated supplemental translation/review IDs')
    if set(reviewed) != pending or set(raw) != pending:
        raise ValueError('Supplemental review must cover exactly every pending family')
    if len(cases) != 300 or len({c['sample_id'] for c in cases}) != 300:
        raise ValueError('Need300unique question families')
    final = []
    provenance = []
    for case in cases:
        sid = case['sample_id']
        previous = source[sid]
        row = reviewed[sid] if sid in pending else previous
        if sid in pending:
            generated = raw[sid]
            if generated['question_hash'] != digest(case):
                raise ValueError('Generated translation question mismatch: ' + sid)
            if any(row.get(k) != previous.get(k) or generated.get(k) != previous.get(k)
                   for k in ('source_url', 'passage_en')):
                raise ValueError('Unreviewed English/source change: ' + sid)
            changes = {k: {'before': generated[k], 'after': row[k]}
                       for k in ('passage_zh', 'passage_vi') if generated[k] != row[k]}
            if changes and not (row.get('translation_corrections') and row.get('correction_reviewer')):
                raise ValueError('Translation correction lacks explicit attribution: ' + sid)
            provenance.append({'sample_id': sid, 'translation_id': generated['translation_id'],
                               'translation_join_id': generated['translation_join_id'],
                               'raw_content_hash': digest({k: generated[k] for k in CONTENT}),
                               'final_content_hash': digest({k: row[k] for k in CONTENT}),
                               'reviewer_corrections': changes,
                               'correction_reviewer': row.get('correction_reviewer')})
        if (row.get('approved_for_experiment') is not True or not row.get('reviewer')
                or any(row.get(k) != 'approved' for k in GATES)
                or row.get('reviewed_question_hash') != digest(case)
                or row.get('reviewed_content_hash') != digest({k: row.get(k) for k in CONTENT})):
            raise ValueError('Missing approval or stale hash: ' + sid)
        final.append(row)
    config = json.loads(config_path.read_text())
    config.update(candidate_hash=digest(cases), dataset_directory=str(output), evidence_file='evidence-reviewed.jsonl')
    readiness = preflight(cases, final, config)
    # Model selection is deliberately outside this data-preparation goal.
    if readiness['ready_questions'] != 300 or set(readiness['blocking_reasons']) != {'model_not_selected'}:
        raise ValueError('Unexpected readiness blockers: ' + json.dumps(readiness))
    placeholder = '{"choice":"UNKNOWN","confidence":0}'
    initial_count = revision_count = 0
    for case, evidence in zip(cases, final):
        assert wrong_option(case, config['wrong_option_salt']) != case['answer']
        for language in ('en', 'zh', 'vi'):
            messages = initial_messages(case, language)
            assert len(messages) == 2
            initial_count += 1
            for advice in ('neutral', 'correct', 'wrong'):
                for source_language in (None, 'en', 'zh', 'vi'):
                    messages = revision_messages(case, language, placeholder, advice,
                                                 source_language, evidence, config['wrong_option_salt'])
                    assert messages[2] == {'role': 'assistant', 'content': placeholder}
                    assert evidence['source_url'] not in messages[-1]['content']
                    assert case['sample_id'] not in messages[-1]['content']
                    revision_count += 1
    assert (initial_count, revision_count) == (900, 10800)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Final directory is not empty; never overwrite an approved snapshot')
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [('main-cases.jsonl', cases), ('evidence-reviewed.jsonl', final),
                       ('supplemental-translation-provenance.jsonl', provenance)]:
        (output / name).write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows))
    (output / 'data-readiness.json').write_text(json.dumps(dict(readiness,
        dataset_ready=True, prompt_construction_counts={'initial':initial_count, 'revision':revision_count},
        prompt_check_used_placeholder_only=True, model_evaluation_calls=0), indent=2) + '\n')
    (output / 'evaluation-config.json').write_text(json.dumps(config, indent=2) + '\n')
    manifest = {'candidate_hash': digest(cases), 'questions':300,
        'subject_counts':dict(Counter(c['subject'] for c in cases)),
        'upstream_label_counts':dict(Counter(c['cultural_sensitivity_label'] for c in cases)),
        'approved_questions':300, 'question_language_rows':900, 'evidence_language_rows':900,
        'review_type':'assistant_source_and_multilingual_review_not_blinded_independent_human_review',
        'model_evaluation_calls':0, 'network_calls_during_finalization':0,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--raw-translations', type=Path, required=True)
    parser.add_argument('--reviewed', type=Path, nargs='+', required=True)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1]/'configs/openai-eval.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(finalize(args.candidate, args.raw_translations, args.reviewed, args.config, args.output), indent=2))
