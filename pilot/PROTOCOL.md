# Precision-aware verifier diagnostic — exploratory protocol

## Question and hypothesis
Does an automated numerical checker use the supplied precision contract when deciding whether a change is contradicted, entailed, or unresolved? Hypothesis: explicit interval reasoning reduces false refutation and overclaiming relative to an equally informed direct prompt. The same numbers are tested under exact-level and rounded-level contracts. This is calibration of a practical false-accusation audit, not a claim to invent interval arithmetic or prove a novel failure class.

## Source population and transformations
Nine fixed seasonally-adjusted percentage rows: unemployment, underemployment and participation from Jan/Feb/Mar2025 ABS Labour Force release pages. Source tables automatically extracted and inspected before model responses; source URLs, hashes and table excerpts committed. Full retrieved HTML snapshots retained in artifacts. Pages retrieved on 2026-11-16 may include publisher updates; no original-publication-version claim. Never mix values from different release vintages.

Each native reported change is tested unchanged, plus +0.1pp and +0.5pp synthetic variants. Each is tested under stipulated exact levels and closed +/-0.05 level intervals: 54 paired cells. Exact-level semantics are counterfactual and do not describe the natural source's precision. The claimed change always denotes a closed +/-0.05pp band. Closed endpoints define this assay and do not claim to reproduce the publisher's exact rounding tie-breaking rule. Published-change column is withheld from model evidence except through the tested claim. Model task is evidence compatibility, not whether the ABS made a true statement.

## Methods and ground truth
Two prompts receive identical values, label definitions and precision rules: direct judgment vs an interval-computation reminder. Model gpt-5.4-mini-2026-03-17, reasoning none. Strong deployable reference is exact integer interval computation from the same public inputs and contract, checked against a separately implemented exhaustive endpoint/midpoint enumeration. Point-estimate subtraction is a deliberately simple baseline, labelled accordingly. An interval-compatible claim is not automatically entailed. Invalid JSON counts as failed, no repair/retry.

## Outcomes and inference limits
Primary: false-refutation rate on compatible rounded-evidence cells; secondary exact three-way accuracy, overclaiming support for unresolved cells, response validity and precision-sensitive label changes. Report all rows and variants. The source release is the coarsest dependence unit (only 3), row is the pairing unit (9); 54 variants are not independent natural claims. No confirmatory significance, natural-error prevalence or deployment-benefit claim.

## Gates and stop criteria
Validate all labels and precision-reversal controls before any API calls. Stop on dependency/API failure; preserve partial outputs; maximum two engineering repairs per node. Do not expand if both prompts are at ceiling, effects only restate elementary rounding, or a simple deterministic parser/calculator already resolves the practical use case. Any later paper claim requires independent natural claim extraction, source/definition/vintage handling, held-out labels and utility beyond the exact baseline; this pilot alone cannot meet that bar.

## Compute and provenance
Independent root, separate code/data from briefing and defense studies. Fixed python3 pilot/run.py; local backend, snapshot-local venv, tiktoken==0.9.0. User-authorized existing API key; never printed or committed. At most 160 uncached requests, 6000 input tokens and 1024 output tokens per request, no retries; nominal request count108. Effective config, cases, full prompt/responses, measurements and summary saved under pilots/numerical-precision/<run>.

## Sprint path
Track4 → Open Track → Do their numbers match? The controlled compatibility component also fits Track1 measurement validity and Track2 citation verification. No organizer endorsement or novelty certification.

## Status before launch
Independent exact-reference and boundary checks passed for all 54 cells; no model outcome observed.
