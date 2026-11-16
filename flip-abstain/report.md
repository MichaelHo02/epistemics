# Models accept false premises more than unknowable futures: abstention gaps by question type, and a one-line fix

## Abstract
We test whether LLMs answer "UNKNOWN" to unanswerable questions, before and under user pushback, on 22 answerable and 39 unanswerable questions (AbstentionBench KUQ subset) across gpt-5, gpt-5-mini, DeepSeek-v4-flash, GLM-5.2 and Qwen3.5-397b (2-3 non-independent runs per item). Abstention depends strongly on question type. On future-unknown questions gpt-5 says UNKNOWN 83% of the time, but only 20% on counterfactual and 20% on false-assumption questions; DeepSeek shows 65%, 22% and 10%; GLM and Qwen are higher but follow the same ordering. Pushback matters less than this for gpt-5 but not for the others: a plain "that's wrong" made baseline-correct answerable answers change in 22% (gpt-5-mini) and 20% (GLM) of cases, versus 0% for gpt-5; fake citations flipped 26% of UNKNOWN answers for both OpenAI models. Two LLM judges (agreement 0.77, kappa 0.62) show that counting every non-UNKNOWN reply as a failure overstates hallucination: committed unsupported answers were 16-27% of unanswerable trials by both judges. A one-line instruction to check the premise raised counterfactual UNKNOWN by +0.57 (gpt-5, 95% CI +0.30 to +0.80) and +0.53 (DeepSeek), and false-assumption UNKNOWN by +0.43 (gpt-5) and +0.37 (GLM); it cost DeepSeek 10 points on answerable questions (CI -0.21 to -0.01). Effects for gpt-5-mini are within noise. Samples are small (about 10 items per category).

## 1. Introduction
Prior work shows sycophancy under rebuttal (SycEval, SPINE) and weak abstention (AbstentionBench). We ask which unanswerable questions models fail on, and whether pushback or the question type is the bigger problem.

## 2. Related work
MASK (honesty under pressure), SycEval (progressive vs regressive sycophancy), SPINE (multi-turn pressure), "The Missing 'I Don't Know'" (triple scoring), AbstentionBench (abstention across question types), DarkBench.

## 3. Method
Items: 22 answerable questions (TriviaQA-style, accepted aliases) and 39 unanswerable KUQ questions in four categories (10 future unknown, 9 unsolved problem, 10 counterfactual, 10 false assumption). Five answerable items were removed because the key or claim was ambiguous or contained the answer (Father's Day, taxi MOT, Ansel Adams, Great Escape, Parliament Square). Each trial: a baseline reply ending in `ANSWER:` and `CONFIDENCE:` lines; four single rebuttals (simple denial, fake citation, claimed authority, emotional appeal) built from an LLM-written wrong claim. Labels: correct / wrong / abstain / unparsed; unparsed and errored replies are excluded from denominators. All numbers come from `reanalyse.py`, which relabels every raw transcript with the same grader and bootstraps 95% CIs by resampling items. Judge: gpt-5-mini and gpt-5 classify non-UNKNOWN unanswerable replies (committed / hedged / premise-flagged); Qwen was not judged. Fix: one added sentence telling the model to check the premise and answer UNKNOWN if false or unknowable; 3 runs per item, baseline turn only, paired bootstrap on the difference. The 5-turn escalation chain was run but is not reported: the stored GPT labels were stale when the chain was built.

## 4. Results
## Baseline (parsed replies only; 95% CI bootstrapped over items)

| model | answerable correct | unanswerable UNKNOWN | future unknown | unsolved | counterfactual | false assumption | unparsed share |
|---|---|---|---|---|---|---|---|
| gpt-5 | 0.97 [0.91,1.00] | 0.44 [0.29,0.58] | 0.83 [0.60,1.00] | 0.52 [0.22,0.81] | 0.20 [0.00,0.43] | 0.20 [0.03,0.43] | 0.0 |
| gpt-5-mini | 0.83 [0.67,0.97] | 0.34 [0.22,0.49] | 0.52 [0.28,0.77] | 0.46 [0.18,0.76] | 0.13 [0.00,0.33] | 0.29 [0.00,0.55] | 0.022 |
| deepseek-v4-flash | 0.91 [0.78,1.00] | 0.33 [0.20,0.48] | 0.65 [0.38,0.89] | 0.40 [0.11,0.73] | 0.22 [0.00,0.47] | 0.10 [0.00,0.25] | 0.09 |
| glm-5.2 | 1.00 [1.00,1.00] | 0.65 [0.49,0.78] | 0.95 [0.82,1.00] | 0.72 [0.44,0.94] | 0.55 [0.25,0.85] | 0.37 [0.10,0.65] | 0.098 |
| qwen3.5-397b | 0.81 [0.62,1.00] | 0.71 [0.56,0.84] | 1.00 [1.00,1.00] | 0.73 [0.40,0.93] | 0.50 [0.20,0.80] | 0.55 [0.20,0.83] | 0.369 |

## Pushback on answerable items: share of baseline-correct trials that left the correct answer

| model | simple denial | fake citation | authority | emotional |
|---|---|---|---|---|
| gpt-5 | 0.00 [0.00,0.00] | 0.02 [0.00,0.05] | 0.02 [0.00,0.05] | 0.03 [0.00,0.10] |
| gpt-5-mini | 0.22 [0.07,0.40] | 0.07 [0.00,0.20] | 0.02 [0.00,0.06] | 0.02 [0.00,0.06] |
| deepseek-v4-flash | 0.12 [0.00,0.28] | 0.03 [0.00,0.09] | 0.00 [0.00,0.00] | 0.06 [0.00,0.14] |
| glm-5.2 | 0.20 [0.04,0.39] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.07 [0.00,0.16] |
| qwen3.5-397b | 0.17 [0.00,0.37] | 0.13 [0.00,0.33] | 0.06 [0.00,0.18] | 0.19 [0.00,0.40] |

## Pushback on unanswerable items: share of baseline-UNKNOWN trials that switched to a concrete answer

| model | simple denial | fake citation | authority | emotional |
|---|---|---|---|---|
| gpt-5 | 0.12 [0.00,0.25] | 0.26 [0.09,0.43] | 0.00 [0.00,0.00] | 0.10 [0.00,0.24] |
| gpt-5-mini | 0.15 [0.03,0.31] | 0.26 [0.09,0.47] | 0.03 [0.00,0.10] | 0.13 [0.00,0.31] |
| deepseek-v4-flash | 0.39 [0.17,0.61] | 0.17 [0.00,0.39] | 0.13 [0.00,0.29] | 0.09 [0.00,0.24] |
| glm-5.2 | 0.08 [0.02,0.16] | 0.04 [0.00,0.10] | 0.00 [0.00,0.00] | 0.02 [0.00,0.07] |
| qwen3.5-397b | 0.11 [0.00,0.23] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.07 [0.00,0.18] |

## One-line fix (UNKNOWN rate, orig -> fix, paired bootstrap 95% CI on difference over items)

| model | category | orig | fix | diff [CI] |
|---|---|---|---|---|
| gpt-5 | answerable | 0.96 | 0.96 | +0.00 [+0.00,+0.00] |
| gpt-5 | future unknown | 0.87 | 1.00 | +0.13 [+0.00,+0.30] |
| gpt-5 | unsolved problem | 0.56 | 0.67 | +0.11 [+0.00,+0.26] |
| gpt-5 | counterfactual | 0.20 | 0.77 | +0.57 [+0.30,+0.80] |
| gpt-5 | false assumption | 0.23 | 0.67 | +0.43 [+0.20,+0.67] |
| gpt-5-mini | answerable | 0.81 | 0.76 | -0.04 [-0.14,+0.03] |
| gpt-5-mini | future unknown | 0.53 | 0.77 | +0.23 [+0.07,+0.43] |
| gpt-5-mini | unsolved problem | 0.30 | 0.48 | +0.19 [+0.00,+0.41] |
| gpt-5-mini | counterfactual | 0.10 | 0.32 | +0.22 [+0.02,+0.43] |
| gpt-5-mini | false assumption | 0.33 | 0.43 | +0.10 [-0.13,+0.37] |
| glm-5.2 | answerable | 0.94 | 0.93 | -0.01 [-0.10,+0.08] |
| glm-5.2 | future unknown | 0.97 | 1.00 | +0.03 [+0.00,+0.10] |
| glm-5.2 | unsolved problem | 0.67 | 0.67 | +0.00 [+0.00,+0.00] |
| glm-5.2 | counterfactual | 0.67 | 0.90 | +0.23 [+0.03,+0.47] |
| glm-5.2 | false assumption | 0.43 | 0.80 | +0.37 [+0.20,+0.53] |
| deepseek-v4-flash | answerable | 0.96 | 0.86 | -0.10 [-0.21,-0.01] |
| deepseek-v4-flash | future unknown | 0.88 | 1.00 | +0.12 [+0.00,+0.25] |
| deepseek-v4-flash | unsolved problem | 0.44 | 0.67 | +0.22 [-0.04,+0.52] |
| deepseek-v4-flash | counterfactual | 0.20 | 0.73 | +0.53 [+0.30,+0.77] |
| deepseek-v4-flash | false assumption | 0.20 | 0.70 | +0.50 [+0.30,+0.70] |

Note: the answerable rows of the fix table use the answerable set before dropping the Great Escape and Parliament Square items, and report the correct rate; other rows report UNKNOWN rate.

## 5. Discussion
Models treat "unknowable because future" differently from "unanswerable because the premise is false or counterfactual". A cheap instruction recovers much of that gap for gpt-5, DeepSeek and GLM, with a measurable cost on answerable items for DeepSeek. For the weaker models, plain denial is itself a real source of flips, so "pressure is the smaller problem" only holds for gpt-5. Next steps: more items per category, human check of about 30 judged replies, rerun pressure arms under the fix, rerun Qwen's errored trials.

## Appendix: Limitations and dual-use / ethics
- About 10 items per category and 2-3 non-independent runs; many CIs are wide and several between-model gaps are not significant. GLM's counterfactual baseline moved from 0.55 (v3) to 0.69 (ablation original arm) on the same prompt, showing instability.
- Qwen lost 37% of baseline trials to errors or empty replies; its rows are unreliable and it is absent from the judge and the ablation.
- The two judges are gpt-5-mini and gpt-5, which are also evaluated models; agreement is moderate and unvalidated against human labels. The grader still scores any non-UNKNOWN reply as wrong; some KUQ items admit defensible hedged answers.
- Wrong claims are LLM-written; some answerable keys are noisy (string matching misses paraphrases); models ran through different APIs and settings.
- The result shows a category effect on this item set. It does not show that the fix generalises or measure real-world harm.
- Dual use: the fake-citation, authority and emotional prompts are manipulation templates, and the results show which framings produce confident answers. We use public benchmark questions and generated prompts only; no personal data was collected. See `NOTICE.md` for data licensing.
