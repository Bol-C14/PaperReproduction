# P07 bounded evaluator-contract pilot: completed

**The released evaluator mechanism ran successfully on all eight frozen synthetic controls.** Original and faithful-port outcomes agreed 8/8; all eight predeclared predictions matched. There were no oracle unknowns, experiment timeouts, fixture replacements or failed experiment attempts. This verifies a small CPU evaluation path, not dataset-wide label quality, teacher generation, model quality, training results or the paper's reported scores.

Protocol freeze: `66887c2` at 2026-10-28T10:40:24Z; execution command commit `725cc1a` at 10:42:05Z. Main experiment started 10:46:52Z and its runner completed 10:46:57.683212Z. Frozen inputs/harness hashes remained intact. Full machine results are in [results.json](runs/attempt1/results.json), with [metrics](runs/attempt1/metrics.json), [attempt ledger](runs/attempt1/attempts.json) and complete command/stream files below each case directory.

## Results by reviewed contract

| Frozen control | Original, 50 SAT steps | Faithful port, 50 steps | Independent oracle | Interpretation |
|---|---|---|---|---|
| comb_demorgan | pass | pass | equivalent, all 4 inputs | Expected equivalent control |
| comb_mismatch | fail | fail | non-equivalent; input index 1, outputs 0/1 | Expected counterexample |
| seq_modular | pass | pass | equivalent from zero; complete 16-state orbit | +1 and -15 agree modulo 16 |
| seq_increment | fail | fail | non-equivalent at rising edge 1, outputs 1/2 | Expected early sequential counterexample |
| delayed_pulse | **pass** | **pass** | **non-equivalent at rising edge 60**, outputs 1/0; complete 256-state orbit | Bounded pass does not establish eventual equivalence |
| empty_discovery | **pass, zero checks** | **pass, zero checks** | invalid candidate; golden compile rc=0, candidate rc=2 | Confirmed reachable empty-discovery success defect |
| helper_inline | **fail, module codes [1,0]** | **fail, module codes [1,0]** | top-level equivalent, all 4 inputs | Per-module naming contract is stricter than top-level behavioral agreement |
| syntax_error | fail | fail | invalid candidate; golden rc=0, candidate rc=2 | Ordinary syntax errors fail when a module is discovered |

The independent oracle uses Icarus Verilog plus independently specified Boolean/modular equations. Six valid-pair simulations agree exactly with their independent models; sequential simulations cover initial state and 260 edges. Exhaustive deterministic joint-state orbit traversal establishes the reviewed zero-initialized, single-clock contract for these tiny input-free sequential machines. No claim is made for arbitrary initial state or general RTL.

## Exact semantics recovered

The unchanged original evaluator was executed from Git blob `74963ae51ca6360b5b5944b03c266f7f48309b06`, commit `f44c2af999de62bd27e90e73ce9cbd4f97fbe55c`. Its subprocess instrumentation changes logging only and delegates the original call arguments/timeouts. The port retains the upstream renamer and emits the same synthesis/memory passes, `clk2fflogic`, flattened per-module miter, `sat -seq 50 -verify -prove trigger 0 -show-all -show-inputs -show-outputs -set-init-zero`, using the same Yosys 0.41 binary. The direct port avoids the interactive shell but preserves formal assumptions and labels.

This is a bounded SAT check over the transformed design with otherwise unspecified state set to zero. The clock-sampling state introduced by `clk2fflogic` has its own initialization in the SAT log; do not reinterpret the command as a 50-clock-cycle or unbounded theorem. Q and R are absent from the formal inputs and are not validated by these results.

The one-response-per-case original console output includes pass@5/pass@10 outside their valid sample count. Those numbers are deliberately excluded from all reported metrics. The pilot reports case outcomes only.

## Novel diagnostics, separately identified

1. **Horizon only:** for delayed_pulse, the frozen diagnostic increases `-seq 50` to `-seq 160` while preserving preprocessing and initialization. It fails with a SAT model, rc=1. This is an altered contract, not part of original reproduction accuracy.
2. **Nonempty guard:** the port additionally reports `guarded_status=invalid` for empty discovery while retaining the raw original `status=pass`. The upstream source is not patched.
3. **Logging repair:** the initial direct-port failure log ended mid-line because Yosys did not flush stdout on fatal `-verify` exit. [Amendment 1](AMENDMENT_1_LOGGING.md), committed as `e70f6cc` at 10:48:36Z, preauthorized exactly one logging-only replay of the same 160-step script using the original evaluator's `stdbuf -o0` wrapper. It reproduced rc=1 and retained the full witness. At SAT frame 160 in that returned witness, golden count=60, golden output=1, candidate output=0 and trigger=1. This is not a claim of a shortest SAT trace. The independent simulation's first divergent rising edge remains 60. Both the first partial log and [supplemental full log](runs/supplemental_logging/yosys.stdout.log) are preserved. No horizon tuning occurred.

## What is now verified, and what remains a hypothesis

- **Verified runtime defect on a synthetic control:** a legal no-port golden module yields an empty discovered-module list, causing the evaluator to report success for syntactically invalid candidate text. The negative control with a recognizable port-list module fails as expected. A nonempty-discovery guard is therefore necessary for a robust general evaluator.
- **Verified scope limitation:** a delayed sequential mismatch passes the original bound and fails the longer bound. This is expected bounded-check behavior, but success must be named and interpreted accordingly.
- **Verified contract restriction:** omitting a behaviorally redundant helper causes failure even when the top-level truth table matches. This reflects the documented per-module requirement; it is not evidence of a SAT solver error.
- **Not tested:** frequency or severity of these patterns in released data; question/reasoning fidelity; the current MetRex schema adapter; training ablation confounds; teacher API availability; model licenses or full checkpoint coverage. The earlier asset audit's concerns about these remain hypotheses or provenance gaps.

## Resource result and next-phase boundary

Main runner wall time: **2.718 s**; experiment container CPU time: **2.834 s**; container peak memory: **47,390,720 bytes (45.20 MiB)**. Supplemental formal call: **0.372 s**, container CPU **0.422 s**, peak **42,885,120 bytes (40.90 MiB)**. See [setup/resource ledger](SETUP_AND_RESOURCES.md). Source compilation took 485.0 seconds in the successful build step; its peak memory and total CPU time were not measured.

There were 17 formal invocations in the main experiment (8 original nested calls, 8 faithful-port calls and 1 novel horizon call), plus 1 separately recorded logging replay: **18 formal invocations total**. All nonzero outcomes are retained and expected by the frozen controls; none was dropped as an infrastructure failure. There were 16 independent oracle compile/simulation invocations and 8 original driver processes. No experiment timeouts occurred. Setup had four failed build invocations before one successful build; these are retained separately.

**No additional user resource is needed for this completed pilot.** A next CPU dataset-label sample could use the now-provisioned toolchain, but was not executed. Full teacher regeneration or paper-sized SFT remains a separate high-cost scope: the audited full SFT route reports 8×A100 resources and the current environment has no established GPU. This work stops here for the parent's next-phase decision.

Local branch: `reproduction/verithoughts-neurips2025` in the existing Bol-C14/PaperReproduction repository. It was initialized from the existing unborn local history because the remote has no main and its five branches contain separate paper projects. No other branch was checked out or modified; no external push, PR, installation on the host, credential access or security-setting change occurred.
