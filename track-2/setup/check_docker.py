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
import obligationguard.container_state as container_state
from obligationguard.container_state import capture_environment

# Docker Desktop requires PID in docker top output; retain upstream sleep-only guard.
_original_command = container_state.docker_command
def portable_command(executable, *arguments):
    if len(arguments) == 4 and arguments[0] == "top" and arguments[2:] == ("-eo", "comm"):
        text = _original_command(executable, "top", arguments[1], "-eo", "pid,comm")
        return "\n".join(line.split(None, 1)[1] for line in text.splitlines() if len(line.split(None, 1)) == 2)
    return _original_command(executable, *arguments)
container_state.docker_command = portable_command

from datetime import datetime, timezone
setup_id = datetime.now(timezone.utc).strftime('setup-%Y%m%dT%H%M%SZ')
out = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/docker-compatibility') / setup_id
out.mkdir(parents=True, exist_ok=True)
report = {'commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(), 'checks': {}, 'model_calls': 0}
containers = []
tag = 'epistemics-check:' + setup_id[:8]
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
    try:
        docker('image', 'inspect', image)
    except subprocess.CalledProcessError:
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
    # Confirm the portability adapter still refuses to lose a persistent process.
    docker('exec', cid, 'sh', '-c', 'tail -f /dev/null >/tmp/epistemics-tail.log 2>&1 &')
    from obligationguard.errors import ConfigurationError
    try:
        capture_environment(env, out / 'must-reject', tag, 'idle_container')
    except ConfigurationError:
        report['checks']['persistent_process_rejected'] = {'passed': True}
    else:
        raise AssertionError('idle snapshot accepted a persistent process')
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

if 'failure' in report:
    sys.exit(1)
