# CVDP bounded reproduction record — 2026-10-28

**Current status: reference_calibration + offline_replay, current-release bubblewrap port.** No live pilot, paid API, paper-level performance reproduction, push or public benchmark-answer payload. Cost USD 0.

## Pins and environment

Paper arXiv:2506.14074v1, 17 June 2025. Infrastructure `8e894cf74414ab1eaea1e2b4e80a02f123df07b6`; HF dataset `5b807d945f6a99aa645f7e43a64a2115e281b4bf`, v1.1.0. Five ordinary splits contain 772 tasks. Exact dataset, record and source hashes are in `manifest.json`, `selection.json` and `raw/`.

Existing Bol-C14/PaperReproduction, local branch reproduction/benchmark-cvdp, base `107d3015cb9a210f1e9a28a7910c0981eacc7600`. Only benchmarks/E1_CVDP changed. Initial inherited checkout needed sparse/partial-clone configuration because unrelated checkpoint blobs were absent; no other paper was modified.

APRIL shared root `<EXECUTION_PRIVATE_ROOT>`. Private dedicated envs/cvdp and tools/cvdp. Python 3.12.12, cocotb 2.0.1, pytest 8.3.2, Icarus 13.0 tag v13_0, source `dfeee909ed9f20b4870dd93423156c0170c0e1ff` (generated configure dirty). Initial build lacked gperf; privately built gperf 3.1, then Icarus with make -j4. Tools about 361 MB, environment 35 MB. No global install, credential or security change. Existing bubblewrap 0.6.3 isolated runs; Docker unavailable, Verilator was initially absent; follow-up privately installed exact v5.038 (see LINT_DELTA.md). Historical paper toolchain and Docker image were not reproduced.

## Authorization and enforced isolation

Earlier sample transfers were denied before execution for isolation, then sensitive-egress authorization. All denials are preserved. After explicit user approval at 22:55:36 UTC naming eight samples/reference material, runner, APRIL destination and private calibration-only use, the original target was verified empty and one original-command retry was approved. Both transferred hashes matched locally and remotely. No future evaluated agent has access to these assets; no evaluated agent ran.

Six synthetic probe groups verified namespace filesystem/process/network boundaries, exact runtime mount escape denial, environment clearing, read-only inputs, writable output, memory/file/CPU and wall-time limits. See ISOLATION_CONTRACT.md. First probe expectation errors (PWD, signal exit encoding) are retained. During calibration only one candidate and one trusted task harness are read-only mounted, with a dedicated writable result directory. No host HOME, shared-root, credentials or repository history mounts. Four CPU-affinity slots; 90-second wall/CPU and 2 GB address-space caps. Per-file cap 100 MB; aggregate output observed about 5.1 MB. No seccomp/cgroup process-count or aggregate quota is claimed.

## Frozen tasks and actual outcomes

| Task ID (cvdp_ prefix omitted) | Category | Official reference | No-op | Invalid | Additional controls |
|---|---|---|---|---|---|
| agentic_Min_Hamming_Distance_Finder_0001 | cid005 | withheld/not_run | rejected: missing top | rejected | not run |
| agentic_lfsr_0001 | cid016 | withheld/not_run | assertion rejected | rejected | not run |
| copilot_Carry_Lookahead_Adder_0001 | cid003 | withheld/not_run | missing code rejected | rejected | independent truth-table + equivalent carry pass; XOR propagate rejected |
| copilot_bcd_adder_0001 | cid002 | withheld/not_run | missing code rejected | rejected | not run |
| copilot_cont_adder_0006 | cid004 | withheld/not_run | compile/elaboration rejected | rejected | not run |
| copilot_cont_adder_0042 | cid007 | withheld/not_run | four simulation tests pass | rejected | follow-up lint rejects no-op; full task fails |
| agentic_fixed_arbiter_0001 | cid003 | example reference passes | missing code rejected | rejected | no-override rejected; extra-wire accepted; reference multihot error accepted; spec-onehot alternative accepted |
| copilot_lfsr_0001 | cid003 | example reference passes | missing code rejected | rejected | constant-zero incorrectly accepted; vector equivalent accepted |

The eight named tasks were frozen before execution; no exclusions or replacement tasks. Six ordinary public references contain empty placeholders, not runnable solutions. Two references come from later official examples, not the held-out paper corpus. The arbiter incorrect_multihot_override row intentionally duplicates reference source; do not count it as independent implementation diversity.

Attempt 1: 26 launches all failed before simulation (sandbox /bin missing). Repaired the namespace with /bin→usr/bin and writable pytest-cache path; no host changes. Attempt 2: 26 launches, 9 simulation harness passes, 17 rejections, six additional reference-not_run records. This control pass count has no model-performance meaning. All eight invalids rejected; one no-op passes simulation only. No timeout. Raw outcomes are in raw/results.json; attempt 1 is retained separately.

Independent specification assertions: LFSR reference and vector equivalent pass; constant zero fails seed loading. Arbiter reference fails override=3 one-hot requirement; one-hot-override alternative passes. That alternative also passes the original one-test cocotb harness. Five assertion runs plus one upstream replay, all with retained compile/run logs. These checks were authored by the same reproduction engineer from the specification; they are a separate oracle, not a separate human audit.

Original harness success requires nonempty cocotb testcase XML with no failures/errors/skips and a successful runner. Independent testbenches use explicit assertions and fatal failures plus completion evidence. No correctness conclusion is inferred from a PASS string or exit status alone. The LFSR and arbiter false acceptances are demonstrated only for these released examples.

## Commands and evidence

Actual setup: Python venv; pip install cocotb==2.0.1 pytest==8.3.2; private gperf build; git clone --depth 1 --branch v13_0 Icarus; autoconf/configure/make -j4/install. See raw tool/build logs.

Actual execution (all absolute paths use the shared root):

```
envs/cvdp/bin/python checkouts/cvdp/calibrate.py checkouts/cvdp results/cvdp/calibration1
envs/cvdp/bin/python checkouts/cvdp/calibrate.py checkouts/cvdp results/cvdp/calibration2
envs/cvdp/bin/python checkouts/cvdp/independent_checks.py
```

The runner invokes timeout → bwrap allowlisted mounts/cleared environment → prlimit → pytest and original task test_runner.py. No model adapter or API call is involved. Private executed runners and per-run exact command arrays are retained, not committed because they contain solution variants/evaluator content.

Private raw archive on APRIL: results/cvdp/calibration-evidence.tar.gz; identical local archive in `<CONTROLLER_PRIVATE_ROOT>/evidence-private/`. SHA256 `4e15e868ac80a109fb6978d199f2865b6e13e4a222942ec8d94c179b481d09b5`. Every archived file hash/path/size is recorded in raw/private_evidence_inventory.json; contents stay private. It includes all failed attempts, candidates, original tests, XML, stdout and independent assertions. Public-safe committed summaries contain no solutions/hidden-test bodies.

Remaining limits: six official references unavailable; cid007 positive reference still unavailable; commercial tasks resource_blocked; comprehension scoring and historical model runs not_run. Meaningful open-tool calibration is complete within the frozen scope; parent independent audit and any live pilot remain separate work.

## Independent-audit delta

After audit baseline ea499155, exact Verilator v5.038 original lint was run on the same no-op and invalid candidates; both reject. The earlier simulation-only pass is retained, while complete-task no-op pass is now false. No prior 32-result record or initial 26 infrastructure failure was changed. Build/runtime dependency details, raw private evidence and exact command are in LINT_DELTA.md and raw/lint_results.json. Two additional test invocations, zero model calls, zero USD.

Audit clarification: arbiter supplemental assertions test the multi-hot override requirement only. They do not test or resolve the synchronous-specification versus asynchronous-reference reset mismatch. Full specification conformance of the alternative is not established.

Accounting correction: 58 pre-lint startup attempts = 26 infrastructure failures + 26 original-checker runs + 6 supplemental checks. The follow-up adds 2 lint attempts, for 60 total startup attempts. They are not 58/60 successful runtime tests. Six missing-reference records are nonexecutions, not additional startup attempts. Earlier raw command/path logs are public redacted derivatives; exact original bytes remain private.

Runner provenance correction: the old source_hashes calibrate.py entry was ambiguous and did not match current bytes. The early draft and initial-isolated source snapshots were not located and remain UNKNOWN; only historically recorded/observed digests survive. The fixed executed runner and later unexecuted draft are separately hashed from real preserved files in raw/runner_version_index.json. No missing version was reconstructed.
