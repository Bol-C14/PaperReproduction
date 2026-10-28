# P07 VeriThoughts — asset-only audit

Audit date: 2026-10-28 (UTC). Scope: dataset construction and formal-verification evaluator, with released training/model assets checked for completeness. **No reproduction, inference, EDA, compilation, dependency installation, model/API call, large download, setting change, commit, push, or publication was performed.** Source snapshots are inert `.txt` evidence files, not an executed checkout.

## Decision

**Minimum faithful mechanism: L2, provisional Go for a future CPU-only evaluator-contract pilot.** Code and suitable released data exist; the missing local Yosys toolchain and small schema/wrapper work should be low cost. This is not L1: this environment lacks formal tools, the scripts need path adaptation, and static review exposes evaluator edge cases. No runtime feasibility or label agreement has been demonstrated.

**Full paper result route: L3, No-Go on this environment as currently provisioned.** Full SFT and benchmark generation need substantial GPU resources and additional provenance/configuration work. Full dataset regeneration also needs two external model services or an expensive local teacher. Exact historical service versions and availability were not verified. This classification concerns cost and completeness, not the necessity of matching published numbers bit for bit.

Confidence: high that code, dataset listings and three checkpoint file sets exist; high in the statically observed bounded evaluator contract; medium in low-cost pilot feasibility; medium-low in full-result completeness. Checkpoint binaries and dataset payloads were not downloaded or validated.

## Actual selected cloud environment

The selected environment completed startup and returned `ready`. All shell inspection and saved files are in the selected PaperReproduction cloud workspace, not a Mac.

| Observed item | Result |
|---|---|
| OS / kernel / architecture | Debian GNU/Linux 13.6 (trixie); Linux 6.18.55; x86_64 |
| Working paths | `/workspace`; existing `/workspace/PaperReproduction` |
| Local repository | PaperReproduction reports `No commits yet on work`; no replacement repository created |
| CPU / memory | 5 online processors; 17 GiB total RAM; no swap |
| Disk | approximately 30 GiB available on a 32 GiB overlay |
| Runtime | Python 3.12.14; Git; bash; stdbuf; gcc/g++; make; pdftotext available |
| Formal tools | `yosys`, `sby`, `iverilog`, `verilator` not found on PATH |
| GPU | no `nvidia-smi` on PATH; no `/dev/nvidia*` entries observed; GPU access not established |
| Python packages | NumPy, pandas, httpx, certifi present; torch, transformers, vllm, datasets, tqdm, google.genai, openai, deepspeed, flash_attn absent by module lookup |
| Local instructions | no AGENTS.md or SKILL.md found in inspected `/workspace/.agents` and PaperReproduction; `/AGENTS.md` and `/workspace/AGENTS.md` absent |

No environment-variable dump, credential file, secret value, account profile, or authentication test was read. Public metadata access does not establish model endpoint access or runtime readiness.

## Provenance and official source inventory

- [Official repository](https://github.com/wilyub/VeriThoughts), audited `main` at [f44c2af999de62bd27e90e73ce9cbd4f97fbe55c](https://github.com/wilyub/VeriThoughts/commit/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c), commit date 2025-05-16. Full recursive tree returned `truncated=false`, with 25 files. Saved in `repo_inventory.json`.
- [Official NeurIPS 2025 paper](https://papers.neurips.cc/paper_files/paper/2025/file/0c946accd3ccc88c09dfae7e1cd40ffe-Paper-Datasets_and_Benchmarks_Track.pdf), 23 pages; read as source documentation.
- [README](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/README.md) links the author-hosted [dataset collection](https://huggingface.co/collections/wilyub/verithoughts-datasets) and NYU DICE Lab [model collection](https://huggingface.co/collections/nyu-dice-lab/verithoughts-models).
- [GitHub releases](https://github.com/wilyub/VeriThoughts/releases) explicitly shows no releases. Code is available through repository commits, not a versioned release bundle.

Main code assets:

| Path | Role / completeness |
|---|---|
| `verithoughts/multi-turn-yosys-generation.py` | MetRex loading/filtering; V-to-Q Gemini calls; Q-to-R/V* DeepSeek calls; Yosys labels; JSONL writing |
| `evaluation_verithoughts/evaluation_script.py` | Parsing, module renaming, Yosys invocation, return-code labels, pass@k |
| `evaluation_verithoughts/verilog_vllm_multi.py` | Local BF16 vLLM generation, repeated samples, benchmark `verified` filtering |
| `training/verilogFinetune/train_*.sh` | Seven launchers: six subset conditions and a 14B reasoning variant |
| `training/verilogFinetune/ds_config_zero3.json` | DeepSpeed ZeRO stage 3 configuration |
| `training/verilogFinetune/data/dataset_info.json` | Six local JSONL filename mappings to instruction/input/output |
| `verilog-eval/` | Generation code, evaluation notebook, four closed-service generation wrappers; external benchmark installation required |

No LICENSE file, automated tests, dataset-splitting/preparation script, lockfile, packaged formal toolchain, inference result archive, training logs, or 32B launcher appears in the complete audited tree. These are repository-inventory findings, not claims that such assets cannot exist elsewhere. GitHub metadata reports `license=null`; one inference file has an Apache-2.0 SPDX header, which does not establish a repository-wide license.

## Released data and models

| Asset | Evidence / size / status |
|---|---|
| [VeriThoughtsBenchmark](https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark/tree/main) | `hf_benchmark.jsonl`, 571 kB; tree total 574 kB; displayed revision `83179e5`. Viewer lists 291 rows, four fields: ground_truth, question, generated_verilog, verified; visible verified values are true. No reasoning trace column listed. |
| [VeriThoughtsTrainSet](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSet/tree/main) | `hf_complete_trainset.jsonl`, 399 MB; revision `75e905d`; viewer approximately 20.2K rows and fields ground_truth, question, generated_verilog, verified, reasoning_trace. |
| [ConsistentInstruction](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetConsistentInstruction/tree/main) | `lf_complete_trainset_instructions.jsonl`, 17.1 MB, revision `fb60a7a`; matches dataset_info mapping. |
| [ConsistentReasoning](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetConsistentReasoning) | Viewer exposes approximately 10.1K rows with instruction/input/output and reasoning text; file-tree fetch unavailable. |
| [InconsistentInstructionGEN](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetInconsistentInstructionGEN) / [GT](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetInconsistentInstructionGT) | Both listed in official collection at approximately 10.1K rows; individual file trees unreachable in this audit. Payload completeness unverified. |
| [InconsistentReasoningGEN](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetInconsistentReasoningGEN/tree/main) | `lf_failed_trainset_reasoning_gen.jsonl`, 286 MB, revision `0ee6a2b`. |
| [InconsistentReasoningGT](https://huggingface.co/datasets/wilyub/VeriThoughtsTrainSetInconsistentReasoningGT) | Listed in official collection at approximately 10.1K rows; individual file tree unreachable. |
| [MetRex](https://huggingface.co/datasets/scale-lab/MetRex) | Upstream source; viewer approximately 25.9K rows, RTL plus synthesis/PPA text; BSD-3-Clause metadata. |
| [Reasoning-7B](https://huggingface.co/nyu-dice-lab/VeriThoughts-Reasoning-7B/tree/main) | Four safetensors shards (4.88/4.93/4.33/1.09 GB), weight index, tokenizer and config files; total 15.2 GB; revision `cd09b43`. |
| [Instruct-7B](https://huggingface.co/nyu-dice-lab/VeriThoughts-Instruct-7B/tree/main) | Four shards, index, tokenizer/config; total 15.2 GB; revision `ded4527`. |
| [Reasoning-14B](https://huggingface.co/nyu-dice-lab/VeriThoughts-Reasoning-14B/tree/main) | Six shards, index, tokenizer/config; total 29.6 GB; revision `6bee440`. |

Dataset pages inspected advertise MIT metadata. That does not by itself establish a full per-design upstream license chain for scraped/repackaged RTL. The Reasoning-7B model card is an autogenerated template with license, base-model provenance, training data and evaluation sections left unspecified. Model file lists establish release presence, not usable downloads or correspondence to every paper ablation. The official collection lists only these three models; 32B/Qwen3 variants and checkpoints for all six ablations are not confirmed there. Do not infer global absence.

Model config files are listed but their contents could not be retrieved through the web tool. No weight hashes or weight/index consistency were checked. Some pages were served from older web caches; displayed abbreviated revisions are metadata observations, not downloaded immutable payload verification. No gated terms were accepted.

## Mechanism and equivalence contract

The generation source implements V → Q → (R,V*) → label. It loads MetRex, keeps RTL shorter than 10,000 characters, sorts by prompt length, asks Gemini for an interface-preserving question with delimiters, then asks DeepSeek for reasoning plus delimited Verilog. It writes golden/generated RTL, Q, reasoning and a Boolean label. The two teacher model identifiers are `gemini-2.0-flash-thinking-exp` and `deepseek-reasoner`; no historical snapshot pin is supplied. See [generation source](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/verithoughts/multi-turn-yosys-generation.py).

The reusable methodological unit is **formal behavioral agreement between independent code paths as a proxy for question/answer consistency**. It is not a proof that Q is complete or that the reasoning R is sound: R and Q are never formal inputs to the checker. Their validity remains an interpretation of the agreement label.

The [evaluator](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/evaluation_script.py) regex-discovers golden modules, renames them by appending `1`, then checks every corresponding named module, not only the top-level interface. For each pair it runs `read_verilog`, preparation/optimization/memory passes, `clk2fflogic`, a flattened equivalence miter, and SAT with `-seq 50`, `-prove trigger 0`, `-verify`, and `-set-init-zero`. All module subprocess return codes must be zero; each invocation has a Python 150-second timeout. The shell sources an OSS CAD Suite environment file before invoking Yosys.

The [Yosys 0.41 SAT documentation](https://yosyshq.readthedocs.io/projects/yosys/en/0.41/cmd/sat.html) defines `-seq` as finite time steps and `-set-init-zero` as setting otherwise unspecified initial state to zero; temporal induction requires an additional option absent here. **Sequential success therefore supports bounded agreement under these initialization assumptions, not unbounded equivalence or all possible initial states.** Clock conversion means SAT steps must not casually be equated to 50 rising clock edges. There is no explicit parameter sweep or reset/clock environment constraint in the script. Combinational equivalence can still be exhaustive over the modeled input space.

## Testable gaps: evidence separated from hypotheses

1. **Confirmed static contract limitation:** finite horizon and initialization restrictions above. A delayed divergence can escape the bound. Dataset-level impact is unknown.
2. **Confirmed static empty-check defect:** if the golden-module regex finds no modules, the subprocess result list stays empty; the success test compares zero successful checks to zero total checks and returns true. No released sample has been shown to trigger this. A future fixture with a legal no-port or escaped-name module can test reachability without any model call.
3. **Confirmed static label conflation:** compilation/tool failures and counterexamples both become failed checks; timeout exceptions use -1. The JSONL stores return codes, not logs or a reason taxonomy. Thus `verified=false` does not isolate an incorrect question or an actual behavioral mismatch.
4. **Confirmed static aggregation fragility:** evaluation appends to an existing output file and groups by row position, with no sample-ID/count validation. Repeated or interrupted runs could contaminate pass@k. No published score is demonstrated wrong.
5. **Potential parser/renamer failures:** regex handling excludes some legal HDL syntax; whole-word replacement can affect non-module identifiers or collide with existing names ending in `1`. Per-module matching can reject a correct top-level design that reorganizes helper modules. These need controlled fixtures and log inspection.
6. **Potential current schema drift:** MetRex's current viewer labels RTL as strings, while the generation script indexes RTL entries as dictionaries with `ground_truth`. The script also writes `reason_list`, while released data uses `reasoning_trace`; no conversion script is in the audited tree. Verify adapters before any regeneration; no runtime schema failure was tested.
7. **Scientific hypotheses:** agreement may reward shared teacher omissions; reasoning generated for V* may contradict a substituted golden V target; consistency filtering can select simpler designs. Future tests should separate prompt fidelity, trace fidelity, structural complexity and formal status. These are research questions, not verified paper errors.

## Dependencies and concrete cost

[Generation requirements](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/verithoughts/requirements.txt): datasets 3.3.2, google-genai 1.7.0, openai 1.65.1, httpx 0.28.1, certifi 2025.1.31, tqdm 4.67.1. Requires external teacher accounts for regeneration; credentials and current service access were not inspected.

[Evaluation requirements](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/requirements.txt): NumPy 1.26.4, tqdm 4.67.1, vLLM 0.7.3, huggingface-hub 0.29.1. CPU evaluator itself imports NumPy and standard library; vLLM/GPU inference is separable. Yosys/OSS CAD Suite is an external dependency, not included. README links Yosys 0.41 documentation but does not pin the actual suite build.

[Training requirements](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/training/requirements.txt): flash-attn 2.7.4.post1, deepspeed 0.16.7, tf-keras 2.19.0, plus separately installed LLaMA-Factory, Torch/CUDA and base models; LLaMA-Factory revision is unpinned. Launchers hard-code `/home/ubuntu` paths. They use eight workers, full SFT, BF16, 16,384-token cutoff, batch 1 per device, accumulation 2 and ZeRO-3.

| Future route | Resource assessment |
|---|---|
| Evaluator-only pilot | No GPU/API/checkpoint needed. Start with Python/NumPy, CPU Yosys, small released pairs and small source files. Proposed budget: 1–2 CPU workers, 2–8 GiB process memory cap, under 1 GB task data excluding toolchain. These are planning limits, not measured requirements. Current 17 GiB host is plausible for tiny circuits; difficult arithmetic/memory designs can exceed them. |
| 20-pair pilot latency | At the source timeout, 20 one-module pairs allow up to 50 minutes of serial subprocess waits; multiple modules increase this. Typical time is unknown. This is a timeout ceiling calculation, not a benchmark. |
| 7B checkpoint inference | Listed weights alone are 15.2 GB, before KV cache/runtime overhead; 17 GiB host RAM offers little margin. A 24–48 GB GPU with reduced batching is a planning estimate for a small BF16 pilot, not a verified minimum. README's example uses tensor parallelism 4, batch 100 and 20 samples; the current cloud has no established GPU. |
| Full benchmark generation | 291 × 20 = 5,820 completions per model, each configured for up to 16,384 new tokens. Actual token volume, latency and memory are unknown. |
| Full SFT | Paper reports 8×A100: approximately 2–4 hours for instruction models and 7–14 hours for reasoning models, or 16–32 and 56–112 GPU-hours per run. A100 memory variant and host RAM are unspecified. This is author-reported, not measured here. Multiple ablations multiply cost. |
| Full dataset regeneration | Roughly 25K filtered source designs, at least a question call plus a reasoning/code call each, with retries and outputs up to 8,192 tokens per service call. Requires material API spend or large teacher hosting resources; no current price quote or endpoint availability established. |

A single 14B checkpoint listing is 29.6 GB, nearly the current free disk capacity before caches, dependencies and outputs; planning a full result route needs a larger disk as well as GPUs.

## Minimum faithful future pilot and substitutions

**Minimum module:** take stored V and V* with Q/R as annotations; preserve the official miter, preprocessing, bound and initialization assumptions; produce module-level statuses and diagnostics. Start with approximately 10–20 small released tuples and synthetic controls. Fix or guard empty discovery and isolate each sample's temporary files; retain an original-behavior result alongside guarded behavior so semantic changes are explicit. No teacher inference or training is necessary to study the core labeling mechanism.

**One useful mechanism test:** a boundedness challenge using two tiny sequential designs that agree from zero for the original 50 SAT steps but diverge only later. Compare the unchanged checker with a longer horizon (or an inductive checker) and retain the first counterexample. Include identical and immediate-mismatch controls. Expected distinction: a bounded pass can coexist with eventual inequivalence. Design the delay in SAT time steps after `clk2fflogic`, then inspect the witness; do not assume a clock-cycle mapping. This is a proposal only and has not been executed.

| Substitution | What it preserves | Semantic loss / changed claim |
|---|---|---|
| Released tuples instead of regenerating teachers | Formal label mechanism, stored provenance fields | Does not validate current V-to-Q/Q-to-V* construction or API cost |
| CPU Yosys without vLLM | Published formal preprocessing/checking | No generation-performance evidence |
| Small present-day teachers | V→Q→R/V*→label architecture | Changes question noise, reasoning distribution and consistency rate; historical model equivalence not assumed |
| Quantized 7B local inference | Practical code-generation experiment | Changes numerical behavior and sampling; not the BF16 inference setup |
| LoRA/QLoRA on a subset | Directional reasoning-vs-instruction learning test | Does not reproduce full SFT, training capacity, or paper-sized comparisons |
| Simulation as quick diagnostic | Some concrete behavioral mismatches | Cannot replace formal labels or preserve exhaustive input coverage |
| Induction / richer initial/reset assumptions | Stronger contract investigation | Changes the evaluator and labels; report separately from original results |

Go is conditional on a separately authorized execution stage: obtain a small pinned public data slice, provision Yosys, resolve schema/path adapters and specify resource caps. Current task ends at this audit. Full training remains No-Go here; it requires a separately provisioned GPU budget and better model/configuration provenance.

## Access limits and remaining blockers

The first shell public GitHub API request was denied by the network proxy with HTTP 403; web API/directory fetches also failed. No escalation, credential change or repeated shell download was attempted. The available approved GitHub connector successfully supplied repository metadata, contents and immutable tree/source reads, resolving repository inventory access. Several Hugging Face raw/config and subset-tree URLs remained unreachable; they are **unverified**, not absent. No auto-review rejection occurred and no approval is pending.

Still unresolved: local Yosys/toolchain, compatible runtime provisioning, model license/provenance, historical teacher availability, full ablation checkpoints, exact data preparation/split lineage, subset payload completeness for inaccessible trees, and the dataset-level frequency of identified evaluator edge cases. These block a direct L1 claim, not the documentary conclusion or a future small mechanism pilot.
