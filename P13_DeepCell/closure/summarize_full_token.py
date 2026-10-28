"""Separately report source-loss fidelity sensitivity, no result selection."""
import collections,json,pathlib,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent

def main():
    folder=ROOT/'results/full_token';out={};by_parent={}
    for arm in ['paired_pretrained','pm_only']:
        rs=[json.loads((folder/f'{arm}_{s}.json').read_text()) for s in [208,209]]
        rows=[x for r in rs for x in r['downstream']['test']['records']];parents=collections.defaultdict(list)
        for x in rows:parents[x['parent']].append(float(x['success']))
        by_parent[arm]={p:np.mean(v) for p,v in parents.items()}
        out[arm]={'trials':len(rows),'successes':sum(x['success'] for x in rows),'success_at3':float(np.mean([x['success'] for x in rows])),
          'per_seed_success':{str(r['seed']):r['downstream']['test']['success_at3'] for r in rs},
          'probability_mae':float(np.mean([r['representation']['test']['probability_mae'] for r in rs])),
          'functional_RE':float(np.mean([r['representation']['test']['masked_hf_l1'] for r in rs])),
          'average_precision':float(np.mean([x['average_precision'] for x in rows])),
          'successful_optimizer_updates':sum(x['steps'] for r in rs for x in r['curves']),
          'successful_run_seconds':sum(r['seconds'] for r in rs)}
    delta=np.array([by_parent['paired_pretrained'][p]-by_parent['pm_only'][p] for p in sorted(by_parent['paired_pretrained'])]);rng=np.random.default_rng(331)
    boot=rng.choice(delta,size=(2000,len(delta)),replace=True).mean(1)
    report={'status':'separate_post_primary_fidelity_sensitivity','objective':'full256-channel MCM and ECO teacher reconstruction; all other settings unchanged','arms':out,
      'paired_minus_PM_only_success_difference':float(delta.mean()),'parent_cluster_bootstrap_95CI':[float(x) for x in np.quantile(boot,[.025,.975])],
      'used_for_selection':False,'independent_parent_units':len(delta)}
    (folder/'controlled_comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
