"""Real checkpoint->real repaired Trainer structural load; external encoder fails closed.

No BERT embedding or policy inference. SparseTensor is an import placeholder because
only module construction/state loading occurs; its use would raise immediately.
"""
import sys,types,pathlib,json,inspect
import torch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'port/repaired'))
class EncoderUnavailable(torch.nn.Module):
 def forward(self,*a,**kw):raise RuntimeError('BERT asset gated: no inference authorized by protocol gate3')
class NoEncoder:
 @staticmethod
 def from_pretrained(*a,**kw):return EncoderUnavailable()
class NoSparse:
 def __init__(self,*a,**kw):raise RuntimeError('torch_sparse not installed; structural-load check only')
sys.modules['transformers']=types.SimpleNamespace(BertModel=NoEncoder)
sys.modules['torch_sparse']=types.SimpleNamespace(SparseTensor=NoSparse)
from trainer import Trainer
p=ROOT/'assets/nn_model.pt'
model=Trainer(preTrainedGraphModel=str(p),device='cpu')
loaded=model.step_model.state_dict()
expected=torch.load(p,map_location='cpu',weights_only=True)
assert loaded.keys()==expected.keys()
assert all(torch.equal(loaded[k],expected[k]) for k in expected)
assert not any(k.startswith('bert') for k in expected)
try:model.step_model.forward(None)
except Exception as exc:
 # None is not a graph; invoke the fail-closed external model directly as well.
 import LogicSynthesisPolicy
 try:LogicSynthesisPolicy.bert_model(None)
 except RuntimeError as gate:gate_message=str(gate)
 else:raise AssertionError('external encoder must fail closed')
else:raise AssertionError('must not produce policy from unavailable BERT')
result={'status':'strict_state_load_pass','keys':len(expected),'all_tensors_equal_to_supplied_checkpoint':True,'device':'cpu','external_bert_state_in_checkpoint':False,'inference_performed':False,'import_placeholders':['BertModel:fail_closed_no_weights_no_outputs','SparseTensor:fail_closed_no_execution'],'gate_message':gate_message,'limitation':'structural compatibility only; not end-to-end CPU inference compatibility'}
(ROOT/'results/structural_loading.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
