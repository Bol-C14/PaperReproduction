#!/usr/bin/env python3
"""Recalculate comparisons from manually transcribed preprint Table IV."""
import csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with (root/'metrics'/'paper_table_iv_transcribed.csv').open() as f:rows=list(csv.DictReader(f))
def n(r,k):return float(r[k])
s={'source':'Georgia Tech preprint Table IV, p8; rounded values, manually transcribed, not reproduced','higher_grpo_power_than_commercial':[r['benchmark'] for r in rows if n(r,'grpo_power_mw')>n(r,'commercial_power_mw')],'worse_grpo_wns_than_commercial':[r['benchmark'] for r in rows if n(r,'grpo_wns_ns')<n(r,'commercial_wns_ns')],'tns_improvements_pct_from_rounded_table':{r['benchmark']:100*(abs(n(r,'commercial_tns_ns'))-abs(n(r,'grpo_tns_ns')))/abs(n(r,'commercial_tns_ns')) for r in rows},'note':'Table precision may differ from printed percentage annotations. Preprint conclusion77.7% does not match this rounded table maximum; do not silently reconcile.'}
(root/'metrics'/'paper_table_audit.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
