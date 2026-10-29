# One-case blind live pilot

Status: **live_pilot**, one preselected Ibex PR48 compressed-decoder episode only. A component-scoped, file-RPC agent using `google/gemini-2.5-flash` through the registered shared Client passed the unchanged official native reproducer and the independent task-described HINT-family contract. This is not the paper's six-hour/500-iteration protocol, a full repository shell-agent run, a model comparison or a benchmark-wide success estimate.

## Actual use and enforced bounds

| Call | Serialized visible-message bytes | Measured provider input tokens | Output tokens | Known cost USD |
|---|---:|---:|---:|---:|
| 1 | 11,556 | 4,002 | 59 | 0.00134810 |
| 2 | 12,137 | 4,183 | 406 | 0.00145828 |
| Total | 23,693 | 8,185 | 465 | **0.00280638** |

There were **2 requests and 3 file-tool actions**. Both returned the fixed model, Google AI Studio provider and zero reasoning tokens. Each request reserved the full **USD0.32** before transmission and settled only to its known provider-usage cost. No retry, unsettled request, unexpected infrastructure failure or timeout occurred. Generation took3.0169 seconds; the complete episode including pristine grading took9.0444 seconds. At the saved post-run snapshot, shared global accounted cost was **USD0.05087063**, with pending/unknown zero and the **USD10 ceiling unchanged**.

The released maxima were4requests,4000 total output tokens,8file tools,300 seconds including grading, USD0.50 actual batch cost, and a full USD0.32 reservation per serial request. Output allowance was `min(1024,4000-output_used)`; no4096 total-output allowance existed. Unknown cost/usage, protocol or infrastructure violations, or a limit stop the trial without automatic retry. The two unused request slots were not consumed and do not authorize another episode. No further calls or experiments are part of this closeout.

## Preregistration amendment and provenance

Before any live call, the planner-chosen24k billed-input-token guarantee was explicitly withdrawn: opaque provider framing cannot be certified by assuming512 tokens per message. Its replacement enforced **24000 visible-message JSON bytes/request and96000 cumulative admitted-attempt bytes**, exactly measured as `len(json.dumps(messages,allow_nan=False).encode('utf-8'))`. Provider input tokens are reported as measured usage, not a guaranteed billed-input cap. Financial, unknown-cost, output, request, tool and time gates remained intact. Reasoning was disabled, standard Google AI Studio was the sole provider, fallbacks were disabled and price caps were fixed.

Executed immutable identities:

| Component | SHA-256 |
|---|---|
| Shared Client | `36eb7c26ea308322f3fbdb883d9c144017f7dd4301f98342e8869c52db75ac71` |
| Driver | `9a364f801bdb2c02c3bf1136e455bdd35582d5634768c4bb31c3b6f3e8830592` |
| Grader | `1b71f68bb6c4e8a00adde42a1de535579572291af77a87b29dfaa586a6a217b8` |
| Registered freeze file | `3c1a5bcaf098210f3dfda1127e8e07536af023873ec77083cc75e4bffa4daa7d` |
| Canonical freeze release | `bd26cd0e4dae15e1bc4548817ee0710e40e9b3d41f6bbedbc90875b2e57edc60` |

All file identities and zero prior batch attempts were verified before the single launch. The agent saw only the released bug and pristine source context; file RPC provided no shell, interpreter, network, history, hidden/reference tests, prior counterexamples or evaluator feedback. Existing credentials stayed inside the host-side shared Client. The final patch was frozen before separate grading; neither raw prompts/responses nor solution/verifier contents are included in this public export.

## Result and interpretation

The base compiled and failed its target behavioral check; the hash-identified candidate applied cleanly, compiled and passed the same native check. The unchanged upstream report records **one fail-to-pass**, zero none/skip-to-pass and **zero pass-to-pass tests**. Process/applicability/simulator evidence was reviewed; a PASS string or exit code alone was not treated as correctness.

The independent HINT contract has **0/31 failures**. On the frozen domain of **65536 two-state lower16 inputs with upper16 bits zero**, the candidate retains **1 reference-vector difference outside the HINT family**. This is not full reference equivalence, universal ISA correctness, four-state/formal equivalence or full-chip validation. No natural official-vs-HINT-contract false acceptance was observed in this episode; prior offline adversarial coverage gaps remain. Training exposure to this public historical task is unknown. One case supports no model advantage, anti-memorization or unseen-task generalization claim.

Pristine grading used the exact reviewed container-internal taskset correction, no network/proxy, immutable no-pull images and existing memory/PID/deadline bounds. Before the pilot, real container and Python/shell/four make-child probes verified CPU0–3 for all three grader contexts; a host-prefix-only control saw192 CPUs. Individual live-process masks were not separately sampled. All task containers were removed.

An evidence-read transport interruption occurred after execution and settlement. Read-only collection resumed; no model request or episode was repeated. Original raw evidence remains private and unchanged. `live_pilot/summary.json` gives bounded metadata; `live_pilot/EVIDENCE_INDEX.json` links hashes and relative private-bundle members. Those hashes do not redistribute the underlying prompts, responses, generated patch, hidden/reference tests or vectors. No push occurred during preparation; this public result update awaits independent final audit.


Financial provenance correction: the privately named `exact-request-ledger.json` is a **field projection**, not a complete original ledger. Its reservation rows omit `caller_reservation_usd` and `cost_envelope`; retained fields and costs match the originals. Original batch-row bytes and full metadata-only ledger/registry snapshots are separately preserved privately, linked by SHA-256 in the evidence index. This labeling correction changes no spend or scientific result. No credential configuration is included.
