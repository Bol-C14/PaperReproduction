# Repeating the bounded CPU pilot

This directory contains synthetic controls for the released evaluator. The audit above it describes released dataset/model assets; this pilot does not download or evaluate those payloads.

1. Use `source_download.json` to obtain the pinned official Yosys archive as `container/yosys-source.tar.gz`. Verify its SHA256 against that file and the Dockerfile. Do not substitute an unreviewed mirror.
2. Build the image with `docker build -t p07-verithoughts:yosys041 container`. The image base is digest-pinned. Build package installation uses Debian's signed repository; exact installed package versions are saved in `runs/attempt1/dpkg-lock.tsv`. The exact local image identity is in `logs/image_inspect.json`. Full historical rebuilds may require a Debian snapshot providing those package versions.
3. Run `bash run_container.sh` from any directory. The script verifies frozen input/harness hashes, records a separate preflight, then starts the restricted network-disabled container. It refuses to overwrite an existing experiment attempt. For an intentional independent rerun, copy the source/protocol to a fresh reviewed run directory and amend the output directory explicitly, retaining the original attempt.

The current environment's Docker daemon could not resolve normal package-host or proxy DNS. The successful build command added only a container-local mapping of the existing proxy hostname and forwarded the already-configured infrastructure proxy through Docker's predefined proxy build arguments. No credentials were added and no host DNS/security settings were changed. The Yosys source-build RUN step explicitly disables networking; experiment containers also disable it. Consult `SETUP_AND_RESOURCES.md` for exact logged attempts and measured costs.

For this first execution, protocol and fixtures were frozen at commit `66887c2`; the execution shell command was recorded separately at `725cc1a` before any fixture run. The final experiment report distinguishes unchanged original evaluator execution, faithful command port, independent oracle, and the novel 160-step diagnostic. Original pass@5/pass@10 console outputs with one sample are not valid estimators and are excluded from reported metrics.

No external branch push or PR is part of this workflow. Source/software licenses remain those of their respective authors; an exact upstream evaluator copy is kept for local research traceability, with provenance in `upstream/provenance.json`.
