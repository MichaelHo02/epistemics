"""Fixed experiment entrypoint: check the unmodified upstream offline release."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
vendor = root / 'track-2/vendor/ObligationGuard'
interpreter = shutil.which('python3.12')
if not interpreter:
    raise SystemExit('Python 3.12 is required for this local readiness run.')
output = Path('/Users/michaelho/.local/share/openresearch/files/epistemics/sprint-review/track-2-systematic-review/upstream-readiness') / os.environ['ORX_RUN_ID']
output.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONPATH=str(vendor / 'src'), PYTHONDONTWRITEBYTECODE='1')
checks = [
    ('benchmark_validation', ['-m', 'obligationguard', 'validate', '--input', 'data/obligationbench.jsonl', '--benchmark']),
    ('upstream_unit_tests', ['-m', 'unittest', 'discover', '-s', 'tests', '-v']),
]
report = {'upstream_revision': '58f644a25e801cb19dca961ba6df0b354c640551',
          'commit': os.environ.get('ORX_COMMIT'), 'python': interpreter, 'checks': [],
          'limitations': ['No LLM inference or training evaluated.', 'Three upstream training files remain LFS pointers.', 'No Docker trajectory replay evaluated.']}
for name, arguments in checks:
    command = [interpreter] + arguments
    print('CHECK ' + name, flush=True)
    try:
        result = subprocess.run(command, cwd=vendor, env=env, text=True, capture_output=True, timeout=180)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code = str(exc.stdout or ''), str(exc.stderr or ''), 124
    (output / (name + '.stdout.txt')).write_text(stdout)
    (output / (name + '.stderr.txt')).write_text(stderr)
    print(stdout, flush=True)
    print(stderr, flush=True)
    report['checks'].append({'name': name, 'command': command, 'returncode': code})
report['all_passed'] = all(check['returncode'] == 0 for check in report['checks'])
(output / 'readiness.json').write_text(json.dumps(report, indent=2) + '\n')
print('ARTIFACT ' + str(output / 'readiness.json'), flush=True)
print('FINAL ' + json.dumps(report), flush=True)
sys.exit(0 if report['all_passed'] else 1)
