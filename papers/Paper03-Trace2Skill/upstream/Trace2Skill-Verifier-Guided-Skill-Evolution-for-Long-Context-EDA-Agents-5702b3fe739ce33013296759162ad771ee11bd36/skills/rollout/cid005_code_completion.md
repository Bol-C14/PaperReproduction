# RTL Agent Skill — cid005: Code Completion / Module Integration

## What this task asks of you

You are either:

**(a) Integrating existing submodules** — given several finished modules (`decoder.v`, `fifo.v`, `arbiter.v`, etc.), write the top-level module that instantiates and connects them correctly. The spec defines ports and behavior of the top-level; the submodules are off-the-shelf.

**(b) Completing a mostly-finished module** — most of the logic is present; some cases, assignments, or branches are missing or incorrect and must be filled in.

In both cases, correctness of your completion is defined by the task spec and an external verifier. Use visible `.v`/`.sv` testbenches when they are naturally present, but do not invent or rely on hidden verifier details.

## Strategy

### Phase 1 — understand the building blocks

1. `ls` the target directory. Identify the submodules (by name match with the prompt).
2. `cat` EVERY submodule the top must instantiate. For each, note:
   - Module name (exact case)
   - Full port list with widths and directions
   - Any parameters you may need to override
   - Reset polarity (some might be `rst_n`, others `rst`)
3. If spec docs exist under `docs/`, cat the relevant `.md` file. Pay particular attention to block diagrams and port mapping tables.

### Phase 2 — plan the wiring

Build a mental (or commented) map of how submodule outputs feed other submodules' inputs:

```
// upstream_valid/data -> parser.valid/data
// parser.payload      -> fifo.wr_data
// fifo.rd_data        -> downstream_interface
// clk, rst_n → everyone
```

Identify:
- Signals the top must declare as internal `wire`/`reg`.
- Signals that directly map from top-level ports to submodule ports (passthrough).
- Any glue logic (pipeline registers, clock domain crossings, simple muxes).

### CID-specific guidance: integration and completion checkpoints

This CID rewards accurate use of existing building blocks. Your main risk is inventing glue signals, changing a provided submodule, or treating a multi-file integration problem as a single isolated compile.

1. Inspect every submodule declaration you instantiate. Use the real module names, real port names, real widths, and real parameter names from local RTL.
2. Keep the requested top-level module name and interface exactly as specified. Do not wrap it in a convenience module or rename it to match an internal component.
3. Use named port connections for every instance. If a port is intentionally unused, tie it to a declared dummy net or safe constant in a way that matches its direction.
4. Complete missing branches or assignments in place when the skeleton already exists. Do not rewrite finished submodules just to make the integration easier.
5. Compile with all required RTL dependencies, not just the file you edited. If `module X not found` appears, add the source file that defines `X` rather than deleting the instance.
6. Read Python/cocotb tests for expected behavior if visible, but pass only `.v`/`.sv` sources to `iverilog`.

### Phase 3 — implement the top (one echo)

Structure:

```verilog
module <top_name> (
    input  wire clk,
    input  wire rst_n,
    // ... top-level ports from the spec ...
);
    // internal signals (prefix consistently, e.g. `w_` for wire, `r_` for reg)
    wire        w_rx_valid;
    wire [7:0]  w_rx_byte;
    // ...

    // submodule 1
    sie u_sie (
        .clk(clk),
        .rst_n(rst_n),
        .rx_byte(w_rx_byte),
        .rx_valid(w_rx_valid),
        // ... all ports, by name (never positional)
    );

    // submodule 2
    // ...

    // glue logic
endmodule
```

**Always connect submodule ports by name (`.port(signal)`), never by position.** Positional wiring silently mis-wires when a module's port order changes.

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 <your_top> <all_submodule_files> <testbench>")
vvp(filename="sim.vvp")
```

If compile fails with "module X not found", add the submodule's file to the iverilog command line.
If compile fails with "port width mismatch", you're wiring wrong widths — re-cat the submodule port list.
If simulation FAILs: the first failing assertion names which submodule's output is wrong — trace backward.

## Common pitfalls for this task type

- **Positional port connections**. Always use `.port(signal)` named style.
- **Width mismatches**. A 4-bit address bus connected to an 8-bit port is a compile error at best, silent bug at worst.
- **Forgetting clock/reset on every submodule**. Every submodule needs `clk` and `rst` connected explicitly.
- **Missing parameter overrides**. If submodule `fifo` has `DEPTH = 16` but your design needs `DEPTH = 64`, use `fifo #(.DEPTH(64)) u_fifo(...);`.
- **Inferring latches in glue logic**. Combinational always blocks must assign every output in every branch.
- **Wrong instance names**. The TB may `dut.u_sie.internal_signal` for debug peeks — use conventional instance names like `u_sie`, `u_fifo_in`.
- **Integration order**. If submodule A feeds B feeds C, and you mis-order wires, you'll get unconnected warnings that hide real bugs.

## Critical rules

- **NEVER** modify the submodules themselves — they're given. If a submodule has a bug, that's not your problem (or your task).
- **NEVER** skip the cat of a submodule's port list. Guessing port names is a guaranteed FAIL.
- **DO** write to the exact file path the prompt specifies (e.g., `/code/<requested_dir>/<requested_top>.v`).
- **DO** include every submodule's file path in your `iverilog` command line, or the compile will fail with "unresolved module reference".
