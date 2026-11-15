# Main dataset preparation status

Completed: 300 question families, 30 in each of ten subjects. Every family has reviewed original English, Chinese and Vietnamese questions and reviewed supporting passages in all three languages. Original questions, options and answers match the pinned upstream snapshot exactly; none of the 20 development questions is included.

The final immutable snapshot is `artifacts/track-1/global-mmlu-main/final-v1/`. Its manifest, integrity audit, translation provenance and data-readiness report record the checks. The evaluator configuration now points to this snapshot. No OpenAI evaluation was run; model selection remains unset.

Review was performed by assistants, not independent human or blinded bilingual reviewers. Supporting translations include explicitly logged assistant corrections. The final selection contains 299 upstream CA-labelled questions and one unannotated astronomy question (astronomy/test/135), selected through the documented pre-outcome fallback. Report a CA-only sensitivity analysis when evaluating.

The following notes preserve preparation history; their earlier pending counts are superseded by the final snapshot.

## Earlier preparation history

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

## Candidate selection v2

A separate version now replaces the 38 original holds with 38 provisionally
retained reserves. The first 53 reserve questions were triaged in fixed order;
15 were excluded with recorded reasons. The new set still has 30 questions in
each of the ten subjects. No original question, option, or answer key was edited.
All 300 remain unapproved pending the final source and multilingual checks.

The first 300 draft English explanations have been pinned for translation-only
preparation through Adaption. Source and language review continue alongside this
step; changed English content requires a matching new translation. See
[evidence-translation.md](evidence-translation.md) for the exact safeguards.

## Remaining work

1. Finish adjudication of the provisional selection and review additional reserves
   if source or language checks uncover further problems. Preserve30per subject
   and log every exclusion before seeing model outcomes.
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


## Direct multilingual review checkpoint (15 November 2026)

The original questions and all four options have now been read side by side in
English, Chinese and Vietnamese for 180 candidate families: astronomy,
high-school mathematics, high-school physics, high-school computing,
college computing and computer security. The supporting passages in all three
languages have also been compared for the latter five subjects (150 families).
Astronomy supporting-passage review remains unfinished. These counts describe
assistant review, not an independent blinded human bilingual review.

Detailed findings are versioned under `data/reviews/material-review-*-01.json`
and `question-language-astronomy-*.json`. They bind the original question hashes
and, for material reviews, the translated-content hashes. They distinguish
question holds, evidence edits, unresolved terminology, source assumptions and
actual final approvals. A language pass does not automatically approve a source.
The separately recorded 22 mathematics and 19 physics families currently have complete
material approval; the full 300-family dataset remains blocked from evaluation.

New defects include changed convex/concave lens labels, flux translated as
current, heads-and-tails translated as heads-and-heads, a stack translated as a
haystack, and inconsistent code identifiers. A near duplicate physics family
is also excluded. Further holds include ambiguous original questions; they are
not all proven translation mistakes or wrong answer keys. Published question
text and labels remain unchanged. The next candidate version must incorporate
these findings in the saved within-subject reserve order before final readiness.

The peer/instruction templates have been compared across the three languages.
Participant labels now use the same neutral role, avoiding the Vietnamese
in-group role previously introduced by the wording. The protocol review records
its exact template hash and assistant-review limitation. Eight evaluator tests
passed after the wording change. No OpenAI request or key test was made.

Remaining direct multilingual subjects are conceptual physics, chemistry,
high-school biology and college biology (120 families), followed by replacement
review and final source adjudication. Existing draft translations can be reused
only when their bound question, English passage and source remain unchanged.
Changed English or new replacement passages need matching supplemental
translations through the authorized dataset workflow.


## Source adjudication follow-up

The conceptual-physics comparison adds 30 families, bringing direct question
language comparison to 210 families and three-language evidence comparison to 180.
Three conceptual-physics questions have material terminology errors; two
additional supporting passages need terminology edits. Their findings are in
`data/reviews/material-review-conceptual-physics-01.json`. Chemistry and the two
biology subjects remain to be compared (90 families).

`material-review-physics-02.json` finalizes 19 of the 30 high-school-physics families
using the cited primary rules and independent calculations. It supersedes the
pending-support fields only for those 19 rows in review01. The remaining 11
include four question-language holds, one near duplicate, and six cases requiring
further source/assumption decisions. In particular, the liquid-mixture question's
unqualified kinetic-energy wording was not automatically approved from a gas
translational-energy rule.

A fresh HTTP access attempt returned 403 for the Caltech lectures. Their displayed
original equations were then read using the web reader. NASA and NIST source
passages were read directly. Failed requests are not source verification. The
review locators identify the actual equations/sections used, and distinguish
those general rules from our own solutions to particular benchmark questions.

The local evaluator readiness check now recognizes 41 reviewed families and 259
pending families in candidate v2. It still refuses a full run. This check makes
zero network calls, leaves the model unset, and does not change the production
evaluation configuration to point at an unfinished candidate selection.


## Parallel review handoff: all300English families

The combined candidate version3has300unique published question families,
30per subject, with all original English/Chinese/Vietnamese rows checked against
the pinned upstream snapshot. There is no overlap with20development questions.
Every English supporting passage has a source/answer/reuse review. The combined
local readiness check recognizes213approved trilingual families;87need matching
supplemental translations and review. No model evaluation has occurred.

The final candidate hash is
`b4b43ea7568d67ba1d57f7bf5bf25fbb59fff193d1015078f7af8442fddb7fe0`.
The manifest records299upstream-CA questions and one manually assessed unannotated
astronomy addition, `/135`. The eligibility amendment and skipped fallback `/85`
are logged before outcomes in the experiment plan and replacement ledger.
Do not describe this slice as entirely upstream-CA.

The topic handoffs are under the four `data/reviews/parallel-*` folders and matching
artifact folders. The supplemental87English passages are frozen separately in
`global-mmlu-main/translation-input-v3`; their checksums and candidate hash are
bound by the translation configuration. The earlier66-row input-v2was prepared
but superseded before any service request, when biology completed its21rows.

Only after the supplemental Chinese and Vietnamese passages have been reviewed
can all300materials be finalized. The OpenAI model remains unset, and no key test
or evaluation request is authorized in this preparation goal.
