# APRIL CROP API stage: prepared, not executed

This packages an API-only extension of the existing CROP reconstruction. It has not completed the semantic/LLM method. The original 272-measurement non-model study remains unchanged; no new synthesis oracle measurement or model call has run.

## Prepared components

- api_adapter.py: standard-library OpenAI-compatible /chat/completions adapter. Credentials enter only through runtime PAPER_LLM_BASE_URL, PAPER_LLM_API_KEY, and PAPER_LLM_MODEL. Network defaults off; errors omit provider bodies and auth headers.
- api_pilot.py: two-stage module/design summaries for six public priors plus held-out FIR3, local canonical MiniLM embeddings, fixed retrieval, and up to three live LLM proposals after c0. It preserves raw prompts/completions and invalid attempts. Parent-created results/crop/API_AUTHORIZED.json authorization marker is required before any calls. Creating that marker itself requires authorization; none is supplied here.
- test_api_adapter.py and offline-tests.log: three offline transport/schema/redaction tests passed. No endpoint contacted.
- ONLINE_MODEL_INTERFACE.json: payload categories, schemas and bounds. Nominal 17 calls, at most 34 attempts, at most four new EDA measurements.
- SETUP_EVIDENCE.json, requirements.freeze.txt: native Yosys0.52 build, source/binary hashes, environment versions and FIR3 parse/structural-check evidence.
- PAUSED.json and DENIAL_RECORD.json: pending state and exact approval barrier.

## Portability and authorization

PAPER_REPRO_ROOT selects an isolated APRIL-style runtime root (default /home/shugu/work/paper-reproduction-april-20261028). The packaged driver locates ../closed_loop relative to itself. Runtime root must supply tools/crop/yosys/yosys, read-only tools/abc-rl/abc/abc, canonical assets/shared/all-minilm-l6-v2, and writable results/crop. No weights or secrets are committed. API LLM use is the user's preference; local Qwen inference is disallowed and never occurred.

Do not execute the live entry point until the parent authorizes endpoint, credentials and public-data transmission. The preflight execution attempt was denied by automatic approval review before execution; no retry occurred. Packaging is independent of that denied operation.

## Scientific limitations

Source SHA: a7b6f8dbfcc2b1c2c8a90d9c29c315388a253e7f. All seven tiny circuits have one top module, so nontrivial multilevel hierarchy is untested. The 48 archived prior QoRs came from the earlier Debian backend; fresh native Yosys/sharedABC may differ. This is cross-backend archival guidance rather than a matched-oracle comparison. A single-target, single-seed pilot cannot establish quality improvement. API model and Yosys/ABC LUT4 substitutions do not reproduce the paper's model or RTL Architect physical PPA.

No completed semantic retrieval, LLM proposal or new optimization result is claimed.
