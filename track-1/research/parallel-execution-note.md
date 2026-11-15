# Parallel execution update

At the user’s request, the sequential run was stopped and resumed with eight independent question-family workers. Model snapshot, request parameters, original-answer reuse, questions and evidence are unchanged. Shared request-budget reservations and measurement writes are protected by locks; workers stop scheduling requests after a fatal error. Successful response caches use unchanged request hashes and are reused.

Before the switch, 3,768 completed responses were preserved. One request interrupted by cancellation had unknown completion/billing state; its intent record and partial measurements are archived under the output recovery folder and it is explicitly retried once. It could incur duplicate billing, but no response from it was saved or counted twice. Earlier HTTP503 attempt is separately preserved. This is an execution change within the same unfinished experiment, not a new scientific condition.

Nine evaluator tests pass, including concurrent overlap, unique request identities and a zero-network cache resume.
