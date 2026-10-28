# P10 claim audit

**Historical fixture-phase audit.** For later implemented mechanisms and controlled synthesis evidence, see [loop/REPORT.md](loop/REPORT.md) and [loop/MECHANISM_COVERAGE.md](loop/MECHANISM_COVERAGE.md). Statements below that extraction/synthesis was not implemented describe the earlier milestone; they are not the current overall status.

This file concerns our bounded pilot; the earlier `ASSET_AUDIT.md` is a historical audit-only snapshot and its “no execution” statement describes that earlier phase.

Primary sources: [accepted paper](https://spiral.imperial.ac.uk/bitstreams/de68c6e8-a66d-42d6-ae3e-16eab9fc9782/download), [author thesis](https://samuelcoward.co.uk/assets/pdf/Thesis_Imperial.pdf). Accepted-paper page numbers below are printed manuscript pages, not journal pages. The full paper was recovered in the previous audit; attempted narrow re-access returned405. Thesis Chapter5 supplied cross-checkable equations/tables. No unavailable artifact contents were invented.

| Claim | Source / evidence | Verdict and boundary |
|---|---|---|
| Original software unavailable openly | Thesis §1.3 p9, Chapter5 mapping §1.4–1.5 | Author explicitly says it cannot be open-sourced; no later full release verified. This reconstruction is ours. |
| ASSUME localizes subdomain equivalence and bottom is distinct from zero | Paper §III pp4–5; thesis pp88–91 Eqs5.5–5.9/Table5.1; F01 Create/Propagate/Combine and bottom control | Implemented restricted transforms and symbolic definedness; not general e-graph congruence or saturation. |
| Guarded abs can simplify | Paper p3 Eq1; F01/F02/F09 | Verified for explicit 4-bit modular abs with positive signed guard. Unsigned guard and global export rejected. INT_MIN is not abstract mathematical abs; the explicit finite-width semantics are fixed. |
| Bitvector ranges must honor signedness and truncation | Paper pp6–7 §IV-A; thesis pp97–98; F05/F06/F08 | Recovers the paper example's interval union and catches early truncation. Does not establish every transfer function sound across all widths or implement SV contextual sizing. |
| Shift amount can shrink under a proven bound | Paper p10 Eq24; thesis p106 Eq5.19; F03/F04 | Valid for y<=1; expanding to y<=2 generates a counterexample. No extrapolation to arithmetic shifts. |
| Range-proven unsigned comparison becomes true | Paper p8 §IV-B; thesis p99; F07 | Verified for a4>=8,b4<=7 only. |
| Empty domain is a valid optimization result | F10; additional pilot control | Rejected. UNSAT guard is recorded separately and not counted as success. |
| Exact paper area-delay extraction implemented | Paper pp8–9 Eqs16–22; derived in protocol | **Not implemented or tested.** No cost model substituted, no physical/ILP claim. |
| 30% faster / 1% smaller replicated | Official abstract and paper TableIII | **Not tested.** No synthesis, technology library, original suite or commercial baseline. |
| Tiny pilot scales like ROVER | Ten unique fixtures, two attempts | **Unsupported.** No scalable saturation or mux-duplication benchmark. Prior asset audit's scaling-gap control remains future work. |
| Independent verification of actual emitted candidates | Attempt2 verifier consumes replacement AST; originals independently encoded; optimizer does not use Z3 | Supported for this fixture set. Both sides still use our chosen explicit-width semantics; not independent SV parsing, proof-certificate checking or cross-solver validation. |

Four negative proposals are controls on our reconstruction/verification interface, **not discovered vulnerabilities or accusations against ROVER**. The valid/invalid expectations were frozen before runs. SAT models are re-evaluated against their full SMT mismatch formula; UNSAT relies on pinned Z3, with no separately checked proof certificate.

Protocol scope did not change after results. The only post-attempt1 implementation change connected actual emitted replacements to verification; old logs were retained. No cases, failures, UNKNOWNs or timeouts were filtered. Runtime failures0; validation-linkage limitation1 (corrected and disclosed).
