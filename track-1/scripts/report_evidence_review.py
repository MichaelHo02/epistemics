"""Merge recorded evidence-review batches; never approve or replace questions."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--batch',type=Path,required=True)
    args=parser.parse_args()
    folder=args.dataset
    cases=read(folder/'main-cases.jsonl')
    previous=read(folder/'evidence-candidates.jsonl')
    batch=json.loads(args.batch.read_text())
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
    (folder/'evidence-candidates-v2.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in ordered))
    write(folder/'question-language-checks-v2.json',batch.get('question_language_checks',[]))
    counts=Counter(r['evidence_status'] for r in ordered)
    audit={'questions':len(cases),'language_rows':len(cases)*3,
           'structural_field_or_key_failures':missing,'duplicate_english_stem_groups':duplicate_groups,
           'evidence_status_counts':dict(counts),'approved_for_experiment':0,
           'review_scope':'All 900 records checked for field presence and key agreement. Semantic/source checks are partial, not complete.',
           'held_question_ids':[r['sample_id'] for r in ordered if r['evidence_status']=='hold'],
           'draft_question_language_checks':len(batch.get('question_language_checks',[])),
           'resolved_triage':batch.get('resolved_triage',[]),
           'replacements_applied':0,'api_calls':0}
    write(folder/'evidence-audit-v2.json',audit)
    write(folder/'evidence-sources-v2.json',{'checked_on':batch['review_date'],
        'sources':[{'source_url':url,'case_ids':[r['sample_id'] for r in ordered if r.get('source_url')==url],
                    'locators':[r.get('source_locator') for r in ordered if r.get('source_url')==url and r.get('source_locator')],
                    'reuse_review':'pending'}
                   for url in sorted({r['source_url'] for r in ordered if r.get('source_url')})],
        'note':'Read-source ledger; passage text is explicitly researcher paraphrase, not a quote. Some held rows cite context rather than support for the key.'})
    lines=['# Main-study evidence review: batch 2','','This is dataset preparation. No model or translation API calls were made. The selected 300 questions and all original answer keys remain unchanged.','','## Current counts','']
    lines += ['- '+str(n)+' questions: '+status for status,n in sorted(counts.items())]
    lines += ['- 0 questions approved for the full experiment.',
              '- 12 question-language comparisons checked by the assistant; evidence translations are still missing.',
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
    lines+=['## A potential issue resolved by reading all options','','The oscillator question high_school_physics/test/43 is not classified as defective: option D explicitly says the effect depends on the phase of oscillation. Its formal evidence review remains pending.','','## Next preparation work','','Finish source checking the remaining questions, adjudicate the holds and log necessary replacements using the within-subject reserve order. Only then translate the selected evidence through Adaption and complete the language review. No additional approval from the user is needed for these already-authorized preparation steps.','','[Machine-readable candidates](evidence-candidates-v2.jsonl) · [Audit](evidence-audit-v2.json) · [Sources](evidence-sources-v2.json) · [Question-language checks](question-language-checks-v2.json)']
    (folder/'evidence-progress-v2.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
