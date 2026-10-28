"""Frozen CPU mechanism port and matched-budget trained controls."""
import collections,hashlib,json,random,resource,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parent;P=json.loads((ROOT/'PROTOCOL.json').read_text());D=P['learning']['dimension']

def normalized_mean(h,mask):return (h*mask[...,None]).sum(1)/mask.sum(1,keepdim=True).clamp_min(1)

def multi_contrast(a,b,positive=None):
    logits=a@b.T/P['learning']['temperature']
    if positive is None:
        y=torch.arange(len(a));return .5*(F.cross_entropy(logits,y)+F.cross_entropy(logits.T,y))
    positive=positive.float();positive=positive/positive.sum(1,keepdim=True)
    return -(positive*F.log_softmax(logits,dim=1)).sum(1).mean()

class Data:
    def __init__(self,rs):
        self.rs=rs;train=[r for r in rs if r['split']=='train'];words=sorted({w for r in train for k in ['code','summary_tokens'] for w in r[k]});kinds=sorted({n[0] for r in train for k in ['graph','equivalent_graph','netlist'] for n in r[k]['nodes']})
        self.words={w:i+3 for i,w in enumerate(words)};self.kinds={k:i+3 for i,k in enumerate(kinds)}
        self.tokens={k:self.pad_tokens([r[k] for r in rs]) for k in ['code','summary_tokens']};self.graphs={k:self.pad_graphs([r[k] for r in rs]) for k in ['graph','equivalent_graph','netlist']}
        self.train=torch.tensor([i for i,r in enumerate(rs) if r['split']=='train']);self.test=torch.tensor([i for i,r in enumerate(rs) if r['split']=='test']);self.families=np.array([r['family'] for r in rs]);self.summary=torch.tensor([sorted({r['summary'] for r in rs}).index(r['summary']) for r in rs]);self.labels=np.array([[r['targets']['gate_count'],r['targets']['gate_depth']] for r in rs],dtype=float)
        # Counts are available RTL features shared by every downstream baseline.
        opkinds=sorted({n[0] for r in train for n in r['graph']['nodes'] if n[0].startswith('$')});self.counts=np.array([[sum(n[0]==k for n in r['graph']['nodes']) for k in opkinds] for r in rs],dtype=float)
    def pad_tokens(self,seqs):
        t=torch.zeros(len(seqs),max(map(len,seqs)),dtype=torch.long)
        for i,s in enumerate(seqs):t[i,:len(s)]=torch.tensor([self.words.get(w,1) for w in s])
        return t
    def pad_graphs(self,graphs):
        n=max(len(g['nodes']) for g in graphs);ids=torch.zeros(len(graphs),n,dtype=torch.long);lane=ids.clone();width=ids.clone();adj=torch.zeros(len(graphs),3,n,n)
        for i,g in enumerate(graphs):
            for j,(kind,l,w) in enumerate(g['nodes']):ids[i,j]=self.kinds.get(kind,1);lane[i,j]=l+1;width[i,j]=w
            for src,dst,role in g['edges']:adj[i,role,dst,src]+=1
        return ids,lane,width,adj
    def rtl(self,idx,alternate=False,summary_idx=None):return self.tokens['code'][idx],self.tokens['summary_tokens'][idx if summary_idx is None else summary_idx],tuple(x[idx] for x in self.graphs['equivalent_graph' if alternate else 'graph'])
    def net(self,idx):return tuple(x[idx] for x in self.graphs['netlist'])
    def rewired(self,graph,seed):
        ids,lane,width,adj=graph;out=adj.clone()
        for b in range(len(ids)):
            n=int(ids[b].ne(0).sum());gen=torch.Generator().manual_seed(seed+101*b);perm=torch.randperm(n,generator=gen);out[b,:,:n,:n]=adj[b,:,:n,:n][:,:,perm]
        return ids,lane,width,out

class Text(nn.Module):
    def __init__(self,n):super().__init__();self.embed=nn.Embedding(n,D,padding_idx=0);self.rnn=nn.GRU(D,D,batch_first=True)
    def forward(self,t):h,_=self.rnn(self.embed(t));return h,t.ne(0)
class Graph(nn.Module):
    def __init__(self,n):
        super().__init__();self.embed=nn.Embedding(n,D,padding_idx=0);self.lane=nn.Embedding(17,D);self.width=nn.Embedding(17,D);self.layers=nn.ModuleList([nn.ModuleList([nn.Linear(D,D) for _ in range(5)]) for _ in range(3)])
    def forward(self,data,mask=None):
        ids,lane,width,adj=data;valid=ids.ne(0);x=ids.clone()
        if mask is not None:x[mask]=2
        h=(self.embed(x)+self.lane(lane.clamp_max(16))+self.width(width.clamp_max(16)))*valid[...,None]
        inbound=adj/adj.sum(-1,keepdim=True).clamp_min(1);rev=adj.sum(1).transpose(1,2);rev=rev/rev.sum(-1,keepdim=True).clamp_min(1)
        for layer in self.layers:
            out=layer[0](h)+layer[4](torch.bmm(rev,h))
            for k in range(3):out=out+layer[k+1](torch.bmm(inbound[:,k],h))
            h=F.gelu(out)*valid[...,None]
        return h,valid
class Model(nn.Module):
    def __init__(self,ds):
        super().__init__();nw=len(ds.words)+3;ng=len(ds.kinds)+3
        self.code=Text(nw);self.summary=Text(nw);self.graph=Graph(ng);self.netlist=Graph(ng);self.cross=nn.MultiheadAttention(D,4,batch_first=True);self.fusion=nn.Linear(D,D);self.text_head=nn.Linear(D*2,D);self.net_head=nn.Linear(D,D);self.graph_decode=nn.Linear(D,ng);self.net_decode=nn.Linear(D,ng);self.summary_decode=nn.Linear(D,nw);self.match=nn.Linear(D,1)
    def rtl(self,batch,arm,masksummary=None):
        code,summ,gdata=batch;c,cm=self.code(code);s_input=summ.clone()
        if masksummary is not None:s_input[masksummary]=2
        s,sm=self.summary(s_input)
        if arm=='text_only':z=self.text_head(torch.cat([normalized_mean(c,cm),normalized_mean(s,sm)],-1));fused=s+z[:,None];g=None
        else:
            if arm=='no_graph':memory,mm=c,cm;g=None
            else:g,gm=self.graph(gdata);memory=torch.cat([c,g],1);mm=torch.cat([cm,gm],1)
            context,_=self.cross(s,memory,memory,key_padding_mask=~mm,need_weights=False);fused=s+context;z=self.fusion(normalized_mean(fused,sm))
        return F.normalize(z,dim=-1),fused,(g,s,sm)
    def net(self,batch):h,m=self.netlist(batch);return F.normalize(self.net_head(normalized_mean(h,m)),dim=-1)

def mask_for(t,seed):return (torch.rand(t.shape,generator=torch.Generator().manual_seed(seed))<.3)&t.ne(0)

def masked_graph(model,graph,net,seed):
    mask=mask_for(graph[0],seed);enc=model.netlist if net else model.graph;head=model.net_decode if net else model.graph_decode;h,_=enc(graph,mask)
    return F.cross_entropy(head(h)[mask],graph[0][mask]) if mask.any() else h.sum()*0

def fixed_negative_map(ds,seed):
    rng=np.random.default_rng(seed);perm=torch.arange(len(ds.rs))
    for family in sorted(set(ds.families[ds.train])):
        ids=ds.train[torch.tensor(ds.families[ds.train]==family)].tolist()
        for _ in range(1000):
            shuffled=rng.permutation(ids)
            if all(a!=b for a,b in zip(ids,shuffled)):break
        else:raise AssertionError('no derangement')
        for a,b in zip(ids,shuffled):perm[a]=int(b)
    assert all(perm[i]!=i and ds.rs[int(perm[i])]['split']=='train' and ds.families[i]==ds.families[int(perm[i])] for i in ds.train)
    return perm

def downstream(z,ds):
    z=z.numpy();train=ds.train.numpy();test=ds.test.numpy();labels=np.log1p(ds.labels);similarity=z@z.T;retrieved=[]
    for i in range(len(z)):
        pool=train[ds.families[train]!=ds.families[i]] if ds.rs[i]['split']=='train' else train
        assert len(pool)>=3 and all(ds.rs[j]['split']=='train' for j in pool)
        neighbors=pool[np.argsort(-similarity[i,pool],kind='stable')[:3]];retrieved.append(labels[neighbors].mean(0))
    retrieved=np.array(retrieved);base=np.concatenate([z,ds.counts],1);out={}
    for name,features in [('counts_only',ds.counts),('embedding_plus_counts',base),('retrieval_augmented',np.concatenate([base,retrieved],1))]:
        mean=features[train].mean(0);std=features[train].std(0);std[std<1e-8]=1;x=(features-mean)/std;x=np.column_stack([x,np.ones(len(x))]);penalty=np.eye(x.shape[1]);penalty[-1,-1]=0
        coef=np.linalg.solve(x[train].T@x[train]+penalty,x[train].T@labels[train]);pred=x@test.__class__ if False else x[test]@coef;errors=np.abs(pred-labels[test]);natural=np.maximum(0,np.expm1(np.clip(pred,-10,10)))
        out[name]={'log1p_mae':errors.mean(0).tolist(),'natural_mae':np.abs(natural-ds.labels[test]).mean(0).tolist(),'per_sample_log1p_abs_error':errors.tolist()}
    out['retrieved_metric_only']={'log1p_mae':np.abs(retrieved[test]-labels[test]).mean(0).tolist()};return out

def evaluate(model,ds,arm,seed):
    with torch.no_grad():
        batch=ds.rtl(torch.arange(len(ds.rs)))
        if arm=='shuffled_edges':batch=(batch[0],batch[1],ds.rewired(batch[2],seed+9000))
        z,_,_=model.rtl(batch,arm);alt=ds.rtl(torch.arange(len(ds.rs)),True)
        if arm=='shuffled_edges':alt=(alt[0],alt[1],ds.rewired(alt[2],seed+9000))
        az,_,_=model.rtl(alt,arm);n=model.net(ds.net(torch.arange(len(ds.rs))));idx=ds.test;scores=z[idx]@n[idx].T;ranking=scores.argsort(1,descending=True);target=torch.arange(len(idx));r1=(ranking[:,0]==target).float();r5=(ranking[:,:5]==target[:,None]).any(1).float();train_scores=z[ds.train]@n[ds.train].T
        out={'test_r1':float(r1.mean()),'test_r5':float(r5.mean()),'per_sample_r1':r1.tolist(),'per_sample_r5':r5.tolist(),'test_sample_ids':[ds.rs[i]['sample_id'] for i in idx],'train_r1':float((train_scores.argmax(1)==torch.arange(len(ds.train))).float().mean()),'equivalent_view_cosine':float((z[idx]*az[idx]).sum(-1).mean()),'downstream':downstream(z,ds),'external_counter_r1':float(r1[-1]),'external_counter_r5':float(r5[-1])}
        if arm=='paired':
            rew=(batch[0],batch[1],ds.rewired(batch[2],seed+9000));rz,_,_=model.rtl(rew,arm);rank=(rz[idx]@n[idx].T).argsort(1,descending=True);out['inference_rewired_r1']=float((rank[:,0]==target).float().mean());out['inference_rewired_embedding_l2']=float(torch.linalg.vector_norm(z[idx]-rz[idx],dim=-1).mean())
        return out

def main():
    start=time.monotonic();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);protocol_hash=hashlib.sha256((ROOT/'PROTOCOL.json').read_bytes()).hexdigest();assert protocol_hash==(ROOT/'PROTOCOL.sha256').read_text().split()[0]
    ds=Data(json.loads((ROOT/'manifest.json').read_text()));out=ROOT/'results';out.mkdir(exist_ok=True);runs=[]
    for seed in P['learning']['seeds']:
        perm=fixed_negative_map(ds,seed);(out/f'negative_pairs_seed{seed}.json').write_text(json.dumps({ds.rs[i]['sample_id']:ds.rs[int(perm[i])]['sample_id'] for i in ds.train},indent=2)+'\n')
        for arm in P['learning']['arms']:
            t=time.monotonic();torch.manual_seed(seed);random.seed(seed);np.random.seed(seed);model=Model(ds);opt=torch.optim.Adam(model.parameters(),lr=.002);batch_rng=torch.Generator().manual_seed(seed+1000);losses=[];components=collections.defaultdict(list);gradient_parameters=0
            for step in range(P['learning']['steps']):
                idx=ds.train[torch.randperm(len(ds.train),generator=batch_rng)[:16]];batch=ds.rtl(idx);alternate=ds.rtl(idx,True)
                if arm=='shuffled_edges':batch=(batch[0],batch[1],ds.rewired(batch[2],seed+9000));alternate=(alternate[0],alternate[1],ds.rewired(alternate[2],seed+9000))
                z,_,(gh,sh,sm)=model.rtl(batch,arm);az,_,_=model.rtl(alternate,arm);target=perm[idx] if arm=='shuffled_pairing' else idx;netbatch=ds.net(target)
                terms={'equivalent_view':multi_contrast(z,az),'implementation_alignment':multi_contrast(z,model.net(netbatch)),'masked_netlist':masked_graph(model,netbatch,True,seed*100000+step*10+1)}
                if arm not in ['no_graph','text_only']:
                    gm=batch[2][0].ne(0);terms['graph_summary_contrastive']=multi_contrast(F.normalize(normalized_mean(gh,gm),dim=-1),F.normalize(normalized_mean(sh,sm),dim=-1),ds.summary[idx,None].eq(ds.summary[idx][None,:]));terms['masked_graph']=masked_graph(model,batch[2],False,seed*100000+step*10+2)
                summarymask=mask_for(batch[1],seed*100000+step*10+3);_,fused,_=model.rtl(batch,arm,summarymask);terms['masked_summary']=F.cross_entropy(model.summary_decode(fused)[summarymask],batch[1][summarymask])
                # Coarse identical summaries are multi-positive, never false mismatches.
                wrong=idx.roll(1);valid=ds.summary[idx].ne(ds.summary[wrong])
                if valid.any():
                    mismatch=(batch[0],ds.tokens['summary_tokens'][wrong],batch[2]);nz,_,_=model.rtl(mismatch,arm);logits=torch.cat([model.match(z[valid]),model.match(nz[valid])]).flatten();labels=torch.cat([torch.ones(int(valid.sum())),torch.zeros(int(valid.sum()))]);terms['matching']=F.binary_cross_entropy_with_logits(logits,labels)
                loss=sum(P['learning']['weights'][k]*v for k,v in terms.items());opt.zero_grad();loss.backward();gradient_parameters=sum(p.numel() for p in model.parameters() if p.grad is not None);opt.step();losses.append(float(loss.detach()))
                for k,v in terms.items():components[k].append(float(v.detach()))
                if time.monotonic()-start>P['limits']['max_training_wall_seconds']:raise TimeoutError('frozen training budget exceeded')
            model.eval();metrics=evaluate(model,ds,arm,seed);row={'seed':seed,'arm':arm,'steps':400,'parameter_count':sum(p.numel() for p in model.parameters()),'last_step_gradient_parameters':gradient_parameters,'first10_loss':float(np.mean(losses[:10])),'last10_loss':float(np.mean(losses[-10:])),'last10_components':{k:float(np.mean(v[-10:])) for k,v in components.items()},'metrics':metrics,'wall_seconds':time.monotonic()-t};runs.append(row);print(json.dumps(row),flush=True);(out/'partial.json').write_text(json.dumps(runs,indent=2)+'\n');torch.save(model.state_dict(),out/f'{arm}_seed{seed}.pt')
    result={'protocol_sha256':protocol_hash,'runs':runs,'resources':{'wall_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'torch':torch.__version__,'threads':2},'chance_r1':1/len(ds.test),'chance_r5':5/len(ds.test),'notes':['no original PPA targets','behavioral summaries are heuristic, not LLM','all parameters random initialization','equal steps, batches, width and allocated modules; different active parameter counts reported','generated families are grammar-disjoint IDs, semantic disjointness checked; grammar overlaps remain','original and previous port results preserved']}
    # Family bootstrap from matched seeds; include external parent as its own group and report separately.
    comparisons={};rng=np.random.default_rng(20261028);families=sorted(set(ds.families[ds.test]));testfam=ds.families[ds.test]
    for control in [a for a in P['learning']['arms'] if a!='paired']:
        delta=[]
        for fam in families:
            indices=np.where(testfam==fam)[0];values=[]
            for seed in P['learning']['seeds']:
                a=next(r for r in runs if r['seed']==seed and r['arm']=='paired')['metrics']['per_sample_r1'];b=next(r for r in runs if r['seed']==seed and r['arm']==control)['metrics']['per_sample_r1'];values.append(np.mean(np.array(a)[indices]-np.array(b)[indices]))
            delta.append(float(np.mean(values)))
        boot=np.array(delta)[rng.integers(0,len(delta),(2000,len(delta)))].mean(1);comparisons[control]={'parent_mean_delta_r1':float(np.mean(delta)),'bootstrap95':np.quantile(boot,[.025,.975]).tolist(),'by_parent':dict(zip(map(str,families),delta))}
    result['comparisons']=comparisons;(out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',json.dumps(result['resources']),flush=True)
if __name__=='__main__':main()
