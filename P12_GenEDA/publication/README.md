# Round 2 public-branch preservation

Publication is authorized only for `Bol-C14/PaperReproduction`, branch `reproduction/geneda-iccad2025`. No main-branch update, force-push, visibility change, PR or private recovery-archive upload is part of this operation. The private Library backup task was superseded before any archive/upload was created; local backup staging remains untouched outside this repository.

The research head preserved before this publication record is `c2dcb6236ae3ef5e3110ad403c2715d2e605b8bb`, with its parent `0710164fa089839411015ffbb49855e2c6742abc`. Both commits remain in the branch history. Original branch worktree was clean; no uncommitted research work was discarded or silently rewritten.

## Included research

- Source/configuration, frozen protocols, source snapshots, asset audit, dependency/version pins, data provenance and hashes.
- The 96-example frozen study subset, approximately 750KB compressed JSON; this is selected public research data, not a recovery archive.
- Actual training traces, raw generations and lexical metrics, controls, seeds, failure logs, resource ledgers and test reports.
- Twenty small locally trained arm checkpoints plus four scratch language-prior checkpoints, all safe numeric NPZ files below 0.8MB each. No downloaded foundation-model weights are included.

The [scientific report](../generation_v1/README.md) is explicit: this is a scratch-decoder methodology reconstruction, not original pretrained GenEDA. Matched pairing did not beat shuffled/modality controls; semantic alignment remains unestablished. The failed startup and its comparison repair remain recorded. Publication does not change any experimental evidence.

## Exclusions and safety scope

[EXCLUSIONS.json](EXCLUSIONS.json) records original locations, SHA-256 hashes or deterministic directory-tree hashes, byte sizes, provenance and external-access requirements for the omitted installed runtime, wheel, partial upstream cache/source, bytecode caches and four full upstream benchmark blobs. The portable selected data supports the completed Round 2 study without downloading the full benchmarks; restoring dependencies still requires the pinned packages or pre-provided copies. This is a research snapshot, not an offline installed execution environment.

The ignored partial upstream source copy contains apparent hard-coded credentials. That ignored copy and its object cache are **not proposed for publication**, and remain unchanged locally. The original branch history does not include them. No credential values are reported here. A separate sanitized history is unnecessary unless the final proposed reachable-object scan finds sensitive content; any such finding blocks the push.

The base scan inspected both existing commits and all 128 reachable blob objects, expanding gzip and ZIP/NPZ payloads. It found no known credential-pattern match. URL review found only public source/dependency domains and no credential-bearing or private-service URL. [Base scan](HISTORY_SCAN_BASE.json) and [URL review](URL_REVIEW_BASE.json) are retained. `scan_history.py` rechecks the entire final proposed history, including this publication record, before push; its final result is retained outside Git to avoid a self-referential commit. Pattern scanning is not a universal certification that unknown secret formats cannot exist.

No `.env`, credential store, cookie store, environment dump, unrelated personal file, installed environment, cache or generated recovery archive is staged. Official Library helper files and local backup materials stay outside the repository.

## Verification procedure

1. Read the exact remote branch ref before push. If it exists, fetch/read and compare ancestry; never overwrite unrelated work. Use an ordinary non-force push for this branch alone.
2. Scan every object reachable from the final local branch with `scan_history.py`, and check staged-file scope and exclusions.
3. After push, independently read the remote ref and require full commit-SHA equality.
4. Clone this branch into a fresh directory, require the expected branch/head, and compare SHA-256 hashes for every tracked file against the publishing checkout. Check the scientific report, frozen data, 24 small checkpoints, raw score files and source hashes. This is restoration verification only, with no research rerun.

The confirmed remote SHA, fresh-clone result and clean/dirty state are returned in the completion response. If any push or verification step is denied or uncertain, publication is reported as incomplete rather than successful.
