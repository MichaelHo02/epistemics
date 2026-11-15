# Offline verification-menu preparation

`check_menu.py` checks a proposed manipulation using the released DIVA finance pilot model. This is preparation, not an LLM experiment or a novelty result. It makes no API calls.

Source: https://github.com/seunghan96/diva/tree/d3fb499629d8d2420cf943e3d09338d75df373b3

The standard-library DP follows the documented recurrence in `envs_synth/core.py`; upstream code is not imported. Supply the pinned `envs_synth/data/binary/finance_pilot.jsonl.gz`:

```sh
/opt/homebrew/bin/python3.12 track-2/setup/verification_budget/check_menu.py --input /path/to/finance_pilot.jsonl.gz --output /path/to/menu-validation.json
```

The validator reproduces stored original-budget values, fixes a three-check budget, adds four positive-cost state-independent checks, and compares optimal value and move sets throughout original-check histories. A perfectly informative added check is the positive control. Full results and overlap assessment live in project artifacts under `sprint-review/track-2-systematic-review/verification-budget-direction/`.
