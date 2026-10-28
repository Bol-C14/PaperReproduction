# OpenRouter candidate and pilot-cost review — no model calls

Checked 2026-10-28 using only unauthenticated GETs to the official model catalog,
per-model endpoint catalogs, model pages and routing/reasoning documentation.
No key/configuration/secret file was opened, copied or changed; no model was
invoked, provider configured or money spent. The shared loader remains owned by
the shared environment thread. This report does not authorize transmission.

## Candidate choice and cost arithmetic

Prefer fixed model ID `google/gemini-2.5-flash` for the first pilot: it matches the
paper model's named family rather than introducing another model immediately.
The catalog supports text/JSON output controls, temperature, top_p and max_tokens,
with 1,048,576 context tokens and sufficient output capacity. This is interface
eligibility, not evidence that its SPICE reasoning/JSON decisions work. Both
`google/gemini-2.5-flash-lite` and `anthropic/claude-sonnet-4.6` are explicit
substitution candidates, not automatic fallbacks. No live quality comparison has
been run. Fixed model IDs are preferable to auto routers; named IDs still do not
prove immutable weights. Record returned model/canonical/provider identities.

| Fixed candidate | Official standard input/output USD per million | 81,920 input + 7,168 generated tokens | Highest listed endpoint rates/cost in this snapshot |
|---|---:|---:|---:|
| Gemini 2.5 Flash | 0.30 / 2.50 | **0.042496 USD** | priority 0.54 / 4.50 =>0.0764928 USD |
| Gemini 2.5 Flash Lite | 0.10 / 0.40 | **0.0110592 USD** | priority 0.18 / 0.72 =>0.01990656 USD |
| Claude Sonnet 4.6 | 3.00 / 15.00 | **0.35328 USD** | regional 3.30 /16.50 =>0.388608 USD |

Formula: 81,920 x input per-token rate + 7,168 x completion per-token rate.
These already include up to ten application attempts (two per each of five
stages), not ten extra retries. No cache discount is assumed. No web search,
paid plugin, explicit cache-write mechanism, image/audio/file operation or other
chargeable feature is needed. Values describe token usage, not unrelated account
charges, funding fees or taxes. `CATALOG_COST_SNAPSHOT.json` saves selected factual
metadata, per-endpoint prices, source URLs and raw public-catalog hashes.

A **conditional conservative proposal** for the preferred standard route is
0.05 USD of pilot token usage: fix `google-ai-studio` standard endpoint, disable
fallbacks, require supported parameters, require prompt <=0.30/M and completion
<=2.50/M via the documented `provider.max_price`, and disable thinking or enforce
a cap including every billed reasoning token. No priority/flex auto-routing,
model fallback or billable tool is selected. For a price-only envelope across
all presently listed Flash endpoint variants, round 0.0764928 up to 0.08 USD,
under the same token/reasoning assumptions; this is not permission to use those
variants. The standard route is cheaper and avoids changing service tier.

**This is not yet an enforced hard-spend guarantee.** Current generic transport
cannot send provider pinning, max_price, explicit reasoning or response-format
controls and does not preserve full usage/cost/finish_reason metadata. The shared
integration must add and validate those controls without moving credentials into
the repository. Optional reasoning must be turned off explicitly for a simple
bounded pilot, or given a separately approved generated-token budget. Hiding
reasoning output does not stop billing; max_tokens covers reasoning plus visible
content on most providers, which is not enough to assume every route behaves the
same. A request cut off with empty content can still consume paid reasoning.

Flash Lite's official page states thinking is off by default; explicit verified
disablement is still preferable for a frozen protocol. For any replacement backend, verify
the selected endpoint accepts temperature=.4/top_p=.85 and freeze any parameter
substitution before use; a model-level parameter list is not a live compatibility
test. Gemini's
listed parameters do not include top_k, so the paper's top_k=20 is not preserved
by this transport. Same model name does not mean same full generation setup.

`qwen/qwen3-coder` was also inspected only in the public directory. Its two listed
endpoints returned nonzero status codes (-2 and -5); no healthy-route claim or
live test is made. It is therefore deferred instead of being substituted into
this pilot or fetched/loaded locally.

## Token-size and fair-runner caveats

Arithmetic of the existing five-stage caps is correct: 1,536+768+256+768+256 =
3,584 nominal output tokens; two attempts per stage gives 7,168. Ten input requests
at 8,192 chat tokens gives 81,920. Caps must apply to retry requests too. With
reasoning disabled/covered, the cost table does not need an increased token cap.

An offline **sizing-only** 22-row reflection projection from archived synthetic-
controller evidence is 15,328 serialized UTF-8 bytes, below the 24,576-byte cap.
It was never sent or saved as new fair-pilot measurements. Actual future model
understanding/domain prose and a schema-correction exchange are unknown; the
selected model's chat tokenizer including framing is still unavailable here.
Therefore exact input token fit is **not certified**, and this representative
byte count is not a worst-case token guarantee. Before each send, count full
messages including prior raw invalid responses against 8,192 tokens and the byte
cap. If too large, stop before sending; do not silently truncate observations or
raise the monetary/token cap. Revise/reapprove the protocol first if needed.

A separate static review found that old bridge request construction subtracts
`len(history)` from 24. In the fair protocol, ten observations are shared initial
data: at reflection, 22 total rows mean **12 fresh attempts remain**, whereas the
old builder would report 2. The old CLI is already excluded by the fair draft;
the future fair request builder must use a separate fresh-attempt count and new
backend labels/usage accounting. No old executable was modified or called here.

## Official sources

- [Official model catalog](https://openrouter.ai/api/v1/models)
- [Gemini 2.5 Flash model/price](https://openrouter.ai/google/gemini-2.5-flash)
- [Flash endpoint catalog](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash/endpoints)
- [Gemini Flash Lite model/price](https://openrouter.ai/google/gemini-2.5-flash-lite)
- [Claude Sonnet 4.6 model/price](https://openrouter.ai/anthropic/claude-sonnet-4.6)
- [Provider selection, parameter support, fallback and price controls](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Reasoning tokens and billing limits](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)

Next: wait for the shared private loader and parent approval of exact model,
provider, public payload, reasoning policy and monetary cap. No new model run or
credential provisioning is performed by this review.
