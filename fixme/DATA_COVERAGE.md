# Why the current public snapshot is not the full 747-task experiment

The earlier delivery stopped after evaluator controls too early. The original
structural-reproduction task remains open. The 24 controls used only **six unique
upstream input directories**; they were never coverage of 747 designs or 24 model
generations. The present audit expands to every advertised upstream case and
executes every cheap reference-only scoring path without new model calls or a
full EDA sweep.

## Count units and verified evidence

The [AAAI-26 paper](https://ojs.aaai.org/index.php/AAAI/article/view/37079/41041)
lists five subset totals and their multimodal portions in its Overview on PDF
page 3. Text counts below are the totals minus those multimodal counts.
[The pinned official TaskScanner](https://github.com/ChatDesignVerification/FIXME/blob/e875437fbb11590b71775b32d3579726d702cfc6/src/config.py#L181)
creates exactly **one Task per case directory**, not one per file, PDF page,
question token, assertion or pass@k candidate. Each SpeCom directory has at most
one q*.txt file. We actually invoked that scanner across all five subsets,
three levels and both modalities: **482 Tasks**. Pass@5 does not explain this gap.

| Subset | Paper total (Text + MM) | Public dirs/scanned Tasks | Loaded critical payloads | Original strict schema complete | Complete after explicit structural overlays | Absent dirs vs paper |
|---|---:|---:|---:|---:|---:|---:|
| SpeCom | 149 (98 + 51) | 149 | 98 | 98 | 98 | 0 |
| MGen | 111 (80 + 31) | 81 | 81 | 55 | 81 | 30 MM |
| TBGen | 158 (107 + 51) | 108 | 107 | 107 | 108 | 50 MM |
| SVAGen | 61 (40 + 21) | 41 | 41 | 41 | 41 | 20 MM |
| RTLFix | 268 (102 + 166) | 103 | 102 | 102 | 102 | 165 MM |
| Total | 747 (427 + 320) | 482 (427 + 55) | 429 | 403 | 430 | 265 MM |

Definitions matter. “Loaded critical payloads” checks task-specific nonempty
question/reference, RTL/TB/interface and PDF image payloads; MGen specifications
are counted separately in strict schema completeness. “Strict” requires all
specified input assets and valid scoring references. “Prompt constructible” is
an even weaker count: the official builder returns **432** prompts, some containing
missing-spec/RTL placeholders or an empty question. It must not be called 432
valid tasks. None of these counts establish hardware correctness or backend support.

The 427 Text *counts* match the paper; exact identity to the original paper tasks
cannot be established without its manifest. The 265 directory deficit is entirely
in multimodal counts, not an effect of free-tool compatibility. The repository
has 55 MM directory keys, but 50 SpeCom MM directories are empty placeholders.
Only five MM cases have usable image/task assets in this snapshot.

## What was found in every subset

* **SpeCom:** 50 of 51 MM directories have empty q.txt/ref.txt and no PDF;
  `SpeCom/L2/Text/GS_62/q.txt` is also empty. The remaining 98 cases have complete
  schema. The official loader additionally omits all 98 available Text specs;
  the explicit adapter inserts those local spec files into the input view.
* **MGen:** all 81 have parseable RTL/TB/DPI interfaces, but 26 L1 Text directories
  lack a spec. Every one has a same-named SpeCom donor with **byte-identical RTL**
  and a nonempty spec. The new adapter verifies this equality before reusing the
  donor spec, and records source path, spec hash and RTL hash. This is structural
  cross-subset reuse, not discovery of 26 missing paper tasks or exact prompt recovery.
* **TBGen:** `TBGen/L3/Text/tbu/tbu.v` exists and is nonempty. The official generic
  finder excludes filenames containing `tb`, and its module selector also skips
  `tbu`. The overlay accepts the sole RTL file using explicit TB-name boundaries
  and its declared module `tbu`. All 108 become schema-ready. Execution on 107
  other testbench-generation inputs is still unattempted.
* **SVAGen:** all 41 present cases have input assets. That does not imply temporal
  proof support: the current executable adapter certifies only the selected CRC
  immediate-property pilot. The official prompt requests concurrent properties;
  the free formal adapter remains a declared substitution with open generalization.
* **RTLFix:** `RTLFix/L2/Text/29/ref52.json` has empty old_code; its TXT fallback
  also contains an empty original-code block. This is a genuine invalid reference
  for the current matcher, not a missing-tool failure. 102 schemas are complete.
  Text reference matching does not constitute an executed repaired-design check.

After the 26+1 structural repairs, **52 existing directories remain asset/reference
blocked**: 50 empty MM SpeCom cases, one missing Text question, one invalid RTLFix
reference. They cannot be silently synthesized and called exact reproduction.

## History, extra files and external sources

All **five reachable public commits**, including initial release
`b19526770f101fed029b23e24523680bf5a7acfc`, have the exact same `data` tree hash:
`2c4635dfd8bfc956d4e63e05b147687fe0f9f179`. Each contains 482 case keys. The checkout
is not shallow; git fsck succeeded. Advertised git refs contain only main and no
tags. There are no submodules, LFS pointers or tracked data archives.

`test/` has 20 case keys, all already in `data/`; its 56 files are byte-identical
to counterparts there. Adding them would double-count examples. README/scripts
contain no supplementary dataset download URL or restore/generation step that
produces the absent cases; the main shell entry invokes evaluation directly.

The releases/issues web pages returned 404, and the branches web page was restricted;
these paths were not retried or bypassed. Thus we do not assert that release assets
are proven absent. Git refs and local source history were checked independently.
The linked [arXiv v1](https://arxiv.org/abs/2507.04276) describes 180 tasks and six
subdomains, an earlier version; it is not an archive of the 747-task final paper.
Why the public snapshot differs from the paper is **unknown**. The evidence does
not support attributing intent, claiming permanent unavailability, or inventing
IDs for the 265 cases absent from this tree.

## Executed coverage and remaining work

The new audit executes the official reference scorer on **all 149 SpeCom and
102 Text RTLFix directories**, each with a known reference response, wrong response
and malformed response: **753 actual in-process scorer calls over 251 directories**.
Across 200 cases with valid references, positives pass and both negatives fail.
The other 51 references cause error for all three controls. One positive-scoring
SpeCom case has an empty question, illustrating why scoring and schema must be
separate. Only **199** of these are complete, reference-checked tasks.

The prior EDA pilot covers four additional unique input directories (MGen, TBGen,
SVAGen and MM RTLFix). Therefore 255 of 482 keys have any scorer/tool execution
record, including invalid-reference diagnostics; 227 code-generation inputs have
**not been EDA-evaluated**. Complete reference-scored tasks plus the four pilot
inputs account for 203 schema-ready case keys. These are oracle/adapter checks,
not 203 LLM results. No live model scores have been produced.

The current EDA runner is case-specific. It is **not** a general executable
747- or 482-case adapter. The matrix labels per-case asset state, actual execution
state, and unverified backend support separately. It does not call unattempted
cases unsupported or executable. Proprietary VCS/VC Static runs, general temporal
SVA support, coverage comparability, full response/model generation and published
aggregate recovery remain open.

## Re-run and concrete full-coverage path

```sh
python3 fixme/benchmark/audit_dataset.py --upstream .cache/fixme/upstream \
  --output fixme/evidence/new_full_audit
python3 fixme/benchmark/validate_audit.py --upstream .cache/fixme/upstream \
  --audit fixme/evidence/new_full_audit
```

Requires existing PyYAML and PyMuPDF. No openai client/API key is needed: the exact
read-only loader/prompt-builder function ASTs are reused without importing model
client code. The official PDF renderer is run at 144 dpi, max eight pages;
PDF text extraction uses PyMuPDF, explicitly marked as an audit substitution.

Evidence is in `evidence/full_dataset_audit_v2/`: detailed `audit.json`, per-case
`coverage.csv`, reproducible summary/history, feedback log, `coverage_plan.jsonl`
and byte/hash validation. The plan lists all 482 keys and their actual input
bindings/overlays, never 265 invented task IDs. The earlier read-only audit is
retained separately; no prior pilot results were changed.

1. **Already done:** enumerate and validate every available case, apply the
   source-verified structural input overlays, replay every safe reference-only
   scoring path, and identify exactly 430 schema-ready input records.
2. **Next within existing authorization:** turn those records into a generic
   offline-response adapter and per-case functional-oracle contracts. First extend
   a bounded L2/L3 selection, then certify the remaining 227 code cases. Use
   observed unsupported/error/unknown states; do not assume feature support from
   file presence. Reuse published references where present and label replay data.
3. **For full 747 identity:** obtain the final paper-time manifest and assets for
   the missing 265 MM tasks and 52 incomplete present cases. A public official
   archive URL or user-supplied archive would suffice; no paid tool is inherently
   needed for this data step. Contacting authors would require explicit messaging
   authorization; none has been sent. Continued local structural work needs no
   additional permission, but cannot recreate unavailable original task identity.
4. **For paper metrics:** require comparable model responses/sampling and tool
   semantics. Free-tool porting can continue; exact proprietary-tool numbers and
   original live-model pass@5 remain unclaimed. Do not run a full costly sweep
   until the case adapters and oracle contracts are reliable.
