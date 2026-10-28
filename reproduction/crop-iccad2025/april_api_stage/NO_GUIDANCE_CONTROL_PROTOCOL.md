# One bounded no-guidance control

Question: on held-out FIR3, does removing the retrieved prior's name and measured
configuration guidance change the three sequential model choices or final QoR?
This is one later no-guidance run compared with the existing guided trajectory,
not a strictly paired experiment or a statistical estimate of retrieval benefit.

Reuse the existing genuine FIR3 summary/cache without any new summarization or
embedding call. This keeps preprocessing fixed but makes total pipeline costs
incomparable: compare search-only requests/cost, and report cached preprocessing
separately. The original fixed MiniLM encoder is neither changed nor rerun.

Keep model google/gemini-2.5-flash, temperature0, reasoning disabled, JSON-object
mode, output640, original prompt/system text, legal8-option pool, seed23,
objective LUT4-count times depth, native tools and correctness requirements.
Keep the context shape/arm label. Only retrieved_prior=null and
retrieved_guidance=[] differ initially. Later target histories evolve separately.
The original protocol seed is not a provider-side determinism guarantee.

Use only the shared public Client.chat(request_options=...) interface. The
shared module owns live/project gates, concurrency, request counters, price caps
and cumulative ledger. No project private-request bridge or direct HTTP route.
The newer shared standard-tier price/parameter routing filters are safety-policy
differences; provider/weight identity across the two time windows is not proven.

Before any new model call, verify source/tool/cache provenance, measure fresh c0,
and compare the reconstructed guided first context and prompt with the original.
Any mismatch stops before model dispatch. Every measured candidate requires ABC
CEC,256 independent vectors and matching LUT depth, using the original oracle.

Budget: nominal3, maximum6 actual requests (at most2 content attempts for each
of3 proposals), inside the existing remaining16. Transport/HTTP/unfinished
completion failures stop without automatic retry. Preserve every failed attempt.
No heuristic fallback, repeated trial or request-limit increase. At most4 actual
synthesis attempts: fresh c0 and3 new options. CPU8-15, thread caps8; inspect load.

Per-request conservative reservation is0.32USD, not a token-count claim; worst
unknown-cost reservation is1.92USD and the shared cumulative10USD ceiling still
applies. Actual usage settles the ledger; unknown costs retain reservations.
Input-size diagnostics are not certified token counts, and contexts are not
truncated to satisfy them. The fixed byte transport bound remains in force.

Save the pre-run runtime protocol/source SHA, shared-module fingerprint, all
requests/responses/usage/failures, contexts, CEC/netlists/raw QoR and final ledger
summary privately. Publish only reviewed code and a scanned minimal result
subset, omitting private paths, service response IDs and shared batch IDs.
No new LICENSE or original benchmark/model-weight redistribution is introduced.

The first preflight stopped before any synthesis/model call because the saved
context's sorted JSON keys were mistaken for a prompt-content difference. The
corrected check parses the original prompt and checks semantic equality plus
its actual serialization order. Preserve the failed preflight log; use a fresh
v2 output directory. This does not add model attempts to the6-call budget.

A second guard found nested key-order loss after one correct fresh c0 and zero
model calls. Resume only that preserved baseline checkpoint if it contains
exactly one successful c0 and no model-attempt/context/output files. Recheck
its netlist/CEC, preserve both failure logs and the original protocol, and write
a separate resume protocol. Reconstruct contexts from the original prompt's
full nested ordering. Total baseline/candidate synthesis budget remains4 and
model budget remains6 across these preflights and the resumed control.
