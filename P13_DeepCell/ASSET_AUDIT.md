# P13 — DeepCell asset audit

Later authorized methodology work is complete in [CLOSURE_REPORT.md](CLOSURE_REPORT.md); the results below retain their earlier phase scope.

Historical audit-only record. A later authorized CPU pilot is documented separately in [PILOT_REPORT.md](PILOT_REPORT.md); the no-execution statements below describe the earlier audit.

Audited 2026-10-28 in the selected PaperReproduction cloud environment. Asset audit only: public documentation, source, configuration, directory listings, and checkpoint metadata. No repository code, model inference, training, simulation, synthesis, benchmarks, installation, API endpoints, license acceptance, settings changes, or publication were performed. Small public text files were retained under `sources/`; checkpoint/data binaries were not downloaded. This audit concerns method learning, not bit-exact reproduction.

## Verdict

| Route | Level | Confidence | Reason |
|---|---|---|---|
| Minimum faithful multiview learning mechanism on a small, newly prepared paired corpus | **L2 — code / missing low-cost fill**, provisional | Medium | Core encoders, cone masking, fusion, losses, and encoder checkpoint files exist. A small schema-compatible PM/AIG corpus, its preparation bridge, and explicit configuration reconciliation remain necessary. Low-cost is relative to full paper reproduction; it is not a ready-to-run claim. |
| Full paper: reported corpus, ablations, functional ECO and technology-mapping execution | **L3 — code / missing high-cost fill** | High for current public-tree insufficiency; medium for eventual acquisition | Exact processed data/splits, commercial mapping recipe, fused/downstream weights, ABC modifications and downstream preparation/evaluation wiring are not supplied in the inspected tree. Availability elsewhere remains unverified. |

L1 requires direct required assets; L2 permits bounded inexpensive fill; L3 requires expensive fill; L4/L5 require confirmed no code with cheap/high-cost implementation. **L4/L5 do not apply: official model/training code is confirmed.** A PM embedding or probability-prediction demonstration would not establish multiview learning or downstream EDA execution.

## Identity and source boundary

Official repository: [zshi0616/DeepCell](https://github.com/zshi0616/DeepCell), inspected at immutable commit `b82aef22559c6d8c52eb4feb437ebdd32709360e`. Public directory JSON records bind the inspected paths to this commit; retained source files use the same revision.

The [v1 preprint](https://arxiv.org/abs/2502.06816v1), submitted 5 February 2025, is titled **DeepCell: Multiview Representation Learning for Post-Mapping Netlists**. The [v2 preprint](https://arxiv.org/html/2502.06816v2), dated 8 July 2025, and repository use **DeepCell: Self-Supervised Multiview Fusion for Circuit Representation Learning**. The [ICCAD proceedings contents](https://www.proceedings.com/content/083/083042webtoc.pdf) also lists the latter title (page 2401). The supplied publication identifier is [10.1109/ICCAD66269.2025.11240883](https://doi.org/10.1109/ICCAD66269.2025.11240883). Its resolver failed in the browser tool; [IEEE document 11240883](https://ieeexplore.ieee.org/document/11240883) presented a robot-verification page. Thus the proceedings title is corroborated, but the DOI page's final text/metadata was not independently read. Do not conflate an earlier title with a different project.

The browser could read arXiv v2; a later cloud static-text fetch received a tunnel **403** and was stopped without bypass or retry. GitHub tree pages unavailable in the browser reader were accessible as ordinary public cloud HTTP pages. No credentials or account data were used. An unavailable page or unlisted asset is **unverified**, not proof of universal absence.

## Paper route specification

The v2 paper describes probability supervision from 15,000 simulation patterns, paired PM/AIG views (ABC `strash`), and masked-cone embedding reconstruction. Its principal setting uses 5% selected roots, four-hop masking, DeepGate2, four Transformer blocks/eight heads, and 128-dimensional structural plus functional embeddings. It reports 16,072/4,019/1,828 training/validation/test circuits, ForgeEDA/DeepCircuitX sources, three training libraries (Sky130, GSCL45, GF180), Nangate45 testing, and commercial mapping. Reported pretraining uses 8 A800 GPUs, batch 128, and 60 epochs per stage. ECO is functional candidate pruning in `runeco`, with 8,000-circuit finetuning (about 2 GPU-hours); mapping uses cell-type/load guidance in modified `&nf`, with 8,000 samples (about 4 GPU-hours), EPFL inputs, Sky130/Nangate45, and `read_lib -G 250`. These are paper requirements/resources, not measured costs or asset availability. [Source: v2 sections III–VI](https://arxiv.org/html/2502.06816v2).

## What the public code actually provides

All code links below refer to the audited revision; the local copies are in `sources/code/`.

- [PM encoder](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/dc_model.py): accepts 64-channel PM node features, computes DAG structural/functional states, and provides probability and connectivity readouts. It uses GRU updates combining messages and cell features. Thus a faithful input bridge must encode real cell Boolean truth tables with a consistent input-pin convention; generic gate IDs do not replace PM cell semantics.
- [Fusion model](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_model.py): constructs PM and selectable AIG encoders; masks the functional half of selected roots and fan-in cones; keeps structural channels; concatenates PM and AIG tokens per graph; applies Transformer or Linformer; reconstructs the selected modality. The counterpart view must be for the same circuit.
- [Fusion trainer](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_trainer.py): L1 masked-token reconstruction plus probability loss; counterpart probability is recorded as `watch`. Reconstruction compares full returned tokens at masked indices. The optimizer takes all model parameters. Neither encoder is frozen in this path, and `.detach()` appears on targets rather than counterpart inputs. This differs from the paper's stated frozen counterpart encoder and needs an explicit future reconciliation, not an assumption that shipped defaults implement it.
- [Stage-one scripts](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/train_pm.py) set the auxiliary truth-table/connectivity loss weights to zero for probability training. Parsers nevertheless eagerly request the auxiliary fields. Supplying only graph edges and probabilities will not satisfy the current schema unchanged.

### Paired data and correspondence

[prepare_dataset.py](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/prepare_dataset.py) reads `npz/iccad_aig.npz`, `npz/gf180.npz`, `npz/gscl45.npz`, and `npz/sky130.npz` into `data/lcm`. It is a converter for already prepared arrays, not an RTL-to-paired-corpus generator. Training/validation scripts also expect `data/lcm_sample` and `data/lcm_test`. The inspected root has no `npz/` or `data/`; `.gitignore` explicitly excludes both, and the README supplies no corpus download link. Public origin datasets do not establish availability of these derived files or exact extraction/mapping recipes.

[parse_pair.py](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/parse_pair.py) reads each NPZ's `circuits` dictionary. A PM key `pm_name` is paired with AIG key `pm_name + '.aig'`; missing partners are skipped. The pair must fit the **combined** node limit, 4096 by default. It stores distinct AIG and PM graphs, their probabilities and traversal arrays. Required PM fields include `x`, `edge_index`, `is_pi`, `no_edges`, `no_nodes`, `prob`, forward/backward indices and levels, `tt_dis`, `tt_pair_index`, `connect_label`, `connect_pair_index`; AIG dictionaries require corresponding graph/traversal/probability and auxiliary-pair fields. [dataset_utils.py](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/utils/dataset_utils.py) defines separate batching index offsets for AIG and PM.

**No explicit one-to-one cross-view internal-node correspondence is consumed by this fusion implementation.** Matching occurs at circuit-pair level; reconstructed targets retain their own modality's node ordering. A PM cell may expand to several AIG gates. Therefore do not invent an identity node map or pair two unrelated graphs. Preserve each graph's traversal/index consistency, source-circuit identity, Boolean equivalence, and pin/truth-table conventions. Cross-view PI identifiers are not explicitly aligned by `generate_hs_init`; this is relevant preprocessing metadata to clarify rather than a proven missing required alignment asset.

### Real checkpoint files, with limited provenance

[Checkpoint directory](https://github.com/zshi0616/DeepCell/tree/b82aef22559c6d8c52eb4feb437ebdd32709360e/ckpt) lists the following ordinary Git files. GitHub blob-page metadata reports `isGitLfs=false`; binaries were not fetched, unpickled or loaded.

| Path | GitHub display size | Short blob ID |
|---|---:|---|
| `ckpt/aig_dg2.pth` | 7.49 MB | `2f1db27` |
| `ckpt/aig_dg3.pth` | 34.7 MB | `3a6af20` |
| `ckpt/aig_gcn.pth` | 15 MB | `105c7fe` |
| `ckpt/aig_hoga.pth` | 1.8 MB | `0a830a6` |
| `ckpt/aig_pg.pth` | 1.27 MB | `18aa7c3` |
| `ckpt/pm_dg2.pth` | 4.76 MB | `910c0e8` |
| `ckpt/pm_gat.pth` | 3.62 MB | `b2c1037` |
| `ckpt/pm_gcn.pth` | 3.61 MB | `03dd140` |
| `deepcell/pretrained/model.pth` | 7.49 MB | `2f1db27` |

The last entry matches `aig_dg2.pth` in displayed size and short blob ID; this is metadata evidence, not tensor inspection. `top_train.py` explicitly consumes the named encoder checkpoints. There is no named fused Transformer, ECO-finetuned, or mapping-head checkpoint in the inspected complete directory tree. Their status elsewhere is unverified. Epoch, data/split lineage, stage-one versus multiview refinement status, and compatibility have not been established from binary names. The README's broad checkpoint claim does not resolve these details. Loaders allow `strict=False` and can skip mismatching shapes, so a future load without an exception would not alone prove full weight coverage.

### Configuration and dependencies

[environment.yaml](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/environment.yaml) supplies Python 3.9.21, PyTorch 2.0.1/CUDA 11.8, PyG 2.6.1, NumPy 1.24, deepgate 2.0.1, Linformer 0.2.3, py-aiger 7.0 and pinned graph-extension packages. Compatibility and installation were not tested. The README says `pip install -r requirements.txt`, but that file is not present in the inspected root; use the environment manifest as evidence of intended dependencies, not a validated installer.

[run/top.sh](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/run/top.sh) selects four GPUs, local batch 4, HOGA AIG, DG2 PM, AIG refinement, 1% masking, four hops, Linformer and resume. `config.py` instead defaults to 15% masking; `train_pm.py` hardcodes 40 training epochs. `train_aig.py` hardcodes loading `aig_pg.pth` even when selecting another AIG encoder. `top_train.py` passes a two-entry loss-weight list while `set_training_args` accepts a changed list only if it has three entries. These are concrete static configuration gaps, not runtime failure claims; no code was changed or executed.

`utils/sat_utils.py` imports `external.PyMiniSolvers.minisolvers`, but no `external/` tree is supplied. AIG conversion utility paths mention `cnf2aig` and `aigtoaig`; those command-line tools are not installed or verified here. They are distinct from the baseline cached-pair training path. AIG-only simulation helpers do not establish a complete PM standard-cell simulation or library-extraction pipeline.

### Downstream execution boundary

`dc_eco_model.py` exists and supports masked PM encoding, but a suggestive filename is insufficient: the inspected project has no ECO finetuning driver, complete driven-signal ranking interface to `runeco`, modified ABC sources, C++/Python inference bridge, mapping cell-type training head/driver, or executable evaluation wrappers. The complete tree inspected comprises root, `run/`, `ckpt/`, `deepcell/`, and its `arch/`, `utils/`, `pretrained/` subdirectories. `eco_runtime.py` and `ecocase` appear only in `.gitignore`.

[ABC upstream](https://github.com/berkeley-abc/abc) is a concrete tool source, but upstream availability does not supply DeepCell-specific hooks or the exact revision used. [EPFL benchmark source](https://github.com/lsils/benchmarks) is public; exact prepared input AIGs, library corners, constraints, and preprocessing lineage remain unverified. No Liberty files, tool binaries, or technology-library version/corner manifests are bundled in DeepCell. The reported commercial mapping tool is not named precisely enough here to recover an exact flow. No license was accepted.

The task is **functional ECO**: alter Boolean behavior to meet a golden implementation, with formal patch validation. It is not a physical timing ECO flow with placement, routing, extracted parasitics and signoff timing. A timing/area report from mapping does not establish that separate physical task. Similarly, `test_pm.py` evaluates probability error from a PM checkpoint; `val_pm_wview.py` expects a resumed fusion experiment. Neither is end-to-end patch generation or technology mapping.

## Minimum faithful route and substitutions — proposed only

1. Retain the official PM encoder, DeepGate2 AIG encoder, functional/structural channel split, paired-view cone masking and reconstruction/probability objectives. Prepare a small set of genuine, functionally equivalent PM/AIG pairs from a chosen open cell library. Include actual truth-table semantics, traversal arrays, simulation-derived probability supervision, and parser-required auxiliary fields or explicitly document a narrow reader adaptation when those auxiliary objectives are disabled.
2. Start from the available encoder files if their future tensor coverage/provenance checks pass; otherwise pretrain small encoders. Supply an explicit PM-refinement configuration and reconcile frozen-counterpart behavior, masking, loss weights, checkpoint selection and resume paths. Learn the MCM mechanism on the small corpus rather than assuming a pretrained fusion model is released.
3. Leave ABC patching/mapping outside this minimum mechanism. Such a result would support learning the representation method and its reconstruction behavior, not the paper's downstream speed/quality results.

Resource estimate for this small route: existing public source; two default encoder files totaling roughly 12.25 MB (not downloaded); a small paired corpus; CPU preprocessing/simulation plus a suitable single GPU for bounded learning. VRAM and wall time cannot be defensibly specified without execution; no A800 requirement is inferred for a reduced corpus. Paired-data generation is the main L2 uncertainty: if the PM parsing/simulation bridge cannot be obtained or implemented narrowly, revise this route to L3.

| Substitution | Retained | Fidelity lost / limitation |
|---|---|---|
| Small newly prepared open-design corpus | Paired-view learning and self-supervision | Original distribution, scale, sampling, split and numerical comparisons |
| Open synthesis/mapping tool for commercial flow | Real mapped cells and equivalent AIGs | Original mapping topology, cell selection, labels and distribution |
| One open library | PM truth-table encoding | Cross-library/OOD claims and library-specific downstream behavior |
| Available encoders plus newly learned fusion | Core two-view mechanism | Exact released-weight lineage and original training trajectory |
| Single GPU/reduced batch | Architecture/objectives when explicitly preserved | Published optimization schedule and performance claims |
| AIG-only/PM-only embedding demo | One encoder | **Insufficient:** removes fusion and cannot stand in for MCM or downstream execution |

Full-route fill remains high cost: recover exact processed pairs, splits and parent design provenance; map/extract with documented tool/library versions; obtain or train fusion and both downstream heads; implement or obtain DeepCell hooks in ABC with pinned baseline; recover contest patch instances, targets/costs and complete mapping evaluation flow. Exact industrial cases may be inaccessible; this is unverified, not confirmed absent.

## One testable gap and control — hypothesis only

**Hypothesis:** a random pair-level split could place variants/subcircuits of one parent RTL design, or its differently mapped library views, on both sides of validation. `NpzParser_Pair` concatenates library pairs, applies `torch.randperm`, then slices; it does not group by parent design. This is a potential generalization-control gap, not evidence that the authors' actual split leaked: the missing corpus might already separate parents upstream.

**Control, not executed:** obtain a manifest mapping each sample to repository/commit, parent RTL/design, extraction cone and library; group all descendants and library variants of a parent into one partition. Compare the same no-view and multiview models under parent-disjoint splits, using the same held-out library and training budget. Check intersection of parent IDs is empty. This directly tests whether multiview gains persist on unseen parent designs without accusing the current results.

## Deliverables and remaining blockers

`ASSET_AUDIT.md`, `assets.json`, sanitized public tree/checkpoint metadata, and small immutable source snapshots are local in `/workspace/PaperReproduction/P13_DeepCell/`. No experiment has been started. Remaining asset blockers are paired data/preparation lineage, verified fusion/downstream weights, specific ABC integration and library/tool recipes. Access limitations: IEEE verification gate and cloud arXiv 403; both stopped, not pending or bypassed. These limit verification; they are not an automatic-approval rejection and do not require credentials. Audit complete; stop here.
