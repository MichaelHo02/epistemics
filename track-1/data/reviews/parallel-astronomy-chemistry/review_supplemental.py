import json,sys,copy
from pathlib import Path
sys.path.insert(0,'track-1/src')
from epistemics_dataset.seeds import digest
B=Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main'); R=Path('track-1/data/reviews/parallel-astronomy-chemistry'); O=B/'parallel-astronomy-chemistry'
T=B.parent/'pilot-generation/evidence-translation/59ae07d02eb5c97a5eb120837f6350c0bf46c3200f6c8e38618a3c3c6a134da6/translation-candidates.jsonl'
def read(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def content(r):return {k:r[k] for k in ('sample_id','source_url','passage_en','passage_zh','passage_vi')}
cases={r['sample_id']:r for r in read(B/'selection-v3/main-cases.jsonl')}; frozen={r['sample_id']:r for r in read(B/'selection-v3/evidence-reviewed-and-pending.jsonl')}
notes={'64':'Same central atom, oxidation state and general acidity direction retained.','122':'Six electron domains, octahedral domain arrangement and square-pyramidal atom geometry retained.','125':'Complete set of four quantum numbers, same atom and no two electrons retained.','4':'Antimony Sb and atomic number 51 retained.','19':'Exponential decay, log2 ratio, and rounding upward for whole counts retained.','8':'Signed ion charge and electron-count subtraction direction retained.','176':'Small-hole condition and inverse square-root molar-mass ratio retained; Vietnamese diffusion wording is disambiguated by explicit small hole and formula.','185':'Acetate hydrolysis, 25C, Kb=Kw/Ka and sqrt of full Kb*C product retained.','78':'Atom/charge conservation and two-versus-three transferred electrons retained.','46':'Sigma connections and one double bond in a nitrate Lewis contributor retained; no actual localized nitrate double-bond claim.'}
out=[];findings=[];reviewer='assistant_astronomy_chemistry_supplemental_review'
for raw in read(T):
 sid=raw['sample_id']
 if not sid.startswith(('astronomy/','high_school_chemistry/')):continue
 e=copy.deepcopy(frozen[sid]);e.update(content(raw));edits=[]
 if sid=='astronomy/test/42':
  before=e['passage_zh'];after='自引力压缩巨行星物质，增加其密度。因此，与密度保持不变的情况相比，质量更大可能只会使半径按小得多的比例增加。';reason='Restore English modal can and proportional-radius scope.'
 elif sid=='astronomy/test/125':
  before=e['passage_zh'];after=before.replace('特洛伊小群','特洛伊小行星群');reason='Restore missing asteroid noun in Trojan swarms.'
 else:before=after=None
 if before is not None:
  assert before!=after;e['passage_zh']=after;edits=[dict(field='passage_zh',language='zh',before=before,after=after,reason=reason)]
 note=notes[sid.split('/')[-1]] if sid.startswith('high_school_chemistry') else 'Direct EN/ZH/VI comparison preserves the factual relation, named objects, quantities and inference; reviewed against frozen source-supported English.'
 e.update(approved_for_experiment=True,reviewer=reviewer,reviewed_question_hash=digest(cases[sid]),reviewed_content_hash=digest(content(e)),review_date='2026-11-15',translation_corrections=edits,translation_origin='Adaption-generated, assistant-corrected' if edits else 'Adaption-generated, assistant-reviewed unchanged',original_generated_content_hash=digest(content(raw)),raw_generated_passages={k:raw[k] for k in ('passage_en','passage_zh','passage_vi')},translation_id=raw['translation_id'],translation_join_id=raw['translation_join_id'],review_note=note,review_limitations=['Assistant review, not independent human or blinded bilingual review.'])
 for k in ('question_review','support_review','reuse_review','language_review'):e[k]='approved'
 if edits:e['correction_reviewer']=reviewer
 out.append(e);findings.append(dict(sample_id=sid,finding=note,reviewer=reviewer,raw_generated_content_hash=digest(content(raw)),reviewed_content_hash=e['reviewed_content_hash'],translation_corrections=edits,raw_generated_passages=e['raw_generated_passages']))
assert len(out)==20
for folder in (R,O):
 for name,rows in [('supplemental-reviewed.jsonl',out),('supplemental-language-review.jsonl',findings)]: (folder/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
print({'reviewed':len(out),'corrected':sum(bool(r['translation_corrections']) for r in out)})
