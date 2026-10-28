# Official source references, original summary

The pinned official README documents separate predictive and contrastive tasks
for circuit modalities and points to the Hugging Face dataset. The PM loader
converts stored feature, edge, probability and level/index arrays to tensors;
it shuffles by a seeded torch permutation before a ratio-based split. The PM
evaluation script loads the supplied checkpoint and reconstructs probabilities
from predicted shifts. This pilot mirrors tensor semantics and split order but
uses single-graph CPU inference instead of its batch evaluation orchestration.

Exact source URLs and original download SHA256s are retained in asset_receipt.json.
Third-party README/evaluation/loader text copies are private and excluded because
redistribution permission has not been independently verified. This summary is
newly written for the reproduction report.
