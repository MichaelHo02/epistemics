"""Fixed local run contract: recreate dependencies, generate draft data, validate/export."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run_id = os.environ.get("ORX_RUN_ID")
    if not run_id:
        parser.error("This entry point requires a tracked run")
    if not args.env_file.is_file():
        parser.error("Private local environment file is missing")
    env_dir = root/".venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = str(env_dir/"bin/python")
    subprocess.run([python, "-m", "pip", "install", "-r", str(root/"requirements.lock")], check=True)
    # Run directly from this immutable snapshot without sharing the worktree venv.
    env = dict(os.environ, PYTHONPATH=str(root/"src"), TRACK1_ENV_FILE=str(args.env_file))
    cli = [python, "-u", "-m", "epistemics_dataset.cli"]
    generated = root/"data/generated"
    destination = args.output_root/run_id
    import shutil
    succeeded = False
    try:
        subprocess.run(cli+["doctor"], env=env, check=True)
        subprocess.run(cli+["adaption"], env=env, check=True)
        subprocess.run(cli+["validate", "--output", str(generated/"quality-report.json")], env=env, check=True)
        subprocess.run(cli+["build"], env=env, check=True)
        succeeded = True
    finally:
        # Preserve partial successful caches and safe failure details after an interrupted run.
        if generated.exists():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(generated, destination, dirs_exist_ok=True)
        print(json.dumps({"status": "draft_generation_complete" if succeeded else "generation_failed",
                          "output_path": str(destination), "review_status": "pending",
                          "model_evaluation_calls": 0}), flush=True)



if __name__ == "__main__":
    main()
