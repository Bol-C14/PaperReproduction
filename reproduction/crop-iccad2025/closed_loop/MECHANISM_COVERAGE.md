# Mechanism coverage and remaining model boundary

Source: [CROP v2, Sections IV and V](https://arxiv.org/html/2507.02128v2). This is a reconstruction against the paper; official CROP code remains unverified.

The published sequence is hierarchical RTL summarization, summary embedding, maximum-inner-product retrieval of a prior design, and delivery of its best historical configurations/QoR to an LLM search. Each proposal is validated, evaluated, and added to later target prompts. The evaluated backend is RTL Architect. Per-trial re-retrieval or insertion of each target into the global retrieval database is not specified. We therefore keep prior retrieval fixed and isolate evolving target histories.

| Mechanism | This deliverable | Classification |
| --- | --- | --- |
| Module summaries → circuit summary | No generation; required fields and provenance checks in `model_contract.py` | Missing model component; not replaced by lexical text |
| Summary → dense semantic representation | No embedding inference; 384-dimensional cache-import contract only | Missing model component |
| Structural representation | Normalized high-level Yosys cell/output-bit features, extracted before measurement | New baseline; not a semantic summary or AST-assisted paper implementation |
| Nearest-design inner product search | Actual query/prior vector comparison; target families excluded from archive | Mathematical retrieval mechanism port, with substituted representation |
| Prior configuration/QoR archive | 48 real measurements, eight legal configurations on six prior circuits | Executed mechanism port with a free oracle |
| Top configurations as guidance | Best three measured entries from one retrieved design, normalized to its common baseline | Executed; guidance count is an explicit reconstruction choice |
| LLM proposal using prior and target history | JSON contexts exported; actual proposer is categorical kernel LCB | LLM component missing; new policy baseline, not faithful LLM search |
| Validate legal options | Fixed eight-option pool; illegal or repeated proposals rejected | Executed infrastructure port |
| Real evaluation | Native Yosys/ABC mapping into a uniform LUT4 resource model | Substituted oracle, not industrial placement or physical PPA |
| Observation → next selection | Per-query archive updated after every real evaluation; later proposal consumes it | Executed closed feedback loop |
| Global database update | Prior archive frozen throughout every query | No invented online database-learning claim |
| Controlled comparison | Structural, random-prior, no-guidance, and random-search arms; four calls each | New baseline experiment, not reported paper results |

None of the files here is an original CROP release. “Mechanism port” describes an abstract step retained from the published process, not equivalence of models, tools, datasets, or performance. The kernel policy is deliberately labeled separately.

## Exact remaining interface

The executable boundary is concrete:

1. Supply a cache per circuit containing module summaries with the six published fields, a whole-design summary with the ten published fields, and a dense embedding. `model_contract.summary_cache` verifies source hash, dimension, finite values, nonzero norm, model revisions, prompt hash, normalization, truncation, and generation provenance. There are no fabricated cached summaries or embeddings in this deliverable.
2. Substitute semantic vectors for the structural vectors in the inner-product retrieval step. Keep prior guidance construction, held-out split, legal configurations, target budgets, and measured oracle identical.
3. Replace `study.propose(context)` with an actual model response to the exported context. The request contains background/objective, legal options, retrieved configuration/QoR guidance, and only the preceding observations for this query. `model_contract.proposal` validates a response shaped as `{"configuration":{"mode":"quality","noalumacc":false}}`. It accepts only the frozen free-tool parameter pool and rejects duplicates. It cannot validate unreleased industrial options.
4. Preserve raw generation, model/revision, decoding parameters, prompt and completion tokens, elapsed time, parsing failures, and every consumed attempt. Do not replace a failed model proposal with the heuristic while labeling the run as LLM-driven.

These validators are offline import interfaces. They do not perform inference and were not used to claim a semantic run. The current driver uses the explicitly named structural/kernel baseline. A full semantic driver integration remains unexecuted until genuine model outputs are available.

## Concrete access outcome

No Torch, Transformers, sentence-transformers, llama.cpp runtime, or model checkpoint was found in the selected workspace/runtime. That is a local observation, not global unavailability. To check a free CPU alternative without installing a model stack, one unauthenticated HEAD request was made to each official public weight URL:

- `sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx`
- `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf`

Both returned **proxy tunnel 403 Forbidden**. Exact URLs/statuses are saved in `model_access_check.json`. No retries, mirror/token/authentication workarounds, gated agreements, model downloads, or model calls followed. This is a denied network access action, not an automatic-approval rejection or an uncertain inference outcome. External LLM calls are also outside this tranche's authorization. Semantic summarization/embedding and LLM selection remain the essential unexecuted components; none is disguised as a heuristic.
