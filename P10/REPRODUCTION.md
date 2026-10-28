# P10 bounded method reconstruction

**Latest CPU extension:** [nested Combine Round 4](nested_combine_round4/REPORT.md) adds Mux assumption propagation and nested-condition conjunction in the e-graph, with 36 passing whole-module SMT/RTL proof pairs, three dual-engine negative controls and 39 actual synthesis calls. It retains the failed first attempt and matched legacy/propagate/combine controls. [Signed-union Round 3](signed_union_round3/REPORT.md) is the preceding extension. These remain authored mechanism workloads and generic synthesis, not original industrial or physical-PPA reproduction. Historical phase statements below describe their original scope and dates.

**Later end-to-end tranche:** [loop/REPORT.md](loop/REPORT.md) and [mechanism coverage](loop/MECHANISM_COVERAGE.md) supersede this phase's stopping point. The earlier fixture results below are preserved; the later work adds actual egglog saturation, constrained DAG extraction, generated RTL equivalence and free synthesis with matched controls.

Completed 2026-10-28 in `/workspace/PaperReproduction`, branch `reproduction/constraint-aware-rover-tcad2025`, remote `Bol-C14/PaperReproduction`. Local only; no push/PR. This is **our small reconstruction**, not released ROVER code and not a reproduction of the paper's physical results.

The final attempt satisfied all ten frozen fixture expectations: four valid rewrites, one signed-range analysis, four deliberately invalid proposals detected, and one empty-domain rejection. No UNKNOWN, timeout or runtime error occurred. This establishes these finite-width identities and rejection controls only.

## What is implemented

`reconstruction/reconstruct.py` has no solver dependency: finite unions of inclusive intervals, conservative truncation, signed/unsigned conversion, add/multiply interval transfer, guard refinement for a few explicitly reviewed patterns, and replacement AST emission. It also implements ASSUME Create, add-Propagate and Combine transformations. It handles only the ten reviewed expression families. No SystemVerilog parser, saturation engine, live-class analysis, general pattern matcher, general equality-class merging, full 179-rule library, RTL backend or industrial verification chain is implemented.

`reconstruction/verify.py` independently encodes each original expression in Z3 bitvectors, translates the emitted replacement AST, checks nonvacuous guards, and checks both local mismatch and complete mux-output mismatch. The optimizer never invokes Z3. Interval claims are checked by asking for a bitvector output outside the emitted interval union. Negative controls inspect an intentionally injected bad candidate after the optimizer refuses it. A separate definedness interpreter checks the actual emitted ASSUME transformations and confirms that replacing bottom with zero is invalid.

The [frozen protocol](reconstruction/PROTOCOL.md) derives semantics with page citations before experiments. Full operator delay functions and implementation details are insufficiently available to justify reproducing calibrated extraction or physical performance in this bounded pilot. The protocol therefore explicitly excludes extraction/Pareto, synthesis and paper-metric claims; it does not replace them with an invented cost function.

## Results

| Fixture | Observation | Meaning |
|---|---|---|
| F01 signed abs, signed x>0 | local/full UNSAT; ASSUME controls pass | Positive signed guard supports the contextual rewrite. |
| F02 unsigned guard misuse | SAT; local witness x=15 | Bit pattern15 is signed -1: abs=1, proposed x=15. |
| F03 bounded shift | local/full UNSAT | y<=1 permits one-bit shift amount. |
| F04 weakened shift guard | SAT; x=204,y=2 | 204>>2=51; low1(2)=0 gives204. |
| F05 7-to-6-bit FMA | local/full/range UNSAT | For three unsigned 3-bit inputs, product+addend <=56. |
| F06 premature truncation | SAT; a=b=15 | Correct 5-bit sum30 differs from zero-extended 4-bit sum14. |
| F07 refined unsigned comparison | local/full UNSAT | a>=8,b<=7 entails a>b. |
| F08 signed result union | range escape UNSAT | Recovers paper's unsigned `[0,22] U [40,63]` for signed5+signed4 assigned6. |
| F09 contextual equality escapes | global SAT x=14; signed-positive local UNSAT | Valid local proof does not justify global replacement. |
| F10 inconsistent guard | guard UNSAT, rejected | Vacuity is not counted as optimization success. |

Canonical machine results: [RESULTS.jsonl](RESULTS.jsonl), [summary](RESULTS.summary.json). Final solver loop wall time0.156724s, process CPU0.157684s, peak process RSS57,768KiB (~56.4MiB). These are tiny-fixture solver-process measurements, not setup time or ROVER runtime.

All attempts are preserved. Attempt1 returned ten expected outcomes but checked manually encoded replacement formulas rather than consuming actual emitted replacements. This was a validation-linkage limitation discovered by review, not a solver failure. The implementation was strengthened to emit replacement ASTs and the verifier now consumes them. Attempt1 logs remain in `reconstruction/attempts/`; canonical results are attempt2. Frozen fixtures/protocol were unchanged. Ten unique fixtures were run twice, not twenty independent benchmarks. No subsequent solver rerun was needed.

## Re-run

Python3.12.14; Z3 4.13.3, package `z3-solver==4.13.3.0`, Linux x86_64 wheel. The official [Z3 README](https://github.com/Z3Prover/z3#python) identifies `z3-solver` as its Python distribution; MIT license. A SHA256-pinned lockfile prevents silently replacing that wheel. Binary and venv are local ignored caches, not committed deliverables.

From the existing cloud checkout:

```bash
cd /workspace/PaperReproduction/P10/reconstruction
.venv/bin/python run.py --output /tmp/P10-rerun.jsonl
```

`--output` must name a new file; the runner refuses to overwrite existing results. For a fresh compatible environment:

```bash
cd /workspace/PaperReproduction/P10/reconstruction
python3 -m venv .venv
.venv/bin/python -m pip download --only-binary=:all: --no-deps --require-hashes -r requirements.lock --dest vendor
.venv/bin/python -m pip install --no-index --find-links=vendor --require-hashes -r requirements.lock
.venv/bin/python run.py --output /tmp/P10-rerun.jsonl
```

On another OS/architecture obtain an officially distributed wheel and explicitly revise the lockfile/provenance; the present lock intentionally admits only the audited Linux wheel. Source and protocol hashes are stored in every row and `SOURCE_VERSIONS.json`. Check source/protocol hashes rather than expecting identical solver witness choices or runtimes.

## Limits and resources requiring a different scope

No new resources are needed for this completed pilot. Full ROVER reconstruction remains high-cost: complete rules/scheduling, SV elaboration, e-graph analysis and original extraction/backend need substantial implementation. Exact original industrial benchmarks, commercial EC/synthesis and TSMC5 assets need legitimate access and configuration. Public substitutes would answer different evaluation questions. No license access was requested and no new resource commitment was made.
