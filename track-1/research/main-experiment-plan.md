# Main experiment preparation

Status: question selection prepared; evidence, translations, peer wording and evaluation runner remain incomplete. This document is a proposed protocol, not a preregistration or measured result.

## Data

Use 300 published Global-MMLU questions, 30 per subject across ten science, computing and mathematics subjects in `configs/global-mmlu-main.json`. Keep the published English, Chinese and Vietnamese question versions and answer keys unchanged. Existing 20 development IDs are excluded. Selection uses a fixed hash ranking, complete fields, equal answer letters and the upstream CA label. This does not certify translation quality or answer correctness. The resulting slice does not represent all Global-MMLU.

Check each question and its translations before model testing. Collect an independently sourced supporting passage, verify the source supports the answer, check reuse terms, then translate the passage. Do not write a passage merely by restating the answer key. Keep source provenance, support decisions and translation checks. Treat source summaries explicitly as researcher paraphrases. Adaption can translate approved evidence; it must not create trusted answer keys or alter the published questions. Do not upload source text until its reuse review is resolved.

For ambiguous, incorrect or unsupported cases, retain the original, log the reason and use the next eligible item from the same subject in the fixed replacement queue. Exhausting the queue requires a documented selection amendment. All replacements happen before inspecting model outcomes. Never drop a question just because the model gets it right or wrong.

## Conditions for the first model

Obtain one actual initial answer per question and conversation language: 900 initial answers. Save its selected option and uncertainty. Reuse that exact initial response when branching the conversation; do not substitute the answer key as the model's first answer.

For each initial answer, compare neutral reconsideration, correct peer advice and wrong peer advice. In each advice condition compare no evidence with English, Chinese and Vietnamese evidence. This gives 36 revision conditions per question: 10,800 revisions, plus 900 initial answers. These counts exclude retries and any later repetitions. They are planned calls, not calls already made. All revisions start from the same saved initial response and run independently, without sharing previous revisions.

Peer messages use the conversation language, the same number of peers, and matched tone/length. Choose one of the three incorrect options using a fixed, seeded rule and record it before model responses. The peer-answer manipulation must not change the evidence. Neutral reconsideration with evidence is necessary to separate evidence usefulness from peer-pressure effects. Verify all instruction and peer translations before execution.

Start with one explicitly pinned model/version. Freeze prompts, decoding settings, output schema and parsing rules after development checks. Store model request/response IDs, failures, retries, token use and cost. Never include the gold answer, condition names or private review metadata in the model input. The older two-option synthetic runner is not suitable for these four-option questions.

## Outcomes

Report baseline accuracy separately for each question language. Among initially correct answers, count changes to wrong answers after wrong advice, with and without evidence. Among initially incorrect answers, count changes to the correct answer after correct advice. Report eligible denominators rather than only percentages. Also report final accuracy on all questions, invalid/missing answers, and uncertainty separately.

Primary comparison: for wrong advice, compare same-language evidence with different-language evidence within the same question and conversation language. Preserve results for each of the nine language pairs so an English/Chinese/Vietnamese difference is visible. Evidence-only neutral controls help identify ordinary evidence comprehension differences.

Use paired comparisons and uncertainty intervals that resample whole question IDs, keeping all conditions and languages together. Do not treat 900 translated rows or 10,800 revisions as independent questions. The target of 300 questions is a budget choice, not a claim of sufficient statistical power. A lack of observed difference is inconclusive when intervals remain wide or few initially incorrect answers are available.

## Before launch

- Resolve question, source-support, reuse and translation reviews.
- Build and check a dedicated four-option evaluation runner with response caching and exact branch reuse.
- Set the model, deterministic wrong-option rule, prompt wording and failure handling.
- Review the call estimate and provider cost before launching the full matrix.
- Save a committed, immutable dataset manifest and protocol with the run.

Preparation artifacts live under `track-1/global-mmlu-main/` in project artifacts. The earlier development set and its evidence review remain separate.
