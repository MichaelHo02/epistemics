"""Two-call live model evaluation of a frozen executed pair."""
import os
from pathlib import Path
import shutil
import sys
if sys.version_info < (3, 11):
    os.execv(shutil.which('python3.12'), ['python3.12', __file__])
import hashlib
import json
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'track-2/vendor/ObligationGuard/src'))
from obligationguard.backends import ResponsesBackend, decode_json_output
from obligationguard.schema import Instance, parse_prediction
from obligationguard.prompting import identification
from obligationguard.identifiers import MODEL_TASK_ID

secret = Path('/Users/michaelho/.local/share/openresearch/worktrees/08a83207-22c3-4b7f-b392-563ac40777a5/chat_d131fa4d-aaa0-4100-84e7-7c6c70f68f4a/.env')
if not os.environ.get('OPENAI_API_KEY'):
    for line in secret.read_text().splitlines():
        name, sep, value = line.strip().removeprefix('export ').partition('=')
        if sep and name.strip() == 'OPENAI_API_KEY':
            os.environ['OPENAI_API_KEY'] = value.strip().strip('\"\'')
data = root / 'track-2/pilot/data/credential-pair.jsonl'
manifest = json.loads(data.with_name('credential-pair-manifest.json').read_text())
assert hashlib.sha256(data.read_bytes()).hexdigest() == manifest['dataset_sha256']
instances = [Instance.from_dict(json.loads(line)) for line in data.read_text().splitlines()]
assert len(instances) == 2 and instances[0].task == instances[1].task
out = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/paired-model-pilot') / os.environ['ORX_RUN_ID']
out.mkdir(parents=True, exist_ok=True)
config = {'model':'gpt-4.1-mini-2025-04-14','max_output_tokens':1024,'max_context_length':32768,'timeout':90,'parameters':{'temperature':0}}
print('CONFIG ' + json.dumps({'model':config,'dataset_sha256':manifest['dataset_sha256'],'commit':os.environ.get('ORX_COMMIT'),'call_limit':2}), flush=True)
backend = ResponsesBackend(config)
records = []
for instance in instances:
    prompt = identification(instance)
    try:
        completion = backend.complete(prompt)
    except Exception as exc:
        print('ENDPOINT_FAILURE ' + type(exc).__name__, flush=True)
        raise SystemExit(1)
    (out / (instance.instance_id + '.json')).write_text(json.dumps({'prompt':prompt,'raw':completion.raw,'completion_error':completion.error},indent=2))
    record = {'instance_id':instance.instance_id,'gold_positive':bool(instance.obligations),'usage':completion.raw.get('usage',{})}
    try:
        if completion.error:
            raise ValueError('incomplete response')
        predictions = parse_prediction(decode_json_output(completion.text),MODEL_TASK_ID)
        record.update(valid=True,predicted_positive=bool(predictions),correct=bool(predictions)==bool(instance.obligations),actions=[p.required_safety_action for p in predictions])
    except Exception:
        record.update(valid=False,correct=False)
    records.append(record)
    (out / 'records.json').write_text(json.dumps(records,indent=2))
    print('RESULT ' + json.dumps(record), flush=True)
summary = {'n':2,'valid':sum(r['valid'] for r in records),'binary_correct':sum(r['correct'] for r in records),'both_binary_correct':all(r['correct'] for r in records),'limitations':['One easy controlled pair, explicit cleanup policy.','Not the trained ObligationGuard model.','Binary score does not verify semantic obligation-set correctness.']}
(out / 'summary.json').write_text(json.dumps(summary,indent=2))
print('FINAL ' + json.dumps(summary), flush=True)
print('ARTIFACT ' + str(out / 'summary.json'), flush=True)
