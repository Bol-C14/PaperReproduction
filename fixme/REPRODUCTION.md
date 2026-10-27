# FIXME structural reproduction

Branch: `reproduction/fixme-aaai2026` in `Bol-C14/PaperReproduction`. No push/PR.
Paper: [AAAI-26, DOI 10.1609/aaai.v40i2.37079](https://ojs.aaai.org/index.php/AAAI/article/view/37079/41041).
Official code: https://github.com/ChatDesignVerification/FIXME at
`e875437fbb11590b71775b32d3579726d702cfc6` (2026-08-12). Initial release is
`b19526770f101fed029b23e24523680bf5a7acfc` (2026-08-03); neither is assumed to be the paper's exact dataset.

## Run

On Linux x86_64, with Python 3, git, curl/HTTPS access, dpkg-deb, g++, make,
libreadline8, libffi8, libtcl8.6 and libseccomp2:

```sh
cd fixme
python3 benchmark/setup.py --root ../.cache/fixme
python3 benchmark/run.py --upstream ../.cache/fixme/upstream \
  --tools ../.cache/fixme/tools --output results/new-run
python3 benchmark/validate.py results/new-run
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
  `chformal -lower`. This is a proof of one invariant, not full SVA equivalence,
  temporal induction, reset protocol validation or the VC Static methodology.
  Unsupported temporal properties are explicitly `unsupported`.
* VCS URG line/toggle/functional coverage is **null**, not zero or estimated.
  Explicit check counts and mutant kill results are supplementary adequacy measures.

`pass` means this named evaluator contract passed. `fail` means an observed
counterexample/invalid output or adequacy violation. `unknown`, `unsupported`,
and `error` never count as passes. Report these counts separately; do not silently
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
