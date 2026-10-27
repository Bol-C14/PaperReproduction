# Frozen behavioral contract (2026-10-27, before tuning)

Source: Wang et al., ISPD 2026, DOI 10.1145/3764386.3779579, author-hosted nine-page PDF https://jpan.me/files/ISPD26_AstroTune.pdf (read through web extraction, direct GET 403). No appendix in these nine pages. No official implementation/artifact link found in paper or author's publication entry; absence is a bounded search result, not proof of nonexistence.

## Paper facts

Phase I: hierarchical LLM module/design JSON summaries of RTL/spec; LLM top-k preselection; Pyverilog AST tokens including node types, edges, widths and spec; frequency-weighted BLAKE2 SimHash, seeded MinHash, normalized signed hashed embedding HASTE. Rerank preselected cases by weighted sum of these three and a direct LLM semantic similarity score; transfer winning case's full parameter vector. Eq1–7.

Phase II: stage-specific BO; GP synthesis and TPE layout. Repeated best candidates promoted after a short stability interval while upstream search continues; later-stage threads inherit exact parent artifacts and warmstart's downstream parameters. Compare first child evaluation with dynamically best stage baseline, prune significantly inferior threads. Longer stability interval terminates stage. Store resulting design/spec/config in database. Eq8–10 normalize PPA to initial flow; synthesis soft timing penalty, layout hard timing branch. Unknown policy constants must be declared.

Original uses Design Compiler/Innovus, Nangate45, 33 discrete parameters/7 stages, 20 default BO iterations per stage, GPT-4.1 summaries; 20 tests plus legacy cases from RTLLM, RTLRewriter, OpenABC-D, FreeV. Do not claim those data, tools or absolute PPA are reproduced by substitutes.

## Local implementation policy

Use only freely available tools and licensed public RTL. Prefer real synthesis and physical placement. Reduce stage/parameter count to fit verified resources. If unavailable, synthesis/mapping stages establish a partial algorithm pilot only, never a physical-flow replication. No fabricated power, timing or oracle EDA metric. No paid API. Deterministic text/spec retrieval is a labeled control, not an LLM. All AST tokenization, hash sizes, weights, candidate thresholds, BO encoding, acquisition and normalization choices are local assumptions and recorded in source/report.

Separate legacy source designs and target designs by files; exclude exact target/altered copies from tuning retrieval. Renamed copies may be used only in a separately labeled robustness identity test. Hash sources and retain provenance. Freeze legacy DB before target runs; never let target results change another target's initial DB. Audit transfer against measured donor choices after searches, never feed target outcome matrix to optimizer.

Run one real end-to-end pilot before bulk search. Compare no retrieval random, no retrieval BO, structural retrieval BO, text/spec retrieval BO, and multi-parent vs single-parent BO with common EDA-stage budget and fresh runs. Report actual count, unique configurations, invalid attempts, per-stage execution, optimizer/retrieval overhead, legacy preparation, walltime and deterministic rechecks separately. Pruning's saved work cannot be claimed as faster walltime unless measured. A no-benefit result is valid. Table5 absolute PPA and LLM independent utility remain Not Replicated absent original tools/online model.
