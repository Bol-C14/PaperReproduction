# CircuitFusion bounded milestone — completed 2026-10-28 UTC

**Decision: Go for the next bounded realism check on CPU; full paper route remains L3 / No-Go here.** This completed method port needs no extra resources. The next useful gate is real HDL-to-netlist pairing and less templated summaries, before any scale-up. No GPU, API, gated weights, paid tools, commercial labels, full-paper training, or push was used.

## Repair evidence

Four deterministic source controls pass. The untouched downloaded functions and loop are executed via AST extraction with small collaborators, alongside the repaired versions. This validates the local defects, not the original paper experiments or full upstream integration.

- Inference HDL sensitivity: original 0; fixed max absolute output change 1.4142. MLM context sensitivity: original 0; fixed loss change 2.0. These are deterministic stub measurements, not language-model quality metrics.
- Summary export: original `.txt` read fails; after adding a `.v` fixture it exits before save. Fixed path reads `.txt` and writes the expected normalized `[0.6, 0.8]` pickle. All model loading is replaced by a test stand-in; no gated request.
- Accumulation: for 129 microbatches original optimizer/scheduler step counts are 130/130; fixed counts are 2/2. Fixed parameter values match explicit averaged-loss references at 1, 128, 129 and 130 microbatches to 1e-10 tolerance. Source patch also computes scheduler update count and rejects unequal/nonzero loader counts. This is a CPU single-process repair; distributed batching is untested.
- Patch leaves unrelated upstream losses, checkpoint requirements, author-local paths, padding behavior and commercial dependencies in place. It is a partial source snapshot, not a runnable full checkout.

## Frozen synthetic method port

Protocol frozen before construction/training: `pilot/PROTOCOL.json`; SHA256 `79aa1cffaf93b11a67a6b7f66934940d7b69182377107117a642b88af01d20e2`. No result-driven parameter/seed/epoch tuning.

Self-authored three-bit combinational next-state cones: 84 unique functions, 56 train / 28 test, 8 train / 4 held-out parent families. Two equivalent HDL-expression views, operator graphs, template functionality summaries and exact gate-graph implementations share explicit IDs. All 5,376 input assignments were checked exhaustively across original expression, equivalent expression and gate evaluator. No duplicate truth tables, cross-family split overlap or modality-ID mismatch. Seven integrity controls pass, including deliberately wrong pairs, split reassignment, duplicate IDs and observable gate corruption. Training symbols cover test symbols; no sample/family IDs enter the encoders.

Architecture: randomly initialized 28,736 parameters; small HDL/summary GRUs, graph message passing, summary-query cross-attention over HDL and graph states, and a separate gate-graph encoder. Objective combines equivalent-view RTL contrastive learning and cross-stage contrastive alignment. No pretrained claims. Three seeds, three arms, 250 updates per run. Shuffled targets are a fixed within-training-family cyclic derangement.

| Arm | Mean held-out Recall@1 | Mean Recall@5 | Recall@1 by seed 11 / 23 / 37 |
|---|---:|---:|---|
| paired | 66.67% | 100.00% | 35.71% / 89.29% / 75.00% |
| shuffled | 0.00% | 35.71% | 0.00% / 0.00% / 0.00% |
| no_alignment | 4.76% | 28.57% | 7.14% / 7.14% / 0.00% |

Chance for 28 candidates: Recall@1 3.57%, Recall@5 17.86%. Paired-minus-shuffled Recall@1 is +66.7 percentage points; exploratory 95% family bootstrap interval +38.1 to +83.3 points (only four held-out families). Paired equivalent-view cosine ranges 0.9920–0.9933. Raw per-sample results, seeds, loss changes, control mapping and resource data are saved.

## What this supports and what it does not

Correct semantic pairing can train a shared RTL/gate space in this small synthetic setting, and held-out-family retrieval improves over the frozen wrong-pair control. This is a smoke result about learnability of the port, not validation of CircuitFusion performance claims, general HDL semantics, synthesis quality, PPA prediction, or multimodal gains.

Key limitations / useful gaps:

- Paired zeroing sensitivity norms: code 0.337–0.564, graph 0.049–0.091, summary 1.263–1.320. Graph influence is small here. Sensitivity is not accuracy benefit; no leave-one-modality-out retraining was authorized in the frozen design. Independently authored summaries and graph-utility ablations are needed before claiming multimodal benefit.
- Summaries deterministically verbalize the AST, so the task can reward structural/template shortcuts. All cones are tiny combinational functions with modular arithmetic; reset, signedness, sequential clocks, registers and real parser robustness remain untested.
- Handwritten Boolean lowering is an implementation graph with exact truth-table semantics, not production or technology-mapped synthesis. There are no delay, power, area or industrial labels.
- In no-alignment runs the netlist encoder stays random. This is a cross-space baseline, not a separately pretrained netlist baseline. The paired-versus-shuffled comparison is the stronger control.
- A cyclic shuffled mapping is systematic, not iid noise; future controls should include independently sampled derangements. Only four synthetic held-out families and three seeds limit inference; observed seed spread is large.
- Original-versus-repaired upstream controls use deterministic collaborators. DGL/BERT/full checkpoint loading and multi-GPU behavior remain untested. Static defects alone do not invalidate the paper.

## Cost, provenance and next gate

Completed pilot: Python-reported 62.93 seconds; Bash total 64.60 seconds; 2 CPU threads; peak RSS 372.80 MiB. PyTorch 2.14.1+cpu. Nine runs completed. Setup and execution stayed inside roughly 10 minutes, well below the 2-hour setup cap. Pip advertised wheel payload totals about 223.74 MB plus 45,485 source bytes and unmetered metadata/transport overhead, well below 2 GB. Installed venv is approximately 970 MiB. No OS-level network meter was available.

All raw files came from the official repository; hashes are in `provenance.json`. Main commit metadata is still inaccessible via GitHub API proxy 403, so content hashes freeze the partial snapshot rather than inventing an immutable commit. `requirements-cpu.lock`, `repairs.patch`, `COMMANDS.md` and logs make the local milestone inspectable. Upstream code license remains unresolved; no publication.

**Next gate:** establish a legally usable small public/self-authored HDL set and official open synthesis/parser installation; generate real mapped netlists with explicit register/cone identity, then test independently checked summaries and modality benefit under family isolation. Keep that follow-up CPU-bounded; no current need to buy GPU/API resources. Full-paper labels/checkpoints and commercial DC/PrimeTime access remain unverified and materially higher-cost. Gated NV-Embed access has not been requested or accepted.

Audit history is preserved in `ASSET_AUDIT.md` and `assets.json`; their no-experiments statements describe the earlier audit-only phase. This later authorized milestone is documented separately here. No further paper or expanded run was started.
