# Publication exclusions

- Original/final DCPs, generated full functional HDL/EDIF and XDC: remain in controlled local evidence; omitted from this lightweight public audit. Benchmarks have source/license/hash references; no claim that every omitted artifact is legally restricted is made.
- Private Library ZIPs, materialized deliveries, Library identifiers, upload receipts and user-specific source metadata: not published. The immutable first-pass bundle was not modified.
- Credentials, private environment and SSH configuration: never copied into the publication input. No secret contents/hashes are published.
- Vendor implementation software, full vendor command help, copied upstream validator source, bytecode and duplicate runtime Python files: excluded; official documentation/source links and relevant bounded conclusions retained.
- No other paper, thread worktree or unrelated pre-existing file is changed. RQ3/RQ4 source summaries remain read-only source evidence, and this commit does not publish their entire independent worktrees.

PUBLICATION_MANIFEST.json contains relative important-artifact omission entries; it does not include secret material. Public logs are labeled transformed, not raw-byte originals. Private original hashes are provenance only, and must not be used to authenticate transformed public bytes.
