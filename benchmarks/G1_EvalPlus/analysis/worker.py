"""Trusted per-task adapter. Run only inside the bubblewrap sandbox."""
import ast, copy, hashlib, json, sys, time
from spec_oracles import oracle
sys.path.insert(0, '/upstream')
from evalplus.gen.util import trusted_exec
from evalplus.eval import untrusted_check
from evalplus.eval.utils import time_limit
job=json.load(sys.stdin)
t=job['task']; code=t['prompt']+t['canonical_solution']; ep=t['entry_point']
r={'task_id':t['task_id'],'variants':{},'contracts':{},'coverage_arcs':[]}
try:
 expected={}; times={}
 for suite in ['base','plus']:
  inputs=t[suite+'_input']
  with time_limit(25): expected[suite],times[suite]=trusted_exec(code,inputs,ep,True)
  g={};exec(t['prompt']+t['contract']+t['canonical_solution'],g)
  bad=[]
  for i,inp in enumerate(inputs):
   try:
    with time_limit(1): g[ep](*copy.deepcopy(inp))
   except BaseException as e: bad.append({'index':i,'exception':type(e).__name__})
  r['contracts'][suite]={'count':len(inputs),'invalid':bad,'contract_present':bool(t['contract'].strip())}
  # Fresh independent reference execution is compared using upstream oracle semantics below.
  r[suite+'_reference_output_sha256']=hashlib.sha256(repr(expected[suite]).encode()).hexdigest()
 # Independent finite-input output checks, with root residual instead of a unique root.
 r['independent_oracle']={}
 for suite in ['base','plus']:
  bad=[];unknown=[]
  for i,(inp,out) in enumerate(zip(t[suite+'_input'],expected[suite])):
   try:
    with time_limit(1):
     if t['task_id']=='HumanEval/32':
      residual=0
      for c in reversed(inp[0]): residual=residual*out+c
      ok=abs(residual)<=t['atol']
     else:
      alt=oracle(int(t['task_id'].split('/')[1]),copy.deepcopy(inp))
      ok=out==alt or (isinstance(out,float) and isinstance(alt,float) and abs(out-alt)<=max(t['atol'],1e-6))
     if not ok: bad.append({'index':i,'reference_repr':repr(out)[:500],'alternative_repr':repr(alt)[:500] if t['task_id']!='HumanEval/32' else 'residual outside tolerance'})
   except BaseException as e: unknown.append({'index':i,'exception':type(e).__name__})
  r['independent_oracle'][suite]={'checked':len(expected[suite]),'mismatches':bad,'unknown':unknown}
 # Arcs of the canonical implementation; observed arcs, not a proof of complete branch coverage.
 g={};exec(compile(code,'<reference>','exec'),g)
 for inp in t['plus_input']:
  arcs=set();last={}
  def tracer(frame,event,arg):
   if frame.f_code.co_filename=='<reference>':
    key=id(frame)
    if event=='line':
     line=frame.f_lineno;arcs.add((last.get(key,-1),line));last[key]=line
    elif event=='return': last.pop(key,None)
   return tracer
  try:
   with time_limit(1):
    sys.settrace(tracer);g[ep](*copy.deepcopy(inp))
  finally: sys.settrace(None)
  r['coverage_arcs'].append(sorted(arcs))
 variants={'reference':code,**job['samples']}
 r['phase']=job['phase']
 # An equivalent forwarding wrapper, explicitly retained outside killed-mutant denominator.
 variants['equivalent_wrapper']=code+'\n_original='+ep+'\ndef '+ep+'(*args):\n    return _original(*args)\n'
 tree=ast.parse(code);found=False
 for node in ast.walk(tree):
  if isinstance(node,ast.Compare) and node.ops:
   mapping={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
   if type(node.ops[0]) in mapping:
    r['implementation_mutation']={'line':node.lineno,'from':type(node.ops[0]).__name__,'to':mapping[type(node.ops[0])].__name__};node.ops[0]=mapping[type(node.ops[0])]();found=True;break
 if found: variants['comparison_mutant']=ast.unparse(tree)
 else: r['implementation_mutation']={'status':'not_run','reason':'no eligible comparison'}
 variants['wrong_none']='def '+ep+'(*args):\n    return None\n'
 for name,source in variants.items():
  if job.get('minimal') and name not in {'reference',*job['samples']}:continue
  row={'source_sha256':hashlib.sha256(source.encode()).hexdigest()}
  for suite in ['base','plus']:
   state,detail=untrusted_check('humaneval',source,copy.deepcopy(t[suite+'_input']),ep,copy.deepcopy(expected[suite]),t['atol'],times[suite],False)
   row[suite]={'status':state,'details':list(map(bool,detail)),'expected_count':len(t[suite+'_input'])}
  r['variants'][name]=row
 r['status']='completed'
except BaseException as e:
 import traceback
 r['status']='infrastructure_or_reference_failure';r['exception']=type(e).__name__;r['traceback']=traceback.format_exc()
print(json.dumps(r))
