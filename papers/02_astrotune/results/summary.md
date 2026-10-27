# Recomputed results

All QoR values minimize. 3 seeds are stochastic search runs; deterministic repeats are separate. Main cases and prospectively added div16 stress case are separate strata.

| Design | Method | n | Mean QoR | Min–max | Calls/run | Unique full/run | Prunes total |
|---|---|---:|---:|---|---|---|---:|
| adder_32bit | ast_gp_all | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | ast_single | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | ast_tournament | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | ast_tournament_no_prune | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | ast_tpe_all | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | fusion_control_single | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | gp_single | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | numeric_single | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| adder_32bit | random | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–13 | 0 |
| adder_32bit | random_inclusive | 3 | 0.98566514 | 0.98566514–0.98566514 | 72–72 | 66–66 | 0 |
| adder_32bit | text_single | 3 | 0.98566514 | 0.98566514–0.98566514 | 18–18 | 12–12 | 0 |
| barrel_shifter | ast_gp_all | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | ast_single | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | ast_tournament | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | ast_tournament_no_prune | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | ast_tpe_all | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | fusion_control_single | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | gp_single | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | numeric_single | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| barrel_shifter | random | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–13 | 0 |
| barrel_shifter | random_inclusive | 3 | 0.99749059 | 0.99749059–0.99749059 | 72–72 | 66–66 | 0 |
| barrel_shifter | text_single | 3 | 0.99749059 | 0.99749059–0.99749059 | 18–18 | 12–12 | 0 |
| div_16bit | ast_tournament | 3 | 104.45314849 | 104.44752692–104.46403727 | 18–18 | 12–12 | 0 |
| div_16bit | ast_tournament_no_prune | 3 | 104.45314849 | 104.44752692–104.46403727 | 18–18 | 12–12 | 0 |
| div_16bit | ast_tournament_prune_probe | 1 | 104.44752692 | 104.44752692–104.44752692 | 18–18 | 12–12 | 2 |
| div_16bit | gp_single | 3 | 104.44752692 | 104.44752692–104.44752692 | 18–18 | 12–12 | 0 |
| div_16bit | random | 3 | 104.44764504 | 104.44752692–104.44788130 | 18–18 | 12–13 | 0 |
| div_16bit | random_inclusive | 1 | 104.44752692 | 104.44752692–104.44752692 | 72–72 | 66–66 | 0 |
| multi_pipe_8bit | ast_gp_all | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | ast_single | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | ast_tournament | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | ast_tournament_no_prune | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | ast_tpe_all | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | fusion_control_single | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | gp_single | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | numeric_single | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |
| multi_pipe_8bit | random | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–13 | 0 |
| multi_pipe_8bit | random_inclusive | 3 | 0.99898374 | 0.99898374–0.99898374 | 72–72 | 66–66 | 0 |
| multi_pipe_8bit | text_single | 3 | 0.99898374 | 0.99898374–0.99898374 | 18–18 | 12–12 | 0 |

## Actual execution ledger

```json
{
  "actual_eda_stage_attempts": 2684,
  "successful_stage_evaluations": 2680,
  "failed_stage_evaluations": 4,
  "phase_stage_attempts": {
    "main_search": 1620,
    "inclusive_random": 720,
    "stress_search": 216,
    "prune_branch_probe": 18,
    "legacy": 54,
    "pilot_debug": 8,
    "deterministic_repeat": 16,
    "posthoc_transfer": 32
  },
  "physical_global_unique_configs": 321,
  "global_unique_synth_configs": 42,
  "summed_eda_wall_s": 1959.7356702090046,
  "main_search_runs": 90,
  "stress_runs": 12,
  "sum_prunes": 2,
  "legacy_db_sha256": "2831f8f4802efc8b097c5722db6f1d6e732f6eb0db205354b9c81fb0f3962bd6",
  "no_online_llm_calls": true,
  "llm_calls": 0,
  "accounting_limits": "Original retrieval calls were outside per-search stopwatch. A separate fresh pass is reported explicitly as remeasurement. Inclusive wall is an estimate plus full one-use history cost, not a directly timed end-to-end measurement. Setup/download/model-attempt time is not fully instrumented; no walltime speedup conclusion is supported. Verification/tool setup executions are not EDA search calls."
}
```

`inclusive_calls` charges the ENTIRE 54-call donor database to each retrieval run. `random_inclusive` receives 72 online calls; ordinary runs receive 18 calls. The former is an EDA-count control, not walltime matching.
