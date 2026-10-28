# Exact commands, pins and offline replay

All local work occurs under `/workspace`, without system installs, credentials, push or PR. Python3.12.14, g++14, Tclsh and Make were available. Initial source/dependency failures are retained in logs, including APT proxy403 and the failed ANSI-port smoke. Do not automatically retry forbidden endpoints. The following are the successful path and replay equivalents.

## Successful acquisition/build in this task

```sh
mkdir -p /workspace/buffalo-tools
python3 -m pip install --target /workspace/buffalo-tools/python cmake ninja
git clone --depth 1 https://github.com/The-OpenROAD-Project/OpenSTA.git /workspace/buffalo-tools/OpenSTA
git clone --depth 1 https://github.com/OpenTimer/OpenTimer.git /workspace/buffalo-tools/OpenTimer
```

Resolved pins, inspected before execution:

- OpenSTA `384b539085c54eef46cbaa02e2e17d2b983247e5` (source/data read; no OpenSTA binary built).
- OpenTimer `cd0565fc7a720368e75751c717be92d76350ee8d`, reports2.1.0.
- CMake4.4.4, ninja1.13.2 from pip; Make generator was actually used.
- Library `test/asap7/asap7sc7p5t_INVBUF_RVT_TT_nldm_220122.lib.gz` in OpenSTA; retained at `vendor/`.

```sh
/workspace/buffalo-tools/python/cmake/data/bin/cmake \
  -S /workspace/buffalo-tools/OpenTimer \
  -B /workspace/buffalo-tools/OpenTimer/build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
/workspace/buffalo-tools/python/cmake/data/bin/cmake \
  --build /workspace/buffalo-tools/OpenTimer/build --target ot-shell -j 4
```

A preceding default all-target `-j2` build was stopped and reused by the targeted build; logs retain both. `BUILD_TESTING=OFF` does not suppress upstream unconditional test target configuration; only `ot-shell` was completed. No broad upstream regression suite ran.

## Exact data extraction and bounded pilot

From repository root:

```sh
python3 papers/Paper04-BUFFALO/src/extract_net.py \
  --netlist /workspace/buffalo-tools/OpenSTA/test/asap7/designs/aes.v
python3 papers/Paper04-BUFFALO/src/pilot.py \
  --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell --smoke
python3 papers/Paper04-BUFFALO/src/pilot.py \
  --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell
python3 papers/Paper04-BUFFALO/src/pilot.py \
  --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell --net aes_cut
python3 papers/Paper04-BUFFALO/src/audit_reward.py
python3 papers/Paper04-BUFFALO/src/verify_archived.py
MPLCONFIGDIR=/tmp/buffalo-matplotlib python3 papers/Paper04-BUFFALO/src/summarize.py
python3 papers/Paper04-BUFFALO/src/audit_paper_table.py
```

`extract_net.py` deterministically extracts the complete selected AES fanout. The resulting JSON is already included; model training/source AES netlist are unnecessary for replay of this cut. This is connectivity provenance, not original placement or timing. Generated `runs/*/*/sta.conf` files record every actual command with original absolute paths. `pilot.py` recreates paths for a relocated workspace; direct raw replay requires adapting paths.

RC sensitivity command used the same evaluation function:

```sh
python3 - <<'PY'
import sys
sys.path.insert(0, 'papers/Paper04-BUFFALO/src')
from pilot import *
_,lib=library()
f=fixture('clustered'); f['c_ff_per_um']=0; f['r_ohm_per_um']=0
t=dict(f['driver'], children=f['sinks'])
print(evaluate(t,f,ROOT/'runs'/'rc-control',ROOT/'vendor'/'asap7.lib',
               '/workspace/buffalo-tools/OpenTimer/bin/ot-shell',lib))
PY
```

## Offline recheck and source build

No network, compiler or STA needed for raw-evidence recomputation:

```sh
python3 papers/Paper04-BUFFALO/src/verify_archived.py
python3 papers/Paper04-BUFFALO/src/audit_reward.py
python3 papers/Paper04-BUFFALO/src/audit_paper_table.py
```

Plots additionally need matplotlib; the first plotting attempt used an unwritable default cache, then was rerun with writable `MPLCONFIGDIR`. Offline tree figures use decoded archived sequences. `decoded_tree.json` files were regenerated from their archived sequence sidecars and equality-checked against deterministic constructions; raw evaluated Verilog/SPEF/STA logs were unchanged.

To build STA without fetching its repository, extract `vendor/OpenTimer-source-minimal.tar.gz` into any writable directory, configure the extracted `OpenTimer` with CMake and build target `ot-shell` as above. The archive contains394 exact tracked upstream files, including all engine headers/sources, main programs, CMake and required example/test source stubs, MIT/license notices. Large benchmark datasets and unrelated example data are intentionally omitted. Archive file hashes are in `vendor/OpenTimer-source-files.sha256.json`. An independent extraction/configure succeeded (`logs/offline-source-configure.log`). A compiler/Make/CMake/Tclsh remain prerequisites; their SDKs are not bundled. No binary is shipped.

## Package and restore local branch

```sh
git bundle create /workspace/buffalo-iccad2025.bundle reproduction/buffalo-iccad2025
git bundle verify /workspace/buffalo-iccad2025.bundle
python3 papers/Paper04-BUFFALO/src/package.py
git clone -b reproduction/buffalo-iccad2025 /workspace/buffalo-iccad2025.bundle /tmp/buffalo-restored
python3 /tmp/buffalo-restored/papers/Paper04-BUFFALO/src/verify_archived.py
```

Use explicit `-b`: this branch-only bundle has no default HEAD. ZIP-member SHA256 checks are performed by `package.py`. It bundles this paper, source archive and local git history; upstream repository ancestry is not established. The outer ZIP hash/Library version are delivery metadata after packaging, not self-referential members.

Configuration-only closeout (zero additional STA):

```sh
python3 papers/Paper04-BUFFALO/src/test_config_contract.py
```

This test emits nondefault timing/load constraints in a temporary directory, checks scoring against the SDC-derived required time, tests configurable fanout thresholds, and compares153 regenerated default evaluated input files byte-for-byte to the archived versions. It does not overwrite archived runs.

Bounded feasibility diagnosis (nine STA calls once; refuses to overwrite existing evidence):

```sh
python3 papers/Paper04-BUFFALO/src/diagnose_feasibility.py --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell
python3 papers/Paper04-BUFFALO/src/verify_feasibility.py
```

The predeclared plan is `config/feasibility_plan.json`. Run the verifier on the supplied existing result instead of rerunning the evaluator. New A/Y and output-required/slack observations are confined to these9 new configurations.

Local provenance/envelope follow-up (12 new STA calls once, refuses overwrite):

```sh
python3 papers/Paper04-BUFFALO/src/audit_units.py
python3 papers/Paper04-BUFFALO/src/study_envelope.py --engine /workspace/buffalo-tools/OpenTimer/bin/ot-shell
python3 papers/Paper04-BUFFALO/src/verify_envelope.py
MPLCONFIGDIR=/tmp/buffalo-matplotlib python3 papers/Paper04-BUFFALO/src/plot_envelope.py
```

The unit audit/verifier/plotter add zero STA. On the delivered existing results, run verifier and plotter rather than rerunning the evaluator. `config/envelope_plan.json` predates new evaluation; original80ps stays fixed. Per-implementation fixture JSONs record the explicit .5→1.44fF load-domain repair.

## Public export packaging override

This sanitized branch intentionally replaces the historical packager's implicit original-bundle path. Use only an explicit bundle of this public branch:

```sh
git bundle create /workspace/buffalo-iccad2025-public.bundle reproduction/buffalo-iccad2025
python3 papers/Paper04-BUFFALO/src/package.py --bundle /workspace/buffalo-iccad2025-public.bundle --output /workspace/buffalo-iccad2025-public.zip
```

Do not follow earlier historical package examples without these explicit arguments. The manifest records omitted nonresearch logs; all scientific raw inputs/results are retained. No original/unsanitized bundle is part of this public history.
