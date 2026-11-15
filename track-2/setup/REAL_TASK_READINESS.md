# Real repair-task readiness

This is setup and reference-state validation, not a model experiment. It invokes no model APIs. Run `check_real_tasks.py` with Python 3.12 from the repository root. The script retrieves the pinned public SusVibes definitions and deterministic count validator, then uses the first three task images with Linux amd64 emulation.

For each task it executes four configurations: golden repair with normal tests, golden repair with added security tests, golden repair with the security patch reversed and normal tests, and the same weakened repair with security tests. Test patch application precedes the repair, matching the official evaluator's order. These mutants are constructed controls, not outputs from an evaluated coding agent.

The script runs the image's original test command without fetching dependencies or enabling container networking. It preserves output logs and patch application failures. It does not run the entire official evaluation harness or claim universal security from test results. The legacy pytest summary adapter reads a completed line ending in `seconds`, then passes explicit counts to the upstream count validator; missing output remains unscorable.

Task 3 has two documented ordinary baseline failures, so shell exit status alone cannot classify it as a failed repair. Compare functional failure counts to the dataset's `expected_pf.func`; for the security-augmented run compare to the accumulated functional plus security allowance, as the official harness does for default non-standalone tests.

The source harness already implements generic advice, exact CWE labels (`oracle`), and exposed security-test advice. These are close prior controls for the proposed pivot. More precise grounded diagnosis differs from merely providing a CWE name, but that difference is not yet a demonstrated novel contribution. Do not launch a broad paid repair study before defining and reviewing that distinction.
