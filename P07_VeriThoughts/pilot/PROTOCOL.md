# P07 evaluator-contract pilot: frozen protocol v1

Freeze time and commit are recorded in `freeze.json` and Git history before any fixture is compiled, simulated, or formally checked. Setup started 2026-10-28T10:34:01Z; stop setup/diagnosis by 2026-10-28T12:34:01Z. Downloads must remain below 2,000,000,000 bytes. CPU only, no paid services, no credentials, no model/API/training/GPU use and no external push/PR.

## Claim and design

This is a synthetic-control reproduction of the released formal evaluation mechanism. It is not a dataset-wide benchmark or a reproduction of generation/training accuracy. Eight authored controls are fixed in `fixtures.json`; both RTL files have SHA256 digests there. Predictions are fixed before execution. There are no random seeds or stochastic components.

Official source is the exact Git blob `74963ae51ca6360b5b5944b03c266f7f48309b06` from VeriThoughts commit `f44c2af999de62bd27e90e73ce9cbd4f97fbe55c`. An extra newline in the audit text snapshot is removed, and blob identity is checked when preparing its executable copy. No source patch is applied.

Yosys is built from official release 0.41 commit `c1ad37779eea6211866a466026322416fb3a832f`, archive SHA256 `a22b1dd9f23bc829ed9bbb938dde5404c2577dc89f4618d5d1e89999eb3d84e8`. ABC, Tcl, readline, plugins and zlib are omitted from this minimal build; none is used by the tested commands. Icarus and Python/NumPy come from signed Debian packages; installed versions are recorded. Debian base digest and source/compiler flags are pinned in the Dockerfile. This is a newly built minimal toolchain, not proof of the authors' original binary identity.

## Conditions and predictions

| Control | Independently reviewed truth | Predicted original 50-step outcome |
|---|---|---|
| comb_demorgan | NAND equals its De Morgan form for all four inputs | pass |
| comb_mismatch | AND differs from OR for mixed inputs | fail |
| seq_modular | 4-bit +1 equals -15 modulo 16, zero initial state | pass |
| seq_increment | 4-bit +1 differs from +2 at the first rising edge | fail |
| delayed_pulse | 8-bit counter pulse at count 60 differs from constant zero | pass within the bound; eventual non-equivalence |
| empty_discovery | legal no-port golden module, syntactically invalid candidate | pass caused by zero discovered checks |
| helper_inline | XOR helper hierarchy and inlined XOR agree at top interface | fail because required helper is absent |
| syntax_error | recognizable module with an invalid assignment | fail |

All sequential claims use zero initial user state. There is only one clock input and no data/reset inputs; rising edges advance state, other clock behavior stutters. The independent oracle explicitly applies the same zero-initial condition. No parameter sweep, reset-contract inference, undefined-state relaxation or changed initialization is allowed. SAT steps after `clk2fflogic` are not assumed equal to rising edges.

## Original vs port vs novel

1. **Original:** execute the unchanged evaluator inside the container once per fixture. A runpy driver instruments subprocess calls and records streams, return codes and times; it delegates to the original subprocess.run with the same arguments and timeout. One response per case avoids duplication. `pass@1` is meaningful per case; original `pass@5/pass@10` outputs are outside their valid sample count and are explicitly excluded from metrics. No paper pass@k comparison is made.
2. **Faithful port:** preserve upstream module-renaming function verbatim through AST extraction; emit the exact preprocessing, `clk2fflogic`, flattened miter, `sat -seq 50 -verify -prove trigger 0 -show-all -show-inputs -show-outputs -set-init-zero` commands. Invoke the same Yosys binary directly, with the same 150-second subprocess timeout. Preserve raw original all-empty-list semantics in `status`; additionally report a separately named nonempty guard without overwriting raw results. Compare original/port outcomes case by case.
3. **Novel diagnostic:** only for delayed_pulse, increase `-seq 50` to `-seq 160`, holding all other solver assumptions unchanged. This is a changed contract and must never be included as original reproduction success. No iterative horizon tuning is preauthorized within this protocol.

## Independent oracle

Icarus compiles and simulates the authored golden/candidate designs without upstream parsing, renaming or SAT. Combinational fixtures exhaust all four Boolean valuations. For sequential fixtures, simulation checks the initial state plus 260 rising edges against independently written modular transition/output equations; an exhaustive joint-state orbit traversal terminates on repetition (16 or 256 states). These no-data-input deterministic machines have no other reachable state evolution; clock stuttering cannot create a new state. This supports the reviewed finite-state contract for these fixtures only. The first mismatching edge is retained. Oracle/model disagreement is **unknown**, not silently corrected or counted as equivalence. Invalid candidates are classified through independent syntax/elaboration failures, not as behavioral counterexamples.

## Execution, budgets and retention

- Runtime container: no network, nonroot uid/gid 1000, read-only image/source mount, writable experiment directory only, /tmp tmpfs, all capabilities dropped, no-new-privileges, 2 CPUs, 4 GiB memory, equal memory+swap cap (no swap), 128 PIDs. No host security changes or privileged container.
- Source compilation runs in a network-disabled Docker build step after package installation. Build dependencies are official signed Debian packages; no arbitrary binary mirror is used. Build uses two workers. Package download traffic may use the existing infrastructure proxy; no proxy values or credentials enter results.
- Preflight tool-version and container-isolation checks are logged separately and do not count as experimental evidence.
- Each formal attempt: 150 seconds. Original wrapper process: 400 seconds. Oracle compilation/simulation: 20 seconds each. Preserve all failures/timeouts and count outer and nested original attempts separately.
- No fixture replacement, dropped failure, silent retry, training, inference or benchmark-data exploration. If a software defect in the authored harness prevents execution, preserve the failure and record any amendment before rerunning. Distinguish setup failures from experiment attempts.
- Retain fixture files, manifests, exact commands/scripts, complete Yosys/compile/simulation streams, subprocess records, JSON results/metrics, package/source/image provenance, download/resource ledger and concise interpretation. Do not commit binary downloads, images or generated simulator executables.

Acceptance: original and faithful port outcomes agree on all eight controls, independent oracle/model agreement holds for all valid designs, invalid candidates are identified, and any differences between formal labels and behavioral truth are explained by the documented contract. A failed prediction is retained as a result. No result supports global dataset error rates or unbounded equivalence.
