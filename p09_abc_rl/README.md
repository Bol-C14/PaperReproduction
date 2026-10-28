# ABC-RL ICLR2024 — bounded reproduction branch

Read [ABLATION_REPORT.md](ABLATION_REPORT.md) for the completed 724-call study:
all candidates passed CEC; adaptive retrieval showed no stable benefit under
this small budget. Read [ABLATION_METHOD.md](ABLATION_METHOD.md) for the design,
training-provenance limits and native graph-lifecycle correction. The executable
contract is [ABLATION_PROTOCOL.json](ABLATION_PROTOCOL.json). The earlier
[APRIL_REPORT.md](APRIL_REPORT.md) retains its actual ADP/CEC evidence, but its
retrieval embeddings require reassessment because its interface was reused.

The earlier [REPRODUCTION.md](REPRODUCTION.md) and [ASSET_AUDIT.md](ASSET_AUDIT.md)
are historical preflight records. The BERT blocker was subsequently resolved and
real CPU policy inference, ABC mapping and CEC ran. The verified pilot commit was
pushed to the existing public branch. No full-paper numerical reproduction or
training-provenance claim is made. Original GPL source and separate repairs are
preserved; external model, circuit and library binaries are excluded from Git.
