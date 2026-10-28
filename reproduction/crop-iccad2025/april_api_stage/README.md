# APRIL CROP API stage: offline interfaces revised; live execution paused

The real-model entry point remains unexecuted. `DENIAL_RECORD.json` preserves
the prior denial and its authorization prerequisite. No API request or local
LLM inference has occurred. The historical 272-measurement non-model study and
its 48 archived prior QoRs are retained unchanged.

[Prepared pilot protocol](PILOT_PROTOCOL.md) describes the requested service,
public payload example, token/request bounds, scientific limitations and exact
separation of EDA preparation from the later real-model pilot.

## Revised interfaces

- `api_adapter.py` refuses network by default, requires a model-approved token
  counter, enforces input/output/byte bounds, refuses redirects and stops on
  transport or truncated-response failures. Credentials enter only at runtime;
  error bodies/headers are omitted and usage fields are allowlisted.
- `pilot_support.py` provides pure tests of semantic retrieval, within-prior
  normalized guidance, attempt accounting, correctness-qualified observations
  and evolving target history. It performs no model, network or EDA operations.
- `api_pilot.py` is a prepared two-stage summary/retrieval/LLM-search driver.
  It now has a side-effect-free import, but has **not been imported or executed**
  during this revision. The parent must explicitly release the denied action.
  Its authorization record must match the runtime endpoint, model, public scope
  and confirmed byte-BPE token-counting profile. Model failures have no heuristic
  fallback. There are at most 34 model attempts and four fresh target EDA calls.
- `prepare_native_priors.py` is a separate CPU-only driver: at most 48 fresh
  prior synthesis attempts, no target or model calls, explicit shared ABC for
  both mapping and CEC, plus independent arithmetic/LUT/depth checks. It creates
  a native bank for the future pilot instead of mixing old Debian QoRs with a
  different tool backend. The preparation protocol and results are separate
  from live-model evidence.
- `test_api_adapter.py`, `test_pilot_interfaces.py` and `offline-tests-v2.log`
  contain 15 passing offline tests, including scripted fake model responses,
  malformed/duplicate proposals, non-normalized vectors, token bounds and a
  deliberately failed CEC. These are interface tests, never research outcomes.

## Runtime and provenance

Set `PAPER_REPRO_ROOT` to the existing isolated runtime root; there is no default
personal home path. Runtime supplies `tools/crop/yosys/yosys`, read-only
`tools/abc-rl/abc/abc`, existing `assets/shared/all-minilm-l6-v2`, and dedicated
`results/crop`. The driver locates `../closed_loop` beside itself. No model
weights, third-party tool binaries, credentials or authorization marker belong
in Git. Existing local Qwen assets remain paused and are not used.

`SETUP_EVIDENCE.json`, `PAUSED.e99589d.json`, `requirements.freeze.txt`,
`offline-tests.log` and `PACKAGE_HASHES.e99589d.json` are historical snapshots
from commit `e99589dd`; their hashes refer to that commit, not the revised files.
The setup and old three-test result were not rerun to claim new evidence.
The current status is described here and by the new preparation artifacts.

The original backend measurements remain historical evidence. Only ratios from
one circuit/backend may serve as prior guidance; fresh target comparisons use
one native run. Even matched tools do not make these toy circuits or LUT4
objectives equivalent to the original industrial method, dataset or PPA.

## Completed native-bank preparation

This continuation executed 48 new native prior measurements on CPU8-15. All48
passed real ABC CEC and independent256-vector checks (12,288 vector cases).
Independent offline rechecking reproduced all48 metrics and rejected a copied
netlist with a deliberately corrupted output. One additional real ABC negative
control rejected non-equivalent BLIFs despite returning exit code0; the pipeline
correctly requires the positive equivalence text as well as the return code.
There were zero API calls, local LLM loads and new target measurements.

See [native-bank report](NATIVE_BANK_REPORT.md), [raw metric comparison](native_priors/comparison.json),
[offline verification](native-bank-verification.json) and current `PAUSED.json`.
Public logs normalize the isolated runtime prefix; APRIL keeps the originals.

## OpenRouter offline preparation

[OpenRouter adapter checks](OPENROUTER_OFFLINE_CHECK.md) add explicit, snapshotted
base/model/key injection for the forthcoming shared loader, an explicit outgoing
no-provider-fallback request, and single-attempt HTTP/timeout tests. All18
offline tests pass; live service behavior and the shared private loader remain
pending. The fixed MiniLM encoder and model-pilot budgets are unchanged.

## Shared-client integration and authorized pilot

The [real pilot protocol](REAL_PILOT_PROTOCOL.md) supersedes the waiting-stage
service/34-request draft: the parent has authorized33 CROP requests through the
shared client and a10USD cumulative API stage across projects. `api_pilot.py`
now uses only `shared_chat_adapter.py`; direct HTTP is disabled. Thirty mock
tests validate the actual shared module with disposable private ledger fixtures.
No key/config copy or global policy change is part of the integration. Live
results, when available, are separate from these offline checks.
