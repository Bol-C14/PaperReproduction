"""Separate full-token reconstruction fidelity sensitivity; all other choices retained."""
import argparse,copy,hashlib,json,os,pathlib,random,resource,sys,time
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'pilot'))
from adapter import load_encoder_classes
from run_pilot import graph_fields,strict_checkpoint
from data import build,ancestors
from eco import synthesize,verify,metrics

ARMS=['paired_pretrained','pm_only','shuffled_aig','paired_random','no_mcm']


def set_seed(seed):random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)

def sid(text):return int(hashlib.sha256(text.encode()).hexdigest()[:8],16)%2147483647

def graph(case,cut=False):
    g=SimpleNamespace(**graph_fields(case['cut' if cut else 'pm'],''),**graph_fields(case['aig'],'aig_'))
    if cut:g.x[case['target']]=0
    return g


class Pipeline(nn.Module):
    def __init__(self,arm,seed):
        super().__init__();set_seed(seed);A,P=load_encoder_classes();self.pm=P();self.aig=A();del self.aig.connect_head
        self.arm=arm;self.encoder_reports={}
        if arm!='paired_random':
            self.encoder_reports['aig']=strict_checkpoint(self.aig,'aig_dg2')
            self.encoder_reports['pm']=strict_checkpoint(self.pm,'pm_dg2')
            assert all(x['compatible'] for x in self.encoder_reports.values())
        for p in self.aig.parameters():p.requires_grad_(False)
        # Identical fusion and ranking initial weights across arms of a seed.
        set_seed(seed+1000)
        layer=nn.TransformerEncoderLayer(d_model=256,nhead=8,dim_feedforward=2048,dropout=.1,batch_first=True)
        self.fusion=nn.TransformerEncoder(layer,num_layers=4,enable_nested_tensor=False)
        self.mask=nn.Parameter(torch.randn(128))
        self.rank=nn.Sequential(nn.Linear(512,128),nn.ReLU(),nn.Linear(128,1))
        self.context={};self.view_partner={}

    def prepare_context(self,cases):
        self.aig.eval()
        for c in cases:
            np.random.seed(sid(c['id']))
            with torch.no_grad():
                h,f=self.aig(graph(c));self.context[c['id']]=torch.cat([h,f],1).detach()
        for split in ['train','validation','test']:
            group=[c for c in cases if c['split']==split]
            for i,c in enumerate(group):
                choices=[x for x in group if x['parent']!=c['parent']]
                assert choices
                self.view_partner[c['id']]=choices[sid(c['id'])%len(choices)]['id']

    def pm_encode(self,c,cut=False):
        np.random.seed(sid(c['id']))
        h,f=self.pm(graph(c,cut));return torch.cat([h,f],1)

    def contextualize(self,pm_tokens,cases,mask_indices,counterfactual=False):
        all_tokens=[]
        for tokens,c,indices in zip(pm_tokens,cases,mask_indices):
            tok=tokens.clone();tok[indices,128:]=self.mask
            use_other=self.arm=='shuffled_aig' or counterfactual
            key=self.view_partner[c['id']] if use_other else c['id']
            other=self.context[key]
            if self.arm=='pm_only':other=torch.zeros_like(self.context[c['id']])
            all_tokens.append(torch.cat([tok,other],0))
        padded=nn.utils.rnn.pad_sequence(all_tokens,batch_first=True)
        lengths=torch.tensor([len(x) for x in all_tokens]);padding=torch.arange(padded.shape[1])[None,:]>=lengths[:,None]
        fused=self.fusion(padded,src_key_padding_mask=padding)
        return [fused[i,:len(t)] for i,t in enumerate(pm_tokens)]


def masked(c,seed):
    rng=random.Random(seed+sid(c['id']));n=len(c['pm']['nodes']);roots=rng.sample(list(range(6,n)),max(1,int(.05*n)))
    selected=set(roots);front=roots
    for _ in range(4):
        front=[p for i in front for p in c['pm']['nodes'][i]['pins']];selected.update(front)
    return sorted(selected)


def batches(cases,seed,epoch):
    group=cases.copy();random.Random(seed+epoch).shuffle(group)
    for i in range(0,len(group),4):yield group[i:i+4]


def probability_loss(model,tokens,cases):
    pred=torch.cat([model.pm.pred_prob(t[:,128:]).reshape(-1) for t in tokens])
    exact=torch.tensor([p for c in cases for p in c['prob_pm']],dtype=torch.float32)
    return nn.functional.l1_loss(pred,exact)


def train_phase(model,cases,phase,epochs,seed,curves):
    params=list(model.pm.parameters()) if phase=='probability' else [p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.Adam(params,lr=1e-4)
    for epoch in range(epochs):
        model.train();model.aig.eval();total=[];start=time.perf_counter()
        for group in batches(cases,seed,epoch):
            optimizer.zero_grad(set_to_none=True)
            if phase in ['probability','mcm']:
                tokens=[model.pm_encode(c) for c in group];prob=probability_loss(model,tokens,group)
                rec=torch.tensor(0.0);classification=torch.tensor(0.0)
                if phase=='mcm' and model.arm!='no_mcm':
                    indices=[masked(c,seed+epoch) for c in group];out=model.contextualize(tokens,group,indices)
                    rec=torch.stack([nn.functional.l1_loss(o[idx],t[idx].detach()) for o,t,idx in zip(out,tokens,indices)]).mean()
                loss=prob+rec
            else:
                gold=[model.pm_encode(c).detach() for c in group]
                cut=[model.pm_encode(c,cut=True) for c in group]
                out=model.contextualize(cut,group,[[c['target']] for c in group])
                rec=torch.stack([nn.functional.l1_loss(o[c['target']],g[c['target']]) for o,g,c in zip(out,gold,group)]).mean()
                bces=[]
                for o,c in zip(out,group):
                    ids=c['legal_candidates'];target=o[c['target']].expand(len(ids),-1)
                    logit=model.rank(torch.cat([o[ids],target],1)).reshape(-1)
                    labels=torch.tensor([float(i in c['ancestry']) for i in ids])
                    bces.append(nn.functional.binary_cross_entropy_with_logits(logit,labels))
                classification=torch.stack(bces).mean();prob=torch.tensor(0.0);loss=classification+rec
            if not torch.isfinite(loss):raise RuntimeError('nonfinite loss')
            loss.backward();norm=torch.nn.utils.clip_grad_norm_(params,10.0)
            assert torch.isfinite(norm);optimizer.step()
            total.append([float(loss.detach()),float(prob.detach()),float(rec.detach()),float(classification.detach())])
        item={'phase':phase,'epoch':epoch+1,'steps':len(total),'loss':np.mean(total,0).tolist(),'seconds':time.perf_counter()-start}
        curves.append(item);print(json.dumps({'arm':model.arm,'seed':seed,**item}),flush=True)


def representation_eval(model,cases,seed):
    model.eval();rows=[]
    with torch.inference_mode():
        for group in batches(cases,seed,0):
            tokens=[model.pm_encode(c) for c in group];idx=[masked(c,seed) for c in group]
            fused=model.contextualize(tokens,group,idx)
            for c,t,o,indices in zip(group,tokens,fused,idx):
                pred=model.pm.pred_prob(t[:,128:]).reshape(-1);truth=torch.tensor(c['prob_pm'])
                rows.append({'id':c['id'],'family':c['family'],'probability_mae':float((pred[6:]-truth[6:]).abs().mean()),
                    'masked_hf_l1':float((o[indices,128:]-t[indices,128:]).abs().mean()),'effective_mask_fraction':len(indices)/len(t)})
    return {'probability_mae':float(np.mean([r['probability_mae'] for r in rows])),
            'masked_hf_l1':float(np.mean([r['masked_hf_l1'] for r in rows])),
            'effective_mask_fraction':float(np.mean([r['effective_mask_fraction'] for r in rows])),'cases':rows}


def eco_eval(model,cases,seed,counterfactual=False):
    model.eval();records=[]
    for c in cases:
        started=time.perf_counter()
        with torch.inference_mode():
            tokens=model.pm_encode(c,cut=True);out=model.contextualize([tokens],[c],[[c['target']]],counterfactual)[0]
            ids=c['legal_candidates'];target=out[c['target']].expand(len(ids),-1)
            logits=model.rank(torch.cat([out[ids],target],1)).reshape(-1)
            ranking=[ids[i] for i in torch.argsort(logits,descending=True,stable=True).tolist()]
        ranking_seconds=time.perf_counter()-started
        result=synthesize(c,ranking,3)
        if result['success']:
            result['verification']=verify(c,result['patch']);assert result['verification']['passed']
        records.append({'id':c['id'],'parent':c['parent'],'family':c['family'],'ranking':ranking,
                        'ranking_seconds':ranking_seconds,**metrics(ranking,c['ancestry']),**result})
    return summarize(records)


def summarize(records):
    good=[r for r in records if r['success']]
    return {'cases':len(records),'success_at3':len(good)/len(records),
      'average_precision':float(np.mean([r.get('average_precision',0) for r in records])),
      'ancestry_recall_at3':float(np.mean([r.get('ancestry_recall_at3',0) for r in records])),
      'mean_support_on_success':float(np.mean([r['support_budget'] for r in good])) if good else None,
      'mean_gates_on_success':float(np.mean([r['patch']['gate_count'] for r in good])) if good else None,
      'mean_solver_seconds':float(np.mean([r['seconds'] for r in records])),
      'mean_ranking_seconds':float(np.mean([r.get('ranking_seconds',0) for r in records])),
      'verified_successes':len(good),'records':records}


def baselines(cases):
    out={}
    for mode in ['random','reverse_topological','oracle_direct_fanin','pi_fallback']:
        records=[]
        for c in cases:
            ranking=c['legal_candidates'].copy()
            if mode=='random':random.Random(208+sid(c['id'])).shuffle(ranking)
            elif mode=='reverse_topological':ranking=sorted(ranking,reverse=True)
            elif mode=='oracle_direct_fanin':ranking=list(c['pm']['nodes'][c['target']]['pins'])+sorted(set(ranking)-set(c['pm']['nodes'][c['target']]['pins']))
            else:ranking=list(range(6))
            result=synthesize(c,ranking,6 if mode=='pi_fallback' else 3)
            if result['success']:result['verification']=verify(c,result['patch']);assert result['verification']['passed']
            records.append({'id':c['id'],'parent':c['parent'],'family':c['family'],**metrics(ranking,c['ancestry']),**result})
        out[mode]=summarize(records)
    # A deliberately inverted successful patch must be rejected by independent oracle.
    c=cases[0];patch=copy.deepcopy(out['oracle_direct_fanin']['records'][0]['patch'])
    patch['nodes'].append({'gate':'NOT','pins':[patch['output']]});patch['output']=len(patch['nodes'])-1
    out['negative_patch_control']=verify(c,patch);assert not out['negative_patch_control']['passed']
    return out


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--arms',nargs='+',default=['paired_pretrained','pm_only']);parser.add_argument('--seeds',nargs='+',type=int,default=[208,209]);args=parser.parse_args()
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    started=time.time();mode='full_token_preflight' if args.preflight else 'full_token';directory=ROOT/'results'/mode;directory.mkdir(exist_ok=True)
    cases,manifest=build(small=args.preflight);parts={s:[c for c in cases if c['split']==s] for s in ['train','validation','test']}
    # All existing upstream bytes must remain unchanged.
    audit=json.loads((ROOT.parent/'assets.json').read_text())
    for x in audit['source_file_manifest']:assert hashlib.sha256((ROOT.parent/x['path']).read_bytes()).hexdigest()==x['sha256']
    epochs=(1,1,1) if args.preflight else (2,6,6);seeds=[208] if args.preflight else args.seeds
    results=[]
    for seed in seeds:
        for arm in args.arms:
            previous=directory/f'{arm}_{seed}.json'
            if args.resume and previous.exists():
                result=json.loads(previous.read_text());results.append(result)
                print('RESUME_COMPLETED',arm,seed,flush=True)
                continue
            model=Pipeline(arm,seed);model.prepare_context(cases);curves=[];runstart=time.time()
            before=representation_eval(model,parts['validation'],seed)
            train_phase(model,parts['train'],'probability',epochs[0],seed,curves)
            train_phase(model,parts['train'],'mcm',epochs[1],seed,curves)
            representation={s:representation_eval(model,parts[s],seed) for s in ['validation','test']}
            train_phase(model,parts['train'],'eco',epochs[2],seed,curves)
            ckpt=ROOT/'checkpoints'/f'{mode}_{arm}_{seed}.pth';torch.save({'state_dict':model.state_dict(),'arm':arm,'seed':seed,'epochs':epochs,'protocol':'PROTOCOL.md'},ckpt)
            downstream={s:eco_eval(model,parts[s],seed) for s in ['validation','test']}
            if arm=='paired_pretrained':downstream['test_wrong_view']=eco_eval(model,parts['test'],seed,True)
            result={'arm':arm,'seed':seed,'epochs':epochs,'encoder_reports':model.encoder_reports,'before_validation':before,'representation':representation,'downstream':downstream,'curves':curves,'seconds':time.time()-runstart,'checkpoint_sha256':hashlib.sha256(ckpt.read_bytes()).hexdigest(),'checkpoint_path':str(ckpt.relative_to(ROOT))}
            (directory/f'{arm}_{seed}.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
            print('RUN_FINISHED',arm,seed,result['seconds'],{k:v['success_at3'] for k,v in downstream.items()},flush=True)
            del model
            if time.time()-started>2700:raise RuntimeError('45minute main limit reached; stop before expansion')
    baseline=baselines(parts['test']);(directory/'baselines.json').write_text(json.dumps(baseline,indent=2)+'\n')
    report={'mode':mode,'config':vars(args),'manifest':{k:v for k,v in manifest.items() if k!='parents'},'split_case_counts':{s:len(x) for s,x in parts.items()},'epochs':epochs,'elapsed_seconds':time.time()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'runtime':{'torch':torch.__version__,'numpy':np.__version__,'threads':2,'device':'cpu'},'runs':[{'arm':r['arm'],'seed':r['seed'],'seconds':r['seconds'],'test_representation':{k:v for k,v in r['representation']['test'].items() if k!='cases'},'test_eco':{k:v for k,v in r['downstream']['test'].items() if k!='records'}} for r in results]}
    (directory/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('COMPLETE',json.dumps(report),flush=True)


if __name__=='__main__':main()
