# Evidence and methodological audit

Status labels distinguish inspected descriptions, executed local modules and unexecuted paper claims. The nine-page [Georgia Tech author preprint](https://gtcad.gatech.edu/www/papers/Hsiao-ICCAD25.pdf) was read end to end via web PDF extraction; pages 5 and 8 were also requested as rendered pages. No standalone appendix was present. No final IEEE text or original training artifacts were acquired. Primary publication identity also matches the NVIDIA official record. See source provenance and byte-verification limitations in REPRODUCTION.md.

## Source-to-mechanism map

| Source | Confirmed description | Local execution |
|---|---|---|
| pp1–2, Fig1/Table I | Whole-tree sequence model, T5-Large, commercial-label dataset, net and chip refinement | Static audit only |
| p3, III A, Table II | >20M unbuffered/buffered pairs; ASAP7; fanout 1–100, delay 100ps–1ns; commercial labeling | Not; two fixtures plus one actual-net connectivity cut |
| p3, III B, Figs3–4/Table III | Factorized gate type/size; brackets; aligned physical/electrical cell/pin features | Partial token format; no attention/embedding implementation |
| p4, III B–C, Alg1/Eq1 | Structural and coordinate heads; masked squared location loss at buffer-size positions | Coordinate mask in serialization only; zero training |
| pp4–5, III D, Alg2/Eqs2–5 | Objective-wise normalization, weighted timing/area advantage, legality penalty, clipping and KL | Arithmetic audit only; no sampled policy or gradients |
| pp5–6, III E/Alg3 | INSTA.netGrad critical-net selection; fullSTA/global feedback | Not |
| p6 IV A–D | SFT training trajectory, 20M and six days; GRPO G=10, batch16, lr1e-4, KL .04, ~5s/batch; commercial proxy check | Not replicated; costs segregated |
| p7 IV E | 83× on a representative 50-sink net, 0.5–1s generation vs30–43s commercial buffering | Not full-chip speedup; no local speedup comparison |
| p8 Table IV, V/VI | Nine ASAP7 benchmarks, SFT and GRPO, same selected nets/downstream optimization | Transcribed and arithmetically audited only |
| p9 | References; OpenPhySyn comparator implementation identified | No authors' BUFFALO code/checkpoint link found |

## Artifacts and licenses

The official NVIDIA page links a preprint, not source/checkpoints. Full-paper links/references and bounded exact-title web searches did not reveal an official BUFFALO release. Connected GitHub repository searches `BUFFALO "buffer" "GRPO"` and `BUFFALO "buffer tree"` each returned zero repositories. This is **not proof that no artifact exists**. No BUFFALO license, teacher dataset, checkpoint, custom tokenizer, training config, `bufferOpt.tcl`, INSTA integration or full-chip export scripts were established; they remain No-Go.

OpenTimer source commit `cd0565fc7a720368e75751c717be92d76350ee8d`, MIT, was inspected before its local CMake build. OpenSTA source commit `384b539085c54eef46cbaa02e2e17d2b983247e5`, GPLv3, was inspected but not executed. Its ASAP7 NLDM test library has its own explicit BSD3 header, retained verbatim in the distributed compressed library. No Nangate file was used after its header revealed separate restrictions. Source bundle/licenses/hashes and acquisition/build logs are included. No paper PDF or proprietary labels are redistributed.

## Audit findings: ambiguities, not accusations about unpublished code

1. **Grammar conflict (pp2–3 examples vs p5 III D).** Nested buffers appear in the DFS examples, yet load-only-groups legality prose excludes buffers inside parentheses. Applying that literally rejects illustrated trees. The pilot explicitly implements nested rooted trees; it cannot claim exact inference-mask equivalence. A complete grammar, root exception and sink-identity encoding need code/author clarification.
2. **Area centering (Eq2 vs Alg2 lines13/16).** The pseudocode computes mean of positive area increases then subtracts it from negative area, which fails zero-mean normalization. `metrics/reward_audit.json` shows that literal interpretation gives legal scores about −25.72 and −26.94, while an invalid output receives −3 and becomes preferred for area-only weight. Correctly centering the negative-area objective yields +1.2247 and 0 for the legal outputs. This is a reproducible textual ambiguity; the authors may have implemented the intended centered version. Zero-variance groups also lack an explicit rule; the pilot declares a zero contribution guard.
3. **KL notation (Eq5).** Expectation under the reference policy of log(reference/current) corresponds to reverse direction from its displayed KL label. Without code, the actual regularizer/sampling approximation is unresolved.
4. **Coordinate RL gradient.** Coordinates come from a regression head, but Alg2's policy likelihood is expressed over token outputs. Sampling distribution/log-probability and reward-gradient treatment for coordinates are unspecified. We do not invent them.
5. **Per-net versus chip grouping.** Alg2 groups alternative trees for the same net. Alg3 instead lists one output per selected net then normalizes over selected nets. How alternatives and combined full-chip insertions are grouped/evaluated is unclear. A net-local scalar experiment cannot verify chip-level credit assignment.
6. **Reported version issues.** Full-chip sections V and VI duplicate one another; discussion points at Table I although the numeric table is IV. Abstract states about71% TNS, conclusion77.7%; Table IV's rounded numbers give maximum about71.10%. These may be preprint editing/version issues. Final IEEE comparison is unavailable, so preserve this provenance instead of claiming final-paper errors.
7. **Metrics differ.** Table IV has higher GRPO power than commercial in five of nine rows and worse WNS for pci_bridge32, despite better TNS. Fig10 reports positive TNS/WNS values and zero TNS alongside WNS3ps, leaving sign/violation conventions unclear there. Original numbers are retained without forcing consistency.
8. **Reproducibility gaps.** Data family split/deduplication, teacher generation cost, SFT optimizer/epochs/exact batch scheduling, masks, all clipping values, random seeds, physical constraints/export and commercial tool versions are not sufficient to reconstruct the full system. The cluster description reports 8 A100 with96GB each; this is transcribed as reported, not independently hardware-verified. Six days is not automatically 1,152 fully utilized GPU-hours.

## Attribution limits

SFT versus GRPO in Table IV provides evidence consistent with refinement helping TNS, but combines learned priors, model/representation, data scale and both net/chip feedback. There is no matched-budget ablation that separately identifies serialization, pretraining, commercial teacher quality, 20M examples, RL, or additional evaluator/search budget. Treating a teacher heuristic as an upper bound on a learned method is not generally a mathematical guarantee: surrogate loss and task metrics differ. The BufFormer comparison uses an algorithmic proxy rather than directly reproducing the trained model; this distinction matters.

PPA configurability is implemented through weighted objectives; the manuscript does not establish a fully specified inference-time conditional-preference token interface. Varying weights in fixed-pool selection here is a baseline behavior, not learned conditional generation. Area is a proxy and cannot guarantee power ordering. Timing/area weighting does not imply all objectives improve together or guarantee Pareto coverage.

## Constraints and evaluator coverage

Locally checked: parsed nesting, driver identity/cell, allowed factorized type/size pair, each fixed sink once, no sink children, nonempty internal groups, unique node IDs, source-rooted connection structure, coordinate bounds, maxfanout4, actual library summed pin+wire capacitance, declared computed cell Y output-slew320ps limit. Cell A input-pin slew was not observed. Seven malformed/constraint mutations were rejected. Tree nesting prevents cycles by construction; arbitrary cyclic Python object graphs are not an accepted parser input. Nested IDs and geometry are carried by explicit local sidecars, not claimed to be exact author encodings.

Not checked: pin metal geometry, site/row alignment, overlap, blockages, detailed routing, congestion, DRC, input-pin slew legality, hold closure, all PVT corners, power/activity, full-chip logical equivalence or downstream timing. No legalizer/router/LEF was used. RC is assumed, not extracted. OpenTimer warning `normalized_voltage` is retained; successful timing runs have finite values/no engine error lines. The RC control confirms dependency, not calibration or cross-engine accuracy.

## Access and execution history

- NVIDIA PDF: shell 403 / web parse failure; no bytes. Stopped that endpoint.
- Georgia Tech PDF: independent author-hosted source supplied later. Shell403; web PDF read succeeded. No permission evasion. Final IEEE and byte hash remain unverified here.
- Configured user repo: local empty checkout, remote HEAD missing; API Forbidden. Retained local branch/root commit; no upstream mutation.
- Configured Debian snapshot indices: proxy403; APT also reported cache permissions. No system sources/security changed, no privilege escalation; stopped that installation path.
- Free alternative: pip-installed CMake/ninja in workspace, built inspected MIT OpenTimer. One superseded full-build process tree stopped; targeted build completed. One setup attempt ran before the executable existed, one ANSI-port parser smoke failed, non-ANSI format corrected it. Raw failure evidence retained.
- Missing trained model/teacher/INSTA/commercial physical flow: still pending, **not executed**. No automatic approval review rejection occurred.

## Closeout audit repair

Independent review identified hardcoded default timing/load values in SDC emission while scoring read fixture required time, plus a hardcoded fanout threshold. The emitter/validator now use the same configuration source as scoring. `src/test_config_contract.py` checks a nondefault SDC/score contract and fanout thresholds2/12/11, then verifies153 default evaluated input files byte-for-byte against the archived inputs. It adds zero STA calls. Default historical results remain unchanged. Existing output-only slew observations are retained; no A-pin measurements are inferred retroactively. Prior audit confirmed v1 ZIP member/source/STA/SPEF evidence independently (parent-reported), resolving the earlier local download failure as an access limitation rather than corrupted upload evidence.

## Bounded feasibility follow-up (2026-10-28)

See [FEASIBILITY_DIAGNOSIS.md](FEASIBILITY_DIAGNOSIS.md). Exactly9 predeclared configurations (three archived baseline replays plus two shallow x8 alternatives per net) were evaluated, separately from the original matched-budget comparison. All9 pass declared structural/cap/fanout and newly measured A/Y-slew checks, with no tool/constraint-contract errors, but all9 still violate80ps timing. Near-source shallow alternatives reduce worst arrival to115–131ps. These measurements improve on the selected baseline, not establish optimality, general Pareto dominance or infeasibility. Earlier Y-only data and the original51-case comparison remain unchanged. SFT/netGRPO/fullchip/power/physical claims remain Not.

## Provenance and local envelope follow-up

[PROVENANCE_AND_ENVELOPE.md](PROVENANCE_AND_ENVELOPE.md) establishes that80ps, input slew, cut output load and RC are local assumptions, not paper/artifact targets. Independent old-log checks find no unit/path mismatch but identify .5fF terminal-load extrapolation below the1.44fF Liberty grid. Twelve predeclared STA calls preserve a before/after replay and evaluate three same-boundary corrected-load actions per net. All actual targets remain80ps. Corrected results expose smaller/slower versus larger/faster choices; Pareto status is per-net/per-load and pairs area/delay from the same implementation. All actual runs still violate80ps. Relaxed target-grid arithmetic is explicitly counterfactual, not paper reproduction. No APIs, model training, paid resources or new physical claims. Old evidence and v3 remain preserved.
