# Unpublished public payload sanitation

This payload is rebuilt as a single root commit containing only the explicit G3 file whitelist. It does not inherit the previous repository history. The original Git directory, pre-sanitation public files and unchanged private evidence archive are retained under the ignored `.private/sanitization/` and `.private/` directories. No original 2.0 task assets, reference answers, hidden tests or private raw logs belong to the public tree.

Execution-host roots and home directories are represented as `${REPRO_ROOT}` and `${HOST_HOME}`; transient host paths and user-service identifiers use neutral placeholders. Public execution scripts require `REPRO_ROOT`; the affinity driver additionally requires `HOST_HOME_PROBE` for a configured forbidden-mount check. Those parameterized scripts have only been syntax-checked after sanitation, not executed as benchmark trials. Historical commands are redacted transcripts; actual byte-identical originals remain private.

The summary exporter sanitizes public views of private metadata and failures. Numerical values, control outcomes, artifact/source/image/raw-log hashes, resource-comparison CSV bytes and the private raw archive are unchanged. The local history receipt records the new root head, tree whitelist digest, reachable-history inspection and preservation checks.

Interpretation remains limited: child survival was observed in this AffinityPort → Harbor 0.25.0 → Podman/podman-compose chain, not established for original Docker or the paper protocol. Cooperative affinity is not an adversarial CPU quota. The alternative regex passes the upstream fixture and only the 10 independent cases tested, without a universal correctness claim. The EDA package is a template with REQUIRED placeholders, not a runnable production task.

No experiment rerun, API request, push or publication is part of this correction.
