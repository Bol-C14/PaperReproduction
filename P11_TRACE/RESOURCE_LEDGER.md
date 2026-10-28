# TRACE resource ledger

Round 2 started 2026-10-28 ~10:34 UTC. Authorization: <=2h setup/diagnosis, <=2GB downloads, current CPU/memory, no GPU/full training/API/push.

Available cgroup: 4 CPU quota, 16 GiB memory. Python 3.12.14. Training restricted to 1 torch thread. No paid resources.

- Initial environment call: ready response preceded execution availability; first command failed `No usable execution environment`; retried after explicit ready environment context. No model work occurred.
- Dependency probe: torch, PyG, Lightning, DGL and torch-scatter absent; numpy/sklearn present. This is a dependency failure, not a method failure.
- Existing upstream metadata snapshot and audit retained. Previous audit's Git object inspection fetched 27,953,032 checkpoint bytes (~28MB); no checkpoint loaded. No hosted dataset downloaded.
- Git origin inspected: Bol-C14/PaperReproduction. No TRACE remote branch existed. Created local orphan branch reproduction/trace-dac2026; other remote branches untouched. No push authorized or attempted.
- Protocol frozen in pilot/PROTOCOL.md before model/data execution.

## Completed bounded run

- Actual dependency install: isolated pilot `.venv` with system-site reuse; torch==2.8.0+cpu from official PyTorch CPU index and torch-geometric==2.7.0 from PyPI. Both successful. No builds, CUDA libraries, DGL, Lightning or torch-scatter installed. Official installation guides and exact transitive versions saved in pilot/SOURCE_VERSIONS.json and requirements-cpu-lock.txt.
- Installation logs sum to approximately **188,511,600 bytes** of rounded reported wheel/metadata transfers; this excludes small unreported index/HTTP overhead. Even adding prior ~28MB checkpoint Git objects, transfer is comfortably below 2GB. No circuit dataset download or repeated asset access occurred. Pilot venv is ~775 MiB installed, distinct from download volume.
- Imports, exact labels, frozen split, tutorial controls and oracle reconstruction all passed on the first model run.
- Model run UTC **10:37:42–10:37:54**; reported wall time **12.6415 s**, process CPU **12.6729 s**, peak RSS **376,000 KiB** (~367 MiB). No CUDA initialization; one torch thread (quota available: 4 CPUs).
- Direct arm: **120 steps, 5.3559 s**, 60,337 parameters. Residual arm: **120 steps, 4.8074 s**, 60,337 parameters. No retries, HPO, GPU time, or paid resources. Residual training yielded five out-of-range reconstructed probabilities; recorded without hiding/clamping.
- Saved-result verification: passed protocol/data hashes, parent-disjoint membership, independent saved MAE calculations, optimizer step counts, rename control tolerance and seven upstream source hashes. No second learning run was performed.
- Nonfatal pip cache ownership warning during `pip freeze --local`: pip disabled its cache automatically; no permissions/settings changed. Installation already used `--no-cache-dir`.
- RESULTS.jsonl includes retrospective setup failure records, with their retrospective status explicit. No training/model failures occurred. Interrupted git metadata size inspection belonged to the earlier audit, not a hidden learning run.
- Entire Round 2 setup/diagnosis and pilot remained far below the two-hour bound. Fresh isolated-environment replay and industrial benchmarks were not run.

## Predictive closure tranche (v2)

- Continued on existing `reproduction/trace-dac2026`, base local commit114072d; no branch changes, push or PR. Repository AGENTS.md and `.agents` skills were searched; none present. Existing pinned CPU venv reused. Paper v3 publicly read; no new dataset/checkpoint/package download, credentials, gated terms, paid resource, security change or external LLM call.
- Official PM checkpoint exported from existing local Git objects:4,241,614 bytes, SHA25619fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0. This is a local copy, not a download. `weights_only=True` loaded all64 source-compatible entries; epoch metadata50. Plain AST extraction avoided installing Lightning; the three original model classes remain unchanged.
- Protocol frozen before data/model experiments;640 sample labels independently checked before optimization. Source `_cop_with_cov` failed deepest-level oracle check (max error0.83673); original source/results retained and inclusive paper recurrence used explicitly as a port correction.
- Attempt1 interrupted for an implementation error: direct sigmoid was applied after residual clamp, contrary to the frozen intended direct baseline. Archived320 completed optimizer updates and all partial results. Approximate wall26.66s (±1s from timestamp precision); partial CPU time not captured. This attempt is excluded from comparisons.
- Attempt2 interrupted to fix explicit PyTorch dropout seed pairing for transfer adaptations. Archived580 completed persisted updates;0–19 further updates were not journaled before interruption. Approximate wall42.55s (±1s); partial CPU time not captured. Data, architecture, LR, step budget and seeds were not tuned; this attempt is excluded from comparisons.
- Corrected valid run UTC11:31:48–11:34:27: **158.652s wall,159.687s process CPU,357,684KiB peak RSS (~349MiB), one CPU thread, no CUDA initialization**. Exactly2400 optimizer updates independently counted in the per-update journal:6×240 pretrain +48×20 adaptation. Parameter count417,761, including unused source parameters.
- Valid pretraining90.48s total; adaptation47.34s total. Mean adaptation roughly0.98–1.01s/family (16 fully node-labeled examples from2 support parents). Batched inference median0.0472s per48 query graphs. Query-label generation, model loading and support adaptation are separately excluded from inference timing.
- Valid plus interrupted execution wall approximately227.87s, plus separately uninstrumented verification/diagnosis/reporting. Total process CPU including interrupted runs is unknown; no exact number invented. Initial20-step resource pilot was retained in the valid240-update run; projected167s and peak349,876KiB passed the predeclared30min/4GiB cap. No scaling beyond protocol.
- Independent read-only verification:96 prediction files, saved MAE checks, generic truth-table recurrence (max difference3.30e-7), protocol/split hashes,2400 update count. Complete pipeline rename/reload check passed24 saved main adapted checkpoints with max difference0. Old v1 weights/predictions reproduced exactly for retrospective diagnosis; no v1 retraining.
- Reporting audit caught a filter that initially mixed direct and FSL rows in the diagnostic-only summary table. Corrected before final report; raw predictions/per-family results and primary table unchanged. No additional model run or tuning.
- PyTorch nested-tensor prototype warning recorded; no API/security settings changed to suppress it. All negative controls, out-of-range probabilities, invalid attempts and source/runtime versions retained.
- Exact commands: closure/CLOSURE_REPORT.md and closure/SOURCE_VERSIONS.json. Structured cost limits/unknowns: closure/RESOURCE_ACCOUNTING.json. No essential resource blocker remains for this reduced-data predictive loop; industrial task/full-data coverage remains outside verified assets and measured budget.

## Targeted scientific evidence audit

- No new optimizer updates or broad sweep. Imported entire unchanged upstream PM file with a declared inert Lightning base-class symbol (trainer orchestration not invoked); compared original versus a separately corrected loop bound on the same graph, official weights and residuals. Zero-shift output0→0.25; same official residual output0→0.2500006854534149. Source and model-state hashes verified unchanged.
- Identity check used raw semantic node IDs, explicit ports and repeated edge columns, with asserted JSON round trip and direct tensor conversion (no dedup/coalescing). Two graph pairs×7 existing pretrained states=14 checks; distinct graph tensors, identical operator sequences/output embeddings.
- Measured focused checks:1.237685s inner wall (starts after imports),2.330524s process CPU including imports,351724KiB peak RSS, no CUDA. Timing boundaries differ explicitly; no exact total including packet-generation tooling was captured. No package/data/model download, paid resource or API/LLM use.
- Generated exact split/label/sample-presentation manifest, per-seed/family paired tables and final-run provenance from existing artifacts. Current summaries explicitly define FSL as function-shift learning; few-shot adaptation remains a separate evaluation. Frozen protocols/data and valid training harness were not edited.
