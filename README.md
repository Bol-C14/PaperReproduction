# PaperReproduction

This local branch contains Paper03's behavior reproduction and evidence audit for NVIDIA Trace2Skill (MLCAD 2026).

Start with [REPRODUCTION.md](papers/Paper03-Trace2Skill/REPRODUCTION.md), then [the evidence audit](papers/Paper03-Trace2Skill/EVIDENCE_AUDIT.md), [novelty/baseline comparison](papers/Paper03-Trace2Skill/BASELINE_COMPARISON.md), and [research opportunities](papers/Paper03-Trace2Skill/RESEARCH_OPPORTUNITIES.md).

Branch: `reproduction/trace2skill-mlcad2026`. Cached numbers and deterministic helper behavior were checked; no new live LLM/RTL rollouts were generated. This branch was prepared locally without pushing or publishing.

Follow-up: [Chat-only, credential-free canary preparation](papers/Paper03-Trace2Skill/PILOT_PREPARATION.md), 45 offline tests passed; no real model requests or verifier executions.

Latest: [verified Icarus and actual isolated RTL smoke readiness](papers/Paper03-Trace2Skill/READINESS_UPDATE.md). Four real RTL simulations, no model/API requests.
