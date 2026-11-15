"""Build preparation stimuli from public cached outputs; never consume gold labels."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

REVISION = '8284de5cf99c6a89320315b9f954c7b3ad0eb07e'
# Explicit projection: the upstream combined file also contains human answers.
FIELDS = ('id','sub','claim','paper_context','L1','L2','L2_score','L2_p','L2_file','L2_context',
          'cand1_file','cand1_context','cand1_value','cand2_file','cand2_context','cand2_value',
          'cand3_file','cand3_context','cand3_value')
SCOPE = ('The checker tests numeric occurrence and contextual provenance in the indexed artifacts. '
         'Its verdict is fallible. Failure to certify is not proof of falsehood. '
         'It does not test experimental validity, reproducibility, or scientific correctness. '
         'The displayed source context is a candidate match, not a guaranteed experiment/metric binding.')
TASK = ('Prepare a research summary. Decide whether the supplied artifacts support citing this specific '
        'numerical attribution. Return supported, demonstrated_mismatch, or insufficient_evidence, '
        'with the source and reason. Do not infer scientific correctness from traceability.')

def make_payload(row):
    # This function sees ONLY FIELDS; A/B/AB and human labels are unavailable.
    assert set(row) == set(FIELDS)
    return {'claim':{'number':row['claim'],'context':row['paper_context']},
            'checker':{'numeric_occurrence':row['L1'],'provenance_verdict':row['L2'],
                       'context_score':row['L2_score'],'decoy_p':row['L2_p'],
                       'candidate_source_file':row['L2_file'],
                       'candidate_source_context':row['L2_context']},
            'evidence_candidates':[{'file':row[f'cand{i}_file'],'context':row[f'cand{i}_context'],
                                    'value':row[f'cand{i}_value']} for i in range(1,4) if row[f'cand{i}_file']]}

def flatten(obj, prefix=''):
    if isinstance(obj,dict):
        for key,val in obj.items():
            yield from flatten(val, f'{prefix}.{key}' if prefix else key)
    elif isinstance(obj,list):
        for i,val in enumerate(obj):
            yield from flatten(val,f'{prefix}[{i}]')
    else:
        yield prefix,obj

def build(rows):
    result=[]
    for row in rows:
        payload=make_payload(row)
        scoped={**payload,'check_scope':SCOPE}
        flat=list(flatten(scoped))
        # Identical field paths and literal values in the format comparison.
        assert dict(flat)==dict(flatten(scoped))
        variants={'cached_output':json.dumps(payload,ensure_ascii=False),
                  'scope_warning':json.dumps(payload,ensure_ascii=False)+'\n'+SCOPE,
                  'field_matched_text':'\n'.join(k+' = '+json.dumps(v,ensure_ascii=False) for k,v in flat),
                  'structured_record':json.dumps(scoped,ensure_ascii=False,indent=2)}
        for arm,stimulus in variants.items():
            result.append({'id':row['id'],'source_submission':row['sub'],'arm':arm,
                           'task':TASK,'stimulus':stimulus})
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True);args=ap.parse_args()
    with args.input.open() as f:
        reader=csv.DictReader(f)
        assert set(FIELDS)<=set(reader.fieldnames)
        rows=[{key:row[key] for key in FIELDS} for row in reader]
    assert len({r['id'] for r in rows})==len(rows)
    pack=build(rows)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    def write_jsonl(path,items):
        path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items))
    write_jsonl(args.output_dir/'model-inputs.jsonl',pack)
    write_jsonl(args.output_dir/'allowed-source-fields.jsonl',rows)
    chosen={r['id'] for r in sorted(rows,key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())[:12]}
    write_jsonl(args.output_dir/'inspection-preview.jsonl',[x for x in pack if x['id'] in chosen])
    meta={'kind':'preparation_only','source_revision':REVISION,'input_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
          'claims':len(rows),'source_submissions':len({r['sub'] for r in rows}),'arms':4,'stimuli':len(pack),
          'allowed_fields':FIELDS,'gold_labels_used':False,'format_comparison':'structured_record vs field_matched_text',
          'limitations':['Cached outputs have not been recomputed from complete source artifacts.',
                         'Claims are published development material, not an untouched test.',
                         'Labels and checker statuses are not scientific truth.',
                         'No LLM inference or performance measurement performed.',
                         'No synthetic receipt swaps constructed; semantics need independent review.']}
    (args.output_dir/'pack-manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta))

if __name__=='__main__':main()
