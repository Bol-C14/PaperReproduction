# AutoSizer APRIL API preparation stage

This directory packages preparation evidence from 2026-10-28. The simulator-to-controller bridge is **not yet implemented**. There were **zero actual API calls, zero SPICE attempts, and zero model loads** in this stage. Offline test responses are explicitly synthetic software fixtures.

The parent checkout was `reproduction/autosizer-icml2026` at `35865afabc05be1a7e5c900bd3097ff8ea70ed85`. Historical optimization results and both phase-closure markers remain unchanged. This directory does not reopen them.

## Included files

- `api_controller.py`: standard-library OpenAI-compatible adapter. It is a reusable class, with no live executable entrypoint and no network activity on import. Calls fail closed unless the caller explicitly sets authorization and supplies all three designated runtime variables: `PAPER_LLM_BASE_URL`, `PAPER_LLM_API_KEY`, and `PAPER_LLM_MODEL`. No real credentials are included.
- `test_api_controller_offline.py` and `offline_adapter_tests.json`: nine passing offline checks. Network access is replaced by a prohibited-call stub. The clearly labeled synthetic credential placeholder belongs only to the offline transport fixture.
- `LIVE_CONTROLLER_INTERFACE.json`: proposed public payload categories, schemas, size caps and bounded call budget. This proposal is not execution authorization. Its earlier paused-backend wording is historical; the final backend policy is **API only**, with no local Qwen use.
- `STAGE_REPORT.json` and `PAUSED_STATE.json`: exact completed work and remaining blockers.
- `SETUP.md`, `requirements.lock`, `ngspice-version.txt` and asset manifests: recorded environment, simulator source identity, and pinned public SKY130 file identities.

The simulator was compiled locally from official ngspice 44.2 source because APRIL uses Rocky Linux 9/glibc 2.34; the historical Debian binary was not reused. The tt selector uses unchanged official SKY130 model bodies. Installed dependencies, native executables, source archives, PDK payloads, environments, caches, shared model weights and full build logs are excluded from this package.

## Remaining work

The parent must provision the designated runtime variables securely, approve the exact endpoint/model and permitted public data scope, and set the API spend cap. A new timestamped execution protocol and fresh output root must then be frozen before any real simulator or API call.

A future bridge must connect actual circuit understanding, active/fixed-domain selection, random/GP-UCB decisions, new ngspice measurements, and model-generated outer reflection. It must enforce domain and unseen-point budgets, preserve invalid raw responses, independently rescore strict constraints, and keep historical oracle/control results out of prompts. The proposed small pilot has two 12-attempt controller batches and a separate 24-attempt GP control. One easy inverter/one seed would establish integration only, not method superiority or reproduction of Gemini/24-task results.

No live model or simulator command is provided or executed by this packaging step. Nothing was pushed.
