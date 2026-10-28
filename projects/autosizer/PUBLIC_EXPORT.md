# AutoSizer Round2 public preservation

This publication was explicitly authorized after the experiments. It changes no
repository visibility and publishes only `reproduction/autosizer-icml2026`, without
a PR, merge, branch deletion or force-push. No new research experiments were run
while preparing the export. Original local history and existing recovery bundles
were retained separately.

## Scientific scope

The [optimization results](experiments/optimization_v1/RESULTS.md) preserve 1,029
actual CPU-only simulator attempts: pilot, four matched numerical controls on
two released circuits with three seeds, independent winner remeasurement and
a held-out inverter grid. Raw metrics, decks, stdout/stderr, seeds, configurations,
source hashes, commands, substitutions and bounded conclusions are included.
Live LLM-generated circuit understanding and decisions were not executed; the
prepared interface fails closed. No claim is made to reproduce the paper's LLM
controller or 24-task result. Previous fixed-point preflight results remain intact.

## Redaction and recovery mapping

The original local result head was
`ea966334b02f8521ee6ac823de3ac14f226b16e9`. A pattern scan found no credential or
private-key candidates, but two audit files contained an internal execution
identifier. That identifier was replaced with `[redacted-local-execution-id]`
throughout the seven AutoSizer commits that introduced/carried it:

* `provenance/ASSET_AUDIT.md`
* `provenance/assets_audit.json`

No experiment source, numerical configuration, measurement, raw log, result or
scientific assertion was changed by this redaction. Historical records deliberately
retain the original local protocol/code commit IDs and hashes. Consult
[PUBLIC_EXPORT_COMMIT_MAP.json](PUBLIC_EXPORT_COMMIT_MAP.json) to resolve them to
the corresponding sanitized public history; do not silently reinterpret those
provenance fields. Inherited existing public history was not rewritten.

The export contains all branch ancestors back to its root. The original checkout
was shallow, so missing ancestral objects were retrieved into a temporary copy
without modifying or discarding original local commits. A naive shallow-bundle
import initially failed despite passing `git bundle verify`; full ancestry was
then recovered. The resulting original-history bundle and locally retained
unredacted branch provide recovery outside this public export. Neither bundle is
published. Their private audit identifier is not a credential and is not needed
to interpret the experiment.

The complete final proposed history and working tree are scanned before push for
private keys, recognized API tokens, credential literals, credential URLs,
authentication/cookie headers, secret-bearing environment assignments and internal
service/host identifiers. Gzip/ZIP research members are examined where applicable.
Pattern scans cannot prove absence of every possible secret. Credentials, Git
authentication configuration, environment-variable dumps, unrelated personal files,
transfer helpers and recovery archives are never selected for publication.

## Assets included and omitted

The small official SKY130 nfet/pfet tt dependency subset is included in
`vendor/sky130_tt/`, with Apache-2.0 license/notices and exact upstream URL/hash
records in `provenance/vendored_sky130_manifest.json`. No device model bodies were
modified. The other required small scientific artifacts are already tracked.

[PUBLIC_OMISSIONS.json](PUBLIC_OMISSIONS.json) lists replaceable packages/indexes,
exploratory download headers and installed environments excluded from publication,
with sizes/hashes/provenance where available. Per-file hashes and sizes for the
excluded ngspice installation are recorded separately. No model checkpoint was
used/generated, and none is silently omitted. Python and system installations,
bytecode/GPG caches and backup bundles are excluded. Restoring an executable
runtime requires compatible external package access; the public tree is not a
byte-for-byte machine image.

## Restoration and inspection

Clone this branch into a fresh directory and read the result JSON/CSV and reports
without installing or executing anything. Git history and tracked scientific
artifacts require no private service or credential. The historical logs use
absolute `/workspace/PaperReproduction` paths; using that path is the simplest
way to preserve their meaning. At another root, use relative attempt IDs for
inspection and create a separately documented runtime configuration for future
experiments. Do not edit archived numeric evidence or closed protocols to make
old commands execute.

For a future separately authorized runtime setup:

1. Provision a compatible Python 3.12 runtime and the versions in
   `configs/public-requirements-pins.txt`. The original simulator was official
   Debian ngspice 44.2+ds-1; its package URL/hash and dependency provenance are
   recorded. A binary port needs glibc >=2.38 or an appropriate build/container.
2. Run `python projects/autosizer/scripts/restore_public_model_assets.py` to copy
   the included, hash-verified model files to the ignored local `downloads/`
   directory. It performs no network or simulation action.
3. Generate a local model selector using the documented `prepare_subset.py`.
   Absolute-path selector hashes are part of the old protocol: a different target
   path requires a new protocol/configuration, not alteration of archived results.
4. Keep the existing phase-closed gates intact. New model/controller experiments
   require their own permitted backend, budget and recorded substitutions.

No simulator, inference, optimizer, Runpod operation or paid resource was invoked
during this preservation/publication task.
