# PDAgent-Bench v7: bounded release and evaluator review

Audit date: 2026-10-28 UTC. This is a release audit and offline calibration, not a reproduced model leaderboard. No paid model calls occurred. Original paper protocol, current-release behavior and new diagnostic experiments are kept separate below.

## Identity and contribution

Paper: [arXiv:2606.17253v7](https://arxiv.org/html/2606.17253v7), submitted 2026-10-13. Type: benchmark/resource plus multi-agent workflow and empirical evaluation. Contribution: combines physical-design knowledge, report interpretation, diagnosis, command generation and long-horizon tool-mediated flow evaluation. Venue: unverified; arXiv metadata inspected does not establish acceptance. CCF: unknown; no venue ranking inferred from the subject or authors.

Official leaderboard commit: `53948a6cc6848e5d29811cf7d2361e59d100d5c7`. Public dataset revision: `794fbb0c3fdf8613ac7384dd5262d67f902986ee`. Dataset-linked [OpenLayout](https://github.com/fenggev56/OpenLayout) commit: `65e440d943443b48f4adfc0de5ef3012634bcd6b`. OpenLayout is a separately versioned current open implementation, not proof that the paper's commercial framework is completely released.

## Counts reconciled without inventing task IDs

| Scope | Count | Actual identity evidence |
|---|---:|---|
| Understanding | 133 | Q1–Q90, RC1–RC21, RPT1–RPT11, TC_01–TC_11; locally parsed JSON |
| Commercial script generation | 210 | FM22 + ECO10 + ICC2/Vendor1 88 + Innovus/Vendor2 90; aggregate categories only, item IDs not released in inspected open subset |
| Leaderboard | 343 | 133 + 210; eight categories |
| Original paper full flow | 10 | TinyRISCV, Open910, Systolic array, 16b pipelined multiplier, AES-256, NVDLA-small, NVDLA-large, UART controller, Elevator FSM, Ethernet MAC |
| Paper total | 353 | 343 + original ten flows |
| Current open release | 133 QA + 16 flow | Eight PlaceReasoner designs × aspect 1:1/2:1; not the original ten commercial-flow designs |

The eight current designs are ariane133, ariane81, bp_be, bp_fe, ethernet, swerv_wrapper, VeriGPU and vga_lcd. The two DEF filenames identify aspect variants. `logs/task_ids.json` contains every available QA ID. `logs/dataset_inventory.json` contains flow file paths and upstream object IDs. Foundational JSON has 81 top-level rows: 80 single wrappers plus a final ten-item plural wrapper, giving 90 questions. No HF viewer row count was used. Report files are PDFs; RPT8–RPT10 share one PDF. Metadata coverage of an ID is not execution of that task.

## Mechanisms and protocol boundaries

The paper evaluates static understanding/command tasks through stateless answers; this differs from its planner/worker/analyzer/debugger/optimizer flow, with reusable procedural skills, checkpoint rollback and bounded refinement. Paper Appendix A.6 explicitly includes direct execution of reference Tcl among worker modes. The current OpenLayout Worker likewise renders proven templates without an LLM. Consequently reference replay is calibration, and an advantage over RAG can include substantial procedural/template exposure. Skill contents, available scripts and human instructions must be frozen for each baseline before attributing improvements to model reasoning. No evaluated agent was run here, and reference materials stayed outside any prospective evaluated-agent workspace.

The claim of broad coverage overlaps with existing pieces: ChiPBench evaluates placement with downstream PPA; ChatEDA and iScript evaluate tool scripting; VerilogEval addresses RTL generation. The paper's plausible added value is the combined backend diagnostic suite and reusable multi-stage agent workflow. Its own comparison table already marks RTL-to-GDS coverage for ChiPBench and ChatEDA, so an unqualified claim to invent end-to-end EDA evaluation would exceed that evidence. This is a scope comparison from the paper's cited descriptions, not an independent re-evaluation of all prior benchmarks.

| Protocol | Paper v7 | Current leaderboard/rebuild code |
|---|---|---|
| Free-response judge | Claude Sonnet 4.6; three senior engineers for calibration | R2 blind GPT-5.4-mini; cross-round judge difference disclosed |
| pass@5, judged QA | Best rubric score among five, §4.1 | `mean_of_5` / 10, with separate `p5_best` field; README says mean |
| Sampling | pass@1 temperature0; pass@5 .8/top-p .95; proprietary defaults when unsupported | R2 medium reasoning, no temperature, 32K cap |
| Aggregate | Mixed rubric/rule scores | Unweighted category mean; text-only models have six categories |

Thus R1/R2 judged columns and the label pass@5 are not directly interchangeable. `scripts/build_data.py` references local later-evaluation summaries and an untracked config; it is a leaderboard builder, not a released QA execution/checker harness. Full commercial script checker alternatives cannot be tested without missing inputs and checker code. The dataset states `exact_match`, `match`, `any_match` for STA, but does not supply the executable normalization/verification implementation.

## Internal claim checks and release drift

The current leaderboard attributes its16-task PlaceReasoner CSV to paper Tables6/7 and names a Claude Opus4.8 agent. In pinned v7, Tables6/7 instead contain script-error breakdown/flag hallucination examples; its macro experiment is the five-design8B-VLM comparison in Table12. These are distinct evidence sets. A later public result may be useful, but it must not be labeled a replay of v7 merely because it shares the project name.

Several narrative summaries need narrower readings. The92% syntax-near-miss figure is supported by48/52 GPT-5.5 Innovus failures in Table6; it does not by itself establish the same rate across every model/tool. The statement that report comprehension is near9/10 conflicts with the aggregate Table4 maximum of.746, while the purported roughly5/10 root-cause category reaches.762. The text calls Opus4.7 best on foundational knowledge at82.4%, but Table4 has Sonnet4.6 at82.6%. The claimed2–6-point human/judge tracking has at least one9.9-point case (GPT-5-mini foundational80.0 versus70.1). Small aggregate gaps do not establish per-item judge reliability without agreement/variance statistics. These discrepancies affect claim calibration; they are not results of our own model experiments.

## Actual calibration evidence

`logs/evaluator_controls.json` executes unmodified current OpenLayout metric parser, error extractor, goal check and score functions. Empty/PASS-only logs fail goal checking. Later keyword-matching values override earlier bad values; keyword-only forged metrics and fatal-plus-good-metrics inputs pass the isolated goal function. An existing malformed DRC report is counted as zero, whereas an absent report returns null. Missing hold slack is accepted if setup/DRC are present, and empty metric vectors receive ideal ranking components although the separate goal check fails.

These are parser/function-level findings. They do **not** establish full-flow false acceptance: process return code, checkpoint checks, debugger behavior and other gates can reject runs. The custom native artifact verifier is intentionally stronger than checking a PASS marker and is not claimed to be an upstream evaluator fix. No upstream code was edited.

`logs/qa_schema_controls.json` is a novel sensitivity probe of hypothetical literal/substring implementations, not a reverse-engineered or executed official checker. It shows why valid paraphrases/full option text and negated keyword-bearing answers need calibrated checker semantics. Official STA grades remain null. RPT1/RPT2 were rendered and visually inspected; references/rubrics were audited without an LLM judge. RPT2's screenshot supports the displacement observations but does not independently measure the density explanation demanded by its rubric.

## Signoff and scientific limitations

Paper §4.4 explicitly excludes LVS despite broader introductory/table language about DRC/LVS. Routed (<1000 DRC), DRC-clean, timing closure and tapeout signoff are distinct. OpenLayout finish skills report STA/area/power/IR and export DEF/Verilog; this does not establish independent LVS or foundry signoff. Original full-flow table also contains residual DRC and negative slack cases. No full-route, LVS, macro-placement quality or live-agent conclusion is established by our initialization calibration.

Macro-placement results condition best-TNS comparisons on routed designs and a DRC threshold. Record excluded methods/tasks and failure reasons; do not average only successful circuits. Freeze downstream scripts, timing constraints, candidate count and feedback budget across methods. Human-instruction and skill ablations are necessary for causal attribution.

## Licenses and payload limits

Paper HTML declares CC BY4.0. The leaderboard checkout has no LICENSE file. HF declares `other` / mixed-open-source, with QA ownership description but no precise standalone QA grant. OpenLayout code declares GPL3. Its collateral includes Nangate45 and FakeRAM with separate terms; the inspected Nangate LIB header explicitly references a restrictive license agreement and trademarks. The dataset's blanket redistribution prose is insufficient to settle component terms. Do not copy QA answers, PDFs, LIB/LEF, netlists, upstream harness or container layers into the public reproduction payload. This package contains original audit scripts, aggregate evidence, task IDs/hashes and logs only. Redistribution needs component-specific review; no legal determination is asserted here.

## Full-workflow follow-up boundary

See WORKFLOW_FEASIBILITY.md. A fresh protected OpenROAD DB probe confirms all11 macros are unplaced at(0,0). The pinned releases have no reference candidate coordinates/placed DB. The advertised --no-llm outer mode still starts model-driven macroflow for this11-macro case. No arbitrary placement or model path was substituted. Full workflow remains not_run/resource_blocked pending a provenance-pinned valid reference placement (or separately approved live pilot); no routed artifact or post-route score exists.
