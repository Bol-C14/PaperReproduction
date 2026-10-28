# Fair API-vs-fixed-GP pilot — authorized, current cost envelope

This protocol was prepared after the synthetic bridge pilot at commit
`af730024262bef23cd44a97654979e4c48e121d4`. The subsequent user authorization permits the declared public data and live
Gemini pilot through the shared client; it does not reopen old roots. The current
fee envelope and its precedence over earlier token estimates are specified in
COST_ENVELOPE_PROTOCOL.md. No exact tokenizer is required. Freeze this draft and a new timestamped
runtime manifest before a future run. The older bridge CLI is not a fair runner:
it hardcodes different initial domains and a test-controller label. Do not call
it with an API adapter and relabel the result.

## Question and treatment

For one released inverter and seed 11, does adding actual model-guided domain and
inner-algorithm decisions after identical initial information change constrained
search outcomes relative to a fixed full-domain GP-UCB policy? This is a paired
integration pilot, not a statistically supported method comparison or the paper's
24-task result. Model guidance is the sole assigned treatment. Domain updates and
random-versus-GP choices are bundled consequences of that treatment; this design
does not isolate circuit understanding, range selection and reflection separately.

Both arms use the same released full 9x9 initial domain, variable mapping,
simulator/PDK/testbench, 27 C, corrected measurement definitions, target constraints,
scorer, fixed numerical GP implementation/hyperparameters, initialization evidence,
attempt limits, numerical-thread settings and proposal RNG implementation/seed.
A model cannot change topology, source measurements, thresholds, GP kernel/UCB,
physical simulator parameters or budget. Every proposal is selected by the same
random/GP engines over legal unseen points. The fixed control always uses the full
grid; the guided arm may choose a valid subset or active/fixed domain and select
random versus the exact same GP port. Both have access to all 81 released points.
The model cannot see control decisions/results, previous pilot/oracle observations
or any test-controller prose.

## Exact common observations and real-call accounting

`PLAN.json` freezes ten distinct seed-11 initial indices sampled without measured
labels from the full domain. Its literal list, source hash and domain are
canonical; the future runner reads it instead of resampling. No seed/initial-set
change is permitted after inspecting outcomes, even if a common point saturates
the small problem's headroom.

1. Three separately charged preflight calls: source, corrected and refined center
   measurements. These are safety/measurement checks, never optimizer observations.
2. Measure the ten common points **once**, serially. Every attempted launch,
   failure, missing metric and invalid row remains in the common ledger. Preserve
   raw deck/stdout/stderr hashes and process outcome; never replace failed common
   points. Before either adaptive arm starts, freeze common row JSON and its hash.
3. Both arms receive deep copies of that exact ten-row dataset, with identical
   values, invalid statuses, ordering and initial full domain. No arm resimulates
   initialization for a different observation and no common measurement is counted
   as two physical SPICE calls. Models receive only the approved public projection.
4. Each arm has exactly 24 **fresh attempted launches**, as two 12-attempt batches.
   Maintain separate histories/proposal RNG streams initialized from the same seed.
   Exclude common and own past indices; no cross-arm cache. If arms propose the
   same post-initial point, launch and charge it separately for each arm.
5. Each arm selects its incumbent once and gets one separately charged refined
   winner validation, without replacing the selection after a failure.

Accounting is explicit: 10 common + 24 guided + 24 control = **58 physical search
launches**, yielding 34 observations per arm (10 common + 24 fresh). Add 3 preflight
and 2 validations for **63 stage attempted launches**, the hard cap. The common
physical cost is a separate ten-call pool; if amortizing costs, each arm receives
five common calls plus 24 fresh = 29, never the misleading claim of 34 independent
physical calls per arm. Validation is one additional physical call per arm.

The 24-call limit counts attempted launches, including timeout/solver/measurement
failure. Distinguish attempted-launch IDs, successful process spawns and valid
measurements. A future launcher sets spawn confirmation only after successful
`Popen`, stores a unique spawn ID plus local PID/start-time evidence, and journals
before/after process execution. A stale launch-pending record must be reconciled,
not rerun. Full matched-budget interpretation requires 24 confirmed fresh process
spawns per arm; an OS launch failure or early stop is disclosed as an incomplete
comparison, not silently refilled. `plan.py` checks declared accounting but cannot
itself prove that an OS process executed; raw process evidence is also mandatory.

Never force a model to continue after stop and never use heuristic filler.
An invalid model response receives at most one prescribed schema correction;
otherwise stop that arm and retain evidence. Preserve the independent control
up to its own cap if safe. Report actual unequal budgets and do not label them a
matched full-budget efficacy result. No conditional post-result seed extension.

## Five model decisions and fixed numerical policy

Only after the common dataset is frozen: actual circuit understanding from public
source (no model-generated prose is injected), initial domain selection using that
understanding plus common observations, first 12-attempt random/GP decision,
outer regeneration after twelve guided attempts, and second 12-attempt decision.
Thus reflection sees 22 observations (10 common + 12 guided), not twelve total.
All model fields and raw output/error must be preserved. Initial/domain decisions
cover each variable exactly once with legal released values and at least twelve
unseen combinations. The nine-value grid cannot provide twelve combinations if
one variable is fixed; reject rather than silently unfix or shrink the batch.
Unchanged domains are valid and honestly reported. Four endpoints/domains are not
four independent statistical replicates.

Both GP engines start with the same common valid observations and use only their
own new history thereafter. There is no extra ten-point random warm-up after the
common set: initialization is already consumed. Use the existing fixed
scikit-learn port (indices/8, normalize_y, Constant(1)*Matern nu=2.5 length=.35 +
white noise 1e-6, UCB mean+2sd, no kernel fitting). With <3 valid measurements,
use the same logged random fallback in either arm. Invalid data are never zero
fitness labels. A model choosing random changes policy; it cannot choose different
GP internals. This remains an explicitly named numerical/backend substitution.

The prior request proposal's five nominal / ten maximum calls and output caps
remain: 1,536 understanding; 768 initial domain; 256 each inner decision;
768 outer reflection. Reserve at most 10,485,760 input tokens (ten full official 1,048,576-token
Gemini input capacities), and at most 7,168 generated tokens. Each full request
retains its scientific context and must be <=24 KiB serialized messages. This is
a conservative fee envelope, not a claim of actual token count. Provider reasoning-token billing needs a separate
approved cap. Reflection now includes up to 22 rows, so the previous payload
shape/max-history description is superseded for this draft. Reserve the full fixed-model input capacity at capped prices before each
request, including correction attempts; use native response usage for actual
accounting. Unknown fees retain the reservation. No silent truncation is allowed.

## Metrics, endpoints and interpretation

Retain the source strict targets: normalized FoM >1, gain >20 dB, average delay
<50 ps and dynamic power <50 uW. FoM=(gain_dB/20)/((delay_ps/50)*(power_uW/50)).
The gain normalization uses the numerical dB metric as specified by the existing
normalization port; it is not a linear-power gain ratio. Source YAML fallback
`gain/(delay*power)` is a different value (normalized FoM is 125 times fallback
for these targets), kept separately and never used to check normalized FoM >1.

Primary descriptive endpoint: best strictly feasible normalized FoM among all 34
observations at the fixed budget, and improvement over the common feasible
incumbent. With no feasible design, report null best-feasible objective and
least violation separately. Secondary: fresh attempt to first **new** feasibility,
feasible fraction among fresh calls, invalid/failed counts, chosen domains/methods,
API attempted calls/tokens/cost and wall/CPU time. If initialization is already
feasible, report feasibility at initialization (fresh count 0); if it already
saturates available headroom, report the ceiling without changing the protocol.
No three-seed inference, paper success-rate claim or isolated reflection causal
claim follows from this single seed. Different adaptive trajectories are expected;
different initial information or numerical engines are prohibited.

Freeze/check simulator executable and every pinned PDK dependency, testbench and
source hashes. Keep write-before-launch ledger and all failure outputs. Check
independent stdout scaling and waveform reconstruction, including a static-power
term integrated directly from the 10..90 ps waveform interval. Independently
rescore every attempt and audit both selected refined winners, with 0.001 physical
unit tolerance; near-threshold disagreements remain failures/uncertainty, never
rounded into feasibility. Preflight/validation samples never enter search history.
Use APRIL CPU24..31, serial processes, one numerical-library thread, existing
15 CPU s /20 wall s /2 GiB per-process limits and a fresh two-hour deadline.
No global environment changes, new model download or paid GPU is required.

## Runtime-preparation revision: separate attempted-launch accounting

The new `fair_runtime.py` builder replaces the old request arithmetic. It reads
the frozen plan, requires the common ten-row dataset hash to be frozen before
branching, and derives `remaining_attempts` solely from the current arm's search
attempt ledger: **24 minus fresh charged launch reservations**. At reflection,
10 common +12 fresh rows means 22 observations and **12 attempts remaining**.
The independent arm still has all 24 until it launches its own search. Preflight,
common data, validation and API attempts have separate pools.

The injected `FairBatchRunner` journals before evaluator invocation. Invalid
measurements, solver/OS failure, explicit retry and unresolved launch all stay
charged; exception outcomes remain pending until reconciled, with no automatic
replacement. Normal proposals must be unseen. An explicitly requested retry is
another charged attempt and violates the unique-point/full-matched criterion
if it replaces a required distinct point; it is never a free diagnostic. API
schema/transport retries consume API reservations (at most two per model-decision
stage and ten total), not fictitious SPICE launches. Local byte/token rejection
before transport is not an actual API request. A project reservation may
conservatively remain charged if the shared gate rejects it before transmission.

`build_messages` uses only the public source and verified completed rows matching
common/current-arm debits. Missing failed rows cannot be silently omitted. Exact
raw invalid responses and local schema errors are appended for correction; all
scientific context is retained. Both normal and corrected full requests pass the 24 KiB byte gate. Without
a local exact tokenizer, the entire official fixed-model input capacity is
reserved; this includes framing and cannot underestimate an accepted prompt.
An oversized request stops without truncation. The earlier 8,192/81,920 input
estimate is superseded by this explicitly frozen fee envelope. `REQUEST_SEQUENCE_CHECKS.json`
records all five stages and one full correction fixture per stage admitted
under the context envelope, not model outputs or an exact tokenizer-fit claim.

`OPENROUTER_PENDING_CONFIG.json` initially remained execution-disabled during
offline preparation. Its project gate is now enabled by the subsequent explicit
public-data authorization, while technical admission remains blocked. It fixes
`google/gemini-2.5-flash`, `service_tier=default`, only/order `google-ai-studio`,
no fallback, require_parameters, max_price prompt .30/completion 2.50 USD per
million and per-request price 0, no reasoning, JSON-object output and stage caps.
The per-request `max_tokens` caps are 1536/768/256/768/256; total reserved generated
tokens <=7168, with billable reasoning required to be zero. The project fee-reservation ceiling is 3.20 USD; all ten context/output
envelopes total 3.163648 USD, under the shared cumulative 10 USD stage cap. Actual full usage/provider/tier/finish reason must be retained, and a
provider/usage/reasoning mismatch blocks subsequent project requests. Missing
reasoning-token confirmation is not silently assumed to mean zero.

The project `SharedController` delegates **only** to the shared public
`Client.chat`; that client owns four-slot concurrency and the locked shared USD
ledger. It neither loads private configuration nor calls private shared HTTP or
request functions. At the inspected shared revision, `Client.chat` does not
accept `request_options` and its internal request overwrites provider controls.
The adapter therefore refuses before invoking it. The shared owner must add and
honor `request_options` (provider, service_tier, temperature/top_p, reasoning and
response_format) while preserving existing auth/project/slot/budget gates. Do
not use a private-method bypass. Mock integration passes these exact options and
per-attempt USD reservations; it is not evidence of completed live integration.
The project disk gate, parent authorization and shared live gate must all allow
execution later. The later authorization opens only the project gate; shared policy is maintained
by its owner, and no call can pass the missing-interface/token-counter gates.

Subsequent authorization: the user permits public circuit/specification/feedback
transmission via the shared OpenRouter client, Gemini 2.5 Flash, at most ten
AutoSizer requests including failures/retries, within a cumulative 10 USD API
stage shared across all projects. This does not increase project token/request
bounds or authorize private payloads. Current live admission remains blocked by
the shared public method lacking request_options as last inspected, rather
than by missing user permission or any tokenizer requirement. No actual request was issued.

Current deployment: shared public request_options is installed and verified.
The cost envelope removes the tokenizer prerequisite. The authorized live runner
is live_pilot.py, with a fresh output root, max10 requests at .32 USD each and
shared cumulative10USD enforcement. Earlier interface/token blockers are resolved.
