# Heterogeneous truthful-copy readiness and bounded downstream pilot

Protocol fixed before the first readiness run. Parent: ef15f873-db7a-4431-a8ed-a307fec4b9d5, frozen commit 57dad82, run 569dcc54-7dae-480a-a71e-af84f5e0c78a. Child: 507bb756-e0cc-4274-bc48-bc0f4042ebdb.

## What the parent established

The templated register pilot had zero clean support retention under the published filter, so its intended incremental-copy contrast was unidentifiable. This child tests a distinct material hypothesis: independent prose domains should eliminate that clean floor while allowing copy-specific support loss to be measured. It changes materials, not filter thresholds. This is a development mechanism check, not a claim of a new attack or defense.

## Frozen material and interventions

Twelve author-written fictional entity families in `materials.py`, seed 981273. Each has one approximately paragraph-length support passage and four factual distractors spanning independent domains. Support domains: horticulture, astronomy, theatre conservation, drilling geology, bakery logistics, wetland ecology, ceramics, ice-core preservation, mechanical clock repair, marine acoustics, seed conservation and public transit. Names are invented; target answers are seeded four-digit identifiers with no real-world truth claim. No passage is taken from a benchmark or generated using filter feedback. Different templates, entities, fields and prose contexts are frozen before any filtering run.

All five original passages remain byte-identical in every condition. Conditions add nothing (clean), two exact support copies, two exact copies of the designated first distractor, or two copies of support with only the target code replaced by a conflicting code. Original support position rotates over five slots; additions are prepended on odd case IDs and appended on even IDs. Distractor selection is a fixed modular schedule, and every distractor domain appears four times. Different passage lengths are retained and reported, not optimized against the filter. The false-copy condition has no authenticated source priority; it measures responses to synthetic conflict, not attack security.

All twelve families and all conditions run under no filter, original published filter, and exact deduplication before that same filter. No retain-one repair is proposed. Labels score support and answers only; neither the filter nor the reader sees policy or condition labels. Original upstream source, SHA256 9c3e79600525756c1938f64f14cb1cfae3961c0a108d04ff6eec1a487634832d, and its license are byte-preserved. Functions are compiled from that file without editing their AST bodies. CPU SimCSE model revision 2d82fab19ac3a73a20dd20333d27eb8a52d6e97f uses the original final-layer CLS representation. Model truncation is forbidden; torch intra/inter-op threads are two; only one local embedding job runs at a time. Dependencies including inherited transitive package versions are pinned and recreated in the run snapshot's private venv.

## Zero-API readiness stage: all 144 cells

The first tracked run contains 12 families x 4 conditions x 3 policies. No API object is instantiated and no credential is read. Save complete cases, every input and kept list, embeddings/index, package/source hashes, filter warnings, paired retention metrics and summary. No failures or cases may be discarded, resampled, paraphrased or replaced after outcomes.

The published-filter progression gates, all required, are:

1. Clean support retained for at least 8/12 families.
2. Among clean-support-retained families, the number losing support under true copies minus the number losing support under distractor copies is at least 4/12.
3. At least four families retain support under both clean and distractor-copy conditions but lose it under true copies.

The primary zero-API outcome is these paired support-retention gates, not answer accuracy. Full counts include false-copy support and false-passage retention. If any gate fails, freeze the answered node, report all data and stop; no paid reader run. Infrastructure failure gets a repair on the same provisional node under the project repair cap, never a material change to make it pass.

## Conditional reader child: fixed first five IDs, at most 180 attempts

Only after readiness passes, freeze it and create a child preserving `python3 pilot/run.py`. Commit stage=reader and the exact readiness case hash. Materials and policies remain unchanged. The fixed case subset is diversity-00 through diversity-04, irrespective of their individual retention outcomes. Evaluate all four conditions and all three policies using the complete original three-stage `conflict_query_gpt` prompts. This is 60 cells x 3 calls = 180 worst-case attempts, under a hard cap of 200; no extra restoration calls, auxiliary judges or retries. Identical full prompts share cached responses, and cache dependence is disclosed.

The approved existing key is read privately from the configured environment file. Model gpt-5.4-mini-2026-03-17, reasoning none, at most 6000 input tokens per request and 1024 output tokens. Any incomplete response, HTTP failure or cap violation stops with partial output preserved. Exact four-digit extraction scores correct only if the complete extracted code set equals the target code alone; false-answer scoring similarly requires the false code alone. Multi-code and missing-code answers fail exact correctness. No policy gets extra context or a different prompt budget. Save all prompts, complete API responses, intermediate memory/consolidation and final text. Report token usage and actual attempts.

Primary reader contrast: per-policy paired clean-to-true-copy correctness difference, compared with clean-to-distractor-copy correctness difference, on all five fixed families. Also report all condition-policy counts, support retention, conflicting-code answers, and clean floor. Do not claim accuracy loss from retention alone, or interpret floor-limited pairs as copy-induced answer harm.

## Interpretation and stopping

Support deletion with a working clean baseline establishes only an implementation behavior in these synthetic fixed-retrieval tasks. If consolidation recovers, no downstream failure is established. If exact deduplication solves loss, that is an established simple remedy and rules out claiming the repair as novel; GuardRAG already addresses copies. No literature search or novelty claim is part of this delegated task. No natural retrieval reproduction, security guarantee, model-general conclusion, prevalence estimate or confirmatory significance test. Even a positive result remains a bounded development observation. Publish null outcomes and all cases.

Artifacts: `pilots/truth-preservation-diversity/<run-id>/`. Durable protocol: `pilots/truth-preservation-diversity/parallel-round-protocol.md`. The source protocol is committed with the readiness node and copied to that artifact path before launch.
