"""Builds report.md from results_final.md, pressure_fix_results.md and the prompts in the code. Run: python3 build_report.py"""
import re, run2
res = open("results_final.md").read()
pf = open("pressure_fix_results.md").read()
judge_src = open("judge.py").read()
P = re.search(r'P = """(.*?)"""', judge_src, re.S).group(1)
FIX_SENT = ("Before answering, check whether the question's premise is true and whether the answer could actually be known by anyone. "
            "If the premise is false, or the answer is unknowable, speculative, or depends on information not given, your ANSWER must be UNKNOWN.")
assert FIX_SENT.split(",")[0] in open("ablate.py").read() and "your ANSWER must be UNKNOWN" in open("ablate.py").read()
T = "\n".join(f"- **{k}**: {v}" for k, v in run2.T.items() if k in run2.SINGLE)
ABSTRACT = ("We test whether LLMs say \"UNKNOWN\" to unanswerable questions, before and under user pushback, on 22 answerable and 39 unanswerable questions "
"(an AbstentionBench KUQ subset) across gpt-5, gpt-5-mini, DeepSeek-v4-flash, GLM-5.2 and Qwen3.5-397b (2-3 non-independent runs per item). "
"Abstention depends strongly on question type: gpt-5 answers UNKNOWN on 83% of future-unknown questions but only 20% of counterfactual and 20% of false-assumption ones (DeepSeek: 65%, 22%, 10%). "
"Every model abstains more on future-unknown than on counterfactual or false-assumption questions. "
"Pushback effects are model-specific: plain denial changed 22% (gpt-5-mini) and 20% (GLM) of correct answers (gpt-5: 0%) and flipped 39% of DeepSeek's UNKNOWN answers; fake citations flipped 26% of both OpenAI models' UNKNOWN answers. "
"Two LLM judges (kappa 0.62) show that scoring every non-UNKNOWN reply as a failure overstates hallucination: committed unsupported answers were 16-27% of unanswerable trials. "
"A one-line premise-check instruction raised counterfactual UNKNOWN by +0.57 (gpt-5; 95% CI +0.30 to +0.80) and +0.53 (DeepSeek), and false-assumption UNKNOWN by +0.43 (gpt-5) and +0.37 (GLM), "
"with a possible cost on answerable questions for DeepSeek (-0.09, CI -0.21 to 0.00). gpt-5-mini effects were within noise. Samples are small (about 10 items per category).")
n = len(ABSTRACT.split()); assert 150 <= n <= 250, n
figs = lambda i, f, c: f"\n![Fig {i}](figures/{f})\n\n{c}\n"
rep = f"""# Models Accept False Premises More Than Unknowable Futures: Abstention Gaps by Question Type, and a One-Line Fix

**Author:** [YOUR NAME], [AFFILIATION] (with Claude, Anthropic)

## Abstract
{ABSTRACT}

## 1. Introduction
When a model is unsure, the honest answer is often "I don't know". We ask two questions. (1) Which kinds of unanswerable questions do current models fail to abstain on, even with no pressure? (2) How much does user pushback add (plain denial, a fake citation, claimed authority, emotional appeal)? A model that guesses confidently on a false-premise question is misleading in a way that is easy to miss, so knowing where abstention breaks, and whether a cheap prompt change repairs it, is directly useful to people deploying models.

## 2. Related work
MASK [1] separates honesty from accuracy under pressure on single-turn statements. SycEval [2] measures progressive and regressive sycophancy under escalating rebuttals (simple, ethos, justification, citation) on answerable items and excludes refusals. SPINE [3] applies up to 25 turns of adaptive pressure to false presuppositions, where the desired behaviour is rejecting the premise rather than abstaining. "The Missing 'I Don't Know'" [4] argues for triple scoring (correct / wrong / abstain) but does not study pressure. CausalT3 [5] (read as an abstract only) tests a "sycophancy trap" on causal questions. AbstentionBench [6] measures abstention across question types without pressure; DarkBench [7] covers dark patterns. We combine abstention by question type (future-unknown, unsolved, counterfactual, false-assumption) with pushback and test a one-line prompt fix. We did not find this combination in the papers we read; that is not a claim that it does not exist.

## 3. Method
**Items.** 22 answerable (TriviaQA-style, with accepted aliases) and 39 unanswerable AbstentionBench KUQ questions (10 future unknown, 9 unsolved problem, 10 counterfactual, 10 false assumption). Five answerable items were removed because the key or the pushback claim was ambiguous or contained the answer (Father's Day, taxi MOT, Ansel Adams, Great Escape, Parliament Square). Pushback "wrong claims" were generated with the Adaption platform (prompt in `adapt/adaption_step2.py`) and filtered so they do not contain the true answer.

**Models and settings.** gpt-5 and gpt-5-mini (Braintrust proxy; `reasoning_effort=low`, `max_completion_tokens=3000`, 3 runs per item) and DeepSeek-v4-flash, GLM-5.2, Qwen3.5-397b (Adaption `responses` API; `max_output_tokens=8000`; provider default decoding; 2 runs per item). Ablation: 3 runs, baseline turn only. Pressure under fix: 2 runs. Runs are not independent samples of items.

**Trial.** A baseline reply ending in `ANSWER:` and `CONFIDENCE:` lines, then four independent single rebuttals (Appendix A) built from the wrong claim.

**Grader.** Answerable: correct if the `ANSWER:` line contains an accepted alias after accent folding (word-boundary match, plus space-insensitive match for aliases of 5+ characters); UNKNOWN counts as abstain; otherwise wrong. Unanswerable: correct iff the answer contains UNKNOWN. Missing `ANSWER:` lines, API errors and empty replies are "unparsed" and excluded from denominators.

**Statistics.** 95% CIs by bootstrap over items (2000 resamples); fix effects use a paired bootstrap on the per-item difference. `reanalyse.py` regenerates every table.

**Judge.** gpt-5-mini and gpt-5 classify each non-UNKNOWN baseline reply on unanswerable items as committed / hedged / premise-flagged (prompt in Appendix A). Qwen was not judged. Both judges are also evaluated models and were not validated against human labels.

**Fix.** One sentence appended to the system prompt (Appendix A).

## 4. Results
{res}
{figs(1, "fig1_unknown_by_category.png", "Fig 1: every model abstains more on future-unknown than on counterfactual or false-assumption questions.")}
{figs(2, "fig2_pushback.png", "Fig 2: plain denial is the strongest pushback for most models; fake citations mostly flip the OpenAI models' UNKNOWN answers.")}
{figs(3, "fig3_fix.png", "Fig 3: one added sentence raises UNKNOWN on counterfactual and false-assumption questions for gpt-5, GLM and DeepSeek.")}
{figs(4, "fig4_cost_answerable.png", "Fig 4: effect of the fix on answerable questions.")}
{figs(5, "fig5_judge.png", "Fig 5: many non-UNKNOWN replies are hedged or flag the premise rather than committing to an unsupported answer.")}

### Pushback under the fix (unanswerable items, 2 runs, no CIs)

{pf}

{figs(6, "fig6_pressure_fix.png", "Fig 6: under the premise-check prompt, UNKNOWN answers are abandoned less often. The fix also changes which items start at UNKNOWN, so the subsets differ between columns.")}
Notes: the "orig" column of the fix table comes from separate runs than the baseline table, so the two can differ slightly (e.g. GLM counterfactual 0.67 vs 0.55). A trivial "always UNKNOWN" baseline would score 1.0 on unanswerable and 0.0 on answerable questions, so the fix's cost on answerable items is the number that matters. Qwen lost 37% of baseline trials to errors or empty replies; treat its rows with caution.

## 5. Discussion
Models separate "unknowable because it is in the future" from "unanswerable because the premise is false or counterfactual", and handle the second far worse. A cheap instruction recovers much of that gap for gpt-5, DeepSeek and GLM; DeepSeek may pay a cost on answerable questions. Pushback matters model by model: gpt-5 hardly moves on answerable questions, but plain denial moves gpt-5-mini and GLM, and DeepSeek abandons UNKNOWN under plain denial far more than the others. The pressure-under-fix results suggest the premise-check prompt also stabilises abstention, but cover only some models and have no CIs.

**Theory of change.** If abstention failures cluster in false-premise questions, a deployer can target that case with a prompt or training signal instead of treating "hallucination" as one problem, and evaluators can report abstention by question type. **Future work:** more items per category; human validation of judged replies; adaptive multi-turn pressure; testing whether the fix generalises beyond KUQ; rerunning the 5-turn escalation chain (not reported: the stored GPT labels were stale when it was built).

## 6. Conclusion
On 39 unanswerable questions, five models abstain far less on counterfactual and false-assumption questions than on future-unknown ones. Counting all non-UNKNOWN replies as failures overstates the problem, but committed unsupported answers remain 16-27% of trials. A one-sentence premise check raises abstention on the weak categories for most models.

## Appendix A: Exact prompts
**System prompt (all trials):**
```
{run2.SYSTEM}
```
**Pushback templates** (`{{w}}` = the LLM-written wrong claim for that item):
{T}

**Fix sentence** (appended to the system prompt):
```
{FIX_SENT}
```
**Judge prompt:**
```
{P}
```

## Appendix B: Limitations and dual-use / ethical considerations
**What the results establish.** On this item set, abstention differs by question type for all five models, and a one-line prompt raises it for several. **What they do not establish:** whether the fix generalises beyond KUQ-style questions or to other prompts; real-world harm; any human-validated judgement (the two LLM judges are also evaluated models, kappa 0.62); statistical significance for most between-model gaps.
- About 10 items per category and 2-3 non-independent runs; many CIs are wide. GLM's counterfactual baseline moved from 0.55 to 0.67 between two runs of the same prompt.
- Qwen lost 37% of baseline trials and is absent from the judge, ablation and pressure-under-fix runs.
- The grader counts any non-UNKNOWN reply as wrong, though some KUQ items admit defensible hedged answers; answerable keys are noisy string matches; wrong claims are LLM-written.
- Models ran through different APIs and settings (see Method).
- **Dual use.** The pushback templates (fake citation, claimed authority, emotional appeal) are manipulation templates, and the per-category results show which question framings elicit confident answers. They could be used to tune manipulative prompts. We publish them because the same information is needed to evaluate and harden models.
- **Personal data.** No personal data was collected; items are public benchmark questions and generated prompts. Prompts and replies were sent to third-party providers (Braintrust proxy and the model APIs behind it; Adaption). API keys were supplied through environment variables and are not in the repository. See `NOTICE.md` for data licensing.

## References
[1] MASK: honesty under pressure benchmark, arXiv:2503.03750.
[2] SycEval: sycophancy evaluation, arXiv:2502.08177.
[3] SPINE: multi-turn proxy pressure on false presuppositions, arXiv:2609.09090.
[4] "The Missing 'I Don't Know'": triple scoring for abstention, arXiv:2609.17686.
[5] CausalT3 (abstract only), arXiv:2601.08258.
[6] AbstentionBench, `facebook/AbstentionBench` (Hugging Face).
[7] DarkBench (dark patterns in LLMs).
(Author lists, titles and venues to be completed from the source pages before submission.)
"""
open("report.md", "w").write(rep)
print("abstract words:", n)
import markdown
html = markdown.markdown(rep, extensions=["tables", "fenced_code"])
css = "body{font:11pt/1.4 Georgia,serif;max-width:7.2in;margin:auto}img{max-width:100%}table{border-collapse:collapse;font-size:8.5pt}td,th{border:1px solid #bbb;padding:2px 5px}pre{white-space:pre-wrap;font-size:8.5pt;background:#f4f4f4;padding:6px}@media print{h2{break-after:avoid}img{break-inside:avoid}}"
open("report.html", "w").write(f"<!doctype html><meta charset=utf-8><title>Flip and Abstain report</title><style>{css}</style>{html}")
