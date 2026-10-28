import argparse,hashlib,json,os,pathlib,resource,subprocess,sys,time
import z3
from circuits import workload,emit,inputs,symbolic

ROOT=pathlib.Path(__file__).resolve().parent


def run(command,cwd,log,timeout):
    t=time.perf_counter()
    with log.open('w') as f:
        try:
            p=subprocess.run(command,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,
                             env={**os.environ,'YOWASP_CACHE_DIR':str(ROOT/'.cache')})
            return {'command':command,'returncode':p.returncode,'wall_seconds':time.perf_counter()-t,'log':str(log)}
        except subprocess.TimeoutExpired:
            return {'command':command,'timeout':True,'wall_seconds':time.perf_counter()-t,'log':str(log)}


def restore(x):return tuple(restore(a) for a in x) if isinstance(x,list) else x


def metrics(path):
    mod=json.loads(path.read_text())['modules']['candidate']; cells=mod['cells']
    arrival={b:0 for p in mod['ports'].values() if p['direction']=='input' for b in p['bits']}
    arrival.update({'0':0,'1':0,'x':0,'z':0}); pending=list(cells.values())
    for _ in range(len(pending)+1):
        if not pending:break
        later=[]
        for c in pending:
            ins=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs]
            outs=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs]
            if any(b not in arrival for b in ins):later.append(c);continue
            d=1+max([arrival[b] for b in ins] or [0])
            for b in outs:arrival[b]=d
        if len(later)==len(pending):raise ValueError('cyclic or unresolved gate graph')
        pending=later
    return {'gates':len(cells),'depth':max(arrival[b] for b in mod['ports']['out']['bits']),
            'cell_types':{ty:sum(c['type']==ty for c in cells.values()) for ty in sorted({c['type'] for c in cells.values()})}}


def evaluate(original,chosen,folder):
    folder.mkdir()
    env={n:z3.BitVec(n,w) for n,w in inputs(original).items()}
    s=z3.SolverFor('QF_BV');s.set(timeout=10000,random_seed=0)
    s.add(symbolic(original,env)!=symbolic(chosen,env));t=time.perf_counter();v=s.check()
    result={'z3':str(v),'z3_seconds':time.perf_counter()-t}
    (folder/'equivalence.smt2').write_text(s.to_smt2())
    if v==z3.sat:result['counterexample']=str(s.model())
    if v!=z3.unsat:return result
    a=emit(original,'original');b=emit(chosen,'candidate')
    (folder/'design.v').write_text(a+b)
    w=next(iter(inputs(original).values()))
    ports=', '.join(f'input [{bw-1}:0] {n}' for n,bw in sorted(inputs(original).items()))
    size=__import__('engine').width(original)
    def inst(term,name,out):return f'{name} u_{name}('+', '.join(f'.{n}({n})' for n in sorted(inputs(term)))+f', .out({out}));'
    miter=f'module miter({ports},output mismatch); wire [{size-1}:0] refout,testout;\n'+inst(original,'original','refout')+inst(chosen,'candidate','testout')+'\nassign mismatch = |(refout ^ testout); endmodule\n'
    (folder/'miter.v').write_text(miter)
    (folder/'verify.ys').write_text('read_verilog design.v miter.v\nprep -top miter -flatten\nsat -verify -prove mismatch 0 -show-inputs\n')
    yosys=str(ROOT/'.venv/bin/yowasp-yosys')
    result['rtl_check']=run([yosys,'-s','verify.ys'],folder,folder/'verify.log',120)
    if result['rtl_check'].get('returncode')!=0:return result
    (folder/'synth.ys').write_text('read_verilog design.v\nhierarchy -top candidate\nsynth -top candidate -noabc\nopt_clean\nwrite_json mapped.json\nstat\n')
    result['synthesis']=run([yosys,'-s','synth.ys'],folder,folder/'synth.log',120)
    if result['synthesis'].get('returncode')==0:result['mapped']=metrics(folder/'mapped.json')
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--pilot',action='store_true');parser.add_argument('--pilot-name',default='guarded_shift');parser.add_argument('--dag',action='store_true');parser.add_argument('--live',action='store_true');args=parser.parse_args()
    out=ROOT/'runs'/args.run;out.mkdir(parents=True,exist_ok=False)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
    hashes['PROTOCOL.md']=hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest()
    if args.dag:hashes['PROTOCOL_DAG.md']=hashlib.sha256((ROOT/'PROTOCOL_DAG.md').read_bytes()).hexdigest()
    if args.live:hashes['PROTOCOL_LIVE.md']=hashlib.sha256((ROOT/'PROTOCOL_LIVE.md').read_bytes()).hexdigest()
    hashes['PROTOCOL_WIDTH.md']=hashlib.sha256((ROOT/'PROTOCOL_WIDTH.md').read_bytes()).hexdigest()
    if args.live:hashes['FINAL_INTEGRATION.md']=hashlib.sha256((ROOT/'FINAL_INTEGRATION.md').read_bytes()).hexdigest()
    (out/'source_hashes.json').write_text(json.dumps(hashes,indent=2))
    tasks=[(args.pilot_name,8)] if args.pilot else [(n,w) for n in ['guarded_shift','bounded_fma','signed_abs','interpolation_clamp','repeated_bounded_mul','unconstrained'] for w in [8,16]]
    cache={};started=time.perf_counter();failed=0;rows=[]
    with (out/'RESULTS.jsonl').open('x') as stream:
        for name,w in tasks:
            original=workload(name,w)
            for mode in (['context_live'] if args.live else ['agnostic','context','context_no_vra']):
                stem=f'{name}_{w}_{mode}';job=out/(stem+'.worker.log')
                proc=run([sys.executable,str(ROOT/'worker.py'),name,str(w),mode]+(['dag'] if args.dag else []),ROOT,job,60)
                try:
                    if proc.get('returncode')!=0:raise ValueError('optimizer failed: '+str(proc))
                    optimization=json.loads(job.read_text())
                    (out/(stem+'.egraph.json')).write_text(json.dumps(optimization,indent=2))
                    for ix,v in enumerate(optimization['variants']):
                        chosen=restore(v['term']);key=hashlib.sha256((emit(original,'original')+emit(chosen,'candidate')).encode()).hexdigest()
                        if key in cache:evalrow={'cached_from':cache[key][0],**cache[key][1]}
                        else:
                            folder=out/(stem+f'_lambda{v["weight"]}')
                            evalrow=evaluate(original,chosen,folder);cache[key]=(str(folder),evalrow)
                        row={'name':name,'width':w,'mode':mode,'weight':v['weight'],'optimizer_process':proc,
                             'optimizer_wall_seconds':optimization['wall_seconds'],'optimizer_cpu_seconds':optimization['cpu_seconds'],
                             'optimizer_peak_rss_kib':optimization['peak_rss_kib'],'nodes':len(optimization['egraph']['nodes']),
                             'history':[{k:v for k,v in h.items() if k!='report'} for h in optimization['history']],
                             'selected':v,'evaluation':evalrow,'source_sha256':hashes,'extraction':'dag' if args.dag else 'tree',
                             'dag_reports':optimization.get('dag_reports')}
                        row['passed']=('mapped' in evalrow and evalrow['z3']=='unsat' and evalrow['rtl_check'].get('returncode')==0)
                        failed+=not row['passed'];rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                        print(name,w,mode,v['weight'],row['passed'],evalrow.get('mapped'),flush=True)
                except Exception as exc:
                    row={'name':name,'width':w,'mode':mode,'error':repr(exc),'passed':False,'optimizer_process':proc}
                    failed+=1;rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush();print(row,flush=True)
    summary={'rows':len(rows),'failed':failed,'wall_seconds':time.perf_counter()-started,
             'runner_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'children_peak_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'unique_evaluations':len(cache)}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print(summary)
    return bool(failed)


if __name__=='__main__':sys.exit(main())
