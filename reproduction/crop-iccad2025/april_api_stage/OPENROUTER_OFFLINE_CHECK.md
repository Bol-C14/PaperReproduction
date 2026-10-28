# OpenRouter adapter: offline preparation only

The parent selected OpenRouter for the shared service. No private configuration
or credential is created/read from a vault here. The shared loader interface and
specific fixed model are still pending. No model call, endpoint probe, live-entry
point execution or encoder change was made.

`ChatAPI` now accepts explicit `base_url`, `api_key` and `model` arguments so the
forthcoming shared loader can inject a single private configuration without
copying credentials into this repository or mutating process-wide environment.
For compatibility, absent arguments still read the existing runtime environment
once at adapter construction. Endpoint/model/credentials are snapshotted for
that instance; later environment changes cannot silently switch them midway
through a run. No key is included in result records or error messages.

The fake-transport tests explicitly construct the URL
`https://openrouter.ai/api/v1/chat/completions` from the configured base, preserve
one exact synthetic fixed model ID, and verify that no alternate `models` list
is sent. For `openrouter.ai`, the outgoing request explicitly sets
`provider.allow_fallbacks: false`. Redirects remain refused. This is a checked
outgoing-wire policy, **not a claim that the live service has honored it**;
service-side behavior remains untested until the parent authorizes a real call.
A fixed service model ID also does not by itself prove an immutable model-weight
revision or a globally fixed underlying provider; do not claim either.

HTTP429, HTTP503 and transport timeouts each cause exactly one fake transport
attempt and then an error. There is no client automatic transport retry, model
switch, alternate endpoint or heuristic fallback. The existing pilot attempt
budget remains34 total and at most2 completed-content/schema attempts per stage;
transport/HTTP/truncation errors stop instead of using that second attempt.
Existing tests retain the total/per-stage budget and duplicate-proposal checks.

All18 offline tests passed in `offline-tests-openrouter.log`. They use only dummy
credentials and scripted transports, never a default network transport. The
real-model pilot remains unexecuted; no API authorization marker was created.
Its existing marker/endpoint/model/public-data/token-counting requirements are
unchanged. The fixed MiniLM revision, local384-dimensional embeddings,
L2 normalization and256-token truncation are unchanged. No embedding API is
introduced. No prior or target EDA measurement was repeated for this check.

Next: accept the parent's public loader interface, inject its selected fixed
model/private runtime values, and retain the existing authorization boundary.
Do not execute the previously denied entry point as a configuration probe.
