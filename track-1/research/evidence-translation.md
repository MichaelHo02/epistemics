# Supporting-evidence translation

The dedicated Adaption dataset workflow uploads the selected English supporting
passages and translates every passage into Simplified Chinese and Vietnamese.
It does not call augmentation, rewrite benchmark questions, supply benchmark
answer keys to the service, or invoke an OpenAI model.

The first input snapshot contains 300 draft English passages for candidate
selection v2. Translation can proceed while the final source and original-question
language reviews continue. This is a scheduling change from doing every review
before translation; it does not weaken the final evaluation gate. Any changed
English passage, source URL, or question content gets a different content ID and
requires its own matching translation. Unchanged reviewed translations can be
reused. No translation success counts as evidence or bilingual approval.

## Reproducibility and checks

`configs/evidence-translation.json` pins source file checksums, the question
selection hash, the SDK version, two target languages, full sampling, and a
25-credit operation cap. Input snapshots live in the existing main-study
artifacts folder. This is a local-backend recipe because the fixed runner reads
those durable local artifacts; it must not be moved to a remote host without
explicit input transport.

The immutable run entry point dispatches `workflow: evidence_translation` to
`epistemics_dataset.evidence_translation`. That module saves upload and translation
dataset IDs, estimates before launching, uses a stable idempotency key for the
translation operation, and saves raw exports. SDK automatic retries are disabled.
An interrupted upload with an uncertain result is not silently repeated.

Each uploaded row has a marker containing the sample ID and content hash. The
translation export must preserve that marker and provide explicit language and
translation-join metadata. Reconciliation requires exactly one original,
Chinese and Vietnamese row per family, an unchanged original English passage,
and one provider join ID that belongs to only that family. Conflicting columns,
unknown markers, duplicates, missing languages or inconsistent joins are
quarantined; order-based pairing is forbidden.

Outputs are `multilingual-evidence-raw.jsonl`, `translation-candidates.jsonl`,
`translation-report.json`, and resumable `state.json`, under a content-addressed
folder. All candidates remain unapproved. Meaning, negation, mathematical
symbols, numbers, causal claims and qualifying assumptions require review before
final materials can pass the evaluator's content-hash gates.

## Selection checks

`apply_replacement_decisions.py` constructs a new candidate version without
changing the original. It validates review hashes, exact per-subject allocation,
unique IDs, and the complete reserve prefix through the last retained candidate.
Every skipped reserve has an exclusion reason. Decisions cannot approve model
evaluation. A real-data check rejected a skipped reserve, forged rank and premature
approval before writing any output.
