# Bounded three-net feasibility diagnosis — 2026-10-28

**Outcome: nine genuine timing failures under the unchanged declared model; no observed connectivity, library, tool, timing-contract or declared A/Y-slew failures. This is not an infeasibility proof.** The new evidence remains a partial STA module reproduction, not SFT/GRPO or full-chip BUFFALO.

## Predeclared scope and retained evidence

`config/feasibility_plan.json` was written before new evaluations. Each of the three existing cases receives exactly one replay of its archived `geometric-3` baseline plus two fixed legal alternatives, **nine configurations and nine actual STA processes total**. No post-feedback proposal, retries or sweep. Source/sinks, all existing RC, corner, delay targets, input transitions, output loads and fanout/cap limits remain fixed. No driver resizing or timing relaxation.

Each alternative is shallow: sort sinks by y then x, partition into groups of at most four, insert one allowed BUFx8 per group. Buffer coordinates lie10% or50% from the source toward the group centroid, rounded to integers. Both are declared in advance. These alternatives jointly change depth, grouping, size and placement; they do not isolate those contributions.

Old 51-comparison data, its48 buffered candidates and all prior logs remain unchanged. A v2 ZIP copy is preserved outside the repository at `/workspace/buffalo-iccad2025-v2-preserved.zip`, SHA256 `366fc69f8c6d084a3e8a85cf83e9fd8445f094806b6b737d86a5cbe0947cd319`. The original v2 commit and Library history remain preserved. Earlier Y-only observations are not retroactively upgraded.

## Measured results

All rows below have tool-reported required time80ps. Local TNS sums endpoint worst-rise/fall negative slacks. Area counts inserted buffers in library units. All9 rows remain timing-violating; all9 pass the declared structural/fanout/capacitance/bounds checks and newly observed A-input/Y-output slew≤320ps checks.

| Case | Fixed configuration | Worst arrival ps | TNS ps | Buffer area | Max A slew ps | Max Y slew ps |
|---|---|---:|---:|---:|---:|---:|
| clustered | archived geometric3 | 191.883 | -1279.533 | 1.63296 | 153.110 | 153.109 |
| clustered | shallow x8,10% | 131.101 | -552.553 | .52488 | 84.397 | 84.395 |
| clustered | shallow x8,50% | 163.289 | -984.448 | .52488 | 112.817 | 112.817 |
| spread | archived geometric3 | 195.761 | -1293.173 | 1.63296 | 114.360 | 114.359 |
| spread | shallow x8,10% | 116.754 | -382.177 | .52488 | 64.197 | 64.194 |
| spread | shallow x8,50% | 147.891 | -780.864 | .52488 | 93.154 | 93.154 |
| AEScut | archived geometric3 | 193.078 | -952.391 | 1.16640 | 103.851 | 103.851 |
| AEScut | shallow x8,10% | 114.709 | -240.763 | .52488 | 64.175 | 64.172 |
| AEScut | shallow x8,50% | 141.291 | -540.476 | .52488 | 82.685 | 82.685 |

Full unrounded observations and classified outcomes are under `runs/feasibility`, `metrics/feasibility.json` and `feasibility.csv`. The displayed slew decimals are regenerated from the metrics by the diagnostic closeout process; the raw values are authoritative.

## Error categories versus timing failures

- **Connectivity:** round-trip nested trees, unique IDs, source-rooted node/edge counts, complete unchanged sink coverage all pass. No connection/cycle/sink errors observed.
- **Library:** all cell choices come from the inspected allowed library; source and sink cells/pins retained; no missing-cell errors observed.
- **Declared constraints:** bounds,fanout and summed pin+wire capacitance pass. Newly queried A/Y rise/fall slews pass320ps. Tool-required output times equal the80ps configuration, and tool slacks agree with required-minus-arrival within report rounding. No contract mismatch observed.
- **Tool:** nine return codes0, finite complete query outputs, empty stderr and no engine E-lines. The previously documented normalized_voltage template warning remains; no independent STA cross-calibration is implied.
- **Timing:** nine negativeTNS/WNS outcomes persist after the checks above. These are actual model-evaluated failures, not parser failures or incorrectly scored constraints.

The new A/Y observations cover only these nine configurations, not the other prior candidates. Passing these declared checks still does not establish physical or complete electrical legality: no site/overlap/obstacle/router/hold/multicorner/power validation exists.

## Delay diagnosis and interpretation

Critical-path cell delay totals range roughly114–195ps; explicit wire propagation sums are below0.7ps in all9 cases. **This does not mean interconnect is irrelevant**: wire capacitance loads cell outputs, and its effect is included in the cell arc delay. Earlier RC-removal control showed a large change in arrival. Weak fixed BUFx2 source loading plus buffer depth/size and the assumed long-wire capacitance remain important under this model.

Moving shallow buffers near the source shifts more long-wire load onto stronger x8 buffers and removes stages relative to the chosen baseline. This is consistent with the observed lower source delay and shorter path, but placement/depth/size/grouping changed jointly, so no causal separation is claimed. The10% alternative improves both timing and inserted area over its specific archived baseline in all three cases; it does not prove a global Pareto frontier, optimality or the original paper's learning mechanism.

The new best arrivals115–131ps exceed80ps. Nine bounded failures cannot establish that80ps is impossible. Likewise the original48 failures cannot establish an infeasible problem: these two additional predeclared priors substantially improve the results. A stronger proof would require a validated lower bound or more exact optimization, neither authorized nor performed here. No new sweep is proposed.

## Costs, verification and blockers

Nine additional STA calls used about0.492s aggregate process wall time; no model/API calls, training, paid compute or physical runs. Prior54 actual engine invocations are preserved, making63 overall. Original51 comparison calls remain a distinct budget; these9 are follow-up diagnostics and must not be folded into its matched-eight comparison.

`src/verify_feasibility.py` independently rechecks all9 raw query outputs, contracts, structural outcomes and exact agreement of the three baseline replays with old metrics. `src/verify_archived.py` still rechecks all51 original cases. Both pass with zero further STA. The predeclared plan hash is stored in the diagnostic metrics. Exact command:

```sh
python3 papers/Paper04-BUFFALO/src/diagnose_feasibility.py --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell
python3 papers/Paper04-BUFFALO/src/verify_feasibility.py
```

The evaluator refuses to overwrite an existing diagnosis result; no rerun occurred. There is no execution blocker for this bounded diagnosis. Remaining limitations are unchanged: no verified BUFFALO checkpoint/labels, no SFT/netGRPO/fullchip feedback, assumed geometry/cut timing, no real power or physical closure, and no infeasibility/optimality proof. Credentials were not read, transmitted, persisted or used.
