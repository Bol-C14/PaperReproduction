# Dataset source summary (original review text)

Source: [henryen/hwe-bench](https://huggingface.co/datasets/henryen/hwe-bench/tree/82a42e0a05719366a326e09ddc668ea0d46c91f6), revision `82a42e0a05719366a326e09ddc668ea0d46c91f6`.

HWE-Bench is the hardware-repair dataset accompanying work by Fan Cui, Hongyuan Hou, Zizhang Luo, Chenyun Yin and Yun Liang. The dataset metadata declares Apache-2.0. This file is an independently written source summary; it does not reproduce the upstream README, reference answers or tests.

The release provides six repository-specific evaluation files and an aggregate analysis file. This audit used the separately pinned Ibex and CVA6 files, each containing 35 records. Their complete-file hashes and the four selected task identities are recorded in selection.json. Record contents distinguish agent-visible problem statements from private reference patches and verifier scripts. Published outcome fields describe the release's calibration claims; our fresh execution evidence is reported separately.

Use the official source repository's harness documentation for evaluation commands. Commercial OpenTitan verification requires a separately licensed tool environment. Individual hardware repositories and container dependencies retain their own licenses; the dataset's declared license does not replace them.
