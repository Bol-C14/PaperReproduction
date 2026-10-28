# Mechanism coverage and exact gaps

This is an independent method reconstruction built from official encoder code, not an assertion that unpublished training/downstream code was recovered. See the final report for metrics and `PROTOCOL.md`/`AMENDMENTS.md` for frozen choices and a correctness repair.

| Mechanism | Executed implementation/evidence | Remaining fidelity boundary |
|---|---|---|
| PM cell semantics | Explicit 64-channel repeated truth tables and ordered pins; exhaustive corpus check | Synthetic cells, not original Liberty version/corner/pin conventions |
| AIG/PM pairing | Exact Boolean agreement and internal correspondence validation; graph-level paired views | SOP lowering in primary corpus, not original mapped corpus or ABC strash |
| Official encoders | Strict PM full56 tensors; strict AIG encoder/readout64 tensors; active source untouched | Original AIG connectivity head16 tensors missing; training parent lineage unknown |
| Stage-one semantic supervision | PM probability adaptation2 epochs, exhaustive exact probabilities; official vs random initialization | AIG frozen, not retrained; reduced corpus/schedule; exact enumeration replaces random simulation |
| Multiview cone modeling | Trainable PM, frozen AIG; four-hop functional masking; 4x8-head Transformer; L1 + probability objectives | CPU batch4 and6 epochs; functional-channel reconstruction; moving detached PM targets; no bit-exact schedule |
| Causal/method controls | PM-only, wrong-parent AIG, random-start encoders, no-MCM; two seeds; family/parent/truth-function holdout | Tiny six-PI domain, two held-out families; shuffle can change token length; no broad statistical generalization |
| ECO observation/finetuning | Unknown single-cell cut; paired golden AIG; BCE ancestry ranking plus embedding reconstruction | Single-site corruption less extensive than paper's cone deletion; fan-in ancestry direction explicitly interpreted; original task labels unavailable |
| ECO patch generation | Exact Boolean obligations from observed output with patch0/1 and golden AIG output; candidate-prefix feasibility; explicit AND/NOT patch | Enumeration substitutes for authors' ABC runeco SAT/exact pruning; top3 budget substitutes for large candidate budget |
| Independent correctness | Separate recursive gate/Boolean-cell checker against direct-family truth signatures; all emitted patches replayed; inverted-patch rejection | Six-PI exhaustive domain; original industrial/contest cases unavailable |
| Inference separation | All48 paired/208 test rankings/repairs reproduced with only id, observed PM, golden AIG, patch site | Oracle direct-fanin baseline intentionally has privileged information and is excluded from learned claim |
| Real public-netlist/ABC extension | Separately declared, pinned ABC/EPFL inputs, bounded build/evaluation | Status and formal checker evidence recorded separately; teaching unit-cost library is not paper Liberty/timing |
| Technology mapping improvements | Not reconstructed | No DeepCell modified &nf/ABC revision, mapping head/checkpoint or library timing/corner/constraints; baseline mapping alone cannot substantiate paper ADP benefit |
| Physical timing ECO | Not attempted | Different scientific task: no placement/routing/parasitic/signoff flow |

Exact useful provision targets for original-result fidelity:

- `npz/iccad_aig.npz`, `npz/gf180.npz`, `npz/gscl45.npz`, `npz/sky130.npz` plus Nangate test equivalent; or processed `data/lcm{,_sample,_test}/inmemory_max_4096/data.pt`. Need schema and repository/commit/parent/cone/split manifest, cell truth-table pin ordering, simulation recipe, mapping tool/version and Liberty file/corner identity. No exact release version was advertised in the inspected tree.
- Original fused `deepcell.top_model.TopModel` checkpoint/config at repository commit `b82aef22559c6d8c52eb4feb437ebdd32709360e`, including refinement direction, PM/AIG encoder types, frozen modules, Transformer/Linformer options and training provenance. Newly trained local fusion weights close execution but do not replace original result provenance.
- Actual functional-ECO finetuning data/corruption and label definitions, task head checkpoint and full modified ABC `runeco` interface/revision, ICCAD17 case/target/cost mapping and any industrial cases. The independent exact solver does not establish authors' patch costs or speedups.
- For mapping, actual cell-type head/fine-tuned checkpoint, cone labels and preprocessing, DeepCell modification to `&nf`, exact ABC version, Liberty files/corners and `read_lib`/constraints recipe. Renting GPU would not supply these assets. No GPU readiness manifest is necessary: the executed core architecture fits current CPU/RAM.

Unverified is not absent. The local reconstruction closes a controlled representation-to-functionally-correct-patch loop, while original data, integration and real-library evidence remain irreducible gaps for the paper's reported generalization/PPA/runtime results.

A separately declared full-token fidelity sensitivity (`FULL_TOKEN_PROTOCOL.md`) also trains paired/PM-only for both seeds using the public trainer's256-channel reconstruction target; its scores and public-tool extension are separate from the five-arm functional-channel primary comparison. No result replaces another.

Additional reproducibility/fidelity detail: structural PI vectors are deterministic per case ID. PM and frozen AIG resets use the same case seed, which aligns the first physical PI basis vectors across the paired views when input order is preserved. This is an explicit reconstruction convention; the released TopModel calls the encoders consecutively and does not explicitly establish that shared basis. No internal PM-to-AIG node map enters the model. Wrong-parent shuffling also perturbs token length and this basis relation, so its score is a broad paired-context corruption control rather than an isolated semantic-only intervention. Moving detached teacher embeddings can make reconstruction error fall without proving useful cross-view semantics; downstream outcomes remain the relevant independent check.
