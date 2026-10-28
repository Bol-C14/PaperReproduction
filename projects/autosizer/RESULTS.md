# P08 bounded measurement preflight — completed

Six simulator attempts completed; no further simulations are authorized by this phase.
The fixed five-transistor OTA point meets its released nominal constraints. The fixed
inverter point fails its unchanged power limit under both original and time-integrated
measurements. This validates a small simulator/measurement route; **AutoSizer's LLM
controller, numerical optimization and outer reflection mechanism have not been run**.

## Fixed-point outcomes

All cases use official SKY130 nfet_01v8/pfet_01v8 tt models at 27°C, VDD=1.8 V,
with the source topology, source load and frozen midpoint widths. “Original” means
original released measurement commands in the documented PDK-subset port; it does
not mean the authors' complete execution environment was recovered. No dimension,
load, bias or specification was tuned to get a pass.

| Circuit / measurement | Gain dB | Delay ps | UGBW MHz | Power µW | Normalized FoM | Outcome |
|---|---:|---:|---:|---:|---:|---|
| Inverter original | 23.81905 | 18.41635 | — | 66.28517 | 2.43902 | Infeasible: power must be <50 |
| Inverter paired edges + same original sample-mean power | 23.81905 | 18.41647 | — | 66.28517 | 2.43900 | Infeasible |
| Inverter paired edges + time-integrated power | 23.81905 | 18.41647 | — | 65.82582 | 2.45602 | Infeasible |
| Inverter diagnostic 0.5 ps maximum step + integrated power | 23.81905 | 18.41864 | — | 65.81266 | 2.45622 | Infeasible |
| Five-transistor OTA original | 18.01931 | — | 21.32281 | 57.53192 | 2.89398 | Feasible at this nominal point |
| OTA original analysis + exported-vector cross-check | 18.01931 | — | 21.32281 | 57.53192 | 2.89398 | Feasible |
| OTA diagnostic 200 AC points/decade | 18.01931 | — | 21.32250 | 57.53192 | 2.89394 | Feasible |

Seven table rows describe six processes: inverter paired-edge and integrated-power
views come from the same attempt 3. The grid refinements are diagnostics, not
additional optimized designs or benchmark-success trials. Constraints were frozen
in [PROTOCOL.md](PROTOCOL.md) and remain unchanged.

The OTA exported operating point is VOUT=1.172088 V, differential-pair source
0.2650952 V, mirror diode node 1.172088 V and supply current −31.9622 µA. The source
20 µA bias reference and 1 pF load remain intact. This establishes one nominal
operating point, not stability, mismatch yield, PVT robustness or layout closure.

## What the comparison establishes

**The suspected inverter edge-pairing error did not materialize at this point.**
Static review initially flagged the misleading `rise`/`fall` variable names.
Runtime evidence shows that `CROSS=1/2` already chooses the appropriate opposite
response edges for the frozen waveform. Explicit TRIG/RISE/FALL pairing gives
tPHL=10.79267 ps and tPLH=26.04027 ps; the average agrees with the original to
0.00012 ps, within printed-value rounding. The source names interchange the edge
interpretations, but claiming an incorrect average delay here would be unsupported.
The initial suspicion and unchanged original outcomes remain preserved.

**A small power-measurement definition difference is verified.** `mean(power)`
averages values on adaptive sample times, rather than weighting by time. At the
source grid it produces 66.28517 µW; integrating the same waveform over the same
0–4 ns window, subtracting the same low-state static-power estimate, gives
65.825823 µW, about 0.70% lower. ngspice's AVG measurement independently agrees
with Python trapezoidal integration within 0.000007 µW. With a 0.5 ps maximum step,
integrated power changes by about 0.020%, whereas the sample-mean value moves by
about 0.345%. Neither definition passes 50 µW. This does not establish a large
paper-level result error or a failure of the LLM method.

**The OTA measurements cross-check.** Exported AC magnitude gives 18.019307 dB
at 1 Hz and an independently interpolated first downward unity crossing of
21.322814 MHz, matching original printed values. Doubling AC resolution changes
UGBW by about 0.0015%. Supply-current×VDD agrees with source power to displayed
precision. No measurement repair was needed on this task at the fixed point.

**FoM definitions must stay explicit.** At the inverter point the source YAML
fallback gives 0.0195121, while the controller's target-normalized definition gives
2.439015; at the OTA point they give 6.67842 and 2.89398, respectively. For fixed
positive targets these are constant rescalings within each circuit, preserving
within-circuit objective ranking but changing the fixed FoM constraint and
cross-circuit aggregates. The upstream controller normally regenerates normalized
FoM; it was not invoked here. Both formula outcomes and every individual threshold
are retained. The inverter remains infeasible even with a normalized FoM >1.

## Original, port and local additions

* Original: unchanged released circuit YAML files, device dimensions, supply/bias,
  waveforms, loads, original measurements and their outputs. Hashes match the
  audited AutoSizer commit `1b9b8f6498e2c7ad3b650bbbc78c8e3b0e1205e1`.
* Port: official Debian ngspice 44.2+ds-1 locally extracted; official SKY130
  `f62031a1be9aefe902d6d54cddd6f59b57627436` two-device tt dependency subset,
  original model bodies unchanged; a visible local library selector preserves
  upstream scale/global parameters and freezes simulation temperature. This is
  not a full installed PDK, layout stack, or generic replacement transistor model.
* Local additions: bounded execution/logging harness, explicit edge pairing,
  same-window time-integrated power, raw-vector cross-checks, diagnostic resolution
  changes, error taxonomy and resource ledger. These are measurement/software
  preflight additions, not new AutoSizer algorithms, training data or novel labels.

## Validation, costs and limits

Debian InRelease signatures were verified using the installed archive keyring;
the signed index hash and package hash matched before binary execution. Models
came from the official public repository at an immutable commit and retain its
Apache-2.0 license. No license gate or unrecognized software installation was
needed. No system packages, global settings or credentials were changed.

Eight offline synthetic software checks verify model/include errors, exit-zero
solver/control errors, missing measurements and infeasible-versus-feasible
classification. Reclassification of all six actual logs agrees with their recorded
outcomes. Synthetic checks are not electrical results. No invalid circuit outcome
was replaced with a label. One harness-only indentation mismatch was corrected
before attempt 3; it launched no simulator.

Warnings are retained: the extracted simulator could not locate its system `spinit`
file and ran with no compatibility mode; `-n` prevents loading user startup files.
The inverter YAML also contains a trailing triple-quote line after `.end`, which
caused an unusual-leading-character warning. Neither warning prevented the logged
analyses or independent vector agreement. They were not silently removed from the
original deck. No extrapolation to other circuits or simulator versions is justified.

Resource ledger: 6/20 simulator attempts, 1.074 s summed simulator-process wall
time, 2.082 s reported child CPU time, peak child RSS 21,084 KiB (~20.6 MiB).
Successful HTTP bodies totaled 16,126,417 bytes (~15.4 MiB). Git/header transfer
overhead was not byte-metered; adding a conservative 64 MiB allowance keeps the
accounted download envelope below 84 MB, far below 2 GB. The declared setup/
diagnosis clock was about 10.1 minutes, plus a short initial repository inspection
and later documentation, well below two hours. Zero paid resources, GPUs,
training, optimizer sweeps or LLM/API calls. Python 3.12.14, NumPy 2.3.5 and
PyYAML 6.0.3 were already installed; no pip installation occurred.

All work is local on `reproduction/autosizer-icml2026`, under `projects/autosizer`.
The inherited Aspen files are unchanged and the paused remote branches were not
modified. The protocol was committed before simulation. [COMMANDS.md](COMMANDS.md)
records setup, source validation, execution and read-only checks; `logs/` retains
all decks/stdout/stderr/raw vectors; `results/` holds machine-readable checks and
resource accounting. `PHASE_CLOSED.json` blocks accidental further runs.

## Remaining gaps and decision for the parent

No additional user-provided compute, payment or credential resource was needed for
this phase. The cheap simulator/PDK route is now concrete for these two tasks.
**Go only for planning a separately bounded next phase**, with measurement
definitions frozen; no next phase has started. The LLM outer controller, numerical
search, range regeneration, algorithm scheduling and claimed 24-task success all
remain untested. A no-LLM numerical baseline could later use this measurement route,
but it would not itself reproduce the reflective mechanism.

The complete paper comparison still needs the authors' exact baseline runners,
task/protocol clarification for the hard circuits, and substantially more integration
and evaluation work; the full-route L3 assessment remains provisional. Author
artifacts could reduce that cost. Original model endpoint access is still unknown
and was neither requested nor probed. No paid/API resource is requested now. The
parent decides any new experiment budget or controller/backend substitution.
