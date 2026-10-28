# Current authorized fee envelope — supersedes the initial input estimate

This execution-safety revision leaves circuit, common data, random seeds, strict
measurements/objective, arm budgets and scientific context unchanged. It replaces
our optional 8,192/request and 81,920-total input estimate and .05 USD project
proposal. These are not paper-method requirements and a missing local tokenizer
must not prevent an otherwise bounded authorized pilot.

Google's official token documentation states that Gemini 2.5 has a separate
**1,048,576-token input budget**. OpenRouter's fixed Gemini 2.5 Flash model and
standard Google AI Studio endpoint catalog report that same input context length.
Thus reserving the entire accepted-model input capacity includes framing and is a
conservative prompt-fee bound, without estimating characters/4 or pretending to
have an exact tokenizer. An over-capacity request must be rejected by the fixed
model rather than silently shortened by us. Model/provider fallback and message
transforms are not enabled. Full serialized scientific messages have a new
explicit 24,576-byte application cap; no prompt/history truncation occurs.

At fixed standard provider price <=.30 USD/M input and <=2.50 USD/M generated,
per-stage reservation is 1,048,576*.30/1e6 + output_cap*2.50/1e6:

| Stage | Maximum output per attempt | USD reserved per attempt |
|---|---:|---:|
| Understanding | 1,536 | 0.3184128 |
| Initial domain | 768 | 0.3164928 |
| First decision | 256 | 0.3152128 |
| Outer reflection | 768 | 0.3164928 |
| Second decision | 256 | 0.3152128 |

Two attempts per stage => **10 requests, 10,485,760 reserved input tokens,
7,168 generated tokens, 3.163648 USD maximum token-fee reservation**. Each request is conservatively rounded to 0.32 USD, so ten reservations
are bounded by exactly 3.20 USD. This is not a prediction of actual cost, and not an
additional allowance outside the shared cumulative 10 USD API-stage budget. The
shared client atomically reserves each bound under global/project request counts
and four-slot concurrency. It refuses if other projects leave insufficient
uncommitted budget. A known lower actual fee replaces the reservation; an unknown
fee or transport failure conservatively retains its full reservation. All ten
unknown fees would still fit the project envelope. No counter resets or extra
clients are used. Native prompt/completion/reasoning counts, cost and provider
metadata are archived; zero cost/reasoning is never invented from missing fields.

Provider policy remains fixed standard Gemini Flash, explicit `service_tier=default`,
provider only/order `google-ai-studio`, no fallback, supported parameters required,
max_price .30/2.50 per million plus per-request surcharge 0, reasoning disabled,
no paid tool/plugin, JSON object response and bounded stage `max_tokens`. Explicit
nonzero reasoning or policy/usage exceeding the bound stops further calls for
reconciliation. Missing reasoning detail is archived as unknown while explicit
reasoning-off and bounded generated usage/cost still apply; a missing actual fee
retains its reservation. The provider's enforcement of request/model/price limits
is the external contract, not a local token-count assertion.

Official exact counting alternative is Google's `count_tokens`/`:countTokens`,
which requires Google's own API client/key. This task has an authorized shared
OpenRouter client, not a separate Google credential or bypass client. It is
unnecessary to obtain another key or add paid/external calls: OpenRouter returns
native usage directly in each response. We therefore use the context envelope
before the request and native usage after, rather than adding an unsupported
OpenRouter count endpoint or halting indefinitely for a local tokenizer.

The five-stage actual builder and each full correction variant are checked by
`review_sequence.py`; they are admitted by the cost envelope without losing any
context. Injected optional exact upper counters can tighten the reservation, but
are no longer mandatory. Simulation ledger accounting remains 10 shared +24+24
fresh search +3 preflight+2 validations =63 attempted launches; output caps and
model retry limits do not increase.

Sources checked 2026-10-28:
- [Google official input/output token budgets](https://ai.google.dev/gemini-api/docs/tokens)
- [OpenRouter fixed model endpoint catalog](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash/endpoints)
- [Native usage/cost accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
- [Provider price controls](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Explicit standard service tier](https://openrouter.ai/docs/guides/features/service-tiers)
