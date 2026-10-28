"""Pinned public EPFL ctrl -> real ABC mapping/strash -> frozen learned ECO -> CEC.

Teaching unit-cost genlib; no claim to original timing libraries or modified ABC.
"""
import argparse,copy,hashlib,itertools,json,pathlib,re,subprocess,sys,time
import numpy as np
import torch
from types import SimpleNamespace
ROOT=pathlib.Path(__file__).resolve().parent
LOG_PREFIX=''
sys.path.insert(0,str(ROOT.parent));sys.path.insert(0,str(ROOT.parents[1]/'pilot'))
from train import Pipeline,graph_fields,sid
from data import legal_candidates
from eco import netlist_for_table,eval_patch
LIB={
 'ZERO':([], '0'),'ONE':([], '1'),'BUF':(['a'],'01'),'INV':(['a'],'10'),
 'AND2':(['a','b'],'0001'),'NAND2':(['a','b'],'1110'),
 'OR2':(['a','b'],'0111'),'NOR2':(['a','b'],'1000')}


def read_blif(path):
    text=path.read_text().replace('\\\n',' ');lines=[x.split('#')[0].strip() for x in text.splitlines()]
    lines=[x for x in lines if x];inputs=[];outputs=[];defs={};i=0
    while i<len(lines):
        words=lines[i].split();tag=words[0];i+=1
        if tag=='.inputs':inputs=words[1:]
        elif tag=='.outputs':outputs=words[1:]
        elif tag=='.gate':
            pins=dict(w.split('=') for w in words[2:]);order,table=LIB[words[1]]
            defs[pins['O']]={'cell':words[1],'pins':[pins[p] for p in order],'tt':table}
        elif tag=='.names':
            pins=words[1:-1];out=words[-1];rows=[]
            while i<len(lines) and not lines[i].startswith('.'):
                rows.append(lines[i].split());i+=1
            off=bool(rows) and all(r[-1]=='0' for r in rows)
            table=[]
            for bits in itertools.product('01',repeat=len(pins)):
                value=int(off)
                for row in rows:
                    pattern=row[0] if pins else '';output=int(row[-1])
                    if all(p=='-' or p==b for p,b in zip(pattern,bits)):value=output
                table.append(str(value))
            defs[out]={'cell':'TABLE','pins':pins,'tt':''.join(table),'cubes':rows}
        elif tag not in ['.model','.end']:raise ValueError('unexpected BLIF directive '+tag)
    return {'inputs':inputs,'outputs':outputs,'defs':defs}


def graph_pm(blif):
    nodes=[{'cell':'PI','name':n,'pins':[]} for n in blif['inputs']];index={n:i for i,n in enumerate(blif['inputs'])};active=set()
    def visit(name):
        if name in index:return index[name]
        if name in active:raise ValueError('BLIF cycle')
        active.add(name);entry=blif['defs'][name];pins=[visit(p) for p in entry['pins']]
        i=len(nodes);nodes.append({'cell':entry['cell'],'name':name,'pins':pins,'tt':entry['tt']});index[name]=i;active.remove(name);return i
    # Include every existing mapped cell, then retain original named output order.
    for name in blif['defs']:visit(name)
    return {'nodes':nodes,'inputs':list(range(len(blif['inputs']))),'outputs':[visit(n) for n in blif['outputs']]}


def graph_bench(path,input_order):
    operations={};outputs=[]
    for line in path.read_text().splitlines():
        line=line.split('#')[0].strip()
        if not line:continue
        if line.startswith('INPUT('):continue
        if line.startswith('OUTPUT('):outputs.append(line[7:-1]);continue
        lhs,rhs=[x.strip() for x in line.split('=',1)]
        m=re.fullmatch(r'(\w+)\((.*)\)',rhs)
        operations[lhs]=(m[1],[x.strip() for x in m[2].split(',')]) if m else (rhs,[])
    nodes=[{'gate':'PI','name':n,'pins':[]} for n in input_order];index={n:i for i,n in enumerate(input_order)}
    def gate(kind,pins):i=len(nodes);nodes.append({'gate':kind,'pins':pins});return i
    def constant(bit):
        z=gate('AND',[0,gate('NOT',[0])]);return gate('NOT',[z]) if bit else z
    def visit(name):
        if name in index:return index[name]
        if name not in operations:
            if name in ['vdd','1']:i=constant(1)
            elif name in ['gnd','0']:i=constant(0)
            else:raise KeyError(name)
        else:
            kind,args=operations[name];pins=[visit(p) for p in args]
            if kind in ['AND','NOT']:i=gate(kind,pins)
            elif kind=='BUF':i=pins[0]
            elif kind in ['1','vdd','VDD']:i=constant(1)
            elif kind in ['0','gnd','GND']:i=constant(0)
            else:raise ValueError(kind)
        index[name]=i;return i
    for name in operations:visit(name)
    return {'nodes':nodes,'inputs':list(range(len(input_order))),'outputs':[visit(n) for n in outputs],'output_names':outputs}


def pm_eval(pm,pattern,target=None,override=0):
    count=len(pm['inputs']);values=list(pattern)
    for i,n in enumerate(pm['nodes'][count:],count):
        if i==target:values.append(override);continue
        key=0
        for p in n['pins']:key=2*key+values[p]
        values.append(int(n['tt'][key]))
    return values


def aig_eval(aig,pattern):
    values=list(pattern)
    for n in aig['nodes'][len(aig['inputs']):]:
        values.append((values[n['pins'][0]] & values[n['pins'][1]]) if n['gate']=='AND' else 1-values[n['pins'][0]])
    return values


def source_outputs(blif,pattern):
    # Evaluate original public BLIF covers, independent of mapped cell tables.
    cache=dict(zip(blif['inputs'],pattern))
    def get(name):
        if name in cache:return cache[name]
        n=blif['defs'][name];bits=[str(get(p)) for p in n['pins']];rows=n['cubes'];off=bool(rows) and all(r[-1]=='0' for r in rows);value=int(off)
        for row in rows:
            cube=row[0] if bits else ''
            if all(a=='-' or a==b for a,b in zip(cube,bits)):value=int(row[-1])
        cache[name]=value;return value
    return tuple(get(n) for n in blif['outputs'])


def abc(command,tag):
    binary=next((ROOT/'upstream').glob('abc-*/abc'));start=time.perf_counter()
    p=subprocess.run([str(binary),'-s','-c',command],capture_output=True,text=True,timeout=30)
    (ROOT/'logs'/f'{LOG_PREFIX}{tag}.log').write_text(p.stdout+p.stderr)
    record={'command':[str(binary),'-s','-c',command],'returncode':p.returncode,'seconds':time.perf_counter()-start,'output':p.stdout+p.stderr}
    if p.returncode:raise RuntimeError(record)
    return record


def synthesize(c,ranking,patterns,budget):
    start=time.perf_counter();rows=[]
    for x in patterns:
        gold=tuple(aig_eval(c['aig'],x)[p] for p in c['aig']['outputs'])
        zero=pm_eval(c['cut'],x,c['target'],0);one=pm_eval(c['cut'],x,c['target'],1)
        choices=[bit for bit,v in [(0,zero),(1,one)] if tuple(v[p] for p in c['cut']['outputs'])==gold]
        if not choices:raise ValueError('cannot patch this site')
        rows.append((zero,None if len(choices)==2 else choices[0]))
    for k in range(1,min(budget,len(ranking))+1):
        inputs=ranking[:k];table={};conflict=False
        for v,required in rows:
            if required is None:continue
            bits=tuple(v[p] for p in inputs)
            if bits in table and table[bits]!=required:conflict=True;break
            table[bits]=required
        if conflict:continue
        truth=[table.get(x,0) for x in itertools.product([0,1],repeat=k)]
        return {'success':True,'support_budget':k,'patch':netlist_for_table(inputs,truth),'seconds':time.perf_counter()-start}
    return {'success':False,'seconds':time.perf_counter()-start}


def export_patch(pm,target,patch,path,input_names,output_names):
    lines=['.model patched_ctrl','.inputs '+' '.join(input_names),'.outputs '+' '.join(output_names)]
    def cover(pins,out,tt):
        lines.append('.names '+' '.join(pins+[out]))
        if not pins:lines.append(tt);return
        for bits,bit in zip(itertools.product('01',repeat=len(pins)),tt):
            if bit=='1':lines.append(''.join(bits)+' 1')
    names=[n['name'] for n in pm['nodes']]
    for i,n in enumerate(pm['nodes'][len(input_names):],len(input_names)):
        if i!=target:cover([names[p] for p in n['pins']],names[i],n['tt'])
    patch_names=[]
    for i,n in enumerate(patch['nodes']):
        if n['gate']=='PI':patch_names.append(names[n['candidate']]);continue
        name=f'__deepcell_patch_{i}';assert name not in names
        cover([patch_names[p] for p in n['pins']],name,'0001' if n['gate']=='AND' else '10');patch_names.append(name)
    cover([patch_names[patch['output']]],names[target],'01');lines.append('.end');path.write_text('\n'.join(lines)+'\n')


def main():
    global LOG_PREFIX
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--training-directory',choices=['main','full_token'],default='main');args=parser.parse_args()
    torch.set_num_threads(2);torch.set_num_interop_threads(1);started=time.time()
    output_dir=ROOT/'results' if args.training_directory=='main' else ROOT/'results/full_token'
    output_dir.mkdir(exist_ok=True);LOG_PREFIX='' if args.training_directory=='main' else 'full_token_'
    original=ROOT/'input_ctrl.blif';mapped=output_dir/'mapped.blif';bench=output_dir/'golden.bench';lib=ROOT/'teaching.genlib'
    commands=[];commands.append(abc(f'read_library {lib}; read_blif {original}; strash; map; write_blif {mapped}; strash; write_bench -l {bench}; print_stats','mapping'))
    assert mapped.exists() and bench.exists()
    proof=abc(f'read_library {lib}; cec {original} {mapped}','mapping_cec');assert 'Networks are equivalent' in proof['output'];commands.append(proof)
    source=read_blif(original);mapped_source=read_blif(mapped);pm=graph_pm(mapped_source);aig=graph_bench(bench,mapped_source['inputs'])
    assert aig['output_names']==mapped_source['outputs']==source['outputs']
    assert len(pm['inputs'])<=10
    patterns=list(itertools.product([0,1],repeat=len(pm['inputs'])));truth=[]
    for x in patterns:
        expected=source_outputs(source,x);pv=pm_eval(pm,x);av=aig_eval(aig,x)
        assert tuple(pv[p] for p in pm['outputs'])==tuple(av[p] for p in aig['outputs'])==expected
        truth.append(expected)
    eligible=[]
    for t,n in enumerate(pm['nodes']):
        if len(n['pins'])!=2:continue
        if any(tuple(pm_eval(pm,x,t,0)[p] for p in pm['outputs'])!=expected for x,expected in zip(patterns,truth)):eligible.append(t)
    targets=[eligible[int(i*(len(eligible)-1)/3)] for i in range(4)];assert len(set(targets))==4
    cases=[]
    for t in targets:
        cut=copy.deepcopy(pm);cut['nodes'][t]={'cell':'PI','name':pm['nodes'][t]['name'],'pins':[]}
        cases.append({'id':f'epfl_ctrl_patch_{t}','target':t,'cut':cut,'aig':aig})
    prepared={'pm':pm,'aig':aig,'cases':cases}
    (output_dir/'paired_graphs.json').write_text(json.dumps(prepared,indent=2)+'\n')
    if args.prepare_only:
        report={'inputs':len(pm['inputs']),'outputs':len(pm['outputs']),'pm_nodes':len(pm['nodes']),'aig_nodes':len(aig['nodes']),
                'targets':targets,'abc_mapping_cec':'equivalent','exhaustive_pairing_patterns':len(patterns),'commands':commands,'seconds':time.time()-started}
        (output_dir/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return
    records=[]
    def accept(c,ranking,label):
        result=synthesize(c,ranking,patterns,len(pm['inputs']) if label=='pi_fallback' else 3)
        record={'case':c['id'],'mode':label,'target':c['target'],'ranking':ranking,**result}
        if result['success']:
            patch=result['patch']
            for x,expected in zip(patterns,truth):
                signals=pm_eval(c['cut'],x,c['target'],0);bit=eval_patch(patch,signals);values=pm_eval(c['cut'],x,c['target'],bit)
                assert tuple(values[p] for p in pm['outputs'])==expected
            path=output_dir/f'{label}_{c["target"]}.blif'
            export_patch(pm,c['target'],patch,path,mapped_source['inputs'],mapped_source['outputs'])
            proof=abc(f'cec {original} {path}',f'cec_{label}_{c["target"]}')
            assert 'Networks are equivalent' in proof['output'];commands.append(proof)
            record['verification']={'exhaustive_patterns':len(patterns),'all_outputs':len(pm['outputs']),'passed':True,'abc_cec':'equivalent','patch_blif':str(path.relative_to(ROOT))}
        records.append(record)
    for seed in [208,209]:
        for arm in (['paired_pretrained','pm_only','paired_random','no_mcm'] if args.training_directory=='main' else ['paired_pretrained','pm_only']):
            result_file=ROOT.parent/'results'/args.training_directory/f'{arm}_{seed}.json'
            if not result_file.exists():raise RuntimeError('wait for declared main runs, do not select available winners')
            result=json.loads(result_file.read_text());checkpoint=ROOT.parent/result['checkpoint_path']
            assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==result['checkpoint_sha256']
            model=Pipeline(arm,seed);model.load_state_dict(torch.load(checkpoint,weights_only=True,map_location='cpu')['state_dict'],strict=True);model.eval()
            for c in cases:
                with torch.inference_mode():
                    np.random.seed(sid(c['id']));h,f=model.aig(SimpleNamespace(**graph_fields(aig,'aig_')));model.context[c['id']]=torch.cat([h,f],1)
                    tokens=model.pm_encode(c,cut=True);out=model.contextualize([tokens],[c],[[c['target']]])[0];ids=legal_candidates(c['cut'],c['target'])
                    logits=model.rank(torch.cat([out[ids],out[c['target']].expand(len(ids),-1)],1)).reshape(-1)
                    ranking=[ids[i] for i in torch.argsort(logits,descending=True,stable=True).tolist()]
                accept(c,ranking,f'{arm}_{seed}')
            del model
    for c in cases:
        ids=legal_candidates(c['cut'],c['target']);ranking=sorted(ids,reverse=True)
        accept(c,ranking,'reverse_topological');r=np.random.default_rng(208+c['target']);r.shuffle(ids);accept(c,ids,'random')
        oracle=pm['nodes'][c['target']]['pins'];accept(c,oracle+sorted(set(ids)-set(oracle)),'oracle_direct_fanin')
        accept(c,list(range(len(pm['inputs']))),'pi_fallback')
    output={'status':'complete','training_directory':args.training_directory,'benchmark':'EPFL ctrl','inputs':len(pm['inputs']),'outputs':len(pm['outputs']),'pm_nodes':len(pm['nodes']),'aig_nodes':len(aig['nodes']),
      'library':'explicit teaching genlib, unit area/delay, not foundry timing','mapping_tool':'pinned public upstream ABC baseline map; no DeepCell &nf modifications',
      'targets':targets,'selection':'four index-quantile nontrivial 2-input sites, fixed before scoring','gold_mapping_cec':'equivalent','exhaustive_pairing_patterns':len(patterns),
      'training_on_public_circuit':False,'new_public_design_count':1,'records':records,'abc_commands':commands,'seconds':time.time()-started}
    (output_dir/'flow_results.json').write_text(json.dumps(output,indent=2)+'\n')
    (output_dir/'paired_graphs.json').write_text(json.dumps({'pm':pm,'aig':aig,'cases':cases},indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ['records','abc_commands']},indent=2));print('successes',sum(r['success'] for r in records),'trials',len(records))


if __name__=='__main__':main()
