# GenEDA bounded CPU validation

**Milestone reached: original-source alignment-interface checks pass; semantic alignment and end-to-end generation are not established.** Work used the existing `Bol-C14/PaperReproduction` cloud workspace on local branch `reproduction/geneda-iccad2025`. No push occurred. The branch was absent remotely when inspected, so this is a new local branch within the same repository, not a new repository or thread.

## Results

| Check | Observed result | Meaning |
|---|---|---|
| Graph schema | Both tasks: 462 rows, 768 finite values each, valid human/assistant target turns, one `<image>` marker per input | Released payload fits the interface. |
| Cross-task pairing | All 462 matching numeric IDs have exactly matching graph vectors | Features are consistent across the two task views; this does not establish provenance against the original circuit. |
| Graph-to-text reference joins | Task 1: 458 unique exact-label matches plus 4 ambiguous row matches within the same module. Task 2: 445 unique, 4 ambiguous within module, 13 unmatched/ambiguous groups | Do not align graph/text rows solely by their row number. Four Task 1 pairings cannot identify a unique text row. |
| Parent identity | No explicit parent design IDs. Task 1 joins yield 7 module-name groups | Module names are grouping proxies. Distinct VexRiscv variants can share ancestry across groups; no claim of independently verified parent-disjoint evaluation. |
| Distinct features | 199 distinct float32 vectors across 462 rows; 263 repeated rows beyond first occurrences | Counts are not independent circuit counts. Repeated features might reflect augmentation, shared outputs or an asset/export issue; this check does not choose among explanations. |
| Frozen fixture split | 96 train / 32 validation / 32 test, grouped by module proxy, excluding 13 cross-task join disagreements; no feature-hash overlap across splits | Educational integration fixtures only; not the original paper split. |
| Original-source tests | **11 passed, 0 failed, 0 errors**, first run | Projection, insertion, batching, masks, padding and gradients operate with the fixtures. |
| Fixed synthetic connector optimization | Initial MSE `0.9838837981` → `0.9200732708`, 40 AdamW steps; shuffled-input training MSE `0.9200732708` | Optimization path works, but there is no observed matched/shuffled separation. Random targets and training-set loss cannot test semantic alignment or generalization. |
| Feature spread diagnostic | Maximum distance from first graph `2.0580841e-4` relative to an approximately unit-norm vector; first 16 frozen training rows: `7.191033e-6` | The released vectors are strongly concentrated. This limits this fixture's use as evidence of informative circuit-conditioned generation. It does not prove that the original encoder is defective. |

Raw outputs: [integrity.json](results/integrity.json), [pairing_map.json](results/pairing_map.json), [split_manifest.json](results/split_manifest.json), [alignment_tests.json](results/alignment_tests.json), [feature_discriminability.json](results/feature_discriminability.json), and [resource_ledger.json](results/resource_ledger.json). Per-step synthetic loss is retained in `alignment_tests.json`.

## Exact tested interface

The unmodified pinned source reads graph vectors from each `conversations` record; the original collator stacks them as `[batch, 768]`. The original projector `mlp2x_gelu` is a linear layer from 768 to decoder hidden width, GELU, then another linear layer at decoder width. `encode_graph` casts to the model dtype before projection. `prepare_inputs_labels_for_multimodal` replaces the `IMAGE_TOKEN_INDEX` position with the projected token and masks its target with `IGNORE_INDEX`; surrounding text embeddings and answer labels remain in place.

The harness executes the original projector builder and AST-extracted, unmodified `encode_graph`, `prepare_inputs_labels_for_multimodal` and original collator. Source SHA-256 hashes are checked before execution. Surrounding Transformers/LLaVA imports are excluded to avoid loading a decoder. Test language embeddings are a frozen random lookup table. Width 32 bounds the integration/gradient fixture; width 2048 is only a dimensional fixture check, **not a verified downloaded decoder configuration**. The original decoder config metadata URL returned proxy HTTP 403 and was not retried.

Two practical boundary cases are captured: missing `<image>` silently yields text-only embeddings even though graph projection occurs, and truncation before the marker can eliminate the graph token. Actual released graph prompts each pass the marker count check. These tests are diagnostic checks of a public interface, not allegations about any original evaluation.

## Original, adapter and method port

- `upstream/` contains byte-for-byte copies of three selected official source files at commit `0a19fde3f1c1e56f49a367bf5f1914de84e1c951`; provenance and hashes are in `results/integrity.json`. No upstream source repair was made.
- `check_assets.py` and the test harness are new adapters. Exact-label matching provides an auditable join; it does not alter labels or repair ambiguous original pairings.
- The random width-32 word table and synthetic regression target are **unit-test scaffolding**. They are not a method port to a substitute semantic task and are not trained language generation. No generic LLM, TF-IDF answer generation or hand-written arithmetic annotations were used.

The earlier L2 minimum remains a provisional planning classification, not a completed semantic reproduction. Full new-netlist encoding remains L3. The new evidence prevents promoting the released fixed features plus successful unit tests to a validated aligned-learning result.

## Commands

From `/workspace/PaperReproduction`:

```bash
# The already available original source clone contains the four cached JSON blobs.
# No new source dataset download was needed in this continuation.
OPENBLAS_NUM_THREADS=1 python P12_GenEDA/validation/check_assets.py

# Executed once: official CPU wheel, no dependencies fetched, isolated installation.
python -m pip download --no-deps --retries 0 --timeout 20 \
  --index-url https://download.pytorch.org/whl/cpu 'torch==2.5.1+cpu' \
  --dest P12_GenEDA/validation/downloads
python -m pip install --no-deps --no-index \
  --target P12_GenEDA/validation/runtime \
  'P12_GenEDA/validation/downloads/torch-2.5.1+cpu-cp312-cp312-linux_x86_64.whl'

# Executed once; source-derived methods, no model/weight loading.
PYTHONPATH="$PWD/P12_GenEDA/validation/runtime" \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 \
  python P12_GenEDA/validation/test_alignment.py

# Targeted diagnostic authorized by the frozen addendum; no additional fitting.
OPENBLAS_NUM_THREADS=1 python P12_GenEDA/validation/check_discriminability.py
```

The saved `fixture_features.npz` loads with `allow_pickle=False`. Interface tests can run from that fixture and the vendored source without the original JSONs or any network access. To regenerate the full integrity map, the original pinned Git blobs are required; `check_assets.py` disables lazy fetching and fails if they are unavailable. NumPy was already installed in the runtime; CPU PyTorch is the only new dependency download. The wheel and installed runtime are ignored by Git.

## Stop condition

Stopped at the authorized bounded milestone. No LLM API, pretrained decoder/encoder weight loading, unsafe checkpoint deserialization, paid resource, GPU training, gate acceptance, settings change or push occurred. Useful semantic alignment would next require verified feature provenance/informative encoder outputs plus an actual compatible decoder objective. That is outside this connector-integrity milestone. The HTTP 403 applies to a public decoder metadata request and has a known denied outcome; it was not bypassed. No pending or uncertain external action remains.
