# TRACE — bounded CPU methodology reproduction

This branch preserves a reduced-data study of **function-shift learning (FSL)** using the official TRACE PM backbone. Few-shot support adaptation is an added evaluation, not the expansion of FSL or an original paper protocol.

- [Scientific evidence packet](P11_TRACE/closure/evidence_packet/EVIDENCE_PACKET.md): pinned-source minimal examples, identity-preserving graph controls, exact splits/label budgets and final-run provenance.
- [Per-seed/family paired MAEs](P11_TRACE/closure/evidence_packet/PAIRED_RESULTS.md), including no-adaptation and transfer comparisons.
- [Methodology report](P11_TRACE/closure/CLOSURE_REPORT.md), [full result table](P11_TRACE/closure/RESULTS_SUMMARY.md), [resource/failure ledger](P11_TRACE/RESOURCE_LEDGER.md).
- [Publication exclusions and asset hashes](PUBLICATION_MANIFEST.json).

Across three seeds and four held-out hardware templates, adapted function-shift output MAE was0.047170±0.001908 versus local-only0.049009. This is a modest synthetic-data result, not a robustness or industrial-benchmark claim. Official-checkpoint adaptation reached0.041842±0.000215, but inherits unknown pretraining cost. Adaptation worsens some family/seed outcomes. Source reconstruction and equal-marginal encoder limitations are documented with executable minimal checks.

## Availability and reproduction

Research source, frozen synthetic circuits/labels, commands/configs, prediction files, actual metrics, failed-attempt evidence, hashes and reports are public. **All43 locally generated checkpoint binaries are preserved in this branch**, including failed-attempt snapshots. Generated archives, installed environments, caches and unmodified upstream pretrained assets remain excluded. [Checkpoint inventory](CHECKPOINT_PRESERVATION.md) lists every file, size, role and regeneration limit. The official checkpoint's pinned public URL/hash is in PUBLICATION_MANIFEST.json; source materialization must likewise use the pinned official repository. Some verification commands intentionally require those omitted weights. Existing report artifact manifests describe original local artifacts, including excluded binaries; consult the publication manifest for public availability.

Dependencies are pinned in P11_TRACE/pilot/requirements-cpu-lock.txt; PyTorch2.8.0+cpu comes from the official CPU index. The complete original history and all local research assets have a separately verified local recovery package. The initial public export is a new root commit; a normal follow-on commit adds small user-generated weights. Excluded upstream pretrained bytes and installation logs remain absent from reachable public history. This does not erase or rewrite the preserved original locally.
