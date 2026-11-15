# Scope-aware verification preparation

Builds four representations of released cached claim-checker outputs. This is offline preparation, not an experiment. It does not call an AI model or read human labels.

Source repository: https://github.com/mos3b-faqeeh/agent-integrity-analysis
Pinned revision: `8284de5cf99c6a89320315b9f954c7b3ad0eb07e`
Input: `data/derived/confirmation_checker_vs_human.csv` at that revision.

```sh
/opt/homebrew/bin/python3.12 track-2/setup/scoped_verification/build_pack.py --input /path/to/confirmation_checker_vs_human.csv --output-dir /path/to/development-pack
```

The combined upstream CSV contains answers. The builder projects only an explicit allowed field set before constructing stimuli. Structured and field-matched text variants carry the same fields and values. Candidate source context is not represented as guaranteed experiment or metric alignment.

Published human traceability labels cannot automatically score a downstream task using incomplete snippets. Full claim context and evidence sufficiency must be reviewed before inference. The pack includes all 72 records; settings/extraction errors require exclusion from later scoring. See project artifacts under `sprint-review/track-2-systematic-review/scoped-verification-decision/` for the preparation outcome and validation.
