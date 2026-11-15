# Development screen: truth-only evidence removal

Question: does the original TrustRAG stage-1 filter lose a known-support group
after exact copies of that support are added, without removing original inputs?

This is a development feasibility check, not the full defense, held-out research
result, or evidence of downstream answer harm. Twenty families were chosen by
SHA256 ordering with salt `filter-screen-development-v1:` without reading model
responses. Four same-subject passages accompany the target support. Their lack
of alternative support has NOT been audited; scoring concerns the known exact
support group, not all logically sufficient evidence.

The original file is from HuichiZhou/TrustRAG, Git blob
`0aa0200027410e803ff595ad195cc2bcef8560c0`; its MIT license is included.
Five function bodies are loaded unchanged via AST extraction. Model inference
uses the released SimCSE checkpoint and last-layer CLS pooling on CPU instead
of CUDA. No OpenAI or Adaption calls, private-key access, or training occurs.
Both ROUGE-gated and ungated variants are reported separately; neither may be
selected after seeing results to hide the other.

Base, support-copy and copied-other-passage contexts use budgets 1/2/4 and two
insertion orders. Every original remains present. Removing the original while
retaining an exact copy counts as support retained. Exceptions are saved, not
scored as successful attacks. All measurements are saved with configuration.

Dependencies are pinned at the top level for this feasibility check; transitive
packages remain pip-resolved and this is not a fully locked publication recipe.
The fixed project runner dispatches this workflow from committed configuration.

Known novelty risk: GuardRAG already tests benign duplication/paraphrase harm,
CamoDocs already reports erasure-related utility loss, and CoordGuard already
tests adaptive and premise-split attacks. A positive mechanism check does not
by itself justify a novel-paper claim or completing the candidate-search goal.
