# Bounded preflight commands and source pins

Working directory: `/workspace/PaperReproduction` in the selected cloud environment.
The initial protocol commit is `beffdd177abc73392ba9bd6f51162ccf28fe7075`.
No simulation occurred before that commit. The execution harness was committed as
`a3df3b7` before attempt 1; the indentation fix was committed as `667796b` after
attempts 3–4 and before attempts 5–6. Its diff only corrects YAML-dedented matching.
Original audit code/model source pins and hashes are in `provenance/`.

## Preparation actually performed

The Git remote had five paused branches and no main. A shallow, read-only fetch of
`reproduction/aspen-mlcad2025` supplied the existing base. No new repository,
remote branch, push or PR was created.

```sh
git fetch --no-tags --depth=1 origin reproduction/aspen-mlcad2025:refs/remotes/origin/reproduction/aspen-mlcad2025
git switch -c reproduction/autosizer-icml2026 refs/remotes/origin/reproduction/aspen-mlcad2025
```

Official assets were obtained via Python HTTPS reads; exact URLs, sizes and SHA-256
are in `provenance/downloads.json`. The first exploration fetched a few unpinned
documentation/model headers; the actual model files are pinned to the official
SKY130 commit, as the manifest records. Two guessed model-wrapper paths returned
404 and were not replaced with invented models: their real wrappers are already
inside the official tt.pm3 files.

The original `gpgv` command was unavailable. Verification instead succeeded using
the installed `gpg` with an isolated workspace home and the installed Debian
archive keyring. The InRelease signature → Packages.xz SHA-256 → ngspice package
SHA-256 chain passed. Package extraction used `dpkg-deb -x`; no apt installation,
maintainer scripts or global configuration changes were made. Minimal dependency
preparation is now reproducibly expressed by the following scripts (they stop
while this phase is marked closed; a future replay needs a new authorization and
budget protocol):

```sh
python projects/autosizer/scripts/fetch_pinned_assets.py
python projects/autosizer/scripts/verify_install.py
python projects/autosizer/scripts/prepare_subset.py
```

## Exact six simulator invocations

```sh
python projects/autosizer/scripts/run_one.py inverter original
python projects/autosizer/scripts/run_one.py five_trans_ota original
python projects/autosizer/scripts/run_one.py inverter repaired_export
python projects/autosizer/scripts/run_one.py five_trans_ota repaired_export
python projects/autosizer/scripts/run_one.py inverter repaired_export --diagnostic-refinement
python projects/autosizer/scripts/run_one.py five_trans_ota repaired_export --diagnostic-refinement
```

Each launches the locally extracted `ngspice -n -b circuit.spice` once, in its
recorded attempt directory, with a 90-second timeout, one OpenMP thread and an
explicit minimal environment. It does not load account/API secrets or upstream
Python/API modules. All deck hashes, commands, UTC times, outcomes, CPU time and
maximum resident memory are in `logs/attempts.json`. Original source YAMLs remain
unchanged. A preparation-only matcher exception before attempt 3 is documented in
`logs/harness_preparation_error.md`; it launched no simulator and consumed no
simulation attempt.

## Read-only analysis and software checks

```sh
python projects/autosizer/scripts/check_classification.py
python projects/autosizer/scripts/analyze_vectors.py
```

Eight synthetic software error-classification cases are explicitly distinct from
measured circuit results. Vector analysis recomputes delays, DC derivative gain,
time-weighted power and AC unity-gain crossing from preserved exports. These
commands launch no simulator and can be rerun after phase closure.
