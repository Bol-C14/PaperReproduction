# Commands and tool-run accounting

Run 1: environment/instructions/status/tool availability inspection. No AGENTS.md found beneath PaperReproduction. Python 3.12.14 and coreutils timeout available; iverilog, vvp, yosys and sby not found on PATH.
Run 2: create reproduction/assertsolver-dac2025 branch and write this pre-test protocol. No upstream source edits.
Run 3: write build_fixtures.py and checker.py. Static-only implementation; no tests executed before protocol. Fixture review is recorded inline and in PROTOCOL.md. No install/download.

Run 4 (sole test run), from independent-port:
```sh
export GIT_NO_LAZY_FETCH=1
date -u +%FT%TZ > logs/run-start.utc
timeout 10s python -I build_fixtures.py > logs/build.stdout 2> logs/build.stderr
# build exit 0; only then:
timeout 10s python -I checker.py > logs/checker.stdout 2> logs/checker.stderr
# checker exit 0; statuses saved in logs/exit-codes.txt
date -u +%FT%TZ > logs/run-end.utc
```
No correction or test rerun was needed. Log inspection was part of the same tool run.

Run 5: write results narrative, append the completed milestone to the existing asset audit, create provenance/resource ledger and artifact hashes. Standard-library file reads/writes only. No additional tests or downloads.
Run 6 (planned final check): inspect JSON/expected-result consistency, checksum verification and branch/resource status. No checker rerun or new fixture.

All commands were executed through exec_command in the selected Linux cloud environment. Total continuation tool runs: 6 if final verification completes; cap 20. No web/API/provider calls in this continuation.
