"""AST-isolated upstream tests; no ABC, external assets, or upstream import side effects."""
import ast,io,json,pathlib,sys,types,unittest,hashlib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'port'))
from mechanism import *
from retrieve import retrieve
import torch

def function_from(path,name,namespace):
 tree=ast.parse(path.read_text())
 node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
 return namespace[name]

def rollout_commands(version,depth):
 calls=[]
 fake_np=types.SimpleNamespace(random=types.SimpleNamespace(randint=lambda lo,hi:0))
 ns={'np':fake_np,'synthesisOpToPosDic':dict(enumerate(ACTIONS)),
     'os':types.SimpleNamespace(system=calls.append),'re':__import__('re'),
     'open':lambda *a:io.StringIO('x 2 x x x x 3 x x x\n')}
 fn=function_from(ROOT/version/'LogicSynthesisEnv.py','get_montecarlo_return',ns)
 env=types.SimpleNamespace(ep_length=10,lib='fixture.lib',logFile='fake.log',baselineReturn=10)
 fn(env,2,'fixture.aig',depth)
 command=calls[0].split('read_lib fixture.lib;')[1].split('map ;')[0]
 return command.split(';')[:-1]

class ContractTests(unittest.TestCase):
 def test_original_and_repaired_horizon(self):
  for depth in (0,1,8,9):
   self.assertEqual(len(rollout_commands('upstream',depth)),11-depth)
   self.assertEqual(len(rollout_commands('port/repaired',depth)),10-depth)
 def test_supplied_checkpoint_argument(self):
  seen=[]
  for version,expected in [('upstream',None),('port/repaired','supplied-policy.pt')]:
   tree=ast.parse((ROOT/version/'cosine_scorer.py').read_text())
   nodes=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='trainer' for t in n.targets)]
   ns={'Trainer':lambda **kw:seen.append(kw['preTrainedGraphModel']),'modelPath':'supplied-policy.pt'}
   for n in nodes:exec(compile(ast.Module(body=[n],type_ignores=[]),'scorer_assignment','exec'),ns)
   self.assertEqual(seen[-1],expected)
 def test_rounding_gradient_and_inference_preservation(self):
  p=ROOT/'upstream/LogicSynthesisPolicy.py';tree=ast.parse(p.read_text())
  node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value).startswith('torch.round'))
  x=torch.tensor([.1234,.9987],requires_grad=True);ns={'torch':torch,'aigEmbedding':x}
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
  ns['aigEmbedding'].sum().backward();self.assertEqual(x.grad.tolist(),[0.,0.])
  y=x.detach().clone().requires_grad_();y.sum().backward();self.assertEqual(y.grad.tolist(),[1.,1.])
  # Patched AST retains rounding in eval, avoids it during training.
  pt=ast.parse((ROOT/'port/repaired/LogicSynthesisPolicy.py').read_text())
  guarded=next(n for n in ast.walk(pt) if isinstance(n,ast.If) and ast.unparse(n.test)=='not self.training')
  for training in [True,False]:
   z=x.detach().clone().requires_grad_();ns={'torch':torch,'aigEmbedding':z,'self':types.SimpleNamespace(training=training)}
   exec(compile(ast.Module(body=[guarded],type_ignores=[]),'patched_round','exec'),ns)
   self.assertTrue(torch.equal(ns['aigEmbedding'],z if training else torch.round(z,decimals=3)))
 def test_train_only_retrieval_provenance(self):
  bank={'checkpoint_sha256':'fixture-only','encoder_id':'synthetic-test-only','training_designs':['train_a'], 'heldout_designs':['test_b'],'embeddings':{'train_a':[1,0]},'threshold':.007,'scaling':100}
  query={'checkpoint_sha256':'fixture-only','encoder_id':'synthetic-test-only','design':'test_b','embedding':[0,1]}
  self.assertEqual(retrieve(query,bank)['cosine_distance'],1)
  with self.assertRaises(ValueError):retrieve(dict(query,checkpoint_sha256='different'),bank)
  with self.assertRaises(ValueError):retrieve(query,dict(bank,training_designs=['test_b'],embeddings={'test_b':[1,0]}))
 def test_safe_checkpoint_tensor_load(self):
  p=ROOT/'assets/nn_model.pt';s=torch.load(p,map_location='cpu',weights_only=True)
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'d4747eeff16c7247acf8f1480a33f2239a1a51adaac78a0a6e915c5ba12164f5')
  self.assertEqual(tuple(s['dense_p2.weight'].shape),(7,256))
  self.assertTrue(all(v.device.type=='cpu' for v in s.values()))
 def test_gate_direction_and_retrieval(self):
  self.assertAlmostEqual(nearest_distance([1,0],[[1,0],[0,1]]),0)
  self.assertAlmostEqual(nearest_distance([1,0],[[0,1]]),1)
  self.assertGreater(guidance_exponent(0),guidance_exponent(.1))
  self.assertAlmostEqual(guidance_exponent(.007),.5)
  p=[.1,.1,.1,.1,.1,.1,.4]
  self.assertEqual(prior_weights(p,0),[1]*7);self.assertEqual(prior_weights(p,1),p)
  with self.assertRaises(ValueError): nearest_distance([0,0],[[1,0]])
 def test_budget_and_zero_beta_are_not_pure_search(self):
  text=(ROOT/'upstream/mcts.py').read_text()
  self.assertLess(text.index('first_node_rolloutReturn',text.index('def synergy_test_episode')),text.index('while testBudget<maxTestBudget',text.index('def synergy_test_episode')))
  # Original rollout first action always chooses argmax. Flattening priors ties at action0.
  self.assertEqual(max(range(7),key=prior_weights([.1]*6+[.4],0).__getitem__),0)
if __name__=='__main__':unittest.main(verbosity=2)
