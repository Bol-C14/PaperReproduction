"""Summarize existing evidence; no model execution or optimization."""
import csv
import hashlib
import json
from pathlib import Path
import random
import statistics
from collections import Counter

R=Path(__file__).resolve().parent;C=R.parent
frozen=json.loads((C/'frozen_families.json').read_text());rows=frozen['rows'];results=json.loads((C/'summary.json').read_text())
seeds=[2026,2027,2028]
families=['ripple_carry','comparator','priority_selector','reconvergent_mux']

def budgets(group):
 return dict(graph_assignments=len(group),parents=len({r['parent'] for r in group}),
  known_PI_probabilities=6*len(group),non_PI_global_probability_labels=sum(len(r['nodes'])-6 for r in group),
  all_node_marginals_generated=sum(len(r['nodes']) for r in group))

train=[r for r in rows if r['split']=='train'];support=[r for r in rows if r['split']=='support'];query=[r for r in rows if r['split']=='query']
manifest=dict(frozen_protocol_sha256=frozen['protocol_sha256'],data_sha256=hashlib.sha256((C/'frozen_families.json').read_bytes()).hexdigest(),
 splits={s:budgets([r for r in rows if r['split']==s]) for s in ['train','support','query']},
 parents=frozen['parents'],sample_membership=[dict(id=r['id'],parent=r['parent'],family=r['family'],split=r['split'],non_PI_labels=len(r['nodes'])-6) for r in rows],
 support_per_family={f:budgets([r for r in support if r['family']==f]) for f in families},
 seed_sampling=[],adaptation_seed={seed:seed+100 for seed in seeds},
 interpretation='Direct and function-shift targets derive from the same fully node-labeled examples. PI marginals are known inputs. Query labels are for evaluation/diagnostics only. Adaptation uses16 assignments from2 parents per family, not16 scalar labels.',
 hyperparameter_boundary='Frozen before first data/model execution: architecture128/8heads/2layers/1round;240 train updates,20 support updates;Adam0.001/0.0001;batch16;seeds2026-2028. No HPO/early stop/best-test checkpoint. Some invalid-attempt query scores existed before correctness repairs; LR,step budget,data,architecture and metric were not changed from them.',
 transfer_boundary='Official checkpoint inherits unknown original pretraining data/compute. Only incremental20-update support budgets matched to random same-shape control; not equal total pretraining cost.')
for seed in seeds:
 rng=random.Random(seed);counts=Counter();scalar_presentations=0
 for step in range(240):
  batch=rng.sample(train,16)
  counts.update(r['id'] for r in batch);scalar_presentations+=sum(len(r['nodes'])-6 for r in batch)
 manifest['seed_sampling'].append(dict(seed=seed,train_updates=240,graph_presentations=3840,
  unique_graph_assignments_observed=len(counts),non_PI_scalar_supervision_presentations=scalar_presentations,
  same_for_arms=['direct','function_shift'],sample_presentation_counts=dict(counts),
  support_updates_each_family=20,support_graph_presentations_each_family=320,
  support_non_PI_scalar_supervision_presentations={f:20*manifest['support_per_family'][f]['non_PI_global_probability_labels'] for f in families}))
(R/'SPLIT_LABEL_BUDGET.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Self-contained per-family, per-seed paired observations, including all no-adapt controls.
fields=['seed','family','track','arm','output_no_adapt','output_adapt','node_no_adapt','node_adapt','adaptation_steps','adaptation_dropout_seed','adaptation_s']
with (R/'PAIRED_RESULTS.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
 for x in results:w.writerow(dict(seed=x['seed'],family=x['family'],track=x['track'],arm=x['arm'],
  output_no_adapt=x['no_adapt']['output_mae'],output_adapt=x['adapt']['output_mae'],
  node_no_adapt=x['no_adapt']['node_mae'],node_adapt=x['adapt']['node_mae'],adaptation_steps=20,
  adaptation_dropout_seed=x['seed']+100,adaptation_s=x['adaptation']['seconds']))
lines=['# Per-seed, per-family paired MAEs','',
'FSL means function-shift learning. Few-shot support adaptation is an added evaluation. Arrows denote0→20 support updates. O=terminal-output MAE; N=non-PI node MAE. Six decimals shown; exact floats in PAIRED_RESULTS.csv.','',
'| Seed | Family | Direct O | Function-shift O | Direct N | Function-shift N |','|---|---|---:|---:|---:|---:|']
for seed in seeds:
 for family in families:
  d=next(x for x in results if x['track']=='scratch_pretrain' and x['seed']==seed and x['family']==family and x['arm']=='direct')
  r=next(x for x in results if x['track']=='scratch_pretrain' and x['seed']==seed and x['family']==family and x['arm']=='fsl')
  def pair(row,key):return f"{row['no_adapt'][key]:.6f}→{row['adapt'][key]:.6f}"
  lines.append(f"|{seed}|{family}|{pair(d,'output_mae')}|{pair(r,'output_mae')}|{pair(d,'node_mae')}|{pair(r,'node_mae')}|")
lines+=['','## Transfer track — incremental support cost matched only','',
'The official checkpoint has unknown inherited pretraining cost. Zero-adapt official scores reuse identical weights, so zero seed SD there is not uncertainty.','',
'| Seed | Family | Official O | Random O | Official N | Random N |','|---|---|---:|---:|---:|---:|']
for seed in seeds:
 for family in families:
  a=next(x for x in results if x['track']=='transfer_official' and x['seed']==seed and x['family']==family)
  b=next(x for x in results if x['track']=='transfer_random' and x['seed']==seed and x['family']==family)
  lines.append(f"|{seed}|{family}|{pair(a,'output_mae')}|{pair(b,'output_mae')}|{pair(a,'node_mae')}|{pair(b,'node_mae')}|")
(R/'PAIRED_RESULTS.md').write_text('\n'.join(lines)+'\n')
versions=json.loads((C/'SOURCE_VERSIONS.json').read_text());resource=json.loads((C/'RESOURCE_ACCOUNTING.json').read_text())
steps=[json.loads(l) for l in (C/'training_steps.jsonl').read_text().splitlines()]
assert len(steps)==2400
counts=Counter(s['tag'] for s in steps)
assert all(c==240 if tag.endswith('_pretrain') else c==20 for tag,c in counts.items())
provenance=dict(final_run_source_commit='76e5cb1761ba775c0927b77c97456333a9931331',upstream_source_commit=versions['source_commit'],
 hashes=versions,config=dict(hidden=128,heads=8,transformer_layers=2,rounds=1,parameters=417761,
  optimizer='Adam',lr_train=.001,lr_adapt=.0001,betas=[.9,.999],eps=1e-8,weight_decay=0,
  train_steps=240,adapt_steps=20,batch_size=16,loss='L1 on all non-PI nodes',seeds=seeds,
  dropout_seed_train=seeds,dropout_seed_adapt=[s+100 for s in seeds],
  direct='sigmoid(unbounded readout)',function_shift='clamp(unbounded readout,-1,1), then inclusive recursive local function + shift; no final probability clamp',
  torch_threads=1,train_dropout='source defaults; Transformer0.1, feature/head MLP0.2',
  batchnorm='source BatchNorm; train mode during updates; eval mode for query; all parameters adapted'),
 fixed_lines=dict(unbounded_readout=[269,270],direct_vs_residual=[273,277],dropout_pairing=[311,314],training_target_and_clamp=[319,323]),
 original_harness_hash_verified=hashlib.sha256((C/'run_closure.py').read_bytes()).hexdigest()==versions['harness_sha256'],
 journal_sha256=hashlib.sha256((C/'training_steps.jsonl').read_bytes()).hexdigest(),updates_by_tag=dict(counts),
 failures=json.loads('['+','.join((C/'ATTEMPTS.jsonl').read_text().splitlines())+']'),resource_accounting=resource,
 setup_cost='Closure reused existing pinned venv; no installation/download. Earlier CPU setup logs and resource ledger retained separately; historical setup process CPU not instrumented.',
 source_vs_port='Deepest-level loop bound is upstream. Direct-clamp and dropout-seed bugs are local harness-only and invalid attempts were excluded. No original weights or source classes were edited.')
assert provenance['original_harness_hash_verified']
(R/'FINAL_RUN_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps(dict(split_budgets=manifest['splits'],support=manifest['support_per_family'],sampling=[{k:v for k,v in x.items() if k not in ['sample_presentation_counts']} for x in manifest['seed_sampling']]),indent=2))
