# CVDP Agentic Heavy — RTL Engineering Guide

Read this file before writing any code.

## Common Mistakes to Avoid

These cause the majority of failures. Do NOT do any of these:

1. **DO NOT guess file paths.** Use `ls` to discover where files are. Projects have different layouts — `hardware/src/`, `src/`, `rtl/` — never assume.
2. **DO NOT stop after iverilog.** iverilog only compiles. You MUST run `vvp` to see if your fix actually works.
3. **DO NOT give text-only answers.** The final verifier only checks files on disk. Use `echo` or `edit` to write your fix.
4. **DO NOT include Python/cocotb/pytest files in iverilog.** `iverilog` accepts Verilog/SystemVerilog sources only; visible `.py` tests are not simulator inputs.
5. **DO NOT use SystemVerilog port syntax with iverilog.** `input logic [7:0] data` will fail. Use `input [7:0] data` or declare ports as `logic` inside the module body.
6. **DO NOT use `typedef enum` with iverilog.** It causes explicit cast errors. Use `localparam` instead (see patterns below).
7. **DO NOT write partial files.** `echo` overwrites the entire file. Always write the complete file content.
8. **DO NOT spend more than 5 turns just reading.** Start writing your fix by turn 6-8.

## Step 0: Classify the Task

Identify the task type from the instruction before doing anything:

- **Bug Fix (CD)**: Existing RTL with described failures. Instruction says "fix", "debug", "incorrect output". Strategy: make the minimal targeted fix. Do NOT rewrite working sections.
- **Code Modification (CM)**: Complete RTL, instruction says "modify", "add feature", "change behavior". Strategy: preserve the existing module interface — the testbench expects it unchanged.
- **Code Completion (CC)**: RTL with blank sections (TODO, BLANK, "Insert code here"). Strategy: fill in the minimum code. Do NOT change the module interface.
- **Spec-to-RTL / Testbench Gen (S2R)**: No RTL provided, or you must write a testbench from a spec. Strategy: read ALL docs before writing. List every expected output file.

## Coding Conventions

These prevent the most common compile-time and simulation errors in LLM-generated Verilog.

1. Use `logic` for all ports and signals. Never use `wire` or `reg`. But in port declarations, use plain types: `input [7:0] data` not `input logic [7:0] data` (iverilog rejects the latter).
2. FSM states: use `localparam` + `logic [N:0]`, NOT `typedef enum`. iverilog generates explicit-cast errors with typedef enum — this is the #1 FSM compile failure.
3. Combinational: `always @(*)`. Sequential: `always @(posedge clk)`. Never write explicit sensitivity lists.
4. Non-blocking `<=` in sequential blocks. Blocking `=` in combinational. Never mix in the same block.
5. All sized constants must have size > 0. `0'b0` is invalid; use `1'b0`. Binary literals: only 0 and 1.
6. Assign all outputs before every `case` statement to prevent latch inference.
7. Every `if` needs an `else`. Every `case` needs a `default`.
8. Initialize registers without reset: `logic [7:0] q = '0;` — uninitialized logic is `x` and testbenches using `===` flag `x` as a mismatch.
9. Always include `endmodule`.

## Common Pitfalls

Ranked by frequency in LLM-generated Verilog (~70% functional, ~30% compile-time):

**Functional errors:**
- **Off-by-one cycle timing**: Check whether outputs should be registered (one-cycle delay) or combinational (same-cycle). This is the hardest error to catch without simulation.
- **FSM errors**: Missing state transitions, wrong output per state. Use default assignments before the case statement so all outputs have a value in every state.
- **Counter off-by-one**: A counter from 0 to N-1 needs `count == N-1`, not `count == N`.
- **Bit-width mismatches**: Use explicit sizing and concatenation (`{4'b0, data}`) rather than relying on implicit zero-extension.
- **Reset polarity mismatch**: active-high `rst` uses `if (rst)`. Active-low `rst_n` uses `if (!rst_n)`. Wrong polarity means reset never fires. For async reset: `always @(posedge clk or posedge rst)`.
- **Accumulator-clock divider coupling**: Keep pulse and accumulator in separate statements — never `{pulse, accum} <= accum + inc`.

**Compile-time errors:**
- `typedef enum` + iverilog = explicit cast error → use `localparam`.
- Uninitialized `logic` → `x` triggers `===` mismatches.
- Missing `endmodule`, truncated case statements.
- Hallucinated signals: referencing `clk` or `rst` that don't exist in the port list.

## CRITICAL: After iverilog, ALWAYS vvp

iverilog only compiles — it does NOT run your design. You MUST call vvp after every successful iverilog. The sequence is always:
1. `iverilog(args="-o sim.vvp -g2012 ...")` — compile
2. `vvp(filename="sim.vvp")` — run and see test results

If you compile but never run, you have no idea whether your fix is correct. Never stop at compilation.

## Interpreting Test Failures

When `vvp` shows failures:

- **Mismatch at cycle N on signal `foo`**: Trace your FSM/datapath at that specific cycle. Check if `foo` is registered vs combinational, whether reset initializes it, whether the transition fires one cycle early or late.
- **All tests fail at cycle 0**: Reset is not clearing outputs to their initial state. Check every output has a reset assignment.
- **One test fails, rest pass**: An edge case — look for off-by-one or missing state transition at the specific input pattern shown.
- **Compilation error**: Read the error message — it tells you the file, line, and what's wrong. Fix and recompile.
- **No output / hang**: Infinite loop in simulation. Check for combinational feedback loops or missing `default` in case statements (latch inference).

## Persistence

Do NOT give up while `vvp` is producing actionable failures (signal mismatches, wrong values, assertion errors). These are fixable RTL bugs — keep iterating. Only stop the fix loop when local simulation passes or the local simulator environment itself is broken.

Do NOT modify verification/testbench files unless the task explicitly asks you to create or extend them. For RTL-fix tasks, fix YOUR code.

## When Stuck

If you have made several fix attempts with no improvement — STOP. Re-read the original task description and any spec/doc files from the beginning. Wrong assumptions about port names, reset polarity, signal widths, or protocol timing compound silently. The original spec is always authoritative.

If vvp output appears truncated, redirect to a file and read it:
```
iverilog(args="-o sim.vvp -g2012 design.v tb.v")
vvp(filename="sim.vvp > /tmp/out.txt 2>&1")
cat(filename="/tmp/out.txt")
```

## Before Finishing

1. Re-read the original task description — verify your fix addresses every stated requirement.
2. Confirm your files exist: `ls` the directory where you wrote them.
3. Make sure you wrote COMPLETE files — `echo` overwrites, so partial writes destroy the original.

## RTL Patterns

### FSM (Three-Block Style)

```verilog
localparam IDLE    = 2'd0;
localparam STATE_A = 2'd1;
localparam STATE_B = 2'd2;

logic [1:0] state, next_state;

always @(posedge clk) begin
    if (reset) state <= IDLE;
    else       state <= next_state;
end

always @(*) begin
    next_state = state;
    case (state)
        IDLE:    if (start) next_state = STATE_A;
        STATE_A: next_state = STATE_B;
        STATE_B: next_state = IDLE;
        default: next_state = IDLE;
    endcase
end

always @(*) begin
    out = 1'b0;
    case (state)
        STATE_A: out = 1'b1;
        default: out = 1'b0;
    endcase
end
```

### Counter with Synchronous Reset

```verilog
always @(posedge clk) begin
    if (reset)
        count <= '0;
    else if (enable) begin
        if (count == MAX_COUNT - 1) count <= '0;
        else                        count <= count + 1'b1;
    end
end
```

### Edge Detector

```verilog
logic signal_prev;
always @(posedge clk) signal_prev <= signal;

assign posedge_detect = signal & ~signal_prev;
assign negedge_detect = ~signal & signal_prev;
assign anyedge_detect = signal ^ signal_prev;
```

### Shift Register

```verilog
always @(posedge clk) begin
    if (reset)
        shift_reg <= '0;
    else
        shift_reg <= {shift_reg[N-2:0], serial_in};  // left shift (MSB out)
        // For right shift: {serial_in, shift_reg[N-1:1]}
end
```

### Accumulator-Based Clock Divider

Keep accumulator and pulse SEPARATE — never pack them together.

```verilog
logic [WIDTH-1:0] accum;
logic pulse;

always @(posedge clk) begin
    if (reset) accum <= '0;
    else       accum <= accum + INCREMENT;
end

assign pulse = (accum + INCREMENT < accum);  // overflow detection
```

WRONG (do not do this):
```verilog
// Couples pulse and accum — misses the overflow cycle
always @(posedge clk) {pulse, accum} <= accum + inc;
```

### Priority Encoder

```verilog
always @(*) begin
    out = '0;
    casez (in)
        4'b1???: out = 2'd3;
        4'b01??: out = 2'd2;
        4'b001?: out = 2'd1;
        4'b0001: out = 2'd0;
        default: out = 2'd0;
    endcase
end
```

### Multiplexer

```verilog
// Small: ternary
assign out = sel ? in1 : in0;

// Large: case
always @(*) begin
    case (sel)
        2'd0: out = in0;
        2'd1: out = in1;
        2'd2: out = in2;
        2'd3: out = in3;
        default: out = '0;
    endcase
end
```

### Dual-Edge Triggered Logic

iverilog does not support `always @(posedge clk or negedge clk)`. Use two blocks with a mux:

```verilog
logic [N-1:0] q_pos, q_neg;
always @(posedge clk) q_pos <= d;
always @(negedge clk) q_neg <= d;
assign q = clk ? q_pos : q_neg;
```

### Async Reset

For active-high async reset:
```verilog
always @(posedge clk or posedge rst) begin
    if (rst) out <= '0;
    else     out <= next_out;
end
```

For active-low async reset:
```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) out <= '0;
    else        out <= next_out;
end
```

### Self-Test Template

When no testbench is provided, write one using assertions:

```verilog
module tb;
  integer fail = 0;
  logic clk = 0;
  always #5 clk = ~clk;

  // Instantiate DUT with actual port names from the design
  MyModule dut (.*);

  task check(input logic [7:0] got, expected, input string label);
    if (got !== expected) begin
      $display("FAIL %s: got=%0h expected=%0h", label, got, expected);
      fail = fail + 1;
    end
  endtask

  initial begin
    rst = 1; #20; rst = 0;
    // ... drive inputs, check outputs ...
    if (fail == 0) $display("PASS");
    else $display("FAIL: %0d errors", fail);
    $finish;
  end
endmodule
```
