"""Descriptive transfer regret from separately measured donor-selected configs."""
import json
from eda import ROOT
from qor import layout
R=ROOT/'results';matrix=json.loads((R/'transfer_matrix.json').read_text());rankings=json.loads((R/'retrieval_rankings.json').read_text());rankings['div_16bit']={'ast':json.loads((R/'extended_rankings.json').read_text())};rows=[]
for design in sorted({x['target'] for x in matrix}):
 cells=[x for x in matrix if x['target']==design];default=layout(cells[0]['reference']['area'],cells[0]['reference']['power'],cells[0]['reference']['slack'],cells[0]['reference']);best=min(cells,key=lambda x:x['qor'])
 for mode,rank in rankings[design].items():
  choice=rank[0]['id'];chosen=next(x for x in cells if x['donor']==choice);rows.append({'target':design,'retrieval':mode,'chosen_donor':choice,'transferred_qor':chosen['qor'],'default_qor':default,'best_measured_donor':best['donor'],'best_measured_donor_qor':best['qor'],'regret_vs_best_measured_donor':chosen['qor']-best['qor'],'delta_vs_default':chosen['qor']-default})
(R/'transfer_audit.json').write_text(json.dumps(rows,indent=2));print(json.dumps([x for x in rows if x['retrieval']=='ast'],indent=2))
