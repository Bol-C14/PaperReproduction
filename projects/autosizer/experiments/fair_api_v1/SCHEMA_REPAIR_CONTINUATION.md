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
