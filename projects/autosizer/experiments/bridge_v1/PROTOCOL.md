# New simulator-controller bridge protocol

This stage authorizes real CPU-only ngspice measurements with the explicitly
labeled `TEST_CONTROLLER_NOT_LLM`. No API request, model download or local model
inference is permitted. Old closed phases and their results remain unchanged.
This is one inverter/seed-11 integration pilot, not the full AutoSizer method,
LLM performance evidence, or the paper's Gemini/24-task reproduction.

Freeze code commit, hashes, runtime binary/selector identities, seed, UTC deadline
and accounting in a fresh `protocol.json` before the first circuit launch.
Do not reuse an output root or resimulate historical observations as free data.
At most 56 charged circuit attempts in two hours: planned 3 preflight, 24 fixture,
24 independent full-domain GP control, and 2 selected-winner refined validations
(53 total). The three remaining slots are diagnostic reserve, never silent retry.
Process wall/CPU/memory caps: 20 s / 15 s / 2 GiB. Bind to CPUs 24-31, run serially,
and cap numerical libraries at one thread. Check server load before launch.

Retain original public inverter topology, 9x9 widths, scaling, SKY130 tt, 1.8 V,
10 fF load, 27 C, all original strict source constraints and normalized objective.
Disclose measurement correction: pair opposite response edges at 0.9 V and use
integral mean power rather than adaptive-time-step sample mean. Preflight measures
source, corrected and refined corrected decks at [4,4]; source failure is evidence,
not a reason to modify thresholds. Require independent vector/strict-constraint
checks of corrected runs before starting the fixture.

Use the local frozen renderer/scorer as pure functions, never the old execution
entrypoint or archived histories. Record exact new decks/stdout/stderr/metrics,
write-before-launch charged attempts including failures, commands, affinity,
wall/CPU/peak-RSS upper bound, source/code hashes and invalid-response logs.

Fixture: five JSON decisions (synthetic circuit understanding, central-domain
selection, random 12-attempt decision, full-domain expansion after twelve new
measured rows, GP 12-attempt decision). This is intentionally a deterministic
software fixture. It must consume actual first-batch measurements before outer
feedback; no hand-written fixture output is evidence of model understanding.
Check complete active/fixed variable coverage, legal released values, unseen
capacity >=12, exact batch size, no duplicates, unsupported method rejection,
and preserve stop/invalid outputs. Domain changes are reported without attributing
scientific gains to this fixture.

Independent GP control: fresh 24-attempt history, 10 random points then the existing
fixed scikit-learn GP-UCB port: index/8 inputs, standardized targets, Constant(1)
times Matern nu=2.5 length=.35 plus white noise 1e-6, UCB mean+2sd, no hyperparameter
fitting. Invalid measurements consume budget and are excluded from training;
<3 valid observations uses explicitly logged random fallback. The fixture GP
batch uses its own prior observations. No control-arm or historical/oracle data
enter controller feedback. No stop-on-first-feasible; select feasible maximum-FoM
or least-violating incumbent and measure each winner on refined vectors once.
The two arms have different initial domains and are integration controls only,
not an efficacy comparison. Independent audit re-parses logs, rescales units,
recomputes strict source constraints and waveform delay/power/gain (<0.001 unit
tolerance), verifies unique points, training counts and twelve-row feedback.

Public delivery retains portable relative commands and model includes. Raw APRIL
runtime paths stay in the private run root; exported decks identify a portable
`MODEL_SELECTOR` placeholder and preserve the original deck hash separately.
No binaries, model weights, downloaded source archives or new upstream source/PDK
bodies are added. Existing SKY130 Apache-2.0 license/notices remain; AutoSizer's
upstream code/benchmark license remains unconfirmed as documented previously.
