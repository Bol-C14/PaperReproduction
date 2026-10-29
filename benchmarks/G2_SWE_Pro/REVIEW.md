# SWE-Bench Pro: paper review and independent public V2 audit

Status: **metadata_audit + partial reference_calibration** (2026-10-28). Three of four preselected public V2 tasks have usable controls; one is resource_blocked. The explicitly amended three-case conditional control study is also complete. No live agent, model API call, private-set evaluation, or full-paper reproduction was performed.

## Identity, venue, and contribution

The paper is [arXiv:2509.16941v2](https://arxiv.org/html/2509.16941v2), revised 2025-11-14. It is a benchmark/dataset and empirical agent-evaluation paper, rather than a new repair algorithm. A peer-reviewed venue has not been independently confirmed. CCF is **unknown**: no dated official CCF list was verified, and a conference must not be inferred from the topic.

Its contribution combines harder repository-level tasks, copyleft/public and private/commercial sourcing, human clarification of expected behavior/interfaces, validated environments and fail-to-pass/pass-to-pass tests, and failure-mode analysis. The current [public V2 release](https://github.com/scaleapi/SWE-bench_Pro-os/tree/66f92766bba642462d4bbe5479e83f91f9211862/v2) is a later protocol and data repair, not the paper's original public evaluation.

## Claims and strength of evidence

| Claim or mechanism | Evidence inspected | Assessment and limits |
|---|---|---|
| More realistic, difficult repository repairs | Paper §§3–4; reference-patch size/file statistics; sampled task specifications | Larger patches and diverse products support a useful increase in task complexity. Patch size is a proxy: this audit contains no independent engineer-time study or task-difficulty measurement. |
| Human augmentation reduces ambiguity | Paper §6.2 and Table 3; explicit selected interfaces and requirements | The reported improvement mixes improved specification with tighter alignment to the existing verifier. It does not establish that every rejected alternative is wrong or that all requirements are sufficiently tested. |
| Copyleft/private sourcing resists contamination | Paper sourcing argument and private/public partition | Private access changes exposure, but license labels alone do not establish whether any model saw public code. No model-training audit or contamination measurement was performed here. |
| Test-based resolvability | Original curation description; V2 release gate; independent local reference/empty controls | The local controls validate only three selected tasks in a Podman port. Reference acceptance plus empty rejection is necessary calibration, not proof of general verifier soundness. |
| Locked V2 grading reduces agent tampering | task.toml; patch_replay.py; locked agent capture; reset logic in unchanged test.sh | Separate pristine grading is materially stronger than trusting the agent sandbox. Diff capture and phase-specific networking still need end-to-end scaffold validation for a live pilot. |
| Reported model scores measure long-horizon coding | Paper §§5–6, appendices A–C | Scores depend on prompt, scaffold, turn/cost budget and evaluation revision. No model ranking was reproduced. |

The v2 paper's main public table and its budget-limited appendix use different result regimes. The conclusion retains an older approximately 23% characterization, while the main table reports a higher leading score. These should be cited with their table and budget context, not combined into a single headline. The failure-mode narrative also needs care: reported prose and the table's submitted/non-submitted breakdown do not consistently share a denominator. Its GPT-5 judge categorization is diagnostic evidence, not an independently verified causal explanation of failure.

## Prior-work overlap

Issue-to-patch evaluation, repository context and regression tests already underlie SWE-bench. Human test/specification repair overlaps SWE-bench Verified; multilingual breadth overlaps Multi-SWE-bench. SWE-agent supplies the scaffold and interface machinery. The distinctive contribution is the particular sourcing/curation, complexity distribution and augmented corpus, rather than inventing issue resolution, containers or pass@1. The current V2 clean-sandbox regrade is a useful evaluator hardening step, but should be attributed to the later release. These comparisons use the primary works discussed in paper §2 and do not claim an exhaustive novelty search.

## Independently checked V1/V2 changes

Both official Parquet tables are pinned to HF revision `2d52cb3df914a3fcf80c7f66738b3a88ae37fc50`. DuckDB 1.4.4 reads all 731 V1 and 642 V2 rows, with unique, non-null IDs. All 642 V2 IDs occur in V1, 89 V1 IDs disappear, and no matched base commit changes. No task substitution was made.

Matched raw payload comparisons find 38 changed reference patches and 214 changed test patches, agreeing with the release's corresponding counts. Raw problem text differs for 547 matched IDs; whitespace-normalized text differs for 510. This does **not** independently reproduce the README's 529 rewritten-problem-statement count: editorial rewrites and byte/whitespace differences are different measures, and a per-task editorial ledger is absent. Requirements/interface payloads and F2P/P2P lists also change; exact counts and selected-task identities are in `metadata_audit.json`. Test-list normalization reduces the apparent raw F2P changes from 635 to 176; raw string changes must not be described as 635 semantic test changes.

All 6,436 entries in upstream V2 SHA256SUMS verify. For every V2 task, the HF gold and test patch bytes exactly equal the independently checked repository files, and parsed F2P/P2P lists agree. This cross-source check resolved the reader issue without dropping records: PyArrow 19.0.0 failed with a repetition-level histogram error, while installed DuckDB 1.4.4 successfully read and validated both tables.

## Four fixed tasks and specification alignment

Full IDs and per-file hashes are in `selected_ids.txt` and `metadata_audit.json`. Selection preceded test outcomes: lexicographically first two IDs from each of two Python repositories, chosen to avoid Go module-download variability. This is a manageable convenience sample, not a random or representative subset.

| Alias (fix-ID prefix) | Specification/test inspection | What the audit can conclude |
|---|---|---|
| qutebrowser `01d1d149` | Version-cache invalidation and version lines; blocklist notifications. F2P covers three mocked-version cases, P2P includes notification checks. | Reference passes 49/49 required tests; empty passes only 46 P2P cases. New-interface wording says none despite naming `_reset_cache` in requirements; the name is nevertheless specified. Behavior beyond required tests remains unproven. |
| qutebrowser `0833b5f6` | Requirement targets WebKit errorOccurred emission. Reference also touches download/IPC signal compatibility, while selected tests focus on networkreply. | Reference passes 10/10, empty only 9 P2P cases. Acceptance would not establish coverage of every extra reference change. |
| Open Library `00bec1e7` | Complete/differentiable validation, exact strong-identifier set, exception priority, named models. Test patch adds isolated ISBN-10/LCCN acceptance cases. | Static alignment supports the stated cases; enforcement of every prose clause and valid-alternative acceptance have not been demonstrated. Exact image import fails on out-of-range UID/GID. |
| Open Library `03095f26` | Old/new nested key difference and top-level output for save/save_many. Tests simulate edition moves. | Reference passes 3/3, empty only 1 P2P case. No real Solr integration verification. |

## Isolation and limits

The official V2 protocol makes the agent offline, retains setup/verifier networking, captures a diff, and regrades it in a fresh sandbox. The local experiment substitutes rootless Podman 5.6.0/crun 1.27 for Harbor 0.22/Modal and leaves the upstream verifier unchanged. Each diff enters a fresh digest-pinned image; no live agent exists. The original default image user remains namespace uid 0 under unprivileged rootless Podman. No privileged mode or host networking/security change was used.

Repaired local probes confirm CPU affinity 0–3 inside every grading workload. The fixing object is absent, only the base main ref is listed, no reflog/stash/unreachable commits are reported, and `/solution` and `/tests` are absent before grader material is copied. A TCP connection to an external numeric address returns ENETUNREACH under `--network none`. This is bounded evidence for the three successfully imported images, not proof about all 642 images, DNS, every endpoint, or Harbor endpoint allowlisting. Hidden/reference material remains private and outside any future agent mount. A unique project-specific writable verifier output directory is the only host bind mount.

Eight original CPU-controller startup failures and eight subsequent log-directory failures remain in `attempts.json` and private raw logs. Host affinity did not propagate in the second batch; that batch is excluded from calibrated results. No infrastructure failure is counted as a model failure. The original gate deferred further controls until all four baseline pairs completed. An explicit subsequent amendment authorized only six frozen controls on the three native cases; `CONDITIONAL_STUDY.json` preserves that change and its reason. Earlier partial/alternative attempts were unusable logging failures, not successful experiments.

The initial two-image download request was denied before execution. Direct user approval at 2026-10-28 23:46:02 resolved that authorization blocker, and the bounded retry was accepted. Open Library `03095f26` imported and calibrated successfully. The exact `00bec1e7` image could not unpack: `/app/node_modules/hpack.js/.npmignore` requests UID/GID `120012366`, while existing rootless mappings cover namespace IDs 0–65536. No host mapping, privilege, image ownership or security setting was changed. This is an infrastructure incompatibility, not a failed solution. One native baseline pair therefore remains resource_blocked. All earlier failures, including superseded cap-blocked records, remain visible.

Eight gold-derived reviewer controls were application-checked and frozen before grading. Six were then evaluated under the explicit three-case conditional amendment: partials pass 46/49, 9/10 and 1/3 required tests (all rejected); alternatives pass 49/49, 10/10 and 3/3 (all accepted). The blocked fourth case's two candidates remain **not_run**. No candidate changed after outcomes. Independent probes of actual patched AST nodes support specific behavioral differences, with explicit fake-import/Qt limitations; see `SEMANTIC_REVIEW.md`. These are reviewer calibration controls, not blind implementations or agent results.

Open Library `03095f26` exposes a particular specification/coverage gap: the reference `find_keys` unconditionally emits non-string key values. Its AST is identical to the partial candidate's `find_keys`; the isolated actual-function probe emitted integer/null values that the prose excludes. The alternative guards strings, passes that probe and all three required native tests. The native reference's 3/3 acceptance does not settle this prose clause. `semantic_alignment.json` records the bounded evidence. The Open Library history probe also reports zero-padded-filemode warnings; no unreachable commit was reported.

The audit establishes metadata consistency, three local reference/empty discrimination pairs, and six conditional controls on those same three cases. The fixed cohort denominator remains four, with the fourth infrastructure failure visible. There is no full-cohort correctness estimate, public/private full-paper result, agent success rate, or claim that these simple alternatives establish general verifier soundness.
