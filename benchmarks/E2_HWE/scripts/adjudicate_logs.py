"""Score private saved logs with pinned unchanged upstream report AST nodes.

Public output contains outcomes and hashes, never test/patch contents.
Hardware-behavior review remains a separate recorded human/agent audit step.
"""
import argparse,ast,dataclasses,enum,hashlib,json,pathlib,re,typing
p=argparse.ArgumentParser();p.add_argument('--upstream',type=pathlib.Path,required=True);p.add_argument('--evidence',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
ns={**vars(typing),'dataclass':dataclasses.dataclass,'field':dataclasses.field,'asdict':dataclasses.asdict,'dataclass_json':lambda c:c,'config':lambda **kw:{},'Enum':enum.Enum}
for rel,names,constants in [('base.py',{'Repository','PullRequestBase','TestStatus','Test','TestResult'},False),('repos/common.py',{'parse_test_markers'},True),('reporting.py',{'Report'},False)]:
 path=a.upstream/'hwe_bench/harness'/rel;tree=ast.parse(path.read_text());nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
 nodes += [n for n in tree.body if getattr(n,'name',None) in names or (constants and isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('_RESULTS_') for t in n.targets))]
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),ns)
parse=ns['parse_test_markers'];Report=ns['Report']
def score(base,fix):
 r=Report(org='audit',repo='audit',number=0,run_result=parse(''),test_patch_result=parse(base),fix_patch_result=parse(fix))
 return {'upstream_report_valid':r.valid,'f2p_count':len(r.f2p_tests),'p2p_count':len(r.p2p_tests),'n2p_count':len(r.n2p_tests),'s2p_count':len(r.s2p_tests)}
raw=json.loads((a.evidence/'native/native_runs.json').read_text());hist={r['id']:r for r in json.loads((a.evidence/'history/summary.json').read_text())};rows=[]
for r in raw:
 key=r['id'].split('/')[1].replace(':pr-','-');folder=a.evidence/'native'/key;base=(folder/'base.log').read_text();fix=(folder/'reference.log').read_text();im=(folder/'image-audit.log').read_text();s=score(base,fix)
 row={'id':r['id'],'status':'reference_calibration','scoring':s,'phases':{k:{q:v[q] for q in ['returncode','timed_out','seconds']} for k,v in r['phases'].items()},'pull_seconds':r['pull']['seconds'],'reference_patch_applies':hist[r['id']]['patch_applies'],'candidate_fix_objects_checked':hist[r['id']]['candidate_fix_commits'],'candidate_fix_objects_present':hist[r['id']]['present_candidate_fix_commits'],'runtime_baseline':re.search(r'BASELINE ([a-f0-9]{40})',im).group(1),'ancestor_count':int(re.search(r'ANCESTOR_COUNT (\d+)',im).group(1))}
 assert s['upstream_report_valid'] and s['f2p_count']==1 and s['n2p_count']==s['s2p_count']==0
 assert row['reference_patch_applies'] and row['phases']['base']['returncode']!=0 and row['phases']['reference']['returncode']==0 and not any(p['timed_out'] for p in row['phases'].values())
 rows.append(row)
variants=[];base=(a.evidence/'native/ibex-48/base.log').read_text()
for v in json.loads((a.evidence/'variants/summary.json').read_text()):
 s=score(base,(a.evidence/'variants'/v['mode']/'official.log').read_text())
 row={k:x for k,x in v.items() if k not in ['command','official_pass_marker']};row['scoring']=s
 assert v['returncode']==0 and v['official_exit']==0 and not v['timeout'] and s['upstream_report_valid'] and v['vector_count']==65536
 variants.append(row)
index=[]
for f in sorted(a.evidence.rglob('*')):
 if f.is_file():index.append({'path':str(f.relative_to(a.evidence)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(a.output/'native_results.json').write_text(json.dumps(rows,indent=2)+'\n');(a.output/'variant_results.json').write_text(json.dumps(variants,indent=2)+'\n');(a.output/'private_evidence_index.json').write_text(json.dumps({'evidence_id':'hwe-evidence-9ca3e0d0141656e9','paths_relative_to':'custodian-provided private evidence bundle; not included in public export','files':index},indent=2)+'\n')
print(json.dumps({'native_calibrated':len(rows),'variant_controls':len(variants),'private_files_indexed':len(index)}))
