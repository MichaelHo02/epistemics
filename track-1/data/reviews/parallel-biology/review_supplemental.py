import pathlib,json,sys,collections
sys.path.insert(0,'track-1/src')
from epistemics_dataset.seeds import digest
B=pathlib.Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main');D=pathlib.Path(__file__).resolve().parent;O=B/'parallel-biology'
P=pathlib.Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/pilot-generation/evidence-translation/59ae07d02eb5c97a5eb120837f6350c0bf46c3200f6c8e38618a3c3c6a134da6/translation-candidates.jsonl')
def rd(p):return [json.loads(x) for x in p.read_text().splitlines()]
cs=rd(B/'selection-v3/main-cases.jsonl');assert digest(cs)=='b4b43ea7568d67ba1d57f7bf5bf25fbb59fff193d1015078f7af8442fddb7fe0'
cases={x['sample_id']:x for x in cs};frozen={x['sample_id']:x for x in rd(B/'selection-v3/evidence-reviewed-and-pending.jsonl')};local={x['sample_id']:x for x in rd(O/'evidence-reviewed.jsonl')};requested={x['sample_id']:x for x in rd(O/'translation-needed.jsonl')};raw=[x for x in rd(P) if x['sample_id'] in requested];assert len(raw)==len(requested)==21
reviewer='assistant_biology_supplemental_semantic_review'
findings={
'high_school_biology/test/142':'en/zh/vi preserve pure water in open beaker zero reference, dissolved solutes lowering potential, and movement toward lower total potential. No positive/negative reversal. Earlier fresh initial tissue assumption remains in frozen source review.',
'high_school_biology/test/81':'en/zh/vi retain many corresponding sequences/proteins as evidence of close relationship, and common ancestry versus similar environmental demand. Can/plausibility qualifiers preserved; no claim sequence similarity proves every organ homologous.',
'high_school_biology/test/278':'en/zh/vi all locate homologous crossing-over in prophase I, before homologues separate. I versus II, DNA segment exchange and sequence of events preserved.',
'college_biology/test/76':'en/zh protein assemblies on centromeric chromosome regions and microtubule attachment match. vi dong tam is replaced with explicit the dong (kinetochore) to avoid confusion with tam dong (centromere); formation site stays centromeric region, not centriole.',
'college_biology/test/36':'vi preserves tropomyosin blocking myosin interaction with actin and calcium-troponin displacement. zh raw uses generic muscle filament (肌丝) for actin: correct only that noun to 肌动蛋白, retaining interaction direction and cross-bridge mechanism. This fixes specificity, without changing frozen English.',
'college_biology/test/3':'en/zh/vi preserve exact1,4,5isomer, intracellular messenger, release from ER stores into cytoplasm. No switch to calcium influx across plasma membrane or wrong phosphate count.',
'college_biology/test/67':'vi preserves water-conducting vessel elements, programmed death, hollow reinforced conduit and living enucleated sieve tubes. zh raw 血管元件 denotes blood-vessel components; replace with botanical 导管分子. Programmed death vs survival and nuclear loss remain correctly contrasted.',
'college_biology/test/9':'en/zh/vi preserve RNA virus, host entry/uncoating before replication/protein synthesis and explicit absence of reverse-transcribed DNA intermediate. Influenza shorthand consistently names virus in context, not medical guidance.',
'college_biology/test/99':'en/zh/vi preserve colchicine binding tubulin, disrupting spindle microtubules, chromosome segregation after DNA replication and possible additional chromosome sets. Can remains possible, not guaranteed polyploidy in every cell.',
'college_biology/test/57':'en/zh/vi preserve one antibody-producing clone versus multiple B-cell lineages and reduced antibody diversity. No substitution of T cells, antigens or multiple clones into monoclonal definition.',
'high_school_biology/test/11':'en/zh/vi preserve whole-trait combined effects, single inherited variant, both beneficial/harmful effects and possible increase of harmful effect with net advantage. Hypothetical shared-gene tradeoff scope remains, not assertion every maladaptive variant increases.',
'high_school_biology/test/223':'en/zh preserve two favored extreme regions vs intermediate phenotype and conditional model. vi raw rat it means very few, stronger than relatively few; correct to tuong doi it. Definition and conditional distribution retained without claiming observational bimodality proves causal selection.',
'high_school_biology/test/155':'en/zh/vi correctly map light to energy, water to electrons, CO2 to carbon fixed into carbohydrate. Explicit oxygenic plant scope preserved; no extension to all bacterial phototrophs.',
'high_school_biology/test/20':'en/zh/vi preserve antigen exposure, possible expansion of matching-receptor lymphocyte populations and responsive cell numbers versus extra receptor kinds on each cell. No claim that vaccine creates new types of antigen-specific macrophages.',
'high_school_biology/test/2':'vi preserves energy from electron transport, proton pumping across inner mitochondrial membrane and gradient-driven ATP synthesis on proton return. zh raw 驱动质子泵过 is grammatically ambiguous about the pump crossing the membrane; correct locally to 驱动质子跨线粒体内膜的泵送. Electron energy is upstream, proton return immediate; no numerical yield added.',
'college_biology/test/11':'en/vi retain some proteins, sequential envelope/thylakoid targeting, separate signal sequences and stroma-only exception. zh raw 类囊体腔 narrows general thylakoid compartment to lumen; correct term to 类囊体区室, retaining some/can and stroma exception. Two-stage targeting is not asserted for every chloroplast protein.',
'college_biology/test/59':'en/zh/vi retain long-distance dispersal enabling geographically separated suitable habitats, possible worldwide range and need for suitable establishment conditions. Can and also-required conditions preserved; worldwide distribution not guaranteed.',
'college_biology/test/110':'en/zh/vi preserve CO2 fixation with light/water-derived reducing power, carbohydrate/cellulose structure, and raw-material contribution to organic dry matter. Incorporated water-derived atoms distinguished implicitly from unbound tissue water; no claim mineral uptake supplies bulk carbon.',
'college_biology/test/96':'en/zh/vi preserve outer and inner envelope around stroma, thylakoid membranes inside, and outward traversal order thylakoid then inner then outer envelope. Lumen origin remains explicit; no nuclear crossing or lipid-leaflet count introduced.',
'college_biology/test/82':'en/zh/vi preserve PTH blood-calcium regulation and more hormone when calcium low. Restoring calcium availability translated as availability/supply in the same blood-level context; not a treatment recommendation or guarantee for every pathological state.',
'college_biology/test/46':'zh preserves CO2 partial-pressure decrease, H+ decrease, pH increase and slower later compensation. vi raw tho qua nhanh denotes fast breathing rather than effective hyperventilation, and thay the means substitutions rather than changes; locally correct to Tang thong khi and thay doi bu tru. Buffer signs and before-compensation timing remain exact.'}
correction_specs={
'college_biology/test/76':[('passage_vi','động tâm','thể động (kinetochore)','Use explicit kinetochore protein-complex term, distinct from centromere tâm động.')],
'college_biology/test/36':[('passage_zh','肌丝上','肌动蛋白上','Actin is the specific binding-site protein; muscle filament is a broader structure.')],
'college_biology/test/67':[('passage_zh','导水血管元件','导水的导管分子','Botanical vessel elements are 导管分子, not animal blood-vessel components.')],
'high_school_biology/test/223':[('passage_vi','rất ít cá thể trung gian','tương đối ít cá thể trung gian','Preserve relatively few rather than strengthen to very few.')],
'high_school_biology/test/2':[('passage_zh','驱动质子泵过线粒体内膜','驱动质子跨线粒体内膜的泵送','Clarify protons are pumped across the inner membrane; the proton pump itself does not cross it.')],
'college_biology/test/11':[('passage_zh','类囊体腔','类囊体区室','Preserve thylakoid compartment scope rather than narrow to lumen only.')],
'college_biology/test/46':[('passage_vi','Thở quá nhanh','Tăng thông khí','Use physiological hyperventilation, not fast respiratory rate alone.'),('passage_vi','các thay thế bù trừ','các thay đổi bù trừ','Compensatory changes are changes, not substitutions/replacements.')]}
keys=('sample_id','source_url','passage_en','passage_zh','passage_vi');outputs=[];audits=[]
for g in raw:
 sid=g['sample_id'];c=cases[sid];f=frozen[sid];l=local[sid];q=requested[sid]
 assert g['question_hash']==digest(c)==q['question_hash']==l['reviewed_question_hash']
 assert g['source_url']==f['source_url']==l['source_url']==q['source_url']
 assert g['passage_en']==f['passage_en']==l['passage_en']==q['passage_en']
 assert all(f[k]=='approved' and l[k]=='approved' for k in ('question_review','support_review','reuse_review'))
 assert f['language_review']=='pending' and not f['approved_for_experiment']
 # Original immutable questions/options/gold already individually reviewed, and exact full case hashes agree.
 assert c==next(x for x in rd(O/'main-cases-proposed.jsonl') if x['sample_id']==sid)
 original_content={k:g.get(k) for k in keys};original_hash=digest(original_content);out=dict(f)
 for k in ('passage_en','passage_zh','passage_vi'):out[k]=g[k]
 changes=[]
 for field,before,after,reason in correction_specs.get(sid,[]):
  assert out[field].count(before)==1,(sid,field,before)
  before_passage=out[field];out[field]=out[field].replace(before,after)
  changes.append({'field':field,'before':before,'after':after,'before_passage':before_passage,'after_passage':out[field],'reason':reason,'correction_reviewer':reviewer})
 assert out['passage_en']==f['passage_en']
 newhash=digest({k:out.get(k) for k in keys})
 out.update({'reviewer':reviewer,'review_date':'2026-11-15','question_review':'approved','support_review':'approved','reuse_review':'approved','language_review':'approved','approved_for_experiment':True,'reviewed_question_hash':digest(c),'reviewed_content_hash':newhash,'original_generated_content_hash':original_hash,'original_generated_record_hash':digest(g),'translation_id':g['translation_id'],'translation_join_id':g['translation_join_id'],'provider_row_indices':g['provider_row_indices'],'translation_provenance':'Adaption-generated, assistant-corrected' if changes else 'Adaption-generated, assistant-reviewed unchanged','translation_corrections':changes,'correction_reviewer':reviewer if changes else None,'human_review':False,'independent_or_blinded_review':False,'supplemental_language_review_note':findings[sid],'raw_generated_passages':{k:g[k] for k in ('passage_en','passage_zh','passage_vi')}})
 for correction in changes:correction['new_content_hash']=newhash
 outputs.append(out)
 audits.append({'sample_id':sid,'reviewer':reviewer,'review_date':'2026-11-15','reviewed_languages':['en','zh','vi'],'finding':findings[sid],'decision':'approved_after_minor_technical_correction' if changes else 'approved_unchanged','source_and_English_match_frozen':True,'question_hash':digest(c),'frozen_candidate_hash':digest(cs),'original_generated_content_hash':original_hash,'original_generated_record_hash':digest(g),'reviewed_content_hash':newhash,'raw_generated_passages':{k:g[k] for k in ('passage_en','passage_zh','passage_vi')},'translation_corrections':changes,'correction_reviewer':reviewer if changes else None,'translation_provenance':out['translation_provenance'],'human_review':False,'independent_or_blinded_review':False,'translation_id':g['translation_id'],'translation_join_id':g['translation_join_id'],'raw_translation_file':str(P)})
assert {x['sample_id'] for x in outputs}==set(requested)
for name,rows in [('supplemental-reviewed.jsonl',outputs),('supplemental-language-review.jsonl',audits)]:
 text=''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows)
 for root in (O,D):(root/name).write_text(text)
summary={'reviewed':len(outputs),'approved':sum(x['approved_for_experiment'] for x in outputs),'approved_unchanged':sum(not x['translation_corrections'] for x in outputs),'approved_after_minor_correction':sum(bool(x['translation_corrections']) for x in outputs),'correction_operations':sum(len(x['translation_corrections']) for x in outputs),'held':0,'corrected_ids':[x['sample_id'] for x in outputs if x['translation_corrections']],'all_English_and_question_bytes_preserved':True,'all_source_and_question_hash_bindings_match':True}
print(json.dumps(summary,indent=2))
