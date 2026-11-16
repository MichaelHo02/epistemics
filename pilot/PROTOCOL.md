# Hypothesis and primary comparison
Providing the actual user's objectives and constraints to an evidence selector increases retention of an optimal feasible option relative to a profile-blind selector under identical extractive formatting and evidence length. Primary endpoint: user-aware minus blind difference in optimal-option retention at two slots, averaged over two profiles within each of 16 families. This tests a known personalization principle empirically in a controlled pipeline; it is not a novelty claim.

# What the parent established
Parent 40171895-3dab-46a7-8b81-fe714dab061f, run 5074f219-a838-41fc-a1db-c96a4bf2f885, established full-input reader solvability, but fixed optimal IDs, nonbinding capacity and prose truncation prevented strong interpretation. This child retains only the API/run scaffolding and replaces materials and the experimental contrast. The independent briefing research line remains separate from all defense experiments.

# Intervention and controls
Fresh seed 270416; 16 synthetic families, eight options, two profiles with disjoint optimal sets; random values and shuffled option order. Half minimize price and half minimize completion subject to deadline/capacity constraints. In price tasks both constraints independently exclude cheaper options; in completion tasks capacity binds, while deadline gates feasibility. Sampling conditions define a diagnostic population with materially different user needs, not representative natural-user demand.

Methods: profile-blind, true-user-aware, swapped-profile selection and lexical overlap. All selectors choose exactly two or four option IDs; all selected records use the same deterministic renderer and original order. Equal delivered token lengths within each slot condition are checked before and during the run. No artificial padding, prose generation or truncation. Two slots is the primary budget; four slots is secondary. The reader always receives the actual user's requirements. Full-source reader control; deterministic optimum-retention scoring separates selection from reader errors. No privileged gold is supplied to selectors.

# Validation
Independent pairwise-dominance solver agrees with the main reference; reproducible material generation; diverse optimal IDs; inclusive limits and ties accepted; invalid choice tested. Token equality and selection-parser malformed/duplicate/out-of-catalog cases checked locally before launch. Run repeats material validation before requests; stops before calls if row-token equality fails. Invalid selection responses remain failures without replacement. All requests and rows saved.

# Metrics and interpretation
Primary optimal-option retention; secondary exact best-feasible-choice correctness, feasibility, abstention, invalid response rate, regret conditional on feasible choice, and usage. Family is the independent unit; two user profiles and budgets are paired, and cached outputs are shared rather than independent repeats. Descriptive pilot; no confirmatory p-value or stable ranking claim. All data retained, including failures.

# Progress/stop gates
Proceed to confirmation only if selection parses reliably, full-source reader is reliable, user conditioning offers a consequential retention benefit over the blind and swapped controls, and the lexical comparison does not trivially settle the method choice. A difference from blind alone is insufficient to propose a new method. If controls reach ceiling or all comparisons are trivial, stop this formulation. Any confirmation needs newly specified held-out structures, a meaningful effect threshold, and additional models. No claim of human benefit, general-domain transfer or free-form briefing superiority.

# Compute and immutable contract
Inherited command python3 pilot/run.py, local backend, snapshot-local venv with tiktoken==0.9.0. Dated gpt-5.4-mini-2026-03-17, reasoning none, existing user-approved key. Hard cap 500 uncached requests, 6000 prompt tokens and 1024 output tokens per request, no automatic retries. Nominal uncached maximum 480 requests before prompt-cache reuse. No other compute changes.

# Outputs
Per-run pilots/decision-briefing-v2/<run-id>: effective configuration and commit, cases/gold, complete saved requests/responses, row measurements, final summary. Hypothesis and design saved before model outcomes.

# Status
Ready for launch. Local validation passed: exhaustive token equality across all 2- and 4-option subsets (27 and 55 tokens), all eight gold IDs represented, independent reference agreement and parser failure checks. No model results yet.
