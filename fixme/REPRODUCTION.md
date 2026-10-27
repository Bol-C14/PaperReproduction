# FIXME structural reproduction

Branch: `reproduction/fixme-aaai2026` in `Bol-C14/PaperReproduction`. No push/PR.
Paper: [AAAI-26, DOI 10.1609/aaai.v40i2.37079](https://ojs.aaai.org/index.php/AAAI/article/view/37079/41041).
Official code: https://github.com/ChatDesignVerification/FIXME at
`e875437fbb11590b71775b32d3579726d702cfc6` (2026-08-12). Initial release is
`b19526770f101fed029b23e24523680bf5a7acfc` (2026-08-03); neither is assumed to be the paper's exact dataset.

The full original structural-reproduction objective remains **open**. The current
EDA pilot used six unique case directories. A subsequent all-case audit now covers
all 482 public keys and 753 cheap reference-scorer controls; see
[the exact 747/482 reconciliation and coverage plan](DATA_COVERAGE.md).
403 original schemas are complete; explicit source-verified overlays bring this
to 430. These counts are not model or HDL pass rates.

## Run

On Linux x86_64, with Python 3, git, curl/HTTPS access, dpkg-deb, g++, make,
libreadline8, libffi8, libtcl8.6 and libseccomp2:

```sh
cd fixme
python3 benchmark/setup.py --root ../.cache/fixme
python3 benchmark/run.py --upstream ../.cache/fixme/upstream \
  --tools ../.cache/fixme/tools --output results/new-run
python3 benchmark/validate.py results/new-run
python3 benchmark/regression.py --upstream ../.cache/fixme/upstream \
  --tools ../.cache/fixme/tools --output results/new-regression
```

Setup fetches public pinned code and Debian binary packages into a local directory;
it runs no upstream shell scripts, installs no system package and calls no model API.
Do not run it on an existing output directory. The tool package hashes are pinned.
No paid API, model credentials, cloud compute or external publication is used.

`run.py --responses reviewed.json` accepts `{subset: {variant: raw_response}}` overrides.
This is an offline response adapter, not a live model adapter. The dataset adapter
loads pinned directories, hashes all inputs, reuses official SpeCom/RTLFix scoring,
MGen DPI wrapper construction and TBGen preparation. All executed fixtures have
been inspected locally; arbitrary model code requires stronger host isolation.

## Fidelity and schema

Canonical task key: `subset/level/modality/case`. Manifest records each file's name,
bytes and SHA256. Levels/modality come from upstream paths, not inferred from filenames.
Paper difficulty starts from 0–100, 100–200 and ≥200 RTL lines, then experts
refine labels using control flow, state machines and interfaces. Boundary rules
are not independently re-inferred here. The fixed release contains 482 directories: SpeCom 149, MGen 81, TBGen 108, SVAGen
41, RTLFix 103. Counts are audited in `evidence/dataset_manifest.json`.

| Subset | Input → response | Current official evaluator | Pilot |
|---|---|---|---|
| SpeCom | spec + q → option | first A–D token matches ref | exact evaluator; L1 full adder |
| MGen | RTL interface/TB → C++ DPI model | VCS wrapper co-simulation | official wrapper + golden 100-vector TB; Verilator |
| TBGen | spec + RTL → SV testbench | VCS execution + coverage | official staging; Icarus; 64 explicit checks and mutant |
| SVAGen | spec + RTL → assertions | VCS syntax + VC Static proof | Yosys SAT of one immediate combinational invariant |
| RTLFix | faulty RTL/spec → repair | Text old/new fragment match; MultiModal simulation | both exact Text matcher and Icarus mux repair |

Every control uses a single fixed response. The suite covers five families, not
three difficulty levels or multimodal perception performance. Raw inputs remain
in the immutable upstream checkout; trace input hashes identify them exactly.
Each case keeps response, compile/simulation feedback, result and command events.
There is no sequential agent handoff between the independent subsets.

## Tool substitution contract

* Icarus 12.0 uses event-driven four-state Verilog/SV simulation, but supports a
  smaller SV language subset than VCS. No classes/UVM, constrained random,
  covergroups, full concurrent SVA or DPI are promised. Compile rejection is a
  failure for supported fixtures; unavailable tools/isolation are infrastructure errors.
* Verilator 5.032 supports timing and DPI here, but uses predominantly two-state
  compiled semantics. X/Z initialization, scheduling races and DPI wrapper
  sensitivity can differ from VCS. The selected combinational full adder avoids
  those differences; sequential/inout/wide-port models are not certified.
  Upstream falls back to replacing DUT top when ref.v is missing in this case:
  the pilot does so too. Thus golden TB arithmetic, rather than a simultaneous
  independent golden DUT comparison, supplies the oracle.
* Yosys 0.52 SAT checks a combinational assertion over all binary inputs, after
  `chformal -lower`. Actual `$assert` cells are counted in the emitted JSON design;
  zero properties cannot pass. Every successful nonzero proof is rerun against
  the same CRC output-bit mutant. Failure to falsify that mutant remains unknown,
  including constant assertions. This is an adequacy gate for this selected
  property, not a complete logical vacuity detector. This is a proof of one invariant, not full SVA equivalence,
  temporal induction, reset protocol validation or the VC Static methodology.
  Unsupported temporal properties are explicitly `unsupported`.
* VCS URG line/toggle/functional coverage is **null**, not zero or estimated.
  Explicit check counts and mutant kill results are supplementary adequacy measures.

The authoritative pilot is `results/revised`; `results/final` and `results/pilot`
are superseded audit records. `results/regression` contains focused response
replacement and infrastructure checks, not extra model samples.

| Status | Executed decision rule |
|---|---|
| pass | Completed command, exit 0, explicit functional evidence; formal additionally requires actual nonzero assertions and output-mutant falsification |
| fail | Candidate syntax/type diagnostics, observed mismatch/counterexample, or missing required test success evidence after completed execution |
| unknown | Wall/resource timeout, zero actual assertion cells, absent proof completion or failed adequacy/vacuity gate |
| unsupported | Actual response uses temporal SVA/assumptions beyond the declared combinational adapter |
| error | Missing executable/dependency, isolation/setup error, tool signal crash, unrecognized nonzero exit or unreadable proof design |

Candidate compilation diagnostics count as task failure because producing code
accepted by the declared supported backend is part of the task. A tool crash,
missing dependency or exhausted time budget is not evidence of wrong function.
All code subsets use the same command-state classifier; timeout/error leaves
functional_pass null. Fixture names are metadata only and never decide status.
`unknown`, `unsupported`, and `error` never count as passes. Report these counts separately; do not silently
exclude them and inflate pass rate. Published pass@5 requires independent samples
per task; five controls are not five model generations.

## Provenance and licensing

No AGENTS.md was present in workspace/official checkout. The full nine-page paper
was read using the browser PDF extraction, including references; direct local PDF
fetch returned HTTP 403 and was not retried. No paper PDF is redistributed.
No LICENSE/COPYING/NOTICE was found in the official commit. Public visibility is
not an open-source license grant. This package grants no upstream redistribution
rights; setup obtains sources directly. Generated build copies are excluded from
the delivery; manifests, locally authored fixtures and tool feedback remain.
Debian packages/tool binaries are not embedded. Their upstream licenses remain applicable.

## Isolation

Every external evaluation command has its own cwd, sanitized environment,
new process group, CPU/file limits, wall timeout, and seccomp denying socket,
connect, ptrace and mount-related syscalls. Network denial is tested. Timeout
kills the process group. Landlock ABI and bwrap user namespaces are unavailable
in this host; filesystem confidentiality/write confinement is not guaranteed.
This runner is for locally reviewed fixtures, not a safe service for untrusted code.


Full-code update: all 231 public code cases have adapter outcomes, including the
previously unattempted 227. See BATCH_EXECUTION.md for the 85 reference calibration
passes, 72 unknowns, 22 errors and 52 explicit contract refusals; these are not model
scores. The current all-482 execution matrix is results/final_coverage_selected.
