# RQ4 protocol self-audit — before any state construction or future outcome

Audit snapshot UTC: 2026-11-02T11:28:51Z (system clock). Original protocol SHA256: `c857b6d1cde65dfc370b9c2c9adc0305d20f2509b334511ce1cb0d9d9fdff8cb`. Original status SHA256: `2c27aeb6eb1891e25fa18dba396964878f5b99b0e9d39f3f942b6b8fa65c8612`. Actual archive-screen evidence SHA256: `b275a7bf28bcef6eb20a29652f29b0fa4630628cc08f392f3b738d9229e2c26e`.

This records the first verifiable hash/time snapshot, NOT a claim that those exact bytes were timestamped when first drafted. Protocol v0 is preserved unchanged. This addendum overrides weaker interpretations and adds required controls. No RQ4 state construction, target-install run, equivalence run, or continuation outcome exists. RQ1's original-state report WAS known when v0 was written.

## Are the future targets real adaptation tasks?

They are legal constraint TYPES according to AMD 2025.1 UG835, not yet demonstrated feasible goals on this design. Source: https://docs.amd.com/r/2025.1-English/ug835-vivado-tcl-commands/set_clock_uncertainty . Installed-tool acceptance, active clock resolution, uncertainty property semantics and target feasibility remain untested. No new constraint may be called a real customer requirement: these are synthetic, engineering-motivated integration-margin scenarios. Exact magnitudes have no external system specification behind them.

**Static re-scoring is not adaptation.** Applying uniform setup uncertainty to an unchanged state can primarily subtract a common slack offset, preserving rankings. Merely reporting different future slacks or pass/fail thresholds would reproduce existing slack/headroom. It cannot establish future adaptability. The constraint must be installed BEFORE timing-driven continuation; logs and exported post-install constraints must show the optimizer consumes the same altered timing problem for both states. Preserve a physical-state signature before/after so no-op changes are not mistaken for engineering response.

Add two controls before interpreting H1:

1. Static A0 under each future target: separates mathematical re-scoring from physical intervention. Report all path/corner changes, not only WNS. If future state gaps are fully explained by static no-op scores, call the finding current headroom.
2. Original-constraint continuation C0 using the SAME panel/budgets/repeats. Re-score its resulting states under each future target without further optimization. Compare this to continuation optimized with the future target installed. Report within-state target-conditioned gain over static A0, cross-state differences in those gains, and target-aware versus original-constraint continuation. This separates generic optimizer effectiveness from target-specific adaptation. Do not infer target use merely from a command existing or from a new timing report.

If no physical change occurs, or future gaps duplicate C0/static headroom within noise, stop the future-adaptability interpretation. If target-conditioned gain differs, this is a protocol response interaction; it still need not be intrinsic global reachability or an online agent capability.

G1 is especially weak as a feasibility target: original WNS is -1.654 ns; another 0.050 ns setup margin does not plausibly turn closure into a reachable short-budget event by itself. Thus v0 can at most probe continuous timing-deficit response unless actual runs establish closure. G2 0.060 ns exceeds the observed original WHS 0.042 ns by 0.018 ns, so it may create a small hold repair problem; dedicated-path feasibility is UNKNOWN. If impossible, record failure rather than tune margin downward after outcomes. These observations are reasons to restrict claims, not evidence of adaptation.

## Why these tolerances and values?

The tolerances are declared pilot operating rules, NOT calibrated noise estimates or industry standards. 0.020 ns WNS is about 1.27% of the 1.570 ns period; 0.010 ns WHS is intentionally tighter, because the observed hold margin is only 0.042 ns. Exact resource counts reject synthesis/resource tradeoff confounding; 1% TNS/endpoints attempts to constrain broad distribution differences but does not match their full distributions. Current slack histograms, path type/corner, clock skew and high-fanout/congestion features remain necessary descriptive controls.

G1 0.050 ns is an order-of-tens-of-picoseconds setup-margin probe (~3.18% of period), not sourced integration data. G2 0.060 ns was chosen WITH KNOWLEDGE of baseline WHS, to exceed it slightly; this is explicit baseline-informed experimental design, not outcome-blind target selection from a real future-demand distribution. Neither value has been selected using results from a constructed pair or a future continuation.

Noise calibration must occur before future data. If its repeat range is too large relative to these fixed thresholds, STOP this preregistration as unmeasurable. Do not relax tolerances or increase the effect threshold after inspecting future data. Any redesign gets a new version, timestamp/hash and explicit exploratory label before further future evaluations. Matching first-passing path IDs prevents future-gap-based pair cherry-picking, but there is still current-only selection and small-sample selection uncertainty.

## Correctness: what can and cannot be guaranteed?

Same instance count, resource count, port count or nominal primitive list does NOT prove identical function. Same logical connectivity alone omits LUT INIT, FF initialization, clock/reset polarity, BRAM contents/modes, primitive parameters and black-box semantics. Generic phys_opt directives can change the logical netlist; no assumption that Default or Explore is physical-only is allowed.

Narrow initial route: same source DCP, only accept outputs whose complete logical representation is unchanged under a strictly defined semantic comparison; no retiming, LUT remapping, replication, clock rewiring or unverified parameter changes. Prefer a validated route/placement-only action if installed help and before/after checks demonstrate that scope. Its exact command is NOT yet selected or verified; do not invent an option that disables logic rewrites. If all v0 phys_opt candidates alter logic, stop or preregister a new action set before any future outcomes.

Minimum independent checker needed for this restricted claim:

- A standalone EDIF semantic comparator, independent of optimization code, covering complete hierarchy, port directions/widths and connectivity, primitive identity, all semantic properties/parameters, LUT/FF/BRAM INIT values, clock/reset/control wiring and unresolved black boxes. Reject unsupported constructs and all unclassified differences. A raw exact EDIF payload hash match is a conservative same-representation screen; differing hashes do not prove inequivalence and may force rejection. This comparator is NOT implemented/validated yet.
- Placement/routing legality plus connectivity verification: Vivado route/DRC reports are available tool checks but are not independent of the vendor toolchain. A separate RapidWright connectivity/physical-legality audit is a candidate since its installation is known, but suitable APIs and coverage have NOT been established. It is not a formal equivalence checker merely because it uses a second library.
- Where logical changes are admitted, a real sequential-equivalence flow with correct device primitive/memory models is necessary. A vendor-netlist Yosys/SymbiYosys miter or commercial equivalence tool is only a potential path; neither configured availability nor correct UltraScale+ modeling is established. Do not call this an available checker.

Exact unchanged logical semantics, routing checks and timing checks can support a narrow preservation claim conditional on primitive/tool correctness, original design correctness and frozen internal-clock contract. They do not prove full RTL-spec correctness, unconstrained-interface timing, bitstream/hardware behavior, analog signal integrity or absence of a vendor tool bug. If no independent physical checker is practical, disclose that limitation and do not label this gate independently verified end-to-end functional equivalence. Generic behavior of a checkpoint load/save is insufficient.

## Dispatch consequence

No compute request activated. Hold the 16-minute gate and continuation batch pending parent allocation and RQ1 artifacts. Added C0 controls increase the future batch from 72 to 108 action-process attempts across both budgets: 2 states * 3 conditions (original + G1 + G2) * 3 actions * 3 repeats * 2 budgets. Worst-case serial process wall is 2*3*3*3*(60+120)=9,720 s (~162 minutes), plus read-only re-scoring and independent confirmation. This supersedes v0's 108-minute estimate and is NOT approved or running. First decision is whether RQ1 produces logically unchanged, currently matched physical states at all.
