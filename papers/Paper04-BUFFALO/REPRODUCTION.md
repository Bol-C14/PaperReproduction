# Paper04 BUFFALO — behavioral pilot and evidence audit

**Outcome: Partial module reproduction; Go for a free, actual-STA pipeline; No-Go for claims about trained BUFFALO, GRPO gains or original numerical performance.** Updated 2026-10-27 UTC. No paid API, model call, training, push or PR.

## Primary source and scope

[Official NVIDIA record](https://research.nvidia.com/labs/electronic-design-automation/publication/lu2025buffalo/) identifies Hao-Hsiang Hsiao, Yi-Chen Lu, Sung Kyu Lim and Haoxing Ren, ICCAD 2025. [Coauthor Georgia Tech preprint](https://gtcad.gatech.edu/www/papers/Hsiao-ICCAD25.pdf) was independently read through the web PDF tool: all nine pages, including algorithms, tables, figures and references. There is no appendix in that file; no separate supplement was located. Shell downloads of both PDF hosts returned 403; the successful web reading does not imply locally acquired PDF bytes. Parent supplied SHA-256 `53cc13ee307ac305b3bc641eda95ea771346d69d58d74002a1df7cc61d45b3ab`, size 2,242,970 bytes, creation Sep 3 2025: **parent-reported provenance, not independently byte-verified here**. We do not have the final IEEE version or a confirmed release license for redistributing the paper, so no full paper is bundled.

The problem is data-net interconnect buffering: source and sinks with electrical/physical context map to a whole buffer tree, including topology, buffer cells and locations (Sections III A–D, pp3–5). It targets high-fanout and timing-critical nets, then evaluates in a full-chip placement flow. This is not a clock-tree/skew synthesis task. The source's single-shot description means one complete sequence generation rather than incremental level-by-level rebuilding; it still uses autoregressive decoding steps.

## What actually ran

An OpenTimer 2.1.0 executable was built from inspected MIT-licensed source, commit `cd0565fc7a720368e75751c717be92d76350ee8d`. The ASAP7 RVT TT INVBUF NLDM library came from inspected OpenSTA commit `384b539085c54eef46cbaa02e2e17d2b983247e5`, with its BSD notice retained. OpenSTA itself was not built: its dependencies were missing and the configured APT snapshot index returned proxy 403. OpenROAD was not installed. OpenTimer provided the actual free STA evaluator; it is not a substitute for INSTA or commercial physical sign-off.

Three cases: two deliberately synthetic 12-sink geometry fixtures, and one actual AES mapped-net cut (`_08638_`, driver `_16685_`, all ten sink connections retained). The AES cut's original connectivity/cell types are real; placement, wire model, input transition and required arrival are local assumptions, and downstream context is cut. This does not reproduce a placed AES design or original test distribution.

For each case: one unbuffered reference, eight geometry-aware tree candidates, eight randomized-partition/location candidates. Both methods use identical per-index branching factors, buffer counts and library cell sizes. There are **51 comparison STA invocations**, plus one failed ANSI-netlist smoke, one corrected smoke and one RC control: **54 actual engine invocations overall**. An earlier attempt before linking launched no engine and is separately logged. All outcomes, including invalid reference nets and failed setup, are retained. No broad sweep.

| Behavior claim | Status | Go/No-Go and evidence |
|---|---|---|
| Primary preprint read and problem boundary | Replicated | Go: nine-page web reading; `EVIDENCE_AUDIT.md` maps sections |
| Full-tree DFS brackets + factorized cell type/size | Partial | Go: round-trip on all candidates; explicit ID/coordinate sidecars are local conventions |
| Buffer-size-position coordinate mask | Partial | Go: coordinates only on buffer size positions; no learned location head |
| Structural legality, sink coverage, library cells, fanout/cap/output-slew | Partial | Go for declared fixture rules; no LEF/site/obstacle/routing legality |
| Real library/RC timing feedback | Replicated locally | Go: actual OpenTimer NLDM/SPEF reports + RC sensitivity; not INSTA equivalence |
| Geometry prior / best-of-N without learning | Replicated locally | Go for these cases only: equal eight-candidate/eight-STA budgets |
| PPA control | Partial | Weight-dependent selection from a fixed evaluated pool, not conditioned generation |
| GRAE and illegality penalty arithmetic | Partial | Numerical audit only; published mean-sign ambiguity preserved |
| T5 architecture/SFT | Not | No-Go: no checkpoint/labels/training; zero steps |
| Net-level GRPO policy updates | Not | No-Go: zero updates; arithmetic is not RL |
| Full-chip feedback / INSTA selection | Not | No-Go: no full-chip model, gradient or integration flow |
| Actual power / legalized or routed PPA | Not | No-Go: buffer area and estimated RC are not measured power or sign-off |
| Original speedup / PPA values | Not | No-Go: original numbers separated from local metrics |

## Input, output and evaluator contract

`config/{clustered,spread,aes_cut}.json` define fixed source/sinks and coordinates in a 100×100 um box, 10 ps input slew, a 100 ps virtual boundary clock and 80 ps output required arrival, 0.5 fF output loads, max fanout 4, 320 ps declared cell-output-slew limit, three allowed non-inverting BUF sizes. Library pin capacitances/maximum capacitance/areas are parsed from the actual liberty file. The virtual clock supplies input/output timing references only; no clock distribution is optimized.

Outputs are decoded rooted trees, factorized DFS sequences with aligned IDs and buffer-size coordinates, Verilog instances, SDC, and SPEF. Recursively bracketed decoding guarantees connected nesting and acyclicity; unique IDs and exactly-once fixed sinks prevent graph aliasing/omission. Cell choices retain non-inverting function. The pilot deliberately accepts nested buffers as in the paper's examples, while flagging the inconsistent load-only-groups prose separately. Coordinates are bounds-checked, not physically legalized.

Wires are independent Manhattan-distance star branches within each driven net, modeled as pi RC with **assumed** 0.5 ohm/um and 0.15 fF/um. There is no shared Steiner routing, congestion, extraction or placement density. OpenTimer computes rise/fall propagation through the real NLDM cell tables and SPEF; metrics aggregate each output's worst max rise/fall arrival. Local TNS is `sum(min(0, 80ps − arrival_i))`; WNS is the worst such slack. The fixed source/sink cell arcs are included; inserted-buffer area excludes source/sinks. This is endpoint-cut STA, not full-chip TNS. Timing violations remain even where the declared fanout, summed capacitance and cell-output-slew checks pass. Cell A input-pin slews were not queried; this is not complete electrical legality.

## Results and practical limit

All 48 buffered candidates passed the declared structural, fanout, capacitance and Y-output-slew checks; all three unbuffered references violated fanout/capacitance/output-slew. **None of the 48 buffered candidates met timing.** A legal tree is not necessarily a timing-feasible solution. The best timing candidate from the geometry prior beat best-of-eight random on all three cases, but area differs between best-timing selections on the synthetic fixtures. The synthetic-case best-of-eight geometry selections have more area than random; the AES best-of-eight selections have equal area. No Pareto-dominance claim is made. Per-index comparisons have matched buffer area/count. See `BASELINE_COMPARISON.md`, `metrics/candidates.csv` and actual raw engine reports.

The RC control changed worst arrival from 508.202 ps to 53.2848 ps, demonstrating that the engine consumed the parasitic model; it does not validate the assumed RC against silicon. OpenTimer logs a warning about a `normalized_voltage` LUT template; scalar timing paths are populated and all successful runs have no engine error lines. No cross-engine agreement or power validation was done.

## Recompute and inspect

Exact build/recompute commands and pins are in `COMMANDS.md`. After tools are built:

```sh
python3 papers/Paper04-BUFFALO/src/pilot.py --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell
python3 papers/Paper04-BUFFALO/src/pilot.py --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell --net aes_cut
python3 papers/Paper04-BUFFALO/src/audit_reward.py
MPLCONFIGDIR=/tmp/buffalo-matplotlib python3 papers/Paper04-BUFFALO/src/summarize.py
```

The ZIP contains enough to recalculate metrics/plots without STA or network, and a source bundle for building the exact MIT STA engine offline. It does not ship an untraceable binary. Wall times may change on replay. Seeds are fixed; there is no independent generalization test. These cases were engineering validation cases, not a train/test split. Teacher data cost, held-out family leakage, real power and original trained mechanisms remain unverified.

## Repository

Existing branch `reproduction/buffalo-iccad2025` and original audit commit are preserved. The provided checkout initially had no commits or files and remote HEAD could not be fetched. Consequently this branch has a local root commit, not a verified upstream ancestry. Do not overwrite another reproduction branch when integrating its bundle. Other paper content was not present or modified. The first blocked-checkpoint observations remain historical evidence; this document supersedes its conclusions after the independent source became readable.

## Configuration consistency closeout

SDC emission now reads period, input slew, optional input delay (default0) and output load from the fixture, deriving `output_delay = period_ps − required_ps`; scoring uses that same `required_ps` through `timing_metrics`. Fanout validation reads `max_fanout`. No additional STA or sweep ran. A nondefault configuration test uses137.5ps period,96.25ps required time,7.25ps input delay,13.75ps input slew and1.25fF load, and checks emitted41.25ps output delay against scoring. All153 archived default Verilog/SDC/SPEF input files remain byte-identical, and all51 archived metric/tree checks still pass. See `logs/config-contract.stdout.json`. The legacy `max_slew_ps` metric and `max_transition` violation label refer only to observed Y output pins, not complete pin-wise electrical legality.

## Bounded feasibility follow-up (2026-10-28)

See [FEASIBILITY_DIAGNOSIS.md](FEASIBILITY_DIAGNOSIS.md). Exactly9 predeclared configurations (three archived baseline replays plus two shallow x8 alternatives per net) were evaluated, separately from the original matched-budget comparison. All9 pass declared structural/cap/fanout and newly measured A/Y-slew checks, with no tool/constraint-contract errors, but all9 still violate80ps timing. Near-source shallow alternatives reduce worst arrival to115–131ps. These measurements improve on the selected baseline, not establish optimality, general Pareto dominance or infeasibility. Earlier Y-only data and the original51-case comparison remain unchanged. SFT/netGRPO/fullchip/power/physical claims remain Not.

## Provenance and local envelope follow-up

[PROVENANCE_AND_ENVELOPE.md](PROVENANCE_AND_ENVELOPE.md) establishes that80ps, input slew, cut output load and RC are local assumptions, not paper/artifact targets. Independent old-log checks find no unit/path mismatch but identify .5fF terminal-load extrapolation below the1.44fF Liberty grid. Twelve predeclared STA calls preserve a before/after replay and evaluate three same-boundary corrected-load actions per net. All actual targets remain80ps. Corrected results expose smaller/slower versus larger/faster choices; Pareto status is per-net/per-load and pairs area/delay from the same implementation. All actual runs still violate80ps. Relaxed target-grid arithmetic is explicitly counterfactual, not paper reproduction. No APIs, model training, paid resources or new physical claims. Old evidence and v3 remain preserved.
