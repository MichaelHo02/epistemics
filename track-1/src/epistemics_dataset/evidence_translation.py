"""Translate supporting evidence with Adaption's dataset API; never invent questions.

Draft translation is separate from source, question and bilingual approval. Stable
content IDs and provider join metadata must agree; positional pairing is forbidden.
"""
import argparse
from collections import Counter, defaultdict
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path

from .adaptive_data import plain, price, save, wait
from .pipeline import read_jsonl, write_jsonl
from .seeds import digest

WORKFLOW = 'evidence-translation-v1'
LANGUAGES = {'original': 'en', 'en': 'en', 'zh-Hans': 'zh', 'zh': 'zh', 'vi': 'vi'}


def prepare(config):
    cases_path = Path(config['cases_file'])
    evidence_path = Path(config['evidence_file'])
    for path, expected in ((cases_path, config['cases_sha256']),
                           (evidence_path, config['evidence_sha256'])):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Translation input checksum mismatch: ' + path.name)
    cases = read_jsonl(cases_path)
    evidence = read_jsonl(evidence_path)
    case_ids = [r['sample_id'] for r in cases]
    row_ids = [r['sample_id'] for r in evidence]
    if (len(cases) != config['expected_questions'] or len(set(case_ids)) != len(case_ids)
            or len(set(row_ids)) != len(row_ids) or set(case_ids) != set(row_ids)):
        raise ValueError('Translation inputs require exactly one evidence row per selected question')
    if digest(cases) != config['candidate_hash']:
        raise ValueError('Translation question selection differs from pinned candidate hash')
    by_id = {r['sample_id']: r for r in evidence}
    materials = []
    for case in cases:
        row = by_id[case['sample_id']]
        if row.get('evidence_status') == 'hold' or not all(
                isinstance(row.get(k), str) and row[k].strip() for k in ('source_url', 'passage_en')):
            raise ValueError('Missing or held English material: ' + case['sample_id'])
        if not config.get('allow_unreviewed_drafts') and row.get('support_review') != 'approved':
            raise ValueError('English support review pending: ' + case['sample_id'])
        item = {'sample_id': case['sample_id'], 'source_url': row['source_url'],
                'passage_en': row['passage_en'], 'question_hash': digest(case)}
        item['translation_id'] = digest(item)
        materials.append(item)
    settings = {k: config[k] for k in ('sdk_version', 'languages', 'sample_rate', 'credit_cap', 'wait_timeout_seconds')}
    if settings['languages'] != ['zh', 'vi'] or settings['sample_rate'] != 1.0:
        raise ValueError('Translate all selected evidence into Simplified Chinese and Vietnamese')
    if settings['sdk_version'] != version('adaption'):
        raise ValueError('Adaption SDK version differs from the committed configuration')
    spec = {'workflow': WORKFLOW, 'candidate_hash': config['candidate_hash'],
            'materials': materials, 'settings': settings}
    return spec, [{'prompt': json.dumps({'sample_id': r['sample_id'], 'translation_id': r['translation_id']},
                                       ensure_ascii=False, sort_keys=True),
                   'completion': r['passage_en']} for r in materials]


def unique_text(row, keys):
    values = {row[k].strip() for k in keys if isinstance(row.get(k), str) and row[k].strip()}
    if len(values) != 1:
        raise ValueError('Missing or conflicting text columns: ' + ','.join(keys))
    return values.pop()


def reconcile(rows, materials):
    """Require explicit IDs, immutable source text, and one consistent three-language join."""
    expected = {r['translation_id']: r for r in materials}
    grouped = defaultdict(list)
    problems = []
    for index, row in enumerate(rows):
        try:
            marker = json.loads(unique_text(row, ('prompt', 'original_prompt', 'enhanced_prompt')))
            tid = marker.get('translation_id')
            source = expected.get(tid)
            if source is None or marker.get('sample_id') != source['sample_id']:
                raise ValueError('Unknown or modified content marker')
            language = LANGUAGES.get(row.get('target_language_code'))
            if language is None:
                raise ValueError('Missing or unsupported provider language code')
            join_id = row.get('translation_join_id')
            if not isinstance(join_id, str) or not join_id.strip():
                raise ValueError('Missing explicit provider translation_join_id')
            text = unique_text(row, ('completion', 'original_completion', 'enhanced_completion'))
            if language == 'en' and text != source['passage_en']:
                raise ValueError('Provider changed original English evidence')
            grouped[tid].append({'language': language, 'text': text, 'join_id': join_id, 'row_index': index})
        except (ValueError, TypeError, AttributeError) as exc:
            problems.append({'row_index': index, 'reason': str(exc)})
    candidates = []
    join_owners = defaultdict(set)
    for tid, entries in grouped.items():
        for entry in entries:
            join_owners[entry['join_id']].add(tid)
    for source in materials:
        tid = source['translation_id']
        entries = grouped.get(tid, [])
        counts = Counter(e['language'] for e in entries)
        joins = {e['join_id'] for e in entries}
        reason = None
        if counts != Counter({'en': 1, 'zh': 1, 'vi': 1}):
            reason = 'Need exactly one original, Chinese and Vietnamese row'
        elif len(joins) != 1 or any(len(join_owners[j]) != 1 for j in joins):
            reason = 'Provider join IDs disagree or combine different source items'
        if reason:
            problems.append({'sample_id': source['sample_id'], 'reason': reason})
            continue
        by_language = {e['language']: e for e in entries}
        candidates.append(dict(source, passage_zh=by_language['zh']['text'], passage_vi=by_language['vi']['text'],
                               translation_join_id=next(iter(joins)),
                               provider_row_indices={lang: e['row_index'] for lang, e in by_language.items()},
                               review_status='pending_bilingual_and_source_review', approved_for_experiment=False))
    report = {'workflow': WORKFLOW, 'input_questions': len(materials), 'raw_rows': len(rows),
              'expected_rows': len(materials) * 3, 'row_count_matches': len(rows) == len(materials) * 3,
              'matched_draft_families': len(candidates), 'lineage_problems': problems,
              'approved_families': 0, 'model_evaluation_calls': 0,
              'note': 'ID consistency does not certify translation meaning, source truth or answer correctness. '
                      'No inferred pairings, generated questions, generated answer keys or automatic approvals.'}
    return report, candidates


def run(config, output_root, client=None):
    spec, upload_rows = prepare(config)
    operation = digest(spec)
    directory = output_root / 'evidence-translation' / operation
    directory.mkdir(parents=True, exist_ok=True)
    state_path = directory / 'state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        'operation': operation, 'workflow': WORKFLOW, 'spec': spec,
        'run_id': os.environ.get('ORX_RUN_ID'), 'commit': os.environ.get('ORX_COMMIT'),
        'approved_families': 0}
    if state.get('operation') != operation or state.get('spec') != spec:
        raise ValueError('Saved translation operation does not match current materials')
    save(state_path, state)
    if client is None:
        from adaption import Adaption
        client = Adaption(max_retries=0, timeout=120.0)
    if not state.get('source_dataset_id'):
        if state.get('upload_in_progress'):
            raise ValueError('Prior upload outcome uncertain; recover dataset ID before another upload')
        upload = directory / 'english-evidence-upload.jsonl'
        write_jsonl(upload, upload_rows)
        state['upload_in_progress'] = True
        save(state_path, state)
        result = client.datasets.upload_file(upload, name='epistemics-evidence-' + operation[:16],
                                             processing_mode='raw',
                                             column_mapping={'prompt': 'prompt', 'completion': 'completion'})
        state['source_dataset_id'] = result.dataset_id
        state['upload_in_progress'] = False
        save(state_path, state)
    timeout = spec['settings']['wait_timeout_seconds']
    wait(client, state['source_dataset_id'], 'english_evidence_upload', timeout, poll_seconds=10)
    if not state.get('translated_dataset_id'):
        estimate = client.datasets.translate(state['source_dataset_id'], sample_rate=1.0,
                                             languages=['zh', 'vi'], estimate=True)
        state['translation_estimate'] = plain(estimate)
        save(state_path, state)
        estimated_rows = plain(estimate).get('estimated_new_rows')
        if estimated_rows is not None and estimated_rows != len(upload_rows) * 2:
            raise ValueError('Provider estimate does not match two translations per evidence passage')
        if price(estimate) > config['credit_cap']:
            raise ValueError('Evidence translation exceeds the committed credit cap; no translation launched')
        result = client.datasets.translate(state['source_dataset_id'], sample_rate=1.0,
                                           languages=['zh', 'vi'], idempotency_key=operation + '-evidence-translate')
        state['translated_dataset_id'] = result.dataset_id
        save(state_path, state)
    wait(client, state['translated_dataset_id'], 'translate_evidence_zh_vi', timeout, poll_seconds=10)
    export = directory / 'multilingual-evidence-raw.jsonl'
    if not export.exists():
        temporary = directory / 'multilingual-evidence-download.tmp'
        client.datasets.download(state['translated_dataset_id'], file_format='jsonl').write_to_file(temporary)
        temporary.replace(export)
    export_hash = hashlib.sha256(export.read_bytes()).hexdigest()
    if state.get('export_sha256') and state['export_sha256'] != export_hash:
        raise ValueError('Downloaded evidence cache changed after the recorded export')
    report, candidates = reconcile(read_jsonl(export), spec['materials'])
    report.update(operation=operation, export_sha256=export_hash,
                  source_dataset_id=state['source_dataset_id'], translated_dataset_id=state['translated_dataset_id'])
    save(directory / 'translation-report.json', report)
    write_jsonl(directory / 'translation-candidates.jsonl', candidates)
    state.update(status='downloaded_pending_review', export_sha256=export_hash)
    save(state_path, state)
    print(json.dumps({'status': state['status'], 'output_path': str(directory),
                      'raw_rows': report['raw_rows'], 'matched_draft_families': len(candidates),
                      'lineage_problem_count': len(report['lineage_problems']),
                      'approved_families': 0, 'model_evaluation_calls': 0}), flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get('ORX_RUN_ID'):
        parser.error('Translation service jobs require the tracked run entry point')
    from dotenv import dotenv_values
    key = os.environ.get('ADAPTION_API_KEY') or dotenv_values(args.env_file).get('ADAPTION_API_KEY')
    if not key:
        parser.error('ADAPTION_API_KEY is not configured')
    os.environ['ADAPTION_API_KEY'] = key
    run(json.loads(args.config.read_text()), args.output_root)


if __name__ == '__main__':
    main()
