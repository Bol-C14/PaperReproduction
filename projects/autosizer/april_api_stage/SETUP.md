# Recorded isolated setup

This is preparation provenance, not a runnable live-controller workflow. Paths in the JSON evidence identify the completed APRIL run; substitute an isolated task root when restoring elsewhere.

## Checkout and Python environment

- Parent commit: `35865afabc05be1a7e5c900bd3097ff8ea70ed85`.
- APRIL: Rocky Linux 9.7, glibc 2.34, Python 3.12.12.
- Isolated environment: `envs/autosizer`; no global package/config changes.
- CPU allocation: logical CPUs 24–31; at most eight OpenMP/BLAS threads.
- Recorded installation used `uv venv --python /usr/bin/python3.12`, followed by CPU-only Torch 2.6.0 from `https://download.pytorch.org/whl/cpu` and pinned Transformers 4.49.0, PyYAML 6.0.3, scikit-learn 1.7.2, and Accelerate 1.12.0. The full resolved environment is in `requirements.lock`. These packages were prepared before the final API-only preference; the API adapter/offline tests themselves use only Python's standard library.
- No local model was loaded or run. Do not treat installed ML packages as authorization for local model inference.

## Native ngspice 44.2

Source URL, exact byte count and SHA-256 are recorded in `ngspice_source_manifest.json`. The archive was extracted inside `tools/autosizer`, and configured with an isolated installation prefix and these switches:

```text
--with-x=no --with-readline=no --disable-openmp --disable-xspice
--disable-cider --disable-osdi --disable-klu
```

Compilation used `make -j8`; installation stayed inside the task prefix. The owned build process tree was restricted to CPUs 24–31 after startup. The resulting executable's `--version` succeeded and its SHA-256 is in `STAGE_REPORT.json`. This metadata check did not run a circuit.

## Official SKY130 tt subset

`asset_manifest.json` records exact official URLs, lengths and SHA-256 hashes from `google/skywater-pdk-libs-sky130_fd_pr`, commit `f62031a1be9aefe902d6d54cddd6f59b57627436`.

The local selector retains the `models/all.spice` prefix before individual diode includes, resolves its lod include to the restored asset location, and includes `models/parameters/critical.spice`, `models/corners/tt/nonfet.spice`, and both nfet/pfet 01v8 mismatch/tt corner files. It encloses these in `.lib tt` / `.endl tt`. Model bodies remain unmodified; corner files resolve their sibling tt.pm3 files. The selector contains absolute restore paths and must be regenerated for a different task root; therefore the generated selector is not copied here.

## API transport and offline verification

`api_controller.py` accepts only the three designated runtime variables and explicit caller authorization. It never searches historical credentials and does not print or store authorization headers. Its attempted-call budget is ten, timeout is 180 seconds, public-message payload cap is 24 KiB, and output limits depend on the stage.

The existing offline evidence came from running `test_api_controller_offline.py` with real network access prohibited by a monkeypatched transport. The test was not rerun for packaging. No live API entrypoint exists in this package, and the experiment bridge still needs implementation and a new authorized protocol.
