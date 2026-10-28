# P16 — AssertSolver asset audit

Date: 2026-10-28. Purpose: method learning, not bit-exact reproduction. Audit only in the selected PaperReproduction Linux cloud environment. No repository code, inference, training, EDA tools, experiments, model/provider APIs, installation, gate acceptance, account-information sharing, settings changes, or publication were performed. Public documentation, source, config, repository tree, benchmark schema examples, and checkpoint listing metadata were inspected. Git metadata and small public assets were fetched; no weights were fetched.

## Decision

**Minimum faithful actual repair route: L3 under the current no-gate-access constraints (medium confidence). Full-paper route: L3 (high confidence).** Code exists, so L4/L5 do not apply. The essential final checkpoint is publicly listed but gated; this means inaccessible under this audit's constraints, not absent. There is no verified low-cost substitute preserving the learned repair behavior. The remaining self-contained route would regenerate missing training assets and train, which is high cost. This L3 is a practical route classification, not a claim that inference itself requires retraining.

**Conditional checkpoint route: L2 once independently authorized access is already available** (medium confidence): use the final model plus the released evaluation records; fill the missing evaluation driver/scoring policy at modest software cost. A single-case generation demo is closer to L1 conditional on obtaining its direct gated assets, but does not reproduce the evaluation or establish successful repairs. Gate access was neither requested nor attempted.

**Checker-only learning route: L2, low cost, auxiliary only.** Implementing a JSON/schema, one-line patch, and golden-line comparison exercise can teach the input/output contract on CPU without a model. It cannot generate novel repairs or teach the learned PT/SFT/DPO effect and must not be called AssertSolver reproduction. A functional checker additionally needs an explicitly chosen SVA-capable toolchain and harness; its exact compatibility and runtime remain unverified.

Levels: L1 code/direct required assets; L2 code/missing low-cost fill; L3 code/missing high-cost fill; L4 confirmed no code/cheap implementation; L5 confirmed no code/high-cost implementation.

## Official sources and snapshot

- [Repository](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25), inspected main commit `96882fe018379d1974fd1e1b6c3b8f75e4de3d0e`. Complete filename inventory: `evidence/repository-files.txt`. Source links below pin this commit.
- [Paper v1](https://arxiv.org/html/2503.04057v1), 6 March 2025. Requested publication identifier: DOI 10.1109/DAC63849.2025.11133324. This audit reads v1; equivalence to the final DAC text is unverified.
- [Official linked model card](https://huggingface.co/1412312anonymous/AssertSolver) and [public file listing](https://huggingface.co/1412312anonymous/AssertSolver/tree/main). The listing was metadata only; no gated file/config/tokenizer content was opened.

## Asset inventory

| Asset | Observation | Availability / confidence |
|---|---|---|
| Repair demo | `fix.py` loads the final checkpoint and emits a response for one embedded example. | Public source, high |
| Benchmark | `testbench/SVA-Eval-Machine.json` (6,365,477 bytes), `SVA-Eval-Human.json` (168,371 bytes). Opening records carry `module_name`, `buggy_code`, `buggy_line`, `fixed_line`, `spec`, `assert_log`; assertions are embedded in RTL strings. | Public, high; counts not recomputed (no EDA). Testbench README is empty. |
| Final model | Linked model is derived from `deepseek-ai/deepseek-coder-6.7b-base`; card shows ~7B, F16. Three listed safetensors shards are 4.94, 4.95, 3.59 GB (~13.48 GB displayed total), plus index, config, generation config and tokenizer metadata. | Existence/listing verified, high; payload access gated and integrity/behavior unverified |
| PT/SFT/DPO implementation | Vendored LLaMA-Factory source, launch script, YAMLs, ZeRO-3 config, dependency ranges. | Public, high; no execution |
| PT corpus | Config names `verilog4pretrain`. | Not present in inspected repository tree; external release unverified |
| SFT corpora | Config names `all_sft_correct_cot_QA`, `all_sft_incorrect_cot_QA`. | Not present in inspected tree; external release unverified |
| DPO pairs | Config names `self_contrast_correct_cot_QA`, `self_contrast_incorrect_cot_QA`. | Not present in inspected tree; external release unverified |
| Dataset registration | Loader expects dataset configuration (or explicit ONLINE mode). No `dataset_info.json` is listed in the complete tree. | Local mapping missing from inspected snapshot, high |
| PT and SFT intermediate checkpoints | YAML paths refer to local `models/.../pt` and SFT directories; no model artifacts in repository tree. HF listing exposes a single final model layout, not stage checkpoints. | Not found in inspected releases; availability elsewhere unverified |
| Paper task evaluator / augmentation pipeline | No task-specific scoring, patch application, generation/validation pipeline, `.sby`, solver setup, split manifest, or experiment result archive appears in the tree. Generic training/evaluation utilities do appear. | Missing in this snapshot, high; not a global claim of absence |
| License | `train/LICENSE` and source headers cover vendored trainer code. No top-level license is listed. Model access has additional conditions. | Overall code/data reuse terms unverified; no terms accepted |

Sources: [benchmark directory](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/tree/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/testbench), [training files](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/tree/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train), [HF file metadata](https://huggingface.co/1412312anonymous/AssertSolver/tree/main).

## Mechanism and semantic contract

Paper-derived outline: augmentation uses GPT-4/Claude-3.5 and Icarus/SymbiYosys. PT uses compilation-failure material; SFT uses assertion and general RTL repair examples; DPO uses errors from 20 SFT responses per training question. The paper reports 22,646 PT, 36,650 Verilog-Bug, 7,842 SVA-Bug, and 915 evaluation instances (877 machine, 38 human). These are reported counts, not audited counts. Training uses eight A800-80GB GPUs with full-parameter ZeRO-3. Evaluation uses 20 responses, temperature 0.2, and pass@1/pass@5, with prompt refinement for JSON compliance. [Paper §§II–IV](https://arxiv.org/html/2503.04057v1)

Actual public demo contract: input contains specification, buggy RTL with assertion, and failure log; output is requested as JSON with `CoT`, `buggy_code`, `correct_code`, where the last two are single replaceable lines. `fix.py` does not parse the JSON, apply the patch, run a compiler/solver, or score the result; it prints decoded text. It uses bfloat16 CUDA, `max_new_tokens=512`, `do_sample=False`, one response, and `return_tensors="pt "` with a trailing space (potential compatibility issue, untested). Its deterministic generation settings differ from the paper's sampling protocol. [fix.py](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/fix.py)

**Scoring is not resolved by the release.** The paper's DPO selection explicitly compares the proposed buggy line with the dataset answer; its final metric describes solving assertion failures without exposing the exact acceptance implementation. The JSON provides golden buggy/fixed lines, which enables text-based comparison but does not establish that the final scores used exact text matching. The vendored SFT metrics compute token accuracy and ROUGE/BLEU, not functional SVA repair success. Neither those metrics nor the pass@k formula specifies the missing repair oracle. Do not conflate line localization, exact repair text, and successful functional verification. [Paper §§III-C, IV-D](https://arxiv.org/html/2503.04057v1), [generic metric source](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train/src/llamafactory/train/sft/metric.py)

**Vacuity, unknowns, and timeouts:** no public task harness defines passing proof versus bounded success, antecedent reachability, vacuous success, four-state/X treatment, unsupported syntax, solver unknown, tool failure, or timeout. One inspected Human `accu` record contains a self-comparison `data_out === data_out` under an implication and a log marked `non_vacuous` for a different property. This is a concrete reminder that a stored log label does not establish coverage of all assertions. No validity claim about that record was tested. A future harness should preserve assertions/specification, distinguish PASS/FAIL/UNKNOWN/TIMEOUT/ERROR, record proof depth and assumptions, and separately check antecedent reachability. Merely removing or weakening assertions is not a valid repair under the intended contract.

**Splits:** the paper describes stratifying by code length and holding out module names. That is narrower than a verified source-parent/template-family split. The release has module names but no training corpora, original source IDs, lineage hashes, augmentation seeds, or split manifest to establish independence across renamed modules or shared templates. Contamination is unverified, not asserted. [Paper §II](https://arxiv.org/html/2503.04057v1)

## Config fidelity and resources

The PT YAML uses full finetuning, cutoff 4096, batch 16/device with accumulation 2, one epoch, LR 1e-4. SFT uses cutoff 8192, batch 4/device with accumulation 2, three epochs, LR 1e-4. DPO uses cutoff 8192, batch 1/device, three epochs, LR 1e-6. These are inspectable starting points, not a fully wired reproduction:

- PT base identifier is `deepseek-coder/deepseek-coder-6.7b-base`, differing from the model card's `deepseek-ai/...`; intended resolution unverified.
- SFT output is `new_sft_without_all_bug`; DPO input is `new_sft_with_all_bug`. `train.sh` sequentially invokes the files without resolving this mismatch.
- SFT names two CoT datasets and does not explicitly name the auxiliary Verilog-Bug corpus. Whether it was merged into those unavailable files is unverified.
- YAMLs reference missing dataset registration and set `report_to: wandb`. No launch or reporting was performed.

Sources: [PT config](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train_pt.yaml), [SFT config](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train_sft.yaml), [DPO config](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train_dpo.yaml), [dataset parser](https://github.com/SEU-ACAL/reproduce-AssertSolver-DAC-25/blob/96882fe018379d1974fd1e1b6c3b8f75e4de3d0e/train/src/llamafactory/data/parser.py).

| Route | Concrete resources | Fidelity loss / boundary |
|---|---|---|
| Static checker exercise | Existing public JSON/source; CPU; small custom parser and line patcher. No GPU or model needed. | Golden-line matching rejects equivalent repairs and can miss semantic errors; supplies no learned repair ability. |
| Final-checkpoint inference | Authorized gated ~13.48GB checkpoint files; Python/PyTorch/Transformers; CUDA GPU. README recommends A800-80GB or advanced NVIDIA GPU. Weight-only F16 footprint is roughly 13.5GB; actual memory adds KV cache, activations and runtime overhead, not measured here. | Much cheaper than training; exact minimum GPU and throughput unverified. Quantization/offload may reduce resources but can alter behavior and were not tested. |
| Functional repair checking | SVA-capable compiler/formal frontend, solver, explicit assumptions/top/reset/proof bounds and status handling. Paper names Icarus/SymbiYosys but no pinned complete task setup is released. | A different frontend or proof policy can change supported SVA semantics and acceptance. An open-source install alone does not establish compatibility with every embedded property. |
| PT/SFT/DPO learning route | Base weights; missing corpora/registration; intermediate checkpoints or retraining; eight A800-80GB paper setup; 20 SFT generations/question for preference mining. | Smaller dataset/LoRA/fewer GPUs can demonstrate stages but changes training regime; no claim of paper-level scores. GPU hours are undisclosed/unverified. |
| Regenerate full data and comparisons | Original corpus provenance, LLM generation prompts/seeds, model service versions, validation scripts/toolchain; historical closed-model outputs or new calls. | High cost; exact historical service behavior may be unavailable. No service/API calls authorized in this audit. |

## One testable gap and control (proposed only)

**Gap:** golden-line agreement and functional assertion repair may disagree, and the released evaluator does not expose the distinction. **Control:** in a later separately authorized check, freeze the released SVAs/specification and proof assumptions, then score each candidate twice: normalized golden-line agreement and functional verification with separate non-vacuity coverage/status. Include an equivalent alternate expression as a positive semantic control and unchanged buggy RTL as a negative control. Retain UNKNOWN/TIMEOUT/ERROR separately instead of crediting them. This would quantify the oracle gap without presuming any defect in the published results. No such check was run.

## Remaining blockers and stop condition

Checkpoint payload access is blocked by the explicit no-gate-acceptance boundary, not by automatic approval review; no access request was submitted. Training corpora, stage checkpoints, task evaluator, proof harness and parent/template lineage remain missing from this snapshot or unverified externally. The requested local audit deliverables are complete; stop here.

## Authorized bounded continuation — evaluator-contract milestone

Completed the independent CPU checker in `independent-port/` on branch `reproduction/assertsolver-dac2025`. All ten reviewed fixture expectations passed in one run. Two fixtures passed the restricted 32-input behavioral check; five matched the golden repair line, including three rejected assertion mutations and one budget TIMEOUT. This is a curated contract control set, not official evaluation or learned repair. Official final scoring and general SVA semantics remain unverified. See `independent-port/RESULTS.md`, protocol, logs and resource ledger. No new remote downloads, installations or model calls were needed.
