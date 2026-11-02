# Resource inventory — 2026-11-02 UTC

## Isolation and input

Repository: existing `https://github.com/Bol-C14/PaperReproduction.git`, restored into this task workspace because the 2026-10-28 checkouts were intentionally deleted on 2026-10-31. Base/default remote HEAD: `809ca20e003c2f5d5a723c77ead8a6de532e4539` (`reproduction/trace2skill-mlcad2026`), **not a main branch**. New local branch: `prepilot/rq1-action-panel-20261102`. Initial checkout clean. No push or PR.

Research attachment: `../input/Pasted text(1).txt`, 47,615 bytes, Library ID `PRIVATE_LIBRARY_REFERENCE`, SHA256 `5fbe2829ca65017ba5eb05356e53069144e3879f9d9743a91f559a9729aff3cc`, Library version xattr 0. Materialized through the actual Library transfer URL and confirmed readable. No Library skill was discoverable in the available skill catalogs; the available purpose-built prepare_materialize tool supplied the transfer. No guessed URL or cross-environment path was used. The document's literature claims are hypotheses/source leads, not verified facts in this inventory.

## Mac

173 GiB available; load averages initially 10.48/5.97/4.84. Active meeting/video processes account for substantial CPU. No native yosys/abc/openroad/verilator/iverilog located on PATH. Docker server 29.1.3 is reachable with execution escalation. Prefer COMPUTE_HOST for actual EDA work and Mac for coordination. No apps stopped or configurations changed.

## COMPUTE_HOST

Existing alias is `compute-host`, not `april`. Existing configuration works under authorized escalation. 192 logical CPUs; 1.5 TiB RAM total / approximately 1.3 TiB available; /home 26 TiB free. Initial load 0.37/0.42/0.34. Existing user processes and Podman containers inspected: no active Podman container and no CPU-heavy shugu experiment observed at snapshot. This is not proof of absence of all scheduled/other-user jobs. Registry coverage explicitly says SELECTED_BATCHES_NOT_EXHAUSTIVE; no exhaustive task-registry claim.

Existing `/workspace/work/AGENTS.md` and toolchain checkout AGENTS require sourced `.env`, its Python, MCP import and matched Vivado. Verified MCP import, executable and RapidWright directory without printing `.env` or credentials. Vivado v2025.1 build 6140274. Toolchain checkout `fpl26_optimization_contest_ablation_shu`: clean observed status, HEAD `f4de013`; Apache-2.0 code license present. This license does not establish rights to redistribute all benchmark DCPs or the proprietary Vivado installation. No redistribution planned.

The old `/workspace/work/paper-reproduction-april-20261028` was deleted in the prior authorized cleanup. The separate longstanding FPGA checkout and its DCPs remain. The smallest located checkpoint is VexRiscv 1,815,178 bytes; other family examples include mini-ISP (3,948,685 bytes) and 3D-rendering (7,937,701 bytes). Existing related versions give candidate state pairs, but their comparability and public source/licensing have not yet been independently audited.

Existing rootless images include `localhost/pdagent-openroad:26Q2`, `localhost/posteda-calibration:klayout-0.30.3` and an ORFS image. A network-disabled temporary pdagent container successfully reported OpenROAD `26Q2-1164-g08f67ee5ec`; it exited and was removed. No new image download. No ODB found in its bounded filesystem search. Container availability does not establish a ready physical-design experiment.

## Reuse candidates and exclusions

Prior PDAgent evidence at `origin/reproduction/benchmark-pdagent:benchmarks/E3_PDAgent/WORKFLOW_FEASIBILITY.md` says the prior bp_fe initialization DB has 11 unplaced macros at origin and there was no released post-macro reference. That old DB path was in the cleaned workspace; current availability is not assumed. Do not reuse it as a placed/routed state or trigger the nominal --no-llm workflow, which prior source audit found can invoke an inner model.

Prior ROVER-inspired independent implementation is on `origin/reproduction/constraint-aware-rover-tcad2025`. Its FINAL_STATUS explicitly limits evidence to authored kernels, generic synthesis, partial method reconstruction and uncalibrated delay, not original industrial/physical results. It is a possible mechanism-study fallback, not an interchangeable real FPGA benchmark and not a full original-system reproduction.

No API/GPU/cloud consumption, new model requests, credential/security/SSH changes, old reproduction reruns, external publication or extra worker threads. This thread owns RQ1 only; RQ3/RQ4 coordination belongs to the parent.

Current-truth follow-up: the public archive-to-input hash chain and VexRiscv MIT assignment were subsequently verified in SOURCE_PROVENANCE.json; ROUND2_REVIEW.md audits the completed limited pipeline comparison. NEXT_GATE_PLAN.md is a proposal, not an executed extension. No new EDA computation occurred during the result-review turn.

Latest actual experiment: ROUND3_V2_RESULT.md completes an original-state no-PSIR A/B pair under versioned short-export identity checks. Both eligible; WNS tie, B cost 1.279x; no confirmations or expansion. Original ROUND3 metadata false rejection retained unchanged. No pilot jobs remain.
