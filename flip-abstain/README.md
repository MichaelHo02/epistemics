# Flip & Abstain: do LLMs say "I don't know" before and under pressure?

Hackathon project on LLM honesty. Measures (a) whether a model keeps a correct answer and keeps saying UNKNOWN on unanswerable questions when a user pushes back (simple, fake citation, authority, emotional), and (b) how well models abstain on unanswerable questions *before* any pressure, split by question type.

- `run2.py` main runner (OpenAI via Braintrust proxy; DeepSeek/Qwen/GLM via the Adaption `responses` API). Keys come from env vars `BRAINTRUST_API_KEY`, `ADAPTION_API_KEY`.
- `items3.json` final 66 items (27 answerable + 39 unanswerable from AbstentionBench KUQ; pressure claims written with Adaption). Three ambiguous items are excluded in analysis.
- `judge.py` two blind LLM judges (gpt-5-mini, gpt-5) classify non-UNKNOWN replies as committed / hedged / premise-flagged.
- `ablate.py` one-line "check the premise" system-prompt fix, 3 runs.
- `results/` raw transcripts and summaries (note: scripts expect `results_v3*` at repo root; move them up to rerun). `mlam.md` is the running lab log. `report.md` is the write-up draft.
- `adapt/` dataset loading and Adaption pipeline scripts. The AbstentionBench data itself is not included.

Synthetic data only, no personal data. See the limitations in `report.md`.
