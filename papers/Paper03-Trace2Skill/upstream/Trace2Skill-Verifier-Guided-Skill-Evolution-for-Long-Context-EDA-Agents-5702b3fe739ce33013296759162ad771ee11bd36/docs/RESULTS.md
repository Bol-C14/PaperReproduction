# Results and packaged evidence

The release includes sanitized numerical records and two content-free action
traces, not raw conversations or hidden verifier content. Run:

```bash
python3 scripts/validate_paper_results.py
```

The validator recomputes every aggregate below from JSONL/CSV evidence.

In the cached rollout evidence, `repeat_index` is the zero-based physical row
ordinal within each archived per-individual JSONL, not the scheduler's
`_ng_rollout_index`. Concurrent completion can permute those four identifiers;
the rewards and all aggregates are unaffected. The action-trace examples
retain the scheduler repeat and record the storage ordinal separately.

| Task | C3 passes / 80 | C4 passes / 80 |
|---|---:|---:|
| `fpga_nes_0003` | 65 | 79 |
| `verilog_pcie_0004` | 0 | 1 |
| `802.11a_0001` | 0 | 11 |
| `verilog_pcie_0028` | 28 | 9 |
| `NoobsCpu-8bit_0002` | 0 | 35 |
| `rvx_0004` | 0 | 0 |
| `async-fifo_0003` | 80 | 80 |
| `schoolMIPS_0012` | 0 | 0 |
| **Total** | **173 / 640 (27.03%)** | **215 / 640 (33.59%)** |

C4 recorded 1,130 runtime-feedback attempts: 1,052 verifier executions, 66
budget rejections, and 12 edit/compile gate rejections. The enforced maximum
was three executions per rollout.

## Quality fields

- `SelectQ`: the combined utility used for candidate selection.
- `SkillQ`: semantic quality/retention of the candidate skill.
- `AgentProgressQ`: execution-progress behavior score.
- `AgentVarianceQ`: consistency across repeated rollouts.
- `AgentAdherenceQ`: skill-adherence score.

The archived candidate metadata had no skill-monitor observations, so
`AgentAdherenceQ` used its default value of 1.0 for all 320 C3/C4 candidate
records. It did not rank candidates and must not be interpreted as an observed
adherence measurement.

The historical AgentProgressQ computation is outcome-aware: a successful final
reward sets several subcomponents to one. The packaged 96-rollout audit also
provides a strict behavior-only post-hoc score. Its AUC is 0.678, compared with
0.982 for the historical outcome-aware score.

Conditions C1 and C2 are not included in the functional evidence because exact
completed-run artifacts were not preserved; draft placeholder values were
withdrawn. C3 and C4 are the supported paper-result conditions.

## Evidence layout

- `artifacts/paper-results/evidence/{c3,c4}/rollouts.jsonl`: one sanitized row
  per rollout.
- `quality_records.jsonl`: one row per generation/individual with all five
  quality fields.
- `runtime/`: path-free call counts, retry coordinates, and launch settings.
- `agentq96/`: outcome-aware and strict behavior-only progress audit.
- `lineage_example/`: one abstract, sanitized lineage record.
- `oss24/`: contextual 24-task outcome table.
- `artifacts/rollout-examples/`: one real C3 failure and one real C4 pass,
  represented as ordered tool/action metadata plus provenance commitments.
