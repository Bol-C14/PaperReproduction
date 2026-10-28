"""Frozen bounded CPU encoder milestone; no training or downstream execution."""
import hashlib
import json
import pathlib
import random
import resource
import time
from types import SimpleNamespace

import numpy as np
import torch
import torch_geometric

from adapter import load_encoder_classes
from paired_circuits import build_and_validate

ROOT=pathlib.Path(__file__).resolve().parent
SEED=208


def seed():
    random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)


def graph_fields(graph,prefix):
    nodes=graph['nodes']; n=len(nodes)
    edges=[(p,i) for i,node in enumerate(nodes) for p in node['pins']]
    edge=torch.tensor(edges,dtype=torch.long).T.contiguous()
    forward=[]
    for node in nodes:
        forward.append(0 if not node['pins'] else max(forward[p] for p in node['pins'])+1)
    successors=[[] for _ in nodes]
    for p,i in edges:successors[p].append(i)
    backward=[0]*n
    for i in reversed(range(n)):
        if successors[i]:backward[i]=1+max(backward[j] for j in successors[i])
    if prefix:
        gate=[{'PI':0,'AND':1,'NOT':2}[node['gate']] for node in nodes]
        features=torch.nn.functional.one_hot(torch.tensor(gate),num_classes=3).float()
    else:
        gate=[0 if node['cell']=='PI' else 1 for node in nodes]
        features=torch.tensor([[int(b) for b in ((node.get('tt','01'))*(64//len(node.get('tt','01'))))]
                               for node in nodes],dtype=torch.float32)
    return {prefix+'x':features,prefix+'edge_index':edge,
            prefix+'gate':torch.tensor(gate,dtype=torch.float32).reshape(n,1),
            prefix+'batch':torch.zeros(n,dtype=torch.long),
            prefix+'forward_index':torch.arange(n),prefix+'backward_index':torch.arange(n),
            prefix+'forward_level':torch.tensor(forward),prefix+'backward_level':torch.tensor(backward)}


def strict_checkpoint(model,name):
    path=ROOT/'downloads'/f'{name}.pth'
    checkpoint=torch.load(path,map_location='cpu',weights_only=True)
    raw=checkpoint['state_dict']
    state={k.removeprefix('module.'):v for k,v in raw.items()}
    expected=model.state_dict()
    missing=sorted(set(expected)-set(state));unexpected=sorted(set(state)-set(expected))
    bad_shapes=[k for k in set(expected)&set(state) if expected[k].shape!=state[k].shape]
    bad_dtypes=[k for k in set(expected)&set(state) if expected[k].dtype!=state[k].dtype]
    report={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'epoch':checkpoint.get('epoch'),'metadata_keys':list(checkpoint),
            'model_state_tensors':len(expected),'checkpoint_state_tensors':len(state),
            'model_state_elements':sum(t.numel() for t in expected.values()),
            'missing':missing,'unexpected':unexpected,'bad_shapes':bad_shapes,'bad_dtypes':bad_dtypes,
            'training_parent_lineage':'unknown','strict':True}
    if missing or unexpected or bad_shapes or bad_dtypes:
        report['compatible']=False
        return report
    model.load_state_dict(state,strict=True);model.eval()
    report['compatible']=True;report['model_tensor_coverage']=1.0
    report['all_checkpoint_tensors_finite']=all(bool(torch.isfinite(t).all()) for t in state.values())
    assert report['all_checkpoint_tensors_finite']
    return report


def infer(model,graph):
    seed()
    with torch.inference_mode():
        hs,hf=model(graph);prediction=model.pred_prob(hf).reshape(-1)
    assert hs.shape==hf.shape and hs.shape[1]==128
    assert all(bool(torch.isfinite(x).all()) for x in [hs,hf,prediction])
    return hs,hf,prediction


def attention_parity(module):
    # Independent edge-by-edge softmax/sum checks PyG's CPU attention execution.
    seed();x=torch.randn(4,module.msg_q.in_features)
    edges=torch.tensor([[0,1,0],[2,2,3]],dtype=torch.long)
    with torch.inference_mode():
        actual=module(x,edges)
        reference=torch.zeros_like(actual)
        for dest in [2,3]:
            src=edges[0,edges[1]==dest]
            query=module.msg_q(x[dest]).expand(len(src),-1)
            key=module.msg_k(x[src])
            alpha=torch.softmax(module.attn_lin(torch.cat([query,key],dim=-1)),dim=0)
            reference[dest]=(module.msg_v(x[src])*alpha).sum(dim=0)
    error=float((actual-reference).abs().max())
    assert error<1e-6
    return {'max_abs_error':error,'tolerance':1e-6,'passed':True}


def main():
    started=time.time();torch.set_num_threads(2);torch.set_num_interop_threads(1);seed()
    # Verify immutable source snapshots before importing any upstream code.
    assets=json.loads((ROOT.parent/'assets.json').read_text()); verified=[]
    for item in assets['source_file_manifest']:
        path=ROOT.parent/item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],str(path)
        verified.append(item['path'])
    pairs,integrity=build_and_validate()
    AIG,PM=load_encoder_classes();models={'aig':AIG(dim_hidden=128),'pm':PM(dim_hidden=128,aggr='dg2')}
    # The full upstream AIG class fails strict loading: its unused connectivity
    # head has no released weights. Narrow only this named inference contract.
    import inspect
    assert 'connect_head' not in inspect.getsource(models['aig'].forward)
    assert 'connect_head' not in inspect.getsource(models['aig'].pred_prob)
    del models['aig'].connect_head
    compatibility={view:strict_checkpoint(model,f'{view}_dg2') for view,model in models.items()}
    compatibility['aig']['contract']='encoder forward + probability readout; connectivity head removed'
    compatibility['aig']['full_upstream_model_compatible']=False
    compatibility['aig']['omitted_untrained_head']='connect_head (16 state tensors)'
    compatibility['pm']['contract']='full upstream PM DG2 class'
    compatibility['pm']['full_upstream_model_compatible']=True
    (ROOT/'results/compatibility.json').write_text(json.dumps(compatibility,indent=2)+'\n')
    if not all(r['compatible'] for r in compatibility.values()):
        raise RuntimeError('strict checkpoint architecture mismatch; stop before inference')
    parity={'aig_attention':attention_parity(models['aig'].aggr_and_func),
            'pm_attention':attention_parity(models['pm'].aggr_cell_func)}
    results=[];first_graph=None;first_outputs=None
    for pair in pairs:
        graph=SimpleNamespace(**graph_fields(pair['pm'],''),**graph_fields(pair['aig'],'aig_'))
        item={'id':pair['id'],'parent':pair['parent'],'split':pair['split'],'views':{}}
        if first_graph is None:first_graph=graph;first_outputs={}
        for view,model in models.items():
            t=time.perf_counter();hs,hf,pred=infer(model,graph);elapsed=time.perf_counter()-t
            if pair is pairs[0]:first_outputs[view]=(hs.clone(),hf.clone(),pred.clone())
            exact=torch.tensor(pair['exact_probabilities'][view])
            graph_def=pair[view]
            interior=[i for i,n in enumerate(graph_def['nodes']) if n['pins']]
            po=graph_def['outputs'][0]
            item['views'][view]={'nodes':len(graph_def['nodes']),'hs_shape':list(hs.shape),
              'hf_shape':list(hf.shape),'finite':True,'seconds':elapsed,
              'all_node_probability_mae':float((pred-exact).abs().mean()),
              'internal_node_probability_mae':float((pred[interior]-exact[interior]).abs().mean()),
              'po_probability_prediction':float(pred[po]),'po_exact_probability':float(exact[po]),
              'predicted_probability_by_node':pred.tolist(),'exact_probability_by_node':exact.tolist(),
              'embedding_sha256':hashlib.sha256(torch.cat([hs,hf],dim=1).numpy().tobytes()).hexdigest()}
        results.append(item)
    repeat={}
    for view,model in models.items():
        actual=infer(model,first_graph)
        error=max(float((a-b).abs().max()) for a,b in zip(actual,first_outputs[view]))
        repeat[view]={'max_abs_error':error,'identical':error==0.0}
        assert error==0.0
    output={'status':'completed_encoder_milestone','protocol':'PROTOCOL.md plus PROTOCOL_AMENDMENTS.md',
       'runtime':{'python':__import__('sys').version,'torch':torch.__version__,'torch_geometric':torch_geometric.__version__,
                  'numpy':np.__version__,'device':'cpu','threads':torch.get_num_threads(),'seed':SEED},
       'upstream_source_hashes_verified':len(verified),'compatibility':compatibility,'integrity':integrity,
       'attention_cpu_parity':parity,'fixed_seed_repeat':repeat,'cases':results,
       'elapsed_seconds':time.time()-started,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'claims':{'strict_named_inference_contract_compatibility':True,'full_aig_model_compatibility':False,
                 'real_checkpoint_encoder_inference':True,
                 'synthetic_paired_functional_integrity':True,'parent_disjoint_fixture':True,
                 'pretraining_parent_disjointness':False,'fusion_verified':False,'training':False,
                 'mapping_executed':False,'eco_executed':False,'paper_results_reproduced':False}}
    for name,value in [('paired_circuits.json',pairs),('integrity_results.json',integrity),('pilot_results.json',output)]:
        (ROOT/'results'/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='cases'},indent=2))
    print('cases',len(results))


if __name__=='__main__':main()
