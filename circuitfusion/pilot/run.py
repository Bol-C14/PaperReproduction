"""Bounded randomly initialized CPU method port. Read PROTOCOL.json first."""
import hashlib,json,math,os,random,resource,sys,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from data import build,check
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=json.loads((ROOT/'pilot/PROTOCOL.json').read_text());DIM=PROTOCOL['encoders']['dimension']

class Dataset:
    def __init__(self,records):
        self.records=records
        words=sorted({tok for r in records for k in ['code','equivalent_code','summary'] for tok in r[k]})
        kinds=sorted({kind for r in records for k in ['graph','equivalent_graph','netlist'] for kind,_ in r[k]['nodes']})
        # Vocabulary is a fixed symbol schema; no held-out targets/statistics enter training.
        self.words={w:i+1 for i,w in enumerate(words)};self.kinds={w:i+1 for i,w in enumerate(kinds)}
        self.tokens={key:self.pad_tokens([r[key] for r in records]) for key in ['code','equivalent_code','summary']}
        self.graphs={key:self.pad_graphs([r[key] for r in records]) for key in ['graph','equivalent_graph','netlist']}
        self.train=torch.tensor([i for i,r in enumerate(records) if r['split']=='train']);self.test=torch.tensor([i for i,r in enumerate(records) if r['split']=='test'])
    def pad_tokens(self,seqs):
        t=torch.zeros(len(seqs),max(map(len,seqs)),dtype=torch.long)
        for i,s in enumerate(seqs):t[i,:len(s)]=torch.tensor([self.words[w] for w in s])
        return t
    def pad_graphs(self,graphs):
        n=max(len(g['nodes']) for g in graphs);b=len(graphs)
        ids=torch.zeros(b,n,dtype=torch.long);lanes=torch.zeros_like(ids);adj=torch.zeros(b,n,n)
        for i,g in enumerate(graphs):
            length=len(g['nodes']);ids[i,:length]=torch.tensor([self.kinds[k] for k,_ in g['nodes']]);lanes[i,:length]=torch.tensor([lane+1 for _,lane in g['nodes']]);adj[i,:length,:length]=torch.eye(length)
            for src,dst in g['edges']:adj[i,dst,src]=1;adj[i,src,dst]=1
        adj=adj/adj.sum(-1,keepdim=True).clamp_min(1)
        return ids,lanes,adj
    def batch(self,indices,variant=False):
        c='equivalent_code' if variant else 'code';g='equivalent_graph' if variant else 'graph'
        return self.tokens[c][indices],self.tokens['summary'][indices],tuple(t[indices] for t in self.graphs[g])
    def net(self,indices):return tuple(t[indices] for t in self.graphs['netlist'])

class TextEncoder(nn.Module):
    def __init__(self,vocab):super().__init__();self.embed=nn.Embedding(vocab+1,DIM,padding_idx=0);self.gru=nn.GRU(DIM,DIM,batch_first=True)
    def forward(self,ids):
        out,_=self.gru(self.embed(ids));return out,ids.ne(0)
class GraphEncoder(nn.Module):
    def __init__(self,vocab):
        super().__init__();self.embed=nn.Embedding(vocab+1,DIM,padding_idx=0);self.lane=nn.Embedding(4,DIM);self.layers=nn.ModuleList([nn.Linear(DIM,DIM) for _ in range(3)])
    def forward(self,data):
        ids,lanes,adj=data;mask=ids.ne(0);h=(self.embed(ids)+self.lane(lanes))*mask.unsqueeze(-1)
        for layer in self.layers:h=F.gelu(layer(torch.bmm(adj,h)))*mask.unsqueeze(-1)
        return h,mask

def mean(h,m):return (h*m.unsqueeze(-1)).sum(1)/m.sum(1,keepdim=True).clamp_min(1)
class Model(nn.Module):
    def __init__(self,ds):
        super().__init__();self.code=TextEncoder(len(ds.words));self.summary=TextEncoder(len(ds.words));self.graph=GraphEncoder(len(ds.kinds));self.netlist=GraphEncoder(len(ds.kinds));self.cross=nn.MultiheadAttention(DIM,4,batch_first=True);self.fusion=nn.Linear(DIM,DIM);self.netproj=nn.Linear(DIM,DIM)
    def rtl(self,batch,ablate=None):
        code,summary,graph=batch;c,cm=self.code(code);s,sm=self.summary(summary);g,gm=self.graph(graph)
        if ablate=='code':c=torch.zeros_like(c)
        if ablate=='summary':s=torch.zeros_like(s)
        if ablate=='graph':g=torch.zeros_like(g)
        memory=torch.cat([c,g],1);mm=torch.cat([cm,gm],1)
        z,_=self.cross(s,memory,memory,key_padding_mask=~mm,need_weights=False)
        return F.normalize(self.fusion(mean(s+z,sm)),dim=-1)
    def net(self,batch):
        h,m=self.netlist(batch);return F.normalize(self.netproj(mean(h,m)),dim=-1)

def contrast(a,b):
    logits=a@b.T/PROTOCOL['training']['temperature'];target=torch.arange(len(a))
    return (F.cross_entropy(logits,target)+F.cross_entropy(logits.T,target))/2

def evaluate(model,ds,idx):
    with torch.no_grad():
        z=model.rtl(ds.batch(idx));alt=model.rtl(ds.batch(idx,True));n=model.net(ds.net(idx));scores=z@n.T;ranks=scores.argsort(1,descending=True);target=torch.arange(len(idx))
        r1=(ranks[:,0]==target).float();r5=(ranks[:,:5]==target[:,None]).any(1).float()
        return {'recall_at_1':float(r1.mean()),'recall_at_5':float(r5.mean()),'equivalent_view_cosine':float((z*alt).sum(-1).mean()),'per_sample_r1':r1.tolist(),'per_sample_r5':r5.tolist(),'modality_zeroing_mean_l2':{m:float(torch.linalg.vector_norm(z-model.rtl(ds.batch(idx),m),dim=-1).mean()) for m in ['code','graph','summary']}}

def main():
    start=time.monotonic();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    protocol_hash=hashlib.sha256((ROOT/'pilot/PROTOCOL.json').read_bytes()).hexdigest();assert protocol_hash==(ROOT/'pilot/PROTOCOL.sha256').read_text().split()[0]
    records,integrity=build(ROOT/'results/data');ds=Dataset(records)
    # Fixed within-family derangement established before any optimization.
    permutation=torch.arange(len(records));negative_map={}
    for f in range(8):
        ids=[i for i,r in enumerate(records) if r['family']==f];assert len(ids)>1
        for a,b in zip(ids,ids[1:]+ids[:1]):permutation[a]=b;negative_map[records[a]['sample_id']]=records[b]['sample_id']
    (ROOT/'results/data/shuffled_pairs.json').write_text(json.dumps(negative_map,indent=2)+'\n')
    runs=[]
    for seed in PROTOCOL['training']['seeds']:
        for arm in PROTOCOL['training']['arms']:
            if time.monotonic()-start>PROTOCOL['limits']['pilot_wall_seconds_max']:raise TimeoutError('frozen pilot wall budget exceeded')
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);model=Model(ds);optimizer=torch.optim.Adam(model.parameters(),lr=.002)
            batch_rng=torch.Generator().manual_seed(seed+1000);losses=[];arm_start=time.monotonic()
            for step in range(PROTOCOL['training']['steps_per_arm']):
                idx=ds.train[torch.randperm(len(ds.train),generator=batch_rng)[:16]]
                z=model.rtl(ds.batch(idx));other=model.rtl(ds.batch(idx,True));within=contrast(z,other)
                loss=within
                if arm!='no_alignment':
                    target_idx=idx if arm=='paired' else permutation[idx];loss=loss+contrast(z,model.net(ds.net(target_idx)))
                optimizer.zero_grad();loss.backward();optimizer.step();losses.append(float(loss.detach()))
                if time.monotonic()-start>PROTOCOL['limits']['pilot_wall_seconds_max']:raise TimeoutError('frozen pilot wall budget exceeded')
            model.eval();test=evaluate(model,ds,ds.test);train=evaluate(model,ds,ds.train)
            row={'seed':seed,'arm':arm,'steps':250,'parameters':sum(p.numel() for p in model.parameters()),'first_10_loss_mean':float(np.mean(losses[:10])),'last_10_loss_mean':float(np.mean(losses[-10:])),'train_recall_at_1':train['recall_at_1'],'test':test,'wall_seconds':time.monotonic()-arm_start}
            runs.append(row);print(json.dumps(row),flush=True)
            (ROOT/'results/pilot_partial.json').write_text(json.dumps(runs,indent=2)+'\n')
    # Bootstrap families, averaging paired-control differences over predeclared seeds.
    families=sorted({records[int(i)]['family'] for i in ds.test});comparisons={};rng=np.random.default_rng(20261028)
    for control in ['shuffled','no_alignment']:
        differences=[]
        for f in families:
            offsets=[j for j,i in enumerate(ds.test) if records[int(i)]['family']==f];d=[]
            for seed in PROTOCOL['training']['seeds']:
                pair=next(r for r in runs if r['seed']==seed and r['arm']=='paired')['test']['per_sample_r1'];con=next(r for r in runs if r['seed']==seed and r['arm']==control)['test']['per_sample_r1']
                d.append(np.mean([pair[j]-con[j] for j in offsets]))
            differences.append(float(np.mean(d)))
        boots=np.asarray(differences)[rng.integers(0,len(families),size=(2000,len(families)))].mean(1)
        comparisons[control]={'mean_paired_minus_control_r1':float(np.mean(differences)),'family_bootstrap_95_percentile_ci':np.quantile(boots,[.025,.975]).tolist(),'family_differences':dict(zip(map(str,families),differences)),'warning':'four synthetic held-out families; exploratory, not population evidence'}
    result={'label':PROTOCOL['label'],'protocol_sha256':protocol_hash,'integrity':integrity,'chance_recall_at_1':1/len(ds.test),'chance_recall_at_5':5/len(ds.test),'runs':runs,'comparisons':comparisons,'resources':{'wall_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'torch_version':torch.__version__,'cpu_threads':torch.get_num_threads(),'cuda_used':False},'limitations':['self-authored combinational expression cones, no sequential resets/clocks tested','synthetic exact gate lowering, no commercial synthesis or timing labels','template-derived summaries and code share structure','random small encoders, no pretrained weights','retrieval within 28 held-out candidates, not PPA prediction','no full upstream pipeline execution']}
    (ROOT/'results/pilot_metrics.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',json.dumps(result['resources']),flush=True)
if __name__=='__main__':main()
