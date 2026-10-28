# PostEDA-Bench v4: calibration review

This is a bounded evaluator calibration, **not a live-agent reproduction**. Four DRC cases and two PPA cases were selected before execution. No model/API calls or paid cloud resources were used.

## Paper and release

The reviewed paper is [PostEDA-Bench, arXiv:2605.06936v4](https://arxiv.org/html/2605.06936v4), revised 7 October 2026. Its contribution is a hierarchical benchmark for post-flow DRC repair and target-constrained PPA optimization, with empirical agent comparisons. Venue acceptance and CCF classification are unverified and remain unknown.

The audited [official release](https://github.com/pengjas/posteda-bench/tree/b04e85a867e81e0817348f7b86a7ae06f83990d7) contains 145 tasks. Its [20 October environment update](https://github.com/pengjas/posteda-bench/commit/b04e85a867e81e0817348f7b86a7ae06f83990d7) changes the ORFS pin relative to the paper; paper-protocol reproduction and current-release calibration must remain distinct. Received HTML and abstract metadata also disagree on model count and the best DRC-Reasoning score, so those descriptions were not silently combined.

The contribution is principally task construction and diagnostic organization. ReAct, Reflexion, Tree-of-Thought and Bayesian knob search are reused mechanisms; target-driven optimization overlaps with the prior systems discussed by the paper. This review does not establish an exhaustive priority claim or reproduce model rankings, vision effects or causal explanations.

## DRC evidence and its limits

The four no-op cases reproduce their declared DRC counts: 1, 1, 10 and 1. Across 15 artifact controls, six outputs have zero counted DRC errors. Four of those deliberately erase the layout. The remaining two are repair candidates with **unknown electrical validity**; zero DRC errors alone is not a completed functional repair.

A separate conservative geometry policy yields 0 confirmed combined successes, 2 UNKNOWN and 13 failures. Partial and harmful controls were retained, including a partial candidate reducing 10 errors to 5 and a gate-edit candidate increasing 1 to 27. This control matrix is not a model success rate; reachability of all adversarial artifacts through the released agent tools was not demonstrated.

**v4 Appendix C.7 does describe a connectivity/device audit.** Its reported archived-corpus results are acknowledged. The pinned repository does not provide the original audit implementation and complete audited input/output pairs needed for exact replay. Our extra geometry check is not that audit, does not extract terminal nets or device censuses, and is not full LVS signoff. Electrical/C.7 verdicts remain UNKNOWN for every selected DRC control.

## PPA evidence and its limits

Both frozen cases completed actual synthesis, placement and routing through the pinned image and ORFS scripts, using an explicitly adapted rootless Podman executor. Fresh final ODBs and reports were verified, and config, SDC and RTL hashes remained unchanged.

| Case | Archived period / actual period (ps) | Archived power / actual power (W) | Archived area / actual area (µm²) |
|---|---:|---:|---:|
| PPA-Mono perf L1 q1 | 269.18 / 262.88 | 0.00133 / 0.00130 | 262.44 / 262.44 |
| PPA-Multi L1 q1 | 319.69 / 319.69 | 0.00161 / 0.00161 | 293.163 / 293.163 |

The mono period differs by approximately −2.34%; the source of this numerical drift is unresolved. Multi matches the archived values at their reported precision. Neither actual run meets its optimization target. Since no candidate optimization was applied, numerical changes must not be credited to a method or model.

Earlier deterministic RTL checks compare 500 output events per case: unchanged sources match, and a harmful output mutant mismatches all 500 events. These finite checks are bounded behavior evidence, not formal equivalence, PPA improvement or layout electrical signoff.

## Timing, runtime and interpretation

Metric targets were fixed throughout. Upstream permits SDC edits, including clock changes; a stronger invariant-clock/IO/exception audit would be a separate scientific contract, not an unstated original restriction. No edited-SDC experiment ran here.

The original batch wrapper requests privileged mode, host networking and X11 mounts. The executor adaptation removes those requests, uses networkless rootless containers, read-only flow code and a single writable task workspace, and limits execution to four CPUs. The final corrective runs use a code-only view excluding earlier workspaces. An isolation/resource probe and live descendant-process checks verified the corrected four-core restriction; original observations made before that correction remain private and are not the final table entries. The original Make, source configuration, tool image and flow algorithms are retained. Thus this is a **runtime port calibration**, not an assertion of byte-for-byte equivalence to the original Docker protocol.

The sample is purposive and too small for population estimates. The 139 unselected tasks are intentional exclusions. Exact paper-protocol evaluation, live-agent experiments and original C.7 replay remain not_run. Private commands, unsuccessful attempts, artifact hashes and raw evidence are retained for independent review; they are excluded from this publication candidate.
