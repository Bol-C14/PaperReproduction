# Fair builder fix and shared adapter preparation

No real API/SPICE call, private credential read or global configuration/authorization
change occurred. Existing frozen bridge code/protocol/results are unchanged.

## Fixed budget semantics

New reusable files: `fair_runtime.py` (serial persistent attempts, public scientific
request builder, injected CPU batch runner and input gates), `shared_controller.py`
(public shared-client adapter only), and explicit OpenRouter policy.
No live executable or direct HTTP/key-loader implementation is included.

Regression evidence: ten exact common observations plus twelve fresh attempted
launches produce `fresh_attempts_used=12`, `remaining_attempts=12`, and 22 public
history rows. Control budget remains 24. Reopening a ledger preserves all debits.
Common data are content-hash frozen and cannot diverge between arms. Missing
failure rows, unresolved process outcomes and changed common values stop execution.

Invalid/failed/timeout/launch-error/explicit-retry attempts remain debited before
execution; an uncertain evaluator exception leaves a charged pending record and
requires reconciliation before resume. Failed API/schema retry attempts debit
the API pool, not the SPICE pool; two per stage and ten total include failures.
No automatic retry, invented observation, refund or filler is used.

## Exact full-request checks

`review_sequence.py` executes the real builder code for understanding, initial
domain, first decision, outer regeneration and second decision, with labeled
synthetic observations/understanding only. It checks each nominal request and a
full correction exchange. Sizes in the checked fixture range from 4,277 bytes
(understanding) to 15,210 bytes (reflection correction). All ten requests are
**blocked** without a certified Gemini chat-token upper-bound counter. This is an
honest unavailable prerequisite, not a fabricated token estimate.

At runtime the full messages (including raw invalid output and exact schema error)
are checked before reserving a transport attempt. >24,576 bytes or >8,192 certified
input tokens is an explicit error. No history/response is silently truncated.
Future actual understanding/domain strings may be longer than these fixtures:
the same gates must run on them; byte size does not certify token fit. Sum of
admitted input reservations <=81,920; generated caps <=7,168, including retries.

## Pending model controls and shared interface

Disk configuration fixes standard Gemini Flash, default service tier, explicit
provider allowlist/order, no fallback, parameter support requirements, max-price
caps .30/2.50 USD per million plus zero per-request surcharge, zero reasoning-token
policy and JSON mode. Per-stage max_tokens stays 1536/768/256/768/256. All three
execution gates remain required. The policy was initially false during offline
preparation; the subsequent public-data authorization opens only the project gate
and does not resolve either shared-interface or token-counter prerequisites. Mock tests
patch a local in-memory project policy only; shared flags/files are untouched.

The new adapter calls only `Client.chat(messages, project='autosizer', run_id=...,
max_tokens=..., max_cost_usd=..., authorize_live=..., request_options=...)`.
The shared client remains responsible for its global four-slot and USD ledger.
Raw useful response content plus usage/model/provider/tier/finish metadata are
retained. Cost reservation is passed to the shared ledger as well as recorded
locally. Nonzero/unreported reasoning, unexpected provider/model/tier, oversized
usage or over-reservation cost stops further calls. JSON/domain/batch validation
uses the existing contract with the corrected remaining budget.

**Blocked shared action:** the inspected installed shared `Client.chat` lacks
`request_options`; internally it replaces provider with only allow_fallbacks=false.
Its current public signature cannot carry the required standard-price, reasoning,
JSON and sampling controls. The adapter detects this and stops before any shared
call. The shared interface owner must extend the public method to honor those
options while retaining existing auth/scope/slot/USD gates. Private `_request` or
`_transport` calls are deliberately absent. No global file is modified here.

**Pending token prerequisite:** the actual selected-model tokenizer/framing upper-
bound counter is not yet supplied. The injected certificate contract and fail-closed
gates are implemented/tested; exact Gemini token fit is not claimed. No token,
provider or monetary limit is increased to work around either prerequisite.

## Verification

Fourteen new runtime/mock tests plus seven existing fair-plan tests pass. They
cover the budget regression, changed common data, persisted retry/failure/pending
charges, write-before-evaluator debit, missing failed history, byte/token rejection
without mutation, disabled config, exact pricing/tier/reasoning/output fields,
shared public signature detection, forwarded shared reservation/options, API retry
accounting, usage-policy stop, and the complete five-stage/ten-reservation path.
The installed shared module is imported from an explicitly supplied source path
for a signature-only probe with an in-memory public configuration stub; its private
`load_config` is patched to raise if touched, and no HTTP is invoked.

Official control references: [service tiers](https://openrouter.ai/docs/guides/features/service-tiers),
[provider and max-price options](https://openrouter.ai/docs/guides/routing/provider-selection),
[reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

## Subsequent authorization and current blocked action

User authorization subsequently permits the declared public SPICE/spec/feedback
payloads, Gemini 2.5 Flash, at most ten AutoSizer requests including failures/retries,
and a cumulative shared 10 USD API-stage budget across projects. The project gate
is now authorized (true); the stricter proposed .05 USD project token reservation
ceiling and all output/input bounds remain. No shared/global policy was changed.
The configuration filename retains PENDING because technical admission is pending,
not because fresh user approval is required.

The latest shared handoff and installed source were read after authorization.
Its public chat still lacks request_options and overwrites provider controls; no
actual selected-model token counter is available. The exact action paused is
AutoSizer's first authorized shared Gemini chat request. It has **not been sent**,
project API usage remains zero, and no transport attempt has an uncertain outcome.
This is a prerequisite block, not an approval denial. Once the shared owner
provides the controls and a certified counter, the existing user authorization
permits continuation without asking again. No private-method/alternate-client
workaround is used.
