# CROP methodology port: bounded transfer smoke test

**Follow-up:** the larger [closed-loop study](closed_loop/README.md) now completes 272 measurements with iterative feedback, held-out circuits, and matched controls. This file preserves the earlier twelve-call milestone and its original evidence.

**Milestone completed: 12/12 real Yosys synthesis measurements and formal checks passed. Structural and random retrieval transferred the same configuration, giving equal results on every target. Semantic summarization/embedding and full CROP were NOT RUN.**

This directory contains an independently authored, CPU-only mechanism reconstruction. It is not official CROP code, RTLRewriter benchmark reproduction, an LLM search experiment, or the paper's industrial evaluation. Official CROP code availability remains unverified. The earlier [asset audit](../../P15_CROP/ASSET_AUDIT.md) and [asset manifest](../../P15_CROP/assets.json) remain separate historical deliverables.

## Method boundary and frozen plan

The paper's evaluated backend is RTL Architect. This port substitutes Yosys generic synthesis and removes semantic summarization, embeddings, and LLM proposal generation. It isolates the narrower question: can measured best configurations from a structurally retrieved prior design be transferred to another circuit, compared with a uniformly random prior? Reusing a history entry is the entire proposal policy here; iterative reasoning and target-history adaptation are outside this milestone.

Before measurement, `manifest.json` froze these choices:

- Three newly authored, inspectable combinational families: adder with carry-in, unsigned minimum via comparator/mux, and four-way mux. Each has an 8-bit prior and a 12-bit target. These are controlled educational fixtures, not downloaded paper assets. Their same-family, width-scaled relationship makes this a smoke test, not architecture-generalization evidence.
- One common legal configuration pool: `synth -top dut -noabc` and `synth -top dut -noabc -noalumacc`. Both use the same Yosys backend and generic gate model. No commercial option names were invented or translated.
- Six prior evaluations: every prior circuit under both configurations. Prior selection minimizes `(generic gate count, unit gate depth)` lexicographically, with configuration ID as a deterministic tie break. Real resulting measurements construct `history.json`; failures cannot be replaced with invented labels.
- Structural retrieval uses normalized counts of `+`, `<`, and `?` in the RTL expressions, after removing comments. It excludes family names, design IDs, role, and width. This is a deliberately simple structural proxy, not semantic or AST-based retrieval. It chooses maximum inner product with deterministic ID tie breaking.
- The random control draws one of the same three priors uniformly, using seed 7. Each arm receives one top configuration from its selected prior and exactly one target tool call. Both arms' proposals were fixed in `transfer_choices.json` before any target result was visible.
- Total cap: twelve synthesis/measurement invocations, including proof in each invocation. No adaptive rerun or additional target configuration sweep. Version/help calls were setup inspection, not synthesis measurements.

No model, embedding weights, paid service, GPU, gated design, PDK, OpenROAD, or external API was used for this milestone. No push or publication occurred. No Astro infrastructure was present or reused.

## Individual measured pairs

Area below means **generic primitive gate count**, with heterogeneous primitives counted equally. Delay means **maximum combinational unit gate depth**, independently cross-checked against Yosys `ltp`. These are transparent synthesis proxies, not physical area, nanoseconds, routed timing, power, or industrial PPA. Every row passed `check -assert` and a SAT proof of equivalence against its own original RTL for all binary input combinations.

| Phase/arm | Design | Retrieved prior | Configuration | (gate count, gate depth) |
| --- | --- | --- | --- | --- |
| history | adder, 8 bit | — | default | (52, 12) |
| history | adder, 8 bit | — | noalumacc | (70, 14) |
| history | compare/min, 8 bit | — | default | (51, 10) |
| history | compare/min, 8 bit | — | noalumacc | (51, 10) |
| history | mux, 8 bit | — | default | (24, 2) |
| history | mux, 8 bit | — | noalumacc | (24, 2) |
| structural | adder, 12 bit | adder | default | (81, 14) |
| random | adder, 12 bit | compare/min | default | (81, 14) |
| structural | compare/min, 12 bit | compare/min | default | (78, 12) |
| random | compare/min, 12 bit | adder | default | (78, 12) |
| structural | mux, 12 bit | mux | default | (36, 2) |
| random | mux, 12 bit | compare/min | default | (36, 2) |

The adder prior favored `default`; both other histories tied and selected `default` by the declared tie break. Thus retrieval selected different prior identities but **never changed the transferred configuration**. This study supplies no evidence of a retrieval advantage. Neither target optimum nor regret can be estimated: the unselected configuration was not measured on the targets. The six target calls deliberately include duplicate arm-specific evaluations to keep their actual measurement budgets equal.

The useful diagnosed gap is lack of diversity among prior-optimal configurations. A future study would need a justified common option pool and circuit set with genuinely different measured best settings before the retrieval-transfer question becomes informative. The current result is not a negative result about semantic CROP. No further sweep has been run.

## Resources, pins, and preserved evidence

The tool was installed locally because no native Yosys or OpenROAD executable was found. It is **Yosys 0.50, git sha1 b5170e139**, from the unofficial [YoWASP package](https://github.com/YoWASP/yosys), version `0.50.0.0.post858`. `requirements.lock` pins every installed Python dependency and wheel SHA-256; `install-report.json` records the resolved package origins and hashes. No global/system installation or security settings were changed. This is an explicitly identified packaging substitution for free Yosys, not a claim of using an official native binary.

The displayed wheel downloads totaled about 19 MB, well below 2 GB. Installed toolchain storage is about 66 MB, compiled WASM cache 60 MB, and measured-run outputs below 1 MB. Six historical evaluations took **1.040 seconds** in aggregate; six target evaluations took **0.991 seconds**. These subprocess times exclude package installation, first WASM compilation, source preparation, retrieval computation, and Python report work. The initial compilation was performed once during version inspection; its absolute setup time was not instrumented. No GPU was used or required.

`measurements.csv` gives each area/delay proxy pair, elapsed time, selected neighbor, and log path. `results.json` is the final per-invocation record; `measurements.jsonl` logs starts and finishes to preserve budget consumption even if a process fails. `runs/` retains scripts, mapped JSON netlists, raw tool logs, and result files. All twelve completed successfully; there are no failed measurement rows to hide. `source_hashes.json` pins the exact fixture bytes used, and `artifact_hashes.json` pins the driver, manifest, lockfile, and fixtures. JSON consistency and all twelve SAT success markers were checked without further tool evaluations.

SAT verification covers combinational binary behavior, not four-state Verilog equivalence, sequential logic, placement legality, or timing constraints. The proxy objective has no physical feasibility constraints. It therefore cannot substantiate any paper-level power, area, timing, or speedup claim.

## Run a fresh bounded copy

From a fresh directory containing `run.py`, `manifest.json`, `requirements.lock`, and `fixtures/`:

```sh
python -m pip install --target toolchain --require-hashes -r requirements.lock --no-compile
python run.py
```

The driver uses the workspace-local executable and cache. It refuses to run if a measurement ledger already exists, protecting this milestone's budget and evidence. Preserve this completed directory and use a separate fresh copy for any separately authorized future run. Do not delete its ledger to reset accounting. No further execution is needed to inspect the delivered results.

## Remaining boundaries

The semantic component was not run: no validated summary cache or semantic model invocation was used. This port does not establish that those assets are globally unavailable. A faithful semantic route still needs a declared summary/model/embedding setup; a full search route needs the actual history-aware proposal policy. Industrial evaluation additionally needs authorized RTL Architect, design, technology, constraints, and history assets. Those are outside this bounded CPU milestone. No high-cost resource request is necessary to inspect or rerun this small proxy study.
