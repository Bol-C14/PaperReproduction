"""Bounded CPU fixture pilot. No optimizer, training, remote unpickling or CUDA."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,math,resource,time,traceback,unittest
import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.utils import scatter
from upstream_loader import load
from static_checkpoint import inspect_pickle

ROOT=Path(__file__).resolve().parent
START=time.monotonic()
torch.set_num_threads(1)
UP=load(capacity=16)
ARGS=SimpleNamespace(hidden=128,tf_arch='sparse',mlp_hidden=128,mlp_layer=3,norm_layer='batchnorm')
METRICS={'protocol':'PROTOCOL.md','seeds':[0,1,2],'device':'cpu','versions':{'torch':torch.__version__,'pyg':__import__('torch_geometric').__version__},'torch_cuda_build':torch.version.cuda,'adaptations':UP.manifest,'checks':{},'runs':[]}
RAW={}

GATES=[0,0,2,1,2,1,2,1]
EDGES=[(0,2),(0,3),(1,3),(3,4),(2,5),(1,5),(1,6),(0,7),(6,7)]
EXPECTED=np.array([[0,0,1,0,1,0,1,0],[0,1,1,0,1,1,0,0],[1,0,0,0,1,0,1,1],[1,1,0,1,0,0,0,0]],dtype=np.int64)


def truth_table(edges=EDGES):
    rows=[]
    for a,b in [(0,0),(0,1),(1,0),(1,1)]:
        values={0:a,1:b}
        pending=set(range(2,8))
        while pending:
            progressed=False
            for node in sorted(pending):
                inputs=[s for s,t in edges if t==node]
                if all(s in values for s in inputs):
                    if GATES[node]==2:
                        assert len(inputs)==1; values[node]=1-values[inputs[0]]
                    else:
                        assert len(inputs)==2; values[node]=values[inputs[0]] & values[inputs[1]]
                    pending.remove(node);progressed=True
            if not progressed:raise ValueError('cycle')
        rows.append([values[i] for i in range(8)])
    return np.array(rows)


def graph(order=None, subset=None, edges=EDGES):
    """order maps new global IDs to old semantic IDs; all attributes relabel."""
    order=list(range(8)) if order is None else list(order)
    inverse={old:new for new,old in enumerate(order)}
    newedges=[(inverse[s],inverse[t]) for s,t in edges]
    levels={inverse[0]:0,inverse[1]:0}
    pending=set(range(8))-set(levels)
    while pending:
        for node in sorted(pending):
            inputs=[s for s,t in newedges if t==node]
            if all(s in levels for s in inputs):
                levels[node]=max(levels[s] for s in inputs)+1;pending.remove(node)
    subset=list(range(8)) if subset is None else list(subset)
    local={g:i for i,g in enumerate(subset)}
    local_edges=[(local[s],local[t]) for s,t in newedges if s in local and t in local]
    ancestors={i:set() for i in subset}
    for node in sorted(subset,key=lambda n:levels[n]):
        for source,target in newedges:
            if target==node and source in ancestors:
                ancestors[node].add(source);ancestors[node].update(ancestors[source])
    virtual=[(local[a],local[b]) for b in subset for a in sorted(ancestors[b])]
    out_and=[sum(s==i and GATES[order[t]]==1 for s,t in newedges) for i in subset]
    out_not=[sum(s==i and GATES[order[t]]==2 for s,t in newedges) for i in subset]
    tt=truth_table(edges)
    return Data(gate=torch.tensor([GATES[order[i]] for i in subset]).view(-1,1),nodes=torch.tensor(subset),forward_level=torch.tensor([levels[i] for i in subset]),forward_index=torch.arange(len(subset)),edge_index=torch.tensor(local_edges,dtype=torch.long).T.contiguous(),global_virtual_edge=torch.tensor(virtual,dtype=torch.long).T.contiguous(),prob=torch.tensor([tt[:,order[i]].mean() for i in subset],dtype=torch.float32),out_and=torch.tensor(out_and),out_not=torch.tensor(out_not),batch=torch.zeros(len(subset),dtype=torch.long))


def make_model(seed,repaired=False):
    torch.manual_seed(seed);np.random.seed(seed)
    cls=UP.RepairedDeepGate4 if repaired else UP.DeepGate4
    return cls(ARGS).eval()


def initial_history(model,seed):
    np.random.seed(seed)
    model.reset_history(graph())
    return (model.hf_history.emb.clone(),model.hs_history.emb.clone())


def initialize(model,initial,order=None,misalign=False):
    order=list(range(8)) if order is None else list(order)
    model.reset_history(graph(order))
    for target,source in zip([model.hf_history,model.hs_history],initial):
        target.emb.zero_();target.emb[:8].copy_(source[order])
    if misalign:
        model.hs_history.emb[[0,1]]=model.hs_history.emb[[1,0]].clone()


@torch.no_grad()
def forward(model,g):
    model(g,large_ckt=True,phase='test')
    ids=torch.arange(8)
    return torch.cat([model.hf_history.pull(ids),model.hs_history.pull(ids)],dim=1).clone()


class Pilot(unittest.TestCase):
    def test_01_known_logic_labels(self):
        tt=truth_table()
        np.testing.assert_array_equal(tt,EXPECTED)
        probabilities=tt.mean(axis=0)
        np.testing.assert_array_equal(probabilities,[.5,.5,.5,.25,.75,.25,.5,.25])
        distances=(tt[:,:,None]!=tt[:,None,:]).mean(axis=0)
        self.assertEqual(float(distances[0,2]),1.0)
        self.assertEqual(float(distances[3,4]),1.0)
        self.assertEqual(float(distances[3,5]),.5)
        METRICS['checks']['logic']={'assignments':[[0,0],[0,1],[1,0],[1,1]],'truth_table_rows':tt.tolist(),'probabilities':probabilities.tolist(),'pairwise_hamming_distance':distances.tolist(),'label_assertions':True}

    def test_02_history_and_native_scatter(self):
        history=UP.FixtureHistory(8,4)
        self.assertEqual(history.emb.numel()*history.emb.element_size(),128)
        self.assertFalse(history.emb.is_pinned())
        ids=torch.tensor([1,3]);values=torch.arange(8).float().view(2,4)
        history.push(values,ids)
        torch.testing.assert_close(history.pull(ids),values,rtol=0,atol=0)
        reference=UP.OriginalHistory.__new__(UP.OriginalHistory)
        torch.nn.Module.__init__(reference)
        reference.num_embeddings=8;reference.embedding_dim=4
        reference.emb=torch.zeros(8,4);reference._device=torch.device('cpu')
        reference.push(values,ids)
        torch.testing.assert_close(history.pull(),reference.pull(),rtol=0,atol=0)
        history.reset_parameters();self.assertEqual(history.emb.count_nonzero().item(),0)
        with self.assertRaises(IndexError):history.pull(torch.tensor([8]))
        with self.assertRaises(IndexError):history.push(torch.ones(1,4),torch.tensor([-1]))
        history.push(torch.ones(2,4),n_id=torch.tensor([2,3]),offset=torch.tensor([2]),count=torch.tensor([2]))
        self.assertEqual(history.pull(torch.tensor([2,3])).sum().item(),8)
        reduced=scatter(torch.tensor([[1.,2.],[3.,6.],[7.,8.]]),torch.tensor([1,1,3]),dim=0,reduce='mean')
        torch.testing.assert_close(reduced,torch.tensor([[0.,0.],[2.,4.],[0.,0.],[7.,8.]]),rtol=0,atol=0)
        METRICS['checks']['history']={'bounded_cpu_bytes_8x4':128,'upstream_push_pull_parity':True,'reset_and_bounds':True,'native_scatter_mean_reference':True}

    def test_03_static_reader_rejects_callable(self):
        # Unsupported callable is rejected before REDUCE; nothing is executed.
        with self.assertRaisesRegex(ValueError,'Unsupported GLOBAL'):
            inspect_pickle(b'\x80\x02cos\nsystem\n)R.')
        METRICS['checks']['checkpoint_safety']={'unsupported_GLOBAL_rejected':True,'torch_load_used':False,'pickle_load_used':False}

    def test_04_checkpoint_coverage(self):
        model=make_model(0)
        own=model.state_dict();tokenizer=model.tokenizer.state_dict()
        rows=json.loads((ROOT/'checkpoint_metadata.json').read_text())
        results=[]
        for row in rows:
            state=row['state_dict']
            direct=[k for k,v in state.items() if k in own and list(own[k].shape)==v['shape']]
            token=[k for k,v in state.items() if k in tokenizer and list(tokenizer[k].shape)==v['shape']]
            missing=[k for k in own if k not in {'tokenizer.'+name for name in token}]
            transformer=[k for k in own if k.startswith('transformer.')]
            results.append({'file':row['file'],'epoch':row['epoch'],'checkpoint_tensors':len(state),'direct_full_model_matches':direct,'tokenizer_matches':token,'tokenizer_total':len(tokenizer),'full_model_tensors':len(own),'full_model_missing_after_tokenizer_prefix':missing,'transformer_tensor_count':len(transformer),'transformer_coverage':0,'full_model_compatible':False})
            self.assertEqual(len(token),len(state));self.assertEqual(len(token),len(tokenizer))
            self.assertTrue(transformer);self.assertTrue(missing)
        (ROOT/'checkpoint_coverage.json').write_text(json.dumps(results,indent=2)+'\n')
        METRICS['checks']['checkpoint_coverage']=[{k:v for k,v in row.items() if not isinstance(v,list)} for row in results]
        METRICS['checks']['architecture']={'tokenizer_module':type(model.tokenizer).__module__,'sparse_module':type(model.transformer).__module__,'sparse_layers':len(model.transformer.tf_layers),'parameters':sum(t.numel() for t in model.parameters()),'four_history_bytes':sum(getattr(model,n).emb.numel()*getattr(model,n).emb.element_size() for n in ['hf_history','hs_history','hf_pooling_history','hs_pooling_history'])}
        self.assertEqual(METRICS['checks']['architecture']['parameters'],7371314)
        self.assertEqual(METRICS['checks']['architecture']['four_history_bytes'],32768)

    def test_05_forward_permutation_controls(self):
        permutations=[[1,0,6,3,2,7,5,4],[7,2,0,5,1,4,6,3]]
        for seed in [0,1,2]:
            for repaired in [False,True]:
                variant='structural_history_repair' if repaired else 'upstream_semantics'
                with self.subTest(seed=seed,variant=variant):
                    model=make_model(seed,repaired);initial=initial_history(model,seed)
                    initialize(model,initial);baseline=forward(model,graph())
                    self.assertEqual(tuple(baseline.shape),(8,256));self.assertTrue(torch.isfinite(baseline).all())
                    RAW[f'{variant}_seed{seed}_canonical']=baseline.numpy()
                    record={'seed':seed,'variant':variant,'embedding_shape':list(baseline.shape),'finite':True,'l2_norm':float(baseline.norm()),'embedding_sha256':hashlib.sha256(baseline.numpy().tobytes()).hexdigest(),'permutations':[]}
                    non_pi=torch.tensor([2,3,4,5,6,7])
                    stream_delta=float((baseline[non_pi,:128]-baseline[non_pi,128:]).abs().max())
                    record['non_pi_function_vs_structure_max_abs']=stream_delta
                    if repaired:self.assertGreater(stream_delta,1e-6)
                    else:self.assertEqual(stream_delta,0.0)
                    # Identical cone revisited: already-updated histories stay unchanged.
                    repeated=forward(model,graph());torch.testing.assert_close(repeated,baseline,rtol=0,atol=0)
                    record['update_once_repeat_max_abs']=float((repeated-baseline).abs().max())
                    for pi,order in enumerate(permutations):
                        initialize(model,initial,order);permuted=forward(model,graph(order))
                        restored=permuted[torch.argsort(torch.tensor(order))]
                        delta=float((restored-baseline).abs().max())
                        torch.testing.assert_close(restored,baseline,atol=1e-5,rtol=1e-4)
                        record['permutations'].append({'order':order,'max_abs':delta,'allclose':True})
                        RAW[f'{variant}_seed{seed}_permutation{pi}']=permuted.numpy()
                    initialize(model,initial,misalign=True);misaligned=forward(model,graph())
                    alignment_delta=float((misaligned-baseline).abs().max())
                    self.assertGreater(alignment_delta,1e-6)
                    record['misaligned_PI_history_max_abs']=alignment_delta
                    changed_edges=[(0 if s==2 and t==5 else s,t) for s,t in EDGES]
                    changed_labels=truth_table(changed_edges)
                    self.assertFalse(np.array_equal(changed_labels,EXPECTED))
                    initialize(model,initial);changed=forward(model,graph(edges=changed_edges))
                    logic_delta=float((changed-baseline).abs().max())
                    self.assertGreater(logic_delta,1e-6)
                    record['altered_logic_embedding_max_abs']=logic_delta
                    record['altered_logic_truth_table_bit_changes']=int((changed_labels!=EXPECTED).sum())
                    # Two ordered overlapping cones: exercise pull/reuse, not equality to full graph.
                    initialize(model,initial)
                    first=graph(subset=[0,1,2,3,6]);forward(model,first)
                    saved=model.hf_history.emb[[2,3,6]].clone()
                    streamed=forward(model,graph())
                    torch.testing.assert_close(model.hf_history.emb[[2,3,6]],saved,rtol=0,atol=0)
                    self.assertTrue(torch.isfinite(streamed).all())
                    record['two_cone_update_once']=True
                    record['two_cone_vs_single_cone_max_abs']=float((streamed-baseline).abs().max())
                    RAW[f'{variant}_seed{seed}_two_cones']=streamed.numpy()
                    METRICS['runs'].append(record)

    def test_06_fixture_capacity_does_not_change_outputs(self):
        reference=make_model(0)
        initial=initial_history(reference,0)
        initialize(reference,initial)
        expected=forward(reference,graph())
        smaller=load(capacity=8)
        torch.manual_seed(0)
        model=smaller.DeepGate4(ARGS).eval()
        np.random.seed(0)
        model.reset_history(graph())
        actual=forward(model,graph())
        torch.testing.assert_close(actual,expected,rtol=0,atol=0)
        METRICS['checks']['capacity_equivalence']={'capacities':[8,16],'max_abs':float((actual-expected).abs().max()),'exact_equal':True}


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Pilot)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    METRICS['test_result']={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful()}
    METRICS['elapsed_seconds']=time.monotonic()-START
    METRICS['process_max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (ROOT/'raw_metrics.json').write_text(json.dumps(METRICS,indent=2)+'\n')
    np.savez_compressed(ROOT/'raw_embeddings.npz',**RAW)
    raise SystemExit(0 if result.wasSuccessful() else 1)
