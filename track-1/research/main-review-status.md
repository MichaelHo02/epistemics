# Main dataset preparation status

The first English triage pass covers all 300 original candidates. The cumulative
v11 review has 262 draft evidence explanations and 38 holds. None is approved
for model evaluation. These are preparation counts, not model results.

A draft may still require a better source, a precise source passage, or a check
of an unstated assumption. In particular, indexed excerpts are explicitly
identified where a full source page could not be opened. A background reference
is not a published solution to a question. Independent calculations and proofs
are researcher derivations, not source quotations.

The 38 holds include missing figures or text, duplicated questions, possible
key errors, ambiguous alternatives, time-dependent claims, and unresolved source
questions. They are not 38 proven key errors. Original labels have not changed.

## Reproduce the accumulated review

Use the existing environment with `PYTHONPATH=track-1/src`. The reporting script
accepts repeated `--batch` arguments for every file under `data/reviews`, from
batch 02 through batch 11. Pass the existing main artifact directory as
`--dataset` and a new version label as `--version`. It preserves the original
selection, checks every language record for populated fields and matching answer
letters, and writes versioned candidates, source references, a report, and an
audit. Field agreement is not semantic translation review.

`prepare_replacement_review.py` verifies the pinned source checksums, replays the
original selection, and independently reconstructs the saved reserve ranking.
It writes a separate review bundle containing all 172 reserves and the first
38 proposed candidates for the nine subjects with holds. It does not replace or
approve any question. Review candidates in order and log each decision before
applying changes to a new selection version.

## Remaining work

1. Adjudicate holds and review enough same-subject reserves to retain 30 eligible
   questions per subject. Log all exclusions before seeing model outcomes.
2. Complete source and answer checks for retained English passages. Replace weak
   references; separate direct factual support from independent formal proofs.
3. Review original English, Chinese, and Vietnamese question meaning and answer
   equivalence for every retained family.
4. Translate only the retained supporting passages through Adaption's dedicated
   dataset translation workflow. Preserve stable IDs; no synthetic questions.
5. Review translations and peer/instruction templates; write signed-content
   hashes, final materials, and a complete manifest; run the data-readiness checks.

Do not launch an OpenAI key test or a model evaluation during this preparation
work. The existing OpenAI model setting remains unset; choosing the model is
separate from making the data ready.
