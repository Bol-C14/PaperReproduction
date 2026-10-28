# Matched native prior bank and remaining model boundary

The new CPU-only preparation completed **48 actual native Yosys/ABC synthesis
measurements**, covering six public prior circuits and all eight legal
configurations. All48 passed ABC CEC, independent arithmetic-versus-LUT checks
on256 vectors each (12,288 vector cases), and independent LUT-depth agreement.
There were **zero real API calls, zero target measurements and zero local LLM
loads/inference**. The old272-measurement study was not rerun or edited.

Preparation source: `83ed96eb4032513837e0ef712686d418724f8069`.
Python3.12.12; native Yosys0.52 at the setup-pinned revision and the existing
read-only ABC build recorded in `native_priors/protocol.json`. Yosys mapping
now explicitly passes `abc -exe` using the same ABC executable used for CEC.
Do not attribute all drift to that pin alone: the historical Debian and native
builds are not a controlled single-variable comparison.

The protocol was written before the first measurement: max48 attempts,
60-second synthesis timeout,30-second CEC timeout, first failure stops. CPU
binding was8-15 (eight distinct physical cores); OMP/OpenBLAS/MKL caps were8.
Initial host load was1.39/1.10/1.28 with roughly1.3TiB MemAvailable. Recorded sum
of per-measurement elapsed time was14.36 seconds. All work completed; there is no
remaining CPU job/reservation. No tool rebuild, global install, GPU job or
paid resource was used.

## Backend drift is observable

43/48 `(LUT count, depth)` pairs matched historical rows exactly. Five differed:

| Prior | Config | Historical LUTs/depth | Native LUTs/depth |
| --- | --- | --- | --- |
| multiply | c1 | 164 / 12 | 162 / 12 |
| multiply | c5 | 164 / 12 | 162 / 12 |
| alu | c1 | 44 / 6 | 43 / 6 |
| alu | c5 | 44 / 6 | 43 / 6 |
| popcount | c6 | 155 / 31 | 153 / 30 |

The best configuration ID for each of the six priors remained the same on this
small bank. This does not make the backends generally interchangeable. The
future pilot uses only the freshly measured native bank, tied to the same tool
bytes and source/config manifest. Prior prompt guidance contains only each
prior's top-three IDs and objective ratios normalized to that prior's c0.
Target performance comparisons must use fresh measurements from the same run.
No historical target/posthoc rows enter search contexts.

## Independent correctness checks

`verify_native_bank.py` independently rechecks all48 saved mapped netlists
against the arithmetic references, checks exact6x8 coverage and sorted bank
membership, verifies source bytes, positive CEC logs, declared objectives,
explicit ABC pinning and source/tool provenance. Its output is in
`native-bank-verification.json`. It also rejects a temporary copied netlist with
a deliberately corrupted output; original outputs remain unchanged.

A separate real ABC negative control compares a one-bit identity with inversion.
ABC prints `NOT EQUIVALENT` but returns0 on this build. The recorded log and
result are under `native_priors/checks/`; this demonstrates why the pipeline
requires explicit positive equivalence text instead of only an exit status.
This adds one negative CEC call and zero synthesis/model calls to the48 positive
measurement/CEC pairs. No unexpected synthesis failure occurred; existing
historical failure evidence remains preserved.

The Mac offline suite now has15 passing interface tests. The separately saved
APRIL13-test log is the earlier same-source environment check, before adding the
cache-roundtrip and process-timeout fixture tests. All fake responses/vectors are explicitly
labeled test fixtures and produce no scientific semantic/LLM result.

## Evidence locations and replay

- `native_priors/protocol.json`: pre-run budget, seed, source/tool provenance,
  affinity and thread caps.
- `native_priors/results.json`, `ledger.jsonl`, `bank.json`: all48 actual rows and
  the matched guidance bank; `comparison.json` contains all48 backend pairs.
- `native_priors/runs/`: synthesis commands/scripts/logs, mapped JSON/BLIF,
  reference BLIF, CEC logs and raw per-row results.
- `native_priors/run.log`: completed driver output.

Public snapshots replace the operator-specific runtime prefix with the literal
`${PAPER_REPRO_ROOT}`. This changes paths only; all metrics/netlist logic and
source/tool identifiers are preserved. These snapshot scripts/logs are evidence,
not a shell to execute unchanged. The original unnormalized evidence remains
in the dedicated APRIL result directory. Reconstruct commands using the checked
in preparation driver and an explicitly selected fresh runtime/output location;
the completed output directory refuses overwrite. Do not rerun completed48 rows
just to validate the report.

The exact preparation invocation used the isolated Python, `taskset -c 8-15`,
`PAPER_REPRO_ROOT` and8-thread caps, with
`april_api_stage/prepare_native_priors.py`, redirecting to the dedicated CROP log.
Offline verification is:

```sh
python3 reproduction/crop-iccad2025/april_api_stage/verify_native_bank.py
python3 -m unittest discover -s reproduction/crop-iccad2025/april_api_stage -p 'test_*.py' -v
```

## What remains unexecuted

Real hierarchical summary generation, genuine semantic retrieval and live LLM
proposal feedback remain unexecuted. The prepared profile requests only a chat
endpoint; embeddings use existing local MiniLM. See `PILOT_PROTOCOL.md` for the
public payload example and17 nominal/34 maximum requests,4096 input+640 output
per attempt (161,024 total token upper bound under the authorized token-counting
profile), and the separate four-target-measurement budget. Endpoint/model,
runtime credentials, public data transmission and token-counting assumptions
still need explicit parent authorization, followed by release of the denied
entry point. No retry has been made.

Even after a successful pilot, these educational circuits and LUT4 count-times-
depth objective will remain substitutes for the paper's benchmarks, model and
RTL Architect physical PPA. A single-target/single-seed run cannot establish a
quality advantage or full paper reproduction.
