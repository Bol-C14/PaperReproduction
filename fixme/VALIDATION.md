# Validation record

Executed 2026-10-27 on Debian 13 x86_64, Python 3.12.14 runtime, g++, Icarus 12.0,
Verilator 5.032 and Yosys 0.52. `results/final` is authoritative. Earlier
`results/pilot` records failed Landlock preexec and missing Yosys lowering from
implementation debugging; do not aggregate the runs.

Final: **24 fixed-response evaluations: 7 pass, 15 fail, 1 unknown, 1 unsupported**.
These are evaluator controls and do not estimate an LLM pass rate.

| Family/path | Positive | Wrong / malformed | Additional checks |
|---|---|---|---|
| SpeCom | B matches golden B | fail / fail | ambiguous A or B selects first A and fails |
| MGen | 100 golden arithmetic TB checks | fail / compile fail | real C++ DPI model via official wrapper |
| TBGen | 64 explicit mux checks | fail / compile fail | output-zero mutant killed; empty TB rejected |
| SVAGen | CRC output bit identity proven | counterexample / parse fail | constant rejected; temporal unsupported |
| RTLFix MultiModal | repaired mux passes golden TB | functional fail / compile fail | original buggy mux rejected |
| RTLFix Text | old/new pair matches | fail / fail | pair-only answer also passes official matcher |

The TB timeout is `unknown`, not a functional pass. Zero properties and partial
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

`benchmark/validate.py` verifies all six positive scoring paths, wrong/malformed
responses, mutation outcomes, timeout, unsupported/vacuous properties, response
hashes, log links, formal parser consistency and actual seccomp socket denial.
Output is in `evidence/validation.txt`. No proprietary-tool differential check,
coverage equivalence, original pass@5, multimodal vision run or L2/L3 evaluation
was completed.

The source dataset/input bytes are recoverable from the pinned official checkout;
manifest hashes and per-case input lists prevent unnoticed drift. Retained traces
record exact command argv, cwd, timeout, exit state, wall duration and raw feedback.
Build products and upstream-derived staging copies are removed from the delivery;
rerunning creates them again. Fixed responses and response hashes are retained.

Raw simulator/compiler logs intentionally preserve trailing whitespace and ASCII
proof banners. Git whitespace checking excludes these `.log` artifacts; authored
code and documentation have no whitespace errors.
