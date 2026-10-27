# Validation record

Executed 2026-10-27 on Debian 13 x86_64, Python 3.12.14 runtime, g++, Icarus 12.0,
Verilator 5.032 and Yosys 0.52. `results/revised` is authoritative. Prior `results/final` and `results/pilot`
are explicitly superseded and retained as audit evidence. Earlier
`results/pilot` records failed Landlock preexec and missing Yosys lowering from
implementation debugging; do not aggregate the runs.

Final: **24 fixed-response evaluations: 7 pass, 14 fail, 2 unknown, 1 unsupported**.
These are evaluator controls and do not estimate an LLM pass rate.

| Family/path | Positive | Wrong / malformed | Additional checks |
|---|---|---|---|
| SpeCom | B matches golden B | fail / fail | ambiguous A or B selects first A and fails |
| MGen | 100 golden arithmetic TB checks | fail / compile fail | real C++ DPI model via official wrapper |
| TBGen | 64 explicit mux checks | fail / compile fail | output-zero mutant killed; empty TB rejected |
| SVAGen | CRC output bit identity proven | counterexample / parse fail | constant unknown; temporal unsupported |
| RTLFix MultiModal | repaired mux passes golden TB | functional fail / compile fail | original buggy mux rejected |
| RTLFix Text | old/new pair matches | fail / fail | pair-only answer also passes official matcher |

The TB timeout and constant-property adequacy failure are `unknown`, not functional passes. Zero properties and partial
formal proofs classify as inconclusive; a complete nonzero proof is proven;
falsification remains falsified. Raw formal counterexample/proof logs are retained.

Official-compatible simulation scoring is a local reproduction of the pinned
VCSRunner predicate, evaluated on free-simulator logs; it is **not a VCS run**.
The empty TB passes that predicate but fails strict marker/check policy. The
buggy RTLFix mux also passes the generic predicate because its summary includes
`Passed`, even with `ERROR` and `FAILED`; strict golden-TB status rejects it.
The specialized upstream MultiModal RTLFix evaluator uses its own pass marker;
therefore this generic-predicate weakness must not be attributed to that specialized
path without separate validation. Text fragment matching passing without executable
repair is an exact current-upstream result, not a functional proof.

SVAGen status now depends on response content, actual Yosys command state and
emitted formal design, never fixture labels. The positive and wrong-property
runs each contain one actual lowered `$assert` cell. The correct property proves
and falsifies the selected output mutant; the constant property proves on both
designs and remains unknown. A separate swapped-response run places an empty
property set under the positive label: Yosys emits zero assertions and reports
proof success, but the actual scoring chain returns unknown.

`benchmark/regression.py` completed **45 checks**. It replaces the five existing
SVAGen response bodies under contrary labels; correct assertions under `wrong`
and `unsupported` pass, temporal content under `vacuous` is unsupported, a constant
under `malformed` is unknown, and zero properties under `positive` are unknown.
It also runs missing tool paths through the real MGen/TBGen/SVAGen/RTLFix adapters;
all selected positive/wrong/malformed cases classify as error. Real DPI model
infinite-loop execution is unknown, a trapping model is error, and a valid model
under the malformed label passes. Small executed process probes verify the shared
compile/simulation/formal status mapper for timeout, missing executable,
missing dependency, signal crash and unrecognized nonzero exit. Success-looking
simulation/proof text with nonzero exit never passes. Logs and command traces are
under `results/regression`; `regression.json` records each assertion.

`benchmark/validate.py` verifies all six positive scoring paths, wrong/malformed
responses, mutation outcomes, timeout, unsupported/vacuous properties, response
hashes, log links, formal parser consistency and actual seccomp socket denial.
Output is in `evidence/validation.txt`. No proprietary-tool differential check,
coverage equivalence, original pass@5, multimodal vision run or L2/L3 evaluation
was completed.

The source dataset/input bytes are recoverable from the pinned official checkout;
manifest hashes and per-case input lists prevent unnoticed drift. Retained traces
record exact command argv, cwd, timeout, exit state, wall duration and raw feedback.
Build products and upstream-derived staging source copies are removed from the delivery;
actual emitted formal JSON designs remain as inspectable property-count evidence.
Rerunning creates them again. Fixed responses and response hashes are retained.

Raw simulator/compiler logs intentionally preserve trailing whitespace and ASCII
proof banners. Git whitespace checking excludes these `.log` artifacts; authored
code and documentation have no whitespace errors.


The subsequent full schema/asset audit is separate from these 24 controls.
See DATA_COVERAGE.md and evidence/full_dataset_audit_v2: 482 keys audited,
403 original/430 structurally repaired complete schemas, and 753 reference-only
scoring calls over all 251 SpeCom/Text RTLFix keys. The 747-task objective remains
open; old control records and metrics have not been replaced by those counts.


Full-code bounded execution and final matrix validation are recorded separately in
BATCH_EXECUTION.md and results/final_coverage_selected/validation.txt. Every one of
231 public code-case IDs has an outcome; actual commands, preflight refusals,
reference-derived fixtures and model scores remain distinct. The prior 24 controls
and 753 reference checks are retained unchanged.


Latest directed-repair update: DIRECTED_REPAIRS.md supersedes earlier code-outcome
totals. The authoritative matrix has 108 reference-calibration passes, 43 unknowns,
30 errors and 50 adapter-contract refusals across 231 code keys. Context leakage,
post-finish resource lifetime and exact oracle parsing were fixed without a full
sweep or model calls; old evidence remains retained.
