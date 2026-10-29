# Mock-ready driver and shared-Client extension contract

Version E3-bridge-v1; specification only, no live implementation or policy change. This preserves the original model-generated strategy→coordinate plan→native legalization/feedback→visual gates mechanism. One candidate/no repair and reduced output/turn budgets are declared deviations; they do not reproduce either outer3- or inner5-candidate performance.

## Trust and process boundary

1. The trusted Mac broker alone loads the existing shared Client and credential. It alone calls its public bounded chat entrypoint and writes the existing global ledger/reservations. No direct urllib/SDK transport, test-transport injection for a real request, alternate project identity, new key or credential copy.
2. The original macroflow control logic receives an injected VLM-compatible adapter and an ORSession-compatible native adapter. A worker has no provider network, keys, ledger/config or home mount. Its request spool contains only numbered/hash-manifested approved messages/images. Broker receives a request ID and immutable packet reference, validates role/budget/packet rights, then returns only normalized response/usage. No open TCP service or SSH-shell action is exposed to the model. The worker may not mutate its mounted code, source/constraints or approved-input manifest.
3. Native EDA processes run through the already established rootless container launcher: network none, read-only root, cap-drop all, no-new-privileges, PID/memory bounds,4-core affinity, explicit thread4, task collateral read-only and candidate output-only writes. A fixed path map translates approved input/output parameter paths; never substitute arbitrary model strings into shell/Tcl. Model actions are JSON data, not candidate Python/Tcl programs.
4. Hidden/reference/evaluator stores remain outside worker mounts and broker model context. The independent artifact/PPA verification runs separately after outputs are copied read-only into its verifier workspace. Public role/gate instructions required by the original mechanism are explicitly agent-visible; additional acceptance implementation/test/fixing commits are not. The candidate cannot select source files, evaluator policy or model endpoint.
5. If worker orchestration dependencies are unavailable in the current image, stop at offline preflight. Do not put the credential into the worker to simplify bridging, weaken seccomp/container settings or run untrusted code on the host. Native image/controller adapters need mock/isolated validation before any real call.

## Shared Client public extension (central owner)

Add explicit validated `tools`, `tool_choice` and multimodal message support to `Client.chat`; keep `request_options` closed rather than permitting arbitrary transport fields. An immutable allocation binds project`pdagent`, protocol hash, exact model/provider,3total attempts, serial execution, max Planner/Placer2048 and Checker1024, **USD0.32 reservation per attempt / USD0.96 aggregate**, globalUSD10 ledger and all prior commitments. Existing combined batch-allocation ceilings must be reconciled by the central owner, not silently raised. Qwen/model registration remains necessary even though the reservation now matches the currentUSD0.32 contract.

Allowed payload: roles system/user/assistant/tool with well-formed native assistant `tool_calls`, exactly linked tool_call_id results and original role schema subset. Content blocks are text or base64 data-URI PNG from reviewed packet bytes. Reject external/http/file URLs, non-PNG payloads, MIME/signature mismatch, unapproved hashes, dimension/byte excess, NaN/Inf coordinates, missing fields, unknown tool names, role escalation and unmatched/replayed tool IDs. No implicit image drop, text-only fallback, JSON-in-prose tool shim or auto-routing fallback.

Input envelope: canonical full text/messages/tool-schema JSON≤65536bytes excluding base64 bytes; at most2images, each≤1048576decoded bytes, both dimensions≤1024; whole UTF8 request≤4194304bytes. Model accepted context≤262144tokens, native tools/schema/image tokens included. If a provider accepts a larger context or charges separately for images/tools/cache/search/request overhead beyond registered limits, reject the route before sending. Output token caps include all billable generated/reasoning tokens; fixed Instruct model has no requested reasoning feature. All auxiliary services/plugins disabled. Validate current image-token billing against primary endpoint docs/metadata; absence of a field is not proof of zero extra cost.

ReserveUSD0.32 before transport, never downgrade it to the theoreticalUSD0.067072 estimate. Global available charges+pending reservations+new bound must remain≤USD10, E3≤USD0.96, existing stage limits preserved. On missing cost or protocol/transport error, charge the full reservation and stop. On uncertain network outcome keep it unresolved for reconciliation; no automatic replay. Shared Client's current finish-on-transport-error behavior must not imply a network timeout proves nonexecution. Any returned actual cost above bound stops all E3 dispatch pending central reconciliation. Provider-side hard price/context/output guarantees are required; a post-response overrun alarm cannot undo a bill.

## VLM adapter surface

- `chat(messages, system, tools, max_tokens) -> LLMResponse`: canonicalize using the original VLLM chat-format conversion, but fail on any missing image. Validate actual role against frozen original tool schema hashes in role_contract_hashes.json. Call only extended shared Client.chat with real allocation/run/request IDs and conservative reservation. Preserve exact sent bytes/hashes and usage metadata privately. Return text, typed native ToolCall(id,name,input), stop reason, normalized assistant raw message, token counts and latency.
- `build_assistant_message(raw)`, `format_tool_result(id,content)`, `build_tool_results_message(results)`: preserve the original assistant/tool linkage and image follow-up sequence. Do not fabricate a terminal action from free-form text or parse a PASS word into a gate verdict.
- Broker max1HTTP request per allocated role. Extra inspection/nudge/tool follow-up requests exhaust that role and stop the candidate. Expose the original read-only tools, but prefeed known official state/image inputs to make a terminal call possible. All three attempts, including errors, consume the request cap. No fallback coordinates or fake model outputs in real mode.
- Preserve upstream functions for strategy, coordinate parsing, preview_plan_quality, legalization/place_plan, native templates and gate/PPA logic. Reject incomplete plans exactly as original pure-coordinate mode; augment safety by validating finite numeric syntax and indices#0–#10 before handing data to those functions. Record any legalizer displacement; report model placement separately from repaired placement.

## Exact original schema subsets

Planner: get_design_state, view_layout, list_snapshots, submit_strategy. Placer: get_design_state, view_layout, submit_placement_plan. Checker: get_design_state, view_layout, list_snapshots, measure, submit_verdict. `measure.what` remains density|overlaps|congestion; `submit_placement_plan` remains the original plan-string/notes schema, and `submit_strategy`/`submit_verdict` retain original required fields/enums. Do not replace them with a bespoke placement JSON schema. Schema bytes/hashes are frozen locally from the original source, not hand-rewritten; full files are retained privately with GPL3 licence sidecar.

## Required offline mock matrix before enabling

Use only wholly original synthetic fixtures, including an original tiny PNG; no real case image/facts are needed for these tests.

| Fixture | Required observation |
|---|---|
|Valid multimodal Planner terminal call|Captured body retains actual PNG bytes/hash, native schema and submit_strategy tool call; one reserve/finish |
|Valid Placer terminal plan on a synthetic11-entry list|Native tool args unchanged; alias indices preserved; no model-supplied code executed |
|Checker verdict + native tool round-trip|tool_call_id matches preceding assistant call; no PASS-string conversion |
|Extra read-only inspection turn|First action may be returned, but a requested second HTTP request is blocked by role budget; no nudge |
|Missing/dropped image, external URL, wrong PNG MIME, over-size request|Rejected before transport/reservation; never fall back to text |
|Tool not allowed for role, rawTcl, unknown index, incomplete/NaN plan|Rejected before native execution; selected candidate retained as failed |
|Truncated/refused/free-text response|No synthetic terminal tool; stop, account actual/full reserved charge |
|HTTP timeout/ambiguous outcome/duplicate request ID|No automatic retry, reservation unresolved or conservatively charged; reconciliation required |
|Missing/over-bound usage|FullUSD0.32 reservation or overrun alarm, no next request; shared total not reset |
|Unauthorized project, model/provider change, stale packet hash or licence gatefalse|No transport call, no alternate identity/provider path |
|Candidate modifies output log to look clean|Independent artifact verifier still requires native DB/DEF/report consistency; forged log alone rejected |
|Worker secret/network probe|No credential, home or evaluator mounts and no worker network; host security unchanged |

These are acceptance requirements, not claims that an adapter or tests already exist. Real endpoint/tool/image compatibility and case-data transmission permission remain unverified until explicit preflight/parent review. A synthetic mock cannot establish benchmark success or clear data licensing.

## Source-aligned call count update

RUNTIME_ALIGNMENT.md is authoritative: the active source has no pre-route fast-place Gate-B call, despite the legacy helper and stale prompt note. Use3role attempts andUSD0.96, then native backend plus deterministic post-route evidence. Set one candidate, pure-model coordinates enabled, exactly one Gate-A check (gate_a_max_refine1), no post-route optimization rounds, and one turn per role; never set Gate-A checks to0 and silently omit the visual gate. Require original terminal tool result from each role before allowing fallback text or continuation. All future exact packets require hashing and review before dispatch. Original source role/schema bytes are unchanged; these bounded stopping/control restrictions are explicit new-pilot deviations.

## Licence-complete initial-packet envelope correction

Active initial body SHA23ee554f… is113,803bytes; structured text/tools are50,104bytes. It preserves original role/image/task/tools and adds an explicitly non-task fullGPLv3/source/attribution block. The proposed text/schema envelope must be64KiB, not24KiB. This is a required central Client extension, not an implemented relaxation. Preserve all required notice text on overflow; stop rather than truncate. Image sources remain reviewed data-URI PNG only. Textual source/licence URLs are inert references and confer no fetch action; no provider/network tool is added. First maxoutput2048 and conservativeUSD0.32reserve stay unchanged. Exact matching-tokenizer count is unavailable, so context/image/token billing checks remain explicit central preflight work. See LICENCE_COMPLETE_PACKET_REVIEW.md; no raw source image/body/prompt asset is published by this metadata.
