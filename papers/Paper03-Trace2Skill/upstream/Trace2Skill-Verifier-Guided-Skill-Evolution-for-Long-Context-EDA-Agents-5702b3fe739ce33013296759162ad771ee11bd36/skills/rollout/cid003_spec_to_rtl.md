# RTL Agent Skill — cid003: Spec → RTL

## What this task asks of you

You are writing a **new RTL module from scratch** against a written specification. The spec usually lives in `docs/` or in the task prompt itself. Reference RTL modules (protocol blocks, wrappers, FIFOs, controllers, etc.) already exist in the project — study them to match interface conventions, but **your output is a brand new `.v` file** (occasionally `.sv`).

Your artifact is one or two RTL files you create under `rtl/`, `hardware/src/`, or whatever path the prompt specifies. An external verifier grades your work after you finish.

## Strategy

### Phase 1 — orient (3-4 tool calls)

1. `ls(".")` to see top-level layout. Look for `docs/`, `rtl/`, `src/`, `hardware/`, a `README.md`.
2. `ls(docs/)` if it exists — there's often a `.md` spec file to read first.
3. `cat` the spec document. This is your contract — extract: module name, port list (names + widths + directions), reset behavior, clocking, parameters, key state transitions.
4. `ls(rtl/)` (or wherever the prompt says the target lives) to see neighbor modules.
5. `cat` one or two of those neighbors — they show the code style (header comment block, port alignment, naming conventions) the reviewers expect. Match it.

### Phase 2 — study visible interface evidence (critical)

Use the visible task prompt, specs, neighbor RTL modules, and any visible Verilog/SystemVerilog testbench (`tb_*.v`, `tb_*.sv`) to infer precisely what inputs will be applied and what outputs are checked. A visible Verilog/SV TB often instantiates your module with the exact port names and widths you must expose.

**Mismatched port names or widths are the #1 reason solutions fail without ever compiling correctly.**

### CID-specific guidance: spec-to-RTL checkpoints

This CID rewards disciplined translation from a written contract into a fresh module. Your main risk is inventing behavior or ports that are not in the prompt, spec, neighbor RTL, or visible Verilog/SystemVerilog testbench.

1. Build a compact interface table before writing: module name, parameters, every port name, direction, width, reset value, and timing rule.
2. Treat visible testbench instantiation as strong evidence for exact port names and widths. If it conflicts with your memory of a common protocol, trust the local files.
3. Implement only the behavior the spec requires. Do not add extra buses, status ports, or protocol features because they are common in similar designs.
4. Keep declaration order and driver ownership simple: declare every internal signal before use, use one driver per net/reg, and choose either registered or combinational ownership for each output.
5. Compile only Verilog/SystemVerilog sources with `iverilog`; Python/cocotb files are evidence to read, not simulator inputs.
6. If compile fails, fix the first compiler error with a small targeted edit. Rewriting a new RTL module from scratch usually creates a different set of interface mistakes.

### Phase 3 — implement (one echo)

Write the complete module in one `echo`. Partial RTL is worse than none.

Required structure for most modules:

```verilog
module <name> #(parameter ... = ...) (
    input  wire         clk,
    input  wire         rst_n,   // or rst — check the neighbors
    // ... port list matching the spec exactly
);
    // local params
    // FSM states (if applicable)
    reg [...] state;
    // sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset all outputs and state
        end else begin
            // state transitions
        end
    end
    // combinational outputs (if not part of the FSM)
    assign ... = ...;
endmodule
```

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 rtl/<your_file>.v <testbench>.sv")
vvp(filename="sim.vvp")
```

If compile fails: read the first error only, fix it, recompile. Later errors are often cascades.
If compile succeeds but simulation FAILs: re-read the failing `$display` or `$error` message — it names the signal that mismatched and the cycle.

## Common pitfalls for this task type

- **Forgetting a port** the testbench drives or checks. Re-cat the TB if iverilog complains "identifier not found".
- **Wrong reset polarity**. Some projects use `rst_n` (active-low), others `rst` (active-high).
- **Missing parameters**. If the spec says `FILTER_LEN = 4`, declare it as a parameter, don't hardcode.
- **Combinational vs registered outputs**. If the TB samples `@(posedge clk)` on your output, it must be registered.
- **Inferring latches**. Every combinational `always @*` must assign every output in every branch, or declare defaults at the top.

## Critical rules

- **NEVER** modify unrelated reference RTL or visible verification files unless the task explicitly asks you to create or extend them.
- **NEVER** skip the visible spec/interface review. You will write the wrong ports otherwise.
- **DO** write to the exact path the prompt specifies (e.g., `/code/rtl/<requested_module>.v` — not a guessed alternate directory).
- **DO** respect the existing naming style of neighbor modules (snake_case, uppercase parameters, etc.).
