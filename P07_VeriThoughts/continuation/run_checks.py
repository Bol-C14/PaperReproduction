"""Pinned released-data frontend inventory and separately frozen controls. No API calls."""
import argparse, ast, collections, hashlib, json, os, pathlib, re, resource, subprocess, sys, time

def sha(b): return hashlib.sha256(b).hexdigest()
def save(p, obj): p.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (4*1024**3, 4*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (150, 155))

def run(cmd, cwd, stem, timeout=10):
    t=time.monotonic(); before=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        r=subprocess.run(cmd,cwd=cwd,capture_output=True,timeout=timeout,preexec_fn=limits)
        rc=r.returncode; out=r.stdout; err=r.stderr; status='completed'
    except subprocess.TimeoutExpired as e:
        rc=None; out=e.stdout or b''; err=e.stderr or b''; status='timeout_unknown'
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    (cwd/(stem+'.stdout.log')).write_bytes(out); (cwd/(stem+'.stderr.log')).write_bytes(err)
    return {'command':cmd,'returncode':rc,'status':status,'wall_seconds':time.monotonic()-t,
            'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'stdout_sha256':sha(out),'stderr_sha256':sha(err)}

def main():
    a=argparse.ArgumentParser(); a.add_argument('--yosys',required=True); a.add_argument('--out',required=True)
    a.add_argument('--phase',choices=['frontend','controls'],required=True); args=a.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]; here=root/'continuation'; out=pathlib.Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=False)
    data=(here/'sources/hf_benchmark.jsonl').read_bytes()
    assert sha(data)=='7090ba304cb5bc07c797ffc94b01ae6006324baa1ea472d472ce0338d81584ca'
    rows=[json.loads(x) for x in data.splitlines()]; assert len(rows)==291
    upstream=(root/'pilot/upstream/evaluation_script.py').read_bytes()
    assert sha(upstream)=='fd27d6f767c458a8e93bda102741a17b6f19e3d05d7024dc0e3bc359bf0a8ddd'
    tree=ast.parse(upstream); names=['rename_modules_and_instantiations']
    ns={'re':re}; exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'pinned-upstream','exec'),ns)
    rename=ns[names[0]]
    version=subprocess.check_output([args.yosys,'-V'],text=True).strip(); assert version.startswith('Yosys 0.41 '),version
    meta={'phase':args.phase,'yosys_version':version,'yosys_sha256':sha(pathlib.Path(args.yosys).read_bytes()),
          'runner_sha256':sha(pathlib.Path(__file__).read_bytes()),'source_sha256':sha(upstream),'calls':[]}
    # Keep the public ledger reproducible without embedding site-specific executable paths.
    if args.phase=='frontend':
        selection=json.loads((root/'benchmark_reachability/selection.json').read_text())['selected']
        selected=[]
        for item in selection:
            i=item['row_index_zero_based']; row=rows[i]; work=out/f'row_{i:03d}'; work.mkdir()
            (work/'gold.v').write_text(row['ground_truth']); (work/'stored.v').write_text(row['generated_verilog'])
            (work/'renamed.v').write_text(rename(row['ground_truth'])[0])
            selected.append({**item,'raw_line_sha256':sha(data.splitlines(keepends=True)[i]),
                             'canonical_record_sha256':sha(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())})
            for name,script in [('gold','read_verilog gold.v'),('stored','read_verilog stored.v'),('pair','read_verilog renamed.v; read_verilog stored.v')]:
                (work/(name+'.ys')).write_text(script+'\n')
                result=run([args.yosys,'-s',name+'.ys'],work,name)
                result['command'][0]='<pinned-yosys>'; result.update(row_index=i,kind=name,script_sha256=sha((work/(name+'.ys')).read_bytes()))
                meta['calls'].append(result); save(out/'ledger.json',meta)
        save(out/'selected_hashes.json',selected)
    else:
        # First preregistered real row, not selected on a proof outcome.
        i=1; gold=rows[i]['ground_truth']
        assert gold.count('pwm <= pwm_next;')==1
        cases=[('legal_identity',gold,gold),('released_pair',gold,rows[i]['generated_verilog']),
               ('behavior_mutant',gold,gold.replace('pwm <= pwm_next;',"pwm <= 1'b0;")),('illegal_candidate',gold,'THIS IS NOT LEGAL VERILOG\n'),
               ('empty_candidate',gold,''),('empty_check_mutation','// negative control: no modules\n','THIS IS NOT LEGAL VERILOG\n')]
        for name,g,c in cases:
            work=out/name; work.mkdir(); renamed,mapping=rename(g)
            (work/'gold.v').write_text(renamed); (work/'candidate.v').write_text(c)
            (work/'responses.jsonl').write_text(json.dumps({'ground_truth':g,'full_response':c})+'\n')
            # Site environment is retained remotely, excluded from reviewable public payload.
            (work/'yosys.env').write_text('export PATH='+str(pathlib.Path(args.yosys).parent)+':$PATH\n')
            cmd=[sys.executable,str(here/'original_entrypoint.py'),str(root/'pilot/upstream/evaluation_script.py'),
                 '--results_path','responses.jsonl','--samples_per_question','1','--benchmark_path','benchmark.jsonl','--yosys_location','yosys.env']
            # Benchmark loader is line-oriented, so use one JSON object per line.
            (work/'benchmark.jsonl').write_text(json.dumps({'ground_truth':g,'verified':True})+'\n')
            result=run(cmd,work,'entrypoint',170)
            result['command']=['<venv-python>','original_entrypoint.py','<pinned-upstream>']+cmd[3:]
            result.update(case=name)
            evaluation=json.loads((work/'responses_evaluation.jsonl').read_text())
            codes=evaluation['stdout_list']; result['yosys_returncodes']=codes
            meta['calls'].append(result)
            meta.setdefault('controls',[]).append({'case':name,'source_row':i if name!='empty_check_mutation' else None,
                'gold_sha256':sha(g.encode()),'candidate_sha256':sha(c.encode()),'modules':mapping,'returncodes':codes,
                'original_success':evaluation['success'],'guarded_success':bool(c.strip()) and bool(mapping) and all(rc==0 for rc in codes),
                'kind':'real_benchmark_derived_control' if name!='empty_check_mutation' else 'synthetic_empty_check_negative_control'})
            save(out/'ledger.json',meta)
    meta['summary']={'calls':len(meta['calls']),'returncode_counts':dict(collections.Counter(str(x['returncode']) for x in meta['calls'])),
                     'cpu_seconds':sum(x['cpu_seconds'] for x in meta['calls']), 'wall_seconds':sum(x['wall_seconds'] for x in meta['calls'])}
    save(out/'ledger.json',meta); print(json.dumps(meta['summary']))

if __name__=='__main__': main()
