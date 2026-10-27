# RTL Agent Skill — cid013: Testbench Checker Extension

**Note:** despite the official CVDP label "testbench_generation", the tasks in
this bucket ask you to **extend an already-existing testbench** — specifically
to add checker logic to a TB that already has stimulus generation. Read the task
prompt carefully to confirm, but expect to be editing an existing `tb_*.sv` file,
not creating one from scratch.

## What this task asks of you

The project already has a testbench that generates stimulus, applies it to the DUT, and captures outputs — but it does not verify correctness. Your job is to add the checker: compute expected values from the stimulus, compare against the DUT's actual outputs, and report mismatches.

Your artifact is the extended testbench file. Occasionally the task also touches one RTL file when the checker needs a small reference helper.

## Strategy

### Phase 1 — understand the existing TB structure

1. `ls` the testbench directory (often `smart_run/logical/verif/` or `tb/`).
2. `cat` the existing `tb_*.sv` file completely. Identify:
   - DUT instance name (usually `dut`).
   - The stimulus task (usually `apply_test` or `drive_inputs`).
   - How inputs are parameterized — often a loop over `num_tests` with an array of test vectors.
   - The DUT output signals that are already captured (as `logic`s in the test module).
   - Whether there's already a `$display` of results, even without comparison.

### Phase 2 — understand the expected-value reference

1. `cat` the DUT to learn its transfer function — given inputs X, what outputs Y should emerge.
2. Look for reference logic the task may have hinted at (e.g., a helper module, an `expected_` signal the stimulus generator precomputes).
3. Construct your checker either:
   - **By software model** — inside the TB, compute the expected output in pure SystemVerilog behavioral code.
   - **By reference signal** — if the stimulus generator already writes `expected_*` signals, compare DUT outputs against those.

### CID-specific guidance: checker-extension checkpoints

This CID rewards adding verification logic without disturbing the existing stimulus. Your main risk is "fixing" the DUT or rewriting the bench so the original coverage disappears.

1. Edit the existing testbench file named by the prompt. Do not modify DUT RTL unless the prompt explicitly expands the scope.
2. Preserve stimulus ordering, delays, random seeds, dumps, and the existing `$finish`. Insert checks at points where expected and actual values are both valid.
3. Use exact labels, names, and messages requested by the prompt when provided. Hidden grading may pattern-match those identifiers.
4. Account for latency. If the DUT responds after N cycles, delay the expected value by N cycles or sample after the existing task has allowed outputs to settle.
5. Compare with `!==` when X/Z should count as failure. Print inputs, expected, actual, and time for every mismatch.
6. Compile only `.sv`/`.v` RTL and testbench files. Python/cocotb files are useful evidence but not `iverilog` sources.

### Phase 3 — insert the checker via `edit` (surgical), NOT `echo` (whole-file rewrite)

**ALWAYS use `edit(filename, old_text, new_text)` to add checker logic.** The testbench is already hundreds of lines long; if you `echo` the whole file from memory you will almost certainly lose or corrupt existing stimulus, dumpvars, or the `$finish` call, and the task will fail before your checker is even tested.

Use a sequence of small `edit` calls, each replacing a narrow unique span:

1. `edit` to add variable declarations near the top of the module (find an existing `localparam` or the top of an `initial` block as the anchor).
2. `edit` to insert comparison logic inside or right after the stimulus task.
3. `edit` to add the summary block right before the existing `$finish;`.

Example for step 3:
```
edit(
  filename="verif/tb_foo.sv",
  old_text="    $finish;",
  new_text="    $display(\"SUMMARY: %0d PASSED, %0d FAILED\", pass_count, fail_count);\n    $finish;"
)
```

If `old_text` is not unique, `edit` will return an error listing the match count — simply include 1-2 extra lines of surrounding context and retry.

Typical insertion point is immediately after the stimulus task applies inputs and captures outputs. Pattern:

```systemverilog
// Inside the existing `apply_test` task or equivalent:
@(negedge clk);  // sample one edge after outputs settle

if (sel_out_onehot !== expected_onehot) begin
    $display("FAIL: test %0d, expected onehot=%b, got %b at time %0t",
             test_idx, expected_onehot, sel_out_onehot, $time);
    fail_count++;
end else begin
    $display("PASS: test %0d", test_idx);
    pass_count++;
end
```

At the end of the test, print a summary and `$finish`:

```systemverilog
$display("SUMMARY: %0d PASS, %0d FAIL", pass_count, fail_count);
if (fail_count == 0) $display("ALL TESTS PASSED");
else                 $display("SOME TESTS FAILED");
$finish;
```

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 <your_extended_tb>.sv <dut_files>.v ...")
vvp(filename="sim.vvp")
```

## Common pitfalls for this task type

- **Comparing at the wrong time**. DUT outputs must settle after the input edge. Use `@(negedge clk)` one cycle after driving, or explicit `#delay` that matches the DUT's pipeline depth.
- **Using `==` instead of `!==`** for reference comparison. In SystemVerilog, `===`/`!==` are case-equality operators that also match X/Z; for checker purposes, usually `!==` (case-inequality) is what you want when X/Z should count as failures.
- **Overwriting stimulus logic**. Add the checker; don't rewrite the existing stimulus structure — the verifier may depend on its timing.
- **Losing the `$finish`**. If the existing TB had one, keep it; if not, add one after your summary.
- **Miscomputing expected values**. If the DUT has latency-2, your expected must also be delayed by 2 cycles before comparison.
- **Forgetting to declare new variables**. `fail_count`, `pass_count`, `expected_onehot` must all be declared at module scope with `int` or `logic [W-1:0]`.

## Critical rules

- **NEVER** `echo` the whole testbench file — use `edit` for surgical additions. `echo` on a long existing file is the most common cause of failure on this task type.
- **NEVER** rewrite the existing stimulus generator — preserve its signature and ordering exactly.
- **NEVER** delete the existing `$dumpfile`/`$dumpvars` — they may be required by the grader.
- **NEVER** compare at `@(posedge clk)` without accounting for DUT pipeline latency.
- **DO** count both passes and failures — a run with zero FAIL messages but zero PASS messages is almost always broken.
- **DO** `$display` the test vector inputs alongside the expected/actual values — makes debugging the checker itself much easier.
