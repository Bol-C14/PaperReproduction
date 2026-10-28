# Prepared real-model pilot; execution still paused

The prior live entry-point denial remains in force. This revision has not run
`api_pilot.py`, imported a local LLM, or contacted any model endpoint. Offline
fake responses test interfaces only and are never model evidence.

## Service and explicit authorization requested

Only `POST <authorized base>/chat/completions` is needed, with Bearer credentials
supplied at runtime through `PAPER_LLM_API_KEY`, a parent-selected model, JSON
messages, `temperature: 0`, `max_tokens: 640`, and `stream: false`. A JSON-object
answer is requested in the prompt; provider `response_format` support is optional.
A successful response must have string `choices[0].message.content` and
`finish_reason: stop`. Record the model ID, usage and elapsed time. Provider
model revisions may not be immutable; record that limitation. Temperature zero
does not promise deterministic generations.

No external embedding endpoint is needed. Existing local MiniLM assets perform
384-dimensional semantic embedding on CPU, using the pinned revision in the
interface JSON. No local LLM loading, inference or service is allowed.

The endpoint/model must support ASCII byte-BPE input tokenization whose chat
framing and hidden input add at most 256 tokens. All visible request text is
ASCII (generated summaries are JSON-escaped); visible ASCII bytes plus 256 is
therefore a conservative upper bound, enforced before transport at 4096. The
parent must confirm this model/template property; the profile cannot run for an
unverified tokenizer/template. If it does not hold, supply a matching local
counter and revise the profile before authorization. `max_tokens` must cap all
billable output at 640, including any hidden reasoning. A service that bills
additional unbounded reasoning is incompatible with this budget.

Authorize the exact base URL, model and public transmission scope below. Then
supply runtime configuration and the existing `results/crop/API_AUTHORIZED.json`
record with fields listed in `ONLINE_MODEL_INTERFACE.json`. Do not commit that
record or credentials. Creating it is a parent action after authorization;
preparing this document does not create authorization or permit an entry-point
retry. Redirects are refused so an authorized request cannot silently move to a
different service.

## Public data scope and example

Only seven independently authored educational Verilog circuits from the existing
public branch are eligible: sumtree, multiply, alu, barrel, minmax, popcount and
held-out fir3. Exact files/source hashes are in `ONLINE_MODEL_INTERFACE.json`.
No private RTL, files from another project, runtime paths, `.env`, credentials,
user documents, or posthoc target-oracle rows enter model messages.

Example public input, copied from `closed_loop/circuits/multiply.v`:

```verilog
module dut(input [15:0] x, output [15:0] y);
assign y=x[7:0]*x[15:8];
endmodule
```

Module requests include one such RTL and six required summary field names.
Design requests include that generated module summary, ten required design
fields, and the explicit fact that there is one top module and no children.
Proposal requests include the generated FIR3 design summary, eight legal
`{mode,noalumacc}` options, the selected prior's top-three configuration IDs and
within-prior c0-normalized QoR ratios, the objective, seed 23, and at most three
preceding fresh target observations. An observation contains only configuration
ID, objective, status and invocation number. No raw cross-backend QoR is pooled.
The proposal response is exactly:

```json
{"configuration":{"mode":"quality","noalumacc":false}}
```

This is a schema example, not a generated or measured result. Duplicate options,
extra envelope keys, non-boolean flags, malformed JSON and invalid summaries
consume attempts and are rejected without a heuristic fallback.

## Budgets and sequencing

| Stage | Nominal requests | Maximum attempts |
| --- | ---: | ---: |
| One module summary per seven circuits | 7 | 14 |
| One design summary per seven circuits | 7 | 14 |
| Three sequential target proposals | 3 | 6 |
| Total | 17 | 34 |

Each input is capped at 4096 counted/bounded tokens; each completion at 640.
Normal-case token upper bound is 80,512, and maximum is 161,024 (139,264 input
plus 21,760 output). Input wire JSON is also capped at 12,000 bytes for summaries
and 18,000 for proposals. Request timeout is 180 seconds; 34 sequential timeouts
would consume at most 6120 seconds of request waiting, excluding local work.
Every attempt is reserved on disk before transport. An HTTP, redirect, transport,
truncation, counter or usage failure stops the run with evidence; it is not
retried. Only a completed but content/schema-invalid generation can use the
second allotted attempt. Provider usage remains the billing evidence; no dollar
budget is claimed before the service/model price is known.

Before the model pilot, a separate CPU-only preparation builds a matched bank:
6 prior circuits times 8 configurations = at most 48 synthesis attempts, each
with a 60-second synthesis and 30-second CEC timeout. Each successful row must
pass ABC CEC, 256 independent arithmetic/LUT vectors, and independent depth
agreement. Stop on the first failure and preserve the ledger/logs. Pin the same
ABC executable explicitly for Yosys mapping and CEC. Compare all 48 old/new
pairs to report backend drift, while retaining the original 272 historical
measurements unchanged. This preparation has zero target measurements and zero
API calls; it is neither a model search nor an online result.

The later authorized model pilot holds prior retrieval fixed and uses only that
native bank. Target budget is exactly c0 plus at most three distinct model
proposals: at most four fresh synthesis attempts, each with CEC and independent
checks. Fresh target history evolves after each accepted measurement. Historical
target and posthoc-oracle outcomes are never supplied to the model. Output
folders refuse overwrite; partial failures retain their attempts and logs.

## Evidence and scope of inference

Keep source SHA, model/embedding IDs, tool versions, CPU affinity, thread limits,
raw requests/completions, token usage/bounds, errors and failed attempts, every
EDA command, CEC logs, independent vector results and per-step history. The
preparation records native tool hashes already required by setup provenance;
the live driver checks that its prepared bank uses those same tool bytes and
manifest, preventing accidental cross-backend guidance.

This remains an educational reconstruction: seven tiny one-module circuits,
one held-out target, one seed, an API model substitute and Yosys/ABC LUT4
count-times-depth objective. It cannot establish the paper's RTL Architect PPA,
industrial benchmark performance, nontrivial hierarchical summarization or a
statistically supported model-quality advantage. No official CROP implementation
or original benchmark/license equivalence is claimed.
