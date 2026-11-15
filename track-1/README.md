# OpenAI model evaluation

The four-option evaluator uses the official OpenAI SDK. Add your existing `OPENAI_API_KEY` to the ignored `track-1/.env`. The key is never included in prompts, saved manifests or logs. Run the zero-network readiness check:

```sh
track-1/.venv/bin/python -m epistemics_dataset.openai_eval check
```

Model selection, reviewed evidence and reviewed instruction/peer templates are still pending. Live evaluation uses the existing tracked entry point and remains disabled during preparation. Setup and output details: `research/openai-evaluator.md`; model/settings: `configs/openai-eval.json`.

---

# Main experiment preparation

The main candidate set contains 300 distinct published Global-MMLU questions, each in English, Chinese and Vietnamese (900 question rows), across ten subjects. The earlier 20 development IDs are excluded. Source passages, translations and the model evaluator are still pending; these are not 300 approved experiment cases. See `research/main-experiment-plan.md` for the planned paired conditions and readiness checks.

Reproduce selection from the previously downloaded, checksum-verified snapshot:

```sh
track-1/.venv/bin/python -m epistemics_dataset.main_dataset --snapshot /path/to/project-artifacts/track-1/global-mmlu-pilot/upstream --output /path/to/project-artifacts/track-1/global-mmlu-main
```

This writes original question rows, review tasks, a fixed replacement queue, a condition plan and a provenance manifest. It makes no model or generation calls. Configuration: `configs/global-mmlu-main.json`.

---

# Current dataset: published Global-MMLU questions

The study now starts from **CohereLabs/Global-MMLU**, a benchmark used by the multilingual-pressure paper in `research/idea.md`. Synthetic examples and service-generated similar rows below are historical engineering checks, not the research benchmark. Automatic generation through the fixed runner is disabled while published evidence is being prepared (`workflow: published_data`).

`configs/global-mmlu.json` pins the upstream revision and file checksums. The read-only importer keeps original question IDs, wording, four answer choices, answer keys and metadata in English/Chinese/Vietnamese. It never fills missing translations or repairs upstream labels silently.

```sh
track-1/.venv/bin/python -m pip install -r track-1/requirements.lock
track-1/.venv/bin/python -m epistemics_dataset.global_mmlu --output /path/to/project-artifacts/track-1/global-mmlu-pilot
```

The public dataset can be downloaded without a key. If configured, supported HF token environment variables are read from the process or private `track-1/.env`; tokens are not logged or saved in manifests.

The pilot selects five complete, answer-consistent questions from each of four subjects, using a fixed hash ranking and the upstream culturally-agnostic label. This is a documented narrow development slice, not the exact 100-question sample from the pressure paper, nor a representative Global-MMLU score. Import reports record upstream answer-letter disagreements and incomplete rows excluded from selection. Different letters do not by themselves prove that a translated answer is factually wrong; these rows need separate review.

Outputs: `pilot-cases.jsonl` (20 aligned cases), `question-preview.md` (all three language versions), `evidence-tasks.jsonl` (unfilled source passage collection tasks), and `import-manifest.json` (checksums, selection, exclusions, licensing declaration). Dataset cards declare Apache-2.0; keep upstream attribution. **Supporting passages are still missing.** A `reference` metadata field is not a verified source excerpt. Existing translations and labels still need review.

Every pilot ID is development material and must be excluded from a later held-out evaluation. The study's future runner must support four choices, actual first answers, uncertainty and explicit evidence; the older two-option fixture builder is not a Global-MMLU evaluator.

Paper: *Global MMLU: Understanding and Addressing Cultural and Linguistic Biases in Multilingual Evaluation*, Singh et al., arXiv:2412.03304. Dataset: https://huggingface.co/datasets/CohereLabs/Global-MMLU

---

# Track 1 dataset preparation

## Current workflow: Adaption Adaptive Data

The default tracked job now uses **dedicated dataset services**, not individual model responses:

1. Upload four representative seed prompt/completion pairs using raw ingestion, preserving our input.
2. Estimate and request four generated **similar rows** with `datasets.augment(similar_rows=4)`.
3. Download the expanded English candidate pool.
4. Estimate and translate the whole pool into Chinese and Vietnamese with `datasets.translate(sample_rate=1.0)`.
5. Download raw rows, dataset/job IDs and a review queue. Never promote service-generated completions to trusted answer keys automatically.

If all rows are retained, four seeds + four new examples yield eight English rows and sixteen translated rows (24 total). These are expected counts, not verified output. New case identity, JSON structure and exact cross-language alignment are **checked after export**, not assumed from a service status. The SDK does not promise that similar rows preserve original case IDs; reused IDs or changed facts remain pending review.

A 25-credit cap applies to combined expansion/translation estimates. Unknown estimates stop launch. Requests use saved operation IDs and idempotency keys; state lives durably under the run output root's `adaptive-data/<operation-hash>/`. Restarting resumes saved IDs instead of creating replacement jobs. An ambiguous file-upload result requires recovering its ID rather than automatic re-upload. Provider polling timeout does not cancel provider processing.

The configuration is in `configs/pilot.json`. The fixed tracked runner remains `scripts/run.py`; it dispatches on the config's `workflow`. Credentials are read from the private .env path supplied to the runner and are never copied into the snapshot. No training job is launched. The previous Responses implementation remains below for reproducibility and offline checks, but is not the default service workflow.

Official documentation: [Generate similar rows](https://docs.adaptionlabs.ai/adaptive-data/expand-data/), [Translate dataset](https://docs.adaptionlabs.ai/api/resources/datasets/methods/translate). This pilot uses Expand and Translate. It does **not** call Invent, because we are extending our existing seeds.

---

# Earlier local/Responses workflow (retained)

Build controlled English (`en`), Simplified Chinese (`zh`) and Vietnamese (`vi`) dataset materials. Correct answers come from explicit seed facts and arithmetic, not model-generated labels. No evaluation model has been selected or run.

## What is here

- `research/`: original idea, closest-paper review, search provenance and dataset protocol.
- `configs/pilot.json`: languages, generator model, SDK version and peer count.
- `src/epistemics_dataset/`: seed builder, Adaption adapter, validators and variant assembly.
- `tests/`: gold-answer, corrupted-number, review-gate, cache and language-pair checks.
- `data/seeds/pilot.jsonl`: 20 deterministic synthetic cases in four families.
- `data/generated/`: ignored draft translations, API cache and assembled prompts.
- `data/reviewed/`: reserved for explicitly reviewed materials; no approved dataset yet.

The dataset contains labels for scoring. **Do not pass complete dataset rows to an evaluated model.** A later runner must select only question, instruction, options, permitted source and peer messages. Gold codes, provenance and condition labels are private evaluation metadata.

## Install (from repository root)

Use an isolated environment in this worktree. Python 3.9+; the SDK is pinned to 0.19.0. If uv is available, use the project's chosen tooling consistently; this machine currently uses venv/pip.

```sh
python3 -m venv track-1/.venv
track-1/.venv/bin/python -m pip install -r track-1/requirements.lock
track-1/.venv/bin/python -m pip install -e ./track-1 --no-build-isolation --no-deps
```

## Local checks: no API or credits

```sh
track-1/.venv/bin/python -m epistemics_dataset.cli doctor
track-1/.venv/bin/python -m epistemics_dataset.cli seeds
track-1/.venv/bin/python -m epistemics_dataset.cli templates
track-1/.venv/bin/python -m epistemics_dataset.cli validate
track-1/.venv/bin/python -m epistemics_dataset.cli build
track-1/.venv/bin/python -m unittest discover -s track-1/tests -v
```

`templates` uses local draft wording, not Adaption. It makes 60 language records. `build` makes 780 prompt records: 60 initial prompts and 720 revision prompts. The 720 comprise 540 source-present variants (nine conversation/source language pairs × three advice conditions × 20 cases) and 180 no-source controls. These are paired variants of **20 cases**, not 780 independent examples.

## Adaption-assisted translation

Configure `ADAPTION_API_KEY` in your process environment; never put the real key in Git. The SDK reads it automatically. No key is included or needed for local checks.

```sh
track-1/.venv/bin/python -m epistemics_dataset.cli adaption
```

This uses Adaption's documented `responses.create` SDK method to translate each fixed English question/source into Chinese and Vietnamese: at most 40 translation requests for the pilot. The generator model is configurable and unrelated to the later evaluation models. No automatic dataset optimization is applied to gold labels, IDs or facts. The broader Adaptive Data inventory/augmentation service is not called by this initial adapter.

Every successful translation is cached by seed, prompt, model and generation settings. Interrupted runs resume from validated caches. Records include SDK version, response ID, usage when available, request hash and timestamp. Automatic SDK retries are disabled to avoid blindly repeating a possibly charged request. A timeout may still have been processed remotely; inspect provider history before manually retrying.

The command fails clearly without credentials. It does not substitute a local template and claim an API success. The CLI reads `ADAPTION_API_KEY` from `track-1/.env` (or the file named by `TRACK1_ENV_FILE`) without overwriting an existing process key. Credentials and model-list access have now been checked successfully; translation output quality still requires generation and review.

## Validation and review

Automatic checks catch missing/duplicate language records, altered numeric facts and bad seed provenance. They **cannot** establish that translations preserve meaning. A fluent reviewer must check every pilot question/source, plus the shared instructions and scripted-advice templates. Also approve `shared_prompt_review` in the config after checking the shared instructions/advice. Mark each language record `review.status = "approved"` and record the reviewer's identifier only after that check. Re-review edited text. Do not simply bulk-toggle the field.

```sh
track-1/.venv/bin/python -m epistemics_dataset.cli validate --require-reviewed
track-1/.venv/bin/python -m epistemics_dataset.cli build --require-reviewed --output track-1/data/reviewed/pilot-variants.jsonl
```

These commands reject pending drafts. Review status is an audit declaration, not independently verified identity or a cryptographic guarantee.

## Research boundaries

These 20 cases are deliberately simple synthetic **engineering fixtures**, not a finished scientific benchmark. All translations and shared prompts remain unreviewed. Numeric validation is not semantic validation.

Fictional questions without a source are generally unknowable; `UNKNOWN` is a legitimate initial answer. Do not call an arbitrary guess a known factual belief. This pilot can check translation, source comprehension and pressure with supplied evidence, but cannot alone establish natural factual-belief correction. Before the main study, choose real factual questions with verified sources or a separately justified initial-evidence protocol. The later runner must collect actual initial answers, never invent them, and reuse them across matched branches. It must handle uncertainty as its own outcome.

Capacity cases are held out by task family as `pilot_validation`; other families are `pilot_development`. Every language/advice variant inherits the case's split. This tiny split is for engineering only and provides no statistical power guarantee. Additional case families and independent factual/source checks are needed before publication claims. Never filter evaluation cases based on desired pressure outcomes.

Durable review outputs retain their original project-artifact paths. Copies of the closest-paper review and query log are here for repository visibility; the artifact originals remain available under `sprint-review/track-1-closest-paper-check.md` and `sprint-review/track-1-closest-paper-search-log.json`.

SDK references: [Responses quickstart](https://docs.adaptionlabs.ai/inference-stacks/quickstart/), [Adaptive Data generation](https://docs.adaptionlabs.ai/adaptive-data/invent-a-dataset/). Translation here uses the Responses API for explicit case pairing rather than assuming that bulk-generated rows preserve experimental IDs.

## Tracked local generation

`scripts/run.py` is the fixed local generation entry point. It recreates a private venv from the committed lock, reads credentials from an explicitly supplied private environment-file path, generates and validates drafts, and copies successful outputs to a run-specific artifact folder. It requires a tracked run ID; use the project run launcher rather than invoking it as an unrecorded evaluation. No key is embedded in the command or source snapshot. CLI helper commands above remain available for lightweight local checks.
