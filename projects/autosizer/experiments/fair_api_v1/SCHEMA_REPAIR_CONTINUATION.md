# Recorded schema-contract repair after the first real phase

The first authorized run, frozen at `9a3ddae`, completed 39 real SPICE attempts
and 3 actual Gemini requests, charged 0.00782799 USD with zero reasoning tokens.
Circuit understanding was valid. Both initial-domain responses selected legal
width grids but additionally placed immutable L, supply/sweep/load parameters
inside `variables_fixed`. The schema allows only W_pmos_base/W_nmos_base there;
both responses therefore failed with 'Each variable must be covered exactly once'.
The generic correction did not identify the extra immutable names, so the second
response repeated the issue. The model arm stopped before fresh search. Independent
GP completed24 fresh attempts; no matched-budget superiority conclusion follows.
The first root, raw responses, errors, results and frozen protocol stay intact.

This engineering continuation fixes the **prompt/validation contract**, not the
measurements or constraints: explicitly name the only two optimization variables,
exclude immutable params from both variable maps, require variables_fixed={} if
both widths are active, and report the exact unexpected names on schema failure.
No response is silently filtered/repaired or hand-substituted. New decisions must
come from actual fresh API calls. The existing actual understanding is carried
with its raw response hash; it is not a synthetic fixture or replay presented as
a new call. The fixed-budget objective is clarified; model stop is still honored.

A new root/protocol freezes this repair. Reuse exactly the real common10 dataset,
preflight3 and already completed independent GP24, with hashes and provenance;
never resimulate or pretend to recharge them. Copy immutable original raw evidence
and a carry-forward manifest, while retaining the first root unchanged. Do not
send any control data to the model. Old guided validation of the common-only
incumbent remains a charged diagnostic; it cannot validate a future new winner.
The actual independent GP winner validation is reused unchanged. Complete at most
24 previously unlaunched guided points and one new guided refined validation.
Thus cumulative real SPICE attempts are at most **64** (39 carried +25 new),
including the one failed-phase diagnostic. This explicitly supersedes the original
63-stage cap for the recovery ledger; the equal search budget is still10 common
+24 per arm, or58 real search launches. All numerical/physical hashes must match
before data can be carried. No original scientific artifact is overwritten.

Shared AutoSizer request accounting stays cumulative:3 already charged, at most7
remain (including all failures/retries); the continuation normally needs4 requests
(initial domain, first decision, outer reflection, second decision). Every shared
call reserves .32 USD under the global10USD and project10-request caps. Changing
root/run labels does not reset either. The local continuation ledger explicitly
records carried_api_attempts=3 and caps new+carried<=10. Actual prior cost is carried
into the final audit. The total7168 generated-token ceiling remains sufficient:
prior actual2244 + maximum7 continuation slots<=3840 =6084, with reasoning off.
Full native usage and any failed correction remain recorded.

This is a repaired integration demonstration, **not** an untouched preregistered
model-efficacy trial. First failure remains a reportable negative result. The
paired data/engine/budget checks can establish search-loop correctness, but a
single task/seed with a prompt fix informed by observed schema failure cannot
establish method superiority. Future efficacy work requires a newly frozen
multi-seed protocol before seeing those results.

## Second continuation: output-encoding repair, two requests remain

The first schema repair completed12 genuine model-guided SPICE attempts. The first
inner decision incorrectly proposed continuous parameters and was rejected; its
one correction returned the required empty parameter override and selected the
actual fixed GP port. Six of12 designs were feasible, best FoM3.400767279.
Both subsequent outer outputs echoed the entire81-point input domain and lengthy
commentary before the required output schema, hit finish_reason=length, and were
rejected without semantic repair. Cumulative requests8, cost0.01965855USD, reasoning0.

A further frozen encoding clarification gives the complete compact outer output
schema, asks not to echo input context/history, and limits output reasoning prose.
It does not remove or truncate input scientific context, change output token caps,
relax physical constraints or fabricate an outer decision. The final two authorized
requests can cover one genuine outer regeneration and one second inner decision;
if either fails or the model stops, preserve that outcome and do not exceed10.

Carry all52 physical measurements and12 guided rows exactly, including negative
phases, and use the original actual understanding with its response hash. Do not
repeat common, control, preflight or first-batch measurements. A prior guided
validation becomes a charged diagnostic because it cannot validate a later winner.
At most12 new guided calls plus1 refined winner validation makes cumulative65
physical calls (58 search,3 preflight,2 failed-phase diagnostics,2 final winners).
If no new designs occur, skip redundant validation. Model-call accounting remains
8 carried plus at most2 new; local and shared caps both enforce this. The output
repair is informed by observed formatting failures, so conclusions remain an
engineering integration result, not a pristine preregistered efficacy trial.
