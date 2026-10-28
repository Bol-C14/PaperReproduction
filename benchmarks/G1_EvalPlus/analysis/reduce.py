"""Freeze development-only suites using the pinned upstream greedy_cover function."""
import ast,hashlib,json,os,pathlib
ROOT=pathlib.Path(os.environ['EVALPLUS_REPRO_ROOT']);R=ROOT/'results/evalplus'
source=(ROOT/'checkouts/evalplus/upstream/tools/tsr/minimization.py').read_text()
tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='greedy_cover')
# Extract the exact function to avoid importing unrelated model-generation dependencies.
module=ast.Module(body=[fn],type_ignores=[]);scope={}
exec('from typing import Dict,List,Any,Tuple',scope);exec(compile(module,'upstream_greedy_cover','exec'),scope)
data=json.loads((R/'development/all-results.json').read_text());out={}
for row in data:
 tid=row['task_id']
 if row['status']!='completed':out[tid]={'status':'not_run','reason':row['status']};continue
 tests={};n=len(row['coverage_arcs']);covers={}
 for kind in ['samples','coverage','mutation']:
  tests={}
  for i in range(n):
   req=[]
   if kind=='samples':
    for m in ['chatgpt','codegen-2b']:
     d=row['variants'][m]['plus']['details']
     if i<len(d) and not d[i]:req.append((m,0))
   elif kind=='coverage':req=[('arc',tuple(x)) for x in row['coverage_arcs'][i]]
   elif 'comparison_mutant' in row['variants']:
    d=row['variants']['comparison_mutant']['plus']['details']
    if i<len(d) and not d[i]:req.append(('implementation_mutant',0))
   tests['plus_'+str(i)]=req
  _,names=scope['greedy_cover'](tid,tests,'HELD_OUT_NOT_PRESENT')
  covers[kind]=[int(x.split('_')[1]) for x in names]
 covers['combined']=sorted(set(sum(covers.values(),[])))
 out[tid]={'status':'frozen','plus_count':n,'selected_plus_indices':covers}
result={'method':'exact pinned upstream greedy_cover function; union of independently reduced criteria, as upstream merge_set_cover','greedy_function_sha256':hashlib.sha256(ast.get_source_segment(source,fn).encode()).hexdigest(),'development_results_sha256':hashlib.sha256((R/'development/all-results.json').read_bytes()).hexdigest(),'development_models':['chatgpt','codegen-2b'],'held_out_models':['gpt-4'],'coverage_deviation':'observed reference line arcs from sys.settrace; not coverage.py branch metric','mutation_deviation':'at most first eligible comparison edit per task; not complete mutmut population; equivalent wrappers retained separately','tasks':out}
(R/'frozen-reduction.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='tasks'},indent=2));print('frozen_tasks',len(out))
