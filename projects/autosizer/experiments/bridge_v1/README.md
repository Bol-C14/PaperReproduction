# AutoSizer real simulator-controller bridge

This **new** 2026-10-28 non-API pilot completed 53 actual ngspice 44.2 runs on
an isolated CPU environment: 3 preflight + 24 test-controller + 24 independent GP
control + 2 refined winner remeasurements. All 53 returned valid measurements;
API calls, local LLM loads and paid GPU launches were zero. This pilot uses
`TEST_CONTROLLER_NOT_LLM`, a deterministic software fixture, and establishes
integration only. It is not the paper's LLM method or a new efficacy result.
The previous 1,029-run numerical phase remains historical and unchanged.

| New measured arm | Attempts | Strictly feasible | First feasible within arm | Best feasible normalized FoM |
|---|---:|---:|---:|---:|
| Test controller (random then GP) | 24 | 7 | 13 | 3.400767279 |
| Independent full-domain GP | 24 | 7 | 1 | 3.400767279 |

The fixture starts inside indices 1..7; the GP control starts on the full 0..8 grid.
Their initial domains differ, so first-feasible counts do **not** establish model
or method superiority. Both selected [0,0] (base widths 0.84/0.84, physical widths
16.8/16.8 um), and each was independently resimulated at the finer transient step.
Independent exported-vector reconstruction gave 23.373441 dB, 20.588637 ps,
41.722106 uW, normalized FoM 3.401252277: all original strict constraints pass.
Do not compare this small result against a hidden historical oracle.

At center widths [4,4], corrected preflight reconstruction gave 23.819049 dB,
18.416472 ps, 65.825823 uW: power violates the original <50 uW limit even though
normalized FoM exceeds 1. Feasibility therefore checks every source clause.
The original source deck, paired-edge/time-weighted correction, and refined
correction were all newly measured and retained separately.

## What is now connected

`bridge.py` passes public circuit context to a controller protocol, validates its
complete active/fixed domains and supported random/GP decision, selects unseen
points, renders the original topology, launches native ngspice, parses scaled
measurements, scores original strict targets and sends actual measured feedback
into outer regeneration. The fixture consumes twelve new measured rows before
changing its central domain to the released full grid, then dispatches twelve GP
proposals. Five fixture calls are preserved with requests/raw/validated responses;
no fixture output is labeled a model result. Independent GP control has fresh
history and never enters controller feedback.

The API adapter wrapper is prepared but has no live executable route here. It
requires separately authorized runtime settings, public payload scope and a local
model-specific chat token counter. See [API_PILOT_PROPOSAL.md](API_PILOT_PROPOSAL.md)
for exact capabilities, example public content and request/token ceilings.

## Checks and evidence

- Nine initial offline boundary tests passed on the isolated experiment Python.
  Five additional tests passed there for early stop, archived invalid batch,
  synthetic-transport JSON correction, input-token gate and ten-request gate.
  Network access is prohibited in transport fixture tests.
- The raw APRIL audit independently rescored all 53 attempts, verified write-before-
  launch IDs, deck hashes, unique arm points, past-valid-only GP training counts,
  original strict constraints and exact twelve-row reflection provenance. Four
  corrected/refined waveform exports agree within 0.001 physical metric unit.
- The Mac public verifier checks all 247 exported artifacts against the export
  manifest, independently rescores 53 raw logs and rechecks four waveforms.
  `evidence/run_01/checks.json`, `preflight_checks.json`, requests, both histories,
  all decks/stdout/stderr, five DC/transient vector pairs (four corrected/refined
  pairs independently checked) and frozen protocol are included.
- [RESOURCE_LEDGER.json](RESOURCE_LEDGER.json) records approximately 8.96 simulator
  CPU seconds and 9.20 simulator wall seconds (summed child runs), explicit
  affinity 24..31, serial processes and one numerical-library thread. These are
  child timings; coordinator/import/audit time is not included in those totals.

The exact code/protocol commit frozen before the first circuit launch was
`2c0c113b655703d3c28a23dcc6cffdb7d5bc8f09`. Files used in execution are hash-listed
in `evidence/run_01/protocol.json`; additional export/test tooling was added only
after measurements, without rerunning or changing those frozen inputs.

## Portable evidence and licenses

`export_public.py` exports only JSON/text/log/vector/deck evidence. It replaces the
private simulator and PDK-selector paths with `NGSPICE` and `MODEL_SELECTOR`.
Original runtime artifact hashes and public hashes/byte counts are both preserved
in `EXPORT_MANIFEST.json`; `attempt.json` keeps its original deck hash. Therefore
raw `check.py` audits the private originals, while `verify_public.py` audits the
portable public package. No scientific numbers changed. Private originals remain
at the experiment's original run root. No metadata sidecars, credentials, runtime
configuration, environments, binaries, source archives or model weights are added.

The observed untracked AppleDouble directory sidecar was identified by file type
and moved outside the repository, without publishing or deleting its contents.
The project ignore rules exclude `._*`; future tar transfers use
`COPYFILE_DISABLE=1` and explicit exclusions. Existing Apache-2.0 SKY130 license/
notices remain intact. No new upstream source or model bodies are redistributed;
AutoSizer code/benchmark license is still unconfirmed, as documented in the asset
audit, and no new license grant is asserted.

## Remaining scientific work

Select and authorize an API backend and spend cap, run a fresh frozen API protocol
with genuine model understanding/domain/decision/reflection outputs, then assess
schema/physical quality and substitutions before scaling tasks or seeds. One
inverter/seed with synthetic decisions cannot establish those model capabilities.
