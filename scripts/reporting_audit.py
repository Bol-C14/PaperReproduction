"""Displayed-value accounting; does not infer which unpublished run is correct."""
import csv,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'sources/table_ii.csv').open()));fig=list(csv.DictReader((root/'sources/figure6_labels.csv').open()));checks=[];aggregates=[]
for f in fig:
 r=next(r for r in rows if r['benchmark']==f['benchmark']);m=f['metric'];checks.append(dict(**f,formula='100*(1-aspen/base)',computed_percent={b:100*(1-float(r['aspen_'+m])/float(r[b+'_'+m])) for b in ['baseline','rover']},classification='reporting ambiguity; original runs/paired point IDs unavailable'))
for b in ['baseline','rover']:
 for m in ['area','delay']:
  ratios=[float(r['aspen_'+m])/float(r[b+'_'+m]) for r in rows]
  aggregates.append(dict(base=b,metric=m,arithmetic_mean_of_percent_improvements=100*(1-sum(ratios)/len(ratios)),geometric_ratio_improvement=100*(1-math.exp(sum(math.log(v) for v in ratios)/len(ratios))),ratio_of_sums_improvement=100*(1-sum(float(r['aspen_'+m]) for r in rows)/sum(float(r[b+'_'+m]) for r in rows))))
(root/'results/reporting_ambiguity.json').write_text(json.dumps(dict(checks=checks,aggregates=aggregates,rounding='inputs rounded to .01; unpublished precision unknown',pareto='Table II independent objective minima; Figure 6 underlying runs/points unknown'),indent=2))
print('Computed two individual-label comparisons and four aggregate comparisons; classification remains reporting ambiguity.')
