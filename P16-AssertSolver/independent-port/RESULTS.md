# Independent evaluator-contract audit — completed bounded milestone

This is an independently constructed, restricted checker port, not the official AssertSolver evaluator and not learned repair reproduction. Branch: `reproduction/assertsolver-dac2025`. Upstream source remains separate in `../../P16-AssertSolver-source`; the pinned public example and ten fixed reviewed fixtures are recorded locally. Protocol was written before fixture construction and testing.

## Findings

**The official final scoring rule remains unverified.** The inspected upstream tree contains the benchmark and a text-generation demo but no task-specific repair evaluator. Paper v1 explicitly describes buggy-line comparison for selecting DPO negatives, while its final evaluation describes effective assertion repairs. That does not settle whether final correctness used exact text, normalization, manual review, or executed assertions. Vendored token/ROUGE/BLEU metrics are not evidence of a functional SVA oracle. No claim that the official scores used exact-text matching is supported by the released material inspected here.

**A golden repair-line match and a behavioral acceptance decision measure different things.** In the fixed ten-fixture control set, five responses match the whitespace-normalized golden replacement, while two pass the independent checker. These are deliberately selected control outcomes, not benchmark accuracy estimates, model results, or an unbiased evaluation sample.

| Fixture | Golden fixed-line match | Independent result | Interpretation |
|---|---|---|---|
| Released fixed line | Yes | PASS | All 32 five-bit inputs satisfy inversion. |
| XOR with five-bit 11111 | No | PASS | Equivalent repair with different text. |
| Unchanged buggy line | No | FAIL | First counterexample: input 0, output 0, expected 31. |
| XOR with five-bit 11110 | No | FAIL | First counterexample: input 0, output 30, expected 31. |
| False assertion antecedent | Yes | INVALID_CONTRACT | Assertion-preservation guard rejects a vacuous implication. |
| Constant-true consequent | Yes | INVALID_CONTRACT | Guard rejects weakened requirement. |
| Removed assertion | Yes | INVALID_CONTRACT | Guard rejects skipped assertion. |
| Malformed JSON | Unavailable | INVALID_OUTPUT | Parsing failure earns no behavioral credit. |
| Equivalent subtraction | No | UNKNOWN | Deliberately unsupported grammar; never counted as success. |
| Zero-case evaluation budget | Yes | TIMEOUT | Budget exhaustion earns no behavioral credit. |

All ten predeclared expectations passed in the sole checker run, with no implementation corrections or reruns. Results: 2 PASS, 2 FAIL, 3 INVALID_CONTRACT, 1 INVALID_OUTPUT, 1 UNKNOWN, 1 TIMEOUT, 0 ERROR. The TIMEOUT fixture tests deterministic case-budget handling, not a solver taking too long. The outer ten-second process guard did not fire. ERROR is an explicit reserved internal-failure status; it was not artificially induced.

## What was actually checked

The public `pcx_buf_pdl` example is a five-bit combinational inverter with an identity-assignment bug. The independent implementation parses only identity, bitwise complement, and five-bit constant XOR assignment forms. It exhaustively enumerates 32 stable two-state input values against an independently stated inversion specification. It does not interpret the SVA language or run RTL. The assertion-preservation check is textual, and the three adversarial contract fixtures are supplied-RTL mutations alongside a candidate line replacement. They test an evaluator's contract boundary; they are not claims about attacks supported by the published one-line repair interface.

No model was loaded, no repairs were generated, and no HDL compiler, simulator or formal tool was installed or executed. Python isolation (`-I`), the execution environment sandbox, a ten-second process timeout, fixed reviewed fixtures and no dynamic `eval`/`exec` bound the run. The checker has no network or subprocess code. The fixture builder uses only a local cached Git object with `GIT_NO_LAZY_FETCH=1`.

**Limits:** only this trusted fixture family is supported. The port is not a general verifier or a safe intake for arbitrary modified RTL. It does not parse the full module or verify unchanged logic outside the protected assertion block. It does not model four-state X/Z, event scheduling, glitches, initialization, reset, sequential behavior, implication reachability across traces, solver uncertainty, or arbitrary equivalent expressions. Unsupported syntax is UNKNOWN. A real concurrent-SVA toolchain and pinned proof/simulation policy would be needed to evaluate these further. No such test is claimed.

## Parent/template split metadata

The selected released record exposes `module_name`, RTL, buggy/fixed lines, specification and an assertion-log string. It supplies no source-parent identity, template-family ID or train/test lineage. The complete upstream filename inventory contains no split manifest, and the named training data are unavailable in the inspected snapshot. The paper's module-name grouping cannot be verified as a parent/template-family separation from these assets. No overlap analysis was run and no leakage is alleged.

## Inspectable evidence

- `PROTOCOL.md`: pre-test contract and fixture expectations.
- `source_record.json`: pinned public example; upstream commit in `provenance.json`.
- `fixtures.json`: all ten reviewed fixtures, expected statuses, and rationales.
- `checker.py`: independent restricted evaluator; `build_fixtures.py`: provenance-preserving construction.
- `results.json` and `results.csv`: exact statuses, counters and counterexamples.
- `logs/`: stdout, stderr, exit codes and UTC run boundaries.
- `COMMANDS.md`, `RESOURCE_LEDGER.json`, `SHA256SUMS`: command record, resource accounting and artifact hashes.

Official references: [repository snapshot](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/tree/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e), [released benchmark](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/testbench/SVA-Eval-Machine.json), [paper v1](https://arxiv.org/html/2503.04057v1). No new remote source requests were needed for this continuation.

The bounded evaluator-contract milestone is complete. Official-score reconstruction, general SVA semantics and learned-repair measurement remain unverified and outside this run. No new resource request is needed for the completed milestone.
