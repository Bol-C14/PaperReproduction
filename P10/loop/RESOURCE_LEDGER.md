# End-to-end resource and failure ledger

Tranche began2026-10-28T11:24:23Z in selected PaperReproduction cloud workspace; final result inventory11:47:02Z (~22m39s through inventory, within the one-hour tranche ceiling). Existing branch `reproduction/constraint-aware-rover-tcad2025`. Current host only: five logical CPUs, ~18GiB RAM; no GPU/resource allocation, paid service, new credentials, gated license, security change, push or PR.

Dependencies:122,801,061 bytes of wheel payload (~117.1MiB), including all transitive requirements; small metadata/documentation transfers are not metered exactly. Source/data checkpoints downloaded0. No gated URL was retried. Local disk at inventory: venv486MiB, wheel cache118MiB, YoWASP compilation cache81MiB, run artifacts66MiB. Both caches and venv are git-ignored. Download/disk use stays well below2GB. Official/free provenance and wheel hashes are recorded in SOURCE_VERSIONS.json; YoWASP is explicitly unofficial packaging of open Yosys.

All11 recorded pilot/matrix runs:288 configuration rows,144 optimizer processes,197 synthesis invocations with per-run identical-pair reuse. Positive RTL SAT invocations197; additional expected-failing RTL negative controls3. These are repeated stages on12 unique circuit instances, not288 independent benchmarks. Full machine inventory is AGGREGATE.json.

| Recorded stage | Rows | Run wall seconds | Failed rows |
|---|---:|---:|---:|
| Tree pilot1 |6|4.226|0|
| Tree matrix1 |72|37.463|0|
| DAG pilot1 |6|12.541|0|
| DAG matrix1 |72|109.207|0|
| Live pilot1 (broad primitive reachability) |2|5.124|0|
| Live pilot2 (expression-class filter) |2|5.756|0|
| Live matrix1 |24|43.098|0|
| Full-width pilot1 |6|17.385|0|
| Full-width matrix1 |72|115.864|0|
| Integrated pilot1 |2|4.519|0|
| Integrated matrix1 |24|48.555|0|

Aggregate measured run wall403.739s (~6m44s); optimizer process CPU193.717s. These exclude dependency installation, initial WASM compilation, assistant authoring, a few diagnostic DSL/API probes and the separately logged negative-control wall (~0.8s). No precise full-tranche CPU accounting is claimed. Largest measured child peak RSS105,900KiB (~103.4MiB); peak memory never approached the1GiB observation target. Parent-process peaks are separately in run SUMMARY.json files. Search node maximum252 in unfiltered final matrices, far below5000.

Failure accounting:

- One initial YoWASP `-V` startup failed with `OSError: [Errno 30] Read-only file system: '/home/agent/.cache/YoWASP'`. This exact target was abandoned; process-local `YOWASP_CACHE_DIR=/workspace/PaperReproduction/P10/loop/.cache` worked. No chmod, HOME substitution, escalation or system configuration edit.
- No optimization subprocess failures, solver UNKNOWN, extraction objective-bound mismatch, timeout, unexpected SAT mismatch or synthesis failure across recorded rows.
- Three expected Yosys exit1 proof failures from invalid-guard, signedness and truncation controls are retained, accompanied by Z3 SAT witnesses. They are control detections, not failed positive results.
- Static review repairs: explicit resize on zero/one identities; restrict live-class traversal to expression sorts; cache key includes original+candidate. Historical cache audit found no cross-original reuse. Old live pilot retained. Full independent operand-width reduction was a coverage completion under a new frozen version, not silently backfilled into earlier results.
- A v2 interpolation-clamp configuration synthesized worse than its agnostic control; it remains in the record and report. Final version success does not erase that negative result.
- Full `git diff --check` reported trailing spaces in verbatim Yosys ASCII-art/log output. Raw evidence was retained byte-for-byte; authored source/document/lock/hash files were checked separately. This formatting diagnostic is distinct from solver/synthesis failures.

Protocol hashes, source hashes, package hashes, complete graph/unions, SMT queries, original/candidate RTL, SAT logs, synthesis scripts/logs and generic netlist JSON are local. No model/LLM was called by the optimization program. Earlier asset/fixture-phase resource records remain untouched except links pointing to this later phase.
