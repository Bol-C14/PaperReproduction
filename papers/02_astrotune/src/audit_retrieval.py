"""Retrieval tests are separate from tuning; identity queries never enter tuning DB."""
import json,re,time,hashlib
import numpy as np
from eda import ROOT
from experiment import data
from retrieval import tokens,signature,similarities,retrieve
start=time.monotonic();ds=data();rows=[]
for q in ds:
 original=q['code']; names=re.findall(r'\bmodule\s+(\w+)',original)
 altered=re.sub(r'/\*.*?\*/|//[^\n]*','',original,flags=re.S)
 for i,name in enumerate(names):altered=re.sub(r'\b'+re.escape(name)+r'\b',f'opaque_module_{i}',altered)
 count=tokens(original);other=tokens(altered)
 assert count==other,(q['id'],'renaming changed AST features')
 a=signature(count);b=signature(other)
 assert np.allclose(similarities(a,b),[1,1,1])
 ranked=retrieve(dict(q,code=altered),ds,'ast');rows.append({'query':q['id'],'kind':'alpha_rename_identity_only','scores':similarities(a,b),'rank':next(i+1 for i,r in enumerate(ranked) if r['id']==q['id']),'ast_tokens_equal':count==other})
# Explicit unit counterexample: operand constants are NOT encoded in this local tokenizer.
ca=tokens("module a(input [7:0] x,output [7:0] y);assign y=x & 8'h00;endmodule")
cb=tokens("module b(input [7:0] x,output [7:0] y);assign y=x & 8'hff;endmodule")
assert ca==cb
ranks={}
for q in ds[3:]:
 a=signature(tokens(q['code']));ranks[q['id']]={}
 for j,metric in enumerate(('simhash','minhash','haste')):
  vals=[{'id':d['id'],'score':similarities(a,signature(tokens(d['code'])))[j]} for d in ds[:3]]
  ranks[q['id']][metric]=sorted(vals,key=lambda x:(-x['score'],x['id']))
result={'identity_tests':rows,'identity_top1':sum(r['rank']==1 for r in rows)/len(rows),'tuning_no_exact_overlap':len({d['sha256'] for d in ds})==len(ds),'functional_collision_unit_test':{'equal_tokens':True,'scores':similarities(signature(ca),signature(cb)),'meaning':'zero mask vs all-one mask. Unit test only; not an EDA/benchmark result.'},'single_metric_tuning_rankings':ranks,'wall_s':time.monotonic()-start,'limits':'Identity alpha-renaming preserves exact AST. This does not test independently generated equivalent RTL, nor LLM semantic preselection.'}
(ROOT/'results/retrieval_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
