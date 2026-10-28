# Real electrical optimization loop completed; live LLM mechanism remains blocked

The candidate → ngspice → metric parsing → exact specification feedback → GP/
range update loop ran on two released SKY130 tasks. Four controls, three seeds
and 36 attempts per run completed, followed by independent remeasurement and a
held-out finite-grid reference. No extra downloads, dependencies, paid resources,
GPU or model calls were used. This is a numerical-form port and new baseline
experiment; it is not reproduction of AutoSizer's LLM controller or 24-task result.

## Matched-budget results

Each row averages seeds 11,29,47, with the same ten independently simulated central
warm-start points per circuit/seed across arms. After initialization, `random_full`
samples uniformly from unseen full-grid points. Thus this is a shared-prior random
control, not an all-full-grid random start benchmark. Failed attempts would consume
budget; no early feasible stop or cross-run simulator cache was used.

| Circuit | Method | Best feasible normalized FoM, mean ± sample SD | First feasible attempt, seeds 11/29/47 | Inverter grid optimum hits |
|---|---|---:|---|---:|
| Inverter | Random full space | 3.31838 ± 0.08767 | 13 / 13 / 11 | 1/3 |
| Inverter | GP full space | 3.40077 ± 0 | 11 / 11 / 12 | 3/3 |
| Inverter | Numerical adaptive GP | 3.40077 ± 0 | 11 / 12 / 12 | 3/3 |
| Inverter | GP frozen initial range | 3.12605 ± 0 | 11 / 12 / 12 | 0/3 |
| Five-transistor OTA | Random full space | 2.91876 ± 0.00899 | 1 / 1 / 1 | Not enumerated |
| Five-transistor OTA | GP full space | 2.92907 ± 0.00173 | 1 / 1 / 1 | Not enumerated |
| Five-transistor OTA | Numerical adaptive GP | 2.93035 ± 0 | 1 / 1 / 1 | Not enumerated |
| Five-transistor OTA | GP frozen initial range | 2.91589 ± 0 | 1 / 1 / 1 | Not enumerated |

All 24 runs found a feasible candidate. On the OTA, the first common initialization
point was already feasible in every seed, so success/first-feasibility is not a
discriminating optimization metric for these starts. Quality trajectories and
evaluations-to-best are retained. With three seeds and two small tasks, these are
descriptive results, not a significance claim or a benchmark-wide ranking.

The GP engine fits actual prior valid measurements using a fixed Matérn ν=2.5
kernel, predicts mean/uncertainty over unseen discrete candidates and maximizes
UCB μ+2σ. Normalized index encoding, fixed length scale 0.35, scikit-learn,
sequential proposals and exact acquisition enumeration are explicit port choices.
No claim is made that this executes the author's scikit-optimize implementation
or exact paper baseline. The numerical adaptive arm is a new, explicitly non-LLM
policy. It retains history and updates ranges from incumbent feasibility,
improvement and boundary status; all variables remain active.

## A real outer-loop update

For inverter/adaptive/seed11, after attempt 12 the only feasible incumbent had
indices `[1,1]`, FoM 3.12605. Four of the five top designs placed the NMOS variable
at the lower initial boundary. The numerical policy changed both index ranges
from `[1,7]` to `[0,3]`, making previously excluded values available. Subsequent
simulations found `[0,0]`, FoM 3.40077. After attempt 24 it proposed `[0,2]`; that
box had no unseen points, so the explicit exhaustion guard restored `[0,8]` and
continued without duplicate evaluations or a hang. Every feedback packet, change,
candidate and actual result is retained.

This closes actual feedback-driven range adaptation, but does not establish that
the heuristic is equivalent to LLM reflection. Full-space GP achieved the same
inverter optimum, so this experiment does **not** show an adaptive advantage over
the full-space numerical control. The frozen-range gap is partly structural:
the restricted control cannot reach the full-grid optimum. It tests range recovery,
not superiority of a particular reasoning mechanism.

## Independent correctness and finite-grid check

The held-out inverter enumeration ran only after all main searches and validation
selections finished. Its 81 real simulator calls yielded 81 valid measurements and
7 feasible grid points. The best is indices `[0,0]`, base widths 0.84/0.84, actual
widths 16.8/16.8 µm, L=0.15 µm, same 10 fF load and 1.8 V supply. Its measured
gain is 23.37344 dB, average delay 20.58636 ps and integrated dynamic power
41.73267 µW; FoM 3.400767. This is the optimum only on the released discrete
inverter grid under this nominal measurement port, not a continuous or PVT optimum.
No oracle data entered any optimizer.

Each of 24 preselected main winners was resimulated with original released
measurements and with a separate exported/refined-grid measurement run: 48 actual
calls. No winner was replaced. All original and refined runs were valid and
feasible; none changed feasibility. An independent script, importing neither the
optimizer nor its scorer, recomputed all 1,029 attempted results' units, normalized
FoM and strict individual constraints from stdout/source specifications. It also
recomputed propagation edges, DC derivative gain, integrated power, AC unity
crossing and supply-current power from the 24 exported winner waveforms.
There were zero precision-edge feasibility discrepancies.

Checks also verify every deck hash, contiguous attempt debit, exactly 36 unique
points in each main run, identical initialization, GP training exclusively on
past valid observations, and post-search oracle ordering. Independent checks do
not establish the original paper's circuit definitions are globally correct;
they substantiate this port's electrical measurements and accounting.

## Cost and execution evidence

Protocol and implementation were committed before the pilot at
`118247d5917e9b7bb430f90bbe7281d17357276a`. Exact protocol/config/source hashes
and timestamps are retained. Pilot rules were not tuned after its outcomes.

* Pilot: 36 real calls; main comparison: 864; winner validation: 48; inverter
  grid oracle: 81. **Total 1,029 / 1,100 allowed calls**, zero invalid outcomes.
* Summed simulator-process wall time: 176.42 s; child CPU: 197.25 s. Main searches
  consumed 157.78 s total wall time, including 1.38 s of recorded proposal work.
* Maximum child-accounted RSS upper bound: 118,264 KiB (~115.5 MiB), including
  fork-inherited parent pages. This is an upper bound, not isolated SPICE heap use.
* The frozen phase began at 11:28:35 UTC and remained well inside its two-hour
  deadline; final analytical timestamps are in the resource ledger. Existing
  CPU/RAM/disk only; no new download, package
  installation, paid resource, pretrained-model training or model API call.
* Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0, PyYAML 6.0.3,
  threadpoolctl 3.6.0; official Debian ngspice 44.2+ds-1 and previously pinned
  official SKY130 two-device tt subset. GP fitting uses observed electrical data;
  it is not LLM training.

No failed simulation was discarded or retried. The one prior preflight
preparation-only indentation exception remains documented in the unchanged prior
phase and is not pooled into these results. Existing simulator initialization and
post-`.end` quote warnings remain in original logs; no hidden startup configuration
or account environment was loaded. Child processes use an explicit minimal
environment and resource limits. No external push or PR occurred.

## Remaining mechanism and testable gaps

**Live LLM-generated understanding and decisions remain unexecuted.** External
LLM calls are prohibited in this tranche, and the bounded asset inventory found no
approved local weights/runtime. Eight real input packets and validated decision
contracts are prepared in `controller_requests/`; `invoke_live()` fails closed.
No heuristic or synthetic contract fixture is reported as an LLM response.
[CONTROLLER_INTERFACE.md](CONTROLLER_INTERFACE.md) spells out the exact handoff,
source prompt fidelity, reduced supported algorithm pool and missing live boundary.

The affordable infrastructure is closed: real candidate evaluation, constrained
objective, persistent history, numerical acquisition updates, range feedback,
matched controls, debit accounting, independent validation and a small grid oracle.
The method-specific contribution of LLM circuit knowledge, variable fixing,
algorithm/batch orchestration and reflection still needs a separately allowed
live-model comparison on these identical interfaces and budgets. An alternative
local model would be a new backend substitution requiring its own measured study;
none was downloaded or assumed equivalent here.

Useful follow-on questions, not verified paper errors: whether LLM decisions beat
this strong full-space GP control at equal failed-attempt and inference cost;
whether benefits emerge only on harder tasks; whether freezing important variables
causes recoverable range exclusion; whether repeated range exhaustion adds overhead;
and whether paper result accounting changes when candidate attempts, unique points
and multipoint SPICE invocations are separated. Nominal feasibility does not test
PVT, mismatch, post-layout parasitics, phase margin or fabrication readiness.

The phase is closed without requesting user resources. The essential missing
permission/resource for the paper's remaining controller is an allowed live model
backend; no credential or paid-service access was probed. Full 24-task reproduction
and author-standardized comparison baselines remain outside these bounded results.
