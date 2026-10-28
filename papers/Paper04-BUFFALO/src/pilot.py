#!/usr/bin/env python3
"""Bounded, non-learning buffer-tree pilot using actual ASAP7 NLDM + OpenTimer.
Not a BUFFALO model or performance reproduction. See REPRODUCTION.md.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
LIBNAME = 'asap7sc7p5t_INVBUF_RVT_TT_nldm_220122.lib.gz'
CELLS = ['BUFx2_ASAP7_75t_R', 'BUFx4f_ASAP7_75t_R', 'BUFx8_ASAP7_75t_R']
SEED = 202510


def blocks(s, keyword):
    for m in re.finditer(r'\b'+keyword+r'\s*\(\s*([^)]*)\)\s*\{', s):
        i, depth = m.end(), 1
        while depth and i < len(s):
            depth += (s[i] == '{') - (s[i] == '}')
            i += 1
        yield m.group(1).strip(), s[m.end():i-1]


def library():
    s = gzip.decompress((ROOT/'vendor'/LIBNAME).read_bytes()).decode()
    result = {}
    for name, body in blocks(s, 'cell'):
        if name not in CELLS:
            continue
        pins = dict(blocks(body, 'pin'))
        scalar = lambda b, key: float(re.search(r'\b'+key+r'\s*:\s*([\d.eE+-]+)', b).group(1))
        result[name] = {'area': scalar(body,'area'), 'cap': scalar(pins['A'],'capacitance'), 'max_cap': scalar(pins['Y'],'max_capacitance'), 'max_slew': 320.0}
    assert set(result) == set(CELLS)
    return s, result


def flatten(tree):
    return [tree] + [n for ch in tree.get('children', []) for n in flatten(ch)]


def encode(tree):
    """Factorized type/size tokens; IDs/locations carried in explicit sidecars."""
    tokens, ids, coords = [], {}, {}
    def visit(n):
        p=len(tokens)
        typ,size=n['cell'].split('_ASAP7')[0].split('x',1)
        tokens.extend([typ,size]); ids[str(p)] = n['id']
        if n['id'].startswith('B'): coords[str(p+1)] = [n['x'],n['y']]
        if n.get('children'):
            tokens.append('(')
            for ch in n['children']: visit(ch)
            tokens.append(')')
    visit(tree)
    return {'tokens':tokens, 'identity_at_type':ids, 'buffer_coordinates_at_size':coords}


def decode(seq, fixed):
    tok=seq['tokens']; pos=0
    def visit():
        nonlocal pos
        p=pos
        if p+1>=len(tok) or tok[p]!='BUF': raise ValueError('cell type')
        cell='BUFx'+tok[p+1]+'_ASAP7_75t_R'
        ident=seq['identity_at_type'].get(str(p))
        if ident is None: raise ValueError('identity')
        node={'id':ident, 'cell':cell, 'children':[]}; pos+=2
        if ident.startswith('B'):
            xy=seq['buffer_coordinates_at_size'].get(str(p+1))
            if xy is None: raise ValueError('coordinate')
            node.update(x=xy[0],y=xy[1])
        else:
            node.update(x=fixed[ident]['x'],y=fixed[ident]['y'])
        if pos<len(tok) and tok[pos]=='(':
            pos+=1
            while pos<len(tok) and tok[pos]!=')':node['children'].append(visit())
            if pos==len(tok):raise ValueError('unclosed')
            pos+=1
        return node
    tree=visit()
    if pos!=len(tok):raise ValueError('trailing tokens')
    return tree


def validate(tree, fixture, lib):
    errors=[]; nodes=flatten(tree); ids=[n['id'] for n in nodes]
    if tree['id']!='D' or tree['cell']!=CELLS[0]:errors.append('driver_mismatch')
    if len(ids)!=len(set(ids)): errors.append('duplicate_id_or_cycle')
    want={n['id'] for n in fixture['sinks']}
    got=Counter(n['id'] for n in nodes if n['id'].startswith('L'))
    if set(got)!=want or any(v!=1 for v in got.values()):errors.append('sink_coverage')
    fixed={n['id']:n for n in fixture['sinks']}
    for n in nodes:
        if n['cell'] not in lib:errors.append('illegal_cell')
        if not(0<=n['x']<=100 and 0<=n['y']<=100):errors.append('out_of_bounds')
        if n['id'].startswith('L'):
            if n.get('children'):errors.append('sink_has_children')
            if n['id'] in fixed and any(n[k]!=fixed[n['id']][k] for k in ['x','y','cell']):errors.append('sink_changed')
        elif not n.get('children'):errors.append('empty_internal')
        if len(n.get('children',[]))>fixture['max_fanout']:errors.append('max_fanout')
        cap=0.0
        for ch in n.get('children',[]):
            length=abs(n['x']-ch['x'])+abs(n['y']-ch['y'])
            cap+=lib.get(ch['cell'],{}).get('cap',0)+fixture['c_ff_per_um']*length
        if n['cell'] in lib and cap>lib[n['cell']]['max_cap']:errors.append('max_capacitance')
    return sorted(set(errors))


def fixture(name):
    if name=='aes_cut': return json.loads((ROOT/'config'/'aes_cut.json').read_text())
    rng=random.Random(SEED)
    if name=='clustered': points=[(rng.randrange(65,96),rng.randrange(5,36)) for _ in range(6)]+[(rng.randrange(65,96),rng.randrange(65,96)) for _ in range(6)]
    else: points=[(10+30*(i%4),15+35*(i//4)) for i in range(12)]
    return {'name':name,'kind':'synthetic geometric net with real ASAP7 cell timing','driver':{'id':'D','cell':CELLS[0],'x':0,'y':50}, 'sinks':[{'id':f'L{i}','cell':CELLS[0],'x':x,'y':y,'children':[]} for i,(x,y) in enumerate(points)], 'r_ohm_per_um':0.5,'c_ff_per_um':0.15,'max_fanout':4,'period_ps':100,'required_ps':80,'input_slew_ps':10,'input_delay_ps':0,'max_slew_ps':320,'output_load_ff':0.5}


def construct(f, method, index):
    rng=random.Random(SEED+index+1000*(method=='random'))
    branch=[2,3,4][index%3]; cell=CELLS[(index//3)%3]; count=0
    def group(items, depth):
        nonlocal count
        if len(items)<=branch: return items
        items=list(items)
        if method=='random':rng.shuffle(items)
        else:items.sort(key=lambda n:(n['x'],n['y']) if depth%2 else (n['y'],n['x']))
        chunks=[items[i:i+math.ceil(len(items)/branch)] for i in range(0,len(items),math.ceil(len(items)/branch))]
        out=[]
        for chunk in chunks:
            children=group(chunk,depth+1)
            x=round(statistics.mean(n['x'] for n in chunk));y=round(statistics.mean(n['y'] for n in chunk))
            if method=='random':x,y=rng.randrange(101),rng.randrange(101)
            out.append({'id':f'B{count}','cell':cell,'x':x,'y':y,'children':children});count+=1
        return out
    return dict(f['driver'],children=group(f['sinks'],0))


def emit(tree, f, out, libpath):
    nodes=flatten(tree); internal=[n for n in nodes if n.get('children')]
    outputs=[f'y{i}' for i in range(len(f['sinks']))]
    lines=['module pilot(a, clk, '+', '.join(outputs)+');','input a, clk;','output '+', '.join(outputs)+';','wire '+', '.join('n'+n['id'] for n in internal)+';']
    parent={ch['id']:n['id'] for n in internal for ch in n['children']}
    for n in nodes:
        source='a' if n['id']=='D' else 'n'+parent[n['id']]
        dest='y'+n['id'][1:] if n['id'].startswith('L') else 'n'+n['id']
        lines.append(f"{n['cell']} {n['id']} (.A({source}), .Y({dest}));")
    lines.append('endmodule'); (out/'tree.v').write_text('\n'.join(lines)+'\n')
    sdc=[f"create_clock -period {f['period_ps']:g} -name clk [get_ports clk]"]
    output_delay=f['period_ps']-f['required_ps']
    for tr in ['rise','fall']:
        sdc += [f"set_input_delay {f.get('input_delay_ps',0):g} -max -{tr} [get_ports a] -clock clk",f"set_input_transition {f['input_slew_ps']:g} -max -{tr} [get_ports a] -clock clk"]
        for y in outputs:sdc.append(f'set_output_delay {output_delay:g} -max -{tr} [get_ports {y}] -clock clk')
    sdc += [f"set_load -pin_load {f['output_load_ff']:g} [get_ports {y}]" for y in outputs]
    (out/'tree.sdc').write_text('\n'.join(sdc)+'\n')
    spef=['*SPEF "IEEE 1481-1998"','*DESIGN "pilot"','*DATE "2026-10-27"','*VENDOR "independent pilot"','*PROGRAM "pilot.py"','*VERSION "1"','*DESIGN_FLOW "NETLIST_TYPE_VERILOG"','*DIVIDER /','*DELIMITER :','*BUS_DELIMITER [ ]','*T_UNIT 1 PS','*C_UNIT 1 FF','*R_UNIT 1 OHM','*L_UNIT 1 UH']
    total_length=0
    for n in internal:
        edges=[(ch,abs(n['x']-ch['x'])+abs(n['y']-ch['y'])) for ch in n['children']]
        total_length+=sum(d for _,d in edges)
        source=n['id']+':Y'; caps={source:0.0}; ress=[]
        for ch,d in edges:
            sink=ch['id']+':A'; c=d*f['c_ff_per_um'];caps[source]+=c/2;caps[sink]=c/2
            ress.append((source,sink,max(d*f['r_ohm_per_um'],0.001)))
        spef += [f"*D_NET n{n['id']} {sum(caps.values()):.8f}",'*CONN',f'*I {source} O']+[f"*I {ch['id']}:A I" for ch,_ in edges]+['*CAP']
        spef += [f'{i} {k} {v:.8f}' for i,(k,v) in enumerate(caps.items(),1)]+['*RES']+[f'{i} {a} {b} {r:.8f}' for i,(a,b,r) in enumerate(ress,1)]+['*END']
    (out/'tree.spef').write_text('\n'.join(spef)+'\n')
    commands=['set_num_threads 1',f'read_celllib {libpath}',f'read_verilog {out}/tree.v',f'read_sdc {out}/tree.sdc',f'read_spef {out}/tree.spef']
    queries=[]
    for n in nodes:
        for tr in ['rise','fall']:
            queries.append(('slew',n['id']+':Y',tr));commands.append(f"report_slew -pin {n['id']}:Y -max -{tr}")
    for y in outputs:
        for tr in ['rise','fall']:
            queries.append(('arrival',y,tr));commands.append(f'report_at -pin {y} -max -{tr}')
    commands += ['report_timing -num_paths 1','exit']
    (out/'sta.conf').write_text('\n'.join(commands)+'\n')
    return queries,total_length


def timing_metrics(arrivals, f):
    """Use the same configured required time as emitted output-delay constraints."""
    if len(arrivals) != 2*len(f['sinks']):
        raise ValueError('Expected max rise and fall arrivals for every sink')
    endpoints=[max(arrivals[2*i:2*i+2]) for i in range(len(f['sinks']))]
    slacks=[f['required_ps']-a for a in endpoints]
    return {'tns_ps':sum(min(0,s) for s in slacks),
            'wns_ps':min(0,min(slacks)), 'max_arrival_ps':max(endpoints)}


def evaluate(tree, f, out, libpath, engine, lib):
    out.mkdir(parents=True,exist_ok=True)
    seq=encode(tree);fixed={n['id']:n for n in [f['driver']]+f['sinks']}
    restored=decode(seq,fixed);assert restored==tree
    (out/'decoded_tree.json').write_text(json.dumps(tree,indent=2)+'\n');(out/'sequence.json').write_text(json.dumps(seq,indent=2)+'\n')
    errors=validate(tree,f,lib)
    q,wl=emit(tree,f,out,libpath)
    start=time.perf_counter()
    p=subprocess.run([engine,'-q','-i',str(out/'sta.conf'),'--log',str(out/'engine.log')],capture_output=True,text=True,timeout=30)
    elapsed=time.perf_counter()-start
    (out/'stdout.txt').write_text(p.stdout);(out/'stderr.txt').write_text(p.stderr)
    vals=[float(line) for line in p.stdout.splitlines() if re.fullmatch(r'\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\s*',line)]
    if p.returncode or len(vals)!=len(q) or not all(map(math.isfinite,vals)):
        raise RuntimeError(f'STA failed in {out}: code={p.returncode}, numeric={len(vals)}/{len(q)}')
    arrivals=[v for k,v in zip(q,vals) if k[0]=='arrival'];slews=[v for k,v in zip(q,vals) if k[0]=='slew']
    timing=timing_metrics(arrivals,f)
    if max(slews)>f['max_slew_ps']:errors.append('max_transition')
    return {**timing, 'max_slew_ps':max(slews), 'buffer_area_um2':sum(lib[n['cell']]['area'] for n in flatten(tree) if n['id'].startswith('B')),'buffer_count':sum(n['id'].startswith('B') for n in flatten(tree)),'wirelength_um':wl,'violations':sorted(set(errors)), 'sta_wall_seconds':elapsed,'sta_calls':1,'roundtrip':True}


def grae(rows, weight, literal=False):
    # Eq.2 corrected area centering; literal Algorithm 2 is also audited.
    timing=[r['tns_ps'] for r in rows];area=[-r['buffer_area_um2'] for r in rows]
    def z(v, raw):
        sd=statistics.pstdev(raw)
        return 0.0 if sd<1e-12 else (v-statistics.mean(raw))/sd
    scores=[]
    for r,t,a in zip(rows,timing,area):
        if r['violations']:scores.append(-3.0)
        else:scores.append(weight*z(t,timing)+(1-weight)*(z(a,area) if not literal else ((a+statistics.mean(area))/statistics.pstdev(area) if statistics.pstdev(area)>1e-12 else 0.0)))
    return scores


def audit_mutations(f,lib):
    import copy
    tree=construct(f,'geometric',0);results=[]
    seq=encode(tree);fixed={n['id']:n for n in [f['driver']]+f['sinks']}
    for name,change in [('unclosed',lambda s:s['tokens'].pop()),('bad_type',lambda s:s['tokens'].__setitem__(0,'NAND'))]:
        s=copy.deepcopy(seq);change(s)
        try:decode(s,fixed);rejected=False
        except ValueError:rejected=True
        results.append({'mutation':name,'rejected':rejected})
    for name in ['duplicate_sink','driver_mismatch','illegal_cell','out_of_bounds','sink_changed']:
        t=copy.deepcopy(tree)
        if name=='duplicate_sink':
            leaves=[n for n in flatten(t) if n['id'].startswith('L')];leaves[1]['id']=leaves[0]['id']
        if name=='driver_mismatch':t['cell']=CELLS[1]
        if name=='illegal_cell':t['cell']='FAKE'
        if name=='out_of_bounds':t['x']=101
        if name=='sink_changed':[n for n in flatten(t) if n['id'].startswith('L')][0]['x']+=1
        e=validate(t,f,lib);results.append({'mutation':name,'rejected':bool(e),'violations':e})
    assert all(x['rejected'] for x in results)
    return results


def main():
    a=argparse.ArgumentParser();a.add_argument('--engine',required=True);a.add_argument('--smoke',action='store_true');a.add_argument('--net',choices=['clustered','spread','aes_cut']);args=a.parse_args()
    s,lib=library();libpath=(ROOT/'vendor'/'asap7.lib').resolve();libpath.write_text(s)
    start=time.perf_counter();rows=[]
    netnames=[args.net] if args.net else (['clustered'] if args.smoke else ['clustered','spread'])
    for name in netnames:
        f=fixture(name);(ROOT/'config'/f'{name}.json').write_text(json.dumps(f,indent=2)+'\n')
        for method in (['unbuffered'] if args.smoke else ['unbuffered','geometric','random']):
            for i in range(1 if method=='unbuffered' else 8):
                tree=dict(f['driver'],children=f['sinks']) if method=='unbuffered' else construct(f,method,i)
                out=(ROOT/'runs'/('smoke' if args.smoke else name)/f'{method}-{i}').resolve()
                r=evaluate(tree,f,out,libpath,args.engine,lib);r.update(net=name,method=method,index=i);rows.append(r)
                print(json.dumps(r),flush=True)
    summary={'seed':SEED,'synthetic_fixture':args.net!='aes_cut','engine':str(Path(args.engine).resolve()),'lib_sha256':hashlib.sha256((ROOT/'vendor'/LIBNAME).read_bytes()).hexdigest(),'candidates':len(rows),'sta_calls':len(rows),'sta_wall_seconds':sum(r['sta_wall_seconds'] for r in rows),'total_wall_seconds':time.perf_counter()-start,'sft_steps':0,'net_grpo_steps':0,'full_chip_feedback_steps':0,'physical_runs':0,'external_model_api_calls':0,'rows':rows}
    if not args.smoke:
        summary['mutation_checks']=audit_mutations(fixture('clustered'),lib)
        summary['selection']=[]
        for name in netnames:
            group=[r for r in rows if r['net']==name and r['method']!='unbuffered']
            for w in [0,0.5,1]:
                scores=grae(group,w);best=max(range(len(group)),key=scores.__getitem__)
                summary['selection'].append({'net':name,'timing_weight':w,'selected':group[best],'score':scores[best]})
        summary['zero_variance_handling']='Explicit local guard returns 0; not specified in paper.'
    (ROOT/'metrics'/('smoke.json' if args.smoke else ('aes_pilot.json' if args.net=='aes_cut' else 'pilot.json'))).write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main()
