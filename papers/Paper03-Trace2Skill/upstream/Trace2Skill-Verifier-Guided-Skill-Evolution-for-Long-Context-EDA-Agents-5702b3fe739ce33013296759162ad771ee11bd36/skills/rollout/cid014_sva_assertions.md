# RTL Agent Skill — cid014: SystemVerilog Assertions (SVA)

**Note:** despite the official CVDP label "testbench_completion", the tasks in
this bucket ask you to **add SystemVerilog Assertions (SVA) to an existing RTL
module**. The assertions live inside the RTL file itself (at module scope or in
a bound `module`), not in a separate testbench. Read the task prompt carefully
to confirm scope.

## What this task asks of you

Add SVA (concurrent and/or immediate assertions) to an existing RTL file to verify protocol correctness, handshake behavior, reset guarantees, and register-access semantics. The assertions are CHECKERS — they do not affect synthesized logic but they fire during simulation if properties are violated.

Your artifact is the modified RTL file with SVA blocks added. An external verifier exercises the design; assertion failures become test failures.

## Strategy

### Phase 1 — understand the module and its properties

1. `ls` the directory; `cat` the target RTL file completely.
2. Identify the module's key signals: inputs (control, data), outputs, internal state registers, clock, reset.
3. `cat` the task prompt carefully — it lists the properties to assert, usually with names and natural-language descriptions. Each property will map to one `assert property` block.
4. Translate each property statement into a temporal formula. Patterns:
   - "After reset deasserts, register X should be Y" →
     `@(posedge clk) $rose(rst_n) |-> (x == Y)`
   - "When `valid` and `!violation`, `access_out` asserts one cycle later" →
     `@(posedge clk) (valid && !violation) |=> access_out`
   - "While `wait_in` is high, `access_out` and `packet_out` must stay stable" →
     `@(posedge clk) disable iff (!rst_n) wait_in |-> $stable(access_out) && $stable(packet_out)`
   - "Signal A implies signal B eventually (within N cycles)" →
     `@(posedge clk) A |-> ##[1:N] B`

### Phase 2 — choose placement

Two idiomatic options:

**(a) Inline at module scope** — assertions live inside the RTL module, after the `endmodule` for logic (or right before it). This is simplest and what most of these tasks expect:

```systemverilog
// inside the module
// ... existing RTL ...

// ── SVA ──
default clocking cb @(posedge clk); endclocking
default disable iff (!rst_n);

property msip_reset_value;
    @(posedge clk) $rose(rst_n) |-> (msip == 1'b0);
endproperty
msip_value_reset_assertion: assert property (msip_reset_value)
    else $error("msip did not reset to 0");
```

**(b) In a `bind` block** — keeps RTL clean by placing assertions in a separate `module` that's bound to the DUT. This is cleaner for production code but some tasks specifically ask for inline SVA.

**Default choice: inline at module scope.** Only use `bind` if the prompt explicitly directs you to.

### CID-specific guidance: assertion-insertion checkpoints

This CID rewards portable checkers that express the requested properties without changing the RTL's functional behavior.

1. Add assertions in the target RTL module unless the prompt explicitly asks for a separate bound checker.
2. Use property names from the prompt exactly when provided. If names are not provided, choose short descriptive labels and keep them stable.
3. Keep each assertion simple enough for the available simulator. Prefer one property per requirement over one clever multi-clause property.
4. If concurrent SVA syntax fails to compile, convert the same requirement into an immediate assertion inside `always @(posedge clk)` guarded by reset and the relevant enable condition.
5. Compile the modified RTL with a visible verification target when one exists; compiling the DUT alone often misses assertion integration issues.
6. Only add checker code. Do not rename ports, change reset behavior, or edit datapath/control logic to make an assertion pass.

### Phase 3 — insert SVA with `edit`, not `echo`

**ALWAYS use `edit(filename, old_text, new_text)` to add SVA.** The RTL file is long; `echo` would require you to reproduce every byte from memory and typically corrupts unrelated logic.

Common pattern: one `edit` with `old_text="endmodule"` and `new_text="<your SVA block>\n\nendmodule"` — inserts the SVA just before the module closes.

If `endmodule` appears more than once in the file (nested modules, `endmodule : <name>` variants), include a few lines of leading context to make `old_text` unique.

You may also use multiple small `edit` calls to add SVA in distinct spots (one near registered outputs, one near handshake signals, etc.). Preserve everything in the original file.

Each assertion should have:
- A meaningful label (`<property_name>_assertion:`).
- An `else $error(...)` or `else $fatal(...)` clause — this gives useful failure messages.
- Correct clocking event (`@(posedge clk)`) and reset gating (`disable iff (!rst_n)` or equivalent).

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 <your_modified_rtl> <testbench_file>")
vvp(filename="sim.vvp")
```

Note: iverilog's SVA support is **partial**. Most concurrent assertion syntax (`property`, `assert property`, `|->`, `|=>`, `$rose`, `$stable`) is supported with `-g2012`. Some advanced constructs (`s_eventually`, complex sequence operators, `bind` in some configurations) are not.

If iverilog rejects a construct, try:
- Simplify to an immediate assertion in an `always` block: `always @(posedge clk) if (rst_n && cond) assert(expected) else $error(...);`
- Break a complex property into simpler ones.

## Common pitfalls for this task type

- **Wrong implication operator**. `|->` is "same cycle" (overlapped); `|=>` is "next cycle" (non-overlapped). "A then B one cycle later" is `|=>`, not `|->`.
- **Missing reset gating**. Without `disable iff (!rst_n)`, your assertion will fire DURING reset every time the reset-invariant signal is X — flooding logs.
- **Using `==` with X/Z signals**. Use `===`/`!==` or ensure the property's LHS excludes the reset window.
- **Forgetting labels**. Unlabeled assertions are hard to diagnose from the output log.
- **Placing SVA outside the module**. Assertions must be inside the `module ... endmodule` block, after all other RTL.
- **Changing the module's functional RTL**. The task only asks for assertions — leave the combinational/sequential logic untouched.

## Critical rules

- **NEVER** `echo` the whole RTL file just to add SVA — use `edit`. `echo` on an existing long file is the top cause of failure on this task type.
- **NEVER** modify the module's existing RTL logic — only add SVA.
- **NEVER** rename the module or change its port list.
- **NEVER** use advanced SVA constructs without verifying iverilog accepts them (err on the side of simpler formulations).
- **DO** label every assertion (`<name>: assert property(...)`).
- **DO** add `else $error("...")` to every assertion so failures print useful context.
- **DO** respect the exact property names the task lists — the grader may pattern-match on them.
