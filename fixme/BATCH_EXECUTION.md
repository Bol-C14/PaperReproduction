# Full public-code-case bounded execution

The remaining 227 code cases were processed, alongside a recheck of the four
prior EDA inputs: **231 unique code cases** (81 MGen, 108 TBGen, 41 SVAGen,
one MM RTLFix). Every case has an adapter outcome. This is reference calibration,
not a live LLM benchmark and not reproduction of original pass@5.

The authoritative selected records are `results/full_code_selected/results.json`.
Their immutable evidence roots are recorded individually. The definitive **482-row
matrix** is `results/final_coverage_selected/matrix.csv` / `matrix.json`.

| Group | Reference calibration pass | Unknown | Reference/adapter error | Adapter contract unsupported |
|---|---:|---:|---:|---:|
| MGen | 5 | 38 | 17 | 21 |
| TBGen | 49 | 34 | 5 | 20 |
| SVAGen | 30 | 0 | 0 | 11 |
| RTLFix MM | 1 | 0 | 0 | 0 |
| Total | **85** | **72** | **22** | **52** |

There were **848 recorded command attempts** across the full corrected batch and
focused follow-ups. The latest evidence selection contains 720 commands: 199 code
cases have commands in their latest attempt and 32 were rejected in content-based
preflight. Across retained attempts, **200 unique code cases actually invoked
verification tools**; one case was later identified as unsuitable for a cloned
oracle because it contains internal randomness. The other 31 have only content/
interface-contract refusal evidence. They are not claimed as simulated or proven.
Of the original 227 additional cases, 196 have actual tool execution somewhere in
the recorded attempts and 31 have preflight-only decisions. No code case remains
uninspected, but broad language/model coverage is still incomplete.

## What the reference providers really do

* **MGen:** compile the supplied reference RTL (or DUT when no ref module exists)
  into a separate Verilator C++ model, expose the real DPI signature through the
  official wrapper, and run the supplied golden TB. The C++ model uses its own
  VerilatedContext. Actual resolved port widths are inspected; TB parameter
  bindings are resolved with a bounded constant-expression parser and applied
  to reference elaboration. A second response flips one output bit. Passing
  requires a completed baseline with explicit checks and a detected negative.
  This is a generated reference fixture, not LLM-produced C++ or independent
  specification validation. Two-state semantics are explicit; inouts, ports
  wider than 64 bits, explicit X/Z reference semantics and internally timed
  submodels have separate unsupported contracts.
* **TBGen:** elaborate the real interface, generate a seeded 64-cycle SV checker,
  and compare the supplied DUT against a renamed copy under identical stimulus.
  Icarus keeps four-state values: any observed unknown blocks a pass. The
  negative checker perturbs the expected output vector by one bit. This verifies
  checker execution/negative sensitivity, not stimulus completeness, independent
  specification correctness or VCS coverage. Clock/reset heuristics and seed are
  recorded. Multiple clocks, unhandled interfaces and independent source
  randomness are refused explicitly rather than assigned invented behavior.
* **SVAGen:** extract a direct continuous-output relation, honor assignment-target
  truncation with a width cast, and assert the relationship using immediate
  assertions. For duplicate generate-branch drivers, actual Verilator XML source
  locations identify the elaborated active assignment. Yosys runs two-timeframe
  SAT with arbitrary initial state; no environment assumptions or zero-state
  initialization are added. The actual assertion count must be nonzero. A true
  RTL output mutation must falsify the same assertion. A constant assertion is
  also run against both source and mutant and remains unknown. This is an
  output-invariant calibration fixture, **not concurrent temporal SVA generation,
  full-specification proof or equivalence to VC Static**. Designs without this
  supported output-relation pattern remain adapter-unsupported.
* **RTLFix MM:** execute the existing reviewed mux repair and the original faulty
  RTL against the supplied TB. Text RTLFix remains the official reference-only
  matcher audit; it is never represented as an executable repaired-design proof.

All results are content/tool-state driven. No fixture/case label assigns a pass.
Each pass requires a successful positive and a detected negative; formal passes
also retain nonzero property evidence and constant-property counterfactual logs.

## The 482-row matrix is not a new model pass rate

| Final state | Cases |
|---|---:|
| Complete reference-only SpeCom/Text RTLFix scorer checks | 199 |
| Missing/invalid original field-level assets or reference | 52 |
| Code reference calibration passed | 85 |
| Insufficient proof/oracle evidence, without wall timeout | 39 |
| Resource limit/external signal, unknown outcome | 4 |
| Actual wall timeout, unknown outcome | 29 |
| Reference/adapter diagnostic error | 19 |
| Additional missing external input dependencies | 3 |
| Explicit adapter contract unsupported | 52 |
| Total | **482** |

The **430** repaired schema count is field-level readiness, not dependency closure
or executable success. Three field-ready TBGen cases additionally lack referenced
input assets: `sq_sin` needs `../tables/sin_table.hex`, `gmii_tx_bfm` needs
`ptpdv2_tx.pcap`, and `alt_exc_upcore` needs its memory configuration/data and
transaction files. These are data errors, not model failures. Existing constant
basename read dependencies are hash-checked and staged; output files and fopen
mode strings are not misclassified as missing input assets.

Unknowns remain explicit. Some supplied MGen TBs print a stream of passed tests
but never terminate within the wall budget; others provide monitor output without
a recognized self-checking oracle. Unknown startup/state in four-state TB checks
also blocks passing. Such cases are not claimed wrong. Error examples include
illegal packed integer TB declarations, undefined RTL variables, a testbench
instantiating a missing module, mixed assignment restrictions, and hierarchical
reference-state accesses that a DPI wrapper does not expose. No silent source
repair turns these into passes.

The prior **753 reference-scorer controls over 251 directories** are separate from
these 231 code-adapter records. Nor are 85 calibration passes model answers.
`live_llm=false` and `is_model_score=false` accompany the final matrix. The original
747-task identity and published metrics remain open because original assets and
comparable sampled responses/tool semantics have not been recovered.

## Bounds, isolation and retained evidence

At most two workers run. Each worker starts its own 150-second case budget when
execution begins; queue time is excluded. Commands have individual wall limits:
interface 15 s, reference emission 20 s, reference C++ build 45 s, DPI compilation
50 s, Icarus compilation 20 s, simulation 2–3 s, Yosys command 15 s with SAT timeout
5 s. Process CPU and per-file limits are 90 s and 16 MiB. Process-group killing
prevents surviving children on a wall timeout. There were no observed OOM/physical disk failures or pending approvals.
Resource-limit signals, including the 16 MiB per-file output cap, remain unknown
and are split out in the final matrix. A timeout remains unknown, even when earlier text says passed.

Filesystem sandboxing is unavailable on this host. Execution is limited to
hash-verified official sources and locally generated/reviewed fixtures, with
sanitized environment, no network syscalls and explicit refusal of process/foreign
code execution and unreviewed file dependencies. Only constant basename output
paths or manifest-verified basename input files are accepted for file I/O. This
is not an arbitrary untrusted-code service.

Per-case source inputs, positive/negative responses, property designs, XML,
command arguments, raw feedback and structured results are retained. Each attempt
has `artifact_manifest.json`; rebuildable binaries, object directories and large
waveform files remain local and are hash-listed in `omitted_artifacts.json` rather
than embedded in the small archive. Batch staging copies are private validation
inputs; no upstream redistribution license is granted, and nothing was published.
Tool packages remain pinned setup downloads.

The first full-batch attempt incorrectly charged queue time to case budgets;
200 records had no tool call. It is explicitly **superseded**, retained for audit,
and excluded from coverage totals above. Interface trials and corrective attempts
are preserved, and selection history explains changed outcomes. Earlier results
are not overwritten or silently counted as executed coverage.

## Run or inspect

```sh
python3 fixme/benchmark/batch_code.py --upstream .cache/fixme/upstream \
  --tools .cache/fixme/tools --audit fixme/evidence/full_dataset_audit_v2/audit.json \
  --output fixme/results/new_code_batch --workers 2
python3 fixme/benchmark/validate_batch.py \
  --audit fixme/evidence/full_dataset_audit_v2/audit.json \
  --batch fixme/results/full_code_selected --output /tmp/fixme-coverage-check
```

`--cases` selects exact case IDs for bounded investigations; `--limit` supports
small pilot checks. Output directories must be empty. The default provider derives
calibration fixtures from supplied references; it does not make model requests.

Remaining work is concrete: broaden reviewed clock/inout/wide-port and temporal
contracts, investigate 19 reference/adapter errors and 72 unknowns, obtain absent
external datasets/original MM assets, and evaluate independently supplied model
responses with comparable oracles. These are not described as completed model
benchmarking, and no paid API or proprietary-tool access has been requested.
