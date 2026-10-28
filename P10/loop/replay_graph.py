"""Replay historical egglog programs and dynamic unions without old Python code."""
import json,pathlib,sys
from egglog.bindings import EGraph
from engine import sx
from run_loop import restore

p=pathlib.Path(sys.argv[1]);record=json.loads(p.read_text());e=EGraph();e.set_num_threads(1)
e.parse_and_run_program(record['program']);position=0
for iteration in record['history']:
    e.parse_and_run_program('(run 1)')
    count=iteration['dynamic_unions'];batch=record['dynamic_unions'][position:position+count]
    if batch:e.parse_and_run_program('\n'.join(batch))
    position+=count
assert position==len(record['dynamic_unions'])
for variant in record['variants']:
    e.parse_and_run_program('(check (= $root '+sx(restore(variant['term']))+'))')
print(json.dumps({'artifact':str(p),'rounds':len(record['history']),'variants_in_root_class':len(record['variants']),'dynamic_unions':position}))
