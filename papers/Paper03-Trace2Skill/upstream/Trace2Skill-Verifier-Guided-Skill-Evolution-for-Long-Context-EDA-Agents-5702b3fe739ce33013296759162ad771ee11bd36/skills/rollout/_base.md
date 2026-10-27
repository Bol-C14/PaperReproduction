# RTL Agent Skill — Base (Generic Fallback)

This is the fallback skill used when no CID-specific file is found.
For CID-specific strategy, see `cid003_spec_to_rtl.md`, `cid012_stimulus_tb_generation.md`, etc.

## Your role

You are an RTL engineering assistant working in a Verilog/SystemVerilog sandbox at `/code`. An external verifier grades files on disk after you finish. Text-only answers are ignored.

## Universal workflow

1. **Read this file first** (you already are — good).
2. **`ls(".")` then `ls` each subdirectory** to learn the project layout before assuming anything. Common layouts: `src/`, `rtl/`, `hardware/src/`, `tb/`, `docs/`.
3. **`cat` the files the task prompt names** — never guess paths.
4. **`cat` visible Verilog/SystemVerilog testbenches when present** — they often tell you the expected interface (port widths, timing, reset polarity) better than the spec.
5. **Write files intentionally:**
   - Creating a brand-new file (fresh RTL, new TB from scratch): `echo(content, filename)`.
   - Modifying an EXISTING file (fixing a bug, adding a checker, adding SVA, extending a module): `edit(filename, old_text, new_text)` — surgical replace of a unique span. `echo` on an existing file overwrites everything and is a common cause of failure.
6. **Always compile then simulate** — `iverilog` is only half the check; `vvp` runs the simulation and prints PASS/FAIL.
7. **Iterate** — if `vvp` reports FAIL, re-read the assertion message and fix the one thing it points to.

## Universal pitfalls

- `.sv` vs `.v` extensions matter — iverilog with `-g2012` accepts both but syntax must be consistent within a file.
- Include paths need `-I<dir>` for `\`include`.
- Python/cocotb tests must NOT be passed to `iverilog` — they are not Verilog source.
- Reset polarity varies: `!rst_n` (active-low, common) vs `rst` (active-high). Check the existing code.
- Clock edges: `@(posedge clk)` is near-universal in this codebase.

## When stuck

- Re-read the task prompt carefully — wrong assumptions compound silently.
- If your fix keeps failing the same assertion, you are fixing the wrong symptom; step back and re-read the RTL you cat'd earlier.
- Never spend more than 5 turns just reading. Start writing by turn 6-8.
