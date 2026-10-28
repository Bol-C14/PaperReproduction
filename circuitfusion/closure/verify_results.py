"""Independent score/ridge/retrieval checks on frozen local checkpoints; no training."""
import json,hashlib,resource,time
from pathlib import Path
import numpy as np
import torch
from train import Data,Model
ROOT=Path(__file__).resolve().parent

def main():
    start=time.monotonic();torch.set_num_threads(2);ds=Data(json.loads((ROOT/'manifest.json').read_text()));out=ROOT/'results_v1_1';saved=json.loads((out/'metrics.json').read_text());checks=[]
    for row in saved['runs']:
        seed=row['seed'];arm=row['arm'];model=Model(ds);model.load_state_dict(torch.load(out/f'{arm}_seed{seed}.pt',map_location='cpu',weights_only=True));model.eval()
        with torch.no_grad():
            indices=torch.arange(len(ds.rs));batch=ds.rtl(indices)
            if arm=='shuffled_edges':batch=(batch[0],batch[1],ds.rewired(batch[2],seed+9000))
            z=model.rtl(batch,arm)[0];net=model.net(ds.net(indices));scores=(z[ds.test]@net[ds.test].T).numpy();truth=np.diag(scores);strict=(truth>np.max(np.where(np.eye(len(scores),dtype=bool),-np.inf,scores),axis=1));possible=truth>=scores.max(1);r1=np.array(row['metrics']['per_sample_r1'],dtype=bool);assert np.all(~strict|r1) and np.all(~r1|possible)
            order=np.argsort(-scores,axis=1,kind='stable');r5=np.any(order[:,:5]==np.arange(len(scores))[:,None],axis=1);scores5=np.take_along_axis(scores,order[:,:5],axis=1)[:,-1];ties5=truth==scores5
            r5saved=np.array(row['metrics']['per_sample_r5'],dtype=bool);assert np.all(r5[ties5==False]==r5saved[ties5==False])
        # Reconstruct every retrieval pool independently: train-only and leave-family-out.
        zn=z.numpy();train=ds.train.numpy();test=ds.test.numpy();labels=np.log1p(ds.labels);retrieve=[]
        for i in range(len(ds.rs)):
            eligible=[j for j in train if i in test or ds.families[j]!=ds.families[i]]
            assert all(ds.rs[j]['split']=='train' for j in eligible)
            if i in train:assert all(ds.families[j]!=ds.families[i] for j in eligible)
            nearest=sorted(eligible,key=lambda j:-(zn[i]@zn[j]))[:3];retrieve.append(np.mean(labels[nearest],axis=0))
        features=np.column_stack([zn,ds.counts,np.array(retrieve)]);mean=features[train].mean(0);std=features[train].std(0);std[std<1e-8]=1;xx=np.column_stack([(features-mean)/std,np.ones(len(features))]);reg=np.eye(xx.shape[1]);reg[-1,-1]=0;coef=np.linalg.solve(xx[train].T@xx[train]+reg,xx[train].T@labels[train]);errors=np.abs(xx[test]@coef-labels[test]);reference=np.array(row['metrics']['downstream']['retrieval_augmented']['per_sample_log1p_abs_error'])
        np.testing.assert_allclose(errors,reference,atol=1e-7,rtol=1e-7)
        checks.append({'seed':seed,'arm':arm,'numpy_rank_metrics_agree':True,'r1_exact_tie_rows':int((possible&~strict).sum()),'r5_boundary_tie_rows':int(ties5.sum()),'retrieval_pools_train_only_and_family_excluded':True,'ridge_errors_recomputed_agree':True})
    result={'checks':checks,'all_passed':True,'wall_seconds':time.monotonic()-start,'limitations':'uses stored learned representations and a separately written metric/retrieval reconstruction; not an independent implementation of the neural encoders'};(out/'independent_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
