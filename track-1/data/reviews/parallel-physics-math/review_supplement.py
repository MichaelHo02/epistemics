"""Assemble direct assistant semantic review of19generated evidence translations."""
import json,sys,copy
from pathlib import Path
from collections import Counter
sys.path.insert(0,'track-1/src')
from epistemics_dataset.seeds import digest
B=Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main');O=B/'parallel-physics-math';R=Path('track-1/data/reviews/parallel-physics-math')
T=B.parent/'pilot-generation/evidence-translation/59ae07d02eb5c97a5eb120837f6350c0bf46c3200f6c8e38618a3c3c6a134da6/translation-candidates.jsonl'
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def content(e):return {k:e.get(k) for k in ('sample_id','source_url','passage_en','passage_zh','passage_vi')}
cs=read(B/'selection-v3/main-cases.jsonl');assert digest(cs)=='b4b43ea7568d67ba1d57f7bf5bf25fbb59fff193d1015078f7af8442fddb7fe0'
cases={c['sample_id']:c for c in cs};raw={t['sample_id']:t for t in read(T)};frozen={e['sample_id']:e for e in read(O/'evidence-reviewed-and-pending.jsonl')};glob={e['sample_id']:e for e in read(B/'selection-v3/evidence-reviewed-and-pending.jsonl')};needs=read(O/'translation-needed.jsonl');oldreview={r['sample_id']:r for r in read(R/'family-review.jsonl')}
reviewer='assistant_parallel_physics_math_supplemental_review'
notes={
'high_school_physics/test/33':'All languages preserve scale normal force, upward-positive N-mg=ma, and downward acceleration when N<mg. No direction-of-velocity substitution; support combines with original moving-up/slowing option.',
'high_school_physics/test/101':'ZH相干 and VI kết hợp retain coherence; both preserve small angle/far field and fringe spacing=lambda*screen-distance/slit-separation. VI hai khe hẹp is conventional narrow double-slit wording, no changed denominator.',
'high_school_physics/test/150':'Both preserve tangential speed increase, below-escape bound ellipse, and closest approach at impulse. VI elip bị ràng buộc is literal but context unambiguously bound orbit; ZH近地点 appropriately specializes closest approach to original Earth orbit. No apocenter/pericenter reversal.',
'high_school_physics/test/124':'Net force/torque both zero preserved; arbitrary potential-energy reference does not require total mechanical energy zero in either translation. No replacement of necessary condition by sufficient condition.',
'high_school_physics/test/117':'VI rest/constant-g/no-drag and g*t^2/2 preserved. ZH initially leaves elapsed time untranslated; replace just that phrase with 已经过的时间. Formula scope remains one half of g times squared elapsed time, not squared g.',
'conceptual_physics/test/58':'All preserve logarithmic pressure amplitude relation, ordinary louder sound with greater amplitude, and fixed other listening conditions. Correct OpenStax source binding now exact; no claim subjective loudness depends exclusively on amplitude at arbitrary frequency.',
'conceptual_physics/test/111':'ZH相互增强/相互抵消 and VI củng cố lẫn nhau/triệt tiêu convey physical reinforcement/cancellation at different angles; regularly spaced openings/rulings and phase differences retained. VI củng cố is less idiomatic than tăng cường but meaning clear from waves/phase/cancellation; no mandatory stylistic rewrite.',
'conceptual_physics/test/102':'Both retain proton count identifying element and mass number counting protons+neutrons. VI repeats ambiguous số nguyên tử for atomic number; replace only with standard số hiệu nguyên tử, preserving explicit proton-count definition. ZH原子序数/质量数 correct.',
'conceptual_physics/test/45':'Both preserve equal temperature and mean speed proportional to inverse square root of molecular mass. Chinese速度 polysemy resolved as scalar average molecular speed in question and molecular-mass scaling, not mean velocity vector.',
'conceptual_physics/test/154':'All distinguish material-particle mechanical disturbance from electromagnetic radiation; visible light/radio/X-rays labels preserved. No sound-in-vacuum assertion.',
'conceptual_physics/test/156':'Both preserve coil/magnetic-field interactions and opposite electrical/mechanical energy-conversion directions. ZH前者/后者 correctly binds motor/generator. VI one/other preserves same relation; no claim devices generate net energy.',
'high_school_mathematics/test/12':'Both preserve 2^3 remainder1 modulo7, exponent period3, reduce exponent modulo3 before separate additive constant. Does not subtract3 from the whole power or reduce exponent modulo7.',
'high_school_mathematics/test/158':'Both explicitly distinguish female/male friend groups, complement each in-town percentage, multiply each own group size by own out-of-town fraction, then sum. Prior subgroup ambiguity removed; no social-group partition introduced.',
'high_school_mathematics/test/111':'Even exponents, three distinct primes, smallest primes and exponent2 preserved. ZH wording separately square primes is understood as their prime-factor product in preceding factorization context, not summing squares; no rewrite required.',
'high_school_mathematics/test/236':'Both preserve equal price within each item type, total/count unit price, and equality of totals relating distinct unit prices. ZH项目 is generic item but mathematical meaning unchanged; no assumption pen and pencil prices equal.',
'high_school_mathematics/test/219':'Both preserve exactly one real intersection, repeated real root of quadratic difference and completing square. ZH重实根 and VI nghiệm thực kép identify repeated root, not two distinct roots.',
'high_school_mathematics/test/8':'ZH fair independent six-sided rolls and success-position binomial powers correct. VI công lập means public/state-run, not probabilistically fair; replace phrase with independent rolls of a fair six-sided die. Counts/success positions and powers1/6,5/6 retained.',
'high_school_mathematics/test/4':'ZH preserves interior point below chord and upward quadratics for attainability. VI a point in domain can overextend chord inequality beyond two endpoints; clarify interior as strictly between the abscissae of the two known points. Strict convexity, strict below chord, and attainability family retained.',
'high_school_mathematics/test/199':'Both preserve point=input/output value and substituting that input into relation between functions. Does not flip output sign or exchange f/g; applying to originalg(3)=f(-3)=2 yields(-3,2).'
}
corrections={
'high_school_physics/test/117':('zh','elapsed time','已经过的时间', 'Untranslated English time phrase in Chinese supporting evidence.'),
'conceptual_physics/test/102':('vi','số nguyên tử','số hiệu nguyên tử','Use standard Vietnamese term atomic number, distinguished from number of atoms.'),
'high_school_mathematics/test/8':('vi','Đối với các lần gieo xúc xắc sáu mặt công lập độc lập,','Đối với các lần gieo độc lập một con xúc xắc sáu mặt công bằng,','Fair was mistranslated as public/state-run; restore unbiased die and independent rolls.'),
'high_school_mathematics/test/4':('vi','Tại một điểm trong miền xác định,','Tại một điểm nằm giữa hai hoành độ của hai điểm đã biết,','Interior refers to interval between chord endpoints, not arbitrary point of function domain.')}
out=[];reviews=[]
for n in needs:
 sid=n['sample_id'];t=raw[sid];c=cases[sid];e=copy.deepcopy(frozen[sid]);g=glob[sid]
 assert digest(c)==n['question_hash']==t['question_hash']==e['reviewed_question_hash']
 assert e['source_url']==n['source_url']==t['source_url']==g['source_url']
 assert e['passage_en']==n['passage_en']==t['passage_en']==g['passage_en']
 assert oldreview[sid]['support_review']=='approved' and oldreview[sid]['question_review']=='approved'
 original_hash=digest(content(t));raw_passages={k:t[k] for k in ('passage_en','passage_zh','passage_vi')}
 for k,v in raw_passages.items():e[k]=v
 edits=[]
 if sid in corrections:
  lang,before,after,reason=corrections[sid];field='passage_'+lang
  assert e[field].count(before)==1
  e[field]=e[field].replace(before,after)
  edits=[dict(language=lang,field=field,before=before,after=after,reason=reason,correction_reviewer=reviewer)]
 assert e['passage_en']==n['passage_en']
 new_hash=digest(content(e))
 origin='Adaption-generated, assistant-corrected' if edits else 'Adaption-generated, assistant-reviewed unchanged'
 e.update(approved_for_experiment=True,question_review='approved',support_review='approved',reuse_review='approved',language_review='approved',reviewer=reviewer,reviewed_question_hash=digest(c),reviewed_content_hash=new_hash,review_date='2026-11-15',evidence_status='reviewed_supported',translation_origin=origin,translation_corrections=edits,original_generated_content_hash=original_hash,translation_id=t.get('translation_id'),translation_join_id=t.get('translation_join_id'),translation_source_path=str(T),review_note=notes[sid],review_limitations=['Assistant semantic review, not independent human or blinded bilingual review.','Source-supported English, original questions/options/gold unchanged; source/derivation review inherited from frozen family review.'])
 if edits:e.update(correction_reviewer=reviewer,raw_generated_passages=raw_passages)
 r=dict(sample_id=sid,subject=e['subject'],reviewer=reviewer,review_date='2026-11-15',question_review='approved',support_review='approved',reuse_review='approved',language_review='approved',approved_for_experiment=True,finding=notes[sid],reviewed_question_hash=digest(c),original_generated_content_hash=original_hash,reviewed_content_hash=new_hash,source_url=e['source_url'],source_review_record='track-1/data/reviews/parallel-physics-math/family-review.jsonl',translation_origin=origin,raw_generated_passages=raw_passages,translation_corrections=edits,correction_reviewer=reviewer if edits else None,translation_id=t.get('translation_id'),translation_join_id=t.get('translation_join_id'),review_limitations=e['review_limitations'])
 out.append(e);reviews.append(r)
assert len(out)==19 and len({e['sample_id'] for e in out})==19
for e in out:
 assert all(e[k]=='approved' for k in ('question_review','support_review','reuse_review','language_review'))
 assert e['reviewed_content_hash']==digest(content(e))
 assert (e['original_generated_content_hash']!=e['reviewed_content_hash'])==bool(e['translation_corrections'])
for folder in [O,R]:
 for name,rows in [('supplemental-reviewed.jsonl',out),('supplemental-language-review.jsonl',reviews)]:
  (folder/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
summary=dict(scope=19,approved=19,held=0,corrected_rows=sum(bool(e['translation_corrections']) for e in out),unchanged_generated_rows=sum(not e['translation_corrections'] for e in out),approved_by_subject=dict(Counter(e['subject'] for e in out)),all_frozen_english_and_source_and_question_bindings_exact=True,all_content_hashes_valid=True,original_question_and_english_edits=0,new_api_compute_service_calls=0,reviewer=reviewer,limitations='Assistant review, not independent human or blinded.')
for folder in [O,R]:(folder/'supplemental-progress.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
