# Authorized CROP real-model pilot, frozen before execution

Parent relayed direct user authorization on2026-10-28: public CROP/AutoSizer
inputs may go to OpenRouter and its model providers; cumulative API-stage budget
is10USD, separate from the parent's Runpod budget. The shared connectivity check
already consumed1 of the44 first-phase requests. CROP therefore has **at most33
actual requests**, including failures/schema retries; AutoSizer's10 are separate.
This supersedes the earlier proposed34-CROP-call/0.25USD batch draft. No global
policy, key or quota is changed by this project.

Use the existing shared `load_config` and `Client`; never extract or copy the
key. Shared source lives outside this repository. The CROP adapter invokes that
same client's budgeted `_request` core so temperature0, JSON mode and
`reasoning.enabled=false` can be supplied; the thin public `chat` wrapper does
not expose these options. The core still enforces its live gate, authorized
project, four global slots,44 cumulative first-phase requests, per-project cap,
USD reservations and failed-attempt accounting. There is no alternate HTTP
client or fallback route. Legacy direct HTTP is now disabled.

Fixed model: `google/gemini-2.5-flash`, the parent-selected API substitute.
Fixed local encoder: `sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`,384 dimensions,L2 normalization,
256-token truncation. Verify the existing READY metadata; use only existing
assets with local-files-only/offline flags. Do not replace it with an embedding
API or another model. No local LLM is loaded or deployed.

## Scope and limits

- Seven previously declared public educational RTLs: six priors and FIR3.
- Genuine module summary then design summary for each, followed by local dense
  embeddings and fixed maximum-inner-product prior retrieval.
- Use the completed48-row matched native prior bank, not old Debian rows.
- One held-out FIR3 target, seed23, c0 plus at most3 untried LLM proposals.
- At most4 new target synthesis attempts, each ABC CEC plus256 independent
  vectors and independent LUT-depth agreement. Existing48 prior rows are reused.
- Nominal17 chat calls, maximum33 total. Each stage/proposal has at most2 content
  attempts. HTTP/transport/truncation failures stop; no automatic retry. Invalid
  schema/duplicate options remain charged and consume attempts. No heuristic
  replacement for model failure.
- Input is ASCII JSON/public text, with conservative visible bytes+256 framing
  estimate capped at4096. For Gemini this is an operational conservative
  estimate, not a claim that its tokenizer is OpenAI byte-BPE. Preserve/check
  actual provider token usage and stop if it exceeds4096.
- `max_tokens=640`, reasoning disabled requested, JSON-object response mode;
  record actual completion/reasoning tokens and any unfinished response. The
  maximum nominal input/output token estimate is156,288 at33x(4096+640).

No private paths, names, credentials, other projects, historical/posthoc target
oracle rows, tool commands or local configuration enter model messages. Prompt
payload examples and categories remain in `PILOT_PROTOCOL.md`; later retry
feedback contains only public schema/duplicate-option errors.

## Pricing reservation and shared accounting

Official model page checked2026-10-28:
https://openrouter.ai/google/gemini-2.5-flash
shows Standard input0.30USD/M and output2.50USD/M. Its listed Priority rates
0.54/4.50 are also below this project's deliberately conservative bounds:
**input1USD/M, output10USD/M, flat request fee0**. These are reservation ceilings,
not a claim that those higher prices are charged. Per-call reservation is
(4096x1+640x10)/1,000,000 = **0.010496USD**;33 calls reserve at most0.346368USD,
within the shared cumulative10USD ceiling. Unknown costs retain the reservation;
actual provider usage/cost and reasoning counts remain authoritative. Any cost
above the reservation blocks further shared calls pending reconciliation.

OpenRouter reasoning documentation:
https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
explains that reasoning is billable output and can consume a small max-token
budget. It is explicitly disabled in this pilot rather than silently increasing
request count/token caps. Retain actual reasoning-token metadata where reported;
absence is unavailable, not a fabricated zero.

The initial shared mock fixture failed because it omitted the newly added
request caps; the fixture was corrected, without changing the real shared
configuration. The final30-test mock integration passes against current shared
source and checks live/project gates, global/project request caps, real flock
slots, cumulative USD rejection, failed reservation retention, reservation
overspend blocking and metadata-only ledger. It never reads the real key file.

## Evidence and interpretation

Before calls, freeze source SHA, package/tool versions, model/encoder IDs,seed,
limits and pricing. Save all raw prompts/completions, response/model IDs,
provider usage/cost, reasoning counts, parsing failures and consumed attempts.
Preserve every EDA command/log/netlist/CEC result and each evolving target
history. Original runtime evidence stays outside Git; public exports normalize
private prefixes and undergo secret/context/license review before ordinary
push to the existing branch.

A successful run demonstrates this substituted semantic-retrieval/LLM-feedback
mechanism on tiny single-module workloads. It does not establish paper PPA,
industrial benchmark quality, multilevel hierarchy or a quality advantage.
Review matched controls after the pilot; do not compare new raw native target
metrics directly to the historical Debian experiment or invent an unrun control.
