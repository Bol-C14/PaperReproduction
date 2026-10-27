# Directed adapter repairs after the v3 audit

Only 42 distinct cases were investigated/replayed: the 29 prior MGen wall-timeout
cases, four same-path file-limit cases, the six named interface/FSDB/dependency
cases, and three completed logs directly affected by the exact Testcase parser
bug. There was no repeat of the 231-case full sweep. Previous logs and the v3
matrix/selection are retained in `results/coverage_v3_snapshot` and original roots.

## Confirmed adapter defects and causal checks

**Thread context leak.** VerilatedContext construction sets the current thread
context. The original nested DPI reference constructed a private static context
without restoring its caller. An actual Verilator-runtime probe demonstrates that
subsequent `$finish` then marks the inner context, leaving the caller unfinished.
The shared `CallerContextGuard` captures the caller before inner construction,
selects the reference context only during evaluation, and restores the caller on
exit. The same runtime probe confirms the repaired flag destinations.

Async DFF provides a real workflow control: identical upstream file hashes and
identical staged TB, unchanged 3-second timeout, before = timeout; after = completed
in about 5 ms with 100 checks and a detected negative. On the new completed log,
the old exact-spaced parser counts zero successes, while the new precise parser
counts 100. Thus parser and context changes have separate evidence. See
`evidence/context_causal_report.json`, its source diff, and `results/context_regression`.

**Post-finish lifetime defect.** GA_89 exposed a second issue: a line-buffered run
completed all 1004 checks, printed `$finish` and a ~3 ms simulation report, yet the
process remained alive until its 6-second watchdog. Further timeout increases
would conceal an exit/lifetime defect. The reference now has explicit ownership
and a TB `final` DPI cleanup hook, releasing the inner model/context before the
outer main context is destroyed. This fixes GA_89 at the default 3-second bound;
positive and negative executions both exit normally. Async DFF was rechecked
with the same lifecycle code. Exact runtime destructor/lock internals were not
instrumented; the observed ordering failure and controlled ownership repair are
what this evidence establishes. The hook changes resource finalization, not
active RTL behavior, test counts or stimulus timing; its diff is retained.

**Precise oracle lexer.** Shared `mgen_score` recognizes the observed complete
phrases `Test case Passed/Failed` and `Testcase Passed/Failed`, plus explicit
HARNESS counts. Failures override success text, including contradictory zero-fail
counts. Numeric `Mismatches`/`Failed testcases` summaries only cause failure when
nonzero. A bare word `Passed`, zero checks, a timeout or an unrecognized nonzero
exit cannot pass. Ten parser/status checks accompany the executed context probe.
Two finite mux cases now pass their actual positive and negative replays; ALU
exposes failed checks and remains an error, rather than receiving a favorable label.

**Measured workload bounds.** Default DPI simulation timeout remains 3 seconds.
GA_74's unchanged TB requires 200 iterations with #300000 delays; 171 checks were
observed in 3 seconds. GS_46 reached 172 of 200 checks in 3 seconds. Their measured
1.5x completion estimates justify a narrowly scoped 6-second budget. Both then
complete and detect negatives. No RTL timing or test counts were shortened.
GA_89's failed 6-second estimate is retained as evidence; line buffering showed
it was an exit hang, and the lifetime repair succeeds at the original 3 seconds.
Budget derivations are in the two measured-budget evidence JSON files.

Across the 33 original context/resource cases, final outcomes are **18 reference
calibration passes, 9 errors and 6 unknowns**, with no remaining simulation timeout
or file-limit termination. Errors are actual baseline disagreements/diagnostics;
unknowns still lack recognized oracle evidence or a detected negative.

## Named-case findings, with upstream unchanged

| Case | Repair or finding | Latest outcome |
|---|---|---|
| GA_74 | Remove only diagnostic FSDB tasks; retain diff/hash; measured 6 s workload bound | positive + negative calibration pass, 200 checks |
| GA_94 | Remove FSDB; select uniquely TB-instantiated CPU_ref instead of first helper MUX32_ref; repair parser-view whitespace for legal `reg[2:0]`, verified against all generated C++ ports | unknown: negative output mutation not detected |
| GA_97 | Prove default lpm_file=NONE disables guarded readmem with no file override; parse legal `)ref_model` adjacency and declared string bindings | positive + negative calibration pass |
| BRSFmnCE | Resolve the actual default readmem parameter rather than calling every variable path unsupported | data error: RAMINIT.mif is absent; no zero-filled substitute |
| GA_67 | TB supplies W/D to a parameterless reference | error: preserve conflict; do not discard bindings/invent parameters |
| GS_58 | TB names top while source declares omsp_watchdog; all 16 named ports match exactly | explicit declaration-name-only overlay; positive + negative pass |

Waveform-only removals are restricted to simple FSDB diagnostic task calls, with
source/staged hashes and unified diffs. No upstream source is edited. The module
alias changes only the declaration name and preserves ports, defaults and body;
its exact diff is retained. Reference-module selection and packed-type whitespace
normalization are parser views, not source logic rewrites. Actual elaborated C++
port sets must match; missing ports are never silently omitted. String parameter
values are passed explicitly to both reference elaboration and DPI wrapper.

GA_94 remains unknown deliberately. Its original expression
`ref_out === ref_out^dut_out^ref_out` feeds a scalar match. A separate real Icarus
probe reproduces the precedence/truncation blind spot: a difference at concat bit
4 (value-output bit 0) leaves the original match true, while a fully parenthesized
vector comparison detects it. The LSB difference is detected. This explains the
observed surviving negative. The official comparator was not repaired to turn
this case into a pass. This finding concerns the pinned public TB and substituted
workflow, not a claim about unobserved original-paper executions.

## Updated coverage and verification

The latest 231-code-case selection has **108 reference calibration passes,
43 unknowns, 30 errors, 50 explicit adapter-contract refusals**. These are not
independent specification validation or LLM scores. The original 747-task identity
and metrics remain open. All 482 public keys still have a final matrix row.

`validate_batch.py` checks actual command/control links, no timeout in a passing
record, nonzero formal property cells, real mutation counterexamples and constant
property controls. The original 24 controls, 45 earlier regressions, 753 matcher
controls and full asset audit remain separate and unchanged. Re-run the context
probe with `context_regression.py --tools PATH --output EMPTY_DIR`.

No paid calls, push/PR, upstream modifications or pending approvals occurred.
All directed commands have ended; residual errors/unknowns are retained explicitly.
