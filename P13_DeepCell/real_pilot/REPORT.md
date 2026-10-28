# Real Liberty interface closed; frozen transfer remains No-Go

2026-10-28 continuation of `reproduction/deepcell-iccad2025`, inherited HEAD `e5cdb1e6dfc8532d42832925bb789fe4c8090d7e`. This adds one bounded, real-library preprocessing/functional-ECO pilot. It does not repeat the old training matrix or replace its results.

## New observable closure

Pinned public EPFL **int2float**, mapped by actual ABC with **Nangate45 typical Liberty**, `read_lib -G 250; strash; map`. Actual input-pin bindings and Boolean functions become the PM encoder's 64-channel truth-table features. ABC then strashes the mapped circuit to its paired AIG. This replaces the old extension's invented unit-cost genlib with real cell semantics. It does not recover the authors' exact commercial preprocessing, Liberty corner selection, constraints, task heads or modified `&nf`/`runeco`.

The mapped PM has **161 nodes**, the AIG **459 explicit nodes**, with **11 inputs/7 outputs**, using 14 library cell types. The original public BLIF, PM evaluator and AIG evaluator agree on **all 2,048 input assignments**; ABC CEC independently proves mapping equivalence. ABC reports 90 Liberty cells, skipping sequential/tri-state/unusable entries, and derives 30 GENLIB gate types using slew **17.19 ps**, gain **250**. No external timing/load constraint or PPA target was supplied, and no paper PPA result is claimed.

Eight observable multi-input cells at fixed index quantiles were selected from 137 eligible sites before model scoring. Frozen full-token paired and PM-only checkpoints from both old seeds 208/209 were loaded strictly, with their recorded SHA256s checked. No optimizer or new training data was used.

| Fixed condition | Verified repair success@3 |
|---|---:|
| Correctly paired AIG, both seeds | 0/16 |
| Same paired model, cyclically permuted AIG PI binding | 0/16 |
| Frozen PM-only, both seeds | 0/16 |
| Fixed random | 0/8 |
| Reverse topological | 0/8 |
| Privileged direct-fanin oracle, same top-3 budget | 6/8 |

The PI intervention preserves AIG node count/topology size while changing PI connectivity. Its output differs from the correct circuit on **1,951/2,048** assignments. It changes **16/16 complete candidate rankings**; maximum absolute per-trial logit changes range **0.00833–0.10269**. Reversing only the counterpart token order gives maximum logit difference **9.54e-7**, consistent with the position-free fusion's expected order invariance. These observations establish semantic input sensitivity, not useful fusion performance. The PM-only row uses a separately trained old model and is not an inference-only causal ablation.

All **6 emitted oracle patches** pass exported-netlist exhaustive checks and ABC CEC. A separate scalar BLIF interpreter importing neither solver nor model rechecks **12,288 assignments** and confirms an explicit counterexample for an inverted patch. The two oracle failures remain in results under the fixed top-3 budget; no support expansion or new site selection was performed. One circuit/eight sites is not a broad generalization sample. Encoder pretraining exposure to EPFL is unknown; retained rankers were trained only on synthetic teaching cells.

## Assets, execution, and failures

- EPFL source commit `82d8cc6910419298e713a46644ed59fd3df53038`, `random_control/int2float.blif`; SHA256 `efcdc03a007ff142c97dd083b1db5cba3378669862d02c8cc3cbb272225d5f85`.
- Nangate Liberty from OpenROAD-flow-scripts commit `0fcc4186e344f85167d97c1d67994bef01e89036`; SHA256 `8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1`. Original downloaded assets remain in the isolated APRIL checkout; raw Liberty/model downloads are excluded from this payload. Library license header restrictions have not been treated as permission to redistribute its raw contents.
- Reused read-only ABC revision `34fe762d36c8cb3327d1d5bb96092a4a8f3b7593`, binary SHA256 `a1b5018f7c5bda200430ece7905deba357519b49f92069953b970a616fe94620`. This differs from the previous cloud ABC revision and is disclosed, not silently equated.
- APRIL CPU only, two torch/BLAS threads. New virtual environment reads existing abc-rl packages without modifying them: torch **2.6.0+cpu**, PyG **2.6.1**, NumPy **2.2.6**. This is dependency reuse, not a fully independent wheel installation. Previous NumPy was 1.24; the actual version is recorded.
- Successful fixed execution **22.634 s**, peak process RSS **575,932 KiB (562.4 MiB)**. Download manifest totals **19,555,331 bytes**, including the two original encoder files, real Liberty, benchmark, and current official tree. Inherited four fused checkpoints are additional Git retrieval, not new models. **0 training updates, 0 paid API requests, USD 0**, no GPU/Runpod. No additional shared API budget requested.
- First benchmark URL used an incorrect `arithmetic/` directory and returned **404**. The pinned repository tree showed `random_control/`; corrected once, no access restriction bypass. Two pre-scoring parser attempts failed on Liberty internal state `IQ`; explicit sequential/state-dependent cell exclusion fixed the combinational parser. Preserve both failures and successful attempt logs. No model-scoring failure prompted tuning.
- Some SSH multiplexed sessions ended with transport code 255 even after remote files completed. Completion is established by final `results.json`, independent receipt, CEC logs and process absence, not by connection state. Original raw logs remain on APRIL; reviewable local copies redact runtime paths and ANSI formatting only.

Official DeepCell `git ls-remote ... HEAD` still returned `b82aef22559c6d8c52eb4feb437ebdd32709360e`; its full recursive public tree was downloaded and hashed. No newly published paired corpus, fused/downstream checkpoint or modified ABC was verified. The original branch has no AGENTS.md, `.agents/skills`, original prompt or files named REPRODUCTION/EVIDENCE_AUDIT/FINAL_STATUS; actual inspected records are ASSET_AUDIT.md, PILOT_REPORT.md, CLOSURE_REPORT.md, mechanism coverage, protocols, code and result manifests.

## Stop decision and exact next requirements

**No-Go for further performance sweeps or GPU rental.** The affordable gap closed here is actual Liberty/pin/tool-to-paired-graph wiring. Frozen learned transfer remains at a floor and cannot identify an ECO benefit. Larger training or more synthetic examples is not justified by this result.

Next original-methodology progress requires at least one concrete new asset: (1) official paired NPZ/processed dataset with parent/split and Liberty/pin/preprocessing manifests, enabling genuine corpus training; (2) author fused/ECO-finetuned head and its corruption/label definition plus driven-signal interface; or (3) DeepCell-modified ABC revision and mapping-head/training recipe, Liberty corner and constraints. These are asset/integration blockers, not a request for paid compute. No new budget batch or GPU specification is warranted until one route has an executable readiness test.

## Replay and evidence

Within the existing paper branch, materialize the four `closure/checkpoints/full_token_{paired_pretrained,pm_only}_{208,209}.pth` files. Set `PYTHON` to the isolated CPU virtualenv and `DEEPCELL_ABC` to the pinned executable, then run:

```sh
"$PYTHON" P13_DeepCell/real_pilot/acquire.py
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 1200 "$PYTHON" P13_DeepCell/real_pilot/run.py
"$PYTHON" P13_DeepCell/real_pilot/verify.py
```

Frozen scope: [PROTOCOL.md](PROTOCOL.md). Exact numerical and per-site rankings/checkpoint hashes: [results/results.json](results/results.json). Independent verification: [results/independent_verification.json](results/independent_verification.json). Asset URLs/hashes: [assets_manifest.json](assets_manifest.json). Actual map/proof/negative logs: `logs/`. Historical failed commands: `attempt_logs/`. No push or PR performed; payload manifest and review receipt accompany the local changes.
