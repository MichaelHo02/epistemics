"""Offline real-task test readiness; no model calls or experiment registration."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import tempfile
import urllib.request

revision = '520f16f9b3f39b06c6013bc0eb57a38280b4deee'
base_url = 'https://raw.githubusercontent.com/LeiLiLab/susvibes/' + revision + '/'
out = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/real-task-readiness') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out.mkdir(parents=True)
with urllib.request.urlopen(base_url+'datasets/default/susvibes_dataset.jsonl',timeout=30) as response:
    data = response.read()
rows = [json.loads(line) for line in data.splitlines()][:3]
# Original upstream deterministic standard-output parser; imports only re, no APIs.
with urllib.request.urlopen(base_url+'susvibes/core/test_counts.py',timeout=30) as response:
    parser_source = response.read()
(out/'upstream_test_counts.py').write_bytes(parser_source)
spec = importlib.util.spec_from_file_location('upstream_test_counts',out/'upstream_test_counts.py')
parser = importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
report = {'revision':revision,'dataset_sha256':hashlib.sha256(data).hexdigest(),'parser_sha256':hashlib.sha256(parser_source).hexdigest(),'model_calls':0,'tasks':[],'limitations':['Direct task-image tests, not full official harness scoring.','Security patch reversal constructs a reference mutant, not an observed agent error.','No test dependencies fetched inside task containers.']}

def run(args,timeout=90):
    return subprocess.run(args,text=True,capture_output=True,timeout=timeout)
def docker(*args,timeout=90):
    r=run(['docker',*args],timeout)
    if r.returncode: raise RuntimeError(r.stderr[-2000:])
    return r.stdout.strip()
def save():
    (out/'readiness.json').write_text(json.dumps(report,indent=2))
for row in rows:
    taskdir=out/row['instance_id'];taskdir.mkdir()
    (taskdir/'task.json').write_text(json.dumps(row,indent=2))
    result={'instance_id':row['instance_id'],'expected_pf':row['expected_pf'],'variants':[]}
    report['tasks'].append(result);save()
    print('TASK '+row['instance_id'],flush=True)
    try:
        image=row['image_name']
        try: docker('image','inspect',image)
        except RuntimeError: docker('pull','--platform','linux/amd64',image,timeout=300)
        metadata=json.loads(docker('image','inspect',image))[0]
        result['image_id']=metadata['Id'];result['test_command']=metadata['Config']['Cmd']
        assert not row['flags'], 'Non-default runner flags require full harness'
        for variant in ('reference_secure','reference_mutant'):
            for suite in ('func','sec'):
                cid=docker('run','-d','--platform','linux/amd64','--network','none','--entrypoint','sleep',image,'1800')
                record={'variant':variant,'suite':suite};result['variants'].append(record)
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        patches=[('golden_patch',False)]
                        # Official evaluator applies security test patch before model patch.
                        if suite=='sec': patches.insert(0,('test_patch',False))
                        if variant=='reference_mutant': patches.append(('security_patch',True))
                        for number,(field,reverse) in enumerate(patches):
                            patch=Path(tmp)/('patch-'+str(number));patch.write_text(row[field])
                            remote='/tmp/readiness-'+str(number)+'.patch'
                            docker('cp',str(patch),cid+':'+remote)
                            args=['exec','-w','/project',cid,'git','apply']+(['-R'] if reverse else [])+[remote]
                            docker(*args)
                    command=['docker','exec','-w','/project',cid,*result['test_command']]
                    try:
                        tested=run(command,timeout=180)
                        text=tested.stdout+'\n'+tested.stderr
                        record['exit_code']=tested.returncode
                        try: record['counts']=parser.validated_test_counts(text,{})
                        except ValueError as exc:
                            # This older pytest prints 'seconds', whereas upstream fallback expects 's'.
                            matches = re.findall(r'^=+ ([^\n]+) in [0-9.]+ seconds =+$',text,re.MULTILINE)
                            if matches:
                                names={'passed':'PASSED','failed':'FAILED','errors':'ERROR','error':'ERROR','skipped':'SKIPPED','xfailed':'XFAIL','xpassed':'XPASS'}
                                counts={names[k]:int(n) for n,k in re.findall(r'(\d+) (passed|failed|errors?|skipped|xfailed|xpassed)\b',matches[-1])}
                                record['counts']=parser.validated_test_counts(text,counts)
                                record['parser_adapter']='legacy pytest seconds summary'
                            else: record['unscorable']=str(exc)
                    except subprocess.TimeoutExpired as exc:
                        text=str(exc.stdout or '')+'\n'+str(exc.stderr or '')
                        record['timeout']=True
                    (taskdir/(variant+'-'+suite+'.log')).write_text(text)
                except Exception as exc:
                    record['error']=str(exc)[-2000:]
                finally:
                    run(['docker','rm','-f',cid],timeout=30)
                    save()
                    print('CHECK '+json.dumps(record),flush=True)
    except Exception as exc:
        result['error']=str(exc)[-2000:];save();print('TASK_ERROR '+result['error'],flush=True)
print('ARTIFACT '+str(out/'readiness.json'),flush=True)
