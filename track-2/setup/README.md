# Docker setup check

Run from the repository root with Python 3.12:

```sh
/opt/homebrew/bin/python3.12 track-2/setup/check_docker.py
```

This is infrastructure setup, not a registered research experiment. It makes no model calls and reads no API key.

The script uses the upstream `capture_environment` function unchanged. Its command adapter requests `pid,comm` from Docker Desktop, which requires a PID column, then returns the command column expected by the upstream sleep-only check. It checks the official first SusVibes task image, restored file contents, isolation of changes, and rejection of a persistent `tail` process. Temporary containers and snapshot images are removed; the reusable downloaded task image remains cached.

Verified locally: amd64 task runs on ARM Docker Desktop; idle filesystem snapshots restore correctly; changes in the restored copy leave the original unchanged; a persistent process is rejected. Full process checkpoints remain unavailable because Docker experimental features are disabled. Idle mode is appropriate only when no persistent services need preserving. It does not demonstrate task completion, safety cleanup, Mini-SWE-Agent integration or guard accuracy.

Setup outputs are saved under project artifacts in `sprint-review/track-2-systematic-review/docker-compatibility/setup-<timestamp>/compatibility.json`. The reported Git commit identifies the base source; this initial verification ran the new setup script before its first commit.
