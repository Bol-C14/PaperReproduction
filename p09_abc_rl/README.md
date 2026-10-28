# ABC-RL ICLR2024 — bounded reproduction branch

Read [REPRODUCTION.md](REPRODUCTION.md) for the completed CPU gate, exact blocker and mechanism status. The [frozen protocol](PROTOCOL.md) precedes tests. [Original asset audit](ASSET_AUDIT.md), [separate repairs](port/repairs.patch), [commands](COMMANDS.md), [metrics](results/metrics.json) and [resource ledger](results/resource_ledger.json) are inspectable.

Seven unit tests pass, plus strict structural loading of all26 real-checkpoint tensors on CPU. The required external BERT asset returned403; no policy inference or ABC evaluation ran. This is not a behavioral/full-paper reproduction. No push/PR was made.
