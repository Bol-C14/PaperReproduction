# Native Planner milestone, 2026-10-29 UTC

Status: **live_pilot**, one selected `bp_fe:1:1` candidate. Three real model requests completed the original Planner tool sequence `get_design_state({})` → `view_layout(init)` → `submit_strategy`. Actual original handlers served all three callbacks; terminal handler returned `done=true` and the exact submitted strategy. This establishes native planning/tool-loop execution, not layout correctness, a completed agent algorithm, or a full paper reproduction. Placer, Checker, detailed placement, CTS, routing, PPA evaluation and LVS remain **not_run**.

## Actual configuration and deviations

Pinned OpenLayout commit `65e440d943443b48f4adfc0de5ef3012634bcd6b`; original macroflow roles, native tools and task objective retained. The bounded pilot substitutes `openai/gpt-6.1-terra`, OpenAI Standard through OpenRouter Chat Completions, medium reasoning, for the published model/interface. It uses one candidate and 2048 total output tokens per request, rather than published outer three candidates (inner default five), Planner six turns and 8192 agent output tokens. It includes full GPL attribution/source context as non-task material. These are explicit protocol/model changes; no paper leaderboard number is reproduced.

The initial state callback used pinned initialized-design facts, not a newly active OpenROAD session. The trusted original view callback returned the exact previously approved 1024×1024 PNG, 47,530 bytes, SHA256 `28d766ddfe52b7263d71de6d79c1fdb84dc0abc11ca79b16a1ef7b8a14d05383`. The amendment request carried exactly two occurrences of that same image, full append-only history and native callback IDs. No raw netlist/PDK, hidden answers, personal data or credentials were transmitted. Payload provenance and the modified-DEF per-file source-mapping limitation remain as documented in the packet reviews; this does not establish redistribution rights for the collateral library.

## Measured requests

| Stage | Input tokens | Output including reasoning | Reasoning | Accounted USD | Native output |
|---|---:|---:|---:|---:|---|
| Initial Planner | 12573 | 15 | 0 | 0.0157905 | get_design_state |
| Single-image continuation | 12749 | 520 | 500 | 0.0185355 | view_layout(init) |
| Same-image linked amendment | 14537 | 377 | 124 | 0.0200555 | submit_strategy |

E3 total: three requests, 912 output tokens including reasoning, **USD0.0543815**. Continuation family: two requests, USD0.0385910, three actual callbacks including the initial state. Final shared ledger: USD0.10593113 of USD10, remaining USD9.89406887, pending0/unknown0. Upstream BYOK usage is accounted even when router cost is zero. USD2.80 was a conservative full-context admission reservation, not the charged amount. Ledger callback count2 at model settlement precedes the final handler; journal count3 includes that terminal callback.

## Strategy and causal limitations

The strategy proposes left/top/bottom bands, opening to the right, a central standard-cell region and 2–3μm gaps. It supplies no macro coordinates or tested orientations. **The model incorrectly calls #0–#8 data SRAM: #0 is BTB; #1–#8 are icache data SRAM, #9 metadata and #10 tag.** Preserve that error in the original strategy and make true design facts available downstream. A schema-valid strategy is not evidence that clustering, pin access, legality, timing or routing improved.

Native strategy: 1184 UTF-8 bytes, SHA256 `ffffde82333c85c8aa5b423913909b4ca0c6cbba6dcbd0891da320d2e2aa14fc`. Privately saved strategy file: 1185 bytes, SHA256 `2cbf68c19829bce48f2af30a197c75fe5f491814c934c03f9c9151bb5c5d0f41`; the extra byte is a final LF. Raw strategy/provider payloads are excluded from this public milestone.

## Stops, amendment and failures

The original continuation window was **07:01:54–07:31:54 UTC**. Its first response requested view_layout; the one-image contract stopped before serving it. That run stayed stopped and its deadline expired. The separately labelled amendment window was **08:54:57–09:24:57 UTC**; terminal evidence records 789.373 seconds from amendment dispatch. Earlier setup and first-call elapsed time are separate. This is not a claim that the whole workflow fit 30 minutes. Prior usage was carried into a linked successor, never reset; family ceiling four continuation requests, eight callbacks including the initial state, 8192 output tokens and USD3.50. Only two continuation requests were consumed.

Approval denials occurred before live process creation; attempts were checked before the single evidence-supported retry. No uncertain model request was repeated. Earlier connectivity/sandbox restrictions, missing test import, a container image-ID validation mismatch and local PTY failure were retained in private failure history and resolved before release; they are infrastructure/protocol failures, not successful benchmark tasks. Offline final integration tests passed 38/38 locally and 38/38 on APRIL Python3.9 and3.12; finance compatibility separately passed127/127 on each APRIL version. These tests validate controls, not EDA quality.

Financial summary V1 incorrectly marked a recognized reconciled BYOK cost source unknown because an ad-hoc whitelist omitted it. V1 remains immutable; V2 uses the shared source whitelist and reports unknown0. No ledger mutation was made. A frozen view-proof component retains an offline-provenance flag; the actual source/container receipt and controller execution record establish its later real callback. Raw proofs were not rewritten.

## Commands and reproducibility boundary

The actual process was a private frozen owner runner on APRIL with separately reviewed financial admission and trusted callback containers. It verified source/body/claim/checkpoint hashes, admitted one request at a time, recorded response and settlement, and invoked only allowlisted original callbacks. No model-generated shell or Python was executed. Public command shapes below intentionally omit private deployment paths and credentials; they are documentation, not a complete executable workflow release:

```sh
sha256sum "$FROZEN_DRIVER" "$FROZEN_PLAN" "$FROZEN_GENESIS"
python3 -m unittest discover -s "$FROZEN_TESTS"
python3 "$REVIEWED_OWNER_RUNNER"  # reviewed immutable dispatch binding; single sole owner
sha256sum "$TERMINAL_RECEIPT" "$TERMINAL_EVIDENCE_ARCHIVE"
```

Controller Python3.9.25; callback Python3.10.12; Podman5.6.0. Callback sandbox had network disabled, read-only root, all capabilities dropped, no home/secrets/reference mounts and exact read-only approved image. The credentialed external controller remained outside it. Existing OpenROAD26Q2-1164-g08f67ee5ec was not used to create a new placed/routed result during this Planner milestone.

See `logs/planner_milestone.json` for sanitized receipt hashes and `NEXT_EXPERIMENT.md` for bounded downstream work. Raw logs, original handler outputs, bodies and ledger evidence remain private and independently audited; their hashes permit review without redistributing upstream inputs.
