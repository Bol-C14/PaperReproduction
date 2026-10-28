# ABC-RL real CPU pilot on APRIL — completed

**Subsequent correction:** the full-bank audit found stale fanins when abc_py
interfaces are reused across circuits. This pilot reused an interface; its
retrieval embeddings/gates cannot support an uncontaminated retrieval claim.
Its separate native ADP/CEC evidence remains valid for the evaluated recipes.
See [ABLATION_METHOD.md](ABLATION_METHOD.md) for the diagnosis and corrected
multi-seed design. Original values and logs below are retained unchanged.

On 2026-10-28 the bounded mechanism pilot completed with the released neural checkpoint, canonical cased BERT, native ABC graph extraction, upstream MCTSNode PUCT/backup, automatic cosine retrieval gate, real 7nm mapped Area*Delay, and winner equivalence checking. This supersedes the earlier structural-only preflight and BERT download blocker. It is not a full-paper numerical reproduction.

| Circuit | resyn2 ADP | Unguided best ADP | Adaptive best ADP | Unguided improvement vs resyn2 | Adaptive improvement vs resyn2 |
|---|---:|---:|---:|---:|---:|
| sin | 21155722.5152 | 19899789.1376 | 19478019.2152 | 5.9366% | 7.9303% |
| cavlc | 124922.4560 | 118681.9590 | 112058.6148 | 4.9955% | 10.2975% |

All four winning un-mapped recipe AIGs passed native ABC CEC against the original circuits. Mapping itself was not separately equivalence certified. ADP values use the author's 7nm liberty library with `map; topo; stime`; they are this tool/library flow's units, not measured hardware PPA.

## Scope and interpretation

Each circuit/arm has exactly three evaluated horizon-10 recipes, including root initialization. Two further leaf expansions use the actual released `MCTSNode` selection and value backup; rollout suffixes remain random as in source. The control uses uniform priors and a policy-independent random rollout starting action. Adaptive mode uses the original unnormalized `pi**beta`, policy argmax starting action, and cosine-derived beta. Initial graph features and BERT recipe-token convention are preserved; lazy prefix states avoid uncounted synthesis transitions and are materialized by each full native recipe evaluation.

The train-only retrieval bank is explicitly the two real source-listed training circuits `alu2` and `int2float`. Evaluation uses `sin` (released TTSPLIT5001 test) and `cavlc` (outside that listed training set). This subset is not the complete paper bank. Source split5001 lists22 training circuits while the paper describes23; the released checkpoint's actual training provenance remains unproven. The model strictly loaded all26 state keys with tensor equality, and no substitute/random encoder or policy was used. BERT is pinned to canonical snapshot cd5ef92a9fb2f889e972770a36d4ed042daf221e, not asserted to be the unrecorded historical snapshot.

Distance/beta: sin .03479458605/.05844434063; cavlc .01415336394/.32842076615. Threshold .007 and scaling100 were fixed before objective evaluations. The tiny, single-seed run demonstrates actual mechanism execution and correctness; it does not establish statistical superiority or reproduce paper-wide claims. Full bank, provenance reconciliation, original-size budget, repeated seeds, and full training remain outside this phase.

## Budget, failures and protocol

`results/april/ledger-audit.json` verifies18 unique native ABC evaluation/correctness invocations:14 mapped ADP calls (2 baselines +12 searched recipes) and4 CEC calls, all return0. The20-call cap retains2 unused diagnostic calls. Twelve native graph extraction reads across preflight/initial/resumed attempts are separately recorded; graph API traversal is not synthesis evaluation. Failed native evaluation calls:0.

A Python adapter failure occurred after2 successful objective calls because upstream MCTSNode expects string/path-like states. Initial runner/log/protocol are retained. An implementation-only amendment changed lazy prefix tuples to digit strings and added deterministic resume; the same2 completed evaluations were reused, not discarded or repeated. Frozen UTC14:34:02.675307 precedes all objective evaluations, with a source SHA256; amendment precedes the remaining evaluations. No result-based tuning or budget expansion occurred. The attempted pre-run local git commit failed due missing author identity, so the pre-run freeze is timestamp+hash evidence, not a pre-run Git commit.

Native build failures are retained: missing Python.h, intermediate script quoting/symlink errors, and absent libbz2 development symlink. The final isolated build uses official CPython3.12.12 headers, installed platform pyconfig, installed runtime `-l:libbz2.so.1`, pybind11 headers, pinned libabc.a, and no upstream native source edits. PyTorch2.6 compatibility additionally removes scheduler `verbose=True`; inference semantics are unchanged. `port/build_repaired.py` reproduces the policy repairs and reviewable patch.

## Evidence and exact execution

Remote root: `/home/shugu/work/paper-reproduction-april-20261028`. Native dependencies at `tools/abc-rl/`, environment `envs/abc-rl`, assets `assets/abc-rl`, full output and winning AIGs `results/abc-rl/pilot`. Committed text copies are in `results/april` and `logs/april`; binary assets remain isolated outside Git. `asset-manifest.json` records URLs, immutable model revision, hashes and sizes; BERT model card declares apache-2.0. `versions.json`, `installed.lock`, `binding-build-command.json` and `port/april_build_binding.py` document setup.

The completed invocation was:

```bash
R=/home/shugu/work/paper-reproduction-april-20261028
ABC_RL_BERT_PATH="$R/assets/abc-rl/bert" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 taskset -c 0-7 \
"$R/envs/abc-rl/bin/python" "$R/checkouts/abc-rl/p09_abc_rl/port/april_pilot.py"
```

Do not rerun against this completed output directory: the global counted ledger and completed results are evidence. A new experiment requires its own frozen protocol and output location. The preflight used `--preflight`; all recipe commands and CEC commands are recorded exactly in `calls.jsonl` with stdout/stderr in `abc_01.log` through `abc_18.log`. CEC logs are05,09,14,18. The initial failure and final resume logs are retained separately.

Validation: all seven existing contract tests passed with the actual verified checkpoint; `git diff --check` passed. The first contract-test rerun found the legacy ignored asset path absent; an ignored symlink to the already verified shared checkpoint resolved the path without changing a test or tensor. The new real-inference/ledger/CEC checks supply behavioral validation beyond those contracts.

All runtime work was CPU only on affinity0-7 with8-thread caps. No GPU/API/LLM call, paid resource, system/global installation, credential/security mutation, push or PR occurred. No process remains running from this pilot.
