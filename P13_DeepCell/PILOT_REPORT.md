# DeepCell bounded CPU pilot

Later authorized methodology work is complete in [CLOSURE_REPORT.md](CLOSURE_REPORT.md); the results below retain their earlier phase scope.

Completed 2026-10-28T10:48:23Z on local branch `reproduction/deepcell-iccad2025` in the selected cloud repository. The frozen protocol and three explicit amendments are in `pilot/PROTOCOL.md` and `pilot/PROTOCOL_AMENDMENTS.md`. This reaches the authorized encoder/pair-integrity milestone; no training or downstream run was started.

## Outcome

- **Real checkpoint encoder inference succeeds on CPU.** Upstream active encoder, attention, GRU, MLP and initialization implementations remain unchanged. All 58 retained upstream source hashes match the audit manifest.
- **PM full class is strictly compatible: 56/56 state tensors**, no missing/unexpected keys, shape or dtype mismatches; checkpoint epoch 10.
- **AIG full class is incompatible: 16 missing `connect_head.*` tensors** out of 80 expected. The released file reports epoch 260. The explicitly narrowed encoder-forward + probability-readout instance removes only that unused auxiliary head and strictly loads all 64/64 remaining tensors. No missing head weights were invented. Full-class failure is retained in `pilot/results/full_model_compatibility.json`.
- Six paired synthetic cases (three parent Boolean functions, two PM variants each) pass exhaustive truth-table agreement with an independent direct-expression oracle, including all PM-output-to-AIG internal correspondences. There are **zero disagreements across 40 input assignments**. PI maps, pin order, table length, graph order, mapping coverage and node bounds are checked.
- Parent partitions are XOR/train, MUX/validation, majority/test; all variants stay with their parent. The mismatched same-arity pair, corrupted MUX pin order and contaminated parent split are rejected. These are fixture controls; **the existing checkpoints' pretraining parent separation remains unknown**.
- Each encoder returns finite structural and functional tensors of shape `[node_count,128]`. Fixed-seed repeat is identical. Independent explicit edge attention matches PyG CPU execution within 2.38e-07 (tolerance 1e-6).

## Tiny-case observations

Exact supervision is newly computed by exhaustive enumeration on synthetic teaching cells. It is not an original paper dataset or a surrogate for undisclosed corpus labels. Every selected parent has output marginal probability 0.5; those marginals alone cannot establish Boolean equivalence, which is why exhaustive functional checks are separate.

| Case | Integrity partition | PM/AIG nodes | PM internal probability MAE | AIG internal probability MAE | PM/AIG output prediction |
|---|---|---:|---:|---:|---:|
| xor_v0 | train | 3/10 | 0.0016 | 0.0099 | 0.4984/0.4922 |
| xor_v1 | train | 6/62 | 0.1766 | 0.0857 | 1.0000/0.5460 |
| mux_v0 | validation | 4/27 | 0.0637 | 0.0267 | 0.4363/0.4211 |
| mux_v1 | validation | 7/19 | 0.1417 | 0.0732 | 1.0000/0.3597 |
| majority_v0 | test | 4/26 | 0.0195 | 0.0287 | 0.5195/0.4114 |
| majority_v1 | test | 8/32 | 0.1651 | 0.0401 | 0.6513/0.4914 |

MAEs are descriptive on these tiny inputs, not comparable to the paper's benchmark errors. PM decomposed XOR and MUX outputs saturate at 1.0 despite exact output probability 0.5. This demonstrates a limitation of this checkpoint/feature/input setup, not a measured failure of the paper. The pilot's PI truth-table feature convention (`01` repeated) and simplified PM cell library are explicit; original corpus conventions and lineage are unavailable. No result is omitted for low accuracy and no prediction-quality threshold was used.

## Method and separation

`pilot/paired_circuits.py` is a small explicit reconstruction of preprocessing. MSB-first input-pin order determines each cell's repeated 64-bit truth-table feature. Generic sum-of-products lowering builds AND/NOT AIGs, retaining PI/PO and every PM output signal's AIG correspondence. This preserves Boolean meaning and paired views; it is **not ABC technology mapping, an original Liberty implementation, or the paper's exact structural hashing pipeline**. It does not assert cross-view one-to-one internal-node identity. `pilot/run_pilot.py` builds only fields consumed by encoder inference, without populating fictitious unused training labels or claiming original NPZ compatibility.

The narrow loader in `pilot/adapter.py` avoids the project's eager package imports of irrelevant training/model modules. PyG 2.6.1 is used with Python 3.12.14, PyTorch 2.6.0+cpu, NumPy 2.3.5, CPU and two threads. This differs from the paper environment. `pilot/compat/gcn_conv.py` removes exactly one unused `torch_scatter.scatter_add` import; the diff is saved. DG2 does not instantiate this GCN branch. No upstream source file was patched, no alternative encoder math was substituted, and the full weight loader was never allowed to silently accept missing keys.

## Costs, commands and errors

Setup window 2026-10-28T10:43:35Z to 2026-10-28T10:48:23Z: **288 seconds**, within 2 hours. Two checkpoint downloads total **12,839,534 bytes**; installed-package logs plus checkpoints show approximately **201.8 MB** of payload, comfortably below 2 GB. Pip sizes are rounded, not a packet-level measurement. The successful pilot function took **0.152 seconds** after imports and peaked at **332.3 MiB process RSS**. Venv occupies about 838 MiB on disk. No GPU, paid service, external model API, security setting change or push.

Commands are recorded in `pilot/COMMANDS.md`; raw install/runtime logs, frozen local package list, source hashes, exact checkpoint SHA256 and per-case outputs are retained. Failures were preserved: negative-test fixture had a stale map and was repaired; the first full-model check stopped on absent AIG auxiliary weights. Pip emitted cache permission warnings when listing packages; no permissions were changed.

The one optional wheel-source access attempt at `https://data.pyg.org/whl/torch-2.6.0+cpu.html` failed with a **tunnel 403**. Pip made its own default retries within that invocation before the denial was observed. No follow-up or alternate-source request was made. The blocked optional asset is a CPython 3.12 Linux x86_64 CPU `torch_scatter` wheel compatible with torch 2.6.0 (typically 2.1.2+pt26cpu); it is unnecessary for this DG2 milestone because only an unused import depended on it. This was a network denial, not an automatic approval-review rejection.

## Remaining scope and exact assets to provision

The pilot does **not** complete the minimum faithful MCM learning route: fusion training and learned fusion behavior remain unverified, so the asset-audit minimum route remains provisional L2 and full-paper route L3. The next work is outside this bounded milestone.

Useful user-provided assets would be:

1. Derived paired arrays `npz/iccad_aig.npz`, `npz/gf180.npz`, `npz/gscl45.npz`, `npz/sky130.npz` (and Nangate test data), or compatible processed `data/lcm/inmemory_max_4096/data.pt`, `data/lcm_sample/inmemory_max_4096/data.pt`, `data/lcm_test/inmemory_max_4096/data.pt`; include schema, source design/commit/cone and parent split manifest, pin/table convention, mapping tool/library version/corner, simulation recipe and seed. Exact corpus release/version is currently unverified.
2. A fused `deepcell.top_model.TopModel` state checkpoint from commit `b82aef22559c6d8c52eb4feb437ebdd32709360e`, with PM/AIG encoder choices, refinement direction, dim=128, Transformer/Linformer choice, layer/head/token limits, masking/freeze settings and training provenance. No public named fused file was found; no filename/version is fabricated here.
3. For complete AIG auxiliary connectivity use, the missing 16 `connect_head.*` tensors listed in `pilot/results/full_model_compatibility.json`, or a matching class/version and provenance. They are not required for completed encoder inference.
4. For future ECO/mapping: actual DeepCell ABC `runeco`/`&nf` integration sources and pinned ABC revision; task-finetuned heads/checkpoints with config; patch inputs/targets/costs and/or library corner, constraints and prepared mapping inputs. No mapping or ECO output was generated, so no equivalence-verified downstream claim is made.

The broad Git whitespace check flags preserved upstream snapshot whitespace; authored pilot files pass the scoped check. No upstream bytes were reformatted.

No provision is required to accept the completed CPU milestone. Do not bypass the wheel-source denial or earlier IEEE/arXiv access restrictions. Stop here.
