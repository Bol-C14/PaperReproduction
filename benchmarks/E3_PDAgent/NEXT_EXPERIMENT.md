# Next bounded experiment: saved strategy → placement → Gate A

Proposal only; **not_run**. No new model or backend call was made while preparing this plan. Use the same selected `bp_fe:1:1`, one candidate, original native strategy bytes (hash in the Planner milestone), task objective and original verifier. Do not rerun Planner or invent a reference layout.

## Original module boundary

Pinned [OpenLayout](https://github.com/fenggev56/OpenLayout/tree/65e440d943443b48f4adfc0de5ef3012634bcd6b): `macroflow/agents.py:298` consumes a strategy through `Specialists.place`; `macroflow/tools.py:390` implements original `submit_placement_plan`; `macroflow/orchestrator.py:908` supports injecting saved `initial_strategies`. Its published `config_macro_gpt.yaml` sets `vlm_place_coords: true`. Retain model-owned coordinates for every macro; do not substitute the alternate deterministic cluster-based path.

Before a live request, freeze the true eleven-macro indexed table, dimensions, core/legal bounds, cluster membership and pin-side facts from the pinned native database/source, with hashes. Existing state proves eleven unplaced macros, not a placement solution. #0 is BTB, #1–#8 icache data SRAM, #9 metadata and #10 tag; expose these true facts alongside the unchanged strategy containing the BTB classification error. Preserve exact index/name mapping to prevent plausible coordinates being applied to the wrong block. This expanded Placer fact packet has not yet been frozen or externally reviewed.

Input: native strategy string, original `planner_context()` facts and initial image. Placer emits indexed `(x,y,orient)` lines through `submit_placement_plan`. The original preview rejects missing coverage; `place_plan` parses, applies overrides, validates, legalizes with gap2 and executes native placement. Keep raw model coordinates, parser output, legalized coordinates and all clamp/repair deltas separately. Original legalizer repairs are part of the mechanism, not evidence that the model produced a legal layout unaided.

Output: placed macro DB/DEF/image, tool result and original Gate-A Checker structured verdict. Checker receives the actual macro/pin-side visualization, strategy and geometric facts. A PASS string or fallback parse is not sufficient. Original Gate-A limit may set `continue_after_limit`; retain the failed quality verdict and do not label that a pass. For this smallest pilot, stop on failed geometry or Checker instead of running an unverified backend; disclose this stop as a bounded protocol deviation.

## Verification and limits

Require exactly all eleven expected macro instances, finite legal coordinates/orientations, inside-core footprints, no overlaps at the configured gap and valid placement statuses. Independently reopen the saved OpenROAD DB and confirm instance/net/macro counts, coordinates, orientation and geometry against the tool result. Confirm planned C opening, central region, cluster/pin-side and IO access claims against design facts; record failures rather than silently repairing the strategy text. Schema-valid submission alone is not correctness. Keep failed proposals/timeouts in the selected-case record.

Use only trusted original tool implementations in a fresh credential-free, network-disabled container with task-only mounts, read-only inputs and a separate bounded output directory. No arbitrary model code, home, hidden answers or reference solution mounts. APRIL CPU bound four cores, memory8GiB; proposed macro placement/readback timeout300 seconds each. Template `set_thread_count 32` commands require a documented resource override or hard affinity bound; do not claim unchanged templates request four threads.

## Current read-only feasibility evidence

APRIL has the pinned selected `bp_fe` netlist, SDC, DEF, standard-cell/macro LEFs and Liberty files; the initialized DB hash is `c8da180431a9d8d45de00724f98581860ff65cedd02abccfa55ff898c9d7a345` (18,473,879 bytes). Prior fresh readback found33199 instances,39512 nets,11 macros, all unplaced at origin. Existing OpenROAD image `080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac`, version26Q2-1164-g08f67ee5ec, is available. These are asset-presence and initialization checks; no new placed/routed DB exists. APRIL checkout is an export; selected module byte hashes matched the pinned local source, rather than claiming a remote Git revision from an absent .git directory.

The host Python3.9 environment has Pillow10.0.1, PyYAML5.4.1 and pexpect4.8.0; original OpenAI SDK is absent. A minimal native-role adapter to the already tested central client must be reviewed, fake-tested and financially registered before live use. No new platform or dependency installation is proposed.

## Budget and release requirements

Propose the smallest two-response path: at most one Placer submission request and one Gate-A Checker request, each at most2048 total output tokens,4096 aggregate; maximum four native callbacks, no repair sweep. This is a new bounded model/protocol pilot, below original per-role turn limits. Exact native read/view behavior must be supported; stop on unreviewed image or envelope rather than omit it. Original tool definitions, rendered prompts, actual image bytes and source/licence notices must be frozen before dispatch.

Provisional additional actual-cost ceiling **USD3.00**, within the existing shared USD10, with a refreshed full-context quote and central admission check before each call. Last reconciled global actual USD0.10593113; nominal remaining USD9.89406887 is not an authorization to ignore existing allocations. Conservative prior full-context reservation was USD2.80; the second call is admissible under this proposal only if its fresh reservation fits the remaining USD3.00 stage cap. Fewer than two calls may be affordable or sufficient; stop rather than overrun. Do not reuse exhausted/retired Planner batches or reset family counters. Central owner must allocate a separate reviewed stage and reconcile outstanding commitments.

No live release is requested in this document. The new placed/pin-highlight image differs from the previously approved initial image and needs exact payload/provenance review before external processing. Preserve GPL source/notice obligations and the existing narrow modified-DEF mapping caveat; do not transmit raw netlist/PDK or claim broad library redistribution permission.

## Subsequent full backend boundary

Only after successful placement/Gate A, propose original detail placement → CTS/route in the same native session with the required libraries/corners/clock/RC setup. Never copy the unplaced init DB into a macro-placed checkpoint slot. Existing `detail_place.tcl`, `cts_route.tcl` and the light-route source need final exact runtime closure. Published light mode omits repair_design/repair_timing and uses five detailed-route iterations: it cannot establish timing closure merely by exiting successfully. Full timing mode is a separately disclosed configuration change. Proposed initial backend aggregate wall cap1500 seconds, four cores/8GiB, no GPU/cloud; record timeout/resource_blocked and request a concrete extension if necessary. This runtime bound is not yet tested.

Finally reopen artifacts and measure native constraints: timing goal WNS≥0 and DRC-clean under the selected task, with explicit STA/DRC report provenance and unresolved failures. CTS/routing completion, placement legality, timing, DRC and LVS are separate checks. LVS remains outside established open-tool coverage; never infer signoff from routing or keyword parser success. Full original workflow, optimizer/repair loops and multi-candidate performance remain not_run until actually exercised.
