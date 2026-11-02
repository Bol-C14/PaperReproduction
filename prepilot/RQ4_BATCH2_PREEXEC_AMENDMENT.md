# Batch 2 pre-execution amendment

Installed Vivado 2025.1 help was captured on APRIL at 11:45:03–11:45:06 UTC, before ANY Batch 2 candidate started. It explicitly says `-no_psir` disables router physical synthesis, including interconnect retiming and LUT restructure. It also documents restrictions on combining `-directive` with specific routing options, leaving a directive-plus-no_psir combination insufficiently established.

Therefore replace the two staged directive candidates, before outcomes, with exactly:

- RouteNoPSIR: `route_design -no_psir`.
- RouteNoPSIRTNS: `route_design -no_psir -tns_cleanup`.

Both start from the same hashed RQ1 no-op checkpoint, independently. TNS cleanup adds a documented route-stage effort focused on failing paths; no phys_opt, unroute, new logic edit, placement pass, reset of original state or future constraint. Installed help supports both switches; actual combined-command acceptance is still an execution gate. Any failure remains a failure, with no substitution. Reject any retained logical difference even with no_psir. This is a bounded route-only attempt, not proof of functional preservation.

Primary 0.020 ns tolerance, secondary gates, timestamp-v1 instrument, 2-thread limit, 300s hard ceiling per candidate and 960s total ceiling remain unchanged. No future-target evaluation is authorized. Initial help probe completed but failed to print returned help text; corrected read-only probe completed and printed it. Both probes count as cost; neither opened a design.

Candidate output folder/path IDs and actual commands supersede the earlier Default/RuntimeOptimized shell example. No candidate from that earlier example was executed. This pre-outcome amendment follows the parent's PSIR audit steering, not observed candidate performance.
