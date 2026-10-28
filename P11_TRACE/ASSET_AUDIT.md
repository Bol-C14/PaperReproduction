# P11 — TRACE: Learning to Compute on Circuit Graphs

Asset-only audit, 2026-10-28, selected PaperReproduction cloud environment (`/workspace`). Goal: learn the method, not bit-exact benchmark reproduction. No experiments, model inference, training, EDA, installation, hosted API calls, settings changes, license acceptance, account sharing, or publication performed.

## Verdict and five-level classification

| Route | Level | Confidence | Basis |
|---|---|---|---|
| Minimum faithful mechanism: ordered hierarchical computation **and** function-shift learning | **L2 — code / missing low-cost fill** | High for code; medium for effort | Backbone tutorial is complete as a walkthrough. Add a small synthetic reconvergent Boolean dataset in the existing AIG schema and use the supplied covariance-training/reconstruction path; learning and evaluation controls are still needed. No need for the full hosted corpus or EDA for method learning. |
| Tutorial backbone walkthrough alone | **L1 — code / direct required assets** | High, static inspection only | Four small Python source files construct 4–9-node arithmetic DAGs locally. No checkpoint or external graph corpus required. This is a narrower deliverable than the whole TRACE mechanism. |
| Full paper, all modalities/tasks/ablations | **L3 — code / missing high-cost fill, provisional** | Medium | Only three checkpoint paths are present at the pinned commit; dataset contents are inaccessible here, and complete task-to-asset/config coverage is unverified. Missing local RTL/AIG predictive checkpoints can require training; sequential/similarity/transition and baseline coverage needs reconciliation. L3 describes an unclosed high-cost route, not proof that assets do not exist elsewhere. |

Scale: L1 code/direct required assets; L2 code/missing low-cost fill; L3 code/missing high-cost fill; L4 confirmed no code/cheap implementation; L5 confirmed no code/high cost. L4/L5 do not apply: official code is verified.

## Version and official sources

- [Paper v3](https://arxiv.org/html/2509.21886v3), arXiv 2509.21886v3, dated 16 June 2026; inspected public HTML.
- [DAC publication identifier](https://doi.org/10.1145/3770743.3803923): supplied DOI resolves toward ACM; browser retrieval failed. Publication landing-page metadata was not independently verified.
- [Official repository](https://github.com/zyzheng17/TRACE_DAC26), pinned via Git HEAD to `b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70`, commit timestamp `2026-06-12T11:07:03+08:00`, message `update readme`. Repository snapshot predates paper v3 by four days; exact version equivalence is unverified.
- [Official dataset link](https://huggingface.co/datasets/zyzheng23/TRACE_dataset/tree/main), referenced by repository README. Public page retrieval unavailable; cloud HTTP connection returned 403. Stopped; no gate bypass or dataset payload download. Reported **9.28 GB is user-supplied/unverified**, not a measured size. Dataset revision, filenames, per-file sizes, hashes, and license are unverified.

All repository source links below are immutable commit URLs. `assets.json` records individual URLs and provenance.

## What must remain faithful

The paper’s mechanism processes nodes by dependency level and applies a Transformer to `[operator, ordered inputs]`, retaining the operator-token output as an intermediate result. Position/port roles and hierarchy matter. Predictive function shift is global probability minus a local independence approximation; inference reconstructs probabilities recursively from predecessor estimates plus learned shifts. Contrastive learning is a separate functional-retrieval objective.

The three graph modalities are **separate representations/tasks**. Neither their presence nor the tutorial’s unified graph explanation establishes aligned cross-layer node correspondence, paired RTL–AIG–PM supervision, or a cross-modal matching objective.

## Actual tutorial inspection

Sources: `computational_graph/{README.md,demo.py,expr_graphs.py,model.py,data.py}`.

- `demo.py` builds one arithmetic DAG, assigns x/y values, computes an analytic scalar target, initializes a fresh model, calls `model.eval()` and one `torch.no_grad()` forward pass, then prints the trace. It contains no optimizer, training loop, or checkpoint load. The target is not used to train or demonstrate accuracy.
- Defaults: x=3, y=5, modulus=97, hidden=64, one Transformer layer, four heads, batch=1. `--use_cpu` is available. Eight expression templates have 4–9 nodes; subtraction is included, MUX is not.
- `model.py` sorts predecessors by explicit `edge_pos`, uses operator/input positional embeddings and level-by-level updates, and reads out the output node. Only torch and torch-geometric are directly imported by this path. Installed dependency compatibility was not checked.
- **No FSL in this tutorial.** It is a small architecture walkthrough, not a pretrained inference demo, a training reproduction, or evidence of learned functional behavior.
- README’s top-level tutorial command points to `tasks/tutorial/computational_graph`, which is not in the pinned tree. Actual files live at root `computational_graph/`; a future run would need the corrected directory.
- `topological_levels` iterates numeric node indices and assumes the templates’ topological numbering. A rename control must transport the already-valid levels/index mappings or recompute a true topological order; rerunning this helper on arbitrary IDs can confound the test.

## Actual full-task code and checkpoint inventory

| Asset at pinned repository commit | Bytes | Git blob ID | Role / limits |
|---|---:|---|---|
| `checkpoints/trace_contrastive_aig_rec.ckpt` | 13,308,852 | `06c56708f1cf304c43ceddd7272d5ec631c30729` | AIG retrieval eval default |
| `checkpoints/trace_contrastive_pm_rec.ckpt` | 10,402,566 | `6d2ecec507fffe789532281309bd73c25f67ce96` | PM retrieval eval default |
| `checkpoints/trace_predictive_pm_probability.pth` | 4,241,614 | `14a73f6e0b4f9f19584681eec95a34ea9866f51a` | PM FSL reconstruction eval default |

These are actual Git-tree entries, not README promises. Git object-size inspection materialized their binary objects (27,953,032 bytes total); they were not deserialized, loaded into a model, or executed. No checkpoint payload semantics, training provenance, tensor shapes, or numerical compatibility was verified. The local metadata repository occupies about 27 MiB of Git storage.

At this commit the tree does not contain the default `trace_contrastive_rtl_rec.ckpt` or `trace_predictive_aig_probability.ckpt` paths referenced by evaluation scripts. This is confirmed repository-path absence only; availability elsewhere remains unverified. No separate sequential/transition/similarity checkpoint paths were found in this tree.

Task loaders require:

- RTL contrastive: `data/rtl/dataset_graph/data_bench/dataset_{train,valid}_{ori,pos}.pkl` (four graph-pair pickles).
- AIG contrastive: `data/aig/forgeeda_pm_aig_{train,test}.pt` (eval uses the `_test.pt` file).
- PM contrastive: `data/pm_netlist/forgeeda_pm_pair_pkl_{train,test}.pt`.
- AIG predictive: `data/aig/aig_predictive.pt`; graph list with `name`, `prob`, gate/edge/level/index metadata. Validation names default to `b12_opt_C`, `b14_opt_C`. Loader derives AND-gate covariance labels from target probability minus product of fanin probabilities. `--learning_target probability` is the default; **use covariance to select FSL**, with `cov2prob.py` reconstructing probabilities at evaluation. Data ordering assumptions must be retained.
- PM predictive: `data/pm_netlist/iccad_dc_pm.npz`, key `circuits`, each circuit with `x`, `edge_index`, `prob`, forward/backward levels and indices. Cell feature/truth-table encoding and fanin order must agree with `_cop`. Training regresses shift; evaluation calls `_cop_with_cov`. Eval default split=0.9, seed=208, `drop_last=True`; train seed defaults to None. Explicit matching split/seed is needed for comparable results.

These filenames are **code-required names, not verified hosted filenames**. No circuit payload was downloaded or inspected. The README mentions an RTL preprocessing path `tasks/contrastive/rtl/data_prep`, but it is absent from the pinned tree. Repository requirements are unpinned, so no exact environment lock is supplied.

## Resources and cost uncertainty

| Route | Concrete needs | What remains uncertain |
|---|---|---|
| Tiny tutorial | CPU, Python, torch, torch-geometric; four core files; no data/checkpoint | No runtime or RAM measured; not a learning experiment |
| Minimum faithful learning | Small role-preserving DAGs plus reconvergence; exact truth-table labels for a few PIs; existing AIG covariance encoder/trainer/reconstructor; CPU initially plausible | Estimated low engineering/compute cost, not benchmarked; schema adaptation and validation controls required |
| Partial checkpoint evaluation | Above checkpoint(s), corresponding graph test payload, compatible torch/PyG and task dependencies; CPU flag supported, GPU preferable for full corpus | Checkpoint/config compatibility and data contents unverified; CPU support does not imply a practical full CPU run |
| Full paper training | Full graph corpora, labels/splits, task-specific models, baselines and ablations, GPU training; extra EDA tools only if graphs must be regenerated | No verified GPU model, VRAM requirement, wall-clock or GPU-hour budget; cannot give defensible dollar cost |

Code defaults: AIG/PM contrastive batch 1024 ×100 epochs; RTL batch 32 ×500; AIG predictive batch 1 ×200; PM predictive train defaults batch 128 ×40, while its README example requests batch 512 ×200. Defaults/examples are not a validated paper run manifest. If 9.28 GB is later confirmed, allow additional storage for processed caches, Python object expansion and logs; their multiplier is unmeasured. Do not infer RAM from archive size. No environment or GPU capability probes were run.

## Substitutions and fidelity loss

- Small synthetic Boolean DAGs can preserve ordered hierarchy, reconvergence, local/global probability distinction and FSL reconstruction; they lose industrial circuit distribution, scale/depth, sequential behavior and benchmark claims.
- Arithmetic tutorial preserves ordered hierarchy but loses probability FSL and all learned-performance evidence; calling it full TRACE reproduction would overstate it.
- AIG-only learning loses RTL MUX/subtraction role diversity and PM cell truth tables; it is useful for FSL, not proof of general input-role handling.
- Checkpoint-only evaluation avoids training cost but cannot establish the training objective’s benefit or reproduce training/ablations.
- Random labels, unordered fanins, node-ID-derived port roles, or missing reconvergent cases break the relevant mechanism and are unsuitable substitutes.

## One testable gap and matched control — proposal only, not executed

**Gap:** input-role preservation versus incidental node numbering has not been validated end to end in the audited assets. Tutorial levels assume topological IDs; RTL additionally initializes PI embeddings by index order. This is a test condition, not an accusation or a result.

With fixed model weights and semantic input identities, compare (A) a bijective node-ID rename that transports every node tensor, edge endpoint, valid level/index mapping and output index while preserving port roles, against (B) an actual role change: swap SUB minuend/subtrahend or MUX select/data ports, keeping node identities fixed. Preserve semantic PI identity encodings in A; independently vary edge storage order while retaining explicit ports/grouping. Expected control: A preserves semantic output; B changes it on nondegenerate inputs. For SUB use x != y and modulus avoiding equality; for MUX use differing data inputs and a discriminating select assignment. ADD/AND swapping is a commutative negative control. Random fresh weights can test structural behavior but cannot establish learned correctness; use trained weights and exact targets for that later. For FSL, add a tiny reconvergent case with a nonzero analytic shift and compare direct regression against covariance/FSL under matched splits. No execution authorized now.

## Remaining blockers and stop state

Dataset metadata request was blocked by cloud HTTP 403; access is unverified, not absent. ACM retrieval failed. Full-route asset mapping, checkpoint compatibility, full-task coverage, dependency versions and compute budget remain unverified. No further dataset access attempt was made after the 403; no model execution was performed. Audit complete; stop at these files.

## Pinned source index

- [README.md](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/README.md)
- [requirements.txt](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/requirements.txt)
- [computational_graph/README.md](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/computational_graph/README.md)
- [computational_graph/demo.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/computational_graph/demo.py)
- [computational_graph/expr_graphs.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/computational_graph/expr_graphs.py)
- [computational_graph/model.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/computational_graph/model.py)
- [computational_graph/data.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/computational_graph/data.py)
- [tasks/contrastive/rtl/eval.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/rtl/eval.py)
- [tasks/contrastive/rtl/models/trace_encoder_impl.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/rtl/models/trace_encoder_impl.py)
- [tasks/contrastive/aig/train.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/aig/train.py)
- [tasks/contrastive/aig/eval.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/aig/eval.py)
- [tasks/contrastive/pm/train.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/pm/train.py)
- [tasks/contrastive/pm/eval.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/contrastive/pm/eval.py)
- [tasks/predictive/aig/train.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/aig/train.py)
- [tasks/predictive/aig/eval.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/aig/eval.py)
- [tasks/predictive/aig/dataset/loader.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/aig/dataset/loader.py)
- [tasks/predictive/aig/models/trace_core.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/aig/models/trace_core.py)
- [tasks/predictive/aig/models/cov2prob.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/aig/models/cov2prob.py)
- [tasks/predictive/pm/train.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/train.py)
- [tasks/predictive/pm/eval.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/eval.py)
- [tasks/predictive/pm/dataset/loader.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/dataset/loader.py)
- [tasks/predictive/pm/models/trace_trainer.py](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/models/trace_trainer.py)
