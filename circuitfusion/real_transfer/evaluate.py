"""Checkpoint-only real RTL stress test. Never update weights or training vocabulary."""
import argparse, re, hashlib, importlib.util, json, resource, time
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'closure'
spec=importlib.util.spec_from_file_location('frozen_closure',OLD/'train.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--checked-summaries",type=Path);args=parser.parse_args()
    start=time.monotonic();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
    p=json.loads((ROOT/'PROTOCOL.json').read_text());assert hashlib.sha256((ROOT/'PROTOCOL.json').read_bytes()).hexdigest()==(ROOT/'PROTOCOL.sha256').read_text().strip()
    rs=json.loads((ROOT/'manifest.json').read_text());assert len(rs)>5
    if args.checked_summaries:
        checked=json.loads(args.checked_summaries.read_text());assert set(checked)=={r['sample_id'] for r in rs}
        for r in rs:r['summary']=checked[r['sample_id']]['summary'];r['summary_tokens']=re.findall('[a-z]+',r['summary'].lower())
        p['arms']=['paired','no_graph']
    ds=old.Data(json.loads((OLD/'manifest.json').read_text()))
    rtl=(ds.pad_tokens([r['code'] for r in rs]),ds.pad_tokens([r['summary_tokens'] for r in rs]),ds.pad_graphs([r['graph'] for r in rs]))
    alt=(ds.pad_tokens([r['equivalent_code'] for r in rs]),rtl[1],ds.pad_graphs([r['equivalent_graph'] for r in rs]))
    net=ds.pad_graphs([r['netlist'] for r in rs]);rows=[];embeddings={};weights=[]
    for seed in p['seeds']:
        for arm in p['arms']:
            path=OLD/'results_v1_1'/f'{arm}_seed{seed}.pt';weights.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            model=old.Model(ds);model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True));model.eval();batch=rtl;other=alt
            if arm=='shuffled_edges':batch=(rtl[0],rtl[1],ds.rewired(rtl[2],seed+9000));other=(alt[0],alt[1],ds.rewired(alt[2],seed+9000))
            with torch.inference_mode():
                z=model.rtl(batch,arm)[0];n=model.net(net);az=model.rtl(other,arm)[0];sim=z@n.T
                rank=sim.argsort(1,descending=True);target=torch.arange(len(rs));positions=(rank==target[:,None]).nonzero()[:,1]+1
                # Independent NumPy reconstruction; no same-rank floating ties expected.
                nr=np.argsort(-sim.numpy(),axis=1,kind='stable');np_pos=(nr==np.arange(len(rs))[:,None]).argmax(1)+1
                assert np.array_equal(np_pos,positions.numpy())
                per=[dict(sample_id=r['sample_id'],source=r['source'],family=r['family'],rank=int(positions[i]),r1=int(positions[i])==1,r5=int(positions[i])<=5) for i,r in enumerate(rs)]
                row=dict(seed=seed,arm=arm,recall1=float((positions==1).float().mean()),recall5=float((positions<=5).float().mean()),mrr=float((1/positions.float()).mean()),equivalent_cosine=float((z*az).sum(-1).mean()),per_sample=per)
                if arm=='paired':
                    corrupt=(rtl[0],rtl[1],ds.rewired(rtl[2],seed+9000));rz=model.rtl(corrupt,arm)[0]
                    row['rewired_r1']=float(((rz@n.T).argmax(1)==target).float().mean());row['rewired_embedding_l2']=float(torch.linalg.vector_norm(z-rz,dim=-1).mean())
                rows.append(row);embeddings[f'{arm}_{seed}_rtl']=z.numpy();embeddings[f'{arm}_{seed}_net']=n.numpy();print(json.dumps(row),flush=True)
                if time.monotonic()-start>p['limits']['max_eval_seconds']:raise TimeoutError('evaluation cap')
    oov=[]
    for i,r in enumerate(rs):
        d={'sample_id':r['sample_id']}
        for k in ['code','summary_tokens']:
            d[k+'_oov_fraction']=sum(w not in ds.words for w in r[k])/max(1,len(r[k]))
        for k in ['graph','netlist']:
            d[k+'_oov_fraction']=sum(n[0] not in ds.kinds for n in r[k]['nodes'])/len(r[k]['nodes'])
            d[k+'_width_or_lane_clipped']=sum(n[1]+1>16 or n[2]>16 for n in r[k]['nodes'])
        oov.append(d)
    summaries={}
    for arm in p['arms']:
        a=[x for x in rows if x['arm']==arm];fam={}
        for f in sorted({r['family'] for r in rs}):fam[f]=float(np.mean([x['r1'] for row in a for x in row['per_sample'] if x['family']==f]))
        summaries[arm]={k:float(np.mean([r[k] for r in a])) for k in ['recall1','recall5','mrr','equivalent_cosine']};summaries[arm]['family_r1']=fam;summaries[arm]['macro_family_r1']=float(np.mean(list(fam.values())))
    out=ROOT/('results_api_summary' if args.checked_summaries else 'results');out.mkdir(exist_ok=True);np.savez_compressed(out/'embeddings.npz',**embeddings)
    result=dict(samples=len(rs),sources=len({r['source'] for r in rs}),families=len({r['family'] for r in rs}),chance_r1=1/len(rs),chance_r5=min(5,len(rs))/len(rs),summaries=summaries,runs=rows,oov=oov,weights=weights,numpy_rank_checks=True,resources={'wall_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'torch':torch.__version__,'threads':2},limitations=['strict sample-identity retrieval; cross-source semantic duplicates not exhaustively excluded','source examples and regression tests, not industrial blocks',('per-cone API-generated summaries with explicit post-generation assistant review and edits' if args.checked_summaries else 'summary per design shared across its register cones'),'boundary combinational formal equivalence only, not initial-state or temporal equivalence','port and width distribution differs from synthetic pretraining; clamping/OOV reported','no original backbone, author checkpoint, commercial PPA or new training'])
    (out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summaries']),flush=True)
if __name__=='__main__':main()
