# Released-benchmark relevance: blocked before corpus inspection

**Reachability is unknown. No zero-observed finding or benchmark-score-inflation claim is supported.** The complete pinned file could not be obtained in the cloud environment, so exhaustive static inventory and frontend checks were not executed. The previously demonstrated synthetic input-validation defect remains valid and distinct from actual-benchmark impact.

## What completed

- Pinned the public dataset repository to revision `83179e5d881234f47fd783d03af22510cd9c6c35` using its [public commit page](https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark/commit/83179e5d881234f47fd783d03af22510cd9c6c35), and identified `hf_benchmark.jsonl` as the sole advertised payload. The public file URL's cached redirect identifies source-file commit `ecae68df53c50b113db57c198465d891fcf7736e` and etag `9f486e6165e9a635087e3eeaa6990949d927537a`. Neither is represented as a locally verified payload hash.
- The [public viewer](https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark) advertises 291 records in its default `train` split, with `ground_truth`, `question`, `generated_verilog`, `verified`; the [file listing](https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark/tree/main) advertises 571 kB. This is the released benchmark, not the full training dataset. Those are remote metadata facts; all-row schema/text inspection remains pending.
- Froze a content-independent 32-position selection from the advertised denominator 291, with a deterministic SHA256 ranking rule. No frontend outcome or content warning influenced selection. See [selection.json](selection.json) and [protocol](PROTOCOL.md), committed before any frontend execution at `d3fcc854b61481066605d888349f075247c33611`.
- Defined exhaustive static inventory of all actual rows and, if access becomes possible, at most 32 original discovery/frontend checks with retained hashes/statuses and no original success-parser modification. Selected-record raw/canonical hashes remain explicitly null because bytes are unavailable. Any actual row-count mismatch requires new preregistration before execution.

## Exact access blocker and status

1. **Denied:** `git ls-remote https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark HEAD refs/heads/main` failed through the existing cloud proxy with `CONNECT tunnel failed, response 403` at 2026-10-28T11:00:51Z.
2. **Denied:** a credential-free HTTPS GET for the exact pinned public payload
   `https://huggingface.co/datasets/wilyub/VeriThoughtsBenchmark/resolve/83179e5d881234f47fd783d03af22510cd9c6c35/hf_benchmark.jsonl`
   failed with `Tunnel connection failed: 403 Forbidden` at 11:01:41Z. Exact attempt/exception: [download_attempt.json](download_attempt.json). The public web tool also could not open that exact revision payload URL.

Public metadata and an older cached, partial text rendering were accessible through web research, but they are not a complete byte-preserving local file. They were not reconstructed into a purported dataset or used to claim exhaustive inspection. No credentials, mirrors, endpoint changes, policy escalation, repeated raw download, or security-setting change was attempted.

This is an access denial, not evidence of an absent/gated dataset. No automatic approval-review rejection occurred, no approval is pending and no outcome is uncertain: the payload download failed and no file was saved.

## Denominators and resource ledger

| Quantity | Status |
|---|---|
| Metadata-advertised record denominator | 291 |
| Locally verified record denominator | unknown |
| Frozen selection size | 32 positions |
| Records exhaustively inventoried from local payload | 0; not executed |
| Selected records run through frontend | 0; not executed |
| Observed empty / invalid / unsupported / timeout counts | unknown, not zero |
| New compiler, simulator, synthesis, SAT, model or training calls | 0 |
| New software installed | none |
| Benchmark payload bytes downloaded to cloud workspace | 0 |
| Public metadata traffic | small; not separately metered; far below 100 MB phase cap |
| Preparation CPU | not separately metered; short metadata/hash/selection scripts only; no corpus/EDA CPU workload |

The advertised `verified=true` field is not treated as independent syntax or behavioral verification. No inference is made about fresh model outputs, full training data, original benchmark scores or score inflation.

## Remaining blocker and stop

To execute the frozen checks, the complete exact `hf_benchmark.jsonl` must become available in this cloud workspace through an authorized, verifiable source. Reconfirm byte/row hashes and the advertised denominator before attaching selected record hashes and running anything. Access is currently **denied**, and frontend execution is **not started**, rather than pending in the background.

The prior completed pilot/review remains unchanged; [preservation.json](preservation.json) checks its tracked files against commit `3dcc3092e4d58f71fa1b43d0f1e83ce5a0cbcbe3`. No push or PR. This follow-on stops at the access blocker, with preregistration and evidence retained for the parent’s decision.
