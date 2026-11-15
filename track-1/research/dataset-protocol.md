# Dataset protocol, v0.1

Scope: prepare materials for the Track 1 evidence-language question; no training or model evaluation. Languages: English, Simplified Chinese, standard Vietnamese with diacritics. Do not label Vietnamese categorically low-resource.

Each immutable seed has a case ID, explicit synthetic facts, two answer choices, a gold code, wrong code, family and split. No generator can set those fields. Adaption only supplies question/source wording through its Responses SDK. Successful outputs must preserve numeric literals; semantic correctness still requires human review.

The nine conversation/source language combinations preserve source facts. Peer advice remains in the conversation language. Correct and wrong advice refer to corresponding option codes, with three identical scripted peer messages; these are simulated assertions, not independent evidence from live peers. Repetition is fixed across languages and conditions.

Controls: initial prompt; neutral reflection with no advice; correct advice; wrong advice; source absent versus present. No-source controls are created once per conversation language and advice condition, not duplicated across imaginary source languages. Source-only/no-advice conditions check comprehension. For study execution, neutral reflection must retain the same actual initial history as advice conditions.

No model responses are in the dataset. `reuse_initial_id` tells a later evaluator which actual first response to branch from. Initial responses must not be synthesized or overwritten using gold codes. Unknown/invalid answers need separate categories rather than arbitrary conversion to correct/wrong.

Engineering-only pilot families: closing-time lookup; arrival-time calculation; mandatory total fee; available-seat subtraction. Five cases per family. Family-based pilot holdout prevents simple number variants being described as independent held-out task structures. All are simple and may produce ceiling effects. A varied real-fact benchmark is still required for claims about models' factual priors; fictional source-free answers are not a valid proxy.

Review covers target question/source meaning, no extra clues, preserved constraints, natural wording and shared instruction/peer templates. Human reviewer identifiers/statuses are recorded locally. Automatic numeric checks alone cannot certify translation quality. Main outcomes later: correct→wrong, wrong→correct, uncertain transitions, full-sample final accuracy and costs; report eligible denominators and paired analysis by case.

SDK authentication uses ADAPTION_API_KEY. Provider credentials have not been supplied in this session. No paid generation or evaluation run has been launched. A live SDK/account check remains necessary before claiming Adaption-generated data exists.
