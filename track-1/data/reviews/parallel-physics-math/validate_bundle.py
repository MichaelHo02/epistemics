"""Review integrity checks only; no model evaluation or network."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
sys.path.insert(0,'track-1/src')
from epistemics_dataset.seeds import digest
B=Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main');O=B/'parallel-physics-math';R=Path('track-1/data/reviews/parallel-physics-math')
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
cs=read(O/'proposed-cases.jsonl');es=read(O/'evidence-reviewed-and-pending.jsonl');rs=read(R/'family-review.jsonl');ts=read(O/'translation-needed.jsonl');ds=read(R/'reserve-decisions.jsonl')
orig=read(B/'selection-v2/main-cases.jsonl');res=read(B/'replacement-review-v1/reserve-cases.jsonl');source={c['sample_id']:c for c in orig};source.update({r['case']['sample_id']:r['case'] for r in res})
assert len(cs)==90 and len({c['sample_id'] for c in cs})==90
assert set(Counter(c['subject'] for c in cs).values())=={30}
assert len(es)==len(rs)==90
by={c['sample_id']:c for c in cs};review={r['sample_id']:r for r in rs};tr={t['sample_id']:t for t in ts}
for c in cs:assert c==source[c['sample_id']]
for e in es:
 sid=e['sample_id'];c=by[sid];r=review[sid]
 assert e['reviewed_question_hash']==digest(c)==r['reviewed_question_hash']
 assert e['reviewed_content_hash']==digest({k:e.get(k) for k in ('sample_id','source_url','passage_en','passage_zh','passage_vi')})==r['reviewed_content_hash']
 if e['approved_for_experiment']:
  assert all(e[k]=='approved' for k in ('question_review','support_review','reuse_review','language_review'))
  assert all(isinstance(e['passage_'+l],str) and e['passage_'+l] for l in ('en','zh','vi'))
 else:
  assert sid in tr and e['language_review']=='pending'
  assert tr[sid]['question_hash']==digest(c) and all(tr[sid][k]==e[k] for k in ('source_url','passage_en'))
# Every consumed reserve is accounted for in fixed order, including prior consumed rows.
for s in Counter(c['subject'] for c in cs):
 consumed=[r for r in res if r['case']['subject']==s and r['rank_within_subject']<=max(d['rank_within_subject'] for d in ds if d['sample_id'].startswith(s+'/'))]
 assert [r['case']['sample_id'] for r in consumed]==[d['sample_id'] for d in ds if d['sample_id'].startswith(s+'/')]
inputs=[B/'selection-v2/main-cases.jsonl',B/'selection-v2/evidence-candidates.jsonl',B/'selection-v2/reviewed-physics-02.jsonl',B/'selection-v2/reviewed-mathematics-01.jsonl',B/'replacement-review-v1/reserve-cases.jsonl']
out=dict(status='passed_integrity_checks_not_model_evaluation',proposed=len(cs),approved=sum(e['approved_for_experiment'] for e in es),pending=len(ts),question_objects_byte_value_unchanged=True,exact_content_and_question_hashes_valid=True,approved_four_fields_exact=True,ordered_reserve_prefix_complete=True,original_question_option_gold_rewrites=0,model_calls=0,input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
(R/'validation.json').write_text(json.dumps(out,indent=2)+'\n');(O/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'},indent=2))
