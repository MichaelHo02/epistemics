"""Bounded live benchmark screening pilot; original upstream code is unchanged."""
import os
from pathlib import Path
import shutil
import sys

if sys.version_info < (3, 11):
    os.execv(shutil.which('python3.12'), ['python3.12', __file__])
import json
from dataclasses import replace

root = Path(__file__).resolve().parents[2]
# Local-only secret source: never archived or copied into run artifacts.
secret = Path('/Users/michaelho/.local/share/openresearch/worktrees/08a83207-22c3-4b7f-b392-563ac40777a5/chat_d131fa4d-aaa0-4100-84e7-7c6c70f68f4a/.env')
if not os.environ.get('OPENAI_API_KEY'):
    for line in secret.read_text().splitlines():
        name, sep, value = line.strip().removeprefix('export ').partition('=')
        if sep and name.strip() == 'OPENAI_API_KEY':
            os.environ['OPENAI_API_KEY'] = value.strip().strip('\"\'')
sys.path.insert(0, str(root / 'track-2/vendor/ObligationGuard/src'))
from obligationguard.schema import Instance, parse_prediction
from obligationguard.prompting import identification, render
from obligationguard.backends import ResponsesBackend, decode_json_output

output = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/live-openai-pilot') / os.environ['ORX_RUN_ID']
output.mkdir(parents=True, exist_ok=True)
instances = [Instance.from_dict(json.loads(line)) for line in (root / 'track-2/vendor/ObligationGuard/data/obligationbench.jsonl').read_text().splitlines() if line.strip()]
selected = []
for domain in sorted({x.task_domain for x in instances}):
    for positive in (False, True):
        candidates = [x for x in instances if x.task_domain == domain and bool(x.obligations) == positive]
        selected.append(min(candidates, key=lambda x: (len(identification(x)), x.instance_id)))
config = {'model': 'gpt-4.1-mini-2025-04-14', 'max_output_tokens': 1024, 'max_context_length': 32768, 'timeout': 90, 'parameters': {'temperature': 0}}
backend = ResponsesBackend(config)
manifest = {'config': config, 'commit': os.environ.get('ORX_COMMIT'), 'cases': [x.to_dict() for x in selected], 'selection': 'Shortest complete prompt in each domain-label cell; six cases. Selection-biased screening sample.', 'call_limit': 12, 'limitations': ['No trained ObligationGuard weights evaluated.', 'No verified same-task completed/unfinished pairs.', 'Binary presence scoring only; no semantic obligation matching.', 'Task-only predictions scored against original labels solely as a shortcut diagnostic.']}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('CONFIG ' + json.dumps({k:v for k,v in manifest.items() if k != 'cases'}), flush=True)
records = []
for instance in selected:
    for mode in ('full_trajectory', 'task_only'):
        prompt = identification(instance) if mode == 'full_trajectory' else render('obligation_identification', **{'guard_input.json': {**instance.guard_input(), 'trajectory': []}})
        record = {'instance_id': instance.instance_id, 'domain': instance.task_domain, 'mode': mode, 'gold_positive': bool(instance.obligations)}
        # No retry: any endpoint failure stops further spending and preserves prior responses.
        try:
            completion = backend.complete(prompt)
        except Exception as exc:
            print('ENDPOINT_FAILURE ' + type(exc).__name__, flush=True)
            raise SystemExit(1)
        (output / (instance.instance_id + '-' + mode + '.json')).write_text(json.dumps({'prompt': prompt, 'raw': completion.raw, 'error': completion.error}, indent=2))
        try:
            if completion.error:
                raise ValueError('Incomplete completion')
            obligations = parse_prediction(decode_json_output(completion.text))
            record.update(valid=True, predicted_positive=bool(obligations), correct=bool(obligations) == bool(instance.obligations))
        except Exception:
            record.update(valid=False, correct=False)
        record['usage'] = completion.raw.get('usage', {})
        records.append(record)
        (output / 'records.json').write_text(json.dumps(records, indent=2))
        print('RESULT ' + json.dumps(record), flush=True)
summary = {mode: {'n': 6, 'valid': sum(r['valid'] for r in records if r['mode'] == mode), 'correct': sum(r['correct'] for r in records if r['mode'] == mode)} for mode in ('full_trajectory', 'task_only')}
(output / 'summary.json').write_text(json.dumps(summary, indent=2))
print('FINAL ' + json.dumps(summary), flush=True)
print('ARTIFACT ' + str(output / 'summary.json'), flush=True)
