# Track 1: closest-paper check before dataset construction

15 November 2026. Step 1 only. No dataset generated, no models evaluated, no experiment launched. The user suggested adaptionlabs.ai for later dataset construction; its capabilities have not been assessed here.

## Decision

**We searched and did not find an exact match for the full proposed experiment. We did find much closer predecessors than the initial review identified.** Language-dependent source selection under conflicting evidence is established, including English/Chinese settings. The proposed study is defensible as a targeted extension/replication, not as the first demonstration that language influences trust or answer changes.

Recommendation: proceed to material design only with a narrower question: **Does switching the language of an otherwise equivalent source change how much that source protects an AI from misleading peer advice, while preserving useful correction?** The interaction between peer advice and source language is the candidate contribution. This focused search does not prove nobody has tested it, and combining existing factors does not automatically make a strong paper.

## What was checked

Current retrieved full texts were inspected for methods, relevant results, limitations and references. Earlier paper reads were reused where appropriate. Newly important papers were WALDO, Language Bias under Conflicting Information, and Faux Polyglot. Reference-following led from the multilingual-pressure paper to Aldahlawi et al., and from WALDO to Faux Polyglot and Linguistic Nepotism. The latter's OpenReview page was blocked by browser verification; its methods were not verified and it is not used for claim-level support.

Searches used default ranking without a publication-date bound, over alphaXiv semantic and keyword discovery. Difficulty 8 allowed two follow-up rounds, used for multilingual conflict and named reference recovery. Exact-title discovery sometimes returned irrelevant results: these failed recoveries are recorded, not treated as evidence of absence. Faux Polyglot was read from its original ACL PDF using the reference URL. This is a focused closest-work review, not a systematic census or complete citation-network search. See the accompanying search log for queries/results.

## Comparison with the nearest predecessors

| Original | Already covered | Distinction remaining for our candidate |
| --- | --- | --- |
| [Faux Polyglot, NAACL 2025](https://aclanthology.org/2025.naacl-long.411/) | Separates multilingual retrieval from generation; fictional conflicting facts and perspectives across five languages, including English and Chinese; neutral and confirmatory queries. Generation permutes languages assigned to competing document sets. | The described protocol does not branch from one recorded initial answer into correct/wrong peer advice and equivalent external-source language conditions. This is a substantial predecessor to the broad idea, including synthetic data and biased queries. |
| [Language Bias under Conflicting Information, v2](https://www.alphaxiv.org/pdf/2604.07123) | Varies languages of contradictory facts, surrounding news text and prompting; includes English/Chinese. Measures choosing one answer versus representing the conflict, with position/context controls. | Contradictory sources are not our intended single verified passage versus unsupported peer messages. Its experiment does not operationalize our initial-right/initial-wrong correction sequence. Merely swapping source languages and reporting answer preference would largely repeat its approach. |
| [WALDO: Query-language Preference under Cross-lingual Knowledge Disparities](https://www.alphaxiv.org/pdf/2610.00606) | Wikipedia-derived knowledge gaps and controlled contradictions; holds retrieved context fixed while changing query language; includes Simplified Chinese/English pairing, content-swapping controls and mitigation methods. | Focus is source selection under gap/conflict, rather than peer-pressure-induced changes from the same initial response. It makes language-matching bias a required competing explanation in our study. |
| [Disentangling Robustness and Sycophancy in Multilingual LLMs](https://www.alphaxiv.org/pdf/2610.30696) | Same questions in six languages; initial accuracy before pressure; native-language challenges including alleged peer consensus; separates not knowing from abandoning a correct answer. Also tests English-bridge reasoning. | It does not independently cross the language of a supplied external source with conversation language in its described pressure protocol. Adding Chinese pressure alone would repeat it. |
| [Investigating the Influence of Language on Sycophantic Behavior](https://www.alphaxiv.org/pdf/2603.27664) | Tweet-like opinion prompts in six languages, including Chinese; multilingual agreement behavior. | Not a controlled external-evidence and initial-answer revision study. Useful background, weaker factual-pressure comparator. |
| [Resistance–Receptivity Frontier](https://www.alphaxiv.org/pdf/2608.11247) | Scripted peer answers; resisting wrong peers while accepting correct ones; comparison of mitigations. Explicitly proposes retrieval/tools as an untested next step in that study. | External checking is a published hypothesis, not an idea we invented. Our potential extension adds equivalent evidence in different languages and comprehension controls. |
| [PAVE](https://www.alphaxiv.org/pdf/2606.01120) | Separates correct versus wrong pre-evidence beliefs and accurate versus misleading evidence; tests prior–evidence arbitration and a JSD-based intervention. | It already supplies the good/bad updating framework. Our candidate adds peer-advice and source-language interaction, rather than claiming selective evidence use is new. |
| [When Expert Disagreement Hurts](https://www.alphaxiv.org/pdf/2611.16694) | One recorded initial answer reused across neutral reflection, anonymous dissent and expert-labelled dissent while evidence stays fixed. Separates useful from harmful revisions; studies evidence-gating instructions. | A very close protocol baseline. Language of equivalent source passages is not independently varied in the described study. A simple expert-label or rechecking experiment would overlap it. |
| [Question, Response, and Verifier Languages](https://www.alphaxiv.org/pdf/2610.32144) | Separates question, response and confidence-verifier languages and shows why grading language matters. | Confidence self-evaluation, not peer advice plus external-source language. Relevant warning against letting a language-sensitive judge create our effect. |

REL-BLOOM (2611.06715), Chinese factual sycophancy (2609.30986), and Correction or Manipulation (2610.36453) remain relevant from earlier verified reading; none should be described as a direct demonstration of our full interaction design.

## What is established versus what remains to test

Established: language can affect which source a model uses; multilingual pressure can change correct answers; external evidence can correct or mislead; resisting all advice is not a useful success criterion. Synthetic fictional facts, cross-language permutations, English reasoning and source translation already have predecessors.

Candidate contribution: whether external checking's benefit under peer advice changes with source language **after accounting for ability to read the source**, assessed both for protection of correct answers and correction of wrong answers. We have not found this exact combined protocol in the works checked. The result could be a small replication-and-extension paper; its value will depend on a reliable effect or a well-bounded informative null, strong controls and reusable materials.

## Design requirements learned from this check (not yet implemented)

1. Separate conversation language, source language and answer/scoring format. Use a fixed exact answer key or validated parsing where possible; do not let an unvalidated model judge define the main effect.
2. Fix facts and source credibility across translations. Avoid different Wikipedia editions as if they were translations: naturally different content is a separate factor.
3. Test source comprehension without peer advice. Compare the added effect of advice across languages, rather than interpreting every cross-language accuracy gap as social pressure.
4. Reuse a single initial answer for matched revision branches within each model/question/conversation language, as in the paired revision baseline. Record all initial outcomes; do not manufacture the model's initial answer and then call it its belief.
5. Include neutral reflection with no peer advice, correct advice, wrong advice, source absent, and source present. Present verified passages directly at first so retrieval quality is not an uncontrolled factor. Keep position, repetition and apparent authority matched.
6. Measure correct-to-wrong and wrong-to-correct transitions with their eligible denominators, final accuracy, uncertainty/invalid outputs and cost. Language-specific initial correctness can change the composition of these groups; report full-sample paired results and sensitivity on common-comprehension items rather than comparing unmatched subsets as if they were randomized.
7. Include a translation-to-conversation-language check as an existing-method comparator. If a simple translation removes the effect, that is a practical baseline, not an intervention we should claim to invent. Equalize or report added model calls.
8. Equivalent verified evidence alone mostly tests comprehension; contradictory unlabeled documents mostly repeat source-preference work. The peer-advice comparison must add a separable test. If a pilot cannot distinguish this from ordinary reading errors or all models perform at ceiling, narrow/rethink before scaling.

## Recommendation for the user

Keep the idea, but label it accurately: **a controlled extension of multilingual evidence and peer-pressure research**. Do not promise a major new direction. Step 1 is complete at the focused-review level; the next deliverable, if pursued, is a dataset specification. The user proposed adaptionlabs.ai for that later step. No dataset or tool integration was started during this review.
