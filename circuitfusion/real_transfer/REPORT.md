# CircuitFusion — real RTL transfer and official asset recheck

Completed 2026-10-28 on the existing `reproduction/circuitfusion-iclr2025` branch, starting at `5d64f6ca702aa43139c5d6b18897c90f44c31dde`. This tranche makes no new full-paper reproduction claim. No repository AGENTS.md, .agents skills, original task prompt, REPRODUCTION, EVIDENCE_AUDIT or FINAL_STATUS files were present at that HEAD; the actual handoff evidence was `ASSET_AUDIT.md`, `MILESTONE.md` and `closure/{REPORT,EXECUTION,MECHANISM_COVERAGE}.md`. The older completed experiments were not retrained.

## Asset conclusion corrected by a complete checkout

The official paper is [CircuitFusion: Multimodal Circuit Representation Learning for Agile Chip Design](https://proceedings.iclr.cc/paper_files/paper/2025/file/7ffb43adf37b3eeaba559098bc084cc6-Paper-Conference.pdf), ICLR 2025. A complete read-only checkout of [the official repository](https://github.com/hkust-zhiyao/CircuitFusion/tree/123bec383aba1d4ce808db486308aaaeb53a25ca) now freezes revision `123bec383aba1d4ce808db486308aaaeb53a25ca`. The previous audit explicitly had only a partial snapshot; its lack of verified assets must not be read as their absence.

There **are 12 matching SPI endpoint IDs** with released cone HDL, RTL graphs, DC netlist graphs and area/power/slack JSON. The restricted passive pickle reader imports no upstream modules or executable graph classes. All 12 netlist graphs parse, contain 11–1541 nodes, and every node resolves in the released node dictionary. This is a real partial paired asset, not the complete training benchmark. ID agreement does not establish released cone semantic equivalence.

Actual Yosys checks of all 12 released HDL cones expose a narrower, reproducible integration problem: five files have out-of-bounds input selects that introduce undefined bits; `wb_int_o.v` fails parsing because a module port is duplicated. Eleven parse; parsing success does not make the five width warnings harmless. These observations concern this released sample, not the paper's private experiment inputs. Exact diagnostics, source hashes and graph counts are in `official_cone_diagnostics.json` and `official_asset_audit.json`.

PPA JSON values exist. Their units, cell-library/constraint/activity context and cross-stage correctness remain unverified. The summary demo has 12 rows with three fields each but no established SPI-ID join: the supplied design list names `b14`, and the inspected caption describes `reg3`. The immutable tree contains no `.pt`, `.pth`, `.ckpt` or `.safetensors` checkpoints and only `demo_lst.json` in its split-list folder. The public [checkpoint request](https://github.com/hkust-zhiyao/CircuitFusion/issues/4) and [design-list request](https://github.com/hkust-zhiyao/CircuitFusion/issues/3) remain supporting evidence, not an exhaustive external-host search. No root license was found. The new payload contains metadata/hashes/diagnostics, not a copy of the unlicensed official asset tree.

## A finite real-source pilot that actually ran

Ten original public Yosys example/regression-test source files were fixed before metrics at Yosys revision `77dddbd6658c80f18204258d6319e9b0ac56df99`. Source copies and the repository ISC notice are retained. These are genuine public RTL examples and compiler regressions, not industrial designs. Three counter-related source files are grouped into one family; the remaining families cover conditional counters, accumulators, multiplication, parity shifts, conditional bit registers, a traffic FSM and blinking logic.

Actual `proc` parsing and synchronous DFF extraction produce 20 candidate register-group D-cones, with all Q boundaries cut and unrelated output logic removed. Nineteen fit the frozen limits (1024 nodes, 2048 tokens); the FSM state-update cone has 1379 nodes and 2054 tokens and is excluded solely by those limits. All 20 candidates complete the synthesis/proof stage; all 19 accepted cones have explicit successful RTL-to-ABC gate equivalence proofs. There is no full temporal/reset/initial-state equivalence claim. Original source widths and state boundaries are retained; there is no arbitrary word-width shrinking. The new graphs include all declared non-clock inputs and Q boundaries, including unused ones, so interface size can be a shortcut.

The 19 accepted cones span 10 source files and eight source families. Each HDL code stream, operator graph, equivalent optimized view, assistant-authored source-level description and ABC netlist shares one ID. These descriptions were written before metrics, are shared across registers from the same source, and are **not live LLM/API summaries or independently validated captions**. The existing external counter was already evaluated in the earlier closure, so this set is not entirely new exposure; no weights were trained on this set or selected using it.

The existing 15 local checkpoints (five trained arms × seeds 11/23/37) were loaded with their exact old training vocabulary, then evaluated without updating weights. Candidate retrieval is strict cone identity among the 19 new gate cones. No test labels enter fitting; there is no new training or downstream PPA experiment. NumPy independently reconstructs every rank. Cross-source semantic duplicates have not been exhaustively excluded, and register cones are correlated within sources; these metrics are descriptive stress tests.

| Existing checkpoint arm | Mean Recall@1 | Mean Recall@5 | Mean MRR |
|---|---:|---:|---:|
| paired | 1.75% | 35.09% | 0.1870 |
| shuffled pairing | 5.26% | 29.82% | 0.2007 |
| no graph | 7.02% | 29.82% | 0.2052 |
| text only | 1.75% | 33.33% | 0.1798 |
| shuffled edges | 8.77% | 22.81% | 0.2022 |

Random-rank expectations are Recall@1 5.26% and Recall@5 26.32%. There is no reliable graph or correct-pairing advantage in this transfer setting. This does not test the pretrained original encoders. Mean per-cone unknown-token rates are HDL 40.31%, descriptions 70.19%, RTL node kinds 6.63%, and netlist node kinds 8.85%; original embedding tables also clamp widths/lanes above 16, with counts recorded per cone. These distribution shifts materially confound an architectural interpretation. Equivalent-view cosines near one do not establish useful discrimination. See `results/metrics.json` for all seed/sample/family ranks and `embeddings.npz` for inspection.

Preparation took 22.77 seconds. Fifteen checkpoint evaluations took 4.75 seconds with two Torch threads and 894.9 MiB peak RSS, using Torch 2.6.0+cpu. Environment setup is additional and preserved in the private execution ledger. APRIL was checked for competing writers and had no CircuitFusion checkout or running job before an isolated checkout, venv and cache were established. No GPU, LLM service or local language model was deployed; API spend this tranche is zero.

## Failures, repairs and reproducibility

The initial boundary builder reused the internal name `state` for a new cut port, conflicting with the traffic FSM's original internal net name. An initial Q-bit deduplication was insufficient; removing the original netname table from the new combinational module fixed the collision while preserving bit-ID connectivity. An HDL tokenizer was also corrected to preserve Verilog numeric literals. Both earlier attempts, their logs, earlier 14-cone metrics and exact source remain in the private evidence archive. No outcome-based model, seed or loss changes were made. The final 19-cone result supersedes both incomplete preparations. `ATTEMPTS.json` records dependency and transport failures as well; no failed SSH return code was treated as proof a remote command had stopped.

The new files `sources.json`, `PROTOCOL.json`, `PROTOCOL.sha256`, `manifest.json`, `formal_checks.json`, `preparation.json`, `requirements-april.lock`, and `results/` preserve inputs, frozen limits, metrics and proofs. `prepare.py` regenerates raw cone artifacts; the raw logs/data and abandoned attempts remain in the APRIL checkout and the private archive outside this branch payload. No source report is overwritten and the old 144-cone experiment is not repeated.

Example commands, with operator-supplied environment paths:

```sh
CIRCUITFUSION_YOSYS="$VENV/bin/yowasp-yosys" CIRCUITFUSION_CACHE="$CACHE" "$VENV/bin/python" circuitfusion/real_transfer/prepare.py
"$VENV/bin/python" circuitfusion/real_transfer/evaluate.py
python3 circuitfusion/real_transfer/audit_official.py "$OFFICIAL_CHECKOUT"
```

## Next bounded gate: real semantic summaries

The paper's functionality descriptions are LLM-produced; the current substitutes do not close that mechanism. `api_quote_plan.json` was produced using only the shared client's pure `conservative_chat_quote` function, without constructing a Client, reading credentials or issuing requests. Proposal: `google/gemini-2.5-flash`, the 19 public derived cones only, 19 generation requests plus at most two correction requests, 512 output tokens, temperature zero, reasoning disabled, sequential execution, all through public `Client.chat`. The largest serialized request is 4689 bytes. Do not send labels, gate counts, endpoint IDs, private paths or checkpoint information.

The shared client's approved pricing envelope reserves **$0.32 per pending request**, because it quotes the model's full accepted context ceiling rather than the tiny actual input. Request a parent-managed **shared cumulative ceiling of $0.50**, allowing 21 additional requests above the then-current global request count; this is not $0.50 per paper or permission to alter policy locally. Expected incremental usage is under $0.05, an estimate only; the ledger is authoritative. Sequential dispatch limits outstanding reservations. API execution is pending parent allocation; nothing is reserved or spent now.

Check generated captions against actual D-cone HDL for dependencies, selectors, widths, signedness and conditional updates, and reject invented clocks/reset/physical claims or source/ID/graph-statistic leakage. Preserve raw outputs privately and freeze checked captions before any matched control. A caption-factor comparison must use the same source-family splits, budgets, encoders and seeds; correct versus source-family-shuffled captions and current coarse captions are the useful contrasts. With only eight source families, this will remain a pilot. Its first deliverable should be verified semantic caption coverage; useful representation gains cannot be promised given the high OOV rate and missing pretrained backbones.

Full CircuitFusion remains incomplete: original 7B code embeddings, BERT/Graphormer capacity, pretrained netlist encoder, full parent-isolated paired benchmark and calibrated commercial PPA remain open. No GPU request is justified for the present checks. No push or PR was performed.

## Released live-summary tranche — completed

Parent released batch `cf-rtl19-v1-20261028`. Exactly19 serial Gemini2.5Flash requests completed,512 output-token cap, temperature0, reasoning off. All used shared public Client.chat with batch_id and $0.32 reservation;19 attempts cost $0.012824, pending0, two correction requests unused. No policy/credential changes. Raw content and usage remain private outside publication payload. ISC notice accompanied each comment-stripped public cone; no official uncertain-license SPI asset was sent.

All19 responses were checked by the same assistant against HDL; this is not independent review. Two clear semantic errors were false bit reordering and false signedness. Six descriptions received explicit factual/wording revisions, including simplifying mux descriptions; one uncertainty incorrectly called a reachable default unreachable. Uncertainty fields were excluded. `summary_review.json` preserves per-caption content hashes/revisions. Checked API-plus-editor descriptions, not untouched model captions, drive this comparison. Canonical signal names remain in accepted captions; source/sample IDs and PPA statistics do not.

Frozen paired/no_graph checkpoints, seeds11/23/37, same19 candidates, no training/tuning: paired Recall@1 coarse1.75% to checked API3.51%, Recall@5 35.09% to29.82%; no_graph Recall@1 7.02% to5.26%, Recall@5 29.82% to26.32%. Mean caption OOV falls70.19% to53.44%; HDL and graph vocabularies are unchanged. No stable graph benefit follows. Caption-factor change is confounded with review/length/content and large residual OOV; it does not establish original backbone semantics. New six-checkpoint results and independent rank reconstruction are in `results_api_summary/`. No further sweep or API retry launched.

The earlier proposal/pending statements above are historical and superseded by this completed tranche. At completion of the experiments, HEAD remained the preserved starting commit and new work was uncommitted. A later local preservation commit is identified in the external closeout receipt; no push/PR.
