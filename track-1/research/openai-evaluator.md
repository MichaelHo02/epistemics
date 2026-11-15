# OpenAI evaluator

Implementation: `src/epistemics_dataset/openai_eval.py`. It uses the pinned official OpenAI Python SDK (2.48.0) and Responses API with a strict JSON schema. No live API call has been made to validate account access. SDK requests are verified with a local HTTP mock, not mocked SDK method signatures alone.

## Private key

The user chose to supply an existing key. Add `OPENAI_API_KEY` to the existing ignored `track-1/.env`, or set it in the launch environment. Never paste the key into chat or commit it. The checker reports presence only. The client explicitly uses the official API endpoint; it does not take an alternative provider URL from environment variables.

## Offline checks

```sh
track-1/.venv/bin/python -m pip install -r track-1/requirements.lock
track-1/.venv/bin/python -m epistemics_dataset.openai_eval check
track-1/.venv/bin/python -m unittest discover -s track-1/tests -v
```

`check` is the default preparation action: no client is created and no network request is made. It reports blockers and the planned call count. A passing software test does not approve the research material.

## Configuration and model

`configs/openai-eval.json` contains data/output paths, a candidate-set hash, call/output-token limits and timeout. The model is deliberately unset until the research model is selected. Use an explicitly named snapshot when available. Optional `temperature` and `reasoning` fields are omitted from requests when null; set only options supported by that model. Do not silently change the model after inspecting results. Output-token requirements depend on reasoning settings; an incomplete response is saved, never accepted as a valid answer.

Instructions and three-peer templates are drafted in English, Chinese and Vietnamese. Their review is pending. Record `protocol_review.status = approved`, reviewer and the exact `templates_hash` reported by the checker only after actual review.

## Reviewed evidence input

The main selection and unreviewed tasks remain intact. Put approved rows in a separate `evidence-reviewed.jsonl` beside `main-cases.jsonl`. The evaluator does not import draft candidates automatically. Each question needs exactly one row with:

- `sample_id`, `source_url`, `passage_en`, `passage_zh`, `passage_vi`;
- `question_review`, `support_review`, `reuse_review`, `language_review`, all `approved`;
- `approved_for_experiment: true` and nonempty `reviewer`;
- `reviewed_question_hash`: digest of the exact selected case;
- `reviewed_content_hash`: digest of a dictionary containing only `sample_id`, `source_url`, `passage_en`, `passage_zh`, `passage_vi`.

Use the project `seeds.digest` function for both hashes. Hashing prevents stale approvals after editing; it is not an independent review. Source-specific license/permission decisions belong in the evidence dossier. Question review must cover answer correctness and equivalence of original translations. The checker requires all 300 questions to pass, not just a convenient subset.

## Conversation and caching

For each question-language pair, the model first chooses A/B/C/D or UNKNOWN and gives confidence. Only the question, four options and output instructions are sent. Gold labels and reference metadata are kept outside that request. The actual first response text is reused verbatim in every branch. Gold labels are used privately to construct the scripted correct advice; one incorrect option is chosen deterministically per question using the configured salt and reused across languages and source conditions.

Each branch independently appends neutral reconsideration or three matched scripted peers, with no source or one source language. No live peer model is involved. Branches do not see other revision answers. The model has no browsing or tools.

Each attempted request is recorded before network I/O. Completed responses, output text, provider request/response IDs, returned model and token usage are saved to the cache. Secret headers and provider error messages are not logged. SDK retries are disabled. Errors are cached and stop that invocation; a restart will not silently retry them. A request interrupted in an unknown billing state requires inspecting its cache entry before retrying. Output-token limits, refusals, malformed responses and UNKNOWN remain distinct. Failed initial responses get no fabricated revision branches.

The cache permits restart after a partially completed run. A changed request, model or SDK version has a different cache key. Dataset/protocol/evidence changes create a separate result directory with a saved materials snapshot. Distinct question IDs retain distinct initial draws even if their prompt text matches. Derived measurement rows are rebuilt from cached responses on restart, avoiding duplicated appended records. Run only one worker against a given output/cache directory.

## Tracked launch wiring

The fixed `scripts/run.py` now supports `workflow: openai_evaluation` in `configs/pilot.json`, dispatching to this evaluator. The existing `published_data` setting is retained while preparation is incomplete. Launch live evaluation only as a committed child experiment through the project experiment runner. Calling `openai_eval run` directly outside a tracked run is rejected.

Outputs are `manifest.json`, `measurements.jsonl`, `execution-summary.json` and `counts.json`, plus a request cache. Counts separate correct-to-wrong changes, wrong-to-correct changes, UNKNOWN and missing results. They are descriptive counts, not statistical significance claims. Uncertainty intervals and question-level paired analysis remain future analysis work.

## Remaining before a full run

Finish evidence and translation reviews, choose a model snapshot, review all instruction/peer wording, estimate cost using that model and expected input lengths, then commit the exact dataset/protocol snapshot. The 11,700-request cap is a request-count limit, not a dollar budget; reasoning/output tokens can materially change cost. Passing preflight does not validate model access or the cost estimate.

Official references: https://developers.openai.com/api/docs/guides/structured-outputs and https://github.com/openai/openai-python
