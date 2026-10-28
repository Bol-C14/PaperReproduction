# Mechanism coverage map

Sources: [final paper](https://proceedings.mlr.press/v306/yu26aw.html), its locally
audited PDF; author source at `1b9b8f6498e2c7ad3b650bbbc78c8e3b0e1205e1`.
No new repository instructions were found in workspace ancestors, `.agents` or
tracked AGENTS.md/SKILL.md paths. This work remains in the existing paper branch.

| Paper component | Evidence / interface | Feasible work in this tranche | Fidelity |
|---|---|---|---|
| Circuit and spec input (§3.1) | Released YAML netlist, loads, constraints and width grid | Execute two real SKY130 tasks | Original templates in documented PDK-subset port |
| Circuit understanding (§3.3) | `CIRCUIT_UNDERSTANDING_PROMPT`, original JSON fields | Render exact input and validate response contract | Live semantic output blocked; no invented analysis |
| Initial variable/range decisions (§3.4) | `optimization_configuration`, active and fixed variables | Contract/domain validation; fixed central initialization for controls | New baseline prior, not LLM-selected ranges |
| Numerical inner loop (§3.5) | Author LHS/GP/etc algorithm pool and simulator history | Sequential random and GP-UCB, true SPICE feedback and history updates | Faithful numerical-form port; not exact author optimizer |
| Measurement/spec evaluation (§3.1,3.6) | Generic ngspice runner and normalized FoM | Individual constraints, failure taxonomy, independent vector checks | Source OTA measurements; explicit inverter power repair |
| Outer reflective update (§3.5,3.6) | Boundary/feasibility/stagnation feedback | Real numerical trust-region-like range update and frozen control | New heuristic baseline; no LLM reflection claim |
| Variable reprioritization/fixing | Source schema for active/fixed variables | Validate complete/disjoint decisions; no actual fixing in baseline | Interface prepared, semantic decisions untested |
| Algorithm orchestration | `{action,method,n_samples,parameters,reasoning}` | Supported random/GP interface and budget clipping/validation | Live LLM decision unavailable; baseline engines fixed |
| Budget and history | Paper uses 300 samples and 3 outer cycles | 36-attempt matched arms, full failed-attempt debit and persistent history | Smaller protocol; history retained across outer updates |
| Layout/PEX | Optional source flow; incomplete wrapper dependency | Deferred | Not needed for these nominal pre-layout tasks |
| Full benchmark/comparators | 24 tasks; author-standardized baselines | Two tasks, 3 seeds, explicit new controls | No paper-level success or superiority claim |

The affordable end-to-end closure is candidate → actual simulator → parsed metrics
→ exact source constraints → normalized FoM/history → GP model/acquisition update
→ candidate, plus an explicit numerical outer range-feedback loop. The essential
unclosed mechanism is live LLM-generated circuit understanding and decisions.
External LLM calls are prohibited in this tranche and no approved local model
weights/runtime are among the existing assets. That restriction cannot be repaired
by renaming a heuristic or returning hand-authored/replayed responses.
