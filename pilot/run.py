"""Fixed tracked-run entry point; recreate the dependency environment per snapshot."""
import os
from pathlib import Path
import subprocess
import venv

root = Path(__file__).resolve().parent
if not os.environ.get('ORX_RUN_ID'):
    raise SystemExit('Launch through the experiment runner')
env = root / '.venv'
venv.EnvBuilder(with_pip=True).create(env)
python = str(env / 'bin/python')
subprocess.run([python, '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True)
subprocess.run([python, '-u', str(root / 'validate.py')], check=True)
subprocess.run([python, '-u', str(root / 'study.py')], check=True)

