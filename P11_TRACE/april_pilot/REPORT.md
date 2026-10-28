# TRACE official PM data: bounded checkpoint evaluation

The official industrial PM predictive data and pretrained checkpoint now execute
together on APRIL CPU. This is new real-data evidence beyond the closed synthetic
v1/v2 matrices, which were not rerun. FSL means **function-shift learning**.

## Assets and fidelity

Paper: [TRACE v3](https://arxiv.org/html/2509.21886v3), source commit
`b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70`; reproduction base
`2f33a6bc2135c521af86a0277e3cd3ce8a79b66d`.
The preserved branch contains no AGENTS.md, .agents skills, original prompt file,
EVIDENCE_AUDIT or FINAL_STATUS. Actual ASSET_AUDIT, REPRODUCTION, CLOSURE_REPORT,
MECHANISM_COVERAGE and evidence packet were read; missing documents were not inferred.
All43 preserved generated checkpoint files matched their inventory SHA256.

The prior403 data-access blocker is resolved in this environment. Public
[Hugging Face metadata](https://huggingface.co/api/datasets/zyzheng23/TRACE_dataset?blobs=true)
declares non-gated, CC BY4.0, revision
`5477721c19229f8a21dc2d789a571becb55fbc0f`. The exact PM predictive NPZ is
948,966,544 bytes with SHA256
`6a05e443aeb824b0b47f53e8355572fbafc3aa18f400540ce0306a3791e6ed36`.
Full download on APRIL matched it. There are83,042 circuit entries, matching
the paper's PM predictive graph count. Other modality payloads were not downloaded.

The official PM checkpoint is4,241,614 bytes, SHA256
`19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0`;
all64 state entries loaded strictly. Official MLP/PlainMLP/TRACE classes were
AST-extracted unchanged. No local LLM, external API, GPU or optimizer update.

## Frozen selection and results

Official seed208 torch permutation,90/10 split yields8,305 validation entries.
First8 eligible entries from the first32 were selected before predictions;
all8 passed the4096-node cap. Exact names are in results/selection.json.
They contain4,757 total nodes,2,552 non-PI labels,205 terminal nodes.
All stored forward indices were identity, edges target-grouped, fanins causal and
at most6. Stored operand order was preserved. Dataset labels are supplied simulated
probabilities; their global ground truth was not independently regenerated.

| Inference condition | Weighted non-PI MAE | Weighted terminal MAE |
|---|---:|---:|
| Official original recurrence |0.012932|0.035014|
| Inclusive deepest-level correction |0.011118|0.012432|
| Local independence, zero learned shift |0.053837|0.061788|
| All positional vectors zero, inclusive |0.070898|0.077693|
| Frozen predecessor representations, inclusive |0.036938|0.050448|

Only the separately copied recurrence's loop bound changes in the corrected
condition; original source and checkpoint remain unchanged. Local-only uses the
same supplied truth tables. The hierarchy lesion replaces predecessor hidden
states by initial gate/PI representations while preserving local reconstruction.
Zeroing all positions also removes the operator position: treat it as a broader
position-encoding lesion, not a pure operand-role test.

A supplementary lesion preserves the operator positional vector and collapses
only operand positions. It raises weighted non-PI MAE to0.063255 and residual MAE
to0.047506 (exact aggregate in the supplement JSON). Reversing operands within
each target then changes neural shifts by at most2.31e-7 across8 graphs, confirming
the intended permutation-insensitive control. This is a post-hoc inference lesion,
not evidence of accuracy on swapped circuits or the benefit of retraining an
architecture without ordered operands. See ROLE_DIAGNOSTIC_ADDENDUM.md.

Residual MAE (using supplied predecessor probabilities for residual labels) is
0.008442 for the official model,0.058152 without positions and0.029200 with
frozen predecessor representations. These neural residual metrics separate the
learned network effect from analytic local-function behavior.

Independent scalar64-pattern enumeration checks implementation consistency only;
it does not establish the dataset labels as true global probabilities. It agrees
with corrected source recurrence
within1.06e-6 on every graph. Saved prediction/metric verification passes all8 files;
see results/INDEPENDENT_VERIFICATION.json. Raw per-circuit outputs are retained locally
and on APRIL. No final probability clipping: corrected predictions contain55
strictly out-of-[0,1] values, including numerical and substantive deviations.

## Failures, resources and boundaries

Attempt0: SSH interrupted a checkpoint transfer. Hash assertion stopped execution
before loading; recovered from pinned public URL. Attempt1: the new independent
verifier read PM truth-table bits in ascending order, contradicting the official
descending encoding (`flip(-1)`). Its assertion failed on the first circuit, with
max difference0.853817. Only the verifier index was corrected; no model/data/selection
change. Both failed logs retained. Some SSH commands returned255 after remote
completion; completion is based on saved summary and verified predictions, not
transport status. Logs for public review have machine-specific paths redacted.

Valid primary run:69.015s wall,71.072s process CPU,18.37GiB peak RSS (including
whole-NPZ object loading),Torch2.8.0+cpu, NumPy2.0.2, Python3.9.25, two Torch/BLAS
threads. Source SHA matches the old closure. The new environment is isolated;
initial load~0.2, later~2.6 on192 logical CPUs, with over1TiB available memory.
Setup/download/failure time is additional and not included in the69s. Full NPZ
loading dominates memory even though only8 graphs are evaluated.
The role-specific supplement took65.910s wall,67.432s CPU and18.36GiB peak RSS.

This uses official data/weights and preprocessing tensor semantics, but replaces
Lightning/PyG orchestration with plain Torch, evaluates individual graphs rather
than default batch128/drop_last, and covers a tiny fixed subset. No full-paper
MAE/R2, training reproduction, unseen-design generalization, split contamination
exclusion, trained architectural ablation or cross-modality result is claimed.
Official checkpoint membership in the selected validation split remains unknown.
The old PI-identity aliasing counterexample is not repaired or contradicted.

No paid resource is required for this finite closure. Shared API ledger was not
touched. No push or PR. Upstream checkpoint, official dataset and caches remain
outside the proposed public payload. See publication review and raw-output hashes.

## Third-party text publication review

The new README, evaluation-script and loader-script downloads have no independently
verified redistribution permission. Their copies are excluded from the proposed
public branch, including its rewritten unpublished history. Pinned public URLs,
byte counts and SHA256s remain in asset_receipt.json. No license is inferred from
a public URL or hash. The previously published base is preserved unchanged.
