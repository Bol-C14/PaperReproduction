"""Independent integrity/representation checks, run before corrected training."""
import copy,hashlib,json,collections,sys
from pathlib import Path
import numpy as np
import torch
from prepare import assignments,evaluate
from train import Data,Model,fixed_negative_map
ROOT=Path(__file__).resolve().parent

def run():
    rs=json.loads((ROOT/'manifest.json').read_text());ds=Data(rs);groups=collections.defaultdict(list)
    for i,r in enumerate(rs):
        key=hashlib.sha256(b''.join(x[i].numpy().tobytes() for x in ds.graphs['graph'])).hexdigest();groups[key].append(r['sample_id'])
    collisions=[g for g in groups.values() if len(g)>1];assert not collisions,collisions
    assert len({r['sample_id'] for r in rs})==len(rs)
    assert not set(ds.families[ds.train])&set(ds.families[ds.test]);assert len({r['semantic_sha256'] for r in rs})==len(rs)
    proofs=[]
    for r in rs:
        assert set(r['modality_ids'].values())=={r['sample_id']}
        d=ROOT/'data'/r['sample_id'];status=(d/'formal_status.txt').read_text();assert '0 are unproven' in status and 'Equivalence successfully proven!' in status;proofs.append(r['sample_id'])
    unknown={k:int((ds.tokens[k][ds.test]==1).sum()) for k in ds.tokens}
    # Every code view retains its full stream; no modality receives an artificial token disadvantage.
    assert max(len(r[k]) for r in rs for k in ['code','equivalent_code'])<384
    assert len({r['summary'] for r in rs})<len(rs)//10
    assert all(r['sample_id'] not in r['code']+r['equivalent_code']+r['summary_tokens'] for r in rs)
    # Actual graph encoder must ignore arbitrary node order.
    torch.manual_seed(1);torch.set_num_threads(2);model=Model(ds).eval();idx=torch.tensor([0,1]);batch=ds.rtl(idx);g=batch[2];n=g[0].shape[1];perm=torch.randperm(n);reordered=(g[0][:,perm],g[1][:,perm],g[2][:,perm],g[3][:,:,perm][:,:,:,perm])
    with torch.no_grad():
        z=model.rtl(batch,'paired')[0];zp=model.rtl((batch[0],batch[1],reordered),'paired')[0];torch.testing.assert_close(z,zp,rtol=1e-5,atol=1e-6)
        rewired=ds.rewired(g,17)
        a=model.rtl(batch,'no_graph')[0];b=model.rtl((batch[0],batch[1],rewired),'no_graph')[0];torch.testing.assert_close(a,b,rtol=0,atol=0)
        graph_change=float(torch.linalg.vector_norm(z-model.rtl((batch[0],batch[1],rewired),'paired')[0],dim=-1).mean());assert graph_change>0
    for seed in [11,23,37]:fixed_negative_map(ds,seed)
    # Observable corruption must fail independent truth equality, even when synthesis metadata looks plausible.
    r=rs[0];d=ROOT/'data'/r['sample_id'];m=next(iter(json.loads((d/'gate.json').read_text())['modules'].values()));m['ports']['next_state']['bits']=['0']*r['bits'];got,_=evaluate(m,assignments(r['bits'],r['external']));assert not np.array_equal(got,np.load(d/'reference.npy'))
    # Detect family-template aliases even when names differ.
    def skeleton(t):
        if isinstance(t,int):return 'K'
        if isinstance(t,str):return t
        op,*xs=t;xs=[skeleton(x) for x in xs]
        if op in ['and','or','xor','add','mul']:xs=sorted(xs,key=str)
        return [op,*xs]
    groups=collections.defaultdict(set)
    for r in rs:
        if r['expression'] is not None:groups[json.dumps(skeleton(r['expression']))].add(r['family'])
    cross=[sorted(fs) for fs in groups.values() if any(f<16 for f in fs) and any(f>=16 for f in fs)];assert not cross
    result={'samples':len(rs),'unique_rtl_graph_tensors':len(rs),'graph_tensor_collisions':0,'formal_proof_files_checked':len(proofs),'family_disjoint':True,'commutative_canonical_skeleton_cross_split_aliases':cross,'truth_table_disjoint':True,'modality_ids_valid':True,'node_order_invariance_checked':True,'graph_removal_independent_of_graph_checked':True,'random_paired_graph_sensitivity_l2':graph_change,'tampered_outputs_rejected':True,'unknown_test_tokens':unknown,'max_code_tokens':max(len(r[k]) for r in rs for k in ['code','equivalent_code']),'summary_classes':len({r['summary'] for r in rs})}
    (ROOT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':run()
