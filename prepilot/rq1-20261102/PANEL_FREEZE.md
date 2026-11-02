# RQ1 first-state panel freeze — before execution

2026-11-02. Input remains original VexRiscv checkpoint hash 8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149. One state only; no candidate-generation claim.

Original preservation: read/report only (contract/original). Serialization: write/reopen/report without implementation (contract/serialized). No-edit implementation rerun: fresh original -> route_design (noop_1). These are distinct controls.

Frozen serial order: noop_1, default_1, explore_1, aggressive_1. Each fresh process opens the same original. First is no physopt; others run `phys_opt_design -directive Default|Explore|AggressiveExplore`. **Every arm then runs the same `route_design`**, followed by identical timing/route/DRC/netlist/constraint export and checkpoint output. Directives select vendor-internal strategies, whose number of passes and actual runtime can differ; they are action definitions, not equal-compute operations. Time-to-outcome and timeout censoring are recorded. The equal limit is an opportunity budget, not a claim of equal consumed compute. Report action time and completion time separately.

Two threads; each process hard timeout 600s plus 10s termination grace; cumulative tool-wall limit 2700s, including contract audit (42s). At most four planned arms; no LLM, paid resource or concurrent arm. No tool seed set because no verified supported seed-control option has been established; determinism is not assumed. The order is frozen, not selected from outcomes. Random selector trials are not yet run; full-panel-derived expectation is not an online policy result.

Conservative functional gate: compare the entire exported functional Verilog against original, dropping only generated Date and Command whole-line comments; compare exported XDC dropping only generated Command comment. Identical exported representation is stronger evidence for the no-change class than cell counts or routing success. It remains conditional on the vendor export/primitive model and is not an independent formal proof or evidence of absolute design correctness. Nonidentical exports are **unconfirmed**, not automatically functionally incorrect; stop further arms and investigate the checker. No state-changing arm is scored as validated merely because of a tool PASS or completed routing.

Timing comparison is limited to the unchanged OOC `clk_fpl26contest` contract, 1.570ns period, and reported constrained endpoints. Missing I/O delays (115/136 ports), missing HD.CLK_SRC, OOC-incomplete DRC coverage and original DCP integrity warning remain explicit. Do not add constraints, infer interface signoff or treat tool ability to reopen as authentication of source integrity. No absolute Fmax claim.

If all four gates permit interpretation, independently confirm the strongest contrast before using its estimated gain. If gate stops, return instrumentation/contract findings rather than expanding models or replacing candidates opportunistically.
