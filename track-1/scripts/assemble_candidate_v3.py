import json,sys,collections,hashlib
from pathlib import Path
import pyarrow.parquet as pq
sys.path.insert(0,'track-1/src')
from epistemics_dataset.openai_eval import preflight
from epistemics_dataset.seeds import digest
b=Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main');out=b/'selection-v3'
def read(p):return list(map(json.loads,p.read_text().splitlines()))
groups=[('parallel-biology','main-cases-proposed.jsonl','evidence-reviewed.jsonl'),('parallel-physics-math','proposed-cases.jsonl','evidence-reviewed-and-pending.jsonl'),('parallel-computing','proposed-cases.jsonl','reviewed-evidence.jsonl'),('parallel-astronomy-chemistry','astronomy-proposed-cases.jsonl','astronomy-evidence-reviewed-and-pending.jsonl'),('parallel-astronomy-chemistry','chemistry-proposed-cases.jsonl','chemistry-evidence-reviewed-and-pending.jsonl')]
cs=[];ev=[]
for d,cn,en in groups:cs+=read(b/d/cn);ev+=read(b/d/en)
assert len(cs)==300 and len(ev)==300 and len({c['sample_id'] for c in cs})==300
assert set(c['sample_id'] for c in cs)==set(r['sample_id'] for r in ev)
cf=json.loads(Path('track-1/configs/global-mmlu-main.json').read_text());rank={s:i for i,s in enumerate(cf['subjects'])};cs.sort(key=lambda c:(rank[c['subject']],c['sample_id']));evby={r['sample_id']:r for r in ev};ev=[evby[c['sample_id']] for c in cs]
assert collections.Counter(c['subject'] for c in cs)==collections.Counter({s:30 for s in cf['subjects']})
ex=set(json.loads(Path('track-1/data/seeds/global-mmlu-pilot-ids.json').read_text())['sample_ids']);assert not ex.intersection(c['sample_id'] for c in cs)
snapshot=b.parent/'global-mmlu-pilot/upstream'
for name,sha in cf['sha256'].items():assert hashlib.sha256((snapshot/name).read_bytes()).hexdigest()==sha
ix={l:{r['sample_id']:r for r in pq.read_table(snapshot/l/'test-00000-of-00001.parquet').to_pylist()} for l in cf['languages']}
for c in cs:
 for l in ix:assert c['languages'][l]==ix[l][c['sample_id']]
for r in ev:
 if r['approved_for_experiment']:
  assert all(r[k]=='approved' for k in ['question_review','support_review','reuse_review','language_review'])
  assert r['reviewed_content_hash']==digest({k:r[k] for k in ['sample_id','source_url','passage_en','passage_zh','passage_vi']})
  assert r['reviewed_question_hash']==digest(next(c for c in cs if c['sample_id']==r['sample_id']))
cfg=json.loads(Path('track-1/configs/openai-eval.json').read_text());cfg['candidate_hash']=digest(cs);report=preflight(cs,ev,cfg)
assert report['ready_questions']==213 and report['pending_questions']==87 and report['network_calls']==0
if out.exists() and any(out.iterdir()):raise ValueError('Use new immutable selection directory')
out.mkdir(exist_ok=True)
for name,rows in [('main-cases.jsonl',cs),('evidence-reviewed-and-pending.jsonl',ev)]: (out/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
(out/'pretranslation-readiness.json').write_text(json.dumps(report,indent=2)+'\n')
manifest={'candidate_hash':digest(cs),'questions':300,'subject_counts':dict(collections.Counter(c['subject'] for c in cs)),'development_overlap':[],'upstream_original_question_preservation':True,'upstream_labels':dict(collections.Counter(c['cultural_sensitivity_label'] for c in cs)),'manual_unannotated_fallback':['astronomy/test/135'],'source_reviewed_questions':300,'approved_trilingual_questions':213,'pending_translation_questions':87,'model_evaluation_calls':0,'status':'all_english_reviewed_supplemental_translation_pending','groups':groups}
(out/'selection-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
