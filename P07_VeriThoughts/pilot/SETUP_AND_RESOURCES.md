# Setup attempts, provenance and bounded resource ledger

Setup started 2026-10-28T10:34:01Z, with a 12:34:01Z stop deadline. Main experiment completed at 10:46:57.683212Z; the sole logging repair completed at 10:48:59.069526Z. Final artifact preparation remained well inside two hours. CPU only; no paid resources, models, APIs, GPU, gated terms, external pushes or credentials.

## Preparation and failures, all retained

1. Existing local Git repository had no commits on `work`; remote `ls-remote` listed only the five existing paper branches and no main. A read-only fetch inspected the ASPEN branch's root for possible shared instructions; no AGENTS.md was present. No ASPEN work was modified. The requested VeriThoughts branch was initialized as an orphan from the existing unborn local history, without a new repository or remote update.
2. Docker 28.4.0 client/server was available. Bubblewrap isolation preflight failed with `setting up uid map: Read-only file system`; no privileges, sysctls or host security settings were changed. Docker was used instead.
3. Official Debian `bookworm-slim` image pulled successfully, digest `sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3`. Image's local uncompressed size: 74,867,380 bytes.
4. Official Yosys release tag was resolved through public Git: tag object `fdaf4a83738fbf4ba4b785ca834360990ad704c2`, peeled source commit `c1ad37779eea6211866a466026322416fb3a832f`. The official GitHub codeload archive was downloaded, measured at 2,810,283 bytes and hashed as `a22b1dd9f23bc829ed9bbb938dde5404c2577dc89f4618d5d1e89999eb3d84e8`. Docker verified that hash before compilation. Details: `source_download.json`.
5. Build invocation 1 failed before package download because Docker buildx tried to write `/home/agent/.docker/buildx` on a read-only filesystem (`container_build.log`). A task-local `/tmp/p07-docker` config directory resolved this without changing host settings or reading credentials.
6. Build invocation 2, default build networking, failed to resolve Debian hosts (`container_build_retry1.log`).
7. Build invocation 3, host build networking, had the same Debian DNS failure (`container_build_retry2.log`).
8. Build invocation 4 forwarded existing infrastructure proxy build arguments but could not resolve the proxy hostname (`container_build_retry3.log`). No proxy values or account data are included in artifacts.
9. Build invocation 5 added a container-local hostname mapping for the existing proxy; signed Debian package downloads and the network-disabled Yosys source build succeeded (`container_build_retry4.log`). No package installation or compiler execution happened on the host. Source build uses two make workers. Package-install step: 18.8 s; source-build/install step: 485.0 s; final export: 1.4 s.

Successful build invocation, with runtime-expanded infrastructure values intentionally omitted from this document:

```bash
DOCKER_CONFIG=/tmp/p07-docker docker build --network=host \
  --add-host "proxy:$(getent ahostsv4 proxy | awk 'NR==1 {print $1}')" \
  --build-arg HTTP_PROXY --build-arg HTTPS_PROXY \
  --build-arg http_proxy="$HTTP_PROXY" --build-arg https_proxy="$HTTPS_PROXY" \
  --progress=plain -t p07-verithoughts:yosys041 P07_VeriThoughts/pilot/container
```

Docker's predefined proxy build arguments were used only for trusted Debian package installation. The separate `RUN --network=none` step compiles source without networking. Both experiment containers use `--network=none` and cannot access the proxy or model services.

## Exact installed environment

Local image: `sha256:9805c8192b5a06fb39955367d95c372ace0dca0b934ae803d92d90235f9f7383`, uncompressed size 495,080,606 bytes. Base digest and build flags: `container/Dockerfile`; runtime image metadata: `logs/image_inspect.json`; complete installed package/version lock: `runs/attempt1/dpkg-lock.tsv`.

| Component | Observed version |
|---|---|
| Yosys | 0.41, git sha1 c1ad37779ee |
| Yosys compiler | g++ 12.2.0-14+deb12u1, -fPIC -Os |
| Icarus Verilog | 11.0 stable; Debian package 11.0-1.1+b1 |
| Python | 3.11.2; Debian package 3.11.2-1+b1 |
| NumPy | 1.24.2; Debian package 1:1.24.2-1+deb12u1 |
| Bison | 2:3.8.2+dfsg-1+b1 |
| Flex | 2.6.4-8.2 |
| Make | 4.3-4.1 |

The official evaluator's requirements advertise NumPy 1.26.4, while this minimal Debian runtime uses 1.24.2. This explicit dependency substitution affects only mean aggregation in the evaluated script; its formal tool calls are unchanged. No claim of complete original environment identity is made. The successful build's Debian packages are version-locked in the manifest and exact local image, but the Dockerfile's apt repository is not time-snapshotted; future binary-identical rebuilds may need a Debian snapshot.

## Downloads and disk

| Download class | Recorded size / bound |
|---|---|
| Official source archive | 2,810,283 bytes exact |
| Debian apt index transfer | build log reports 9,397 kB, rounded |
| Debian package archive transfer | build log reports 98.2 MB, rounded |
| Debian base layer | compressed transfer not metered; local uncompressed 74.87 MB is a conservative payload bound |
| Git read-only fetch and metadata | Git object store approximately 3.42 MB before final result commits; network bytes not directly metered |
| Other package/project metadata checks | small public JSON/HTML, not separately metered; no YoWASP package was downloaded or installed |

Accounted successful payload classes sum to approximately 189 MB using the uncompressed base as an overestimate. Allowing broad metadata/rounding margin gives an estimated envelope below 250 MB, far below the 2 GB limit. This is not a packet-level network meter. Docker build context copies are local transfers, not additional internet downloads. Final image is approximately 495 MB uncompressed; build cache disk usage is not the same as download traffic. No dataset or checkpoint payload was downloaded. The source archive and generated simulator executables are excluded from Git; their hashes/commands are retained.

## Experiment resource ledger

All runs: nonroot uid/gid 1000, read-only image and source, only designated result directory writable, /tmp tmpfs 256 MB, no network, capabilities dropped, no-new-privileges, 128 PID cap, 2 CPU quota, 4 GiB memory and equal memory/swap limit (no swap). Preflight observed effective capabilities zero and NoNewPrivs=1. No Docker socket or credential directories were mounted.

| Quantity | Main frozen attempt | Logging-only supplemental |
|---|---:|---:|
| Runner / formal command wall time | 2.717983 s runner | 0.372035 s Yosys call |
| Container launch-to-return observation | timestamp window 10:46:52–10:46:58 | 5.088715 s |
| Cgroup CPU time | 2.833982 s | 0.421836 s |
| Cgroup peak memory | 47,390,720 bytes | 42,885,120 bytes |
| Child-process max RSS | 46,352 KiB | not separately collected |
| Formal invocations | 17 | 1 |
| Original driver subprocesses | 8 | 0 |
| Oracle compile/simulation invocations | 16 | 0 |
| Timeouts / unknowns | 0 / 0 | 0 / 0 |

Main outer ledger contains 33 subprocess attempts: 8 original-driver processes, 9 direct formal calls (8 port + 1 novel bound), and 16 oracle calls. The original drivers additionally record 8 nested Yosys calls. Thus there are 41 subprocess launches across those layers, including parent drivers; they are not 41 independent cases. Supplemental adds one formal call, for 18 formal invocations overall. Expected rc=1 formal failures and rc=2 syntax failures are retained as substantive outcomes, not discarded failures. Empty discovery performs no formal call.

Build peak memory and aggregate compiler CPU time were not collected; make used two workers and the successful compilation step lasted 485 s. Runtime resource figures must not be presented as end-to-end setup cost. No experiment was repeated except the one pre-recorded buffering repair; no fixture or horizon was selected after looking at results.
