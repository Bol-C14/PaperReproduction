# API pilot proposal — authorization still pending

No endpoint or model is selected, and no API request has been sent. The current
executable exposes only the labeled software fixture. `APIBridgeController` is a
deferred adapter, requiring explicit parent authorization, designated secure runtime
variables, a model-specific chat token counter including framing, and a fresh
evidence directory. The API run needs a new frozen protocol/output root; it cannot
reuse this non-API fixture protocol. No local LLM is needed.

Required model capabilities: text chat at an explicitly approved OpenAI-compatible
`/chat/completions` endpoint; return a single JSON object (fences accepted), follow
nested domain schemas, read a two-transistor SPICE netlist and DC/transient
measurement definitions, reason about interacting p/n widths, select active/fixed
released values and random/GP decisions, then revise domains using twelve actual
measurements. These capabilities are requirements, not observed results. No tool
calling, image input, code execution or provider-side file upload is needed.
The model must support at least 8,192 input chat tokens and the per-stage output
caps below; a model-specific local counter is required before sending. Exact backend
name, context window, pricing and any parameter incompatibility remain to be agreed.
OpenAI-compatible transport passes temperature=.4 and top_p=.85; no top_k field.
Any backend differing from paper Gemini 2.5 Flash is named as a substitution.

Nominal five requests, at most ten attempted requests including transport failures:

| Stage | Nominal calls | Output tokens/call |
|---|---:|---:|
| Circuit understanding | 1 | 1,536 |
| Initial domain | 1 | 768 |
| Inner decision, twice | 2 | 256 |
| Outer reflection after 12 new measurements | 1 | 768 |

At most one local JSON/schema/domain correction per stage; no automatic transport
retry, no heuristic/model-response replacement. Thus nominal maximum generated
content is 3,584 tokens; worst case 7,168 output tokens and 81,920 input chat tokens
(10 x 8,192), 89,088 combined. Each request also has a 24 KiB serialized-message
cap and 180 s timeout; ten timeouts could total 30 minutes of waiting. API spend cap
must be set after the parent chooses endpoint/model/pricing. Budget caps include
failed calls but do not yet claim provider billing or reasoning-token accounting;
a reasoning model with separately billed hidden tokens needs an explicit additional
budget before authorization. Simulation proposal: 24 controller candidates and
24 independent GP-control candidates plus separately charged preflight/validation.
One inverter and one seed establish integration only.

Only allowlisted public source context is sent: two-device topology, original
inverter DC/transient testbench with a public model-selector placeholder, fixed
parameters, legal widths/scaling, original strict targets, disclosed measurement
correction and GP port, earlier model understanding/domain, and up to 24 measured
rows from the new controller arm (twelve at reflection). Public feedback includes
indices/widths, measurement status, gain/delay/power, normalized objective, strict
feasibility/violation and boundary counts. Never send control-arm or old oracle
results, machine paths, raw runtime logs, account identity, credential/config
contents, unrelated files or private data.

Illustrative allowed content fragment (numbers are examples, not a measurement):

```json
{
  "stage": "outer_regeneration",
  "constraints": "fom > 1 AND dc_gain_db > 20 AND average_delay < 50 AND dynamic_power < 50",
  "width_mapping": {"W_pmos": "20*W_pmos_base", "W_nmos": "20*W_nmos_base"},
  "legal_base_widths": [0.84,1.05,1.26,1.47,1.68,1.89,2.1,2.31,2.52],
  "example_row_not_observed": {"indices":[4,4],"metrics":{"dc_gain_db":24.0,"average_delay":12.0,"dynamic_power":20.0}},
  "pdk_reference": "PUBLIC_SKY130_TT_SELECTOR"
}
```

The generated fixture request JSON contains the full actual public payload shape.
Synthetic circuit-understanding output in that request is labeled TEST FIXTURE;
it must never be used as a live model's understanding or claimed as API evidence.
