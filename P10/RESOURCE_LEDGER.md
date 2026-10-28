# P10 resource ledger — bounded pilot

Start2026-10-28T10:35:15Z; resource inventory10:39:42Z; local commit10:41:49Z (~6m34s through commit). Authorized setup/diagnosis ceiling2h; download ceiling2GB. Linux cloud only, no Mac access. Python3.12.14, Linux6.18.55 x86_64/glibc2.41, five available logical CPUs, total RAM18,007MiB, no swap. Solver runs single process; no extra hardware or GPU was allocated. Capacity was observed, not changed.

| Action | Outcome / resource |
|---|---|
| Inspect repo, preserve other branches, create requested local branch | `reproduction/constraint-aware-rover-tcad2025`; checkout initially reported unborn `work` (no existing commits/listed branch refs); no existing branch history overwritten; origin matches Bol-C14/PaperReproduction. |
| Read official manuscript via web tool | Initial full-text response available. Three subsequent narrow page requests returned405; not retried. |
| Read author thesis via web tool | Equations and chapter mapping readable. |
| Download thesis to local sources | One attempt HTTP403, exit22, no PDF obtained; stopped. |
| Download fixed official Z3 Python distribution via package index | One wheel28,124,043 bytes, z3-solver4.13.3.0, SHA256 in lockfile; no dependency resolution beyond that wheel. |
| Local isolated installation | venv and offline wheel install succeeded; pip cache warning (unwritable home cache) was informational and no permission/security change was made. |
| Attempt1 | 10/10 expected identities; wall0.102933s, CPU0.103438s, max RSS58,192KiB. Verification-linkage limitation later identified; logs retained. |
| Attempt2 canonical | Same ten fixtures, actual replacement ASTs verified; 10/10 expected outcomes. Wall0.156724s, CPU0.157684s, max RSS57,768KiB. |
| Runtime totals | 20 fixture executions / 10 unique fixtures; aggregate measured solver-loop wall0.259656s, CPU0.261122s; peak58,192KiB (~56.8MiB). Includes all attempts. Not total tool/setup CPU. |
| Disk | venv78MiB; wheel cache27MiB; source/log/docs small. Caches ignored by git. |
| Other network | Public HTML/PDF reader requests and small pip metadata; exact reader-transfer bytes unavailable. No large paper/data archive downloaded, no checkpoint download. Measured wheel payload~28.1MB; no evidence of approaching2GB. |

Failure accounting: solver runtime errors0, timeouts0, UNKNOWN0, failed frozen expectations0. Four expected SAT negative controls per attempt are successes at detecting intentionally bad proposals, not hidden errors. Empty guard rejected once per attempt. Source-access failures4 (three405, one403) in this phase; earlier audit403 failures remain recorded separately. One validation-design limitation corrected before final attempt. No denied permission escalation or pending approval.

No commercial tools/licenses, paid resources, LLM/model calls for optimization, credentials, API service, system configuration changes, external push or PR. This assistant authored code; execution only used Python/Z3. Initial install was exact-version pinned; fresh re-runs use the recorded hash-enforcing lockfile. Source hashes appear in both attempt logs.
