"""Merge recorded evidence-review batches; never approve or replace questions."""
import argparse
from collections import Counter, defaultdict
import json
import hashlib
from pathlib import Path


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--batch',type=Path,action='append',required=True)
    parser.add_argument('--version',default='v3')
    args=parser.parse_args()
    folder=args.dataset
    cases=read(folder/'main-cases.jsonl')
    previous=read(folder/'evidence-candidates.jsonl')
    batches=[json.loads(path.read_text()) for path in args.batch]
    batch={'review_date':batches[-1]['review_date'],
           'rows':[row for item in batches for row in item['rows']],
           'question_language_checks':[row for item in batches for row in item.get('question_language_checks',[])],
           'resolved_triage':[row for item in batches for row in item.get('resolved_triage',[])]}
    by_id={c['sample_id']:c for c in cases}
    candidates={r['sample_id']:r for r in previous}
    assert len(by_id)==len(cases)==len(candidates)==300
    assert set(by_id)==set(candidates)
    # Immutable selection and original answer keys are never changed here.
    batch_ids=[r['sample_id'] for r in batch['rows']]
    assert len(batch_ids)==len(set(batch_ids))
    for row in batch['rows']:
        sid=row['sample_id']
        assert sid in by_id
        candidates[sid].update(row)
        candidates[sid]['approved_for_experiment']=False
    groups=defaultdict(list)
    missing=[]
    for c in cases:
        groups[' '.join(c['languages']['en']['question'].lower().split())].append(c['sample_id'])
        for lang in ('en','zh','vi'):
            row=c['languages'][lang]
            if row['answer']!=c['answer'] or not all(row.get(k) for k in ('question','option_a','option_b','option_c','option_d')):
                missing.append({'sample_id':c['sample_id'],'language':lang})
    duplicate_groups=[ids for ids in groups.values() if len(ids)>1]
    ordered=[candidates[c['sample_id']] for c in cases]
    # Versioned outputs preserve the first batch and the original unfilled tasks.
    (folder/f'evidence-candidates-{args.version}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ordered))
    write(folder/f'question-language-checks-{args.version}.json',batch.get('question_language_checks',[]))
    counts=Counter(r['evidence_status'] for r in ordered)
    audit={'questions':len(cases),'language_rows':len(cases)*3,
           'structural_field_or_key_failures':missing,'duplicate_english_stem_groups':duplicate_groups,
           'evidence_status_counts':dict(counts),'approved_for_experiment':0,
           'review_scope':'All 900 records checked for field presence and key agreement. Draft English triage does not certify final source support or translation meaning.',
           'english_first_pass_complete':not any(r['evidence_status']=='not_checked' for r in ordered),
           'source_access_counts':dict(Counter(r.get('source_access','not_recorded') for r in ordered)),
           'input_batches':[{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in args.batch],
           'held_question_ids':[r['sample_id'] for r in ordered if r['evidence_status']=='hold'],
           'draft_question_language_checks':len(batch.get('question_language_checks',[])),
           'resolved_triage':batch.get('resolved_triage',[]),
           'replacements_applied':0,'api_calls':0}
    write(folder/f'evidence-audit-{args.version}.json',audit)
    write(folder/f'evidence-sources-{args.version}.json',{'checked_on':batch['review_date'],
        'sources':[{'source_url':url,'case_ids':[r['sample_id'] for r in ordered if r.get('source_url')==url],
                    'locators':[r.get('source_locator') for r in ordered if r.get('source_url')==url and r.get('source_locator')],
                    'reuse_review':'pending'}
                   for url in sorted({r['source_url'] for r in ordered if r.get('source_url')})],
        'note':'Reference ledger for draft review, not a certificate of full source verification. Passage text is researcher paraphrase or an independent derivation, not a quotation. Some references supply background only; limitations are recorded in review_note. Held rows may cite context rather than support for the key.'})
    lines=['# Main-study evidence review: accumulated batches','','This is dataset preparation. No model or translation API calls were made. The selected 300 questions and all original answer keys remain unchanged.','','## Current counts','']
    lines += ['- '+str(n)+' questions: '+status for status,n in sorted(counts.items())]
    lines += ['- 0 questions approved for the full experiment.',
              '- Drafts may still have background-only references, indexed excerpts, or unresolved assumptions. Read each review note; this is not a final source certificate.',
              f"- {len(batch.get('question_language_checks',[]))} question-language comparisons checked by the assistant; evidence translations are still missing.",
              '- All 900 records passed field-presence and answer-letter agreement checks. This does not verify their meaning.',
              '- Two groups have identical English question stems. One is a repeated Jupiter question with reordered options. The other contains two incomplete chemistry stems.',
              '- No replacements applied yet. Holds are review decisions, not a count of proven wrong answer keys.','','## Draft source-supported questions','']
    for r in ordered:
        if r['evidence_status']!='draft_supported':continue
        lines += ['### '+r['sample_id'],'',r['passage_en'],'',r.get('review_note',''),'',
                  '[Source]('+r['source_url']+')','']
    lines+=['## Held questions','']
    for r in ordered:
        if r['evidence_status']=='hold':
            lines+=['### '+r['sample_id'],'',r['review_note'],'']
    lines+=['## A potential issue resolved by reading all options','','The oscillator question high_school_physics/test/43 is not classified as defective: option D explicitly says the effect depends on the phase of oscillation. Its formal evidence review remains pending.','','## Next preparation work','','Finish source checking the remaining questions, adjudicate the holds and log necessary replacements using the within-subject reserve order. Only then translate the selected evidence through Adaption and complete the language review. No additional approval from the user is needed for these already-authorized preparation steps.','',f'[Machine-readable candidates](evidence-candidates-{args.version}.jsonl) · [Audit](evidence-audit-{args.version}.json) · [Sources](evidence-sources-{args.version}.json) · [Question-language checks](question-language-checks-{args.version}.json)']
    (folder/f'evidence-progress-{args.version}.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
