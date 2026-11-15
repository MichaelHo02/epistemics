# Models accept false premises: abstention gaps by question type, and a one-line fix

## Abstract
We test whether LLMs answer "UNKNOWN" to unanswerable questions, before and under user pushback, using 24 answerable and 39 unanswerable questions (AbstentionBench KUQ) across gpt-5, gpt-5-mini, DeepSeek-v4-flash, GLM-5.2 and Qwen3.5-397b (2-3 runs each). Pushback (plain denial, fake citation, claimed authority, emotional appeal) rarely changed correct answers (at most about 18% flipped; fake citation flipped abstentions in 0-26% of cases). The larger failure comes before any pressure: abstention depends strongly on question type. UNKNOWN rates for future-unknown questions were 0.87 (gpt-5) and 0.88 (DeepSeek) but only 0.20 and 0.18 on counterfactual and 0.23 and 0.20 on false-assumption questions. Two blind LLM judges (agreement 0.77, kappa 0.62) show a strict "any non-UNKNOWN is a miss" metric overstates hallucination: only 16-27% of unanswerable trials were committed answers by both judges. A one-line instruction to check the premise raised UNKNOWN on counterfactual questions from 0.20 to 0.77 (gpt-5) and 0.18 to 0.73 (DeepSeek), at little cost on answerable questions except DeepSeek (0.96 to 0.86). The sample is small and effects for gpt-5-mini are within noise.

## 1. Introduction
Prior work shows sycophancy under rebuttal (SycEval, SPINE) and weak abstention (AbstentionBench). We ask which unanswerable questions models fail on, and whether pushback or the question itself is the bigger problem.

## 2. Related work
MASK (honesty under pressure), SycEval (progressive vs regressive sycophancy), SPINE (multi-turn pressure), "The Missing 'I Don't Know'" (triple scoring), AbstentionBench (abstention across question types), DarkBench.

## 3. Method
Items: 27 answerable (TriviaQA-style, accepted aliases) and 39 unanswerable KUQ questions in four categories (future unknown, unsolved problem, counterfactual, false assumption); 3 ambiguous items removed. Each trial: baseline reply with `ANSWER:` and `CONFIDENCE:` lines; four single rebuttals (simple, citation, authority, emotional) built from a wrong claim; a 5-turn escalation chain for baseline-correct items. Labels: correct / wrong / abstain / unparsed (errors excluded). Statistics: bootstrap over items. Judge: gpt-5-mini and gpt-5 classify non-UNKNOWN unanswerable replies (committed / hedged / premise-flagged). Fix: one added sentence telling the model to check the premise and answer UNKNOWN if false or unknowable.

## 4. Results
See `mlam.md` (v3 cross-vendor, v4 judge and ablation) and `results/`.
Baseline UNKNOWN by category (gpt-5 / mini / DeepSeek / GLM / Qwen): future unknown .83/.52/.65/.95/1.0; unsolved .52/.46/.40/.72/.73; counterfactual .20/.13/.22/.55/.50; false assumption .20/.29/.11/.37/.55 (Qwen has many errored trials).
Fix, UNKNOWN orig to fix, false assumption: gpt-5 .23 to .67, mini .33 to .43, GLM .43 to .80, DeepSeek .20 to .70.

## 5. Discussion
Models treat "unknowable because future" differently from "unanswerable because the premise is false". A cheap prompt instruction recovers much of the gap for three of four models. TODO before submission: bootstrap CIs on the ablation, hand-check about 30 judged replies, rerun pressure arms with the fix, rerun Qwen errors.

## Appendix: Limitations and dual-use / ethics
- Small sample (24+39 items, 2-3 non-independent runs); most between-model gaps are not significant; no CIs yet on the ablation.
- The judge is an LLM and agreement is moderate (kappa 0.62); not validated against human labels.
- Wrong claims were LLM-written; some answerable keys are noisy; models ran through different APIs and settings; Qwen lost about a third of trials to errors.
- The result shows models accept false premises more than future-unknown ones on this item set. It does not show the fix generalises, nor measure real-world harm.
- Dual use: the fake-citation, authority and emotional prompts are manipulation templates and the false-premise items show which framing gets confident answers. We use only synthetic prompts and public benchmark questions; no personal data was collected.
