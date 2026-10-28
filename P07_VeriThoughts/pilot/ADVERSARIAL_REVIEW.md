# Adversarial claim-boundary review — existing evidence only

Reviewed base: `af2b7d4833a51c63ba3693f4915dbceafd1ee2c4`. No new HDL execution, simulation, synthesis, inference, EDA experiment, model/API call, tool installation, or push. The only computation was reading existing logs, checking hashes and re-deriving elementary fixture truth tables/closed forms. Supporting output: [recomputed.json](review/recomputed.json).

**Conclusion:** one verified evaluator input-validation defect on a synthetic edge case; one documented bounded-contract limitation; one expected rejection under the paper's explicit per-module contract; one logging artifact introduced by our direct port. None establishes a published numerical error, a released-dataset error rate, or invalidity of the paper.

## Pinned primary sources

Upstream commit: `f44c2af999de62bd27e90e73ce9cbd4f97fbe55c`; file `evaluation_verithoughts/evaluation_script.py`; verified Git blob `74963ae51ca6360b5b5944b03c266f7f48309b06`, SHA256 `fd27d6f767c458a8e93bda102741a17b6f19e3d05d7024dc0e3bc359bf0a8ddd`.

- [Lines 31–70: formal invocation](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/evaluation_script.py#L31-L70): loop over discovered golden modules; bounded command at L46; original `stdbuf` at L54; timeout/return-code capture at L59–69.
- [Lines 72–94: module discovery/renaming](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/evaluation_script.py#L72-L94): L74 regex requires a parenthesized port list after the module name/optional parameters.
- [Lines 113–125: candidate parsing](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/evaluation_script.py#L113-L125): plain candidate text is retained if no module block is extracted.
- [Lines 128–165: normal entrypoint and label](https://github.com/wilyub/VeriThoughts/blob/f44c2af999de62bd27e90e73ce9cbd4f97fbe55c/evaluation_verithoughts/evaluation_script.py#L128-L165): argparse/load at L128–140; per-row execution at L154–156; zero-count success and JSON output at L157–165.
- [Official paper, printed p.5, §3.4](https://papers.neurips.cc/paper_files/paper/2025/file/0c946accd3ccc88c09dfae7e1cd40ffe-Paper-Datasets_and_Benchmarks_Track.pdf#page=5): broad verification discussion includes “for all possible input combinations”; its final paragraph explicitly requires “all sub-modules are functionally equivalent” for a positive label. These two short excerpts are the only direct paper quotations in this review.
- [Paper printed p.19, Appendix A](https://papers.neurips.cc/paper_files/paper/2025/file/0c946accd3ccc88c09dfae7e1cd40ffe-Paper-Datasets_and_Benchmarks_Track.pdf#page=19): the displayed Yosys script discloses `-seq 50` and `-set-init-zero`, after `clk2fflogic`. No induction option is present.
- [Paper printed p.4, Figure 2 and §3.3](https://papers.neurips.cc/paper_files/paper/2025/file/0c946accd3ccc88c09dfae7e1cd40ffe-Paper-Datasets_and_Benchmarks_Track.pdf#page=4): question construction preserves module/interface names for every module, reinforcing the intended module-level interface contract.

Page numbers above are printed page numbers and 1-based PDF page numbers; web tool zero-based PDF indices were 4, 18 and 3 respectively.

## 1. Delayed divergence: expected bounded-contract limitation

Existing [original 50-step log](runs/attempt1/delayed_pulse/original/yosys_0.stdout.log) reports SAT success; the [faithful port](runs/attempt1/delayed_pulse/port/top.stdout.log) does too. The separate frozen [160-step diagnostic](runs/attempt1/delayed_pulse/novel_bound160/top.ys) changes only the bound; it reports proof failure. The full [logging-only replay witness](runs/supplemental_logging/yosys.stdout.log) has count=60, gold.y=1, gate.y=0 and trigger=1 at returned SAT frame 160. That returned frame is not claimed to be the earliest possible SAT divergence.

From the RTL, after n rising edges from zero, golden count is n modulo 256 and golden output is 1 exactly when that count is 60; candidate output is constant zero. Existing [Icarus observations](runs/attempt1/delayed_pulse/oracle/simulate.stdout.log) match this closed form for n=0…260; first differing edge is 60. A 50-step transformed check cannot establish behavior beyond its horizon, and the disclosure in Appendix A makes this a documented limitation rather than a hidden solver defect.

**Reporting ambiguity, limited inference:** §3.4's general equivalence language could be read too broadly if separated from Appendix A. Universal input coverage at a fixed depth does not imply an unbounded temporal theorem. The paper does disclose its command; the pilot does not prove that authors intended an unbounded claim, that any published score is wrong, or that any released example actually diverges late. Calling this a published error would overstate the evidence.

**Classification:** expected bounded-contract limitation; possible clarity ambiguity in summary wording. No new implementation defect established by this case.

## 2. Empty discovery: verified input-validation defect, scoped to a synthetic edge case

This is **not solely our port's behavior**. The unchanged upstream blob was executed through its full argparse/load/parse/evaluate/write entrypoint using `runpy.run_path(..., run_name='__main__')` and the original CLI arguments. [original_driver.py](original_driver.py) only intercepts subprocess calls to retain logs, delegating unchanged arguments/timeouts. For this case the subprocess loop is never entered, so that instrumentation cannot manufacture a Yosys success code.

The existing evidence chain is internally consistent:

1. [responses.jsonl](runs/attempt1/empty_discovery/original/responses.jsonl) supplies legal no-port golden text and candidate text `THIS IS NOT LEGAL VERILOG`.
2. The original candidate parser's fallback at L122–124 preserves that text. The original [written verilog_gen.v](runs/attempt1/empty_discovery/original/responses/verilog_gen.v) is byte-for-byte identical to the supplied invalid text, including its newline.
3. L74's regex does not recognize `module top; ... endmodule`. It returns an empty map. L37–38 thus leads to no Yosys calls; L157–163 compares 0 successful checks with 0 total checks and sets success true.
4. [Original evaluation JSON](runs/attempt1/empty_discovery/original/responses_evaluation.jsonl) contains exactly one row: empty stdout_list and success true. The [outer attempt ledger](runs/attempt1/attempts.json), attempt 22, records normal original-driver exit rc=0. The console's pass@1=1.0 agrees; invalid pass@5/pass@10 values are not used as evidence.
5. Independent Icarus syntax/elaboration attempts 23 and 24 have golden rc=0 and candidate rc=2, with an explicit syntax diagnostic in [candidate.stderr.log](runs/attempt1/empty_discovery/oracle/candidate.stderr.log). These statuses are re-read from the ledger, not inferred from a container's success exit.

The defective acceptance is real at the entrypoint for these supplied inputs. It is an **input-validation/empty-loop robustness defect**, not a proof of behavioral equivalence for invalid syntax. The golden fixture has no ports or observable outputs and is not an independently validated member of the released benchmark domain. That edge case and corpus reachability limitation must accompany the defect claim. No released label is shown incorrect.

**Classification:** verified implementation defect on a synthetic valid-gold/invalid-candidate input. Impact in the actual dataset/benchmark is unmeasured, and no security severity is assigned.

## 3. Helper rewrite: expected rejection within the claimed contract

The golden design defines a helper XOR module and a top module instantiating it. The candidate retains the top interface and inlines XOR, omitting the helper. Existing [oracle output](runs/attempt1/helper_inline/oracle/simulate.stdout.log) exhausts the top-level truth table 0,1,1,0 on both sides. This proves the tiny top-interface equivalence claim, not compliance with the required sub-module inventory.

Original/port labels fail with module return codes [1,0]. The [original first module stderr](runs/attempt1/helper_inline/original/yosys_0.stderr.log) says the candidate helper cannot be found. The [second module check](runs/attempt1/helper_inline/original/yosys_1.stdout.log) succeeds for the top pair. Source L38–46 deliberately iterates all golden modules. Printed p.5 §3.4 explicitly requires all corresponding sub-modules, while p.4 Figure 2 asks for every module/interface.

The candidate is therefore **outside the paper's full per-module response contract**, even though it is inside a weaker top-level-only contract. Describing this as a false rejection of a contract-compliant answer would be wrong. It is useful when adapting the evaluator to architecture-changing code generation, but it is not evidence of an upstream bug or an error in this paper's stated protocol. Our fixtures do not contain a generated Q establishing that helper omission would be allowed.

**Classification:** expected contract restriction; no verified defect. The term false rejection is withdrawn for the claimed paper contract.

## 4. Our port artifact and initial-state boundaries

The incomplete first 160-step stdout belongs to **our direct port**, which omitted the original command's `stdbuf -o0` wrapper. The original evaluator already uses unbuffered stdout at L54. Its labels were unaffected, but direct-port output ended mid-line on fatal proof failure. [Amendment 1](AMENDMENT_1_LOGGING.md), commit `e70f6cc`, was committed before exactly one replay of the same 160-step script. That replay is logging-only, not original-method reproduction evidence or a statistical replicate. Its wrapper/container exit rc=0 must not be confused with its recorded Yosys proof-failure rc=1.

The sequential fixtures have no reset input and no RTL initial blocks. The Icarus testbench explicitly forces user registers to zero, matching the SAT command's assumed initialization for unspecified state. Native HDL execution without that testbench would initially contain X values; the pilot does not prove four-state or arbitrary-initial-state equivalence. `clk2fflogic` also introduces clock-sampling state whose explicit initialization appears in the SAT witness; it is not correctly described as forcing every transformed register to zero. SAT steps and rising edges are different units. No reset sequencing, asynchronous reset fidelity, multi-clock behavior, parameter sweep or eventual inductive invariant was tested.

Rechecked controls: De Morgan truth table agrees on all four inputs; AND/OR first differs at index 1; modulo-16 +1 versus -15 agrees; +1 versus +2 first differs at edge 1; delayed pulse first differs at edge 60; inlined XOR agrees at top; both invalid candidates have independent syntax failure. These checks use existing 4/261-row logs and closed forms; no new HDL execution occurred.

## Corrections and evidence preservation

Earlier shorthand about three contract gaps was too broad. Documentation now distinguishes the single implementation defect from expected limitations/restrictions and our logging artifact. The original numeric observations and raw outcomes remain unchanged. No rate is estimated from handpicked fixtures and no paper-invalid claim is made.

The review's [before snapshot](review/before_hashes.json) hashes 218 existing protocol/input/harness/result/log files, including the original freeze manifest and logging amendment. [After snapshot](review/after_hashes.json) and [hash verification](review/hash_verification.json) record whether every protected byte remained unchanged. The frozen PROTOCOL SHA256 remains `0f0efbea3d8d99efef2a3db529ad3a2ef6bfec2143091160c3c236d5ad624875`; all 23 original freeze entries are reverified. The first review-only ledger filter assertion failure and its correction are transparently noted in [RECOMPUTATION_NOTE.md](review/RECOMPUTATION_NOTE.md).
