# RQ3 — information value prepilot

**Current decision: pause the tested empirical route; do not add an LLM.** This branch contains one real, bounded report-generation probe and its negative selection result. It does not demonstrate an information-induced action change, engineering benefit, or a general negative result about value-of-information theory.

Start with [the real probe result](PROBE_RESULT.md). [PLAN.md](PLAN.md) preserves the initial proposal and its limitations; its strict action-crossover requirement is superseded by PROBE_RESULT.md. Ranking crossover is a strong witness, not necessary: observations could change whether to act, retain the baseline, stop, or validate.

## Completed / not run

- Completed: public-source and native-interface review; one two-thread Vivado 2025.1 process, 36.861568 s, exit 0; two already-existing DCP states; 20 report invocations, before/after input hashes and original report hash checks.
- Completed: synthetic receipt guard test. `protocol.py` checks records only; it is not a budget ledger, functionality checker or engineering validator.
- Not run: an LLM, report-treatment randomization, selected-vs-random policies, a downstream action-value experiment, new implementation/optimization actions, full simulation or formal equivalence. RQ1 results are referenced evidence owned by that branch, not RQ3 executions.
- Transport failures retained in the result narrative: SSH disconnected after launching the sole run; remote receipt and process checks resolved it. An incomplete SCP was repaired by fetching missing files. Neither caused an experimental rerun.

## Limited alternative review

Two alternatives were reviewed read-only after the probe; neither currently warrants another execution batch:

1. **Accepting a logic-changing FPGA candidate.** Functional simulation with completion and output-knownness evidence could change accept/retain/validate decisions, which timing/fanout reports cannot settle. Existing Default output has only a scoped two-state local proof. The semantic acceptance contract, stimulus adequacy, negative controls and bounded two-thread simulation adapter are not established; no natural counterexample is known. A validator calibration is not yet a VOI experiment. [Official validation source](https://github.com/Xilinx/fpl26_optimization_contest/blob/main/validate_dcps.py).
2. **Proceeding from ASIC placement to routing.** New global routing could reveal congestion not resolved by the already-visible RUDY estimate and change continue/re-place/stop decisions. [Placement documentation](https://openroad.readthedocs.io/en/latest/main/src/gpl/README.html) and [global routing documentation](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html) establish the mechanisms. Existing APRIL inventory confirms OpenROAD but no ready placed ODB; no natural estimate discrepancy or <=10-minute setup-and-test was established. ORFS code, design and platform licenses must be checked separately. No new flow was built or run.

Restart requires a real, correctly sourced state with a credible acceptance/checking contract, a nonredundant observation beyond all native visible information, a material legal decision it can change, and measured budget-feasible costs. Do not manufacture ambiguity by concealing reports or count historical metadata as a fresh experiment.

## Evidence and publication

[PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) maps 25 original evidence files to sanitized public versions under `probe/public_evidence/`. Original report SHA256 values in the receipt refer to **original bytes**; published files have separate hashes because machine-specific paths/hostnames were replaced with role placeholders and tool-generated trailing whitespace/blank EOF lines were normalized. Numerical metrics, design identifiers, warnings, timestamps, statuses and failure evidence were retained. No DCP, proprietary tool, environment file, source research attachment or raw personal path is included. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

`probe/report_probe.tcl` is the executed report logic. `probe/run_probe.py` is the same controller with its two previously hardcoded machine input paths converted to required `--original` and `--updated` options for publication; this portability edit was not executed as a new EDA run. The historical launcher and exact argument roles are preserved in the sanitized receipt/result.

Protocol-only check:

```bash
python3 -m unittest discover -s prepilot/rq3 -p 'test_*.py' -v
```

There is no RQ3 CI configuration; none is added. Do not run the probe without an explicitly assigned resource budget and the toolchain's environment/AGENTS instructions.
