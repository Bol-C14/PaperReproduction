# RTL Agent Skill — cid004: RTL Refine / Enhance Design

## What this task asks of you

You are **modifying an existing RTL module** to add a feature, support a new interface, or fix an incomplete design. The module already works — your job is to preserve that behavior while extending it. Sometimes the task also requires writing a small testbench snippet to verify the new feature.

Your artifact is a modified version of one (occasionally two) existing RTL files. An external verifier grades your work after you finish.

## Strategy

### Phase 1 — understand what exists (critical)

**`cat` the target file completely before thinking about edits.** This is the most common failure mode — agents echo a rewrite that breaks the original behavior.

1. `ls` the directory the prompt names (e.g., `/code/<project>/<rtl_dir>/`).
2. `cat` the target module top-to-bottom. Note: module name, port list, parameters, internal state, existing always blocks, existing output assignments.
3. `cat` any neighbor / sub-module the target instantiates.
4. `cat` the testbench that exercises it — the TB will drive signals for BOTH the old behavior AND the new feature you're adding.

### Phase 2 — plan the delta (don't code yet)

Map the new feature onto the existing structure:

- Is the new behavior a new FSM state? → add to the state enum and the state-transition always block.
- Is it a new output port? -> add to the port list and any visible RTL instantiation that is part of the requested change. Do not modify verification files unless the task explicitly asks for it.
- Is it a new input control signal? → add to the port list and gate existing logic on it.
- Is it a parallel sub-FSM? → add a new always block, don't tangle with existing ones.

**Keep the original port names, widths, and reset behavior exactly the same.** Existing testbenches rely on them.

### CID-specific guidance: refinement checkpoints

This CID is not asking for a cleaner rewrite. It is asking for a small extension to a design that already has working behavior.

1. Identify the exact before/after behavior from the prompt: what must remain unchanged, and what new behavior must appear.
2. Locate the narrowest existing block that owns the behavior. Add new logic near that owner instead of scattering unrelated edits across the file.
3. Preserve timing. If an output was combinational, do not accidentally register it; if it was registered, do not turn it into a continuous assign.
4. When adding a port or parameter, update only local RTL that must see it. Do not change visible verification files unless the task explicitly asks for that.
5. After each edit, compile the modified RTL with visible dependencies. A compile clean result is useful even before the full verifier runs.

### Phase 3 — apply changes with `edit`, not `echo`

**ALWAYS use `edit(filename, old_text, new_text)` for refinement tasks.** The existing RTL file is already long and well-structured; `echo` overwrites the whole file and you will lose or corrupt unrelated sections when reconstructing from memory.

Use a sequence of narrow `edit` calls:
- `edit` to extend the port list (anchor on the trailing `);` of the existing port declaration).
- `edit` to add the new parameter (anchor on an existing `parameter` line).
- `edit` to add the new always block (anchor on `endmodule` or the last existing always block).
- `edit` to update the reset-branch of an existing always block (anchor on the existing `if (!rst_n)` line).

If `old_text` matches more than once, include more context lines and retry. If you truly need to replace a large contiguous section, prefer multiple small edits over one giant one — it's easier to recover from a mis-anchored small edit than a mis-reproduced large one.

You only need `echo` if the task explicitly asks you to create a new file alongside the modified one.

Preserve:

- The original header comment block (copyright, filename).
- The original port order (append new ports at the end of the list).
- The original reset values of existing signals.
- The original combinational/registered distinction of existing outputs.

Add your extension in a new always block or as additional branches in the existing state machine — never interleave new logic into existing lines unless absolutely necessary.

### Phase 4 — compile, simulate, iterate

```
iverilog(args="-o sim.vvp -g2012 <your_modified_file> <testbench>")
vvp(filename="sim.vvp")
```

The TB will run BOTH the old regression suite AND the new-feature tests. A pass means neither was broken.

## Common pitfalls for this task type

- **Renaming ports**. Even casing changes (`data_in` → `DataIn`) break the instantiating TB.
- **Changing reset polarity or reset value** of existing signals. Keep `rst_n` as `rst_n`.
- **Squashing combinational with sequential**. If `status_out` was `assign status_out = ...;` and you rewrite it as a `reg` in an `always @(posedge clk)` block, you've added one cycle of latency — existing TB checks at cycle N will now fail.
- **Forgetting to declare new `reg`s before using them** in always blocks.
- **Tangling new FSM states with existing ones** such that the existing state transitions now trigger incorrectly.
- **Missing the second target file**. Some refine tasks require changes to both the RTL and a small tb_*.sv addition — check the patch expectations in the prompt carefully.

## Critical rules

- **NEVER** `echo` the whole RTL file just to add a feature — use `edit` for surgical changes. `echo` reconstructs from memory and almost always loses unrelated existing logic.
- **NEVER** rename existing ports, even for style consistency.
- **NEVER** remove or rename parameters that are already in use — extend with new parameters instead.
- **NEVER** change existing always-block sensitivity lists.
- **DO** keep the file's directory path unchanged. Write to the same `/code/<path>` you cat'd.
- **DO** add comments at the boundary of your changes marking what's new and why — helps the reviewer (and future agents) trace behavior.
