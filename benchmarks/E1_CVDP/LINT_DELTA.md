# Frozen-task lint delta after independent-audit baseline ea499155

No new sample, solution repair, model call or reference transfer. The prior raw/results.json and initial 26 infrastructure-failure records remain unchanged. Host-path-bearing derivatives elsewhere are separately sanitized for the publication candidate. This delta adds only the missing original lint service for no-op and invalid candidates of cvdp_copilot_cont_adder_0042.

Official Verilator tag v5.038, commit f037ac50b419f675ea23fa38abfc363505d7b43a, compiled nonprivileged with four make jobs (GCC 11.5.0, flex 2.6.4, bison 3.7.4, autoconf 2.69). Version verifies `Verilator 5.038 2025-07-08 rev v5.038`; binary SHA256 f86a7498e8e84d5b50a5d2e6c0596a46419c7c8fe52ce7a1e3923547c1b4d08c. Source Git data about 36 MB; private install 115 MB; total CVDP tools footprint around 2 GB includes build objects, not downloaded assets. Additional downloads remain far below original 2 GB allowance; setup took minutes, no paid resources.

Full make compiled binaries but returned error because help2man was missing for manpage generation. Used upstream-supported `make installbin installdata installredirect` to install runtime without manpages. The executable then revealed missing standard Perl FindBin. System Perl is 5.32.1; matching official Perl v5.32.1 source at df9d952d734ef94233ed84af97ca318d7972eed0 supplied dist/FindBin/lib/FindBin.pm (SHA256 1e3a2b0e07f61fa1c4cc98590e6855154f1b44f76a73478fd97fbc7fa8de924c) via a private read-only PERL5LIB mount. Initial lib/FindBin.pm URL returned 404; official tree lookup corrected it. No host security settings or system Perl changed. Verilator licensing: LGPL-3.0-only OR Artistic-2.0; no binaries distributed in this commit.

The original evaluator src/lint.py, original waiver file and candidate bytes are retained. Its exact command, with no weakened warnings or additional waiver:

```
verilator --lint-only -Wall -Wno-EOFNEWLINE /src/lint_config.vlt $VERILOG_SOURCES > lint_results.log 2>&1
```

VERILOG_SOURCES=/code/rtl/cont_adder.sv. Original working directory /src/rundir and pytest /src/lint.py -s -v preserved; only XML/cache output arguments added. Bubblewrap mounts candidate and harness read-only, dedicated result directory over /src/rundir, plus dedicated tool/Perl runtime. No agent, HOME, credentials, network or history exposure. Same time/memory/thread bounds apply.

Observed two pytest test_lint failures with actual Verilator diagnostics, not launch failures:

- No-op: WIDTHEXPAND, WIDTHTRUNC, UNUSEDPARAM; original warning policy rejects. Its four earlier simulation tests still pass. Combined no-op task result is **FAIL**.
- Invalid: deliberate malformed RTL produces syntax error. Combined invalid task result is **FAIL**.

**UNKNOWN boundary:** official reference is withheld, and no independently validated lint-clean positive implementation was supplied. Thus this proves the original service rejects these controls; it does not prove positive-reference acceptance or reproduce a model score. Other six missing-reference limitations and commercial-tool blockers remain. Prior evaluator false-acceptance evidence is unchanged.

Private raw delta archive: evidence-private/lint-evidence.tar.gz, SHA256 77cfd7acf06b9b6721c812ad3cfdcaf45f9e3dc66e61959fc9ded2c7b9704366. It contains original evaluator/waiver files, candidate, pytest XML, full stdout and lint diagnostics. Committed raw/lint_results.json contains only outcome metadata/diagnostic classes; raw/lint_evidence_inventory.json pins every private file. Private build logs are under evidence-private/april-setup-logs/verilator-*.log. No sample, source snippet, reference or private launcher is committed. Parent must review this incremental change at its new head.
