#!/usr/bin/env python3
"""Bounded offline execution of original pure functions; no LLM, tool, Docker or RTL execution.
Selected optimizer definitions are AST-extracted verbatim to avoid unavailable live imports.
Original test functions execute with assert statements, no mocked model outputs.
"""
import ast, copy, hashlib, inspect, json, math, re, runpy, sys, tempfile, time, traceback
from pathlib import Path
P=Path(__file__).resolve().parents[1];U=next((P/'upstream').iterdir());sys.path.insert(0,str(U/'optimizer'))
results=[]; sources={}
def run_tests(ns,label):
 for name,fn in sorted(ns.items()):
  if name.startswith('test_') and callable(fn):
   try:
    with tempfile.TemporaryDirectory(prefix='t2s-replay-') as d:
     args={k:Path(d) for k in inspect.signature(fn).parameters if k=='tmp_path'}
     assert set(args)==set(inspect.signature(fn).parameters)
     fn(**args)
    results.append(dict(suite=label,test=name,status='pass'))
   except Exception as e: results.append(dict(suite=label,test=name,status='fail',error=repr(e),trace=traceback.format_exc()))
for name in ['test_skill_integration.py','test_skill_selector.py','test_lesson_bank.py']:
 run_tests(runpy.run_path(str(U/'tests'/name)),name)
# Explicit executable source subset; no surrogate openai/ray/telemetry implementations.
names={'Individual','_json_safe','_write_json','_append_jsonl','_append_one_jsonl','_sha256_text','_carry_prompt_for_reevaluation','_semantic_metrics','_semantic_score_from_metrics','_skill_quality_from_individual','_skill_validity_from_individual','_safe_float','_apply_combined_selection_fitness','defer_child_semantic_selection','make_standard_ea_survivor_record'}
path=U/'optimizer/run_optimizer.py';tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names];assert len(nodes)==len(names)
ns=dict(Path=Path,json=json,copy=copy,hashlib=hashlib,math=math,time=time)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
sources['optimizer_definitions']=[dict(name=n.name,line=n.lineno,end=n.end_lineno) for n in nodes]
test=U/'tests/test_standard_ea_flow.py'; tt=ast.parse(test.read_text()); funcs=[n for n in tt.body if isinstance(n,ast.FunctionDef)]
exec(compile(ast.Module(body=funcs,type_ignores=[]),str(test),'exec'),ns);run_tests(ns,'test_standard_ea_flow.py AST subset')
# Ordered public trace replay: verify provenance joins, action counts, and causal ordering only.
traces=[]
for path in sorted((U/'artifacts/rollout-examples').glob('*.jsonl')):
 for r in [json.loads(x) for x in path.read_text().splitlines() if x.strip()]:
  actions=r['actions'] if 'actions' in r else r.get('events',[])
  if not actions:
   for v in r.values():
    if isinstance(v,list) and v and isinstance(v[0],dict) and 'tool' in v[0]:actions=v;break
  assert len(actions)==r['trace_summary']['tool_call_count']
  feedback=[]
  for i,a in enumerate(actions):
   if a['tool']=='verify_feedback':
    assert any(x['action_family']=='modify' for x in actions[:i])
    assert any(x['tool']=='iverilog' for x in actions[:i])
    feedback.append(dict(sequence=a['sequence'],scalars=a.get('verifier_feedback')))
  assert len(feedback)==r['outcome']['verify_feedback_executions']
  traces.append(dict(file=path.name,outcome=r['outcome']['outcome'],tools=[x['tool'] for x in actions],feedback=feedback,skill_sha256=r['provenance']['skill_sha256'],scheduler_repeat=r.get('coordinate',{})))
payload=dict(scope='offline original pure helper tests + metadata replay; no generated model traces',tests=results,source_subset=sources,traces=traces)
(P/'metrics/replay.json').write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2));assert all(x['status']=='pass' for x in results)
