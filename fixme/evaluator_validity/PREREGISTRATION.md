# Evaluator-validity pilot: preregistration

Frozen before new oracle experiments on 2026-10-28 UTC. This is a purposive,
mechanism-testing sample, not a prevalence estimate. No model API or GitHub issue
operation is permitted. The original five task definitions remain unchanged;
this round uses four independent designs from four families. The known executable
GA_94 blind spot is a sentinel rather than a prior calibration-pass sample.

## Samples and fixed interventions

1. **MGen/L3/Text/GA_94**, supplied CPU TB and source-derived C++ reference.
   Preserve its comparator. Eleven candidate trials: identity; XOR value_o_ref
   bits 0/7, is_positive_ref bit 0, easter_egg_ref bits 0/1/2; value_o_ref stuck
   zero/all-ones; malformed C++; nonterminating C++. XOR changes are witnessed
   at the DPI output; constant faults count as activated only if actual before/
   after values differ. Expected mechanism: the original scalar match can miss
   non-LSB concat differences. No comparator repair is allowed.
2. **TBGen/L1/Text/address_mux**, a prior executable calibration-pass input.
   Correct source; stuck-zero output; stuck-ones output; reversed select;
   upper-byte truncation; output LSB inversion; empty TB bypass. Execute all
   seven candidates with both Icarus and Verilator, same deterministic 64-vector
   checker and seed 13579. Correct checking emits TEST_PASS/TEST_FAIL. Replay the
   exact pinned VCSRunner parser on actual captured logs; this is parser replay,
   not a VCS run. Independent source-derived oracle limits remain explicit.
3. **RTLFix/L1/MultiModal/1**, a prior executable 4:1 mux input.
   Correct repair; unchanged original bug; output stuck zero/one; reversed select;
   an exception only for the all-zero six-input vector. Run each of six candidates
   against both unchanged official six-check TB and an independent exhaustive
   64-vector binary mux oracle, with both simulators. Hypothesis: the rare-trigger
   candidate can survive the supplied sample but fail the exhaustive oracle.
4. **SVAGen/L1/Text/usbh_crc16**, a prior proof-calibration-pass input.
   Compare a valid single-bit invariant and a 16-output reference-derived property
   suite on original source and four RTL faults: covered-bit inversion, covered
   bit stuck-zero, uncovered-bit inversion, bit15 XOR-to-OR operator error.
   These ten proofs plus constant assertion on original/covered mutant, empty
   property set, and malformed assertion make fourteen formal trials. Count actual
   lowered assertion cells. A proof of one relationship does not certify complete
   specification coverage. Constant/empty sets cannot pass the adequacy policy.

Total planned primary trials: 11 + 14 + 24 + 14 = **63**. Baseline materialization
and isolation probes are auxiliary, separately counted. No new designs or fault
classes may be selected in response to outcomes. Ordinary syntax/adapter repairs
may preserve these frozen inputs/interventions, with old failures/diffs retained.

## Budgets and stop rule

At most 150 supervised subprocess invocations and 14 minutes wall time for this
round; at most two simultaneous workers. Per command: compile/build <=45 s,
simulation <=3 s, Yosys <=15 s with SAT <=5 s. Child CPU <=60 s, address space
<=2 GiB, file <=8 MiB, open FDs <=256; kill process groups on timeout. If a cap is
reached, retain unexecuted/unknown records and stop. Do not increase budgets,
change check counts, invent assets or repair official comparators to improve scores.

## Isolation and provenance

Only hash-verified pinned inputs and locally authored fixed mutations are executed.
No shell or arbitrary supplied response is accepted. Use a sanitized credential-
free environment, private cwd, closed inherited FDs, no-new-privileges and existing
seccomp network/process-control denial. Probe with synthetic canaries, never real
credentials. Host namespace/Landlock filesystem isolation was previously unavailable;
no host/security/network/credential configuration will be changed to enable it.
A synthetic sibling-file probe documents the actual boundary. If filesystem
confinement remains absent, restrict execution to these reviewed recipes and state
that this is not an untrusted-code service. All tools already exist from pinned
Debian packages; no package or paid-service installation is needed.

Retain original/candidate source hashes and unified injection diffs, per-command
raw feedback/return state, functional witness counts, oracle decisions, and backend
identity. Distinguish comparator/coverage weakness, adapter error, language/tool
unsupported state and timeout/infrastructure unknown.

## Falsification and reporting

A surviving mutant is only an observed blind spot if it compiled/ran, a baseline
passed, and its wrong behavior was activated/witnessed or independently established.
A nonactivated constant fault is not evidence of false acceptance. Malformed and
nonterminating candidates are separate from functional-mutant denominators.
Report outcomes by independent design, fault class and backend. Cross-simulator
agreement is descriptive for these binary-input fixtures, not proof of VCS or
four-state equivalence. Do not infer a corpus-wide false-positive rate, model
ranking or published aggregate. Stop after these planned outcomes and archive the
round, even if hypotheses are falsified or results remain inconclusive.
