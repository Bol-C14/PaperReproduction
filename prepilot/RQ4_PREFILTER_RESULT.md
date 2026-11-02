# Completed RQ1 artifact prefilter: no admissible state pair

No Vivado process, state construction or future evaluation was run. Source RQ1 summary states `running_jobs=false`; each included arm has exit code 0 and `tool_complete`. Copied 28 completed files into this worktree's gitignored `prepilot/rq1_snapshot/`. SHA256, size and nanosecond mtime were checked before/after the entire copy set; all source and copied hashes agreed. Source files were not modified. Detailed manifest: `RQ4_RQ1_SCREEN.json`.

## Current-only matching result

| Pair | Relevant current evidence | Decision under frozen gate |
|---|---|---|
| serialized original vs no-op reroute | WNS -1.654 vs -0.885 ns, delta 0.769 ns | Reject: WNS far outside 0.020 ns tolerance |
| no-op reroute vs Default | WNS -0.885 vs -0.862 ns, delta 0.023 ns; TNS delta 3.248 ns (~0.51%); failing endpoints 1897 vs 1914 (~0.89%) | Reject: WNS exceeds fixed tolerance; Default also changes logical representation |
| no-op vs no-op confirmation | Same WNS/TNS/hold metrics, same generating path repeated | Reject as distinct-path pair: technical repeat, not an independently generated different-path state |

No pair survives the necessary conditions; resource matching/other features cannot rescue it. RQ1's actual local LUT proof for Default is explicitly conditional two-state Boolean evidence, not the strict unchanged-representation condition or full sequential/XZ equivalence. It is not used to waive this RQ4 gate. Explore/AggressiveExplore were not run by RQ1. No new candidate fabricated and no tolerance changed.

## Byte equality, decoded EDIF and semantics are different claims

DCP `.edf` entries here contain Zstandard streams (magic `28 b5 2f fd`), not raw UTF-8 EDIF. The initial exact archive-payload comparison correctly found all six pairwise comparisons unequal; those results concern stored representation, not semantic differences. A lossless diagnostic using already-installed `zstandard 0.23.0` decoded each payload; all decoded EDIF byte comparisons also remained unequal. No whitespace, timestamp or property normalization was applied. See `RQ4_DECODED_EDIF_DIAGNOSTIC.json`.

The entire decoded no-op versus no-op-confirmation text diff is ONLY a `timeStamp` change, retained in `RQ4_NOOP_TEXT_DIFF.txt`. This is direct evidence of a harmless difference that the strict byte gate rejects. Therefore failure of exact bytes is conservative rejection, NOT evidence that function changed. No timestamp removal or semantic-acceptance rule was introduced after observing it. Even a future timestamp-only allowlist would not solve today's separate same-path and current-QoR failures.

For a later version, a predeclared metadata-only normalizer could improve acceptance yield, with explicit positive/negative mutation tests and no claim of general semantic equivalence. It is deliberately not implemented or activated in this frozen attempt.

## Lightweight screening boundary checks actually run

Four unittest cases passed in ~0.002 seconds (`test_exact_screen.py`): identical copy accepted; INIT/cellRef/connected-pin/property-removal byte mutations rejected; a benign whitespace change also rejected; different ZIP container encoding with identical `.edf` payload accepted. These establish exact-comparison and extraction behavior only. They do NOT validate an EDIF parser, prove mutation function, test the RapidWright comparator or establish circuit equivalence. All fixtures were authored scratch data in this worktree/temporary directories; original artifacts untouched.

`screen_rq1_completed.py` is an archive/byte stability prefilter, not an equivalence checker. `inspect_rq4_archives.py` counts lexical tokens and is likewise only a screen. Existing RapidWright selection boundaries from `RQ4_MINIMAL_CHECKER_GATE.md` remain unchanged.

## Outcome and missing evidence

**Stop this candidate batch at the predeclared matching gate.** Accepted RQ4 pairs: zero; H1/H2/H3 future-effect evidence: none. Missing is a completed distinct generating path that satisfies frozen current matching and unchanged-representation requirements (plus native validity and secondary resource/constraint checks). Existing outputs do not provide it. Whether to authorize a separately versioned, metadata-tolerant screen or a new physical-only candidate path is a parent decision after this result, not a silent relaxation. No repeated polling or background job scheduled; waiting for parent allocation.
