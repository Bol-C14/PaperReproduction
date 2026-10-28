"""Recompute paired comparisons and complete resource inventory from saved rows."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent


def rows(name):return [json.loads(s) for s in (ROOT/'runs'/name/'RESULTS.jsonl').read_text().splitlines()]


def main():
    primary=('width_matrix1','integrated_matrix1') if (ROOT/'runs/integrated_matrix1/SUMMARY.json').exists() else ('dag_matrix1','live_matrix1')
    baseline=rows(primary[0]);live=rows(primary[1]);paired=[]
    table=['| Kernel | Bits | Policy | Agnostic gates/depth | Context gates/depth | No VRA gates/depth | Live-filter gates/depth |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for r in baseline:
        if r['mode']!='agnostic':continue
        match=lambda t: (t['name'],t['width'],t['weight'])==(r['name'],r['width'],r['weight'])
        c=next(t for t in baseline if match(t) and t['mode']=='context')
        n=next(t for t in baseline if match(t) and t['mode']=='context_no_vra')
        l=next(t for t in live if match(t))
        mm=lambda t:t['evaluation']['mapped']
        a,b,d,e=map(mm,[r,c,n,l]);paired.append({'name':r['name'],'width':r['width'],'target_multiplier':r['weight'],'agnostic':a,'context':b,'no_vra':d,'live':e})
        table.append(f'| {r["name"]} | {r["width"]} | {r["weight"]} | {a["gates"]}/{a["depth"]} | {b["gates"]}/{b["depth"]} | {d["gates"]}/{d["depth"]} | {e["gates"]}/{e["depth"]} |')
    (ROOT/'PAIRED_RESULTS.md').write_text('\n'.join(table)+'\n')
    summaries={p.parent.name:json.loads(p.read_text()) for p in sorted((ROOT/'runs').glob('*/SUMMARY.json'))}
    allrows=[r for name in summaries for r in rows(name)]
    # Audit the historical cache: all reused candidates were verified against
    # the same original workload/width. Current runner also hashes original RTL.
    for r in allrows:
        cached=r.get('evaluation',{}).get('cached_from')
        if cached and not pathlib.Path(cached).name.startswith(f'{r["name"]}_{r["width"]}_'):
            raise ValueError('cross-original historical cache reuse')
    jobs={r['optimizer_process']['log']:r for r in allrows}
    info={'primary_runs':primary,'summaries':summaries,'all_recorded_rows':len(allrows),'failed_rows':sum(not r['passed'] for r in allrows),
          'unique_syntheses':sum(s['unique_evaluations'] for s in summaries.values()),
          'sum_run_wall_seconds':sum(s['wall_seconds'] for s in summaries.values()),
          'peak_child_rss_kib':max(s['children_peak_rss_kib'] for s in summaries.values()),
          'optimizer_cpu_seconds_all_runs':sum(r.get('optimizer_cpu_seconds',0) for r in jobs.values()),
          'gates_context_vs_agnostic':{label:sum((p['context']['gates']-p['agnostic']['gates'])*sign>0 for p in paired) for label,sign in [('wins',-1),('losses',1)]},
          'paired':paired,'historical_cache_originals_audited':True}
    info['gates_context_vs_agnostic']['ties']=sum(p['context']['gates']==p['agnostic']['gates'] for p in paired)
    info['gates_live_vs_agnostic']={'wins':sum(p['live']['gates']<p['agnostic']['gates'] for p in paired),
        'ties':sum(p['live']['gates']==p['agnostic']['gates'] for p in paired),'losses':sum(p['live']['gates']>p['agnostic']['gates'] for p in paired)}
    (ROOT/'AGGREGATE.json').write_text(json.dumps(info,indent=2)+'\n')
    versions=json.loads((ROOT/'SOURCE_VERSIONS.json').read_text())
    versions['code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
    (ROOT/'SOURCE_VERSIONS.json').write_text(json.dumps(versions,indent=2)+'\n')
    print({k:v for k,v in info.items() if k not in ['paired','summaries']})


if __name__=='__main__':main()
