# RQ1 scientific prepilot — public audit export

Completed 2026-11-02; this branch publishes existing results only. No new EDA/model run was performed for publication. Start with FINAL_DECISION_SUMMARY.md, ROUND3_V2_RESULT.md and second-family/RESULT.md.

Two independent design families, one eligible pair each: VexRiscv incremental WNS 0ps; mini-ISP 9ps, both below a prospectively specified 50ps engineering screen. These are not significance tests or general capability conclusions. Single-pair wall-time ratios are observations, not stable action costs. RQ3/RQ4 summaries are attributed supporting thread evidence, not experiments independently rerun here. No LLM, policy/ranker training, future-target evaluation or paid API/GPU/cloud run.

## Publication transformations and evidence boundaries

This is a sanitized public copy. Original private evidence/capsules remain unchanged. User/home/site installation paths and host labels are replaced consistently; private Library item IDs are not published. Verbose third-party vendor help is omitted from logs, with an explicit marker; exact tool commands, runtime outcomes, failures and warnings remain. PUBLICATION_MANIFEST.json records source/public hashes and transformations. Full generated netlists, constraints, DCPs, private ZIP capsules, credential/environment/SSH files, and full third-party validator/help source are excluded; see EXCLUSIONS.md. Source benchmark URLs/license assignments and SHA256 provenance remain in SOURCE_PROVENANCE.json and second-family/SELECTION.json. No inference of functional correctness follows merely from routing success.

Historical reports saying no push/publication describe their time of experiment closeout. Publication was later explicitly authorized; they are preserved as historical evidence rather than silently rewritten. All failed and not-run states remain visible. The first-pass and second-family delivery artifacts are private; Library placeholders are not download links.

## Reuse and validation

scripts/identity_v2.py is directly reusable, and standalone boundary tests in tests/ run with standard-library unittest. Historical scripts and captured argv retain placeholder absolute paths: map /workspace and /local-user to a controlled environment before reuse. Do not run remote executors or assume the recorded source-site toolchain exists. There is no automatic job or new CI.

Tests that inspect actual exported HDL/XDC or recompute the narrow Default proof require intentionally omitted local artifacts; they were run privately and their result receipts are included. They are not claimed rerunnable from this lightweight public export alone. The standalone public tests use synthetic minimal strings to exercise the exact same identity checker, not an EDA circuit or experimental performance sample.

The source repository's existing license applies where established; this snapshot does not relicense third-party toolchains or benchmark data. Use the upstream benchmark licensing/versions stated in the provenance before obtaining artifacts. This publication does not claim paper novelty has been established.
