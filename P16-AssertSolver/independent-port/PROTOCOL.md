# Bounded evaluator-contract protocol (written before tests)

Objective: measure the difference between golden repair text and functional behavior on one reviewed public combinational example, not reproduce learned AssertSolver repair or official paper scores.

Upstream source is read only: repository commit 96882fe018379d1974fd1e1b6c3b8f75e4de3d0e, testbench/SVA-Eval-Machine.json, record module_name pcx_buf_pdl. The released module maps a five-bit input to a five-bit output. Its embedded assertion uses an unconditional antecedent and requires output == bitwise complement of input. The buggy assignment omits inversion. The released fixed line restores inversion. Source-derived fixture provenance will be saved separately.

Official evaluator status: the inspected release does not expose the task-specific score implementation. The paper describes line comparison for DPO selection and solving assertion failures for final evaluation. Neither proves final exact-text scoring nor executed-assertion scoring. The independent checker below is explicitly a port with a narrower contract.

Port scope: Python standard library only, current CPU, no installs or model calls. Parse a strict JSON repair object (CoT, buggy_code, correct_code string fields), enforce one exact unique buggy-line replacement, and require the original assertion text unchanged in each supplied RTL fixture. Parse only three deliberately supported RHS forms: a five-bit input, its bitwise complement, or its XOR with an explicit five-bit binary constant. Exhaustively compare all 32 input values against the fixed five-bit inversion specification. This is a two-state, stable-value combinational check, not a SystemVerilog frontend, concurrent-SVA scheduler, simulator, or formal solver. It does not establish event scheduling, X/Z, reset, sequential, or general SVA semantics. Unsupported expressions yield UNKNOWN, never PASS. Assertion preservation rejects deletion, weakening, and forced-false antecedents before evaluating data behavior. This prevents these fixtures from earning acceptance but does not claim a general vacuity analyzer.

Report two independent scores per fixture: whitespace-normalized golden fixed-line match (explicitly our chosen baseline, not an official metric) and independent status. Functional mismatch gives FAIL with first counterexample. Non-JSON/schema/patch ambiguity gives INVALID_OUTPUT. Modified/missing assertion gives INVALID_CONTRACT. Budget exhaustion gives TIMEOUT (port evaluation budget, not an HDL solver timeout). Unexpected internal exceptions give ERROR and fail the run. Only PASS earns functional credit. Cover all 32 inputs before PASS. ERROR is reserved; no artificial crash fixture is required.

Ten pre-reviewed fixtures, no model output or discovered variants:
1. Released correct inversion: expected text match and PASS.
2. Equivalent XOR with 11111: expected text mismatch and PASS.
3. Unchanged buggy assignment: expected text mismatch and FAIL.
4. XOR with 11110: expected text mismatch and FAIL.
5. Correct line plus false assertion antecedent: expected text match and INVALID_CONTRACT.
6. Correct line plus constant-true assertion consequent: expected text match and INVALID_CONTRACT.
7. Correct line plus removed assertion: expected text match and INVALID_CONTRACT.
8. Malformed JSON: expected text score unavailable and INVALID_OUTPUT.
9. Unsupported but mathematically equivalent subtraction expression: expected text mismatch and UNKNOWN; correctness does not expand parser support.
10. Released correct line with an evaluation case budget of zero: expected text match and TIMEOUT; demonstrates status handling only.

Split audit: inspect existing filename inventory and selected record keys only. No train/test overlap inference; missing training data and source-parent/template IDs prevent a family-split determination.

Limits: <=10 reviewed fixtures, <=20 tool runs for this continuation, <=2 hours setup, <=2 GB downloaded, current CPU. Run checker in an isolated interpreter (`python -I`), no network in checker, only reviewed bounded integer expressions, process timeout via coreutils. Preserve protocol, script, fixtures, commands, stdout/stderr, environment and resource ledger. Stop after one bounded run and necessary corrections; any correction must be disclosed.
