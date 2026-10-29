# Private raw evidence

Archive: `.private/raw-evidence.tar.gz` (Git-ignored, local mode 0600). SHA256: `c97f8b609dd1906ea60254776c062d974a5d12c34a57843f2e3c71204bfea073`; size: 527574 bytes. Extracted under `.private/evidence/` (parent mode 0700).

Remote source root: `${REPRO_ROOT}`.

- `logs/terminal-bench/`: full dependency/build output, each calibration revision's raw log, original/final image inspections, package inventories, isolation scans.
- `results/terminal-bench/`: all 43 trial records: 30 infrastructure/incomplete attempts and 13 final controls. Per-trial `commands.json`, full exceptions, structured verifier output, rewards, artifact hashes and actual reference artifacts are retained wherever produced.
- `assets/terminal-bench/`: pre-result selection, hashes, source HTML snapshots, full modified task ports, exact build recipes, and metadata.
- `tools/terminal-bench/`: historical driver revisions and independent checker.
- `checkouts/terminal-bench/dataset/`: only the three original selected task directories, preserved privately with original references and tests.

The public Git head contains reports, audit scripts, hashes and sanitized summaries. It excludes raw task inputs, reference answers, hidden tests, source snapshots and private raw logs. Never expose this archive, extraction, auditor scripts or result directory to an evaluated agent. Use the EDA agent-bundle allowlist instead.

The complete per-file raw inventory is `.private/raw-inventory.json`. The archive SHA above protects the complete preserved byte stream; no score is inferred from archive existence.
