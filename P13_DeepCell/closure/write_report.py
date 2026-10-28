"""Write source-backed final experiment report; no selection or model execution."""
import collections,datetime,hashlib,json,pathlib,time
ROOT=pathlib.Path(__file__).resolve().parent


def load(path):return json.loads((ROOT/path).read_text())


def main():
    c=load('results/main/controlled_comparison.json');f=load('results/full_token/controlled_comparison.json')
    independent=load('results/main/independent_verification.json');fullcheck=load('results/full_token/independent_verification.json')
    ext=load('external/results/flow_results.json');full_ext=load('external/results/full_token/flow_results.json')
    negative=load('external/results/negative_formal_control.json');public=load('results/main/public_input_noninterference.json')
    cost=load('costs.json');full_summary=load('results/full_token/summary.json')
    extra_updates=sum(v['successful_optimizer_updates'] for v in f['arms'].values())
    cost.update({'completed_all_experiments_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'full_token_process_seconds':full_summary['elapsed_seconds'],
       'full_token_process_peak_rss_kib':full_summary['peak_rss_kib'],'full_token_successful_updates':extra_updates,
       'all_successful_main_and_fidelity_updates':c['total_successful_main_updates']+extra_updates,
       'total_optimizer_updates_including_failed_and_preflight':c['total_successful_main_updates']+extra_updates+c['failed_attempt_extra_updates']+3,
       'full_token_public_flow_seconds':full_ext['seconds'],'public_ABC_build_and_original_extension_kept':True})
    start=datetime.datetime.fromisoformat(cost['started_main_utc'].replace('Z','+00:00'));end=datetime.datetime.fromisoformat(cost['completed_all_experiments_utc'].replace('Z','+00:00'))
    cost['total_main_start_to_all_experiments_seconds']=(end-start).total_seconds();assert cost['total_main_start_to_all_experiments_seconds']<2700
    (ROOT/'costs.json').write_text(json.dumps(cost,indent=2)+'\n')
    primary=[]
    for arm,x in c['arms'].items():primary.append(f"| `{arm}` | {x['successes']}/{x['test_trials']} ({100*x['success_at3']:.2f}%) | {x['stage2_test_probability_mae']:.4f} | {x['stage2_test_masked_hf_l1']:.4f} |")
    faithful=[]
    for arm,x in f['arms'].items():faithful.append(f"| `{arm}` | {x['successes']}/{x['trials']} ({100*x['success_at3']:.2f}%) | {x['probability_mae']:.4f} | {x['functional_RE']:.4f} |")
    full_learned=[x for x in full_ext['records'] if x['mode'].startswith(('paired_pretrained','pm_only'))]
    full_real_success=sum(x['success'] for x in full_learned)
    pp=c['paired_differences']['pm_only'];ci=[100*x for x in pp['parent_cluster_bootstrap_95CI']]
    fullci=[100*x for x in f['parent_cluster_bootstrap_95CI']]
    report=f'''# DeepCell: closest feasible CPU methodology closure

Implemented and executed a learned representation-to-functional-ECO loop, with independent patch checking and a real public ABC/netlist extension. **The controlled runs do not establish a useful paired-view pruning advantage.** They establish executable learning, patch synthesis and correctness checks; the paper's original accuracy, runtime and technology-mapping results remain unreproduced.

The minimum multiview mechanism has been independently reconstructed and run. The historical asset audit remains valid for the original release; the full-paper route still has L3 asset/integration gaps. No GPU/Runpod, paid resource, external model API, credentials, gated agreement, upload, push or PR was used.

## Executed loop

1. Use unchanged official 128+128-dimensional PM/AIG DG2 encoders. PM checkpoint loads its full 56 state tensors; AIG loads all 64 encoder/readout tensors after explicitly removing the unprovided auxiliary connectivity head (the full class still lacks 16 tensors). Frozen AIG, trainable PM.
2. Generate 216 semantically verified paired graphs from 108 distinct six-input parent functions. Training 144 variants/72 parents from parity/muxbank/arithmetic; validation 24/12 from conditional; testing 48/24 from majority/comparator. Families, parent descendants and full truth functions are disjoint across splits. Every case agrees with separate Boolean expressions and AIG evaluation on 64 input assignments. Synthetic cells and SOP lowering substitute for original Liberty/commercial mapping assets.
3. Probability adaptation 2 epochs; four-hop cone MCM 6 epochs; ECO finetuning 6 epochs, batch 4, Adam 1e-4. Fusion retains the full 4-layer, 8-head, 256-channel Transformer shape. All 5 primary arms use both seeds 208/209 with no early stopping, tuning or winner selection.
4. Erase one known cell's pins/function from the observed PM. Refine with the golden AIG, learn candidate ancestry ranking with BCE plus teacher reconstruction, and send ranked candidates to a separate exact repair engine. The engine derives patch requirements by comparing whole-circuit outputs under patch 0/1 to golden outputs. It receives no hidden golden-PM function/pin/ancestry labels or internal cross-view map at inference.
5. Synthesize explicit AND/NOT patches when top-three prefix constraints are feasible. Independently evaluate all resulting full circuits and retain failures. Oracle direct-fanin and PI fallback are separately labelled, privileged/correctness baselines.

Source, configuration, data/checkpoint hashes, complete curves and failed-attempt logs are retained. [Protocol](closure/PROTOCOL.md), [correctness amendment](closure/AMENDMENTS.md), [coverage map](closure/MECHANISM_COVERAGE.md), [replay commands](closure/REPLAY.md), and [command ledger](closure/COMMANDS.md) are the inspectable record.

## Primary controlled comparison

The first declared experiment reconstructs functional channels. The stage2 probability MAE uses common exact-probability units; reconstruction L1 is in each model's learned latent space and does not alone demonstrate semantic quality.

| Arm | Held-out ECO success at3 | Stage2 probability MAE | Functional reconstruction L1 |
|---|---:|---:|---:|
{chr(10).join(primary)}

Each arm has 96 trials = 48 cases x 2 seeds; these are **24 parent-function units**, not 96 independent designs. Paired minus PM-only success is {100*pp['paired_minus_control_success_difference']:.2f} percentage points; the descriptive parent-cluster bootstrap95% interval is [{ci[0]:.2f}, {ci[1]:.2f}] points. Only two held-out families are covered.

On 48 test cases, fixed random ranking solves 2/48, reverse-topological 13/48, privileged direct-fanin oracle 48/48, and the separate six-PI fallback 48/48. The oracle confirms that feasible compact repairs exist; it does not represent learned performance. The learned paired model averages about {c['arms']['paired_pretrained']['ranking_ms']:.1f}ms ranking plus {c['arms']['paired_pretrained']['solver_ms']:.1f}ms exact solving here. These tiny workloads and overlapping ABC build do not support a speedup claim.

Wrong-parent AIG counterfactuals change 72/96 rankings but solve 7/96 versus 6/96 with correct views. That establishes input sensitivity without a useful paired-context benefit. Shuffling also changes context length and the shared PI initialization relation, so this is a broad corruption control. Random-start encoders receive the same PM optimization schedule and a frozen random AIG; their higher probability error measures a warm-start contribution in this setup, not a clean equal-pretraining comparison or demonstrated downstream benefit.

## Full-token source-fidelity sensitivity

The public trainer applies reconstruction L1 to full returned structural+functional tokens. A separately declared sensitivity therefore repeats paired and PM-only for both seeds with the full 256-channel MCM and ECO teacher target, leaving the primary experiment intact. It is post-primary, predeclared before these four runs, and never used to select a better result.

| Full-token arm | Held-out ECO success at3 | Stage2 probability MAE | Functional RE metric |
|---|---:|---:|---:|
{chr(10).join(faithful)}

Full-token paired minus PM-only success is {100*f['paired_minus_PM_only_success_difference']:.2f} points, with descriptive 24-parent bootstrap interval [{fullci[0]:.2f}, {fullci[1]:.2f}]. See [separate protocol](closure/FULL_TOKEN_PROTOCOL.md), [source diff](closure/full_token_changes.patch), and [full-token results](closure/results/full_token/controlled_comparison.json). No primary-control row is silently relabelled as full-token training.

## Independent correctness and real tool execution

The separate checker imports neither trainer nor solver. It executes patch gates recursively, evaluates PM cell Boolean operations directly without trusting stored cell truth tables, and compares whole-circuit outputs with separately generated parent truth signatures. **All {independent['patches_checked']} primary/control/baseline patches ({independent['primary_input_assignments_checked']:,} assignments) and all {fullcheck['patches_checked']} full-token patches ({fullcheck['primary_input_assignments_checked']:,} assignments) pass.** Deliberately inverted patches produce counterexamples. All {public['cases_checked']} principal held-out rankings and repairs are reproduced after removing hidden golden PM, cell function/pins, internal correspondence, ancestry/probability labels and family-oracle specification from inputs. [Primary replay evidence](closure/results/main/independent_verification.json), [full-token replay](closure/results/full_token/independent_verification.json), [inference separation](closure/results/main/public_input_noninterference.json).

A separately bounded public-flow extension builds upstream ABC commit`ba65576141a5a0f605d2876ad5041e3ec7dfbf59` locally. It reads EPFL `ctrl.blif` from benchmark commit`82d8cc6910419298e713a46644ed59fd3df53038`, maps with an explicit unit-cost teaching genlib, and converts PM back through actual`strash`. Parsed views contain 167 PM and 266 explicit AIG nodes, 7 inputs and 26 outputs. All 128 assignments agree with the original public BLIF; **ABC CEC proves mapping equivalence**.

Four nontrivial patch sites are fixed at index quantiles before model scoring. No model is trained on this public circuit. Primary frozen models solve 0/32 top-three trials across 8 model/seed combinations; random and reverse-topological controls solve 0/4 each. Direct-fanin oracle and seven-PI fallback each emit 4/4 repairs; **all 8 actual patch BLIFs pass 128-assignment checks and ABC CEC against the original public circuit**. Full-token frozen paired/PM-only models solve{full_real_success}/{len(full_learned)} additional trials at the same sites; their complete results and baseline proofs are retained separately. A deliberately inverted public output is confirmed **NOT EQUIVALENT** by ABC with a counterexample; the harness checks proof text because ABC can return process exit 0 for failed equivalence.

This is an actual baseline mapping/functional repair flow, not the authors' DeepCell-enhanced`&nf` or`runeco` implementation. Teaching library costs/delays have no foundry significance, so no PPA/physical timing ECO result is claimed. Original pretraining exposure to EPFL remains unknown even though this CPU training used only synthetic families. [Public flow](closure/external/results/flow_results.json), [full-token public flow](closure/external/results/full_token/flow_results.json), [negative formal control](closure/external/results/negative_formal_control.json), and emitted repair BLIFs are saved locally.

## Costs, errors and remaining gaps

Across 14 successful model/seed runs there are {cost['all_successful_main_and_fidelity_updates']:,} optimizer updates, plus 504 duplicate failed-attempt updates and 3 preflight updates. Main resumed process: {cost['resumed_main_process_seconds']:.1f}s and {cost['main_process_peak_rss_kib']/1024:.1f}MiB peak RSS; full-token process: {cost['full_token_process_seconds']:.1f}s and {cost['full_token_process_peak_rss_kib']/1024:.1f}MiB. ABC build: {cost['abc_build_seconds']:.1f}s with two jobs. Observed environment-wide memory peak including build is {cost['observed_cloud_cgroup_memory_peak_bytes']/2**30:.2f}GiB under the existing 16 GiB limit. This phase downloads only {cost['additional_download_payload_bytes']:,} bytes of public ABC source/README/benchmark payload, plus small unmetered git metadata. No new model weights or system installation. Costs overlap; adding wall times would overstate elapsed time. [Costs](closure/costs.json).

Two errors were repaired and preserved: verifier scheduling of legal later-serialized wires, and ABC's default LUT BENCH output requiring documented`write_bench -l` for the AND/NOT reader. These were correctness/format repairs, not response to model quality. Earlier IEEE/arXiv/wheel access restrictions were not bypassed; this phase encountered no new access denial.

The remaining boundary is original-result fidelity and effective transfer, not an inability to fit the model. Exact original paired corpus/split/parent lineage, Liberty/pin/tool recipes, original ECO corruption/label definitions, author-finetuned heads and modified ABC integration are still unverified. For mapping, the actual load/cell-type head, modified`&nf`, library corners and constraints remain essential. A GPU would not supply those assets; none is requested.

Our explicit substitutions include a single-cell cut, interpreted fan-in ancestry labels, tiny exact enumeration instead of SAT-scale ECO, reduced training, deterministic per-case/shared paired PI basis and synthetic teaching libraries. Low reconstruction error can reflect moving teacher embeddings and generic reconstruction; it did not establish a paired-view advantage here. The execution loop is closed and verified on these domains. Original paper performance/generalization claims remain open. Exact provision targets are listed in the [coverage/gap map](closure/MECHANISM_COVERAGE.md). Stop after this declared comparison and fidelity sensitivity.
'''
    for old,new in [('commit`','commit `'),('actual`','actual `'),('enhanced`','enhanced `'),('or`','or `'),('documented`','documented `'),('modified`','modified `'),('solve0/','solve 0/'),('bootstrap95%','bootstrap 95%'),('20.8ms','20.8 ms'),('2.0ms','2.0 ms')]:report=report.replace(old,new)
    report=report.replace('## Executed loop','Reference: [paper v2](https://arxiv.org/html/2502.06816v2), [official fusion model](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_model.py), [official reconstruction trainer](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_trainer.py). Title history and original asset evidence remain in [ASSET_AUDIT.md](ASSET_AUDIT.md).\n\n## Executed loop')
    (ROOT.parent/'CLOSURE_REPORT.md').write_text(report)
    summary={'status':'completed_controlled_independent_methodology_loop','original_paper_results_reproduced':False,'minimum_multiview_core_executed':True,
      'paired_pruning_advantage_established':False,'primary':c['arms'],'full_token':f,'independent_verification':{k:independent[k] for k in ['patches_checked','primary_input_assignments_checked','all_passed']},
      'full_token_independent_verification':{k:fullcheck[k] for k in ['patches_checked','primary_input_assignments_checked','all_passed']},
      'public_primary_learned_top3_successes':0,'public_primary_learned_trials':32,'public_full_token_learned_top3_successes':full_real_success,'public_full_token_learned_trials':len(full_learned),
      'public_primary_actual_equivalent_patches':8,'public_negative_equivalence_control_confirmed':negative['expected_non_equivalence_confirmed'],
      'resources':cost,'remaining_gaps':['original paired corpus/provenance/library preprocessing','original ECO corruption/labels/fine-tuned head/ABC integration','actual mapping head/modified &nf/Liberty corners/constraints']}
    (ROOT/'FINAL_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
    assets=ROOT.parent/'assets.json';a=json.loads(assets.read_text());a['later_methodology_closure']={k:v for k,v in summary.items() if k not in ['primary','full_token','resources']};a['later_methodology_closure']['report']='CLOSURE_REPORT.md';assets.write_text(json.dumps(a,indent=2)+'\n')
    print('Wrote CLOSURE_REPORT.md and closure/FINAL_RESULTS.json')


if __name__=='__main__':main()
