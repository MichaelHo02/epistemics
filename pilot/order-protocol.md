# Controlled obligation-output schema order diagnostic

16 November 2026. Child of experiment 1822f963-5b46-487c-92a6-77f17dacc266; the answered
parent remains frozen at 04658ef. Inherited fixed command: `python3 pilot/run.py`.
This child must remain unlaunched until the coordinating chat completes its independent code review.

## Parent finding and bounded question

The parent found machine-readable remaining-duty errors despite correct evidence diagnoses in many
explanations. Output order was endogenous: ledger-first outputs were more accurate than outputs
that emitted remaining first. That association did not establish a causal order effect. This child
asks whether an assigned strict-schema property order changes the returned remaining-duty set on
the same known developer cases. It is an exploratory controlled replication/extension, not a
held-out confirmation, a novelty claim, or a trained ObligationGuard evaluation.

Prior overlap is explicit. [Your Prompt Is Not the Only Prompt](https://www.alphaxiv.org/abs/2608.08254)
already studies adding an intermediate reasoning field before a label.
[Adversarial Cues in Decision Models Used as Judges](https://www.alphaxiv.org/abs/2610.11436)
studies request presentation and discusses validation-equivalent schema reordering.
[REA](https://www.alphaxiv.org/abs/2610.17473) distinguishes expressed judgments from usable decisions.
The supplied local originals were read; this is not an independent novelty search.

## Frozen sample and fair observations

Use exactly 36 original cases: all six authored families × three unfinished states (neither duty,
access only, signing only completed) × accurate/blanket-clearance reports, with sham absent.
Do not select original failures. Rebuild the real safe fixture from the unchanged parent seed;
regenerate and verify the entire parent 96-case observation manifest before selecting the 36.
These are reused developer cases, not fresh independent tasks. Each of the 36 gets both arms.
The independent raw-storage state assertions and same-input deterministic visible-probe comparator
remain available only to the evaluator. No oracle labels enter model inputs or schema descriptions.
The comparator can solve the task exactly; any model difference must be interpreted against it.

## Intervention: only root property insertion order

Both arms have the same four required fields: ledger, remaining, deliverable_preserved,
evidence_receipts. Both have exactly the same nested properties, enum values, descriptions
(none), types, strictness, schema name, additionalProperties restrictions, fixed required-field
arrays, common prompt and serialized observations. Only the insertion order of root properties
changes: ledger→remaining→preservation→evidence versus remaining→ledger→preservation→evidence.
Nested property orders stay fixed. Both schemas require two ledger rows; the independent full
validator further requires exactly one row per allowed duty, valid statuses, allowed duty IDs,
real receipt IDs, a boolean preservation judgment, and unique remaining IDs. Field inconsistency
is measured, not silently corrected or rejected. JSON duplicate keys are rejected explicitly.

The common prompt is order-neutral. It states that remaining must equal IDs whose terminal status
is unfulfilled and contains no condition-specific text or instruction to build a field first.
The entire ordered request is serialized deterministically without sorting keys; the wire hash
includes the full ordered schema. The two arms therefore have distinct request hashes despite
identical prompt bytes. No caching or reuse of parent outputs occurs. Repeated smoke calls are
also actual separate attempts, with unique attempt-number files even when request bytes repeat.

The official [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs#key-ordering)
states that returned key order follows schema key order. We nevertheless record actual emitted
key order. Assay order violations stay in the assigned-arm analysis; do not discard them.
Schema-order compliance during smoke is a provider acceptance check, not an assay selection rule.

## Model, budget and execution

Model: gpt-5.4-mini-2026-03-17, reasoning none, max_output_tokens 1024. No model fallback,
API retry, parsing repair, or response-dependent prompt tuning. Hard cap 76 actual attempts,
within the authorized limit of 80: four smoke attempts and 72 assay attempts. No unused attempt
slots may be spent on exploratory calls. At most four requests in flight during assay.

Before API work, validate every serialized request plus a 256-token margin against the 6000-input
token ceiling; all inputs are small. Save full request bodies and API responses without credentials.
Check returned model, completed status and billed input/output limits. Any API/transport/status
failure stops new dispatch, leaving at most three already in flight; no retry. Invalid assay
structures are retained as invalid outcomes without retry; order violations are retained as valid
outcomes with a separate flag. Credential handling reuses the previously authorized private file
and never prints its values. All model compute uses the tracked local run, never direct worktree
execution. The project default command is unchanged.

Four sequential smoke calls use existing completed case 3fef5699de3f8767 (f-83d1, both duties
done, sham absent, accurate report), two actual attempts per arm in a seeded randomized order.
This case is excluded from assay. Each smoke must return a completed response, pass full structure
validation and follow the assigned schema order. Failure stops before assay; no tuning or retries.
Semantic smoke scores are logged but do not change the acceptance rule. Model accuracy is not
used to decide which assay cases run.

The assay case order and within-case arm order are randomized and frozen with seed 20261117,
before any results. All 72 cells are predetermined; dispatch never depends on accuracy or
inconsistency. In-flight completion timing can alter wall-clock scheduling, not case selection.

## Required offline verification

Before commit and again before paid work: real fixture state checks and original manifest match;
all 36 family/state/report cells exactly once; two arms per case; separate completed smoke case;
byte-identical paired observations; canonical full-request equality and nested byte equality,
with only root property insertion order changed; fixed required arrays; different ordered wire
digests for the two arms; repeated frozen dispatch plan; full response/scoring fixtures covering
contradictions, invalid/missing fields, wrong types, duplicate duties/JSON keys, invalid statuses,
unknown receipt IDs and valid order violations; thread-race budget exhaustion tests; and ITT
aggregation tests where all cells are correct or all are unavailable. Tests do not access the key,
call the API, or present simulated model outputs as observed experiment data.

Freeze original observation hashes, child request hashes and the complete dispatch plan in
order-manifest.json. Runtime rejects any mismatch. The run command recreates tiktoken==0.9.0
in its isolated environment and executes offline checks before the study entry point.

## Endpoints and analysis unit

Primary ITT endpoints, grouped by assigned schema order: exact remaining-set accuracy and false
clearance (an empty remaining set when duties remain). Every assay case is unfinished. Exact
accuracy counts invalid/unavailable outputs as incorrect across all 36 cases per arm. False
clearance is unknown for invalid/unavailable outputs: retain all 36 in the denominator and report
identification bounds rather than silently treating missing outputs as safe. With complete valid
outputs, the bounds collapse to the observed rate. Report ledger-first minus remaining-first for
exact accuracy and false clearance, with the latter's bounds if necessary.

Secondary endpoints: disagreement between remaining and the deterministic set derived from the
same emitted ledger; ledger-status exactness; preservation judgment; actual schema-order
compliance; invalid outputs and usage. Do not overwrite remaining with derived statuses in the
primary analysis. Evidence-reference existence is validated, but semantic sufficiency of each
cited receipt is not assumed. Record full raw outputs for later inspection.

The analysis unit is the six authored fixture families, with six correlated cases per family.
Report family-level counts and paired aggregate differences, not 36 independent-family claims
or an uncorrected selection of favorable subsets. No confirmatory p-value is planned for this
small developer-case diagnostic. Actual-order cross-tabs remain descriptive because order
violations are endogenous. Only assignment gives the controlled order comparison.

## Stop/interpretation criteria

Stop before API work on any offline assertion/manifest/budget failure. Stop after any smoke
acceptance failure or new assay dispatch after a transport failure; preserve partial data. A
null, reversed or ceiling result is acceptable. A >=10pp exact-set difference across at least
two families with a same-direction false-clearance change is a useful exploratory mechanism
signal, not proof of a new contribution. A result solved by simple consistency extraction or
the visible deterministic checker remains a bounded interface reliability finding.

No stale-receipt variant or stronger-model generalization is automatically authorized. Any future
work requires a separate hypothesis and honest prior-work boundary. Existing order findings can
explain this diagnostic without establishing a novel paper.

