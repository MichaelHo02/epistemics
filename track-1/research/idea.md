# Track 1 — Idea 1: Does the language of a source change whether AI follows the evidence?

Status: saved research idea; no model experiment has been run.

Implementation update (15 November 2026): the dataset pipeline now includes English, Simplified Chinese and Vietnamese. The four-condition table below records the original two-language proposal; the current implementation expands it to nine language pairs. See ../README.md and dataset-protocol.md. The initial synthetic cases are engineering fixtures, not a final factual-prior benchmark.

## Question

When someone pushes an AI toward a wrong answer, does a source in English or Chinese help it stay correct? When the AI starts wrong, does that source help it correct itself?

This belongs primarily to the sprint's **Track 1: Model Epistemics & Decision-Making Evals**. It measures whether an AI changes its answer for a good reason and whether language affects that behaviour. Track 2 could become relevant if we build a source-checking tool.

Sprint: https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15

## What our literature search established

**We searched and did not find a study testing this exact combination: source language, misleading advice, and helpful correction.** This accurately describes our search result. It does not establish that no such study exists. The idea is a possible extension of existing work, not a confirmed first.

Related work already covers substantial parts:

- **Conformity Mitigations in Large Language Models Lie on a Single Resistance–Receptivity Frontier** tests resisting wrong peer answers and accepting correct ones. https://www.alphaxiv.org/pdf/2608.11247
- **Disentangling Robustness and Sycophancy in Multilingual LLMs** tests pressure across six languages, including English and Chinese, while distinguishing initial accuracy from abandoning a correct answer. https://www.alphaxiv.org/pdf/2610.30696
- **Evaluating Sycophancy in Chinese Large Language Models on Factual Questions Derived from Online Search Queries** tests false user beliefs and anti-agreement prompts in Chinese. https://www.alphaxiv.org/pdf/2609.30986
- **Correction or Manipulation? Measuring Epistemic Vigilance in LLM Agents Under User Pressure** tests useful corrections versus misleading pressure, including citations. https://www.alphaxiv.org/pdf/2610.36453
- **Reasoning over Non-Parametric Memory in Multilingual LLMs: A Cognitive-Based Analysis of Relational Knowledge (REL-BLOOM)** tests supplied facts in multiple languages and mixed-language settings, including facts conflicting with familiar knowledge. https://www.alphaxiv.org/pdf/2611.06715
- **Cognitive Bias Signatures in Search-Equipped LLM Agents: A Stage-Resolved Analysis** shows why search-result order needs controlling. https://www.alphaxiv.org/pdf/2611.05720

Searches included `sycophancy multilingual`, `sycophancy cross-lingual evidence`, `sycophancy multilingual retrieval`, `multilingual knowledge conflict evidence`, and a semantic query about the language of conflicting evidence and misleading advice. Relevant full texts were inspected. This was a focused search, not an exhaustive systematic review.

Simply showing that language matters, or that AI sometimes follows wrong advice, would repeat existing work. The possible contribution is testing whether source language changes the benefit of checking evidence under both wrong and helpful advice.

## Concrete example

Invented example: a timetable clearly says a museum closes at **5 pm**. Scripted messages from supposed other AI assistants insist on **6 pm**. Give the model the timetable and check its final answer. Repeat with matched English and Chinese versions. Also include cases where the model initially answers wrongly and the timetable supports a useful correction.

These are controlled test materials, not claims about a real museum or live conversations with other assistants.

## Proposed small experiment

Use the same questions and facts across four conditions:

| Conversation language | Source language |
| --- | --- |
| English | English |
| English | Chinese |
| Chinese | English |
| Chinese | Chinese |

Keep the advice in the conversation's language. Supply the exact source text initially, rather than using live search, to separate reading and evidence use from search quality.

Compare answering without advice, advice without a source, and advice with a source. Include both wrong advice and correct advice. Measure separately:

1. How often an initially correct answer becomes wrong.
2. How often an initially wrong answer becomes correct.
3. How often the model becomes uncertain or refuses to answer.

Check source comprehension without misleading advice first. A language-reading failure should not be described as giving in to pressure. Keep facts, source labels, tone, message order, and model settings matched. Have a fluent bilingual reader check translation quality. Do not infer cultural differences from language differences.

## Before selecting this project

1. Inspect the closest papers' methods and references for the exact combination, including alternative terminology.
2. Prepare a few matched bilingual examples and review their meaning and tone.
3. Run a small pilot only after defining the test materials and evaluation. Check that the task is neither universally easy nor universally impossible.

Possible finding: a model reads both language versions correctly alone but becomes easier to mislead with one source language. This is a hypothesis, not a measured result. A finding of little difference would also be informative within the tested models and materials.
