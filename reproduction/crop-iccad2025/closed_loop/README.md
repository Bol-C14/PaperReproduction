# CROP: closed non-model methodology study

**The affordable non-model loop is closed:** structural retrieval → configuration proposal → real LUT mapping → validated measurement → target archive update → subsequent selection. The 272-measurement controlled experiment is complete. **Semantic summarization/embedding and LLM proposal generation remain unrun**, with a concrete weight-access blocker. This is an independent baseline around CROP's retrieval/transfer question, not full CROP or original released code.

The earlier [twelve-call smoke test](../README.md) and [asset audit](../../../P15_CROP/ASSET_AUDIT.md) remain preserved. [Mechanism coverage](MECHANISM_COVERAGE.md) separates retained mechanisms from substitutions and missing models. [Commands and costs](COMMANDS.md) records tool repair, preliminary failures, versions, downloads, exact execution forms, and bounds.

## Outcome

Structural retrieval did **not** outperform random retrieval. Across four held-out circuits and three seeds, structural retrieval had one loss and eleven ties against random-prior retrieval. Against the same proposal policy without guidance, it had one win and eleven ties. Against random search it had two wins, one loss, and nine ties. These small, heavily tied observations do not support a general retrieval-performance claim.

| Arm | Mean best / common initial objective ↓ | Mean best / eight-option reference ↓ | Reference optimum reached |
| --- | --- | --- | --- |
| Structural retrieval + kernel proposal | 0.902775 | 1.013318 | 10/12 |
| Random-prior retrieval + same kernel | 0.896609 | 1.006659 | 11/12 |
| No guidance + same kernel | 0.908942 | 1.019977 | 9/12 |
| Uniform random untried configurations | 0.906399 | 1.017106 | 9/12 |

Every case contributes equally to these arithmetic means. The score is **LUT4 count × maximum unit LUT depth**, with lower values preferred. The reference optimum is only over the frozen eight configurations; it is not a global circuit optimum. The reference sweep was performed after all online proposals and never entered retrieval or search contexts. No confidence interval or significance claim is justified by four circuits and three seeds.

Illustrative actual structural-arm trace, FIR3, seed 23:

| Evaluation | Config | LUT count | Unit LUT depth | Product | Best so far |
| --- | --- | --- | --- | --- | --- |
| 1 | c0 | 344 | 11 | 3784 | 3784 |
| 2 | c5 | 292 | 12 | 3504 | 3504 |
| 3 | c6 | 284 | 15 | 4260 | 3504 |
| 4 | c1 | 308 | 13 | 4004 | 3504 |

Here fewer LUTs alone would pick a worse area/depth product. Individual pairs, including all controls and seeds, are in [measurements.csv](measurements.csv). Per-trace selected neighbors, configuration sequences, best pairs, and ratios are in [trace_summary.csv](trace_summary.csv). Machine-readable aggregate results are in [analysis.json](analysis.json).

## Experiment construction

Ten independently authored, fully inspectable RTL workloads replace the three old width-scaled fixtures. The six prior families are four-input sum, multiplication, configurable ALU, barrel shift, min/max, and population count. The four held-out application families are three-tap variable-coefficient FIR, CRC8 update, priority encoding, and Manhattan distance. No target or width-scaled copy is in the prior archive. They share primitive operators by design; this is a composition-transfer study, not a claim of learning across an established industrial benchmark split. Neither EPFL nor RTLRewriter sources were imported. These small workloads are suitable for running the feedback mechanism on CPU, but remain a limitation on external validity.

Before measurements, [manifest.json](manifest.json) froze circuits, hashes, options, objective, seeds, arms, guidance count, budgets, and correctness limits. The eight configurations cross `alumacc` enabled/disabled with four actual ABC LUT4 mappings: fast, default quality, area-oriented, and depth-oriented. All use the same LUT4 resource model. The two explicit ABC scripts are under `abc_scripts/`. These are legal Yosys/ABC options, not invented substitutes for undisclosed industrial parameter names.

The real historical archive required **48 mapping evaluations**: six priors × eight options. Its best configurations are diverse: c0 for sum, multiply and min/max, and c1 for ALU, barrel and popcount. Some ties exist. Thus retrieval can change guidance content, unlike the earlier smoke test where every prior transferred the same option.

Structural representation uses normalized log-scaled output-bit counts from elaborated Yosys operators plus an I/O-size feature. It is extracted before fine synthesis and contains no family label, measured QoR, target result, or semantic summary. Nearest-prior selection is by inner product. One selected prior supplies its best three measured configurations and normalized objectives. The random-prior arm uses the same archive and guidance count. Its RNG is reinitialized per seed, so each seed chooses the same random neighbor across targets; this reduces neighbor-draw coverage and is recorded as a limitation, not hidden as independent sampling.

The proposal policy is a **new categorical kernel lower-confidence-bound baseline**. It predicts normalized objective from the target observations and optional fixed guidance using Hamming distance over the two legal options. A seeded tie order and an uncertainty bonus allow exploration. It does not impersonate an LLM. Every arm starts with c0 and makes four distinct actual evaluations. No-guidance and random-search controls deliberately omit archival guidance; online budgets are matched, while the 48-call history construction cost is separately reported and is not a cost those controls inherently require.

Each measured result updates only that query/seed/arm's target history. The next JSON context includes those preceding results, and the pure proposal function consumes them. Prior retrieval stays fixed; no unreported cross-query learning or target insertion into the prior database occurs. The 192 online calls cover four targets × three seeds × four arms × four evaluations. A separate **32-call** sweep of the four targets' eight options supplies the post-hoc reference. None of those 32 calls is credited to the online arms.

## Correctness and evidence

All **272/272** measured runs passed structural checks and ABC combinational equivalence between the pre-ABC generic network and the mapped network. A separately written Python arithmetic reference was compared with the mapped LUT truth tables on 256 boundary, one-hot, and seeded random inputs per call: **69,632 vector checks**, with vectors intentionally reused across configurations/repeats. These are not 69,632 independent random samples. Yosys `ltp` independently agreed with reported unit LUT depth on every run.

The Python check covers the original workload's intended arithmetic and bit operations; ABC CEC covers mapping equivalence. The sampled reference checks are not a formal proof of the entire behavioral-RTL-to-generic-synthesis transformation or four-state Verilog semantics. Every workload is combinational and unsigned, with explicit widths. There are no sequential or physical-design correctness claims.

Checks also established exact online budgets, isolated target histories, common initialization, legal non-repeated proposals, deterministic proposal replay, stable structural features, matching metrics on repeated measurements, and no post-hoc reference leakage. A deliberately corrupted COPY of a mapped output was correctly rejected by the independent checker. That negative check is preserved under `checks/` and is not counted as a failed synthesis trial.

Feedback affects behavior: replacing only prior measured target objective differences with flat values, while preserving the same visited configurations, changed **49/72** later non-random decisions and **69/72** candidate score sets. This is a policy-sensitivity check with zero additional oracle calls; it is not evidence of improved optimization quality. The method is doing more than replaying a fixed configuration list.

`contexts/` contains every proposal request and response. `archives/` contains each final target history and hash. `ledger.jsonl` preserves starts and finishes. Each `runs/` directory contains exact commands, synthesis script, high-level and mapped JSON, BLIF reference/output, raw Yosys and CEC logs, and results. There were no post-freeze failures to discard. Preliminary tool failures are preserved separately under `pilot/`.

## Reuse and remaining gap

To inspect or regenerate only analysis, without any synthesis calls:

```sh
python check_and_report.py
```

To execute the study again, preserve this completed directory and prepare a new directory containing `study.py`, `check_and_report.py`, `model_contract.py`, `bootstrap_native.py`, and `native/downloads.json`:

```sh
python bootstrap_native.py
python study.py freeze
python study.py
python check_and_report.py
```

The bootstrap uses pinned packages and SHA-256 values from Debian, unpacks locally, and stops on denial. No system installation is required. The study refuses to overwrite an existing ledger. The reference platform is Debian 13; package dependencies resolved from this environment. New downloads totaled about 11.2 MB, and the expanded run took about 79.5 seconds on CPU. No peak-RAM estimate was fabricated.

The [offline model import contract](model_contract.py) specifies the missing summary, embedding, and proposal interfaces. No local inference stack or checkpoint was found; both official free-weight access checks returned proxy 403s and were stopped without bypass. No external LLM call was made. Genuine semantic generation, embedding retrieval, and LLM proposals remain unexecuted, so this deliverable cannot evaluate the core semantic advantage claimed by CROP. The industrial route also still needs authorized RTL Architect and design/technology assets; free LUT proxies do not become physical PPA by changing their labels.
