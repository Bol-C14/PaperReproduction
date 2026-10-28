# ABC-RL complete-bank checkpoint ablation — completed

The 2026-10-28 corrected run completed all 30 circuit/seed/arm searches. It does **not show a stable advantage from adaptive retrieval** over fixed policy guidance under this small budget. Policy choice of rollout starting action is a more visible contributor than the tested adaptive gate. These observations are limited to two circuits and three seeds; no full-paper numerical reproduction or retraining is claimed.

## Evidence and execution

Exactly **724 native ABC invocations** completed: 362 mapped Area*Delay evaluations (360 searched candidates plus 2 resyn2 baselines) and 362 CEC checks covering every baseline and candidate, including all losers. All calls returned zero, all 362 CEC checks passed, and no candidate was invalid. Root initialization is included in each arm's twelve recipes. The 16-call diagnostic reserve was unused. Runtime was 710.935 seconds, CPU affinity0-7, with eight-thread caps and one search process. The process exited and the runner wrote `ABLATION_COMPLETE 724`.

The frozen run is `ablation_fullbank_s3_b12_v3`; its protocol and runner hashes are in `results/ablation_fullbank_s3_b12_v3/audit.json`. [Method](ABLATION_METHOD.md), [protocol](ABLATION_PROTOCOL.json), [analysis](results/ablation_fullbank_s3_b12_v3/analysis.json), [all candidates](results/ablation_fullbank_s3_b12_v3/results.json), [best-so-far curves](results/ablation_fullbank_s3_b12_v3/curves.json), [call ledger](results/ablation_fullbank_s3_b12_v3/calls.jsonl) and all724 individual native logs are retained. `port/summarize_ablation.py` independently checks invocation IDs, arm budgets, seed completeness and CEC text and reconstructs the curves without running synthesis. External AIG/model/library binaries remain on APRIL; all output file hashes, including AIG hashes, are recorded.

## Every seed and arm

Values below are percentage ADP reduction from the shared resyn2 baseline, using the best CEC-valid recipe among exactly twelve evaluated recipes. A positive value means lower ADP. The median is across the three seeds, not an average of inverse-ADP factors. All seed results are shown.

| Circuit | Arm | Seed566 | Seed567 | Seed568 | Median | Range |
|---|---|---:|---:|---:|---:|---:|
| sin | unguided | 7.5086% | 11.1192% | 11.6491% | 11.1192% | 7.5086–11.6491% |
| sin | policy_start | 13.9354% | 13.7131% | 17.4270% | 13.9354% | 13.7131–17.4270% |
| sin | fixed | 12.4377% | 11.9755% | 14.7998% | 12.4377% | 11.9755–14.7998% |
| sin | adaptive_full | 12.4377% | 11.7443% | 14.7998% | 12.4377% | 11.7443–14.7998% |
| sin | adaptive_subset | 9.3412% | 11.7443% | 14.7998% | 11.7443% | 9.3412–14.7998% |
| cavlc | unguided | 10.6363% | 11.0487% | 11.3049% | 11.0487% | 10.6363–11.3049% |
| cavlc | policy_start | 18.8629% | 10.0362% | 13.8787% | 13.8787% | 10.0362–18.8629% |
| cavlc | fixed | 13.6128% | 13.1728% | 12.7276% | 13.1728% | 12.7276–13.6128% |
| cavlc | adaptive_full | 14.3995% | 12.7909% | 9.2340% | 12.7909% | 9.2340–14.3995% |
| cavlc | adaptive_subset | 14.3995% | 12.7909% | 9.2340% | 12.7909% | 9.2340–14.3995% |

Baselines: sin ADP21155722.5152; cavlc ADP124922.4560. These are the author7nm `map; topo; stime` flow's units, not measured silicon PPA.

## Paired contribution checks

Each cell is the seed566/567/568 difference in ADP reduction, followed by its median, in **percentage points**. This compares the same seeds and counted budget; the difference between arm medians is not substituted for the paired median.

| Executed comparison | sin: seed differences; median | cavlc: seed differences; median |
|---|---|---|
| policy_start minus unguided | +6.4268, +2.5940, +5.7779; **+5.7779** | +8.2266, -1.0125, +2.5738; **+2.5738** |
| fixed minus policy_start | -1.4977, -1.7377, -2.6272; **-1.7377** | -5.2501, +3.1366, -1.1510; **-1.1510** |
| adaptive_full minus fixed | +0.0000, -0.2312, +0.0000; **+0.0000** | +0.7867, -0.3819, -3.4936; **-0.3819** |
| adaptive_full minus adaptive_subset | +3.0966, +0.0000, +0.0000; **+0.0000** | +0.0000, +0.0000, +0.0000; **+0.0000** |

The rollout-start comparison is positive in5/6 circuit/seed pairs; its paired median is +5.7779pp on sin and +2.5738pp on cavlc. Adding fixed policy PUCT priors to that same start rule is worse in5/6 pairs, with medians -1.7377pp and -1.1510pp. This supports examining where the policy enters search, rather than attributing the whole guidance result to retrieval. It does not establish a population-level ranking.

The adaptive-full versus fixed comparison has median0.0000pp on sin and -0.3819pp on cavlc. Expanding the retrieval bank gives +3.0966pp only for sin seed566; the other five paired outcomes are unchanged, and both circuit-wise paired medians are zero. There is no consistent full-bank retrieval benefit in this experiment. Individual recipe traces still matter even when final best values coincide.

With fresh graphs, sin retrieves `multiplier` from the22-member bank (distance0.03155485057, beta0.07903836171), versus `alu2` from the two-member bank (distance0.03802972732, beta0.04298479909). Cavlc retrieves `alu2` in both banks (distance0.01611826680, beta0.28662618755). Both cavlc adaptive arms have identical recipes and ADPs for every candidate in every seed, matching the identical gate and providing an implementation consistency check.

## Failures, corrections and residual limits

Two earlier attempts stopped during graph inference, each after starting three native graph reads and before any ADP/CEC call. Their original protocols, hashes, ledgers and failure logs are in `results/ablation_audit/attempt1` and `attempt2`, with source commits in `attempt-index.json`. The root cause was abc_py retaining old fanins across circuit reads. Explicit square adjacency alone did not fix stale edges; fresh non-overlapping interfaces did. The48-read lifecycle audit found zero out-of-range edges in all24 fresh graphs. All82 known phase graph reads, plus an overlapping-context diagnostic with uncertain partial read count, are disclosed in `phase-setup-audit.json`; none is counted as a synthesis subprocess. Setup mistakes and the native diagnostic failure are retained separately from the zero failed objective calls.

The old pilot's int2float, sin and cavlc embeddings and policy probabilities change under fresh extraction. Its reported retrieval distances and improvement numbers cannot establish a clean retrieval effect. Its independent native ADP/CEC records remain evidence for those specific old recipes. No old objective value was reused in this experiment.

Complete bank means the22 circuits in released source split5001. The paper describes23; checkpoint training provenance remains unresolved. The released two-layer checkpoint, source graph-feature convention, canonical cased BERT snapshot, fixed threshold.007/scaling100 and unnormalized prior exponentiation are preserved and documented; they are not proven to match historical paper training. Unnormalized exponentiation changes total exploration weight as well as relative action preferences. The search is a bounded single-root mechanism port, not the complete per-depth original evaluation schedule. Twelve recipes per arm and three seeds are far below a broad original-budget evaluation. No significance or distance/usefulness-correlation claim is warranted.

CEC checks every un-mapped candidate AIG against the original. Mapped library netlists are not separately equivalence certified. No full training, API/LLM call, local generative model deployment, GPU job, paid resource, global installation, credential change or other branch change occurred.

## Reproduction and safe inspection

The actual run command, executed after source commit `e938e49`, was:

```bash
R=/home/shugu/work/paper-reproduction-april-20261028
cd "$R/checkouts/abc-rl"
ABC_RL_BERT_PATH="$R/assets/abc-rl/bert" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 taskset -c 0-7 \
"$R/envs/abc-rl/bin/python" -u p09_abc_rl/port/april_ablation.py \
  --root "$R" --protocol p09_abc_rl/ABLATION_PROTOCOL.json
```

Do not rerun this command against the completed run ID: the runner refuses to overwrite its output. A new run requires a separately frozen run ID/protocol. Existing results can be rechecked without synthesis:

```bash
python p09_abc_rl/port/summarize_ablation.py p09_abc_rl/results/ablation_fullbank_s3_b12_v3
python p09_abc_rl/port/verify_ablation.py p09_abc_rl/results/ablation_fullbank_s3_b12_v3
```

The independent raw-log verifier checked732 available text hashes, recomputed all362
ADPs directly from native Area/Delay output, checked all362 CEC texts, verified360
MCTS trace rows and confirmed the executed runner/policy match the frozen hashes.
The original remote hash inventory retains362 omitted binary AIG hashes when
these scripts inspect a public text export.
