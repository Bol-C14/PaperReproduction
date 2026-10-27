You are analyzing rollout data from an LLM agent that solves Verilog/SystemVerilog chip design tasks in a Docker sandbox with tools: ls, cat, echo, iverilog (compile), vvp (simulate).

Below is structured rollout data from one generation of a genetic algorithm that evolves the agent's skill document (prompt). Your job is to produce a CONCISE behavioral analysis that will guide the next round of prompt mutations.

ROLLOUT DATA:
{rollout_data}

SCOREBOARD:
{scoreboard}

GENERATION STATS: best={best:.3f}, mean={mean:.3f}, worst={worst:.3f}, rollouts={total} ({n_pass} pass, {n_fail} fail)

Analyze the data and produce a report with EXACTLY these sections:

## SUCCESS MODES
For each reliably solved task, identify the 2-3 key behavioral patterns that lead to success. Be specific: which tools in what order, what the agent reads before writing, how it handles compilation errors.

## FAILURE MODES
For each failing/flaky task, identify the ROOT CAUSE of failure. Don't just say "compilation error" — say WHY the compilation fails (missing include file, wrong module interface, iverilog syntax limitation). Group by task and be specific about the error chain.

## CRITICAL INSIGHTS
List the 3-5 most actionable insights that distinguish passing from failing rollouts. Focus on behavioral differences that the skill document can influence. Examples:
- "Passing rollouts on task X always cat the testbench before writing, failing ones don't"
- "Task Y fails because the agent never creates the missing tbench.h include file"
- "10/32 successes pass WITHOUT compiling — agent just writes correct code and cocotb harness verifies it"

## DIRECTIVES FOR MUTATION
Specific, actionable instructions for how to modify the skill document:
- KEEP: What guidance must be preserved (cite which tasks it helps)
- ADD: What new guidance is needed (cite specific failure modes it would address)
- REMOVE: What guidance is counterproductive or wasting steps
- CHANGE: What existing guidance needs to be modified and how

Be concise. Every sentence must be grounded in the rollout data above. No generic advice.
