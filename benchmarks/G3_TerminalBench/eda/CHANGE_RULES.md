# EDA task changes: reuse, regrade, rerun

This is a proposed EDA interpretation of the [continuous benchmark protocol](https://www.tbench.ai/news/continuous-benchmarks), not an EDA experiment or an upstream format implementation.

| Change | Required action | Reason/evidence required |
|---|---|---|
| RTL/netlist/problem input, prompt, legal-edit rule, SDC, library, corner, exposed tool or tool version | Rerun | Changes what the agent observes or can achieve |
| Agent CPU/memory/time limit, network/tool access, seed affecting the task environment | Rerun | Changes the optimization problem or action budget |
| New/removed circuits | Rerun new circuits; recompute dataset aggregate | Changed denominator; never reuse old aggregate without explicit mapping |
| Hidden simulation/equivalence bug; tolerance/parser correction; metric recomputation | Regrade saved artifacts | Only when all required artifacts are retained and agent-visible state did not change |
| Verifier fix that changes artifacts requested from the agent | Rerun | Old artifact snapshot is insufficient |
| Verifier-only OpenROAD/STA version change | Regrade with new metric namespace | Retain both metric versions; if tools were exposed to agent, rerun instead |
| Metadata, spelling outside instructions, documentation only | Reuse | Hash/diff establishes no semantic exposure or grading change |
| Moving dependency pin correction | Reuse only if equivalent effective dependency proved | If actual environment changed or unknown, rerun |
| Oracle implementation or flakiness fix | Recalibrate reference; reuse agent trials only if task/grade unchanged | Oracle success is not a model result |
| Uncertain impact or missing snapshots | Rerun | Do not invent a regrade from partial stdout |

Minimal package boundaries are specified in [package_contract.json](package_contract.json): one small public agent bundle, allowlisted artifacts, and an independently pinned private verifier. No universal scheduling platform is introduced.
