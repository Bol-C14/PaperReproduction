"""Prove a saved learned ranking and exact repair need only public ECO inputs."""
import json,pathlib,sys,hashlib
from types import SimpleNamespace
import numpy as np
import torch
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from train import Pipeline,graph_fields,sid
from data import legal_candidates
from eco import synthesize


def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    cases=json.loads((ROOT/'results/corpus.json').read_text());index={c['id']:c for c in cases}
    result=json.loads((ROOT/'results/main/paired_pretrained_208.json').read_text())
    path=ROOT/result['checkpoint_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==result['checkpoint_sha256']
    model=Pipeline('paired_pretrained',208);state=torch.load(path,weights_only=True,map_location='cpu');model.load_state_dict(state['state_dict'],strict=True);model.eval()
    checked=[]
    # All test cases, not chosen by success, and without any hidden golden-PM metadata.
    for r in result['downstream']['test']['records']:
        c=index[r['id']];public={k:c[k] for k in ['id','target','cut','aig']}
        assert not set(public)&{'pm','pm_to_aig','ancestry','prob_pm','prob_aig','spec','legal_candidates'}
        with torch.inference_mode():
            np.random.seed(sid(public['id']))
            g=SimpleNamespace(**graph_fields(public['aig'],'aig_'))
            hs,hf=model.aig(g);model.context[public['id']]=torch.cat([hs,hf],1).detach()
            tokens=model.pm_encode(public,cut=True)
            fused=model.contextualize([tokens],[public],[[public['target']]])[0]
            ids=legal_candidates(public['cut'],public['target'])
            logits=model.rank(torch.cat([fused[ids],fused[public['target']].expand(len(ids),-1)],1)).reshape(-1)
            ranking=[ids[i] for i in torch.argsort(logits,descending=True,stable=True).tolist()]
        assert ranking==r['ranking'],public['id']
        solved=synthesize(public,ranking,3)
        assert solved['success']==r['success']
        if solved['success']:assert solved['patch']==r['patch'] and solved['support_budget']==r['support_budget']
        checked.append({'case':public['id'],'same_ranking':True,'same_repair':True})
    report={'cases_checked':len(checked),'all_passed':True,'allowed_case_fields':['id','target','cut','aig'],
      'not_available_to_ranker_or_solver':['golden PM','original target cell type/pins/truth table','PM-to-AIG internal map','ancestry labels','teacher probabilities','family oracle spec'],
      'direct_fanin_oracle_baseline_excluded_from_this_claim':True,'records':checked}
    (ROOT/'results/main/public_input_noninterference.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))


if __name__=='__main__':main()
