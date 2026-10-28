# Live controller boundary — prepared, never invoked

`scripts/llm_interface.py` creates JSON requests and validates response objects.
It imports no model SDK, reads no credentials, contacts no endpoint, and has no
heuristic/replay fallback. `invoke_live()` raises `LiveLLMUnavailable` before any
candidate simulation. This is a concrete unexecuted boundary, not an online LLM
result. The numerical experiments do not call it as a policy.

`scripts/controller_adapter.py` provides the concrete response-to-engine bridge:
it converts active/fixed maps, including noncontiguous subsets, into legal ordered
index tuples, excludes measured candidates, dispatches supported random/GP
proposals and contains the per-attempt simulation/debit path. Controller-driven
execution is disabled by the frozen permission flag before any simulation, while
pure conversion/proposal checks use explicitly synthetic software fixtures only.
Thus a future approved backend has a numerical connection ready; it still needs
the actual allowed live transport and model outputs, not a replay file.

Eight actual input packets are saved in `controller_requests/`, four stages for
each circuit. Circuit understanding uses the original source prompt, rendered by
literal string extraction without importing the source module. The other stages
use local transport instructions preserving the source decision structures and
explicitly describing the reduced supported numerical pool. Original prompt files
are preserved, byte-for-byte from the audited commit, in `upstream_reference/`.
The interface does not claim source-identical prompts for those adapted stages.

Every request carries stage, source commit, netlist/testbench, fixed parameters,
released discrete domains, width scaling, units, exact source constraints,
normalization and remaining attempt count. Inner/outer example packets contain the
first 12 **real numerical-baseline** observations and their actual outer feedback,
with 24 attempts remaining. Their origin is explicitly tagged. They contain no
LLM output, generated sensitivities, fabricated measurements or hidden state.
`understanding:null` means the prerequisite live CU response has not happened.

## Expected response objects

Circuit understanding retains the author's five top-level fields:
`circuit_topology_overview`, `optimization_variables_mapping`,
`optimization_variables_impact`, `variable_interactions`,
`key_insights_for_optimization`. Presence validation cannot establish correctness
of an LLM's physical reasoning; that remains an experiment, not a schema property.

Initial-space and outer-regeneration response:

```json
{
  "optimization_configuration": {
    "variables_to_optimize": {
      "W_pmos_base": {"search_space": [0.84, 1.05, 1.26]}
    },
    "variables_fixed": {
      "W_nmos_base": {"fixed_value": 1.68}
    }
  },
  "search_space_summary": {},
  "reasoning": "MODEL-OUTPUT PLACEHOLDER; NOT AN OBSERVED DECISION"
}
```

This is a schema illustration, never used as a search decision. Validate complete,
disjoint variable coverage, nonempty unique allowed values and fixed values inside
the released grid. Derive the number of combinations in code rather than trusting
an asserted count. No new device model, value range or target is silently accepted.

Inner decision response:

```json
{
  "action": "search",
  "method": "bayesian",
  "n_samples": 4,
  "parameters": {},
  "reasoning": "MODEL-OUTPUT PLACEHOLDER; NOT AN OBSERVED DECISION"
}
```

Supported methods for this adapter are `random` and the documented GP-UCB port
named `bayesian`; unsupported source-pool algorithms must raise, not silently
fall back. Parameters must be an empty object: fixed kernel/UCB settings are part
of this numerical port, and unsupported overrides are rejected rather than ignored.
Adaptive numerical hyperparameter orchestration is therefore not a tested or
supported mechanism in this adapter. `n_samples` must be a true integer, positive and no larger than remaining
attempts. `stop` is a distinct action. Batch execution would debit each actual
attempt, including failures; fixed-budget experimental arms never use model stop.
The one-sample/sequential adapter and strict remaining-budget validation differ
from the author's looser batch handling and are explicit accounting port choices.

The requested future model settings match the paper: Gemini-2.5-Flash, T=0.4,
top-p=0.85, top-k=20, max output 8192. This metadata establishes no access, quota,
current endpoint availability or permission to send. No local weights/runtime are
among the inspected authorized assets, and external LLM calls are prohibited in
this tranche. The parent must decide a future allowed model/backend experiment;
no user credential or paid-resource request is made here.
