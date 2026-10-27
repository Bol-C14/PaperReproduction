# RTL Agent Skill — cid012: Stimulus Testbench Generation

**Note:** despite the official CVDP label "rtl_debugging", the tasks in this bucket
ask you to **write a new testbench from scratch** that generates stimulus vectors
for a given DUT (design under test). Read the task prompt carefully to confirm,
but expect to be producing a `tb_*.sv` file, not debugging RTL.

## What this task asks of you

Given a working DUT (provided in the context), write a SystemVerilog testbench that:

1. Instantiates the DUT (by the instance name the task specifies, usually `dut`).
2. Generates a clock and reset sequence.
3. Applies a sequence of input stimulus vectors aimed at maximizing functional coverage (reset, boundary values, back-to-back transactions, corner cases).
4. Optionally dumps waves for debug.

An external verifier compiles your TB together with the DUT and checks coverage / assertions.

## Strategy

### Phase 1 — study the DUT (non-negotiable)

1. `ls` the RTL directory the task names.
2. `cat` the DUT Verilog file — note every port (name, width, direction) and every parameter.
3. `cat` the spec doc in `docs/` if present — it describes the DUT's behavior under each input combination, which is exactly what your stimulus must exercise.
4. Identify:
   - Clock signal name(s) (often multiple for async FIFOs).
   - Reset polarity and reset value.
   - Any handshake signals (valid/ready, req/ack).
   - Data widths and protocol (e.g., AHB, AXI, custom streaming).

### Phase 2 — plan stimulus coverage

Enumerate test vectors by category:

- **Reset behavior**: assert reset high (or low), then de-assert; confirm outputs settle to spec values.
- **Basic functionality**: one or two canonical inputs, predictable outputs.
- **Back-to-back transactions**: new valid input on consecutive cycles.
- **Back-pressure**: downstream ready deasserted while upstream valid is high.
- **Boundary values**: min (0), max (2^N - 1), just-under-max, just-over-zero.
- **Simultaneous events**: reset mid-transaction, rapid mode switching.

### CID-specific guidance: stimulus-generation checkpoints

This CID rewards a focused, deterministic testbench that exercises the DUT broadly without trying to recreate an entire production verification environment.

1. Create the exact file and module the prompt requests. If the prompt names the DUT instance, use that name exactly, usually `dut`.
2. Copy the DUT port list from local RTL. Do not assume a standard bus interface if the project uses custom names or polarity.
3. Use task names and localparams that are unique to your bench so you do not collide with helpers, macros, or descriptors in included files.
4. Every wait must be bounded. Wrap handshakes, FIFO waits, protocol waits, and reset waits with a timeout counter so `vvp` reaches `$finish`.
5. Prefer compact deterministic stimulus with clear `$display` checkpoints over a large protocol-perfect model. The goal is broad, compiling coverage that finishes.
6. Add `$dumpfile`/`$dumpvars` and a final summary message. If the run fails, the next agent needs enough trace to see which stimulus phase caused the issue.

### Phase 3 — write the TB (one echo)

Structure:

```systemverilog
`timescale 1ns/1ps

module tb_<dut_name>;
    // Parameters matching the DUT
    localparam int CLK_PERIOD = 10;

    // DUT signals
    logic        clk;
    logic        rst_n;
    // ... every DUT port as a `logic` here ...

    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // DUT instantiation — use the exact name the task says (usually `dut`)
    <dut_name> #(/* parameter overrides if any */) dut (
        .clk(clk),
        .rst_n(rst_n),
        // ... by-name connections for every DUT port ...
    );

    // Stimulus
    initial begin
        // Reset
        rst_n = 0;
        repeat (4) @(posedge clk);
        rst_n = 1;

        // Test vectors
        apply_basic();
        apply_back_to_back();
        apply_backpressure();
        apply_boundary();

        $display("ALL TESTS COMPLETE");
        $finish;
    end

    // Waveform dump (optional but usually expected)
    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, tb_<dut_name>);
    end

    // Per-test tasks
    task apply_basic;
        begin /* ... */ end
    endtask
    // ...
endmodule
```

### Phase 4 — compile + run

```
iverilog(args="-o sim.vvp -g2012 tb/<your_tb>.sv src/<dut>.v src/<submodule>.v ...")
vvp(filename="sim.vvp")
```

Iverilog with `-g2012` supports most SystemVerilog testbench constructs (tasks, `logic`, `localparam`, some SVA). For advanced coverage (`covergroup`, some assertion patterns), you may need `-g2012` with caveats — cross-check your TB doesn't use unsupported features.

## Common pitfalls for this task type

- **Instance name mismatch**. Coverage/checker logic often expects `dut.internal_signal`; if you name the instance `u_dut` when the task says `dut`, coverage hits will be zero.
- **Wrong clock/reset polarity**. Cat the DUT first to see if reset is `rst` (active-high) or `rst_n` (active-low).
- **No `$finish`**. Without it, vvp runs forever and times out.
- **No `$dumpfile/$dumpvars`**. Some coverage tools rely on the VCD dump — add them even if unused.
- **Missing parameter overrides**. If the DUT has `parameter WIDTH = 8` and the task mentions testing WIDTH = 16, instantiate with `dut #(.WIDTH(16))`.
- **Hanging stimulus**. If the DUT has back-pressure, your `@(posedge clk)` delays must respect `ready` before advancing the next input.

## Critical rules

- **NEVER** modify the DUT or any file under `src/` or `rtl/` — your output is the testbench, nothing else.
- **NEVER** instantiate the DUT by anything other than the name the prompt specifies (usually `dut`).
- **NEVER** skip `$finish` — an unterminated simulation is counted as FAIL.
- **DO** write to the exact `/code/tb/<file>.sv` path the prompt specifies.
- **DO** include `$dumpfile`/`$dumpvars` for debuggability even if not strictly required.
