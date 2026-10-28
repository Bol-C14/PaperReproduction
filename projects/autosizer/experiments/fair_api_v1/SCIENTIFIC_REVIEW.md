# Independent scientific review of the completed bridge pilot

This is a targeted read-only review, not a new experimental run. Existing evidence
is the 53-measurement bridge stage. No new simulator or API calls occurred here.
Old protocol/source/results are unchanged. The new fair protocol remains a draft.

## Fairness finding

The former test-controller arm began on indices 1..7 while the independent GP
control began on 0..8. Both used seed 11, but different candidate lists create
different initial points and observed data. Consequently the reported first
feasibility 13 versus 1 is confounded by initialization/domain prior and is not an
estimate of model guidance. Both ultimately selected [0,0]; equal final values
also do not prove equivalence. Further, the former controller was synthetic,
not a live model. The old report correctly labels these as integration controls.

The next draft removes those factors: identical full initial domain, one immutable
shared ten-measurement dataset, identical numerical engine/hyperparameters and
24 new charged SPICE attempts per arm. Model-guided domain/method decisions are
the only assigned difference after initialization. Total search physical calls
are 58, not 68: common measurements occur once. Each arm sees 34 observations.
This isolates the bundled guidance policy, not individual understanding/reflection
components. Stop/failure cannot be repaired by fabricated filler while claiming
a matched budget. Planning helpers have no execution route.

## Unit and parsing evidence

| Quantity | Preserved source/raw meaning | Conversion / strict check |
|---|---|---|
| `dc_gain_db` | max 20 log10(abs(dVout/dVin)) | already dB, >20 |
| `average_delay` | mean of opposite-edge paired 0.9 V delays | seconds x 1e12 = ps, <50 |
| `dynamic_power_timeweighted` | abs(0..4 ns mean supply power minus static power) | W x 1e6 = uW, <50 |
| `static_power_abs` | abs(mean supply current in 10..90 ps) x 1.8 V | W; new check reconstructs directly from supply-power vectors |
| normalized FoM | `(gain_dB/20)/((delay_ps/50)*(power_uW/50))` | dimensionless target normalization, >1 plus every individual check |
| YAML fallback FoM | `gain_dB/(delay_ps*power_uW)` | retained separately; factor 125 differs from normalized FoM |
| transistor widths | 20 x released base value; `.option scale=1e-6` | physical width in um; index [0,0] =>16.8/16.8 um, not 0.84 um |

`METRIC_REVIEW.json` re-parses **four representative existing** raw logs
(source center, corrected center, refined center, refined selected winner) with
an independent parser and strict-score implementation, not bridge/engine imports.
It supports E/e scientific notation, applies seconds/W scaling and rejects missing
or nonfinite measurements. Every parsed metric and feasibility agrees with the
archived record. This is a small targeted check rather than another 53-run sweep.

The previous four corrected/refined waveform checks independently reconstructed
gain/delay/dynamic power, but their static-power subtraction consumed the parsed
attempt JSON static value. The added check instead clips/interpolates the exported
waveform exactly at 10 and 90 ps, integrates static power there, independently
integrates 0..4 ns supply power, then subtracts. Three representative corrected/
refined exports agree with logged dynamic power within 0.001 uW and with the
recorded static term within 1e-14 W. Existing delay/gain waveform checks remain
valid; their static-term dependency is now explicitly documented and checked.

At the center, source sample-mean power is 66.28517 uW and corrected integral-mean
power is 65.82583 uW. Both violate <50 uW despite normalized FoM >1. Corrected
paired-edge delay (~18.41647 ps) is close to source average (~18.41635 ps) here:
these data do not show a catastrophic original averaged-delay error. Explicit
opposite-edge pairing clarifies edge identity; the time-weighted power port is an
actual measurement-definition change. Both are disclosed substitutions and must
be identical in the next arms. The old pilot does not validate all 24 source tasks.

The refined selected winner independently satisfies all strict constraints.
Numerical agreement for these exports is evidence of parser/unit consistency,
not fabrication-process accuracy, statistical superiority or model understanding.
The tt-only subset, ideal pre-layout netlist, corrected measurement port, fixed
scikit-learn GP port and any future API model replacement remain named limits.
