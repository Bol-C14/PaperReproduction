"""Exhaustive static audit; no HDL execution and no model calls."""
import ast, collections, hashlib, json, pathlib, re
p=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
b=(p/'sources/hf_benchmark.jsonl').read_bytes()
m=json.loads((p/'sources/hf_metadata.json').read_text())
blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert m['sha']=='83179e5d881234f47fd783d03af22510cd9c6c35'
assert not m['private'] and not m['gated'] and not m['disabled']
assert m['cardData']['license']=='mit'
asset=next(x for x in m['siblings'] if x['rfilename']=='hf_benchmark.jsonl')
assert len(b)==asset['size']==571089 and blob==asset['blobId']=='9f486e6165e9a635087e3eeaa6990949d927537a'
tree=ast.parse((p.parent/'pilot/upstream/evaluation_script.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rename_modules_and_instantiations')
ns={'re':re}; exec(compile(ast.Module(body=[node],type_ignores=[]),'upstream','exec'),ns)
rows=[json.loads(x) for x in b.splitlines()]; assert len(rows)==291
inventory=[]
pattern=re.compile(r'\bmodule\s+(\w+)\s*(?:#\s*\(.*?\))?\s*\(',re.DOTALL)
for i,(line,row) in enumerate(zip(b.splitlines(keepends=True),rows)):
    assert set(row)=={'ground_truth','question','generated_verilog','verified'}
    assert all(isinstance(row[k],str) for k in ['ground_truth','question','generated_verilog'])
    assert isinstance(row['verified'],bool)
    item={'row_index':i,'raw_line_sha256':sha(line),'canonical_record_sha256':sha(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()),
          'keys':sorted(row),'types':{k:type(v).__name__ for k,v in row.items()},'fields':{}}
    for k,v in row.items():
        if isinstance(v,str): item['fields'][k]={'characters':len(v),'bytes':len(v.encode()),'sha256':sha(v.encode()),'empty':not v,'null':False}
    for k in ['ground_truth','generated_verilog']:
        names=pattern.findall(row[k]); mapping=ns[node.name](row[k])[1]
        assert list(dict.fromkeys(names))==list(mapping)
        item[k+'_modules']=names; item[k+'_module_count']=len(names)
        item[k+'_duplicate_names']=[name for name,n in collections.Counter(names).items() if n>1]
        item[k+'_module_tokens']=len(re.findall(r'\bmodule\b',row[k]))
        item[k+'_unmatched_module_token_warning']=item[k+'_module_tokens']!=len(names)
    inventory.append(item)
(p/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
report={'revision':m['sha'],'gated':m['gated'],'license':m['cardData']['license'],'bytes':len(b),'sha256':sha(b),'git_blob_sha1':blob,
        'matches_independent_metadata':True,'records':len(rows),'lf_count':b.count(b'\n'),'crlf_count':b.count(b'\r\n'),'final_newline':b.endswith(b'\n'),
        'schema_counts':dict(collections.Counter('|'.join(sorted(r)) for r in rows)), 'verified_counts':dict(collections.Counter(str(r['verified']) for r in rows))}
for k in ['ground_truth','generated_verilog']:
    report[k+'_zero_discovery']=[x['row_index'] for x in inventory if not x[k+'_module_count']]
    report[k+'_duplicate_name_rows']=[x['row_index'] for x in inventory if x[k+'_duplicate_names']]
    report[k+'_unmatched_token_warnings']=[x['row_index'] for x in inventory if x[k+'_unmatched_module_token_warning']]
(p/'asset_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
