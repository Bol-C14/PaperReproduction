# DeepGate4 bounded CPU pilot

The CPU functional/integration milestone is complete on local branch `reproduction/deepgate4-iclr2025`, using upstream commit `85e20742a2d4702426f94e86666cdcdb408fba8a`. Six final test groups pass. The model has 12 sparse GAT transformer layers and 7,371,314 trainable parameters. This is a method/integration result with random full-model weights, not evidence of learned circuit accuracy or the paper's GPU speedup.

## Checkpoint result

Both official files contain **64 state-dict tensors** that match **all 64 tokenizer tensors** by name and shape. The full sparse DG4 state dict has 492 entries, including 144 transformer entries. Neither file has a sparse-transformer tensor; even after adding the tokenizer prefix, 428 full-model entries remain missing. Recorded epochs are 20 (`model_last.pth`) and 50 (`model_last_workload.pth`). Thus these two released files are tokenizer checkpoints, not complete sparse DG4 checkpoints. Any other external full-model release remains unverified.

`checkpoint_fetch.json` records pinned URLs, exact bytes, SHA-256 and Git blob identities. Total checkpoint transfer: 15,705,442 bytes. The ZIP containers were bounded and their `data.pkl` metadata was interpreted through an allowlisted, non-executing symbolic parser. It accepts only the four observed metadata symbols and constructs ordinary dictionaries/lists. No pickle deserialization or `torch.load` was used, and no released tensor data was loaded into a model. `checkpoint_metadata.json` and `checkpoint_coverage.json` contain every inspected shape and coverage decision. A callable-rejection control passes.

## Original, CPU adaptation and functional repair

Upstream files are unchanged, and their hashes are recorded in `adaptation_manifest.json` and the raw metrics. The actual sparse layer source is imported unchanged. The tokenizer removes only an unused `deepgate` import. The full sparse model uses an explicit import adapter that omits unrelated eager GraphGPS/DAGformer/parser imports and uses PyG's native CPU scatter mean. A CPU-wheel fetch for optional `torch_scatter` failed at the network tunnel; no gate was bypassed or repeated. The reduction has an analytical duplicate-index parity test.

The adapter replaces only six allocation constants in the constructor, bounding four CPU histories and two masks to 16 fixture IDs, and removes pinning for CPU histories. It retains upstream push/pull/reset implementations and checks fixture bounds. Four histories occupy **32,768 bytes**, versus the release's 11,264,000,000-byte host reservation at hidden 128. Capacities 8 and 16 produce bit-identical fixture outputs. Valid push/pull operations also match the original History methods on an unpinned small reference. The large reservation was never allocated.

Two explicitly separate variants are tested with identical seeded weights:

- `upstream_semantics` retains the original forward code, including `all_update_hs = scatter(hf_tf, ...)`.
- `structural_history_repair` changes only that scatter input to `hs_tf`.

On every seed the original variant stores exactly identical functional and structural histories at non-input gates. The repaired variant keeps them distinct (maximum channel differences 5.28–5.95). This reproduces a source-level integration issue on this fixture; it does not establish how the paper's authors ran their experiments or whether the repair improves trained quality.

## Frozen fixture and controls

`PROTOCOL.md` was written before installation/model runs. The authored circuit has 8 nodes, two primary inputs, explicit NOT and AND gates, and reconvergent paths. Its four exhaustive input assignments yield independently checked labels for `a`, `b`, `not(a)`, `a AND b`, `not(a AND b)`, `not(a) AND b`, `not(b)`, `a AND not(b)`. Exact probabilities are `[0.5, 0.5, 0.5, 0.25, 0.75, 0.25, 0.5, 0.25]`. Pairwise truth-table distances are also saved. These labels validate the fixture/oracle, not the random neural model's predictive accuracy.

For seeds 0, 1, 2, both variants have finite 8×256 embeddings. Two node relabellings per run consistently map edges, levels, structural attributes and initial primary-input histories. The latter must follow node identity; leaving it misaligned is the negative control.

| Control | Observed result |
|---|---|
| 12 relabelling comparisons | Maximum absolute difference ≤7.153e-7; all meet frozen atol 1e-5 / rtol 1e-4 |
| Misaligned primary-input features | Output changes 2.69–4.52 in maximum absolute value |
| Valid altered logic at one AND input | Two truth-table bits change; output changes 0.562–3.176 |
| Revisit an already processed cone | Saved histories remain exactly unchanged |
| Two ordered overlapping cones | Existing gate histories stay fixed; new gates get finite histories |
| Two cones versus one full cone | Outputs differ by 1.658–2.151; partition equivalence is **not** established |
| Capacity 8 versus 16 | Exact output equality |

The two-cone fixture exercises pull/reuse/update-once behavior. It is not the paper's full cone-extraction/preprocessing pipeline, and its partition-sensitive outputs should not be treated as a failure of permutation equivariance. No optimizer steps, training, label fitting or threshold tuning occurred. Raw embeddings are in `raw_embeddings.npz`; numerical summaries, labels, seeds and controls are in `raw_metrics.json`.

## Commands and environment

From the existing workspace:

```bash
cd /workspace/PaperReproduction
bash P14_DeepGate4/pilot/replay.sh
```

Replay is offline and writes current raw results. It requires the preserved local official sources, inspected checkpoint containers, and the isolated environment; third-party files are intentionally excluded from Git. Original successful and failed test logs remain in `tests_attempt2.log` and `tests_attempt1.log`; first-attempt metrics are retained separately.

The executed setup used Python 3.12, a `--system-site-packages` venv, CPU-only Torch 2.6.0 and PyG 2.6.1. This is an explicit CPU compatibility substitution for the inconsistent original torch/PyG wheel pins, not the original paper environment. Exact installed overlay versions and inherited package notes are in `requirements-lock.txt` and `environment.json`.

```bash
python -m venv --system-site-packages P14_DeepGate4/.venv
UV_CACHE_DIR="$PWD/P14_DeepGate4/.uv-cache" uv pip install \
  --python P14_DeepGate4/.venv/bin/python --only-binary :all: \
  torch==2.6.0+cpu --index-url https://download.pytorch.org/whl/cpu
UV_CACHE_DIR="$PWD/P14_DeepGate4/.uv-cache" uv pip install \
  --python P14_DeepGate4/.venv/bin/python --only-binary :all: torch_geometric==2.6.1
python P14_DeepGate4/pilot/fetch_checkpoints.py
P14_DeepGate4/.venv/bin/python P14_DeepGate4/pilot/static_checkpoint.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 P14_DeepGate4/.venv/bin/python \
  P14_DeepGate4/pilot/run_pilot.py
```

Those are the actual successful setup commands, not a fully hermetic replacement for the preserved environment. Source pinning is checked in the recorded manifest; the original partial clone and text files were acquired in the prior asset audit. Rebuilding elsewhere would require those same source files from the pinned official commit. Package index resolution can vary, so consult the lock before any later setup.

## Resources, failures and stopping point

The final suite took about **1.42 seconds** including local model construction/metadata comparisons, with process peak RSS **414,696 KiB (~405 MiB)**. This is a ledger measurement, not a systems benchmark. Setup/downloads are approximately **220 MiB** from rounded install logs plus exact checkpoint bytes; total network overhead was not metered. Both the 2-hour setup and 2-GB download bounds were comfortably respected. `resource_ledger.json` records timing, limits, logical disk use, package-download precision and failures.

Four failed commands/attempts are recorded: the initial repository inventory had no HEAD commit; optional scatter-wheel transport failed; a local symbolic-reader APPENDS bug was fixed; and the first test suite supplied the wrong upstream chunked-push signature. That fixture error was corrected without changing upstream behavior. The final suite has **6/6 passing test groups**, zero failures/errors; no resource gate was reached.

No gated access, CUDA, paid resources, security changes, API use, push or publication occurred. DG4 code/weights lack verified license terms; third-party sources, weights and installed packages are excluded by `.gitignore`. No third-party assets were republished. The initial asset-only audit is preserved, with a dated pilot addendum.

**Stop:** the bounded CPU pilot is complete. Minimum mechanism remains L2 with a working tiny CPU adaptation. Complete learned DG4 inference remains blocked on a compatible full-model checkpoint (L3 if obtaining it requires full training). Full-paper quality/scaling/fused speedup remain L3. No further training or kernel implementation is authorized by this milestone.

## Public backup addendum — 2026-10-28

The user subsequently authorized backing up this branch to the existing public `Bol-C14/PaperReproduction` repository. This supersedes the earlier no-push milestone instruction; it does not authorize additional research runs. Historical protocol/report statements remain unchanged as dated evidence.

The backup includes authored source, frozen protocol, commands, dependency versions (not environment variables), all successful and failed test evidence, exact labels and numerical metrics, and the 134,338-byte locally generated `raw_embeddings.npz`. No locally trained model checkpoint was produced. There is no indispensable user-produced research output omitted from this paper's backup.

Excluded: installed environments/caches, official checkpoint payloads, the third-party code checkout and copied README/setup evidence, raw/processed sample assets, and any archives. `source_provenance.json` records hashes and pinned public URLs for the inspected text sources; `checkpoint_fetch.json` records exact checkpoint hashes/provenance. These exclusions preserve the uncertain third-party license boundary. The archive/weight exclusions do not apply to the small authored raw embedding artifact, which is included.

For recovery into a new checkout, inspect the manifests, optionally run `python P14_DeepGate4/pilot/restore_sources.py` to recover only the seven pinned source files, then use the documented CPU setup, checkpoint-fetch/metadata steps and replay command. The restoration helper was syntax-checked during backup preparation, but no new downloads, model runs or research tests were performed for this public backup. Public repository visibility is unchanged; only this paper branch is pushed.
