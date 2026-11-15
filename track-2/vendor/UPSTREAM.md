# ObligationGuard upstream checkpoint

Repository: https://github.com/THU-Agent/ObligationGuard

Revision: `58f644a25e801cb19dca961ba6df0b354c640551`

The `ObligationGuard/` directory contains every file from this revision's Git
tree. File bytes were independently checked against the upstream Git blob IDs;
the complete inventory and SHA-256 hashes are in
`obligationguard-upstream-manifest.json`.

The sole path adjustment is `.gitattributes` → `.gitattributes.upstream`, preserving
its original bytes without applying upstream LFS filters to our repository.
Three large training files remain the original upstream Git LFS pointers. The
240-case benchmark, validation data, source, tests, prompts, configs, documentation
and supplementary PDF are present. Fetch the training objects from the upstream
release before training; a pointer is not training data. No trained model weights
are included. No upstream license file was present in this Git tree; this import
does not invent or replace upstream licensing.

Initial checkpoint deliberately precedes test execution. The original source is
unmodified. Local integration and readiness findings should be kept outside this
directory, or recorded as explicit patches with provenance.

Offline starting points (Python 3.11+):

```sh
cd track-2/vendor/ObligationGuard
PYTHONPATH=src python3 -m obligationguard validate --input data/obligationbench.jsonl --benchmark
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

These are upstream's lightweight validation and tests. Do not start training,
container workloads or model/API evaluation through `scripts/run_all.sh` just to
check installation. Our tracked readiness runner will use the existing fixed
Track 2 command and explicitly report dependencies and skipped capabilities.
