# ROVER signed interval-union CPU closure
A new signed value-analysis mechanism is implemented and exercised; historical P10/loop v4 remains unchanged. This is an independent ROVER-inspired reconstruction on eight authored guarded arithmetic instances, not original Intel source or full-paper reproduction.

The new domain preserves disjoint unsigned bit-pattern intervals for signed ranges crossing zero, refines signed constant comparisons and Boolean combinations, and propagates modular Add/Mul, Cut/zero-Ext, logical shift, Neg, Abs and Mux unions. It intersects equivalent e-class representatives and limits interval explosion conservatively. Bounds feed the existing width-reduction rules and constrained DAG extraction. The input DSL adds Slt, And and Neg consistently in egglog declarations, cost model, symbolic BV semantics and emitted RTL. Signed constants must be representable at their operand width; no arbitrary SystemVerilog frontend is claimed.

## Actual outcomes
24 configurations (four kernels × two widths × three arms), each with two fixed relative DAG-delay targets, completed. All48 selected outputs pass unconditional full-domain Z3 BV equivalence and separate parsed-RTL Yosys SAT equivalence. All3 wrong signed-guard, missing-guard and truncation controls return SAT counterexamples in both engines. No positive proof fails, times out or is discarded. Every DAG optimization reports equal objective lower/upper bounds.

Six of eight kernel/width pairs improve proxy area against both original-hull/context_live and union/agnostic controls; two nested-Mux cases tie. The table uses the first delay target; second-target proxy areas are identical; one tied-cost negative-product8 representative has54 gates/depth12 rather than54/depth13. All raw variants remain retained. Proxy area is an uncalibrated extraction objective. Generic gates and depth are separately measured after selection using actual Yosys synth -noabc, including complete guards and muxes. Neither is physical PPA, cell-library area, STA or a silicon result.

| Kernel | Bits | Hull proxy area | Union proxy area | Actual generic gates | Actual gate depth |
| --- | ---: | ---: | ---: | ---: | ---: |
| signed_magnitude_multiply | 8 | 73 | 55 | 185 → 97 | 19 → 16 |
| wrapped_signed_offset | 8 | 73 | 58 | 165 → 90 | 18 → 15 |
| signed_range_mux | 8 | 49 | 49 | 67 → 67 | 12 → 12 |
| negative_product | 8 | 65 | 50 | 126 → 54 | 17 → 13 |
| signed_magnitude_multiply | 16 | 145 | 103 | 420 → 168 | 25 → 18 |
| wrapped_signed_offset | 16 | 145 | 106 | 394 → 145 | 26 → 17 |
| signed_range_mux | 16 | 97 | 97 | 144 → 144 | 15 → 15 |
| negative_product | 16 | 129 | 90 | 302 → 70 | 23 → 13 |

The signed-magnitude kernel restricts a to [-3,3]. Its bit patterns form [0,3] union [2^w-3,2^w-1]; an unsigned hull loses this information, while Abs maps the union into [0,3]. Narrow arithmetic follows without assuming the guard outside its original mux. Wrapped-offset and negative-product cases test modular wrapping and negative-only ranges. The nested-Mux kernel exposes a remaining propagation gap and is retained as a tie.

## Independent audit and cost
The transfer-domain calibration checks1,858,952 concrete containment decisions over seeded interval pairs at widths1–8, with all contained values checked, plus all signed thresholds/bit encodings. These software checks support the new abstract operations; the full-domain SMT/RTL circuit proofs are separate and remain the acceptance criterion. Forty-six unique actual post-selection synthesis calls all succeed. Synthesis never guides candidate selection, and no best-of-synthesis winner is chosen.

Main experiment wall53.4535s; optimizer-worker wall sum39.9528s; independent domain/synthesis audit10.7655s. Maximum optimizer-worker RSS117,648KiB. These exclude dependency setup and authoring; they are not full-task CPU totals. Seed20261028. Execution stayed in taskset16–23 with OMP/MKL/OpenBLAS/NumExpr limits8 and one sequential experiment process; significant APRIL headroom remained. No paid compute, GPU, provider API, credentials or global environment changes.

Dependencies installed in the isolated env from official PyPI: egglog14.0.0, z3-solver4.13.3.0, yowasp-yosys0.63.0.0.post1107. Yosys identifies0.63 git70a11c6bf, an explicitly unofficial YoWASP packaging of Yosys. Python3.12.12. install.log retains exact resolved packages. Base repository SHA5f787308443dad7bbe1f5d314f0ec5a73122f55b.

## Protocol, evidence and replay
PROTOCOL.json was timestamped before experiments; evidence/manifest.json freezes actual fixtures and optimizer/runner source hashes. The independent audit was added after selection and did not change any frozen optimizer/runner source; all frozen source hashes were rechecked before packaging. evidence/summary.json, audit.json, journal.jsonl and per-configuration optimization/proof directories retain all selected terms, DAG bounds, raw SMT, RTL, complete Yosys logs, source hashes and costs. No experiment attempt needed a repair or retry. A post-packaging read-only audit rejected an initial assumption that both delay-target gate/depth counts were identical; the report was corrected against retained measurements, without any experiment rerun. Dependency/runtime prewarming was setup, not an experimental result.

On APRIL:
- checkout: /home/shugu/work/paper-reproduction-april-20261028/checkouts/rover
- env: /home/shugu/work/paper-reproduction-april-20261028/envs/rover
- original results: /home/shugu/work/paper-reproduction-april-20261028/results/rover/signed_union_round3
- logs: /home/shugu/work/paper-reproduction-april-20261028/logs/rover

run.py freeze refuses an existing results directory, and run.py refuses an existing experiment journal. For an independent replay first select a new isolated output path in a copied runner; preserve the original evidence. Execute from this directory with the isolated env and taskset16–23; set YOWASP_CACHE_DIR and XDG_CACHE_HOME to the owned cache/rover directory. audit.py also refuses overwrite. Frozen original commands are recorded per worker/proof and logs; COMMANDS.md records outer execution.

## Remaining gaps
Nested Combine/assumption propagation is not added. The nested-Mux control remains a limitation. This domain is a finite unsigned-bit-pattern union representation with signed comparison/Abs/Neg support, not unrestricted signed RTL operator coverage; arithmetic right shifts, signed division, X/Z, sequential semantics and arbitrary elaboration remain unsupported. The interval-count cap may lose precision. Hand-authored kernels are in-sample mechanism examples, not held-out industrial evidence. Eight saturation rounds and5000-node budget do not guarantee mathematical saturation. Physical cost calibration, TSMC5 commercial-flow results, original benchmark assets and general SV ingestion remain open. No publication or push occurred.
