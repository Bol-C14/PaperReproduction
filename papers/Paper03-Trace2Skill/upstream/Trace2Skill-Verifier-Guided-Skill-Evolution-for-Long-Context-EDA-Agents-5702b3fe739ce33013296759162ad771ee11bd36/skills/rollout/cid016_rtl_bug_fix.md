# RTL Agent Skill — cid016: Verification Bug Fix (RTL Debugging)

## What this task asks of you

You are given an RTL design that **fails verification** — the cocotb/Verilog tests report mismatches, hangs, or wrong register values. Your job is to find the bug(s) in the RTL and fix them so the tests pass.

The bugs are usually localized — missing reset, wrong bit, off-by-one, swapped operands, combinational loop, missing case branch. Multiple files may contain bugs; the prompt usually names which files to inspect.

Your artifact is the modified version of one or more RTL files. An external verifier runs after you finish and checks your fixed design.

## Strategy

### Phase 1 — reproduce the failure first

**Never start fixing before you've seen it fail.** Understanding what the existing tests say is half the battle.

1. `ls` the top level, find where the RTL, visible testbenches, and docs live.
2. `cat` the task prompt carefully — it usually names the symptom ("registers don't hold correct values", "adder gives wrong result for normal numbers") and may hint at which file.
3. `cat` visible Verilog/SystemVerilog testbenches when present — they tell you the exact inputs and expected outputs.
4. Compile the current (buggy) design with its testbench and run:
   ```
   iverilog(args="-o sim.vvp -g2012 <RTL files> <testbench>")
   vvp(filename="sim.vvp")
   ```
   Record the EXACT failure message — it names the signal that mismatched, the cycle, and the expected vs actual values.

### Phase 2 — localize the bug

Using the failure message, trace backward through the RTL:

- The signal named in the failure is the bug's **symptom**.
- `cat` the RTL file where that signal is assigned — scan every `always` block or `assign` statement that drives it.
- If the value looks wrong but the logic looks right, check its **inputs** — the bug may be one level up.
- Repeat until you find a line that is demonstrably incorrect.

Common bug patterns:

| Symptom | Likely cause |
|---|---|
| Signal stuck at X or 0 | Missing reset value, or combinational always block that misses a branch |
| Off-by-one value | Wrong index (`[i]` vs `[i-1]`), wrong bit slice |
| Works for some inputs, fails others | Wrong case branch, missing default, missed corner (overflow, zero) |
| Hangs (vvp times out) | Combinational loop — a wire depends on itself through combinational logic |
| Wrong timing (one cycle late/early) | Combinational vs registered logic confusion |
| Intermittent failure | Uninitialized register, race condition across clock domains |

### Phase 3 — fix with `edit`, minimum surgery

**The fix should be as small as possible.** Ideally 1-5 lines changed.

**ALWAYS use `edit(filename, old_text, new_text)`** for bug fixes. It replaces a unique span with new text and leaves every other byte of the file alone — which is exactly what "minimum surgery" means mechanically. `echo` overwrites the whole file and would force you to reproduce hundreds of lines from memory, virtually guaranteeing you introduce new bugs while fixing the old one.

Typical pattern:
```
edit(
  filename="rtl/fsm.v",
  old_text="        state <= IDLE;  // BUG: should be RESET",
  new_text="        state <= RESET;"
)
```

- Resist rewriting the module — even if you think you could write it better.
- If multiple files have bugs (as the patch expectations may indicate), fix them one at a time with separate `edit` calls, re-running the simulation between each to isolate cause and effect.
- Reserve `echo` for the rare case where the task explicitly asks you to create a new file.

### Phase 3.5 — if vvp times out, make the simulator talk

**`vvp` timing out with no output means the testbench is waiting for a completion condition that your broken design never reaches.** Without feedback, every additional edit is a blind guess. Fix this first: make the simulator print something before you make more bug-fix edits.

Use `edit` to insert `$display` probes into the RTL module most likely to be stuck (often the FSM, datapath, or interface block that drives the testbench's wait condition). Probe the signals that must advance for the test to complete: state registers, counters, valid/ready handshakes, addresses, and values the testbench checks against.

Example — insert a probe at every clock edge near the top of the main always block:

```
edit(
  filename="/code/rtl/<suspect_module>.v",
  old_text="    always @(posedge clk) begin\n        if (rst)",
  new_text="    always @(posedge clk) begin\n        $display(\"[t=%0t] state=%h valid=%b ready=%b\", $time, state, valid, ready);\n        if (rst)"
)
```

After inserting the probe, the ordering is **non-negotiable**:

1. `edit` to insert `$display` probes
2. `iverilog` to recompile with the probes
3. **`vvp` to run the simulation and produce the probe output**
4. **READ the vvp output carefully BEFORE making any further edits**

**Never skip steps 3–4.** A probe that is never read is worse than no probe at all — it burned a turn and you are still debugging blind. If you find yourself about to call `edit` again without having seen probe output from the previous cycle, STOP and run `vvp` first. The probe output is the entire point — going straight from `edit` (instrument) → `edit` (guess fix) without an intervening `vvp` forfeits all the information you just paid to generate.

Once you have the probe output, read it to localize the bug:

- **State/counter stuck at one value** -> bug is in the transition or increment enable logic.
- **A checked value becomes wrong starting at cycle N** -> bug is in the assignment active at cycle N or one producer level upstream.
- **Handshake `valid` asserted but `ready` never asserts** -> bug is in the responder's ready-generation logic or back-pressure condition.

**Guidelines for using probes wisely:**

- Keep probes focused. Printing 20 signals every cycle floods the output and is hard to read. Start with 3-5 signals you suspect.
- If the simulation still times out even with probes (output shows thousands of cycles without progress), the probes confirm the hang and point at the stuck signal — that's useful.
- If a subsequent fix makes the trace advance past the previous hang-point but hits a new one, that's progress — the trace evolution IS your debug signal.
- Probes in RTL may affect simulation behavior and output volume. Keep them focused, and remove them once they have revealed the bug if they are no longer useful.

Do this **before** your third blind-guess edit, not instead of fixing the bug. One or two probes converts "vvp timeout" from a black hole into a debuggable signal.

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 <your_fixed_file(s)> <other_RTL> <testbench>")
vvp(filename="sim.vvp")
```

Re-read the failure message after each iteration:
- If the SAME assertion still fails with the SAME values, your fix missed the symptom — look elsewhere.
- If the assertion count dropped but one remains, you fixed one bug; find the next.
- If NEW assertions fail that weren't failing before, you broke something else — revert that change.

## Common pitfalls for this task type

- **Rewriting instead of fixing**. A 100-line rewrite to fix a 1-line bug is almost always wrong — it changes behavior the TB wasn't testing but might test next time.
- **Fixing symptoms not causes**. Clamping an output to match the expected value at the failing cycle hides the real bug and usually breaks later cycles.
- **Modifying the testbench**. The TB is evidence for expected behavior; if you change it during an RTL-fix task, you are no longer testing the real bug.
- **Changing reset polarity mid-file**. If the original uses `rst_n`, keep using `rst_n`.
- **Forgetting to include the fixed file in iverilog command line**. Always recompile with your latest edit.
- **Skipping vvp after iverilog**. Compile success ≠ test pass.
- **Continuing to blind-edit after 2 vvp timeouts**. If vvp has timed out twice with no useful output, stop guessing at the bug fix — insert `$display` probes (Phase 3.5) to see what's happening, then fix with information.

## Critical rules

- **NEVER** `echo` a whole RTL file just to fix a few lines — use `edit`. `echo` on a working-but-buggy file almost always introduces NEW bugs elsewhere.
- **NEVER** modify verification/testbench files unless the task explicitly asks you to create or extend them.
- **NEVER** modify `docker-compose.yml` or `.env`.
- **NEVER** clamp outputs to constants just to pass the test — find the real bug.
- **DO** keep every change minimal and justified by the failure message.
- **DO** re-run the full test after each edit — don't batch fixes and debug at the end.
- **DO** apply your `edit` call to the exact RTL file path the prompt or patch expects (if the patch expects `rtl/sm_cpu.v`, your `edit` targets `/code/rtl/sm_cpu.v`).
- **DO** insert `$display` probes (Phase 3.5) when vvp times out — converting silence into a trace is almost always worth 1-2 turns.
- **DO** always run `vvp` immediately after an `edit` that added probes, and READ the output before any next `edit`. `edit(add probe) → iverilog → vvp → read → edit(fix)` is the pattern. Never `edit(add probe) → iverilog → edit(fix)` — that wastes the probe.
