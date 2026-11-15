"""Prepare a fixed main-study candidate set from a verified local HF snapshot.

No network requests, model calls, evidence generation or automatic approvals.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .global_mmlu import align, answer_agrees, complete, select
from .pipeline import write_jsonl
from .seeds import digest


def prepare(config_path, snapshot, output):
    import pyarrow.parquet as pq
    root = Path(__file__).resolve().parents[2]
    config = json.loads(config_path.read_text())
    exclusions = json.loads((root/config['exclude_ids_file']).read_text())['sample_ids']
    config['exclude_ids'] = exclusions
    files = []
    for name, expected in config['sha256'].items():
        path = snapshot/name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Snapshot checksum mismatch: '+name)
        files.append({'path':name, 'sha256':actual})
    rows = {lang:pq.read_table(snapshot/lang/'test-00000-of-00001.parquet').to_pylist()
            for lang in config['languages']}
    indexes = align(rows, allow_answer_disagreements=True)
    cases = select(indexes, config)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output/'main-cases.jsonl', cases)
    selected = {c['sample_id'] for c in cases}
    reserves = []
    # Same fixed ranking as the main selection; replacement reasons must be logged.
    for subject in config['subjects']:
        eligible = [r for r in indexes['en'].values() if r['subject']==subject
                    and r['cultural_sensitivity_label']==config['cultural_sensitivity_label']
                    and r['sample_id'] not in exclusions and complete(indexes,r['sample_id'])
                    and answer_agrees(indexes,r['sample_id'])]
        eligible.sort(key=lambda r:hashlib.sha256((config['selection_salt']+r['sample_id']).encode()).hexdigest())
        reserves.extend({'sample_id':r['sample_id'],'subject':subject,'rank_within_subject':i+1}
                        for i,r in enumerate(eligible) if r['sample_id'] not in selected)
    write_jsonl(output/'replacement-queue.jsonl',reserves)
    write_jsonl(output/'question-rows.jsonl',[
        {'sample_id':c['sample_id'],'language':lang,'original':r}
        for c in cases for lang,r in c['languages'].items()])
    write_jsonl(output/'evidence-tasks.jsonl',[
        {'sample_id':c['sample_id'],'subject':c['subject'],
         'question':c['languages']['en']['question'],'answer_code':c['answer'],
         'answer_text':c['languages']['en']['option_'+c['answer'].lower()],
         'source_url':None,'passage_en':None,'passage_zh':None,'passage_vi':None,
         'support_review':'pending','reuse_review':'pending','language_review':'pending',
         'approved_for_experiment':False}
        for c in cases])
    plan=[]
    for c in cases:
        for language in config['languages']:
            for advice in ('neutral','correct','wrong'):
                for evidence_language in (None,)+tuple(config['languages']):
                    plan.append({'sample_id':c['sample_id'],'conversation_language':language,
                                 'advice':advice,'evidence_language':evidence_language,
                                 'status':'blocked_pending_material_review'})
    write_jsonl(output/'condition-plan.jsonl',plan)
    manifest={'dataset':config['dataset'],'revision':config['revision'],'files':files,
              'selection':config,'main_candidate_questions':len(cases),
              'question_language_rows':len(cases)*len(rows),'candidate_hash':digest(cases),
              'development_overlap':sorted(selected.intersection(exclusions)),
              'reserve_questions':len(reserves),'planned_initial_answers':len(cases)*len(rows),
              'planned_revision_conditions':len(plan),'model_calls':0,
              'approved_questions':0,'status':'questions_selected_evidence_pending',
              'limits':['Not representative of all Global-MMLU subjects.',
                        'Matching answer letters does not verify translation meaning.',
                        '300 is a planning target, not a power calculation.',
                        'Condition rows are paired measurements, not independent questions.']}
    (output/'preparation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'review-sheet.md').write_text('# Main-study question review\n\nOriginal English questions and dataset keys. Chinese and Vietnamese originals are in question-rows.jsonl. Evidence and language reviews are pending.\n\n'+'\n\n'.join(
        '## '+c['sample_id']+'\n\n'+c['languages']['en']['question']+'\n\n'+'\n'.join(
            '- '+a+'. '+c['languages']['en']['option_'+a.lower()] for a in 'ABCD')+'\n\nDataset key: '+c['answer'] for c in cases)+'\n')
    return manifest


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=root/'configs/global-mmlu-main.json')
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=prepare(args.config,args.snapshot,args.output)
    print(json.dumps({k:report[k] for k in ('main_candidate_questions','question_language_rows','development_overlap','reserve_questions','planned_initial_answers','planned_revision_conditions','approved_questions','model_calls')},indent=2))

if __name__=='__main__':
    main()
