# GenEDA: controlled training-to-generation reconstruction

**The actual training → autoregressive generation → independent scoring loop is complete. The result is negative: this small scratch decoder does not establish useful circuit-semantic alignment.** Both raw and numerically conditioned graph features were tested against matched-budget controls, with two seeds and two declared training budgets. This is a methodology reconstruction, not pretrained GenEDA or reproduction of its reported scores.

## What was actually run

The [paper's embedding-alignment path](https://arxiv.org/html/2504.09485v2) conditions a decoder on circuit features through a learned connector. The public [projector source](https://github.com/hkust-zhiyao/GenEDA/blob/0a19fde3f1c1e56f49a367bf5f1914de84e1c951/model/embed_align/model/model/multimodal_projector/builder.py) and [instruction-tuning script](https://github.com/hkust-zhiyao/GenEDA/blob/0a19fde3f1c1e56f49a367bf5f1914de84e1c951/model/embed_align/scripts/circuit/finetune_lora_summary.sh) identify the 768-input MLP/LoRA route used as the structural reference here. The previous original-source interface tests remain unchanged under `../validation/`.

This implementation uses actual released Task 1 graph vectors and actual reference descriptions, not synthetic target answers or a generic LLM API. A 139,008-parameter, two-block causal Transformer of width 64 is trained from scratch on the training-family reference text. The 768→64→64 GELU connector then trains with the decoder frozen; a second stage trains the connector and rank-4 LoRA adapters while freezing the base decoder. The graph token follows the signal/interface prompt. Only answer tokens contribute to the autoregressive loss. Greedy generation produces up to 512 UTF-8 bytes, with no answer text in the input.

The independent evaluator imports neither PyTorch nor the trainer. It reads saved generations and scores exact answer-prefix matching, token ROUGE-L F1, a fixed functional-vocabulary precision/recall/F1, and repetition. These are lexical diagnostics, **not circuit equivalence or a substitute for a functional checker**. Original descriptions are truncated to the same 512-byte prefix used for training; these metrics cannot be compared with the paper's full-answer scores.

The raw-feature arm retains the released numerical scale. A separate conditioned arm subtracts training-only coordinate means and divides by training-only standard deviations, floored at `1e-8`; that is an explicit numerical method port. All vectors remain frozen. No circuit encoder is trained or inferred in this experiment.

## Leakage controls and budgets

There are **64 training examples from Rocket**, **16 reserved validation examples from ITC99 (`b14`, `b20_1`)**, and **16 test examples from the VexRiscv family**, grouping all three VexRiscv variants together. `Core` is excluded because its project provenance is uncertain. Exact feature and whitespace-normalized target duplicates are disallowed within/across selected splits. All graph-to-text joins are unique exact reference-label joins. The validation set was reserved and not used to select settings; the longer budget was motivated by training-only diagnostic failure before any G1 held-out metric was inspected.

This is stricter than the earlier interface fixture: VexRiscv variants no longer cross the family split. It is still one training project family and only 16 test cases. Original encoder pretraining exposure and ultimate parent-design identity are unverified. The frozen G1/G2 manifest is byte-identical; its hash is retained in [summary.json](summary.json).

| Protocol | Scratch language-pretraining updates | Connector-only updates | Joint connector/LoRA updates | Seeds |
|---|---:|---:|---:|---|
| G1 | 160 | 40 | 80 | 17, 23 |
| G2 | 1,600 | 120 | 240 | 17, 23 |

Each arm uses the same shared initial language decoder within seed, identical training-row minibatches (batch 4), context/answer limits and task-update count. Controls are: matched raw vectors; matched conditioned vectors; conditioned vectors with a seeded derangement of training pairing; all-zero vector input with the same trainable connector; and non-aligned text SFT with a zero graph token. The matched models also undergo held-out graph shuffling and graph-token zeroing at inference.

Connector-only stages train 53,376 parameters; joint stages train 59,520. Text SFT trains 6,144 LoRA parameters throughout all 120/360 task updates. Thus data/update budgets are matched, while the intentionally different non-aligned architecture has a different trainable-parameter count and more adapter-update steps. The shuffled and zero-input connector controls have exactly the same architecture, parameter counts and stage budgets as matched conditioning; they are the primary pairing/modality controls. Exact FLOPs are not claimed equal.

G1's malformed training generations and training NLL around 2.4 showed an inadequate scratch prior. [G2's budget](PROTOCOL_G2.md) was fixed from those training-only diagnostics; no held-out quality selected its settings. No additional fitted budget follows G2.

## Results

Mean token ROUGE-L F1 over both seeds on the same 16 held-out answer prefixes (scale 0–1):

| Condition | G1 | G2 |
|---|---:|---:|
| Raw matched | 0.00140 | 0.02455 |
| Conditioned matched | 0.00137 | 0.01736 |
| Conditioned shuffled training pairing | 0.00172 | 0.01900 |
| Zero-input modality control | 0.00212 | 0.02894 |
| Non-aligned text SFT | 0.00701 | 0.03558 |
| Generic template baseline | 0.15307 | 0.15307 |
| Training-answer-frequency baseline | 0.18239 | 0.18239 |

Every arm has zero exact-prefix matches. Functional-vocabulary F1 is zero throughout; 10 of the 16 references contain at least one term in the declared vocabulary, so this is not an empty-reference average. Coverage is limited and the vocabulary cannot certify semantic correctness. Generated outputs remain fragmentary and repetitive; even the strongest trained arm is worse on ROUGE-L than the fixed generic baseline. Better NLL alone did not produce useful descriptions.

Raw matched models produced **identical answers for all 32 held-out cases across both seeds when the graph vectors were shuffled**, in both budgets. Zeroing the graph token changed all 32 outputs, so graph-token presence affects the decoder, but this is compatible with a learned generic prefix rather than circuit-specific information. Conditioned graph shuffling changed all 32 G2 outputs, yet matched training pairing did not outperform the shuffled or zero-input controls. Sensitivity alone is not useful alignment.

The longer scratch language pretraining did learn its standalone answer distribution. A [train-only context diagnostic](results_g2/context_diagnostic.json), performed after the fixed runs with their own safe NPZ checkpoints, found:

| Seed | Mean answer-only NLL | Same answers with signal prompt and zero graph token |
|---|---:|---:|
| 17 | 0.48960 | 7.04715 |
| 23 | 0.63197 | 6.58816 |

This jointly changes prompt context and absolute answer positions; it does not isolate a specific cause. It demonstrates that this scratch language prior is not robust in the conditional interface. Consequently, these negative generations cannot identify a failure of the original pretrained GenEDA approach or isolate encoder-feature quality from decoder inadequacy. The experiment closes the local training/generation/evaluation procedure while leaving the scientific capability claim open.

There are 20 completed arm/seed/budget runs, four shared language-pretraining runs, 656 planned autoregressive generations (including training diagnostics and interventions), and 128 fixed baseline records. Four additional generation replays verify NPZ checkpoint restoration before/after portable-data packaging. All 784 planned scored records and per-example outputs are retained. No confidence/significance claim is made from two seeds.

## Mechanism coverage and remaining gaps

| Component | Coverage |
|---|---|
| Frozen circuit representation → trainable MLP → decoder input embedding | Exercised with the released 768-dimensional vectors and actual text targets. |
| Frozen-decoder alignment followed by connector/decoder-adapter tuning | Exercised, with width/rank reduced and a decoder trained from scratch. |
| Training → genuine autoregressive generation → separate evaluation | Complete for the declared Task 1 reconstruction and controls; no synthetic answer target was substituted. |
| Original pretrained decoder semantics and context robustness | **Not retained.** No compatible pretrained decoder is available locally; this scratch substitute does not provide a capable foundation-language prior. No previously denied provider request was retried. |
| Raw netlist → learned circuit encoder | Not run. Only cached features are used; encoder checkpoint, preprocessing provenance and original training data remain unverified. |
| Useful learned circuit-semantic alignment | **Not established.** Matched pairing does not improve the declared controls; outputs are poor. |
| Full Task 2 results | Not run; its feature/pairing integrity was inspected previously, not its generation capability. |
| Prediction alignment / Task 3 RTL reconstruction | Not reconstructed. The learned gate predictor and annotation provenance remain unverified; manual/oracle labels would replace its learned mechanism. No RTL functional-success claim follows from these language metrics. |
| Original full-paper scale, data split, tools and scores | Open. Full-paper route remains L3; the low-cost structural reconstruction does not promote it to L1 or establish paper-level reasoning. |

Obtaining a verified compatible pretrained decoder and informative encoder outputs would remove concrete limitations identified here. Rebuilding the original encoder/data stack is a different, substantially larger resource task. Further tuning this tiny model until a template looks convincing would not close those gaps, so no additional quality-selected run is made.

## Reproduce and inspect

Use the existing selected cloud workspace; no Mac, external model API, or model download is involved. From `/workspace/PaperReproduction`:

```bash
export PYTHONPATH="$PWD/P12_GenEDA/validation/runtime"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=3
cd P12_GenEDA/generation_v1

# New reconstruction implementation tests (five passed).
python test_reconstruction.py

# Pilot: 10 steps, 1.62 seconds, 317,488KiB peak RSS.
python run_generation.py --pilot --seed 17

# G1, each seed separately.
python run_generation.py --seed 17
python run_generation.py --seed 23
python evaluate.py

# G2, fixed before held-out metric inspection.
python run_generation.py --seed 17 --results-dir results_g2 \
  --pretrain-steps 1600 --stage1-steps 120 --stage2-steps 240
python run_generation.py --seed 23 --results-dir results_g2 \
  --pretrain-steps 1600 --stage1-steps 120 --stage2-steps 240
python evaluate.py --results-dir results_g2
python diagnose_context.py
python replay_check.py
python check_outputs.py
python summarize_results.py
```

Commands above describe the completed run; rerunning them in the same output directory overwrites generated result files. Copy the study directory to a separate local location, or use different `--results-dir` values, before starting a new run if preserving these artifacts. Weights are local numeric NPZ arrays loaded only with `allow_pickle=False`; adapter enable flags must be restored as shown in `replay_check.py`.

The selected, previously frozen raw records are included in `frozen_study.json.gz`, with hashes in `frozen_study_metadata.json`; no new selection occurred during export. The loader verifies compressed/raw hashes, feature hashes, reference hashes, prompts and the manifest before use. This permits offline training/replay without the full upstream clone. If that portable package is absent, original JSON blobs are read from the existing pinned Git cache with lazy network fetch disabled. The exact trainer used for G2 is preserved in `source_snapshots/run_generation_g2_executed.py`; the later portable-loader addition changes transport, not records or the model implementation.

Evidence: [frozen G1 protocol](PROTOCOL.md), [G2 protocol](PROTOCOL_G2.md), [implementation repairs](PRE_RUN_REPAIRS.md), [source snapshot](source_snapshots/run_generation_g1_attempt1.py), [G1 raw evaluation](results/evaluation.json), [G2 raw evaluation](results_g2/evaluation.json), [G1 per-seed runs](results/), [G2 per-seed runs and checkpoints](results_g2/), [summary](summary.json), [output integrity checks](output_checks.json), and [resource/attempt ledger](RESOURCE_LEDGER.json).

The initial seed-23 manifest-check failure occurred before model training: Python tuples did not compare equal to their JSON-list serialization. The canonicalization repair changed no split or example; the failed log is preserved. A prompt whitespace typo was repaired after the language-only pilot and before full training, with the pilot manifest preserved. The initially specified byte-repetition diagnostic was added after the first G1 lexical evaluation; the earlier evaluation JSON is retained and ROUGE/functional definitions did not change. No experiment failure or low-quality result was discarded.

Training/generation process wall times total **644.99 seconds**; peak observed process RSS is **342,988KiB (334.95MiB)**. The study uses three Torch threads within the existing four-CPU quota. New model/dataset downloads: **zero**; the earlier CPU PyTorch installation is reused. Raw study artifacts occupy approximately 24MB before Git compression. Exact final bytes, source hashes, timing anchors and failed-attempt accounting are in the ledger. No paid resource, GPU, gate agreement, credential/security change, upload, push, PR or Runpod action occurred.
