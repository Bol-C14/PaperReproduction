# Public CVDP data

No benchmark payload is versioned in this repository. The downloader pins the
official Hugging Face dataset revision
`5b807d945f6a99aa645f7e43a64a2115e281b4bf` and verifies the byte size and
SHA-256 digest of every downloaded file.

It fetches exactly:

- `cvdp_v1.1.0_agentic_heavy_code_generation_no_commercial.jsonl`
- Seven public Git bundles needed by the eight tasks in
  [`reproduction/paper_tasks.json`](../reproduction/paper_tasks.json)

Download and verify:

```bash
./scripts/fetch_cvdp_subset.py
./scripts/fetch_cvdp_subset.py --check-only
```

The resulting `data/cvdp-v1.1.0/` tree is ignored by Git. The preparation
script filters by exact task ID, reconstructs visible repositories from the
public bundles, removes commercial-simulator tool declarations and guidance,
injects the CID seed skill, and writes generated task payloads under the
ignored `runs/` tree.

The eight archived paper tasks were field- and byte-checked against this
official release for category, prompt, context, origin, patch, and harness.
Downloaded data remains under the upstream terms reproduced in
[`CVDP_DATASET_LICENSE`](../CVDP_DATASET_LICENSE) and
[`CVDP_DATASET_NOTICE`](../CVDP_DATASET_NOTICE).
