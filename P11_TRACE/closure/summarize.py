"""Generate tables from all prespecified comparisons; no model fitting or selection."""
import json
from pathlib import Path
import statistics as s
import hashlib
import importlib.metadata as metadata
import os
import sys

R=Path(__file__).resolve().parent
rows=json.loads((R/'summary.json').read_text())
log=[json.loads(l) for l in (R/'RESULTS.jsonl').read_text().splitlines()]
assert len(rows)==48
seeds=[2026,2027,2028]
families=['ripple_carry','comparator','priority_selector','reconvergent_mux']
groups=[('scratch_pretrain','direct'),('scratch_pretrain','fsl'),('transfer_official','fsl'),('transfer_random','fsl')]
lines=['# TRACE closure results — all prespecified comparisons','',
'FSL means function-shift learning. Few-shot support adaptation is a separate added evaluation; official checkpoint comparisons are transfer with unknown inherited pretraining cost.','',
'Primary score is the mean terminal-output MAE across four held-out families; ± is sample SD across three seeds, not a confidence interval. Family data and seeds are paired. No best-seed or best-family selection.','',
'| Track | Stage | Macro output MAE ± SD | Macro non-PI MAE ± SD | Worst family output MAE | Adaptation time per family (s) |',
'|---|---|---:|---:|---:|---:|']
aggregates=[]
for track,arm in groups:
    selected=[x for x in rows if x['track']==track and x['arm']==arm]
    assert len(selected)==12
    for stage in ['no_adapt','adapt']:
        out=[s.mean(x[stage]['output_mae'] for x in selected if x['seed']==seed) for seed in seeds]
        node=[s.mean(x[stage]['node_mae'] for x in selected if x['seed']==seed) for seed in seeds]
        worst=max(s.mean(x[stage]['output_mae'] for x in selected if x['family']==family) for family in families)
        adaptation=s.mean(x['adaptation']['seconds'] for x in selected) if stage=='adapt' else 0.
        aggregate=dict(track=track,arm=arm,stage=stage,output_mae_mean=s.mean(out),output_mae_sd=s.stdev(out),
                       node_mae_mean=s.mean(node),node_mae_sd=s.stdev(node),worst_family_output_mae=worst,
                       mean_adaptation_s=adaptation,seed_output_mae=out)
        aggregates.append(aggregate)
        lines.append(f'| {track}/{arm} | {stage} | {s.mean(out):.6f} ± {s.stdev(out):.6f} | {s.mean(node):.6f} ± {s.stdev(node):.6f} | {worst:.6f} | {adaptation:.3f} |')
local=[x for x in log if x['phase']=='local_only']
lines+=['',f"Local-only (no learned weights): macro output MAE **{s.mean(x['metrics']['output_mae'] for x in local):.6f}**, macro non-PI MAE **{s.mean(x['metrics']['node_mae'] for x in local):.6f}**.",
'', '| Track | Family | Output MAE no-adapt → adapt (seed mean) | Non-PI MAE no-adapt → adapt | FSL oracle-predecessor output MAE after adaptation |',
'|---|---|---:|---:|---:|']
for track,arm in groups:
    for family in families:
        sub=[x for x in rows if x['track']==track and x['arm']==arm and x['family']==family]
        def mean(stage,key):return s.mean(x[stage][key] for x in sub)
        teacher=f"{mean('adapt','teacher_output_mae'):.6f}" if arm=='fsl' else 'n/a'
        lines.append(f"| {track}/{arm} | {family} | {mean('no_adapt','output_mae'):.6f} → {mean('adapt','output_mae'):.6f} | {mean('no_adapt','node_mae'):.6f} → {mean('adapt','node_mae'):.6f} | {teacher} |")
lines+=['','## Diagnosis without metric selection','',
'FSL teacher-predecessor scores below use true intermediate marginals. They isolate one-step residual error and are unavailable at real inference. A difference from recursive output error is evidence consistent with propagation; it is not an independently controlled causal attribution.',
'', '| FSL track | Stage | Recursive output MAE | Oracle-predecessor output MAE | Mean absolute recursive–oracle prediction gap | Outside-range nodes / evaluated nodes |',
'|---|---|---:|---:|---:|---:|']
for track,arm in groups:
    if arm!='fsl':continue
    sub=[x for x in rows if x['track']==track and x['arm']=='fsl']
    for stage in ['no_adapt','adapt']:
        lines.append(f"| {track} | {stage} | {s.mean(x[stage]['output_mae'] for x in sub):.6f} | {s.mean(x[stage]['teacher_output_mae'] for x in sub):.6f} | {s.mean(x[stage]['recursive_teacher_gap_output'] for x in sub):.6f} | {sum(x[stage]['outside_unit'] for x in sub)} / {sum(x[stage]['nodes'] for x in sub)} |")
lines+=['', 'Per-depth MAE/teacher MAE and counts are retained for every seed/family/stage in summary.json. Per-parent records and raw predictions are retained in predictions/.',
'', '## Ordered-role controls','',
'Exact MUX target delta is 0.54 for the select/data swap; exact AND target delta is zero. Predictions below are reported, not asserted accurate.',
'', '| Track | Mean MUX prediction delta | Mean absolute AND port-swap difference |',
'|---|---:|---:|']
for track,arm in groups:
    sub=[x for x in rows if x['track']==track and x['arm']==arm]
    lines.append(f"| {track}/{arm} | {s.mean(x['role_control']['mux_prediction_delta'] for x in sub):.6f} | {s.mean(x['role_control']['and_prediction_swap_abs'] for x in sub):.6f} |")
complete=next(x for x in log if x['phase']=='complete')
pre=[x for x in log if x['phase']=='pretrain']
lines+=['','## Cost','',f"Valid run: {complete['wall_s']:.2f} s wall, {complete['cpu_s']:.2f} s process CPU, peak RSS {complete['peak_rss_kib']} KiB, {complete['optimizer_steps']} optimizer updates, one CPU thread, CUDA initialized={complete['cuda_initialized']}.",
 f"Six 240-update pretraining runs consumed {sum(x['seconds'] for x in pre):.2f} s; 48 twenty-update family adaptations consumed {sum(x['adaptation']['seconds'] for x in rows):.2f} s. Saved batched-query inference times exclude adaptation, exact-label generation and model loading.",
 f"Batched inference (48 query graphs/family) median {s.median(x[stage]['inference_s'] for x in rows for stage in ['no_adapt','adapt']):.4f} s. All models have417,761 parameters (including source unused parameters).",
'','Two interrupted harness attempts are archived and excluded from aggregate scores. Their consumed resources are additional to this valid-run budget; see ATTEMPTS.jsonl and RESOURCE_LEDGER.md. Original checkpoint inherited training cost is unknown. No new package/dataset/checkpoint downloads or paid resources were used in this tranche.']
(R/'RESULTS_SUMMARY.md').write_text('\n'.join(lines)+'\n')
(R/'aggregate.json').write_text(json.dumps(aggregates,indent=2)+'\n')
# Source/version and artifact identity record; do not include generated self hash.
version=dict(python=sys.version,torch=metadata.version('torch'),numpy=metadata.version('numpy'),
 source_commit='b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70',base_commit='114072d8656683c528fd2f8fda20fb7d58d9f062',
 official_pm_checkpoint_sha256=hashlib.sha256((R/'official_pm_probability.pth').read_bytes()).hexdigest(),
 protocol_sha256=hashlib.sha256((R/'PROTOCOL.md').read_bytes()).hexdigest(),
 frozen_data_sha256=hashlib.sha256((R/'frozen_families.json').read_bytes()).hexdigest(),
 source_sha256=hashlib.sha256((R/'official_pm_source.py').read_bytes()).hexdigest(),
 harness_sha256=hashlib.sha256((R/'run_closure.py').read_bytes()).hexdigest(),
 commands=['OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../pilot/.venv/bin/python run_closure.py',
 '../pilot/.venv/bin/python verify_closure.py','OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../pilot/.venv/bin/python check_pipeline_controls.py','../pilot/.venv/bin/python summarize.py'],
 no_new_installations=True,no_new_asset_downloads=True,public_paper_page_read='https://arxiv.org/html/2509.21886v3')
(R/'SOURCE_VERSIONS.json').write_text(json.dumps(version,indent=2)+'\n')
print('\n'.join(lines[:18]))
