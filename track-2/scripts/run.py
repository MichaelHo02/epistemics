"""Real official task-image and upstream snapshot compatibility; no model calls."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import urllib.request

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'track-2/vendor/ObligationGuard/src'))
from obligationguard.container_state import capture_environment

out = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/docker-compatibility') / os.environ['ORX_RUN_ID']
out.mkdir(parents=True, exist_ok=True)
report = {'commit': os.environ.get('ORX_COMMIT'), 'checks': {}, 'model_calls': 0}
containers = []
tag = 'epistemics-check:' + os.environ['ORX_RUN_ID'][:8]
snapshot_created = False

def docker(*args, **kwargs):
    return subprocess.run(['docker', *args], capture_output=True, text=True, timeout=kwargs.get('timeout', 90), check=True).stdout.strip()

def save():
    (out / 'compatibility.json').write_text(json.dumps(report, indent=2))
    print('STATUS ' + json.dumps(report), flush=True)

try:
    report['server'] = json.loads(docker('info', '--format', '{{json .}}'))
    # Store only relevant public server properties.
    report['server'] = {k:report['server'].get(k) for k in ('ServerVersion','OSType','Architecture','ExperimentalBuild')}
    url = 'https://raw.githubusercontent.com/LeiLiLab/susvibes/520f16f9b3f39b06c6013bc0eb57a38280b4deee/datasets/default/susvibes_dataset.jsonl'
    with urllib.request.urlopen(url, timeout=30) as r:
        task = json.loads(r.readline())
    report['task'] = task['instance_id']
    image = task['image_name']
    report['image'] = image
    save()
    docker('pull', '--platform', 'linux/amd64', image, timeout=300)
    report['image_metadata'] = json.loads(docker('image','inspect', image))[0]
    report['image_metadata'] = {k:report['image_metadata'].get(k) for k in ('Id','Architecture','RepoDigests')}
    cid = docker('run','-d','--platform','linux/amd64','--entrypoint','sleep',image,'600')
    containers.append(cid)
    probe = docker('exec', cid, 'sh','-c', 'uname -m; test -d /project; cd /project; git rev-parse HEAD; python --version')
    report['checks']['task_execution'] = {'passed': True, 'output':probe}
    docker('exec',cid,'sh','-c','printf before-cleanup > /tmp/epistemics-state-marker')
    class Config:
        executable = 'docker'
        def model_dump(self, **kwargs):
            return {'executable':'docker','image':image,'cwd':'/project','run_args':['--platform','linux/amd64']}
    env = SimpleNamespace(config=Config(), container_id=cid)
    try:
        capture_environment(env, out / 'checkpoint', tag, 'checkpoint')
        report['checks']['process_checkpoint'] = {'passed':True}
        snapshot_created = True
        # Restart original so the idle snapshot check can proceed.
        docker('start',cid)
    except subprocess.CalledProcessError as exc:
        report['checks']['process_checkpoint'] = {'passed':False,'error':exc.stderr[-2000:]}
    save()
    snapshot = capture_environment(env, out / 'idle-snapshot', tag, 'idle_container')
    snapshot_created = True
    restored = docker('run','-d','--platform','linux/amd64','--entrypoint','sleep',snapshot['image'],'600')
    containers.append(restored)
    before = docker('exec',restored,'cat','/tmp/epistemics-state-marker')
    docker('exec',restored,'sh','-c','printf after-cleanup > /tmp/epistemics-state-marker')
    original = docker('exec',cid,'cat','/tmp/epistemics-state-marker')
    after = docker('exec',restored,'cat','/tmp/epistemics-state-marker')
    assert before == original == 'before-cleanup' and after == 'after-cleanup'
    report['checks']['idle_snapshot_restore_isolation'] = {'passed':True,'restored_initial':before,'original_after_branch_change':original,'branch_after_change':after}
except Exception as exc:
    report['failure'] = {'type':type(exc).__name__, 'detail':getattr(exc,'stderr','')[-2000:]}
finally:
    for cid in containers:
        try: docker('rm','-f',cid)
        except Exception: pass
    if snapshot_created:
        try: docker('image','rm',tag)
        except Exception: pass
    save()
    print('FINAL ' + json.dumps(report), flush=True)
    print('ARTIFACT ' + str(out / 'compatibility.json'), flush=True)
