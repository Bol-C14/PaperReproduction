"""Audit pinned private official inputs; emit hashes and counts, never gold/tests text."""
from pathlib import Path
import argparse,json,hashlib,ast,collections
import duckdb
p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
h=lambda b:hashlib.sha256(b).hexdigest()
v2=a.private/'upstream/v2';checks=[]
for line in (v2/'SHA256SUMS').read_text().splitlines():
 digest,path=line.split(maxsplit=1);f=v2/path.strip().lstrip('*');checks.append(f.exists() and h(f.read_bytes())==digest)
def load(n):
 con=duckdb.connect(); cur=con.execute('SELECT * FROM read_parquet(?)',[str(a.private/(n+'.parquet'))]); cols=[x[0] for x in cur.description]; rows=[dict(zip(cols,r)) for r in cur.fetchall()]; return {x['instance_id']:x for x in rows}
v1,now=load('v1'),load('default');common=sorted(v1.keys()&now.keys());selected=Path(__file__).resolve().parents[1]/'selected_ids.txt'
fields=['problem_statement','requirements','interface','patch','test_patch','fail_to_pass','pass_to_pass','base_commit']
changed={f:sum(v1[t].get(f)!=now[t].get(f) for t in common) for f in fields}
def norm(x,f):
 if f in ['fail_to_pass','pass_to_pass']:return sorted(ast.literal_eval(x)) if isinstance(x,str) else sorted(x or [])
 return ' '.join(str(x or '').split())
normalized={f:sum(norm(v1[t].get(f),f)!=norm(now[t].get(f),f) for t in common) for f in ['problem_statement','requirements','interface','fail_to_pass','pass_to_pass']}
source_ids={d.name for d in (v2/'tasks').iterdir() if d.is_dir()}
source_check={'ids_equal':source_ids==set(now),'gold_exact':0,'test_patch_exact':0,'config_lists_equal':0}
for task,r in now.items():
 d=v2/'tasks'/task;c=json.loads((d/'tests/config.json').read_text())
 source_check['gold_exact']+= (d/'solution/gold_patch.diff').read_text()==r['patch']
 source_check['test_patch_exact']+= (d/'tests/test_patch.patch').read_text()==r['test_patch']
 source_check['config_lists_equal']+=all(norm(c[f],f)==norm(r[f],f) for f in ['fail_to_pass','pass_to_pass'])
rows=[]
for task in selected.read_text().splitlines():
 d=v2/'tasks'/task;cfg=json.loads((d/'tests/config.json').read_text());parse=lambda x:ast.literal_eval(x) if isinstance(x,str) else x
 rows.append({'task':task,'repo':now[task]['repo'],'base_commit':now[task]['base_commit'],'matched_v1':task in v1,'changed_fields':[f for f in fields if v1[task].get(f)!=now[task].get(f)],'fail_to_pass_count':len(parse(cfg['fail_to_pass'])),'pass_to_pass_count':len(parse(cfg['pass_to_pass'])),'files_sha256':{str(f.relative_to(d)):h(f.read_bytes()) for f in sorted(d.rglob('*')) if f.is_file()}})
res={'sha256sums_count':len(checks),'sha256sums_passed':sum(checks),'v1_count':len(v1),'v2_count':len(now),'matched_ids':len(common),'v1_only_count':len(v1.keys()-now.keys()),'v2_only_count':len(now.keys()-v1.keys()),'matched_changed_fields':changed,'normalized_changed_fields':normalized,'independent_source_validation':source_check,'reader':{'name':'DuckDB','version':duckdb.__version__,'previous_reader_failure':'PyArrow 19.0.0: Repetition level histogram size mismatch; no records skipped'},'repositories':dict(collections.Counter(x['repo'] for x in now.values())),'selected':rows,'parquet_sha256':{n:h((a.private/(n+'.parquet')).read_bytes()) for n in ['default','v1']}}
a.out.write_text(json.dumps(res,indent=2));print(json.dumps({k:v for k,v in res.items() if k!='selected'},indent=2))
