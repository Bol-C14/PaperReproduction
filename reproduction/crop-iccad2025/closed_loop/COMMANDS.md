# Exact commands and resource record

All working paths below are under `/workspace/PaperReproduction/reproduction/crop-iccad2025`. No global installation or security setting was changed.

## Tool repair and probes

The earlier local YoWASP Yosys 0.50 remains intact. This new probe, from repository root, returned without producing a complete ABC mapping result; its log ends at `/yosys-abc` invocation:

```sh
PYTHONPATH=reproduction/crop-iccad2025/toolchain XDG_CACHE_HOME=/workspace/PaperReproduction/reproduction/crop-iccad2025/cache reproduction/crop-iccad2025/toolchain/bin/yowasp-yosys -Q -T -p 'read_verilog reproduction/crop-iccad2025/fixtures/adder_prior.v; synth -top dut'
```

Log: `pilot/abc_probe.log`. It was not counted as a successful measurement. Rather than interpreting its exit status as mapping success, the study requires an actual mapped netlist and verification.

Two Debian packages were downloaded using Python `urllib.request.urlopen` from the exact official URLs in `native/downloads.json`, with no credentials. The local unpack/run commands from `closed_loop/native` were:

```sh
dpkg-deb -x yosys_0.52-2_amd64.deb root
dpkg-deb -x yosys-abc_0.52-2_amd64.deb root
ldd root/usr/bin/yosys
ldd root/usr/bin/yosys-abc
root/usr/bin/yosys -V
root/usr/bin/yosys-abc -c version
root/usr/bin/yosys-abc -c 'if -h'
root/usr/bin/yosys -Q -T -p 'help abc'
```

Versions: **Yosys 0.52**, git SHA `fee39a3284c90249e1d9684cf6944ffbbcbb8f90`; **ABC 1.01**, compiled May 4, 2025. Native linked libraries resolved from the existing Debian 13 environment. Distribution copyright/license records remain under `native/root/usr/share/doc/`; binaries and packages are local ignored files. Source package provenance is the [official Debian pool](https://deb.debian.org/debian/pool/main/y/yosys/).

An initial native probe used the wrong relative source path, `../../../fixtures/adder_prior.v`, and failed to find module `dut`. It is preserved as `pilot/native_probe.log`. Correcting that path was an implementation repair, not an access workaround:

```sh
root/usr/bin/yosys -Q -T -p 'read_verilog ../../fixtures/adder_prior.v; synth -top dut -noabc; abc -lut 4; stat'
```

Log: `pilot/native_probe_corrected.log`; it mapped the old adder fixture to 18 LUTs. Thus there were **three preliminary synthesis attempts: one incomplete, one failed, one successful**, separate from the frozen expanded study and the earlier twelve-call milestone.

## Frozen study and checks

From `closed_loop`:

```sh
python study.py freeze
python study.py > progress.log 2>&1
python check_and_report.py > checks.log
```

`study.py freeze` wrote the ten RTL circuits, two ABC scripts, source hashes, and the full manifest before any expanded-study synthesis. The first eight history calls were the pilot; all passed before further scaling. For every measured invocation the exact argument vectors are saved in its `result.json`, and the complete synthesis script is saved as `flow.ys`. The command form is:

```sh
native/root/usr/bin/yosys -Q -T -s runs/NNN_PHASE_DESIGN_CONFIG/flow.ys
native/root/usr/bin/yosys-abc -c 'cec runs/NNN_PHASE_DESIGN_CONFIG/reference.blif runs/NNN_PHASE_DESIGN_CONFIG/mapped.blif'
```

Four additional feature-only extraction commands, with no mapping/QoR objective, are recorded under `features/*/extraction.json`. The 272 measured synthesis calls each have one ABC CEC verification call. No optimization run was added by the checking script. Its deliberately corrupted netlist is a negative correctness-check artifact, not an experimental outcome.

## Costs and limits

The two new native package downloads total **11,170,612 bytes**, with SHA-256 pins in `native/downloads.json`. They unpack to roughly 39 MB; with package files the native directory occupies about 50 MB. Measured run artifacts occupy about 56 MB. Earlier YoWASP installation/cache and results are preserved separately. No GPU, paid API, external LLM call, credential, or gated asset was used. The selected host reports five CPUs and approximately 17.6 GiB total RAM; peak process RAM was not instrumented.

Expanded study wall time: **79.496 seconds**. Aggregate per-measurement times: history **12.948 seconds**, online **55.718 seconds**, post-hoc reference **9.551 seconds**. These include synthesis, CEC, JSON parsing, sampled arithmetic verification, and per-row bookkeeping; the study wall time also includes feature extraction and study-level overhead. They exclude earlier tool setup and download time. Individual synthesis and CEC subprocess times are in every result record.

Frozen limits were 272 mapping evaluations, 60 seconds per synthesis process, and 30 seconds per equivalence process. No timeouts or measurement failures occurred after freezing. Search seeds were 11, 23, and 37; checker seed was 701 plus input width. Every trace has four actual evaluations with common initialization and no duplicate configuration. The driver refuses to overwrite an existing ledger.

Both later weight-access HEAD checks were denied by the proxy (403); no weight download or model execution occurred. `model_access_check.json` preserves the exact action targets and outcomes. No denial bypass was attempted.
