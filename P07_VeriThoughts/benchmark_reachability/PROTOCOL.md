# Released-benchmark empty-discovery reachability — preregistration

This phase calibrates whether the synthetic empty-discovery robustness defect is reachable on the released small benchmark. It does not reproduce benchmark scores, generate outputs, inspect full training data, or estimate model-output error rates.

## Asset pin and availability gate

Dataset: `wilyub/VeriThoughtsBenchmark`; revision `83179e5d881234f47fd783d03af22510cd9c6c35`; file `hf_benchmark.jsonl`. The public commit page identifies that revision as a README-only license addition with parent `ecae68d…`; the public file download redirects to source-file commit `ecae68df53c50b113db57c198465d891fcf7736e` and advertises etag `9f486e6165e9a635087e3eeaa6990949d927537a`. These are remote metadata pins, not a verified local payload hash.

The public viewer advertises a single `train` split with 291 records and fields `ground_truth`, `question`, `generated_verilog`, `verified`. This is the repository's benchmark file, despite the viewer naming its default split train; it is not the 20K training dataset. There is no split declaration beyond the observed viewer metadata in the 20-byte license-only README. Verify actual row count/schema and downloaded bytes before treating those as a locally established manifest.

**Gate:** no runtime frontend checks without the complete exact file. Download limit: 100 MB new bytes, actual requested file cap 1 MB. No credentials, gated terms, security/network-policy changes or unofficial mirrors. If access is denied, retain the denial and stop dependent execution; unknown corpus reachability must not be reported as zero observed.

## Exhaustive static inventory, only after the gate

Read every raw JSONL line in file order. Record file SHA256, Git blob SHA1, byte count, line count and line-ending details; require advertised source blob agreement if independently established. Each row gets a 0-based row index, raw-line SHA256, canonical-JSON SHA256, field keys/types, empty/null flags, field character/byte lengths and SHA256 for each text field. Preserve native IDs if any; do not invent native IDs.

Apply the exact original module-discovery regex from upstream evaluator commit `f44c2af999de62bd27e90e73ce9cbd4f97fbe55c`, file `evaluation_verithoughts/evaluation_script.py`, L74–75, to both golden and stored generated text. Record names/counts, duplicate names, zero discoveries, and text-level warnings (e.g. module tokens without a match). Do not equate regex discovery with valid syntax. Preserve schema failures and unsupported/ambiguous cases explicitly. A zero golden count is a potential empty-check-path input; only actual original-entrypoint evidence would establish a new acceptance result.

Inventory all 291 records if the file confirms that count; do not stop after clean records. No question correctness, reasoning fidelity, equivalence, reset semantics, or score evaluation is part of this inventory.

## Non-cherry-picked bounded frontend sample

Before any compiler/frontend call, freeze 32 indices selected solely from advertised file positions, independent of record text or static warnings. Rank indices i=0…290 by ascending SHA256 of UTF-8 string:

`P07-empty-discovery-v1|83179e5d881234f47fd783d03af22510cd9c6c35|hf_benchmark.jsonl|i`

where i is its unpadded decimal representation. Take the first 32 hashes; execute selected records in ascending row-index order. The fixed indices/rank hashes are recorded in `selection.json`. Selection denominator is **291 advertised**, pending byte-level confirmation. If actual row count differs, stop before execution and preregister a new denominator/selection; do not silently adapt. Invalid records remain in the sample. No replacement, oversampling of flagged records, or post-result tuning.

After payload acquisition, attach each selected row's raw/canonical hashes before frontend checks. At present those hashes are pending because the payload is blocked; the index selection is not a claim that any record was inspected.

## Allowed execution and stopping

Use the existing pinned Yosys 0.41 container image `sha256:9805c8192b5a06fb39955367d95c372ace0dca0b934ae803d92d90235f9f7383`, nonroot, read-only inputs, writable result directory only, no network, dropped capabilities, no-new-privileges, 1 CPU, 4 GiB memory/no swap and 128 PIDs. Run the unchanged upstream discovery function (AST extraction, no top-level evaluator run) in that container and retain its name/count outputs.

For each selected row, at most three frontend invocations: `read_verilog` on golden alone; stored generated text alone; and the original renamed golden followed by stored generated text, preserving the original read order. Retain command/source hashes, exit codes, stdout/stderr and wall/CPU usage. No `prep`, synthesis, miter, SAT, equivalence proof, simulation, model/API, training or new generated candidates. Each frontend call has a 10-second timeout; a timeout is unknown, not invalid. Tool rejection is frontend-failed/unsupported until diagnostics justify syntax-invalid classification. Original success parsing/label logic is not changed or used to relabel this benchmark.

Total selected records <=32; formal proof calls=0; frontend calls <=96. Single-CPU execution and 10-second frontend limits keep the subprocess envelope below 16 CPU-minutes, leaving margin within the 60 CPU-minute phase budget. Stop at the phase cap or any access/security blocker. Do not expand after clean results.

## Reporting

Report exhaustive static denominator, selected/executed denominators, golden and stored-candidate discovery counts, empty/invalid/unsupported counts, timeout/unknown counts, versions/hashes and every attempted command. If no empty golden discovery occurs after exhaustive inspection, say zero observed in exactly this pinned file; do not infer score inflation, absence in training data, safety for arbitrary model-generated outputs or defect removal. If blocked before inspection, say unknown / not executed, never zero observed.

Preserve the prior pilot and review artifacts unchanged. No push or PR. Stop after this bounded phase, even if broader questions remain.
