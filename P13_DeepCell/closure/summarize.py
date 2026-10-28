"""Summarize frozen held-out results without model selection or retraining."""
import collections,datetime,hashlib,json,pathlib,statistics
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
ARMS=['paired_pretrained','pm_only','shuffled_aig','paired_random','no_mcm']


def main():
    directory=ROOT/'results/main';runs={a:[json.loads((directory/f'{a}_{seed}.json').read_text()) for seed in [208,209]] for a in ARMS}
    summaries={};byparent={}
    for arm,rs in runs.items():
        records=[(r['seed'],x) for r in rs for x in r['downstream']['test']['records']]
        parents=collections.defaultdict(list)
        for seed,x in records:parents[x['parent']].append(float(x['success']))
        byparent[arm]={p:np.mean(v) for p,v in parents.items()}
        families={f:np.mean([float(x['success']) for _,x in records if x['family']==f]) for f in ['majority','comparator']}
        variants={v:np.mean([float(x['success']) for _,x in records if x['id'].endswith(v)]) for v in ['v0','v1']}
        summaries[arm]={'test_trials':len(records),'successes':sum(x['success'] for _,x in records),
            'success_at3':float(np.mean([float(x['success']) for _,x in records])),
            'per_seed_success':{str(r['seed']):r['downstream']['test']['success_at3'] for r in rs},
            'per_family_success':{k:float(v) for k,v in families.items()},'per_variant_success':{k:float(v) for k,v in variants.items()},
            'average_precision':float(np.mean([x['average_precision'] for _,x in records])),
            'ancestry_recall_at3':float(np.mean([x['ancestry_recall_at3'] for _,x in records])),
            'stage2_test_probability_mae':float(np.mean([r['representation']['test']['probability_mae'] for r in rs])),
            'stage2_test_masked_hf_l1':float(np.mean([r['representation']['test']['masked_hf_l1'] for r in rs])),
            'effective_mask_fraction':float(np.mean([r['representation']['test']['effective_mask_fraction'] for r in rs])),
            'ranking_ms':1000*float(np.mean([x['ranking_seconds'] for _,x in records])),
            'solver_ms':1000*float(np.mean([x['seconds'] for _,x in records])),
            'optimizer_updates':sum(x['steps'] for r in rs for x in r['curves']),
            'successful_run_seconds':sum(r['seconds'] for r in rs)}
    rng=np.random.default_rng(331);deltas={}
    for control in ['pm_only','shuffled_aig','paired_random','no_mcm']:
        names=sorted(byparent['paired_pretrained']);diff=np.array([byparent['paired_pretrained'][p]-byparent[control][p] for p in names])
        samples=rng.choice(diff,size=(2000,len(diff)),replace=True).mean(1)
        deltas[control]={'paired_minus_control_success_difference':float(diff.mean()),'parent_cluster_bootstrap_95CI':[float(x) for x in np.quantile(samples,[.025,.975])],
            'independent_parent_units':len(names),'seeds':2,'bootstrap_resamples':2000,'interpretation':'descriptive clustered uncertainty; two held-out families only'}
    wrong=[x for r in runs['paired_pretrained'] for x in r['downstream']['test_wrong_view']['records']]
    paired=[x for r in runs['paired_pretrained'] for x in r['downstream']['test']['records']]
    wrong_diagnostic={'correct_view_success':float(np.mean([x['success'] for x in paired])),
        'wrong_view_success':float(np.mean([x['success'] for x in wrong])),
        'rankings_changed':sum(a['ranking']!=b['ranking'] for a,b in zip(paired,wrong)),
        'trials':len(wrong),'notes':'counterfactual same-split different-parent AIG; token length may differ, so this perturbs content and length'}
    baselines=json.loads((directory/'baselines.json').read_text());baseline_summary={k:{a:b for a,b in v.items() if a!='records'} for k,v in baselines.items()}
    failed=[]
    for line in (ROOT/'logs/main_attempt1_error.log').read_text().splitlines():
        try:r=json.loads(line)
        except ValueError:continue
        if r.get('arm')=='pm_only':failed.append(r)
    result={'arms':summaries,'paired_differences':deltas,'wrong_view_diagnostic':wrong_diagnostic,'baselines':baseline_summary,
            'total_successful_main_updates':sum(x['optimizer_updates'] for x in summaries.values()),
            'failed_attempt_extra_updates':sum(x['steps'] for x in failed),'failed_attempt_extra_epoch_seconds':sum(x['seconds'] for x in failed),
            'total_successful_run_seconds':sum(x['successful_run_seconds'] for x in summaries.values()),
            'aggregation':'96 trials per arm =48 held-out paired cases x2 seeds, clustered by24 parent functions; not96 independent designs',
            'main_complete_summary':json.loads((directory/'summary.json').read_text()),'analysis_used_for_selection':False}
    (directory/'controlled_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='main_complete_summary'},indent=2))


if __name__=='__main__':main()
