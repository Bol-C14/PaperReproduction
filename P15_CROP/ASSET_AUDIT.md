# P15 — CROP asset audit

Audit date: 2026-10-28. Selected PaperReproduction cloud workspace only. Scope: public source and asset metadata; method learning, not bit-exact reproduction. No experiment, inference, installation, model/API invocation, large download, setting change, license acceptance, or publication was performed. Public web reads were used. The companion `assets.json` holds the compact paper-derived algorithm/configuration record and source registry.

## Decision

**Minimum faithful mechanism: inexpensive reconstruction appears feasible, but official implementation availability is unverified. Full paper industrial evaluation: high-cost and access-dependent.** Commercial assets do not prevent studying semantic circuit retrieval. Retrieval alone, however, does not establish an improvement in configuration search: that requires transferable configuration/QoR history and an evaluation oracle.

The requested levels have evidence preconditions: L1–L3 require code; L4–L5 require confirmed no code. Neither condition is established here. Consequently neither route receives an unconditional level. The minimum route has a **provisional L4 cost profile if no code is confirmed**, and the full route a **provisional L5 cost profile if no code is confirmed**. If official code becomes verified, reassess toward L2 for a small public mechanism study or L3 for the industrial route, depending on what the release contains. This avoids converting “not found” into “absent.” Confidence is medium in the minimum-route cost assessment, high in the full-route access dependency, and low in any claim of global code absence.

## What was actually verified

The [lead author's publication page](https://jpan.me/publications/) identifies the ICCAD 2025 paper and links arXiv and IEEE, with no code link in its CROP entry. Its [GitHub link resolves to panjingyu](https://github.com/panjingyu). The profile overview did not establish a CROP repository, and its repository-list page was restricted by the web tool. Searches by exact title and author did not establish another official project. No guessed CROP repository was adopted. These observations establish only the inspected search boundary.

The benchmark link is author-grounded through the [RTLRewriter paper](https://arxiv.org/abs/2409.11414), which explicitly names [yaoxufeng/RTLRewriter-Bench](https://github.com/yaoxufeng/RTLRewriter-Bench). Its public README and root tree show `examples`, `long_benchmark`, and `short_benchmark`; the README describes 55 short cases with original/optimized versions and five long cases. This is a benchmark asset, not a verified CROP implementation or configuration-history archive. A short-benchmark directory read was restricted; a guessed directory README returned 404, which says nothing about the directory's contents. No full tree, individual RTL files, benchmark license, CROP query manifest, or revision pin was verified.

The [official embedding model files](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/main) are publicly listed with Apache-2.0 metadata. One safetensors checkpoint is 90.9 MB; the 977 MB repository total includes alternative formats and exports and is not a necessary single-model download. [Model configuration](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/config.json) specifies six layers and width 384. [Sentence-transformer configuration](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/main/sentence_bert_config.json) sets a 256-token sequence limit. No weights were downloaded or loaded. A future implementation should explicitly record truncation, pooling, normalization, and checkpoint revision rather than assuming an arbitrary embedding call matches the paper.

## Resource and fidelity ledger

| Resource | Current evidence/access | Consequence and permissible future fill |
| --- | --- | --- |
| Official CROP source, README, configuration files | Unverified; no repository established | Cannot inspect actual parser, retry policy, scheduling, dependency versions, or executable configuration. Reconstructing from the paper is implementation work, not running released code. |
| Public RTL benchmark | Repository and root README verified; exact CROP subset unverified | Small public retrieval study is plausible. Selecting a fresh subset loses direct comparability with the paper's query set. |
| Query IDs, labels, split, exclusions, cached summaries/embeddings | Unverified | New documented manifest can support method learning, but not a claim to reproduce the reported retrieval score. Original/rewritten relatives should be tracked. |
| Prompt templates, model snapshots, call/token/cost logs | Unverified as executable artifacts | Reconstructed prompts or substitute models change generated semantics and configuration choices. Named commercial models are not downloadable paper checkpoints. Current access was not tested. |
| Historical configurations and QoR values | No author-linked downloadable archive verified | A retrieval demo can omit them only by narrowing its claim. Faithful search learning needs real history; generating a small public history is additional future work and cost. |
| Complete discrete search schema and flow scripts | Unverified as files; paper examples are not a machine-readable complete configuration | New legal parameter ranges and flow adapters change the optimization landscape. |
| Industrial designs and technology assets | Proprietary description; public release/access not verified | Would need authorized RTL, technology libraries/PDKs, constraints, and evaluation setup. Do not seek or share account data. |
| RTL Architect tool/version/license and runtime | Backend identified; local installation and entitlement not probed | Full industrial route needs authorized access and enough repeated flow evaluations. Runtime percentages cannot determine CPU-hours, RAM, or wall time. |

The low-cost learning route would need a CPU-capable workstation/cloud instance, a small RTL manifest, a summarization provider or deliberately declared substitute, the small embedding checkpoint plus tokenizer/configuration, an inner-product retrieval implementation, and stored summaries/query results. No dedicated training or GPU requirement is established for this route; future LLM access and token cost remain unresolved. Extending it to configuration transfer also needs an authorized cheap oracle, prior-design histories, an option validator, and an iterative search log. No numerical dollar, memory, or elapsed-time estimate is justified by the inspected assets.

An open flow could substitute for the commercial oracle only as an explicitly scoped mechanism port. It changes tool semantics, parameter meanings, process technology, timing/power estimates, and the industrial transfer task. Static structural retrieval, raw-text embeddings, and random retrieval are comparators, not replacements that preserve CROP's semantic summarization mechanism. A smaller/local LLM is a useful possible cost substitution with summary-quality and search-policy fidelity loss. Synthetic objective values would demonstrate wiring, not circuit optimization.

Verified Astro infrastructure may be reused later only as execution/logging infrastructure after checking its available artifacts. No Astro files were established in this selected checkout, and no Astro algorithm or result is evidence for CROP.

## One testable gap and control — proposed only

**Gap:** whether semantic neighbor selection improves downstream configuration transfer beyond receiving any equally informative history. This is a research control, not an allegation about the paper.

For a future small authorized study, compare semantic CROP retrieval, structural-feature retrieval, and seeded random retrieval from the same prior-design pool. Match retrieved-history count, top-configuration count, accessible history/QoR budget, prompt length allowance, model/settings, initial evaluations, total oracle calls, and the rule for showing accumulated target history. Exclude the query itself and track original/rewritten family membership to prevent trivial relatives from silently deciding retrieval. Measure both category retrieval quality and best feasible QoR after an equal budget; enforce the same timing/area constraints rather than power alone. If only retrieval is evaluated, explicitly withhold any claim about optimization improvement. No part of this control was implemented or run.

## Access outcomes and stopping point

The [paper HTML](https://arxiv.org/html/2507.02128v2) was readable through public browsing. A direct cloud-shell GET to that URL returned proxy tunnel **403 Forbidden**; the download was not retried. The [IEEE page](https://ieeexplore.ieee.org/document/11240643/) displayed JavaScript/robot verification; no bypass was attempted. Restricted GitHub reads were stopped. These limit byte-level/source-tree verification; the audit itself is complete with explicit unknowns. No automatic approval rejection occurred, no approval is pending, and no uncertain external mutation exists.

Stop after saving this report and manifest. No experiments are authorized by this audit.
