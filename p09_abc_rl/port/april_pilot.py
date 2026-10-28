"""Bounded real CPU mechanism pilot; upstream MCTSNode, real graph/BERT/policy/ABC."""
import os,sys,json,time,hashlib,re,subprocess,math,shutil
from pathlib import Path
import numpy as np
import torch
R=Path('/home/shugu/work/paper-reproduction-april-20261028')
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'repaired'));sys.path.insert(0,str(P))
from trainer import Trainer
from LogicSynthesisEnv import LogicSynthesisEnv, RESYN2_CMD, synthesisOpToPosDic
from mcts import MCTSNode
from mechanism import nearest_distance,guidance_exponent
import abc_py
O=R/'results/abc-rl/pilot';O.mkdir(parents=True,exist_ok=True)
A=R/'assets/abc-rl';ABC=R/'tools/abc-rl/abc/abc'
ledger=O/'calls.jsonl'
def save(name,obj): (O/name).write_text(json.dumps(obj,indent=2)+'\n')
def record(obj):
 with ledger.open('a') as f:f.write(json.dumps(obj)+'\n');f.flush()
torch.set_num_threads(8);torch.manual_seed(566);np.random.seed(566)
trainer=Trainer(str(A/'nn_model.pt'));trainer.step_model.eval()
strict=torch.load(A/'nn_model.pt',weights_only=True,map_location='cpu')
assert all(torch.equal(v,trainer.step_model.state_dict()[k]) for k,v in strict.items())
env=LogicSynthesisEnv.__new__(LogicSynthesisEnv)
env._abc=abc_py.AbcInterface();env._abc.start()
graphs={};inference={}
for name in ['alu2','int2float','sin','cavlc']:
 t=time.monotonic();g=env.extract_init_graph(str(A/(name+'.aig')));graphs[name]=g
 d=env.createDataFromGraphAndSequence('0 0',g)
 pi,val,emb=trainer.stepNgetEmbedding([d]);assert np.isfinite(pi).all() and np.isfinite(emb).all()
 inference[name]=dict(nodes=g['nodes'],edges=g['edge_index'].shape[1],probabilities=pi[0].tolist(),value=float(val[0]),embedding=emb[0].tolist(),seconds=time.monotonic()-t)
 record(dict(kind='native_graph_read',circuit=name,nodes=g['nodes'],edges=g['edge_index'].shape[1]))
env._abc.end()
bank=[inference[n]['embedding'] for n in ['alu2','int2float']]
gates={n:dict(distance=nearest_distance(inference[n]['embedding'],bank)) for n in ['sin','cavlc']}
for g in gates.values():g['beta']=guidance_exponent(g['distance'])
save('inference.json',dict(strict_keys=len(strict),bert_revision='cd5ef92a9fb2f889e972770a36d4ed042daf221e',circuits=inference,train_only_subset_bank=['alu2','int2float'],gates=gates))
if '--preflight' in sys.argv: print('REAL_INFERENCE_OK',json.dumps(gates));sys.exit(0)
protocol=O/'PROTOCOL.json';assert protocol.exists(),'Freeze protocol before evaluation'
results=json.loads((O/'results.json').read_text()) if (O/'results.json').exists() else []
count=max([json.loads(line).get('id',0) for line in ledger.read_text().splitlines()] or [0])
def abc_call(kind,cmd,meta):
 global count
 count+=1;assert count<=20
 entry=dict(id=count,kind=kind,command=[str(ABC),'-c',cmd],**meta);record(dict(**entry,status='started'))
 t=time.monotonic()
 try:
  cp=subprocess.run(entry['command'],capture_output=True,text=True,timeout=120)
  text=cp.stdout+cp.stderr;(O/f'abc_{count:02d}.log').write_text(text)
  record(dict(**entry,status='finished',returncode=cp.returncode,seconds=time.monotonic()-t))
  assert cp.returncode==0,text[-1000:]
  return text
 except Exception as e:
  record(dict(**entry,status='failed',error=repr(e)));raise

def evaluate(name,recipe,arm,iteration):
 existing=[x for x in results if x['circuit']==name and x['arm']==arm and x['iteration']==iteration]
 if existing:return existing[0]
 out=O/f'{name}_{arm}_{iteration}.aig'
 cmd=f'read {A/(name+".aig")}; '+recipe+f'; write {out}; read_lib {A/"7nm.lib"}; map; topo; stime'
 text=abc_call('mapped_adp',cmd,dict(circuit=name,arm=arm,iteration=iteration,recipe=recipe))
 clean=re.sub(r'\x1b\[[0-9;]*m','',text)
 area=re.findall(r'Area\s*=\s*([0-9.eE+-]+)',clean);delay=re.findall(r'Delay\s*=\s*([0-9.eE+-]+)',clean)
 assert area and delay,clean[-2000:]
 row=dict(circuit=name,arm=arm,iteration=iteration,recipe=recipe,path=str(out),area=float(area[-1]),delay=float(delay[-1]))
 row['adp']=row['area']*row['delay'];results.append(row);save('results.json',results);return row
class LazyEnv:
 n_actions=7
 def __init__(self,name):self.name=name
 def next_state(self,state,depth,action):return state+str(int(action))
 def is_done_state(self,depth):return depth==10
for name in ['sin','cavlc']:
 baseline=evaluate(name,RESYN2_CMD,'resyn2',0)
 for arm in ['unguided','adaptive']:
  rng=np.random.default_rng(566);beta=0. if arm=='unguided' else gates[name]['beta']
  treeenv=LazyEnv(name);root=MCTSNode('', '',7,treeenv,graphData=graphs[name])
  for iteration in range(3):
   leaf=root.select_leaf();prefix=tuple(map(int,leaf.state))
   sentence=str(len(prefix))+' '+' '.join('0'+''.join(map(str,prefix)))
   data=env.createDataFromGraphAndSequence(sentence,graphs[name]);pi,value,emb=trainer.stepNgetEmbedding([data])
   priors=np.ones(7,dtype=np.float32) if arm=='unguided' else np.power(pi[0],beta)
   start=int(rng.integers(7)) if arm=='unguided' else int(np.argmax(priors))
   actions=prefix+(start,)+tuple(int(x) for x in rng.integers(0,7,size=9-len(prefix)))
   assert len(actions)==10
   recipe='; '.join(synthesisOpToPosDic[a] for a in actions)
   row=evaluate(name,recipe,arm,iteration);reward=max(-1.,1.-row['adp']/baseline['adp'])
   leaf.incorporate_estimates(priors,reward,reward,up_to=root)
   record(dict(kind='mcts_inference',circuit=name,arm=arm,iteration=iteration,prefix=list(prefix),actions=list(actions),beta=beta,raw_policy=pi[0].tolist(),priors=priors.tolist(),reward=reward,root_visits=root.child_N.tolist(),root_monte_carlo=root.child_M.tolist()))
  best=min((x for x in results if x['circuit']==name and x['arm']==arm),key=lambda x:x['adp'])
  text=abc_call('cec',f'cec {A/(name+".aig")} {best["path"]}',dict(circuit=name,arm=arm,winner=best['path']))
  assert 'Networks are equivalent' in text,text
save('summary.json',dict(evaluation_correctness_calls=count,graph_reads=4,results=results,gates=gates,scope='real-guided-search mechanism pilot; two-member train-only retrieval subset; no full-paper reproduction'))
print('PILOT_COMPLETE',count,json.dumps(gates))
