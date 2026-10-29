# Frozen bp_fe:1:1 full-workflow feasibility

Current status (2026-10-29): native Planner live_pilot completed; Placer/Checker/backend remain not_run. See [Planner milestone](pilot/PLANNER_MILESTONE.md). Historical proposal details below describe earlier stages, not additional executed results.

Follow-up audited 2026-10-28 after initialization closeout. **No end-to-end reference workflow has been executed or established.** Status: resource_blocked by missing replay collateral under the zero-model constraint, not by insufficient CPU/RAM. Initialization remains reference_calibration only. Selection, input DEF, 1.8 ns clock, 60% utilization, aspect1:1, downstream objectives/constraints and official checkers are unchanged.

## What is actually released

The pinned HF revision supplies bp_fe netlist, SDC, LEF/LIB, two floorplan DEFs and a cluster file. It does not supply macro candidate coordinates or a placed/routed reference checkpoint. The pinned OpenLayout tracked-file inventory likewise has no `coords.json`, ODB, DEF or GDS candidate artifacts. `logs/workflow_release_audit.json` lists the inspected files and hashes the relevant launcher function; this conclusion is scoped to those pinned releases, not every possible upstream source.

The official README advertises `run_openlayout.py --config configs/bp_fe.yaml --no-llm`, but source inspection shows that `use_llm=False` disables only the outer Debugger/Optimizer client. `Flow.run_macro_place()` does not check `self.llm`; with the default `macro_stage.enable:auto` and11 macros it still calls `_run_macroflow()`, which launches `run_flow.py`. `MacroFlowOrchestrator.setup()` builds the configured VLM when none is injected. The inner `config_macro_gpt.yaml` specifies OpenAI GPT-5.4 and defaults to five candidates. The outer `configs/bp_fe.yaml` has `macro_stage.candidates:3`; `_run_macroflow()` passes it as `--macro-candidates 3`, so the effective outer whole-flow configuration uses three candidates, overriding the inner default five. The proposed one-candidate pilot is a new bounded experiment and is not either configured performance protocol. The separately documented coding-agent route also requires a model to create/check/refine candidate placements, including visual gates; it is a live-agent experiment, not a reference replay.

We did not invoke either model path, inject fake model responses, disable macro placement, alter objective/repair parameters, or substitute RTL-MP/arbitrary coordinates. Injected fakes are documented as a testing mechanism and are not a benchmark reference solution. Copying the initialization DB into the macro-placed slot would also be invalid: downstream `detail_place.tcl` marks every macro FIRM before PDN, rather than solving an unplaced macro arrangement.

## Additional native validation of the actual artifact

A fresh network-disabled, read-only rootless OpenROAD process reopened the preserved reference DB without modifying it. It reported **11/11 macros unplaced (`NONE`), all at origin(0,0)**. The probe returned0 and wrote raw per-macro state evidence in `logs/macro_state.log`; command, DB hash and summary are in `logs/macro_state.json`. This is a direct database query, not inference from a PASS string. The same DB previously read back33,199 instances and39,512 nets. Its SHA256 is `c8da180431a9d8d45de00724f98581860ff65cedd02abccfa55ff898c9d7a345`.

| Artifact | Actual availability / validation |
|---|---|
| Initialization DB | APRIL `results/pdagent/native_affinity/reference/floorplan.odb`;18,473,879bytes; independently reopened |
| Reference macro placement | Not released in inspected snapshot; initialization contains no usable reference coordinates |
| Macro-placed DB | Not produced |
| Detailed-placement / CTS DB | Not produced |
| Routed DB / routed DEF | Not produced |
| Post-route timing / DRC reports | Not produced; no post-route scores inferred |
| LVS | Not run, also outside paper's implemented scope |

No database, collateral or reference answers are copied into the public audit payload. Raw DB remains in the isolated APRIL results path and private controller copy for independent review. Future candidate containers must not receive reference/evaluator directories or home/secret mounts.

## Strongest bounded next step

For an offline **reference** workflow, the missing dependency is a pinned valid bp_fe:1:1 macro candidate (all11 macro names, x/y/orientation, and halo if needed) or a matching post-macro-placement DB with provenance. Once that specific asset is available and reviewed, replay it through unchanged published detail-placement, CTS, route and timing-repair templates, then run the official Gate-B checks and independently reopen the routed DB/DEF. Record command defaults, setup/hold/WNS/TNS/DRC and completion, including failures. Use the existing isolated OpenROAD image, four threads and original per-tool timeout; stop on timeout rather than quietly enlarge it.

Alternatively, a parent-approved live pilot can use the documented coding-agent/model route with its original gates and declared candidate budget. That is a separate experiment requiring a frozen protocol and budget; it cannot be called reference calibration. The current no-model-API instruction remains in force. Missing valid reference placement is sufficient to block offline replay before debating full-route runtime; no extra installations, downloads or paid resources were used in this assessment.
