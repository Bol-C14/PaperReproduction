"""Targeted source/identity checks only; no optimization or new data sweep."""
import copy
import hashlib
import importlib.util
import inspect
import itertools
import json
from pathlib import Path
import resource
import sys
import textwrap
import time
import types
import torch
from torch import nn

ROOT=Path(__file__).resolve().parent
C=ROOT.parent
START=time.perf_counter()
torch.set_num_threads(1);torch.set_num_interop_threads(1)
SOURCE=C/'official_pm_source.py'
UPSTREAM=C.parent.parent/'TRACE_DAC26_metadata/tasks/predictive/pm/models/trace_trainer.py'
assert SOURCE.read_bytes()==UPSTREAM.read_bytes()
# Import the entire unchanged upstream module. Its trainer constructor/orchestration is NOT invoked.
# This inert dependency substitution supplies only the inheritance symbol, not any method under test.
pl=types.ModuleType('pytorch_lightning');pl.LightningModule=nn.Module
sys.modules['pytorch_lightning']=pl
spec=importlib.util.spec_from_file_location('trace_upstream_unmodified',SOURCE)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)


def hbytes(value):return hashlib.sha256(value).hexdigest()

def state_hash(model):
    h=hashlib.sha256()
    for key,value in model.state_dict().items():
        h.update(key.encode());h.update(str(value.dtype).encode());h.update(str(tuple(value.shape)).encode())
        h.update(value.contiguous().numpy().tobytes())
    return h.hexdigest()


def truth_feature(op):
    if op=='PI':return [0]*64
    assert op=='AND'
    return [int(((63-i)&1)==1 and (((63-i)>>1)&1)==1) for i in range(64)]


def make_graph(name,npi,fanin_list):
    nodes=[dict(id=i,op='PI',semantic_identity=f'x{i}',inputs=[]) for i in range(npi)]
    for sources in fanin_list:
        nodes.append(dict(id=len(nodes),op='AND',inputs=list(sources)))
    edges=[];levels=[]
    for node in nodes:
        levels.append(0 if not node['inputs'] else 1+max(levels[j] for j in node['inputs']))
        edges.extend(dict(src=j,dst=node['id'],port=port) for port,j in enumerate(node['inputs']))
    return dict(name=name,npi=npi,nodes=nodes,edges=edges,levels=levels,pi_prob=[.5]*npi)


def tensor_graph(saved):
    # Direct edge-list conversion, no graph library/coalescing/deduplication.
    edges=[[e['src'],e['dst']] for e in saved['edges']]
    return types.SimpleNamespace(x=torch.tensor([truth_feature(n['op']) for n in saved['nodes']],dtype=torch.float32),
        prob=torch.tensor(saved['pi_prob']+[0.]*(len(saved['nodes'])-saved['npi'])),
        edge_index=torch.tensor(edges,dtype=torch.long).t().contiguous(),
        forward_level=torch.tensor(saved['levels']),forward_index=torch.arange(len(saved['nodes'])))


def exact(saved):
    outputs=[]
    for bits in itertools.product([0,1],repeat=saved['npi']):
        values=list(bits)
        for node in saved['nodes'][saved['npi']:]:
            a,b=node['inputs'];values.append(values[a]*values[b])
        outputs.append(values[-1])
    return sum(outputs)/len(outputs)


checkpoint=torch.load(C/'official_pm_probability.pth',map_location='cpu',weights_only=True)
model=module.TRACE(num_rounds=1,dim_hidden=128,num_heads=8,num_layers=2)
model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
original=module.TRACETrainer._cop_with_cov
original_text=textwrap.dedent(inspect.getsource(original))
assert original_text.count('max_level = torch.max(graph.forward_level)')==1
corrected_text=original_text.replace('def _cop_with_cov(', 'def corrected(').replace(
    'max_level = torch.max(graph.forward_level)','max_level = torch.max(graph.forward_level) + 1')
namespace={'torch':torch};exec(compile(corrected_text,str(ROOT/'corrected_recurrence.py'),'exec'),namespace)
(ROOT/'corrected_recurrence.py').write_text(corrected_text)
proxy=types.SimpleNamespace();proxy._cop=types.MethodType(module.TRACETrainer._cop,proxy)
graph_dict=make_graph('minimal_two_PI_AND',2,[[0,1]])
g=tensor_graph(graph_dict)
weights_before=state_hash(model)
with torch.no_grad():
    residual=model.pred_prob(model(g))
    out_original=original(proxy,g,residual)
    out_corrected=namespace['corrected'](proxy,g,residual)
    zero=torch.zeros_like(residual)
    oracle_original=original(proxy,g,zero);oracle_corrected=namespace['corrected'](proxy,g,zero)
assert state_hash(model)==weights_before
assert oracle_original[-1].item()==0 and abs(oracle_corrected[-1].item()-.25)<1e-6
assert out_original[-1].item()==0 and abs(out_corrected[-1].item()-(.25+residual[-1].item()))<1e-6
source_record=dict(source_commit='b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70',
    path='tasks/predictive/pm/models/trace_trainer.py',
    permalink='https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/models/trace_trainer.py#L139-L151',
    source_sha256=hbytes(SOURCE.read_bytes()),method_lines=[139,151],bound_lines=[142,143],
    full_module_imported_unchanged=True,dependency_substitution='inert pytorch_lightning.LightningModule=nn.Module inheritance symbol only; trainer constructor/orchestration not invoked',
    correction='Only add +1 to max_level in a separate copied function; original source file unchanged',
    minimal_graph=graph_dict,oracle_exact=.25,zero_residual_original=oracle_original.tolist(),
    zero_residual_corrected=oracle_corrected.tolist(),official_model_residual=residual.squeeze(-1).tolist(),
    identical_weights_input_original=out_original.tolist(),identical_weights_input_corrected=out_corrected.tolist(),
    state_sha256_unchanged=weights_before,
    checkpoint_sha256=hbytes((C/'official_pm_probability.pth').read_bytes()),
    attribution='The loop-bound defect is in pinned upstream source, not introduced by the task port. Prior direct-clamp/dropout bugs are local harness defects, not upstream defects.')
(ROOT/'DEEPEST_LEVEL.json').write_text(json.dumps(source_record,indent=2)+'\n')

pairs=[(make_graph('repeated_shared',2,[[0,0]]),make_graph('distinct_inputs',2,[[0,1]])),
       (make_graph('shared_diamond',6,[[0,1],[0,2],[6,7]]),make_graph('independent_diamond',6,[[0,1],[2,3],[6,7]]))]
# Explicit graph serialization round trip. Repeated edge columns/port positions remain present.
serialized=json.dumps(pairs,sort_keys=True)
(ROOT/'IDENTITY_GRAPHS.json').write_text(serialized+'\n')
reloaded=json.loads((ROOT/'IDENTITY_GRAPHS.json').read_text())
assert reloaded==json.loads(serialized)
assert [e['src'] for e in reloaded[0][0]['edges']]==[0,0]
assert [e['src'] for e in reloaded[0][1]['edges']]==[0,1]
states=[('official',checkpoint['state_dict'])]
for seed in [2026,2027,2028]:
    for arm in ['direct','fsl']:
        states.append((f'{seed}_{arm}',torch.load(C/'weights'/f'{seed}_{arm}_pretrain.pt',map_location='cpu',weights_only=True)))
observations=[]
for state_name,state in states:
    model.load_state_dict(state,strict=True);model.eval()
    for ga,gb in reloaded:
        a=tensor_graph(ga);b=tensor_graph(gb)
        assert not torch.equal(a.edge_index,b.edge_index)
        sequences=[]
        handle=model.aggr_and.register_forward_pre_hook(lambda mod,args:sequences.append(args[0].detach().clone()))
        with torch.no_grad():ha=model(a);seq_a=sequences[:];sequences.clear();hb=model(b);seq_b=sequences[:]
        handle.remove()
        delta=float((ha[-1]-hb[-1]).abs().max())
        sequence_delta=max(float((x-y).abs().max()) for x,y in zip(seq_a,seq_b))
        assert delta==0 and sequence_delta==0
        observations.append(dict(weights=state_name,pair=[ga['name'],gb['name']],
            edge_index_a=a.edge_index.tolist(),edge_index_b=b.edge_index.tolist(),
            operator_sequence_max_abs=sequence_delta,output_embedding_max_abs=delta,
            exact_probabilities=[exact(ga),exact(gb)],edge_column_counts=[a.edge_index.shape[1],b.edge_index.shape[1]],
            tensor_graphs_distinct=True,serialization_roundtrip_preserved=True))
report=dict(upstream_encoder_lines=[54,90],PI_initialization_lines=[56,57],source=source_record['permalink'],
    serialization='Raw semantic node IDs plus explicit port edge list; no dedup/coalescing; tensor edge_index differs',
    observations=observations,
    conclusion='In this pinned PM encoder with identical PI marginal initialization, distinct dependency identities can collapse to the same operator token sequences and output embeddings. This is an encoder-information limitation in these examples, not lost edge information in serialization. No claim about all TRACE modalities/PI encodings.')
(ROOT/'EQUAL_MARGINAL.json').write_text(json.dumps(report,indent=2)+'\n')
resource_report=dict(wall_s=time.perf_counter()-START,cpu_s=time.process_time(),
    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,optimization_steps=0,
    model_states_checked=len(states),graph_pairs=len(pairs),cuda_initialized=torch.cuda.is_initialized())
(ROOT/'FOCUSED_CHECK_COST.json').write_text(json.dumps(resource_report,indent=2)+'\n')
print(json.dumps(dict(source_failure=source_record,ambiguity_first_two=observations[:2],resources=resource_report),indent=2))
