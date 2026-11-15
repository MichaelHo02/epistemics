"""Dataset preparation: execute four independently verified paired families."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

root = Path(__file__).resolve().parents[2]
rows, assertions, builds = [], [], []
for target, other in [('temporary-publication','retired-auxiliary'), ('key-alpha','key-beta')]:
    for clarity in ('compact','explicit'):
        result = subprocess.check_output([sys.executable,str(Path(__file__).with_name('build_pair.py')),target,other,clarity],text=True)
        directory = Path(json.loads(result.strip())['output'])
        manifest = json.loads((directory/'manifest.json').read_text())
        pair = [json.loads(x) for x in (directory/'instances.jsonl').read_text().splitlines()]
        assert len(pair) == 2 and pair[0]['task'] == pair[1]['task']
        assert pair[0]['trajectory'][:7] == pair[1]['trajectory'][:7]
        rows.extend(pair)
        assertions.extend(manifest['state_assertions'])
        builds.append({'directory':str(directory),'manifest':manifest})
        print('BUILT ' + target + ' ' + clarity,flush=True)
out = root/'track-2/pilot/data'
data = out/'credential-pair.jsonl'
data.write_text(''.join(json.dumps(x)+'\n' for x in rows))
(out/'credential-pair-manifest.json').write_text(json.dumps({'dataset_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'state_assertions':assertions,'source_builds':builds,'limitations':['Eight histories from four miniature families.','Auxiliary credential is already inactive; wrong-target revocation is idempotent.','Compact outputs do not explicitly name the issued or checked key.','No independent human adjudication.']},indent=2))
